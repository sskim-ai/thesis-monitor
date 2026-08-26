# thesis-monitor — Price Structure v3 Renderer Integration Micro Repair
## Fib Confluence Range Preservation + Current SR vs Stored Price Rules + Legacy Technical Prose Suppression
## Final message-layer cleanup before bounded selective enablement
## No calculation-engine redesign; no live enablement in this task

## Metadata

- Workstream: `PRICE_STRUCTURE_V3_RENDERER_INTEGRATION_MICRO_REPAIR`
- Instruction version: `1.0`
- Date: `2026-08-26 KST`
- Repository: `sskim-ai/thesis-monitor`
- Task type: `BOUNDED_RENDERER_MICRO_REPAIR`
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

`bb4e5b0772f56b22ac49cb1c2bf72287391b8b19`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

### Current-data pre-enablement validation

```text
Instruction:
688c17280a10e91214d4bd9888522fdc6f9bc0c5

Implementation:
ef586c3816ff76417d2620636975d054935533d4

Final/main/operating:
bb4e5b0772f56b22ac49cb1c2bf72287391b8b19

TARGET_SESSION_KR = 2026-08-26
TARGET_SESSION_US = 2026-08-25

KR:
ELIGIBLE = 6
ELIGIBLE_SR_ONLY = 1

US/foreign:
ELIGIBLE = 4
ELIGIBLE_SR_ONLY = 9

FULL_UNIVERSE_MESSAGE_COUNT = 20

MATERIAL_IMPROVEMENT = 16
MINOR_IMPROVEMENT = 4
WORSE = 0

PREENABLEMENT_CURRENT_DATA_VALIDATION = PASS
PRODUCTION_ENABLEMENT_RECOMMENDATION = ENABLE_SELECTIVELY
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

This task exists because the **calculation engine passed**, but exact candidate-message review exposed
three bounded renderer-integration issues.

---

# 0. Scope — exactly three repair surfaces

Repair only:

```text
A. Fib/SR confluence range preservation in user-visible text

B. clear role separation:
   current deterministic price structure
   vs
   pre-existing stored holder/management price rules

C. suppression / replacement of stale legacy technical prose
   when the new current-session v3 price-structure block is active
```

Do NOT reopen:

```text
OHLCV 1200/600/300
bar-completion temporal contract
pivot detection
wave-degree logic
family consensus
SR nearest/major calculation
cross-timeframe proximity
Fib formulas
confluence eligibility
numeric registry
```

unless an exact renderer test proves a direct integration defect.

---

# 1. Repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-price-structure-v3-renderer-integration-micro-repair.md`

Then:

1. `git fetch origin`
2. verify clean worktree
3. resolve actual latest safe main/operating SHA
4. commit this exact instruction docs-only
5. create branch:

`codex/price-structure-v3-renderer-integration-micro-repair`

6. use latest safe main as base
7. no force push/history rewrite
8. remain shadow-only
9. no live enablement in this task

---

# 2. Hard prohibitions

Do NOT:

- change any backend SR/Fib raw numeric
- change SR nearest/major ranking
- change family eligibility
- change confluence tolerance
- widen Fib range
- shrink Fib range merely for concise prose
- change stored confirmation/warning/invalidation prices
- rewrite stored holder rules as current technical SR
- delete stored price-rule history from persistence
- call a current SR zone a stored price rule
- call a stored rule a current SR zone
- show stale legacy technical prose beside current-session v3 as if both were current
- invent current RSI/MACD values
- regenerate missing indicators from raw prices in the renderer
- change business/fundamental text
- create targets/stops
- enable production in this task
- send Telegram
- manually execute scheduled tasks
- mutate DB / official assessment

---

# TRACK A — Fib/SR Confluence Range Preservation

# 3. Root cause to audit

Current candidate-message review shows a case where:

```text
major structural resistance
and
Fib/SR confluence
```

overlap but are **not identical ranges**.

The renderer currently may collapse this to wording like:

```text
Fib/SR: 위 구조 구간과 겹쳐 보조 확인 근거로만 봅니다.
```

without displaying the extra part of the confluence range.

This can lose material price information.

---

# 4. Mandatory SK hynix control

Current-data candidate example:

```text
000660 SK hynix

near support:
approx 1.564M–1.591M KRW

near resistance:
approx 1.806M–1.816M KRW

major structural resistance:
approx 1.869M–1.879M KRW

safe Fib/SR confluence:
approx 1.869M–1.916M KRW
```

The current short renderer effectively says:

```text
major structure: 1.869M–1.879M
Fib/SR: overlaps above structure
```

This hides approximately:

```text
1.879M–1.916M
```

of safe confluence information.

Do NOT hard-code these prices.

Use frozen/current evidence to prove the issue.

---

# 5. Confluence rendering rule

When Fib/SR confluence is user-visible eligible:

## Case A — effectively identical range

If the Fib/SR confluence range and already-rendered structural range are
the same under the existing display-equivalence policy:

Allowed:

```text
Fib/SR: 같은 구조 구간에 겹칩니다.
```

Numeric repetition may be suppressed.

## Case B — partial overlap but material extension

If Fib/SR:

```text
overlaps
but extends materially above/below the already-rendered SR range
```

the renderer MUST preserve the confluence range.

Example semantic form:

```text
• 주요 구조적 저항: 약 A~B
• Fib/SR confluence: 약 A~C
```

or a compact combined form that preserves both boundaries.

## Case C — distinct nearby confluence

Render separately.

## Case D — Fib reference only / no meaningful SR overlap

Do not promote it into the short current-price block.

---

# 6. Material extension policy

Create deterministic:

`CONFLUENCE_RENDER_EQUIVALENCE_POLICY`

It must decide:

```text
IDENTICAL_DISPLAY_RANGE
MATERIAL_RANGE_EXTENSION
DISTINCT_RANGE
```

Inputs may include:

```text
raw overlap
display-rounded boundaries
zone width
price magnitude
```

Do not use arbitrary text-generation judgment.

Hard targets:

```text
MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0
REDUNDANT_IDENTICAL_FIB_RANGE_REPEATED = 0
```

---

# 7. Raw-range ownership

The renderer may only choose how to display already-registered values.

Hard target:

`RAW_FIB_OR_SR_VALUE_CHANGED_BY_RENDERER = 0`

---

# 8. Confluence label

Use a concise label such as:

```text
Fib/SR 겹침
Fib/SR 구조대
피보나치·SR 겹침
```

Do not imply certainty.

Keep semantics:

```text
보조 확인 근거
구조적 겹침
```

not:

```text
목표
반전 확정
매도대
```

---

# TRACK B — Current Price Structure vs Stored Price Rules

# 9. Root cause

Current US candidate messages can contain both:

```text
new v3 current OHLCV-derived price structure
```

and:

```text
existing stored holder price rules
```

in close proximity.

Both can contain ranges called "지지", which can look contradictory even though their ownership
and purpose are different.

---

# 10. Mandatory SNDK control

Current candidate example:

```text
current v3 nearest support:
approx $1,407.57–$1,420.10

existing stored holder dynamic support:
$950.35–$1,046.03

stored chart invalidation:
$874.30
```

These are not the same object.

Required renderer semantics:

```text
current v3 SR
= current OHLCV-derived market structure

stored rule
= pre-existing holder / monitoring management rule
```

Do not collapse them.

---

# 11. Canonical ownership taxonomy

Every price-bearing user-visible item in the message must have one owner:

```text
CURRENT_PRICE_STRUCTURE
STORED_MONITORING_PRICE_RULE
VALUATION
OTHER
```

For this task audit the first two.

---

# 12. Current price structure

Use section heading:

```text
📐 현재 가격 구조
```

or equivalent explicit wording.

This section owns:

```text
nearest support
nearest resistance
major structural support
major structural resistance
safe Fib/SR confluence
```

It must not own:

```text
stored warning price
stored invalidation price
old confirmation line
stored holder support rule
```

---

# 13. Stored monitoring rules

If existing stored price rules are shown, label them explicitly.

Preferred semantic heading:

```text
🧭 기존 등록 가격 규칙
```

or:

```text
보유 관리용 기존 등록 규칙
```

Fields may include:

```text
기존 확인선
기존 경고 가격
기존 무효화 가격
기존 등록 지지 규칙
```

Do not call them simply:

```text
현재 지지
현재 저항
```

---

# 14. Stored rule persistence remains unchanged

This task changes **rendering/labeling only**.

Do NOT mutate:

```text
monitorStock price rules
stored confirmation
stored support
stored warning
stored invalidation
rule history
```

Hard target:

`STORED_PRICE_RULE_DATA_MUTATION = 0`

---

# 15. Holder meaning

The renderer may explain:

```text
현재 구조상 지지
```

and:

```text
기존 등록 관리 규칙
```

as two different decision layers.

Do not say one automatically supersedes the other.

Example:

```text
현재 가격구조는 $1,408~$1,420 부근을 가까운 지지로 봅니다.
기존 등록 관리 규칙의 지지·무효화 기준은 별도입니다.
```

Do not force this exact prose.

---

# 16. Current/stored conflict audit

Create:

`CURRENT_SR_STORED_RULE_SEPARATION_AUDIT`

For every stock where both are present, report:

```text
current nearest support
current nearest resistance
stored support
stored confirmation
stored warning
stored invalidation

same/overlap/different
display labels
user-confusion risk
```

Hard target:

`UNLABELED_CURRENT_STORED_PRICE_CONFLICT = 0`

---

# 17. Mandatory US controls

At minimum audit:

```text
SNDK
MU
TSM
GOOGL
IBM
HUT
WULF
CORZ
CRCL
RXRX
TSLA
```

where stored holder/price rules may coexist with current v3.

---

# 18. MU control

Current candidate contains:

```text
v3 current:
near support approx $900–$915
near resistance approx $949–$954

stored:
invalidation $835.70
dynamic support $868.39–$914.93
confirmation $950
```

The proximity between current SR and stored rules is useful but ownership must remain explicit.

The renderer may note overlap but must not merge the source ownership.

---

# 19. TSM control

Current candidate contains:

```text
v3 current:
near support approx $414–$416
near resistance approx $425–$427

stored:
invalidation $374.08
dynamic support $380.77–$390.31
confirmation $432
```

Do not make the stored $432 confirmation line appear to be the same as the new nearest resistance.

---

# 20. Stored rule section density

When stored rules are present:

do not automatically repeat all historical rule details.

Prioritize:

```text
active confirmation
active warning
active invalidation
active stored support
```

according to existing production policy.

Preserve existing behavior unless density review proves a safe renderer-only simplification.

No persistence deletion.

---

# TRACK C — Legacy Technical Prose Suppression / Replacement

# 21. Root cause

Some current candidate messages retain older free-form technical prose in fundamental/core text,
while also adding the new current-session v3 price-structure block.

Example from MU current candidate:

```text
2026-08-12 OHLCV 기준 ...
월봉·주봉 ...
주봉 MACD ...
일봉 MACD histogram ...
```

while the new v3 structure is based on:

```text
2026-08-25 US completed session
```

Even if the new structured price block itself is session-safe, this can make the full message look
like it contains two simultaneous technical-analysis systems.

---

# 22. Legacy technical narrative definition

Classify existing prose as `LEGACY_TECHNICAL_PROSE` when it contains price/indicator analysis such as:

```text
dated OHLCV regime statements
RSI
MACD
MACD histogram
Bollinger technical interpretation
old trend-state narrative
legacy support/resistance prose
old technical comparisons between tickers
```

and is not part of the current v3 structured price block.

Do NOT classify business/earnings/valuation prose as legacy technical prose.

---

# 23. Suppression rule

When:

```text
v3 current price-structure section is active and eligible
```

then stale or redundant `LEGACY_TECHNICAL_PROSE` should not appear as a parallel current technical
assessment.

Preferred behavior:

```text
remove legacy technical sentence from current message renderer
```

or:

```text
replace it with current v3 structured interpretation
```

only if the replacement is backend-supported.

Do not update old technical prose by AI arithmetic.

---

# 24. Freshness rule

A legacy technical statement may remain only if:

```text
its as_of matches the current price-structure session
AND
its indicator facts are still canonically available
AND
it adds information not already represented by v3
```

Otherwise suppress.

Hard target:

`STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0`

---

# 25. Mandatory MU control

Before:

```text
core thesis sentence contains 2026-08-12 OHLCV / MACD narrative
+
2026-08-25 current v3 SR block
```

After:

```text
business investment logic remains intact
current v3 price structure owns the technical interpretation
stale 2026-08-12 technical prose is absent
```

Hard target:

`MU_LEGACY_TECHNICAL_DUPLICATION = 0`

---

# 26. Legacy prose audit across full universe

Search all 20 candidate messages for:

```text
OHLCV
RSI
MACD
Bollinger
지지선
저항선
상승 레짐
하락 레짐
기술적
차트 구조
```

Classify every occurrence:

```text
CURRENT_V3
STORED_PRICE_RULE
VALID_NONREDUNDANT_LEGACY
STALE_OR_REDUNDANT_LEGACY
```

Hard target:

`UNCLASSIFIED_TECHNICAL_PRICE_PROSE = 0`

---

# 27. No business-thesis rewrite

If legacy technical text is embedded inside a core/business paragraph:

remove only the technical clause/sentence.

Do not change the underlying business claim.

Hard targets:

```text
BUSINESS_FACT_CHANGED_BY_RENDERER_REPAIR = 0
BUSINESS_THESIS_CHANGED_BY_RENDERER_REPAIR = 0
```

---

# TRACK D — Unified Message Composition

# 28. Final composition ownership

Candidate stock message should have a clean semantic order.

Recommended:

```text
🏢 Company

투자 논리 / 구조적 위험 / 시장 기대

🎯 핵심
📈 사업·실적
👁 핵심 감시

💰 현재 가격

📐 현재 가격 구조
• 가까운 지지
• 가까운 저항
• 주요 구조
• Fib/SR 겹침 — when material

🧭 기존 등록 가격 규칙 — only if present
• 확인 / 경고 / 무효화 / 기존 등록 지지

📐 Valuation
📌 다음 확인
```

Do not mechanically add absent sections.

---

# 29. Current-price line

If the surrounding message already has:

```text
💰 가격
현재가 ...
```

the v3 section does not need to repeat the current price unless the market-specific current style
requires it.

KR Pilot currently may show a `기준 종가` in the v3 block.

Audit for unnecessary repetition but do not change unrelated stable production style unless needed.

---

# 30. Fib line visibility

Candidate message must show a Fib/SR line only when:

```text
safe family eligible
AND
confluence meaningful
AND
the line adds information
```

If identical to major structure:
one compact label may suffice.

If materially extends the range:
show range.

If not material:
omit.

---

# 31. SR-only message

For `ELIGIBLE_SR_ONLY` stocks:

```text
do not show an empty Fib line
```

No:

```text
Fib/SR: 없음
```

unless user-facing policy explicitly benefits from stating the absence.

Silence is preferred.

---

# 32. No-wave message

For no-wave stocks such as SNDK:

```text
current SR section remains complete
wave/Fib terminology does not need to appear
```

Do not tell the user "Elliott wave failed".

---

# 33. Candidate message density

Current validation already found:

```text
MESSAGE_NUMERIC_DENSITY = PASS
REDUNDANT_ZONE_REPETITION = PASS
```

Preserve that.

The renderer repair must not increase overall density materially.

Set:

```text
MESSAGE_NUMERIC_DENSITY_AFTER =
PASS / PARTIAL / FAIL
```

---

# 34. Exact before/after controls

Create exact before/after candidate messages for:

```text
000660 SK hynix
SNDK
MU
TSM
TSLA
012450
```

Mandatory comparisons:

## SK hynix
Fib confluence material extension preserved.

## SNDK
current SR and stored rules clearly separated.

## MU
stale 2026-08-12 legacy technical prose removed/suppressed.

## TSM
current resistance and stored confirmation clearly distinguished.

## TSLA
SR-only remains; no unstable Fib reintroduced.

## 012450
stable family/Fib behavior remains intact.

---

# 35. Full 20-stock current-data replay

Use the same safe session policy:

```text
KR = 2026-08-26 completed session
US = latest completed safe US session
```

If execution date/session advances:
resolve latest completed session dynamically and document.

Do not use partial daily bars as complete.

---

# 36. Message-level exact diff

For all 20 produce:

```text
before candidate
after repaired candidate
exact diff

business text diff
valuation text diff
price-structure diff
stored-rule label diff
legacy-technical diff
```

Only intended message-layer surfaces may change.

---

# 37. Regression: current-data eligibility

Preserve prior safe rollout cohort unless the renderer reveals a true blocker.

Baseline:

```text
KR:
ELIGIBLE 6
ELIGIBLE_SR_ONLY 1
OMIT 0
BLOCKED 0

US:
ELIGIBLE 4
ELIGIBLE_SR_ONLY 9
OMIT 0
BLOCKED 0
```

Hard target:

`MESSAGE_ELIGIBILITY_REGRESSION = 0`

unless a new real safety defect is found.

---

# 38. Renderer-specific quality review

Human-review all 20:

```text
Can I distinguish current market structure from old monitoring rules?

If Fib matters, do I know its actual price band?

If Fib does not matter, is it absent?

Is there only one current technical-analysis narrative?

Do stale MACD/RSI/OHLCV sentences remain?

Are the nearest/major ranges readable?

Is the message longer only when useful?
```

Classify:

```text
MATERIAL_IMPROVEMENT
MINOR_IMPROVEMENT
NO_ADDED_VALUE
WORSE
```

Required:

`WORSE = 0`

---

# 39. Numeric provenance

Every displayed v3 number remains bound to existing registry.

Every stored rule number remains bound to the stored-rule registry/contract.

Hard targets:

```text
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
UNREGISTERED_STORED_PRICE_RULE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
```

---

# 40. Source-ownership safety

Hard targets:

```text
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
FIB_RENDERED_AS_STORED_RULE = 0
```

---

# 41. Technical semantics safety

Hard targets:

```text
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
FIBONACCI_AS_CERTAIN_REVERSAL = 0
STORED_INVALIDATION_RELABELED_AS_FUNDAMENTAL_KILL = 0
```

---

# 42. Calculation-engine parity

Hard targets:

```text
RAW_SR_VALUE_CHANGED = 0
RAW_FIB_VALUE_CHANGED = 0
SR_ELIGIBILITY_CHANGED_BY_RENDERER = 0
FIB_FAMILY_ELIGIBILITY_CHANGED_BY_RENDERER = 0
CROSS_TIMEFRAME_RANKING_CHANGED_BY_RENDERER = 0
```

---

# 43. Temporal safety

Hard targets:

```text
WRONG_SESSION_DATA = 0
MIXED_SESSION_V3_BLOCK = 0
PARTIAL_BAR_USED_FOR_PIVOT_CONFIRMATION = 0
LOOKAHEAD_LEAK = 0
```

A legacy technical sentence with an older date is not automatically a calculation error, but if it
appears as parallel current technical guidance it must be suppressed under Track C.

---

# 44. Production isolation

Hard targets:

```text
CURRENT_RUNTIME_VISIBLE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
STORED_PRICE_RULE_DATA_MUTATION = 0
```

No production flag changes.

---

# 45. Focused tests — Fib rendering

Required:

- identical SR/Fib range → no redundant numeric repetition
- partial overlap + material Fib extension → Fib range shown
- distinct nearby Fib/SR → separate safe line
- Fib reference only → omitted from short current block
- SR-only stock → no empty Fib line
- raw Fib values unchanged

---

# 46. Focused tests — current vs stored rule ownership

Required:

- current SR + distant stored support → separate headings/labels
- overlapping current SR + stored support → retain separate ownership
- stored confirmation near current resistance → not merged
- stored invalidation → remains stored management rule
- stored-rule numeric unchanged
- no persistence mutation

---

# 47. Focused tests — legacy technical suppression

Required:

- old dated OHLCV technical sentence + active v3 → legacy sentence suppressed
- stale MACD sentence + active v3 → suppressed
- current-session valid nonredundant indicator statement → may remain if canonical
- business clause beside legacy technical clause → business clause preserved
- no AI-generated replacement indicator values

---

# 48. Focused tests — exact controls

Required fixtures/replay:

```text
000660
SNDK
MU
TSM
TSLA
012450
```

---

# 49. Full validation

Required:

```text
focused renderer tests PASS
20/20 current-data candidate messages generated
all numeric provenance PASS
all ownership semantics PASS
legacy technical audit complete
message quality review complete

full pytest PASS
Ruff PASS
git diff --check PASS
Knowledge / Chart Knowledge consistency PASS
Public Action unchanged
operation IDs unchanged
implementation SHA Actions PASS
final main Actions PASS
API /health PASS
worktrees clean
```

---

# 50. Required architecture / policy docs

Create/update:

1. `docs/architecture/PRICE_STRUCTURE_V3_RENDERER_OWNERSHIP.md`
2. `docs/architecture/FIB_CONFLUENCE_RENDER_EQUIVALENCE.md`
3. `docs/architecture/CURRENT_SR_VS_STORED_PRICE_RULES.md`
4. `docs/architecture/LEGACY_TECHNICAL_PROSE_SUPPRESSION.md`
5. update `PRICE_STRUCTURE_V3_SHADOW_POLICY.md`
6. update the current production-message renderer policy document if one exists

---

# 51. Required reports

Create:

1. `docs/reports/20260826-v3-renderer-root-cause.md`
2. `docs/reports/20260826-v3-fib-confluence-render-audit.md`
3. `docs/reports/20260826-v3-current-vs-stored-price-rule-audit.md`
4. `docs/reports/20260826-v3-legacy-technical-prose-audit.md`
5. `docs/reports/20260826-v3-renderer-exact-controls.md`
6. `docs/reports/20260826-v3-renderer-full-universe.md`
7. `docs/reports/20260826-v3-renderer-exact-message-diff.md`
8. `docs/reports/20260826-v3-renderer-message-quality.md`
9. `docs/reports/20260826-v3-renderer-safety-parity.md`
10. `docs/reports/20260826-v3-renderer-readiness.md`
11. `docs/reports/20260826-v3-renderer-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-v3-renderer-readiness.json`

---

# 52. Exact message artifact

Create:

`docs/reports/20260826-v3-renderer-exact-candidate-messages.json`

Per stock:

```text
before_message
after_message
before_price_structure_section
after_price_structure_section
stored_price_rule_section
legacy_technical_occurrences
exact_diff
quality
eligibility
```

---

# 53. Gates

Set exactly:

```text
FIB_CONFLUENCE_RENDER_EQUIVALENCE =
PASS / FAIL

MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED =
0 / NONZERO

REDUNDANT_IDENTICAL_FIB_RANGE_REPEATED =
0 / NONZERO

CURRENT_SR_STORED_RULE_SEPARATION =
PASS / FAIL

UNLABELED_CURRENT_STORED_PRICE_CONFLICT =
0 / NONZERO

STORED_PRICE_RULE_DATA_MUTATION =
0 / NONZERO

LEGACY_TECHNICAL_PROSE_POLICY =
PASS / FAIL

STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 =
0 / NONZERO

UNCLASSIFIED_TECHNICAL_PRICE_PROSE =
0 / NONZERO

MU_LEGACY_TECHNICAL_DUPLICATION =
0 / NONZERO

SK_HYNIX_FIB_RANGE_RENDER =
PASS / FAIL

SNDK_CURRENT_STORED_SEPARATION =
PASS / FAIL

TSM_CURRENT_STORED_SEPARATION =
PASS / FAIL

TSLA_SR_ONLY_PRESERVED =
PASS / FAIL

012450_FAMILY_RENDER_REGRESSION =
0 / NONZERO

MESSAGE_ELIGIBILITY_REGRESSION =
0 / NONZERO

MESSAGE_NUMERIC_DENSITY_AFTER =
PASS / PARTIAL / FAIL

WORSE =
0 / NONZERO

RAW_FIB_OR_SR_VALUE_CHANGED_BY_RENDERER =
0 / NONZERO

RAW_SR_VALUE_CHANGED =
0 / NONZERO

RAW_FIB_VALUE_CHANGED =
0 / NONZERO

SR_ELIGIBILITY_CHANGED_BY_RENDERER =
0 / NONZERO

FIB_FAMILY_ELIGIBILITY_CHANGED_BY_RENDERER =
0 / NONZERO

CROSS_TIMEFRAME_RANKING_CHANGED_BY_RENDERER =
0 / NONZERO

UNREGISTERED_PRICE_STRUCTURE_NUMERIC =
0 / NONZERO

UNREGISTERED_STORED_PRICE_RULE_NUMERIC =
0 / NONZERO

NUMBERS_WITHOUT_PROVENANCE =
0 / NONZERO

CURRENT_SR_RENDERED_AS_STORED_RULE =
0 / NONZERO

STORED_RULE_RENDERED_AS_CURRENT_SR =
0 / NONZERO

BUSINESS_FACT_CHANGED_BY_RENDERER_REPAIR =
0 / NONZERO

BUSINESS_THESIS_CHANGED_BY_RENDERER_REPAIR =
0 / NONZERO

CURRENT_RUNTIME_VISIBLE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_V3_RENDERER_INTEGRATION =
SHADOW /
INTEGRATED_READY_NOT_ARMED /
FAIL

CODE_CORRECTNESS =
PASS / FAIL

PRODUCTION_ENABLEMENT_READY =
YES / NO
```

---

# 54. Mandatory baseline counts

Preserve or explain:

```text
BASELINE_KR_ELIGIBLE = 6
BASELINE_KR_ELIGIBLE_SR_ONLY = 1
BASELINE_KR_BLOCKED = 0

BASELINE_US_ELIGIBLE = 4
BASELINE_US_ELIGIBLE_SR_ONLY = 9
BASELINE_US_BLOCKED = 0

BASELINE_MATERIAL_IMPROVEMENT = 16
BASELINE_MINOR_IMPROVEMENT = 4
BASELINE_WORSE = 0
```

---

# 55. Readiness criteria

Set:

```text
PRICE_STRUCTURE_V3_RENDERER_INTEGRATION =
INTEGRATED_READY_NOT_ARMED
```

and:

```text
PRODUCTION_ENABLEMENT_READY = YES
```

only if:

```text
Fib material range-loss = 0

current SR / stored rule confusion = 0

stale legacy technical prose with active v3 = 0

SK hynix control PASS
SNDK control PASS
MU control PASS
TSM control PASS
TSLA control PASS
012450 control PASS

message eligibility regression = 0

numeric density safe
WORSE = 0

raw calculations unchanged
business text unchanged
provenance complete

P0 = 0
material P1 = 0
```

---

# 56. Expected next action

If PASS:

```text
NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT
```

Do not create another calculation-engine repair unless this renderer task discovers a real backend
correctness issue.

---

# 57. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BRANCH = ...
BASE_SHA = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

FIB_CONFLUENCE_RENDER_EQUIVALENCE = ...
MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0
REDUNDANT_IDENTICAL_FIB_RANGE_REPEATED = 0

SK_HYNIX_MAJOR_RESISTANCE = ...
SK_HYNIX_FIB_SR_CONFLUENCE = ...
SK_HYNIX_RENDERED_FIB_LINE = ...
SK_HYNIX_FIB_RANGE_RENDER = ...

CURRENT_SR_STORED_RULE_SEPARATION = ...
UNLABELED_CURRENT_STORED_PRICE_CONFLICT = 0

SNDK_CURRENT_SR = ...
SNDK_STORED_PRICE_RULE = ...
SNDK_CURRENT_STORED_SEPARATION = ...

TSM_CURRENT_RESISTANCE = ...
TSM_STORED_CONFIRMATION = ...
TSM_CURRENT_STORED_SEPARATION = ...

LEGACY_TECHNICAL_PROSE_POLICY = ...
STALE_LEGACY_TECHNICAL_PROSE_WITH_V3 = 0
UNCLASSIFIED_TECHNICAL_PRICE_PROSE = 0

MU_LEGACY_TECHNICAL_BEFORE = ...
MU_LEGACY_TECHNICAL_AFTER = ...
MU_LEGACY_TECHNICAL_DUPLICATION = 0

TSLA_SR_ONLY_PRESERVED = ...
012450_FAMILY_RENDER_REGRESSION = 0

KR_ELIGIBLE_AFTER = ...
KR_ELIGIBLE_SR_ONLY_AFTER = ...
KR_BLOCKED_AFTER = ...

US_ELIGIBLE_AFTER = ...
US_ELIGIBLE_SR_ONLY_AFTER = ...
US_BLOCKED_AFTER = ...

MESSAGE_ELIGIBILITY_REGRESSION = 0

MATERIAL_IMPROVEMENT = ...
MINOR_IMPROVEMENT = ...
NO_ADDED_VALUE = ...
WORSE = 0

MESSAGE_NUMERIC_DENSITY_AFTER = ...

RAW_FIB_OR_SR_VALUE_CHANGED_BY_RENDERER = 0
RAW_SR_VALUE_CHANGED = 0
RAW_FIB_VALUE_CHANGED = 0

SR_ELIGIBILITY_CHANGED_BY_RENDERER = 0
FIB_FAMILY_ELIGIBILITY_CHANGED_BY_RENDERER = 0
CROSS_TIMEFRAME_RANKING_CHANGED_BY_RENDERER = 0

UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
UNREGISTERED_STORED_PRICE_RULE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0

CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0

BUSINESS_FACT_CHANGED_BY_RENDERER_REPAIR = 0
BUSINESS_THESIS_CHANGED_BY_RENDERER_REPAIR = 0

CURRENT_RUNTIME_VISIBLE_DIFF = 0
TELEGRAM_SEND = 0
MANUAL_TASK = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
STORED_PRICE_RULE_DATA_MUTATION = 0

PRICE_STRUCTURE_V3_RENDERER_INTEGRATION = ...
CODE_CORRECTNESS = ...
PRODUCTION_ENABLEMENT_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT /
KEEP_SHADOW_AND_REVIEW /
BOUNDED_REPAIR

EXACT_MESSAGE_ARTIFACT = ...
ZIP = ...
ZIP_SHA256 = ...
```

---

# 58. Mandatory completion ZIP

Create:

`20260826-price-structure-v3-renderer-integration-micro-repair-bundle.zip`

Include:

- exact instruction
- Fib render audit
- current SR vs stored rule audit
- legacy technical prose audit
- exact controls
- full-universe replay
- exact message diff
- quality review
- safety parity
- readiness
- exact message JSON
- artifact index

Do not include:

- secrets
- auth headers
- account identifiers
- hidden chain-of-thought

Compute/report SHA-256.

---

# 59. Severity

## P0

- raw SR/Fib number changed by renderer
- wrong security/currency price displayed
- stored invalidation/confirmation changed
- unstable Fib reintroduced
- current SR mislabeled as stored rule in a way that changes meaning
- stored rule mislabeled as current SR in a way that changes meaning
- business investment logic changed
- live send/mutation during shadow task

## P1

- material Fib confluence extension hidden
- SNDK-like current/stored price-rule conflict remains unlabeled
- stale legacy MACD/RSI/OHLCV technical prose remains beside current v3
- stored confirmation is merged into nearest resistance
- duplicate technical frameworks remain in one current message
- message eligibility regresses without safety reason
- numeric density becomes materially worse

## P2

- exact heading wording preference
- identical Fib/SR range shown with slightly different concise wording
- current vs stored rule sections separated by a different visual heading
- minor message-length differences

---

# 60. Final principle

This task does not change what the price-structure engine knows.

It changes only how the message explains ownership.

The final renderer must make three things obvious:

```text
1. What is the current market-derived price structure?

2. What are the old monitoring rules I previously registered?

3. When Fibonacci adds a real extra structural range,
   what is that exact range?
```

There should be only one current technical-analysis narrative.

If v3 is active:

```text
v3 owns current SR/Fib interpretation.
```

Stored rules remain:

```text
management references,
not current SR.
```

Legacy stale technical prose must not compete with either.

Once this passes, proceed directly to bounded selective enablement.
