# thesis-monitor — OHLCV Technical Context Root-Cause + Resilient V2 Pipeline Repair
## Restore the OHLCV path first; graceful degradation is only the final safety net
## Remove decision-time fragile local-network dependency by packet-owning validated technical context
## Isolate subject/service failures instead of killing an entire market cohort
## Repair the false-positive numeric-provenance `:2000` rejection without weakening provenance safety
## Test with fault injection, frozen US run-49 replay, KR regression, test sink, then main merge
## No manual production replay

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-01 KST`
- Workstream: `OHLCV_TECHNICAL_CONTEXT_RESILIENCE_AND_PROVENANCE_REPAIR`
- Task class: `MATERIAL_P1_ROOT_CAUSE + PIPELINE_REPAIR + RESILIENCE + VALIDATOR_REPAIR`
- Automated trading: `0`
- Order sizing: `0`
- Production Assist: preserve `OFF`
- Accepted-v2 decision ownership: preserve
- Price Structure algorithm changes: `0`
- Valuation algorithm changes: `0`
- Market delivery scheduler changes: `0`
- Manual production resend of run-49: `0`

Source proof bundle:

`20260901-us-v2-natural-live-readonly-verification-bundle.zip`

Latest user-reported report/main/operating after the read-only verification:

```text
f7c4331e7aa34eeb87e0627fb7e79ee27a1cbfa7
```

The verified natural run itself executed on runtime code:

```text
5b3e6e1a721b84db72c7b277bf53ff55880a1819
```

Work-instruction commit for the proof:

```text
e6c11cff168fa430d7ddc7095d8c407d80948553
```

At implementation start:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve actual operating checkout
resolve runtime/deployed code SHA
use f7c4331... or a safe linear descendant as branch base
record exact lineage
```

Do not confuse a report-only descendant with the runtime code that produced run-49.

---

# 1. Source-supported facts

The run-49 proof establishes the following facts.

## 1.1 Source monitor succeeded

```text
source monitor:
success
2026-09-01T08:05:34.939847+09:00
to
2026-09-01T08:06:48.494921+09:00

14 / 14 US/foreign subjects
```

## 1.2 Frozen cohort was correct

```text
US cutoff-eligible stock count = 14
CPNG = ACTIVE_READY before cutoff
packet universe mutation after cutoff = 0
```

## 1.3 Price Structure and valuation were available

```text
US_PRICE_STRUCTURE_CONTRACT = PASS
US_VALUATION_CONTRACT = PASS
```

Therefore the incident does NOT prove:

```text
"all 14 securities had no OHLCV data anywhere in the system"
```

## 1.4 V2 candidate preparation failed at a separate local OHLCV fetch

The source trace says:

```text
accepted_decision_v2_runtime.prepare_context
→ local OHLCV fetch
→ httpcore.ConnectError
→ candidate NOT_GENERATED
```

for the cohort.

## 1.5 The failure was systemic

```text
fresh candidate = 0 / 14
packet-bound accepted plan = 0 / 14
explicit BUY/HOLD/SELL = 0 / 14
```

## 1.6 Safe fallback worked

```text
1 US market + 14 stock = 15 / 15 delivered exactly once
duplicate = 0
orphan = 0
raw candidate visible = 0
```

## 1.7 There was a separate P1 in numeric provenance

Backup AI validation retained:

```text
market_review:numbers_without_provenance:market_context.text:2000
```

even though the proof concluded there was no literal `2000` in the repaired final market sentence.

---

# 2. Important Unknown

The proof identifies the failure boundary as a local OHLCV connection error.

It does NOT yet prove the lower-level reason.

Possible causes to investigate, not assume:

```text
local OHLCV service/process not running
wrong host/port
wrong environment variable
IPv4/IPv6 bind mismatch
startup-order race
service crash/restart
client connection-pool lifecycle bug
incorrect working-directory/config resolution
container/host namespace mismatch
health endpoint healthy but data endpoint unavailable
socket exhaustion
timeout/retry policy defect
```

Codex must reproduce and identify the actual root cause.

Hard:

```text
ROOT_CAUSE_ASSUMED_WITHOUT_REPRODUCTION = 0
```

---

# 3. Product principle

OHLCV/technicals are important.

The repair must prioritize:

```text
1. reliably obtaining the correct OHLCV
2. validating its session/timeframe/bar quality
3. computing and packet-owning technical features
4. allowing V2 to use the technical evidence normally
```

Graceful degradation is only the final fallback when safe OHLCV cannot be recovered in time.

Do NOT solve the incident merely by deleting OHLCV from V2 reasoning.

Hard:

```text
REPAIR_REMOVES_TECHNICAL_CONTEXT_FROM_V2 = 0
```

---

# 4. Architectural target

Current fragile shape:

```text
source acquisition
Price Structure path
        ...
V2 prepare_context
        ↓
new local HTTP OHLCV fetch
        ↓
shared connection failure
        ↓
cohort candidate generation dies
```

Target:

```text
market/stock acquisition stage
        ↓
canonical OHLCV acquisition
        ↓
bar validation
        ↓
D/W/M technical feature computation
        ↓
PACKET-OWNED TECHNICAL_CONTEXT artifact
        ↓
immutable packet
        ↓
V2 prepare_context consumes packet-owned artifact
        ↓
candidate → adjudication → accepted
```

A decision-stage network fetch must not be the only path to required technical context.

---

# 5. Work split

```text
Track A
Local OHLCV connection root cause + service/client lifecycle repair

Track B
Packet-owned technical context + freshness + reconnect/fallback + failure isolation

Track C
`:2000` numeric-provenance false-positive root cause and validator repair

Track D
Fault injection + run-49 replay + KR/US regression + test sink + main merge + natural-live guard
```

Recommended branches:

```text
codex/ohlcv-connection-root-cause
codex/packet-owned-technical-context
codex/provenance-numeric-lexer-repair
codex/v2-technical-resilience-regression
```

---

# 6. Track A — reproduce the exact local OHLCV connection failure

Use archived run-49 configuration/evidence.

Identify the exact client call used by:

```text
accepted_decision_v2_runtime.prepare_context
```

Record:

```text
module
function
client class
resolved base URL
host
port
path
timeout
connection pool settings
environment/config source
process/service expected to own the endpoint
```

Do not expose secrets.

---

# 7. Compare OHLCV paths

Map ALL current OHLCV/price consumers:

```text
source monitor
Price Structure
technical feature engine
accepted_decision_v2_runtime.prepare_context
fallback renderer
onboarding INITIAL_EVIDENCE
```

For each:

```text
data source
transport
host/process
session semantics
bar basis
cache
freshness
failure behavior
```

Answer:

```text
Why could Price Structure PASS while V2 local OHLCV fetch failed?
```

This must be evidence-backed.

Hard:

```text
OHLCV_PATH_TOPOLOGY_MAPPED = PASS
```

---

# 8. Root-cause categories

Determine the actual root cause from reproduction and logs.

Set one primary:

```text
SERVICE_NOT_RUNNING
SERVICE_CRASHED
STARTUP_ORDER_RACE
HOST_PORT_CONFIG_MISMATCH
BIND_ADDRESS_MISMATCH
PROCESS_NAMESPACE_MISMATCH
CLIENT_POOL_LIFECYCLE
TIMEOUT_RETRY_POLICY
RESOURCE_EXHAUSTION
DATA_ENDPOINT_FAILURE
OTHER
```

If multiple contributed:

record primary + contributing factors.

---

# 9. Service health contract

If a local OHLCV service remains part of acquisition architecture:

provide distinct health semantics:

```text
process alive
transport reachable
data endpoint functional
latest expected completed-bar session available
```

A `/health` 200 alone is not enough if actual bar retrieval fails.

Recommended machine state:

```text
OHLCV_SERVICE_HEALTH =
READY
DEGRADED
UNAVAILABLE
```

with reason.

---

# 10. Startup ordering

If startup-order race is possible:

ensure the producer/acquisition process does not assume the OHLCV service is ready merely because the scheduler fired.

Use bounded readiness wait:

```text
health
→ data-path probe
→ ready
```

within the configured acquisition window.

Do not block indefinitely.

Hard:

```text
UNBOUNDED_SERVICE_STARTUP_WAIT = 0
```

---

# 11. Connection client robustness

Use one repository-native client lifecycle.

Review/fix:

```text
connection pooling
keepalive
DNS/localhost resolution
IPv4/IPv6 behavior
timeouts
retry classification
client close/reopen behavior
service restart behavior
```

Do not retry non-retryable malformed-data errors as transport errors.

---

# 12. Bounded reconnect

For retryable transport errors such as:

```text
ConnectError
ConnectTimeout
ReadTimeout
temporary 5xx
connection reset
```

use bounded reconnect/backoff.

Required properties:

```text
finite attempts
jitter/backoff
fresh connection on retry where needed
total deadline budget
observable attempt count
```

Hard:

```text
UNBOUNDED_OHLCV_RECONNECT = 0
```

---

# 13. Reconnection after service restart

In non-production fault-injection tests:

```text
client healthy
→ service disappears/restarts
→ first call fails
→ service returns
→ bounded reconnect
→ data retrieval resumes
```

must PASS.

Gate:

```text
OHLCV_SERVICE_RESTART_RECOVERY = PASS
```

---

# 14. Track B — canonical packet-owned OHLCV artifact

Create or normalize a packet-owned artifact per subject.

Recommended structure:

```text
technical_context_id
ticker
market
session
as_of
source
source_version
bars:
  D
  W
  M
last_completed_bar:
  D
  W
  M
bar_counts:
  D
  W
  M
quality:
  D
  W
  M
features:
  ...
raw_bar_fingerprint
feature_fingerprint
freshness_state
failure_reason
```

Use repository-native schemas if equivalent.

---

# 15. Completed-bar semantics

Preserve existing no-lookahead rules.

For each timeframe identify the expected last completed bar.

Do not mark a weekly/monthly bar stale merely because its calendar close is naturally older than the daily bar.

Freshness must be timeframe-aware.

Hard:

```text
OHLCV_FRESHNESS_USES_NAIVE_WALLCLOCK_ONLY = 0
```

---

# 16. Data validation

Validate before feature computation:

```text
timestamp ordering
duplicate bars
OHLC consistency
nonnegative/valid volume where expected
expected session identity
split/adjustment basis consistency
currency/security identity
minimum bar count per feature
future bar absence
```

Malformed subject data fails closed for that subject's technical context.

Do not poison the entire cohort.

---

# 17. Feature families

Preserve current safe feature families:

```text
returns / drawdown
SMA / EMA
MACD / signal / histogram
RSI
ATR / realized volatility
Bollinger
ADX / DMI
ROC / Stochastic
OBV / CMF / MFI where supported
Donchian / breakout
validated divergence where safe
```

No algorithm retuning in this task.

---

# 18. Technical numerical parity

For identical validated bars, moving feature computation/ownership earlier in the pipeline must not materially change the numbers.

Compare old feature engine vs packet-owned engine.

For deterministic formulas:

```text
exact or documented floating-point tolerance parity
```

Hard:

```text
TECHNICAL_FEATURE_NUMERIC_PARITY = PASS
```

---

# 19. Packet ownership

Once technical context is validated for the packet:

```text
persist/freeze it with the packet
```

Decision generation must consume this immutable artifact.

Hard:

```text
V2_DECISION_STAGE_REQUIRES_FRESH_LOCAL_OHLCV_HTTP = 0
```

This does NOT mean the acquisition stage cannot use the OHLCV service.

It means the decision stage must not independently refetch the same critical data through a fragile network hop.

---

# 20. Single-acquisition / reuse principle

Prefer:

```text
acquire once
validate once
feature-compute once
freeze once
reuse by:
  Price Structure where semantically appropriate
  V2 technical reasoning
  renderer/validator evidence bindings
```

Do not force Price Structure and technical features to share concepts that have different completed/provisional semantics.

Shared bars are allowed; derived semantic products remain distinct.

---

# 21. Avoid duplicate competing OHLCV truths

There must not be:

```text
Price Structure bars = source A/session X
V2 technical bars = source B/session Y
```

without explicit comparability metadata.

For every packet expose:

```text
same canonical bar set
or
documented source/basis difference
```

Hard:

```text
UNEXPLAINED_OHLCV_SOURCE_DIVERGENCE = 0
```

---

# 22. Acquisition-time recovery hierarchy

For each subject:

```text
1. primary canonical OHLCV fetch
2. bounded reconnect/retry
3. if repository has an approved redundant/cached source:
   use only if session/basis/freshness validation PASS
4. otherwise technical_context = PARTIAL_SAFE / UNAVAILABLE
```

Do not silently substitute a different source with unknown adjustment basis.

---

# 23. Cached snapshot policy

A cached completed-bar snapshot may be used only when it is still valid for the expected completed bar of that timeframe.

Example concept:

```text
daily expected completed session = 2026-08-31
cache daily last completed = 2026-08-31
→ current-safe

cache daily last completed = 2026-08-28
→ stale for current daily signal
```

Weekly/monthly expectations must use their actual completed-bar calendar.

Hard:

```text
STALE_DAILY_CACHE_PRESENTED_AS_CURRENT = 0
```

---

# 24. Technical context states

Per subject:

```text
FULL
PARTIAL_SAFE
UNAVAILABLE
INVALID
```

Meaning:

## FULL
Required configured D/W/M features available and safe.

## PARTIAL_SAFE
Some timeframe/features unavailable, remaining facts safe.

## UNAVAILABLE
No safe technical context after bounded recovery.

## INVALID
Data exists but fails integrity/comparability validation.

---

# 25. Important: restore first, degrade second

Normal production target:

```text
FULL
```

The existence of graceful degradation must not hide service failures.

Track operational counts:

```text
FULL
PARTIAL_SAFE
UNAVAILABLE
INVALID
```

Systemic PARTIAL/UNAVAILABLE triggers an operational warning.

---

# 26. Candidate generation under technical failure

OHLCV/technicals are important but are not the sole owner of long-horizon BUY/HOLD/SELL.

If technical context is `PARTIAL_SAFE` or `UNAVAILABLE`:

V2 may continue only if sufficient safe non-technical evidence exists:

```text
fundamentals
earnings
expectations
valuation
macro transmission
company events
safe Price Structure already packet-owned where available
```

The decision plan must explicitly know technical context quality.

Hard:

```text
MISSING_TECHNICAL_CONTEXT_SILENTLY_TREATED_AS_NEUTRAL = 0
```

---

# 27. Timing semantics under missing technical context

Do not invent timing.

If the missing features materially prevent timing assessment:

```text
timing = INSUFFICIENT / UNKNOWN
```

or repository-native equivalent.

No fixed automatic mapping from missing technicals to HOLD.

Hard:

```text
TECHNICAL_UNAVAILABLE_HARD_MAPS_TO_HOLD = 0
```

---

# 28. Confidence semantics

Technical incompleteness may influence AI confidence if material.

Do not hard-code:

```text
UNAVAILABLE → LOW
```

The AI reasons over its importance.

But the limitation must be represented in the structured evidence.

---

# 29. Subject-level failure isolation

One malformed/unavailable ticker:

```text
technical context affected for that ticker
```

must not kill ready peers.

Hard:

```text
ONE_SUBJECT_OHLCV_FAILURE_BLOCKS_COHORT = 0
```

---

# 30. Systemic OHLCV outage

If the entire OHLCV service is unavailable after bounded recovery:

```text
all subjects may have technical_context = UNAVAILABLE
```

but candidate generation should still be attempted subject-by-subject using remaining safe evidence.

If a specific subject then lacks enough evidence for decision:

```text
that subject = NOT_READY
```

Do not automatically force cohort-wide deterministic fallback solely because the shared OHLCV transport is down.

Hard:

```text
SYSTEMIC_OHLCV_OUTAGE_AUTOMATICALLY_KILLS_ALL_CANDIDATES = 0
```

---

# 31. Technical evidence binding

Every numeric technical claim in the V2 decision packet must bind to:

```text
technical_context_id
feature key
timeframe
as_of/completed bar
value
```

No AI recomputation.

Hard:

```text
AI_CALCULATES_TECHNICAL_NUMERIC = 0
```

---

# 32. Price Structure remains semantically independent

Historical structural S/R and Bollinger layers retain current contracts.

Technical context may share validated bars but must not alter:

```text
major-SR reality gate
near/major selection
completed Bollinger semantics
provisional Bollinger semantics
stored monitoring price rules
```

Hard:

```text
PRICE_STRUCTURE_ALGORITHM_DIFF = 0
```

---

# 33. Observability

Add safe structured telemetry for each run:

```text
OHLCV acquisition start/end
service health
data-path health
request count
success count
retry count
connection error count
timeout count
cache use count
FULL/PARTIAL_SAFE/UNAVAILABLE/INVALID counts
candidate generation count
```

Per subject:

```text
ticker
technical_context status
source
last completed D/W/M bars
retry count
failure class
```

No secrets.

---

# 34. Alerting

Operational warning when:

```text
service unreachable
connection errors exceed threshold
systemic technical_context degradation
expected daily completed bar unavailable after acquisition window
feature computation failure rate elevated
```

Do not page on one safely isolated optional feature unless configured material.

---

# 35. Track C — reproduce `:2000` false positive exactly

Use the archived final AI prose candidate/validation artifact from run-49.

Reproduce:

```text
market_review:numbers_without_provenance:market_context.text:2000
```

Then prove whether literal `2000` exists in:

```text
raw AI candidate
normalized candidate
final repaired candidate
rendered market sentence
```

Do not merely add `2000` to an allowlist.

Hard:

```text
PROVENANCE_2000_ALLOWLIST_HACK = 0
```

---

# 36. Validator diagnostic span

For every unproven number error, diagnostics must record:

```text
raw matched text
normalized token
parsed numeric value
character span
field path
matching/normalization rule
candidate fact binding attempt
```

No hidden chain-of-thought.

This makes synthesized phantom numbers observable.

---

# 37. Validate the actual final visible candidate

The provenance validator must validate the exact structured/render candidate state that will be sent.

Do not validate an earlier intermediate text and later report the error against a different final sentence.

Hard:

```text
PROVENANCE_VALIDATES_DIFFERENT_TEXT_THAN_RENDERER = 0
```

---

# 38. Numeric lexer/normalizer safety

Investigate whether tokens such as:

```text
S&P500
10년물
percentages
dates
ranges
ticker/product labels
```

can synthesize phantom numeric values during normalization.

Fix the root tokenizer/parser rule.

Do not weaken valid number detection.

---

# 39. Provenance positive controls

These MUST continue to fail:

```text
unsupported literal 2000
unsupported $2000
unsupported 2,000
unsupported 2000%
```

where no canonical fact binding exists.

Gate:

```text
REAL_UNSUPPORTED_2000_REJECTED = PASS
```

---

# 40. Provenance negative controls

These MUST NOT generate phantom `2000`:

```text
sentence with no literal 2000
S&P500
미국 10년물 실질금리
SPY -0.30%
SOXX +0.48%
```

when their actual visible numerics are safely bound or semantically non-numeric labels as defined by the contract.

Gate:

```text
PHANTOM_2000_FALSE_POSITIVE = 0
```

---

# 41. Do not bypass market provenance

The repair must not broadly exempt:

```text
market_context.text
```

from numeric provenance.

Hard:

```text
MARKET_CONTEXT_PROVENANCE_DISABLED = 0
```

---

# 42. Track D — archived run-49 frozen replay

Use:

```text
packet_id = 2026-09-01-us-run-49-2d1bb6df1608
```

as the incident replay.

Do not mutate historical packet/delivery records.

Build a replay fixture/copy.

Required questions:

```text
Does the repaired pipeline generate packet-bound technical contexts?
Do 14 subjects reach candidate generation?
Does provenance no longer reject phantom 2000?
Do accepted plans reach renderer?
Do explicit decision blocks render?
```

Fresh decision labels do NOT need to match historical prior controls unless evidence/policy is frozen identically.

---

# 43. Replay with healthy OHLCV path

With validated run-49 bars/approved replay fixture:

require:

```text
US_TECHNICAL_CONTEXT_FULL_COUNT = 14
US_CANDIDATE_GENERATED_COUNT = 14
```

unless a ticker-specific integrity issue is independently proven.

Then:

```text
accepted-ready / NOT_READY
```

must be determined by normal V2 logic.

---

# 44. Fault injection — connection refused

Simulate the exact class:

```text
httpcore.ConnectError
```

for the OHLCV transport.

Expected:

```text
bounded reconnect attempted
acquisition records failure
packet does not crash globally
technical context degrades safely after budget exhausted
candidate generation continues where other evidence is sufficient
```

Gate:

```text
CONNECT_ERROR_FAULT_INJECTION = PASS
```

---

# 45. Fault injection — timeout

Simulate:

```text
connect timeout
read timeout
```

Require bounded behavior.

Gate:

```text
OHLCV_TIMEOUT_FAULT_INJECTION = PASS
```

---

# 46. Fault injection — service restart

Simulate:

```text
service reachable
→ restart/unreachable
→ reconnect
→ service recovers
→ acquisition resumes
```

Gate:

```text
OHLCV_SERVICE_RESTART_RECOVERY = PASS
```

---

# 47. Fault injection — one malformed ticker

One subject returns:

```text
malformed OHLC
duplicate timestamps
future bar
wrong security identity
```

Expected:

```text
that subject technical context INVALID
other subjects FULL
cohort continues
```

Gate:

```text
MALFORMED_SINGLE_SUBJECT_ISOLATION = PASS
```

---

# 48. Fault injection — stale daily cache

Provide a cache one completed session behind.

Expected:

```text
not current-safe
no current daily technical claim
```

Gate:

```text
STALE_DAILY_CACHE_CONTROL = PASS
```

---

# 49. Fault injection — partial W/M

Provide valid daily but unavailable weekly/monthly.

Expected:

```text
PARTIAL_SAFE
daily features usable
missing W/M explicit
no fabricated W/M features
```

Gate:

```text
PARTIAL_TIMEFRAME_CONTROL = PASS
```

---

# 50. Cross-market regression

The OHLCV technical-context architecture is shared.

Run:

```text
KR current monitored cohort
US current monitored cohort
```

in non-production.

Verify:

```text
market session semantics
D/W/M features
candidate generation
accepted ownership
renderer
Price Structure isolation
```

Do not fix US by breaking KR.

---

# 51. CPNG and 047810 controls

Mandatory:

```text
CPNG
047810
```

because they exercised recent onboarding.

Verify their technical context is produced through the same generic path, with no ticker-specific exception.

Hard:

```text
NEW_SUBJECT_TECHNICAL_CONTEXT_SPECIAL_CASE = 0
```

---

# 52. Feature parity controls

Use representative:

```text
CORZ
GOOGL
MU
TSLA
CPNG
000660
047810
```

Compare D/W/M feature values against the existing deterministic feature implementation on identical bar fixtures.

Required:

```text
MACD parity
RSI parity
Bollinger parity
ATR parity
trend/return parity
volume feature parity where applicable
```

Gate:

```text
TECHNICAL_FEATURE_NUMERIC_PARITY = PASS
```

---

# 53. Test sink

After all tests pass:

generate current/non-production US production-equivalent messages for all current eligible US/foreign subjects.

Expected current reference:

```text
14 stock subjects
+
1 market message if included in test proof
```

Also run KR regression in test sink or validator path.

No production recipient.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 54. Explicit v2 message controls

At minimum inspect exact test messages:

```text
CORZ
CPNG
GOOGL
HUT
TSLA
WULF
MU
```

Each accepted-ready subject must have explicit:

```text
BUY / HOLD / SELL
```

not merely:

```text
투자 논리: 유지
```

---

# 55. Technical-context visibility

Do not overload user messages with infrastructure diagnostics.

Normal messages need not say:

```text
OHLCV service healthy
```

If technical context is materially unavailable, user-facing decision may briefly say:

```text
단기 기술 신호는 이번 점검에서 확인하지 못했습니다.
```

only when it affects interpretation.

Internal reports retain exact failure detail.

---

# 56. No decision retuning

This task must not retune:

```text
BUY/HOLD/SELL calibration
evidence maturity
pre-confirmation asymmetry logic
adjudication policy
```

Any decision difference caused solely by technical numerical drift is a failure.

Hard:

```text
DECISION_POLICY_RETUNED_IN_OHLCV_REPAIR = 0
```

---

# 57. Accepted decision ownership

Preserve:

```text
candidate
→ material disagreement
→ adjudication
→ accepted_decision_plan
```

Hard:

```text
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
```

---

# 58. Fallback remains available

Deterministic fallback remains the terminal safety mechanism for true pipeline failure.

Do not delete it.

But a retryable/local OHLCV transport problem alone should no longer automatically drive the entire cohort to fallback.

Hard:

```text
DETERMINISTIC_FALLBACK_REMOVED = 0
```

---

# 59. Main merge gate

Merge only if:

```text
ROOT CAUSE identified and reproduced
OHLCV path topology mapped
connection lifecycle repaired
service restart recovery PASS
packet-owned technical context PASS
feature numeric parity PASS
subject/system failure isolation PASS
run-49 replay PASS
phantom 2000 eliminated
real unsupported 2000 still rejected
KR regression PASS
US test-sink PASS
accepted ownership unchanged
Price Structure/valuation algorithms unchanged
P0 = 0
material P1 = 0
```

---

# 60. No manual production replay

After main merge:

do NOT replay run-49 or manually send corrected US messages.

Wait for the next normal eligible natural cycle.

Hard:

```text
RUN49_MANUAL_PRODUCTION_REPLAY = 0
```

---

# 61. Natural-live guard

After deployment, observe the next KR and US natural cycles read-only.

For the next US cycle specifically require:

```text
OHLCV service/acquisition state
technical_context FULL/PARTIAL counts
candidate generated count
accepted-ready count
explicit v2 decision block count
fallback count
exactly-once delivery
```

Do not declare final LIVE_PASS from test sink alone.

---

# 62. Operational target

Normal healthy run target:

```text
technical context FULL for all expected subjects
candidate generated for all expected subjects
```

Safe degradation target:

```text
one technical failure does not cascade
systemic OHLCV outage does not automatically erase all candidates
```

These are both required.

---

# 63. Required architecture docs

Create/update:

```text
docs/architecture/OHLCV_ACQUISITION_TOPOLOGY.md
docs/architecture/PACKET_OWNED_TECHNICAL_CONTEXT.md
docs/architecture/TECHNICAL_CONTEXT_FRESHNESS_AND_FAILURE_STATES.md
docs/architecture/OHLCV_CONNECTION_RETRY_AND_RECOVERY.md
docs/architecture/NUMERIC_PROVENANCE_VALIDATION.md
docs/architecture/DECISION_ENGINE_V2_PRODUCTION_RUNTIME.md
```

---

# 64. Required reports

Create at minimum:

1. `docs/reports/20260901-ohlcv-root-cause-reproduction.md`
2. `docs/reports/20260901-ohlcv-path-topology.md`
3. `docs/reports/20260901-ohlcv-service-client-lifecycle.md`
4. `docs/reports/20260901-ohlcv-reconnect-policy.md`
5. `docs/reports/20260901-packet-owned-technical-context-contract.md`
6. `docs/reports/20260901-technical-context-freshness.md`
7. `docs/reports/20260901-technical-feature-numeric-parity.md`
8. `docs/reports/20260901-technical-context-failure-isolation.md`
9. `docs/reports/20260901-run49-connecterror-replay.md`
10. `docs/reports/20260901-ohlcv-fault-injection.md`
11. `docs/reports/20260901-provenance-2000-root-cause.md`
12. `docs/reports/20260901-provenance-validator-controls.md`
13. `docs/reports/20260901-kr-us-technical-context-regression.md`
14. `docs/reports/20260901-current-us-v2-test-sink.md`
15. `docs/reports/20260901-current-v2-message-quality.md`
16. `docs/reports/20260901-ohlcv-v2-main-merge.md`
17. `docs/reports/20260901-ohlcv-v2-live-guard.md`
18. `docs/reports/20260901-ohlcv-v2-repair-readiness.md`
19. `docs/reports/20260901-ohlcv-v2-artifact-index.md`

Machine-readable:

```text
docs/reports/20260901-ohlcv-root-cause.json
docs/reports/20260901-technical-context-regression.json
docs/reports/20260901-provenance-validator-controls.json
docs/reports/20260901-ohlcv-v2-repair-readiness.json
```

---

# 65. Required gates

Set exactly:

```text
ROOT_CAUSE_ASSUMED_WITHOUT_REPRODUCTION =
0 / NONZERO

OHLCV_PATH_TOPOLOGY_MAPPED =
PASS / FAIL

OHLCV_PRIMARY_ROOT_CAUSE =
SERVICE_NOT_RUNNING /
SERVICE_CRASHED /
STARTUP_ORDER_RACE /
HOST_PORT_CONFIG_MISMATCH /
BIND_ADDRESS_MISMATCH /
PROCESS_NAMESPACE_MISMATCH /
CLIENT_POOL_LIFECYCLE /
TIMEOUT_RETRY_POLICY /
RESOURCE_EXHAUSTION /
DATA_ENDPOINT_FAILURE /
OTHER

OHLCV_CONTRIBUTING_FACTORS =
...

REPAIR_REMOVES_TECHNICAL_CONTEXT_FROM_V2 =
0 / NONZERO

UNBOUNDED_SERVICE_STARTUP_WAIT =
0 / NONZERO

UNBOUNDED_OHLCV_RECONNECT =
0 / NONZERO

OHLCV_SERVICE_RESTART_RECOVERY =
PASS / FAIL

OHLCV_FRESHNESS_USES_NAIVE_WALLCLOCK_ONLY =
0 / NONZERO

TECHNICAL_FEATURE_NUMERIC_PARITY =
PASS / FAIL

V2_DECISION_STAGE_REQUIRES_FRESH_LOCAL_OHLCV_HTTP =
0 / NONZERO

UNEXPLAINED_OHLCV_SOURCE_DIVERGENCE =
0 / NONZERO

STALE_DAILY_CACHE_PRESENTED_AS_CURRENT =
0 / NONZERO

TECHNICAL_CONTEXT_FULL_COUNT_US_REPLAY =
...

TECHNICAL_CONTEXT_PARTIAL_SAFE_COUNT_US_REPLAY =
...

TECHNICAL_CONTEXT_UNAVAILABLE_COUNT_US_REPLAY =
...

TECHNICAL_CONTEXT_INVALID_COUNT_US_REPLAY =
...

MISSING_TECHNICAL_CONTEXT_SILENTLY_TREATED_AS_NEUTRAL =
0 / NONZERO

TECHNICAL_UNAVAILABLE_HARD_MAPS_TO_HOLD =
0 / NONZERO

ONE_SUBJECT_OHLCV_FAILURE_BLOCKS_COHORT =
0 / NONZERO

SYSTEMIC_OHLCV_OUTAGE_AUTOMATICALLY_KILLS_ALL_CANDIDATES =
0 / NONZERO

AI_CALCULATES_TECHNICAL_NUMERIC =
0 / NONZERO

PRICE_STRUCTURE_ALGORITHM_DIFF =
0 / NONZERO

PROVENANCE_2000_ALLOWLIST_HACK =
0 / NONZERO

PROVENANCE_VALIDATES_DIFFERENT_TEXT_THAN_RENDERER =
0 / NONZERO

REAL_UNSUPPORTED_2000_REJECTED =
PASS / FAIL

PHANTOM_2000_FALSE_POSITIVE =
0 / NONZERO

MARKET_CONTEXT_PROVENANCE_DISABLED =
0 / NONZERO

CONNECT_ERROR_FAULT_INJECTION =
PASS / FAIL

OHLCV_TIMEOUT_FAULT_INJECTION =
PASS / FAIL

MALFORMED_SINGLE_SUBJECT_ISOLATION =
PASS / FAIL

STALE_DAILY_CACHE_CONTROL =
PASS / FAIL

PARTIAL_TIMEFRAME_CONTROL =
PASS / FAIL

NEW_SUBJECT_TECHNICAL_CONTEXT_SPECIAL_CASE =
0 / NONZERO

DECISION_POLICY_RETUNED_IN_OHLCV_REPAIR =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

DETERMINISTIC_FALLBACK_REMOVED =
0 / NONZERO

RUN49_REPLAY_COHORT_COUNT =
14 / OTHER

RUN49_REPLAY_CANDIDATE_GENERATED_COUNT =
14 / OTHER

RUN49_REPLAY_EXPLICIT_V2_DECISION_COUNT =
...

CURRENT_US_TEST_STOCK_COUNT =
...

CURRENT_US_TEST_EXACT_PAYLOAD =
PASS / FAIL

CURRENT_KR_REGRESSION =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

MARKET_DELIVERY_SCHEDULE_DIFF =
0 / NONZERO

RUN49_MANUAL_PRODUCTION_REPLAY =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OHLCV_V2_PIPELINE_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 66. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_IMPLEMENTATION = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

OHLCV_PRIMARY_ROOT_CAUSE = ...
OHLCV_CONTRIBUTING_FACTORS = ...

FAILED_OLD_PATH =
...

REPAIRED_PATH =
...

OHLCV_SERVICE_HEALTH_CONTRACT =
...

OHLCV_RECONNECT_POLICY =
...

OHLCV_SERVICE_RESTART_RECOVERY = ...

PACKET_OWNED_TECHNICAL_CONTEXT =
enabled / disabled

V2_DECISION_STAGE_REQUIRES_FRESH_LOCAL_OHLCV_HTTP = 0

TECHNICAL_FEATURE_NUMERIC_PARITY = ...

CONNECT_ERROR_FAULT_INJECTION = ...
OHLCV_TIMEOUT_FAULT_INJECTION = ...
MALFORMED_SINGLE_SUBJECT_ISOLATION = ...
STALE_DAILY_CACHE_CONTROL = ...
PARTIAL_TIMEFRAME_CONTROL = ...

RUN49_REPLAY_COHORT_COUNT = 14
RUN49_REPLAY_TECHNICAL_FULL = ...
RUN49_REPLAY_TECHNICAL_PARTIAL_SAFE = ...
RUN49_REPLAY_TECHNICAL_UNAVAILABLE = ...
RUN49_REPLAY_TECHNICAL_INVALID = ...
RUN49_REPLAY_CANDIDATE_GENERATED_COUNT = ...
RUN49_REPLAY_ACCEPTED_READY_COUNT = ...
RUN49_REPLAY_EXPLICIT_V2_DECISION_COUNT = ...

PROVENANCE_2000_ROOT_CAUSE = ...
PROVENANCE_2000_ALLOWLIST_HACK = 0
PHANTOM_2000_FALSE_POSITIVE = 0
REAL_UNSUPPORTED_2000_REJECTED = PASS
MARKET_CONTEXT_PROVENANCE_DISABLED = 0

CURRENT_US_TEST_STOCK_COUNT = ...
CURRENT_US_TEST_EXACT_PAYLOAD = ...
CURRENT_KR_REGRESSION = ...

CPNG_TECHNICAL_CONTEXT = ...
047810_TECHNICAL_CONTEXT = ...

ONE_SUBJECT_OHLCV_FAILURE_BLOCKS_COHORT = 0
SYSTEMIC_OHLCV_OUTAGE_AUTOMATICALLY_KILLS_ALL_CANDIDATES = 0

ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
DECISION_POLICY_RETUNED_IN_OHLCV_REPAIR = 0

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
MARKET_DELIVERY_SCHEDULE_DIFF = 0

TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
RUN49_MANUAL_PRODUCTION_REPLAY = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

OHLCV_V2_PIPELINE_REPAIR =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_LIVE /
BOUNDED_REPAIR /
ROLLBACK_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

# 67. Mandatory completion ZIP

Create:

`20260901-ohlcv-technical-context-root-cause-and-resilient-v2-pipeline-repair-bundle.zip`

Include:

```text
exact master instruction
all track instructions
root-cause reproduction
OHLCV topology map
service/client lifecycle evidence
reconnect/restart evidence
packet-owned technical-context contract
freshness/quality contract
technical numeric-parity evidence
run-49 frozen replay
all fault-injection results
`:2000` reproduction/root cause
provenance positive/negative controls
KR/US regression
US test-sink exact messages
message-quality review
main-merge evidence
live-guard state
readiness JSON
test/CI summary
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

---

# 68. Final principle

OHLCV is important enough that the system should make a serious effort to retrieve it reliably.

Therefore:

```text
restore the connection path
prove why it failed
make reconnect/restart robust
acquire and validate OHLCV before decision reasoning
freeze technical context into the packet
reuse that immutable context
```

But resilience also requires:

```text
a local transport failure must not erase an entire market's ability to reason
when safe fundamentals, earnings, expectations, valuation, and other evidence remain available.
```

The desired result is not "ignore OHLCV."

It is:

```text
OHLCV normally available and fully used,
OHLCV failures observable and recoverable,
and residual failures isolated instead of systemic.
```
