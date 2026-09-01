# thesis-monitor — CPNG/HUT Technical Recovery
## Completed-Bar Finality + Feature-Dependency-Scoped Validity + Approved Secondary OHLCV Recovery
## Keep fail-closed integrity, but recover every technical fact that can be proven safe

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-01 KST`
- Workstream: `CPNG_HUT_TECHNICAL_RECOVERY`
- Task class: `BOUNDED_OHLCV_RECOVERY + TECHNICAL_CONTEXT_V2 + DATA_FINALITY`
- Automated trading: `0`
- Order sizing: `0`
- Production Assist: preserve `OFF`
- Scheduler changes: `0`
- Manual production replay/send: `0`
- Accepted-v2 decision ownership: preserve
- Price Structure algorithm changes: `0`
- Valuation algorithm changes: `0`

Source bundle:

`20260901-malformed-ohlc-provider-integrity-root-cause-and-repair-bundle(2).zip`

Current user-reported safe main/operating:

```text
69d74fdf1600f812f0e542f0c3de5fcc544e5bc6
```

Current source-supported technical state:

```text
US:
FULL = 12
INVALID = 2
PARTIAL_SAFE = 0
UNAVAILABLE = 0

INVALID:
CPNG
HUT

MU = FULL
SKHY = FULL
```

Current test state:

```text
KR approved = 8 / 8 PASS
US test sink = 14
KR test sink = 8
TOTAL = 22 / 22 exact

production recipient send = 0
production delivery intent = 0
```

Resolve actual latest origin/main / operating / runtime SHA before work.

---

# 1. Source-supported CPNG case

CPNG current classification:

```text
STABLE_BAD_SOURCE
first bad stage = KIWOOM_RAW_RESPONSE
repair = RAW_PROVIDER_INVALID_RETAIN_INVALID
```

Exact bad date:

```text
2023-06-05
```

Daily specimen:

```text
open  = 16.35
high  = 15.80
low   = 15.43
close = 15.66

violation:
HIGH_LT_OPEN
```

Weekly specimen:

```text
open  = 16.35
high  = 16.20
low   = 15.43
close = 16.01

violation:
HIGH_LT_OPEN
```

The malformed provider row is historical and reproducibly bad.

Do not modify the raw specimen.

---

# 2. Source-supported HUT case

HUT current classification:

```text
INTERMITTENT_BAD_SOURCE
first bad stage = KIWOOM_RAW_RESPONSE
repair = RAW_PROVIDER_INVALID_RETAIN_INVALID
```

Exact bad date:

```text
2026-08-31
```

Daily/weekly specimen:

```text
open  = 79.43
high  = 79.99
low   = 75.71
close = 81.94

violation:
HIGH_LT_CLOSE
```

Prior forensics state:

```text
the dated row carries a mutable cur_prc above the row high
```

This strongly suggests a finality/session-field issue, but this task must prove the exact provider semantics before changing mapping.

Hard:

```text
HUT_MUTABLE_CUR_PRC_CAUSE_ASSUMED_WITHOUT_FIELD_PROOF = 0
```

---

# 3. Core objective

Do not choose between:

```text
"everything FULL"
or
"whole ticker INVALID"
```

when the evidence supports something more precise.

Target architecture:

```text
raw/provider integrity
        ↓
completed-bar finality
        ↓
timeframe integrity
        ↓
feature dependency coverage
        ↓
safe feature-level facts
        ↓
packet-owned technical context
        ↓
V2
```

The system should recover every technical fact whose exact inputs are safe, while preserving explicit invalidity for facts whose inputs are not safe.

---

# 4. Three repair pillars

## Pillar A — HUT completed-bar finality

Separate:

```text
live/current quote
```

from:

```text
completed regular-session OHLC candle
```

A mutable `cur_prc` must never be silently treated as the completed candle close unless the provider contract explicitly guarantees that meaning for that endpoint/session.

## Pillar B — CPNG feature-dependency-scoped validity

A malformed 2023 bar must not automatically erase a 2026 technical fact if the exact deterministic feature calculation does not depend on that bar.

But no feature may be declared safe based on an assumed lookback.

## Pillar C — approved secondary-source recovery

A known-bad primary row may be replaced only by a validated, approved, comparable secondary source under strict identity/session/basis rules.

No heuristic repair.

---

# 5. Contract evolution

Current `packet-owned-technical-context-v1` behavior effectively does:

```text
any invalid timeframe
→ overall INVALID
→ features = None
```

Create a backward-compatible v2 or equivalent contract that separates:

```text
source integrity
timeframe integrity
feature validity
aggregate usable coverage
```

Recommended internal fields:

```text
source_integrity_state
timeframe_quality
feature_quality
safe_feature_count
invalid_feature_count
invalid_source_rows
recovery_provenance
```

Do not remove raw integrity events.

---

# 6. Aggregate technical states

Preserve existing public/internal concepts:

```text
FULL
PARTIAL_SAFE
UNAVAILABLE
INVALID
```

but define aggregate semantics more precisely.

Suggested:

## FULL
All configured current technical facts are safe.

## PARTIAL_SAFE
At least one material technical fact/timeframe is safe and usable, while other components are stale, unavailable, or source-invalid.

## UNAVAILABLE
No safe data was acquired.

## INVALID
No safe technical facts can be used because a cross-cutting integrity/identity/comparability failure prevents reliable computation.

Important:

```text
a single historical invalid row does not automatically require aggregate INVALID
if safe feature-level facts can be proven independent of it.
```

Per-component invalidity must still be preserved.

Hard:

```text
INVALID_COMPONENT_HIDDEN_BY_PARTIAL_SAFE = 0
```

---

# 7. Track A — HUT provider field semantics

Inspect the actual Kiwoom adapter and raw response schema used for US OHLCV.

For the relevant endpoint/fields identify:

```text
open source field
high source field
low source field
close source field
cur_prc source field
regular close field if separate
extended-hours/current quote field if separate
session status/finality metadata if available
```

Create a field-semantics map.

Hard:

```text
HUT_PROVIDER_FIELD_SEMANTICS_MAPPED = PASS
```

---

# 8. Quote vs candle ownership

Create separate semantic owners:

```text
CURRENT_QUOTE
COMPLETED_BAR_CLOSE
```

The same raw field may own both only if provider documentation/runtime evidence proves it is safe.

Hard:

```text
CURRENT_QUOTE_SILENTLY_OWNS_COMPLETED_CLOSE = 0
```

---

# 9. Completed-bar finality state

For every candidate completed bar define:

```text
FINAL
PROVISIONAL
UNCONFIRMED
INVALID
```

A bar is `FINAL` only if:

```text
correct session identity
completed market session
provider field semantics compatible
OHLC enclosure valid
timestamp/finality safe
```

Date alone is not sufficient.

---

# 10. HUT post-close finality probe

For HUT reproduce the 2026-08-31 case with bounded non-production probes.

Capture over several bounded observations where allowed:

```text
row date
open/high/low
cur_prc/current quote
candidate completed close
provider finality/session metadata
payload fingerprint
```

Determine whether:

```text
A. cur_prc moves after the regular bar high/low are frozen
B. provider exposes a separate settled regular close
C. row becomes internally consistent after a later publication point
D. provider never exposes a safe final close on this endpoint
```

Choose one evidence-backed result.

---

# 11. HUT recovery priority

Use this order:

```text
1. provider-native settled regular close if explicitly available
2. later FINAL version of the same canonical provider row
3. approved secondary completed-bar source
4. otherwise current D/W technical components remain unsafe
```

Do not use:

```text
current quote as close
previous close as current close
high = max(high, cur_prc)
```

---

# 12. HUT safe partial behavior

If daily and/or weekly current bars remain invalid but monthly or other independent components are safe:

allow:

```text
aggregate = PARTIAL_SAFE
```

with:

```text
D = INVALID
W = INVALID
M = FULL
```

if and only if the monthly feature inputs are independently valid.

Do not set `features=None` for the whole ticker merely because D/W is invalid.

---

# 13. HUT automatic recovery

When a future acquisition produces a valid FINAL row:

```text
INVALID component
→ validated
→ features recomputed
→ FULL/PARTIAL_SAFE recalculated
```

without manual ticker repair.

Hard:

```text
HUT_TICKER_SPECIFIC_RECOVERY_PATCH = 0
```

---

# 14. Track B — feature dependency registry

Before changing CPNG behavior, map every technical fact emitted by the existing feature engine.

For every fact:

```text
feature key
timeframe
formula implementation
required input bars
dependency start/end
recursive/non-recursive
warmup/initialization semantics
minimum contiguous clean history
numeric tolerance if applicable
```

Examples include:

```text
returns
drawdown
SMA
EMA
MACD
RSI
ATR
Bollinger
ADX/DMI
ROC
Stochastic
OBV
CMF
MFI
Donchian
breakout
validated divergence
```

Do not assume textbook windows if implementation differs.

Hard:

```text
TECHNICAL_FEATURE_DEPENDENCY_REGISTRY = PASS
```

---

# 15. Recursive-indicator rule

For recursive features such as EMA-family/Wilder-family indicators:

do NOT assume:

```text
"26 bars means only 26 bars matter"
```

If the current implementation's exact output depends on earlier initialization/history, that history remains part of the dependency unless a finite warmup equivalence is mathematically and empirically proven.

Hard:

```text
RECURSIVE_INDICATOR_HISTORY_APPROXIMATED_AS_SAFE = 0
```

---

# 16. Contiguous clean suffix

For each timeframe identify:

```text
last invalid row
first clean row after it
contiguous clean suffix length
```

A feature may be computed from the clean suffix only if its exact existing implementation contract permits it.

Do not silently delete the malformed row from the middle of a dependency span.

Hard:

```text
INVALID_ROW_DROPPED_INSIDE_FEATURE_DEPENDENCY = 0
```

---

# 17. CPNG feature-level classification

For every current CPNG feature classify:

```text
SAFE_INDEPENDENT_OF_BAD_ROW
SAFE_AFTER_PROVEN_WARMUP
UNSAFE_DEPENDS_ON_BAD_ROW
UNAVAILABLE_OTHER_REASON
```

For safe features:

```text
compute normally
bind provenance
allow V2 use
```

For unsafe:

```text
do not compute/use
record exact bad dependency
```

---

# 18. CPNG timeframe behavior

Do not require an entire timeframe to be all-or-nothing if the feature registry proves narrower validity.

Recommended internal result example:

```text
D source history:
contains invalid 2023-06-05 row

D safe features:
SMA20 = safe
Bollinger20 = safe
finite recent returns = safe

D unsafe features:
any feature whose exact initialization/dependency reaches 2023-06-05
```

This is only an example.

The actual safe list must come from the implementation dependency audit.

---

# 19. CPNG monthly behavior

Prior replay showed:

```text
M: timeframe_unavailable
```

Re-evaluate why monthly became unavailable.

If valid monthly bars and enough bars exist, compute monthly independently.

If not enough input exists, keep unavailable.

Do not infer monthly validity from D/W.

---

# 20. Feature-fingerprint contract

Feature packet fingerprint must include:

```text
source row fingerprints actually used
dependency-window metadata
feature status
recovery source if any
```

Two feature facts with different recovered source rows must not share an indistinguishable fingerprint.

---

# 21. Feature-safe V2 evidence

Only safe feature-level facts enter V2.

V2 must be able to see:

```text
technical_context aggregate state
safe feature facts
missing/invalid feature cautions
```

Missing features are not neutral.

Hard:

```text
INVALID_FEATURE_NUMERIC_VISIBLE_TO_V2 = 0
```

---

# 22. Price Structure isolation

Price Structure remains a separate semantic evidence family.

Do not route repaired CPNG/HUT feature logic into Price Structure unless the existing Price Structure contract explicitly shares the canonical bars.

Hard:

```text
PRICE_STRUCTURE_ALGORITHM_DIFF = 0
PRICE_STRUCTURE_NUMERIC_DIFF = 0
```

---

# 23. Track C — approved secondary-source discovery

Inspect repository/runtime for already approved OHLCV alternatives.

For each possible secondary source capture:

```text
provider
coverage
US support
historical coverage
regular-session semantics
adjustment basis
currency
rate limits
cost/policy status
production approval status
```

Do not introduce a new paid/external provider without explicit operator authorization.

---

# 24. Secondary recovery eligibility

A secondary bar may replace a bad primary bar only if all pass:

```text
security identity exact
ticker/security mapping exact
session exact
regular/extended semantics compatible
currency exact
adjustment basis compatible
OHLC integrity PASS
timestamp safe
provider approved for production
```

Hard:

```text
UNAPPROVED_SECONDARY_SOURCE_USED = 0
```

---

# 25. Row-level recovery, not whole-series replacement

If CPNG has exactly one historical bad date:

prefer:

```text
primary series
+
approved secondary exact-date recovery row
```

over replacing the entire history.

Preserve:

```text
primary bad specimen
secondary recovery specimen
source provenance
comparability proof
```

Hard:

```text
WHOLE_SERIES_PROVIDER_SWAP_FOR_SINGLE_BAD_ROW = 0
```

unless a systemic primary defect is separately proven.

---

# 26. Cross-provider consistency

Before recovered row becomes canonical:

compare neighboring periods and corporate-action basis.

Reject if:

```text
material unexplained scale mismatch
split-adjustment mismatch
currency mismatch
session mismatch
security mismatch
```

Do not average providers.

Hard:

```text
CROSS_PROVIDER_PRICE_AVERAGING = 0
```

---

# 27. CPNG secondary-source outcome

Allowed:

```text
RECOVERED_FULL_OR_PARTIAL
NO_APPROVED_SECONDARY_SOURCE
SECONDARY_NOT_COMPARABLE
SECONDARY_ALSO_INVALID
```

If no safe secondary is available:

use feature-dependency-scoped validity.

Do not force recovery.

---

# 28. HUT secondary-source outcome

Secondary source is particularly useful if the primary endpoint never yields a safe settled regular close.

But use it only for the completed candle.

Current quote may remain primary/provider-native.

Keep quote and candle provenance separate.

---

# 29. Corporate-action guard

Before using a secondary CPNG historical row:

check the exact date for:

```text
split
reverse split
special distribution
ADR/security-basis change
other corporate action
```

No row substitution across incompatible adjustment bases.

---

# 30. Data-state separation

Introduce/retain separate internal states:

```text
provider_raw_integrity
bar_finality
timeframe_quality
feature_quality
technical_aggregate_state
```

Do not collapse all five into one boolean.

---

# 31. Observability

Per subject/timeframe report:

```text
raw invalid count
final/unconfirmed/provisional bar count
safe feature count
invalid feature count
feature dependency blocked count
secondary recovery count
secondary rejection count
```

For HUT:

```text
quote field
completed-close field
finality source
```

For CPNG:

```text
bad historical date
safe feature count
blocked feature count
```

---

# 32. Alert semantics

Operational warning when:

```text
current-session completed bar cannot be finalized
same provider repeatedly mixes quote/candle semantics
secondary recovery becomes frequent
safe-feature coverage materially falls
```

Historical isolated bad row with adequate safe current feature coverage may be lower severity.

---

# 33. Safety against silent improvement

Do not relabel CPNG/HUT to FULL merely because more features became usable.

`FULL` requires all configured required current technical facts to be safe.

If some remain blocked:

```text
PARTIAL_SAFE
```

is the correct outcome.

Hard:

```text
PARTIAL_COVERAGE_RELABELED_FULL = 0
```

---

# 34. Current V2 decision behavior

Re-run current CPNG/HUT in test namespace.

Decision changes are allowed only if newly recovered safe technical evidence actually changes reasoning.

Do not retune decision policy.

Hard:

```text
DECISION_POLICY_RETUNED_FOR_TECHNICAL_RECOVERY = 0
```

---

# 35. CPNG control

Required checks:

```text
raw 2023-06-05 bad specimen preserved
no high/low clipping
feature dependency classification complete
safe features visible only when independent
unsafe features absent
secondary recovery provenance if used
candidate generated
accepted decision
explicit v2 block
```

---

# 36. HUT control

Required checks:

```text
2026-08-31 mixed/mutable row reproduced
quote vs completed close semantics proven
bar finality gate tested
no cur_prc->close unsafe ownership
automatic future recovery tested
candidate generated
accepted decision
explicit v2 block
```

---

# 37. Unit tests — HUT finality

Mandatory fixtures:

## A. current quote > regular high, safe settled close exists

Expected:

```text
quote kept as quote
settled close owns candle
OHLC valid
technical may proceed
```

## B. current quote > regular high, no settled close

Expected:

```text
bar not FINAL
current timeframe not usable
no synthesized close
```

## C. later provider row becomes valid

Expected:

```text
automatic recovery
features recomputed
```

## D. date matches completed session but finality unknown

Expected:

```text
do not treat date alone as FINAL
```

---

# 38. Unit tests — CPNG dependency scope

Create a clean deterministic series and inject one old malformed bar.

Verify:

```text
feature outside exact dependency → safe
feature whose dependency includes bad row → blocked
recursive feature without proven finite warmup → blocked
```

Then move bad bar into recent dependency and ensure safe feature count falls appropriately.

---

# 39. Numeric parity

For every recovered safe feature compare against the existing feature engine on an equivalent fully clean canonical fixture.

Require:

```text
exact or documented deterministic floating-point tolerance
```

Hard:

```text
RECOVERED_FEATURE_NUMERIC_PARITY = PASS
```

---

# 40. Secondary-source controls

Mandatory:

## exact comparable row
→ PASS recovery

## security mismatch
→ reject

## date mismatch
→ reject

## adjustment mismatch
→ reject

## material unexplained scale mismatch
→ reject

## secondary malformed
→ reject

## provider not approved
→ reject

---

# 41. Run-49 replay

Use immutable copy of:

```text
2026-09-01-us-run-49-2d1bb6df1608
```

Report after repair:

```text
FULL
PARTIAL_SAFE
UNAVAILABLE
INVALID
```

Specifically show:

```text
CPNG
HUT
MU
SKHY
```

Do not force expected counts.

---

# 42. Current US regression

Current US/foreign 14 subjects:

require:

```text
14 decision contexts
14 candidates unless independently NOT_READY
accepted ownership intact
explicit v2 decisions for accepted-ready subjects
```

Technical coverage may be:

```text
FULL / PARTIAL_SAFE / INVALID
```

based on facts.

---

# 43. KR regression

All current KR 8 subjects must pass the same shared technical contract.

Mandatory:

```text
000660
047810
```

Hard:

```text
KR_TECHNICAL_RECOVERY_REGRESSION = PASS
```

---

# 44. Test sink

Use dedicated test sink:

```text
US = 14
KR = 8
TOTAL = 22
```

Expected reference:

```text
22 / 22 exact
```

unless monitored universe legitimately changes before execution; then record actual frozen counts.

No production recipient.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 45. Message quality

For CPNG/HUT accepted-ready messages:

if technical coverage remains partial/invalid and materially affects timing, render a short limitation.

Do not expose infrastructure detail.

Allowed concept:

```text
일부 기술지표 원천 데이터는 이번 점검에서 안전하게 사용하지 않았습니다.
```

Do not say provider names or raw error codes to normal users.

---

# 46. No decision-block regression

Accepted-ready subjects must still show:

```text
🧠 AI 분석 판단: BUY / HOLD / SELL
```

`투자 논리: 유지` is not a substitute.

Hard:

```text
EXPLICIT_V2_DECISION_BLOCK_REGRESSION = 0
```

---

# 47. No fallback regression

The technical recovery work must not reintroduce cohort-wide fallback for one ticker.

Hard:

```text
ONE_TECHNICAL_RECOVERY_FAILURE_BLOCKS_COHORT = 0
```

---

# 48. Main merge gate

Merge only if:

```text
HUT provider field semantics mapped
HUT finality gate PASS
CPNG dependency registry PASS
feature-scoped validity PASS
recursive-feature safety PASS
secondary-source policy PASS
no synthetic OHLC
no validator weakening
numeric parity PASS
run-49 replay PASS
current US regression PASS
KR 8 regression PASS
test sink PASS
accepted decision ownership unchanged
Price Structure/Valuation unchanged
P0 = 0
material P1 = 0
```

---

# 49. No production replay

Do not resend historical US messages.

Hard:

```text
HISTORICAL_US_PRODUCTION_REPLAY = 0
```

---

# 50. Natural-live guard

After main merge, wait for the next ordinary US natural cycle.

Read-only observe:

```text
CPNG technical aggregate
CPNG safe/blocked feature counts
HUT bar finality
HUT technical aggregate
US 14 candidate count
accepted-ready count
explicit v2 count
fallback count
exactly-once
```

Do not claim LIVE_PASS from tests alone.

---

# 51. Required architecture docs

Create/update:

```text
docs/architecture/OHLCV_COMPLETED_BAR_FINALITY.md
docs/architecture/OHLCV_QUOTE_VS_CANDLE_SEMANTICS.md
docs/architecture/TECHNICAL_FEATURE_DEPENDENCY_REGISTRY.md
docs/architecture/FEATURE_SCOPED_TECHNICAL_VALIDITY.md
docs/architecture/OHLCV_SECONDARY_SOURCE_RECOVERY.md
docs/architecture/PACKET_OWNED_TECHNICAL_CONTEXT.md
```

---

# 52. Required reports

Create at minimum:

1. `docs/reports/20260901-hut-provider-field-semantics.md`
2. `docs/reports/20260901-hut-completed-bar-finality.md`
3. `docs/reports/20260901-hut-automatic-recovery.md`
4. `docs/reports/20260901-cpng-feature-dependency-map.md`
5. `docs/reports/20260901-cpng-feature-scoped-validity.md`
6. `docs/reports/20260901-recursive-indicator-dependency-audit.md`
7. `docs/reports/20260901-secondary-ohlcv-source-audit.md`
8. `docs/reports/20260901-secondary-row-recovery-controls.md`
9. `docs/reports/20260901-cpng-hut-technical-context-v2.md`
10. `docs/reports/20260901-cpng-hut-run49-replay.md`
11. `docs/reports/20260901-current-us-technical-recovery-regression.md`
12. `docs/reports/20260901-kr-technical-recovery-regression.md`
13. `docs/reports/20260901-technical-recovery-test-sink.md`
14. `docs/reports/20260901-technical-recovery-message-quality.md`
15. `docs/reports/20260901-technical-recovery-main-merge.md`
16. `docs/reports/20260901-technical-recovery-live-guard.md`
17. `docs/reports/20260901-technical-recovery-artifact-index.md`

Machine-readable:

```text
docs/reports/20260901-hut-finality.json
docs/reports/20260901-cpng-feature-validity.json
docs/reports/20260901-secondary-recovery.json
docs/reports/20260901-technical-recovery-readiness.json
```

---

# 53. Required gates

Set exactly:

```text
HUT_MUTABLE_CUR_PRC_CAUSE_ASSUMED_WITHOUT_FIELD_PROOF =
0 / NONZERO

HUT_PROVIDER_FIELD_SEMANTICS_MAPPED =
PASS / FAIL

CURRENT_QUOTE_SILENTLY_OWNS_COMPLETED_CLOSE =
0 / NONZERO

HUT_COMPLETED_BAR_FINALITY =
PASS / FAIL

HUT_TICKER_SPECIFIC_RECOVERY_PATCH =
0 / NONZERO

TECHNICAL_FEATURE_DEPENDENCY_REGISTRY =
PASS / FAIL

RECURSIVE_INDICATOR_HISTORY_APPROXIMATED_AS_SAFE =
0 / NONZERO

INVALID_ROW_DROPPED_INSIDE_FEATURE_DEPENDENCY =
0 / NONZERO

CPNG_SAFE_FEATURE_COUNT =
...

CPNG_BLOCKED_FEATURE_COUNT =
...

CPNG_TECHNICAL_AGGREGATE =
FULL /
PARTIAL_SAFE /
UNAVAILABLE /
INVALID

HUT_SAFE_FEATURE_COUNT =
...

HUT_BLOCKED_FEATURE_COUNT =
...

HUT_TECHNICAL_AGGREGATE =
FULL /
PARTIAL_SAFE /
UNAVAILABLE /
INVALID

INVALID_COMPONENT_HIDDEN_BY_PARTIAL_SAFE =
0 / NONZERO

INVALID_FEATURE_NUMERIC_VISIBLE_TO_V2 =
0 / NONZERO

UNAPPROVED_SECONDARY_SOURCE_USED =
0 / NONZERO

WHOLE_SERIES_PROVIDER_SWAP_FOR_SINGLE_BAD_ROW =
0 / NONZERO

CROSS_PROVIDER_PRICE_AVERAGING =
0 / NONZERO

SECONDARY_SOURCE_STATUS =
APPROVED_AVAILABLE /
NO_APPROVED_SOURCE /
NOT_COMPARABLE

CPNG_SECONDARY_RECOVERY =
RECOVERED_FULL_OR_PARTIAL /
NO_APPROVED_SECONDARY_SOURCE /
SECONDARY_NOT_COMPARABLE /
SECONDARY_ALSO_INVALID /
NOT_NEEDED

HUT_SECONDARY_RECOVERY =
RECOVERED_FULL_OR_PARTIAL /
NO_APPROVED_SECONDARY_SOURCE /
SECONDARY_NOT_COMPARABLE /
SECONDARY_ALSO_INVALID /
NOT_NEEDED

PARTIAL_COVERAGE_RELABELED_FULL =
0 / NONZERO

RECOVERED_FEATURE_NUMERIC_PARITY =
PASS / FAIL

DECISION_POLICY_RETUNED_FOR_TECHNICAL_RECOVERY =
0 / NONZERO

RUN49_REPLAY_FULL_COUNT =
...

RUN49_REPLAY_PARTIAL_SAFE_COUNT =
...

RUN49_REPLAY_UNAVAILABLE_COUNT =
...

RUN49_REPLAY_INVALID_COUNT =
...

RUN49_CANDIDATE_GENERATED_COUNT =
14 / OTHER

CURRENT_US_DECISION_CONTEXT_COUNT =
14 / OTHER

CURRENT_US_CANDIDATE_GENERATED_COUNT =
...

KR_TECHNICAL_RECOVERY_REGRESSION =
PASS / FAIL

TEST_SINK_US_COUNT =
...

TEST_SINK_KR_COUNT =
...

TEST_SINK_TOTAL_EXACT =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

EXPLICIT_V2_DECISION_BLOCK_REGRESSION =
0 / NONZERO

ONE_TECHNICAL_RECOVERY_FAILURE_BLOCKS_COHORT =
0 / NONZERO

PRICE_STRUCTURE_ALGORITHM_DIFF =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

HISTORICAL_US_PRODUCTION_REPLAY =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

CPNG_HUT_TECHNICAL_RECOVERY =
READY_FOR_MAIN /
FAIL
```

---

# 54. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_IMPLEMENTATION = ...
TRACK_B_IMPLEMENTATION = ...
TRACK_C_IMPLEMENTATION = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...

HUT_PROVIDER_FIELD_SEMANTICS_MAPPED = ...
HUT_COMPLETED_BAR_FINALITY = ...
HUT_QUOTE_FIELD = ...
HUT_COMPLETED_CLOSE_FIELD = ...
HUT_FINALITY_SOURCE = ...

CPNG_BAD_DATE = 2023-06-05
CPNG_SAFE_FEATURE_COUNT = ...
CPNG_BLOCKED_FEATURE_COUNT = ...
CPNG_TECHNICAL_AGGREGATE = ...

HUT_SAFE_FEATURE_COUNT = ...
HUT_BLOCKED_FEATURE_COUNT = ...
HUT_TECHNICAL_AGGREGATE = ...

SECONDARY_SOURCE_STATUS = ...
CPNG_SECONDARY_RECOVERY = ...
HUT_SECONDARY_RECOVERY = ...

RECOVERED_FEATURE_NUMERIC_PARITY = ...

RUN49_REPLAY_FULL_COUNT = ...
RUN49_REPLAY_PARTIAL_SAFE_COUNT = ...
RUN49_REPLAY_UNAVAILABLE_COUNT = ...
RUN49_REPLAY_INVALID_COUNT = ...
RUN49_CANDIDATE_GENERATED_COUNT = ...

CURRENT_US_DECISION_CONTEXT_COUNT = ...
CURRENT_US_CANDIDATE_GENERATED_COUNT = ...

KR_TECHNICAL_RECOVERY_REGRESSION = ...

TEST_SINK_US_COUNT = ...
TEST_SINK_KR_COUNT = ...
TEST_SINK_TOTAL_EXACT = ...

INVALID_FEATURE_NUMERIC_VISIBLE_TO_V2 = 0
CURRENT_QUOTE_SILENTLY_OWNS_COMPLETED_CLOSE = 0
INVALID_ROW_DROPPED_INSIDE_FEATURE_DEPENDENCY = 0
UNAPPROVED_SECONDARY_SOURCE_USED = 0

DECISION_POLICY_RETUNED_FOR_TECHNICAL_RECOVERY = 0
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0

TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
HISTORICAL_US_PRODUCTION_REPLAY = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

CPNG_HUT_TECHNICAL_RECOVERY =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_LIVE /
BOUNDED_TECHNICAL_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 55. Mandatory completion ZIP

Create:

`20260901-cpng-hut-technical-recovery-finality-feature-scope-secondary-source-bundle.zip`

Include:

```text
exact master instruction
all track instructions
HUT provider field semantics
HUT finality probes
CPNG feature dependency registry
CPNG safe/blocked feature table
recursive indicator audit
secondary-source audit
secondary recovery controls
technical-context v2 schema
run-49 replay
current US regression
KR regression
test-sink exact messages
message-quality review
main-merge evidence
natural-live guard
machine-readable JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
provider auth values
Telegram recipient IDs
tokens
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 56. Final principle

Do not "fix bad prices."

Fix ownership and validity.

For HUT:

```text
quote ≠ completed candle close
until proven otherwise
```

For CPNG:

```text
one historical bad row ≠ every current technical fact invalid
```

but only when exact feature dependencies prove independence.

For both:

```text
secondary recovery is allowed only with approved, comparable evidence.
```

The desired end state is:

```text
maximum safe technical coverage
+
explicit residual limitations
+
zero fabricated OHLC
+
zero invalid technical numerics
+
no cohort-wide failure.
```
