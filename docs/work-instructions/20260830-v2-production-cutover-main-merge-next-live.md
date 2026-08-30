# thesis-monitor — V2 Production Cutover + Main Merge + Next Live Coverage
## Include decision-aware wording repair
## Promote accepted v2 decision ownership to the production stock-message path
## Merge to main only after preflight passes
## Apply from the next scheduled live cycles; no manual production send today

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-30 KST`
- Workstream: `V2_PRODUCTION_CUTOVER_MAIN_MERGE_NEXT_LIVE`
- Task class: `PRODUCTION_MIGRATION + RENDERER_POLISH + MAIN_MERGE + LIVE_PROOF`
- User authorization:
  - merge approved production-safe implementation to `main`
  - enable accepted v2 for the next normal live stock messages
- Automated trading: `0`
- Order sizing: `0`
- Manual production Telegram today: `0`
- Scheduled-task manual trigger today: `0`
- Existing regular schedules: preserve unless explicitly required for safe deployment
- Production Assist: preserve current OFF state
- Price Structure: no calculation change
- Valuation: no calculation change

Source bundle:

`20260830-v2-adjudicated-decision-ownership-repair-bundle.zip`

Latest source-supported implementation / operating state:

```text
FINAL_MAIN / OPERATING =
f55605189ee0179ab4af7030b94d79d706ed32a8

V2_ACCEPTED_OWNERSHIP =
READY_FOR_MIGRATION_REVIEW

V2_MIGRATION_RECOMMENDATION =
READY_WITH_OBSERVATION

Candidate distribution on frozen evidence =
BUY 2 / HOLD 14 / SELL 4

Accepted distribution on frozen evidence =
BUY 1 / HOLD 16 / SELL 3

Accepted BUY control =
GOOGL

Accepted SELL controls =
HUT / TSLA / WULF

Accepted HOLD controls include =
003690 코리안리 / RXRX / SNDK

Open P0 / material P1 =
0 / 0

Accepted v2 test sink =
20 / 20 exact PASS
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve actual operating checkout
use f556051... or a safe linear descendant
record current regular scheduler state
record current production delivery configuration without exposing secrets
record current monitored KR/US subject universe
record current v1/v2 feature flags
```

---

# 1. Goal

After this work, the production stock-message path should be:

```text
fresh canonical evidence
        ↓
v2 candidate reasoning
        ↓
required adjudication / accepted resolution
        ↓
accepted_decision_plan
        ↓
Korean user-facing renderer
        ↓
validator
        ↓
immutable production packet
        ↓
normal scheduled delivery
```

The next normal live stock messages should use this accepted-v2 path.

---

# 2. Calendar / live-cycle target

Today is:

```text
2026-08-30 KST
```

Target cycles:

## KR

First target:

```text
2026-08-31 Korea regular close cycle
```

All monitored KR stock messages produced by that normal cycle should use the accepted-v2 production path if they pass readiness.

## US

The next US regular session is:

```text
2026-08-31 America/New_York session
```

Its regular-close message is expected on:

```text
2026-09-01 KST morning
```

All monitored US/foreign stock messages from that normal cycle should use the accepted-v2 production path if they pass readiness.

Do not manufacture a US "2026-08-31 KST morning" close message if no new US regular session exists.

---

# 3. Scope interpretation of "전부 포함"

Production rollout target:

```text
ALL CURRENTLY MONITORED STOCK MESSAGES
```

not merely the old 4-name v1 canary.

The market-summary messages remain governed by their current production contracts and already-deployed cleanup.

This task does not add BUY/HOLD/SELL to market-summary messages.

---

# 4. Hard safety boundary

Even though rollout target is full monitored-stock coverage, never show a raw candidate merely to achieve 100% visibility.

If a subject lacks a safe accepted decision:

```text
accepted_decision = NOT_READY
```

then fail closed for that subject's decision block.

The stock message itself may still render its safe non-decision sections according to existing production policy.

Hard:

```text
RAW_CANDIDATE_VISIBLE_TO_FORCE_COVERAGE = 0
```

---

# 5. Track A — decision-aware change-condition wording

Fix the P2 wording issue observed in 003690.

Bad semantic example for a current HOLD:

```text
하향 조건:
... 보유 판단으로 낮추고
```

This is invalid because the current accepted decision is already HOLD.

Do not patch only 003690.

Implement a decision-aware condition renderer.

---

# 6. Change-condition semantic contract

The renderer must know the current accepted decision.

## Current BUY

Upgrade/strengthen conditions may:

```text
increase BUY confidence
strengthen the investment logic
improve timing
```

Downgrade conditions may:

```text
trigger HOLD/SELL reassessment
reduce BUY confidence
```

## Current HOLD

Upgrade conditions may:

```text
trigger BUY reassessment
increase confidence in favorable asymmetry
```

Downgrade conditions may:

```text
trigger SELL reassessment
reduce confidence in HOLD
shift risk/reward negatively
```

Never say:

```text
HOLD → HOLD로 낮춘다
```

## Current SELL

Upgrade conditions may:

```text
trigger HOLD/BUY reassessment
reduce SELL conviction
```

Further downside conditions may:

```text
strengthen SELL conviction
worsen the investment logic
increase downside risk
```

Never say:

```text
SELL → SELL로 낮춘다
```

---

# 7. Decision-transition wording validator

Add validator checks for impossible/self transitions.

Reject user-facing phrases semantically equivalent to:

```text
HOLD → HOLD로 낮춤
BUY → BUY로 상향
SELL → SELL로 하향
```

unless the wording explicitly refers to:

```text
confidence
timing
risk level
```

rather than top-level decision.

Hard:

```text
SELF_TRANSITION_WORDING = 0
```

---

# 8. 003690 exact wording control

Current frozen accepted decision:

```text
코리안리(003690) = HOLD
```

Its downgrade condition must read as:

```text
SELL/부정적 재평가
or
HOLD 확신도 약화
```

according to actual evidence.

It must not say:

```text
보유 판단으로 낮춘다
```

Hard:

```text
003690_CHANGE_CONDITION_WORDING = PASS
```

---

# 9. Preserve AI autonomy

Do not convert change conditions into deterministic trade triggers.

They are:

```text
reassessment conditions
```

not:

```text
automatic BUY/SELL commands
```

Hard:

```text
CHANGE_CONDITION_AS_AUTOMATIC_TRADE_RULE = 0
```

---

# 10. Track B — accepted v2 becomes production stock-decision authority

Promote the already-repaired ownership contract:

```text
candidate_decision
→ required adjudication
→ accepted_decision_plan
```

to the production stock-message runtime.

Production renderer may consume only:

```text
accepted_decision_plan
```

Hard:

```text
PRODUCTION_RENDERER_USES_RAW_V2_CANDIDATE = 0
```

---

# 11. V1 production path after cutover

Do not delete v1 code in this task.

Retain it as:

```text
rollback / shadow comparison path
```

but it must not own the visible decision block after successful cutover.

Required production authority:

```text
VISIBLE_DECISION_ENGINE = V2_ACCEPTED
```

Rollback flag must be explicit and audited.

---

# 12. Initial production baseline

Use the accepted-v2 records from the ownership repair as the migration baseline.

Frozen controls:

```text
GOOGL = BUY

HUT = SELL
TSLA = SELL
WULF = SELL

003690 = HOLD
RXRX = HOLD
SNDK = HOLD
```

The frozen distribution:

```text
BUY 1 / HOLD 16 / SELL 3
```

is a migration regression control only.

Fresh live evidence may change decisions.

---

# 13. Fresh production-cycle reasoning

For each next live cycle:

```text
fresh evidence
→ new candidate
→ compare against relevant prior accepted state / migration baseline
→ adjudicate material change if required by the v2 contract
→ accepted decision
```

Do not freeze tomorrow's decisions to 1/16/3.

Hard:

```text
LIVE_DECISION_FORCED_TO_FROZEN_DISTRIBUTION = 0
```

---

# 14. Accepted decision before deadline

Every visible v2 decision must be final before message rendering.

If required adjudication is incomplete at render deadline:

```text
decision block = suppress / NOT_READY
```

Never:

```text
candidate fallback
```

Hard:

```text
UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0
```

---

# 15. No unexplained same-evidence churn

If canonical evidence fingerprint is unchanged from the accepted baseline but top-level decision changes:

fail the decision block unless the reason is an explicitly versioned reasoning-policy migration justified in this deployment.

Hard:

```text
SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0
```

---

# 16. Fresh evidence may change decisions

If evidence fingerprint changes:

BUY/HOLD/SELL may change.

Required accepted record:

```text
changed evidence refs
prior accepted decision
new candidate
adjudication if required
new accepted decision
decisive delta
```

Do not classify every change as an error.

---

# 17. V2 fields available to production AI

Accepted-v2 production reasoning may use:

```text
evidence maturity
market expectations
pricing requirement
Bear/Base/Bull scenarios
asymmetry
confirmation cost
preconfirmation error cost
PRE_CONFIRMATION_BUY where applicable
fundamentals
earnings quality
valuation
macro
market context
positioning
Price Structure
safe OHLCV-derived technicals
```

No fixed weighted score.

---

# 18. Pre-confirmation BUY production contract

A visible BUY may be:

```text
PRE_CONFIRMATION_BUY = true
```

when:

```text
decisive evidence remains EARLY/PARTIAL
but accepted reasoning concludes current asymmetry is favorable.
```

User-facing explanation should identify:

```text
what remains unconfirmed
why waiting may be costly
why current price compensates for uncertainty
what would invalidate the BUY
```

Do not promote speculative uncertainty as an advantage by itself.

---

# 19. Post-confirmation HOLD/SELL remains valid

Production reasoning must retain:

```text
CONFIRMED business proof
+
expensive / demanding pricing
→ HOLD or SELL possible
```

Do not display:

```text
좋은 회사니까 BUY
```

without price/expectation reasoning.

---

# 20. Pricing and price movement

A stock price increase alone must not cause:

```text
VALUATION = worse
```

without comparing relevant earnings/FCF/value evidence where safe.

Likewise, business confirmation alone must not cause BUY.

Preserve v2 asymmetry logic.

---

# 21. Korean localization

All US and KR user-facing decision prose remains Korean.

Allowed English:

```text
ticker
proper noun
standard financial acronym where natural
```

Hard:

```text
PRODUCTION_DECISION_MIXED_LANGUAGE_CORE_FIELDS = 0
```

---

# 22. Polarity

Preserve:

```text
BUY 쪽 근거 = BULLISH only
SELL 쪽 근거 = BEARISH only
NEUTRAL/quality limitations = separate
```

Hard:

```text
PRODUCTION_POLARITY_REGRESSION = 0
```

---

# 23. Message density

Do not expose every internal v2 field.

Renderer selects only material v2 concepts.

Typical maximum:

```text
top-level decision
confidence
timing
1–3 BUY-side points
1–3 SELL-side points
1 key maturity/asymmetry concept
upgrade condition
downgrade condition
```

Keep Price Structure / valuation / existing message sections intact.

---

# 24. Full monitored-stock coverage inventory

Before merge, produce an exact runtime inventory:

```text
KR monitored stock subjects
US/foreign monitored stock subjects
total
```

For each:

```text
ticker
canonical identity
accepted-v2 readiness
message route
expected next live session
```

Hard:

```text
MONITORED_SUBJECT_INVENTORY_COMPLETE = PASS
```

---

# 25. Full-coverage preflight

Before main merge, run fresh/non-production current-data preflight for the complete monitored universe.

Required for every subject:

```text
canonical evidence packet
v2 candidate generated
accepted resolution complete OR safely NOT_READY
renderer validation
numeric ownership
polarity
Korean localization
Price Structure parity
valuation parity
```

Target:

```text
100% accepted readiness
```

but do not compromise safety to reach it.

---

# 26. Main-merge gate

Merge to `main` only if:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

full-universe preflight PASS
accepted test-sink PASS
change-condition wording PASS
production rollback path PASS
scheduler unchanged
production recipient not used during preflight
```

If any blocker exists:

do not merge.

---

# 27. Test-sink before main merge

Send the complete monitored-stock candidate production payloads to the dedicated non-production test sink.

Do not send market-summary messages unless needed for regression.

Require:

```text
rendered = outbound = received
```

for every test message.

Hard:

```text
PREMERGE_TEST_EXACT_PAYLOAD = PASS
PREMERGE_TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 28. Required test controls

At minimum inspect exact accepted test messages for:

```text
003690 HOLD
GOOGL BUY
HUT SELL
RXRX HOLD
SNDK HOLD
TSLA SELL
WULF SELL
000660
one additional KR financial/cyclical subject
one additional US high-expectation subject
```

If fresh evidence changes a control:

document the exact evidence delta and adjudication.

---

# 29. Main merge

After PASS:

```text
merge implementation/report commits into main
push main
verify origin/main
verify operating checkout
```

Required:

```text
FINAL_MAIN = ORIGIN_MAIN = OPERATING
```

Do not leave production runtime on a pre-merge feature branch.

Hard:

```text
MAIN_OPERATING_DIVERGENCE = 0
```

---

# 30. Production feature state

After main merge, set the repository-native production state so that:

```text
VISIBLE_STOCK_DECISION_ENGINE = V2_ACCEPTED
FULL_MONITORED_STOCK_COVERAGE_TARGET = true
V1_VISIBLE_DECISION_ENGINE = false
V1_SHADOW_OR_ROLLBACK_AVAILABLE = true
```

Use actual repository-native flag names.

Record exact before/after.

---

# 31. No manual production send today

After enabling on main:

do NOT manually execute the normal KR/US production delivery jobs merely to prove the feature.

Wait for the next scheduled live cycles.

Hard:

```text
MANUAL_PRODUCTION_SEND_20260830 = 0
MANUAL_SCHEDULED_JOB_TRIGGER_20260830 = 0
```

---

# 32. Scheduler preservation

Do not change normal schedule times simply to force the rollout.

Record before/after scheduler configuration.

Hard:

```text
SCHEDULER_DIFF_UNRELATED_TO_CUTOVER = 0
```

---

# 33. KR next-live proof

Target:

```text
2026-08-31 KR regular close
```

Read-only review after the natural job.

Required observations:

```text
market message delivered under existing market contract
all monitored KR stock messages delivered exactly once
all visible stock decision blocks owned by accepted v2
no raw candidate visible
003690 wording fixed
Price Structure parity
valuation parity
no duplicate/orphan
```

---

# 34. US next-live proof

Target:

```text
2026-08-31 US regular session close
```

Expected receipt:

```text
2026-09-01 KST morning
```

Read-only review after the natural job.

Required:

```text
US market message under existing current contract
all monitored US/foreign stock messages exactly once
accepted v2 decision blocks
Korean localization
polarity
night-futures safe inclusion/omission
Price Structure parity
valuation parity
no duplicate/orphan
```

---

# 35. Live coverage semantics

Target:

```text
all monitored stock messages include accepted-v2 decision block
```

But if any subject is legitimately:

```text
NOT_READY
```

report separately:

```text
subject
reason
blocked stage
```

Do not fabricate 100% coverage.

Hard:

```text
LIVE_RAW_CANDIDATE_FALLBACK = 0
```

---

# 36. Exactly-once delivery

Preserve immutable production-packet and exactly-once delivery contracts.

For each live cycle:

```text
expected messages
sent messages
received messages
duplicates
orphans
unowned retries
```

must be audited.

---

# 37. Rollback conditions

Immediately switch visible stock decision engine back to the safe prior production path if any material production defect occurs:

```text
raw candidate visible
accepted decision mismatch
polarity inversion
wrong ticker identity
numeric provenance failure
Price Structure numeric regression
valuation numeric regression
mixed-language core decision block
duplicate/orphan delivery
material message truncation
systematic NOT_READY coverage failure
```

Rollback must not delete v2 evidence/history.

---

# 38. Rollback does not require message replay

Do not automatically resend already-delivered production messages after rollback.

Preserve exactly-once semantics.

Correct the next eligible cycle unless there is a separately authorized emergency communication workflow.

---

# 39. Production live BUY semantics

A visible BUY is analytical classification.

Do not add:

```text
매수하세요
지금 사세요
비중 X%
목표가
손절가
```

unless separately supported by an approved product contract.

Hard:

```text
ORDER_COMMAND_LANGUAGE = 0
ORDER_SIZING_OUTPUT = 0
AI_INVENTED_TARGET_OR_STOP = 0
```

---

# 40. Price Structure isolation

No changes to:

```text
historical structural S/R
completed Bollinger
provisional Bollinger
current quote / structure-close labeling
major-SR reality gate
```

Hard:

```text
PRICE_STRUCTURE_NUMERIC_DIFF = 0
```

---

# 41. Valuation isolation

No changes to valuation calculations/security-basis rules.

Hard:

```text
VALUATION_NUMERIC_DIFF = 0
ADR_SHARE_BASIS_BYPASS = 0
```

---

# 42. Market-message regression

Preserve the already-deployed US cleanup:

```text
SOXX/IWM material relative signals
RSP participation semantics
night-futures canonical gate
Korean market-message wording
```

Preserve current KR market-message contract.

This task changes stock decision runtime, not market-message decision classification.

---

# 43. P2 wording should not become a migration blocker if isolated

The wording fix itself is small, but it must PASS before main merge because the user explicitly requested it to appear in the next live messages.

No need to retune decisions because of wording.

Hard:

```text
WORDING_REPAIR_CHANGED_ACCEPTED_DECISION = 0
```

---

# 44. Required architecture docs

Create/update:

```text
docs/architecture/V2_PRODUCTION_DECISION_RUNTIME.md
docs/architecture/V2_ACCEPTED_DECISION_OWNERSHIP.md
docs/architecture/DECISION_CHANGE_CONDITION_RENDERING.md
docs/architecture/DECISION_ENGINE_V2_SHADOW_MIGRATION.md
```

---

# 45. Required reports

Create at minimum:

1. `docs/reports/20260830-v2-production-cutover-scope.md`
2. `docs/reports/20260830-v2-production-subject-inventory.md`
3. `docs/reports/20260830-decision-change-condition-wording-repair.md`
4. `docs/reports/20260830-003690-change-condition-control.md`
5. `docs/reports/20260830-v2-production-runtime-contract.md`
6. `docs/reports/20260830-v2-production-preflight.md`
7. `docs/reports/20260830-v2-production-premerge-test-sink.md`
8. `docs/reports/20260830-v2-production-message-quality.md`
9. `docs/reports/20260830-v2-production-main-merge.md`
10. `docs/reports/20260830-v2-production-feature-state.md`
11. `docs/reports/20260831-v2-kr-natural-live-proof.md`
12. `docs/reports/20260901-v2-us-natural-live-proof.md`
13. `docs/reports/20260830-v2-production-rollout-readiness.md`
14. `docs/reports/20260830-v2-production-artifact-index.md`

Machine-readable:

```text
docs/reports/20260830-v2-production-subject-inventory.json
docs/reports/20260830-v2-production-rollout-readiness.json
docs/reports/20260831-v2-kr-natural-live-proof.json
docs/reports/20260901-v2-us-natural-live-proof.json
```

Natural-live proof reports may be produced only after those cycles actually occur.

Do not manufacture them during deployment.

---

# 46. Required gates before main merge

Set exactly:

```text
SELF_TRANSITION_WORDING =
0 / NONZERO

003690_CHANGE_CONDITION_WORDING =
PASS / FAIL

CHANGE_CONDITION_AS_AUTOMATIC_TRADE_RULE =
0 / NONZERO

PRODUCTION_RENDERER_USES_RAW_V2_CANDIDATE =
0 / NONZERO

LIVE_DECISION_FORCED_TO_FROZEN_DISTRIBUTION =
0 / NONZERO

UNADJUDICATED_MATERIAL_CHANGE_VISIBLE =
0 / NONZERO

SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN =
0 / NONZERO

PRODUCTION_DECISION_MIXED_LANGUAGE_CORE_FIELDS =
0 / NONZERO

PRODUCTION_POLARITY_REGRESSION =
0 / NONZERO

MONITORED_SUBJECT_INVENTORY_COMPLETE =
PASS / FAIL

PREMERGE_ACCEPTED_READY_COUNT =
...

PREMERGE_NOT_READY_COUNT =
...

PREMERGE_TEST_MESSAGE_COUNT =
...

PREMERGE_TEST_EXACT_PAYLOAD =
PASS / FAIL

PREMERGE_TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

MAIN_OPERATING_DIVERGENCE =
0 / NONZERO

SCHEDULER_DIFF_UNRELATED_TO_CUTOVER =
0 / NONZERO

MANUAL_PRODUCTION_SEND_20260830 =
0 / NONZERO

MANUAL_SCHEDULED_JOB_TRIGGER_20260830 =
0 / NONZERO

WORDING_REPAIR_CHANGED_ACCEPTED_DECISION =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

ADR_SHARE_BASIS_BYPASS =
0 / NONZERO

ORDER_COMMAND_LANGUAGE =
0 / NONZERO

ORDER_SIZING_OUTPUT =
0 / NONZERO

AI_INVENTED_TARGET_OR_STOP =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

PREMERGE_PRODUCTION_CUTOVER =
PASS / FAIL
```

---

# 47. Required post-merge state

After PASS and main merge:

```text
VISIBLE_STOCK_DECISION_ENGINE =
V2_ACCEPTED

V2_PRODUCTION_ENABLED =
true

FULL_MONITORED_STOCK_COVERAGE_TARGET =
true

V1_VISIBLE_DECISION_ENGINE =
false

V1_ROLLBACK_AVAILABLE =
true

PRODUCTION_ASSIST =
OFF
```

Use repository-native field names in actual implementation.

---

# 48. KR natural-live gates

After the 2026-08-31 KR natural close:

```text
KR_LIVE_JOB_EXIT =
0 / NONZERO

KR_EXPECTED_STOCK_MESSAGE_COUNT =
...

KR_RECEIVED_STOCK_MESSAGE_COUNT =
...

KR_ACCEPTED_V2_VISIBLE_COUNT =
...

KR_NOT_READY_DECISION_BLOCK_COUNT =
...

KR_RAW_CANDIDATE_VISIBLE =
0 / NONZERO

KR_EXACT_PAYLOAD =
PASS / FAIL

KR_DUPLICATE =
0 / NONZERO

KR_ORPHAN =
0 / NONZERO

KR_UNOWNED_RETRY =
0 / NONZERO

KR_PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

KR_VALUATION_NUMERIC_DIFF =
0 / NONZERO

KR_V2_NATURAL_LIVE =
PASS /
PARTIAL_SAFE /
FAIL
```

---

# 49. US natural-live gates

After the 2026-08-31 US regular close / 2026-09-01 KST delivery:

```text
US_LIVE_JOB_EXIT =
0 / NONZERO

US_EXPECTED_STOCK_MESSAGE_COUNT =
...

US_RECEIVED_STOCK_MESSAGE_COUNT =
...

US_ACCEPTED_V2_VISIBLE_COUNT =
...

US_NOT_READY_DECISION_BLOCK_COUNT =
...

US_RAW_CANDIDATE_VISIBLE =
0 / NONZERO

US_EXACT_PAYLOAD =
PASS / FAIL

US_DUPLICATE =
0 / NONZERO

US_ORPHAN =
0 / NONZERO

US_UNOWNED_RETRY =
0 / NONZERO

US_PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

US_VALUATION_NUMERIC_DIFF =
0 / NONZERO

US_NIGHT_FUTURES =
CURRENT_SAFE /
SOURCE_LIMITATION_SAFE /
OMITTED_OTHER_SAFE /
FAIL

US_V2_NATURAL_LIVE =
PASS /
PARTIAL_SAFE /
FAIL
```

---

# 50. Main-merge PASS rule

Before merge require:

```text
P0 = 0
material P1 = 0

wording repair PASS
full inventory PASS
preflight safe
test-sink exact PASS
no production-recipient test send
accepted ownership intact
rollback path ready
Price Structure/valuation parity
```

Then merge to main and arm for natural schedules.

---

# 51. Overall completion status

At deployment completion, before natural cycles:

```text
V2_PRODUCTION_CUTOVER =
MERGED_ARMED_AWAITING_NATURAL_LIVE /
FAIL
```

After both KR and US natural cycles:

```text
V2_PRODUCTION_CUTOVER =
LIVE_PASS /
PARTIAL_SAFE /
ROLLED_BACK /
FAIL
```

Do not declare `LIVE_PASS` before both required natural proofs actually exist.

---

# 52. Completion response — deployment phase

Return immediately after safe main merge:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_IMPLEMENTATION = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...

MONITORED_KR_COUNT = ...
MONITORED_US_COUNT = ...
MONITORED_TOTAL = ...

SELF_TRANSITION_WORDING = 0
003690_CHANGE_CONDITION_WORDING = PASS

PREMERGE_ACCEPTED_READY_COUNT = ...
PREMERGE_NOT_READY_COUNT = ...
PREMERGE_TEST_MESSAGE_COUNT = ...
PREMERGE_TEST_EXACT_PAYLOAD = PASS

VISIBLE_STOCK_DECISION_ENGINE = V2_ACCEPTED
V2_PRODUCTION_ENABLED = true
FULL_MONITORED_STOCK_COVERAGE_TARGET = true
V1_VISIBLE_DECISION_ENGINE = false
V1_ROLLBACK_AVAILABLE = true

PRODUCTION_RENDERER_USES_RAW_V2_CANDIDATE = 0
UNADJUDICATED_MATERIAL_CHANGE_VISIBLE = 0
SAME_EVIDENCE_UNEXPLAINED_DECISION_CHURN = 0

PRODUCTION_DECISION_MIXED_LANGUAGE_CORE_FIELDS = 0
PRODUCTION_POLARITY_REGRESSION = 0

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0

MANUAL_PRODUCTION_SEND_20260830 = 0
MANUAL_SCHEDULED_JOB_TRIGGER_20260830 = 0

KR_NEXT_LIVE_TARGET = 2026-08-31
US_NEXT_SESSION_TARGET = 2026-08-31 America/New_York
US_EXPECTED_KST_DELIVERY = 2026-09-01

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

V2_PRODUCTION_CUTOVER =
MERGED_ARMED_AWAITING_NATURAL_LIVE /
FAIL

NEXT_ACTION =
WAIT_FOR_20260831_KR_NATURAL_LIVE /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 53. Completion response — after natural live proofs

After KR and US natural cycles, return:

```text
FINAL_MAIN = ...
OPERATING = ...

KR_V2_NATURAL_LIVE = ...
KR_EXPECTED_STOCK_MESSAGE_COUNT = ...
KR_RECEIVED_STOCK_MESSAGE_COUNT = ...
KR_ACCEPTED_V2_VISIBLE_COUNT = ...
KR_NOT_READY_DECISION_BLOCK_COUNT = ...
KR_EXACT_PAYLOAD = ...
KR_DUPLICATE = 0
KR_ORPHAN = 0

US_V2_NATURAL_LIVE = ...
US_EXPECTED_STOCK_MESSAGE_COUNT = ...
US_RECEIVED_STOCK_MESSAGE_COUNT = ...
US_ACCEPTED_V2_VISIBLE_COUNT = ...
US_NOT_READY_DECISION_BLOCK_COUNT = ...
US_EXACT_PAYLOAD = ...
US_DUPLICATE = 0
US_ORPHAN = 0
US_NIGHT_FUTURES = ...

LIVE_RAW_CANDIDATE_FALLBACK = 0
ORDER_COMMAND_LANGUAGE = 0
ORDER_SIZING_OUTPUT = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

V2_PRODUCTION_CUTOVER =
LIVE_PASS /
PARTIAL_SAFE /
ROLLED_BACK /
FAIL

NEXT_ACTION =
NORMAL_MONITORING /
BOUNDED_REPAIR /
ROLLBACK_REVIEW
```

---

# 54. Mandatory completion ZIP

Create:

`20260830-v2-production-cutover-main-merge-next-live-bundle.zip`

Include:

```text
exact master instruction
all track instructions
wording repair
003690 control
subject inventory
production runtime contract
fresh preflight
premerge test-sink exact messages
message-quality review
main merge evidence
feature-state evidence
scheduler before/after
rollback readiness
deployment readiness JSON
test/CI summary
artifact index
```

Do not fabricate natural-live reports before the cycles occur.

After the natural cycles, either append a second live-proof bundle or produce:

```text
20260901-v2-production-natural-live-proof-bundle.zip
```

with the actual KR/US natural evidence.

Exclude:

```text
secrets
Telegram recipient IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 55. Final principle

The requested production outcome is:

```text
main contains the wording repair
main contains the accepted-v2 production runtime
the old raw candidate cannot leak into user messages
all monitored stock messages target accepted-v2 coverage
the next normal KR and US live cycles use it without manual forcing
```

Do not sacrifice accepted-decision safety merely to make every decision block visible.

If fresh evidence cannot produce a safe accepted decision before rendering,
fail closed for that subject and report it explicitly.
