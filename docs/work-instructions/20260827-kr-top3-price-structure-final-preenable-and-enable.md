# thesis-monitor — KR TOP3 + Price Structure Final Pre-Enable & KR-Only Enablement
## Dedicated test sink → market + all monitored KR stock test messages → operating promotion → sequential KR-only flags → natural proof
## No further calculation repair in this task

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_TOP3_PRICE_STRUCTURE_FINAL_PREENABLE_AND_ENABLE`
- Task class: `CONTROLLED_KR_ONLY_PREENABLE_AND_RUNTIME_ENABLEMENT`
- Source policy: preserve current production source policy
- Production Assist: preserve `OFF`
- US Price Structure: preserve `OFF`
- Telegram production-recipient test sends: `0`
- Manual production scheduler execution: `0`
- DB / official assessment mutation: `0`
- Historical archive rewrite: `0`

### Latest validated Price Structure / data-contract lineage

The immediately preceding bounded repair completed with:

```text
Instruction commit:
3e42f3fad2e32ff1b3cca47861cfb9704095ce28

Base:
48a699798462639b27056523ef8fdd94b261092b

Track A:
c9e8fc1e25394857bd88d4652e3a8b1e88638011

Track B:
d60b7b2a9edecbad0ed54c2151ecfba163478522

Track C:
f957bea48e1bf8df23c6b8fe769812ade5663456

Final main:
0ede6a0eb3335371322d1f7921b350d07f669f9a

Operating:
43731f015901b96e2dee3af009b9e1d074382349
(intentionally not promoted)
```

Validated gates:

```text
KR_DAILY_1200_REPAIR = REPLAY_PASS_READY_FOR_PREENABLE
DAILY_1200_PROVIDER_CAPABILITY = PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW
DAILY_1200_IMPLEMENTATION_PATH = VERIFIED_PARTIAL_SAFE_1000
KR_DAILY_1200_COVERAGE = VERIFIED_PARTIAL_SAFE_1000

canonical daily target = 1200
official thesis-monitor provider cap = 1000
actual completed daily = 1000
coverage = PARTIAL_SAFE/provider_limit

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
UNSTABLE_FIB_EXPOSED = 0

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

The previous validation also confirmed these runtime flags remained false:

```text
kr_market_sector_top3_enabled = false
kr_price_structure_v3_enabled = false
Production Assist = OFF
```

Before execution:

1. `git fetch origin`
2. verify all relevant worktrees clean
3. resolve actual latest safe `origin/main`
4. require it to contain `0ede6a0...` or a safe linear descendant
5. resolve actual current operating SHA
6. do not discard any validated repair
7. record exact lineage

---

# 1. Objective

This is the final KR-only pre-enable flow.

Execute in strict order:

```text
TRACK A
Dedicated non-production test sink configuration + isolation proof

TRACK B
Latest completed KR session
→ production-equivalent data
→ KR market TOP3 digest
→ all currently monitored KR stock messages with Price Structure policy
→ send every test artifact exactly once to test sink
→ exact payload / formatting / provenance review

TRACK C
Only after Track B PASS:
1. promote latest validated main to operating with KR flags still OFF
2. health/smoke
3. enable KR market TOP3 flag only
4. smoke
5. enable KR Price Structure flag only
6. smoke
7. prove US Price Structure still OFF
8. wait for next natural KR messages
```

No additional Price Structure calculation redesign is authorized.

---

# 2. Strict stage dependency

Do not overlap enablement with preflight.

Required state sequence:

```text
A PASS
→ B PASS
→ operating promotion with both KR flags OFF
→ health PASS
→ TOP3 flag ON
→ smoke PASS
→ Price Structure KR flag ON
→ smoke PASS
→ ENABLED_AWAITING_NATURAL_PROOF
```

If any stage fails:

```text
STOP
ROLL BACK current stage if changed
DO NOT continue
```

---

# 3. Track A — dedicated test sink

Configure exactly one existing/approved non-production notification destination through the repository's
existing secret/config mechanism.

Do not create a parallel notification framework.

Required:

```text
test sink alias
test sink redacted hash
production sink redacted hash
```

Never expose raw private IDs.

Hard:

```text
TEST_SINK_AVAILABLE = YES
TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0
SECRET_IN_REPO = 0
PRIVATE_SINK_ID_IN_REPORT = 0
```

If a safe test sink cannot be configured:

```text
STOP
KR_FINAL_PREENABLE = BLOCKED_NO_TEST_SINK
```

No production-recipient substitute.

---

# 4. Test-only delivery namespace

Use a clearly non-production delivery identity:

```text
TEST_ONLY
KR_FINAL_PREENABLE
NON_PRODUCTION
```

Production sender/receipt logic must not consume it.

Hard:

```text
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
```

---

# 5. No manual production scheduler

Do not manually execute:

```text
KR afternoon production scheduler
stock-monitoring production scheduler
```

Use the existing safe preflight/replay/test harness and production-equivalent data builders.

Hard:

`MANUAL_PRODUCTION_TASK = 0`

---

# 6. Track B target session

Resolve the latest completed KR regular session dynamically.

If this task is still executed after 2026-08-27 close and before the next completed close:

```text
TARGET_KR_SESSION = 2026-08-27
```

If later:

use the latest genuinely completed KR session.

Never use an incomplete bar/session.

---

# 7. Production-equivalent KR market data

Collect exactly the currently supported production families:

```text
ka20001
→ KOSPI/KOSDAQ index + breadth

ka20003
→ size/style + sector rows

ka10051
→ aggregate foreign/institution/retail

ka10066
→ full stock-level pagination + reconciliation evidence
```

Run current:

```text
numeric semantic registry
provenance
AI eligibility
KR local-first plan
TOP3 sector selection
```

---

# 8. Market-data hard gates

Required before market message send:

```text
KIWOOM_KA20001 = PASS / PARTIAL_SAFE
KIWOOM_KA20003 = PASS / PARTIAL_SAFE
KIWOOM_KA10051 = PASS

KOSPI_KA10066_PAGINATION = PASS
KOSDAQ_KA10066_PAGINATION = PASS

NUMERIC_GATE = PASS
SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0

KR_LOCAL_FIRST_PLAN = PASS
```

If expected same-session data is unexpectedly absent:

STOP before test send.

---

# 9. Reconciliation remains fail-closed

Recompute current-session:

```text
ka10051 aggregate
vs
sum ka10066
```

Use existing tolerance.

Do not widen.

If unresolved:

```text
concentration = BLOCKED_RECONCILIATION
```

Hard:

```text
RECONCILIATION_TOLERANCE_WIDENED = 0
UNRECONCILED_CONCENTRATION_PROSE = 0
```

---

# 10. KR market message content

The market test message must preserve:

```text
1. KOSPI/KOSDAQ direction
2. breadth
3. foreign/institution/retail aggregate flow
4. size/style
5. KOSPI relative strong TOP3
6. KOSPI relative weak TOP3
7. KOSDAQ relative strong TOP3
8. KOSDAQ relative weak TOP3
9. global context only as secondary
```

---

# 11. TOP3 sector deterministic ownership

TOP3 ranking must be backend deterministic.

AI must not rank raw rows.

User-facing terminology:

```text
업종 상대 강세
업종 상대 약세
```

Never:

```text
leader
laggard
```

Hard:

```text
AI_DERIVED_SECTOR_RANKING = 0
SECTOR_TOP3_DUPLICATE = 0
STALE_SECTOR_IN_TOP3 = 0
USER_FACING_LEADER_LAGGARD_TERM = 0
SECTOR_RETURN_AS_SECTOR_BREADTH = 0
```

---

# 12. Market test message required visibility

When enough safe rows exist:

```text
TEST_MARKET_DIRECTION_VISIBLE = PASS
TEST_MARKET_BREADTH_VISIBLE = PASS
TEST_MARKET_FLOW_VISIBLE = PASS
TEST_MARKET_SIZE_STYLE_VISIBLE = PASS

TEST_KOSPI_STRONG_TOP3_VISIBLE = PASS
TEST_KOSPI_WEAK_TOP3_VISIBLE = PASS
TEST_KOSDAQ_STRONG_TOP3_VISIBLE = PASS
TEST_KOSDAQ_WEAK_TOP3_VISIBLE = PASS
```

If fewer than 3 safe rows exist for one side:

render only available safe rows and record `PARTIAL_SAFE`.

No fabricated fill.

---

# 13. Current monitored KR stock universe

Use the actual current monitored KR universe at execution time.

The validated regression universe was:

```text
000660
003690
005490
005930
010120
012450
086280
```

If unchanged, test all seven.

If the current monitored KR universe differs:

test ALL currently monitored KR tickers and report the exact diff.

This final preflight intentionally tests the full bounded KR monitored universe, not a sample.

---

# 14. Price Structure daily coverage contract

For each KR ticker preserve:

```text
canonical requested daily = 1200
official provider cap = 1000
actual completed = up to 1000
coverage = PARTIAL_SAFE/provider_limit
```

Do not label 1000 as full 1200 coverage.

Hard:

```text
CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 = 0
PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0
SYNTHETIC_DAILY_BARS = 0
```

---

# 15. Price Structure eligibility

Use existing runtime eligibility only:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT_PRICE_STRUCTURE
BLOCKED
```

Do not hard-code that all current KR names are SR-only.

Recompute using latest completed session.

---

# 16. ELIGIBLE renderer

For `ELIGIBLE`:

```text
📐 현재 가격 구조

가까운 지지
가까운 저항

주요 구조 지지/저항 when available

Fib/SR 겹침
only when safe/material
```

No target/stop conversion.

---

# 17. ELIGIBLE_SR_ONLY renderer

For `ELIGIBLE_SR_ONLY`:

```text
safe deterministic SR
```

No Fib line.

Hard:

```text
SR_ONLY_EMPTY_FIB_LINE = 0
UNSTABLE_FIB_EXPOSED = 0
```

---

# 18. OMIT/BLOCKED renderer

For:

```text
OMIT_PRICE_STRUCTURE
BLOCKED
```

omit the v3 block and preserve the rest of the stock message.

Hard:

`PRICE_STRUCTURE_BLOCK_FAILS_WHOLE_MESSAGE = 0`

---

# 19. User-facing proximity safety

Preserve the repaired proximity contract:

```text
LONG_HORIZON
≠ 가까운

internal nearest available
≠ automatically user-visible 가까운
```

Hard:

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
FABRICATED_SR_FILL = 0
```

---

# 20. Current vs stored price ownership

Preserve:

```text
📐 현재 가격 구조
🧭 기존 등록 가격 규칙
```

Hard:

```text
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
UNLABELED_CURRENT_STORED_PRICE_CONFLICT = 0
```

---

# 21. Numeric ownership

All Price Structure numbers are backend-owned.

Hard:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 22. Fib policy

Fib remains optional.

Only expose if current eligibility/family-safety permits.

Hard:

```text
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0
```

The prior seven-ticker replay being SR-only does NOT authorize forcing Fib.

---

# 23. Stock-message AI/fallback parity

For every currently monitored KR stock:

generate both:

```text
AI candidate
deterministic fallback candidate
```

using identical packet/Price Structure facts.

Required safety parity:

```text
AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY = PASS
AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY = PASS
```

Exact prose need not match.

---

# 24. Test-send message count

Default test-send scope:

```text
1 KR market digest
+
1 message for every current monitored KR stock
```

If the current monitored set remains seven:

```text
TEST_MARKET_MESSAGE_COUNT = 1
TEST_STOCK_MESSAGE_COUNT = 7
TEST_TOTAL_MESSAGE_COUNT = 8
```

Do not silently sample fewer.

---

# 25. Test route

For each test artifact, use the same route production would choose:

```text
AI if production eligibility says AI
otherwise deterministic fallback
```

Record route per message.

Do not choose by aesthetics.

---

# 26. Exactly-once test delivery

Every test artifact must be delivered exactly once to the dedicated test sink.

Hard:

```text
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_UNOWNED_RETRY = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

No automatic resend after successful receipt.

---

# 27. Exact payload proof

For every test message compare:

```text
rendered payload
outbound test payload
receipt-linked / received payload
```

Hard:

`TEST_EXACT_PAYLOAD_MATCH = PASS`

Store payload hashes.

---

# 28. Actual received formatting review

Inspect the actual received messages.

Market digest:

```text
line breaks
TOP3 readability
KOSPI/KOSDAQ separation
size/style readability
no truncation
```

Stock messages:

```text
company header
investment logic/business text
current price structure block
stored-rule separation
no empty Fib
no stale legacy technical prose
no truncation
```

Hard:

```text
TEST_FORMATTING_BROKEN = 0
TEST_MESSAGE_TRUNCATED = 0
TEST_MESSAGE_QUALITY = PASS
```

---

# 29. Pre-enable full test gates

Do not promote/enable unless:

```text
TEST_SINK_AVAILABLE = YES
all market-data gates PASS
TOP3 market message PASS
all monitored KR stock messages PASS
Price Structure provenance PASS
proximity validator PASS
AI/fallback parity PASS
exact payload PASS
formatting PASS
test exactly-once PASS
P0 = 0
material P1 = 0
```

---

# 30. Track C — promote code with flags still OFF

Only after Track B PASS:

promote the latest validated main containing all repairs to operating.

At this step REQUIRE:

```text
kr_market_sector_top3_enabled = false
kr_price_structure_v3_enabled = false
US Price Structure = false
Production Assist = OFF
```

Then:

```text
restart/reload using normal deployment procedure
API health
provider health
smoke render with flags OFF
```

Hard:

```text
FEATURE_OFF_PARITY = PASS
```

---

# 31. Enable market TOP3 first

After operating health PASS:

set only:

```text
kr_market_sector_top3_enabled = true
```

Keep:

```text
kr_price_structure_v3_enabled = false
US Price Structure = false
```

Run read-only market smoke.

Required:

```text
POST_TOP3_ENABLE_MARKET = PASS
POST_TOP3_ENABLE_STOCK_PRICE_STRUCTURE_LEAK = 0
```

If fail:

rollback TOP3 flag and STOP.

---

# 32. Enable KR Price Structure second

Only after TOP3 smoke PASS:

set:

```text
kr_price_structure_v3_enabled = true
```

Scope must remain:

```text
current monitored KR universe only
```

Keep US OFF.

Run read-only stock smoke for the full monitored KR universe.

Required:

```text
POST_KR_PRICE_STRUCTURE_ENABLE = PASS
POST_ENABLE_US_PRICE_STRUCTURE_LEAK = 0
```

If fail:

rollback only KR Price Structure flag and STOP.

---

# 33. Existing flags only

Use existing flags/config:

```text
kr_market_sector_top3_enabled
kr_price_structure_v3_enabled
```

Do not introduce new rollout systems.

If exact names differ in code:

use repository-native existing names and report mapping.

---

# 34. Final enabled state before natural proof

After both smokes PASS:

```text
KR market TOP3 = ON
KR Price Structure = ON
US Price Structure = OFF
Production Assist = OFF
```

Set:

`KR_ROLLOUT = ENABLED_AWAITING_NATURAL_PROOF`

Do not claim LIVE_PASS yet.

---

# 35. Natural KR market proof

Wait for next naturally scheduled KR afternoon close.

Do not manually trigger.

Verify:

```text
correct completed session
exactly once
direction/breadth/flow
size/style
KOSPI strong/weak TOP3
KOSDAQ strong/weak TOP3
no concentration leak
```

Hard:

```text
NATURAL_KR_MARKET_TOP3 = PASS
NATURAL_KR_MARKET_DUPLICATE = 0
NATURAL_KR_MARKET_ORPHAN = 0
```

---

# 36. Natural KR stock proof

Wait for next natural KR monitored-stock message cycle.

Verify across naturally included monitored KR names:

```text
eligibility respected
SR block visible where eligible
Fib only where safe
remote zones not "가까운"
stored rules separated
no target/stop
exactly once
```

Hard:

```text
NATURAL_KR_PRICE_STRUCTURE = PASS
NATURAL_KR_PRICE_STRUCTURE_NUMERIC_SAFETY = PASS
NATURAL_KR_STOCK_DUPLICATE = 0
NATURAL_KR_STOCK_ORPHAN = 0
```

---

# 37. US isolation after enablement

Prove:

```text
US Price Structure flag/state = OFF
```

and a read-only US candidate does not gain Price Structure because of KR enablement.

Hard:

```text
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_RUNTIME_DIFF = 0
US_MARKET_DIGEST_CODE_DIFF = 0
```

---

# 38. Business / valuation isolation

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF_FROM_KR_ENABLEMENT = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
```

---

# 39. Rollback

Document exact rollback:

```text
kr_price_structure_v3_enabled = false
kr_market_sector_top3_enabled = false
```

Rollback can be independent.

No DB cleanup.

If a natural live defect occurs:

disable only the affected flag first.

---

# 40. Tests before operating promotion

Required:

```text
dedicated test-sink routing tests
production/test collision tests
TOP3 selection tests
KR local-first tests
all monitored KR Price Structure replay
daily PARTIAL_SAFE/provider_limit tests
proximity validator tests
Fib family-safety tests
stored-rule ownership tests
AI/fallback parity
numeric provenance
exact payload tests

full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
OHLCV health
```

No Public Action change expected.

---

# 41. Required reports

Create:

1. `docs/reports/20260827-kr-final-test-sink-configuration.md`
2. `docs/reports/20260827-kr-final-test-sink-isolation.md`
3. `docs/reports/20260827-kr-final-preflight-target-session.md`
4. `docs/reports/20260827-kr-final-market-data.md`
5. `docs/reports/20260827-kr-final-market-top3-message.md`
6. `docs/reports/20260827-kr-final-price-structure-per-ticker.md`
7. `docs/reports/20260827-kr-final-ai-fallback-parity.md`
8. `docs/reports/20260827-kr-final-test-delivery.md`
9. `docs/reports/20260827-kr-final-exact-test-messages.md`
10. `docs/reports/20260827-kr-final-test-message-quality.md`
11. `docs/reports/20260827-kr-final-operating-promotion.md`
12. `docs/reports/20260827-kr-final-top3-enablement.md`
13. `docs/reports/20260827-kr-final-price-structure-enablement.md`
14. `docs/reports/20260827-kr-final-post-enable-smoke.md`
15. `docs/reports/20260827-kr-final-natural-proof-status.md`
16. `docs/reports/20260827-kr-final-rollout-safety-parity.md`
17. `docs/reports/20260827-kr-final-rollout-readiness.md`
18. `docs/reports/20260827-kr-final-rollout-artifact-index.md`

Machine-readable:

```text
docs/reports/20260827-kr-final-price-structure-per-ticker.json
docs/reports/20260827-kr-final-test-delivery.json
docs/reports/20260827-kr-final-rollout-readiness.json
```

Never include raw sink IDs or secrets.

---

# 42. Required gates

Set exactly:

```text
TEST_SINK_AVAILABLE =
YES / NO

TEST_PRODUCTION_SINK_COLLISION =
0 / NONZERO

TEST_PRODUCTION_INTENT_COLLISION =
0 / NONZERO

SECRET_IN_REPO =
0 / NONZERO

PREENABLE_TARGET_SESSION =
...

PREENABLE_DATA_COLLECTION =
PASS / FAIL

KR_LOCAL_FIRST_PLAN =
PASS / FAIL

NUMERIC_GATE =
PASS / FAIL

KOSPI_STRONG_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

KOSPI_WEAK_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

KOSDAQ_STRONG_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

KOSDAQ_WEAK_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

USER_FACING_LEADER_LAGGARD_TERM =
0 / NONZERO

CURRENT_KR_MONITORED_STOCK_COUNT =
...

TEST_MARKET_MESSAGE_COUNT =
...

TEST_STOCK_MESSAGE_COUNT =
...

TEST_TOTAL_MESSAGE_COUNT =
...

ALL_KR_STOCK_PRICE_STRUCTURE_REPLAY =
PASS / FAIL

PRICE_STRUCTURE_ELIGIBLE_RENDER =
PASS / NOT_OBSERVED / FAIL

PRICE_STRUCTURE_SR_ONLY_RENDER =
PASS / NOT_OBSERVED / FAIL

PRICE_STRUCTURE_OMIT_BLOCKED_RENDER =
PASS / NOT_OBSERVED / FAIL

CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 =
0 / NONZERO

PROVIDER_LIMIT_MISREPORTED_AS_FULL =
0 / NONZERO

LONG_HORIZON_RENDERED_AS_NEAR =
0 / NONZERO

REMOTE_ZONE_PROMOTED_AS_NEAR_FILL =
0 / NONZERO

RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY =
0 / NONZERO

UNSTABLE_FIB_EXPOSED =
0 / NONZERO

CURRENT_SR_RENDERED_AS_STORED_RULE =
0 / NONZERO

STORED_RULE_RENDERED_AS_CURRENT_SR =
0 / NONZERO

AI_CALCULATED_TECHNICAL_PRICE =
0 / NONZERO

UNREGISTERED_PRICE_STRUCTURE_NUMERIC =
0 / NONZERO

UNSUPPORTED_TARGET_PRICE =
0 / NONZERO

UNSUPPORTED_STOP_PRICE =
0 / NONZERO

AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY =
PASS / FAIL

AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY =
PASS / FAIL

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL / NOT_SENT

TEST_MESSAGE_QUALITY =
PASS / FAIL / NOT_SENT

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_UNOWNED_RETRY =
0 / NONZERO

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

FEATURE_OFF_PARITY =
PASS / NOT_RUN / FAIL

KR_MARKET_TOP3_ENABLED =
true / false

POST_TOP3_ENABLE_MARKET =
PASS / NOT_RUN / FAIL

POST_TOP3_ENABLE_STOCK_PRICE_STRUCTURE_LEAK =
0 / NONZERO

KR_PRICE_STRUCTURE_ENABLED =
true / false

POST_KR_PRICE_STRUCTURE_ENABLE =
PASS / NOT_RUN / FAIL

US_PRICE_STRUCTURE_ENABLED =
0 / NONZERO

POST_ENABLE_US_PRICE_STRUCTURE_LEAK =
0 / NONZERO

PRODUCTION_ASSIST =
OFF / OTHER

BUSINESS_THESIS_MUTATION =
0 / NONZERO

VALUATION_TEXT_DIFF_FROM_KR_ENABLEMENT =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

KR_FINAL_PREENABLE =
PASS /
BLOCKED /
FAIL

KR_ROLLOUT =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_KR_MARKET_TOP3 =
PENDING / PASS / FAIL

NATURAL_KR_PRICE_STRUCTURE =
PENDING / PASS / FAIL
```

---

# 43. Pre-enable PASS rule

Set:

```text
KR_FINAL_PREENABLE = PASS
```

only if:

```text
safe dedicated test sink exists
full current KR market packet PASS
TOP3 market message PASS
ALL current monitored KR stocks replay PASS
all test messages delivered exactly once to test sink
exact payloads match
formatting PASS
numeric provenance PASS
proximity safety PASS
Fib safety PASS
stored-rule separation PASS
production recipients untouched
P0 = 0
material P1 = 0
```

Only then proceed to Track C enablement.

---

# 44. Enablement PASS rule

After:

```text
operating promotion with flags OFF
→ health PASS
→ TOP3 ON + smoke PASS
→ KR Price Structure ON + smoke PASS
→ US OFF proof
```

set:

```text
KR_ROLLOUT = ENABLED_AWAITING_NATURAL_PROOF
```

---

# 45. Final LIVE_PASS rule

Only after both natural proofs:

```text
NATURAL_KR_MARKET_TOP3 = PASS
NATURAL_KR_PRICE_STRUCTURE = PASS
```

and:

```text
natural duplicates/orphans = 0
US Price Structure leak = 0
P0/P1 = 0/0
```

set:

`KR_ROLLOUT = LIVE_PASS`

---

# 46. Stop conditions

STOP / DO NOT ENABLE if:

```text
no dedicated safe test sink
test sink collides with production
test message reaches production recipient
current KR market data unsafe
TOP3 stale/duplicate
any monitored KR stock fails Price Structure validator
remote zone appears as 가까운
unstable Fib appears
unsupported numeric appears
stored/current price-rule ownership merges
target/stop is invented
test duplicate/orphan
operating health fails
feature OFF parity fails
US Price Structure turns on
new P0
new material P1
```

---

# 47. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...
LATEST_VALIDATED_MAIN = ...
PREVIOUS_OPERATING = ...

TRACK_A_BRANCH = ...
TRACK_A_RESULT = ...

TRACK_B_BRANCH = ...
TRACK_B_RESULT = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

FINAL_MAIN = ...
OPERATING = ...

PREENABLE_TARGET_SESSION = ...

TEST_SINK_AVAILABLE = ...
TEST_SINK_ALIAS = ...
TEST_SINK_REDACTED_HASH = ...
PRODUCTION_SINK_REDACTED_HASH = ...
TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0

PREENABLE_DATA_COLLECTION = ...
KR_LOCAL_FIRST_PLAN = ...
NUMERIC_GATE = ...

KOSPI_STRONG_TOP3 = ...
KOSPI_WEAK_TOP3 = ...
KOSDAQ_STRONG_TOP3 = ...
KOSDAQ_WEAK_TOP3 = ...

CURRENT_KR_MONITORED_STOCK_COUNT = ...
KR_STOCK_TICKERS = ...

ALL_KR_STOCK_PRICE_STRUCTURE_REPLAY = ...

PRICE_STRUCTURE_ELIGIBLE_COUNT = ...
PRICE_STRUCTURE_SR_ONLY_COUNT = ...
PRICE_STRUCTURE_OMIT_COUNT = ...
PRICE_STRUCTURE_BLOCKED_COUNT = ...

PER_TICKER_PRICE_STRUCTURE_AUDIT = ...

TEST_MARKET_MESSAGE_COUNT = ...
TEST_STOCK_MESSAGE_COUNT = ...
TEST_TOTAL_MESSAGE_COUNT = ...

TEST_EXACT_PAYLOAD_MATCH = ...
TEST_MESSAGE_QUALITY = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_UNOWNED_RETRY = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 = 0
PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0

UNSTABLE_FIB_EXPOSED = 0
CURRENT_SR_RENDERED_AS_STORED_RULE = 0
STORED_RULE_RENDERED_AS_CURRENT_SR = 0
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0

KR_FINAL_PREENABLE = ...

OPERATING_PROMOTION = ...
FEATURE_OFF_PARITY = ...

KR_MARKET_TOP3_ENABLED = ...
POST_TOP3_ENABLE_MARKET = ...

KR_PRICE_STRUCTURE_ENABLED = ...
POST_KR_PRICE_STRUCTURE_ENABLE = ...

US_PRICE_STRUCTURE_ENABLED = 0
POST_ENABLE_US_PRICE_STRUCTURE_LEAK = 0
PRODUCTION_ASSIST = OFF

BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF_FROM_KR_ENABLEMENT = 0

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

KR_ROLLOUT =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_KR_MARKET_TOP3 =
PENDING /
PASS /
FAIL

NATURAL_KR_PRICE_STRUCTURE =
PENDING /
PASS /
FAIL

ROLLBACK_TOP3 = ...
ROLLBACK_PRICE_STRUCTURE = ...

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_MESSAGES /
NO_ACTION /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 48. Mandatory completion ZIP

Create:

`20260827-kr-top3-price-structure-final-preenable-and-enable-bundle.zip`

Include:

```text
exact master instruction
all track instructions
test-sink configuration/isolation
current KR market data
TOP3 market message
all monitored KR stock Price Structure audit
AI/fallback parity
exact test messages
test-delivery evidence
message quality
operating promotion
feature-off parity
TOP3 enablement
KR Price Structure enablement
post-enable smoke
US isolation proof
natural-proof status
rollback
safety parity
readiness JSON
test/CI summary
artifact index
```

Exclude:

```text
raw sink IDs
secrets
auth headers
tokens
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 49. Final principle

No more shadow-only ambiguity.

The safe final sequence is:

```text
validated code
→ isolated real test delivery
→ exact user-visible verification
→ operating promotion with flags OFF
→ TOP3 KR market flag ON
→ smoke
→ KR Price Structure flag ON
→ smoke
→ US still OFF
→ natural KR proof
```

KR market messages should expose the internal market structure:

```text
direction
breadth
flow
size/style
relative strong TOP3
relative weak TOP3
```

Eligible KR stock messages should expose only backend-owned safe current structure:

```text
가까운 지지
가까운 저항
주요 구조 지지/저항
safe Fib/SR only when eligible
```

Never turn remote history into "가까운".
Never force Fib.
Never invent targets/stops.
Never enable US Price Structure in this task.
