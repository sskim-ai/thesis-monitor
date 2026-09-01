# thesis-monitor — 2026-09-02 KST US Morning Natural Live
## Read-Only Data Extraction + V2 Production Proof

Target: `2026-09-01 US regular session`, observed on `2026-09-02 KST morning`.

Reference latest validated runtime: `26004d926247c4ef053e49b74dc8fb9654353199`.
Verify actual `origin/main`, operating HEAD, and runtime SHA before using it.

## Hard rules

- No manual source-monitor, primary, backup, dispatcher, or fallback execution.
- No Telegram resend, historical replay, DB/archive mutation, accepted-decision mutation, cache patch, scheduler change, or repair during proof.
- Production Assist remains OFF.
- Read-only inspection only.

## Reference US/foreign cohort

`CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF`

Reference count = `14`.

If the immutable cutoff cohort differs, use actual cutoff evidence and explain it. Do not force 14.

If all 14 are cutoff eligible, expected production messages are:

`1 market + 14 stocks = 15`

## 1. Run identity / scheduler / lineage

Capture:
- source-monitor run ID and planned/actual start/end
- primary/backup/dispatcher planned/actual start/end
- run ID, packet ID, claim ID
- packet claim owner and claim timestamp
- evidence cutoff and frozen-cohort timestamp
- final delivery window
- origin/main, operating HEAD, runtime SHA
- production feature state

Required:
- `US_CANONICAL_SESSION_DATE = 2026-09-01`
- `US_RUNTIME_LINEAGE = PASS/FAIL`
- `MULTIPLE_US_PRODUCERS_OWNED_SAME_PACKET = 0`
- `UNOWNED_US_RETRY = 0`
- `US_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0`

## 2. Natural CLI-path repair live proof

Prove from production artifacts/logs:
- schema file created
- effective schema path resolved
- schema exists at invocation
- model subprocess started
- model call reached
- no duplicated path like `data/ai_review/claims/data/ai_review/claims/...`

Required:
- `US_V2_SCHEMA_PATH_DUPLICATION = 0`
- `US_V2_MODEL_CALL_REACHED = PASS`

If candidate generation fails before model invocation, record the exact path/runtime error.

## 3. Frozen cutoff cohort

For each reference ticker:
- active at cutoff
- monitoring_requested
- onboarding_state
- production_eligible
- first eligible session
- included/excluded
- exclusion reason

Mandatory CPNG control.

Set:
- `US_CUTOFF_ELIGIBLE_STOCK_COUNT = ...`
- `US_EXPECTED_MESSAGE_COUNT = ...`

## 4. US market-message raw data

Extract exactly what the production market builder had available.

At minimum inspect:
- SPY
- QQQ
- IWM
- SOXX
- RSP

For each:
`symbol, session, return_pct, source, as_of, quality`.

Extract relative-strength candidates:
- QQQ vs SPY
- SOXX vs SPY
- IWM vs SPY

For each record:
`relative_return_pct, threshold, selected/not-selected, reason`.

Extract all candidate sector facts and actual selected strongest/weakest sectors.

Extract breadth/participation where configured. Missing = `UNAVAILABLE`, not zero.

## 5. 시장환경 점검 data

Extract when available:
- VIX
- US 10Y nominal yield
- US 10Y real yield
- 10Y breakeven inflation
- high-yield/credit spread
- WTI
- USD/KRW

For each:
`value/change, observation date, source, freshness, temporal role`.

Mandatory:
`US_REAL_YIELD_TEMPORAL_SAFETY = PASS/FAIL`

## 6. Night futures

Mandatory because the prior US market message omitted them.

Inspect actual configured night-futures products, including KOSPI200/KOSDAQ150 if configured.

For each:
- instrument
- target trading date/session
- provider observation timestamp
- official/provider row available?
- row_count
- change_pct
- quality
- publication readiness
- selected?
- rendered?
- omission reason

Required:
- `US_NIGHT_FUTURES_EXPECTED_COUNT = ...`
- `US_NIGHT_FUTURES_READY_COUNT = ...`
- `US_NIGHT_FUTURES_RENDERED_COUNT = ...`
- `US_NIGHT_FUTURES_STATUS = PASS / SOURCE_LIMITATION_SAFE / RENDERER_OMISSION_FAILURE / VALIDATION_FAILURE`

Interpretation:
- source unavailable + safe omission = acceptable
- source available/valid/selected + not rendered = bug

## 7. Market numeric provenance / exact payload

For every rendered market number capture:
`fact_id, field_path, formatted value, semantic type, source`.

Verify no phantom numeric errors for labels such as:
`S&P500, Russell 2000, KOSPI200, KOSDAQ150, US 10Y`.

Required:
`US_MARKET_PHANTOM_NUMERIC_ERRORS = 0`

Archive:
- market renderer text
- final validated text
- outbound payload SHA
- archive/ledger SHA
- recorded/received SHA

Set:
`US_MARKET_MESSAGE_STATUS = PASS / PARTIAL_SAFE / FAIL`

## 8. US14 source readiness

For every cutoff-eligible stock extract:
- current close / price_as_of
- OHLCV acquisition state
- latest completed D/W/M bars
- latest earnings checkpoint
- valuation availability
- thesis/event facts
- market expectation level
- Price Structure
- relevant macro inputs
- positioning/supply if supported

## 9. Packet-owned technical context

For each:
- technical_context_id
- aggregate state
- D/W/M state
- safe feature count
- blocked/invalid feature count
- source/source version
- bar fingerprint
- feature fingerprint

Set:
- `US_TECHNICAL_FULL_COUNT = ...`
- `US_TECHNICAL_PARTIAL_SAFE_COUNT = ...`
- `US_TECHNICAL_UNAVAILABLE_COUNT = ...`
- `US_TECHNICAL_INVALID_COUNT = ...`

Mandatory controls:

**CPNG**
- bad historical raw row still preserved?
- aggregate state
- safe/blocked feature counts
- invalid technical numerics visible to V2?
- secondary-source recovery used?

Required:
`CPNG_INVALID_RAW_ROW_PRESERVED = PASS`
`CPNG_INVALID_TECHNICAL_NUMERIC_VISIBLE_TO_V2 = 0`

**HUT**
- current quote
- completed-close ownership
- bar finality
- D/W/M state
- aggregate state
- automatic recovery if safe FINAL row is now available

Required:
`HUT_CURRENT_QUOTE_OWNS_COMPLETED_CLOSE = 0`

**MU / SKHY**
Confirm current recovery state from fresh evidence. Do not preserve FULL merely from old state.

Required:
`ONE_US_TECHNICAL_FAILURE_BLOCKS_COHORT = 0`

## 10. Evidence packet / prepare_context

For each ticker capture:
- thesis version
- market expectation
- evidence maturity inputs
- pricing requirement inputs
- valuation state
- earnings state
- technical aggregate
- Price Structure
- macro transmission
- Unknowns
- evidence fingerprint
- prepare_context started/completed
- context ready/failure

Set:
`US_V2_CONTEXT_READY_COUNT = ...`

## 11. Model invocation / candidate

For every model batch/subject:
- model call reached
- attempt ID / batch membership
- start/end
- response state
- timeout/rate-limit/error class
- schema parse state

For each candidate:
- candidate status
- BUY/HOLD/SELL
- confidence
- evidence maturity
- pricing requirement
- asymmetry
- confirmation cost
- preconfirmation error cost
- preconfirmation_buy
- candidate validation state

Set:
- `US_V2_MODEL_CALL_REACHED_COUNT = ...`
- `US_V2_CANDIDATE_GENERATED_COUNT = ...`
- `ONE_US_CANDIDATE_ERROR_KILLS_BATCH = 0`

Healthy reference if cohort remains 14: `14/14`.

## 12. Product/model identifier provenance

Scan US validation for identifiers containing digits.

Require:
- canonical identifier digits are not phantom standalone numeric claims
- real adjacent numeric claims remain validated
- unsupported identifiers are not automatically exempt

Set:
`US_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC = 0`

## 13. Candidate validator details

Capture every non-PASS error involving:
- numeric provenance
- semantic provenance
- PER/PBR/fPER/fPBR
- historical multiple/percentile
- price/EPS/BVPS
- risk/reward
- technical values
- market values

Do not weaken genuine guards.

## 14. Adjudication / accepted plan

For each:
- prior accepted decision
- fresh candidate
- material disagreement?
- adjudication required/invoked/completed
- result
- accepted plan present
- accepted decision
- accepted source/confidence/timing
- evidence fingerprint

Set:
- `US_ADJUDICATION_REQUIRED_COUNT = ...`
- `US_ADJUDICATION_COMPLETED_COUNT = ...`
- `US_REQUIRED_ADJUDICATION_MISSING = 0`
- `US_ACCEPTED_READY_COUNT = ...`
- `US_NOT_READY_COUNT = ...`
- `US_RAW_CANDIDATE_USED_AS_FINAL = 0`

Record actual:
- `US_ACCEPTED_BUY_COUNT`
- `US_ACCEPTED_HOLD_COUNT`
- `US_ACCEPTED_SELL_COUNT`

Mandatory path controls:
`GOOGL, HUT, TSLA, WULF, CPNG`.

Historical labels do not force today's labels.

## 15. Renderer / explicit V2 block

For each:
- selector state
- accepted plan present
- renderer route
- explicit decision block?
- suppression reason

Routes:
`V2_ACCEPTED_RENDERER / DETERMINISTIC_FALLBACK / LEGACY_V1 / OTHER`

Required:
- `US_RENDERER_ROUTE_IDENTIFIED_COUNT = ...`
- `US_FALLBACK_STOCK_COUNT = ...`
- `US_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...`
- `ACCEPTED_READY_WITHOUT_EXPLICIT_DECISION = 0`
- `LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED = 0`

`투자 논리: 유지` alone does not count as HOLD.

## 16. Final validator / correction loop

For each stock record terminal state:
`PASS / REPAIRED_PASS / REJECTED / FALLBACK_ELIGIBLE`.

Capture exact errors if non-PASS.

If correction runs:
- initial errors
- repair attempt count
- allowed actions
- terminal state

Required:
`US_VALIDATION_REPAIR_LOOP_UNBOUNDED = 0`

## 17. Fallback

If fallback occurs, record the earliest reason:
`context / model / candidate / adjudication / accepted / renderer / validator / other`.

Safe fallback is not V2 success.

## 18. Delivery

Capture:
- expected
- intent
- sent
- recorded/received
- duplicate
- orphan
- unowned retry
- attempt count
- chunk count

Compare:
`final renderer text ↔ outbound ↔ archive/ledger ↔ recorded/received payload`.

Required:
- `US_EXACTLY_ONCE_DELIVERY = PASS/FAIL`
- `US_LIVE_EXACT_PAYLOAD = PASS/FAIL`

## 19. Mandatory stock matrix

Produce one table:

`ticker | source_ready | technical | context_ready | model_reached | candidate | candidate_validation | adjudication | accepted | renderer | explicit_decision | final_validation | delivery | earliest_failure`

## 20. Mandatory market matrix

Produce one row:

`session | indices_ready | relative_ready | sector_ready | macro_temporal_safe | night_futures_ready/rendered | validator | delivery | status`

## 21. Earliest failure taxonomy

Choose the FIRST failure only:

`NONE / SOURCE_DATA_NOT_READY / SOURCE_DATA_VALIDATION_FAILED / SESSION_FRESHNESS_MISMATCH / TECHNICAL_CONTEXT_INVALID / TECHNICAL_CONTEXT_UNAVAILABLE / EVIDENCE_PACKET_INVALID / PREPARE_CONTEXT_FAILED / SCHEMA_PATH_RESOLUTION_FAILED / MODEL_TRANSPORT_FAILURE / MODEL_TIMEOUT / MODEL_RATE_LIMIT / CANDIDATE_SCHEMA_INVALID / CANDIDATE_NUMERIC_PROVENANCE_REJECTED / CANDIDATE_SEMANTIC_PROVENANCE_REJECTED / ADJUDICATION_INCOMPLETE / ACCEPTED_PLAN_NOT_CREATED / SELECTOR_WRONG_ROUTE / RENDERER_REJECTED / FINAL_VALIDATOR_REJECTED / FALLBACK_SELECTED / DELIVERY_FAILED / OTHER`

Set:
`US_FAILURE_SCOPE = NONE / SYSTEMIC / SUBJECT_SPECIFIC / MIXED`

## 22. Natural LIVE_PASS

Declare `US_V2_NATURAL_LIVE = PASS` only if:
- canonical US session correct
- cutoff cohort correct
- repaired runtime present
- natural schema path works
- model call reaches V2
- cutoff-eligible subjects reach normal candidate/accepted outcomes
- accepted-ready subjects show explicit V2 decisions
- no systemic repaired-path regression
- market message safe
- night-futures rendering/omission correctly explained
- exact payload PASS
- exactly-once PASS
- P0=0, material P1=0

If accepted-ready=14, preferred proof:
`candidate 14/14, accepted 14/14, explicit 14/14`.

## 23. Next action

If PASS:
`NO_ACTION` or `WAIT_FOR_NEXT_KR_NATURAL_LIVE`.

If fail, choose exactly one:
`BOUNDED_SOURCE_DATA_REPAIR / BOUNDED_TECHNICAL_CONTEXT_REPAIR / BOUNDED_MODEL_RUNTIME_REPAIR / BOUNDED_VALIDATOR_REPAIR / BOUNDED_RENDERER_REPAIR / BOUNDED_DELIVERY_REPAIR / TEST_LIVE_ENVIRONMENT_PARITY_REPAIR / ROLLBACK_REVIEW`

Do not perform repair in this task.

## 24. Required reports

Create:
1. `docs/reports/20260902-us-natural-live-run-identity.md`
2. `docs/reports/20260902-us-runtime-lineage.md`
3. `docs/reports/20260902-us-scheduler-ownership.md`
4. `docs/reports/20260902-us-frozen-cohort.md`
5. `docs/reports/20260902-us-market-raw-data.md`
6. `docs/reports/20260902-us-market-relative-sector-breadth.md`
7. `docs/reports/20260902-us-macro-temporal-safety.md`
8. `docs/reports/20260902-us-night-futures-proof.md`
9. `docs/reports/20260902-us-market-message-proof.md`
10. `docs/reports/20260902-us14-source-readiness.md`
11. `docs/reports/20260902-us14-technical-context.md`
12. `docs/reports/20260902-cpng-hut-live-technical-controls.md`
13. `docs/reports/20260902-us14-evidence-packet.md`
14. `docs/reports/20260902-us-v2-model-candidate-generation.md`
15. `docs/reports/20260902-us-candidate-validation.md`
16. `docs/reports/20260902-us-adjudication-accepted.md`
17. `docs/reports/20260902-us-renderer-routes.md`
18. `docs/reports/20260902-us-final-validator.md`
19. `docs/reports/20260902-us-live-exact-messages.md`
20. `docs/reports/20260902-us-live-delivery.md`
21. `docs/reports/20260902-us-live-stage-matrix.md`
22. `docs/reports/20260902-us-natural-live-proof.md`
23. `docs/reports/20260902-us-natural-live-artifact-index.md`

Machine-readable:
- `docs/reports/20260902-us-market-data.json`
- `docs/reports/20260902-us-night-futures.json`
- `docs/reports/20260902-us-live-decisions.json`
- `docs/reports/20260902-us-live-stage-matrix.json`
- `docs/reports/20260902-us-live-delivery.json`
- `docs/reports/20260902-us-natural-live-proof.json`

## 25. Completion response

Return:

```text
RUN_ID = ...
PACKET_ID = ...
US_CANONICAL_SESSION_DATE = 2026-09-01

SOURCE_MONITOR_RUN = ...
PRIMARY_RUN = ...
BACKUP_RUN = ...
DISPATCH_RUN = ...
PACKET_CLAIM_OWNER = ...
EVIDENCE_CUTOFF = ...
FINAL_DELIVERY_TIME = ...

ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...
US_RUNTIME_LINEAGE = ...

US_V2_SCHEMA_PATH_DUPLICATION = 0
US_V2_MODEL_CALL_REACHED = ...

US_CUTOFF_ELIGIBLE_STOCK_COUNT = ...
US_EXPECTED_MESSAGE_COUNT = ...

MARKET = ...
NIGHT_FUTURES = ...
US_NIGHT_FUTURES_STATUS = ...
US_MARKET_MESSAGE_STATUS = ...

US_TECHNICAL_FULL_COUNT = ...
US_TECHNICAL_PARTIAL_SAFE_COUNT = ...
US_TECHNICAL_UNAVAILABLE_COUNT = ...
US_TECHNICAL_INVALID_COUNT = ...

CPNG_LIVE_TECHNICAL = ...
HUT_LIVE_TECHNICAL = ...

US_V2_CONTEXT_READY_COUNT = ...
US_V2_MODEL_CALL_REACHED_COUNT = ...
US_V2_CANDIDATE_GENERATED_COUNT = ...
US_ACCEPTED_READY_COUNT = ...
US_ACCEPTED_BUY_COUNT = ...
US_ACCEPTED_HOLD_COUNT = ...
US_ACCEPTED_SELL_COUNT = ...

DECISIONS =
CORZ ...
CPNG ...
CRCL ...
GOOGL ...
HUT ...
IBM ...
MU ...
RXRX ...
SKHY ...
SNDK ...
TSLA ...
TSM ...
WRD ...
WULF ...

US_RENDERER_ROUTE_IDENTIFIED_COUNT = ...
US_FALLBACK_STOCK_COUNT = ...
US_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...

US_FINAL_VALIDATION_PASS_COUNT = ...
US_FINAL_VALIDATION_REJECT_COUNT = ...

US_SENT_MESSAGE_COUNT = ...
US_RECEIVED_MESSAGE_COUNT = ...
US_DUPLICATE = ...
US_ORPHAN = ...
US_UNOWNED_RETRY = ...
US_LIVE_EXACT_PAYLOAD = ...
US_EXACTLY_ONCE_DELIVERY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...
US_FAILURE_SCOPE = ...
US_PRIMARY_FAILURE_CLASS = ...
US_V2_NATURAL_LIVE = ...
NEXT_ACTION = ...

ZIP = ...
ZIP_SHA256 = ...
```

## 26. Mandatory completion ZIP

Create:
`20260902-us-morning-natural-live-data-extraction-and-proof-bundle.zip`

Include the exact instruction, all reports/JSON, exact messages, market/night-futures proof, US14 technical/candidate/accepted/renderer/validator evidence, delivery proof, runtime lineage, and artifact index.

Exclude secrets, Telegram recipient IDs, tokens, auth headers, account identifiers, hidden chain-of-thought.

## Final principle

Do not merely prove that messages arrived.

Prove:

`correct US session → market/environment data → cutoff cohort → technical context → repaired natural CLI path → model call → candidate → adjudication → accepted → explicit V2 renderer → validator → exactly-once delivery`.

Night futures:
- available but omitted = investigate
- unavailable and safely omitted = acceptable

Fallback delivered safely does not equal V2 natural-live PASS.
