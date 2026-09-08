# Track F — Unseen FIRST + A/B/C Generalization Proof

Reverify the decision hashes before FIRST.

Run unseen FIRST using the frozen source lock.

No same-generation repair.

Classify:
VALIDATED
SOURCE_COVERAGE_LIMIT
ONTOLOGY_GAP
MODEL_SEMANTIC_MISUSE
VALIDATOR_FALSE_POSITIVE
HARD_SAFETY_TRUE_REJECT
ACCOUNTING_OR_SECURITY_BASIS_BLOCK
SCHEMA_FAILURE.

Only if FIRST has no validator false positives, schema failures, or hard-safety regressions:
run A/B/C with the exact same source lock.

Measure STABLE / BOUNDARY_UNCERTAINTY / UNSTABLE.
Do not tune thresholds or majority-vote a production decision.
