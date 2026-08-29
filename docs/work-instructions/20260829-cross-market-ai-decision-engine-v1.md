# thesis-monitor — Cross-Market AI Decision Engine v1
## KR / US per-stock analytical BUY / HOLD / SELL classification
## Very-high reasoning
## Fundamental + valuation + expectations + macro + market internals + positioning + Price Structure + full safe OHLCV feature catalog
## Shadow first → test sink → selective production enablement
## No automated trading / no order execution

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `CROSS_MARKET_AI_DECISION_ENGINE_V1`
- Task class: `SHARED_DECISION_EVIDENCE_ENGINE + VERY_HIGH_REASONING + SHADOW_ROLLOUT`
- Markets:
  - KR
  - US / supported foreign securities in current monitored universe
- Output:
  - `BUY`
  - `HOLD`
  - `SELL`
  as an **analytical classification**, not an order command
- Default reasoning grade:
  - user-facing: `추론등급: 매우 높음`
  - backend: use the repository/model-provider supported equivalent of `very_high`
  - do not invent an unsupported model parameter/string
- Automated brokerage/order action: `0`
- Production Assist: preserve current state unless separately authorized
- Thesis / monitoring mutation: no automatic mutation from this decision output
- Price Structure / valuation / macro numeric calculations: backend-owned only

---

# 1. Latest validated baseline

Source bundle:

`20260829-us-night-futures-friday-saturday-and-ai-validator-repair-bundle.zip`

Latest validated result:

```text
BASE_SHA =
3cc91234ef88c655df981b0366a17045c95983f3

FINAL_MAIN / OPERATING =
7269120fb4d97abb61c5d5d5f91863f4c998e84b
```

Current closed items:

```text
US night futures Friday→Saturday:
SOURCE_LIMITATION_SAFE

Official KRX date semantics:
END_DATE

Friday→Saturday official KRX current row:
not published / not observed

Run-45 primary AI validator:
37 → 0

Run-45 backup AI validator:
4 → 0

US13 full-stock validation:
PASS

test sink:
14/14 exact PASS

open P0 / material P1:
0 / 0
```

Before implementation:

```text
git fetch origin
verify clean worktrees
resolve latest safe origin/main
resolve actual operating checkout
use 726912... or safe linear descendant
record exact lineage
```

---

# 2. Product objective

For every monitored KR / US-supported stock, build one canonical decision packet that lets AI reason across:

```text
company fundamentals
earnings quality
investment logic
market expectations
valuation
catalysts / risks
macro transmission
market regime
index / sector / breadth
futures
positioning / flows where supported
Price Structure
completed Bollinger
provisional Bollinger
multi-timeframe OHLCV-derived features
```

Then produce one current analytical classification:

```text
BUY
HOLD
SELL
```

with:

```text
reasoning grade
confidence
time horizon
strongest supporting evidence
strongest opposing evidence
unknowns
what would change the classification
```

---

# 3. Important semantic distinction

The engine is allowed to conclude:

```text
BUY
HOLD
SELL
```

but the user-facing output must describe this as:

```text
AI 종합 판단
분석 등급
현재 증거 기준 판단
```

not:

```text
지금 매수하세요
전량 매도하세요
시장가 주문
```

No order sizing.
No brokerage action.
No automatic trade.

Hard:

```text
AUTOMATED_TRADE_EXECUTION = 0
ORDER_SIZING_OUTPUT = 0
```

---

# 4. Primary time horizon

The classification must have an explicit horizon.

For registered stocks:

```text
use stored monitoring time_horizon if valid
```

Otherwise default analytical horizon:

```text
6–24 months
```

Separate:

```text
investment classification
```

from:

```text
short-term timing context
```

Example:

```text
AI 종합 판단: BUY
단기 타이밍: 불리 / 추가 확인 필요
```

or:

```text
AI 종합 판단: HOLD
단기 모멘텀: 강함
```

Do not let a short-term MACD cross silently become a long-horizon BUY.

---

# 5. Decision is free reasoning, not a point system

Do NOT implement:

```text
MACD +1
RSI +1
foreign flow +1
= BUY
```

No fixed weighted score may own the final classification.

The AI should reason from the full evidence packet.

Component states may be structured, but the final conclusion is a bounded evidence-grounded inference.

Hard:

```text
FINAL_DECISION_FROM_FIXED_WEIGHT_SUM = 0
```

---

# 6. Required reasoning hierarchy

Use this reasoning order:

```text
1. Fact integrity / data quality
2. Business quality / investment logic
3. Earnings trajectory / earnings quality
4. Market expectations
5. Valuation
6. Catalysts / risks / dilution
7. Macro transmission
8. Market / sector context
9. Positioning / flows
10. Price Structure
11. Multi-timeframe momentum / technical features
12. Opposing evidence
13. Unknowns
14. Final BUY / HOLD / SELL classification
15. Timing context
16. What changes the classification
```

Market/technical evidence can influence classification and timing,
but must not automatically mutate the stored business investment logic.

---

# 7. Evidence authority hierarchy

Prefer:

```text
canonical company / financial facts
canonical market facts
canonical price / OHLCV
canonical Price Structure
canonical derived indicator facts
structured AI interpretation
```

Never allow:

```text
free-form prose
```

to become numeric authority.

Every user-visible numeric that influences the decision must map to registered evidence.

Hard:

```text
UNREGISTERED_DECISION_NUMERIC = 0
FREEFORM_TEXT_AS_NUMERIC_AUTHORITY = 0
```

---

# 8. Track A — OHLCV Multi-Timeframe Feature Engine

Build/reuse a canonical backend feature engine from safe OHLCV.

Required timeframe order:

```text
monthly
weekly
daily
```

Authoritative features must use completed bars unless explicitly tagged provisional.

Do not mix partial bars into completed-bar features.

---

# 9. Canonical OHLCV coverage

Preserve current Price Structure targets:

```text
Daily target = 1200
Weekly target = 600
Monthly target = 300
```

Provider hard caps remain explicit:

```text
PARTIAL_SAFE / provider_limit
```

No synthetic history.
No fake resampling when an independently available higher timeframe is required.

Hard:

```text
SYNTHETIC_OHLCV = 0
LOOKAHEAD_LEAK = 0
```

---

# 10. Safe OHLCV feature catalog

Calculate the following where mathematically valid and supported by the available OHLCV history.

## 10.1 Returns / trend

```text
1 / 5 / 10 / 20 / 60 / 120 / 252-bar returns
rolling highs/lows
distance from rolling high/low
drawdown
trend slope
higher-high / lower-low state
```

Respect repository semantics for bar-window returns.

Do not relabel a 20-bar return as "1 month" unless the contract explicitly defines it that way.

## 10.2 Moving averages

```text
SMA
EMA
```

Supported horizons should include common decision-useful windows such as:

```text
5
10
20
50
100
200
```

only where sufficient history exists.

Derived states:

```text
price above/below
MA ordering
slope
cross state
distance
```

## 10.3 MACD

Canonical:

```text
MACD line
signal line
histogram
```

Default standard parameters may use the repository's canonical choice
(e.g. 12/26/9) only if explicitly documented.

For each D/W/M timeframe record:

```text
MACD
signal
histogram
cross state
cross recency
histogram direction
zero-line state
```

No AI calculation.

## 10.4 RSI

Calculate canonical RSI where supported.

Record:

```text
value
direction
overbought / oversold state only under documented thresholds
failure swing only if explicitly implemented and tested
```

Do not make RSI alone a BUY/SELL trigger.

## 10.5 ATR / volatility

```text
ATR
ATR %
realized volatility
range expansion/contraction
gap magnitude
```

Use for risk/timing context, not intrinsic valuation.

## 10.6 Bollinger

Preserve the existing three-layer policy:

```text
price structure
completed-bar Bollinger
provisional in-progress Bollinger
```

No semantic regression.

## 10.7 ADX / DMI

Where safe:

```text
ADX
+DI
-DI
trend-strength state
```

## 10.8 Momentum / ROC

```text
rate of change
price momentum
momentum acceleration/deceleration
```

## 10.9 Stochastic

Where mathematically supported:

```text
%K
%D
cross state
```

Use as secondary evidence only.

## 10.10 Volume-derived

Where volume is valid/comparable:

```text
volume vs rolling average
volume expansion/contraction
OBV
CMF / money-flow equivalent if supported
MFI if supported by valid volume and price basis
```

Do not compute volume-derived signals when volume basis is absent/incomparable.

## 10.11 Channels / breakouts

Where supported:

```text
Donchian / rolling breakout state
breakout / breakdown
failed breakout
gap state
```

Do not create target prices.

---

# 11. "All OHLCV indicators" does not mean arbitrary indicator explosion

The user permits any safely derivable OHLCV indicator.

The implementation may add repository-supported indicators beyond the explicit catalog above.

But every indicator must satisfy:

```text
documented formula
documented input basis
timeframe
minimum history
completed/provisional ownership
unit
fact ID
test coverage
```

Do not import a huge third-party TA catalog blindly.

Hard:

```text
UNDOCUMENTED_TECHNICAL_FEATURE = 0
```

---

# 12. Indicator redundancy control

The AI may see the full canonical feature packet.

But the renderer and final explanation must select only material evidence.

Do not dump:

```text
MACD
RSI
ADX
Stochastic
ATR
ROC
OBV
CMF
...
```

into every user message.

Target:

```text
2–5 material technical observations
```

unless an exceptional case requires more.

---

# 13. Multi-timeframe interpretation

Use hierarchy:

```text
monthly = structural / long-horizon momentum
weekly = intermediate
daily = tactical
```

Examples:

```text
D/W/M aligned bullish
weekly improving while monthly weak
daily reversal against strong monthly trend
```

The AI may reason across these states.

Do not force a simple "3/3 bullish" score.

---

# 14. Divergence

MACD/RSI/other divergence may be used only if the backend validates:

```text
price pivot A/B
indicator pivot A/B
same timeframe
correct temporal order
sufficient separation
completed bars
```

Hard:

```text
AI_INVENTED_TECHNICAL_DIVERGENCE = 0
```

---

# 15. Provisional technical features

Partial-bar technical features may be calculated only as explicitly provisional.

Allowed user-facing wording:

```text
진행 중
잠정
봉 마감 전 변동 가능
```

Provisional technicals may affect timing context but must not independently own:

```text
major structural S/R
business thesis
valuation
stored price rules
```

---

# 16. Track B — Cross-Market Per-Stock Evidence Packet

Create one canonical `decision_evidence_packet` per stock.

Required sections:

```text
identity
business thesis
earnings
earnings quality
market expectations
valuation
catalysts
risks
macro exposures
market context
sector context
positioning/flows
price context
Price Structure
OHLCV features
data-quality gates
unknowns
```

Every section must carry `as_of` and evidence refs.

---

# 17. KR market context packet

Where available, include:

```text
KOSPI
KOSDAQ
breadth
foreign / institution / retail flows
foreign ownership
size/style
sector TOP3 / full supported sector context
KOSPI200 / KOSDAQ150 night futures when canonical-current
KR macro transmission
FX
rates
oil where relevant
```

Participant flows remain positioning evidence.

They must not alone mutate business investment logic.

---

# 18. US market context packet

Include:

```text
SPY
QQQ
IWM
SOXX
RSP
sector ETF dispersion
official Nasdaq breadth when exact-session current
NYSE breadth only if supported
US rates
real rates
VIX
WTI
USD/KRW / dollar context where transmission exists
Korea night futures when canonical-current
```

Friday→Saturday KRX limitation remains:

```text
SOURCE_LIMITATION_SAFE
```

Do not fabricate the missing section.

---

# 19. Macro integration

For each stock, only include macro factors with an actual transmission channel.

Examples:

```text
rates → duration / valuation discount rate
real rates → long-duration growth equity
oil → energy producer margin / transport cost
FX → exporter/importer earnings
AI CAPEX → semiconductor demand
```

Each macro exposure needs:

```text
factor
direction
channel
horizon
condition
```

Do not let generic macro narrative dominate a company with no clear channel.

---

# 20. Market expectations

Require one of:

```text
depressed
low
balanced
elevated
very_high
speculative
unknown
```

The AI must explicitly reason:

```text
what is already priced in?
what positive surprise is needed?
what downside surprise would matter?
```

Strong business quality with `very_high` expectations may still classify `HOLD`.

---

# 21. Valuation

Use the industry-appropriate primary framework.

Possible examples:

```text
SOTP
PER
PBR
EV/EBITDA
FCF yield
EV/Sales
NAV
biotech cash/runway
other documented method
```

No universal PER-centric decision.

Preserve:

```text
ADR/security basis
currency
share denominator
basic/diluted basis
official attribution
```

If valuation basis is unsafe:

do not invent a multiple.

---

# 22. Price Structure integration

Preserve current hierarchy:

```text
near support/resistance
price-anchored major structural S/R
completed Bollinger
provisional Bollinger
Fib only if safe
stored monitoring price rules separate
```

The AI may use these for timing/risk/reward interpretation.

No target/stop invention.

---

# 23. Positioning / flows

KR:

```text
foreign
institution
retail
1D / 5D / 20D
foreign ownership
```

US:

use only supported positioning data.

Do not mimic KR participant-flow semantics where US data does not support it.

Hard:

```text
US_FAKE_KR_STYLE_FLOW = 0
```

---

# 24. Data-quality gates

Each evidence packet must contain:

```text
hard_invalid
material_partial
stale
source_limitation
security_basis_conflict
currency_conflict
financial_quality_denied
unknowns
```

The decision engine must see these flags.

---

# 25. Track C — Very-High Reasoning Decision Engine

Use the repository-supported AI route with the strongest available reasoning configuration.

User-facing field:

```text
추론등급: 매우 높음
```

This describes reasoning depth.

It is NOT confidence.

Separate:

```text
판단 확신도:
높음 / 중간 / 낮음
```

or repository-native equivalent.

Do not present reasoning grade as probability.

---

# 26. Decision taxonomy

Required enum:

```text
BUY
HOLD
SELL
```

User-facing Korean:

```text
BUY
HOLD
SELL
```

may be supplemented with:

```text
매수 우위
보유/관망
매도 우위
```

but use one canonical enum internally.

---

# 27. Data-limited fail-closed behavior

If essential company/security/valuation evidence is materially invalid:

do not force an overconfident directional rating.

Allowed safe form:

```text
HOLD
판단 확신도: 낮음
핵심 사유: valuation/security basis 미확인
```

or repository-native `HOLD_DATA_LIMITED` substate mapped user-facing to HOLD.

Do not introduce a fourth top-level decision unless explicitly approved.

---

# 28. BUY analytical meaning

A `BUY` classification should generally require an evidence-grounded combination such as:

```text
business investment logic attractive or strengthening
earnings path supportive
expectations not excessively demanding relative to upside
valuation offers sufficient asymmetry
key risks not currently dominant
market/technical context not invalidating the thesis
```

Not every item must be bullish.

The AI must explain opposing evidence.

---

# 29. HOLD analytical meaning

`HOLD` may mean:

```text
good company but valuation/expectations too high
business thesis intact but catalyst unclear
positive fundamentals vs negative market regime
data conflict / insufficient evidence
price already reflects much of the upside
balanced bull/bear evidence
```

Do not treat HOLD as "nothing happening".

---

# 30. SELL analytical meaning

A `SELL` classification should generally require evidence such as:

```text
business thesis materially weakened
earnings estimates deteriorating
expectations still too high
valuation asymmetry poor
structural/dilution/regulatory risk rising
or
evidence combination makes downside materially dominant
```

Technical weakness alone must not automatically become a long-horizon SELL.

---

# 31. Business quality vs timing

Output both:

```text
AI 종합 판단
단기 타이밍
```

Timing enum may use:

```text
우호적
중립
불리
```

or repository-native equivalent.

Examples:

```text
BUY + 단기 타이밍 불리
HOLD + 단기 모멘텀 우호적
SELL + 단기 기술적 반등 가능
```

---

# 32. Required opposing-evidence reasoning

Every BUY/HOLD/SELL output must contain:

```text
strongest bullish evidence
strongest bearish evidence
key unknown
decisive reason for final classification
```

Hard:

```text
ONE_SIDED_DECISION_WITHOUT_OPPOSING_EVIDENCE = 0
```

---

# 33. Decision-change conditions

Every decision must state:

```text
what would strengthen BUY case
what would weaken it
what would flip HOLD→BUY / HOLD→SELL
what would invalidate current classification
```

Use real monitored metrics/facts.

Do not invent target prices.

---

# 34. Decision confidence

Confidence must be derived from:

```text
evidence completeness
source quality
cross-domain agreement/conflict
freshness
security/valuation basis
unknowns
```

Not from how strongly the AI phrases the answer.

Do not express confidence as an event probability.

---

# 35. Suggested user-facing message

Target shape:

```text
🏢 Company(TICKER)

🧠 AI 종합 판단: HOLD
추론등급: 매우 높음
판단 확신도: 높음
판단 기준: 6–24개월

🎯 판단
...

✅ BUY 쪽 근거
• ...
• ...

⚠️ SELL 쪽 근거
• ...
• ...

🌐 시장환경
• ...

📐 가격 구조
• ...

📈 모멘텀
• 주봉 MACD ...
• 일봉 RSI ...
• 거래량 / 상대강도 ...

💰 Valuation
• ...

👁 판단이 바뀌는 조건
• ...

📌 의미
신규 관찰자: ...
기존 보유자: ...
```

Do not force every section if evidence is absent.

---

# 36. Message-density policy

The AI may reason over the full feature packet.

The user-facing message should show only material factors.

Target:

```text
2–4 fundamental/valuation factors
1–3 market/macro factors
2–5 price/momentum factors
1–3 opposing/unknown factors
```

No technical indicator dump.

---

# 37. Numeric provenance

Every number selected into the final explanation must have:

```text
fact_id
field_path
unit
as_of
source/basis
```

Hard:

```text
DECISION_NUMERIC_WITHOUT_PROVENANCE = 0
```

---

# 38. Validator ownership

The validator must consume the same structured decision plan used by the renderer.

Do not repeat the run-44 legacy mistake.

Required states:

```text
SELECTED_REQUIRED
SELECTED_AS_SUPPORTING_EVIDENCE
OMITTED_BY_MATERIALITY
OMITTED_BY_DISPLAY_BUDGET
OMITTED_BY_SAFETY
NOT_AVAILABLE
```

Intentional omission is not a validation failure.

Selected evidence missing from the final message must still fail.

---

# 39. No hidden AI calculations of market features

Backend calculates:

```text
MACD
RSI
ATR
ADX
returns
Bollinger
volume indicators
relative spreads
valuation multiples
price distances
```

AI only reasons from registered values/states.

Hard:

```text
AI_CALCULATED_TECHNICAL_FEATURE = 0
AI_CALCULATED_VALUATION_MULTIPLE = 0
```

---

# 40. Track D — Shadow mode

Before user-facing BUY/HOLD/SELL production enablement:

run in shadow mode.

Current reference universes:

KR controls:

```text
000660
003690
005490
005930
010120
012450
086280
```

US current monitored reference:

```text
CORZ
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

Use the ACTUAL current monitored universes at execution time.

---

# 41. Current-date shadow replay

For every stock produce:

```text
decision
confidence
time horizon
timing state
bull evidence refs
bear evidence refs
unknown refs
decision-change conditions
selected technical refs
```

Do NOT send these BUY/HOLD/SELL labels to production yet.

Store sanitized shadow artifacts only.

---

# 42. Temporal historical replay

Use historical cutoff dates with strict no-lookahead.

At minimum where data availability supports it:

```text
10 historical decision checkpoints per stock
```

across multiple market regimes.

For every checkpoint:

```text
packet contains only evidence available as of cutoff
AI decision generated
future data unavailable to AI
```

Then separately evaluate future outcomes after generation.

Hard:

```text
HISTORICAL_REPLAY_LOOKAHEAD_LEAK = 0
```

---

# 43. Historical outcome evaluation

Outcome evaluation is diagnostic, not a new deterministic training rule.

Possible measurements:

```text
forward 20 / 60 / 120 trading-day return
max drawdown
relative return vs market/sector
decision persistence
decision flip frequency
```

Do not tune thresholds to individual stocks after seeing outcomes.

Report overfitting risk.

---

# 44. Decision stability

Detect pathological churn:

```text
BUY → SELL → BUY
```

without meaningful evidence changes.

Require:

```text
decision change
→ evidence delta / expectation / valuation / thesis / market context explanation
```

Set:

```text
UNEXPLAINED_DECISION_CHURN = 0
```

---

# 45. Cross-market consistency

Equivalent evidence should produce consistent semantics across KR/US.

But do not force identical outcomes because:

```text
valuation methods
market data
flows
security basis
macro transmission
```

differ.

---

# 46. Shadow review report

For every current stock show:

```text
ticker
decision
confidence
fundamental state
expectation level
valuation state
market state
technical state
top bull reason
top bear reason
key unknown
```

This is the main operator review table.

---

# 47. Track E — Dedicated test sink

After shadow replay and temporal tests PASS:

send decision-enabled messages to the existing dedicated non-production test sink.

Test:

```text
all current KR monitored stocks
all current US/foreign monitored stocks
```

No production recipient.

---

# 48. Test-sink review

Verify:

```text
BUY/HOLD/SELL label readable
reasoning grade = very high
confidence separate
no order instruction
fundamental vs timing distinction
technical evidence material, not dumped
valuation basis safe
Price Structure intact
message length acceptable
```

Hard:

```text
TEST_DECISION_MESSAGE_QUALITY = PASS
```

---

# 49. AI / fallback behavior

The BUY/HOLD/SELL decision is AI-owned.

If the AI candidate fails validation:

do NOT fabricate a deterministic BUY/HOLD/SELL replacement unless a separately approved deterministic policy exists.

Preferred safe behavior:

```text
decision label omitted
existing deterministic stock message still delivered
```

or:

```text
HOLD / 판단 보류
```

only if explicitly specified by the product contract.

Do not silently convert validation failure to SELL or BUY.

---

# 50. Production enablement strategy

Do NOT globally expose on first implementation.

Use:

```text
SHADOW
→ TEST_SINK
→ BOUNDED_CANARY
→ FULL_MONITORED_UNIVERSE
```

Suggested canary:

```text
KR <= 2
US <= 2
```

chosen to cover different business/valuation/technical states.

Do not cherry-pick only obvious winners.

---

# 51. Canary PASS requirements

Require at least:

```text
2 natural production cycles per enabled market
```

with:

```text
validator pass
no unsupported numeric
no decision churn without evidence delta
no message-quality regression
no false automated trade implication
```

before broadening.

---

# 52. Production state machine

Use explicit states:

```text
OFF
SHADOW
TEST_SINK_READY
CANARY
FULL_MONITORED_UNIVERSE
```

Do not conflate `SHADOW` with user-visible enablement.

---

# 53. No auto-monitor mutation

Decision output does not automatically:

```text
change core investment logic
change monitoring thesis version
change warning lifecycle
change price rules
stop monitoring
```

Those remain separate owned processes.

---

# 54. Required architecture docs

Create/update:

```text
docs/architecture/CROSS_MARKET_AI_DECISION_ENGINE.md
docs/architecture/OHLCV_MULTI_TIMEFRAME_FEATURE_ENGINE.md
docs/architecture/DECISION_EVIDENCE_PACKET.md
docs/architecture/DECISION_VALIDATOR_OWNERSHIP.md
docs/architecture/DECISION_SHADOW_AND_CANARY_ROLLOUT.md
```

---

# 55. Required reports

Create at minimum:

1. `docs/reports/20260829-decision-engine-scope.md`
2. `docs/reports/20260829-ohlcv-feature-catalog.md`
3. `docs/reports/20260829-macd-dwm-contract.md`
4. `docs/reports/20260829-technical-feature-data-quality.md`
5. `docs/reports/20260829-cross-market-evidence-packet.md`
6. `docs/reports/20260829-decision-reasoning-contract.md`
7. `docs/reports/20260829-decision-validator-contract.md`
8. `docs/reports/20260829-kr-current-shadow-decisions.md`
9. `docs/reports/20260829-us-current-shadow-decisions.md`
10. `docs/reports/20260829-temporal-shadow-replay.md`
11. `docs/reports/20260829-decision-churn-analysis.md`
12. `docs/reports/20260829-decision-ai-fallback-behavior.md`
13. `docs/reports/20260829-decision-test-sink.md`
14. `docs/reports/20260829-decision-message-quality.md`
15. `docs/reports/20260829-decision-canary-readiness.md`
16. `docs/reports/20260829-decision-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-ohlcv-feature-catalog.json
docs/reports/20260829-current-shadow-decisions.json
docs/reports/20260829-temporal-shadow-replay.json
docs/reports/20260829-decision-canary-readiness.json
```

---

# 56. Required gates

Set exactly:

```text
DECISION_ENGINE_REASONING_GRADE =
VERY_HIGH / OTHER

AUTOMATED_TRADE_EXECUTION =
0 / NONZERO

ORDER_SIZING_OUTPUT =
0 / NONZERO

FINAL_DECISION_FROM_FIXED_WEIGHT_SUM =
0 / NONZERO

UNREGISTERED_DECISION_NUMERIC =
0 / NONZERO

FREEFORM_TEXT_AS_NUMERIC_AUTHORITY =
0 / NONZERO

UNDOCUMENTED_TECHNICAL_FEATURE =
0 / NONZERO

AI_CALCULATED_TECHNICAL_FEATURE =
0 / NONZERO

AI_CALCULATED_VALUATION_MULTIPLE =
0 / NONZERO

AI_INVENTED_TECHNICAL_DIVERGENCE =
0 / NONZERO

DECISION_NUMERIC_WITHOUT_PROVENANCE =
0 / NONZERO

ONE_SIDED_DECISION_WITHOUT_OPPOSING_EVIDENCE =
0 / NONZERO

US_FAKE_KR_STYLE_FLOW =
0 / NONZERO

HISTORICAL_REPLAY_LOOKAHEAD_LEAK =
0 / NONZERO

UNEXPLAINED_DECISION_CHURN =
0 / NONZERO

KR_CURRENT_SHADOW_COUNT =
...

US_CURRENT_SHADOW_COUNT =
...

KR_SHADOW_VALIDATION =
PASS / FAIL

US_SHADOW_VALIDATION =
PASS / FAIL

TEMPORAL_SHADOW_REPLAY =
PASS / PARTIAL_SAFE / FAIL

TEST_DECISION_MESSAGE_COUNT =
...

TEST_DECISION_MESSAGE_QUALITY =
PASS / FAIL

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

DECISION_CANARY_READINESS =
PASS / FAIL / BLOCKED

DECISION_ENGINE_STATE =
OFF /
SHADOW /
TEST_SINK_READY /
CANARY /
FULL_MONITORED_UNIVERSE

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...
```

---

# 57. Pre-canary PASS rule

Require:

```text
OHLCV feature catalog documented/tested
D/W/M MACD PASS
data-quality gates PASS
decision evidence packet complete
numeric provenance PASS
current KR shadow PASS
current US shadow PASS
temporal no-lookahead replay PASS/PARTIAL_SAFE
no unexplained churn
test-sink messages PASS
no auto-trading semantics
P0 = 0
material P1 = 0
```

Then:

```text
DECISION_ENGINE_STATE = TEST_SINK_READY
DECISION_CANARY_READINESS = PASS
```

Do not automatically enable production canary without operator review of the shadow/test bundle.

---

# 58. Completion response

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

TRACK_E_BRANCH = ...
TRACK_E_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

DECISION_ENGINE_REASONING_GRADE = VERY_HIGH

OHLCV_FEATURE_COUNT = ...
OHLCV_FEATURE_FAMILIES = ...

MACD_DAILY = PASS / FAIL
MACD_WEEKLY = PASS / FAIL
MACD_MONTHLY = PASS / FAIL

KR_CURRENT_SHADOW_COUNT = ...
US_CURRENT_SHADOW_COUNT = ...

CURRENT_SHADOW_DECISIONS =
...

KR_SHADOW_VALIDATION = ...
US_SHADOW_VALIDATION = ...

TEMPORAL_SHADOW_REPLAY = ...
HISTORICAL_REPLAY_LOOKAHEAD_LEAK = 0
UNEXPLAINED_DECISION_CHURN = 0

AI_CALCULATED_TECHNICAL_FEATURE = 0
AI_CALCULATED_VALUATION_MULTIPLE = 0
UNREGISTERED_DECISION_NUMERIC = 0
DECISION_NUMERIC_WITHOUT_PROVENANCE = 0

ONE_SIDED_DECISION_WITHOUT_OPPOSING_EVIDENCE = 0

TEST_DECISION_MESSAGE_COUNT = ...
TEST_DECISION_MESSAGE_QUALITY = ...
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

AUTOMATED_TRADE_EXECUTION = 0
ORDER_SIZING_OUTPUT = 0

DECISION_CANARY_READINESS = ...

DECISION_ENGINE_STATE =
SHADOW /
TEST_SINK_READY /
CANARY /
FULL_MONITORED_UNIVERSE /
FAIL

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

NEXT_ACTION =
REVIEW_SHADOW_DECISIONS /
ENABLE_BOUNDED_CANARY /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 59. Mandatory completion ZIP

Create:

`20260829-cross-market-ai-decision-engine-v1-bundle.zip`

Include:

```text
exact master instruction
all track instructions
OHLCV feature catalog
MACD D/W/M evidence
data-quality contract
cross-market evidence packet examples
decision reasoning contract
validator ownership
KR current shadow decisions
US current shadow decisions
temporal replay
decision-churn analysis
test-sink exact messages
message-quality review
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

# 60. Final principle

The engine may use every safe piece of evidence the system owns.

That does NOT mean every indicator gets equal weight,
and it does NOT mean every indicator is printed.

The AI should reason freely across:

```text
business
earnings
expectations
valuation
macro
market
positioning
price structure
OHLCV features
```

with very-high reasoning,
while every factual/numeric input remains backend-owned and auditable.

The final `BUY / HOLD / SELL` label is an analytical classification,
not an automated trade command.
