# Verified agent pipeline

The verified agent answers in four auditable stages.

First the question is recorded as shared memory so other agents can reuse
the context of this run.

Second the agent retrieves evidence from the local corpus with hybrid
BM25 plus TF-IDF retrieval fused by Reciprocal Rank Fusion.

Third the answer is generated extractively: every sentence is a verbatim
quote from a retrieved chunk, followed by its exact line citation.

Fourth the safety gate checks the produced answer for PII leaks and
injection obedience before delivery. A red gate means refusal.
