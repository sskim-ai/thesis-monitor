# Track E — Unseen Ticker Cold-Start FIRST + A/B/C

Freeze architecture before unseen selection.

Select 16 unseen securities where safely supported; allowed 12–20.
No overlap with the retired 22.

Apply objective source preflight.
Minimum eligible = 12.

Run unseen FIRST without post-result repair.
Classify failures:
SOURCE_COVERAGE_LIMIT
ONTOLOGY_GAP
MODEL_SEMANTIC_MISUSE
VALIDATOR_FALSE_POSITIVE
HARD_SAFETY_TRUE_REJECT
ACCOUNTING_OR_SECURITY_BASIS_BLOCK
SCHEMA_FAILURE.

Only if FIRST has no validator/schema/hard-safety regression, run unseen A/B/C using the same source lock.

No majority voting and no same-generation tuning.
