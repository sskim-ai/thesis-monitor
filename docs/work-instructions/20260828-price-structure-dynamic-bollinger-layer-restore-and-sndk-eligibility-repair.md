# thesis-monitor — Price Structure v3 Dynamic Bollinger Layer Restore + SNDK Eligibility Repair
## Keep historical "주요 구조 지지/저항" price-anchored
## Restore useful Bollinger-only zones under a separate transparent dynamic S/R layer
## Audit SNDK full Price Structure disappearance independently
## US full universe + KR 7 controls replay/test before deployment

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `PRICE_STRUCTURE_DYNAMIC_BOLLINGER_LAYER_RESTORE_AND_SNDK_ELIGIBILITY_REPAIR`
- Task class: `SHARED_RENDERER_SEMANTIC_EXTENSION + BOUNDED_ELIGIBILITY_AUDIT + CROSS_MARKET_REPLAY`
- Production Assist: preserve `OFF`
- US Price Structure: preserve `ON`
- KR Price Structure: preserve `ON`
- US/KR market-message pipelines: no functional changes
- Production-recipient test send: `0`
- Manual production scheduler execution: `0`
- DB / official assessment mutation: `0`

### Latest known operating lineage

The prior Major Structural S/R Reality Gate repair reports:

```text
final main / operating =
281699c07490066e5981df836883f26989d0a9bf
```

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve latest safe `origin/main`
4. resolve actual operating SHA
5. use `281699c...` or a safe linear descendant
6. record exact lineage
7. do not revert the Major S/R Reality Gate

---

# 1. Product decision

The prior repair correctly established:

```text
주요 구조 지지/저항
=
actual price-anchored historical structure
```

That contract remains.

However Bollinger-only levels can still be useful as:

```text
dynamic volatility-based support/resistance
```

especially when current price approaches weekly/monthly bands.

Therefore add a separate user-facing semantic layer:

```text
볼린저 지지
볼린저 저항
```

or repository-consistent equivalent:

```text
동적 지지(주봉 볼린저)
동적 저항(월봉 볼린저)
```

Do NOT relabel them back to `주요 구조`.

---

# 2. Why this change is needed

The reality-gate repair removed useful information together with invalid structural labels.

Source-supported examples from the supplied before/after artifacts:

## SK hynix 000660

Before:

```text
주요 구조 저항:
약 181.9만~182.9만원
source = BOLLINGER_WEEKLY only
```

After:

```text
omitted
```

The historical-structure label was wrong,
but the weekly Bollinger upper area remains useful as a dynamic resistance reference.

## MU

Before:

```text
주요 구조 저항:
약 $1,020.52~$1,025.65
source = BOLLINGER_MONTHLY only
```

After:

```text
omitted
```

Again:
not valid historical major resistance,
but potentially useful as monthly dynamic resistance.

## SNDK

Prior current-time E2E artifact:

```text
eligibility = ELIGIBLE_SR_ONLY
basis close = $1,456.93

near support:
$1,412.98~$1,447.71

near resistance:
$1,481.27~$1,518.11

Bollinger-weekly major candidate:
$1,527.66~$1,535.33
```

Latest Major-SR replay artifact:

```text
eligibility_before = BLOCKED
eligibility_after = BLOCKED
current_price = $1,499.37
before_renderer = null
after_renderer = null
```

Therefore SNDK's complete Price Structure disappearance is not explained solely by the Major S/R reality gate.

It requires an independent eligibility/data-basis audit.

---

# 3. Semantic model after this repair

Price Structure user-facing semantics become:

```text
CURRENT PRICE
→ 기준 종가

NEAR_SUPPORT / NEAR_RESISTANCE
→ 가까운 지지 / 가까운 저항

MAJOR_SUPPORT / MAJOR_RESISTANCE
→ 주요 구조 지지 / 주요 구조 저항
→ price-anchor required

DYNAMIC_BOLLINGER_SUPPORT / DYNAMIC_BOLLINGER_RESISTANCE
→ 볼린저 지지 / 볼린저 저항
→ historical reaction NOT required
→ indicator provenance explicit

FIB_CONFLUENCE
→ optional secondary confluence only

STORED PRICE RULES
→ separate ownership
```

---

# 4. Hard semantic boundary

Keep:

```text
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
```

Add:

```text
BOLLINGER_ONLY_DYNAMIC_SR_VISIBLE =
allowed when safe/material
```

A Bollinger-only zone may be visible,
but only under the dynamic/Bollinger label.

Hard:

```text
BOLLINGER_DYNAMIC_AS_MAJOR_STRUCTURAL = 0
```

---

# 5. New backend semantic types

Prefer explicit backend-owned semantic types:

```text
DYNAMIC_BOLLINGER_SUPPORT
DYNAMIC_BOLLINGER_RESISTANCE
```

If the existing architecture already has a generic dynamic-zone semantic type,
reuse it with:

```text
source_family = BOLLINGER_*
```

Do not encode the distinction only in free-form AI prose.

AI must not calculate or promote these numerics.

Hard:

```text
AI_CALCULATED_BOLLINGER_SR = 0
AI_PROMOTED_BOLLINGER_SR = 0
```

---

# 6. Role determination

A Bollinger-derived zone should be classified by its relation to current price:

```text
safe zone entirely below current price
→ dynamic support candidate

safe zone entirely above current price
→ dynamic resistance candidate

zone straddles current price
→ do not force support/resistance role
```

Do not assume:

```text
upper band always = resistance
lower band always = support
```

without current-role compatibility.

---

# 7. Timeframe hierarchy

Use the established analysis order:

```text
monthly → weekly → daily
```

But do not mechanically display the highest timeframe.

Select the most material non-duplicative dynamic zone on each side.

Possible sources:

```text
BOLLINGER_MONTHLY
BOLLINGER_WEEKLY
BOLLINGER_DAILY
```

Record timeframe explicitly.

---

# 8. User-facing labels

Preferred transparent format:

```text
• 볼린저 지지(주봉): 약 ...
• 볼린저 저항(월봉): 약 ...
```

or:

```text
• 동적 지지(주봉 볼린저): 약 ...
• 동적 저항(월봉 볼린저): 약 ...
```

Choose one wording consistently after test-message readability review.

Do not use:

```text
주요 구조 지지
주요 구조 저항
```

for Bollinger-only zones.

---

# 9. Display budget — avoid information overload

Maximum standalone dynamic Bollinger lines per stock:

```text
1 support
1 resistance
```

Do not dump:

```text
daily upper/lower
weekly upper/lower
monthly upper/lower
```

all at once.

Hard:

```text
DYNAMIC_BOLLINGER_SUPPORT_LINE_COUNT <= 1
DYNAMIC_BOLLINGER_RESISTANCE_LINE_COUNT <= 1
```

---

# 10. Duplicate / overlap handling

If a selected Bollinger zone materially overlaps an already visible near or major structural zone:

do not print a second nearly identical range.

Instead annotate the existing line with confluence, for example:

```text
• 가까운 저항: 약 $...~$... · 주봉 볼린저 중첩
```

or:

```text
• 주요 구조 저항: 약 $...~$... · 월봉 볼린저 중첩
```

Hard:

```text
DUPLICATE_SR_RANGE_VISIBLE = 0
```

---

# 11. Standalone Bollinger zone

If the Bollinger zone adds a distinct price area:

show it separately.

Example target behavior:

## SK hynix

```text
📐 현재 가격 구조
• 기준 종가: 1,730,000원
• 가까운 지지: 약 158.1만~159.8만원
• 볼린저 저항(주봉): 약 181.9만~182.9만원
```

Do not call it `주요 구조 저항`.

## MU

```text
📐 현재 가격 구조
• 기준 종가: $915.99
• 가까운 지지: 약 $851.82~$856.10
• 가까운 저항: 약 $946.42~$951.18
• 볼린저 저항(월봉): 약 $1,020.52~$1,025.65
```

Exact current replay values may differ.

These ranges are regression controls, not hard-coded outputs.

---

# 12. Dynamic-zone safety

A standalone Bollinger zone must have:

```text
current completed-bar indicator observation
same security basis
same currency
same corporate-action adjustment basis
valid timeframe coverage
valid current role
registered numeric provenance
```

Historical price reactions are NOT required,
because the label explicitly says Bollinger/dynamic.

Hard:

```text
BOLLINGER_SR_SECURITY_BASIS_CONFLICT = 0
BOLLINGER_SR_CURRENCY_CONFLICT = 0
BOLLINGER_SR_ADJUSTMENT_BASIS_CONFLICT = 0
STALE_BOLLINGER_SR_VISIBLE = 0
PARTIAL_BAR_BOLLINGER_SR_VISIBLE = 0
```

---

# 13. Materiality / relevance gate

Do not display every valid band.

A standalone Bollinger zone must be relevant under existing Price Structure relevance logic.

Prefer repository-native signals such as:

```text
ACTIVE_NEAR
ACTIVE_STRUCTURAL
proximity tier
current role
timeframe importance
material distance
```

Do not introduce an arbitrary fixed percentage cutoff unless the repository already has one.

Hard:

```text
IRRELEVANT_REMOTE_BOLLINGER_NOISE_VISIBLE = 0
```

---

# 14. Historical-traded-range rule does NOT apply to dynamic Bollinger

The Major S/R reality gate correctly rejects an untraded derived level as:

```text
historical major structural resistance
```

But a Bollinger upper/lower band is allowed to exist outside prior traded highs/lows under the explicit label:

```text
볼린저 저항 / 지지
```

because it is an indicator-derived dynamic reference.

Therefore:

```text
UNTRADED_DERIVED_MAJOR_SR = prohibited
UNTRADED_BOLLINGER_DYNAMIC_SR = allowed if safe/material
```

Do not reintroduce semantic confusion.

---

# 15. Indicator observation vs price interaction

Preserve the prior repair:

```text
indicator_observation_date
≠
last_price_interaction_date
```

Bollinger dynamic zones should normally expose:

```text
indicator_observation_date
```

and must not fabricate:

```text
historical_interaction_count
last_price_interaction_date
```

Hard:

```text
INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0
```

---

# 16. Structural + Bollinger confluence

When a price-anchored structural zone and Bollinger overlap:

the structural zone remains authoritative.

Bollinger is secondary evidence.

Example:

```text
• 주요 구조 저항: 약 ... · 월봉 볼린저 중첩
```

Do not create two independent authoritative prices.

---

# 17. Fib interaction

Fib remains under existing family-consensus safety.

Possible hierarchy:

```text
price-anchored structural S/R
> Bollinger dynamic S/R
> Fib as optional confluence
```

Do not turn this task into a Fib selector redesign.

Hard:

```text
FIB_FAMILY_POLICY_DIFF = 0
WAVE_POLICY_DIFF = 0
```

---

# 18. SNDK independent eligibility audit

Track SNDK from:

```text
prior current-time E2E
ELIGIBLE_SR_ONLY
```

to:

```text
latest Major-SR replay
BLOCKED before and after
```

Determine exactly why.

Record:

```text
packet/source identity
target session
price_as_of
current_price / basis close
daily/weekly/monthly end dates
security basis
adjustment basis
coverage status
denial reasons
quality gate
eligibility decision
```

Hard:

```text
SNDK_ELIGIBILITY_ROOT_CAUSE = PASS
```

---

# 19. SNDK price-basis discrepancy

Explicitly compare the source-supported values:

Prior E2E:

```text
basis close = $1,456.93
```

Latest Major-SR replay:

```text
current_price = $1,499.37
```

Both artifacts use target/as-of `2026-08-27`.

Determine whether this is:

```text
different provider snapshot
current quote vs completed-session close
adjustment/corporate-action basis
replay fixture difference
stale/newer cache
data quality defect
```

Do not assume.

Hard:

```text
SNDK_PRICE_BASIS_EXPLAINED = PASS / FAIL
```

---

# 20. SNDK fail-closed rule

If SNDK's basis/session/history cannot be safely reconciled:

keep:

```text
BLOCKED
```

and do not fabricate S/R.

If safely reconciled:

restore its Price Structure eligibility and then apply the same generic dynamic Bollinger layer.

No ticker-specific bypass.

---

# 21. SNDK expected positive control if eligibility is restored

Prior real E2E control:

```text
near support:
$1,412.98~$1,447.71

near resistance:
$1,481.27~$1,518.11

Bollinger-weekly upper area:
$1,527.66~$1,535.33
```

These are NOT hard-coded targets.

If current replay safely reproduces equivalent structure:

expected user-facing semantics are:

```text
가까운 지지
가까운 저항
볼린저 저항(주봉)
```

not a Bollinger-only `주요 구조 저항`.

---

# 22. Track A — implementation

Implement:

```text
dynamic Bollinger candidate extraction
role compatibility
materiality/relevance
overlap/confluence handling
numeric registry ownership
renderer support
AI/fallback parity
```

Preserve Major S/R Reality Gate.

---

# 23. Track B — SNDK eligibility repair

Audit and repair only if a real shared defect is found.

If SNDK is correctly blocked:

document why and do not bypass.

If a shared eligibility/data-basis bug is found:

repair generically and rerun all relevant regression subjects.

---

# 24. Track C — US full-universe replay

Replay every current monitored US/foreign stock.

Per ticker report:

```text
current price
eligibility
near support/resistance
major structural support/resistance
dynamic Bollinger support/resistance
Bollinger timeframe
overlap/confluence
Fib visibility
stored-rule ownership
exact renderer block
```

---

# 25. Track C — KR 7 replay

Replay:

```text
000660
003690
005490
005930
010120
012450
086280
```

Verify:

```text
major structural semantics remain price-anchored
useful Bollinger-only zones can reappear dynamically
near S/R unchanged
no duplicate noise
```

---

# 26. Required positive controls

At minimum audit:

```text
000660 SK hynix
MU
SNDK
GOOGL
TSM
005930 Samsung Electronics
012450 Hanwha Aerospace
```

Why:

```text
SK hynix → useful weekly Bollinger resistance previously disappeared
MU → useful monthly Bollinger resistance disappeared
SNDK → full Price Structure disappeared
GOOGL → old $424 derived zone must never return as "major structural"
TSM → previous dynamic-only major zones removed
005930 / 012450 → KR shared semantics regression controls
```

---

# 27. GOOGL negative semantic control

GOOGL's old:

```text
$424.82~$426.96
```

may be eligible to appear only as a clearly labeled dynamic Bollinger reference if it passes current materiality/relevance.

It must NEVER return as:

```text
주요 구조 저항
```

If it is too remote/not material:

omit it entirely.

Hard:

```text
GOOGL_424_AS_MAJOR_STRUCTURAL = 0
```

---

# 28. Message ordering

Preferred Price Structure order:

```text
📐 현재 가격 구조
• 기준 종가
• 가까운 지지
• 가까운 저항
• 주요 구조 지지
• 주요 구조 저항
• 볼린저 지지(<timeframe>)
• 볼린저 저항(<timeframe>)
```

But omit absent lines.

If Bollinger overlaps an existing line:

annotate confluence instead of adding a standalone line.

---

# 29. Message length control

Price Structure must not dominate the stock message.

Target maximum standalone lines:

```text
current price = 1
near S/R = max 2
major structural = max 2
dynamic Bollinger = max 2
```

Typical messages should use fewer.

No three-timeframe indicator dump.

---

# 30. AI / fallback parity

For every replayed subject:

```text
same dynamic-zone eligibility
same dynamic-zone numerics
same timeframe label
same overlap/confluence decision
same structural-vs-dynamic ownership
```

Hard:

```text
AI_FALLBACK_DYNAMIC_BOLLINGER_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_DYNAMIC_BOLLINGER_NUMERIC_PARITY = PASS
AI_FALLBACK_DYNAMIC_BOLLINGER_LABEL_PARITY = PASS
```

---

# 31. Test sink

Use dedicated non-production test sink.

Send:

```text
all current monitored US/foreign stock messages
+
KR 7 control messages
```

No production recipients.

Review exact received messages.

---

# 32. Human quality checks

For each message verify:

```text
important dynamic information restored
historical vs dynamic labels are unambiguous
no duplicate ranges
no indicator dump
no target/stop
stored rules separate
message readable
```

Hard:

```text
TEST_DYNAMIC_BOLLINGER_MESSAGE_QUALITY = PASS
TEST_EXACT_PAYLOAD_MATCH = PASS
```

---

# 33. SK hynix exact readability control

The operator should be able to see a meaningful weekly upper-band reference without mistaking it for a historical high.

Target style:

```text
• 볼린저 저항(주봉): 약 181.9만~182.9만원
```

or equivalent current replay value.

Do not write:

```text
주요 구조 저항: 181.9만~182.9만원
```

unless independent price-anchor evidence separately qualifies it.

---

# 34. MU exact readability control

Target style:

```text
• 볼린저 저항(월봉): 약 $1,020.52~$1,025.65
```

or equivalent current replay value.

---

# 35. SNDK exact readability control

If safe eligibility restored:

message should contain useful S/R again.

If not:

the report must clearly state the blocking reason.

No silent disappearance.

Hard:

```text
SNDK_SILENT_PRICE_STRUCTURE_DISAPPEARANCE = 0
```

---

# 36. Operating promotion

Deploy only if:

```text
dynamic semantic layer PASS
Major S/R reality gate preserved
SNDK root cause understood
US full-universe replay PASS
KR 7 replay PASS
test-sink quality PASS
P0 = 0
material P1 = 0
```

Preserve feature states.

---

# 37. Post-deploy smoke

Read-only verify:

```text
SK hynix
MU
SNDK
GOOGL
all US monitored
KR 7
```

Hard:

```text
POST_DEPLOY_DYNAMIC_BOLLINGER = PASS
POST_DEPLOY_MAJOR_SR_REALITY_GATE = PASS
POST_DEPLOY_US_PRICE_STRUCTURE = PASS
POST_DEPLOY_KR_PRICE_STRUCTURE = PASS
```

---

# 38. Next natural proof

Do not manually trigger production.

Observe next natural stock-monitoring messages.

Verify:

```text
useful Bollinger dynamic zones appear when material
major structural zones remain price-anchored
SNDK behavior is explicit/safe
near S/R intact
no duplicate clutter
```

Set:

```text
NATURAL_DYNAMIC_BOLLINGER_LAYER =
PASS / FAIL
```

---

# 39. Required reports

Create:

1. `docs/reports/20260828-dynamic-bollinger-layer-policy.md`
2. `docs/reports/20260828-dynamic-vs-structural-sr-contract.md`
3. `docs/reports/20260828-skhynix-bollinger-positive-control.md`
4. `docs/reports/20260828-mu-bollinger-positive-control.md`
5. `docs/reports/20260828-sndk-eligibility-root-cause.md`
6. `docs/reports/20260828-sndk-price-basis-comparison.md`
7. `docs/reports/20260828-us-dynamic-bollinger-replay.md`
8. `docs/reports/20260828-kr7-dynamic-bollinger-replay.md`
9. `docs/reports/20260828-dynamic-bollinger-ai-fallback-parity.md`
10. `docs/reports/20260828-dynamic-bollinger-test-messages.md`
11. `docs/reports/20260828-dynamic-bollinger-message-quality.md`
12. `docs/reports/20260828-dynamic-bollinger-operating-promotion.md`
13. `docs/reports/20260828-dynamic-bollinger-natural-proof-status.md`
14. `docs/reports/20260828-dynamic-bollinger-readiness.md`
15. `docs/reports/20260828-dynamic-bollinger-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-dynamic-bollinger-replay.json
docs/reports/20260828-kr7-dynamic-bollinger-replay.json
docs/reports/20260828-dynamic-bollinger-readiness.json
```

---

# 40. Required gates

Set exactly:

```text
DYNAMIC_BOLLINGER_LAYER =
PASS / FAIL

BOLLINGER_DYNAMIC_AS_MAJOR_STRUCTURAL =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

DYNAMIC_BOLLINGER_SUPPORT_LINE_COUNT_MAX =
1 / OTHER

DYNAMIC_BOLLINGER_RESISTANCE_LINE_COUNT_MAX =
1 / OTHER

DUPLICATE_SR_RANGE_VISIBLE =
0 / NONZERO

IRRELEVANT_REMOTE_BOLLINGER_NOISE_VISIBLE =
0 / NONZERO

INDICATOR_OBSERVATION_AS_PRICE_INTERACTION =
0 / NONZERO

BOLLINGER_SR_SECURITY_BASIS_CONFLICT =
0 / NONZERO

BOLLINGER_SR_CURRENCY_CONFLICT =
0 / NONZERO

BOLLINGER_SR_ADJUSTMENT_BASIS_CONFLICT =
0 / NONZERO

STALE_BOLLINGER_SR_VISIBLE =
0 / NONZERO

PARTIAL_BAR_BOLLINGER_SR_VISIBLE =
0 / NONZERO

AI_CALCULATED_BOLLINGER_SR =
0 / NONZERO

AI_PROMOTED_BOLLINGER_SR =
0 / NONZERO

GOOGL_424_AS_MAJOR_STRUCTURAL =
0 / NONZERO

SKHYNIX_DYNAMIC_BOLLINGER_CONTROL =
PASS / NOT_MATERIAL / FAIL

MU_DYNAMIC_BOLLINGER_CONTROL =
PASS / NOT_MATERIAL / FAIL

SNDK_ELIGIBILITY_ROOT_CAUSE =
PASS / FAIL

SNDK_PRICE_BASIS_EXPLAINED =
PASS / FAIL

SNDK_PRICE_STRUCTURE_STATE =
ELIGIBLE /
BLOCKED_SAFE /
FAIL

SNDK_SILENT_PRICE_STRUCTURE_DISAPPEARANCE =
0 / NONZERO

US_CURRENT_MONITORED_REPLAY =
PASS / FAIL

KR7_CONTROL_REPLAY =
PASS / FAIL

AI_FALLBACK_DYNAMIC_BOLLINGER_ELIGIBILITY_PARITY =
PASS / FAIL

AI_FALLBACK_DYNAMIC_BOLLINGER_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_DYNAMIC_BOLLINGER_LABEL_PARITY =
PASS / FAIL

TEST_MESSAGE_COUNT =
...

TEST_DYNAMIC_BOLLINGER_MESSAGE_QUALITY =
PASS / FAIL

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

POST_DEPLOY_DYNAMIC_BOLLINGER =
PASS / NOT_RUN / FAIL

POST_DEPLOY_MAJOR_SR_REALITY_GATE =
PASS / NOT_RUN / FAIL

POST_DEPLOY_US_PRICE_STRUCTURE =
PASS / NOT_RUN / FAIL

POST_DEPLOY_KR_PRICE_STRUCTURE =
PASS / NOT_RUN / FAIL

FIB_FAMILY_POLICY_DIFF =
0 / NONZERO

WAVE_POLICY_DIFF =
0 / NONZERO

UNSUPPORTED_TARGET_PRICE =
0 / NONZERO

UNSUPPORTED_STOP_PRICE =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

DYNAMIC_BOLLINGER_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_DYNAMIC_BOLLINGER_LAYER =
PENDING / PASS / FAIL
```

---

# 41. Pre-deploy PASS rule

Require:

```text
Major S/R Reality Gate preserved
SK hynix useful Bollinger reference recoverable when material
MU useful Bollinger reference recoverable when material
SNDK disappearance root cause understood
no silent SNDK block
US full universe PASS
KR 7 PASS
no duplicate clutter
AI/fallback parity PASS
test sink PASS
P0/P1 = 0/0
```

---

# 42. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_RESULT = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

TRACK_D_BRANCH = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

DYNAMIC_BOLLINGER_LAYER = ...

SKHYNIX_CURRENT_PRICE = ...
SKHYNIX_NEAR_SUPPORT = ...
SKHYNIX_NEAR_RESISTANCE = ...
SKHYNIX_MAJOR_SUPPORT = ...
SKHYNIX_MAJOR_RESISTANCE = ...
SKHYNIX_BOLLINGER_SUPPORT = ...
SKHYNIX_BOLLINGER_RESISTANCE = ...

MU_CURRENT_PRICE = ...
MU_NEAR_SUPPORT = ...
MU_NEAR_RESISTANCE = ...
MU_MAJOR_SUPPORT = ...
MU_MAJOR_RESISTANCE = ...
MU_BOLLINGER_SUPPORT = ...
MU_BOLLINGER_RESISTANCE = ...

SNDK_ELIGIBILITY_ROOT_CAUSE = ...
SNDK_PRICE_BASIS_EXPLAINED = ...
SNDK_PRICE_STRUCTURE_STATE = ...
SNDK_NEAR_SUPPORT = ...
SNDK_NEAR_RESISTANCE = ...
SNDK_MAJOR_SUPPORT = ...
SNDK_MAJOR_RESISTANCE = ...
SNDK_BOLLINGER_SUPPORT = ...
SNDK_BOLLINGER_RESISTANCE = ...

BOLLINGER_DYNAMIC_AS_MAJOR_STRUCTURAL = 0
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
DUPLICATE_SR_RANGE_VISIBLE = 0
INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0

US_CURRENT_MONITORED_REPLAY = ...
KR7_CONTROL_REPLAY = ...

AI_FALLBACK_DYNAMIC_BOLLINGER_ELIGIBILITY_PARITY = ...
AI_FALLBACK_DYNAMIC_BOLLINGER_NUMERIC_PARITY = ...
AI_FALLBACK_DYNAMIC_BOLLINGER_LABEL_PARITY = ...

TEST_MESSAGE_COUNT = ...
TEST_DYNAMIC_BOLLINGER_MESSAGE_QUALITY = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0

POST_DEPLOY_DYNAMIC_BOLLINGER = ...
POST_DEPLOY_MAJOR_SR_REALITY_GATE = ...

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...
OHLCV_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

DYNAMIC_BOLLINGER_ROLLOUT =
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_DYNAMIC_BOLLINGER_LAYER =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 43. Mandatory completion ZIP

Create:

`20260828-price-structure-dynamic-bollinger-layer-restore-and-sndk-eligibility-repair-bundle.zip`

Include:

```text
exact instruction
dynamic-vs-structural semantic policy
SK hynix control
MU control
SNDK root cause / price-basis comparison
US full-universe replay
KR 7 replay
AI/fallback parity
exact test messages
message-quality review
operating promotion
post-deploy smoke
natural-proof status
readiness JSON
test/CI summary
artifact index
```

Exclude secrets, sink IDs, tokens, auth headers, account identifiers, hidden chain-of-thought.

Compute SHA-256.

---

# 44. Final principle

Do not choose between:

```text
semantic correctness
and
useful information
```

Keep both.

Historical structural levels should remain historically grounded.

Bollinger levels should remain visible when useful,
but transparently labeled as dynamic indicator-based support/resistance.

And a stock like SNDK must never lose its entire Price Structure silently:
either render safe structure or explain the explicit blocking reason in audit/reporting.
