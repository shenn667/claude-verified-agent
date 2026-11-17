# Citations and fidelity

Every affirmative sentence of an answer carries a citation with the source
file and exact line offsets, for example a claim followed by its reference.

The fidelity score is the fraction of answer sentences found verbatim in
their cited chunk. Answers below the fidelity threshold of 0.5 are refused.

When no chunk scores above the minimum relevance score, the agent refuses
with Insufficient evidence instead of inventing an answer. A refused answer
carries zero citations, which the tests assert explicitly.
