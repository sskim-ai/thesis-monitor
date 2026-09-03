# thesis-monitor — 2026-09-03 US Morning Natural Live
## Immediate Extraction + V2 Directional-Balance Proof
## Finish and report immediately after the US cycle
## DO NOT WAIT FOR THE KR MARKET CLOSE

### 0. Scope
Target KST morning: 2026-09-03.
Target completed US regular session: 2026-09-02.
Read-only natural-live observation only.

Mandatory:
- no manual source monitor / primary / backup / dispatcher trigger
- no resend/requeue
- no production state mutation
- no repair/merge during proof
- Production Assist stays OFF
- do not wait for KR close

Hard gate:
`WAIT_FOR_KR_BEFORE_US_REPORT = 0`

As soon as the US natural cycle is terminal:
`extract -> classify -> package -> return`.

### 1. Reference US cohort
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF.
Reference count = 14.
Use actual immutable cutoff cohort if different.
If all 14 eligible: expected 1 market + 14 stocks = 15.

### 2. Run identity / scheduler / cutoff
Capture:
- source-monitor run
- primary / backup / dispatcher
- run ID / packet ID / claim ID
- packet owner / claim time
- evidence cutoff / frozen cohort time
- delivery start/end
- terminal status

Require:
- `US_CANONICAL_SESSION_DATE = 2026-09-02`
- `MULTIPLE_US_PRODUCERS_OWNED_PACKET = 0`
- `US_UNOWNED_RETRY = 0`
- `US_PACKET_COHORT_MUTATED_AFTER_CUTOFF = 0`

### 3. Runtime lineage
Capture actual:
- origin/main
- operating HEAD
- runtime/deployed SHA
- feature selector
- Codex runtime-state contract
- network-preflight contract
- directional-balance contract version

Verify runtime includes:
- Codex writable state repair
- natural path repair
- DNS/network preflight/retry
- directional balance
- same-evidence/adjudication changes
- daily-review convergence
- disclaimer removal
- Treasury 3Y/5Y/10Y/30Y block
- temporary night-futures suppression

Set `US_RUNTIME_LINEAGE = PASS/FAIL`.

### 4. Source readiness
For each cutoff-eligible ticker:
- regular close / price_as_of
- OHLCV acquisition
- technical source
- earnings checkpoint
- valuation availability
- thesis/event evidence
- relevant macro inputs

Set `US_SOURCE_READY_COUNT`.

### 5. Packet-owned technical context
For each:
- technical_context_id
- aggregate state
- D/W/M state
- safe/blocked feature counts
- source fingerprint

Set:
- US_TECHNICAL_FULL_COUNT
- US_TECHNICAL_PARTIAL_SAFE_COUNT
- US_TECHNICAL_UNAVAILABLE_COUNT
- US_TECHNICAL_INVALID_COUNT

Mandatory controls:
- CPNG invalid-row preservation
- HUT quote vs completed-close
- MU/SKHY current recovery state

Require:
- `ONE_US_TECHNICAL_FAILURE_BLOCKS_COHORT = 0`
- `US_DECISION_STAGE_LOCAL_OHLCV_HTTP = 0`

### 6. Natural network / Codex proof
Capture:
- scheduler-context DNS preflight
- TLS/connectivity preflight
- Codex state preflight
- app-server initialization
- model transport start

Set:
- US_NETWORK_PREFLIGHT
- US_CODEX_RUNTIME_STATE_PREFLIGHT
- US_CODEX_APP_SERVER_INITIALIZATION
- US_MODEL_TRANSPORT_REACHED

If failure occurs, classify exact earliest failure:
LOCAL_DNS_RESOLUTION_FAILURE /
LOCAL_NETWORK_CONNECTIVITY_FAILURE /
TLS_HANDSHAKE_FAILURE /
CODEX_APP_SERVER_TRANSPORT_FAILURE /
MODEL_PROVIDER_RESPONSE_FAILURE /
MODEL_TIMEOUT /
MODEL_RATE_LIMIT /
OTHER

Do not wait for KR after a terminal failure.

### 7. V2 prepare / model / candidate
Per ticker:
- prepare_context
- context ready
- model reached / batch
- candidate decision
- BUY balance
- SELL balance
- confidence
- evidence maturity
- candidate validation

Set:
- US_V2_CONTEXT_READY_COUNT
- US_V2_MODEL_COVERED_COUNT
- US_V2_CANDIDATE_GENERATED_COUNT

### 8. Directional balance validation
Contract:
- BUY balance + SELL balance = 10
- BUY if buy >= 6
- SELL if sell >= 6
- HOLD otherwise

Anchors:
6:4 BUY
5.5:4.5 HOLD
5:5 HOLD
4.5:5.5 HOLD
4:6 SELL

HOLD must not inherit the previous label.

Set:
- BALANCE_SUM_VALID_COUNT
- HOLD_PRIOR_CARRY_FORWARD_COUNT = 0

### 9. Candidate validation
Audit:
- schema
- evidence binding
- numeric provenance
- semantic provenance
- valuation basis
- technical safety
- canonical identifiers
- balance/label consistency

Set:
- US_CANDIDATE_VALIDATION_PASS_COUNT
- US_PHANTOM_NUMERIC_ERRORS

### 10. Adjudication / accepted
Per ticker:
- prior accepted label + balance
- fresh candidate label + balance
- prior/current evidence fingerprints
- material evidence delta?
- adjudication required/invoked/completed
- accepted label + balance
- accepted source

Set:
- US_ADJUDICATION_REQUIRED_COUNT
- US_ADJUDICATION_COMPLETED_COUNT
- US_REQUIRED_ADJUDICATION_MISSING = 0
- US_ACCEPTED_READY_COUNT
- US_RAW_CANDIDATE_USED_AS_FINAL = 0

### 11. Decision-change audit
For every accepted label change:
record ticker / prior label+balance / current label+balance / evidence delta / adjudication / whether business thesis, valuation, expectations, or price/timing changed.

Require:
`US_ACCEPTED_CHANGE_WITHOUT_EXPLANATION = 0`.

Flag large unexplained balance jumps.
Set:
`US_UNEXPLAINED_BALANCE_JUMP = 0/NONZERO`.

### 12. Mandatory GOOGL control
Capture:
- prior evidence fingerprint
- current evidence fingerprint
- prior accepted label/balance
- fresh candidate label/balance
- adjudication
- final accepted label/balance

Set:
`GOOGL_CURRENT_DECISION_EXPLAINED = PASS/FAIL`.

Do not run 3-repeat diagnostics in the live production path.

### 13. Accepted distribution
Record actual:
BUY / HOLD / SELL / NOT_READY counts.
List all 14 ticker labels and balances.

### 14. Renderer / stock message
Every accepted-ready stock must show:
`🧠 AI 분석 판단: BUY/HOLD/SELL`
and
`판단 균형: BUY x : SELL y`

Set:
- US_EXPLICIT_V2_COUNT
- US_BALANCE_VISIBLE_COUNT
- US_FALLBACK_COUNT

Require:
`COMMON_ORDER_DISCLAIMER_OCCURRENCE = 0`.

Check no internal contradiction between:
decision / balance / core judgment / re-evaluation / investment-logic status / expectations / Price Structure / valuation / next checks.

### 15. US market message
Extract and validate:
- SPY / QQQ / IWM / SOXX / RSP
- relative-strength / sector facts
- breadth/participation if configured
- all rendered numeric provenance

Set `US_MARKET_CORE_DATA = PASS/FAIL`.

### 16. Treasury curve
Mandatory user-facing:
3Y / 5Y / 10Y / 30Y nominal Treasury.

For each:
- latest safe yield
- observation date
- previous valid observation
- delta in bp
- provenance

Set:
- US_TREASURY_3Y_PRESENT
- US_TREASURY_5Y_PRESENT
- US_TREASURY_10Y_PRESENT
- US_TREASURY_30Y_PRESENT
- US_TREASURY_DELTA_PROVENANCE

### 17. Night futures
For this proof the night-futures user-facing section must be absent intentionally while the date/session convention remains pending.

Require:
- `US_NIGHT_FUTURES_USER_FACING_COUNT = 0`
- `US_NIGHT_FUTURES_SECTION_ABSENT = PASS`

Do not fail natural-live because night futures are absent.

### 18. Market final validation
Set:
`US_MARKET_MESSAGE_STATUS = PASS/PARTIAL_SAFE/FAIL`.

Require no phantom numerics, Treasury provenance PASS, intentional night suppression, correct temporal labels.

### 19. Delivery
Capture:
expected / intent / sent / acknowledged / duplicate / orphan / unowned retry.

Set:
- US_SENT_MESSAGE_COUNT
- US_ACKNOWLEDGED_MESSAGE_COUNT
- US_DUPLICATE
- US_ORPHAN
- US_UNOWNED_RETRY
- US_EXACTLY_ONCE
- US_EXACT_PAYLOAD

### 20. Mandatory per-stock table
Columns:
ticker | source_ready | technical | context | model | candidate | candidate_balance | candidate_validation | prior_accepted | prior_balance | evidence_delta | adjudication | accepted | accepted_balance | renderer | explicit_decision | balance_visible | final_validation | delivery | earliest_failure

### 21. Mandatory market row
session | core_market_data | Treasury 3Y/5Y/10Y/30Y | night_futures_absent | validator | delivery | status

### 22. Earliest-failure taxonomy
NONE /
SOURCE_DATA_NOT_READY /
TECHNICAL_CONTEXT_FAILURE /
NETWORK_PREFLIGHT_FAILURE /
CODEX_RUNTIME_STATE_FAILURE /
MODEL_TRANSPORT_FAILURE /
PREPARE_CONTEXT_FAILED /
CANDIDATE_INVALID /
BALANCE_SCHEMA_INVALID /
NUMERIC_PROVENANCE_REJECTED /
SEMANTIC_PROVENANCE_REJECTED /
ADJUDICATION_INCOMPLETE /
ACCEPTED_PLAN_NOT_CREATED /
SELECTOR_WRONG_ROUTE /
FINAL_VALIDATOR_REJECTED /
DELIVERY_FAILED /
OTHER

### 23. Immediate report rule
The moment the US production cycle is terminal:
- create reports
- create JSON
- create completion ZIP
- return completion response

Hard:
`US_REPORT_GENERATED_BEFORE_KR_CLOSE = PASS`.

### 24. Natural-live classification
Preferred PASS if cohort remains 14:
- source ready 14
- network preflight PASS
- Codex app-server PASS
- model covered 14
- candidate 14
- candidate validation 14
- accepted 14
- explicit V2 14
- balance visible 14
- fallback 0
- Treasury curve PASS
- night futures intentionally absent
- 15/15 exactly once
- exact payload PASS
- material P1 0

Set:
`US_V2_NATURAL_LIVE = PASS/PARTIAL_SAFE/FAIL`.

### 25. Required reports
Create immediately:
1. 20260903-us-natural-run-identity.md
2. 20260903-us-runtime-lineage.md
3. 20260903-us-scheduler-ownership.md
4. 20260903-us-frozen-cohort.md
5. 20260903-us-source-readiness.md
6. 20260903-us-technical-context.md
7. 20260903-us-network-codex-natural-proof.md
8. 20260903-us-v2-candidates-and-balances.md
9. 20260903-us-candidate-validation.md
10. 20260903-us-adjudication-accepted-balances.md
11. 20260903-us-decision-change-audit.md
12. 20260903-us-googl-balance-control.md
13. 20260903-us-renderer-message-consistency.md
14. 20260903-us-market-message-proof.md
15. 20260903-us-treasury-curve-proof.md
16. 20260903-us-night-futures-suppression-proof.md
17. 20260903-us-delivery-proof.md
18. 20260903-us-live-stage-matrix.md
19. 20260903-us-natural-live-immediate-proof.md
20. 20260903-us-natural-live-artifact-index.md

Machine-readable:
- 20260903-us-decisions-balances.json
- 20260903-us-decision-delta.json
- 20260903-us-market-data.json
- 20260903-us-live-stage-matrix.json
- 20260903-us-delivery.json
- 20260903-us-natural-live.json

### 26. Completion response
Return immediately:
RUN_ID / PACKET_ID / session
source/primary/backup/dispatch
claim owner / cutoff / final delivery
origin/main / operating / runtime SHA
network preflight / app-server / model transport
cutoff count / expected count / source-ready
technical states
V2 context/model/candidate/validation/adjudication/accepted
all ticker decisions + BUY:SELL balances
distribution
decision changes
GOOGL control
Treasury 3Y/5Y/10Y/30Y
night futures absent
renderer/fallback/disclaimer
delivery/exact payload/exactly once
P0/P1/P2
US_V2_NATURAL_LIVE
US_REPORT_GENERATED_BEFORE_KR_CLOSE = PASS
NEXT_ACTION
ZIP / ZIP_SHA256

### 27. Mandatory completion ZIP
Create:
`20260903-us-morning-natural-live-immediate-extraction-and-proof-bundle.zip`

Include all reports/JSON and exact sanitized market + stock messages.
Exclude recipient IDs, tokens, credentials, account identifiers, secrets, hidden chain-of-thought.

### Final principle
This task is US-only.
Do not wait for KR.
As soon as the US natural run is terminal:
extract, classify, package, return.
