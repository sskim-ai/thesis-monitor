# thesis-monitor — US Morning Full Message Integration + Iterative Validation
## Explicit index numbers + Korean night futures + current-session market structure + temporally safe macro
## Dedicated test-sink full-message review → bounded refinements → deploy only after PASS
## US Price Structure remains OFF

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `US_MORNING_FULL_MESSAGE_INTEGRATION_AND_ITERATIVE_VALIDATION`
- Task class: `BOUNDED_US_MESSAGE_INTEGRATION_AND_TEST`
- Target product: US morning market digest
- Current US natural state: `LIVE_PASS`
- Current-session evidence consumption: `PASS`
- RSP propagation: `PASS`
- sector dispersion: `PASS`
- macro temporal boundary: `PASS`
- Nasdaq exact-session breadth boundary: `PASS`
- US Price Structure: keep `OFF`
- Production Assist: keep `OFF`
- Manual production task: `0`
- Production-recipient test send: `0`
- DB / assessment mutation: `0`

Resolve actual latest safe `origin/main` and operating SHA before implementation.

Do not reopen already-passing packet ownership, exactly-once, temporal normalization, or US current-session evidence-selection logic unless a direct regression is found.

---

# 1. Objective

Bring the US morning message to this user-facing structure:

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY +x.xx%
• QQQ +x.xx%
• IWM +x.xx%
• SOXX +x.xx%
• RSP +x.xx%

🔎 시장 내부
• current-session interpretation
• RSP participation/style interpretation
• 업종 강세: <sector> +x.xx%
• 업종 약세: <sector> -x.xx%

🌙 한국 야간선물
• KOSPI200 야간선물 +x.xx%
• KOSDAQ150 야간선물 +x.xx%

🌐 보조 시장환경
• only temporally valid rates / VIX / WTI / FX context
  with explicit date/session qualification when not same-session

📌 다음 확인
• bounded next-check items
```

Then validate the full exact message in the dedicated non-production test sink.

This task is not complete merely because individual facts are present in the packet.
The whole message must be reviewed as one user-facing product.

---

# 2. Work split

This work MUST be splittable.

```text
Track A
Explicit US index numeric block

Track B
KOSPI200 / KOSDAQ150 night-futures reintegration + session alignment

Track C
Full US morning renderer integration

Track D
Dedicated test-sink exact-message validation
+ bounded iterative refinement
+ operating deployment only after PASS
```

Tracks A and B may run in parallel.

Track C starts after A+B are on the same latest safe main.

Track D starts only after C deterministic/replay tests PASS.

Recommended branches:

```text
codex/us-index-numeric-block
codex/us-night-futures-reintegration
codex/us-full-message-renderer
codex/us-full-message-test-and-refine
```

---

# 3. Existing canonical night-futures facts

Do not invent a new numeric identity if the existing canonical facts remain supported.

Existing historical canonical identities include:

```text
market:night_futures:1
→ KOSPI200 야간선물 등락률
→ fields.change_pct
→ semantic_type = futures_return_pct

market:night_futures:2
→ KOSDAQ150 야간선물 등락률
→ fields.change_pct
→ semantic_type = futures_return_pct
```

Audit current code/registry before changing anything.

If these canonical facts still exist:

reuse them.

If their acquisition path disappeared:

restore the smallest compatible acquisition/packet propagation path.

Do not create duplicate aliases for the same economic fact.

---

# 4. Track A — explicit index numeric block

For every safe current completed US session, the user-facing message must explicitly show these five percentage returns:

```text
SPY
QQQ
IWM
SOXX
RSP
```

This is now a required baseline numeric block, not optional prose evidence.

Hard:

```text
SPY_RETURN_VISIBLE = PASS
QQQ_RETURN_VISIBLE = PASS
IWM_RETURN_VISIBLE = PASS
SOXX_RETURN_VISIBLE = PASS
RSP_RETURN_VISIBLE = PASS
```

---

# 5. Index numeric ownership

All five returns must come from backend-owned current-session facts.

AI must not calculate them from prices.

Hard:

```text
AI_CALCULATED_INDEX_RETURN = 0
UNREGISTERED_INDEX_RETURN = 0
INDEX_NUMBER_WITHOUT_PROVENANCE = 0
```

---

# 6. Index block formatting

Preferred format:

```text
📈 주요 지수
• SPY +0.66%
• QQQ +1.37%
• IWM +0.29%
• SOXX +1.95%
• RSP -0.30%
```

Rules:

```text
sign always visible
2 decimal places by default
preserve backend rounding policy if canonical formatter differs
no raw close required by default
```

Do not color-code or add unsupported arrows.

---

# 7. Current-session requirement

A displayed index return must be:

```text
CURRENT_DIRECTIONAL
```

for the target completed US session.

If an item is only:

```text
CURRENT_LEVEL_ONLY
SOURCE_UNAVAILABLE
```

do not fabricate a return.

Hard:

```text
NONCURRENT_INDEX_RETURN_VISIBLE = 0
LEVEL_ONLY_INDEX_DIRECTION_VISIBLE = 0
```

---

# 8. RSP dual role

RSP appears in two places semantically:

```text
📈 주요 지수
→ explicit numeric return

🔎 시장 내부
→ equal-weight participation/style interpretation
```

This is intentional, not duplicate noise.

The numeric block answers:

```text
what was the return?
```

The interpretation answers:

```text
what does it imply relative to cap-weighted market behavior?
```

Hard:

`RSP_AS_EXCHANGE_BREADTH = 0`

---

# 9. Track B — Korean night futures reintegration

Restore / preserve:

```text
KOSPI200 야간선물
KOSDAQ150 야간선물
```

as a dedicated `🌙 한국 야간선물` section in the US morning digest.

Do not mix them into `📈 주요 지수`.

---

# 10. Night-futures session mapping

The target US session date and Korean overnight-futures session date are not necessarily the same calendar date.

For a US completed session:

```text
US target session = YYYY-MM-DD US trading date
US morning digest = following KST morning
Korean night futures = overnight session relevant to the upcoming Korean regular session
```

The system must resolve the correct Korean overnight session explicitly.

Do not assume:

```text
night_futures.session_date == US target_session
```

Hard:

```text
NIGHT_FUTURES_SESSION_MAPPING = PASS
WRONG_NIGHT_FUTURES_SESSION_VISIBLE = 0
```

---

# 11. Night-futures freshness states

Introduce/reuse explicit state semantics such as:

```text
CURRENT_OVERNIGHT_DIRECTIONAL
CURRENT_OVERNIGHT_LEVEL_ONLY
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
STALE
```

Use repository-native enum names if equivalents already exist.

Only safe current overnight directional values may be rendered as:

```text
KOSPI200 야간선물 +x.xx%
KOSDAQ150 야간선물 +x.xx%
```

---

# 12. Night-futures provenance

Every displayed futures return must carry:

```text
fact_id
field_path
observation/session date
source
semantic type
unit
```

Hard:

```text
NIGHT_FUTURES_NUMERIC_PROVENANCE = PASS
AI_CALCULATED_NIGHT_FUTURES_RETURN = 0
UNREGISTERED_NIGHT_FUTURES_NUMERIC = 0
```

---

# 13. Night-futures missing-data behavior

If both are safely current:

show both.

If only one is safe:

show only the safe one.

If neither is safe:

omit the entire section.

Do not leave:

```text
🌙 한국 야간선물
```

as an empty heading.

Hard:

```text
EMPTY_NIGHT_FUTURES_SECTION = 0
STALE_NIGHT_FUTURES_AS_CURRENT = 0
```

---

# 14. No stale carry-forward

Do not carry forward a prior night's return merely because today's source is unavailable.

Hard:

```text
PRIOR_NIGHT_FUTURES_AS_CURRENT = 0
```

---

# 15. Night futures are not Korean regular-session index returns

Do not confuse:

```text
KOSPI200 야간선물
```

with:

```text
KOSPI200 regular-session return
```

or:

```text
KOSPI return
```

Hard:

`NIGHT_FUTURES_AS_REGULAR_INDEX = 0`

---

# 16. Track C — full-message renderer integration

Use one explicit renderer contract for the US market digest.

Required section order:

```text
🇺🇸 미국시장 마감

📈 주요 지수

🔎 시장 내부

🌙 한국 야간선물
(if safe current data exists)

🌐 보조 시장환경
(if material and temporally valid)

📌 다음 확인
```

Do not let AI reorder these sections arbitrarily.

---

# 17. Full-message section ownership

Recommended semantic ownership:

```text
HEADER
→ deterministic

INDEX_BLOCK
→ deterministic current-session numerics

MARKET_INTERNAL
→ shared US market digest plan
→ bounded AI/fallback interpretation

NIGHT_FUTURES
→ deterministic current overnight numerics

MACRO_CONTEXT
→ shared plan + temporal gate

NEXT_CHECK
→ bounded AI/fallback interpretation
```

The AI may help write interpretation but cannot remove required deterministic numeric sections.

---

# 18. `📈 주요 지수` is mandatory

When all five current returns are safely available:

all five must appear.

This section cannot be omitted for brevity.

Hard:

```text
MANDATORY_INDEX_BLOCK_OMITTED = 0
```

---

# 19. `🔎 시장 내부` content

Use current-session evidence already proven in production:

```text
semiconductor relative strength / weakness
RSP participation/style
material strongest sector
material weakest sector
breadth state if useful
```

User-facing target style:

```text
🔎 시장 내부
• 반도체가 상대적으로 강했습니다.
• 동일가중 RSP는 하락해 대형주 중심 상승 성격이 있었습니다.
• 업종 강세: 정보기술 +3.16%
• 업종 약세: 필수소비재 -1.38%
```

Exact wording must adapt to actual data.

---

# 20. Sector numeric visibility

When strongest/weakest sectors are selected by the shared plan:

show the backend-owned sector return numerically.

Hard:

```text
SELECTED_STRONG_SECTOR_RETURN_VISIBLE = PASS
SELECTED_WEAK_SECTOR_RETURN_VISIBLE = PASS
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0
```

---

# 21. RSP interpretation guard

Do not mechanically claim:

```text
대형주 중심 상승
```

just because RSP is negative.

Interpretation should compare RSP with SPY/current cap-weight behavior and other current evidence.

Examples:

```text
SPY positive + RSP negative
→ cap-weight leadership / narrower participation

SPY negative + RSP positive
→ equal-weight relative resilience

same direction / similar magnitude
→ participation less divergent
```

Hard:

`UNSUPPORTED_RSP_STYLE_INTERPRETATION = 0`

---

# 22. `🌐 보조 시장환경`

This section is secondary.

Potential items:

```text
nominal 10Y
real 10Y
VIX
WTI
USD/KRW
DXY / liquidity if supported
```

Only use if:

```text
current
or
explicitly date-qualified prior/reference context
```

Hard:

```text
STALE_MACRO_AS_CURRENT = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
```

---

# 23. Macro context must not crowd out market sections

Length priority:

```text
1. major-index numeric block
2. market-internal interpretation
3. Korean night futures
4. next-check
5. macro context
```

If length pressure occurs:

reduce macro details first.

Hard:

`MACRO_CROWDS_OUT_REQUIRED_MARKET_SECTION = 0`

---

# 24. Full target layout

Use this as a rendering contract, not hard-coded text:

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY +x.xx%
• QQQ +x.xx%
• IWM +x.xx%
• SOXX +x.xx%
• RSP +x.xx%

🔎 시장 내부
• <current-market interpretation>
• <RSP participation/style interpretation>
• 업종 강세: <sector> +x.xx%
• 업종 약세: <sector> -x.xx%

🌙 한국 야간선물
• KOSPI200 야간선물 +x.xx%
• KOSDAQ150 야간선물 +x.xx%

🌐 보조 시장환경
• <temporal-safe macro context>

📌 다음 확인
• <bounded next check>
```

---

# 25. AI / deterministic fallback parity

Both routes must preserve:

```text
same index numbers
same selected sector strong/weak numerics
same night-futures numbers
same temporal eligibility
same required section order
```

Exact explanatory prose may differ.

Hard:

```text
AI_FALLBACK_INDEX_BLOCK_PARITY = PASS
AI_FALLBACK_SECTOR_NUMERIC_PARITY = PASS
AI_FALLBACK_NIGHT_FUTURES_PARITY = PASS
AI_FALLBACK_SECTION_ORDER_PARITY = PASS
AI_FALLBACK_TEMPORAL_PARITY = PASS
```

---

# 26. Full-message evidence utilization

Create an explicit message-coverage map:

```text
SPY
QQQ
IWM
SOXX
RSP numeric
RSP interpretation
strongest sector
weakest sector
KOSPI200 night futures
KOSDAQ150 night futures
nominal yield
real yield
VIX
WTI
FX
next-check refs
```

Classify:

```text
MESSAGE_USED_REQUIRED
MESSAGE_USED_OPTIONAL
MESSAGE_OMITTED_SAFE
MESSAGE_OMITTED_MATERIAL_LOSS
```

Hard:

`US_FULL_MESSAGE_MATERIAL_INFORMATION_LOSS = 0`

---

# 27. Track D — dedicated test-sink validation

Use the existing dedicated non-production test sink.

Do NOT send to production recipients.

Run one production-equivalent full US morning message using the latest completed safe US session.

Default:

```text
TEST_US_MARKET_MESSAGE_COUNT = 1
```

---

# 28. Test-sink exact payload

Compare:

```text
renderer output
outbound test payload
receipt-linked received payload
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 29. Actual received-message visual review

Human-review the real received Telegram message.

Check:

```text
section order
blank lines
bullets
signs / percentages
index block readability
market-internal readability
night-futures visibility
macro section readability
message length
truncation
duplicate claims
```

Hard:

```text
FULL_MESSAGE_LAYOUT = PASS
TEST_MESSAGE_TRUNCATED = 0
TEST_FORMATTING_BROKEN = 0
TEST_MESSAGE_QUALITY = PASS
```

---

# 30. Iterative bounded refinement loop

The user explicitly wants to inspect the whole US message and improve it.

Allow at most:

```text
INITIAL_PASS + 2 bounded refinement passes
```

within this task.

Each refinement must be classified as:

```text
FORMATTING_ONLY
SELECTION_PRIORITY
MISSING_REQUIRED_SECTION
DUPLICATE_CONTENT
TEMPORAL_WORDING
OTHER_BOUNDED_RENDERER
```

No acquisition/provider redesign unless a true P1 defect is found.

---

# 31. Refinement loop rules

For each pass:

```text
1. save exact before message
2. state concrete defect
3. apply smallest change
4. regenerate exact message
5. diff
6. rerun provenance/temporal/section gates
7. test-sink send only if content changed materially
```

Maximum test sends in this task:

```text
3
```

All test sends must remain test-only and exactly once per version.

---

# 32. Stop refinement when stable

Stop iterative refinement when:

```text
all mandatory sections present
no material evidence loss
no stale/current confusion
message length acceptable
no duplicated interpretation
no unreadable dense sections
P0/P1 = 0/0
```

Do not endlessly polish wording.

P2 stylistic backlog may remain.

---

# 33. Deployment policy

After final test-sink PASS:

deploy through the normal operating path.

This is a US market-message renderer/evidence-presentation change only.

Do not alter:

```text
US Price Structure state
KR Price Structure state
KR market TOP3 state
Production Assist
packet claim ownership
exactly-once delivery system
```

---

# 34. Feature state

No new feature flag is required unless an existing US message renderer gate already owns this change.

Prefer code-default message layout after validation.

If a current renderer flag exists:

use the existing flag.

Do not create redundant rollout infrastructure.

---

# 35. Natural proof after deployment

Wait for the next natural US morning message.

Do not manually trigger.

Verify:

```text
index numeric block visible
market-internal interpretation visible
night futures visible when current/safe
macro temporal safety
exactly once
```

Then:

`US_FULL_MESSAGE = LIVE_PASS`

---

# 36. Night-futures natural-proof caveat

If the next natural US message has:

```text
night futures SOURCE_UNAVAILABLE / PUBLICATION_PENDING
```

the section may safely be omitted.

Do not fail natural proof solely because the source is legitimately unavailable.

But verify:

```text
state is explicit in evidence
no stale carry-forward
```

---

# 37. US Price Structure isolation

Hard:

```text
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_LEAK = 0
```

This task does not enable stock-level US SR/Fib.

---

# 38. KR isolation

Hard:

```text
KR_MARKET_DIGEST_CODE_DIFF = 0
KR_PRICE_STRUCTURE_RUNTIME_DIFF = 0
```

Except shared generic formatting helpers with proven exact parity.

---

# 39. Business-thesis isolation

Hard:

```text
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
BUSINESS_THESIS_MUTATION = 0
```

---

# 40. Focused Track A tests

Required:

```text
all five current directional → all visible
one level-only → no fake return
one unavailable → safe policy
positive / negative / near-zero formatting
2-decimal formatting
RSP numeric + interpretation dual use
```

---

# 41. Focused Track B tests

Required:

```text
both night futures current → both visible
one current / one unavailable → one visible
both unavailable → section omitted
prior night only → section omitted
wrong session mapping → validator fail
future session timestamp → fail
numeric provenance
```

---

# 42. Focused Track C tests

Required:

```text
full section order
mandatory index block
market-internal sector numeric
RSP interpretation
night-futures placement
macro secondary placement
macro section omitted when no safe macro
next-check
AI/fallback parity
```

---

# 43. Focused Track D tests

Required:

```text
test sink isolation
exact payload
Telegram formatting
full-message length
refinement diff discipline
max 3 test sends
production-intent isolation
```

---

# 44. Full regression

Required before deployment:

```text
focused A/B/C/D tests
US natural-message tests
shared market plan tests
evidence-utilization validator tests
macro temporal tests
packet claim / exactly-once regression
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
```

No Public Action change expected.

---

# 45. Required architecture / policy docs

Create/update:

```text
docs/architecture/US_MORNING_MESSAGE_LAYOUT.md
docs/architecture/US_MARKET_DIGEST_EVIDENCE_OWNERSHIP.md
docs/architecture/KOREA_NIGHT_FUTURES_IN_US_MORNING.md
docs/architecture/US_FULL_MESSAGE_REFINEMENT_POLICY.md
```

---

# 46. Required reports

Create:

1. `docs/reports/20260828-us-index-block-policy.md`
2. `docs/reports/20260828-us-night-futures-root-cause.md`
3. `docs/reports/20260828-us-night-futures-session-mapping.md`
4. `docs/reports/20260828-us-night-futures-provenance.md`
5. `docs/reports/20260828-us-full-message-layout.md`
6. `docs/reports/20260828-us-full-message-before-after.md`
7. `docs/reports/20260828-us-full-message-ai-fallback-parity.md`
8. `docs/reports/20260828-us-full-message-evidence-utilization.md`
9. `docs/reports/20260828-us-full-message-test-delivery.md`
10. `docs/reports/20260828-us-full-message-exact-test-message.md`
11. `docs/reports/20260828-us-full-message-refinement-history.md`
12. `docs/reports/20260828-us-full-message-quality.md`
13. `docs/reports/20260828-us-full-message-safety-parity.md`
14. `docs/reports/20260828-us-full-message-readiness.md`
15. `docs/reports/20260828-us-full-message-natural-proof-status.md`
16. `docs/reports/20260828-us-full-message-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-full-message-evidence-utilization.json
docs/reports/20260828-us-full-message-readiness.json
```

---

# 47. Required gates

Set exactly:

```text
US_INDEX_BLOCK_POLICY =
PASS / FAIL

SPY_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

QQQ_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

IWM_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

SOXX_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

RSP_RETURN_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

AI_CALCULATED_INDEX_RETURN =
0 / NONZERO

UNREGISTERED_INDEX_RETURN =
0 / NONZERO

NONCURRENT_INDEX_RETURN_VISIBLE =
0 / NONZERO

MANDATORY_INDEX_BLOCK_OMITTED =
0 / NONZERO

NIGHT_FUTURES_CANONICAL_FACT_REUSE =
PASS / NOT_AVAILABLE / FAIL

NIGHT_FUTURES_SESSION_MAPPING =
PASS / FAIL

NIGHT_FUTURES_NUMERIC_PROVENANCE =
PASS / PARTIAL_SAFE / FAIL

KOSPI200_NIGHT_FUTURES_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

KOSDAQ150_NIGHT_FUTURES_VISIBLE =
PASS / NOT_AVAILABLE / FAIL

WRONG_NIGHT_FUTURES_SESSION_VISIBLE =
0 / NONZERO

STALE_NIGHT_FUTURES_AS_CURRENT =
0 / NONZERO

PRIOR_NIGHT_FUTURES_AS_CURRENT =
0 / NONZERO

EMPTY_NIGHT_FUTURES_SECTION =
0 / NONZERO

NIGHT_FUTURES_AS_REGULAR_INDEX =
0 / NONZERO

US_FULL_MESSAGE_LAYOUT =
PASS / FAIL

SELECTED_STRONG_SECTOR_RETURN_VISIBLE =
PASS / NOT_SELECTED / FAIL

SELECTED_WEAK_SECTOR_RETURN_VISIBLE =
PASS / NOT_SELECTED / FAIL

UNSUPPORTED_RSP_STYLE_INTERPRETATION =
0 / NONZERO

MACRO_CROWDS_OUT_REQUIRED_MARKET_SECTION =
0 / NONZERO

STALE_MACRO_AS_CURRENT =
0 / NONZERO

AI_FALLBACK_INDEX_BLOCK_PARITY =
PASS / FAIL

AI_FALLBACK_SECTOR_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_NIGHT_FUTURES_PARITY =
PASS / FAIL

AI_FALLBACK_SECTION_ORDER_PARITY =
PASS / FAIL

AI_FALLBACK_TEMPORAL_PARITY =
PASS / FAIL

US_FULL_MESSAGE_MATERIAL_INFORMATION_LOSS =
0 / NONZERO

TEST_US_MARKET_MESSAGE_COUNT =
...

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL / NOT_SENT

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

FULL_MESSAGE_LAYOUT =
PASS / FAIL

TEST_MESSAGE_TRUNCATED =
0 / NONZERO

TEST_FORMATTING_BROKEN =
0 / NONZERO

TEST_MESSAGE_QUALITY =
PASS / FAIL

REFINEMENT_PASS_COUNT =
0 / 1 / 2

REFINEMENT_EXCEEDED_BOUND =
0 / NONZERO

US_PRICE_STRUCTURE_ENABLED =
0 / NONZERO

US_PRICE_STRUCTURE_LEAK =
0 / NONZERO

KR_MARKET_DIGEST_CODE_DIFF =
0 / NONZERO

BUSINESS_THESIS_MUTATION =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

US_FULL_MESSAGE =
TEST_PASS_READY_TO_DEPLOY /
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL
```

---

# 48. Hard PASS rule before deployment

Require:

```text
index block correct
night-futures session/provenance safe
full section order correct
selected sector numerics visible
RSP interpretation safe
macro temporal gate safe
AI/fallback parity PASS
test-sink exact payload PASS
message quality PASS
material information loss = 0
P0 = 0
material P1 = 0
```

Then:

`US_FULL_MESSAGE = TEST_PASS_READY_TO_DEPLOY`

---

# 49. Deployment state

After normal deployment and smoke:

`US_FULL_MESSAGE = DEPLOYED_AWAITING_NATURAL_PROOF`

Do not claim `LIVE_PASS` until a natural US morning run proves it.

---

# 50. Completion response

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
TRACK_D_IMPLEMENTATION = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

TARGET_SESSION = ...

US_INDEX_BLOCK_POLICY = ...

SPY = ...
QQQ = ...
IWM = ...
SOXX = ...
RSP = ...

SPY_RETURN_VISIBLE = ...
QQQ_RETURN_VISIBLE = ...
IWM_RETURN_VISIBLE = ...
SOXX_RETURN_VISIBLE = ...
RSP_RETURN_VISIBLE = ...

NIGHT_FUTURES_CANONICAL_FACT_REUSE = ...

KOSPI200_NIGHT_FUTURES = ...
KOSPI200_NIGHT_FUTURES_SESSION = ...
KOSPI200_NIGHT_FUTURES_STATE = ...

KOSDAQ150_NIGHT_FUTURES = ...
KOSDAQ150_NIGHT_FUTURES_SESSION = ...
KOSDAQ150_NIGHT_FUTURES_STATE = ...

NIGHT_FUTURES_SESSION_MAPPING = ...
NIGHT_FUTURES_NUMERIC_PROVENANCE = ...

SECTOR_STRONGEST = ...
SECTOR_WEAKEST = ...

US_FULL_MESSAGE_LAYOUT = ...

EXACT_TEST_MESSAGE =
...

TEST_US_MARKET_MESSAGE_COUNT = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0

REFINEMENT_PASS_COUNT = ...
REFINEMENT_HISTORY = ...

US_FULL_MESSAGE_MATERIAL_INFORMATION_LOSS = 0

US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_LEAK = 0
KR_MARKET_DIGEST_CODE_DIFF = 0
BUSINESS_THESIS_MUTATION = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

US_FULL_MESSAGE =
TEST_PASS_READY_TO_DEPLOY /
DEPLOYED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_US_FULL_MESSAGE_PROOF =
PENDING /
PASS /
FAIL

NEXT_ACTION =
DEPLOY_US_FULL_MESSAGE /
WAIT_FOR_NEXT_NATURAL_US_MORNING /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 51. Mandatory completion ZIP

Create:

`20260828-us-morning-full-message-integration-and-iterative-validation-bundle.zip`

Include:

```text
exact master instruction
all track instructions
index block policy
night-futures root cause/session/provenance
full-message layout
before/after messages
AI/fallback parity
evidence-utilization
test-delivery evidence
exact test message(s)
refinement history
message-quality review
safety parity
deployment status
natural-proof status
readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw sink IDs
auth headers
tokens
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 52. Final principle

The US morning message should let the user verify the interpretation from the raw headline numbers.

Therefore:

```text
first show the major index returns,
then explain market internals,
then show Korea-relevant overnight futures,
then add temporally safe macro context.
```

Do not hide the five core returns behind prose.

Do not lose night futures if current safe canonical facts exist.

Do not let stale macro replace current market evidence.

And from this point onward, review the entire exact message as a product and make only bounded, evidence-safe refinements.
