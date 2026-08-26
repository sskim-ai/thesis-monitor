# thesis-monitor — Price Structure / Wave / Fibonacci Engine v3
## 1200D / 600W / 300M OHLCV baseline
## Monthly structural wave first → Weekly intermediate → Daily tactical
## Wave-aware Fibonacci resistance/support bands + pivot/Bollinger/cross-timeframe confluence
## Reference implementation: user-supplied `codex_stock_wave_engine`
## Shadow-first architecture redefinition; do not enable live output in this instruction

## Metadata

- Workstream: `PRICE_STRUCTURE_WAVE_FIBONACCI_ENGINE_V3`
- Instruction version: `3.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `PRICE_STRUCTURE_ARCHITECTURE_REDEFINITION_SHADOW_FIRST`
- Source policy: `FREE_ONLY`
- User-visible production mutation in first stage: `0`
- Current live KR/US messages: `UNCHANGED`
- Open Research production integration: preserve `0`
- Trade AR: preserve `OFF`
- Free Analyst full mode / canary: preserve current runtime state
- Public Action / operationId / schema: preserve current values

### Required current base

Use the actual latest safe `origin/main` / operating SHA at execution time.

The most recently reported price-structure base before this instruction may include the
Fibonacci SR-ownership / consensus bounded repair. Do not hard-code an older SHA.

### Supersession / relationship to prior Fibonacci work

This v3 instruction changes the **conceptual price-structure model**.

Prior work remains valuable for:

```text
numeric provenance
look-ahead protection
monthly → weekly → daily ownership
AI ID-only selection
valid abstention
deterministic support/resistance ownership
shadow isolation
KR/US schema parity
```

But do not promote the prior "generic low→high per-timeframe Fib" model merely because
its engineering gates pass.

The target model is now **wave-aware / recovery-aware / confluence-aware**, based on the
user-supplied reference engine.

If prior bounded repair is still running:
- let it finish shadow-only
- preserve its safety improvements
- do NOT run live enablement
- use its final main as this v3 implementation base

---

# 0. User requirement — canonical

From this task forward, support/resistance analysis must use these default OHLCV history
budgets:

```text
DAILY   = 1200 bars
WEEKLY  =  600 bars
MONTHLY =  300 bars
```

These are **calculation/history defaults**, not merely UI display counts.

The analytical order remains:

```text
MONTHLY
→ WEEKLY
→ DAILY
→ CROSS-TIMEFRAME SYNTHESIS
```

The Fibonacci logic must follow the same hierarchy but must preserve the true **source wave
degree/timeframe**.

---

# 1. User-supplied reference implementation

The task is based on the user-provided archive:

`codex_stock_wave_engine(1).zip`

Relevant source artifacts:

```text
CODEX_IMPLEMENTATION_GUIDE.md
stock_structure_engine.py
SK하이닉스_structure_analysis_auto.json
regression_check_sk_hynix.py
example_commands.txt
requirements.txt
```

Treat this archive as a **reference implementation**, not production code to copy blindly.

The reference explicitly implements:

```text
raw OHLCV
→ confirmed/provisional pivots
→ long-cycle anchor candidates
→ Elliott hard-rule filtering
→ Fibonacci fit as soft scoring
→ Bollinger / volume / MACD / weekly confirmation as supporting evidence
→ partial impulse support
→ Fibonacci retracement / rebound / W5 projection families
→ pivot/Bollinger/Fibonacci confluence zones
→ box detection
```

Preserve the reference philosophy:

> Fibonacci does not create the endpoint.  
> Pivot/wave structure creates endpoint candidates; Fibonacci validates and contextualizes them.

---

# 2. Mandatory reference-source audit

Before implementation, create:

`docs/reports/20260826-user-reference-wave-engine-audit.md`

Audit the supplied reference code and explicitly document at minimum:

## Reference defaults

The reference guide currently says:

```text
daily zone lookback   = 300
weekly zone lookback  = 60
monthly zone lookback = 60
```

The new canonical thesis-monitor requirement overrides this:

```text
daily   = 1200
weekly  = 600
monthly = 300
```

## Reference pivot defaults

```text
daily left/right   = 3 / 3
weekly left/right  = 2 / 2
monthly left/right = 2 / 2
```

These are starting/reference rules, not untouchable constants.

## Reference grouping

```text
daily   pivot grouping = 1.75%
weekly  pivot grouping = 2.25%
monthly pivot grouping = 3.00%

adaptive tolerance =
max(price * grouping_pct, ATR14 * 0.50)

pivot-zone padding =
min(ATR14 * 0.10, center_price * 0.01)
```

## Reference wave hypothesis

The provided SK hynix regression expects the reference engine's primary monthly hypothesis:

```text
W0  2023-01-02     73,100
W1  2024-07-01    248,500
W2  2024-09-02    144,700
W3  2026-06-01  2,987,000  provisional
W4  2026-07-01  1,246,000  provisional
W5  None

status = W4_CANDIDATE_W5_UNCONFIRMED
```

This is a **SK hynix reference regression**, not a universal hard-coded answer.

## Reference Fibonacci families

```text
wave1_retracement_prices
wave3_retracement_prices
primary_cycle_retracement_prices
current_rebound_prices
wave5_projection_raw
wave5_projection_clusters
```

## Reference zone engine

```text
pivot groups
+ Bollinger point anchors
+ Fibonacci point anchors
→ merge confluent zones
→ classify SUPPORT / RESISTANCE / CURRENT_ZONE
```

---

# 3. Mandatory reference-code defect / limitation audit

Do not copy the reference implementation before addressing its known architectural limits.

Create:

`docs/reports/20260826-reference-wave-engine-production-gap-audit.md`

At minimum include:

### Gap A — history depth

Reference `TF_CONFIG` uses:

```text
300 / 60 / 60
```

for zone lookback.

Production v3 must use:

```text
1200 / 600 / 300
```

where history exists.

### Gap B — source-timeframe provenance

The reference code extracts one Fibonacci set from the selected **monthly primary hypothesis**,
then passes the same `fib_sets` into:

```text
build_zones(daily)
build_zones(weekly)
build_zones(monthly)
```

The reference `fib_point_anchors()` stamps:

```text
"timeframe": target timeframe
```

which can make a monthly-cycle Fib appear as if it were a daily/weekly Fib.

Production v3 must not do this.

Required distinction:

```text
source_timeframe = MONTHLY
source_degree = PRIMARY_MONTHLY_CYCLE
confluence_target_timeframe = DAILY / WEEKLY / MONTHLY
```

### Gap C — cross-timeframe merge

Reference `merge_confluent_zones()` runs inside each timeframe map.

Production v3 needs a separate final:

`CROSS_TIMEFRAME_CONFLUENCE`

stage after monthly/weekly/daily maps are independently built.

### Gap D — correlated Fib evidence

Multiple Fib ratios/methods from the same wave family must not inflate strength as if they were
fully independent evidence.

Production v3 needs explicit:

```text
evidence_family
method_family
source_degree
```

ownership/deduplication.

### Gap E — bullish standard impulse only

Reference v1 primarily implements a bullish standard impulse / partial W4-W5 path.

Do not force this hypothesis on stocks with no valid impulse.

Bearish impulse / ABC / nested degrees may remain future work.

---

# 4. OHLCV acquisition contract — 1200 / 600 / 300

Change the canonical price-structure history request:

```text
DAILY_REQUIRED_BARS   = 1200
WEEKLY_REQUIRED_BARS  = 600
MONTHLY_REQUIRED_BARS = 300
```

This applies to:

```text
pivot calculation
zone calculation
wave candidate generation
Bollinger / ATR context
historical box/reaction analysis
```

---

# 5. Independent timeframe availability

Audit how thesis-monitor currently gets weekly/monthly bars.

If weekly/monthly are fetched independently:
- request up to 600 weekly / 300 monthly

If weekly/monthly are resampled from daily:
- 1200 daily bars are NOT enough to construct 600 weekly or 300 monthly bars
- acquire sufficient underlying historical daily data, or use independent higher-timeframe
  provider endpoints

Do not silently claim:

```text
weekly = 600
monthly = 300
```

when only 1200 daily observations exist.

Create an acquisition coverage report:

```text
requested bars
returned bars
earliest date
latest completed date
provider limit
adjustment basis
```

per timeframe / market.

---

# 6. Short listing / insufficient history

For younger listings:

```text
available history < configured maximum
```

is not an error.

Use all safe available completed history.

Persist:

```text
requested_count
actual_count
history_start
history_complete_to_listing = true/false
```

Do not pad missing bars.

---

# 7. Corporate actions / adjusted basis

All price-structure math requires one consistent security basis.

For every timeframe:

```text
adjusted/raw status
split handling
stock dividend handling
security identity
currency
```

must match.

No Fib/wave structure across inconsistent price bases.

Hard target:

`CORPORATE_ACTION_BASIS_CONFLICT = 0`

---

# 8. Timeframe semantic roles

Keep the explicit hierarchy:

## MONTHLY = structural / primary degree

Questions:

```text
Where is the long-cycle structure?
Which major cycle/base low matters?
Is there a valid primary impulse / partial impulse?
Which long-horizon recovery or projection bands matter?
```

## WEEKLY = intermediate confirmation / structure

Questions:

```text
Does weekly price action confirm the monthly endpoints?
Where are the intermediate support/resistance zones?
Where does the current correction/rebound sit?
```

## DAILY = tactical execution context

Questions:

```text
Which near-term pivot/rejection/reclaim zones matter now?
Is the price approaching/rejecting a higher-degree Fib band?
```

Final message order is always:

```text
월봉 → 주봉 → 일봉 → 종합
```

---

# 9. Pivot detection

Reuse current proven thesis-monitor pivot safety if stronger.

Reference starting rules:

```text
daily   left/right = 3/3
weekly  left/right = 2/2
monthly left/right = 2/2
```

Required fields:

```text
pivot_id
ticker/security
timeframe
bar_date
confirmation_date
kind = LOW/HIGH
price
ATR
confirmed/provisional
adjustment basis
```

Symmetric pivot is eligible as confirmed only after required right bars exist.

Hard target:

`LOOKAHEAD_LEAK = 0`

---

# 10. Support/resistance — independent per timeframe

Build independent maps from the full configured history:

```text
MONTHLY_SR_MAP
WEEKLY_SR_MAP
DAILY_SR_MAP
```

Do not collapse them before analysis.

Each map may contain:

```text
pivot zones
Bollinger references
balance boxes
recovery bands
local Fib references
higher-degree Fib confluence references
```

but source provenance must remain explicit.

---

# 11. Pivot-zone construction reference

Use the supplied engine as the starting model:

```text
same-kind pivots sorted by price
→ adaptive tolerance grouping
→ ATR padding
→ width cap
```

Reference adaptive grouping:

```text
max(price * grouping_pct, ATR14 * 0.50)
```

Reference padding:

```text
min(ATR14 * 0.10, center * 0.01)
```

Do not assume the exact percentages are universally optimal.

First implement as configurable defaults and validate across the monitored universe.

Do not tune only to SK hynix.

---

# 12. Support/resistance evidence ownership

Every zone must show contributing source types.

Suggested:

```text
PIVOT_MONTHLY
PIVOT_WEEKLY
PIVOT_DAILY

BOLLINGER_MONTHLY
BOLLINGER_WEEKLY
BOLLINGER_DAILY

FIB_PRIMARY_MONTHLY_CYCLE
FIB_INTERMEDIATE_WEEKLY
FIB_TACTICAL_DAILY

WAVE5_PROJECTION
BALANCE_BOX
RECOVERY_BAND
PRIOR_HIGH_LOW
```

Do not allow unlabeled "technical resistance".

---

# 13. Zone roles are current-price dependent

Do not pre-label all Fib as support or resistance.

After construction:

```text
zone.high < current
→ SUPPORT

zone.low > current
→ RESISTANCE

current inside zone
→ CURRENT_ZONE
```

Then AI interprets significance.

---

# 14. Structural importance vs proximity

Maintain two rankings:

```text
STRUCTURAL_IMPORTANCE
CURRENT_PRICE_PROXIMITY
```

A monthly structural resistance can be more important but farther away.

A daily resistance can be closer but tactically smaller.

Do not merge these meanings into one rank.

---

# 15. Primary monthly wave hypothesis engine

Use the user reference as the initial production model for **candidate generation**, not absolute truth.

Pipeline:

```text
monthly confirmed/provisional pivots
→ candidate W0 anchors
→ W1/W2/W3/W4/W5 candidate sequences
→ hard-rule filtering
→ soft scoring
→ top-N primary monthly hypotheses
```

Return multiple candidates.

Do not force one.

---

# 16. Primary-cycle anchor candidates

Reference engine searches recent monthly confirmed pivot lows and scores:

```text
impulse score
+ major-base quality
+ mild recency
```

Production v3 should keep the same philosophy.

The reference's 8-year auto-anchor window is a starting parameter.

Because monthly history is now 300 bars, do not restrict all structural work to 8 years by accident.

Separate:

```text
history available = up to 300 monthly bars
candidate cycle search horizon = configurable
```

Report top hypotheses and score gaps.

---

# 17. Elliott hard rules — reference baseline

For bullish standard impulse candidate generation, preserve the reference safety philosophy.

Examples:

```text
W1 > W0
W2 between W0 and W1
W3 > W1
W4 between W1 high and W3
W5 > W3 for non-truncated standard W5
W3 not shortest among 1/3/5 when W5 exists
```

Endpoint must also satisfy running max/min consistency as in the reference.

Do not let Fibonacci "beauty" override hard structure.

---

# 18. Provisional wave endpoints

The user reference intentionally allows recent W3/W4 candidates to be provisional when right-side
pivot confirmation is not yet available.

Preserve explicit status:

```text
CONFIRMED
PROVISIONAL
PROJECTION
```

Never write:

```text
4파 확정
```

when the endpoint is provisional.

---

# 19. W4 candidate / W5 unconfirmed state

Preserve a state equivalent to:

`W4_CANDIDATE_W5_UNCONFIRMED`

Meaning:

```text
W0-W4 hard-rule hypothesis exists
W3/W4 may be provisional
W5 breakout above W3 is not yet confirmed
current rebound may still be W4 internal structure
```

This state is especially important for "rebound resistance" Fib analysis.

---

# 20. Fibonacci source model — change from generic swing Fib

The central v3 change:

Fibonacci references must be tied to a **wave/source degree**, not just an arbitrary timeframe
low/high pair.

Canonical families:

```text
PRIMARY_MONTHLY:
  WAVE1_RETRACEMENT
  WAVE3_RETRACEMENT
  PRIMARY_CYCLE_RETRACEMENT
  CURRENT_REBOUND
  WAVE5_PROJECTION

INTERMEDIATE_WEEKLY:
  LOCAL_RETRACEMENT optional
  LOCAL_EXTENSION optional

TACTICAL_DAILY:
  LOCAL_RETRACEMENT optional
  LOCAL_EXTENSION optional
```

Primary monthly-cycle Fib is the first-class structural layer.

Weekly/daily Fib is secondary and only exists when independently meaningful.

---

# 21. Current rebound Fibonacci — key resistance concept

For a monthly W3→W4 decline:

```text
span = W3 - W4

rebound(level) =
W4 + span * level
```

Reference levels:

```text
0.236
0.382
0.500
0.618
0.786
```

These are **recovery/rebound references from the W4 candidate**, not generic retracement levels.

When price is rebounding from W4, these can form resistance candidates.

This family is a primary target for the user's intended "Fibonacci resistance band" concept.

---

# 22. Other primary monthly Fib families

Preserve separately:

```text
wave1_retracement
wave3_retracement
primary_cycle_retracement
```

Do not flatten them into one anonymous list.

Each numeric level requires:

```text
family
ratio
source wave endpoints
source degree
confirmed/provisional status
formula
calculation version
```

---

# 23. W5 projections

When W5 is not confirmed, calculate projections as **projection references**, not targets.

Reference families include:

```text
W4 + W1 * {0.618, 1.0, 1.618, 2.618}

W4 + W3_length * {0.382, 0.5, 0.618, 1.0}

W4 + W0→W3 span * {0.5, 0.618, 1.0}
```

Cluster nearby methods.

Do not label:

```text
"목표가 확정"
```

Allowed:

```text
projection cluster
higher structural reference
```

---

# 24. Fib projection independence

Projection strength should depend on genuinely independent methods.

Record:

```text
method_family:
  WAVE1_MULTIPLE
  WAVE3_MULTIPLE
  SPAN03_MULTIPLE
```

Two ratios from the same family are correlated evidence.

Do not count them as two fully independent sources simply because there are two numbers.

---

# 25. Fib source provenance — mandatory correction

Every Fib source needs both:

```text
source_timeframe
source_degree
```

and when reused in another timeframe's zone map:

```text
confluence_target_timeframe
```

Example:

```text
source_timeframe = MONTHLY
source_degree = PRIMARY_MONTHLY_CYCLE
family = CURRENT_REBOUND
ratio = 0.382

confluence_target_timeframe = WEEKLY
```

User-facing meaning:

```text
월봉 primary-cycle rebound 38.2%가
주봉 pivot resistance와 겹친다
```

NOT:

```text
주봉 Fibonacci 38.2%
```

---

# 26. Monthly / weekly / daily Fib ownership

Build separate local Fib maps:

```text
MONTHLY_FIB_MAP
WEEKLY_FIB_MAP
DAILY_FIB_MAP
```

But also allow a higher-degree source to overlap a lower-timeframe zone while preserving its origin.

A daily zone can therefore contain:

```text
daily pivot
+ monthly rebound Fib
```

without relabeling the monthly Fib as daily.

---

# 27. AI role — select/rank validated hypotheses, not invent numerics

Preserve the prior safe architecture.

Backend generates:

```text
top-N valid monthly wave hypotheses
optional valid weekly local swing structures
optional valid daily local swing structures
```

AI receives **price-only** evidence and may:

```text
rank/select the most meaningful hypothesis
select VALID_ABSTENTION
explain why one candidate better fits current candle structure
```

AI returns IDs only.

AI must not:
- invent W0-W5 price/date
- calculate Fib
- create SR numerics

---

# 28. AI hypothesis evidence packet

For primary monthly selection include:

```text
top-N valid hypothesis IDs
W0-W4/W5 endpoint refs
monthly raw candle neighborhoods
recent completed monthly bars
weekly endpoint confirmation facts
volume / trading-value facts
Bollinger facts
MACD facts only if already safely derived
hypothesis hard-rule results
soft-score components
```

Do not send final Fib prices before Stage-1 selection if that would bias selection.

Fibonacci fit metrics may be included only as explicit soft features if the reference architecture requires them,
but raw final resistance outputs should not be used to force endpoint choice.

---

# 29. Weekly confirmation of monthly endpoints

Reference engine uses weekly pivots as endpoint confirmation.

Starting reference:

```text
date distance approximately ±45 days
price distance approximately ±6%
same kind high/high or low/low
```

Treat this as configurable shadow default.

Validate across multiple stocks before production enablement.

Do not tune only to SK hynix.

---

# 30. Support/resistance confluence engine — source-family aware

Zone strength must be based on independent evidence families.

Suggested ownership:

```text
PIVOT
BOLLINGER
FIBONACCI
BOX
PRIOR_HIGH_LOW
```

Inside Fibonacci also preserve:

```text
PRIMARY_CYCLE_RETRACEMENT
WAVE3_RETRACEMENT
CURRENT_REBOUND
W5_PROJECTION / method family
LOCAL_WEEKLY
LOCAL_DAILY
```

A zone with:

```text
weekly pivot
+ monthly current-rebound 0.382
+ monthly cycle retracement
+ Bollinger
```

should be stronger than an isolated Fib.

But correlated Fib levels should not create arbitrary strength inflation.

---

# 31. Cross-timeframe confluence — new final stage

Build first:

```text
MONTHLY_ZONE_MAP
WEEKLY_ZONE_MAP
DAILY_ZONE_MAP
```

Then separately build:

`CROSS_TIMEFRAME_CONFLUENCE_MAP`

Example contributors:

```text
monthly rebound Fib
+ weekly pivot resistance
+ daily repeated rejection
```

Persist each source independently.

Do not flatten the source timeframe.

---

# 32. Confluence tolerance

Reuse the proven canonical zone tolerance where possible.

Reference engine uses per-timeframe confluence percentages near:

```text
daily   2.0%
weekly  2.5%
monthly 3.0%
```

Audit actual code/current production values.

Do not widen tolerance merely to make the SK hynix example match.

Hard target:

`ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0`

---

# 33. Balance box vs recovery band

Keep two separate concepts.

## BALANCE_BOX

Actual sideways equilibrium region based on recent bar occupancy/touches.

Reference conditions include:
- timeframe width cap
- recent close-inside ratio
- range-overlap ratio
- upper/lower touch

## RECOVERY_BAND

A broader structural area between meaningful rebound/Fib references.

Do not call a broad Fib recovery region a balance box.

---

# 34. Current price classification

After all zone construction:

```text
below current → support
above current → resistance
contains current → current zone
```

Then rank separately by:

```text
structural importance
distance from current
evidence confluence
confirmation quality
```

---

# 35. Message design — desired shadow form

Create a hierarchical shadow message.

Example semantic layout:

```text
📐 가격 구조

월봉 — 구조
• 지지: ...
• 저항: ...
• 파동: W4 후보 / W5 미확정 같은 상태
• Fib: 현재 반등에서 중요한 rebound / cycle 구간

주봉 — 중기
• 지지: ...
• 저항: ...
• 월봉 Fib와 주봉 pivot이 겹치는지
• endpoint 확인 여부

일봉 — 단기
• 지지: ...
• 저항: ...
• 최근 rejection / reclaim / volume
• 상위 시간축 저항 접근 여부

종합
• 가장 가까운 단기 저항
• 가장 중요한 구조적 저항
• 가장 강한 cross-timeframe confluence
• 무엇이 확인되면 다음 구간으로 넘어가는지
```

Do not dump all ratios.

---

# 36. SK hynix golden reference — mandatory

Use the supplied SK hynix sample as the first mandatory regression.

The goal is NOT to hard-code its prices.

The implementation must prove that, from the supplied equivalent OHLCV, it can generate a
primary hypothesis materially consistent with the reference engine:

```text
W0 ≈ 2023-01 low
W1 ≈ 2024-07 high
W2 ≈ 2024-09 low
W3 ≈ 2026-06 high candidate
W4 ≈ 2026-07 low candidate
W5 unconfirmed
```

and preserve:

```text
provisional status for latest endpoints
current rebound Fib family
primary-cycle Fib family
W5 projections as projections
```

If the thesis-monitor implementation selects a different hypothesis:
do not force the reference answer.

Instead classify:

```text
REFERENCE_MATCH
DIFFERENT_BUT_DEFENSIBLE
MATERIAL_METHOD_CONFLICT
```

and document why.

---

# 37. SK hynix required Fib regression

The user-supplied reference includes the conceptual current-rebound levels from the selected
W3/W4 structure.

The v3 engine should reproduce the same **formula family and source ownership** when the same
hypothesis is selected.

Do not use expected numeric values as injected inputs.

Calculate from OHLCV-selected endpoints.

Report:

```text
family
ratio
calculated value
reference value
difference
source endpoint refs
```

---

# 38. SK hynix resistance-zone benchmark

The benchmark should specifically test whether v3 can create zones conceptually like:

```text
weekly pivot resistance
+ monthly primary-cycle Fib
+ monthly wave3/current-rebound Fib
+ Bollinger reference
```

when the sources genuinely overlap.

The user wants the **reason the band matters**, not merely one Fib line.

Report exact source provenance for each benchmark zone.

---

# 39. Generalization benchmark — do not overfit SK hynix

After SK hynix, validate across different price structures.

Use the current monitored universe and automatically choose at least:

```text
2 KR additional stocks
3 US stocks
```

covering as available:

```text
clean long uptrend
range-bound
recent IPO / short history
deep correction
high-volatility cyclical
non-Elliott / no valid impulse
```

Do not hard-code favorable names.

---

# 40. Mandatory full-universe shadow replay

Run all monitored KR/US stocks with sufficient OHLCV.

For every stock classify:

```text
PRIMARY_MONTHLY_HYPOTHESIS =
VALID_CONFIRMED /
VALID_PROVISIONAL /
AMBIGUOUS /
NONE

FIB_VALUE =
MATERIAL /
MINOR /
NONE

SR_VALUE =
MATERIAL /
MINOR /
NONE

WAVE_FIT_RISK =
LOW /
MEDIUM /
HIGH
```

No valid wave hypothesis is a normal result.

---

# 41. No forced Elliott

If:

```text
selected_impulse = null
```

then still produce:

```text
monthly SR
weekly SR
daily SR
Bollinger
boxes
pivot confluence
```

and omit wave Fib families that depend on the absent hypothesis.

This is mandatory.

---

# 42. Bullish-only scope disclosure

If v3 initially retains the reference engine's bullish standard-impulse scope:

state clearly:

```text
BEARISH_WAVE_ENGINE = NOT_IMPLEMENTED
ABC_INTERNAL_STRUCTURE = NOT_IMPLEMENTED
NESTED_INTERMEDIATE_DEGREE = PARTIAL / NOT_IMPLEMENTED
```

Do not infer a bullish wave count for every stock.

These may remain P2 roadmap items.

---

# 43. AI variable-selection stability

Use the safety work already completed.

For frozen candidate packets:

```text
5-run benchmark
3-run wider universe
```

Measure hypothesis ID stability.

But do not require exact ID consistency if:

```text
different valid hypotheses
→ same meaningful structural resistance/support band
→ same provisional/confirmed conclusion
```

Classify:

```text
STABLE
MINOR_VARIATION
MATERIAL_VARIATION
VALID_ABSTENTION
```

Unstable Fib must remain omitted.

---

# 44. Deterministic SR ownership

Preserve the new rule:

```text
AI does NOT own authoritative SR zone numerics.
```

AI may interpret/rank significance after deterministic maps exist.

Hard target:

```text
MONTHLY_SR_RUNTIME_VARIATION = 0
WEEKLY_SR_RUNTIME_VARIATION = 0
DAILY_SR_RUNTIME_VARIATION = 0
```

for frozen evidence.

---

# 45. Source-family scoring audit

Create an explicit score table.

Suggested starting reference:

```text
pivot group = 1.0 + repeat bonus
Bollinger = 1.2
Fib = 1.4
independent source-type confluence bonus
multi-timeframe bonus
confirmed pivot bonus
```

Do not copy these as immutable production truth.

Calibrate only enough to prevent obvious ranking defects.

Hard rule:

```text
score = technical-evidence density
NOT buy/sell score
```

---

# 46. Numeric provenance

Every user-visible technical price requires provenance.

For Fib:

```text
ticker/security
currency
source timeframe
source degree
wave hypothesis ID
family
ratio/method
endpoint refs
formula
calculated price
rounding
status confirmed/provisional/projection
as_of
```

For pivot zone:

```text
timeframe
pivot refs
grouping rule
ATR
padding
zone low/high
```

Hard target:

`UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0`

---

# 47. AI arithmetic ban

AI may not calculate:

```text
Fib prices
zone bounds
distance percentages
ATR
Bollinger prices
projection cluster centers
```

All backend-owned.

Hard target:

`AI_CALCULATED_TECHNICAL_PRICE = 0`

---

# 48. Look-ahead / incomplete-bar safety

Preserve:

```text
pivot_bar_date
pivot_confirmation_date
```

Latest incomplete weekly/monthly bar cannot confirm a pivot unless explicit canonical policy allows it.

Provisional wave endpoint may exist but must be labeled.

Hard target:

`LOOKAHEAD_LEAK = 0`

---

# 49. Projection language safety

Hard targets:

```text
PROJECTION_AS_CONFIRMED_TARGET = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0
```

Allowed:

```text
구조적 후보
회복 저항 후보
projection cluster
확인 필요
```

---

# 50. Relationship to investment logic

Technical price structure is separate from business investment logic.

It must not itself change:

```text
business_thesis_change
earnings estimates
valuation context
market expectation level
kill condition
```

unless a separately configured deterministic price rule owns that state.

---

# 51. Relationship to price rules

Do not auto-rewrite:

```text
confirmation_price
support_zone
warning_price
invalidation_price
```

from v3 wave/Fib output.

The new engine is analytical context first.

Any persistent rule migration requires a later explicit task.

---

# 52. Performance / data-volume budget

Increasing to:

```text
1200 + 600 + 300 bars per stock
```

changes acquisition/storage/compute load.

Measure:

```text
provider calls
bytes
parse time
indicator time
pivot time
wave-candidate time
zone time
AI packet size
total per-stock runtime
total full-watchlist runtime
```

Do not optimize by silently reducing the requested history.

If provider rate limits are hit:
- cache immutable historical bars
- fetch incremental new bars
- preserve 1200/600/300 canonical local history

---

# 53. Historical cache strategy

Prefer:

```text
initial backfill
→ immutable/local canonical cache
→ incremental updates
```

rather than refetching 2100 bars per stock daily.

Document:

```text
cache key
security identity
timeframe
adjustment version
latest bar
revision behavior
```

---

# 54. Provider count validation

For every monitored stock/timeframe record:

```text
requested_count
actual_count
actual_start_date
actual_end_date
completed_count
provider_limit_hit
```

Do not silently truncate.

Set:

```text
OHLCV_1200_600_300_COVERAGE =
PASS / PARTIAL / FAIL
```

Safe `PARTIAL` is valid only for:
- short listing
- documented provider historical limitation

not a coding bug.

---

# 55. Reference implementation integration policy

Do NOT drop `stock_structure_engine.py` directly into production and call it done.

Production integration must adapt concepts into existing thesis-monitor layers:

```text
provider/canonical OHLCV
price-structure domain models
deterministic calculators
numeric registry
AI evidence contract
validator
shadow receipt/archive
renderer
```

Reuse current architecture.

---

# 56. Reference-code provenance in repository

If the user-supplied reference files are staged into the repository, place them under a clearly
non-production reference path such as:

`docs/reference/user-wave-engine/`

with a README:

```text
REFERENCE_ONLY
NOT_PRODUCTION_RUNTIME
SK_HYNIX_VALIDATED_EXAMPLE
```

Do not import production runtime directly from `docs/reference`.

If the attachment is not available to Codex runtime:
record that fact and use this work instruction's source-derived contract.

Do not invent unseen code.

---

# 57. Shadow-first rollout state

First implementation state:

```text
PRICE_STRUCTURE_WAVE_FIB_V3 = SHADOW
USER_VISIBLE = 0
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```

No live Telegram price-structure changes in this instruction.

---

# 58. Exact before/after benchmark

Create:

`docs/reports/20260826-price-structure-v3-exact-before-after.md`

For each human benchmark:

```text
CURRENT_PRODUCTION_PRICE_SECTION

PRIOR_FIB_V2_SHADOW

V3_WAVE_AWARE_SHADOW

MONTHLY
  SR
  wave hypothesis/status
  Fib families
  resistance/support source provenance

WEEKLY
  SR
  monthly endpoint confirmation
  local weekly structure if available
  higher-degree Fib confluence

DAILY
  SR
  local tactical structure
  higher-degree Fib confluence

CROSS_TIMEFRAME
  strongest support
  strongest resistance
  nearest tactical resistance
  structural resistance
  confluence sources
```

---

# 59. SK hynix exact report

Create:

`docs/reports/20260826-sk-hynix-wave-fibonacci-v3-validation.md`

Must include:

```text
reference engine result
thesis-monitor v3 result
endpoint-by-endpoint comparison
confirmed/provisional state
current rebound Fib comparison
primary cycle Fib comparison
W5 projection comparison
weekly endpoint confirmation
monthly/weekly/daily SR
cross-timeframe confluence
reason for every material difference
```

No "PASS" based only on matching expected prices.

---

# 60. Generalization report

Create:

`docs/reports/20260826-wave-fibonacci-v3-generalization.md`

For every benchmark stock answer:

```text
Did a valid primary monthly hypothesis exist?
Was it confirmed/provisional?
Did Fib add material information?
Did the strongest zone contain independent non-Fib evidence?
Did the engine force a wave structure?
Did long lookback change SR materially vs old lookback?
```

---

# 61. Long-lookback impact audit

Create:

`docs/reports/20260826-ohlcv-long-history-sr-impact.md`

Compare:

```text
OLD:
daily 300
weekly 60
monthly 60

NEW:
daily 1200
weekly 600
monthly 300
```

For benchmark stocks show:

```text
new structural pivots discovered
support zones changed
resistance zones changed
old zones preserved/lost
monthly historical levels newly available
false/noisy zones introduced
```

This is essential.

Do not assume "more history = automatically better".

---

# 62. Zone-density control

Longer history can create too many stale zones.

Add deterministic relevance controls such as:

```text
reaction count
recency
structural timeframe
reclaim/rejection history
distance from current
evidence-family confluence
```

Do not simply output every historical pivot cluster.

Preserve long-history calculation but rank/omit low-value stale zones in messages.

---

# 63. Old-zone retirement / role conversion

A historical resistance may become support after a sustained reclaim.

Track:

```text
historical role
current role
reclaim status
last meaningful interaction
```

Do not permanently label an old resistance as resistance.

---

# 64. Bollinger source treatment

Reference code supports multiple Bollinger upper bands.

Production v3 should audit existing thesis-monitor Bollinger ownership first.

Do not duplicate indicators with inconsistent windows/parameters.

If adopting reference windows, keep explicit names and source timeframe.

Bollinger remains supporting evidence, not the primary wave endpoint generator.

---

# 65. MACD/RSI treatment

The reference input allows RSI/MACD and uses MACD histogram as supporting wave3 evidence.

Do not add RSI/MACD merely because the example includes columns.

Only use indicators already safely supported or added with deterministic provenance.

They remain soft evidence.

No indicator can override a wave hard rule.

---

# 66. Volume/trading-value treatment

Volume/trading value may strengthen:

```text
wave3 expansion
wave4 reaction
breakout/reclaim/rejection
```

but never create endpoint price.

Use security-appropriate adjusted volume semantics.

Do not compare incompatible share-basis periods around corporate actions.

---

# 67. Box engine

Reference `BALANCE_BOX` logic is useful as a separate technical structure.

Preserve distinction:

```text
BALANCE_BOX = actual price occupancy equilibrium
RECOVERY_BAND = Fib/wave recovery region
```

Do not merge them into the same label.

---

# 68. P0/P1/P2 framework

## P0

- wrong price/date/security
- future pivot/look-ahead
- inconsistent corporate-action basis
- AI-calculated authoritative technical price
- unlabeled provisional wave shown as confirmed
- projection shown as guaranteed target
- live user-visible mutation from shadow task
- technical signal mutates business logic
- secret/private evidence egress

## P1

- 1200/600/300 request silently truncates because implementation uses old lookback
- weekly/monthly history is faked by insufficient daily resampling
- monthly Fib is relabeled as weekly/daily Fib
- cross-timeframe confluence loses source provenance
- Fib method correlation materially inflates zone strength
- long history creates uncontrolled zone explosion
- SK hynix reference conflict is unexplained
- engine forces Elliott when no valid hypothesis exists
- variable AI selects unstable wave but Fib remains eligible

## P2

- bearish/ABC/nested degrees not yet implemented
- some stocks have no useful Fib
- short-listed company lacks full 300 monthly bars
- optional MACD/RSI absent
- stylistic output differences
- some old historical zones safely omitted from renderer

---

# 69. Focused tests — OHLCV history

Required:

- daily requests/retains up to 1200
- weekly requests/retains up to 600
- monthly requests/retains up to 300
- short listing safe partial
- provider cap visible
- no fake higher timeframe from inadequate daily history
- cache incremental update
- completed bar status

---

# 70. Focused tests — reference pivot/zone logic

Required:

- daily pivot 3/3
- weekly pivot 2/2
- monthly pivot 2/2
- adaptive ATR grouping
- zone width cap
- padding
- confirmed/provisional
- current role classification
- role conversion after reclaim
- long-history zone-density ranking

---

# 71. Focused tests — wave candidate generation

Required:

- W1 running-max rule
- W2 deepest-low rule
- W2 above W0
- W3 above W1
- W3 running-max rule
- W4 above W1 high in standard impulse
- W4 deepest-low rule
- W5 above W3 for non-truncated default
- W3 not shortest when W5 exists
- no valid impulse returns null
- provisional W3/W4 allowed with label

---

# 72. Focused tests — Fib families

Required:

- wave1 retracement
- wave3 retracement
- primary-cycle retracement
- current rebound
- W5 projection method families
- projection clustering
- source degree/timeframe
- projection vs confirmed status
- no relabel across confluence target timeframe

---

# 73. Focused tests — confluence

Required:

- monthly Fib + monthly pivot
- monthly Fib + weekly pivot
- monthly Fib + daily rejection
- weekly local Fib + weekly pivot
- daily local Fib + daily pivot
- independent family scoring
- correlated Fib dedup
- cross-timeframe final merge
- no artificially wide zone
- source provenance preserved

---

# 74. Focused tests — AI hypothesis selection

Required:

- AI selects valid hypothesis ID only
- valid abstention
- no raw price invention
- no endpoint invention
- unstable hypothesis → Fib omitted
- deterministic SR survives
- 5-run benchmark
- 3-run wider universe
- no reference answer seeded into primary trial

---

# 75. Focused tests — renderer

Required:

- order monthly→weekly→daily→summary
- source degree visible for material Fib
- monthly Fib overlapping weekly pivot is described correctly
- no all-ratio dump
- provisional status visible
- W5 projection not called target
- structural vs nearest tactical zone separated
- no target/stop command language
- no investment-logic mutation

---

# 76. KR/US parity

Use one core price-structure schema across KR/US.

Differences allowed only in:

```text
provider
calendar
currency
security adjustment
available history
```

Do not create separate Korean and US wave logic.

Set:

`KR_US_PRICE_STRUCTURE_V3_SCHEMA_COMMON = PASS / FAIL`

---

# 77. Performance acceptance

The 1200/600/300 baseline must not make the daily monitoring run operationally unsafe.

Report:

```text
median per-stock runtime
p95 per-stock runtime
full KR runtime
full US runtime
memory
provider call count
cache hit rate
AI packet size
```

If performance is too slow:
optimize cache/computation.

Do not shrink the canonical history without explicit review.

---

# 78. Existing-price-engine coexistence

Until v3 is enabled:

```text
current production SR
= unchanged

v3
= shadow sidecar
```

Do not remove current price analysis.

The exact before/after report determines whether v3 should replace/augment the existing section.

---

# 79. Promotion readiness — shadow only

After implementation, expected best state:

```text
PRICE_STRUCTURE_WAVE_FIB_V3 =
INTEGRATED_READY_NOT_ARMED
```

Set only if:

```text
1200/600/300 history contract passes
SK hynix benchmark explained
generalization benchmark passes
no forced wave structures
source provenance passes
cross-timeframe confluence passes
numeric/lookahead safety passes
variable AI unstable Fib omitted
full tests/CI pass
P0 = 0
material P1 = 0
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```

No live enablement in this instruction.

---

# 80. Required architecture docs

Create/update:

1. `docs/architecture/PRICE_STRUCTURE_WAVE_FIB_V3.md`
2. `docs/architecture/OHLCV_LONG_HISTORY_CONTRACT.md`
3. `docs/architecture/PRIMARY_MONTHLY_WAVE_HYPOTHESIS.md`
4. `docs/architecture/WAVE_FIBONACCI_SOURCE_PROVENANCE.md`
5. `docs/architecture/MULTI_TIMEFRAME_SR_CONFLUENCE_V3.md`
6. `docs/architecture/TECHNICAL_ZONE_EVIDENCE_FAMILIES.md`
7. `docs/architecture/PRICE_STRUCTURE_V3_SHADOW_POLICY.md`

---

# 81. Required reports

Create:

1. `docs/reports/20260826-user-reference-wave-engine-audit.md`
2. `docs/reports/20260826-reference-wave-engine-production-gap-audit.md`
3. `docs/reports/20260826-ohlcv-1200-600-300-acquisition.md`
4. `docs/reports/20260826-ohlcv-long-history-sr-impact.md`
5. `docs/reports/20260826-primary-monthly-wave-hypothesis-validation.md`
6. `docs/reports/20260826-wave-fibonacci-source-provenance-audit.md`
7. `docs/reports/20260826-technical-zone-evidence-family-audit.md`
8. `docs/reports/20260826-cross-timeframe-confluence-v3-audit.md`
9. `docs/reports/20260826-sk-hynix-wave-fibonacci-v3-validation.md`
10. `docs/reports/20260826-wave-fibonacci-v3-generalization.md`
11. `docs/reports/20260826-price-structure-v3-variable-ai-stability.md`
12. `docs/reports/20260826-price-structure-v3-exact-before-after.md`
13. `docs/reports/20260826-price-structure-v3-kr-us-shadow-replay.md`
14. `docs/reports/20260826-price-structure-v3-performance.md`
15. `docs/reports/20260826-price-structure-v3-safety-parity.md`
16. `docs/reports/20260826-price-structure-v3-readiness.md`
17. `docs/reports/20260826-price-structure-v3-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-price-structure-v3-readiness.json`

---

# 82. Exact human benchmark requirements

For each selected benchmark stock report:

```text
OHLCV counts:
daily
weekly
monthly

MONTHLY:
major SR
primary wave hypothesis
confirmed/provisional status
primary-cycle Fib families
recovery resistance/support

WEEKLY:
SR
monthly endpoint confirmation
higher-degree Fib confluence
local weekly Fib if valid

DAILY:
SR
recent candle/rejection/reclaim
higher-degree Fib confluence
local daily Fib if valid

SYNTHESIS:
nearest tactical support/resistance
structural support/resistance
strongest multi-source zone
strongest cross-timeframe zone
next technical confirmation
```

---

# 83. Gates

Set exactly:

```text
USER_REFERENCE_ENGINE_AUDIT =
PASS / FAIL

OHLCV_1200_600_300_CONTRACT =
PASS / PARTIAL / FAIL

DAILY_1200 =
PASS / PARTIAL / FAIL

WEEKLY_600 =
PASS / PARTIAL / FAIL

MONTHLY_300 =
PASS / PARTIAL / FAIL

LONG_HISTORY_SR =
PASS / FAIL

PRIMARY_MONTHLY_WAVE_HYPOTHESIS =
PASS / PARTIAL / FAIL

SK_HYNIX_REFERENCE =
REFERENCE_MATCH /
DIFFERENT_BUT_DEFENSIBLE /
MATERIAL_METHOD_CONFLICT /
FAIL

PROVISIONAL_WAVE_SEMANTICS =
PASS / FAIL

CURRENT_REBOUND_FIB =
PASS / NOT_APPLICABLE / FAIL

PRIMARY_CYCLE_FIB =
PASS / NOT_APPLICABLE / FAIL

WAVE5_PROJECTION =
PASS / NOT_APPLICABLE / FAIL

WAVE_FIB_SOURCE_PROVENANCE =
PASS / FAIL

WEEKLY_ENDPOINT_CONFIRMATION =
PASS / PARTIAL / FAIL

MONTHLY_SR_MAP =
PASS / FAIL

WEEKLY_SR_MAP =
PASS / FAIL

DAILY_SR_MAP =
PASS / FAIL

CROSS_TIMEFRAME_CONFLUENCE_V3 =
PASS / PARTIAL / FAIL

TECHNICAL_EVIDENCE_FAMILY_SCORING =
PASS / FAIL

NO_FORCED_ELLIOTT =
PASS / FAIL

VARIABLE_AI_HYPOTHESIS_SELECTION =
PASS / PARTIAL / FAIL

UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

KR_US_PRICE_STRUCTURE_V3_SCHEMA_COMMON =
PASS / FAIL

KR_SHADOW_REPLAY =
PASS / FAIL

US_SHADOW_REPLAY =
PASS / FAIL

PERFORMANCE =
PASS / PARTIAL / FAIL

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_WAVE_FIB_V3 =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 84. Hard safety targets

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
ANCHOR_TICKER_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_PRICE_MISMATCH = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

MONTHLY_FIB_RELABELED_AS_WEEKLY = 0
MONTHLY_FIB_RELABELED_AS_DAILY = 0

PROVISIONAL_WAVE_AS_CONFIRMED = 0
PROJECTION_AS_CONFIRMED_TARGET = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0

ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

---

# 85. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

USER_REFERENCE_ENGINE_AUDIT = ...

OHLCV_1200_600_300_CONTRACT = ...
DAILY_1200 = ...
WEEKLY_600 = ...
MONTHLY_300 = ...

KR_OHLCV_COVERAGE = ...
US_OHLCV_COVERAGE = ...

OLD_DAILY_LOOKBACK = ...
OLD_WEEKLY_LOOKBACK = ...
OLD_MONTHLY_LOOKBACK = ...

NEW_DAILY_LOOKBACK = 1200
NEW_WEEKLY_LOOKBACK = 600
NEW_MONTHLY_LOOKBACK = 300

LONG_HISTORY_SR = ...

PRIMARY_MONTHLY_WAVE_HYPOTHESIS = ...
SK_HYNIX_REFERENCE = ...

SK_HYNIX_SELECTED_STATUS = ...
SK_HYNIX_W0 = ...
SK_HYNIX_W1 = ...
SK_HYNIX_W2 = ...
SK_HYNIX_W3 = ...
SK_HYNIX_W4 = ...
SK_HYNIX_W5 = ...

PROVISIONAL_WAVE_SEMANTICS = ...

CURRENT_REBOUND_FIB = ...
PRIMARY_CYCLE_FIB = ...
WAVE5_PROJECTION = ...
WAVE_FIB_SOURCE_PROVENANCE = ...

WEEKLY_ENDPOINT_CONFIRMATION = ...

MONTHLY_SR_MAP = ...
WEEKLY_SR_MAP = ...
DAILY_SR_MAP = ...

CROSS_TIMEFRAME_CONFLUENCE_V3 = ...
TECHNICAL_EVIDENCE_FAMILY_SCORING = ...

NO_FORCED_ELLIOTT = ...

GENERALIZATION_BENCHMARK_STOCKS = ...
VALID_PRIMARY_HYPOTHESIS_COUNT = ...
PROVISIONAL_PRIMARY_HYPOTHESIS_COUNT = ...
AMBIGUOUS_COUNT = ...
NO_IMPULSE_COUNT = ...

VARIABLE_AI_HYPOTHESIS_SELECTION = ...
UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0

KR_US_PRICE_STRUCTURE_V3_SCHEMA_COMMON = ...

KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

PERFORMANCE = ...
FULL_WATCHLIST_RUNTIME = ...
CACHE_HIT_RATE = ...

AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
LOOKAHEAD_LEAK = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

MONTHLY_FIB_RELABELED_AS_WEEKLY = 0
MONTHLY_FIB_RELABELED_AS_DAILY = 0

PROVISIONAL_WAVE_AS_CONFIRMED = 0
PROJECTION_AS_CONFIRMED_TARGET = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

PRICE_STRUCTURE_WAVE_FIB_V3 = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 86. Mandatory ZIP

Create:

`20260826-price-structure-wave-fibonacci-engine-v3-bundle.zip`

Include:

- this exact instruction
- reference audit
- production-gap audit
- 1200/600/300 acquisition report
- long-history SR impact report
- SK hynix exact validation
- generalization benchmark
- source-provenance audit
- confluence audit
- KR/US shadow replay
- performance report
- safety parity
- readiness
- artifact index

If user reference source files are included, keep them under a clearly marked
`reference/` path and do not include secrets/private credentials.

Compute/report SHA-256.

---

# 87. Final principle

The new engine should not think:

```text
"find a low and high,
calculate 0.618,
call it resistance."
```

It should think structurally:

```text
MONTHLY
What long-cycle wave / correction are we in?
Which primary-cycle hypothesis is actually defensible?

FIBONACCI
Given that wave structure,
where are the recovery / retracement / projection references?

WEEKLY
Do actual weekly pivots confirm the monthly endpoints?
Which higher-degree Fib levels overlap intermediate resistance/support?

DAILY
Where is the nearest tactical pivot/rejection/reclaim?
Is price interacting with a higher-degree structural band?

CONFLUENCE
Which zone has independent:
pivot + Fib + Bollinger + multi-timeframe evidence?

INTERPRETATION
What is the nearest tactical barrier?
What is the more important structural barrier?
What remains provisional?
```

The user-supplied SK hynix engine is the reference example for this philosophy, not a template
to hard-code across every stock.

The permanent design rule is:

```text
1200 daily
600 weekly
300 monthly

monthly structure first
weekly confirmation second
daily tactical third

wave creates the structural hypothesis
Fibonacci validates / projects within that hypothesis
pivot/Bollinger/candle evidence turns levels into zones
AI interprets validated hypotheses
backend owns every number
```
