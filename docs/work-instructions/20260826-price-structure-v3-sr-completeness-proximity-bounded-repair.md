# thesis-monitor — Price Structure v3 SR Completeness / Proximity / Relevance Bounded Repair
## Deterministic SR is the base layer; Wave/Fibonacci is optional confluence
## Monthly / Weekly / Daily Major + Nearest Support/Resistance
## Fix stale-far cross-timeframe zone promotion before production enablement

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_SR_COMPLETENESS_PROXIMITY_REPAIR`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_PREENABLEMENT_SR_REPAIR`
- Source policy: `FREE_ONLY`
- Current v3 state: `INTEGRATED_READY_NOT_ARMED`
- User-visible production mutation in this task: `0`
- Telegram / scheduled-task / DB / assessment mutation: `0`
- Production Assist: preserve `OFF`
- Trade AR: preserve `OFF`
- Open Research production integration: preserve `0`
- Public Action / operationId / schema: preserve current values

### Required base

Latest reported safe final/main/operating:

`cb5e660a617cc5bdff7cc4fa8d0d44e1fab27317`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous pre-enablement result

```text
Instruction:
38b5fbca8a7264e3b73ef78c121b6ed6758c3ad8

Implementation:
84f8f549bc8fa0338309a84b23b2738f2e357646

Report/final/main/operating:
cb5e660a617cc5bdff7cc4fa8d0d44e1fab27317

CONSENSUS_MEMBERSHIP_SEMANTICS = PASS
PREVIOUS_STABLE_BASELINE/EVALUATED/REGRESSION = 7/7/0
012450 family FAIL → PASS
TSLA true conflict preserved
TSM W3 conflict preserved
SK hynix family structure = PASS
SK hynix display resistance = approx 1.869M–1.916M KRW
Knowledge price-history default = 1200/600/300
PRICE_STRUCTURE_V3_PREENABLEMENT = INTEGRATED_READY_NOT_ARMED
PRODUCTION_ENABLEMENT_READY = YES
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Do not reopen family-consensus, wave-degree, temporal, or OHLCV-history architecture unless a
regression proves a direct defect.

---

# 0. User requirement — canonical

The price-structure engine must no longer depend on a valid wave/Fibonacci hypothesis to produce a
useful support/resistance analysis.

Canonical priority:

```text
1. deterministic monthly / weekly / daily support-resistance
2. major support / major resistance per timeframe
3. nearest support / nearest resistance per timeframe
4. cross-timeframe confluence when relevant
5. wave/Fibonacci only when structurally valid
6. Fib + SR overlap receives extra emphasis
```

The system must treat:

```text
NO_VALID_WAVE
NO_STABLE_FIB
NO_FIB_SR_OVERLAP
```

as normal states.

None of them may make the base SR analysis disappear.

---

# 1. Core architecture

Target pipeline:

```text
OHLCV
1200 daily
600 weekly
300 monthly

→ deterministic monthly SR map
→ deterministic weekly SR map
→ deterministic daily SR map

→ per-timeframe:
   major support
   major resistance
   nearest support
   nearest resistance
   current zone

→ optional valid wave hypothesis
→ optional family-stable Fibonacci
→ optional SR/Fib confluence

→ cross-timeframe relevance ranking

→ final:
   nearest support
   nearest resistance
   major structural support
   major structural resistance
   meaningful Fib/SR confluence if any
```

SR must exist independently of wave/Fib.

---

# 2. Hard prohibitions

Do NOT:

- invent resistance above an all-time/highest confirmed structure merely to fill a field
- invent support below history merely to fill a field
- force an Elliott hypothesis
- force a Fibonacci family
- convert an unstable Fib family into deterministic SR
- relabel higher-timeframe SR as local-timeframe SR
- promote a very distant cross-timeframe zone as "nearest"
- widen SR grouping/confluence tolerances to manufacture overlap
- use current price itself as an artificial support/resistance level
- use raw distance alone as "structural importance"
- use structural importance alone as "nearest"
- remove long-history SR calculation merely because a historical zone is far away
- expose stale-far historical zones as the primary current actionable barrier
- change price rules / target / stop automatically
- mutate business investment logic from technicals
- enable v3 live in this task

---

# 3. Deterministic SR base layer — mandatory

For each timeframe independently build:

```text
MONTHLY_SR_MAP
WEEKLY_SR_MAP
DAILY_SR_MAP
```

from the canonical long-history contract.

Each map must exist even when:

```text
selected wave = null
AI = valid abstention
all Fib families = omitted
```

---

# 4. SR source families

Audit current deterministic SR sources and retain only safe backend-owned sources.

At minimum distinguish:

```text
PIVOT
PRIOR_HIGH_LOW
BALANCE_BOX
BOLLINGER if canonical/currently supported
ROLE_CONVERSION / RECLAIM if implemented
```

Fib is NOT part of the base SR family.

Fib enters only after the base SR map exists.

---

# 5. Per-timeframe SR output contract

Each timeframe should produce separate fields:

```text
timeframe = MONTHLY / WEEKLY / DAILY

current_zone optional

nearest_support
nearest_resistance

major_support
major_resistance

additional_supports optional
additional_resistances optional
```

Each object:

```text
zone_id
low
high
center
role
source refs
structural score
proximity score
recency / last interaction
reaction count
confirmation quality
```

Do not collapse `nearest` and `major`.

---

# 6. Meaning of "nearest"

`nearest_support`:

```text
closest eligible support zone below current price
```

`nearest_resistance`:

```text
closest eligible resistance zone above current price
```

If current price is inside a zone:

```text
current_zone
```

is separate.

Do not use the same current-zone object simultaneously as both nearest support and resistance
unless the canonical model explicitly defines and labels boundary semantics.

---

# 7. Nearest quality floor

A tiny noisy pivot should not win simply because it is 0.1% away.

Nearest ranking must first require an eligibility/quality floor.

Eligible evidence may consider:

```text
confirmed pivot
reaction count
zone width sanity
source validity
role validity
not retired/obsolete
```

Then proximity ranks among eligible zones.

Do not tune the floor to one ticker.

---

# 8. Meaning of "major"

`major_support` / `major_resistance` represent structural importance.

Use deterministic factors such as:

```text
timeframe
reaction count
pivot prominence
source-family diversity
role conversion / reclaim history
last meaningful interaction
confirmation quality
volume/trading-value evidence if canonical
```

Current-price distance is a relevance modifier, not the definition of "major".

---

# 9. Structural importance vs active relevance

A historically major level can be too far away to be the main current structural barrier.

Separate:

```text
STRUCTURAL_IMPORTANCE
ACTIVE_RELEVANCE
```

Classify zones:

```text
ACTIVE_NEAR
ACTIVE_STRUCTURAL
LONG_HORIZON_HISTORICAL
RETIRED_OR_LOW_RELEVANCE
```

Do not delete long-horizon zones from audit/history.

Do not promote them to current `nearest`/`major` summary unless active relevance supports it.

---

# 10. Proximity / relevance gate

Create a deterministic:

`SR_PROXIMITY_RELEVANCE_GATE`

Purpose:

```text
prevent stale-far cross-timeframe zones
from outranking much closer valid local SR.
```

The gate must be volatility/timeframe aware.

Potential inputs:

```text
distance_pct from current
ATR-normalized distance
timeframe
recent range / volatility
last interaction age
role
structural importance
```

Do not hard-code one universal fixed % merely to pass controls.

Report the final policy and calibration evidence.

---

# 11. Distance tiers

Create deterministic tiers, for example:

```text
NEAR
RELEVANT
LONG_HORIZON
OUT_OF_ACTIVE_RANGE
```

Exact thresholds are implementation-owned and must be validated across KR/US.

Do not widen the `NEAR` tier to include obviously remote zones.

---

# 12. Cross-timeframe confluence role

Cross-timeframe confluence is an overlay, not the default SR source.

Pipeline:

```text
local timeframe SR maps first
→ optional stable Fib
→ cross-timeframe confluence
```

A cross-timeframe zone may:

```text
strengthen a nearby local zone
identify a major structural zone
```

but must NOT automatically replace the nearest local support/resistance.

---

# 13. Cross-timeframe "nearest" rule

The final summary field:

`nearest_cross_timeframe_zone`

may be populated only if it passes the active proximity/relevance gate.

Otherwise:

```text
nearest_cross_timeframe_zone = null
reason = NO_RELEVANT_CROSS_TIMEFRAME_ZONE
```

Then the final user summary falls back to the closest eligible local SR.

This is a normal state.

---

# 14. Cross-timeframe "major" rule

A very distant but important historical cross-zone may remain:

```text
LONG_HORIZON_HISTORICAL
```

It must not be called:

```text
most important current structural support/resistance
```

unless its active relevance passes.

The renderer may omit it from the short message while keeping it in audit output.

---

# 15. Fib is optional

After deterministic SR selection:

```text
valid / stable wave
→ calculate eligible Fib families

no wave / unstable wave
→ Fib omitted
```

Then compare Fib with existing SR.

Do not make the base SR wait for Fib.

---

# 16. Fib/SR confluence

Classify Fib interaction:

```text
DIRECT_SR_CONFLUENCE
NEAR_SR_CONFLUENCE
FIB_REFERENCE_ONLY
NO_MEANINGFUL_SR_OVERLAP
```

Use existing canonical tolerance / zone-overlap logic.

Hard target:

`FIB_CONFLUENCE_TOLERANCE_WIDENING = 0`

---

# 17. Fib without SR overlap

When an eligible Fib family has no meaningful SR overlap:

```text
do not promote it as the representative resistance/support solely because it is Fib.
```

Allowed:

```text
secondary reference
audit-only
omit from short renderer
```

The base deterministic SR remains primary.

---

# 18. No-wave case

When:

```text
VALID_ABSTENTION
NO_VALID_STANDARD_IMPULSE
```

the output must still contain useful SR where the data supports it:

```text
monthly major / nearest
weekly major / nearest
daily major / nearest
```

No-wave is not a renderer failure.

---

# 19. One-sided-history case

A timeframe may genuinely have no confirmed resistance above current price or no support below it.

Examples:

```text
price above all confirmed historical resistance
short listing
very sparse higher-timeframe history
```

Do NOT fabricate a number.

Return:

```text
NO_CONFIRMED_HISTORICAL_RESISTANCE
NO_CONFIRMED_HISTORICAL_SUPPORT
```

Then the final summary may use a safe higher/lower timeframe source while preserving provenance.

---

# 20. Timeframe fallback provenance

If daily has no valid resistance but weekly does:

Allowed user meaning:

```text
일봉에서 확인된 저항은 없고,
가장 가까운 상위 시간축 저항은 주봉 약 X~Y입니다.
```

Not allowed:

```text
일봉 저항 X~Y
```

if the source is weekly.

Required fields:

```text
requested_timeframe
source_timeframe
fallback_reason
```

---

# 21. Major / nearest separation — renderer

Each timeframe shadow renderer should support:

```text
월봉
• 주요 지지
• 주요 저항
• 가까운 지지
• 가까운 저항

주봉
• 주요 지지
• 주요 저항
• 가까운 지지
• 가까운 저항

일봉
• 주요 지지
• 주요 저항
• 가까운 지지
• 가까운 저항
```

Do not necessarily show all 12 lines in the final short live message.

The structured packet must contain them.

The renderer selects only decision-relevant lines.

---

# 22. Final summary contract

Structured summary:

```text
nearest_support
nearest_resistance

major_structural_support
major_structural_resistance

nearest_cross_timeframe_zone optional
major_cross_timeframe_zone optional

fib_sr_confluence optional

no_wave_reason optional
no_resistance_reason optional
```

---

# 23. Final summary priority

For user-facing short output:

```text
1. nearest support
2. nearest resistance
3. major structural support/resistance if materially different
4. stable Fib/SR confluence if meaningful
```

Do not let a distant cross-zone displace 1–3.

---

# 24. Exact known negative controls — current shadow

Use the immutable pre-enablement replay as the baseline.

## 010120 LS ELECTRIC

Observed shadow:

```text
monthly:
support ≈ 113k–115k KRW
resistance ≈ 263k–265k

weekly:
support ≈ 153k–155k
resistance ≈ 211k–213k

daily:
support ≈ 195k–197k
resistance ≈ 226k–228k

cross summary:
nearest ≈ 54k–56k support
major ≈ 53k–55k support
```

The cross summary is clearly less current-relevant than the local timeframe SR.

Required outcome:

```text
distant 54k–56k historical cross zone
must not be labeled nearest current barrier.
```

Do not hard-code the replacement level.

---

# 25. MU negative control

Observed shadow:

```text
monthly resistance ≈ $1,024.78–$1,029.93
weekly support ≈ $852.79–$857.07
weekly resistance ≈ $948.90–$953.66
daily support ≈ $900.13–$914.52
daily resistance ≈ $1,022.54–$1,027.67

cross summary:
nearest ≈ $87–$89.04 support
major ≈ $63.04–$64.61 support
```

Required:

```text
remote old cross zones cannot be nearest / active major
when much closer valid local zones exist.
```

---

# 26. TSM negative control

Observed shadow:

```text
weekly support ≈ $414.07–$416.16
weekly resistance ≈ $450.67–$452.94
daily resistance ≈ $438.40–$440.61

cross summary:
nearest ≈ $185.04–$189.28 support
major ≈ $83.63–$85.66 support
```

Required:

```text
remote historical cross zones
must not outrank active local support/resistance.
```

TSM W3 family-consensus safety must remain unchanged.

---

# 27. SNDK no-wave negative control

Observed:

```text
full wave = VALID_ABSTENTION
SR-only fallback = true

monthly support ≈ $995.69–$1,000.69
monthly resistance ≈ $2,348.5–$2,360.28

weekly resistance ≈ $1,529.22–$1,536.89
daily support ≈ $1,407.87–$1,420.10
daily resistance ≈ $1,783.56–$1,792.51

cross summary:
nearest/major ≈ $995.69–$1,000.69 support
```

Required:

```text
no wave
→ deterministic SR remains useful

cross summary must not prefer a remote old zone
over current-relevant local SR.
```

SNDK is the mandatory no-wave SR control.

---

# 28. 003690 missing daily resistance control

Observed:

```text
daily resistance = none
monthly / weekly resistance exists
```

Audit why.

Possible legitimate outcomes:

```text
A. daily data truly has no confirmed resistance above current
→ preserve none and identify nearest higher-timeframe resistance

B. daily zone ranking/filtering accidentally drops a valid resistance
→ repair deterministic daily SR
```

Do not fabricate.

---

# 29. HUT missing daily resistance control

Observed:

```text
daily resistance = none
weekly/monthly resistance exists
```

Run the same audit.

HUT is also a previously stable family-control; do not regress family consensus.

---

# 30. SKHY short-history control

Observed:

```text
monthly support/resistance = none
weekly and daily SR exist
wave = VALID_ABSTENTION
```

This is likely a legitimate short-history condition.

Required:

```text
no fake monthly SR
no fake wave
weekly/daily structure remains usable
```

Do not turn data insufficiency into a failure.

---

# 31. SK hynix positive control

Current safe shadow:

```text
monthly/weekly/daily structural resistance
≈ 1.869M–1.916M KRW

family consensus = PASS
```

This must not regress.

The new nearest/major ranking should make the output more useful while preserving the safe Fib/SR
structural band.

Hard target:

`SK_HYNIX_PRICE_STRUCTURE_REGRESSION = 0`

---

# 32. 012450 positive control

Current micro-repair:

```text
full hypothesis = STABLE
family = PASS
safe Fib families = 7
```

Do not regress it while changing SR ranking.

---

# 33. TSLA true-conflict control

Current:

```text
family = FAIL
Fib safe = 0
SR-only fallback = true
```

The new SR layer should improve output without reintroducing unstable Fib.

Hard target:

`TSLA_UNSTABLE_FIB_REINTRODUCED = 0`

---

# 34. Current-zone semantics

If price lies inside a support/resistance zone:

return:

```text
CURRENT_ZONE
```

and distinguish:

```text
lower boundary
upper boundary
next support below
next resistance above
```

Do not call the same current zone both a clean support and a clean resistance without explaining
that the price is inside it.

---

# 35. Role conversion

Historical resistance that has been reclaimed may become support.

Historical support that has broken may become resistance if the deterministic reclaim/break logic
supports it.

Do not rank zones using original role only.

Use current role.

---

# 36. Stale-zone relevance

Long-history zones can remain structurally valid but inactive.

Record:

```text
last meaningful interaction
interaction count
age
role conversion
```

Where data supports it.

A zone with no meaningful interaction for a very long time should need stronger structural evidence
to remain an active major zone.

---

# 37. Structural score audit

Audit the current zone score.

Ensure no factor such as:

```text
reaction_count accumulated over 20 years
```

can dominate current relevance without recency/role context.

Do not remove historical evidence; separate historical importance from active relevance.

---

# 38. Cross-timeframe score audit

Audit why the current renderer chose remote zones for:

```text
010120
MU
TSM
SNDK
```

Create explicit root-cause categories:

```text
DISTANCE_NOT_IN_RANK
STRUCTURAL_SCORE_DOMINATES_DISTANCE
HISTORICAL_REACTION_ACCUMULATION
CROSS_TF_SOURCE_COUNT_DOMINANCE
CURRENT_ROLE_FILTER_GAP
OTHER
```

---

# 39. No AI SR ownership

All:

```text
nearest
major
proximity tier
relevance
fallback source
```

must be deterministic.

AI may explain but may not select arbitrary numeric zones.

Hard target:

`AI_SELECTED_AUTHORITATIVE_SR = 0`

---

# 40. Numeric provenance

Every returned major/nearest zone requires:

```text
zone_id
ticker/security
currency
source timeframe
requested timeframe
source family
pivot/source refs
raw low/high
display low/high
current role
distance_pct
structural score
active relevance
as_of
```

No unsupported numeric.

---

# 41. Display formatting

Reuse the newly proven display-only formatter.

Do not change raw numbers.

Examples:

```text
KRW:
약 186.9만~191.6만원

USD:
약 $438.40~$440.61
```

Hard target:

`RAW_NUMERIC_CHANGED_BY_SR_RENDERER = 0`

---

# 42. Human-review output examples

The new shadow renderer may look like:

```text
📐 가격 구조

월봉
• 주요 지지: ...
• 주요 저항: ...
• 가까운 지지: ...
• 가까운 저항: ...

주봉
• 주요 지지: ...
• 주요 저항: ...
• 가까운 지지: ...
• 가까운 저항: ...

일봉
• 주요 지지: ...
• 주요 저항: ...
• 가까운 지지: ...
• 가까운 저항: ...

종합
• 가장 가까운 지지: ...
• 가장 가까운 저항: ...
• 주요 구조적 지지/저항: ...
• Fib/SR confluence: ... (있을 때만)
```

This is a semantic example, not mandatory exact prose.

---

# 43. Short-message density

Do not force all timeframe lines into production later.

This task must create the structured data and shadow renderer.

Later live enablement can choose a compact subset.

---

# 44. Full 20-subject replay

Run all monitored KR/US/foreign stocks.

For every subject report:

```text
monthly:
  nearest support
  nearest resistance
  major support
  major resistance

weekly:
  same

daily:
  same

final:
  nearest support
  nearest resistance
  major structural support
  major structural resistance
  nearest cross-zone
  major cross-zone
  Fib/SR confluence

wave state
Fib state
```

---

# 45. Coverage metrics

Count:

```text
timeframe_support_side_available
timeframe_resistance_side_available

nearest_support_available
nearest_resistance_available

legitimate_no_support
legitimate_no_resistance

unexpected_empty_support
unexpected_empty_resistance
```

Goal is not 100% numeric fill.

Goal is:

```text
unexpected empty = 0
fabricated fill = 0
```

---

# 46. Required classifications

Per timeframe side:

```text
AVAILABLE_LOCAL
AVAILABLE_HIGHER_TF_FALLBACK
NO_CONFIRMED_HISTORICAL_LEVEL
INSUFFICIENT_HISTORY
```

Do not use generic `NONE` without reason.

---

# 47. Material-value review

For mandatory controls:

```text
010120
MU
TSM
SNDK
003690
HUT
SKHY
000660
012450
TSLA
```

Human classify:

```text
MATERIAL_IMPROVEMENT
MINOR_IMPROVEMENT
NO_ADDED_VALUE
WORSE
```

Required:

`WORSE = 0`

---

# 48. Focused tests — nearest ranking

Required:

- close valid local support beats remote cross support for nearest
- close valid local resistance beats remote cross resistance
- low-quality micro pivot cannot win quality floor
- current zone handled separately
- no valid side returns explicit reason
- distance tier deterministic

---

# 49. Focused tests — major ranking

Required:

- major != nearest when appropriate
- strong structural zone can be farther than nearest
- extremely remote stale zone moves to LONG_HORIZON
- recent role conversion updates current role
- historical reaction count alone cannot dominate indefinitely

---

# 50. Focused tests — cross-timeframe

Required:

- cross-zone strengthens a relevant local zone
- remote cross-zone cannot be called nearest
- remote cross-zone can remain audit-only long-horizon
- no cross-zone falls back to local nearest
- provenance preserved

---

# 51. Focused tests — no wave / no Fib

Required:

- valid abstention still yields monthly/weekly/daily SR
- Fib family 0 still yields useful final nearest/major
- no Fib/SR overlap does not suppress SR
- no-wave wording is not an error

---

# 52. Focused tests — missing local side

Required:

- daily no resistance + valid weekly resistance
  → daily reason + weekly fallback provenance
- short-history monthly no level
  → insufficient-history reason
- no fabricated numeric
- fallback never relabeled as local

---

# 53. Focused negative controls

Required fixtures/replays:

```text
010120 remote cross-zone
MU remote cross-zone
TSM remote cross-zone
SNDK no-wave remote cross-zone
003690 missing daily resistance
HUT missing daily resistance
SKHY short monthly history
```

---

# 54. Positive-control regressions

Required:

```text
000660 family-confluence preserved
012450 stable family preserved
TSLA unstable Fib not reintroduced
```

---

# 55. Safety parity

Hard targets:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

FIB_CONFLUENCE_TOLERANCE_WIDENING = 0
SR_GROUPING_TOLERANCE_WIDENING = 0

REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

RAW_NUMERIC_CHANGED_BY_SR_RENDERER = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

---

# 56. Required architecture docs

Create/update:

1. `docs/architecture/DETERMINISTIC_SR_BASE_LAYER.md`
2. `docs/architecture/SR_NEAREST_VS_MAJOR.md`
3. `docs/architecture/SR_PROXIMITY_RELEVANCE_GATE.md`
4. `docs/architecture/SR_TIMEFRAME_FALLBACK_PROVENANCE.md`
5. `docs/architecture/FIB_OPTIONAL_CONFLUENCE_POLICY.md`
6. `docs/architecture/CROSS_TIMEFRAME_SR_RELEVANCE.md`
7. update `PRICE_STRUCTURE_WAVE_FIB_V3.md`
8. update `PRICE_STRUCTURE_V3_SHADOW_POLICY.md`

---

# 57. Required reports

Create:

1. `docs/reports/20260826-v3-sr-base-layer-audit.md`
2. `docs/reports/20260826-v3-sr-nearest-major-policy.md`
3. `docs/reports/20260826-v3-cross-timeframe-proximity-root-cause.md`
4. `docs/reports/20260826-v3-sr-proximity-relevance-validation.md`
5. `docs/reports/20260826-v3-missing-local-sr-side-audit.md`
6. `docs/reports/20260826-v3-no-wave-sr-fallback-validation.md`
7. `docs/reports/20260826-v3-fib-optional-confluence-audit.md`
8. `docs/reports/20260826-v3-sr-negative-controls.md`
9. `docs/reports/20260826-sk-hynix-sr-regression.md`
10. `docs/reports/20260826-v3-sr-full-universe-replay.md`
11. `docs/reports/20260826-v3-sr-before-after-shadow.md`
12. `docs/reports/20260826-v3-sr-safety-parity.md`
13. `docs/reports/20260826-v3-sr-readiness.md`
14. `docs/reports/20260826-v3-sr-artifact-index.md`

Recommended:

`docs/reports/20260826-v3-sr-readiness.json`

---

# 58. Gates

Set exactly:

```text
DETERMINISTIC_SR_BASE_LAYER =
PASS / FAIL

MONTHLY_SR_BASE =
PASS / PARTIAL / FAIL

WEEKLY_SR_BASE =
PASS / PARTIAL / FAIL

DAILY_SR_BASE =
PASS / PARTIAL / FAIL

SR_NEAREST_MAJOR_SEPARATION =
PASS / FAIL

SR_PROXIMITY_RELEVANCE_GATE =
PASS / FAIL

REMOTE_ZONE_PROMOTED_AS_NEAREST =
0 / NONZERO

CROSS_TIMEFRAME_ACTIVE_RELEVANCE =
PASS / FAIL

FIB_OPTIONAL_CONFLUENCE =
PASS / FAIL

NO_WAVE_SR_FALLBACK =
PASS / FAIL

UNEXPECTED_EMPTY_SUPPORT =
0 / NONZERO

UNEXPECTED_EMPTY_RESISTANCE =
0 / NONZERO

FABRICATED_SR_FILL =
0 / NONZERO

FALLBACK_TIMEFRAME_RELABEL =
0 / NONZERO

LS_ELECTRIC_REMOTE_CROSS_CONTROL =
PASS / FAIL

MU_REMOTE_CROSS_CONTROL =
PASS / FAIL

TSM_REMOTE_CROSS_CONTROL =
PASS / FAIL

SNDK_NO_WAVE_SR_CONTROL =
PASS / FAIL

003690_DAILY_RESISTANCE_AUDIT =
LEGITIMATE_NONE /
REPAIRED /
FAIL

HUT_DAILY_RESISTANCE_AUDIT =
LEGITIMATE_NONE /
REPAIRED /
FAIL

SKHY_SHORT_HISTORY_CONTROL =
PASS / FAIL

SK_HYNIX_PRICE_STRUCTURE_REGRESSION =
0 / NONZERO

012450_PRICE_STRUCTURE_REGRESSION =
0 / NONZERO

TSLA_UNSTABLE_FIB_REINTRODUCED =
0 / NONZERO

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE =
0 / NONZERO

UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

RAW_NUMERIC_CHANGED_BY_SR_RENDERER =
0 / NONZERO

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_SR_COMPLETENESS =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 59. Acceptance criteria

The task can finish:

```text
PRICE_STRUCTURE_V3_SR_COMPLETENESS =
INTEGRATED_READY_NOT_ARMED
```

when:

```text
deterministic SR base PASS
nearest vs major separation PASS
proximity/relevance gate PASS
remote nearest promotion = 0
no-wave SR fallback PASS
unexpected empty sides = 0
fabricated fill = 0
fallback relabel = 0

010120 PASS
MU PASS
TSM PASS
SNDK PASS
003690 explained/repaired
HUT explained/repaired
SKHY short-history PASS

SK hynix regression = 0
012450 regression = 0
TSLA unstable Fib reintroduced = 0

P0 = 0
material P1 = 0
full tests/CI pass
current visible message diff = 0
```

---

# 60. Production enablement readiness

Set:

`PRODUCTION_ENABLEMENT_READY = YES`

only if the next bounded task can safely enable:

```text
deterministic nearest / major SR
+
only safe family-stable Fib/SR confluence
```

without displaying remote irrelevant zones.

Do NOT enable production in this instruction.

Expected next action after PASS:

`BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`

---

# 61. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

DETERMINISTIC_SR_BASE_LAYER = ...

MONTHLY_SR_BASE = ...
WEEKLY_SR_BASE = ...
DAILY_SR_BASE = ...

SR_NEAREST_MAJOR_SEPARATION = ...
SR_PROXIMITY_RELEVANCE_GATE = ...
REMOTE_ZONE_PROMOTED_AS_NEAREST = 0

CROSS_TIMEFRAME_ACTIVE_RELEVANCE = ...
FIB_OPTIONAL_CONFLUENCE = ...
NO_WAVE_SR_FALLBACK = ...

UNEXPECTED_EMPTY_SUPPORT = 0
UNEXPECTED_EMPTY_RESISTANCE = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

LS_ELECTRIC_REMOTE_CROSS_CONTROL = ...
MU_REMOTE_CROSS_CONTROL = ...
TSM_REMOTE_CROSS_CONTROL = ...
SNDK_NO_WAVE_SR_CONTROL = ...

003690_DAILY_RESISTANCE_AUDIT = ...
HUT_DAILY_RESISTANCE_AUDIT = ...
SKHY_SHORT_HISTORY_CONTROL = ...

SK_HYNIX_PRICE_STRUCTURE_REGRESSION = 0
SK_HYNIX_NEAREST_SUPPORT = ...
SK_HYNIX_NEAREST_RESISTANCE = ...
SK_HYNIX_MAJOR_SUPPORT = ...
SK_HYNIX_MAJOR_RESISTANCE = ...
SK_HYNIX_FIB_SR_CONFLUENCE = ...

012450_PRICE_STRUCTURE_REGRESSION = 0
TSLA_UNSTABLE_FIB_REINTRODUCED = 0

KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

MATERIAL_IMPROVEMENT = ...
MINOR_IMPROVEMENT = ...
NO_ADDED_VALUE = ...
WORSE = 0

AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

FIB_CONFLUENCE_TOLERANCE_WIDENING = 0
SR_GROUPING_TOLERANCE_WIDENING = 0

RAW_NUMERIC_CHANGED_BY_SR_RENDERER = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

PRICE_STRUCTURE_V3_SR_COMPLETENESS = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 62. Mandatory completion ZIP

Create:

`20260826-price-structure-v3-sr-completeness-proximity-bounded-repair-bundle.zip`

Include:

- exact instruction
- base-layer audit
- nearest/major policy
- proximity root-cause
- missing-side audit
- no-wave fallback audit
- Fib optional confluence audit
- mandatory negative controls
- SK hynix regression
- full 20-subject replay
- before/after shadow
- safety parity
- readiness
- artifact index

Do not include secrets, auth headers, account identifiers, or hidden chain-of-thought.

Compute/report SHA-256.

---

# 63. Severity

## P0

- fabricated support/resistance numeric
- wrong security/currency/basis
- look-ahead pivot
- unstable Fib leaks into user-visible confluence
- fallback timeframe relabeled as local
- technical output mutates business investment logic
- shadow leaks to live
- review/replay mutates production state

## P1

- remote historical cross-zone shown as nearest current zone
- valid local SR exists but summary prefers irrelevant old zone
- no-wave subject loses usable deterministic SR
- unexpected local support/resistance side becomes empty
- major and nearest rankings are identical by construction
- historical reaction count dominates active relevance
- fallback provenance lost
- 010120/MU/TSM/SNDK negative controls fail
- SK hynix / 012450 safe output regresses
- TSLA unstable Fib reintroduced

## P2

- genuine no-resistance breakout state
- short-history monthly SR unavailable
- no useful Fib confluence
- long-horizon historical zones omitted from short renderer
- minor wording/style differences

---

# 64. Final principle

The permanent price-structure priority is:

```text
SR first.
Fib second.
```

Specifically:

```text
monthly / weekly / daily deterministic SR
must work whether or not an Elliott count exists.

"nearest"
means current-price relevant.

"major"
means structurally important.

"cross-timeframe"
means corroboration,
not automatic priority.

"Fibonacci"
means optional structural confluence,
not the source of the base support/resistance map.
```

When Fib and SR overlap:

```text
highlight the confluence.
```

When Fib does not overlap:

```text
keep deterministic SR primary.
```

When there is no wave:

```text
nothing is broken.
show the support/resistance structure.
```
