# thesis-monitor — 2026-09-01 KR Natural Live Failure
## Deep Read-Only Root-Cause Investigation
## Identify the first failing stage and the exact live-data trigger
## No rerun, resend, mutation, repair, or "make it pass" behavior during proof

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Investigation date: `2026-09-01 KST`
- Target KR session: `2026-09-01 KRX completed session`
- Workstream: `KR_NATURAL_LIVE_FAILURE_DEEP_PROOF`
- Task class: `READ_ONLY_PRODUCTION_FORENSICS + DATA_TRIGGER_ISOLATION`
- Production Assist: preserve `OFF`
- Manual production job run: `0`
- Manual scheduler trigger: `0`
- Production Telegram resend: `0`
- Production DB mutation: `0`
- Accepted-decision mutation: `0`
- Monitoring/onboarding mutation: `0`
- Scheduler mutation: `0`
- Main merge/repair during proof: `0`

The user reports that the 2026-09-01 KR natural live message failed again.

Do NOT assume the failure is the same as the prior US incident.
Do NOT assume it is OHLCV, AI generation, validator, renderer, scheduler, provider, or fallback.
Prove the earliest failing stage.

# 1. Current expected KR monitored universe

Read current runtime truth first.

Reference active KR subjects at investigation start:

```text
000660  SK하이닉스
003690  코리안리
005490  POSCO홀딩스
005930  삼성전자
010120  LS일렉트릭
012450  한화에어로스페이스
047810  한국항공우주산업
086280  현대글로비스
```

Reference count: `8`

If the immutable packet cutoff cohort differs, use the actual cutoff evidence and explain why.

Expected natural packet if all eight were cutoff-eligible:

```text
KR market message = 1
KR stock messages = 8
TOTAL = 9
```

Hard:
`EXPECTED_COUNT_FORCED_WITHOUT_CUTOFF_PROOF = 0`

# 2. Deployment-lineage caution

Latest previously completed OHLC provider-integrity repair was reported as:

```text
main / operating =
69d74fdf1600f812f0e542f0c3de5fcc544e5bc6
```

A later CPNG/HUT technical-recovery work instruction may exist in documentation, but unless its implementation was actually merged and deployed before today's KR run, it must NOT be treated as runtime code.

Capture actual:

```text
origin/main
operating checkout
runtime/deployed SHA
work-instruction/doc-only descendants if any
```

Gate:

`KR_RUNTIME_LINEAGE = PASS / DOC_ONLY_DESCENDANT_NOT_RUNTIME / FAIL`

# 3. Hard read-only prohibition

During this investigation, do NOT:

```text
run KR producer manually
run primary/backup manually
run dispatcher manually
requeue the packet
resend Telegram
rewrite archive
change accepted decisions
write replacement assessments
patch provider rows
change OHLCV cache
change feature flags
restart services just to make proof pass
merge a fix
```

Service/process inspection is allowed read-only.

Hard gates:

```text
MANUAL_KR_PRODUCTION_JOB_TRIGGER = 0
MANUAL_KR_PRODUCTION_SEND = 0
KR_PRODUCTION_STATE_MUTATION = 0
KR_REPAIR_DURING_PROOF = 0
```

# 4. Identify the exact natural run

Find the exact natural run corresponding to:

```text
KRX session = 2026-09-01
KST delivery window = 2026-09-01 afternoon/evening
```

Do not assume exact times from historical runs.

Capture from actual scheduler/runtime evidence:

```text
source-monitor run ID
producer run IDs
primary scheduler planned time
primary actual start/end
backup planned time
backup actual start/end
dispatcher/fallback planned time
dispatcher/fallback actual
packet ID
claim owner
claim timestamp
evidence cutoff
frozen cohort timestamp
final delivery timestamp(s)
job exit states
```

If multiple natural attempts exist, map ownership and relationship.

# 5. Scheduler ownership / exactly-one producer

Determine:

```text
which natural task owned the packet
which attempts lost/abstained
whether primary and backup both produced artifacts
whether claim ownership was respected
whether fallback was invoked
```

Hard:

```text
MULTIPLE_KR_PRODUCERS_OWNED_SAME_PACKET = 0
UNOWNED_KR_RETRY = 0
```

# 6. Canonical session correctness

Require:

`KR_CANONICAL_SESSION_DATE = 2026-09-01`

Verify every same-day market/stock price fact uses the correct completed KR session or an explicitly labeled prior/reference role.

Check:

```text
KOSPI / KOSDAQ / KOSPI200 / KOSDAQ150 where configured
KR market breadth/cross-section if present
KR market flow if present
stock price_as_of
supply as_of
OHLCV latest completed daily
weekly/monthly completed-bar roles
macro temporal roles
```

No lookahead/future bar.

# 7. Frozen cohort at cutoff

For each of the eight record:

```text
active at cutoff
monitoring_requested
onboarding_ready
production_eligible
first eligible session
included in frozen cohort
excluded reason
```

Special control: `047810`.

Current backend may show a `needs_review` assessment. Determine whether that is:
- a valid business/daily assessment outcome
- a data-quality review state
- a decision-readiness blocker
- unrelated to production eligibility

Do not infer from the enum alone.

Hard:
`047810_STATUS_MISINTERPRETED_AS_PACKET_FAILURE = 0`

# 8. Packet immutability

After cutoff the cohort must not mutate.

Hard:
`KR_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0`

# 9. Stage 1 — source monitor / acquisition

For all eight collect a compact per-subject acquisition receipt:

```text
ticker
price/current close
price_as_of
OHLCV acquisition status
D/W/M latest completed bars
supply availability/as_of
earnings checkpoint availability
valuation context availability
company/thesis event acquisition
macro exposure input availability
```

Capture provider errors separately.

Set:
`KR_SOURCE_MONITOR_READY_COUNT = ...`

If source monitor is less than 8, identify exact failing ticker/component.

# 10. KR market-data acquisition

Audit the market packet:

```text
official/current session date
index values/returns
breadth/cross-section if configured
sector proxies
market flows
night-futures/reference inputs if configured
macro supporting inputs
```

Distinguish:

```text
UNAVAILABLE
STALE
PARTIAL
VALIDATION_FAILED
```

Do not turn missing into zero.

# 11. Price / supply data

For each KR ticker verify:

```text
price close
price_as_of
supply.available
supply.as_of_date
foreign daily / 5 / 20
institution daily / 5 / 20
individual daily / 5 / 20
foreign holding ratio
supply score/quality/primary signal if available
```

Stale supply must not be labeled as today's flow.
Supply alone must not own BUY/HOLD/SELL.

# 12. Stage 2 — packet-owned technical context

For all eight capture:

```text
technical context artifact present?
technical_context_id
source
source version
D state
W state
M state
aggregate state
safe feature count
blocked/invalid feature count
raw bar fingerprint
feature fingerprint
```

Expected from prior KR regression was 8/8 FULL, but today's live data must be independently proven.

Set:

```text
KR_TECHNICAL_FULL_COUNT = ...
KR_TECHNICAL_PARTIAL_SAFE_COUNT = ...
KR_TECHNICAL_UNAVAILABLE_COUNT = ...
KR_TECHNICAL_INVALID_COUNT = ...
```

# 13. Decision-stage local HTTP regression

Confirm today’s KR V2 decision stage did NOT reintroduce fresh localhost OHLCV HTTP.

Hard:
`KR_V2_DECISION_STAGE_LOCAL_OHLCV_HTTP = 0`

# 14. Technical data integrity

For every non-FULL subject capture exact:

```text
timeframe
bar/session
violation
source
first bad stage
feature impact
```

Do not fix during proof.

Hard:
`ONE_KR_TECHNICAL_FAILURE_BLOCKED_PEERS = 0`

# 15. Stage 3 — canonical evidence packet

For every cutoff-eligible subject collect:

```text
thesis version
latest baseline/daily assessment
earnings facts
company/thesis event facts
valuation facts
market expectation level
macro factors actually transmitted
Price Structure
technical context
Unknowns
evidence fingerprint
```

Verify:
- all V2 evidence references resolve
- no missing mandatory fact IDs
- no cross-ticker fact contamination

# 16. Today-vs-last-pass data delta

Compare today’s failing natural packet with the latest previously passing equivalent KR test/replay packet.

For every subject and market packet classify every material input change:

```text
UNCHANGED
NEW_FACT
CHANGED_VALUE
NEW_NULL
STALE
VALIDATION_FAILED
SOURCE_CHANGED
SEMANTIC_CHANGED
```

Create a field-level delta ledger.

# 17. Failure-trigger isolation

If today is a data-dependent failure, identify the smallest exact trigger:

```text
ticker
fact_id
field_path
old value/state
new value/state
source
as_of
validation rule
first failing function/stage
```

Required shape:

```text
FAILURE_TRIGGER =
ticker: ...
fact_id: ...
field_path: ...
value/state: ...
rule: ...
first failing stage: ...
```

Hard:

`KR_FAILURE_TRIGGER_EXACTLY_LOCALIZED = PASS / NOT_DATA_TRIGGERED / FAIL`

# 18. Stage 4 — V2 candidate generation

For every cutoff-eligible ticker record:

```text
prepare_context reached?
context ready?
candidate generation invoked?
model/runtime call started?
candidate returned?
schema valid?
candidate decision
confidence
evidence maturity
pricing requirement
asymmetry
confirmation cost
preconfirmation error cost
preconfirmation_buy
```

Set:
`KR_CANDIDATE_GENERATED_COUNT = ...`

If less than cutoff cohort count, identify earliest candidate-generation failure per ticker.

# 19. AI runtime / model call forensic

If AI/model generation failed, capture:

```text
attempt ID
model config
reasoning effort
start/end
timeout
response status
schema parse status
rate-limit/provider error class
retry count
retry budget
```

Differentiate:

```text
TRANSPORT_FAILURE
MODEL_TIMEOUT
MODEL_PROVIDER_5XX
RATE_LIMIT
INVALID_SCHEMA
EMPTY_RESPONSE
POLICY_REJECTION
LOCAL_PREPARE_FAILURE
OTHER
```

No secrets.

# 20. Batch-vs-subject isolation

If candidate generation is batched, determine whether one malformed subject invalidated the full batch.

Hard:
`ONE_KR_SUBJECT_CANDIDATE_ERROR_KILLED_BATCH = 0`

If nonzero, identify the exact subject and schema/data field.

# 21. Stage 5 — candidate validation

For each candidate:

```text
schema validation
fact-reference validation
numeric provenance
semantic provenance
decision polarity
technical fact safety
valuation basis safety
macro attribution
wording/self-transition validation
```

Capture all validation errors with exact field path.

# 22. Numeric provenance investigation

For every numeric validation error capture:

```text
raw matched span
normalized token
parsed value
field path
semantic type
canonical candidate binding
final candidate text
```

Hard:
`KR_PHANTOM_NUMERIC_VALIDATION_ERROR = 0 / NONZERO`

# 23. Valuation semantic validation

Distinguish:

```text
PER
PBR
fPER
fPBR
historical multiple/current multiple
percentile
modeled vs consensus vs provider-only
```

For every valuation rejection record:

```text
ticker
rendered claim
canonical fact
semantic mismatch
basis mismatch
```

Do not weaken valuation provenance.

# 24. Stage 6 — adjudication

For each subject:

```text
prior accepted decision
fresh candidate decision
material disagreement?
adjudication required?
adjudication invoked?
adjudication completed?
result?
```

Set:

```text
KR_ADJUDICATION_REQUIRED_COUNT = ...
KR_ADJUDICATION_COMPLETED_COUNT = ...
```

Hard:
`KR_REQUIRED_ADJUDICATION_MISSING = 0`

# 25. Stage 7 — accepted decision plan

For each subject:

```text
accepted plan created?
accepted decision
accepted source
accepted confidence
accepted timing
accepted evidence fingerprint
accepted change conditions
```

Set:

```text
KR_ACCEPTED_READY_COUNT = ...
KR_NOT_READY_COUNT = ...
```

Hard:
`KR_RAW_CANDIDATE_USED_AS_FINAL = 0`

# 26. Decision distribution

Record actual fresh packet-bound:

```text
BUY
HOLD
SELL
NOT_READY
```

Do not force previous distribution.

# 27. Stage 8 — accepted-block renderer

For every subject identify renderer route:

```text
V2_ACCEPTED_RENDERER
DETERMINISTIC_FALLBACK
LEGACY_V1
AI_ASSIST_PILOT
OTHER
```

Capture:

```text
selector state
accepted_decision_plan present?
decision block selected?
suppression reason?
```

Set:

```text
KR_RENDERER_ROUTE_IDENTIFIED_COUNT = ...
KR_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...
KR_FALLBACK_STOCK_COUNT = ...
```

# 28. Explicit v2 requirement

Every accepted-ready subject must visibly include top-level BUY/HOLD/SELL.
`투자 논리: 유지` does not count.

Hard:
`ACCEPTED_READY_WITHOUT_EXPLICIT_DECISION = 0 / NONZERO`

# 29. Stage 9 — final validator

Trace final rendered candidate through:

```text
message schema
numeric registry
numeric provenance
semantic valuation interpretation
technical safety
fact binding
duplicate/substantive-span checks
length/section checks
order-language checks
```

Set:
`KR_FINAL_VALIDATION_STATUS = PASS / PARTIAL / REJECTED`

# 30. Correction/repair loop audit

If correction exists, capture:

```text
initial validation errors
correction prompt/context
allowed actions
repaired candidate
second validation
repair count
terminal state
```

Determine whether it:
- converged
- looped
- introduced a new error
- exhausted retry budget

Hard:
`KR_VALIDATION_REPAIR_LOOP_UNBOUNDED = 0`

# 31. Stage 10 — market message renderer

Audit market message separately.

Verify:
- market data correct
- session correct
- market prose quality
- macro temporal safety
- night-futures/reference omission reason if absent

Set:
`KR_MARKET_MESSAGE_STATUS = PASS / PARTIAL_SAFE / FAIL`

# 32. Stage 11 — deterministic fallback

If fallback occurred, prove why it became terminal.

For each stock:

```text
fallback eligible reason
AI/V2 terminal failure reason
fallback payload generated?
fallback payload safe?
```

Set:
`KR_DETERMINISTIC_FALLBACK_COUNT = ...`

# 33. Stage 12 — delivery

Capture:

```text
expected message count
intent count
sent count
recorded/acknowledged count
duplicate count
orphan count
unowned retry
chunking
send attempts
```

Hard:
`KR_EXACTLY_ONCE_DELIVERY = PASS / FAIL`

# 34. Exact payload

Compare:

```text
renderer output
outbound payload
archive/ledger payload
received/recorded payload
```

for every message.

Set:
`KR_LIVE_EXACT_PAYLOAD = PASS / FAIL`

No recipient IDs.

# 35. User-visible symptom capture

Archive exact user-visible production messages from records.
If the user later provides copied Telegram text, compare it.
The user must not be required to provide internal logs.

# 36. Mandatory 047810 deep trace

Trace 047810 end-to-end:

```text
source
technical
evidence
candidate
validation
adjudication
accepted
renderer
delivery
```

Set:

```text
047810_LIVE_STATUS =
PASS /
LEGITIMATE_NEEDS_REVIEW /
DATA_FAILURE /
DECISION_PIPELINE_FAILURE /
VALIDATOR_FAILURE /
FALLBACK /
OTHER
```

# 37. Mandatory controls

Inspect specifically:

```text
000660
005930
010120
012450
047810
```

For 010120/012450, pay special attention to:
- large backlog/order numerics
- margin percentages
- valuation basis
- numeric provenance

# 38. KR per-stock forensic table

Produce exactly one table for all 8:

```text
ticker
source_ready
technical_state
context_ready
candidate
candidate_validation
adjudication
accepted
renderer
final_validation
delivery
earliest_failure
```

Mandatory.

# 39. Market forensic row

Separate market row:

```text
session
data_ready
macro_safe
renderer
validation
delivery
earliest_failure
```

# 40. Earliest-failure taxonomy

Choose exactly one earliest category per subject:

```text
NONE
SOURCE_DATA_NOT_READY
SOURCE_DATA_VALIDATION_FAILED
SESSION_FRESHNESS_MISMATCH
PACKET_COHORT_EXCLUDED
TECHNICAL_CONTEXT_INVALID
TECHNICAL_CONTEXT_UNAVAILABLE
EVIDENCE_PACKET_INVALID
PREPARE_CONTEXT_FAILED
MODEL_TRANSPORT_FAILURE
MODEL_TIMEOUT
MODEL_RATE_LIMIT
CANDIDATE_SCHEMA_INVALID
CANDIDATE_NUMERIC_PROVENANCE_REJECTED
CANDIDATE_SEMANTIC_PROVENANCE_REJECTED
ADJUDICATION_INCOMPLETE
ACCEPTED_PLAN_NOT_CREATED
SELECTOR_WRONG_ROUTE
RENDERER_REJECTED
FINAL_VALIDATOR_REJECTED
FALLBACK_SELECTED
DELIVERY_FAILED
OTHER
```

# 41. Systemic vs subject-specific

Set:

`KR_FAILURE_SCOPE = SYSTEMIC / SUBJECT_SPECIFIC / MIXED`

If systemic, identify shared component.
If mixed, separate primary systemic and subject-specific secondary issues.

# 42. Today-data trigger vs regression

Choose one primary class:

```text
LIVE_DATA_TRIGGER
CODE_REGRESSION
CONFIG_REGRESSION
SERVICE_RUNTIME_FAILURE
PROVIDER_RUNTIME_FAILURE
SCHEDULER_OWNERSHIP_FAILURE
MULTI_FACTOR
OTHER
```

Evidence-backed only.

# 43. Compare against prior passing KR regression

Prior repair reported:

```text
KR 8/8 PASS
US 14 + KR 8 = 22/22 exact test sink
```

Answer:

```text
What changed between that passing test path and today's production path?
```

Compare:
- code SHA
- runtime config
- service namespace
- packet data
- provider data
- feature fingerprints
- model/runtime conditions
- validator input
- scheduler execution mode

Mandatory:

`PASSING_TEST_VS_LIVE_FIRST_DIVERGENCE = ...`

# 44. Production-vs-test environment parity

Audit differences in:

```text
cwd
env vars
process namespace
service access
file/cache paths
model auth/runtime
feature flags
scheduler user
Python environment
network restrictions
```

Hard:

`UNEXPLAINED_TEST_LIVE_ENVIRONMENT_DIVERGENCE = 0 / NONZERO`

# 45. Data fingerprint comparison

For each subject compare:
- test/replay evidence fingerprint
- today natural evidence fingerprint
- today candidate input fingerprint

If failure is data-triggered, identify exact new/changed fact.

# 46. No retrospective mutation

Use immutable production artifacts or read-only copied replay fixtures.
Do not alter today's packet.

# 47. Optional diagnostic replay

After root-cause localization, isolated replay COPY is allowed only to confirm causality.

Rules:

```text
no production recipient
no delivery intent
no archive rewrite
no official assessment mutation
no accepted-state mutation
```

Inject/remove only the suspected trigger in the copy.

Hard:
`DIAGNOSTIC_REPLAY_PRODUCTION_MUTATION = 0`

# 48. Root-cause proof standard

Accept root cause only with:

```text
observed live failure
exact first failing stage
exact input/state
reproduction in isolated copy if feasible
negative control where trigger absent
```

# 49. Severity

P0:
- wrong recipient
- secret exposure
- duplicate send
- raw candidate visible as final
- cross-ticker identity corruption

Material P1:
- most/all KR v2 candidates fail
- accepted decisions systematically not rendered
- validator false-positive blocks live
- test passes but production namespace/config breaks
- one subject kills full batch
- avoidable systemic fallback

P2:
- isolated wording/formatting

# 50. Final classification

Set:
`KR_V2_NATURAL_LIVE = PASS / PARTIAL_SAFE / FAIL`

Do not force the outcome before evidence.

# 51. Next-action classification

Choose one after proof only:

```text
NO_ACTION
BOUNDED_SOURCE_DATA_REPAIR
BOUNDED_PROVIDER_REPAIR
BOUNDED_TECHNICAL_CONTEXT_REPAIR
BOUNDED_DECISION_PIPELINE_REPAIR
BOUNDED_MODEL_RUNTIME_REPAIR
BOUNDED_VALIDATOR_REPAIR
BOUNDED_ADJUDICATION_REPAIR
BOUNDED_RENDERER_ROUTE_REPAIR
BOUNDED_SCHEDULER_OWNERSHIP_REPAIR
TEST_LIVE_ENVIRONMENT_PARITY_REPAIR
ROLLBACK_REVIEW
```

Do not perform repair in this task.

# 52. Required reports

Create:

1. `docs/reports/20260901-kr-natural-live-run-identity.md`
2. `docs/reports/20260901-kr-runtime-lineage.md`
3. `docs/reports/20260901-kr-scheduler-ownership.md`
4. `docs/reports/20260901-kr-frozen-cohort.md`
5. `docs/reports/20260901-kr-source-monitor-data-readiness.md`
6. `docs/reports/20260901-kr-market-data-session-proof.md`
7. `docs/reports/20260901-kr-price-supply-proof.md`
8. `docs/reports/20260901-kr-technical-context-live-proof.md`
9. `docs/reports/20260901-kr-evidence-packet-audit.md`
10. `docs/reports/20260901-kr-today-vs-last-pass-data-delta.md`
11. `docs/reports/20260901-kr-v2-candidate-generation.md`
12. `docs/reports/20260901-kr-ai-runtime-model-forensics.md`
13. `docs/reports/20260901-kr-candidate-validation.md`
14. `docs/reports/20260901-kr-adjudication-accepted.md`
15. `docs/reports/20260901-kr-renderer-route.md`
16. `docs/reports/20260901-kr-final-validator.md`
17. `docs/reports/20260901-kr-market-message-proof.md`
18. `docs/reports/20260901-kr-fallback-proof.md`
19. `docs/reports/20260901-kr-live-delivery-exactly-once.md`
20. `docs/reports/20260901-kr-live-exact-payload.md`
21. `docs/reports/20260901-kr-047810-deep-trace.md`
22. `docs/reports/20260901-kr-eight-stock-forensic-table.md`
23. `docs/reports/20260901-kr-test-vs-live-environment-parity.md`
24. `docs/reports/20260901-kr-failure-trigger-proof.md`
25. `docs/reports/20260901-kr-natural-live-root-cause.md`
26. `docs/reports/20260901-kr-natural-live-artifact-index.md`

Machine-readable:

```text
docs/reports/20260901-kr-live-stage-matrix.json
docs/reports/20260901-kr-data-delta.json
docs/reports/20260901-kr-failure-trigger.json
docs/reports/20260901-kr-natural-live-proof.json
```

# 53. Required gates

```text
MANUAL_KR_PRODUCTION_JOB_TRIGGER = 0 / NONZERO
MANUAL_KR_PRODUCTION_SEND = 0 / NONZERO
KR_PRODUCTION_STATE_MUTATION = 0 / NONZERO
KR_REPAIR_DURING_PROOF = 0 / NONZERO
KR_CANONICAL_SESSION_DATE = 2026-09-01 / OTHER
KR_RUNTIME_LINEAGE = PASS / DOC_ONLY_DESCENDANT_NOT_RUNTIME / FAIL
KR_ACTIVE_COUNT_AT_INVESTIGATION = ...
KR_CUTOFF_ELIGIBLE_STOCK_COUNT = ...
KR_EXPECTED_PRODUCTION_MESSAGE_COUNT = ...
MULTIPLE_KR_PRODUCERS_OWNED_SAME_PACKET = 0 / NONZERO
UNOWNED_KR_RETRY = 0 / NONZERO
KR_PACKET_UNIVERSE_MUTATED_AFTER_CUTOFF = 0 / NONZERO
047810_STATUS_MISINTERPRETED_AS_PACKET_FAILURE = 0 / NONZERO
KR_SOURCE_MONITOR_READY_COUNT = ...
KR_TECHNICAL_FULL_COUNT = ...
KR_TECHNICAL_PARTIAL_SAFE_COUNT = ...
KR_TECHNICAL_UNAVAILABLE_COUNT = ...
KR_TECHNICAL_INVALID_COUNT = ...
KR_V2_DECISION_STAGE_LOCAL_OHLCV_HTTP = 0 / NONZERO
ONE_KR_TECHNICAL_FAILURE_BLOCKED_PEERS = 0 / NONZERO
KR_FAILURE_TRIGGER_EXACTLY_LOCALIZED = PASS / NOT_DATA_TRIGGERED / FAIL
KR_CANDIDATE_GENERATED_COUNT = ...
ONE_KR_SUBJECT_CANDIDATE_ERROR_KILLED_BATCH = 0 / NONZERO
KR_PHANTOM_NUMERIC_VALIDATION_ERROR = 0 / NONZERO
KR_ADJUDICATION_REQUIRED_COUNT = ...
KR_ADJUDICATION_COMPLETED_COUNT = ...
KR_REQUIRED_ADJUDICATION_MISSING = 0 / NONZERO
KR_ACCEPTED_READY_COUNT = ...
KR_NOT_READY_COUNT = ...
KR_RAW_CANDIDATE_USED_AS_FINAL = 0 / NONZERO
KR_RENDERER_ROUTE_IDENTIFIED_COUNT = ...
KR_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...
KR_FALLBACK_STOCK_COUNT = ...
ACCEPTED_READY_WITHOUT_EXPLICIT_DECISION = 0 / NONZERO
KR_FINAL_VALIDATION_STATUS = PASS / PARTIAL / REJECTED
KR_VALIDATION_REPAIR_LOOP_UNBOUNDED = 0 / NONZERO
KR_MARKET_MESSAGE_STATUS = PASS / PARTIAL_SAFE / FAIL
KR_DETERMINISTIC_FALLBACK_COUNT = ...
KR_EXPECTED_MESSAGE_COUNT = ...
KR_SENT_MESSAGE_COUNT = ...
KR_RECEIVED_MESSAGE_COUNT = ...
KR_LIVE_EXACT_PAYLOAD = PASS / FAIL
KR_EXACTLY_ONCE_DELIVERY = PASS / FAIL
KR_DUPLICATE = 0 / NONZERO
KR_ORPHAN = 0 / NONZERO
KR_UNOWNED_RETRY = 0 / NONZERO
047810_LIVE_STATUS = PASS / LEGITIMATE_NEEDS_REVIEW / DATA_FAILURE / DECISION_PIPELINE_FAILURE / VALIDATOR_FAILURE / FALLBACK / OTHER
PASSING_TEST_VS_LIVE_FIRST_DIVERGENCE = ...
UNEXPLAINED_TEST_LIVE_ENVIRONMENT_DIVERGENCE = 0 / NONZERO
KR_PRIMARY_FAILURE_CLASS = LIVE_DATA_TRIGGER / CODE_REGRESSION / CONFIG_REGRESSION / SERVICE_RUNTIME_FAILURE / PROVIDER_RUNTIME_FAILURE / SCHEDULER_OWNERSHIP_FAILURE / MULTI_FACTOR / OTHER
KR_FAILURE_SCOPE = SYSTEMIC / SUBJECT_SPECIFIC / MIXED
KR_PRIMARY_EARLIEST_FAILURE_STAGE = NONE / SOURCE_DATA_NOT_READY / SOURCE_DATA_VALIDATION_FAILED / SESSION_FRESHNESS_MISMATCH / PACKET_COHORT_EXCLUDED / TECHNICAL_CONTEXT_INVALID / TECHNICAL_CONTEXT_UNAVAILABLE / EVIDENCE_PACKET_INVALID / PREPARE_CONTEXT_FAILED / MODEL_TRANSPORT_FAILURE / MODEL_TIMEOUT / MODEL_RATE_LIMIT / CANDIDATE_SCHEMA_INVALID / CANDIDATE_NUMERIC_PROVENANCE_REJECTED / CANDIDATE_SEMANTIC_PROVENANCE_REJECTED / ADJUDICATION_INCOMPLETE / ACCEPTED_PLAN_NOT_CREATED / SELECTOR_WRONG_ROUTE / RENDERER_REJECTED / FINAL_VALIDATOR_REJECTED / FALLBACK_SELECTED / DELIVERY_FAILED / OTHER
DIAGNOSTIC_REPLAY_PRODUCTION_MUTATION = 0 / NONZERO
OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...
KR_V2_NATURAL_LIVE = PASS / PARTIAL_SAFE / FAIL
NEXT_ACTION = NO_ACTION / BOUNDED_SOURCE_DATA_REPAIR / BOUNDED_PROVIDER_REPAIR / BOUNDED_TECHNICAL_CONTEXT_REPAIR / BOUNDED_DECISION_PIPELINE_REPAIR / BOUNDED_MODEL_RUNTIME_REPAIR / BOUNDED_VALIDATOR_REPAIR / BOUNDED_ADJUDICATION_REPAIR / BOUNDED_RENDERER_ROUTE_REPAIR / BOUNDED_SCHEDULER_OWNERSHIP_REPAIR / TEST_LIVE_ENVIRONMENT_PARITY_REPAIR / ROLLBACK_REVIEW
```

# 54. Completion response

Return:

```text
RUN_ID = ...
PACKET_ID = ...
KR_CANONICAL_SESSION_DATE = 2026-09-01

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
KR_RUNTIME_LINEAGE = ...

KR_ACTIVE_COUNT_AT_INVESTIGATION = ...
KR_CUTOFF_ELIGIBLE_STOCK_COUNT = ...
KR_EXPECTED_MESSAGE_COUNT = ...

KR_SOURCE_MONITOR_READY_COUNT = ...

KR_TECHNICAL =
000660 ...
003690 ...
005490 ...
005930 ...
010120 ...
012450 ...
047810 ...
086280 ...

KR_CANDIDATES =
000660 ...
003690 ...
005490 ...
005930 ...
010120 ...
012450 ...
047810 ...
086280 ...

KR_ACCEPTED =
000660 ...
003690 ...
005490 ...
005930 ...
010120 ...
012450 ...
047810 ...
086280 ...

KR_RENDERER_ROUTES =
000660 ...
003690 ...
005490 ...
005930 ...
010120 ...
012450 ...
047810 ...
086280 ...

047810_LIVE_STATUS = ...

KR_SOURCE_MONITOR_READY_COUNT = ...
KR_CANDIDATE_GENERATED_COUNT = ...
KR_ACCEPTED_READY_COUNT = ...
KR_EXPLICIT_DECISION_BLOCK_VISIBLE_COUNT = ...
KR_FALLBACK_STOCK_COUNT = ...

KR_FINAL_VALIDATION_STATUS = ...
KR_MARKET_MESSAGE_STATUS = ...

KR_SENT_MESSAGE_COUNT = ...
KR_RECEIVED_MESSAGE_COUNT = ...
KR_LIVE_EXACT_PAYLOAD = ...
KR_EXACTLY_ONCE_DELIVERY = ...
KR_DUPLICATE = 0
KR_ORPHAN = 0
KR_UNOWNED_RETRY = 0

PASSING_TEST_VS_LIVE_FIRST_DIVERGENCE = ...

KR_FAILURE_TRIGGER =
ticker/fact/field/value/rule/stage or NOT_DATA_TRIGGERED

KR_PRIMARY_FAILURE_CLASS = ...
KR_FAILURE_SCOPE = ...
KR_PRIMARY_EARLIEST_FAILURE_STAGE = ...

ROOT_CAUSE = ...
CONTRIBUTING_FACTORS = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

KR_V2_NATURAL_LIVE = ...
NEXT_ACTION = ...

ZIP = ...
ZIP_SHA256 = ...
```

# 55. Mandatory completion ZIP

Create:

`20260901-kr-natural-live-failure-deep-readonly-root-cause-investigation-bundle.zip`

Include:

```text
exact master instruction
all track instructions
run identity
scheduler ownership
runtime lineage
frozen cohort
source-monitor readiness
market/session data proof
price/supply proof
technical-context artifacts
evidence fingerprints
today-vs-last-pass data delta
candidate/model runtime traces
validation errors
adjudication/accepted audit
renderer routes
final validation
market message
fallback payloads
exact delivery ledger
047810 deep trace
8-stock forensic matrix
test-vs-live environment parity
failure-trigger proof
root-cause classification
machine-readable JSON
artifact index
```

Exclude:

```text
secrets
Telegram recipient IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

# 56. Final principle

The question is:

```text
What is the earliest stage where today's natural KR packet diverged from the previously passing path,
and what exact live data or runtime state triggered that divergence?
```

Trace:

```text
scheduler
→ source data
→ frozen cohort
→ technical context
→ evidence
→ candidate
→ candidate validation
→ adjudication
→ accepted plan
→ renderer
→ final validator
→ fallback
→ delivery
```

Stop at the FIRST failure.
Do not repair until that evidence is complete.
