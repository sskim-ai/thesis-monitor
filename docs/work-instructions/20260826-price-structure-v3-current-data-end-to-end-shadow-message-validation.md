# thesis-monitor — Price Structure v3 Current-Data End-to-End Shadow Message Validation
## 2026-08-26 KR completed session + latest completed US session
## Collect real test data → run full v3 price structure → generate exact candidate messages → validate before enablement
## Read-only / shadow-only / no live send

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_CURRENT_DATA_E2E_SHADOW_MESSAGE_VALIDATION`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `READ_ONLY_PREENABLEMENT_E2E_VALIDATION`
- Current v3 state: `INTEGRATED_READY_NOT_ARMED`
- Source policy: `FREE_ONLY`
- Production Assist: preserve `OFF`
- User-visible production mutation: `0`
- Telegram send: `0`
- Manual scheduled task execution: `0`
- DB / official assessment mutation: `0`
- Trade AR: preserve `OFF`
- Open Research production integration: preserve `0`
- Public Action / operationId / schema: unchanged

### Required base

Latest reported safe final/main/operating:

`68e927b5eaf2a10dadd5faafa26de9c18b67170f`

Resolve actual latest safe `origin/main` and operating SHA before running this validation.

### Proven preconditions

Previous bounded repair reported:

```text
DETERMINISTIC_SR_BASE_LAYER = PASS
SR_NEAREST_MAJOR_SEPARATION = PASS
SR_PROXIMITY_RELEVANCE_GATE = PASS
NO_WAVE_SR_FALLBACK = PASS

REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
UNEXPECTED_EMPTY_SUPPORT = 0
UNEXPECTED_EMPTY_RESISTANCE = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

SK hynix regression = 0
012450 regression = 0
TSLA unstable Fib reintroduced = 0

KR replay = 7/7
US/foreign replay = 13/13

PRICE_STRUCTURE_V3_SR_COMPLETENESS =
INTEGRATED_READY_NOT_ARMED

PRODUCTION_ENABLEMENT_READY = YES
```

This task is not a new implementation task unless a validation failure proves a bounded defect.

---

# 0. Objective

Before selective production enablement, run the current v3 engine against **today's real safely available data**
and inspect the exact messages users would see.

Required flow:

```text
current approved provider data
→ completed-session temporal gate
→ canonical OHLCV 1200D / 600W / 300M
→ deterministic monthly/weekly/daily SR
→ nearest / major SR
→ family-stable optional Fib
→ optional Fib/SR confluence
→ cross-timeframe relevance gate
→ user-visible price formatting
→ exact shadow message
→ numeric/provenance validation
→ human-readable quality review
```

No live message may be sent in this task.

---

# 1. Session targets — exact

At validation time on 2026-08-26 KST:

## KR securities

Use:

```text
TARGET_SESSION_KR = 2026-08-26
```

only if the regular Korean market session is completed.

Expected at post-close validation time:

```text
2026-08-26 = COMPLETE
```

## US / foreign securities traded on US session

Use the latest completed US regular session.

At 2026-08-26 evening KST, before the 2026-08-26 US session has completed, expected:

```text
TARGET_SESSION_US = 2026-08-25
```

Do NOT use an incomplete 2026-08-26 US daily bar as completed history.

If actual execution occurs after the next US regular close:
resolve the latest completed US session dynamically and document it.

Hard target:

```text
WRONG_SESSION_DATA = 0
PARTIAL_DAILY_BAR_USED_AS_COMPLETE = 0
```

---

# 2. Read-only rule

Do NOT:

- send Telegram
- manually execute production monitoring task
- mutate delivery/receipt state
- record official thesis assessments
- update monitoring versions
- alter stored price rules
- change scheduler configuration
- enable v3 production flag
- enable Production Assist
- commit code solely because a message looks stylistically imperfect

This is evidence collection and shadow rendering.

---

# 3. Test universe

Use the actual current monitored universe.

Expected current universe:

## KR — 7

```text
000660
003690
005490
005930
010120
012450
086280
```

## US / foreign — 13

```text
CORZ
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

If current monitored universe differs:
- use the actual current universe
- report the exact diff
- do not silently omit subjects

---

# 4. Data collection — canonical price history

For every subject collect:

```text
daily requested = 1200
weekly requested = 600
monthly requested = 300
```

Report per timeframe:

```text
requested_count
returned_count
completed_count
used_count

first_date
last_date
last_bar_state

adjustment basis
currency
security identity
provider
provider limit
coverage status
```

Short-listing partial history is valid when all available safe history is used.

Do not pad.

---

# 5. Completed vs partial bars

Keep current partial bars for contextual observation only when the canonical engine supports that safely.

They may NOT:

```text
confirm pivots
confirm wave endpoints
enter completed-bar historical calculations as complete
```

Hard targets:

```text
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0
LOOKAHEAD_LEAK = 0
```

---

# 6. Current price context

For every subject record:

```text
current/latest safe price
price_as_of
currency
security basis
```

The message must not mix:

```text
KRW ordinary share
USD ADR
different share/security basis
```

Hard target:

`SECURITY_BASIS_CONFLICT = 0`

---

# 7. Deterministic monthly / weekly / daily SR

For each subject generate the full structured base layer.

Per timeframe:

```text
CURRENT_ZONE optional

NEAREST_SUPPORT
NEAREST_RESISTANCE

MAJOR_SUPPORT
MAJOR_RESISTANCE

additional eligible zones optional
```

Every zone must retain exact provenance.

---

# 8. Per-timeframe required fields

For every nearest/major zone include:

```text
zone_id
requested_timeframe
source_timeframe
role

raw_low
raw_high
display_low
display_high

distance_pct
proximity tier
structural score
active relevance

source families
source refs

as_of
currency
```

If a local side is unavailable:

```text
NO_CONFIRMED_HISTORICAL_LEVEL
INSUFFICIENT_HISTORY
```

or a proven higher-timeframe fallback with explicit provenance.

No generic unexplained null.

---

# 9. Nearest vs major validation

For every subject verify:

```text
nearest
≠ automatically major
```

When they are the same:
explain why.

When they differ:
the message should preserve the distinction if material.

---

# 10. Cross-timeframe relevance validation

For every subject run the repaired proximity/relevance gate.

Hard target:

```text
REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
```

Audit exact current distance for every final cross-timeframe zone.

If no relevant cross zone:

```text
nearest_cross_timeframe_zone = null
```

and the message falls back to local SR.

---

# 11. Wave/Fibonacci state

For every subject record:

```text
full wave state
selected degree if any
family consensus state

eligible Fib families
omitted unstable Fib families
no-wave/abstention reason
```

Fib is optional.

---

# 12. Fib/SR confluence

For every eligible family determine:

```text
DIRECT_SR_CONFLUENCE
NEAR_SR_CONFLUENCE
FIB_REFERENCE_ONLY
NO_MEANINGFUL_SR_OVERLAP
```

Only safe confluence may enter the candidate message.

Hard targets:

```text
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
FIB_CONFLUENCE_TOLERANCE_WIDENING = 0
```

---

# 13. Message-generation objective

Generate an exact user-facing **candidate price-structure section** for each stock.

This must use the current production message style as the surrounding reference.

Do not redesign the entire investment-review message.

The candidate section should be compact enough for actual monitoring use.

---

# 14. Candidate price-structure message hierarchy

Recommended semantic hierarchy:

```text
📐 가격 구조

• 가까운 지지:
• 가까운 저항:
• 주요 구조적 지지/저항:
• Fib/SR confluence: only if meaningful
```

If monthly/weekly/daily differences are important, include them compactly.

Do not mechanically show all 12 monthly/weekly/daily fields.

---

# 15. Detailed audit view vs user message

The artifact must contain two forms:

## A. Detailed audit

```text
monthly:
  nearest / major support-resistance

weekly:
  nearest / major support-resistance

daily:
  nearest / major support-resistance

Fib families
cross-timeframe confluence
```

## B. Candidate user-visible message

Only the decision-relevant subset.

Do not confuse the detailed audit with the intended live message.

---

# 16. Display formatting

Reuse the proven display-only formatter.

KR high-price example:

```text
raw:
1,869,163.404750–1,915,788.795250

display:
약 186.9만~191.6만원
```

Raw registry values remain unchanged.

Hard target:

`RAW_NUMERIC_CHANGED_BY_RENDERER = 0`

---

# 17. Message numeric-density budget

Count per candidate stock message:

```text
price-structure numeric values
price zones
percentages
technical labels
```

Flag if the price-structure section becomes visually dense.

Create:

```text
MESSAGE_NUMERIC_DENSITY =
GOOD / HIGH / EXCESSIVE
```

Do not reduce useful content merely to hit an arbitrary number.

Human-readable clarity is the target.

---

# 18. Repetition / redundancy

Detect:

```text
same zone repeated as nearest + major + confluence
same numeric range repeated in multiple lines
monthly/weekly/daily identical zone repeated unnecessarily
```

Prefer one line with combined provenance/meaning where appropriate.

Set:

`REDUNDANT_ZONE_REPETITION_COUNT`

---

# 19. Semantic wording safety

Allowed:

```text
가까운 저항
주요 구조적 저항
Fib/SR이 겹치는 구간
현재가 위에서 확인할 구간
```

Avoid:

```text
목표가
손절가
반드시 반등
반드시 저항
매수 구간
매도 구간
```

unless those are separately supported stored price rules, which this v3 renderer must not create.

Hard targets:

```text
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0
```

---

# 20. Current-zone wording

If current price is inside a zone:

say:

```text
현재가가 해당 구간 안에 있음
```

not:

```text
현재 지지선 아래/위
```

unless the deterministic boundary relation supports it.

---

# 21. Mandatory controls — exact review

## 000660 SK hynix

Verify current-data output preserves the expected architecture:

```text
nearest tactical resistance
vs
major structural / Fib-SR resistance
```

The previous safe reference band was approximately:

```text
1.869M–1.916M KRW
```

Do NOT force the same band if current 2026-08-26 data legitimately changes it.

Report source-backed difference.

---

# 22. 010120 LS ELECTRIC

Verify:

```text
remote old 50k-range cross zone
is not promoted as nearest
```

The candidate message should use current-relevant local SR.

---

# 23. MU

Verify:

```text
old $60–$90 historical zones
do not outrank current $900-range local SR
```

Use today's current-data calculation, not hard-coded values.

---

# 24. TSM

Verify remote historical cross zones remain non-primary.

Preserve TSM W3 dependency-family safety.

---

# 25. SNDK

Mandatory no-wave control.

Expected behavior:

```text
no valid/stable wave
→ useful deterministic SR message
→ no fabricated Fib
```

---

# 26. 003690 and HUT

Confirm previously repaired daily resistance remains available or safely explained from today's data.

No unexplained regression.

---

# 27. SKHY

Short-history control.

Do not fabricate monthly structure.

Weekly/daily SR should remain usable where supported.

---

# 28. 012450

Preserve the corrected stable family consensus from the micro-repair.

No diagnostic-alternative contamination.

---

# 29. TSLA

Preserve true conflict safety:

```text
unstable Fib omitted
deterministic SR still useful
```

No false stabilization.

---

# 30. Full 20-stock exact message archive

For each stock store:

```text
ticker
company name
market
target session
current price/as-of

detailed SR audit
wave/Fib audit

candidate price-structure section
full candidate monitoring message with section inserted

baseline production message
candidate message

exact diff
```

No live delivery.

---

# 31. Baseline vs candidate comparison

The purpose is to see what production would change.

For every stock calculate:

```text
line count delta
character count delta
numeric token delta

new technical facts
removed technical facts
business/fundamental text changed?
```

Required:

```text
BUSINESS_TEXT_CHANGED_BY_PRICE_STRUCTURE = 0
```

The only expected candidate change is the bounded price-structure rendering surface.

---

# 32. User-visible usefulness review

Human-review every candidate:

```text
Does it tell me the nearest downside structure?
Does it tell me the nearest upside barrier?
Does it distinguish a farther major barrier when useful?
Does it avoid meaningless old levels?
Does Fib add anything?
Is the message too long?
```

Classify:

```text
MATERIAL_IMPROVEMENT
MINOR_IMPROVEMENT
NO_ADDED_VALUE
WORSE
```

Required for enablement:

`WORSE = 0`

---

# 33. Message-level enablement eligibility

Per stock assign:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT_PRICE_STRUCTURE
BLOCKED
```

Suggested semantics:

## ELIGIBLE

```text
nearest/major SR useful
optional Fib confluence safe
message readable
```

## ELIGIBLE_SR_ONLY

```text
deterministic SR useful
Fib absent/unstable/not useful
```

## OMIT_PRICE_STRUCTURE

```text
data too sparse to add useful value
```

## BLOCKED

```text
numeric/provenance/safety defect
```

Do not use a global all-or-nothing decision.

---

# 34. Market-level rollout summary

Count:

```text
KR:
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT
BLOCKED

US/foreign:
same
```

This becomes the input to the next selective-enablement task.

---

# 35. Production rollout recommendation

This validation may recommend:

```text
ENABLE_SELECTIVELY
KEEP_SHADOW
BOUNDED_REPAIR
```

It may NOT actually enable.

---

# 36. Data-freshness audit

Per message validate:

```text
price_as_of
OHLCV completed session
SR as_of
wave as_of
Fib as_of
```

No mixed-session technical block.

Hard target:

`MIXED_SESSION_PRICE_STRUCTURE = 0`

---

# 37. Corporate-action / basis audit

Hard targets:

```text
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0
```

---

# 38. Numeric registry audit

Every candidate message technical number must bind to a registry entry.

Hard targets:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
```

---

# 39. Full safety parity

Hard targets:

```text
LOOKAHEAD_LEAK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
PROVISIONAL_WAVE_AS_CONFIRMED = 0

REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0
BUSINESS_TEXT_CHANGED_BY_PRICE_STRUCTURE = 0

TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
```

---

# 40. No accidental natural-production interaction

If a natural scheduled monitoring run occurs while this validation runs:

do not alter it.

The test run must have its own immutable:

```text
TEST_RUN_ID
TEST_DATASET_ID
TEST_RENDER_ID
```

No production claim/delivery ownership.

---

# 41. Required reports

Create:

1. `docs/reports/20260826-v3-current-data-session-audit.md`
2. `docs/reports/20260826-v3-current-data-ohlcv-coverage.md`
3. `docs/reports/20260826-v3-current-data-sr-audit.md`
4. `docs/reports/20260826-v3-current-data-wave-fib-audit.md`
5. `docs/reports/20260826-v3-current-data-confluence-audit.md`
6. `docs/reports/20260826-v3-current-data-message-generation.md`
7. `docs/reports/20260826-v3-current-data-message-diff.md`
8. `docs/reports/20260826-v3-current-data-message-quality.md`
9. `docs/reports/20260826-v3-current-data-control-stocks.md`
10. `docs/reports/20260826-v3-current-data-full-universe.md`
11. `docs/reports/20260826-v3-current-data-safety-parity.md`
12. `docs/reports/20260826-v3-current-data-enablement-readiness.md`
13. `docs/reports/20260826-v3-current-data-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-v3-current-data-enablement-readiness.json`

---

# 42. Required exact message artifact

Create:

`docs/reports/20260826-v3-current-data-exact-candidate-messages.json`

For every stock include:

```text
baseline_message
candidate_message
candidate_price_structure_section
exact_diff
eligibility
quality classification
```

This is mandatory.

---

# 43. Required compact human review report

Create:

`docs/reports/20260826-v3-current-data-message-review-table.md`

Columns:

```text
Ticker
Current price
Nearest support
Nearest resistance
Major support
Major resistance
Fib/SR confluence
Wave state
Message eligibility
Quality
Primary reason
```

---

# 44. Gates

Set exactly:

```text
CURRENT_DATA_COLLECTION =
PASS / PARTIAL / FAIL

TARGET_SESSION_KR =
YYYY-MM-DD

TARGET_SESSION_US =
YYYY-MM-DD

COMPLETED_SESSION_SAFETY =
PASS / FAIL

OHLCV_1200_600_300 =
PASS / PARTIAL / FAIL

DETERMINISTIC_SR_CURRENT_DATA =
PASS / PARTIAL / FAIL

NEAREST_MAJOR_CURRENT_DATA =
PASS / FAIL

CROSS_TIMEFRAME_RELEVANCE_CURRENT_DATA =
PASS / FAIL

NO_WAVE_SR_CURRENT_DATA =
PASS / FAIL

FAMILY_STABLE_FIB_CURRENT_DATA =
PASS / PARTIAL / FAIL

FIB_SR_CONFLUENCE_CURRENT_DATA =
PASS / PARTIAL / NOT_MATERIAL

EXACT_CANDIDATE_MESSAGE_GENERATION =
PASS / FAIL

FULL_UNIVERSE_MESSAGE_COUNT =
integer

KR_MESSAGE_ELIGIBLE =
integer

KR_MESSAGE_ELIGIBLE_SR_ONLY =
integer

KR_MESSAGE_OMIT =
integer

KR_MESSAGE_BLOCKED =
integer

US_MESSAGE_ELIGIBLE =
integer

US_MESSAGE_ELIGIBLE_SR_ONLY =
integer

US_MESSAGE_OMIT =
integer

US_MESSAGE_BLOCKED =
integer

MATERIAL_IMPROVEMENT =
integer

MINOR_IMPROVEMENT =
integer

NO_ADDED_VALUE =
integer

WORSE =
integer

MESSAGE_NUMERIC_DENSITY =
PASS / PARTIAL / FAIL

REDUNDANT_ZONE_REPETITION =
PASS / PARTIAL / FAIL

BUSINESS_TEXT_CHANGED_BY_PRICE_STRUCTURE =
0 / NONZERO

WRONG_SESSION_DATA =
0 / NONZERO

MIXED_SESSION_PRICE_STRUCTURE =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAREST =
0 / NONZERO

FABRICATED_SR_FILL =
0 / NONZERO

FALLBACK_TIMEFRAME_RELABEL =
0 / NONZERO

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE =
0 / NONZERO

UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE =
0 / NONZERO

UNREGISTERED_PRICE_STRUCTURE_NUMERIC =
0 / NONZERO

NUMBERS_WITHOUT_PROVENANCE =
0 / NONZERO

CURRENT_RUNTIME_VISIBLE_DIFF =
0 / NONZERO

PREENABLEMENT_CURRENT_DATA_VALIDATION =
PASS / PARTIAL / FAIL

PRODUCTION_ENABLEMENT_RECOMMENDATION =
ENABLE_SELECTIVELY /
KEEP_SHADOW /
BOUNDED_REPAIR
```

---

# 45. Mandatory control gates

```text
SK_HYNIX_CURRENT_DATA =
PASS / FAIL

LS_ELECTRIC_CURRENT_DATA =
PASS / FAIL

MU_CURRENT_DATA =
PASS / FAIL

TSM_CURRENT_DATA =
PASS / FAIL

SNDK_NO_WAVE_CURRENT_DATA =
PASS / FAIL

003690_CURRENT_DATA =
PASS / FAIL

HUT_CURRENT_DATA =
PASS / FAIL

SKHY_SHORT_HISTORY_CURRENT_DATA =
PASS / FAIL

012450_CURRENT_DATA =
PASS / FAIL

TSLA_TRUE_CONFLICT_CURRENT_DATA =
PASS / FAIL
```

---

# 46. Readiness

Recommend:

```text
PRODUCTION_ENABLEMENT_RECOMMENDATION =
ENABLE_SELECTIVELY
```

only if:

```text
all hard safety counters = 0

all 10 mandatory controls PASS

WORSE = 0

BLOCKED = 0
or each blocked subject is safely omitted and reason is structural/data insufficiency

business text changed = 0

message numeric density acceptable

exact candidate messages human-readable

P0 = 0
material P1 = 0
```

---

# 47. Expected next action

If PASS:

```text
NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT
```

If quality is safe but too verbose:

```text
NEXT_ACTION =
BOUNDED_RENDERER_DENSITY_REPAIR
```

If correctness fails:

```text
NEXT_ACTION =
BOUNDED_REPAIR
```

---

# 48. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

TEST_RUN_ID = ...
TEST_DATASET_ID = ...
TEST_RENDER_ID = ...

TARGET_SESSION_KR = ...
TARGET_SESSION_US = ...

CURRENT_DATA_COLLECTION = ...
COMPLETED_SESSION_SAFETY = ...
OHLCV_1200_600_300 = ...

DETERMINISTIC_SR_CURRENT_DATA = ...
NEAREST_MAJOR_CURRENT_DATA = ...
CROSS_TIMEFRAME_RELEVANCE_CURRENT_DATA = ...
NO_WAVE_SR_CURRENT_DATA = ...

FAMILY_STABLE_FIB_CURRENT_DATA = ...
FIB_SR_CONFLUENCE_CURRENT_DATA = ...

SK_HYNIX_CURRENT_DATA = ...
SK_HYNIX_CURRENT_PRICE = ...
SK_HYNIX_NEAREST_SUPPORT = ...
SK_HYNIX_NEAREST_RESISTANCE = ...
SK_HYNIX_MAJOR_SUPPORT = ...
SK_HYNIX_MAJOR_RESISTANCE = ...
SK_HYNIX_FIB_SR_CONFLUENCE = ...

LS_ELECTRIC_CURRENT_DATA = ...
MU_CURRENT_DATA = ...
TSM_CURRENT_DATA = ...
SNDK_NO_WAVE_CURRENT_DATA = ...
003690_CURRENT_DATA = ...
HUT_CURRENT_DATA = ...
SKHY_SHORT_HISTORY_CURRENT_DATA = ...
012450_CURRENT_DATA = ...
TSLA_TRUE_CONFLICT_CURRENT_DATA = ...

FULL_UNIVERSE_MESSAGE_COUNT = ...

KR_MESSAGE_ELIGIBLE = ...
KR_MESSAGE_ELIGIBLE_SR_ONLY = ...
KR_MESSAGE_OMIT = ...
KR_MESSAGE_BLOCKED = ...

US_MESSAGE_ELIGIBLE = ...
US_MESSAGE_ELIGIBLE_SR_ONLY = ...
US_MESSAGE_OMIT = ...
US_MESSAGE_BLOCKED = ...

MATERIAL_IMPROVEMENT = ...
MINOR_IMPROVEMENT = ...
NO_ADDED_VALUE = ...
WORSE = ...

MESSAGE_NUMERIC_DENSITY = ...
REDUNDANT_ZONE_REPETITION = ...

WRONG_SESSION_DATA = 0
MIXED_SESSION_PRICE_STRUCTURE = 0

REMOTE_ZONE_PROMOTED_AS_NEAREST = 0
FABRICATED_SR_FILL = 0
FALLBACK_TIMEFRAME_RELABEL = 0

UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0

AI_CALCULATED_TECHNICAL_PRICE = 0
AI_SELECTED_AUTHORITATIVE_SR = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0

LOOKAHEAD_LEAK = 0
CORPORATE_ACTION_BASIS_CONFLICT = 0
SECURITY_BASIS_CONFLICT = 0
CURRENCY_MISMATCH = 0

BUSINESS_THESIS_MUTATION_FROM_TECHNICALS = 0
BUSINESS_TEXT_CHANGED_BY_PRICE_STRUCTURE = 0

CURRENT_RUNTIME_VISIBLE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

PREENABLEMENT_CURRENT_DATA_VALIDATION = ...
PRODUCTION_ENABLEMENT_RECOMMENDATION = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

EXACT_MESSAGE_ARTIFACT = ...
REVIEW_TABLE = ...

ZIP = ...
ZIP_SHA256 = ...
```

---

# 49. Mandatory completion ZIP

Create:

`20260826-price-structure-v3-current-data-end-to-end-shadow-message-validation-bundle.zip`

Include:

- exact instruction
- current-session data audit
- OHLCV coverage
- full SR audit
- wave/Fib audit
- confluence audit
- exact 20 candidate messages
- baseline/candidate diffs
- message review table
- control-stock report
- safety parity
- enablement readiness
- artifact index

Do not include:
- secrets
- auth headers
- account IDs
- hidden chain-of-thought

Compute/report SHA-256.

---

# 50. Final principle

Do not enable based on unit tests alone.

Before production:

```text
use real current completed-session data
generate the exact message
read the exact message
verify every number
verify the message is useful
```

The desired live behavior is:

```text
nearest SR first
major structural SR second
Fib only when it genuinely adds confluence
no wave = normal SR-only analysis
no remote historical zone promoted as current
no unsupported target/stop
```

If the real-data message passes that test across the current universe,
then proceed to bounded selective production enablement.
