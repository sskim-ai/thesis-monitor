# thesis-monitor — Decision Calibration P1 Repair Before Canary
## Close the four material P1s from the 20-stock Decision Quality Review
## Repair taxonomy/calibration, not class distribution
## Re-run all 20 stocks blind after repair
## Canary remains OFF until P1 = 0

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `DECISION_CALIBRATION_P1_REPAIR_BEFORE_CANARY`
- Task class: `DECISION_TAXONOMY + TIMING + CONFIDENCE + CHANGE_CONDITION_REPAIR`
- Decision Engine current state: `TEST_SINK_READY`
- Production canary: `OFF`
- Production BUY/HOLD/SELL messages: `OFF`
- Automated trading: `0`
- Order sizing: `0`
- Production recipient send: `0`
- Thesis/monitoring mutation: `0`
- Scheduler mutation: `0`

Source bundle:

`20260829-cross-market-ai-decision-quality-review-before-canary-bundle.zip`

Source-supported latest state:

```text
FINAL_MAIN / OPERATING =
3317ef76b9f820b9deab6724f29544821b2a7ddc

BASELINE:
BUY 2 / HOLD 18 / SELL 0

FINAL REVIEW:
BUY 2 / HOLD 15 / SELL 3

Final review SELL:
RXRX
TSLA
WULF

BUY retained:
003690 DB Insurance
GOOGL

CANARY_RECOMMENDATION =
NOT_READY

OPEN_P0 =
0

OPEN_MATERIAL_P1 =
4
```

Before work:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve actual operating checkout
use 3317ef... or a safe linear descendant
record exact lineage
```

---

# 1. Four material P1s to close

The source review identifies exactly these open material P1s:

```text
P1-1
Resolve HUT's adjudication-confirmed DECISION_TAXONOMY defect.

P1-2
Resolve final timing for:
003690
005490
010120
GOOGL
SKHY
SNDK

P1-3
Resolve final confidence tiers for:
CORZ
SKHY
SNDK

P1-4
Add a downside decision-change trigger for adjudicated HOLD HUT.
Its supplied change conditions are upgrade-only.
```

Do not expand scope until these are closed.

---

# 2. Important non-P1 findings to preserve

Source review also found:

```text
HOLD_DEFAULT_BIAS = MATERIAL
SELL_SUPPRESSION_BIAS = MATERIAL

CONFIDENCE_CALIBRATION = NEEDS_REPAIR
TIMING_CALIBRATION = NEEDS_REPAIR

CROSS_MARKET_DECISION_SEMANTICS = PASS

MACD_ALONE_OWNS_BUY_SELL = 0
FORCED_SELL_FOR_CLASS_BALANCE = 0
ORDER_COMMAND_LANGUAGE = 0
```

These findings must guide the repair.

Do not "fix" bias by forcing more SELL labels.

---

# 3. P2 backlog

Source review records:

```text
- Standardize quantitative thresholds and observation windows
  for otherwise directional decision-change conditions.

- TSLA adjudication-noted DECISION_TAXONOMY P2 issue.
```

Do not let these P2 items block this P1 repair.

However:

if the same generic taxonomy repair naturally resolves the TSLA P2 issue
without scope expansion, include the regression test.

Do not create ticker-specific TSLA logic.

---

# 4. Repair philosophy

The goal is NOT:

```text
more SELL
fewer HOLD
more HIGH confidence
more favorable timing
```

The goal is:

```text
same canonical evidence
→ same semantic decision rules
→ stable classification
```

Hard:

```text
FORCED_CLASS_DISTRIBUTION_TARGET = 0
```

---

# 5. Track A — BUY/HOLD/SELL taxonomy

Create/update one canonical analytical-decision taxonomy.

Internal top-level enum remains:

```text
BUY
HOLD
SELL
```

No fourth top-level class.

---

# 6. BUY contract

BUY means:

```text
At the stated investment horizon,
expected upside/asymmetry is materially better than downside
based on current evidence,
with sufficient business/earnings/valuation support.
```

BUY does NOT require:

```text
favorable short-term timing
all technical indicators bullish
perfect data quality
```

But missing critical evidence must reduce confidence.

---

# 7. HOLD contract

HOLD must have one explicit subtype/reason category.

Allowed internal reason taxonomy:

```text
BALANCED_EVIDENCE
GOOD_BUSINESS_INSUFFICIENT_ASYMMETRY
VALUATION_EXPECTATION_CONSTRAINT
FUNDAMENTALS_NOT_YET_PROVEN
DATA_LIMITED
OPTIONALITY_OFFSETS_DOWNSIDE
THESIS_INTACT_TIMING_POOR
OTHER_DOCUMENTED
```

This is a reason taxonomy, not a new top-level decision.

Every HOLD must explicitly answer:

```text
WHY_NOT_BUY
WHY_NOT_SELL
```

Hard:

```text
HOLD_WITHOUT_WHY_NOT_BUY = 0
HOLD_WITHOUT_WHY_NOT_SELL = 0
```

---

# 8. SELL contract

SELL means:

```text
At the stated horizon,
current evidence makes downside / impaired risk-reward
materially dominate upside optionality.
```

SELL does NOT require:

```text
formal thesis invalidation
price breakdown
kill condition
```

Those are stronger states.

This distinction is mandatory.

A stock can be:

```text
business thesis not fully invalidated
but
analytical classification = SELL
```

when:

```text
valuation + expectations + weak economics + dilution/risk
```

make current risk/reward materially negative.

This is the key repair for SELL suppression.

---

# 9. HOLD vs SELL boundary

Define the boundary explicitly.

## HOLD

Use HOLD when:

```text
positive optionality / business evidence remains material
AND
negative evidence is meaningful
BUT
downside dominance is not sufficiently established.
```

## SELL

Use SELL when:

```text
negative present evidence is stronger and more direct than optional upside,
especially when:
- economics are unproven / deteriorating
- valuation / expectations remain demanding
- dilution / funding / structural risk is material
- bullish evidence is conditional or long-dated
```

Do not require all conditions.

No point score.

---

# 10. HUT mandatory taxonomy control

Source adjudication:

```text
Baseline = HOLD / LOW / UNFAVORABLE
Independent = SELL / MEDIUM / UNFAVORABLE
Adjudicated = HOLD / LOW / UNFAVORABLE

semantic_or_contract_problem =
DECISION_TAXONOMY

severity =
P1
```

Adjudicated decisive reason:

```text
AI/HPC infrastructure option value remains meaningful,
but contract revenue/margin conversion is unproven
and valuation/expectations are demanding.

This blocks BUY,
but current evidence is not yet sufficient to establish
downside dominance over the long-term option,
so HOLD is better supported.
```

Repair the generic taxonomy so HUT resolves to HOLD for the correct reason,
without ticker-specific exceptions.

Required HUT HOLD reason:

```text
OPTIONALITY_OFFSETS_DOWNSIDE
or semantically equivalent canonical reason
```

Hard:

```text
HUT_DECISION_TAXONOMY = PASS
```

---

# 11. RXRX / WULF / TSLA SELL positive controls

Final adjudicated SELLs:

```text
RXRX
TSLA
WULF
```

The repaired taxonomy must preserve these SELLs
unless a separate evidence-contract defect is found.

Why they matter:

```text
RXRX:
unproven economic/clinical repeatability
+ losses/cash burn/dilution
+ low P/B not enough

TSLA:
demanding valuation
+ speculative autonomy expectations
+ weakening profitability
+ monetization unproven

WULF:
HPC expectations
+ profitability/cash conversion unproven
+ high valuation
+ dilution risk
```

Hard:

```text
SELL_POSITIVE_CONTROLS = PASS
```

Do not hard-code ticker outcomes.
Use their evidence as semantic regression fixtures.

---

# 12. CRCL HOLD negative SELL control

Adjudication retained:

```text
CRCL = HOLD / LOW / INSUFFICIENT
```

despite independent SELL.

Reason:

```text
speculative expectations / demanding point valuation block BUY,
but historical/relative valuation evidence is insufficient
and USDC/platform optionality remains credible,
so SELL is not established.
```

Preserve this distinction.

Hard:

```text
CRCL_HOLD_SELL_BOUNDARY = PASS
```

---

# 13. Track B — timing taxonomy

Canonical timing enum remains:

```text
FAVORABLE
NEUTRAL
UNFAVORABLE
INSUFFICIENT
```

Do not infer timing from long-horizon BUY/HOLD/SELL.

---

# 14. FAVORABLE timing

FAVORABLE requires:

```text
current price/technical/positioning evidence
meaningfully supports entry timing
```

Examples may include:

```text
constructive Price Structure
support confirmation
positive multi-timeframe momentum
relative strength
non-adverse market/sector context
```

No single indicator required.

---

# 15. UNFAVORABLE timing

UNFAVORABLE means:

```text
usable timing evidence exists
AND
it materially argues against current entry/near-term setup.
```

Examples:

```text
weak relative strength
negative multi-timeframe momentum
distribution
poor price structure
elevated volatility
unfavorable market/sector setup
```

---

# 16. NEUTRAL timing

NEUTRAL means:

```text
usable timing evidence exists
AND
positive/negative timing evidence is balanced or not decisive.
```

Do not use NEUTRAL as a default for uncertainty.

---

# 17. INSUFFICIENT timing

INSUFFICIENT means:

```text
the required timing evidence is materially unavailable,
denied, stale, basis-conflicted, or incomplete enough
that a directional timing conclusion is not supportable.
```

This is distinct from NEUTRAL.

Hard:

```text
NEUTRAL_USED_FOR_DATA_INSUFFICIENT = 0
UNFAVORABLE_USED_WITHOUT_USABLE_TIMING_EVIDENCE = 0
```

---

# 18. Timing ownership hierarchy

Use timing evidence from:

```text
Price Structure
completed/provisional Bollinger
D/W/M OHLCV features
MACD
relative strength
volume/positioning
market/sector context
```

Technical timing is separate from investment classification.

Hard:

```text
TIMING_OWNS_LONG_HORIZON_DECISION = 0
```

---

# 19. Six unresolved timing cases

Resolve these deterministically from the canonical timing contract:

```text
003690
baseline UNFAVORABLE
independent NEUTRAL

005490
baseline NEUTRAL
independent UNFAVORABLE

010120
baseline NEUTRAL
independent UNFAVORABLE

GOOGL
baseline NEUTRAL
independent UNFAVORABLE

SKHY
baseline INSUFFICIENT
independent UNFAVORABLE

SNDK
baseline INSUFFICIENT
independent UNFAVORABLE
```

For each produce:

```text
usable timing evidence
missing timing evidence
positive timing evidence
negative timing evidence
final timing
decisive timing reason
```

Hard:

```text
TIMING_UNRESOLVED_COUNT_AFTER = 0
```

---

# 20. CRCL timing positive control

Adjudication resolved:

```text
CRCL = INSUFFICIENT
```

because:

```text
verified supply evidence was unavailable
and canonical chart contract lacked a confirmed setup.
```

Preserve.

Hard:

```text
CRCL_TIMING = INSUFFICIENT
```

unless the evidence packet has materially changed.

---

# 21. Track B — confidence taxonomy

Canonical confidence:

```text
HIGH
MEDIUM
LOW
```

Confidence is about:

```text
decision evidence quality and convergence
```

not reasoning effort.

Reasoning grade remains:

```text
VERY_HIGH
```

---

# 22. HIGH confidence

HIGH requires:

```text
critical evidence complete
security/currency basis safe
valuation basis safe enough for the decision
fundamental and market evidence reasonably convergent
few material unknowns
```

HIGH does NOT mean certainty.

---

# 23. MEDIUM confidence

MEDIUM means:

```text
decision is reasonably supported
but material uncertainty / conflict remains.
```

Examples:

```text
partial valuation uncertainty
fundamental vs technical conflict
expectation uncertainty
missing secondary evidence
```

---

# 24. LOW confidence

LOW means:

```text
top-level decision is the safest classification,
but critical evidence limitations or unresolved uncertainty
materially weaken confidence in direction.
```

Examples:

```text
critical valuation comparability missing
economic proof incomplete
security basis limitations
important data-quality denial
```

LOW does NOT automatically mean HOLD.

A BUY or SELL may be LOW confidence if direction is supported but evidence quality is weak.

---

# 25. Confidence reason taxonomy

Every confidence output must include one primary reason:

```text
EVIDENCE_CONVERGENT
MATERIAL_EVIDENCE_CONFLICT
DATA_QUALITY_LIMIT
VALUATION_LIMIT
SECURITY_BASIS_LIMIT
ECONOMIC_PROOF_LIMIT
OTHER_DOCUMENTED
```

This is diagnostic.

No numeric confidence score required.

---

# 26. Three unresolved confidence cases

Resolve:

```text
CORZ
baseline LOW
independent MEDIUM

SKHY
baseline LOW
independent MEDIUM

SNDK
baseline LOW
independent MEDIUM
```

For each determine:

```text
which missing/denied facts are decision-critical
whether the decision itself is stable
whether missing facts affect direction or only precision
```

Hard:

```text
CONFIDENCE_UNRESOLVED_COUNT_AFTER = 0
```

---

# 27. Confidence positive controls

Preserve source adjudications unless evidence-contract defects emerge:

```text
HUT = LOW
CRCL = LOW

RXRX = MEDIUM
TSLA = MEDIUM
WULF = MEDIUM
```

These controls distinguish:

```text
data/economic uncertainty
vs
directionally strong negative evidence
```

---

# 28. HIGH absence audit

After taxonomy repair, independently ask:

```text
Does any current stock genuinely deserve HIGH?
```

Do not force one.

If HIGH remains 0:

report why.

Hard:

```text
FORCED_HIGH_CONFIDENCE = 0
```

---

# 29. Track C — decision-change conditions

Every decision must contain:

```text
UPGRADE / more bullish condition
DOWNGRADE / more bearish condition
```

For HOLD specifically:

```text
HOLD → BUY condition
HOLD → SELL condition
```

For BUY:

```text
what strengthens BUY
what would reduce to HOLD/SELL
```

For SELL:

```text
what validates SELL
what would improve to HOLD/BUY
```

---

# 30. Conditions must be asymmetric and observable

Reject:

```text
only upside conditions
only downside conditions
vague "if momentum improves"
```

Require evidence-linked conditions.

Examples:

```text
margin / FCF / ROIC
expectations
valuation
dilution
contract economics
Price Structure
macro transmission
```

No invented thresholds.

---

# 31. HUT mandatory downside trigger

Source P1:

```text
HUT adjudicated HOLD
but supplied conditions are upgrade-only.
```

Add a canonical downside decision-change condition based only on existing evidence.

Conceptual shape:

```text
if contract economics fail to convert into revenue/margin/cash generation
or
funding/dilution risk worsens while valuation/expectations remain demanding,
HOLD may move toward SELL
```

Use exact existing evidence refs.

Do not invent numeric thresholds.

Hard:

```text
HUT_DOWNSIDE_CHANGE_CONDITION = PASS
```

---

# 32. Decision-change condition completeness

For all 20:

```text
UPGRADE_CONDITION_PRESENT
DOWNGRADE_CONDITION_PRESENT
EVIDENCE_REFS_PRESENT
```

Hard:

```text
MISSING_UPGRADE_CONDITION_COUNT = 0
MISSING_DOWNGRADE_CONDITION_COUNT = 0
UNOWNED_DECISION_CHANGE_CONDITION = 0
```

---

# 33. Track D — same-evidence blind rerun

After taxonomy/calibration repair:

rerun all 20 current decision evidence packets.

Rules:

```text
same evidence packet
same as_of
no new web facts
no future data
reasoning grade = VERY_HIGH
blind to prior label on first pass
```

Output:

```text
decision
hold reason if HOLD
confidence
confidence reason
timing
bull case
bear case
key unknown
change conditions
```

---

# 34. Blind review + adjudication

Compare repaired result with:

```text
baseline
prior independent review
prior adjudication
```

If new material disagreement appears:

run a bounded adjudication.

Do not mechanically preserve old adjudicated labels.

Do not mechanically choose the new result either.

---

# 35. Expected semantic controls

The following are controls, not hard-coded final outputs:

```text
003690 BUY should remain plausible
GOOGL BUY should remain plausible

RXRX SELL should remain plausible
TSLA SELL should remain plausible
WULF SELL should remain plausible

HUT HOLD should remain plausible
CRCL HOLD should remain plausible
```

If any flips:

require explicit evidence/taxonomy explanation.

---

# 36. Bias re-audit

After repair recompute:

```text
HOLD_DEFAULT_BIAS
SELL_SUPPRESSION_BIAS
```

Allowed final values:

```text
NONE
LOW
MATERIAL
FAIL
```

Canary cannot proceed if either remains `MATERIAL` or `FAIL`.

Hard:

```text
HOLD_DEFAULT_BIAS_AFTER != MATERIAL
SELL_SUPPRESSION_BIAS_AFTER != MATERIAL
```

---

# 37. Timing distribution audit

Recompute:

```text
FAVORABLE
NEUTRAL
UNFAVORABLE
INSUFFICIENT
```

Do not target a balanced distribution.

If FAVORABLE remains 0:

explain why.

If almost all remain UNFAVORABLE:

prove that the evidence supports it.

---

# 38. Confidence distribution audit

Recompute:

```text
HIGH
MEDIUM
LOW
```

Do not force HIGH.

Check whether:

```text
LOW is concentrated in real data/economic limits
MEDIUM covers genuine mixed evidence
HIGH only appears if evidence is strongly convergent
```

---

# 39. Fundamental-vs-timing separation

Mandatory controls:

```text
BUY + UNFAVORABLE
HOLD + favorable/neutral
SELL + technical rebound possibility
```

are all semantically allowed.

No timing state may automatically map:

```text
UNFAVORABLE → SELL
FAVORABLE → BUY
```

Hard:

```text
TIMING_TO_DECISION_HARD_MAPPING = 0
```

---

# 40. MACD isolation

Preserve:

```text
MACD_ALONE_OWNS_BUY_SELL = 0
```

MACD may materially own timing.

Do not reduce timing to MACD only.

---

# 41. Fixed-score prohibition

Do not implement:

```text
axis scoring
weighted sum
threshold on bull vs bear count
```

Hard:

```text
FINAL_DECISION_FROM_FIXED_WEIGHT_SUM = 0
AXIS_STATE_USED_AS_FIXED_SCORE = 0
```

---

# 42. Validator updates

If taxonomy fields are added:

validator must enforce:

```text
HOLD → why_not_buy + why_not_sell + hold_reason
all decisions → confidence_reason
all decisions → timing basis
all decisions → upgrade + downgrade conditions
```

But intentional renderer omission due display budget remains allowed.

Do not repeat legacy run-44 ownership errors.

---

# 43. Numeric/provenance safety

This repair should add almost no new numerics.

Any selected numeric still requires canonical fact refs.

Hard:

```text
UNREGISTERED_DECISION_NUMERIC = 0
DECISION_NUMERIC_WITHOUT_PROVENANCE = 0
```

---

# 44. Test-sink rerun

After 20/20 repaired shadow decisions pass:

send all 20 decision-enabled messages to the dedicated non-production test sink.

No production recipient.

Verify exact payload.

Hard:

```text
TEST_DECISION_MESSAGE_COUNT = 20
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 45. Message quality

Every exact message must clearly distinguish:

```text
AI 종합 판단
추론등급: 매우 높음
판단 확신도
판단 기준
단기 타이밍
```

For HOLD include user-readable:

```text
왜 BUY가 아닌가
왜 SELL이 아닌가
```

or equivalent concise prose.

Do not turn the message into a taxonomy dump.

---

# 46. Production state

This task does NOT enable canary.

During the entire task:

```text
PRODUCTION_CANARY_ENABLED = false
DECISION_ENGINE_STATE = TEST_SINK_READY
```

At completion:

only output canary readiness.

---

# 47. Canary readiness rule

Set:

```text
DECISION_CANARY_READINESS = PASS
```

only if:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

HUT_DECISION_TAXONOMY = PASS
TIMING_UNRESOLVED_COUNT_AFTER = 0
CONFIDENCE_UNRESOLVED_COUNT_AFTER = 0
HUT_DOWNSIDE_CHANGE_CONDITION = PASS

HOLD_DEFAULT_BIAS_AFTER in {NONE, LOW}
SELL_SUPPRESSION_BIAS_AFTER in {NONE, LOW}

CONFIDENCE_CALIBRATION = PASS
TIMING_CALIBRATION = PASS
DECISION_CHANGE_CONDITION_QUALITY = PASS
CROSS_MARKET_DECISION_SEMANTICS = PASS

20/20 shadow validation PASS
20/20 test-sink exact PASS
```

Do NOT enable canary automatically.

---

# 48. Proposed canary set

Only if readiness PASS:

produce a recommendation.

The previous review proposed:

```text
003690
086280
010120
GOOGL
CRCL
RXRX
```

Do not automatically reuse it.

Re-evaluate after repair.

A bounded canary recommendation should cover diverse states:

```text
KR + US
BUY + HOLD + SELL
high-quality evidence + data-limited
different timing states
```

The next operator task may further reduce to <=2 KR + <=2 US.

---

# 49. Required reports

Create:

1. `docs/reports/20260829-decision-calibration-p1-scope.md`
2. `docs/reports/20260829-buy-hold-sell-taxonomy.md`
3. `docs/reports/20260829-hold-sell-boundary.md`
4. `docs/reports/20260829-hut-taxonomy-repair.md`
5. `docs/reports/20260829-sell-positive-controls.md`
6. `docs/reports/20260829-timing-taxonomy.md`
7. `docs/reports/20260829-six-timing-case-resolution.md`
8. `docs/reports/20260829-confidence-taxonomy.md`
9. `docs/reports/20260829-three-confidence-case-resolution.md`
10. `docs/reports/20260829-decision-change-condition-contract.md`
11. `docs/reports/20260829-hut-downside-condition.md`
12. `docs/reports/20260829-repaired-20-stock-blind-review.md`
13. `docs/reports/20260829-repaired-decision-agreement.md`
14. `docs/reports/20260829-repaired-adjudication.md`
15. `docs/reports/20260829-hold-default-bias-after.md`
16. `docs/reports/20260829-sell-suppression-bias-after.md`
17. `docs/reports/20260829-confidence-calibration-after.md`
18. `docs/reports/20260829-timing-calibration-after.md`
19. `docs/reports/20260829-decision-test-sink-after-calibration.md`
20. `docs/reports/20260829-decision-canary-readiness-after-calibration.md`
21. `docs/reports/20260829-decision-calibration-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-repaired-20-stock-decisions.json
docs/reports/20260829-decision-calibration-readiness.json
```

---

# 50. Required gates

Set exactly:

```text
HUT_DECISION_TAXONOMY =
PASS / FAIL

SELL_POSITIVE_CONTROLS =
PASS / FAIL

CRCL_HOLD_SELL_BOUNDARY =
PASS / FAIL

HOLD_WITHOUT_WHY_NOT_BUY =
0 / NONZERO

HOLD_WITHOUT_WHY_NOT_SELL =
0 / NONZERO

FORCED_CLASS_DISTRIBUTION_TARGET =
0 / NONZERO

NEUTRAL_USED_FOR_DATA_INSUFFICIENT =
0 / NONZERO

UNFAVORABLE_USED_WITHOUT_USABLE_TIMING_EVIDENCE =
0 / NONZERO

TIMING_OWNS_LONG_HORIZON_DECISION =
0 / NONZERO

TIMING_UNRESOLVED_COUNT_BEFORE =
6

TIMING_UNRESOLVED_COUNT_AFTER =
...

CRCL_TIMING =
INSUFFICIENT / OTHER

CONFIDENCE_UNRESOLVED_COUNT_BEFORE =
3

CONFIDENCE_UNRESOLVED_COUNT_AFTER =
...

FORCED_HIGH_CONFIDENCE =
0 / NONZERO

HUT_DOWNSIDE_CHANGE_CONDITION =
PASS / FAIL

MISSING_UPGRADE_CONDITION_COUNT =
0 / NONZERO

MISSING_DOWNGRADE_CONDITION_COUNT =
0 / NONZERO

UNOWNED_DECISION_CHANGE_CONDITION =
0 / NONZERO

REPAIRED_SHADOW_COUNT =
20 / OTHER

REPAIRED_BUY_COUNT =
...

REPAIRED_HOLD_COUNT =
...

REPAIRED_SELL_COUNT =
...

HOLD_DEFAULT_BIAS_AFTER =
NONE / LOW / MATERIAL / FAIL

SELL_SUPPRESSION_BIAS_AFTER =
NONE / LOW / MATERIAL / FAIL

CONFIDENCE_CALIBRATION =
PASS / NEEDS_REPAIR / FAIL

TIMING_CALIBRATION =
PASS / NEEDS_REPAIR / FAIL

DECISION_CHANGE_CONDITION_QUALITY =
PASS / NEEDS_REPAIR / FAIL

CROSS_MARKET_DECISION_SEMANTICS =
PASS / MATERIAL_INCONSISTENCY / FAIL

TIMING_TO_DECISION_HARD_MAPPING =
0 / NONZERO

MACD_ALONE_OWNS_BUY_SELL =
0 / NONZERO

FINAL_DECISION_FROM_FIXED_WEIGHT_SUM =
0 / NONZERO

AXIS_STATE_USED_AS_FIXED_SCORE =
0 / NONZERO

UNREGISTERED_DECISION_NUMERIC =
0 / NONZERO

DECISION_NUMERIC_WITHOUT_PROVENANCE =
0 / NONZERO

TEST_DECISION_MESSAGE_COUNT =
20 / OTHER

TEST_DECISION_MESSAGE_QUALITY =
PASS / FAIL

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

PRODUCTION_CANARY_ENABLED =
false / true

DECISION_ENGINE_STATE =
TEST_SINK_READY / OTHER

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

DECISION_CANARY_READINESS =
PASS / FAIL / BLOCKED

CANARY_RECOMMENDATION =
READY /
READY_WITH_OBSERVATION /
NOT_READY
```

---

# 51. Completion response

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
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

HUT_DECISION_TAXONOMY = ...
HUT_FINAL_DECISION = ...
HUT_HOLD_REASON = ...
HUT_DOWNSIDE_CHANGE_CONDITION = ...

SELL_POSITIVE_CONTROLS = ...
CRCL_HOLD_SELL_BOUNDARY = ...

TIMING_CASES =
- 003690: ...
- 005490: ...
- 010120: ...
- GOOGL: ...
- SKHY: ...
- SNDK: ...

TIMING_UNRESOLVED_COUNT_AFTER = 0

CONFIDENCE_CASES =
- CORZ: ...
- SKHY: ...
- SNDK: ...

CONFIDENCE_UNRESOLVED_COUNT_AFTER = 0

REPAIRED_BUY_COUNT = ...
REPAIRED_HOLD_COUNT = ...
REPAIRED_SELL_COUNT = ...

REPAIRED_20_STOCK_DECISIONS =
...

HOLD_DEFAULT_BIAS_AFTER = ...
SELL_SUPPRESSION_BIAS_AFTER = ...

CONFIDENCE_CALIBRATION = ...
TIMING_CALIBRATION = ...
DECISION_CHANGE_CONDITION_QUALITY = ...
CROSS_MARKET_DECISION_SEMANTICS = ...

MISSING_UPGRADE_CONDITION_COUNT = 0
MISSING_DOWNGRADE_CONDITION_COUNT = 0

TIMING_TO_DECISION_HARD_MAPPING = 0
MACD_ALONE_OWNS_BUY_SELL = 0
FINAL_DECISION_FROM_FIXED_WEIGHT_SUM = 0
AXIS_STATE_USED_AS_FIXED_SCORE = 0

TEST_DECISION_MESSAGE_COUNT = 20
TEST_DECISION_MESSAGE_QUALITY = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

PRODUCTION_CANARY_ENABLED = false
DECISION_ENGINE_STATE = TEST_SINK_READY

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

DECISION_CANARY_READINESS =
PASS /
FAIL /
BLOCKED

CANARY_RECOMMENDATION =
READY /
READY_WITH_OBSERVATION /
NOT_READY

PROPOSED_CANARY_SET =
...

NEXT_ACTION =
PREPARE_BOUNDED_CANARY_INSTRUCTION /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 52. Mandatory completion ZIP

Create:

`20260829-decision-calibration-p1-repair-before-canary-bundle.zip`

Include:

```text
exact instruction
all track instructions
decision taxonomy
HOLD/SELL boundary
HUT repair
timing taxonomy and six-case resolution
confidence taxonomy and three-case resolution
decision-change condition contract
HUT downside trigger
20-stock blind rerun
adjudications
bias re-audit
test-sink exact messages
canary readiness
machine-readable JSON
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

# 53. Final principle

Do not repair the engine by making it more bullish, more bearish, or more decisive.

Repair it so:

```text
BUY / HOLD / SELL
timing
confidence
decision-change conditions
```

each have a clear independent semantic contract.

Then re-run the same 20 evidence packets blind.

Only if the material P1 count reaches zero should production canary be reconsidered.
