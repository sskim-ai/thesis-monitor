# thesis-monitor — AI Swing Anchor + Multi-Timeframe Support/Resistance + Fibonacci Confluence v2
## Monthly → Weekly → Daily structural analysis hierarchy
## Deterministic pivots/OHLCV → AI structural judgment → deterministic Fibonacci math → multi-timeframe confluence
## Shadow-first; current live messages unchanged

## Metadata

- Workstream: `AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE_V2`
- Instruction version: `2.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `PRICE_STRUCTURE_ANALYSIS_SHADOW_FIRST`
- Source policy: `FREE_ONLY`
- User-visible production mutation in first stage: `0`
- Current KR/US live messages: `UNCHANGED`
- Open Research production integration: `0`
- Free Analyst full mode: preserve `OFF`
- Existing bounded AI canary: preserve current state/limits
- Trade AR: preserve `OFF`
- Public Action: preserve current version
- operationId/schema: preserve current values

### Supersedes

This instruction supersedes:

`docs/work-instructions/20260826-ai-swing-anchor-fibonacci-confluence-shadow-v1.md`

The v1 instruction correctly introduced:

```text
deterministic pivots
→ AI swing-anchor selection
→ deterministic Fibonacci calculation
→ deterministic confluence
→ AI interpretation
```

but still allowed a single `dominant_timeframe` to become too central.

v2 changes the analytical contract:

```text
MONTHLY structure first
→ WEEKLY structure second
→ DAILY structure third
→ cross-timeframe synthesis last
```

Every sufficiently supported stock should therefore have separate:

```text
monthly support/resistance
weekly support/resistance
daily support/resistance
```

and separate timeframe-specific Fibonacci structure where valid.

Do not delete/rewrite the v1 instruction if already committed.
Preserve it as history and add a supersession note.

### Expected current safe baseline

Most recently reported production main / operating:

`0e916197b2d3214d9a10a6ed0ae17c09c9f00f3e`

Resolve actual latest safe `origin/main` / operating SHA before implementation.

---

# 0. Core objective

The system should analyze price structure in this order:

```text
1. MONTHLY
   structural / long-horizon support-resistance
   major cycle swing
   monthly Fibonacci

2. WEEKLY
   intermediate trend support-resistance
   weekly swing
   weekly Fibonacci

3. DAILY
   tactical / near-term support-resistance
   daily swing
   daily Fibonacci

4. SYNTHESIS
   multi-timeframe confluence
   current-price relevance
   nearest tactical zone
   higher-timeframe structural zone
```

Do not collapse the whole analysis to one timeframe.

The user preference is explicit:

```text
월봉 지지/저항
→ 주봉 지지/저항
→ 일봉 지지/저항
```

and Fibonacci must follow the same hierarchy.

---

# 1. Architecture principle

The intended architecture is:

```text
canonical OHLCV
→ deterministic monthly/weekly/daily bars
→ deterministic pivot candidates by timeframe
→ deterministic current support/resistance candidates by timeframe
→ AI judges which pivot/swing structure is meaningful within EACH timeframe
→ backend validates selected IDs
→ backend calculates Fibonacci levels for EACH timeframe
→ deterministic multi-timeframe confluence
→ AI synthesizes hierarchy and current relevance
→ validator
→ shadow output
```

The AI owns:

```text
which monthly swing matters
which weekly swing matters
which daily swing matters
which zone matters most within each timeframe
how higher/lower timeframe structures relate
what candle structure supports the interpretation
```

The backend owns:

```text
OHLCV
bar aggregation
pivot identity
support/resistance candidate math
Fibonacci arithmetic
zone overlap math
distance math
dates/prices
provenance
numeric validation
```

---

# 2. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-ai-swing-anchor-fibonacci-multi-timeframe-structure-shadow-v2.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating
2. verify whether v1 instruction was already committed
3. commit/push this exact v2 instruction as docs-only instruction commit
4. record instruction commit/base SHA
5. create dedicated branch:

`codex/ai-fibonacci-multi-timeframe-structure-v2`

6. no force push/history rewrite
7. do not change current user-visible live messages in first stage

---

# 3. Mandatory existing-code audit

Audit current ownership before implementing.

Find/report:

```text
OHLCV provider
daily bars
weekly aggregation
monthly aggregation
pivot extraction
support/resistance zone generation
box generation
Bollinger calculations
legacy Fibonacci calculations
legacy swing/Elliott calculations
price_rules / support_zone ownership
AI price-context input
renderer price sections
numeric registry/provenance
```

Classify:

```text
EXISTING_FIBONACCI_PATH =
COMPUTED_AND_RENDERED /
COMPUTED_NOT_RENDERED /
PARTIALLY_COMPUTED /
LEGACY_ONLY /
NOT_PRESENT
```

Also classify current support/resistance architecture:

```text
CURRENT_SR_ARCHITECTURE =
SINGLE_TIMEFRAME /
MULTI_TIMEFRAME_COLLAPSED /
MULTI_TIMEFRAME_SEPARATE /
UNKNOWN
```

This audit is mandatory because the user observes that current messages look like support/resistance from only one specific timeframe.

---

# 4. Hard prohibitions

Do NOT:

- replace current business-investment logic
- let price/Fibonacci alter business thesis status
- create buy/sell commands
- create target prices
- create stop-loss orders
- let AI calculate numeric Fibonacci prices
- let AI invent pivot price/date
- hard-code ticker-specific anchors
- force Fibonacci into every timeframe
- force every timeframe to produce a level when history/structure is weak
- let daily structure silently override monthly structural context
- let monthly structure suppress a genuinely nearer tactical daily risk
- collapse monthly/weekly/daily into one "best timeframe" output
- mix adjusted and unadjusted OHLCV
- use unconfirmed future-dependent pivots
- enable Open Research
- increase production canary
- change current live messages before bounded enablement
- mutate monitoring state from replay/shadow

---

# 5. Timeframe roles — mandatory

Define analytical roles explicitly.

## MONTHLY = STRUCTURAL

Purpose:

```text
major cycle support/resistance
multi-quarter / multi-year swing structure
large base / major breakout origin
structural extension/retracement reference
```

Monthly zones answer:

```text
어디가 장기 구조적으로 중요한가?
```

## WEEKLY = INTERMEDIATE

Purpose:

```text
intermediate trend
major pullback structure
breakout/retest
multi-week/month support-resistance
```

Weekly zones answer:

```text
현재 중기 추세가 어느 구간에서 유지/훼손되는가?
```

## DAILY = TACTICAL

Purpose:

```text
nearest support/resistance
recent swing
short-term breakout/rejection/reclaim
tactical candle structure
```

Daily zones answer:

```text
당장 가격이 어디에서 반응할 가능성이 높은가?
```

---

# 6. Hierarchy is structural importance, not distance ranking

The order:

```text
MONTHLY > WEEKLY > DAILY
```

means:

```text
structural significance
```

not:

```text
monthly level is always the next level price will hit
```

The renderer must distinguish:

```text
PRIMARY_STRUCTURAL_ZONE
INTERMEDIATE_ZONE
NEAREST_TACTICAL_ZONE
```

A daily resistance may be the nearest resistance while a higher monthly resistance remains the more important structural ceiling.

Do not confuse:
- importance
- proximity

---

# 7. Canonical timeframe bars

Use existing canonical adjusted OHLCV.

Every bar requires:

```text
bar_id
ticker/security identity
timeframe
period start/end
open
high
low
close
volume
trading value if available
adjustment basis
source
as_of
completed / partial status
```

Pivot anchors should normally use completed bars only.

Partial weekly/monthly bars may be current-candle context but not confirmed pivot anchors unless existing canonical rules explicitly support them.

---

# 8. Pivot extraction — separate by timeframe

Use existing canonical rules where proven.

Expected starting framework:

```text
MONTHLY:
left/right 1–2
lookback ~60 completed bars

WEEKLY:
left/right 2
lookback ~60 completed bars

DAILY:
left/right 3
lookback ~300 completed bars
```

Do not silently replace existing production rules.

Extract by timeframe:

```text
PRIMARY_PIVOT_LOW
PRIMARY_PIVOT_HIGH
```

and preserve:

```text
pivot_bar_date
pivot_confirmation_date
```

---

# 9. Separate support/resistance candidates per timeframe

Do not construct one shared pool first.

Build:

```text
MONTHLY_SR_CANDIDATES
WEEKLY_SR_CANDIDATES
DAILY_SR_CANDIDATES
```

Each candidate needs:

```text
zone_id
timeframe
role = SUPPORT / RESISTANCE / RECLAIM / BREAKOUT_REFERENCE
low
high
source pivot refs
touch/rejection/reclaim facts
quality metadata
as_of
```

Only after each timeframe is internally analyzed may the system create cross-timeframe confluence.

---

# 10. AI analysis is mandatory per timeframe where evidence exists

Replace the v1 concept of one central `dominant_timeframe`.

v2 output must have independent slots:

```text
monthly_analysis
weekly_analysis
daily_analysis
```

For a timeframe with insufficient evidence:

```text
status = INSUFFICIENT_STRUCTURE
```

Do not copy a weekly structure into monthly/daily.

---

# 11. Monthly analysis contract

AI receives:

```text
monthly pivot sequence
monthly support/resistance candidates
monthly candle neighborhoods
recent completed monthly bars
major monthly box/reclaim facts
monthly Bollinger facts if available
```

AI selects:

```text
primary monthly support
primary monthly resistance
monthly swing low anchor
monthly swing high anchor
monthly correction low if extension-valid
monthly structural regime
confidence
evidence refs
```

Monthly should generally favor:

```text
major base low
major cycle low
structural breakout origin
major prior high
multi-quarter consolidation boundaries
```

not a tiny recent fluctuation.

---

# 12. Weekly analysis contract

AI receives:

```text
weekly pivot sequence
weekly SR candidates
weekly candle neighborhoods
recent completed weekly bars
weekly breakout/retest/reclaim facts
weekly Bollinger facts if available
```

AI selects:

```text
primary weekly support
primary weekly resistance
weekly swing low
weekly swing high
weekly correction low if valid
intermediate regime
confidence
refs
```

Weekly should usually resolve:

```text
current intermediate trend
pullback support
breakout/retest
intermediate resistance
```

---

# 13. Daily analysis contract

AI receives:

```text
daily pivot sequence
daily SR candidates
recent daily candles
daily pivot neighborhoods
volume/trading-value facts
daily breakout/rejection/reclaim facts
daily Bollinger facts if available
```

AI selects:

```text
nearest meaningful daily support
nearest meaningful daily resistance
daily swing low
daily swing high
daily correction low if valid
tactical regime
confidence
refs
```

Daily analysis is allowed to be the most immediately actionable/tactical, but should not be presented as the sole structural view.

---

# 14. Structured AI output

Use a typed object.

Suggested:

```text
multi_timeframe_price_structure_selection:

  monthly:
    status
    support_zone_id
    resistance_zone_id
    fib_mode:
      RETRACEMENT / EXTENSION / BOTH / NONE
    low_pivot_id
    high_pivot_id
    correction_low_pivot_id
    confidence
    evidence_refs
    concise_reason

  weekly:
    same

  daily:
    same

  synthesis:
    primary_structural_timeframe = MONTHLY
    intermediate_timeframe = WEEKLY
    tactical_timeframe = DAILY

    nearest_support_ref
    nearest_resistance_ref

    strongest_support_confluence_refs
    strongest_resistance_confluence_refs

    timeframe_agreement:
      ALIGNED / MIXED / CONFLICTING / INSUFFICIENT

    concise_summary
```

Do not persist hidden chain-of-thought.

---

# 15. Fibonacci must be calculated separately for each timeframe

For every valid timeframe structure:

```text
MONTHLY_FIBONACCI
WEEKLY_FIBONACCI
DAILY_FIBONACCI
```

must remain separately owned.

Do not calculate one Fib structure and relabel it across timeframes.

Each level stores:

```text
timeframe
ratio
mode
anchor refs
calculated price
currency
adjustment basis
as_of
```

---

# 16. Deterministic Fibonacci formulas

AI selects anchor IDs only.

Backend calculates.

Retracement:

```text
R0.382 = H - (H-L)*0.382
R0.500 = H - (H-L)*0.500
R0.618 = H - (H-L)*0.618
```

Extension:

```text
E0.618 = C + (H-L)*0.618
E1.000 = C + (H-L)*1.000
E1.618 = C + (H-L)*1.618
E2.618 = C + (H-L)*2.618
```

Do not expose AI-calculated price numerics.

---

# 17. Per-timeframe Fibonacci interpretation

For each timeframe, AI may choose only the most relevant Fib levels after backend calculation.

Examples:

```text
monthly:
major structural extension / long-horizon retracement

weekly:
intermediate retracement / extension

daily:
near-term retracement / breakout extension
```

Do not show all ratios.

Preferred:

```text
0–2 Fib references per timeframe
```

and often zero when no value is added.

---

# 18. Multi-timeframe Fibonacci confluence

After independent timeframe calculations, backend may identify overlap such as:

```text
MONTHLY 0.618 retracement
≈ WEEKLY pivot support

WEEKLY 1.0 extension
≈ DAILY prior high

MONTHLY prior high
≈ WEEKLY 1.618 extension
≈ DAILY resistance cluster
```

Confluence is strongest when independent structures overlap.

Store:

```text
confluence_id
contributors[]
timeframes[]
zone_low/high
tolerance method
distance/current-price relation
```

---

# 19. Confluence tolerance

Reuse existing canonical zone tolerance.

Do not widen tolerance to manufacture overlap.

If current repo uses timeframe-sensitive tolerance:
reuse it.

If not, add a bounded deterministic rule with tests and documentation.

Hard target:

```text
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
```

---

# 20. Conflict handling across timeframes

Timeframes may disagree.

Example:

```text
monthly = structural uptrend
weekly = pullback
daily = short-term resistance
```

This is not an error.

The system should express:

```text
장기 구조는 유지되지만
주봉 조정이 진행 중이고
일봉에서는 가까운 저항이 남아 있다
```

instead of choosing one timeframe and discarding the others.

---

# 21. Priority rule when conflicts occur

For structural interpretation:

```text
MONTHLY
> WEEKLY
> DAILY
```

For near-term price interaction:

```text
nearest validated DAILY/WEEKLY zone
may matter first
```

Required output distinction:

```text
구조적 중요도
vs
현재가와의 근접도
```

Do not let daily tactical structure rewrite the monthly structural regime.

---

# 22. Support/resistance hierarchy

User-visible analytical order must always be:

```text
월봉
→ 주봉
→ 일봉
```

when data is available.

Do not reorder by:
- confidence
- distance
- "dominant timeframe"

Distance may be summarized after the hierarchy.

---

# 23. Fibonacci hierarchy

User-visible Fibonacci order follows the same contract:

```text
월봉 Fib
→ 주봉 Fib
→ 일봉 Fib
```

If a timeframe has no useful Fib:

```text
omit Fib for that timeframe
```

but preserve the timeframe's support/resistance analysis if valid.

---

# 24. Current price and zone relation

Backend calculates:

```text
distance from current price
inside zone / below / above
nearest support
nearest resistance
```

for every timeframe.

AI interprets:

```text
long-horizon structural reference
intermediate confirmation zone
near-term tactical zone
```

No AI distance arithmetic.

---

# 25. Price structure evidence packet

Create a typed:

`MULTI_TIMEFRAME_PRICE_STRUCTURE_EVIDENCE_PACKET`

Contents:

```text
ticker/security
currency
current_price
session/as_of

MONTHLY:
  pivots
  SR candidates
  recent candles
  pivot neighborhoods
  volume/trading value if valid
  Bollinger facts
  box/reclaim facts

WEEKLY:
  same

DAILY:
  same

existing current price rules
```

---

# 26. Compact evidence strategy

Do not blindly pass every OHLCV bar.

For each timeframe send:

```text
all major pivot candidates
serious SR candidates
candidate neighborhoods
recent continuous bars
major trend/reclaim/rejection facts
```

Shadow/debug may compare against full OHLCV.

If compact evidence causes materially different anchor choices vs full-debug evidence:

```text
COMPACT_EVIDENCE_SUFFICIENCY = FAIL/PARTIAL
```

and do not enable production.

---

# 27. Anchor validation

For each timeframe independently validate:

```text
IDs exist
ticker/security matches
timeframe matches
date/price matches canonical bar
chronology valid
low < high
correction chronology valid
confirmed pivot as-of cutoff
adjustment basis consistent
no future bar
```

Invalid one timeframe does not invalidate all timeframes.

Example:

```text
monthly PASS
weekly PASS
daily REJECTED
```

→ use monthly/weekly and omit daily Fib.

---

# 28. Look-ahead safety

Symmetric pivots are known only after right-side confirmation bars.

Store:

```text
pivot_bar_date
pivot_confirmation_date
```

At historical/current cutoff:
only confirmed pivots are eligible.

Hard target:

`LOOKAHEAD_LEAK = 0`

---

# 29. Corporate actions/security basis

Require:

```text
same adjusted/raw basis
same listed security
same currency
```

across anchors and current price.

No ADR/ordinary-share cross-use.

Hard targets:

```text
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
```

---

# 30. Existing support/resistance engine remains baseline

Do not replace current deterministic SR zones.

New AI multi-timeframe analysis may:

```text
select
rank
qualify
explain
combine with Fib
```

Existing deterministic zone values remain the numeric source.

If legacy/current SR already has multiple timeframe zones:
reuse them.

If current renderer collapsed them:
fix the shadow renderer first, not the calculator.

---

# 31. Existing price rules remain separate

Do not automatically rewrite:

```text
confirmation_price
support_zone
warning_price
invalidation_price
```

from the new analysis.

The new structure is context.

Persistent price-rule changes require separate ownership/approval.

---

# 32. Shadow user-visible format

Create a compact but hierarchical shadow section.

Preferred shape:

```text
📐 가격 구조

월봉
• 지지: ...
• 저항: ...
• 피보나치: ... (if material)

주봉
• 지지: ...
• 저항: ...
• 피보나치: ... (if material)

일봉
• 지지: ...
• 저항: ...
• 피보나치: ... (if material)

종합
• 구조적 핵심 구간: ...
• 가장 가까운 단기 구간: ...
• 다중 timeframe confluence: ...
• 다음 확인: ...
```

Do not collapse to:

```text
지지 ...
저항 ...
```

only.

---

# 33. Message density control

Do not show every price zone.

Default maximum:

```text
MONTHLY:
1 support + 1 resistance + up to 2 Fib references

WEEKLY:
1 support + 1 resistance + up to 2 Fib references

DAILY:
1 support + 1 resistance + up to 2 Fib references
```

The AI may omit low-value entries.

---

# 34. Example analytical shape

Illustrative only:

```text
월봉
장기 지지는 월봉 주요 저점 기반 구간에 있고,
상단에서는 과거 주요 고점과 월봉 Fib 확장이 겹친다.

주봉
최근 조정은 주봉 higher-low 구간을 유지하고 있으며
주봉 0.618 되돌림이 기존 지지대와 겹친다.

일봉
현재가는 일봉 단기 저항 바로 아래이고
돌파 후 종가 안착 여부가 가장 가까운 확인 포인트다.

종합
장기 구조는 유지되지만 단기적으로는 일봉 저항을 먼저 넘어야 하며,
그 위의 주봉/월봉 confluence가 더 중요한 구조적 저항이다.
```

Do not hard-code this prose.

---

# 35. AI interpretation task after calculation

After backend calculation, AI receives:

```text
monthly validated SR/Fib
weekly validated SR/Fib
daily validated SR/Fib
cross-timeframe confluence
current price
recent candle facts
```

AI decides:

```text
1. monthly structural map
2. weekly intermediate map
3. daily tactical map
4. timeframe agreement/conflict
5. which current zone matters first
6. which higher-timeframe zone matters most structurally
7. what candle behavior confirms/weakens the interpretation
```

---

# 36. No mandatory Fibonacci

A timeframe may have:

```text
support/resistance = valid
Fibonacci = not useful
```

That is acceptable.

The feature is successful if it omits weak Fib rather than forcing a number.

---

# 37. Timeframe-specific value gate

For each timeframe classify:

```text
SR_VALUE = MATERIAL / MINOR / NONE
FIB_VALUE = MATERIAL / MINOR / NONE
```

Do not show `NONE` content in user-facing output.

---

# 38. Cross-timeframe value gate

Classify:

```text
MULTI_TIMEFRAME_CONFLUENCE_VALUE =
MATERIAL /
MINOR /
NONE
```

MATERIAL examples:

```text
monthly resistance overlaps weekly Fib extension
weekly support overlaps daily Fib retracement
multiple independent timeframe pivots converge
```

---

# 39. Relationship to business investment logic

Price structure is tactical/technical context only.

It must not itself change:

```text
business_thesis_change
earnings_estimate_impact
valuation_context
market_expectation_level
warning lifecycle
kill condition
```

unless an independently configured price rule already owns that state.

---

# 40. Shadow-first rollout

First stage:

```text
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = SHADOW
USER_VISIBLE = 0
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```

Current live Telegram/messages remain unchanged.

Shadow sidecars are archived for review.

---

# 41. Shadow benchmark universe

Run on all monitored stocks with sufficient OHLCV.

For human exact benchmark select at least:

```text
2 KR
2 US
```

and try to include:

```text
one extension/uptrend case
one retracement/pullback case
one mixed-timeframe case
one ambiguous/no-value case
```

Select based on evidence, not ticker hard-coding.

---

# 42. Mandatory exact benchmark report

Create:

`docs/reports/20260826-ai-fibonacci-multi-timeframe-exact-benchmark.md`

For each benchmark stock show:

```text
CURRENT PRODUCTION PRICE SECTION

SHADOW V2 PRICE STRUCTURE

MONTHLY
  support/resistance candidates
  selected support/resistance
  low/high/correction anchors
  Fib calculations
  confidence

WEEKLY
  same

DAILY
  same

MULTI-TIMEFRAME CONFLUENCE

CURRENT PRICE RELATION

VALIDATION STATUS

HUMAN QUALITY CLASSIFICATION
```

---

# 43. Before/after comparison

Create:

`docs/reports/20260826-price-structure-single-vs-multi-timeframe-before-after.md`

Compare:

```text
current simple/collapsed SR
vs
v2 monthly→weekly→daily structure
```

For each case answer:

```text
Did v2 reveal a higher-timeframe level missing from current message?
Did v2 reveal a nearer daily level hidden by higher timeframe?
Did Fib materially explain an existing zone?
Did output become too dense?
```

---

# 44. Anchor-selection stability — per timeframe

For frozen evidence, run multiple selections where AI runtime can vary.

Recommended:

```text
3 runs
```

Compare separately:

```text
monthly anchors
weekly anchors
daily anchors
```

Classify each:

```text
STABLE
MINOR_VARIATION
MATERIAL_VARIATION
```

If monthly or weekly material variation changes a structural zone materially:

```text
user-visible eligibility = false
```

Daily material variation may still be allowed only if daily Fib is omitted/fallback-safe.

---

# 45. Timeframe hierarchy stability

Also verify the synthesis does not randomly flip hierarchy.

Hard requirement:

```text
monthly remains structural
weekly remains intermediate
daily remains tactical
```

No run may promote daily to "structural primary" merely because it has higher confidence.

---

# 46. Historical temporal sanity

For frozen historical cutoffs:

```text
cut at T
→ build completed monthly/weekly/daily bars as of T
→ confirm pivot eligibility by confirmation date
→ select anchors
→ calculate Fib
```

Hard target:

`LOOKAHEAD_LEAK = 0`

---

# 47. Numeric provenance

Every displayed Fib numeric requires:

```text
timeframe
anchor refs
formula
ratio
calculation version
rounding
currency
security identity
adjustment basis
as_of
```

Hard target:

`UNREGISTERED_FIBONACCI_NUMERIC = 0`

---

# 48. Semantic safety

Hard targets:

```text
FIBONACCI_AS_CERTAIN_CAUSE = 0
FIBONACCI_AS_GUARANTEED_REVERSAL = 0
FIBONACCI_AS_BUSINESS_THESIS_CHANGE = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
TIMEFRAME_ROLE_CONFUSION = 0
```

---

# 49. Focused tests — timeframe separation

Required:

- monthly SR candidates remain monthly-owned
- weekly SR candidates remain weekly-owned
- daily SR candidates remain daily-owned
- no cross-timeframe relabeling
- each timeframe can independently be insufficient
- output order always monthly→weekly→daily
- daily nearest zone can be nearer without becoming structural primary
- monthly structural zone can remain important without being nearest

---

# 50. Focused tests — Fibonacci per timeframe

Required:

- monthly retracement calculation
- monthly extension
- weekly retracement
- weekly extension
- daily retracement
- daily extension
- correct anchor timeframe
- no monthly anchor used in daily Fib unless explicitly cross-timeframe analysis and not relabeled
- provenance includes timeframe

---

# 51. Focused tests — confluence

Required:

- monthly Fib + weekly pivot
- weekly Fib + daily pivot
- daily Fib + prior daily high
- monthly + weekly + daily multi-confluence
- timeframe-sensitive tolerance
- isolated Fib remains isolated
- no giant merged zone
- stronger structural zone not overwritten by lower timeframe noise

---

# 52. Focused tests — conflict interpretation

Required scenarios:

```text
monthly bullish / weekly neutral / daily bearish
monthly resistance / weekly breakout / daily pullback
monthly support far below / daily support near current
weekly resistance inside monthly broad resistance
```

Ensure output distinguishes:
- structural
- intermediate
- tactical

---

# 53. Focused tests — renderer

Required:

- exact order monthly→weekly→daily
- each timeframe has independent SR labels
- Fib omitted when no value
- no all-ratio dump
- current price proximity summarized separately
- confluence summarized last
- current production fallback unchanged
- no target/stop wording
- no business thesis mutation

---

# 54. Compact-vs-full evidence validation

For benchmark cases compare:

```text
compact evidence packet
vs
FULL_OHLCV_DEBUG
```

For each timeframe compare:
- selected support/resistance
- anchor selection
- Fib mode

Set:

```text
COMPACT_EVIDENCE_SUFFICIENCY =
PASS / PARTIAL / FAIL
```

If material higher-timeframe structure is missed in compact mode:
repair packet construction before enablement.

---

# 55. KR/US common schema

Use the same:

```text
monthly
weekly
daily
synthesis
```

schema in KR and US.

Market differences only in:
- calendar/session
- provider
- currency
- corporate-action adjustment

Set:

`KR_US_MULTI_TIMEFRAME_SCHEMA_COMMON = PASS / FAIL`

---

# 56. Current-message regression

Because current live messages are being observed separately:

```text
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```

must hold for this implementation.

No Telegram change until a later bounded enablement.

---

# 57. Shadow archive

Persist:

```text
evidence hash

monthly:
  candidates
  AI selection
  validator
  Fib
  selected SR

weekly:
  same

daily:
  same

cross-timeframe confluence
shadow render
eligibility
```

No hidden chain-of-thought.

---

# 58. Production readiness state

If all gates pass:

```text
AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE =
INTEGRATED_READY_NOT_ARMED
```

Do not enable user-visible output in this instruction.

A later enablement task should only toggle/route already-proven output.

---

# 59. Required architecture docs

Create/update:

1. `docs/architecture/AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE.md`
2. `docs/architecture/MULTI_TIMEFRAME_PRICE_STRUCTURE_EVIDENCE_PACKET.md`
3. `docs/architecture/MULTI_TIMEFRAME_SUPPORT_RESISTANCE_HIERARCHY.md`
4. `docs/architecture/FIBONACCI_NUMERIC_PROVENANCE.md`
5. `docs/architecture/PRICE_STRUCTURE_SHADOW_POLICY.md`

Document explicitly:

```text
MONTHLY = structural
WEEKLY = intermediate
DAILY = tactical
```

---

# 60. Required reports

Create:

1. `docs/reports/20260826-current-sr-timeframe-ownership-audit.md`
2. `docs/reports/20260826-existing-fibonacci-path-audit-v2.md`
3. `docs/reports/20260826-multi-timeframe-pivot-contract.md`
4. `docs/reports/20260826-multi-timeframe-sr-contract.md`
5. `docs/reports/20260826-multi-timeframe-evidence-packet.md`
6. `docs/reports/20260826-ai-timeframe-anchor-selection-validation.md`
7. `docs/reports/20260826-fibonacci-per-timeframe-numeric-provenance.md`
8. `docs/reports/20260826-multi-timeframe-confluence-audit.md`
9. `docs/reports/20260826-multi-timeframe-anchor-stability.md`
10. `docs/reports/20260826-multi-timeframe-lookahead-sanity.md`
11. `docs/reports/20260826-price-structure-single-vs-multi-timeframe-before-after.md`
12. `docs/reports/20260826-ai-fibonacci-multi-timeframe-exact-benchmark.md`
13. `docs/reports/20260826-ai-fibonacci-multi-timeframe-kr-us-shadow-replay.md`
14. `docs/reports/20260826-ai-fibonacci-multi-timeframe-readiness.md`
15. `docs/reports/20260826-ai-fibonacci-multi-timeframe-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-ai-fibonacci-multi-timeframe-readiness.json`

---

# 61. Human benchmark questions

For every benchmark stock answer separately by timeframe.

## Monthly

```text
1. 월봉에서 가장 중요한 지지/저항은 어디인가?
2. 어떤 월봉 low/high pivot을 선택했는가?
3. 월봉 Fib가 실제로 기존 zone을 설명/강화하는가?
```

## Weekly

```text
4. 주봉에서 현재 중기 추세를 결정하는 지지/저항은 어디인가?
5. 어떤 weekly swing이 현재 구조에 가장 관련 있는가?
6. weekly Fib는 월봉 구조와 확인/충돌하는가?
```

## Daily

```text
7. 현재가에서 가장 가까운 일봉 지지/저항은 어디인가?
8. 최근 캔들/거래량이 돌파/거부/눌림 중 무엇을 보여주는가?
9. daily Fib는 실질적 추가정보인가?
```

## Synthesis

```text
10. 월/주/일봉이 같은 방향인가, 혼조인가?
11. 현재가가 먼저 만날 tactical zone은 무엇인가?
12. 더 중요한 structural zone은 무엇인가?
13. Fibonacci를 빼도 같은 결론인가?
14. Fib가 없다면 더 깔끔한가?
```

---

# 62. Full validation

Required:

```text
existing ownership audit PASS
focused timeframe separation tests PASS
focused pivot tests PASS
focused anchor selection tests PASS
focused Fibonacci tests PASS
focused confluence tests PASS
conflict interpretation tests PASS
renderer tests PASS
compact-vs-full evidence PASS/safe PARTIAL
KR shadow replay PASS
US shadow replay PASS
anchor stability PASS/safe fallback
lookahead safety PASS
current user-visible diff = 0
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action unchanged
operationId/schema unchanged
implementation SHA Actions PASS
final main SHA Actions PASS if integrated to main
API /health PASS
worktrees clean
```

---

# 63. Gates

Set exactly:

```text
EXISTING_FIBONACCI_PATH =
COMPUTED_AND_RENDERED /
COMPUTED_NOT_RENDERED /
PARTIALLY_COMPUTED /
LEGACY_ONLY /
NOT_PRESENT

CURRENT_SR_ARCHITECTURE =
SINGLE_TIMEFRAME /
MULTI_TIMEFRAME_COLLAPSED /
MULTI_TIMEFRAME_SEPARATE /
UNKNOWN

MONTHLY_SR_ANALYSIS =
PASS / PARTIAL / FAIL

WEEKLY_SR_ANALYSIS =
PASS / PARTIAL / FAIL

DAILY_SR_ANALYSIS =
PASS / PARTIAL / FAIL

MONTHLY_FIBONACCI =
PASS / PARTIAL / NOT_APPLICABLE / FAIL

WEEKLY_FIBONACCI =
PASS / PARTIAL / NOT_APPLICABLE / FAIL

DAILY_FIBONACCI =
PASS / PARTIAL / NOT_APPLICABLE / FAIL

MULTI_TIMEFRAME_CONFLUENCE =
PASS / PARTIAL / NOT_APPLICABLE / FAIL

TIMEFRAME_HIERARCHY =
PASS / FAIL

PRICE_STRUCTURE_EVIDENCE_PACKET =
PASS / FAIL

AI_SWING_ANCHOR_SELECTION =
PASS / FAIL

ANCHOR_SELECTION_STABILITY =
PASS / PARTIAL / FAIL

COMPACT_EVIDENCE_SUFFICIENCY =
PASS / PARTIAL / FAIL

FIBONACCI_DETERMINISTIC_CALC =
PASS / FAIL

FIBONACCI_NUMERIC_PROVENANCE =
PASS / FAIL

LOOKAHEAD_SAFETY =
PASS / FAIL

KR_US_MULTI_TIMEFRAME_SCHEMA_COMMON =
PASS / FAIL

KR_SHADOW_REPLAY =
PASS / FAIL

US_SHADOW_REPLAY =
PASS / FAIL

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 64. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

SUPERSEDED_INSTRUCTION =
20260826-ai-swing-anchor-fibonacci-confluence-shadow-v1.md

EXISTING_FIBONACCI_PATH = ...
CURRENT_SR_ARCHITECTURE = ...

MONTHLY_SR_ANALYSIS = ...
WEEKLY_SR_ANALYSIS = ...
DAILY_SR_ANALYSIS = ...

MONTHLY_FIBONACCI = ...
WEEKLY_FIBONACCI = ...
DAILY_FIBONACCI = ...

MULTI_TIMEFRAME_CONFLUENCE = ...
TIMEFRAME_HIERARCHY = ...

PRICE_STRUCTURE_EVIDENCE_PACKET = ...
AI_SWING_ANCHOR_SELECTION = ...
ANCHOR_SELECTION_STABILITY = ...
COMPACT_EVIDENCE_SUFFICIENCY = ...

FIBONACCI_DETERMINISTIC_CALC = ...
FIBONACCI_NUMERIC_PROVENANCE = ...
LOOKAHEAD_SAFETY = ...

KR_US_MULTI_TIMEFRAME_SCHEMA_COMMON = ...

KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

BENCHMARK_MATERIAL_VALUE = ...
BENCHMARK_MINOR_VALUE = ...
BENCHMARK_NO_ADDED_VALUE = ...
BENCHMARK_WORSE = ...

AI_CALCULATED_FIB_PRICE = 0
UNREGISTERED_FIBONACCI_NUMERIC = 0
ANCHOR_PRICE_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_TICKER_MISMATCH = 0
LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

FIBONACCI_AS_CERTAIN_CAUSE = 0
FIBONACCI_AS_GUARANTEED_REVERSAL = 0
FIBONACCI_AS_BUSINESS_THESIS_CHANGE = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
TIMEFRAME_ROLE_CONFUSION = 0
ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

AI_FIBONACCI_MULTI_TIMEFRAME_STRUCTURE = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_MULTI_TIMEFRAME_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 65. Mandatory ZIP

Create:

`20260826-ai-swing-anchor-fibonacci-multi-timeframe-structure-v2-bundle.zip`

Include:
- this exact instruction
- architecture docs
- sanitized evidence examples
- exact monthly/weekly/daily anchor selections
- per-timeframe Fibonacci calculations
- confluence audit
- exact before/after benchmark
- KR/US shadow replay
- readiness report
- artifact index

Never include secrets/auth/account identifiers.

Compute/report SHA-256.

---

# 66. Severity

## P0

- wrong ticker/security anchor
- wrong anchor date/price
- future/look-ahead pivot
- adjusted/unadjusted basis mixed
- AI-exposed unvalidated Fib price
- unsupported target/stop
- price structure mutates business thesis
- current live message changes in shadow-only task
- replay mutates production state
- secret exposure

## P1

- system still collapses monthly/weekly/daily into one timeframe
- daily tactical signal is presented as monthly structural signal
- monthly/weekly structure is omitted despite valid evidence
- same Fib anchors are relabeled across timeframes
- material anchor instability becomes user-visible eligible
- excessive tolerance creates false confluence
- existing deterministic support/resistance fallback regresses
- compact evidence misses material monthly/weekly structure
- renderer ignores explicit monthly→weekly→daily order

## P2

- a timeframe legitimately has no useful Fib
- daily structure has minor anchor ambiguity
- same structural zone appears in multiple timeframes with valid provenance
- no confluence on range-bound names
- stylistic density issues
- insufficient monthly history on newer listings

---

# 67. Final principle

The system should not answer:

```text
"저항은 123,000원입니다."
```

as if one timeframe were sufficient.

It should think:

```text
월봉:
장기 구조적 지지/저항은 어디인가?

주봉:
중기 추세의 유지/훼손 구간은 어디인가?

일봉:
현재가가 가장 먼저 부딪히는 tactical 구간은 어디인가?

피보나치:
각 timeframe의 meaningful swing에서 계산한 level이
기존 pivot zone과 어디에서 겹치는가?

종합:
가까운 가격대와 더 중요한 구조적 가격대가
같은가, 다른가?
```

The required order is always:

```text
MONTHLY
→ WEEKLY
→ DAILY
→ SYNTHESIS
```

Backend calculates all prices.
AI judges the structural meaning.
