# KR Live Rehearsal And US Exchange Breadth v1 Completion

## Repository

```text
INSTRUCTION_COMMIT = d7a01015617b3fbfb16f4194d1d02c41004a4197

PHASE_A_BRANCH = codex/20260826-kr-postdeploy-live-rehearsal-us-exchange-breadth-v1
PHASE_A_BASE = d7a01015617b3fbfb16f4194d1d02c41004a4197
PHASE_A_REPORT_COMMIT = 3b1fef7050dbed7eea535ba57e614c104d82e4de

CURRENT_MAIN_AT_REHEARSAL = 73de7d4cc35bb05af3fe40fdfbca46243e0f6f6c
CURRENT_OPERATING_AT_REHEARSAL = 73de7d4cc35bb05af3fe40fdfbca46243e0f6f6c
```

## Phase A

```text
KR_TARGET_SESSION = 2026-08-25
KR_POSTDEPLOY_LIVE_RECOLLECTION = PASS
KR_POSTDEPLOY_DATA_STABILITY = MATCH
KR_POSTDEPLOY_CANONICAL_CONTEXT = PASS
KR_POSTDEPLOY_MESSAGES = PASS 8/8
KR_POSTDEPLOY_MESSAGE_VALIDATION = PASS
KR_POSTDEPLOY_CANARY_SIMULATION = PASS 1/2/3

KR_EXACT_MESSAGES_REPORT = docs/reports/20260826-kr-postdeploy-exact-generated-messages.md

PHASE_A_FACT_MISMATCH = 0
PHASE_A_UNIT_CONFLICT = 0
PHASE_A_SESSION_DATE_CONFLICT = 0
PHASE_A_SEMANTIC_OWNERSHIP_ERRORS = 0
PHASE_A_UNSUPPORTED_CAUSALITY = 0
PHASE_A_HIDDEN_ARITHMETIC = 0
PHASE_A_TELEGRAM_SEND = 0
PHASE_A_DB_MUTATION = 0

PHASE_A_READY_TO_PROCEED = YES
```

The first post-midnight attempt failed closed. Commit
`ad0f51d6e017d8fde63984a06bf3ee7a1796ad39` changed the guard from KST calendar-date equality to
the calendar-derived latest completed regular session. The retry completed 42/42 calls and matched
the prior stable source SHA exactly.

## Phase B

```text
US_BRANCH = codex/20260826-kr-postdeploy-live-rehearsal-us-exchange-breadth-v1
US_BASE = d7a01015617b3fbfb16f4194d1d02c41004a4197
US_IMPLEMENTATION_SHA = 0e2fc6548e4eadc53df6acbdae8f92b397bd6522
US_REPORT_COMMIT = 3b1fef7050dbed7eea535ba57e614c104d82e4de
FINAL_MAIN = HEAD (resolve with git rev-parse origin/main)
OPERATING = HEAD (resolve with git -C /Users/sskim/Codex/thesis-monitor rev-parse HEAD)

NASDAQ_OFFICIAL_BREADTH_CONTRACT = PASS
NASDAQ_BREADTH = PARTIAL
NYSE_BREADTH_SOURCE = UNAVAILABLE
NYSE_BREADTH = UNAVAILABLE
US_EXCHANGE_BREADTH = PARTIAL

US_TARGET_IMMUTABLE_PACKET = 2026-08-25-us-run-37-7e04812311c2
US_TARGET_COMPLETED_SESSION = 2026-08-24
US_TARGET_PUBLICATION_STATE = PUBLICATION_PENDING
US_TARGET_LATEST_AVAILABLE_SESSION = 2026-08-20
US_BREADTH_RUN37_REPLAY = PASS 14/14, breadth injection 0
US_EXCHANGE_BREADTH_VALUE_ADD = PASS (separate published 2026-08-20 context holdout)
US_BREADTH_MESSAGE_VALIDATION = PASS
US_BREADTH_CANARY_SIMULATION = PASS 1/2/3

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
SESSION_DATE_CONFLICT = 0
BREADTH_SCOPE_MISLABEL = 0
INTRADAY_PROMOTED_AS_FINAL = 0
UNIVERSE_PARTIAL_PROMOTED = 0
DEFAULT_ZERO = 0
HIDDEN_ARITHMETIC = 0
UNSUPPORTED_CAUSALITY = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
MATERIAL_INFORMATION_LOSS = 0
TRADE_AR_LEAK = 0

FREE_ANALYST_CANARY = ENABLED_PENDING_NATURAL
FULL_MODE = OFF
CANARY_LIMIT = 1/2/3
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
TRADE_AR = OFF

US_EXCHANGE_BREADTH_PRODUCTION_READY = YES

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
P2_BACKLOG = Nasdaq exact-session publication lag; NYSE official/free breadth unavailable

NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_PROOF
PRODUCTION_MUTATION_FROM_REHEARSAL = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_SCHEDULED_TASK = 0

ZIP = 20260826-kr-live-rehearsal-us-exchange-breadth-v1-bundle.zip
ZIP_SHA256 = reported by the adjacent transport checksum after final bundle construction
```

## Validation

- Focused breadth/adapter/fail-open tests: 35 passed.
- Full pytest: 1,580 passed, one upstream deprecation warning.
- Ruff and `git diff --check`: PASS.
- Investment Knowledge and Chart Knowledge parity: PASS.
- Public Action 0.4.5, operationId 20/20 unique, output schema 4: unchanged.
- Implementation exact-SHA Actions: run `32867988586`, Test/Lint PASS.
- Runtime behavior: new supplemental provider only; packet failure remains fail-open.

No older Nasdaq row was projected into run-37. No NYSE result was derived from partial pricing.
Telegram, manual task, Pilot, DB, official assessment, original archive, and Production Assist
mutations were all zero.
