"""Inter-agent memory adapter: agent-context-bridge first, stdlib fallback.

Primary path uses the ``agent-context-bridge`` pillar (ACB) exactly as
documented: ``acb record`` / ``acb inject`` / ``acb search`` semantics via
``MemoryStore`` + ``ContextRecord`` + ``search_records``.
When the pillar is not installed (portable CI), a stdlib JSONL store with
the same record/search semantics is used. No network, no secrets.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND = "unavailable"


def _pillars_allowed() -> bool:
    """`CVA_FORCE_FALLBACK=1` exercises the portable stdlib path in tests/CI."""
    return os.environ.get("CVA_FORCE_FALLBACK") != "1"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryRecord:
    agent: str
    topic: str
    summary: str
    details: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "topic": self.topic,
            "summary": self.summary,
            "details": self.details,
            "tags": list(self.tags),
            "timestamp": self.timestamp,
        }


class FallbackStore:
    """Minimal JSONL memory store (same record/search contract as ACB)."""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()
        self.bridge_dir = self.workspace / ".agent_bridge"
        self.records_file = self.bridge_dir / "records.jsonl"

    def initialize(self) -> Path:
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        if not self.records_file.exists():
            self.records_file.write_text("", encoding="utf-8")
        return self.bridge_dir

    def add_record(self, record: MemoryRecord) -> None:
        self.initialize()
        with open(self.records_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _load_all(self) -> List[MemoryRecord]:
        if not self.records_file.exists():
            return []
        out: List[MemoryRecord] = []
        with open(self.records_file, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    out.append(MemoryRecord(
                        agent=str(data.get("agent", "unknown")),
                        topic=str(data.get("topic", "general")),
                        summary=str(data.get("summary", "")),
                        details=data.get("details"),
                        tags=list(data.get("tags", [])),
                        timestamp=str(data.get("timestamp", _utcnow())),
                    ))
                except (ValueError, AttributeError):
                    continue
        return out

    def list_records(self, limit: Optional[int] = 10) -> List[MemoryRecord]:
        records = self._load_all()
        records.reverse()
        if limit is None:
            return records
        return records[: max(0, limit)]

    def search(self, query: str, limit: int = 5) -> List[MemoryRecord]:
        words = [w.lower() for w in (query or "").split()]
        if not words:
            return []
        hits: List[MemoryRecord] = []
        for rec in self._load_all()[::-1]:
            hay = " ".join([rec.topic, rec.summary, rec.details or "",
                             " ".join(rec.tags)]).lower()
            if any(w in hay for w in words):
                hits.append(rec)
                if len(hits) >= limit:
                    break
        return hits


class AgentMemory:
    """Unified memory facade: ACB when installed, JSONL fallback otherwise."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace)
        self.backend = "fallback-jsonl"
        self._store: Any = None
        self._acb: Any = None
        if _pillars_allowed():
            try:
                from agent_context_bridge.core import (  # type: ignore
                    ContextRecord,
                    MemoryStore,
                    search_records,
                )
                self._acb = (ContextRecord, search_records)
                self._store = MemoryStore(self.workspace)
                self._store.initialize()
                self.backend = "agent-context-bridge"
            except Exception:
                pass
        if self.backend != "agent-context-bridge":
            self._store = FallbackStore(self.workspace)
            self._store.initialize()
        global BACKEND
        BACKEND = self.backend

    def record(self, agent: str, topic: str, summary: str,
               details: Optional[str] = None,
               tags: Optional[List[str]] = None) -> None:
        tags = list(tags or [])
        if self.backend == "agent-context-bridge":
            ContextRecord, _ = self._acb
            self._store.add_record(ContextRecord(
                agent=agent, topic=topic, summary=summary,
                details=details, tags=tags))
        else:
            self._store.add_record(MemoryRecord(
                agent=agent, topic=topic, summary=summary,
                details=details, tags=tags))

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if self.backend == "agent-context-bridge":
            _, search_records = self._acb
            try:
                hits, _skipped = search_records(self._store, query, limit=limit)
            except ValueError:
                return []
            return [{"agent": r.agent, "topic": r.topic, "summary": r.summary,
                     "details": r.details, "tags": list(r.tags or []),
                     "timestamp": r.timestamp} for r in hits]
        return [r.to_dict() for r in self._store.search(query, limit=limit)]

    def list_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        recs = self._store.list_records(limit=limit)
        out = []
        for r in recs:
            if isinstance(r, dict):
                out.append(r)
            elif hasattr(r, "agent"):
                out.append({"agent": r.agent, "topic": r.topic,
                            "summary": r.summary,
                            "details": getattr(r, "details", None),
                            "tags": list(getattr(r, "tags", []) or []),
                            "timestamp": str(getattr(r, "timestamp", ""))})
            else:
                out.append(dict(r))
        return out

    @property
    def records_path(self) -> str:
        return os.path.join(str(self.workspace), ".agent_bridge", "records.jsonl")
