# thesis-monitor — Cross-Market AI Decision Quality Review Before Canary
## Review all 20 current shadow BUY / HOLD / SELL decisions before any production canary
## Independent very-high-reasoning challenge review using the same canonical evidence packets
## Detect HOLD bias, SELL suppression, valuation-vs-momentum conflicts, confidence miscalibration, and cross-market inconsistency
## No production enablement in this task

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `CROSS_MARKET_AI_DECISION_QUALITY_REVIEW_BEFORE_CANARY`
- Task class: `READ_ONLY_DECISION_AUDIT + INDEPENDENT_SHADOW_REVIEW + CALIBRATION`
- Decision Engine current state: `TEST_SINK_READY`
- Production canary current state: `OFF`
- Production BUY/HOLD/SELL exposure: `OFF`
- Automated trade execution: `0`
- Brokerage/order action: `0`
- Thesis/monitoring mutation: `0`
- Production Telegram send: `0`
- Scheduler mutation: `0`

Source bundle:

`20260829-cross-market-ai-decision-engine-v1-bundle.zip`

Source bundle SHA-256:

`47539df2abb50f89400c71857ad755161f3d1ed30eebd6177c500251a31268e6`

Latest source-supported implementation state:

```text
Base / previous operating:
7269120fb4d97abb61c5d5d5f91863f4c998e84b

Implementation:
f28d4bb3b8eacebe7fb48a3ca7800094711793eb

DECISION_ENGINE_STATE:
TEST_SINK_READY

DECISION_CANARY_READINESS:
PASS

PRODUCTION_CANARY_ENABLED:
false

Open P0 / material P1:
0 / 0
```

Before analysis:

```text
git fetch origin
resolve actual latest safe origin/main
resolve actual operating checkout
record exact lineage
```

Do not enable production canary in this task.

---

# 1. Objective

Determine whether the current 20-stock shadow decisions are economically and semantically well-calibrated before any user-visible canary.

Current distribution:

```text
BUY  = 2
HOLD = 18
SELL = 0
```

The review must answer:

```text
1. Are the two BUY decisions genuinely supported?
2. Are any HOLD decisions actually BUY?
3. Are any HOLD decisions actually SELL?
4. Is SELL=0 a legitimate consequence of the evidence,
   or does the engine have a structural conservatism / HOLD-default bias?
5. Are confidence levels calibrated to data quality and evidence conflict?
6. Does the engine treat KR and US evidence consistently?
7. Are valuation and market expectations receiving enough weight?
8. Are technical/OHLCV signals influencing timing appropriately
   without overriding long-horizon fundamentals?
9. Does missing/denied valuation data automatically push too many stocks to HOLD?
10. Are decision-change conditions specific enough to be useful?
```

---

# 2. Current shadow baseline to preserve

The source bundle reports the following accepted shadow classifications.

## KR

```text
000660 SK hynix
HOLD / confidence MEDIUM / timing UNFAVORABLE / horizon 12-36개월

003690 DB Insurance
BUY / confidence MEDIUM / timing UNFAVORABLE / horizon 12-36개월

005490 POSCO Holdings
HOLD / confidence MEDIUM / timing NEUTRAL / horizon 6~24개월

005930 Samsung Electronics
HOLD / confidence MEDIUM / timing UNFAVORABLE / horizon 6~24개월

010120 LS ELECTRIC
HOLD / confidence MEDIUM / timing NEUTRAL / horizon 6-24개월

012450 Hanwha Aerospace
HOLD / confidence MEDIUM / timing UNFAVORABLE / horizon 6-24개월

086280 Hyundai Glovis
HOLD / confidence MEDIUM / timing NEUTRAL / horizon 6~24개월
```

## US / foreign

```text
CORZ
HOLD / LOW / UNFAVORABLE / 12-36개월

CRCL
HOLD / LOW / INSUFFICIENT / 6~24개월

GOOGL
BUY / MEDIUM / NEUTRAL / 6~24개월

HUT
HOLD / LOW / UNFAVORABLE / 12-36개월

IBM
HOLD / MEDIUM / NEUTRAL / 6~24개월

MU
HOLD / MEDIUM / UNFAVORABLE / 12-36개월

RXRX
HOLD / LOW / UNFAVORABLE / 6~24개월

SKHY
HOLD / LOW / INSUFFICIENT / 12-36개월

SNDK
HOLD / LOW / INSUFFICIENT / 6~24개월

TSLA
HOLD / MEDIUM / UNFAVORABLE / 6~24개월

TSM
HOLD / MEDIUM / UNFAVORABLE / 6~24개월

WRD
HOLD / LOW / UNFAVORABLE / 6~24개월

WULF
HOLD / MEDIUM / UNFAVORABLE / 12-36개월
```

Do not modify these source decisions in-place.

They are the baseline being audited.

---

# 3. Current BUY decisions — mandatory challenge cases

## 3.1 DB Insurance (003690)

Source decisive reason:

```text
검증된 장부가치 기준의 할인과 균형적인 시장 기대가 존재하고
최신 이익 자료도 주의 조건 아래 사용 가능해,
언더라이팅·자본환원 논리의 장기 위험보상이 긍정적이라는 점이 BUY의 결정적 이유다.
```

But:

```text
timing = UNFAVORABLE
confidence = MEDIUM
```

Review whether:

```text
long-horizon BUY + unfavorable timing
```

is coherent and useful.

Challenge:

```text
Would HOLD be more appropriate until combined ratio / ROE /
investment yield / capital adequacy trend is sufficiently verified?
```

Also challenge the opposite:

```text
Is the existing discount so compelling that BUY is justified
even with incomplete underwriting trend evidence?
```

---

## 3.2 GOOGL

Source decisive reason:

```text
Search, Cloud, AI earnings thesis
+
trailing earnings valuation near the lower portion of its high-quality history
→ BUY
```

with:

```text
confidence = MEDIUM
timing = NEUTRAL
expectations = elevated
capex risk = material
```

Challenge:

```text
Does the valuation discount adequately compensate for elevated AI expectations
and capital-spending intensity?
```

Also challenge:

```text
Is the current BUY too conservative at MEDIUM confidence
if business quality + valuation + earnings path align strongly?
```

---

# 4. Mandatory HOLD challenge cases

At minimum perform deep review on:

```text
000660 SK hynix
005930 Samsung Electronics
012450 Hanwha Aerospace
MU
TSM
TSLA
CRCL
SNDK
RXRX
WULF
```

Why:

```text
000660 / 005930 / MU / TSM
→ strong AI/semiconductor fundamentals vs high expectations / valuation / timing

012450
→ strong backlog/profitability vs high expectations / pursuit risk

TSLA
→ extreme expectations / valuation vs optionality

CRCL / SNDK
→ attractive themes but speculative expectations / data-quality limitations

RXRX
→ weak economic proof / dilution risk vs depressed valuation

WULF
→ AI/HPC optionality vs current profitability / dilution / valuation
```

For every HOLD ask both:

```text
What prevents BUY?
What prevents SELL?
```

A HOLD is valid only if both answers are explicit and evidence-grounded.

---

# 5. SELL=0 bias audit

This is a mandatory product-level review.

Determine whether SELL=0 is caused by:

```text
A. genuinely balanced current universe

B. HOLD as a safe default whenever:
   valuation is uncertain
   security basis is unclear
   financial-quality data is denied

C. insufficient downside taxonomy

D. insufficient weighting of:
   speculative expectations
   dilution
   deteriorating fundamentals
   extreme valuation
   poor risk/reward

E. asymmetric product policy:
   BUY allowed on positive inference
   but SELL requires near-invalidation-level evidence
```

Do not force a SELL for distributional balance.

Hard:

```text
FORCED_SELL_FOR_CLASS_BALANCE = 0
```

But do identify whether the decision contract itself suppresses legitimate SELL outcomes.

---

# 6. HOLD-default audit

For each of 18 HOLD decisions classify the primary reason:

```text
BALANCED_EVIDENCE
VALUATION_TOO_HIGH
EXPECTATIONS_TOO_HIGH
FUNDAMENTALS_NOT_YET_PROVEN
DATA_QUALITY_LIMIT
SECURITY_BASIS_LIMIT
UNFAVORABLE_TIMING
DILUTION_RISK
THESIS_WEAKENING
OTHER
```

Then aggregate.

If a large share of HOLDs result from:

```text
DATA_QUALITY_LIMIT
SECURITY_BASIS_LIMIT
```

determine whether the correct product response is:

```text
HOLD
```

or:

```text
HOLD / 판단 제한
```

without creating a fourth top-level decision.

---

# 7. Independent second-pass reviewer

Run a separate reviewer pass using:

```text
same canonical decision_evidence_packet
same numeric facts
same as_of
same time horizon
same source availability
```

but a distinct prompt role:

```text
"Challenge the original decision.
Try to falsify it.
Do not preserve the baseline classification unless the evidence warrants it."
```

Reasoning grade:

```text
VERY_HIGH
```

The reviewer must NOT receive the future outcome.

No web enrichment.
No extra facts outside the packet.

This is a decision-quality audit, not a research refresh.

---

# 8. Blindness policy

Preferred:

```text
Reviewer first sees the evidence packet without original BUY/HOLD/SELL label.
```

After the reviewer independently classifies:

```text
BUY / HOLD / SELL
```

then compare with baseline.

If implementation constraints require the baseline label to be visible:

record that as a calibration limitation.

Set:

```text
INDEPENDENT_REVIEW_LABEL_BLIND =
PASS / PARTIAL / FAIL
```

---

# 9. Reviewer output

For each stock require:

```text
independent_decision
confidence
timing
decisive_reason
strongest_bull_case
strongest_bear_case
key_unknown
valuation_assessment
expectation_assessment
technical_assessment
data_quality_assessment
decision_change_conditions
```

No new numerics.

---

# 10. Decision agreement matrix

For every stock create:

```text
ticker
baseline decision
independent decision
agreement
baseline confidence
independent confidence
timing agreement
reason-level agreement
```

Agreement categories:

```text
EXACT
SAME_DECISION_DIFFERENT_CONFIDENCE
SAME_DECISION_MATERIAL_REASON_CONFLICT
ONE_STEP_DISAGREEMENT
TWO_STEP_DISAGREEMENT
```

Examples:

```text
BUY ↔ HOLD = ONE_STEP
HOLD ↔ SELL = ONE_STEP
BUY ↔ SELL = TWO_STEP
```

---

# 11. Material disagreement policy

A material disagreement is:

```text
decision differs
or
same decision but decisive rationale materially conflicts
or
confidence differs by >= 2 internal confidence tiers
```

For each material disagreement:

```text
do NOT silently update baseline
```

Create an adjudication record.

---

# 12. Third-pass adjudication

Only for material disagreements:

run a third very-high-reasoning adjudicator using:

```text
same canonical evidence packet
baseline reasoning
independent reasoning
```

The adjudicator must answer:

```text
Which decision is better supported?
Which argument improperly over/underweighted evidence?
Was there a semantic or product-contract problem?
```

Do not use majority voting mechanically.

---

# 13. Axis-by-axis review

For every stock classify these axes:

```text
business quality
earnings trajectory
earnings quality
market expectations
valuation
catalyst profile
structural risk
macro sensitivity
market/sector context
positioning/flows
Price Structure
technical momentum
data quality
```

State per axis:

```text
POSITIVE
NEUTRAL
NEGATIVE
UNKNOWN
```

This is diagnostic only.

The final decision must still NOT be generated by fixed score summation.

Hard:

```text
AXIS_STATE_USED_AS_FIXED_SCORE = 0
```

---

# 14. Fundamental vs technical conflict review

For every stock identify one of:

```text
ALIGNED_POSITIVE
ALIGNED_NEGATIVE
FUNDAMENTAL_POSITIVE_TECHNICAL_NEGATIVE
FUNDAMENTAL_NEGATIVE_TECHNICAL_POSITIVE
MIXED
INSUFFICIENT
```

Special focus:

```text
000660
005930
012450
MU
TSM
```

Determine whether `UNFAVORABLE` timing is appropriately separated from long-horizon classification.

---

# 15. Valuation vs expectations review

For every stock explicitly compare:

```text
valuation attractiveness
vs
market expectation level
```

Examples to challenge:

```text
cheap but low quality / uncertain
expensive but extraordinary earnings durability
high expectations + high valuation
low expectations + weak fundamentals
```

Do not equate low PBR/PER with BUY automatically.

---

# 16. Data-quality penalty audit

List all stocks where classification is materially influenced by:

```text
financial_quality denied
valuation basis unavailable
security basis unverified
ADR basis uncertainty
missing forward valuation
insufficient OHLCV feature history
```

For each ask:

```text
Does this appropriately reduce confidence?
Does it incorrectly force HOLD?
Could the business conclusion still support BUY/SELL while confidence is low?
```

This is particularly important for:

```text
000660
010120
012450
CORZ
CRCL
SKHY
SNDK
TSM
WRD
```

---

# 17. Confidence calibration

Current source decisions appear to use:

```text
MEDIUM
LOW
```

with no source-supported HIGH decisions in the 20-stock set.

Audit whether:

```text
HIGH is structurally too difficult to reach
or
current evidence genuinely does not justify HIGH
```

For every BUY:

```text
why not HIGH?
```

For each LOW HOLD:

```text
is LOW because decision itself is uncertain,
or because data quality is incomplete?
```

These should be distinguishable.

---

# 18. Timing calibration

Current timing states include:

```text
UNFAVORABLE
NEUTRAL
INSUFFICIENT
```

Audit:

```text
why no favorable timing states?
```

Do not force one.

But determine whether:

```text
technical feature engine
Price Structure
relative strength
market context
```

has a structural pessimism bias.

---

# 19. OHLCV feature contribution review

For every current shadow decision record which OHLCV feature families were actually material to the final decision:

```text
returns/trend
SMA/EMA
MACD
RSI
ATR/volatility
Bollinger
ADX/DMI
ROC/Stochastic
volume-derived
breakout/channel
validated divergence
```

Separate:

```text
available feature
selected evidence
decisive evidence
```

A feature being available does not mean it should affect the classification.

---

# 20. MACD review

Because MACD was newly enabled:

for each ticker record D/W/M:

```text
availability
state
selected or omitted
decision contribution
timing contribution
```

Determine whether MACD is being used primarily as:

```text
timing context
```

rather than long-horizon valuation/business authority.

Hard:

```text
MACD_ALONE_OWNS_BUY_SELL = 0
```

---

# 21. Cross-market consistency

Compare similar situations across KR / US.

Examples:

```text
000660 / MU / TSM
→ AI-memory exposure, high expectations, technical timing

005930 / TSM
→ high-quality semiconductor franchises

010120 / IBM
→ quality business + expectations/valuation

012450 / high-growth US names
→ backlog/growth visibility vs valuation/expectations
```

Look for inconsistent standards.

Set:

```text
CROSS_MARKET_DECISION_SEMANTICS =
PASS / MATERIAL_INCONSISTENCY / FAIL
```

---

# 22. New buyer vs holder perspective

For every stock require separate interpretation:

```text
NEW_BUYER_VIEW
HOLDER_VIEW
```

A `HOLD` classification should not mean the same thing for both.

Example:

```text
HOLD
new buyer → wait / asymmetry insufficient
holder → thesis intact, no exit evidence
```

For BUY:

```text
new buyer → attractive long-horizon setup
holder → thesis supports continued ownership
```

For SELL:

```text
new buyer → avoid
holder → downside evidence dominates
```

Still no order command.

---

# 23. Decision-change condition quality

Audit whether each condition is:

```text
observable
specific
evidence-linked
decision-relevant
```

Reject vague conditions such as:

```text
"if things improve"
"if momentum weakens"
```

Prefer:

```text
specific margin / earnings / expectation / valuation / Price Structure / macro transmission metrics
```

Do not invent unsupported thresholds.

---

# 24. Decision-language quality

The exact test message should make clear:

```text
AI 종합 판단 = analytical classification
추론등급 = reasoning depth
판단 확신도 = evidence confidence
단기 타이밍 = separate dimension
```

Avoid:

```text
즉시 매수
전량 매도
무조건 보유
```

Hard:

```text
ORDER_COMMAND_LANGUAGE = 0
```

---

# 25. No production change

This task must NOT:

```text
enable canary
change DECISION_ENGINE_STATE to CANARY
send BUY/HOLD/SELL to production recipients
change monitoring thesis
change price rules
change assessments
```

Final engine state after this task should remain:

```text
TEST_SINK_READY
```

unless the task fails and requires repair.

---

# 26. Repair classification

If the audit finds issues, classify:

```text
PROMPT_REASONING_BIAS
EVIDENCE_PACKET_GAP
CONFIDENCE_CALIBRATION
DECISION_TAXONOMY
TIMING_CALIBRATION
VALIDATOR_OWNERSHIP
MESSAGE_RENDERING
DATA_QUALITY
NO_MATERIAL_DEFECT
```

Do not modify runtime inside this review unless the instruction is explicitly extended.

The primary output is a review/readiness bundle.

---

# 27. Canary recommendation only

At the end, produce:

```text
CANARY_RECOMMENDATION =
READY /
READY_WITH_OBSERVATION /
NOT_READY
```

Do not enable.

If `READY`, propose a bounded candidate set that covers diverse states.

Preferred diversity:

```text
one BUY with unfavorable timing
one BUY with neutral timing
one HOLD with strong fundamentals/high expectations
one HOLD with low confidence/data limitation
```

This is a recommendation only.

---

# 28. Required operator summary

Create one compact 20-row table:

```text
market
ticker
baseline decision
independent decision
adjudicated decision
confidence
timing
business
expectations
valuation
technical
data quality
top bull
top bear
key unknown
disagreement state
```

This is the primary review artifact.

---

# 29. Required deep-dive reports

At minimum create detailed case reviews for:

```text
003690
GOOGL
000660
005930
012450
MU
TSM
TSLA
CRCL
SNDK
RXRX
WULF
```

---

# 30. Required distribution diagnostics

Report:

```text
baseline BUY/HOLD/SELL distribution
independent distribution
adjudicated distribution

confidence distribution
timing distribution
HOLD reason distribution
data-quality-limited count
valuation-limited count
expectation-limited count
technical-unfavorable count
```

If SELL remains 0:

explain why.

If SELL appears in independent/adjudicated review:

show exact evidence.

---

# 31. Required historical replay context

Use the existing temporal shadow replay only as a secondary diagnostic.

Do NOT claim predictive calibration from the current `PARTIAL_SAFE` historical replay.

State clearly:

```text
historical feature reconstruction is incomplete
forward outcome evaluation is not yet sufficient for production performance claims
```

Hard:

```text
PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA = 0
```

---

# 32. Required reports

Create:

1. `docs/reports/20260829-decision-quality-review-scope.md`
2. `docs/reports/20260829-current-20-decision-baseline.md`
3. `docs/reports/20260829-independent-blind-review.md`
4. `docs/reports/20260829-decision-agreement-matrix.md`
5. `docs/reports/20260829-material-disagreement-adjudication.md`
6. `docs/reports/20260829-buy-case-db-insurance.md`
7. `docs/reports/20260829-buy-case-googl.md`
8. `docs/reports/20260829-hold-challenge-kr.md`
9. `docs/reports/20260829-hold-challenge-us.md`
10. `docs/reports/20260829-sell-zero-bias-audit.md`
11. `docs/reports/20260829-hold-default-audit.md`
12. `docs/reports/20260829-confidence-calibration.md`
13. `docs/reports/20260829-timing-calibration.md`
14. `docs/reports/20260829-valuation-expectation-conflict.md`
15. `docs/reports/20260829-fundamental-technical-conflict.md`
16. `docs/reports/20260829-ohlcv-feature-contribution.md`
17. `docs/reports/20260829-macd-decision-contribution.md`
18. `docs/reports/20260829-cross-market-decision-consistency.md`
19. `docs/reports/20260829-decision-change-condition-quality.md`
20. `docs/reports/20260829-decision-canary-review-recommendation.md`
21. `docs/reports/20260829-decision-quality-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-decision-quality-review.json
docs/reports/20260829-decision-agreement-matrix.json
docs/reports/20260829-decision-canary-review-recommendation.json
```

---

# 33. Required gates

Set exactly:

```text
BASELINE_SUBJECT_COUNT =
20 / OTHER

BASELINE_BUY_COUNT =
2 / OTHER

BASELINE_HOLD_COUNT =
18 / OTHER

BASELINE_SELL_COUNT =
0 / OTHER

INDEPENDENT_REVIEW_LABEL_BLIND =
PASS / PARTIAL / FAIL

INDEPENDENT_REVIEW_COUNT =
20 / OTHER

MATERIAL_DISAGREEMENT_COUNT =
...

ADJUDICATION_COUNT =
...

FINAL_REVIEW_BUY_COUNT =
...

FINAL_REVIEW_HOLD_COUNT =
...

FINAL_REVIEW_SELL_COUNT =
...

FORCED_SELL_FOR_CLASS_BALANCE =
0 / NONZERO

AXIS_STATE_USED_AS_FIXED_SCORE =
0 / NONZERO

MACD_ALONE_OWNS_BUY_SELL =
0 / NONZERO

ORDER_COMMAND_LANGUAGE =
0 / NONZERO

CROSS_MARKET_DECISION_SEMANTICS =
PASS / MATERIAL_INCONSISTENCY / FAIL

HOLD_DEFAULT_BIAS =
NONE / LOW / MATERIAL / FAIL

SELL_SUPPRESSION_BIAS =
NONE / LOW / MATERIAL / FAIL

CONFIDENCE_CALIBRATION =
PASS / NEEDS_REPAIR / FAIL

TIMING_CALIBRATION =
PASS / NEEDS_REPAIR / FAIL

DECISION_CHANGE_CONDITION_QUALITY =
PASS / NEEDS_REPAIR / FAIL

ONE_SIDED_DECISION_COUNT =
0 / NONZERO

PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA =
0 / NONZERO

PRODUCTION_CANARY_ENABLED =
false / true

PRODUCTION_DECISION_MESSAGE_SENT =
0 / NONZERO

DECISION_ENGINE_STATE =
TEST_SINK_READY / OTHER

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

CANARY_RECOMMENDATION =
READY /
READY_WITH_OBSERVATION /
NOT_READY
```

---

# 34. Review PASS rule

Review PASS requires:

```text
20/20 independent review
all material disagreements adjudicated
no forced class balancing
no fixed-score decision ownership
no MACD-alone directional ownership
no order-command wording
confidence calibration acceptable or explicitly repairable
timing calibration acceptable or explicitly repairable
cross-market semantics consistent
SELL=0 explained if it remains
BUY=2 defended or corrected
HOLD=18 defended or corrected
P0 = 0
material P1 = 0
```

This does NOT authorize production canary by itself.

---

# 35. Completion response

Return:

```text
BASE_SHA = ...
FINAL_MAIN = ...
OPERATING = ...

BASELINE_SUBJECT_COUNT = 20
BASELINE_BUY_COUNT = 2
BASELINE_HOLD_COUNT = 18
BASELINE_SELL_COUNT = 0

INDEPENDENT_REVIEW_LABEL_BLIND = ...
INDEPENDENT_REVIEW_COUNT = 20
MATERIAL_DISAGREEMENT_COUNT = ...
ADJUDICATION_COUNT = ...

FINAL_REVIEW_BUY_COUNT = ...
FINAL_REVIEW_HOLD_COUNT = ...
FINAL_REVIEW_SELL_COUNT = ...

DB_INSURANCE_REVIEW =
...

GOOGL_REVIEW =
...

SKHYNIX_REVIEW =
...

SAMSUNG_ELECTRONICS_REVIEW =
...

MU_REVIEW =
...

TSM_REVIEW =
...

SELL_ZERO_BIAS_AUDIT =
...

HOLD_DEFAULT_BIAS =
...

SELL_SUPPRESSION_BIAS =
...

CONFIDENCE_CALIBRATION =
...

TIMING_CALIBRATION =
...

CROSS_MARKET_DECISION_SEMANTICS =
...

MACD_DECISION_CONTRIBUTION =
...

DATA_QUALITY_LIMITED_TICKERS =
...

VALUATION_LIMITED_TICKERS =
...

ONE_SIDED_DECISION_COUNT = 0
MACD_ALONE_OWNS_BUY_SELL = 0
AXIS_STATE_USED_AS_FIXED_SCORE = 0
FORCED_SELL_FOR_CLASS_BALANCE = 0
ORDER_COMMAND_LANGUAGE = 0

PRODUCTION_CANARY_ENABLED = false
PRODUCTION_DECISION_MESSAGE_SENT = 0
DECISION_ENGINE_STATE = TEST_SINK_READY

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

CANARY_RECOMMENDATION =
READY /
READY_WITH_OBSERVATION /
NOT_READY

PROPOSED_CANARY_SET =
...

NEXT_ACTION =
REVIEW_OPERATOR_TABLE /
PREPARE_BOUNDED_CANARY_INSTRUCTION /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 36. Mandatory completion ZIP

Create:

`20260829-cross-market-ai-decision-quality-review-before-canary-bundle.zip`

Include:

```text
exact instruction
20-stock baseline
independent review
agreement matrix
adjudications
BUY deep dives
HOLD challenge reviews
SELL=0 bias audit
HOLD-default audit
confidence/timing calibration
valuation-expectation conflict
fundamental-technical conflict
OHLCV/MACD contribution
cross-market consistency
canary recommendation
machine-readable JSON
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

# 37. Final principle

Before production canary, challenge the engine as if its current decisions are wrong.

The goal is not to preserve:

```text
BUY 2 / HOLD 18 / SELL 0
```

and not to force a more balanced distribution.

The goal is to determine whether each label is the best evidence-grounded analytical classification
for that stock, at that horizon, with that data quality.

Only after the 20 decisions survive this challenge review should a bounded production canary be considered.
