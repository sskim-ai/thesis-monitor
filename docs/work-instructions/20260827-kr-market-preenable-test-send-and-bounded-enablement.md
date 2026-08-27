# thesis-monitor — KR Market Pre-Enable Test Send + Bounded Enablement
## Production-equivalent data collection → render → dedicated test-sink delivery → review → bounded KR size/sector enablement
## Price Structure v3 remains OUT OF SCOPE / NOT ARMED

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-27 KST`
- Workstream: `KR_MARKET_PREENABLE_TEST_SEND_AND_BOUNDED_ENABLEMENT`
- Task class: `CONTROLLED_PREENABLE_TEST_AND_BOUNDED_RUNTIME_ENABLEMENT`
- Target market: `KR`
- User authorization:
  - production-equivalent data collection: YES
  - test-only message delivery: YES
  - bounded KR size/sector message enablement after PASS: YES
  - production-user manual send: NO
  - manual scheduled production task execution: NO
  - Price Structure v3 enablement: NO
- Production Assist: preserve `OFF`
- Price Structure v3: preserve `INTEGRATED_READY_NOT_ARMED`
- Business investment-logic mutation: `0`
- DB / official assessment mutation: `0`

### Latest known KR size/sector repair state

```text
KR_SIZE_SECTOR_MESSAGE_REPAIR =
REPLAY_PASS_NATURAL_REPROOF_PENDING

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Latest reported repair lineage:

```text
INSTRUCTION_COMMIT =
794c6f5d956d0928eac0113d658fede58b1266dc

IMPLEMENTATION_SHA =
6a54db130e95e25969a5ca0a100648d4a12c3aa2

REPORT_COMMIT / FINAL_MAIN / OPERATING =
de352342f15a75069289f35f00b4bd24ddcdd19f
```

Before execution:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. resolve actual operating SHA
5. confirm whether KR size/sector selection is:
   - shadow/test-only
   - runtime-gated
   - already active by code default
6. do not invent a second rollout framework

---

# 1. Objective

Perform one controlled end-to-end KR market-message preflight using the latest completed Korean session:

```text
current completed KR session
→ production-equivalent market data collection
→ canonical packet
→ numeric registry / provenance
→ KR local-first plan
→ size/style + sector selection
→ AI candidate
→ deterministic fallback candidate
→ dedicated TEST SINK delivery exactly once
→ inspect exact received message
→ if and only if all gates PASS:
   bounded enablement of KR size/sector selection
```

This is NOT a Price Structure rollout.

---

# 2. Target-session resolution

At task start, resolve the latest completed regular KR session dynamically.

Expected if executed on 2026-08-27 after close:

```text
TARGET_SESSION = 2026-08-27
```

If market close is not complete:

```text
STOP
PREENABLE_TEST = NOT_READY_SESSION_INCOMPLETE
```

Do not use an incomplete session.

---

# 3. Test delivery safety

The test message may be sent only to an existing, explicitly configured:

```text
test sink
test Telegram chat
staging notification channel
developer-only notification sink
```

The sink must be provably separate from production recipients.

Hard prohibitions:

```text
no production Telegram channel
no production user recipient
no manual production scheduled task
no reuse of production delivery intent
no mutation of historical delivery/receipt
```

If no dedicated test sink exists:

```text
TEST_SINK_AVAILABLE = NO
TEST_SEND = BLOCKED_NO_SAFE_SINK
```

Do not create a fake proof by sending to production.

---

# 4. No manual production task

Do NOT run the production afternoon scheduler manually.

Instead invoke the existing safe:

```text
test harness
replay/preflight harness
staging render path
or isolated production-equivalent packet builder
```

that does not create a production delivery intent.

If no such safe path exists:

```text
STOP
P0/P1 classify as appropriate
```

Do not bypass scheduler ownership.

---

# 5. Production-equivalent data collection

Collect the same data families the live KR close message uses.

## ka20001

For KOSPI and KOSDAQ:

```text
close
change
return_pct
advance
decline
unchanged
eligible issue count if supported
listed issue count if supported
```

Canonical breadth owner:

`Kiwoom ka20001`

---

# 6. ka20003 — size/style + sector

Collect current-session:

```text
KOSPI large
KOSPI mid
KOSPI small

KOSDAQ100
KOSDAQ MID300
KOSDAQ SMALL

sector-index rows
sector component breadth rows if separately supported
```

Do not conflate:

```text
sector return
sector breadth
```

Hard:

`SECTOR_RETURN_AS_SECTOR_BREADTH = 0`

---

# 7. ka10051 — aggregate participant flow

Collect:

```text
KOSPI foreign
KOSPI institution
KOSPI retail

KOSDAQ foreign
KOSDAQ institution
KOSDAQ retail
```

Canonical owner:

`ka10051`

Raw unit:

`100M_KRW`

Normalize through deterministic backend only.

---

# 8. ka10066 — stock-level flow pagination

For both markets:

```text
full pagination
page count
row count
duplicate count
session basis
```

Raw unit:

`1M_KRW`

Hard:

```text
KOSPI_KA10066_PAGINATION = PASS
KOSDAQ_KA10066_PAGINATION = PASS
KA10066_DUPLICATE_ROWS = 0
```

---

# 9. Reconciliation / concentration

Recompute current-session:

```text
ka10051 aggregate
vs
sum ka10066
```

for:

```text
KOSPI foreign/institution/retail
KOSDAQ foreign/institution/retail
```

Use existing canonical tolerance.

Do not widen.

If unresolved:

```text
UNRESOLVED_BASIS_OR_TAXONOMY
→ concentration BLOCKED
```

Hard:

```text
RECONCILIATION_TOLERANCE_WIDENED = 0
UNRECONCILED_CONCENTRATION_PROSE = 0
```

---

# 10. Numeric registry / provenance

Run the exact production numeric semantic gate.

Collect:

```text
TOTAL_NUMERIC_PATHS
SUPPORTED_CANONICAL_PATHS
REGISTERED_SUPPORTED_PATHS
INTERNAL_ONLY_PATHS
UNSUPPORTED_PATHS
```

Hard:

```text
SUPPORTED_CANONICAL_PATH_REGISTRATION_GAP = 0
UNKNOWN_NUMERIC_SEMANTIC_REGISTERED = 0
WILDCARD_REGISTRY_BYPASS = 0
NUMERIC_GATE = PASS
```

Every user-visible size/sector number must have backend provenance.

---

# 11. AI readiness

Record:

```text
READY_FOR_AI
NUMERIC_GATE
OTHER_AI_BLOCKING_GATES
```

If `READY_FOR_AI=false`:

explain exact blocking gate.

Do not force eligibility.

Hard:

`UNEXPLAINED_AI_INELIGIBILITY = 0`

---

# 12. KR local-first plan

Use the existing shared KR market digest plan.

Required priority:

```text
1. KOSPI / KOSDAQ direction
2. breadth
3. aggregate foreign/institution/retail flow
4. size/style
5. sector relative strength/weakness
6. KR FX if material
7. global/prior macro as secondary
8. next-check
```

Hard:

```text
KR_LOCAL_FIRST_PLAN = PASS
GLOBAL_CONTEXT_DOMINATES_KR_LOCAL = 0
```

---

# 13. Size/style required-selection

When safe current-session data exists, select:

```text
KOSPI large / mid / small
KOSDAQ100 / MID300 / SMALL
```

Hard:

```text
SIZE_STYLE_AVAILABLE_BUT_OMITTED = 0
```

Compact display is preferred.

---

# 14. Sector extrema required-selection

When safe current-session sector returns exist, select bounded extrema:

```text
KOSPI relative strong 1
KOSPI relative weak 1

KOSDAQ relative strong 1
KOSDAQ relative weak 1
```

Do not display internal labels:

```text
leader
laggard
```

Use Korean:

```text
업종 상대 강세
업종 상대 약세
```

Hard:

```text
SECTOR_EXTREMES_AVAILABLE_BUT_OMITTED = 0
USER_FACING_LEADER_LAGGARD_TERM = 0
```

---

# 15. AI vs fallback render

Render both from the same exact packet:

```text
AI candidate
deterministic fallback candidate
```

Both must consume the same selected:

```text
direction
breadth
aggregate flow
size/style
sector extrema
```

Exact prose need not match.

Hard:

```text
AI_FALLBACK_LOCAL_FIRST_PARITY = PASS
AI_FALLBACK_SIZE_STYLE_PARITY = PASS
AI_FALLBACK_SECTOR_PARITY = PASS
AI_FALLBACK_NUMERIC_SAFETY_PARITY = PASS
```

---

# 16. Candidate message quality

Before test send, validate:

```text
target session correct
company/security content not relevant
no unsupported numerics
no stale source
no unreconciled concentration
no Price Structure v3
no investment-logic mutation
```

Expected user-facing structure:

```text
🎯 시장 요약
KOSPI / KOSDAQ + breadth

💰 수급
foreign / institution / retail

📊 시장 내부
규모별
업종 상대 강세
업종 상대 약세

📌 다음 확인
```

Global macro may remain secondary if material.

---

# 17. Test-sink message selection

Choose one candidate for test delivery according to existing production ownership:

```text
if AI eligible and production would use AI
→ use AI candidate

otherwise
→ use deterministic fallback candidate
```

Record:

```text
TEST_ROUTE = AI / deterministic_fallback
```

Do not arbitrarily choose the prettier message.

---

# 18. Exact one test delivery

Send exactly once to the dedicated test sink.

Create a test-only delivery identity clearly namespaced:

```text
TEST_ONLY
NON_PRODUCTION
```

Hard:

```text
TEST_DELIVERY_COUNT = 1
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

Do not retry automatically after a confirmed successful delivery.

---

# 19. Test delivery receipt

Collect:

```text
test delivery ID
test sink ID/alias
sent_at
receipt/ack
attempt_count
payload hash
```

Do not expose private chat IDs or secrets in user-facing reports.

Use redacted alias.

---

# 20. Exact payload parity

Compare:

```text
rendered candidate payload
test-send payload
received/receipt-linked payload
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
```

---

# 21. Human-visible formatting review

Inspect the actual received test message.

Check:

```text
line breaks
Telegram markdown/formatting
emoji rendering
percent signs
KRW units
KOSPI/KOSDAQ separation
size/style readability
sector strong/weak readability
message length
truncation
duplicate sections
```

Hard:

```text
TEST_MESSAGE_TRUNCATED = 0
TEST_FORMATTING_BROKEN = 0
TEST_MESSAGE_QUALITY = PASS
```

---

# 22. Test message content hard gates

The received message must show, when safe data exists:

```text
KOSPI/KOSDAQ direction
breadth
aggregate participant flow
KOSPI size/style
KOSDAQ size/style
KOSPI relative strong/weak sector
KOSDAQ relative strong/weak sector
```

Hard:

```text
TEST_KR_DIRECTION_VISIBLE = PASS
TEST_KR_BREADTH_VISIBLE = PASS
TEST_KR_AGGREGATE_FLOW_VISIBLE = PASS
TEST_KR_SIZE_STYLE_VISIBLE = PASS
TEST_KR_SECTOR_EXTREMES_VISIBLE = PASS
```

---

# 23. Test message prohibited content

Hard:

```text
TEST_UNSUPPORTED_NUMERIC = 0
TEST_UNRECONCILED_CONCENTRATION = 0
TEST_STALE_KRX = 0
TEST_GLOBAL_CONTEXT_DOMINANCE = 0
TEST_MARKET_FLOW_AS_THESIS_CHANGE = 0
```

---

# 24. Price Structure v3 must remain invisible

This task is not Price Structure enablement.

Hard:

```text
TEST_V3_PRICE_STRUCTURE_LEAK = 0
PRICE_STRUCTURE_RUNTIME_ARMED = 0
PRICE_STRUCTURE_V3_CODE_DIFF = 0
```

No:

```text
current nearest support
current nearest resistance
major structural SR
Fib/SR confluence
wave state
```

in this KR market test message.

---

# 25. Pre-enable decision gate

Only if ALL pre-enable gates pass:

```text
DATA_COLLECTION = PASS
NUMERIC_GATE = PASS
KR_LOCAL_FIRST_PLAN = PASS
AI_FALLBACK_PARITY = PASS
TEST_DELIVERY = PASS
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_MESSAGE_QUALITY = PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

may bounded enablement proceed.

Otherwise:

```text
ENABLEMENT = DO_NOT_ENABLE
```

---

# 26. Runtime-gate discovery

Before enablement, identify the current mechanism controlling KR size/sector message selection.

Possible valid states:

```text
EXISTING_FEATURE_FLAG
EXISTING_CONFIG
SHADOW_ONLY_SWITCH
ALREADY_ACTIVE_BY_CODE_DEFAULT
NO_RUNTIME_GATE
```

Do not invent a redundant rollout mechanism.

---

# 27. If already active by code default

If the current operating code already uses the repaired policy for natural production with no separate runtime gate:

do NOT create an unnecessary flag.

Record:

```text
ENABLEMENT_ACTION = NO_OP_ALREADY_ACTIVE
```

Then the test-send is a preflight verification only.

Next natural close remains the final proof.

---

# 28. If existing runtime gate exists

If a real existing runtime config/flag controls KR size/sector message selection:

after all test gates PASS:

```text
enable only KR size/sector message selection
```

Do not change:

```text
US behavior
Price Structure
Production Assist
numeric registry
scheduler timing
packet ownership
flow reconciliation
```

Record:

```text
old value
new value
changed_at
operating SHA
rollback value
```

---

# 29. Bounded enablement scope

Scope must be:

```text
KR afternoon/close market digest
```

Only the size/style and sector selection policy.

Not:

```text
stock monitoring messages
US market digest
Price Structure v3
stored price rules
business thesis
```

Hard:

`ENABLEMENT_SCOPE_BLEED = 0`

---

# 30. Rollback

Rollback must be one bounded config/flag reversal or code-default revert using the existing rollout mechanism.

Record exact rollback instruction.

Do not require DB cleanup.

---

# 31. Post-enable smoke replay

After enablement/no-op active confirmation:

run one read-only production-equivalent render against the same frozen packet.

Hard:

```text
POST_ENABLE_RENDER = PASS
POST_ENABLE_SIZE_STYLE_VISIBLE = PASS
POST_ENABLE_SECTOR_EXTREMES_VISIBLE = PASS
POST_ENABLE_PRICE_STRUCTURE_LEAK = 0
```

No second test send is required unless the first send occurred before the actual runtime gate change and
the renderer output materially changes.

If a second test send is needed:

explicitly justify and keep total test sends bounded to 2.

Default target:

```text
TEST_SEND_COUNT = 1
```

---

# 32. Natural close proof after enablement

Do not manually trigger production.

Wait for the next natural KR afternoon/close run.

Read-only verify:

```text
target session
packet
route
exact message
exactly once
size/style visible
sector extrema visible
index/breadth/flow preserved
no concentration leak
no Price Structure leak
```

Until then state:

```text
KR_SIZE_SECTOR_PRODUCTION =
ENABLED_AWAITING_NATURAL_PROOF
```

or, if already active by code default:

```text
KR_SIZE_SECTOR_PRODUCTION =
ACTIVE_AWAITING_NATURAL_PROOF
```

---

# 33. Natural proof hard gates

Required:

```text
NATURAL_KR_SIZE_STYLE_VISIBLE = PASS
NATURAL_KR_SECTOR_EXTREMES_VISIBLE = PASS
NATURAL_KR_DIRECTION_REGRESSION = 0
NATURAL_KR_BREADTH_REGRESSION = 0
NATURAL_KR_FLOW_REGRESSION = 0

NATURAL_KR_DUPLICATE = 0
NATURAL_KR_ORPHAN = 0

NATURAL_KR_PRICE_STRUCTURE_LEAK = 0
```

Only then:

```text
KR_SIZE_SECTOR_PRODUCTION = LIVE_PASS
```

---

# 34. Price Structure relationship

This task must not alter:

```text
PRICE_STRUCTURE_TRACK_C
PRICE_STRUCTURE_RUNTIME_ARMED
```

Price Structure selective enablement remains a separate explicit task.

---

# 35. US isolation

Do not modify current US market-message code or rollout state.

Hard:

```text
US_MARKET_DIGEST_CODE_DIFF = 0
US_RUNTIME_POLICY_DIFF = 0
```

---

# 36. Business / assessment isolation

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
DB_MUTATION = 0
```

---

# 37. Tests

Required before test send:

```text
focused KR market tests
size/style selection tests
sector selection tests
numeric provenance tests
reconciliation/concentration tests
AI/fallback parity tests
test-sink routing tests
production-recipient isolation tests
```

Required before enablement:

```text
full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
```

---

# 38. Test-sink routing negative controls

Must prove:

```text
test sink ID cannot equal production sink ID
test delivery namespace != production namespace
test intent cannot be consumed by production sender
production receipt cannot satisfy test proof
```

Hard:

```text
TEST_PRODUCTION_SINK_COLLISION = 0
TEST_PRODUCTION_INTENT_COLLISION = 0
```

---

# 39. Required reports

Create:

1. `docs/reports/20260827-kr-preenable-target-session.md`
2. `docs/reports/20260827-kr-preenable-data-collection.md`
3. `docs/reports/20260827-kr-preenable-numeric-provenance.md`
4. `docs/reports/20260827-kr-preenable-reconciliation.md`
5. `docs/reports/20260827-kr-preenable-market-digest-plan.md`
6. `docs/reports/20260827-kr-preenable-ai-fallback-parity.md`
7. `docs/reports/20260827-kr-preenable-test-sink-safety.md`
8. `docs/reports/20260827-kr-preenable-test-delivery.md`
9. `docs/reports/20260827-kr-preenable-exact-test-message.md`
10. `docs/reports/20260827-kr-preenable-message-quality.md`
11. `docs/reports/20260827-kr-preenable-gate-matrix.md`
12. `docs/reports/20260827-kr-size-sector-enablement-action.md`
13. `docs/reports/20260827-kr-size-sector-post-enable-smoke.md`
14. `docs/reports/20260827-kr-size-sector-natural-proof-status.md`
15. `docs/reports/20260827-kr-preenable-safety-parity.md`
16. `docs/reports/20260827-kr-preenable-artifact-index.md`

Recommended machine-readable:

```text
docs/reports/20260827-kr-preenable-gate-matrix.json
docs/reports/20260827-kr-preenable-test-message.json
docs/reports/20260827-kr-size-sector-enablement-status.json
```

---

# 40. Required gates

Set exactly:

```text
PREENABLE_TARGET_SESSION =
...

PREENABLE_DATA_COLLECTION =
PASS / FAIL

KIWOOM_KA20001 =
PASS / PARTIAL_SAFE / FAIL

KIWOOM_KA20003 =
PASS / PARTIAL_SAFE / FAIL

KIWOOM_KA10051 =
PASS / FAIL

KOSPI_KA10066_PAGINATION =
PASS / FAIL

KOSDAQ_KA10066_PAGINATION =
PASS / FAIL

NUMERIC_GATE =
PASS / FAIL

READY_FOR_AI =
true / false

KR_LOCAL_FIRST_PLAN =
PASS / FAIL

SIZE_STYLE_SELECTED =
PASS / NOT_AVAILABLE / FAIL

SECTOR_EXTREMES_SELECTED =
PASS / NOT_AVAILABLE / FAIL

AI_FALLBACK_LOCAL_FIRST_PARITY =
PASS / FAIL

AI_FALLBACK_SIZE_STYLE_PARITY =
PASS / FAIL

AI_FALLBACK_SECTOR_PARITY =
PASS / FAIL

AI_FALLBACK_NUMERIC_SAFETY_PARITY =
PASS / FAIL

RECONCILIATION_TOLERANCE_WIDENED =
0 / NONZERO

UNRECONCILED_CONCENTRATION_PROSE =
0 / NONZERO

TEST_SINK_AVAILABLE =
YES / NO

TEST_PRODUCTION_SINK_COLLISION =
0 / NONZERO

TEST_PRODUCTION_INTENT_COLLISION =
0 / NONZERO

TEST_ROUTE =
AI / deterministic_fallback / NOT_SENT

TEST_DELIVERY_COUNT =
0 / 1 / 2 / NONZERO_OTHER

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL / NOT_SENT

TEST_MESSAGE_TRUNCATED =
0 / NONZERO

TEST_FORMATTING_BROKEN =
0 / NONZERO

TEST_MESSAGE_QUALITY =
PASS / FAIL / NOT_SENT

TEST_KR_DIRECTION_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_KR_BREADTH_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_KR_AGGREGATE_FLOW_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_KR_SIZE_STYLE_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_KR_SECTOR_EXTREMES_VISIBLE =
PASS / FAIL / NOT_SENT

TEST_UNSUPPORTED_NUMERIC =
0 / NONZERO

TEST_UNRECONCILED_CONCENTRATION =
0 / NONZERO

TEST_GLOBAL_CONTEXT_DOMINANCE =
0 / NONZERO

TEST_V3_PRICE_STRUCTURE_LEAK =
0 / NONZERO

RUNTIME_GATE_TYPE =
EXISTING_FEATURE_FLAG /
EXISTING_CONFIG /
SHADOW_ONLY_SWITCH /
ALREADY_ACTIVE_BY_CODE_DEFAULT /
NO_RUNTIME_GATE

ENABLEMENT_ACTION =
ENABLED_EXISTING_GATE /
NO_OP_ALREADY_ACTIVE /
DO_NOT_ENABLE

ENABLEMENT_SCOPE_BLEED =
0 / NONZERO

POST_ENABLE_RENDER =
PASS / FAIL / NOT_RUN

POST_ENABLE_SIZE_STYLE_VISIBLE =
PASS / FAIL / NOT_RUN

POST_ENABLE_SECTOR_EXTREMES_VISIBLE =
PASS / FAIL / NOT_RUN

POST_ENABLE_PRICE_STRUCTURE_LEAK =
0 / NONZERO

PRICE_STRUCTURE_RUNTIME_ARMED =
0 / NONZERO

PRICE_STRUCTURE_V3_CODE_DIFF =
0 / NONZERO

US_MARKET_DIGEST_CODE_DIFF =
0 / NONZERO

US_RUNTIME_POLICY_DIFF =
0 / NONZERO

BUSINESS_THESIS_MUTATION =
0 / NONZERO

DB_MUTATION =
0 / NONZERO

OFFICIAL_ASSESSMENT_MUTATION =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

KR_SIZE_SECTOR_PRODUCTION =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
ACTIVE_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL
```

---

# 41. Pre-enable PASS rule

Proceed to bounded enablement only if:

```text
test sink is safe
target session correct
data collection PASS
numeric gate PASS
local-first PASS
size/style selected
sector extrema selected
AI/fallback parity PASS
reconciliation boundaries safe
test send exactly once
exact test payload match PASS
formatting/message quality PASS
no unsupported numeric
no Price Structure leak
P0 = 0
material P1 = 0
```

---

# 42. Stop conditions

STOP and do not enable if:

```text
no safe test sink
wrong target session
ka20003 missing unexpectedly
numeric provenance failure
AI/fallback selection divergence
test message omits size/style
test message omits safe sector extrema
test message sent to production recipient
duplicate test delivery
unreconciled concentration appears
Price Structure v3 appears
new P0
new material P1
```

Return:

```text
ENABLEMENT_ACTION = DO_NOT_ENABLE
NEXT_ACTION = BOUNDED_REPAIR
```

---

# 43. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...
BRANCH = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

PREENABLE_TARGET_SESSION = ...

PREENABLE_DATA_COLLECTION = ...
KIWOOM_KA20001 = ...
KIWOOM_KA20003 = ...
KIWOOM_KA10051 = ...
KOSPI_KA10066_PAGINATION = ...
KOSDAQ_KA10066_PAGINATION = ...

NUMERIC_GATE = ...
READY_FOR_AI = ...

KR_LOCAL_FIRST_PLAN = ...
SIZE_STYLE_SELECTED = ...
SECTOR_EXTREMES_SELECTED = ...

AI_FALLBACK_LOCAL_FIRST_PARITY = ...
AI_FALLBACK_SIZE_STYLE_PARITY = ...
AI_FALLBACK_SECTOR_PARITY = ...
AI_FALLBACK_NUMERIC_SAFETY_PARITY = ...

KOSPI_RECONCILIATION = ...
KOSDAQ_RECONCILIATION = ...
UNRECONCILED_CONCENTRATION_PROSE = 0

TEST_SINK_AVAILABLE = ...
TEST_SINK_ALIAS = ...
TEST_ROUTE = ...

TEST_DELIVERY_COUNT = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

TEST_EXACT_PAYLOAD_MATCH = ...
TEST_MESSAGE_QUALITY = ...

TEST_KR_DIRECTION_VISIBLE = ...
TEST_KR_BREADTH_VISIBLE = ...
TEST_KR_AGGREGATE_FLOW_VISIBLE = ...
TEST_KR_SIZE_STYLE_VISIBLE = ...
TEST_KR_SECTOR_EXTREMES_VISIBLE = ...

TEST_UNSUPPORTED_NUMERIC = 0
TEST_UNRECONCILED_CONCENTRATION = 0
TEST_GLOBAL_CONTEXT_DOMINANCE = 0
TEST_V3_PRICE_STRUCTURE_LEAK = 0

EXACT_TEST_MESSAGE =
...

RUNTIME_GATE_TYPE = ...
ENABLEMENT_ACTION = ...

ENABLEMENT_OLD_VALUE = ...
ENABLEMENT_NEW_VALUE = ...
ENABLEMENT_SCOPE = ...
ROLLBACK = ...

POST_ENABLE_RENDER = ...
POST_ENABLE_SIZE_STYLE_VISIBLE = ...
POST_ENABLE_SECTOR_EXTREMES_VISIBLE = ...
POST_ENABLE_PRICE_STRUCTURE_LEAK = 0

PRICE_STRUCTURE_RUNTIME_ARMED = 0
PRICE_STRUCTURE_V3_CODE_DIFF = 0
US_MARKET_DIGEST_CODE_DIFF = 0
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

DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_SIZE_SECTOR_PRODUCTION =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
ACTIVE_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

NATURAL_KR_PROOF =
PENDING /
PASS /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_CLOSE /
NO_ACTION /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 44. Mandatory completion ZIP

Create:

`20260827-kr-market-preenable-test-send-and-bounded-enablement-bundle.zip`

Include:

```text
exact instruction
target-session report
data collection
numeric provenance
reconciliation
digest plan
AI/fallback parity
test-sink safety
test delivery
exact test message
message quality
gate matrix
enablement action
post-enable smoke
natural-proof status
safety parity
machine-readable gate JSON
artifact index
```

Do not include:

```text
secrets
auth headers
real private chat IDs
account identifiers
private tokens
hidden chain-of-thought
```

Compute SHA-256.

---

# 45. Final principle

The last pre-enable proof should test the actual user experience without touching production recipients:

```text
real completed KR session data
→ production-equivalent packet
→ production-equivalent renderer
→ one isolated test delivery
→ exact received message review
→ bounded size/sector enablement only
→ next natural KR close live proof
```

Do not bundle Price Structure v3 into this rollout.

Do not use a production Telegram recipient as a test sink.

Do not enable if the test message is incomplete, numerically unsafe, or structurally wrong.
