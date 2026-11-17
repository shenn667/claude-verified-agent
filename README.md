# claude-verified-agent

[![CI](https://github.com/shenn667/claude-verified-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/shenn667/claude-verified-agent/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![offline](https://img.shields.io/badge/offline-stdlib--only-lightgrey.svg)](https://github.com/shenn667/claude-verified-agent)

**An end-to-end verified agent: every answer is cited or refused, every
delivery passes safety gates, every run is CI-blocked on regression.**

No hallucination by design, no PII/injection leak by gate, no silent
regression by suite. Stdlib-only core, fully offline, no API key.

```bash
pip install -e .
make demo     # 1 command: cited answer + refusal + gate verdicts
make test     # 14 contract tests (pytest, offline)
make gates    # 3 llm-eval-ci suites, exit != 0 blocks CI
```

## Architecture

```text
 question
    |
    v
 [1] record-contexte (agent-context-bridge)
    |  acb record question + answer | acb search past context
    v
 [2] ask cite (cited-rag)
    |  BM25 + TF-IDF -> RRF -> verbatim sentences + [file:L1-L2]
    |  max_score < 0.35 or fidelity < 0.5 -> "Insufficient evidence"
    v
 [3] gate (llm-eval-ci)
    |  no_pii_leak + no_injection_obey over the produced answer
    |  red gate -> refusal (raw text never delivered)
    v
 cited answer  |  refusal (no-evidence / safety-gate)
```

Each stage prefers its pillar implementation and degrades to a compact
stdlib equivalent when the pillar is not installed (`backends` field of
every answer states which implementation served each stage, so the demo
output is auditable). Set `CVA_FORCE_FALLBACK=1` to exercise the portable
path — the 14 tests pass identically on both paths.

## The 3 pillars (used, not rewritten)

| Stage | Pillar repo | How it is used here |
|-------|--------------|---------------------|
| Inter-agent memory | [agent-context-bridge](https://github.com/shenn667/agent-context-bridge) | `MemoryStore` + `ContextRecord` + `search_records`: every question and every verdict is recorded (`acb record` semantics) and past context is searched before retrieval |
| Cited RAG | [cited-rag](https://github.com/shenn667/cited-rag) | `build_index_data` + `Retriever.search` + `generate_answer`: hybrid retrieval, extractive verbatim answers with exact `[file:L1-L2]` citations, `Insufficient evidence` refusal with zero citations |
| CI gates | [llm-eval-ci](https://github.com/shenn667/llm-eval-ci) | `check_no_pii_leak` + `check_no_injection_obey` gate every answer; `evals/*.json` suites run via `llm-eval run` with blocking exit codes |

## Eval results (reproduce with `make gates` + `make test`)

`llm-eval run` on the bundled suites (deterministic, offline):

| Suite | Cases | Result |
|-------|-------|--------|
| `evals/non_regression.json` | cited answers (contains + citation regex + PII-free), off-corpus refusal | 3/3 passed, exit 0 |
| `evals/schema.json` | JSON payload contract (cited + refused shapes, budgets) | 2/2 passed, exit 0 |
| `evals/tripwires.json` | PII request refused, injection-laced prompt refused | 2/2 passed, exit 0 |

`pytest`: **14/14 passed** on the pillar path and **14/14 passed** with
`CVA_FORCE_FALLBACK=1` (portable stdlib path): exact verbatim citations,
refusal with zero citations, gate blocks PII/injection strings,
injection-laced questions never obeyed, answer determinism, JSON contract,
memory records, backend auditability.

The red path (a leaked PII string or an obeyed injection **fails** the
gate, exit 1) is proven in `pytest`, not in the suites: the suites must
stay green or CI blocks.

## Quickstart (3 commands)

```bash
pip install -e .
make demo    # offline demo, no key
make gates   # 3 blocking eval suites
```

CI (`.github/workflows/ci.yml`): job `pytest` + job `gates` (one step per
suite, `llm-eval run` when installed, stdlib fallback runner otherwise).
Any red gate fails the build.

## License

MIT — see [LICENSE](LICENSE).
