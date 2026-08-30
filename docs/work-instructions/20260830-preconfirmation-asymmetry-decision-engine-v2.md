# thesis-monitor — Pre-Confirmation Asymmetry Decision Engine v2
## Allow BUY before full proof when uncertainty is already cheaply priced
## Prevent "wait for confirmation → price already rerated" bias
## Preserve AI autonomy: no fixed score / no mandatory confirmation checklist
## Shadow-v2 only in this task; current production canary remains unchanged

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-30 KST`
- Workstream: `PRECONFIRMATION_ASYMMETRY_DECISION_ENGINE_V2`
- Task class: `DECISION_REASONING_EXTENSION + SHADOW_V2 + MIGRATION_READINESS`
- Current production Decision Engine: preserve existing bounded canary behavior
- v2 production exposure in this task: `0`
- Automated trading: `0`
- Order sizing: `0`
- Thesis/monitoring mutation from v2 shadow: `0`
- Price-rule mutation: `0`
- Production Telegram send from v2: `0`
- Natural canary counters: do not increment from v2 tests

Latest source bundle:

`thesis-monitor-cleanup-20260830.zip`

Source-supported cleanup result:

```text
MASTER_INSTRUCTION_COMMIT =
506a0178b5cbd33fbc3c2fdc5a0d81cd7672a920

BASE_SHA =
08c1d29b292fb575f92e56f47a9b6e041339eb6a

IMPLEMENTATION_SHA =
d44b624200791bef69b56a60c74b7388d91d0346

FINAL_MAIN / ORIGIN_MAIN / OPERATING =
1359a5769c36d64dd5e0acc9bbf03f90578fb062

Decision Engine state =
CANARY

Production canary enabled =
true

Canary scope =
KR: 003690, 000660
US: GOOGL, RXRX

Current accepted decisions =
003690 HOLD
000660 HOLD
GOOGL HOLD
RXRX SELL

Natural canary cycles in supplied bundle =
KR 0/2
US 0/2

Open P0 / material P1 =
0 / 0
```

Cleanup items already closed:

```text
US SOXX/IWM market-internal relative signals = PASS
US decision Korean localization = PASS
003690 canonical identity = 코리안리
5/5 cleanup test sink = PASS
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve actual latest safe origin/main
resolve actual operating checkout
use 1359a576... or safe linear descendant
read current canary/natural-proof state from runtime
```

---

# 1. Product problem

The current decision engine can become structurally late if it reasons like:

```text
"Wait until the business improvement is fully confirmed.
Then consider BUY."
```

In markets, confirmation itself can cause:

```text
earnings revisions
multiple expansion
expectation repricing
price appreciation
```

so by the time the evidence is fully confirmed, the investment may no longer be attractively priced.

The engine therefore needs to reason about:

```text
what is known
what is not yet known
what the market already prices
what the current price pays for uncertainty
what happens if we wait for confirmation
```

---

# 2. Core principle

BUY does NOT require full confirmation.

A pre-confirmation BUY may be valid when:

```text
evidence is still EARLY/PARTIAL,
but the current price/expectations already discount substantial uncertainty,
the observed evidence is directionally supportive,
and upside/downside asymmetry is favorable enough.
```

Conversely:

```text
evidence may be CONFIRMED,
but if price/expectations already require an optimistic outcome,
the correct decision may be HOLD or SELL.
```

This is not a deterministic rule.

It is a reasoning contract.

---

# 3. AI autonomy

Do NOT implement:

```text
EARLY + LOW expectations + cheap valuation = BUY
```

or any weighted score.

The structured fields introduced in this task are inputs to very-high-reasoning AI.

The AI remains free to conclude:

```text
BUY
HOLD
SELL
```

after weighing all evidence.

Hard:

```text
PRECONFIRMATION_DECISION_FROM_FIXED_RULE = 0
FINAL_DECISION_FROM_FIXED_WEIGHT_SUM = 0
```

---

# 4. Hard factual safety vs business uncertainty

Keep these as fail-closed factual safety issues:

```text
security basis conflict
ADR/share basis conflict
currency conflict
unverified denominator
malformed OHLCV
future-data leakage
numeric provenance failure
```

These are NOT "uncertainty the AI can price."

But these are legitimate investment uncertainties the AI may price:

```text
new product monetization not fully proven
margin improvement early-stage
cycle recovery partially visible
AI demand durability uncertain
new customer ramp not complete
capital return not fully demonstrated
```

Do not conflate the two.

---

# 5. Work split

```text
Track A
Evidence maturity + market pricing / expectation interpretation

Track B
Bear/Base/Bull scenario asymmetry + confirmation-cost reasoning

Track C
Integrate pre-confirmation BUY / post-confirmation HOLD reasoning

Track D
20-stock shadow-v2 blind replay + historical diagnostic + test sink + migration readiness
```

Recommended branches:

```text
codex/evidence-maturity-pricing-v2
codex/scenario-asymmetry-confirmation-cost
codex/preconfirmation-buy-reasoning
codex/decision-v2-shadow-replay
```

---

# 6. Track A — evidence maturity

Create a structured AI interpretation for each major investment-logic driver.

Allowed maturity enum:

```text
EARLY
PARTIAL
CONFIRMED
MIXED
UNKNOWN
```

Definitions:

## EARLY

```text
credible initial evidence exists,
but repeatability / economic conversion is not yet established.
```

## PARTIAL

```text
multiple supporting observations exist,
but one or more economically important links remain unproven.
```

## CONFIRMED

```text
the relevant economic mechanism has been demonstrated with sufficiently repeatable evidence
for the stated decision horizon.
```

## MIXED

```text
different parts of the investment logic are at materially different maturity levels
or supporting/contradicting evidence coexists.
```

## UNKNOWN

```text
evidence quality/availability is insufficient to classify maturity.
```

---

# 7. Maturity is per driver first

Do not reduce a company immediately to one global maturity label.

For each core investment-logic driver:

```text
driver
maturity
supporting evidence refs
contradicting evidence refs
what remains unproven
as_of
```

Then AI may create an overall summary.

Example:

```text
Search monetization = CONFIRMED
Cloud AI monetization = PARTIAL
AI CAPEX cash-return conversion = EARLY
overall = MIXED
```

---

# 8. Evidence maturity is not confidence

Separate:

```text
evidence maturity
```

from:

```text
decision confidence
```

A company can have:

```text
PARTIAL maturity
+
MEDIUM confidence BUY
```

if the price asymmetry is highly favorable.

A company can also have:

```text
CONFIRMED maturity
+
HIGH confidence HOLD
```

if current valuation is already demanding.

Hard:

```text
MATURITY_HARD_MAPS_TO_CONFIDENCE = 0
MATURITY_HARD_MAPS_TO_DECISION = 0
```

---

# 9. Existing market expectations remain canonical

Preserve the current market-expectation enum:

```text
depressed
low
balanced
elevated
very_high
speculative
unknown
```

Do not replace it.

This remains one of the core inputs.

---

# 10. New pricing-requirement interpretation

Add a separate AI interpretation:

```text
PRICING_REQUIREMENT =
CONSERVATIVE_OUTCOME_SUFFICIENT
BASE_CASE_REQUIRED
OPTIMISTIC_CASE_REQUIRED
BULL_CASE_REQUIRED
UNKNOWN
```

Meaning:

## CONSERVATIVE_OUTCOME_SUFFICIENT

Current valuation/price can be justified without requiring a strong operating outcome.

## BASE_CASE_REQUIRED

Current price broadly requires the base operating thesis.

## OPTIMISTIC_CASE_REQUIRED

A meaningfully above-base outcome is needed to justify current pricing.

## BULL_CASE_REQUIRED

Current pricing appears to require a strong bullish scenario.

## UNKNOWN

Evidence/valuation basis is insufficient.

This is an AI interpretation grounded in:

```text
valuation
historical multiples
earnings/FCF trajectory
expectations
scenario assumptions
```

It is not a backend fact.

---

# 11. Pricing requirement must expose its evidence

For every pricing-requirement conclusion:

```text
pricing_requirement
supporting refs
valuation basis
expectation refs
key assumption
unknowns
```

No unsupported fair-value target.

Hard:

```text
PRICING_REQUIREMENT_WITHOUT_EVIDENCE = 0
```

---

# 12. "Cheap" does not equal favorable asymmetry

The engine must not infer:

```text
low PER/PBR → favorable asymmetry
```

without checking:

```text
business quality
cycle position
earnings sustainability
capital intensity
dilution
balance-sheet risk
expectations
```

This is especially important for:

```text
cyclicals
financials
biotech
high-capex infrastructure
```

---

# 13. Track B — scenario reasoning

For each stock create structured scenario interpretations:

```text
BEAR
BASE
BULL
```

No target price is required.

Each scenario should include:

```text
business assumptions
earnings/margin/FCF assumptions
expectation implications
valuation implications
macro/market conditions where relevant
key evidence refs
```

Do not invent precise numeric forecasts if the backend does not own them.

---

# 14. Scenario requirements

## BEAR

Must describe:

```text
what can go wrong
which current warning signs support it
what economic impairment would result
```

## BASE

Must describe:

```text
what current evidence most reasonably supports
without requiring optimistic extrapolation
```

## BULL

Must describe:

```text
what must go right beyond the base case
and which evidence suggests that possibility is credible
```

---

# 15. No scenario target-price invention

Do not create arbitrary:

```text
Bear target $X
Base target $Y
Bull target $Z
```

unless canonical backend valuation ranges already exist and pass security/currency/basis gates.

Hard:

```text
AI_INVENTED_SCENARIO_TARGET_PRICE = 0
```

---

# 16. Asymmetry interpretation

Add:

```text
ASYMMETRY =
FAVORABLE
BALANCED
UNFAVORABLE
UNKNOWN
```

This is an AI interpretation, not a deterministic score.

The AI should consider:

```text
current price / valuation
market expectations
evidence maturity
bear/base/bull scenario requirements
business quality
downside permanence
dilution/funding risk
technical/market timing as secondary context
```

---

# 17. FAVORABLE asymmetry

Conceptually:

```text
the base or even conservative outcome can support acceptable value,
while credible upside is not fully priced,
and downside is sufficiently compensated.
```

This can occur BEFORE full confirmation.

---

# 18. UNFAVORABLE asymmetry

Conceptually:

```text
current price requires optimistic/bull execution,
while downside from disappointment is material
or the valuation/expectation burden leaves little margin for error.
```

This can occur AFTER full confirmation.

---

# 19. Confirmation-cost interpretation

Add:

```text
CONFIRMATION_COST =
LOW
MEDIUM
HIGH
UNKNOWN
```

Meaning:

```text
How much investment opportunity may disappear if we wait for full confirmation?
```

Factors may include:

```text
earnings revision sensitivity
operating leverage
cycle inflection
scarce supply / capacity constraints
rapid rerating potential
catalyst proximity
market skepticism
current valuation discount
```

This is AI reasoning, not a price forecast.

---

# 20. HIGH confirmation cost

Conceptually:

```text
the evidence may become more reliable only after a catalyst that is also likely to reprice the stock materially.
```

Examples:

```text
new product revenue proof
margin inflection
cycle recovery confirmation
contract announcement
regulatory de-risking
```

Do not assume every catalyst causes price appreciation.

---

# 21. Error-cost interpretation

Add:

```text
PRECONFIRMATION_ERROR_COST =
LOW
MEDIUM
HIGH
UNKNOWN
```

Question:

```text
If the early thesis is wrong, how damaging is the downside?
```

Consider:

```text
balance sheet
cash burn
dilution
cyclicality
valuation
permanent capital loss risk
business durability
```

This helps distinguish:

```text
early BUY in high-quality discounted franchise
```

from:

```text
early BUY in fragile speculative story
```

---

# 22. Confirmation cost vs error cost

The AI may reason:

```text
HIGH confirmation cost
+
LOW/MEDIUM error cost
+
FAVORABLE asymmetry
→ pre-confirmation BUY may be attractive
```

But this is NOT a rule.

Likewise:

```text
HIGH confirmation cost
+
HIGH error cost
→ HOLD may still be appropriate
```

No fixed mapping.

---

# 23. Track C — pre-confirmation BUY contract

Introduce explicit product support for:

```text
PRE_CONFIRMATION_BUY = true/false
```

This is a decision explanation flag, not a separate top-level decision.

Use only when:

```text
decision = BUY
and
one or more decisive drivers are EARLY/PARTIAL
```

The message should explain why waiting for full confirmation is not required.

---

# 24. Pre-confirmation BUY explanation

Required elements:

```text
what is not yet confirmed
why current evidence is still directionally credible
what the market appears to price
why current asymmetry is favorable
what could prove the thesis wrong
what would cause BUY → HOLD/SELL
```

No "buy before everyone else" promotional language.

---

# 25. Example semantic shape

Conceptual only:

```text
AI 종합 판단: BUY
추론등급: 매우 높음
판단 확신도: 중간
증거 성숙도: PARTIAL
가격 비대칭: FAVORABLE

판단:
핵심 성장 논리는 아직 완전히 증명되지 않았지만,
현재 시장 기대와 valuation이 상당한 불확실성을 반영하고 있으며
현재까지의 증거는 같은 방향으로 진행되고 있다.

완전 확인을 기다리면 해당 개선이 이익 추정과 가격에 동시에 반영될 가능성이 있어,
현재 위험/보상은 확인 이후보다 더 유리할 수 있다.
```

Do not hard-code this prose.

---

# 26. Post-confirmation HOLD contract

Explicitly support:

```text
evidence maturity = CONFIRMED
decision = HOLD
```

when:

```text
market expectations / valuation have rerated enough
that current asymmetry is no longer favorable.
```

The message should say:

```text
business proof improved
but price also repriced
```

rather than implying the business thesis weakened.

---

# 27. Confirmed business can still be SELL

Also allow:

```text
CONFIRMED business quality
+
BULL_CASE_REQUIRED pricing
+
UNFAVORABLE asymmetry
→ SELL may be possible
```

if downside evidence dominates.

Do not make high-quality business a permanent HOLD floor.

---

# 28. Decision reasoning order v2

Update reasoning sequence:

```text
1. hard factual/data safety
2. business quality / investment logic
3. evidence maturity by driver
4. earnings trajectory / quality
5. market expectations
6. valuation
7. pricing requirement
8. bear/base/bull scenarios
9. asymmetry
10. confirmation cost
11. pre-confirmation error cost
12. macro / market / sector
13. positioning
14. Price Structure
15. OHLCV momentum / timing
16. opposing evidence / unknowns
17. BUY / HOLD / SELL
18. confidence
19. timing
20. decision-change conditions
```

---

# 29. Fundamentals still dominate long-horizon decision

Do not let:

```text
MACD
RSI
short-term market flow
night futures
```

alone determine:

```text
evidence maturity
pricing requirement
asymmetry
long-horizon BUY/HOLD/SELL
```

They remain context/timing unless economically linked.

Hard:

```text
TECHNICAL_FEATURE_OWNS_ASYMMETRY = 0
```

---

# 30. Market expectation vs confirmation timing

The engine must explicitly ask:

```text
Did the stock reprice BEFORE the evidence matured?
```

and:

```text
Did earnings/FCF/ROIC estimates improve faster than the stock price?
```

Where safe canonical estimates exist, backend-derived comparisons may be provided.

Do not calculate forward estimate changes from unsupported numbers.

---

# 31. Price increased ≠ valuation worsened

The reasoning must distinguish:

```text
price +20%
earnings/FCF value estimate +40%
```

from:

```text
price +40%
earnings estimate +10%
```

The first may preserve/improve asymmetry.

The second may compress it.

Do not infer from price return alone.

---

# 32. Existing decision-change conditions audit

Challenge conditions that currently imply:

```text
"Wait until X is confirmed, then BUY."
```

For every HOLD, ask:

```text
If X is confirmed, is it likely price/expectations also reprice?
Would the current uncertainty already justify BUY at lower confidence?
```

Do not automatically change HOLD.

Record the answer.

---

# 33. 003690 / GOOGL mandatory challenge controls

These two were previously BUY then recalibrated to HOLD.

Use them as mandatory v2 challenge cases.

## 003690 코리안리

Ask:

```text
Is sustainable underwriting/ROE proof truly required before BUY,
or does current book-value discount already compensate for partial proof?
What is the confirmation cost if improved underwriting becomes obvious only after rerating?
What is the error cost if improvement fails?
```

Do not force BUY.

## GOOGL

Ask:

```text
Is AI CAPEX→FCF conversion confirmation truly required before BUY,
or do Search/Cloud durability + current valuation already provide favorable asymmetry?
How much AI monetization is already priced?
Could confirmation itself cause earnings/multiple rerating?
```

Do not force BUY.

---

# 34. Other mandatory controls

At minimum challenge:

```text
000660
005930
012450
MU
TSM
TSLA
RXRX
WULF
CRCL
SNDK
```

Why:

```text
strong businesses/high expectations
partial proof
speculative optionality
valuation burden
data limitations
```

---

# 35. Data-limited HOLD remains valid

If factual valuation/security basis is not safe:

the AI cannot "price uncertainty" using invalid numbers.

It may still reason qualitatively where supported,
but confidence must reflect the limitation.

Do not use pre-confirmation logic to bypass factual safety gates.

Hard:

```text
PRECONFIRMATION_LOGIC_BYPASSES_DATA_SAFETY = 0
```

---

# 36. Decision confidence under pre-confirmation BUY

A pre-confirmation BUY will often have:

```text
MEDIUM
or
LOW
```

confidence.

Do not prohibit HIGH if evidence genuinely supports it,
but maturity alone cannot dictate confidence.

No automatic downgrade rule.

---

# 37. User-facing v2 additions

Potential compact fields:

```text
증거 성숙도: PARTIAL
시장 기대: 낮음
가격 비대칭: 유리
확인 대기 비용: 높음
```

Do not show all fields if they make the message dense.

Renderer should select material fields.

At minimum the internal decision packet must contain them.

---

# 38. Message-density policy

Do not turn messages into scenario reports.

The AI may reason over:

```text
maturity
pricing requirement
scenarios
asymmetry
confirmation cost
error cost
```

but user-facing output should usually surface only:

```text
1–2 decisive v2 concepts
```

unless the decision is otherwise hard to understand.

---

# 39. Polarity and Korean localization

Preserve already-passing cleanup:

```text
BULLISH / BEARISH / NEUTRAL polarity
US Korean decision rendering
003690 = 코리안리
```

Hard:

```text
POLARITY_REGRESSION = 0
US_DECISION_LOCALIZATION_REGRESSION = 0
TICKER_003690_IDENTITY = 코리안리
```

---

# 40. Current production canary isolation

This task must NOT change current production canary decisions or message logic.

Keep current v1 canary operational as-is:

```text
KR: 003690, 000660
US: GOOGL, RXRX
```

V2 runs in parallel SHADOW only.

Hard:

```text
V2_PRODUCTION_DECISION_BLOCK_VISIBLE = 0
V2_MUTATED_CANARY_STATE = 0
```

---

# 41. Track D — current 20-stock shadow-v2 replay

Use the actual current monitored universe.

Expected reference count:

```text
20
```

but use runtime truth.

For every stock produce:

```text
v1 current decision
v2 shadow decision
decision agreement
evidence maturity by driver
overall maturity summary
market expectation
pricing requirement
bear/base/bull scenario summary
asymmetry
confirmation cost
preconfirmation error cost
preconfirmation_buy flag
confidence
timing
decisive reason
what changes decision
```

---

# 42. Blind v2 review

Preferred:

```text
v2 reasoning does not see the v1 BUY/HOLD/SELL label on first pass.
```

After v2 decision:

compare against v1.

Material disagreement requires adjudication.

Do not mechanically preserve v1.

Do not mechanically favor v2.

---

# 43. Adjudication questions

For each disagreement:

```text
Did v1 over-require confirmation?
Did v2 underweight execution risk?
Did v1 ignore confirmation cost?
Did v2 overstate favorable asymmetry?
Did either side misuse valuation/expectations?
Did data quality make the comparison unsafe?
```

---

# 44. Expected decision distribution is unconstrained

Do not target:

```text
more BUY
fewer HOLD
more balanced BUY/HOLD/SELL
```

If v2 still produces 0 BUY:

that may be correct.

If v2 produces multiple BUY:

each must be independently defended.

Hard:

```text
FORCED_PRECONFIRMATION_BUY_COUNT = 0
```

---

# 45. Historical diagnostic replay

Use existing no-lookahead temporal replay where safe.

Add a diagnostic question:

```text
At historical checkpoints where evidence was EARLY/PARTIAL,
did waiting for later confirmation coincide with substantial repricing?
```

This is retrospective diagnostics only.

Do not present as validated alpha.

No future data enters the historical decision packet.

Hard:

```text
HISTORICAL_REPLAY_LOOKAHEAD_LEAK = 0
PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA = 0
```

---

# 46. Confirmation-delay diagnostic

Where safe historical outcome data exists, measure separately:

```text
price change from early/partial checkpoint
to later confirmation checkpoint

earnings/FCF/ROIC estimate changes over same period
expectation/valuation rerating over same period
```

Only use canonical historical values.

If unavailable:

mark `NOT_AVAILABLE`.

Do not reconstruct unsupported estimates.

---

# 47. Test sink

After 20-stock v2 shadow validation:

send v2 decision-enabled messages to dedicated non-production test sink only.

Do NOT overwrite the current production canary.

Use a clear label such as:

```text
🧪 SHADOW V2 · 비대칭/증거성숙도 검증
```

No production recipient.

---

# 48. Test-sink quality

Verify:

```text
v2 decision understandable
pre-confirmation BUY explanation if present
post-confirmation HOLD explanation if present
no target-price invention
no fixed-score language
no order command
no numeric provenance violation
message density acceptable
```

Hard:

```text
V2_TEST_MESSAGE_QUALITY = PASS
```

---

# 49. Decision migration readiness

At task end output:

```text
V2_MIGRATION_RECOMMENDATION =
READY_FOR_BOUNDED_CANARY_MIGRATION
READY_WITH_OBSERVATION
NOT_READY
```

Do NOT migrate production in this task.

---

# 50. V2 migration PASS criteria

Require:

```text
20/current-universe v2 shadow PASS
all material disagreements adjudicated
no factual-safety bypass
no fixed-rule decision
no target-price invention
polarity/localization preserved
historical no-lookahead preserved
test-sink PASS
P0 = 0
material P1 = 0
```

---

# 51. Required architecture docs

Create/update:

```text
docs/architecture/EVIDENCE_MATURITY_MODEL.md
docs/architecture/PRICING_REQUIREMENT_AND_ASYMMETRY.md
docs/architecture/PRECONFIRMATION_BUY_REASONING.md
docs/architecture/DECISION_ENGINE_V2_SHADOW_MIGRATION.md
```

---

# 52. Required reports

Create at minimum:

1. `docs/reports/20260830-preconfirmation-v2-scope.md`
2. `docs/reports/20260830-evidence-maturity-contract.md`
3. `docs/reports/20260830-pricing-requirement-contract.md`
4. `docs/reports/20260830-scenario-asymmetry-contract.md`
5. `docs/reports/20260830-confirmation-cost-contract.md`
6. `docs/reports/20260830-preconfirmation-error-cost-contract.md`
7. `docs/reports/20260830-preconfirmation-buy-contract.md`
8. `docs/reports/20260830-postconfirmation-hold-contract.md`
9. `docs/reports/20260830-003690-preconfirmation-challenge.md`
10. `docs/reports/20260830-googl-preconfirmation-challenge.md`
11. `docs/reports/20260830-semiconductor-preconfirmation-controls.md`
12. `docs/reports/20260830-speculative-optionality-controls.md`
13. `docs/reports/20260830-current-20-v2-shadow-decisions.md`
14. `docs/reports/20260830-v1-v2-decision-agreement.md`
15. `docs/reports/20260830-v2-material-disagreement-adjudication.md`
16. `docs/reports/20260830-confirmation-delay-historical-diagnostic.md`
17. `docs/reports/20260830-v2-test-sink.md`
18. `docs/reports/20260830-v2-message-quality.md`
19. `docs/reports/20260830-v2-migration-readiness.md`
20. `docs/reports/20260830-v2-artifact-index.md`

Machine-readable:

```text
docs/reports/20260830-current-20-v2-shadow-decisions.json
docs/reports/20260830-v1-v2-decision-agreement.json
docs/reports/20260830-v2-migration-readiness.json
```

---

# 53. Required gates

Set exactly:

```text
PRECONFIRMATION_DECISION_FROM_FIXED_RULE =
0 / NONZERO

FINAL_DECISION_FROM_FIXED_WEIGHT_SUM =
0 / NONZERO

MATURITY_HARD_MAPS_TO_CONFIDENCE =
0 / NONZERO

MATURITY_HARD_MAPS_TO_DECISION =
0 / NONZERO

PRICING_REQUIREMENT_WITHOUT_EVIDENCE =
0 / NONZERO

AI_INVENTED_SCENARIO_TARGET_PRICE =
0 / NONZERO

TECHNICAL_FEATURE_OWNS_ASYMMETRY =
0 / NONZERO

PRECONFIRMATION_LOGIC_BYPASSES_DATA_SAFETY =
0 / NONZERO

FORCED_PRECONFIRMATION_BUY_COUNT =
0 / NONZERO

HISTORICAL_REPLAY_LOOKAHEAD_LEAK =
0 / NONZERO

PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA =
0 / NONZERO

POLARITY_REGRESSION =
0 / NONZERO

US_DECISION_LOCALIZATION_REGRESSION =
0 / NONZERO

TICKER_003690_IDENTITY =
코리안리 / OTHER

V2_PRODUCTION_DECISION_BLOCK_VISIBLE =
0 / NONZERO

V2_MUTATED_CANARY_STATE =
0 / NONZERO

V2_SHADOW_SUBJECT_COUNT =
...

V2_BUY_COUNT =
...

V2_HOLD_COUNT =
...

V2_SELL_COUNT =
...

V1_V2_MATERIAL_DISAGREEMENT_COUNT =
...

V2_ADJUDICATION_COUNT =
...

PRECONFIRMATION_BUY_COUNT =
...

POSTCONFIRMATION_HOLD_COUNT =
...

V2_TEST_MESSAGE_COUNT =
...

V2_TEST_MESSAGE_QUALITY =
PASS / FAIL

V2_TEST_EXACT_PAYLOAD =
PASS / FAIL

V2_TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

CURRENT_V1_DECISION_ENGINE_STATE =
CANARY / OTHER

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

V2_MIGRATION_RECOMMENDATION =
READY_FOR_BOUNDED_CANARY_MIGRATION /
READY_WITH_OBSERVATION /
NOT_READY
```

---

# 54. Completion response

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

CURRENT_V1_DECISION_ENGINE_STATE = CANARY

V2_SHADOW_SUBJECT_COUNT = ...

V2_BUY_COUNT = ...
V2_HOLD_COUNT = ...
V2_SELL_COUNT = ...

PRECONFIRMATION_BUY_COUNT = ...
POSTCONFIRMATION_HOLD_COUNT = ...

V2_003690 =
decision ...
maturity ...
pricing_requirement ...
asymmetry ...
confirmation_cost ...
error_cost ...
preconfirmation_buy ...
decisive_reason ...

V2_GOOGL =
decision ...
maturity ...
pricing_requirement ...
asymmetry ...
confirmation_cost ...
error_cost ...
preconfirmation_buy ...
decisive_reason ...

V1_V2_MATERIAL_DISAGREEMENT_COUNT = ...
V2_ADJUDICATION_COUNT = ...

V2_DECISIONS =
...

PRECONFIRMATION_DECISION_FROM_FIXED_RULE = 0
FINAL_DECISION_FROM_FIXED_WEIGHT_SUM = 0
MATURITY_HARD_MAPS_TO_DECISION = 0
AI_INVENTED_SCENARIO_TARGET_PRICE = 0
PRECONFIRMATION_LOGIC_BYPASSES_DATA_SAFETY = 0
FORCED_PRECONFIRMATION_BUY_COUNT = 0

HISTORICAL_REPLAY_LOOKAHEAD_LEAK = 0
PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA = 0

POLARITY_REGRESSION = 0
US_DECISION_LOCALIZATION_REGRESSION = 0
TICKER_003690_IDENTITY = 코리안리

V2_PRODUCTION_DECISION_BLOCK_VISIBLE = 0
V2_MUTATED_CANARY_STATE = 0

V2_TEST_MESSAGE_COUNT = ...
V2_TEST_MESSAGE_QUALITY = ...
V2_TEST_EXACT_PAYLOAD = ...
V2_TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

V2_MIGRATION_RECOMMENDATION =
READY_FOR_BOUNDED_CANARY_MIGRATION /
READY_WITH_OBSERVATION /
NOT_READY

NEXT_ACTION =
REVIEW_V2_SHADOW_DECISIONS /
PREPARE_V2_BOUNDED_MIGRATION /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 55. Mandatory completion ZIP

Create:

`20260830-preconfirmation-asymmetry-decision-engine-v2-bundle.zip`

Include:

```text
exact master instruction
all track instructions
evidence-maturity contract
pricing-requirement contract
scenario/asymmetry contract
confirmation-cost/error-cost contract
pre-confirmation BUY contract
post-confirmation HOLD contract
003690 challenge
GOOGL challenge
20-stock/current-universe v2 shadow decisions
v1-v2 agreement
adjudications
historical confirmation-delay diagnostic
v2 test-sink exact messages
message-quality review
migration readiness
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

# 56. Final principle

The engine should not wait for certainty if the market already pays the investor to bear uncertainty.

And it should not reward a company merely because the thesis is fully confirmed if the price already requires the bull case.

The AI remains autonomous.

The new structure exists to make it ask the right economic question:

```text
"How much uncertainty remains,
how much of it is already priced,
and is the current asymmetry attractive before the market gets full confirmation?"
```
