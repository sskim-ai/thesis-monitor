# Canary Fixture Root Cause

| Gate | Value |
| --- | --- |
| allowed_market_enum | ["kr", "us"] |
| contract | canary-fixture-root-cause-v1 |
| model_invocation_at_failure | 0 |
| prior_value | synthetic |
| production_schema_defect | 0 |
| repair_scope | TEST_FIXTURE_ONLY_BEFORE_FIRST_MODEL_CANARY |
| root_cause | SYNTHETIC_CANARY_FIXTURE_MARKET_ENUM_INVALID |
| status | CLOSED |

The prior stop occurred before a Directional Core model invocation: the test fixture used an invalid production routing market.

Machine proof: `20260906-synthetic-canary-resume-proofs/canary-fixture-root-cause.json`.
