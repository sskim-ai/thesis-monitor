# thesis-monitor — Directional Core / Price-Timing Ownership Separation + Fresh Issuer Holdout
## Authorized architecture repair after clean fundamental enrichment
## Company direction is owned by non-price investment evidence
## OHLCV / technical / supply evidence owns timing, entry and price-review context
## Preserve all validated technical indicators actually emitted by the OHLCV stack
## No fixed factor weights
## No ticker-specific repair
## New issuer-level holdout after architecture freeze
## FIRST → A → B → C on one immutable source lock
## No production activation

---

# 0. Immutable source result

Source report bundle:

```text
thesis-monitor-20260906-official-fundamental-enrichment-source-sufficiency-new-holdout-report(2).zip
```

SHA-256:

```text
05e3f65245d069e761f46147be6a363b3994f665d1a14d92d811d4ef74f9977b
```

Source implementation freeze:

```text
commit:
25906030070830327401ae7bc77aefb0910b6b58

tree:
05d1e5f82ad6239628e238aee5824e3835c3c1be
```

Source generation:

```text
20260906-fundamental-holdout-20260906T065029Z-a6b43b8a61c4
```

Source lock:

```text
bc307daaf43bf5ee561e1b8a927357e91535613e101687e8872d99d030e55832
```

Observed source result:

```text
prior unseen16 enrichment fixtures:
16/16 SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT

candidate coverage:
64 attempted
55 sufficient
6 limited
3 insufficient

new issuer holdout:
16
KR 8 / US 8

FIRST = 16/16
A     = 16/16
B     = 16/16
C     = 16/16

source sufficiency escape = 0
price-only directional model calls = 0
hard-safety regression = 0
decision-engine hash drift = 0
same-generation repair = 0
```

Stability:

```text
STABLE = 7
BOUNDARY_UNCERTAINTY = 8
UNSTABLE = 1

unstable subject:
PLTR

PLTR:
HOLD throughout
BUY:SELL 5.5:4.5
→ 4.5:5.5
→ 5:5

reason:
BUY_LEAN_SELL_LEAN_FLIP
```

Fundamental-vs-price audit:

```text
NKE:
decision = SELL
dominant classification = PRICE_TIMING
dominant evidence =
weekly chart
monthly chart
chart structure state

price_only_buy_sell_review_flag = true
```

Final source verdict:

```text
GENERALIZATION_NEEDS_ARCHITECTURE_WORK

blocking observations:
PLTR_BUY_LEAN_SELL_LEAN_FLIP
NKE_PRICE_ONLY_DOMINATED_SELL_REVIEW_FLAG
```

This task addresses those findings generically.

It MUST NOT contain PLTR- or NKE-specific decision logic.

---

# 1. Core architectural principle

Separate:

```text
WHAT THE COMPANY IS WORTH / DIRECTION
```

from:

```text
WHEN PRICE / POSITIONING IS FAVORABLE
```

Target architecture:

```text
validated fundamental packet
        ↓
DIRECTIONAL CORE
        ↓
overall BUY / HOLD / SELL
BUY:SELL balance
HOLD lean
fundamental new-buyer stance
fundamental holder stance
business invalidation
        ↓
----------------------------------
        ↓
validated OHLCV / technical / supply packet
        ↓
PRICE-TIMING OVERLAY
        ↓
technical state
entry mode
timing downgrade / caution
price review
holder price-review pressure
        ↓
----------------------------------
        ↓
DETERMINISTIC COMPOSER
        ↓
final structured decision
        ↓
existing V2 renderer
```

The price-timing layer may constrain execution.

It may not own business direction.

---

# 2. Do NOT implement fixed factor weights

Forbidden:

```text
fundamentals = 60%
valuation = 20%
technical = 20%
```

Forbidden:

```text
RSI score + MACD score + FCF score = total score
```

The repair is evidence ownership, not weighted scoring.

AI remains responsible for substantive interpretation inside its permitted evidence domain.

Deterministic code owns:
- domain fencing
- allowed state transitions
- field ownership
- provenance
- lifecycle constraints

---

# 3. Source enrichment and sufficiency are frozen

The successful cold-start fundamental enrichment path is NOT the repair target.

Expected source-enrichment hashes:

```text
coldstart_assembler =
ce6bd772ad105cd2425570607806ae1ec8afa109eca94fd4c6b2e08c4b306780

company_profile =
fd4854c7781d672bf414ea43341e21ceb1879436c97defc5dff153037bdbbf5f

financial_lineage =
1a9ba3fa0d867f4d0c1fb2c5e1b034d9adeebbe32b22b0d796571d468922ff91

fundamental_enrichment =
c18627e3dd3a9a124b08583466de4361e1c5246be7ed6d2aadb306c770ed7538

opendart_recovery =
c3190d3db087ca474a9cdf250570ba36c4fd82554439b60a6ac31354cfec19b0

orchestrator =
2599d049400eab81fdf54336807bd37912496836504d1722c636cad70710afbe

provider_sector_map =
e0c1ca2c52809484594b88e1dd904fd0a985c9db76d8524c21134ab8850d99bf

provider_symbol_registry =
6cc8d7f38545a3abbe2fa882ef187ff7200d71a914d8b63e521a3917b6e226a6

sec_financial_normalizer =
9fa2d3c12c75adf0872010a84ef749b8a4c6449d244ee4f35bb042ded7874136
```

Required:

```text
FUNDAMENTAL_SOURCE_ENRICHMENT_DRIFT = 0
SOURCE_SUFFICIENCY_POLICY_DRIFT = 0
```

The source-sufficiency contract remains:

```text
identity/security required
issuer fundamental anchor required
framework-appropriate second anchor required
current quality required
price direction prohibited
valuation optional
```

---

# 4. Existing decision semantics to preserve

Current threshold semantics remain unchanged:

```text
BUY:
BUY score >= 6.0

SELL:
SELL score >= 6.0

otherwise:
HOLD

BUY:SELL sum = 10
increment = 0.5

HOLD lean:
5.5:4.5 = BUY_LEAN
5:5     = NEUTRAL
4.5:5.5 = SELL_LEAN
```

Do not change these thresholds.

Existing user-facing enums remain unless an additive internal field is required:

```text
new buyer:
ATTRACTIVE / WAIT / AVOID

entry:
PULLBACK / CONFIRMATION / BOTH / NONE

holder:
HOLDABLE / REVIEW / REDUCE
```

---

# 5. Authorized decision-layer mutation surface

Unlike the previous task, this is an authorized architecture repair.

Allowed changes are limited to:

```text
evidence-domain contract
directional-core prompt/schema
price-timing prompt/schema
input fencing
ownership validator
deterministic composer
stability audit
dominance audit
```

Preserve unless strictly necessary for additive compatibility:

```text
investment thresholds
numeric provenance
accounting attribution
security / ADR basis
evidence identity
logical-condition ownership
future-checkpoint ownership
Structured Actionability semantics
primary renderer wording ownership
hard actionable-language safety
```

Any unrelated decision change is a STOP condition.

---

# 6. Evidence-domain contract

Every evidence object used by the architecture must have a source-owned machine-readable domain.

Minimum conceptual domains:

## Directional-core eligible

```text
BUSINESS_CURRENT
EARNINGS_FINANCIAL_CURRENT
LIQUIDITY_CASHFLOW_CURRENT
SECTOR_OPERATING_CURRENT
REGULATORY_CAPITAL_CURRENT
CLINICAL_REGULATORY_CURRENT
CAPITAL_ALLOCATION_CURRENT
VALUATION_SAFE
MARKET_EXPECTATIONS
STRUCTURAL_RISK
MACRO_TRANSMISSION
```

## Price-timing only

```text
PRICE_CONTEXT
OHLCV_TECHNICAL
SUPPORT_RESISTANCE
VOLUME_LIQUIDITY
TECHNICAL_STATE
RISK_REWARD_PRICE
SUPPLY_POSITIONING
```

Use repository-native names where they already exist.

Do not classify evidence by parsing free-form prose.

---

# 7. Directional Core — hard input isolation

The Directional Core receives ONLY directional-core eligible evidence.

It must NOT receive raw:

```text
daily / weekly / monthly chart state
support / resistance
RSI
MACD
Bollinger
moving-average state
volume signal
technical breakout/breakdown
technical risk/reward
foreign/institution/individual flow
supply score
raw price transition
technical structure state
```

Raw current price is not directional evidence by itself.

A hard-valid `VALUATION_SAFE` fact derived from current price may be used as valuation evidence.

Required:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
```

---

# 8. Directional Core outputs

The Directional Core AI owns:

```text
overall_direction
directional_balance
hold_lean
directional_confidence
core_investment_judgment
buy_drivers
sell_drivers
fundamental_new_buyer_stance
fundamental_holder_stance
business_invalidation_condition
business_reevaluation_up
business_reevaluation_down
```

All directional claims must point to allowed non-price evidence.

The core may use:
- business quality
- earnings
- cash conversion
- capital efficiency
- balance sheet
- sector-operating facts
- official events
- valuation
- market expectations
- structural risks
- actual macro transmission

---

# 9. BUY / SELL material anchor

A BUY or SELL direction must have at least one same-direction material non-price anchor.

Examples:

```text
earnings improvement/deterioration
margin / FCF / ROIC change
business execution
regulatory / clinical result
balance-sheet improvement/deterioration
safe valuation / expectations asymmetry
structural risk activation
```

Macro may modify the conclusion when a real company channel exists.

Macro alone may not be the only issuer-direction anchor.

Price/technical/supply may never satisfy this requirement.

Required:

```text
BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
```

---

# 10. HOLD lean ownership

BUY_LEAN / NEUTRAL / SELL_LEAN belongs to Directional Core.

Price timing may NOT alter it.

This directly addresses same-fundamental-evidence cases where technical interpretation moves:

```text
BUY_LEAN ↔ SELL_LEAN
```

If the Directional Core input is byte-identical, the price-timing stage cannot change:
- balance
- direction
- hold lean

Required:

```text
TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0
```

---

# 11. Price-Timing Overlay — full validated OHLCV context

The price-timing stage should use the full validated technical context ACTUALLY EMITTED by the existing OHLCV/technical stack.

Inventory and preserve available fields such as:

```text
daily / weekly / monthly OHLCV context
window returns / range position where contractually defined
support / resistance zones
moving averages if provider emits them
volume / trading value
RSI if provider emits it
MACD level / signal / histogram / zero-line if provider emits it
Bollinger bands / band position if provider emits it
breakout / breakdown state
price transition
technical structure state
chart risk/reward
volatility / exhaustion context if provider emits it
```

For KR, also use validated supply/positioning where available:

```text
foreign net buy daily / 5d / 20d
institution net buy daily / 5d / 20d
individual net buy daily / 5d / 20d
foreign holding quantity / ratio
provider supply score
supply quality
primary supply signal
supply as-of date
```

Do not assume score ranges.

Do not treat stale supply as today's flow.

---

# 12. Do not invent missing technical indicators

This task does NOT authorize creation of new RSI/MACD/Bollinger formulas merely because the names appear in this work instruction.

Rule:

```text
if existing validated OHLCV/technical provider emits it:
route it to PRICE_TIMING

if it does not emit it:
preserve unavailable / omit
```

Required:

```text
OHLCV_ANALYST_CALCULATION_ALGORITHM_MUTATION = 0
INVENTED_TECHNICAL_INDICATOR = 0
```

If an existing provider already calculates a field but the decision packet drops it, wiring that existing field through is allowed.

---

# 13. Price-Timing Overlay outputs

Price-Timing AI owns only timing/positioning semantics.

Suggested additive internal outputs:

```text
technical_state:
FAVORABLE / NEUTRAL / CAUTION / ADVERSE / UNKNOWN

timing_new_buyer_modifier:
ALLOW / WAIT / AVOID

entry_mode:
PULLBACK / CONFIRMATION / BOTH / NONE

holder_price_review:
NONE / REVIEW

price_review_context
price_confirmation_context
price_support_context
technical_rationale
supply_positioning_rationale
```

Use repository naming conventions if equivalent fields already exist.

Price timing cannot emit:
- BUY/HOLD/SELL
- directional balance
- HOLD lean
- business invalidation
- business strengthening/weakening

---

# 14. Fundamental new-buyer stance vs timing modifier

Direction Core owns a pre-timing stance:

```text
fundamental_new_buyer_stance =
ATTRACTIVE / WAIT / AVOID
```

Price timing may only keep or make the final stance more conservative.

Conceptually:

```text
ATTRACTIVE
→ ATTRACTIVE / WAIT / AVOID

WAIT
→ WAIT / AVOID

AVOID
→ AVOID
```

Technical strength alone cannot upgrade:

```text
WAIT → ATTRACTIVE
AVOID → WAIT
```

If the stock becomes attractive because the price is genuinely cheap, that must enter through validated `VALUATION_SAFE`, not MACD/RSI/support alone.

Required:

```text
PRICE_TIMING_NEW_BUYER_UPGRADE = 0
```

---

# 15. Fundamental holder stance vs price review

Direction Core owns:

```text
fundamental_holder_stance =
HOLDABLE / REVIEW / REDUCE
```

Price timing may:
- keep HOLDABLE
- escalate HOLDABLE to REVIEW
- keep REVIEW
- add price-review context

Price timing may NOT create REDUCE.

Conceptually:

```text
HOLDABLE
→ HOLDABLE / REVIEW

REVIEW
→ REVIEW

REDUCE
→ REDUCE
```

A final REDUCE requires a non-price business/valuation/structural basis from Direction Core.

Required:

```text
PRICE_ONLY_HOLDER_REDUCE = 0
```

---

# 16. Business invalidation vs technical breakdown

Keep two separate concepts:

```text
BUSINESS INVALIDATION
```

and:

```text
PRICE REVIEW / TECHNICAL BREAKDOWN
```

Technical invalidation may trigger:
- REVIEW
- WAIT
- AVOID
- price reassessment

It may not automatically become:
- business invalidation
- thesis invalidation
- REDUCE
- SELL

Business invalidation must be non-price and issuer-specific.

---

# 17. Valuation boundary

`VALUATION_SAFE` belongs to Directional Core.

Examples:
- hard-valid trailing multiple
- comparable forward multiple
- safe historical valuation position
- framework-appropriate valuation state

Do not treat:
- support
- RSI
- Bollinger
- MACD
- chart risk/reward

as valuation.

Missing valuation remains Unknown.

Do not reverse-engineer denominator values.

---

# 18. Market expectations boundary

Market expectations may belong to Directional Core when supported by:
- validated expectation state
- consensus/guidance context
- safe valuation/expectation evidence

Do not infer "high expectations" solely from:
- price momentum
- RSI
- recent rally
- technical breakout

Technical overextension belongs to Price Timing.

---

# 19. Supply / positioning boundary

Supply is:

```text
FLOW / POSITIONING
```

It may affect:
- timing confidence
- price confirmation
- REVIEW pressure
- entry mode

It may not alter:
- business thesis
- earnings estimate
- valuation context
- directional core
- business invalidation

Required:

```text
SUPPLY_DIRECTIONAL_CORE_USAGE = 0
```

---

# 20. Two-stage execution isolation

Preferred architecture:

```text
Stage 1:
Directional Core call
input = non-price evidence only

Stage 2:
Price-Timing call
input =
frozen Directional Core structured result
+
technical/supply evidence only
```

Stage 2 does not receive permission to recompute core direction.

A single model call is acceptable ONLY if equivalent hard input fencing is proven.

Report which architecture is used:

```text
OWNERSHIP_EXECUTION_MODE =
TWO_STAGE_FENCED /
EQUIVALENT_HARD_FENCED_SINGLE_STAGE
```

Two-stage fenced is preferred.

---

# 21. Deterministic composer

The composer owns mechanical combination only.

It must:
- copy overall direction from Direction Core
- copy balance from Direction Core
- copy HOLD lean from Direction Core
- apply only conservative new-buyer timing downgrade
- apply only holder REVIEW timing escalation
- keep business invalidation separate
- attach price review/entry context
- preserve provenance

It must NOT:
- create investment reasoning
- recalculate BUY:SELL
- infer business deterioration
- invent price levels

Required:

```text
COMPOSER_INVESTMENT_REASONING_INVENTED = 0
```

---

# 22. Existing V2 renderer ownership

Preserve:

```text
PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
```

User-visible form may remain conceptually:

```text
판단: HOLD · BUY:SELL 5:5
신규 관찰자: WAIT
보유자: REVIEW
```

But the reason for REVIEW may explicitly say:

```text
사업 방향은 유지되지만 가격 구조는 재점검이 필요함
```

Do not render technical weakness as business deterioration.

---

# 23. Ownership validator

Add deterministic hard checks:

```text
directional core contains price/technical ref
→ FAIL

directional core contains supply ref
→ FAIL

BUY/SELL lacks non-price material anchor
→ FAIL

price timing mutates direction/balance/lean
→ FAIL

price timing upgrades new-buyer stance
→ FAIL

price timing creates REDUCE
→ FAIL

technical breakdown mapped to business invalidation
→ FAIL
```

This validator uses structured domains/refs.

Do not parse arbitrary prose to decide ownership.

---

# 24. Counterfactual invariance synthetic suite

Before any real ticker regression, create ticker-free synthetic packets.

At minimum:

### Case A
```text
same strong fundamentals
price favorable vs adverse
```

Expected:

```text
same direction
same balance
same HOLD lean

timing fields may change
```

### Case B
```text
same neutral fundamentals
price rally vs price collapse
```

Expected:

```text
HOLD core unchanged
new buyer / holder review may change
SELL/REDUCE from price alone prohibited
```

### Case C
```text
same weak fundamentals
price strong vs weak
```

Expected:

```text
SELL core may remain
technical strength cannot rescue direction
```

### Case D
```text
BUY core + adverse MACD/RSI/support/volume
```

Expected:

```text
BUY core preserved
new buyer WAIT/AVOID allowed
holder REVIEW allowed
```

### Case E
```text
HOLD core + adverse technical + negative supply
```

Expected:

```text
HOLD core
WAIT/AVOID
REVIEW
no REDUCE
```

### Case F
```text
business deterioration + FCF deterioration + adverse technical
```

Expected:

```text
SELL/REDUCE allowed
because non-price anchor exists
```

### Case G
```text
technical breakdown only
```

Expected:

```text
price review
not business invalidation
```

Required:

```text
DIRECTION_TIMING_COUNTERFACTUAL_SUITE = PASS
```

---

# 25. Technical feature routing synthetic suite

Use ticker-free technical fixtures to prove the timing layer can ingest existing provider features without granting directional ownership.

Cover, where schema supports:

```text
support/resistance
volume
RSI
MACD
Bollinger
multi-timeframe structure
risk/reward
KR supply/positioning
```

The test must distinguish:

```text
feature unavailable
```

from:

```text
feature neutral
```

Do not fill unavailable features with zeros.

---

# 26. Prior latest holdout16 — one-shot regression only

Latest exposed holdout:

```text
PLTR, V, MA, AMZN, XOM, DIS, NKE, MCD, 033920, 104480, 071320, 096240, 032860, 060570, 016600, 462520
```

These subjects are NOT generalization evidence after this repair.

After architecture + selection policy freeze, they may be run ONCE for catastrophic regression / ownership audit.

Required:

```text
LATEST_HOLDOUT16_PURPOSE =
REGRESSION_ONLY

LATEST_HOLDOUT16_POST_RESULT_TUNING = 0
LATEST_HOLDOUT16_RERUN_COUNT <= 1
```

Do not demand a specific label for NKE or PLTR.

Instead require generic invariants:

```text
price-only BUY/SELL ownership violation = 0
price-only REDUCE = 0
timing mutation of core balance = 0
```

PLTR/NKE names must not appear in production rules.

---

# 27. Architecture freeze before new holdout selection

Freeze:

```text
evidence-domain registry
directional-core prompt/schema
price-timing prompt/schema
ownership validator
composer
renderer adapter
stability classifier
candidate selection policy
model
reasoning effort
source policy
```

Then no architecture mutation.

Required:

```text
OWNERSHIP_ARCHITECTURE_MUTATION_AFTER_FREEZE = 0
```

---

# 28. Final fresh issuer-level holdout

Exclude every issuer represented by all earlier exposed cohorts.

## Retired22

```text
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF, 000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280
```

## Preflight11

```text
010140, 011200, 017800, 021240, 024110, 035420, 051160, 055550, 443060, MSFT, NVDA
```

## Prior unseen16

```text
LLY, AAPL, NFLX, GOOG, CRM, PFE, META, AMD, 446070, 011090, 093370, 092460, 067280, 309930, 397810, 027970
```

## Latest holdout16

```text
PLTR, V, MA, AMZN, XOM, DIS, NKE, MCD, 033920, 104480, 071320, 096240, 032860, 060570, 016600, 462520
```

Issuer-level exclusion is authoritative.

Different share class or listing of the same issuer is excluded.

Required:

```text
FINAL_NEW_HOLDOUT_ISSUER_OVERLAP = 0
```

---

# 29. Candidate selection

Use the frozen canonical supported-security universe and frozen source-sufficiency policy.

Predeclare deterministic ranking.

Target:

```text
16 issuer-distinct subjects
KR 8 / US 8 preferred
```

Allowed:

```text
12–20
```

Minimum:

```text
12
```

Do not select based on expected BUY/HOLD/SELL.

Do not manually choose "easy" companies.

---

# 30. Source sufficiency remains pre-model

Every final subject must already pass:

```text
SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT
```

before any decision model call.

Required:

```text
DIRECTIONAL_CALLS_ON_SOURCE_INSUFFICIENT = 0
```

---

# 31. New immutable source lock

Freeze:
- issuer/security identity
- fundamental packet
- valuation
- market expectations where available
- technical/OHLCV packet
- supply packet
- all source timestamps
- all packet hashes
- domain registry version

Then create:

```text
NEW_OWNERSHIP_HOLDOUT_SOURCE_LOCK_SHA256
```

FIRST/A/B/C must use exactly the same lock.

---

# 32. FIRST

Run one fresh FIRST using:

```text
gpt-5.6-sol / xhigh
```

with frozen ownership architecture.

Required per subject:
- Directional Core result
- Directional Core evidence refs/domains
- Price-Timing result
- technical/supply refs
- composer result
- final validation

No same-generation repair.

---

# 33. FIRST gates

Proceed to A/B/C only if:

```text
validator false positive = 0
schema failure = 0
hard-safety regression = 0
ownership violation = 0
source-sufficiency escape = 0
```

If a generic architecture defect appears:

```text
STOP
```

Do not patch within the same holdout generation.

---

# 34. A / B / C

Use:
- same issuer cohort
- same source lock
- same Directional Core input
- same technical input
- same model/effort
- same architecture

No run reads another run.

No majority-vote production decision.

---

# 35. Core stability audit

Measure separately:

```text
DIRECTIONAL CORE STABILITY
```

and:

```text
TIMING OVERLAY STABILITY
```

Core fields:

```text
direction
balance
HOLD lean
fundamental new-buyer stance
fundamental holder stance
```

Timing fields:

```text
technical state
timing modifier
entry mode
price review
holder price review
```

A timing fluctuation must not be counted as core directional instability.

---

# 36. Counterfactual price sensitivity audit on real holdout

For audit only, do NOT change source facts.

Where safely possible using cloned test packets:

```text
same fundamental core
+
alternate valid technical states
```

verify:

```text
core direction / balance / lean invariant
```

This is not a new investment judgment.

It is an architecture invariance test.

Do not use synthetic alternate prices in user-visible recommendations.

---

# 37. Dominance audit v2

Replace the old coarse audit with ownership-aware diagnostics.

For every subject report:

```text
directional_core_dominant_domains
timing_overlay_dominant_features
final_direction_owner
new_buyer_final_owner
holder_final_owner
```

Required:

```text
FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0
PRICE_ONLY_HOLDER_REDUCE = 0
```

Price may dominate timing.

That is expected.

---

# 38. Hard-safety regression

Re-run:

```text
numeric provenance
accounting attribution
official provisional earnings
ADR/security basis
evidence identity/fencing
future checkpoint
logical condition
actionability command detection
structured/prose contradiction
source sufficiency
issuer dedup
renderer ownership
```

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
```

---

# 39. Registration/bootstrap is NOT implemented in this task

Do not yet modify monitoring registration lifecycle.

This task only produces the architecture handoff needed for the next step.

Required:

```text
MONITORING_REGISTRATION_CALLS = 0
BOOTSTRAP_PRODUCTION_MUTATION = 0
```

If this ownership proof passes, the next bounded task will connect:

```text
user-approved Initial Analysis
→ monitor registration
→ stored investment-logic baseline
→ same fundamental enrichment bootstrap
→ source sufficiency
→ monitoring-ready baseline
→ Daily Delta only after baseline
```

Initial bootstrap enrichment must not later be recorded as a Daily Delta.

---

# 40. Production remains untouched

Required:

```text
MAIN_MERGE = 0
PRODUCTION_DB_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
LIVE_V2_CHANGE = 0
```

---

# 41. Night futures remains unchanged

Required:

```text
NIGHT_FUTURES_CODE_MUTATION = 0
NIGHT_FUTURES_DECISION_PACKET_INJECTION = 0
```

Night futures stays market/timing context only.

---

# 42. Readiness outcome

If:
- source/fundamental path stays clean
- Directional Core owns direction
- price timing owns execution
- no price-only SELL/BUY or REDUCE violation
- new issuer holdout FIRST/A/B/C all validate
- core stability is acceptable
- hard-safety regression = 0

then maximum readiness is:

```text
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW
```

Not production deployment.

The next task is monitoring-registration bootstrap integration.

---

# 43. Required reports

Create:

1. `docs/reports/20260906-direction-timing-root-cause.md`
2. `docs/reports/20260906-evidence-domain-contract.md`
3. `docs/reports/20260906-directional-core-contract.md`
4. `docs/reports/20260906-price-timing-overlay-contract.md`
5. `docs/reports/20260906-ohlcv-technical-feature-routing-audit.md`
6. `docs/reports/20260906-supply-positioning-routing-audit.md`
7. `docs/reports/20260906-composer-ownership-contract.md`
8. `docs/reports/20260906-ownership-validator-contract.md`
9. `docs/reports/20260906-counterfactual-invariance-synthetic-suite.md`
10. `docs/reports/20260906-technical-feature-routing-synthetic-suite.md`
11. `docs/reports/20260906-latest-holdout16-one-shot-regression.md`
12. `docs/reports/20260906-ownership-architecture-freeze.md`
13. `docs/reports/20260906-new-issuer-holdout-selection-policy.md`
14. `docs/reports/20260906-new-issuer-holdout-selection.md`
15. `docs/reports/20260906-new-issuer-holdout-source-preflight.md`
16. `docs/reports/20260906-new-issuer-holdout-source-lock.md`
17. `docs/reports/20260906-ownership-first.md`
18. `docs/reports/20260906-ownership-run-a.md`
19. `docs/reports/20260906-ownership-run-b.md`
20. `docs/reports/20260906-ownership-run-c.md`
21. `docs/reports/20260906-core-stability-audit.md`
22. `docs/reports/20260906-timing-stability-audit.md`
23. `docs/reports/20260906-real-holdout-price-invariance-audit.md`
24. `docs/reports/20260906-dominance-ownership-audit-v2.md`
25. `docs/reports/20260906-renderer-shadow-proof.md`
26. `docs/reports/20260906-hard-safety-regression.md`
27. `docs/reports/20260906-monitoring-bootstrap-next-handoff.md`
28. `docs/reports/20260906-production-no-change.md`
29. `docs/reports/20260906-night-futures-no-change.md`
30. `docs/reports/20260906-program-completion.md`
31. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 44. Machine-readable proofs

Create:

```text
evidence-domain-contract.json
directional-core-contract.json
price-timing-overlay-contract.json
ohlcv-technical-feature-routing-audit.json
supply-positioning-routing-audit.json
composer-ownership-contract.json
ownership-validator-contract.json
counterfactual-invariance-synthetic-suite.json
technical-feature-routing-synthetic-suite.json
latest-holdout16-one-shot-regression.json
ownership-architecture-freeze.json
new-issuer-holdout-selection-policy.json
new-issuer-holdout-selection.json
new-issuer-holdout-source-preflight.json
new-issuer-holdout-source-lock.json
ownership-first.json
ownership-run-a.json
ownership-run-b.json
ownership-run-c.json
core-stability-audit.json
timing-stability-audit.json
real-holdout-price-invariance-audit.json
dominance-ownership-audit-v2.json
renderer-shadow-proof.json
hard-safety-regression.json
monitoring-bootstrap-next-handoff.json
production-no-change.json
night-futures-no-change.json
program-completion.json
```

---

# 45. Required gates

```text
SOURCE_REPORT_BUNDLE_SHA256 =
05e3f65245d069e761f46147be6a363b3994f665d1a14d92d811d4ef74f9977b

ROOT_CAUSE_CLASS =
DIRECTION_TIMING_OWNERSHIP_LEAKAGE / OTHER

OWNERSHIP_EXECUTION_MODE =
TWO_STAGE_FENCED /
EQUIVALENT_HARD_FENCED_SINGLE_STAGE

FUNDAMENTAL_SOURCE_ENRICHMENT_DRIFT =
0 / NONZERO

SOURCE_SUFFICIENCY_POLICY_DRIFT =
0 / NONZERO

INVESTMENT_DECISION_THRESHOLD_MUTATION =
0 / NONZERO

OHLCV_ANALYST_CALCULATION_ALGORITHM_MUTATION =
0 / NONZERO

INVENTED_TECHNICAL_INDICATOR =
0 / NONZERO

DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS =
0 / NONZERO

DIRECTIONAL_CORE_SUPPLY_REFS =
0 / NONZERO

SUPPLY_DIRECTIONAL_CORE_USAGE =
0 / NONZERO

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR =
0 / NONZERO

SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR =
0 / NONZERO

TIMING_STAGE_DIRECTION_MUTATION =
0 / NONZERO

TIMING_STAGE_BALANCE_MUTATION =
0 / NONZERO

TIMING_STAGE_HOLD_LEAN_MUTATION =
0 / NONZERO

PRICE_TIMING_NEW_BUYER_UPGRADE =
0 / NONZERO

PRICE_ONLY_HOLDER_REDUCE =
0 / NONZERO

COMPOSER_INVESTMENT_REASONING_INVENTED =
0 / NONZERO

DIRECTION_TIMING_COUNTERFACTUAL_SUITE =
PASS / FAIL

TECHNICAL_FEATURE_ROUTING_SYNTHETIC_SUITE =
PASS / FAIL

LATEST_HOLDOUT16_RERUN_COUNT =
0 / 1

LATEST_HOLDOUT16_POST_RESULT_TUNING =
0 / NONZERO

OWNERSHIP_ARCHITECTURE_MUTATION_AFTER_FREEZE =
0 / NONZERO

FINAL_NEW_HOLDOUT_ISSUER_OVERLAP =
0 / NONZERO

FINAL_NEW_HOLDOUT_SELECTED_COUNT =
...

FINAL_NEW_HOLDOUT_ELIGIBLE_COUNT =
...

FINAL_NEW_HOLDOUT_KR_COUNT =
...

FINAL_NEW_HOLDOUT_US_COUNT =
...

NEW_OWNERSHIP_HOLDOUT_SOURCE_LOCK_SHA256 =
...

DIRECTIONAL_CALLS_ON_SOURCE_INSUFFICIENT =
0 / NONZERO

FIRST_ABC_SOURCE_DRIFT =
0 / NONZERO

OWNERSHIP_FIRST_VALIDATED =
...

OWNERSHIP_FIRST_VALIDATOR_FALSE_POSITIVE =
0 / NONZERO

OWNERSHIP_FIRST_SCHEMA_FAILURE =
0 / NONZERO

OWNERSHIP_FIRST_HARD_SAFETY_TRUE_REJECT =
...

OWNERSHIP_FIRST_OWNERSHIP_VIOLATION =
0 / NONZERO

OWNERSHIP_RUN_A_VALIDATED =
... / NOT_RUN

OWNERSHIP_RUN_B_VALIDATED =
... / NOT_RUN

OWNERSHIP_RUN_C_VALIDATED =
... / NOT_RUN

CORE_STABLE_COUNT =
... / NOT_MEASURED

CORE_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

CORE_UNSTABLE_COUNT =
... / NOT_MEASURED

TIMING_STABLE_COUNT =
... / NOT_MEASURED

TIMING_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

TIMING_UNSTABLE_COUNT =
... / NOT_MEASURED

FINAL_DIRECTION_OWNER =
DIRECTIONAL_CORE / OTHER

PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS =
0 / NONZERO

PRIMARY_USER_ACTION_WORDING_OWNER =
RENDERER / OTHER

AI_IMPERATIVE_PRIMARY_ACTION =
0 / NONZERO

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO

MONITORING_REGISTRATION_CALLS =
0 / NONZERO

BOOTSTRAP_PRODUCTION_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

LIVE_STRUCTURED_AUTONOMY_ACTIVATION =
0 / NONZERO

LIVE_V2_CHANGE =
0 / NONZERO

NIGHT_FUTURES_CODE_MUTATION =
0 / NONZERO

READINESS =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW /
NEEDS_ARCHITECTURE_WORK /
BLOCKED_BY_SOURCE_COVERAGE /
NOT_READY
```

---

# 46. Stop conditions

STOP if:
- source enrichment or sufficiency is weakened
- decision thresholds are changed
- PLTR/NKE ticker-specific logic appears
- any prior exposed issuer enters the final holdout
- price/technical refs enter Directional Core
- supply enters Directional Core
- timing stage changes balance/direction/HOLD lean
- price timing upgrades a fundamental new-buyer stance
- price timing creates REDUCE
- a missing technical indicator is fabricated
- OHLCV calculation algorithms are changed merely to improve this holdout
- post-result same-generation repair is attempted
- source lock changes between FIRST/A/B/C
- production state is mutated

---

# 47. Completion response

Return:

```text
ROOT CAUSE =
...

OWNERSHIP ARCHITECTURE =
two-stage / equivalent fenced

DIRECTIONAL CORE =
allowed domains
price refs = 0
supply refs = 0

PRICE TIMING =
OHLCV feature inventory
RSI/MACD/Bollinger availability
support/resistance
volume
risk/reward
KR supply
invented features = 0

COMPOSER =
direction mutation = 0
new-buyer upgrades = 0
price-only REDUCE = 0

SYNTHETIC INVARIANCE =
...

LATEST HOLDOUT16 REGRESSION =
...
post-result tuning = 0

NEW ISSUER HOLDOUT =
selected ...
eligible ...
KR/US ...
issuer overlap = 0

SOURCE LOCK =
...

FIRST =
...

A =
...

B =
...

C =
...

CORE STABILITY =
...

TIMING STABILITY =
...

PRICE INVARIANCE =
...

DOMINANCE OWNERSHIP =
direction owner ...
violations ...

HARD SAFETY =
...

MONITORING BOOTSTRAP =
not yet activated
next handoff ...

PRODUCTION MUTATION =
0

NIGHT FUTURES =
unchanged

READINESS =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 48. Final principle

Use all validated price/technical/supply information for the question it can actually answer:

```text
When is price/timing favorable?
```

Do not let it answer a different question:

```text
Has the company's investment direction become BUY or SELL?
```

Company direction belongs to business, earnings, cash flow, valuation, expectations and structural risk.

Technical evidence belongs to timing, entry and review.

That separation is the architecture.
