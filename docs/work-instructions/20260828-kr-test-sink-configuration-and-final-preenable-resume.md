# thesis-monitor — KR Test Sink Configuration + Final Pre-Enable Resume
## Configure one real non-production Telegram test chat, rerun the blocked final pre-enable, then KR-only sequential enablement
## No new feature work; resume from already-validated code

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `KR_TEST_SINK_CONFIGURATION_AND_FINAL_PREENABLE_RESUME`
- Task class: `BOUNDED_TEST_INFRA_AND_ROLLOUT_RESUME`
- Production Assist: preserve `OFF`
- US Price Structure: preserve `OFF`
- Manual production scheduler execution: `0`
- Production-recipient test send: `0`
- DB / assessment mutation: `0`
- Historical archive rewrite: `0`

### Latest blocked final-preenable state

The prior final pre-enable stopped safely because no dedicated test sink was configured.

Reported state:

```text
latest validated main:
6a2068b00f10e28c5eba2133d2423293f4a1bb25

operating:
43731f015901b96e2dee3af009b9e1d074382349

KR market TOP3 flag:
OFF

KR Price Structure flag:
OFF

US Price Structure:
OFF

Production Assist:
OFF

TEST_SINK_AVAILABLE:
NO

TEST_MARKET_MESSAGE_COUNT:
0

TEST_STOCK_MESSAGE_COUNT:
0

OPERATING_PROMOTION:
NOT_RUN

KR_ROLLOUT:
NOT_ENABLED

OPEN_P0:
0

OPEN_MATERIAL_P1:
1

P1:
dedicated_test_sink_not_configured
```

Before execution:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. require it to contain `6a2068...` or a safe linear descendant
5. resolve current operating SHA
6. do not redo already-passing calculation/renderer repairs
7. record exact lineage

---

# 1. Objective

Close the only remaining blocker:

`dedicated_test_sink_not_configured`

Then resume the already-approved final flow:

```text
A. configure one dedicated non-production Telegram test sink
B. prove it is different from production sink
C. rerun production-equivalent KR final preflight
D. send 1 KR market digest + every current monitored KR stock message to test sink exactly once
E. verify exact payload / formatting / numeric provenance
F. only if all PASS:
   promote latest validated main to operating with flags OFF
G. enable KR market TOP3 only → smoke
H. enable KR Price Structure only → smoke
I. prove US Price Structure remains OFF
J. wait for next natural KR market + stock messages
```

No new Price Structure feature development is authorized.

---

# 2. Allowed test-sink configuration keys

The repository already recognizes test-recipient style configuration.

Use the existing project-native configuration path.

Known accepted names may include:

```text
TELEGRAM_TEST_CHAT_ID
TEST_TELEGRAM_CHAT_ID
TELEGRAM_STAGING_CHAT_ID
TELEGRAM_DEVELOPER_CHAT_ID
```

Prefer the canonical existing key used by current code/config resolution.

Do NOT add redundant aliases unless compatibility tests prove one is needed.

---

# 3. Operator-supplied secret only

A real test Telegram chat/channel ID must come from:

```text
existing secure environment
secret manager
deployment secret configuration
```

Never:

```text
invent a chat ID
copy production chat ID
commit raw chat ID into git
write raw chat ID into reports
```

If no real test chat ID is available:

```text
STOP
TEST_SINK_AVAILABLE = NO
NEXT_ACTION = OPERATOR_PROVIDE_DEDICATED_TEST_CHAT
```

Do not continue.

---

# 4. Secret handling

Raw test/production IDs must remain secret.

Reports may expose only:

```text
alias
redacted hash
collision result
```

Hard:

```text
SECRET_IN_REPO = 0
PRIVATE_SINK_ID_IN_REPORT = 0
RAW_TEST_CHAT_ID_IN_LOG = 0
RAW_PRODUCTION_CHAT_ID_IN_LOG = 0
```

---

# 5. Test sink vs production sink collision proof

Resolve both effective recipients:

```text
production sink
test sink
```

Compare using redacted hash / direct runtime equality.

Hard:

```text
TEST_PRODUCTION_SINK_COLLISION = 0
```

If equal:

```text
STOP
TEST_SEND = BLOCKED_PRODUCTION_COLLISION
```

No override.

---

# 6. Delivery namespace isolation

Test deliveries must use a non-production namespace such as:

```text
TEST_ONLY
KR_FINAL_PREENABLE
NON_PRODUCTION
```

Existing production sender/receipt logic must not consume test intents.

Hard:

```text
TEST_PRODUCTION_INTENT_COLLISION = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 7. No manual production task

Do not manually run:

```text
KR afternoon production scheduler
stock monitoring production scheduler
```

Use only:

```text
preflight/test harness
production-equivalent packet builder
isolated test delivery path
```

Hard:

`MANUAL_PRODUCTION_TASK = 0`

---

# 8. Resume from validated code

Do not redo:

```text
daily 1200/provider-limit contract
nearest/proximity semantics
Fib family safety
TOP3 sector ranking
numeric registry
KR local-first ownership
US current-session repair
```

These are already validated.

Only a direct new regression may justify reopening them.

---

# 9. Target session

Resolve the latest completed KR regular session dynamically.

If executed before the 2026-08-28 close:

use the latest completed prior session.

If executed after the 2026-08-28 close:

expected:

`2026-08-28`

Never use incomplete current-session daily data as a completed session.

---

# 10. Current KR market packet

Build the production-equivalent KR market packet using:

```text
ka20001
ka20003
ka10051
ka10066
```

Run:

```text
numeric registry
provenance
reconciliation
AI readiness
KR local-first plan
TOP3 sector selection
```

Hard:

```text
PREENABLE_DATA_COLLECTION = PASS
NUMERIC_GATE = PASS
KR_LOCAL_FIRST_PLAN = PASS
```

---

# 11. Reconciliation remains fail-closed

Recompute same-session:

```text
ka10051 aggregate
vs
full ka10066
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

# 12. KR market TOP3 message

The test market digest must include safe current-session:

```text
KOSPI/KOSDAQ direction
breadth
aggregate participant flow
size/style

KOSPI relative strong TOP3
KOSPI relative weak TOP3

KOSDAQ relative strong TOP3
KOSDAQ relative weak TOP3
```

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
USER_FACING_LEADER_LAGGARD_TERM = 0
AI_DERIVED_SECTOR_RANKING = 0
SECTOR_TOP3_DUPLICATE = 0
STALE_SECTOR_IN_TOP3 = 0
```

---

# 13. Current monitored KR stock universe

Use ALL current monitored KR tickers at execution time.

Validated previous universe:

```text
000660
003690
005490
005930
010120
012450
086280
```

If current universe differs:

```text
report added/removed tickers
test all current monitored KR names
```

Do not silently sample.

---

# 14. Price Structure daily coverage contract

Preserve:

```text
canonical daily target = 1200
current supported provider cap = 1000
actual completed up to 1000
coverage = PARTIAL_SAFE/provider_limit
```

Hard:

```text
CANONICAL_DAILY_BUDGET_CHANGED_TO_1000 = 0
PROVIDER_LIMIT_MISREPORTED_AS_FULL = 0
SYNTHETIC_DAILY_BARS = 0
```

---

# 15. Price Structure runtime eligibility

For each KR monitored ticker use existing:

```text
ELIGIBLE
ELIGIBLE_SR_ONLY
OMIT_PRICE_STRUCTURE
BLOCKED
```

Do not hard-code historical eligibility.

Recompute on target session.

---

# 16. User-visible Price Structure rules

For `ELIGIBLE`:

```text
📐 현재 가격 구조

가까운 지지
가까운 저항

주요 구조 지지/저항 when available

Fib/SR 겹침
only if safe/material
```

For `ELIGIBLE_SR_ONLY`:

```text
safe SR only
no Fib line
```

For `OMIT/BLOCKED`:

```text
no Price Structure block
rest of message still valid
```

---

# 17. Proximity safety

Preserve:

```text
LONG_HORIZON != 가까운
internal nearest != automatically user-visible 가까운
```

Hard:

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
FABRICATED_SR_FILL = 0
```

---

# 18. Fib safety

Fib is optional.

Hard:

```text
UNSTABLE_FIB_EXPOSED = 0
UNSTABLE_FIB_SOURCE_IN_CONFLUENCE = 0
UNSTABLE_FIB_FAMILY_USER_VISIBLE_ELIGIBLE = 0
MATERIAL_FIB_RANGE_EXTENSION_SUPPRESSED = 0
```

No forced Fib.

---

# 19. Current structure vs stored rules

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

# 20. Numeric ownership

Hard:

```text
AI_CALCULATED_TECHNICAL_PRICE = 0
UNREGISTERED_PRICE_STRUCTURE_NUMERIC = 0
NUMBERS_WITHOUT_PROVENANCE = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 21. AI/fallback parity before send

Generate both:

```text
AI candidate
deterministic fallback candidate
```

for:

```text
KR market digest
every current monitored KR stock
```

Required:

```text
AI_FALLBACK_LOCAL_FIRST_PARITY = PASS
AI_FALLBACK_TOP3_PARITY = PASS
AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY = PASS
AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY = PASS
AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY = PASS
```

---

# 22. Test-send count

Default:

```text
1 market digest
+
N current monitored KR stock messages
```

If current monitored KR count = 7:

```text
TEST_MARKET_MESSAGE_COUNT = 1
TEST_STOCK_MESSAGE_COUNT = 7
TEST_TOTAL_MESSAGE_COUNT = 8
```

No silent reduction.

---

# 23. Test route selection

For each test message use the route production would choose.

```text
AI when current production eligibility says AI
otherwise deterministic fallback
```

Record route per message.

No aesthetic selection.

---

# 24. Exactly-once test delivery

Send every test message exactly once to the dedicated test sink.

Hard:

```text
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_UNOWNED_RETRY = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
```

---

# 25. Exact payload proof

For every test message compare:

```text
rendered candidate
outbound test payload
receipt-linked/received payload
```

Hard:

`TEST_EXACT_PAYLOAD_MATCH = PASS`

Use hashes.

---

# 26. Actual received-message review

Inspect the actual received Telegram messages.

Market:

```text
TOP3 strong/weak readable
size/style readable
KOSPI/KOSDAQ distinct
no truncation
```

Stocks:

```text
company header intact
Price Structure section readable
stored rule separated
no empty Fib
no stale technical prose
no truncation
```

Hard:

```text
TEST_FORMATTING_BROKEN = 0
TEST_MESSAGE_TRUNCATED = 0
TEST_MESSAGE_QUALITY = PASS
```

---

# 27. Pre-enable PASS rule

Proceed only if:

```text
TEST_SINK_AVAILABLE = YES
TEST_PRODUCTION_SINK_COLLISION = 0
market packet PASS
TOP3 market message PASS
all monitored KR stock messages PASS
numeric provenance PASS
proximity safety PASS
Fib safety PASS
AI/fallback parity PASS
exact payload PASS
formatting PASS
test exactly once PASS
P0 = 0
material P1 = 0
```

Then:

`KR_FINAL_PREENABLE = PASS`

---

# 28. Promote validated code to operating with flags OFF

After pre-enable PASS:

promote latest validated main to operating.

At promotion REQUIRE:

```text
kr_market_sector_top3_enabled = false
kr_price_structure_v3_enabled = false
US Price Structure = false
Production Assist = OFF
```

Then run:

```text
API health
provider health
feature-off parity
market render smoke
stock render smoke
```

Hard:

`FEATURE_OFF_PARITY = PASS`

---

# 29. Enable KR TOP3 first

Set only:

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
POST_TOP3_ENABLE_PRICE_STRUCTURE_LEAK = 0
```

If fail:

rollback TOP3 and STOP.

---

# 30. Enable KR Price Structure second

Only after TOP3 smoke PASS:

set:

```text
kr_price_structure_v3_enabled = true
```

Keep US OFF.

Run read-only full monitored-KR stock smoke.

Required:

```text
POST_KR_PRICE_STRUCTURE_ENABLE = PASS
POST_ENABLE_US_PRICE_STRUCTURE_LEAK = 0
```

If fail:

rollback KR Price Structure and STOP.

---

# 31. Final pre-natural state

Expected:

```text
KR market TOP3 = ON
KR Price Structure = ON
US Price Structure = OFF
Production Assist = OFF

KR_ROLLOUT =
ENABLED_AWAITING_NATURAL_PROOF
```

Do not claim `LIVE_PASS` yet.

---

# 32. Natural proof

Do not manually trigger.

Wait for:

```text
next natural KR afternoon market digest
next natural KR monitored-stock cycle
```

Verify:

```text
market TOP3 visible
Price Structure visible only where eligible
SR/Fib provenance safe
stored rules separated
no target/stop
exactly once
```

Then:

`KR_ROLLOUT = LIVE_PASS`

only if both product families pass.

---

# 33. US isolation

After KR enablement prove:

```text
US_PRICE_STRUCTURE_ENABLED = 0
US_PRICE_STRUCTURE_RUNTIME_DIFF = 0
US_MARKET_DIGEST_CODE_DIFF = 0
```

No accidental global flag behavior.

---

# 34. Business / valuation isolation

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF_FROM_KR_ENABLEMENT = 0
MARKET_CONTEXT_AS_BUSINESS_THESIS_CHANGE = 0
```

---

# 35. Rollback

Document exact independent rollback:

```text
kr_price_structure_v3_enabled = false
kr_market_sector_top3_enabled = false
```

If one product family fails naturally:

disable only the affected flag first.

No DB cleanup.

---

# 36. Required tests

Before test send:

```text
test-sink config resolution
sink collision
namespace isolation
KR market packet
TOP3 ranking
all monitored KR stock Price Structure replay
daily provider-limit contract
proximity validator
Fib safety
stored-rule ownership
AI/fallback parity
numeric provenance
exact payload
```

Before operating promotion:

```text
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

# 37. Required reports

Create:

1. `docs/reports/20260828-kr-test-sink-config.md`
2. `docs/reports/20260828-kr-test-sink-isolation.md`
3. `docs/reports/20260828-kr-final-preflight-session.md`
4. `docs/reports/20260828-kr-final-market-packet.md`
5. `docs/reports/20260828-kr-final-top3-message.md`
6. `docs/reports/20260828-kr-final-price-structure-per-ticker.md`
7. `docs/reports/20260828-kr-final-ai-fallback-parity.md`
8. `docs/reports/20260828-kr-final-test-delivery.md`
9. `docs/reports/20260828-kr-final-exact-test-messages.md`
10. `docs/reports/20260828-kr-final-message-quality.md`
11. `docs/reports/20260828-kr-final-operating-promotion.md`
12. `docs/reports/20260828-kr-final-top3-enablement.md`
13. `docs/reports/20260828-kr-final-price-structure-enablement.md`
14. `docs/reports/20260828-kr-final-post-enable-smoke.md`
15. `docs/reports/20260828-kr-final-natural-proof-status.md`
16. `docs/reports/20260828-kr-final-rollout-readiness.md`
17. `docs/reports/20260828-kr-final-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-kr-final-price-structure-per-ticker.json
docs/reports/20260828-kr-final-test-delivery.json
docs/reports/20260828-kr-final-rollout-readiness.json
```

Exclude raw sink IDs and secrets.

---

# 38. Required gates

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

NUMERIC_GATE =
PASS / FAIL

KR_LOCAL_FIRST_PLAN =
PASS / FAIL

KOSPI_STRONG_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

KOSPI_WEAK_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

KOSDAQ_STRONG_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

KOSDAQ_WEAK_TOP3_VISIBLE =
PASS / PARTIAL_SAFE / FAIL

CURRENT_KR_MONITORED_STOCK_COUNT =
...

ALL_KR_STOCK_PRICE_STRUCTURE_REPLAY =
PASS / FAIL

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

AI_FALLBACK_LOCAL_FIRST_PARITY =
PASS / FAIL

AI_FALLBACK_TOP3_PARITY =
PASS / FAIL

AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY =
PASS / FAIL

AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY =
PASS / FAIL

TEST_MARKET_MESSAGE_COUNT =
...

TEST_STOCK_MESSAGE_COUNT =
...

TEST_TOTAL_MESSAGE_COUNT =
...

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

KR_FINAL_PREENABLE =
PASS /
BLOCKED_NO_TEST_SINK /
FAIL

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

FEATURE_OFF_PARITY =
PASS / NOT_RUN / FAIL

KR_MARKET_TOP3_ENABLED =
true / false

POST_TOP3_ENABLE_MARKET =
PASS / NOT_RUN / FAIL

POST_TOP3_ENABLE_PRICE_STRUCTURE_LEAK =
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

# 39. Stop conditions

STOP if:

```text
no real test chat
test and production recipient collide
test namespace can route to production
market packet unsafe
TOP3 stale/duplicate
any monitored KR stock fails Price Structure validator
remote zone appears as 가까운
unstable Fib appears
numeric provenance fails
test send duplicates
test payload mismatches
operating health fails
feature-off parity fails
US Price Structure becomes enabled
new P0
new material P1
```

---

# 40. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...
LATEST_VALIDATED_MAIN = ...
PREVIOUS_OPERATING = ...

BRANCH = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

TEST_SINK_AVAILABLE = ...
TEST_SINK_ALIAS = ...
TEST_SINK_REDACTED_HASH = ...
PRODUCTION_SINK_REDACTED_HASH = ...

TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0
SECRET_IN_REPO = 0

PREENABLE_TARGET_SESSION = ...
PREENABLE_DATA_COLLECTION = ...
NUMERIC_GATE = ...
KR_LOCAL_FIRST_PLAN = ...

KOSPI_STRONG_TOP3 = ...
KOSPI_WEAK_TOP3 = ...
KOSDAQ_STRONG_TOP3 = ...
KOSDAQ_WEAK_TOP3 = ...

CURRENT_KR_MONITORED_STOCK_COUNT = ...
KR_STOCK_TICKERS = ...
ALL_KR_STOCK_PRICE_STRUCTURE_REPLAY = ...

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

LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
UNSTABLE_FIB_EXPOSED = 0
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
OPERATOR_PROVIDE_DEDICATED_TEST_CHAT /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 41. Mandatory completion ZIP

Create:

`20260828-kr-test-sink-configuration-and-final-preenable-resume-bundle.zip`

Include:

```text
exact instruction
test-sink config/isolation
current KR market packet
TOP3 market message
all current KR stock Price Structure audit
AI/fallback parity
test delivery
exact test messages
message quality
operating promotion
feature-off parity
TOP3 enablement
KR Price Structure enablement
US isolation
post-enable smoke
natural-proof status
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

# 42. Final principle

The only missing prerequisite is a real non-production Telegram destination.

Once that exists, do not reopen repaired logic.

The safe sequence is:

```text
real test sink
→ current KR market + every monitored KR stock test message
→ exact received-message proof
→ latest validated code to operating with flags OFF
→ TOP3 ON
→ smoke
→ KR Price Structure ON
→ smoke
→ US still OFF
→ natural KR proof
```

No production recipient may be used as a test sink.
No new feature flag framework.
No calculation redesign.
