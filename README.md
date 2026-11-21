# claude-verified-agent

[![CI](https://github.com/shenn667/claude-verified-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/shenn667/claude-verified-agent/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/claude-verified-agent.svg)](https://pypi.org/project/claude-verified-agent/)
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
make banking-demo  # banking & SecOps vertical: 4 asserted offline cases
make test     # 48 contract tests (pytest, offline)
make gates    # 4 llm-eval-ci suites, exit != 0 blocks CI
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
path — the 48 tests pass identically on both paths.

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
| `evals/banking_compliance.json` | banking cited answer, off-corpus refusal, PII gate, injection gate, masked memory | 5/5 passed, exit 0 |

`pytest`: **48/48 passed** on the pillar path and **48/48 passed** with
`CVA_FORCE_FALLBACK=1` (portable stdlib path): exact verbatim citations,
refusal with zero citations, gate blocks PII/injection strings,
injection-laced questions never obeyed, answer determinism, JSON contract,
memory records, backend auditability. The count is 14 core contract tests
(`tests/test_verified_agent.py`) plus 34 banking-compliance tests
(`tests/test_banking_compliance.py`, 16 cases × 2 backends).

The red path (a leaked PII string or an obeyed injection **fails** the
gate, exit 1) is proven in `pytest`, not in the suites: the suites must
stay green or CI blocks.

## Banking & SecOps Compliance Use Case (B2B)

A regulated-banking vertical built on the same verified pipeline, shipped
under `examples/banking-compliance/`. The corpus is **100% synthetic** —
four bilingual (FR + EN) markdown files for the fictional *Banque Exemple
SA / Example Bank SA*. Every file opens with a `SYNTHETIC` header; there is
**zero real enterprise data**, no real PII, and no actual regulatory text
(the BCEAO-inspired audit policy is explicitly labelled synthetic).

Topics: PCI DSS controls (AES-256 at rest, TLS 1.2+ in transit, PAN
masking first-6/last-4, HSM key storage, 90-day key rotation), BCEAO-inspired
audit logs (10-year retention, WORM integrity, NTP sync, maker/checker),
a SecOps ransomware playbook (VLAN isolation, east-west blocking, forensic
image before rebuild, RSSI/CISO escalation within 1 hour, 72-hour regulator
notification), and IAM privileged access (mandatory bastion, phishing-resistant
MFA, quarterly review, JIT elevation, session recording) ending in an
assistant-secrecy section that serves as the injection tripwire target.

The offline demo (`demo_banking.py`, tempfile workspace, no API key) runs
four cases with hard asserts (exit 1 on any failure):

| Case | Question theme | Expected outcome |
|------|----------------|------------------|
| C1 | PCI DSS key-rotation frequency (in-corpus) | cited verbatim answer, gate PASS |
| C2 | off-corpus trading query | `no-evidence` refusal, zero citations |
| C3 | IBAN + PAN + email probe | gate blocks `no_pii_leak`; no raw value in answer or workspace; memory masked |
| C4 | injection-laced IAM question | `safety-gate` refusal via `no_injection_obey` |

```bash
make banking-demo   # 4 asserted cases, offline, exit 0 on success
make gates          # 4 blocking eval suites (incl. banking_compliance)
make test           # 48 contract tests, both backends
```

**PAN gate extension.** The pillar PII patterns are frozen and carry no
card-number rule, so the agent-side gate (`verified_agent.gates`) now
supplements **both** backends with Luhn-validated PAN detection
(`_luhn_ok` + `_pan_candidates`): 13-19 digit runs (separators
stripped) that pass the Luhn checksum are flagged as `pan` under
`no_pii_leak` and masked. Detection and masking share one overlap-safe
span collector (`_collect_spans`), so a greedy IBAN match can no longer
swallow an adjacent PAN and a phone sub-pattern cannot leave an IBAN
fragment in the masked output (no raw value or digit fragment survives).
`4111111111111111` is detected; `4111111111111112` (bad Luhn) is not.
The demo and the 34 banking tests
pass identically on the native-pillar path and with `CVA_FORCE_FALLBACK=1`.

## Quickstart (3 commands)

```bash
pip install -e .
make demo    # offline demo, no key
make gates   # 4 blocking eval suites
```

CI (`.github/workflows/ci.yml`): job `pytest` + job `gates` (one step per
suite, `llm-eval run` when installed, stdlib fallback runner otherwise).
Any red gate fails the build.

## Links

- Dataset (Hugging Face): https://huggingface.co/datasets/SHENNN667/cited-rag-golden-52
  (published under namespace `SHENNN667` — no write rights on `shenn667`;
  the lowercase `shenn667/...` URL returns 401, do not use it as the main link)
- Eval page: https://shenn667.github.io/eval/ (live, deployed from
  `shenn667/shenn667.github.io` main branch)

## License

MIT — see [LICENSE](LICENSE).
