"""Verified agent: memory -> cited RAG -> safety gate -> answer-or-refusal.

Pipeline (one question, fully offline, stdlib + 3 local pillars):

1. **record-contexte** (agent-context-bridge): the question is recorded as a
   shared memory item and past memory is searched for context.
2. **ask cité** (cited-rag): hybrid BM25+TF-IDF retrieval, extractive answer
   where every sentence is verbatim + cited ``[file:L1-L2]``, refusal with
   ``Insufficient evidence`` when ``max_score < min_score``.
3. **gate** (llm-eval-ci): ``no_pii_leak`` + ``no_injection_obey`` tripwires
   over the produced answer. Red gate -> refusal, never the raw text.
4. **réponse ou refus**: cited answer, or refusal (no-evidence / gate-blocked).

Each stage prefers its pillar implementation and falls back to a compact
stdlib equivalent when the pillar is not installed, so ``pytest`` and the
demo run identically everywhere. The ``backends`` field of every answer
states which implementation served each stage (auditability).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import gates
from .memory import AgentMemory

REFUSAL_NO_EVIDENCE = ("Insufficient evidence — I can't help answer "
                       "from the indexed corpus.")
REFUSAL_GATE = ("Refused by safety gate (PII/injection tripwire) — "
                "I can't help with that.")
CITATION_RE = re.compile(r"\[([^[\]]+):L(\d+)-L(\d+)\]")

_STOPWORDS = frozenset(
    "a an the and or but of to in on for with is are was were be been "
    "what how why when where which who does do did can could should would "
    "it its this that these those there here from as at by nous les des du "
    "une un et ou est sont dans pour avec que qui quoi comment".split())


def _tokens(text: str) -> List[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in toks if t not in _STOPWORDS]


@dataclass
class AgentConfig:
    corpus_dir: str | Path
    workspace_dir: str | Path
    k: int = 5
    min_score: float = 0.35
    agent_name: str = "verified-agent"


class VerifiedAgent:
    """One-shot verified Q&A over a local markdown corpus."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.memory = AgentMemory(config.workspace_dir)
        self.backends = {"memory": self.memory.backend,
                         "rag": "unavailable", "gate": "unavailable"}
        self._rag: Any = None
        self._fallback_chunks: List[Dict[str, Any]] = []
        self._init_rag()

    # -- RAG init ------------------------------------------------------
    def _init_rag(self) -> None:
        import os as _os
        if _os.environ.get("CVA_FORCE_FALLBACK") != "1":
            try:
                from cited_rag.index import build_index_data  # type: ignore
                from cited_rag.retrieval import Retriever  # type: ignore
                data, _warnings = build_index_data(str(self.config.corpus_dir))
                self._rag = Retriever(data)
                self.backends["rag"] = "cited-rag"
                return
            except Exception:
                pass
        self._fallback_chunks = self._build_fallback_chunks(
            Path(self.config.corpus_dir))
        self._rag = None
        self.backends["rag"] = "stdlib-fallback"

    @staticmethod
    def _build_fallback_chunks(root: Path) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        if not root.is_dir():
            return chunks
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in (".md", ".txt"):
                continue
            try:
                rel = str(path.relative_to(root))
                lines = path.read_text(encoding="utf-8",
                                       errors="replace").splitlines()
            except OSError:
                continue
            step, width, start = 30, 40, 0
            while start < len(lines):
                end = min(start + width, len(lines))
                text = "\n".join(lines[start:end])
                if text.strip():
                    chunks.append({"file": rel, "start_line": start + 1,
                                   "end_line": end, "text": text})
                if end >= len(lines):
                    break
                start += step
        return chunks

    # -- retrieval ------------------------------------------------------
    def _retrieve(self, question: str) -> Tuple[List[Dict[str, Any]], float]:
        """Return (hits, max_score). Hit: {chunk, score}."""
        if self._rag is not None:
            hits = self._rag.search(question, k=self.config.k)
            max_score = max((h["score"] for h in hits), default=0.0)
            return hits, max_score
        qtoks = _tokens(question)
        if not qtoks or not self._fallback_chunks:
            return [], 0.0
        scored = []
        for chunk in self._fallback_chunks:
            ctoks = set(_tokens(chunk["text"]))
            matched = sum(1 for t in set(qtoks) if t in ctoks)
            score = matched / max(1, len(set(qtoks)))
            scored.append({"chunk": chunk, "score": round(score, 4)})
        scored.sort(key=lambda h: -h["score"])
        top = scored[: max(0, self.config.k)]
        return top, max((h["score"] for h in top), default=0.0)

    # -- extractive generation ------------------------------------------
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        blocks = [b.strip() for b in text.split("\n")
                  if b.strip() and not b.lstrip().startswith("#")]
        parts = re.split(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])",
                         " ".join(blocks))
        return [p.strip() for p in parts if p.strip()]

    def _extract(self, question: str,
                 hits: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict]]:
        qtoks = set(_tokens(question))
        picked: List[Tuple[str, Dict]] = []
        seen = set()
        for hit in hits:
            chunk = hit["chunk"]
            for sent in self._split_sentences(chunk["text"]):
                key = sent.lower()
                if key in seen:
                    continue
                if qtoks and not (set(_tokens(sent)) & qtoks):
                    continue
                seen.add(key)
                picked.append((sent, chunk))
                if len(picked) >= 3:
                    break
            if len(picked) >= 3:
                break
        if not picked:  # fallback: first sentence of each hit
            for hit in hits[:3]:
                sents = self._split_sentences(hit["chunk"]["text"])
                if sents and sents[0].lower() not in seen:
                    seen.add(sents[0].lower())
                    picked.append((sents[0], hit["chunk"]))
        sentences = [s for s, _ in picked]
        citations = [{"file": c["file"], "start_line": c["start_line"],
                      "end_line": c["end_line"]} for _, c in picked]
        return sentences, citations

    # -- public API ------------------------------------------------------
    def ask(self, question: str) -> Dict[str, Any]:
        q = (question or "").strip()
        q_masked = gates.mask_pii_fallback(q)
        self.memory.record(agent=self.config.agent_name, topic="question",
                           summary=q_masked[:200] or "(empty question)",
                           details=q_masked, tags=["verified-agent", "question"])
        _mem_ctx = self.memory.search(q, limit=3)

        if self._rag is not None:
            from cited_rag.generate import generate_answer  # type: ignore
            hits, _ = self._retrieve(q)
            result = generate_answer(q, hits, min_score=self.config.min_score)
            if result.get("refused"):
                payload = self._refusal(REFUSAL_NO_EVIDENCE,
                                        float(result.get("max_score", 0.0)), 0.0)
                self._record_outcome(q, payload)
                return payload
            sentences = result["answer"]
            citations = [{"file": c["file"], "start_line": c["start_line"],
                          "end_line": c["end_line"]}
                         for c in result["citations"]]
            fidelity, max_score = (float(result.get("fidelity", 0.0)),
                                   float(result.get("max_score", 0.0)))
        else:
            hits, max_score = self._retrieve(q)
            if not hits or max_score < self.config.min_score:
                payload = self._refusal(REFUSAL_NO_EVIDENCE, max_score, 0.0)
                self._record_outcome(q, payload)
                return payload
            sentences, citations = self._extract(q, hits)
            fidelity = self._fidelity(sentences,
                                      [h["chunk"] for h in hits])
            if not sentences or fidelity < 0.5:
                payload = self._refusal(REFUSAL_NO_EVIDENCE, max_score,
                                        fidelity)
                self._record_outcome(q, payload)
                return payload

        answer_text = "\n".join(
            f"{s} [{c['file']}:L{c['start_line']}-L{c['end_line']}]"
            for s, c in zip(sentences, citations))
        gate = gates.run_gate(answer_text)
        self.backends["gate"] = gate["backend"]
        if not gate["passed"]:
            # Red gate: raw text NEVER stored nor delivered (PII/injection).
            # Audit keeps masked excerpt only; raw_blocked is dropped.
            gate.pop("raw_blocked", None)
            payload = self._refusal(REFUSAL_GATE, max_score, fidelity,
                                    gate=gate)
            self._record_outcome(q, payload)
            return payload
        payload = {"question": q, "answer_text": answer_text,
                   "answer": sentences, "citations": citations,
                   "refused": False, "refusal_reason": None,
                   "fidelity": round(fidelity, 4),
                   "max_score": round(max_score, 4),
                   "gate": gate, "memory_hits": len(_mem_ctx),
                   "backends": dict(self.backends)}
        self._record_outcome(q, payload)
        return payload

    @staticmethod
    def _fidelity(sentences: List[str], chunks: List[Dict]) -> float:
        if not sentences:
            return 0.0
        norm = lambda t: re.sub(r"\s+", " ", t.lower()).strip()  # noqa: E731
        bodies = [norm(c["text"]) for c in chunks]
        ok = sum(1 for s in sentences
                 if norm(s) and any(norm(s) in b for b in bodies))
        return ok / len(sentences)

    def _refusal(self, text: str, max_score: float, fidelity: float,
                 gate: Dict[str, Any] | None = None,
                 masked: str | None = None) -> Dict[str, Any]:
        if gate is None:
            probe = "llm-eval-ci" if gates._llm_eval_security() is not None else "stdlib-fallback"
            gates.BACKEND = probe
            gate = {"passed": True, "failed_checks": [],
                    "detections": [], "backend": probe}
        self.backends["gate"] = gate["backend"]
        reason = ("no-evidence" if text == REFUSAL_NO_EVIDENCE
                  else "safety-gate")
        return {"question": "", "answer_text": masked or text,
                "answer": [], "citations": [], "refused": True,
                "refusal_reason": reason, "fidelity": round(fidelity, 4),
                "max_score": round(max_score, 4), "gate": gate,
                "memory_hits": 0, "backends": dict(self.backends)}

    def _record_outcome(self, question: str, payload: Dict[str, Any]) -> None:
        verdict = ("refused:" + str(payload.get("refusal_reason"))
                   if payload["refused"] else "answered-cited")
        safe_details = gates.mask_pii_fallback(str(payload.get("answer_text", ""))[:2000])
        self.memory.record(
            agent=self.config.agent_name, topic="answer",
            summary=f"{verdict} | fidelity={payload['fidelity']} "
                    f"| gate={payload['gate']['backend']}",
            details=safe_details,
            tags=["verified-agent", verdict.split(":")[0]])

    def answer_json(self, question: str) -> str:
        import json as _json
        payload = self.ask(question)
        return _json.dumps({"answer": (payload["answer_text"] if payload["refused"]
                                       else payload["answer"]),
                            "citations": payload["citations"],
                            "refused": payload["refused"],
                            "fidelity": payload["fidelity"],
                            "max_score": payload["max_score"]},
                           ensure_ascii=False)


def ask(question: str, corpus_dir: str | Path = "demo/corpus",
        workspace_dir: str | Path = ".") -> Dict[str, Any]:
    """One-liner convenience: build an agent and ask one question."""
    return VerifiedAgent(AgentConfig(corpus_dir=corpus_dir,
                                     workspace_dir=workspace_dir)).ask(question)
