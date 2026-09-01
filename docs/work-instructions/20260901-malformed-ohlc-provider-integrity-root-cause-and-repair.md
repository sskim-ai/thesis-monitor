# thesis-monitor — Malformed OHLC Provider Integrity Root-Cause + Repair
## Investigate CPNG / HUT / MU / SKHY invalid OHLC rows from the repaired run-49 technical-context path
## Restore FULL technical context only when raw/provider/normalization evidence supports it
## Never "repair" OHLC by inventing prices or clipping fields
## Preserve INVALID fail-closed semantics, subject isolation, packet-owned technical context, and accepted-v2 ownership

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-01 KST`
- Workstream: `MALFORMED_OHLC_PROVIDER_INTEGRITY_REPAIR`
- Task class: `DATA_INTEGRITY_ROOT_CAUSE + PROVIDER_NORMALIZATION_REPAIR + REGRESSION`
- Automated trading: `0`
- Order sizing: `0`
- Production Assist: preserve `OFF`
- Accepted-v2 decision ownership: preserve
- Price Structure algorithm changes: `0`
- Valuation algorithm changes: `0`
- Scheduler changes: `0`
- Manual production replay: `0`

Source bundle:

`20260901-ohlcv-technical-context-root-cause-and-resilient-v2-pipeline-repair-bundle.zip`

Latest source-supported implementation/main/operating from that bundle:

```text
FINAL_MAIN / OPERATING =
813beb6345fc2c6643018b33f568702b50fab37d
```

Source-supported run-49 technical-context result:

```text
FULL = 10
PARTIAL_SAFE = 0
UNAVAILABLE = 0
INVALID = 4
```

Known INVALID subjects:

```text
CPNG
HUT
MU
SKHY
```

Source-supported classification from the prior repair:

```text
CPNG = historical malformed OHLC row
HUT  = current malformed OHLC row
MU   = current malformed OHLC row
SKHY = current malformed OHLC row
```

The prior repair already established:

```text
OHLCV connection root cause = PROCESS_NAMESPACE_MISMATCH
V2 decision-stage local OHLCV HTTP dependency = removed
packet-owned technical context = enabled
candidate generation run-49 replay = 14/14
accepted-ready = 14/14
explicit v2 decision blocks = 14/14
cohort isolation = PASS
phantom :2000 provenance bug = repaired
P0/material P1 = 0/0
```

Do not reopen those closed issues unless a regression is proven.

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve operating/runtime SHA
use 813beb... or a safe linear descendant
record exact lineage
```

---

# 1. Core objective

For each of:

```text
CPNG
HUT
MU
SKHY
```

determine exactly:

```text
which bar was invalid
which timeframe it belongs to
what the raw provider payload contained
what normalization/transformation occurred
where the OHLC invariant first became false
whether the source row itself was malformed
whether the system mapped/adjusted/aggregated it incorrectly
whether a corporate action or split basis explains the apparent inconsistency
whether cache/state corruption was involved
```

Then:

```text
repair only the proven transformation/provider-selection defect
or
retain INVALID safely if the source itself cannot be trusted
```

The goal is not to force `FULL = 14`.

The goal is:

```text
maximum safely recoverable FULL coverage
+
zero fabricated OHLC
+
zero cross-ticker contamination
+
zero weakening of integrity gates
```

---

# 2. Hard OHLC invariants

For every bar:

```text
high >= open
high >= close
low <= open
low <= close
high >= low
```

If the provider supplies adjusted variants:

apply the invariant only after confirming all four fields are on the SAME adjustment basis.

Additional requirements:

```text
finite numeric values
positive price where required
valid timestamp/session
correct security identity
correct currency/security basis
no future completed bars
no duplicate timestamp with conflicting values
```

Hard:

```text
OHLC_INTEGRITY_VALIDATOR_WEAKENED = 0
```

---

# 3. Never synthesize a valid candle

Forbidden "repairs":

```text
high = max(open, high, close)
low = min(open, low, close)
swap high/low
copy previous close into malformed field
interpolate OHLC
replace a bad provider row with a peer/ticker row
silently drop a bad current bar and call the series current
```

unless a repository-approved corporate-action reconstruction contract already exists and the exact transformation is provably reversible.

Hard:

```text
SYNTHETIC_OHLC_REPAIR = 0
```

---

# 4. Work split

```text
Track A
Raw/provider forensics for CPNG/HUT/MU/SKHY

Track B
Normalization / adjustment / mapping / aggregation repair

Track C
Corporate-action, cache, redundant-provider diagnostic controls

Track D
Run-49 replay + current regression + test sink + main merge + natural-live guard
```

Recommended branches:

```text
codex/ohlc-four-ticker-forensics
codex/ohlc-normalization-integrity
codex/ohlc-corporate-action-cache-diagnostics
codex/ohlc-integrity-regression
```

---

# 5. Track A — identify exact invalid bars

For each of the four subjects, produce a canonical table:

```text
ticker
timeframe
bar timestamp/session
open
high
low
close
volume
raw source
raw payload fingerprint
normalized payload fingerprint
invariant violated
current vs historical
first bad stage
```

Examples of violation labels:

```text
HIGH_LT_OPEN
HIGH_LT_CLOSE
LOW_GT_OPEN
LOW_GT_CLOSE
LOW_GT_HIGH
NONFINITE_VALUE
DUPLICATE_CONFLICT
IDENTITY_MISMATCH
ADJUSTMENT_BASIS_MISMATCH
SESSION_TIMESTAMP_INVALID
OTHER
```

Hard:

```text
FOUR_TICKER_INVALID_BAR_IDENTIFIED = PASS
```

---

# 6. Preserve raw evidence

For every malformed row, archive a sanitized raw provider specimen sufficient to reproduce the transformation.

Include:

```text
field names
raw values
timestamp
symbol/security identifier
provider endpoint/query mode
adjustment flags
interval
timezone/session flags
```

Exclude:

```text
tokens
cookies
auth headers
account IDs
```

Compute fingerprints.

Do not mutate historical provider evidence.

---

# 7. Stage-by-stage lineage

Trace each row through:

```text
provider raw response
→ provider adapter
→ field mapping
→ adjustment normalization
→ timezone/session normalization
→ resampling/aggregation if any
→ cache serialization/deserialization
→ packet-owned OHLCV artifact
→ technical-context validator
```

At each stage save the relevant row/fingerprint.

Required answer:

```text
first stage where valid → invalid
or
raw source already invalid
```

Hard:

```text
MALFORMED_ROW_FIRST_BAD_STAGE_KNOWN = PASS
```

---

# 8. CPNG historical malformed control

CPNG was classified as:

```text
historical malformed OHLC row
```

Determine:

```text
how far back
which timeframe/source series
whether the bad row is required by current feature lookback
whether it is a corporate-action date
whether it persists on fresh refetch
whether cache contains a different copy than provider
```

Do not simply remove the historical row to get FULL.

If it lies inside the feature lookback:

the series remains invalid unless safely repaired/replaced from an approved canonical source.

If outside all required lookbacks:

document why it no longer affects current technical context.

---

# 9. HUT / MU / SKHY current malformed controls

For each:

```text
identify exact current completed-bar date
prove whether raw provider row itself violates OHLC
compare immediate refetch
compare cache
compare packet copy
```

A current malformed row is more severe because current D/W/M signals may depend on it.

Do not fall back to previous session and call the timeframe current.

---

# 10. Reproducibility

Run at least:

```text
3 deterministic raw fetches
```

where provider/service policy permits.

Classify:

```text
STABLE_BAD_SOURCE
INTERMITTENT_BAD_SOURCE
NORMALIZATION_ONLY_DEFECT
CACHE_ONLY_DEFECT
TRANSIENT_PROVIDER_DEFECT
OTHER
```

Do not hammer external providers; use bounded calls and cached evidence where appropriate.

---

# 11. Track B — field mapping audit

Verify provider adapter mapping for:

```text
open
high
low
close
adjusted close
volume
timestamp
```

Check for:

```text
high/low field swap
close/adjusted_close substitution
open from unadjusted basis with high/low/close adjusted
locale/decimal parsing
string truncation
column index shift
API schema-version drift
```

Hard:

```text
OHLC_FIELD_MAPPING_CONTRACT = PASS
```

---

# 12. Adjustment-basis audit

This is mandatory.

For each source/provider, determine whether bars are:

```text
raw/unadjusted
split-adjusted
split+dividend adjusted
provider-specific adjusted
```

All O/H/L/C fields used in one candle must be on a compatible basis.

Do NOT combine:

```text
raw open/high/low
+
adjusted close
```

into an OHLC candle.

Hard:

```text
MIXED_ADJUSTMENT_BASIS_CANDLE = 0
```

---

# 13. Corporate actions

Check whether any malformed date aligns with:

```text
stock split
reverse split
ADR ratio change
spin-off
special distribution
ticker/security change
other material corporate action
```

If yes:

prove the correct canonical adjustment treatment.

Do not infer a split only because prices differ materially.

---

# 14. Split/reverse-split transformation

If the source requires system-side split normalization:

use one canonical factor consistently across:

```text
open
high
low
close
volume where contract requires inverse adjustment
```

and preserve raw source separately.

Hard:

```text
PARTIAL_FIELD_SPLIT_ADJUSTMENT = 0
```

---

# 15. Resampling / aggregation audit

If weekly/monthly bars are derived from daily:

verify:

```text
open = first valid daily open
high = max(valid daily high)
low = min(valid daily low)
close = last valid daily close
volume = sum where appropriate
```

Only aggregate validated constituent bars.

If one constituent day is INVALID:

weekly/monthly derived context must not silently become FULL.

Hard:

```text
AGGREGATION_IGNORES_INVALID_CONSTITUENT = 0
```

---

# 16. Provider-native W/M vs locally resampled W/M

Map which timeframe uses:

```text
provider-native bars
or
local resampling
```

Do not mix them without provenance.

If provider-native weekly/monthly is malformed but daily constituents are valid and local resampling is an approved canonical route:

it may be acceptable to derive W/M locally, but:

```text
document source change
prove formula
prove session coverage
prove numeric parity against valid control periods
```

No silent substitution.

---

# 17. Timezone/session audit

Verify:

```text
market timezone
session date
timestamp interpretation
DST
regular-session vs extended-session inclusion
```

A timestamp shift must not combine data from different sessions into one bar.

Hard:

```text
CROSS_SESSION_OHLC_AGGREGATION = 0
```

---

# 18. Partial/current bar contamination

Completed technical context must not include an in-progress bar as a completed bar.

Verify particularly for:

```text
weekly
monthly
```

Hard:

```text
IN_PROGRESS_BAR_AS_COMPLETED_TECHNICAL = 0
```

Provisional Bollinger remains a separate Price Structure concept and must not be confused with completed technical features.

---

# 19. Numeric type / serialization

Audit:

```text
float/decimal conversion
JSON serialization
DB storage
cache serialization
NaN/null coercion
rounding
scientific notation
```

Do not allow rounding to create apparent OHLC violations.

Keep integrity validation at sufficient raw precision.

---

# 20. Repair taxonomy

For each subject choose exactly one outcome:

```text
MAPPING_REPAIRED
ADJUSTMENT_REPAIRED
AGGREGATION_REPAIRED
CACHE_REPAIRED
PROVIDER_REFETCH_RECOVERED
APPROVED_REDUNDANT_SOURCE_RECOVERED
RAW_PROVIDER_INVALID_RETAIN_INVALID
HISTORICAL_BAD_ROW_OUTSIDE_REQUIRED_LOOKBACK
OTHER_SAFE_REPAIR
```

Do not report `REPAIRED` without identifying the category.

---

# 21. Track C — cache forensics

Compare:

```text
provider raw
latest cache
packet-owned bars
previous packet cache
```

for all four.

Determine if malformed rows were:

```text
inserted by provider
inserted by normalization
inserted by stale/corrupt cache
```

If cache corruption:

invalidate only the affected cache key/version.

Do not purge all price caches without necessity.

Hard:

```text
BROAD_CACHE_PURGE_WITHOUT_CAUSE = 0
```

---

# 22. Cache versioning

If adapter/normalization semantics change:

bump or fingerprint cache schema/version so incompatible old bars are not reused silently.

Hard:

```text
OLD_INCOMPATIBLE_OHLC_CACHE_REUSED = 0
```

---

# 23. Redundant provider as diagnostic

If the repository already has an approved secondary OHLCV source, use it as a diagnostic comparator.

Compare:

```text
same security
same session
same adjustment basis
same regular/extended-session semantics
```

A secondary source does NOT automatically override the primary.

---

# 24. Redundant provider as recovery

Only allow recovery from a secondary provider if an explicit repository contract is satisfied:

```text
security identity exact
session exact
currency exact
adjustment basis known
bar semantics comparable
source freshness safe
OHLC integrity PASS
```

Then record:

```text
primary failure
secondary source
recovery reason
provenance
```

Hard:

```text
UNVALIDATED_CROSS_PROVIDER_SUBSTITUTION = 0
```

---

# 25. Cross-provider tolerance

Do not require exact price equality across providers if valid adjustment/market-data conventions differ.

But unexplained material divergence must block substitution.

Record:

```text
difference
known explanation
comparability decision
```

---

# 26. Provider incident quarantine

If a provider returns a reproducibly malformed row:

quarantine that exact:

```text
provider
symbol/security
session
interval
adjustment mode
```

combination where architecture supports it.

Do not blacklist the entire provider unless systemic evidence supports it.

---

# 27. Retry policy for malformed content

Malformed content is NOT a normal transport retry.

Policy:

```text
one bounded refetch may test transience
if same malformed row repeats:
  classify content integrity failure
  do not infinite-retry
```

Hard:

```text
MALFORMED_CONTENT_INFINITE_RETRY = 0
```

---

# 28. Subject technical-state semantics

Preserve:

```text
FULL
PARTIAL_SAFE
UNAVAILABLE
INVALID
```

Do not relabel malformed content as `UNAVAILABLE`.

`INVALID` means data exists but cannot be trusted.

This distinction must remain visible internally.

---

# 29. No forced 14/14 FULL target

Do not implement workarounds merely to obtain:

```text
FULL = 14
```

Allowed final replay outcome:

```text
FULL < 14
```

if one or more raw providers remain genuinely invalid.

The gate is:

```text
all recoverable defects fixed
all unrecoverable defects correctly INVALID and isolated
```

---

# 30. Technical feature regeneration

For any safely repaired series:

recompute:

```text
D/W/M returns
SMA/EMA
MACD/signal/histogram
RSI
ATR/volatility
Bollinger
ADX/DMI
ROC/Stochastic
volume features
Donchian/breakout
validated divergence
```

using canonical deterministic formulas.

Do not reuse features computed from bad bars.

Hard:

```text
FEATURES_FROM_INVALID_BARS_REUSED = 0
```

---

# 31. Feature invalidation lineage

When bad bars are replaced/repaired safely:

record:

```text
old raw_bar_fingerprint
new raw_bar_fingerprint
old feature_fingerprint
new feature_fingerprint
repair reason
as_of
```

Preserve auditability.

---

# 32. Price Structure interaction

Price Structure previously passed while technical context had four invalid series.

Determine whether Price Structure used:

```text
different source
different bar window
different validation path
cached validated bars
```

for these names.

Document the exact reason.

Do not force Price Structure to consume repaired technical bars unless the architecture contract supports it.

Hard:

```text
PRICE_STRUCTURE_SOURCE_CHANGED_WITHOUT_EXPLICIT_REVIEW = 0
```

---

# 33. V2 decision interaction

After safe technical repair:

rerun V2 using the repaired packet-owned technical context.

Do not tune decisions.

Any decision change is allowed only because:

```text
previous technical context was INVALID
and
new valid technical evidence materially changes the reasoning
```

Record the delta.

Hard:

```text
DECISION_POLICY_RETUNED_FOR_OHLC_REPAIR = 0
```

---

# 34. INVALID technical context remains usable as limitation

If a subject remains INVALID:

V2 may continue using safe non-technical evidence under the existing repaired contract.

The accepted decision must not cite invalid technical numerics.

Hard:

```text
INVALID_TECHNICAL_NUMERIC_LEAKED_TO_DECISION = 0
```

---

# 35. Run-49 replay

Use archived copy of:

```text
2026-09-01-us-run-49-2d1bb6df1608
```

Do not mutate historical packet records.

Replay all 14 subjects through the repaired integrity path.

Report:

```text
FULL
PARTIAL_SAFE
UNAVAILABLE
INVALID
candidate generated
accepted-ready
explicit decision blocks
```

---

# 36. Mandatory four-ticker replay controls

For each:

```text
CPNG
HUT
MU
SKHY
```

show:

```text
old invalid bar
root cause
repair category
new technical context state
feature recomputation status
V2 decision visibility
```

No vague summary.

---

# 37. Ten previously FULL subjects regression

All ten previously FULL subjects must remain safe.

Hard:

```text
PREVIOUSLY_FULL_10_REGRESSION = PASS
```

No repair for four bad names may corrupt the good names.

---

# 38. Current US fresh non-production regression

After run-49 frozen replay, perform one current-safe non-production US capture.

For all current US/foreign monitored subjects:

```text
technical state
latest completed D/W/M bars
OHLC integrity
feature generation
candidate generation
accepted decision
renderer
```

No production delivery.

---

# 39. KR regression

Run representative/full current KR monitored cohort through the same shared integrity path.

Mandatory controls:

```text
000660
047810
```

Verify:

```text
KR bar/session semantics
technical features
packet ownership
candidate generation
Price Structure isolation
```

Hard:

```text
KR_OHLC_INTEGRITY_REGRESSION = PASS
```

---

# 40. Corporate-action test fixtures

Create deterministic fixtures for:

```text
normal split
reverse split
no split
ADR/share-ratio change if architecture supports it
```

Verify:

```text
all OHLC fields transform consistently
volume treatment follows contract
integrity remains valid
no mixed basis
```

Gate:

```text
CORPORATE_ACTION_OHLC_FIXTURES = PASS
```

---

# 41. Mapping-schema drift fixture

Simulate provider response schema/column changes.

The adapter must fail closed rather than map the wrong fields.

Gate:

```text
PROVIDER_SCHEMA_DRIFT_FAIL_CLOSED = PASS
```

---

# 42. Malformed-content fixture

Inject:

```text
high < close
low > open
low > high
duplicate timestamp conflicting row
future bar
```

Each must produce:

```text
INVALID
```

not corrected candles.

Gate:

```text
MALFORMED_OHLC_NEGATIVE_CONTROLS = PASS
```

---

# 43. Safe-refetch fixture

Simulate:

```text
first provider response malformed
second bounded refetch valid
```

Required:

```text
PROVIDER_REFETCH_RECOVERED
```

with both fingerprints retained.

Gate:

```text
TRANSIENT_MALFORMED_REFETCH_CONTROL = PASS
```

---

# 44. Stable-bad-provider fixture

Simulate same malformed row repeatedly.

Required:

```text
remain INVALID
no infinite retry
no synthetic repair
```

Gate:

```text
STABLE_BAD_PROVIDER_CONTROL = PASS
```

---

# 45. Secondary-source recovery fixture

If approved redundant source exists:

simulate primary malformed + secondary comparable valid.

Require all recovery comparability gates.

If no approved secondary source exists:

mark this control `NOT_APPLICABLE`, do not invent one.

---

# 46. Test sink

After all integrity tests pass, generate production-equivalent stock messages in test sink.

US current eligible subjects:

```text
all current US/foreign monitored subjects
```

KR regression:

```text
all current KR or repository-approved representative full cohort
```

No production recipient.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 47. Test message technical claims

For subjects now FULL:

technical/timing evidence may be rendered if selected.

For subjects still INVALID:

do not show invalid MACD/RSI/Bollinger/etc.

User-facing limitation may say:

```text
이번 점검에서는 일부 기술지표 원천 데이터의 무결성을 확인하지 못해 단기 기술 신호를 판단에 사용하지 않았습니다.
```

only if material to the message.

---

# 48. CPNG control

CPNG is both:

```text
recent onboarding control
+
historical malformed OHLC control
```

Verify no special-case code.

Hard:

```text
CPNG_OHLC_TICKER_SPECIFIC_BYPASS = 0
```

---

# 49. HUT/MU/SKHY controls

Verify all three use generic provider/integrity logic.

Hard:

```text
HUT_MU_SKHY_TICKER_SPECIFIC_BYPASS = 0
```

---

# 50. Observability

For every invalid/repaired row expose internally:

```text
provider
ticker
session
interval
adjustment mode
violation
first bad stage
retry/refetch result
cache state
recovery source if any
final technical-context state
```

No secrets.

---

# 51. Provider quality metrics

Add aggregate metrics:

```text
raw bars validated
invalid raw rows
normalization-induced invalid rows
cache-induced invalid rows
transient malformed recovered
stable malformed unresolved
per-provider invalid rate
```

Do not use tiny sample sizes to permanently downgrade a provider automatically.

---

# 52. Alerting

Operational warning if:

```text
current completed-bar malformed
same provider/session malformed for multiple tickers
invalid-rate spikes materially
normalization-induced invalid row occurs
```

Historical isolated bad row outside required lookback may be lower severity.

---

# 53. Existing fallback preserved

Do not remove:

```text
technical_context INVALID
→ safe non-technical V2 reasoning
```

This repair aims to reduce INVALID frequency, not eliminate the safety state.

---

# 54. Main merge gate

Merge only if:

```text
4/4 root causes individually classified
raw/provider evidence archived
first bad stage known
no synthetic OHLC repair
mapping/adjustment/aggregation/session contracts PASS
corporate-action fixtures PASS
schema-drift fail-closed PASS
negative malformed controls PASS
run-49 replay PASS
previous FULL10 regression PASS
KR regression PASS
test sink PASS
accepted-v2 ownership unchanged
Price Structure algorithm unchanged
valuation unchanged
P0 = 0
material P1 = 0
```

If one raw provider remains genuinely bad:

that ticker may remain INVALID without blocking main merge, provided:

```text
cause proven
isolation PASS
no invalid technical claims leak
```

---

# 55. No production replay

Do not resend historical run-49 or other prior messages.

Hard:

```text
HISTORICAL_US_PRODUCTION_REPLAY = 0
```

---

# 56. Natural-live guard

After deployment, observe next eligible KR and US natural cycles read-only.

For US report:

```text
FULL/PARTIAL/UNAVAILABLE/INVALID counts
four control tickers
candidate generated count
accepted-ready count
explicit v2 block count
fallback count
exactly-once
```

Do not declare LIVE_PASS from replay/test sink alone.

---

# 57. Required architecture docs

Create/update:

```text
docs/architecture/OHLCV_PROVIDER_INTEGRITY.md
docs/architecture/OHLCV_ADJUSTMENT_BASIS.md
docs/architecture/OHLCV_CORPORATE_ACTION_NORMALIZATION.md
docs/architecture/OHLCV_CACHE_VERSIONING.md
docs/architecture/PACKET_OWNED_TECHNICAL_CONTEXT.md
```

---

# 58. Required reports

Create at minimum:

1. `docs/reports/20260901-four-ticker-ohlc-root-cause.md`
2. `docs/reports/20260901-cpng-malformed-ohlc-forensics.md`
3. `docs/reports/20260901-hut-malformed-ohlc-forensics.md`
4. `docs/reports/20260901-mu-malformed-ohlc-forensics.md`
5. `docs/reports/20260901-skhy-malformed-ohlc-forensics.md`
6. `docs/reports/20260901-ohlc-provider-field-mapping.md`
7. `docs/reports/20260901-ohlc-adjustment-basis-audit.md`
8. `docs/reports/20260901-ohlc-corporate-action-audit.md`
9. `docs/reports/20260901-ohlc-resampling-session-audit.md`
10. `docs/reports/20260901-ohlc-cache-forensics.md`
11. `docs/reports/20260901-cross-provider-diagnostics.md`
12. `docs/reports/20260901-run49-four-ticker-repair-replay.md`
13. `docs/reports/20260901-previous-full10-regression.md`
14. `docs/reports/20260901-current-us-ohlc-integrity-regression.md`
15. `docs/reports/20260901-kr-ohlc-integrity-regression.md`
16. `docs/reports/20260901-ohlc-negative-positive-controls.md`
17. `docs/reports/20260901-current-ohlc-v2-test-sink.md`
18. `docs/reports/20260901-ohlc-integrity-main-merge.md`
19. `docs/reports/20260901-ohlc-integrity-live-guard.md`
20. `docs/reports/20260901-ohlc-integrity-artifact-index.md`

Machine-readable:

```text
docs/reports/20260901-four-ticker-ohlc-root-cause.json
docs/reports/20260901-run49-technical-context-after-integrity-repair.json
docs/reports/20260901-current-ohlc-integrity-regression.json
docs/reports/20260901-ohlc-integrity-readiness.json
```

---

# 59. Required gates

Set exactly:

```text
OHLC_INTEGRITY_VALIDATOR_WEAKENED =
0 / NONZERO

SYNTHETIC_OHLC_REPAIR =
0 / NONZERO

FOUR_TICKER_INVALID_BAR_IDENTIFIED =
PASS / FAIL

MALFORMED_ROW_FIRST_BAD_STAGE_KNOWN =
PASS / FAIL

CPNG_ROOT_CAUSE =
...

HUT_ROOT_CAUSE =
...

MU_ROOT_CAUSE =
...

SKHY_ROOT_CAUSE =
...

OHLC_FIELD_MAPPING_CONTRACT =
PASS / FAIL

MIXED_ADJUSTMENT_BASIS_CANDLE =
0 / NONZERO

PARTIAL_FIELD_SPLIT_ADJUSTMENT =
0 / NONZERO

AGGREGATION_IGNORES_INVALID_CONSTITUENT =
0 / NONZERO

CROSS_SESSION_OHLC_AGGREGATION =
0 / NONZERO

IN_PROGRESS_BAR_AS_COMPLETED_TECHNICAL =
0 / NONZERO

BROAD_CACHE_PURGE_WITHOUT_CAUSE =
0 / NONZERO

OLD_INCOMPATIBLE_OHLC_CACHE_REUSED =
0 / NONZERO

UNVALIDATED_CROSS_PROVIDER_SUBSTITUTION =
0 / NONZERO

MALFORMED_CONTENT_INFINITE_RETRY =
0 / NONZERO

FEATURES_FROM_INVALID_BARS_REUSED =
0 / NONZERO

PRICE_STRUCTURE_SOURCE_CHANGED_WITHOUT_EXPLICIT_REVIEW =
0 / NONZERO

DECISION_POLICY_RETUNED_FOR_OHLC_REPAIR =
0 / NONZERO

INVALID_TECHNICAL_NUMERIC_LEAKED_TO_DECISION =
0 / NONZERO

RUN49_REPLAY_FULL_COUNT =
...

RUN49_REPLAY_PARTIAL_SAFE_COUNT =
...

RUN49_REPLAY_UNAVAILABLE_COUNT =
...

RUN49_REPLAY_INVALID_COUNT =
...

RUN49_REPLAY_CANDIDATE_GENERATED_COUNT =
14 / OTHER

RUN49_REPLAY_ACCEPTED_READY_COUNT =
...

RUN49_REPLAY_EXPLICIT_V2_DECISION_COUNT =
...

PREVIOUSLY_FULL_10_REGRESSION =
PASS / FAIL

KR_OHLC_INTEGRITY_REGRESSION =
PASS / FAIL

CORPORATE_ACTION_OHLC_FIXTURES =
PASS / FAIL

PROVIDER_SCHEMA_DRIFT_FAIL_CLOSED =
PASS / FAIL

MALFORMED_OHLC_NEGATIVE_CONTROLS =
PASS / FAIL

TRANSIENT_MALFORMED_REFETCH_CONTROL =
PASS / FAIL

STABLE_BAD_PROVIDER_CONTROL =
PASS / FAIL

SECONDARY_SOURCE_RECOVERY_CONTROL =
PASS /
NOT_APPLICABLE /
FAIL

CPNG_OHLC_TICKER_SPECIFIC_BYPASS =
0 / NONZERO

HUT_MU_SKHY_TICKER_SPECIFIC_BYPASS =
0 / NONZERO

CURRENT_US_TECHNICAL_FULL_COUNT =
...

CURRENT_US_TECHNICAL_PARTIAL_SAFE_COUNT =
...

CURRENT_US_TECHNICAL_UNAVAILABLE_COUNT =
...

CURRENT_US_TECHNICAL_INVALID_COUNT =
...

CURRENT_US_TEST_EXACT_PAYLOAD =
PASS / FAIL

CURRENT_KR_TEST_EXACT_PAYLOAD =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

HISTORICAL_US_PRODUCTION_REPLAY =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OHLC_PROVIDER_INTEGRITY_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 60. Completion response

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

FOUR_TICKER_INVALID_BAR_IDENTIFIED = ...
MALFORMED_ROW_FIRST_BAD_STAGE_KNOWN = ...

CPNG =
invalid bar ...
root cause ...
first bad stage ...
repair category ...
final technical state ...

HUT =
invalid bar ...
root cause ...
first bad stage ...
repair category ...
final technical state ...

MU =
invalid bar ...
root cause ...
first bad stage ...
repair category ...
final technical state ...

SKHY =
invalid bar ...
root cause ...
first bad stage ...
repair category ...
final technical state ...

OHLC_FIELD_MAPPING_CONTRACT = ...
MIXED_ADJUSTMENT_BASIS_CANDLE = 0
PARTIAL_FIELD_SPLIT_ADJUSTMENT = 0
AGGREGATION_IGNORES_INVALID_CONSTITUENT = 0
CROSS_SESSION_OHLC_AGGREGATION = 0

RUN49_REPLAY_FULL_COUNT = ...
RUN49_REPLAY_PARTIAL_SAFE_COUNT = ...
RUN49_REPLAY_UNAVAILABLE_COUNT = ...
RUN49_REPLAY_INVALID_COUNT = ...
RUN49_REPLAY_CANDIDATE_GENERATED_COUNT = 14
RUN49_REPLAY_ACCEPTED_READY_COUNT = ...
RUN49_REPLAY_EXPLICIT_V2_DECISION_COUNT = ...

PREVIOUSLY_FULL_10_REGRESSION = ...
KR_OHLC_INTEGRITY_REGRESSION = ...

CORPORATE_ACTION_OHLC_FIXTURES = ...
PROVIDER_SCHEMA_DRIFT_FAIL_CLOSED = ...
MALFORMED_OHLC_NEGATIVE_CONTROLS = ...
TRANSIENT_MALFORMED_REFETCH_CONTROL = ...
STABLE_BAD_PROVIDER_CONTROL = ...
SECONDARY_SOURCE_RECOVERY_CONTROL = ...

CURRENT_US_TECHNICAL_FULL_COUNT = ...
CURRENT_US_TECHNICAL_PARTIAL_SAFE_COUNT = ...
CURRENT_US_TECHNICAL_UNAVAILABLE_COUNT = ...
CURRENT_US_TECHNICAL_INVALID_COUNT = ...

CURRENT_US_TEST_EXACT_PAYLOAD = ...
CURRENT_KR_TEST_EXACT_PAYLOAD = ...

CPNG_OHLC_TICKER_SPECIFIC_BYPASS = 0
HUT_MU_SKHY_TICKER_SPECIFIC_BYPASS = 0

SYNTHETIC_OHLC_REPAIR = 0
OHLC_INTEGRITY_VALIDATOR_WEAKENED = 0
FEATURES_FROM_INVALID_BARS_REUSED = 0
INVALID_TECHNICAL_NUMERIC_LEAKED_TO_DECISION = 0

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0

TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
HISTORICAL_US_PRODUCTION_REPLAY = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

OHLC_PROVIDER_INTEGRITY_REPAIR =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_LIVE /
BOUNDED_PROVIDER_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 61. Mandatory completion ZIP

Create:

`20260901-malformed-ohlc-provider-integrity-root-cause-and-repair-bundle.zip`

Include:

```text
exact master instruction
all track instructions
sanitized raw malformed-row specimens
four-ticker stage lineage
provider field mapping
adjustment-basis audit
corporate-action audit
resampling/session audit
cache forensics
cross-provider diagnostics
repair categories
run-49 replay
previous FULL10 regression
current US regression
KR regression
positive/negative integrity fixtures
test-sink messages
main-merge evidence
live-guard state
machine-readable JSON
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

# 62. Final principle

The right fix is not:

```text
"make the validator less strict"
```

and not:

```text
"force all 14 to FULL"
```

It is:

```text
trace every malformed candle to its first bad stage,
repair only proven adapter/adjustment/cache/aggregation defects,
preserve the raw source,
and leave genuinely untrustworthy source data INVALID.
```

Technical context is valuable only when its candle data is trustworthy.
