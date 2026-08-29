# thesis-monitor — Current-Time Cross-Market Canary Message E2E Test
## Fresh data collection as of actual execution time
## KR market + US market + 4 current canary stock decision messages
## Dedicated test sink only
## Do NOT count as natural canary cycle

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `CURRENT_TIME_CROSS_MARKET_CANARY_MESSAGE_E2E_TEST`
- Task class: `READ_ONLY_FRESH_DATA_COLLECTION + TEST_SINK_E2E`
- Production recipient send: `0`
- Production delivery intent: `0`
- Scheduler mutation: `0`
- Thesis/monitoring mutation: `0`
- Decision-engine canary membership mutation: `0`
- Natural canary counters: do not increment
- Automated trade execution: `0`
- Order sizing: `0`

Latest validated baseline:

```text
FINAL_MAIN / OPERATING =
0f96a6464769cd1ca01ff5d2da632d2759ee32d9

DECISION_ENGINE_STATE =
CANARY

PRODUCTION_CANARY_ENABLED =
true

CANARY KR =
003690
000660

CANARY US =
GOOGL
RXRX

Last accepted decisions:
003690 HOLD
000660 HOLD
GOOGL HOLD
RXRX SELL

Natural canary cycles:
KR 0/2
US 0/2

Open P0 / material P1:
0 / 0
```

Before execution:

```text
git fetch origin
verify clean working tree
resolve actual latest safe origin/main
resolve actual operating checkout
confirm 0f96a6... or safe linear descendant
record exact execution_time_kst
```

---

# 1. Objective

At the actual current execution time:

```text
1. collect fresh KR market data
2. collect fresh US market data
3. collect fresh company/earnings/valuation/market/price/OHLCV evidence
   for the 4 canary subjects
4. rebuild each canonical decision evidence packet
5. run VERY_HIGH reasoning decision generation
6. validate decision polarity / confidence / timing / provenance
7. render exact current messages
8. send only to the dedicated non-production test sink
9. inspect the received Telegram messages
```

Required current test messages:

```text
KR market message = 1
US market message = 1
KR canary stock messages = 2
US canary stock messages = 2

TOTAL = 6
```

Use actual current canary membership at execution time.
If membership changed unexpectedly:

STOP and report.

---

# 2. Important time semantics

This is a Saturday KST current-time test.

Do not assume current calendar date is a trading session.

Resolve:

```text
EXECUTION_TIME_KST
LATEST_COMPLETED_KR_SESSION
LATEST_COMPLETED_US_SESSION
NEXT_KR_REGULAR_SESSION
```

Expected by calendar may be:

```text
KR latest completed = 2026-08-28
US latest completed = 2026-08-28
```

but resolve from actual exchange/provider calendars.

Hard:

```text
CURRENT_TIME_SESSION_RESOLUTION = PASS
```

---

# 3. KR market fresh collection

Collect the current canonical KR market packet using the latest completed safe KR session.

Required where supported:

```text
KOSPI
KOSDAQ

breadth:
advance
decline
unchanged
A/D ratio

participant flows:
foreign
institution
retail

size/style:
KOSPI large / mid / small
KOSDAQ100 / MID300 / SMALL

sector:
full supported sector set
TOP3 strong
TOP3 weak

foreign ownership / other canonical KR market context where current
```

Do not reuse the prior report values merely because the session is unchanged.

Run the actual providers again and record fresh acquisition timestamps.

---

# 4. KR market message candidate

Render the currently deployed KR market-message contract.

Required checks:

```text
index numbers
breadth
participant flow
size/style
sector TOP3
line breaks / readability
```

No Price Structure in market message.

Create:

```text
EXACT_CURRENT_KR_MARKET_MESSAGE
```

---

# 5. US market fresh collection

Collect current canonical US market data for the latest completed US session.

Required:

```text
SPY
QQQ
IWM
SOXX
RSP

sector ETF universe
strongest / weakest sectors

Nasdaq official breadth when exact-session available

rates / real rates / VIX / WTI / FX
only under existing temporal roles
```

No AI-calculated index return.

---

# 6. Korea night futures in the US message

Run the canonical night-futures gate again at actual execution time.

Current known source contract:

```text
Friday→Saturday KRX current overnight row
may be officially unavailable.

Prior conclusion:
SOURCE_LIMITATION_SAFE
source date semantics = END_DATE
```

Do not force a night-futures section.

If a new current-safe source observation unexpectedly exists:

record it and render normally.

If not:

safe omission remains correct.

Hard:

```text
NIGHT_FUTURES_CANONICAL_GATE_USED = PASS
STALE_NIGHT_FUTURES_VISIBLE = 0
RAW_SUMMARY_NIGHT_FUTURES_BYPASS = 0
```

---

# 7. US market message candidate

Render the current deployed US market contract:

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY ...
• QQQ ...
• IWM ...
• SOXX ...
• RSP ...

🔎 시장 내부
• participation/style
• semiconductor relative behavior
• selected sector dispersion

🌙 한국 야간선물
(only current-safe)

🌐 보조 시장환경
(only material/temporally safe)

📌 다음 확인
...
```

Create:

```text
EXACT_CURRENT_US_MARKET_MESSAGE
```

---

# 8. Four canary subjects

Current expected canary subjects:

```text
KR:
003690 DB Insurance
000660 SK hynix

US:
GOOGL
RXRX
```

Use actual current canary membership from runtime state.

Hard:

```text
CURRENT_CANARY_KR_COUNT = 2
CURRENT_CANARY_US_COUNT = 2
```

No automatic substitution.

---

# 9. Fresh per-stock evidence collection

For each canary subject refresh all canonical evidence available now:

```text
company identity
business thesis
earnings checkpoints
financial quality
market expectations
valuation
catalysts / risks
macro exposures
market context
sector context
positioning/flows where supported
current quote
structure-basis close
Price Structure
completed Bollinger
provisional Bollinger
OHLCV multi-timeframe features
data-quality flags
unknowns
```

Do not copy the previous decision packet without reacquisition.

---

# 10. OHLCV / technical feature refresh

Recompute current safe D/W/M features from canonical OHLCV.

Where supported:

```text
returns / drawdown
SMA / EMA
MACD / signal / histogram
RSI
ATR / volatility
Bollinger
ADX / DMI
ROC / Stochastic
volume-derived features
breakout/channel states
validated divergence
```

Completed-bar features authoritative.

Partial-bar features only if explicitly provisional.

No AI calculations.

Hard:

```text
AI_CALCULATED_TECHNICAL_FEATURE = 0
```

---

# 11. Price Structure refresh

Preserve current semantics:

```text
near support/resistance
price-anchored major structural S/R
completed Bollinger
provisional Bollinger
stored monitoring price rules separate
```

No target/stop invention.

Hard:

```text
BOLLINGER_ONLY_MAJOR_SR_VISIBLE = 0
PROVISIONAL_BOLLINGER_AUTHORITY_LEAK = 0
UNSUPPORTED_TARGET_PRICE = 0
UNSUPPORTED_STOP_PRICE = 0
```

---

# 12. Current quote vs structure-basis price

If equal:

allow concise:

```text
현재가(정규장 종가): ...
```

If different:

require:

```text
현재가: ...
가격 구조 기준 종가(정규장): ...
```

No ambiguous two-price presentation.

Hard:

```text
AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL = 0
```

---

# 13. Fresh decision generation

Run the validated current decision engine using:

```text
reasoning grade = VERY_HIGH
```

For each subject produce:

```text
BUY / HOLD / SELL
confidence
confidence reason
horizon
timing
HOLD reason if HOLD
WHY_NOT_BUY if HOLD
WHY_NOT_SELL if HOLD
bullish evidence
bearish evidence
neutral context
key unknown
upgrade condition
downgrade condition
```

No fixed weighted score.

---

# 14. Decision continuity vs fresh evidence

Compare the fresh evidence packet SHA / canonical fingerprint with the last accepted canary packet.

## Same evidence

If evidence is materially identical:

```text
decision should remain continuous
```

An unexplained decision flip is a failure.

## Changed evidence

If evidence materially changed:

decision may change,
but require an explicit evidence delta.

Record:

```text
previous decision
new decision
evidence delta
decisive reason for change
```

Hard:

```text
UNEXPLAINED_CURRENT_DECISION_CHURN = 0
```

---

# 15. Previous accepted decisions are controls, not hard-coded outputs

Previous accepted:

```text
003690 HOLD
000660 HOLD
GOOGL HOLD
RXRX SELL
```

Do not force them if genuinely fresh evidence changes.

Do not allow a change without evidence delta.

---

# 16. Evidence polarity

Use the repaired canonical polarity contract:

```text
BULLISH
BEARISH
NEUTRAL
```

User-facing:

```text
✅ BUY 쪽 근거
→ selected BULLISH only

⚠️ SELL 쪽 근거
→ selected BEARISH only
```

Neutral/data-quality facts cannot own either section.

Hard:

```text
BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS
NEUTRAL_FACT_FORCED_INTO_BUY_SELL_SECTION = 0
```

---

# 17. Reasoning grade / confidence / timing separation

Every canary decision message must clearly separate:

```text
추론등급: 매우 높음
판단 확신도: ...
판단 기준: ...
단기 타이밍: ...
```

Hard:

```text
REASONING_GRADE_AS_CONFIDENCE = 0
TIMING_TO_DECISION_HARD_MAPPING = 0
MACD_ALONE_OWNS_BUY_SELL = 0
```

---

# 18. No trading-command language

No:

```text
지금 매수
지금 매도
전량 매도
시장가
비중
자동 주문
```

The decision remains analytical.

Hard:

```text
ORDER_COMMAND_LANGUAGE = 0
ORDER_SIZING_OUTPUT = 0
```

---

# 19. Render current stock messages

For each canary subject render the exact current production-equivalent message.

Create:

```text
EXACT_CURRENT_003690_MESSAGE
EXACT_CURRENT_000660_MESSAGE
EXACT_CURRENT_GOOGL_MESSAGE
EXACT_CURRENT_RXRX_MESSAGE
```

Use current fresh evidence.

---

# 20. Dedicated test sink only

Send exactly the six current messages:

```text
1 KR market
1 US market
4 current canary stock messages
```

to the existing dedicated non-production test sink.

Do NOT send historical BUY fixtures in this task.

Do NOT send to production recipients.

Hard:

```text
TEST_MESSAGE_COUNT = 6
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 21. Exact payload proof

For each test message compare:

```text
rendered
outbound
received
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
```

---

# 22. Actual Telegram visual review

Human-review the received messages.

KR market:

```text
readability
TOP3
flows
breadth
```

US market:

```text
index block
market internals
night-futures safe display/omission
macro
```

Stocks:

```text
decision
bull/bear polarity
confidence
timing
Price Structure
Bollinger
valuation
message density
```

Hard:

```text
CURRENT_TIME_MESSAGE_QUALITY = PASS
```

---

# 23. Test does NOT count as natural canary proof

Do not increment:

```text
KR_NATURAL_CANARY_CYCLES
US_NATURAL_CANARY_CYCLES
```

Expected after this test:

```text
KR 0/2
US 0/2
```

unless actual natural production cycles independently happened during the task.

Test-sink traffic never counts.

---

# 24. Production canary state

Do not disable/expand canary merely because of this test.

If all tests PASS:

preserve:

```text
DECISION_ENGINE_STATE = CANARY
PRODUCTION_CANARY_ENABLED = true
```

for the same exact four subjects.

If a material P1/P0 is found:

stop and report.
Do not silently expand or repair in production.

---

# 25. Data-quality issue handling

Classify any issue:

```text
SAFE_OMISSION
STALE
SOURCE_LIMITATION
PROVIDER_ERROR
SECURITY_BASIS_CONFLICT
VALUATION_LIMIT
TECHNICAL_FEATURE_LIMIT
DECISION_SEMANTIC_CONFLICT
P1
P0
```

Do not guess missing facts.

---

# 26. Current-time operator review table

Create one compact table:

```text
market
ticker/product
latest session
current decision
previous decision
confidence
timing
evidence changed?
top bull
top bear
Price Structure summary
test message PASS
```

Rows:

```text
KR market
US market
003690
000660
GOOGL
RXRX
```

---

# 27. Required reports

Create:

1. `docs/reports/20260829-current-time-session-resolution.md`
2. `docs/reports/20260829-current-time-kr-market-data.md`
3. `docs/reports/20260829-current-time-us-market-data.md`
4. `docs/reports/20260829-current-time-night-futures-state.md`
5. `docs/reports/20260829-current-time-canary-evidence-refresh.md`
6. `docs/reports/20260829-current-time-canary-decision-delta.md`
7. `docs/reports/20260829-current-time-canary-exact-messages.md`
8. `docs/reports/20260829-current-time-market-exact-messages.md`
9. `docs/reports/20260829-current-time-test-delivery.md`
10. `docs/reports/20260829-current-time-message-quality.md`
11. `docs/reports/20260829-current-time-canary-review-summary.md`
12. `docs/reports/20260829-current-time-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-current-time-canary-review.json
```

---

# 28. Required gates

Set exactly:

```text
EXECUTION_TIME_KST =
...

LATEST_COMPLETED_KR_SESSION =
...

LATEST_COMPLETED_US_SESSION =
...

CURRENT_TIME_SESSION_RESOLUTION =
PASS / FAIL

CURRENT_CANARY_KR_COUNT =
2 / OTHER

CURRENT_CANARY_US_COUNT =
2 / OTHER

CURRENT_CANARY_SUBJECTS =
...

KR_MARKET_DATA_REFRESH =
PASS / PARTIAL_SAFE / FAIL

US_MARKET_DATA_REFRESH =
PASS / PARTIAL_SAFE / FAIL

NIGHT_FUTURES_CANONICAL_GATE_USED =
PASS / FAIL

NIGHT_FUTURES_CURRENT_STATE =
...

STALE_NIGHT_FUTURES_VISIBLE =
0 / NONZERO

AI_CALCULATED_TECHNICAL_FEATURE =
0 / NONZERO

BOLLINGER_ONLY_MAJOR_SR_VISIBLE =
0 / NONZERO

PROVISIONAL_BOLLINGER_AUTHORITY_LEAK =
0 / NONZERO

AMBIGUOUS_CURRENT_VS_STRUCTURE_PRICE_LABEL =
0 / NONZERO

CURRENT_003690_DECISION =
BUY / HOLD / SELL

CURRENT_000660_DECISION =
BUY / HOLD / SELL

CURRENT_GOOGL_DECISION =
BUY / HOLD / SELL

CURRENT_RXRX_DECISION =
BUY / HOLD / SELL

003690_EVIDENCE_CHANGED =
YES / NO

000660_EVIDENCE_CHANGED =
YES / NO

GOOGL_EVIDENCE_CHANGED =
YES / NO

RXRX_EVIDENCE_CHANGED =
YES / NO

UNEXPLAINED_CURRENT_DECISION_CHURN =
0 / NONZERO

BUY_SELL_POLARITY_MESSAGE_QUALITY =
PASS / FAIL

NEUTRAL_FACT_FORCED_INTO_BUY_SELL_SECTION =
0 / NONZERO

REASONING_GRADE_AS_CONFIDENCE =
0 / NONZERO

TIMING_TO_DECISION_HARD_MAPPING =
0 / NONZERO

MACD_ALONE_OWNS_BUY_SELL =
0 / NONZERO

ORDER_COMMAND_LANGUAGE =
0 / NONZERO

ORDER_SIZING_OUTPUT =
0 / NONZERO

TEST_MESSAGE_COUNT =
6 / OTHER

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

CURRENT_TIME_MESSAGE_QUALITY =
PASS / FAIL

KR_NATURAL_CANARY_CYCLES =
0 / 1 / 2 / MORE

US_NATURAL_CANARY_CYCLES =
0 / 1 / 2 / MORE

PRODUCTION_CANARY_ENABLED =
true / false

DECISION_ENGINE_STATE =
CANARY / TEST_SINK_READY / OTHER

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

CURRENT_TIME_CANARY_E2E =
PASS / PARTIAL_SAFE / FAIL
```

---

# 29. PASS rule

PASS requires:

```text
fresh KR/US market collection
fresh 4-stock evidence packets
decision continuity or explained evidence delta
polarity PASS
technical/Price Structure safety PASS
6/6 exact test messages
no production recipient
no duplicate/orphan
P0 = 0
material P1 = 0
```

Then:

```text
CURRENT_TIME_CANARY_E2E = PASS
```

This is still not a natural-cycle proof.

---

# 30. Completion response

Return:

```text
BASE_SHA = ...
OPERATING = ...

EXECUTION_TIME_KST = ...
LATEST_COMPLETED_KR_SESSION = ...
LATEST_COMPLETED_US_SESSION = ...

KR_MARKET_DATA_REFRESH = ...
US_MARKET_DATA_REFRESH = ...

NIGHT_FUTURES_CURRENT_STATE = ...

CURRENT_DECISIONS =
003690 ...
000660 ...
GOOGL ...
RXRX ...

PREVIOUS_DECISIONS =
003690 HOLD
000660 HOLD
GOOGL HOLD
RXRX SELL

EVIDENCE_DELTAS =
003690 ...
000660 ...
GOOGL ...
RXRX ...

UNEXPLAINED_CURRENT_DECISION_CHURN = 0

EXACT_CURRENT_KR_MARKET_MESSAGE =
...

EXACT_CURRENT_US_MARKET_MESSAGE =
...

EXACT_CURRENT_003690_MESSAGE =
...

EXACT_CURRENT_000660_MESSAGE =
...

EXACT_CURRENT_GOOGL_MESSAGE =
...

EXACT_CURRENT_RXRX_MESSAGE =
...

BUY_SELL_POLARITY_MESSAGE_QUALITY = ...
CURRENT_TIME_MESSAGE_QUALITY = ...

TEST_MESSAGE_COUNT = 6
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

KR_NATURAL_CANARY_CYCLES = ...
US_NATURAL_CANARY_CYCLES = ...

PRODUCTION_CANARY_ENABLED = ...
DECISION_ENGINE_STATE = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

CURRENT_TIME_CANARY_E2E =
PASS /
PARTIAL_SAFE /
FAIL

NEXT_ACTION =
REVIEW_EXACT_MESSAGES /
WAIT_FOR_NATURAL_CANARY_CYCLES /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 31. Mandatory completion ZIP

Create:

`20260829-current-time-cross-market-canary-message-e2e-test-bundle.zip`

Include:

```text
exact instruction
session resolution
fresh KR market data
fresh US market data
night-futures state
4 fresh decision evidence packets
decision-delta comparison
exact 6 test messages
test delivery evidence
message-quality review
operator summary
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

# 32. Final principle

This test asks:

```text
"If we built the canary messages right now from freshly collected data,
what would the user actually see?"
```

Use fresh evidence.
Do not force yesterday's decision.
Do not count test-sink traffic as natural proof.
Do not send anything to production.
