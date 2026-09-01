# Technical Context Failure Isolation

Unit and replay controls show that one malformed subject becomes `INVALID` while a valid peer stays
`FULL`. A total mocked transport outage creates subject-local `UNAVAILABLE` contexts, after which
`prepare_context` still returns all decision evidence packets. Missing technicals are explicit
data-quality cautions and are neither neutral nor an automatic `HOLD`.

Run-49 enriched replay produced all 14 decision contexts despite four independently proven source
integrity failures.

`ONE_SUBJECT_OHLCV_FAILURE_BLOCKS_COHORT = 0`

`SYSTEMIC_OHLCV_OUTAGE_AUTOMATICALLY_KILLS_ALL_CANDIDATES = 0`

`MISSING_TECHNICAL_CONTEXT_SILENTLY_TREATED_AS_NEUTRAL = 0`

`TECHNICAL_UNAVAILABLE_HARD_MAPS_TO_HOLD = 0`
