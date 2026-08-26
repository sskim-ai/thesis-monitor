# thesis-monitor — Price Structure / Wave / Fibonacci v3 Bounded Repair
## Partial-Bar Temporal Safety + True 1200D Backfill + Wave-Degree Separation + Variable-AI Feedback Loop
## SK hynix as mandatory regression; shadow-only until all material P1s close

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_TEMPORAL_CYCLE_FEEDBACK_BOUNDED_REPAIR`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_P1_REPAIR`
- User-visible production mutation: `0`
- Current v3 state: `SHADOW`
- Open Research production integration: preserve `0`
- Trade AR: preserve `OFF`
- Production Assist / canary: preserve current runtime state
- Source policy: `FREE_ONLY`
- Public Action / operationId / schema: preserve current values

### Required base

Latest reported safe final main / operating:

`d78940be0aab43227a1eb76bc0d9caa6f56c0d00`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Previous v3 result

```text
20-stock replay:
KR 7/7
US/foreign 13/13

Variable AI:
17 calls
stable 14 stocks
valid abstention 6
semantic rejection 0

DAILY_1200 = PARTIAL
  provider cap = 1000

WEEKLY_600 / MONTHLY_300 =
  selective coverage depending on listing history

SK_HYNIX_REFERENCE =
  MATERIAL_METHOD_CONFLICT

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 2

PRICE_STRUCTURE_WAVE_FIB_V3 = SHADOW
PRODUCTION_ENABLEMENT_READY = NO
```

### Important review findings that this instruction must address

This bounded repair treats the following as distinct surfaces:

```text
A. PARTIAL BAR TEMPORAL CORRECTNESS

B. TRUE DAILY 1200 HISTORY

C. WAVE DEGREE / CYCLE CANDIDATE COVERAGE

D. VARIABLE-AI SELECTION → BACKEND FIB → CONFLUENCE → SHADOW RENDER FEEDBACK LOOP

E. USER REFERENCE IMPLEMENTATION AVAILABILITY / METHOD COMPARISON
```

Do not redesign the entire v3 architecture.

---

# 0. Objective

Close the remaining correctness/integration gaps before any live price-structure enablement.

Target architecture after repair:

```text
canonical OHLCV
→ explicit COMPLETE / PARTIAL bar state
→ only completed bars may confirm pivots
→ 1200D / 600W / 300M canonical history
→ degree-aware wave candidate generation
→ variable AI chooses valid hypothesis ID or abstains
→ backend validates selected ID
→ backend calculates wave/Fibonacci families
→ backend builds monthly/weekly/daily SR maps
→ backend builds cross-timeframe confluence
→ shadow renderer produces exact monthly→weekly→daily message
```

The repair is successful only if the **actual variable-AI selected hypothesis** flows through the deterministic Fib/confluence/render pipeline.

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-price-structure-v3-temporal-cycle-feedback-bounded-repair.md`

Before implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. verify actual latest safe main/operating
2. commit/push this exact instruction as docs-only instruction commit
3. record instruction commit/base SHA
4. create branch:

`codex/price-structure-v3-temporal-cycle-feedback-repair`

5. no force push/history rewrite
6. remain shadow-only throughout this instruction

---

# 2. Hard prohibitions

Do NOT:

- enable v3 price structure in Telegram/live messages
- weaken look-ahead protection
- mark a partial weekly/monthly bar as completed
- use a partial bar as a right-side pivot-confirmation bar
- reduce the 1200/600/300 requirement merely because one provider caps daily at 1000
- fake 600 weekly / 300 monthly from insufficient daily history
- hard-code SK hynix 2023 W0 as the production answer
- hard-code user-reference wave endpoints
- bias the primary AI prompt with the desired SK hynix reference answer
- widen Fib/confluence tolerance to force a match
- let AI calculate Fibonacci numerics
- let AI alter deterministic SR numerics
- let archive-only AI selection count as end-to-end v3 success
- mutate business investment logic from technical structure
- add paid providers
- mutate monitoring/assessment DB from shadow/replay
- manually send Telegram
- expose secrets / tokens / account data

---

# TRACK A — Partial-Bar Temporal Safety

# 3. Canonical bar-state contract

Every canonical OHLCV bar must have:

```text
bar_state:
  COMPLETE
  PARTIAL

timeframe:
  DAILY
  WEEKLY
  MONTHLY

session/period start
session/period end
market calendar
observed_at
```

Do not infer completion only from provider presence.

---

# 4. Daily completion rule

For a daily bar:

```text
COMPLETE
only after the market's regular session has completed
for that trading date
```

Before regular-session close:

```text
current daily bar = PARTIAL
```

The partial daily bar may be used for:

```text
current candle context
current price context
intraday tactical observation
```

It may NOT be used for:

```text
confirmed pivot
right-side pivot confirmation
completed-bar historical wave endpoint
```

---

# 5. Weekly completion rule

For a weekly bar:

```text
COMPLETE
only after the final regular trading session
of that market week has completed
```

A current Monday–Thursday weekly aggregation is:

`PARTIAL`

It may be used as current weekly candle context.

It may NOT:

```text
confirm a prior weekly pivot
become a confirmed weekly wave endpoint
serve as a right-side confirmation bar
```

---

# 6. Monthly completion rule

For a monthly bar:

```text
COMPLETE
only after the final regular trading session
of that market month has completed
```

A current incomplete month is:

`PARTIAL`

It may be used as:

```text
current monthly candle context
provisional current-wave evidence
```

It may NOT:

```text
confirm a prior monthly pivot
act as a right-side confirmation bar
convert a provisional endpoint to confirmed
```

---

# 7. Pivot confirmation date

Persist for every symmetric pivot:

```text
pivot_bar_date
required_right_bar_count
pivot_confirmation_date
confirmation_bar_ids
```

A pivot becomes `CONFIRMED` only when all required right-side bars are themselves `COMPLETE`.

Hard target:

```text
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
```

---

# 8. Provisional wave endpoint semantics

A wave endpoint may use a recent partial/structurally interesting bar only if it is explicitly:

```text
PROVISIONAL
```

Provisional endpoint may feed:

```text
shadow hypothesis
provisional rebound/projection analysis
```

only when the price basis is explicit.

Do not promote:

```text
PROVISIONAL → CONFIRMED
```

until pivot confirmation rules pass.

Hard targets:

```text
PROVISIONAL_WAVE_AS_CONFIRMED = 0
PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT = 0
```

---

# 9. SK hynix temporal negative control

Mandatory check on the current SK hynix frozen/replayed context.

If the analysis date is inside August 2026:

```text
August monthly bar
= PARTIAL until final August trading session closes
```

Therefore a June monthly high requiring two right-side monthly bars under a 2/2 pivot rule must not be marked confirmed using an incomplete August bar.

Report the exact before/after status of:

```text
W3 candidate
W4 candidate
monthly pivots near 2026-06 / 2026-07 / 2026-08
```

Do not force the user's reference status; derive it from the repaired temporal contract.

---

# 10. Temporal audit of all 20 stocks

Create per-stock/timeframe counts:

```text
complete bars
partial bars
confirmed pivots
provisional pivots
previously misclassified pivots if any
```

Set:

`BAR_COMPLETION_TEMPORAL_CONTRACT = PASS / FAIL`

---

# TRACK B — True Daily 1200 Historical Backfill

# 11. Daily 1200 remains canonical

Do not relax:

```text
DAILY_REQUIRED_BARS = 1200
```

A provider page/endpoint limit of 1000 is an acquisition implementation issue.

The permanent requirement remains 1200 where listing history supports it.

---

# 12. Audit current provider capabilities

For KR and US/foreign daily OHLCV:

document:

```text
provider
per-request limit
pagination support
date-range support
historical endpoint
oldest available date
adjusted price support
revision semantics
```

Create:

`docs/reports/20260826-daily-1200-provider-capability-audit.md`

---

# 13. Daily backfill strategy

Implement the safest available FREE_ONLY strategy.

Preferred options, in order:

```text
1. provider-native pagination / cursor
2. provider date-range segmented requests
3. approved free secondary historical source with canonical reconciliation
4. existing local historical cache + incremental append
```

Do not:
- scrape prose pages
- add paid providers
- mix adjusted/unadjusted history

---

# 14. Canonical historical cache

Prefer:

```text
initial historical backfill
→ local canonical cache
→ incremental daily append / revision
```

Cache key must bind:

```text
security_id
market/listing
timeframe
adjustment basis/version
currency
```

Persist:

```text
first bar
last complete bar
bar count
source lineage
revision timestamp
```

---

# 15. Daily 1200 stitching

If multiple requests are stitched:

validate:

```text
no duplicate dates
no missing trading dates where provider should have data
same adjustment basis
same security identity
same currency
monotonic chronological order
```

Hard targets:

```text
OHLCV_DUPLICATE_DATE = 0
OHLCV_STITCH_BASIS_CONFLICT = 0
OHLCV_SECURITY_MISMATCH = 0
```

---

# 16. Daily 1200 coverage gate

For long-listed stocks with sufficient source history:

```text
actual completed daily bars >= 1200
```

Short-listed stocks:

```text
actual bars < 1200
listing history fully covered
→ safe PARTIAL
```

Provider limitation without attempted backfill:

```text
FAIL
```

Set:

```text
DAILY_1200 =
PASS / PARTIAL / FAIL
```

---

# 17. Weekly/monthly history integrity

Do not regress:

```text
WEEKLY 600
MONTHLY 300
```

Where history exists.

If weekly/monthly come from dedicated provider series:
validate counts directly.

If they are resampled:
prove enough underlying historical data exists.

Hard target:

`FAKE_HIGHER_TIMEFRAME_COVERAGE = 0`

---

# 18. Backfill performance

Report:

```text
initial backfill runtime
incremental runtime
cache hit rate
provider calls
bytes downloaded
full-watchlist update runtime
```

Do not refetch full 1200 daily bars every day if cache can safely avoid it.

---

# TRACK C — Wave Degree / Current-Cycle Separation

# 19. Root cause to test

The v3 SK hynix candidate set appears to have favored a much older 2016 low across top hypotheses.

The repair must determine whether the candidate generator is conflating:

```text
GRAND_CYCLE
```

with:

```text
PRIMARY_CURRENT_CYCLE
```

Do not assume that diagnosis; prove it in a candidate audit.

---

# 20. Wave degree model

Introduce explicit candidate degree metadata.

Minimum initial degree taxonomy:

```text
GRAND_CYCLE
PRIMARY_CURRENT_CYCLE
INTERMEDIATE
TACTICAL
```

This is a structural labeling system, not full Elliott-theory ontology.

The primary v3 monthly hypothesis should normally compare:

```text
GRAND_CYCLE candidates
vs
PRIMARY_CURRENT_CYCLE candidates
```

rather than letting the longest/largest historical swing dominate automatically.

---

# 21. 300-month history remains useful

Do not solve the problem by shrinking monthly lookback.

Keep:

```text
MONTHLY = up to 300 bars
```

The long history is needed to know older structural zones and grand-cycle context.

The change is:

```text
history breadth
≠ automatic W0 age
```

---

# 22. Current-cycle candidate generation

Create a distinct:

`PRIMARY_CURRENT_CYCLE_CANDIDATE_SET`

using recent structural monthly pivots / major bases.

Candidate generation may consider:

```text
major monthly base low
major breakout origin
large higher-low after prior cycle
regime change / structural reclaim
volatility contraction → expansion transition
```

Use deterministic features.

Do not hard-code calendar years.

---

# 23. Grand-cycle candidate generation

Create:

`GRAND_CYCLE_CANDIDATE_SET`

from longer-history monthly structures.

Grand-cycle candidates can influence:

```text
long-horizon structural resistance/support
higher-degree Fib reference
context
```

but should not automatically displace a valid current-cycle candidate.

---

# 24. Degree-aware scoring

Separate score components.

Suggested:

```text
hard structural validity

cycle-degree fit
recency appropriate to requested degree
impulse magnitude
base quality
pivot prominence
weekly endpoint confirmation
volume/trading-value evidence
Fib fit as soft evidence
```

Do not let:

```text
raw magnitude
```

alone dominate.

Do not tune weights only to make SK hynix 2023 win.

---

# 25. Candidate diversity requirement

For every stock with enough monthly history, the top candidate packet should include:

```text
at least one plausible current-cycle candidate
```

when one exists.

If all top-N candidates come from one old grand-cycle anchor:

the generator must explain:

```text
NO_VALID_CURRENT_CYCLE
```

or fail the diversity audit.

Do not silently present only one degree family.

---

# 26. SK hynix mandatory candidate coverage

For SK hynix, audit whether a materially valid current-cycle candidate using the 2023-era base exists from the OHLCV.

Do NOT hard-code:

```text
W0 = 2023-01 73,100
```

as an answer.

Instead require:

```text
if a structurally valid 2023-era current-cycle candidate exists,
it must appear in the PRIMARY_CURRENT_CYCLE candidate set
and be available to the AI selector.
```

Set:

```text
SK_HYNIX_CURRENT_CYCLE_COVERAGE =
PASS / NO_VALID_CANDIDATE / FAIL
```

---

# 27. AI degree selection

Stage-1 variable AI receives:

```text
grand-cycle candidate IDs
primary-current-cycle candidate IDs
price-only candle context
weekly confirmation facts
degree labels
hard-rule outcomes
```

AI returns:

```text
selected_hypothesis_id
selected_degree
confidence
or VALID_ABSTENTION
```

No price invention.

---

# 28. Degree hierarchy in rendering

If both valid:

```text
GRAND_CYCLE
→ long-horizon context only

PRIMARY_CURRENT_CYCLE
→ main current monthly wave/Fib analysis
```

Do not dump both equally.

Message should prioritize:

```text
current-cycle structural resistance/support
```

while optionally noting an important grand-cycle level.

---

# 29. Degree stability benchmark

Run variable AI repeated selection.

Measure:

```text
selected hypothesis ID
selected degree
visible structural zone
```

A shift:

```text
PRIMARY_CURRENT_CYCLE ↔ GRAND_CYCLE
```

that materially changes visible resistance is a material variation.

Unstable output remains shadow-only.

---

# TRACK D — User Reference Implementation Availability

# 30. Reference archive must be available to implementation

The user supplied:

`codex_stock_wave_engine(1).zip`

The previous v3 run reportedly could not perform byte-level reference comparison because the archive was not available in the Codex runtime/repository.

For this repair:

either:

```text
A. stage sanitized reference files under:
docs/reference/user-wave-engine/
```

or:

```text
B. explicitly make the attachment available to the implementation runtime
```

Preferred staged files:

```text
CODEX_IMPLEMENTATION_GUIDE.md
stock_structure_engine.py
SK하이닉스_structure_analysis_auto.json
regression_check_sk_hynix.py
example_commands.txt
```

Mark:

```text
REFERENCE_ONLY
NOT_PRODUCTION_RUNTIME
```

Do not import runtime code from docs/reference.

---

# 31. Reference integrity

If staged:

record:

```text
source attachment name
file SHA-256
staged file SHA-256
```

No silent edits.

If a file needs sanitization:
report exact changes.

---

# 32. Method comparison, not answer matching

Compare:

```text
reference implementation
vs
thesis-monitor v3 repaired method
```

For SK hynix:

```text
pivot confirmation semantics
candidate degree
W0-W4/W5 endpoints
confirmed/provisional status
current rebound Fib
primary-cycle Fib
projection families
zone confluence
```

Classify differences:

```text
REFERENCE_MATCH
DIFFERENT_BUT_DEFENSIBLE
REFERENCE_TEMPORAL_ISSUE
THESIS_MONITOR_METHOD_ISSUE
MATERIAL_METHOD_CONFLICT
```

Do not force match if repaired temporal safety makes the reference endpoint status obsolete.

---

# TRACK E — Variable AI Selection → Deterministic Feedback Loop

# 33. Current integration gap to prove

The previous v3 result may have run variable AI selection as an archive/stability trial without feeding the selected hypothesis back into the actual v3 shadow engine.

Audit exact current path:

```text
candidate generation
→ variable AI
→ selected ID
→ ??
```

Set:

```text
VARIABLE_AI_SELECTION_CONNECTED_TO_V3_ENGINE =
YES / NO
```

---

# 34. Required end-to-end shadow path

The repaired path must be:

```text
canonical OHLCV
→ wave candidates
→ variable AI selected hypothesis ID
→ backend validation
→ deterministic wave/Fib family calculation
→ deterministic SR maps
→ deterministic cross-timeframe confluence
→ bounded AI interpretation
→ shadow render
→ validation/archive
```

No archive-only dead end.

---

# 35. Selected-ID validator

Validate:

```text
hypothesis ID exists
ticker/security matches
degree matches
all endpoint refs exist
endpoint status valid
temporal cutoff valid
corporate-action basis valid
```

Invalid:

```text
Fib omitted
deterministic SR survives
packet continues
```

No guessing.

---

# 36. Deterministic calculations after selection

Only after a selected hypothesis validates, calculate:

```text
wave1 retracement
wave3 retracement
primary-cycle retracement
current rebound
W5 projection families
```

according to the selected hypothesis.

Do not precompute all final price outputs and leak them into Stage-1 AI selection unless explicitly used as allowed soft fit metrics without final resistance-label bias.

---

# 37. Feedback-loop exact artifact

For every variable-AI-selected stock/timeframe archive:

```text
input evidence hash
candidate IDs
selected hypothesis ID
selected degree
validator result
calculated Fib families
SR map
confluence map
rendered shadow text
numeric registry refs
```

No hidden chain-of-thought.

---

# 38. SK hynix end-to-end mandatory proof

For SK hynix show:

```text
AI selected hypothesis
→ backend validates
→ Fib values calculated
→ monthly SR/Fib
→ weekly confirmation/confluence
→ daily tactical confluence
→ exact shadow message
```

This is mandatory.

A stable AI selection without downstream Fib output is no longer sufficient.

---

# 39. Full-universe feedback-loop replay

Run all monitored stocks.

Report:

```text
AI SELECTED
VALID_ABSTENTION
VALIDATOR_REJECTED
FIB CALCULATED
FIB OMITTED
SHADOW RENDERED
```

per stock.

Hard target:

```text
SELECTED_BUT_NOT_FED_TO_ENGINE = 0
```

unless deterministic validator explicitly rejects it.

---

# TRACK F — SK hynix Exact Revalidation

# 40. Mandatory SK hynix report

Create:

`docs/reports/20260826-sk-hynix-v3-bounded-repair-validation.md`

Include:

```text
A. complete/partial bar timeline
B. monthly pivot confirmation status
C. 1200D / 600W / 300M actual coverage
D. grand-cycle candidates
E. primary-current-cycle candidates
F. variable AI 5-run selections
G. selected degree/hypothesis
H. deterministic Fib families
I. monthly SR
J. weekly SR / endpoint confirmation
K. daily SR
L. cross-timeframe confluence
M. exact shadow message
N. comparison to user reference engine
```

---

# 41. No SK hynix hard-coded pass condition

Do not require exact reference endpoints.

Accept:

```text
REFERENCE_MATCH
or
DIFFERENT_BUT_DEFENSIBLE
```

only if:

```text
temporal safety correct
candidate coverage correct
method/provenance explained
AI selection stable/safely abstains
```

---

# 42. Current-rebound resistance check

If selected hypothesis has a valid/provisional:

```text
W3 high
W4 low
```

and current price is rebounding from W4:

calculate:

```text
0.236
0.382
0.500
0.618
0.786
```

from the selected W3/W4 structure.

Then determine whether any levels overlap:

```text
monthly pivot zone
weekly pivot resistance
daily pivot/rejection
Bollinger
prior high
```

This is the intended "Fibonacci resistance band" validation.

---

# 43. Provisional current-rebound semantics

If W3/W4 are provisional:

Fib values may be calculated as:

```text
PROVISIONAL_STRUCTURAL_REFERENCE
```

but user-visible eligibility remains shadow-only until the later enablement policy decides how provisional zones are displayed.

Do not call them confirmed resistance.

---

# TRACK G — Generalization Regression

# 44. Non-SK benchmark

Use at least:

```text
2 additional KR
3 US/foreign
```

and the full 20-stock monitored replay.

Required structures where available:

```text
old grand-cycle history
clean current-cycle impulse
range-bound
short-history listing
deep correction
no valid impulse
```

---

# 45. Candidate degree audit across universe

For every stock report:

```text
grand-cycle candidate count
current-cycle candidate count
selected degree
abstention reason
```

Hard target:

```text
CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED = 0
```

---

# 46. No-forced-wave regression

Stocks with no valid impulse:

```text
deterministic monthly/weekly/daily SR remains
wave Fib omitted
```

Set:

`NO_FORCED_ELLIOTT = PASS / FAIL`

---

# 47. Long-history SR regression after daily 1200 fix

Repeat the long-history SR impact audit after actual daily 1200 is available.

Compare:

```text
old 1000 / prior data
vs
true 1200 daily
```

Determine whether the extra 200 bars introduce:

```text
new valid historical zones
stale/noisy zones
material support/resistance changes
```

No automatic claim that more history is always better.

---

# 48. Zone density remains controlled

Do not output every long-history level.

Preserve deterministic relevance filters:

```text
structural timeframe
reaction count
recency
role conversion
current distance
independent evidence-family confluence
```

Hard target:

`LONG_HISTORY_ZONE_EXPLOSION = 0`

---

# TRACK H — Tests

# 49. Focused tests — bar completion

Required:

- daily pre-close = PARTIAL
- daily post-close = COMPLETE
- current week before final session = PARTIAL
- completed prior week = COMPLETE
- current month before final session = PARTIAL
- completed prior month = COMPLETE
- partial bar cannot confirm symmetric pivot
- pivot confirmation date requires complete right bars
- partial bar may be current candle context
- provisional endpoint remains provisional

---

# 50. Focused tests — 1200 backfill

Required:

- provider first page 1000 + older page(s) reaches 1200
- duplicate date dedupe
- chronological stitch
- adjustment-basis match
- short listing safe partial
- provider failure fail-closed
- cache initialization
- incremental append
- historical revision handling
- no fake 600W/300M

---

# 51. Focused tests — wave degree

Required:

- grand-cycle candidate creation
- current-cycle candidate creation
- same history can contain both
- magnitude alone cannot suppress current cycle
- no valid current cycle returns explicit state
- candidate packet includes degree
- AI selected degree validates
- degree mismatch rejected

---

# 52. Focused tests — feedback loop

Required:

- valid AI selected ID enters backend calculator
- invalid ID fails closed
- abstention produces no Fib
- selected hypothesis calculates current rebound
- calculated Fib enters confluence
- confluence enters shadow render
- numeric registry complete
- selected-but-not-rendered gap detected
- current user-visible message unchanged

---

# 53. Focused tests — temporal SK hynix control

Add fixture/regression proving:

```text
in-progress August monthly bar
cannot be the second complete right-side confirmation bar
for a June 2/2 pivot.
```

No ticker hard-coding in production logic; fixture may use SK hynix sample.

---

# 54. Full validation

Required:

```text
focused temporal tests PASS
focused backfill tests PASS
focused degree tests PASS
focused feedback-loop tests PASS
SK hynix exact validation complete
reference archive comparison complete
full 20-stock shadow replay PASS/safe
variable AI trial complete
numeric provenance PASS
look-ahead safety PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action unchanged
operationId/schema unchanged
implementation SHA Actions PASS
final main Actions PASS
API /health PASS
worktrees clean
```

---

# 55. Required architecture docs

Create/update:

1. `docs/architecture/OHLCV_BAR_COMPLETION_CONTRACT.md`
2. `docs/architecture/OHLCV_1200_BACKFILL_CACHE.md`
3. `docs/architecture/WAVE_DEGREE_CURRENT_CYCLE.md`
4. `docs/architecture/PRICE_STRUCTURE_V3_AI_FEEDBACK_LOOP.md`
5. update `PRICE_STRUCTURE_WAVE_FIB_V3.md`
6. update `PRIMARY_MONTHLY_WAVE_HYPOTHESIS.md`
7. update `PRICE_STRUCTURE_V3_SHADOW_POLICY.md`

---

# 56. Required reports

Create:

1. `docs/reports/20260826-v3-partial-bar-temporal-root-cause.md`
2. `docs/reports/20260826-v3-bar-completion-contract-validation.md`
3. `docs/reports/20260826-daily-1200-provider-capability-audit.md`
4. `docs/reports/20260826-daily-1200-backfill-validation.md`
5. `docs/reports/20260826-wave-degree-root-cause.md`
6. `docs/reports/20260826-wave-degree-candidate-coverage.md`
7. `docs/reports/20260826-user-reference-engine-availability.md`
8. `docs/reports/20260826-variable-ai-v3-feedback-loop-audit.md`
9. `docs/reports/20260826-sk-hynix-v3-bounded-repair-validation.md`
10. `docs/reports/20260826-v3-generalization-bounded-repair.md`
11. `docs/reports/20260826-v3-long-history-sr-after-1200.md`
12. `docs/reports/20260826-v3-bounded-repair-safety-parity.md`
13. `docs/reports/20260826-v3-bounded-repair-readiness.md`
14. `docs/reports/20260826-v3-bounded-repair-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-v3-bounded-repair-readiness.json`

---

# 57. Readiness gates

Set exactly:

```text
BAR_COMPLETION_TEMPORAL_CONTRACT =
PASS / FAIL

PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION =
0 / NONZERO

PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT =
0 / NONZERO

DAILY_1200 =
PASS / PARTIAL / FAIL

WEEKLY_600 =
PASS / PARTIAL / FAIL

MONTHLY_300 =
PASS / PARTIAL / FAIL

OHLCV_1200_BACKFILL =
PASS / PARTIAL / FAIL

FAKE_HIGHER_TIMEFRAME_COVERAGE =
0 / NONZERO

WAVE_DEGREE_MODEL =
PASS / FAIL

SK_HYNIX_CURRENT_CYCLE_COVERAGE =
PASS / NO_VALID_CANDIDATE / FAIL

CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED =
0 / NONZERO

USER_REFERENCE_ENGINE_AVAILABLE =
YES / NO

REFERENCE_METHOD_COMPARISON =
REFERENCE_MATCH /
DIFFERENT_BUT_DEFENSIBLE /
REFERENCE_TEMPORAL_ISSUE /
THESIS_MONITOR_METHOD_ISSUE /
MATERIAL_METHOD_CONFLICT /
NOT_OBSERVED

VARIABLE_AI_SELECTION_CONNECTED_TO_V3_ENGINE =
YES / NO

SELECTED_BUT_NOT_FED_TO_ENGINE =
0 / NONZERO

CURRENT_REBOUND_FIB =
PASS / NOT_APPLICABLE / FAIL

PRIMARY_CYCLE_FIB =
PASS / NOT_APPLICABLE / FAIL

CROSS_TIMEFRAME_CONFLUENCE_V3 =
PASS / PARTIAL / FAIL

NO_FORCED_ELLIOTT =
PASS / FAIL

LONG_HISTORY_ZONE_EXPLOSION =
0 / NONZERO

UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

LOOKAHEAD_SAFETY =
PASS / FAIL

CURRENT_USER_VISIBLE_MESSAGE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_WAVE_FIB_V3 =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / PARTIAL / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 58. Hard safety targets

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT = 0

ANCHOR_TICKER_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_PRICE_MISMATCH = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

OHLCV_DUPLICATE_DATE = 0
OHLCV_STITCH_BASIS_CONFLICT = 0
FAKE_HIGHER_TIMEFRAME_COVERAGE = 0

MONTHLY_FIB_RELABELED_AS_WEEKLY = 0
MONTHLY_FIB_RELABELED_AS_DAILY = 0

PROVISIONAL_WAVE_AS_CONFIRMED = 0
PROJECTION_AS_CONFIRMED_TARGET = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0

ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED = 0
SELECTED_BUT_NOT_FED_TO_ENGINE = 0
UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

---

# 59. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

BAR_COMPLETION_TEMPORAL_CONTRACT = ...
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = ...
PARTIAL_BAR_PROMOTED_TO_CONFIRMED_ENDPOINT = ...

SK_HYNIX_JUNE_MONTHLY_PIVOT_STATUS_BEFORE = ...
SK_HYNIX_JUNE_MONTHLY_PIVOT_STATUS_AFTER = ...
SK_HYNIX_W3_STATUS = ...
SK_HYNIX_W4_STATUS = ...

DAILY_1200 = ...
WEEKLY_600 = ...
MONTHLY_300 = ...

DAILY_PROVIDER_LIMIT = ...
DAILY_BACKFILL_METHOD = ...
DAILY_1200_LONG_LISTED_PASS_COUNT = ...
DAILY_1200_SHORT_LISTING_PARTIAL_COUNT = ...

OHLCV_1200_BACKFILL = ...
FAKE_HIGHER_TIMEFRAME_COVERAGE = 0

WAVE_DEGREE_MODEL = ...

SK_HYNIX_GRAND_CYCLE_CANDIDATES = ...
SK_HYNIX_CURRENT_CYCLE_CANDIDATES = ...
SK_HYNIX_CURRENT_CYCLE_COVERAGE = ...

CURRENT_CYCLE_CANDIDATE_STARVATION_UNEXPLAINED = 0

USER_REFERENCE_ENGINE_AVAILABLE = ...
REFERENCE_METHOD_COMPARISON = ...

VARIABLE_AI_SELECTION_CONNECTED_TO_V3_ENGINE = ...
SELECTED_BUT_NOT_FED_TO_ENGINE = 0

SK_HYNIX_AI_SELECTED_DEGREE = ...
SK_HYNIX_AI_SELECTED_HYPOTHESIS = ...

CURRENT_REBOUND_FIB = ...
PRIMARY_CYCLE_FIB = ...
CROSS_TIMEFRAME_CONFLUENCE_V3 = ...

SK_HYNIX_EXACT_SHADOW_MESSAGE = ...

NO_FORCED_ELLIOTT = ...
LONG_HISTORY_ZONE_EXPLOSION = 0

KR_SHADOW_REPLAY = .../...
US_SHADOW_REPLAY = .../...

AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0

LOOKAHEAD_LEAK = 0
ANCHOR_TICKER_MISMATCH = 0
ANCHOR_DATE_MISMATCH = 0
ANCHOR_PRICE_MISMATCH = 0

CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0

OHLCV_DUPLICATE_DATE = 0
OHLCV_STITCH_BASIS_CONFLICT = 0

MONTHLY_FIB_RELABELED_AS_WEEKLY = 0
MONTHLY_FIB_RELABELED_AS_DAILY = 0

PROVISIONAL_WAVE_AS_CONFIRMED = 0
PROJECTION_AS_CONFIRMED_TARGET = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0

ARTIFICIAL_CONFLUENCE_BY_WIDE_TOLERANCE = 0
CORRELATED_FIB_STRENGTH_INFLATION = 0

UNSTABLE_FIB_USER_VISIBLE_ELIGIBLE = 0

CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

LOOKAHEAD_SAFETY = ...
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

# 60. Mandatory ZIP

Create:

`20260826-price-structure-v3-temporal-cycle-feedback-bounded-repair-bundle.zip`

Include:
- this exact instruction
- temporal root-cause / validation
- 1200 backfill capability / validation
- degree root-cause / coverage
- reference-engine availability / comparison
- variable-AI feedback-loop audit
- SK hynix exact validation
- full KR/US shadow replay
- long-history SR audit
- safety parity
- readiness
- artifact index

Never include secrets, auth headers, account identifiers, or hidden chain-of-thought.

Compute/report SHA-256.

---

# 61. Severity

## P0

- wrong price/security
- future/look-ahead pivot
- partial bar used as confirmed pivot input in user-visible path
- AI-calculated authoritative price
- wrong adjustment/security basis
- projection shown as guaranteed target
- technicals mutate business investment logic
- shadow leaks into live output
- replay mutates production state
- secret/private data leakage

## P1

- partial weekly/monthly bar can confirm pivots
- daily 1200 requirement remains capped at 1000 without a real backfill path
- long history starves valid current-cycle candidates
- SK hynix current-cycle candidate exists but AI cannot see it
- variable AI selection never feeds deterministic Fib/confluence/render
- reference method conflict remains unexplained when the reference files are available
- selected unstable Fib becomes eligible
- fake 600W/300M coverage
- backfill mixes incompatible adjustment bases

## P2

- short-listed stock lacks 1200/600/300 full history
- some stocks have no valid impulse
- grand-cycle analysis exists but is omitted from short message
- daily Fib omitted because unstable
- user reference archive unavailable after explicit audit
- stylistic message differences

---

# 62. Final principle

The remaining v3 problem is not the Fibonacci formula.

It is ensuring that:

```text
the bars are temporally valid,
the history is actually long enough,
the candidate generator distinguishes current cycle from grand cycle,
and the AI-selected wave actually flows into the deterministic calculator.
```

The repaired system should therefore behave like:

```text
COMPLETE historical bars
+ PARTIAL current candle context

→ long-history monthly/weekly/daily SR

→ GRAND_CYCLE context
+ PRIMARY_CURRENT_CYCLE candidates

→ variable AI selects the meaningful current structure
or safely abstains

→ backend calculates rebound/cycle/projection Fib

→ backend merges real pivot/Bollinger/cross-timeframe evidence

→ exact shadow message
```

For SK hynix specifically, the goal is NOT to hard-code a 2023 W0.

The goal is to prove that if the 2023-era structure is a valid current-cycle hypothesis,
the system can generate it, show it to the AI, compare it against the older grand cycle,
and then calculate the corresponding rebound resistance bands from the actually selected hypothesis.
