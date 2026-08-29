# thesis-monitor — Cross-Market AI Decision Engine v1 Bounded Production Canary
## 2 KR + 2 US only
## Current natural decisions only in production
## BUY positive path proven separately with historical canonical shadow fixtures
## No global enablement / no automated trading

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `CROSS_MARKET_DECISION_ENGINE_BOUNDED_CANARY`
- Task class: `CONTROLLED_PRODUCTION_CANARY`
- Decision Engine current state: `TEST_SINK_READY`
- Production canary entering state: `OFF`
- Global production decision exposure: `OFF`
- Automated trade execution: `0`
- Brokerage/order integration: `0`
- Order sizing: `0`
- Thesis/monitoring mutation from decision output: `0`
- Price-rule mutation from decision output: `0`

Latest validated baseline:

```text
FINAL_MAIN / OPERATING =
f7e0829647c782ce39353086f4fcc51101b9b566

OPEN_P0 =
0

OPEN_MATERIAL_P1 =
0

DECISION_CANARY_READINESS =
PASS

CANARY_RECOMMENDATION =
READY_WITH_OBSERVATION

DECISION_ENGINE_STATE =
TEST_SINK_READY

PRODUCTION_CANARY_ENABLED =
false
```

Latest repaired current distribution:

```text
BUY  = 0
HOLD = 17
SELL = 3
```

SELL positive controls:

```text
RXRX
TSLA
WULF
```

Previously BUY but now adjudicated HOLD:

```text
003690 DB Insurance
GOOGL
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve latest safe origin/main
resolve actual operating checkout
use f7e082... or safe linear descendant
record exact lineage
```

---

# 1. Objective

Enable a small production canary for the analytical decision layer:

```text
AI 종합 판단: BUY / HOLD / SELL
추론등급: 매우 높음
판단 확신도
판단 기준
단기 타이밍
```

but only for:

```text
KR <= 2 monitored stocks
US <= 2 monitored stocks
```

All other monitored stocks continue using the existing production stock message WITHOUT the decision block.

No global enablement.

---

# 2. Hard product rule

Production canary must use the CURRENT natural decision for each selected stock.

Do not:

```text
force BUY for pathway coverage
replay historical BUY as current
override current HOLD/SELL
select the prettier AI result
```

BUY pathway coverage is test-only.

Hard:

```text
FORCED_CURRENT_BUY = 0
HISTORICAL_BUY_SENT_AS_CURRENT = 0
```

---

# 3. Recommended 2 + 2 canary subjects

Use the following as the DEFAULT recommended set, subject to current monitoring status and unchanged evidence contracts at execution time.

## KR

```text
003690 DB Insurance
000660 SK hynix
```

Why:

```text
003690
→ prior BUY → repaired HOLD
→ MEDIUM confidence
→ NEUTRAL timing
→ strong taxonomy/calibration control

000660
→ HOLD
→ MEDIUM confidence
→ UNFAVORABLE timing
→ high-expectation semiconductor / technical-context control
```

## US

```text
GOOGL
RXRX
```

Why:

```text
GOOGL
→ prior BUY → repaired HOLD
→ MEDIUM confidence
→ UNFAVORABLE timing
→ high-quality business + valuation/expectation conflict

RXRX
→ adjudicated SELL
→ MEDIUM confidence
→ UNFAVORABLE timing
→ genuine SELL-path live control
```

This set covers:

```text
KR + US
HOLD + SELL
NEUTRAL + UNFAVORABLE timing
high-quality business + expectation constraint
speculative/weak-economics SELL
prior BUY→HOLD calibration changes
```

---

# 4. Canary-subject failover policy

Do not silently substitute subjects.

If one recommended subject is:

```text
no longer monitored
data-quality blocked
security-basis invalid
decision packet unavailable
```

then:

```text
stop canary preparation
report unavailable subject
propose one replacement
require operator review before enablement
```

No automatic replacement.

Hard:

```text
AUTOMATIC_CANARY_SUBJECT_SUBSTITUTION = 0
```

---

# 5. Track A — freeze current canary evidence

Immediately before canary enablement:

for the four selected subjects create a fresh canonical decision evidence packet.

Record:

```text
ticker
decision
confidence
confidence reason
time horizon
timing
HOLD reason if applicable
WHY_NOT_BUY
WHY_NOT_SELL
bull evidence refs
bear evidence refs
key unknown
upgrade condition
downgrade condition
data-quality gates
```

Do not use stale shadow packets if fresh production evidence differs.

---

# 6. Decision freshness gate

The canary decision must use the same evidence cutoff as the stock message being delivered.

Hard:

```text
DECISION_PACKET_AS_OF =
STOCK_MESSAGE_AS_OF
```

or repository-native equivalent.

No:

```text
yesterday's decision + today's stock message
```

unless the product explicitly marks the decision as prior and that behavior is separately approved.

Preferred:

```text
generate decision in the current stock-message packet
```

---

# 7. Very-high reasoning contract

For the canary decision route:

use the strongest repository-supported reasoning configuration already validated in shadow.

User-facing:

```text
추론등급: 매우 높음
```

Backend:

use the supported configuration corresponding to very-high reasoning.

Do not invent a provider parameter.

Hard:

```text
CANARY_REASONING_GRADE = VERY_HIGH
```

---

# 8. Decision confidence remains separate

Display:

```text
판단 확신도: 높음 / 중간 / 낮음
```

or current canonical Korean mapping.

Do not map:

```text
추론등급 매우 높음
→ 확신도 높음
```

automatically.

Hard:

```text
REASONING_GRADE_AS_CONFIDENCE = 0
```

---

# 9. BUY positive-path technical proof

Current universe has no BUY.

Before production canary enablement, prove the BUY renderer/validator path separately using a TEST-ONLY historical canonical shadow fixture.

Preferred real fixtures:

```text
003690 prior canonical BUY shadow decision
GOOGL prior canonical BUY shadow decision
```

Use at least one, preferably both if both complete canonical packets are retained.

Required label in test sink:

```text
🧪 TEST FIXTURE · BUY 경로 검증
```

The fixture must include its historical `as_of`.

Do not modify the decision.

---

# 10. BUY fixture safety

The BUY fixture must never go to:

```text
production Telegram
production recipient
production decision state
monitoring assessment
```

Hard:

```text
BUY_FIXTURE_PRODUCTION_SEND = 0
BUY_FIXTURE_PRODUCTION_STATE_MUTATION = 0
```

---

# 11. BUY fixture validation

Verify:

```text
BUY label
reasoning grade
confidence
horizon
timing
bull case
bear case
decision-change conditions
no order-command wording
numeric provenance
exact payload
```

Hard:

```text
BUY_PATH_TEST_FIXTURE = PASS
```

If no retained canonical BUY fixture is available:

```text
BUY_PATH_TEST_FIXTURE = NOT_AVAILABLE
```

and canary may proceed only with explicit report of this limitation.

Do not synthesize a BUY.

---

# 12. Track B — production message contract

Only the four canary subjects get the decision block.

All other stocks:

```text
existing production message unchanged
```

Hard:

```text
NON_CANARY_DECISION_BLOCK_VISIBLE = 0
```

---

# 13. Decision block placement

Recommended placement:

```text
🏢 Company(TICKER)

🧠 AI 종합 판단: HOLD
추론등급: 매우 높음
판단 확신도: 중간
판단 기준: 6–24개월
단기 타이밍: 불리

🎯 판단
...

✅ BUY 쪽 근거
...

⚠️ SELL 쪽 근거
...

[existing message sections]
```

Do not duplicate the same thesis text twice.

The renderer may choose a more compact layout if already validated.

---

# 14. HOLD message requirement

For a canary HOLD:

the message must make both boundaries understandable:

```text
왜 BUY가 아닌가
왜 SELL이 아닌가
```

Do not necessarily use those literal headings if prose is concise.

Hard:

```text
CANARY_HOLD_WITHOUT_BUY_BOUNDARY = 0
CANARY_HOLD_WITHOUT_SELL_BOUNDARY = 0
```

---

# 15. SELL message requirement

For RXRX or another valid SELL canary:

make clear:

```text
SELL = current analytical risk/reward classification
```

not:

```text
formal thesis invalidation
mandatory liquidation
```

unless those stronger facts are independently true.

Hard:

```text
SELL_RENDERED_AS_MANDATORY_LIQUIDATION = 0
```

---

# 16. No trading-command language

Prohibit:

```text
지금 사세요
지금 파세요
전량 매도
시장가 매수
몇 % 비중
손절
목표가
```

unless separately owned by existing explicit price-rule systems, and never as output of this decision engine.

Hard:

```text
ORDER_COMMAND_LANGUAGE = 0
ORDER_SIZING_OUTPUT = 0
```

---

# 17. Existing message integrity

Preserve existing:

```text
investment logic
risk/warnings
monitoring metrics
market expectations
Price Structure
current price / structure basis
completed Bollinger
provisional Bollinger
stored price rules
valuation
positioning/flows
next check
```

The decision block is an additional analytical summary, not a replacement.

---

# 18. Price Structure integrity

Hard:

```text
PRICE_STRUCTURE_NUMERIC_DIFF = 0
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
PROVISIONAL_BOLLINGER_AUTHORITY_LEAK = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 19. Fundamental / timing separation

Required:

```text
decision
≠
timing
```

Allow:

```text
HOLD + NEUTRAL
HOLD + UNFAVORABLE
SELL + possible short-term rebound
BUY + unfavorable timing
```

Hard:

```text
TIMING_TO_DECISION_HARD_MAPPING = 0
```

---

# 20. MACD / technical safety

Preserve:

```text
MACD_ALONE_OWNS_BUY_SELL = 0
```

User-facing technical evidence should remain material and concise.

No technical indicator dump.

---

# 21. Track B — decision validator ownership

Validator must consume the same selected decision plan as the renderer.

Selected decision facts:

```text
must be rendered
```

Intentional omissions due message density:

```text
must not cause false failures
```

Do not reintroduce run-44-style legacy validator ownership.

Hard:

```text
VALIDATOR_RECOMPUTES_DECISION_SELECTION = 0
```

---

# 22. AI candidate failure behavior

If the decision-enabled AI candidate fails validation for a canary stock:

do NOT send the rejected decision.

Fallback behavior:

```text
deliver the existing non-decision production stock message
```

and record:

```text
CANARY_DECISION_SUPPRESSED_SAFE
```

Do not fabricate deterministic BUY/HOLD/SELL.

Hard:

```text
REJECTED_DECISION_SENT = 0
```

---

# 23. Canary delivery must remain exactly once

A failed decision candidate must not cause:

```text
duplicate stock message
one decision message + one fallback message
unowned retry
```

There must be exactly one production stock message per intended stock.

Hard:

```text
CANARY_DUPLICATE = 0
CANARY_ORPHAN = 0
CANARY_UNOWNED_RETRY = 0
```

---

# 24. Feature state

Create/reuse market/ticker-scoped state.

Required:

```text
DECISION_ENGINE_STATE = CANARY
```

with explicit subject membership:

```text
KR:
003690
000660

US:
GOOGL
RXRX
```

Do NOT turn on:

```text
FULL_MONITORED_UNIVERSE
```

---

# 25. No global code-default exposure

If the current decision block is code-default visible when the engine is enabled:

add/reuse the smallest subject-scoped gate.

Hard:

```text
GLOBAL_DECISION_BLOCK_ENABLED = 0
```

---

# 26. Track C — pre-enable test sink

Immediately before production canary:

send current production-equivalent messages for the four subjects to the dedicated non-production test sink.

Also send the BUY fixture message(s).

Expected:

```text
4 current canary messages
+ 1 or 2 BUY fixture messages
```

No production recipient.

---

# 27. Test-sink gates

Require:

```text
current decision correct
confidence correct
timing correct
message readable
existing stock message intact
BUY fixture clearly historical/test-only
exact payload match
```

Hard:

```text
PRECANARY_TEST_EXACT_PAYLOAD = PASS
PRECANARY_MESSAGE_QUALITY = PASS
TEST_PRODUCTION_RECIPIENT_SEND = 0
```

---

# 28. Canary enablement

Enable only after:

```text
fresh four-stock evidence PASS
BUY test fixture PASS or explicit NOT_AVAILABLE limitation
precanary test sink PASS
P0 = 0
material P1 = 0
```

Set:

```text
DECISION_ENGINE_STATE = CANARY
PRODUCTION_CANARY_ENABLED = true
```

only for the exact subject set.

---

# 29. No manual production decision blast

Do not manually send all four canary messages after enablement merely to prove the feature.

Observe them through their next normal/natural production stock-message cycles.

If an operator separately authorizes a one-shot proof later, use a separate instruction.

---

# 30. Track D — natural proof requirement

Require at least:

```text
2 natural production cycles per market
```

for the canary subjects.

KR:

```text
2 natural KR monitored-stock cycles
```

US:

```text
2 natural US monitored-stock cycles
```

Do not count test-sink sends.

---

# 31. Natural proof checklist

For every canary message:

```text
decision matches current packet
reasoning grade = very high
confidence separate
timing separate
bull/bear evidence
change conditions
Price Structure intact
valuation safe
no unsupported numeric
exactly once
```

---

# 32. Decision stability

If a canary subject changes:

```text
HOLD → SELL
SELL → HOLD
HOLD → BUY
```

require an evidence delta.

Record:

```text
previous decision
new decision
business delta
expectation/valuation delta
market delta
technical delta
data-quality delta
decisive cause
```

Hard:

```text
UNEXPLAINED_CANARY_DECISION_CHURN = 0
```

---

# 33. Current BUY=0 natural handling

If no natural BUY occurs during the canary window:

that is NOT a canary failure.

Record:

```text
NATURAL_BUY_LIVE_PROOF = PENDING
```

The historical BUY fixture proves renderer/validator plumbing only.

Live BUY proof remains pending until a real current BUY naturally occurs.

Do not relax the BUY threshold.

---

# 34. Canary stop conditions

Immediately disable the decision block for all canary subjects if any P0 occurs.

For a material P1:

```text
freeze expansion
consider disabling only the affected market/subject
depending on scope
```

Hard stop examples:

```text
wrong ticker decision
stale decision attached to current message
unsupported numeric
SELL rendered as mandatory liquidation
duplicate Telegram delivery
decision block on non-canary stock
decision validator bypass
business/security basis conflict
```

---

# 35. Rollback

Rollback must be one-step:

```text
DECISION_ENGINE_STATE = TEST_SINK_READY
PRODUCTION_CANARY_ENABLED = false
```

Existing non-decision stock messages continue normally.

No DB cleanup.
No history deletion.

---

# 36. Canary success criteria

After two natural cycles per market:

require:

```text
all canary messages valid
no unsupported numerics
no validator bypass
no duplicate/orphan
no unexplained churn
no message-quality regression
no false trading-command implication
P0 = 0
material P1 = 0
```

Then:

```text
BOUNDED_CANARY = LIVE_PASS
```

This still does NOT automatically authorize full-universe expansion.

---

# 37. Expansion review

After canary LIVE_PASS:

produce an expansion recommendation:

```text
HOLD
EXPAND_TO_MORE_SUBJECTS
FULL_MONITORED_UNIVERSE_READY
```

Do not auto-expand.

---

# 38. Required reports

Create:

1. `docs/reports/20260829-decision-canary-scope.md`
2. `docs/reports/20260829-decision-canary-subject-selection.md`
3. `docs/reports/20260829-decision-canary-fresh-evidence.md`
4. `docs/reports/20260829-decision-buy-positive-fixture.md`
5. `docs/reports/20260829-decision-canary-message-contract.md`
6. `docs/reports/20260829-decision-canary-validator-contract.md`
7. `docs/reports/20260829-decision-canary-preenable-test.md`
8. `docs/reports/20260829-decision-canary-operating-promotion.md`
9. `docs/reports/20260829-decision-canary-natural-cycle-1.md`
10. `docs/reports/20260829-decision-canary-natural-cycle-2.md`
11. `docs/reports/20260829-decision-canary-churn-analysis.md`
12. `docs/reports/20260829-decision-canary-final-status.md`
13. `docs/reports/20260829-decision-canary-expansion-recommendation.md`
14. `docs/reports/20260829-decision-canary-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-decision-canary-state.json
docs/reports/20260829-decision-canary-natural-proof.json
```

---

# 39. Required gates

Set exactly:

```text
CANARY_KR_COUNT =
2 / OTHER

CANARY_US_COUNT =
2 / OTHER

CANARY_KR_SUBJECTS =
...

CANARY_US_SUBJECTS =
...

AUTOMATIC_CANARY_SUBJECT_SUBSTITUTION =
0 / NONZERO

FORCED_CURRENT_BUY =
0 / NONZERO

HISTORICAL_BUY_SENT_AS_CURRENT =
0 / NONZERO

BUY_PATH_TEST_FIXTURE =
PASS / NOT_AVAILABLE / FAIL

BUY_FIXTURE_PRODUCTION_SEND =
0 / NONZERO

BUY_FIXTURE_PRODUCTION_STATE_MUTATION =
0 / NONZERO

CANARY_REASONING_GRADE =
VERY_HIGH / OTHER

REASONING_GRADE_AS_CONFIDENCE =
0 / NONZERO

CANARY_HOLD_WITHOUT_BUY_BOUNDARY =
0 / NONZERO

CANARY_HOLD_WITHOUT_SELL_BOUNDARY =
0 / NONZERO

SELL_RENDERED_AS_MANDATORY_LIQUIDATION =
0 / NONZERO

ORDER_COMMAND_LANGUAGE =
0 / NONZERO

ORDER_SIZING_OUTPUT =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

PROVISIONAL_BOLLINGER_AUTHORITY_LEAK =
0 / NONZERO

TIMING_TO_DECISION_HARD_MAPPING =
0 / NONZERO

MACD_ALONE_OWNS_BUY_SELL =
0 / NONZERO

VALIDATOR_RECOMPUTES_DECISION_SELECTION =
0 / NONZERO

REJECTED_DECISION_SENT =
0 / NONZERO

CANARY_DUPLICATE =
0 / NONZERO

CANARY_ORPHAN =
0 / NONZERO

CANARY_UNOWNED_RETRY =
0 / NONZERO

NON_CANARY_DECISION_BLOCK_VISIBLE =
0 / NONZERO

GLOBAL_DECISION_BLOCK_ENABLED =
0 / NONZERO

PRECANARY_TEST_EXACT_PAYLOAD =
PASS / FAIL

PRECANARY_MESSAGE_QUALITY =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

DECISION_ENGINE_STATE =
TEST_SINK_READY /
CANARY /
FULL_MONITORED_UNIVERSE

PRODUCTION_CANARY_ENABLED =
true / false

KR_NATURAL_CANARY_CYCLES =
0 / 1 / 2 / MORE

US_NATURAL_CANARY_CYCLES =
0 / 1 / 2 / MORE

NATURAL_BUY_LIVE_PROOF =
PENDING / PASS / FAIL

UNEXPLAINED_CANARY_DECISION_CHURN =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

BOUNDED_CANARY =
NOT_ENABLED /
ENABLED_AWAITING_NATURAL_PROOF /
LIVE_PASS /
FAIL

EXPANSION_RECOMMENDATION =
HOLD /
EXPAND_TO_MORE_SUBJECTS /
FULL_MONITORED_UNIVERSE_READY
```

---

# 40. Pre-enable PASS rule

Require:

```text
exact canary subjects confirmed
fresh decision packets valid
BUY fixture safe
test-sink messages PASS
decision validator PASS
Price Structure parity PASS
no order-command language
P0 = 0
material P1 = 0
```

Then:

```text
BOUNDED_CANARY = ENABLED_AWAITING_NATURAL_PROOF
```

---

# 41. Completion response — enablement stage

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_BRANCH = ...
TRACK_A_RESULT = ...

TRACK_B_BRANCH = ...
TRACK_B_IMPLEMENTATION = ...

TRACK_C_BRANCH = ...
TRACK_C_IMPLEMENTATION = ...

TRACK_D_BRANCH = ...
TRACK_D_STATUS = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

CANARY_KR_SUBJECTS = ...
CANARY_US_SUBJECTS = ...

CURRENT_DECISIONS =
...

BUY_PATH_TEST_FIXTURE = ...
BUY_FIXTURE_SOURCE = ...
BUY_FIXTURE_AS_OF = ...

PRECANARY_TEST_EXACT_PAYLOAD = ...
PRECANARY_MESSAGE_QUALITY = ...

NON_CANARY_DECISION_BLOCK_VISIBLE = 0
GLOBAL_DECISION_BLOCK_ENABLED = 0
REJECTED_DECISION_SENT = 0

PRODUCTION_CANARY_ENABLED = ...
DECISION_ENGINE_STATE = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

BOUNDED_CANARY =
ENABLED_AWAITING_NATURAL_PROOF /
FAIL

NEXT_ACTION =
WAIT_FOR_NATURAL_CANARY_CYCLES /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 42. Completion response — after natural proof

After two natural cycles per market, update:

```text
KR_NATURAL_CANARY_CYCLES = ...
US_NATURAL_CANARY_CYCLES = ...

NATURAL_CANARY_MESSAGES =
...

UNEXPLAINED_CANARY_DECISION_CHURN = 0
NATURAL_BUY_LIVE_PROOF = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

BOUNDED_CANARY =
LIVE_PASS /
FAIL

EXPANSION_RECOMMENDATION =
HOLD /
EXPAND_TO_MORE_SUBJECTS /
FULL_MONITORED_UNIVERSE_READY
```

---

# 43. Mandatory completion ZIP

Create:

`20260829-cross-market-decision-engine-bounded-canary-bundle.zip`

Include:

```text
exact master instruction
all track instructions
canary subject selection
fresh decision evidence
BUY positive fixture
message contract
validator contract
pre-enable test-sink messages
operating promotion
natural-cycle evidence
churn analysis
final canary status
expansion recommendation
machine-readable state JSON
test/CI summary
artifact index
```

Exclude:

```text
secrets
Telegram IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 44. Final principle

The canary must test the production product without changing the analytical standard.

Current BUY count is zero.

That is acceptable.

Use real current HOLD/SELL decisions in production,
prove BUY plumbing separately with a historical canonical test fixture,
and wait for the first genuine current BUY to obtain live BUY proof.

Do not manufacture a BUY for coverage.
