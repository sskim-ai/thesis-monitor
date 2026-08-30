# thesis-monitor — US Market Internals + Decision Korean Localization + Identity Cleanup

## Purpose

Final bounded cleanup before natural canary observation.

Close only these three remaining product-quality items:

1. Add material SOXX/IWM relative signals to the US market-internals section.
2. Render the US decision block consistently in Korean.
3. Correct ticker `003690` identity to `코리안리` everywhere current/mutable.

Do not redesign the decision engine, Price Structure, valuation, market-data acquisition, or canary scope.

---

## 0. Baseline

Repository: `sskim-ai/thesis-monitor`

Latest source-supported operating lineage before this cleanup:

`0f96a6464769cd1ca01ff5d2da632d2759ee32d9`

Current canary scope:

- KR: `003690`, `000660`
- US: `GOOGL`, `RXRX`

Current accepted decisions:

- `003690 HOLD`
- `000660 HOLD`
- `GOOGL HOLD`
- `RXRX SELL`

Current product observations from the latest current-time E2E:

- SPY `-0.23%`
- QQQ `-0.65%`
- IWM `-1.35%`
- SOXX `-3.20%`
- RSP `-0.34%`

Observed issues:

- US market message showed RSP and sector strong/weak, but omitted material SOXX and IWM relative weakness.
- GOOGL/RXRX decision reasoning was mixed English/Korean.
- `003690` was previously mislabeled in conversational/canary documentation as DB손해보험; canonical identity is `코리안리`.

Before work:

- `git fetch origin`
- confirm clean worktrees
- resolve actual latest safe `origin/main`
- resolve actual operating checkout
- use the SHA above or a safe linear descendant
- read current natural-canary counters from runtime; do not assume they are still 0/2.

---

## 1. Hard scope boundaries

Do NOT change:

- BUY/HOLD/SELL taxonomy
- current accepted decisions on identical evidence
- confidence/timing taxonomy
- decision polarity contract
- canary membership
- Price Structure numerics
- completed/provisional Bollinger numerics
- valuation numerics
- KR market-message logic
- night-futures canonical contract

Hard gates:

- `DECISION_OUTPUT_DIFF_FROM_SAME_EVIDENCE = 0`
- `PRICE_STRUCTURE_NUMERIC_DIFF = 0`
- `VALUATION_NUMERIC_DIFF = 0`
- `CANARY_SCOPE_DIFF = 0`

---

## 2. US market internals — relative-signal selection

Preserve the major-index block:

- SPY
- QQQ
- IWM
- SOXX
- RSP

Backend, not AI, computes relative spreads:

- SOXX vs SPY
- IWM vs SPY
- RSP vs SPY
- QQQ vs SPY

AI must not calculate the spread itself.

Hard:

`AI_CALCULATED_RELATIVE_SPREAD = 0`

Use the repository-native materiality/relevance policy.

Candidate semantic states may be repository-native equivalents of:

- `RELATIVE_STRENGTH`
- `RELATIVE_WEAKNESS`
- `ROUGHLY_IN_LINE`
- `NOT_MATERIAL`

Do not print every comparison every day.

### SOXX

If SOXX materially diverges from SPY, render one concise semiconductor interpretation.

Example only:

`• 반도체 SOXX가 SPY를 크게 밑돌아 반도체 상대약세가 두드러졌습니다.`

Hard:

`MATERIAL_SOXX_RELATIVE_SIGNAL_OMITTED = 0`

### IWM

If IWM materially diverges from SPY, render one concise small-cap/risk-appetite interpretation.

Example only:

`• 소형주 IWM도 SPY보다 약해 위험선호는 제한적이었습니다.`

Hard:

`MATERIAL_IWM_RELATIVE_SIGNAL_OMITTED = 0`

### RSP

Preserve RSP as equal-weight participation/style proxy.

Hard:

`RSP_AS_EXCHANGE_BREADTH = 0`

### Density

Target user-facing budget:

- participation/style: 1–2 lines
- semiconductor: 0–1 line
- sector strong/weak: current production policy

Hard:

- `US_MARKET_INTERNALS_OVERLOADED = 0`
- `US_SECTOR_SELECTION_POLICY_DIFF = 0`
- `NIGHT_FUTURES_POLICY_DIFF = 0`

---

## 3. US decision-block Korean localization

All user-facing US decision prose should be Korean by default.

Localize:

- 판단
- BUY 쪽 근거
- SELL 쪽 근거
- 핵심 Unknown / 판단 제한
- 상향 조건
- 하향 조건
- 신규 관찰자 관점
- 기존 보유자 관점

Canonical tickers, framework names, and unavoidable proper nouns may remain English.

Preferred flow:

`structured decision plan → Korean renderer/templates → validator`

Do NOT translate a final free-form English answer afterward and treat that translation as the source of truth.

Hard:

`POSTHOC_FREEFORM_TRANSLATION_AS_SOURCE_OF_TRUTH = 0`

Localization must not alter:

- decision
- confidence
- horizon
- timing
- bullish evidence refs
- bearish evidence refs
- unknown refs
- upgrade/downgrade conditions
- numeric bindings

Hard:

- `LOCALIZATION_CHANGED_DECISION_SEMANTICS = 0`
- `LOCALIZATION_NUMERIC_BINDING_MISMATCH = 0`

### GOOGL control

Current accepted decision: `HOLD`.

After localization, BUY-side content must remain genuinely bullish and SELL-side content genuinely bearish under the existing polarity contract.

Hard:

`GOOGL_KOREAN_DECISION_RENDER = PASS`

### RXRX control

Current accepted decision: `SELL`.

After localization, bullish optionality belongs in BUY-side and unproven economics / losses / cash burn / dilution risk belong in SELL-side where supported.

Hard:

`RXRX_KOREAN_DECISION_RENDER = PASS`

Preserve:

`BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS`

Core labels must not remain mixed-language:

`US_DECISION_MIXED_LANGUAGE_CORE_FIELDS = 0`

No imperative trading language:

- `ORDER_COMMAND_LANGUAGE = 0`
- `ORDER_SIZING_OUTPUT = 0`

---

## 4. 003690 identity cleanup

Canonical identity:

- ticker: `003690`
- company_name: `코리안리`

Audit current mutable files/config/report fixtures/canary metadata for incorrect names such as DB손해보험 / DB Insurance attached to `003690`.

Use the canonical company/watchlist identity as source of truth.

Do not implement a renderer-only string replacement.

Hard:

- `TICKER_003690_IDENTITY = 코리안리`
- `003690_RENDERER_ONLY_NAME_PATCH = 0`
- `003690_IDENTITY_REGRESSION = PASS`

For immutable historical evidence, prefer an errata/correction report rather than rewriting historical artifacts.

Current message/header/canary metadata must show:

`코리안리(003690)`

---

## 5. Same-evidence decision preservation

Using identical canonical decision packets, cleanup must preserve:

- `003690 HOLD`
- `000660 HOLD`
- `GOOGL HOLD`
- `RXRX SELL`

Hard:

`CLEANUP_CHANGED_CANARY_DECISION = 0`

If fresh evidence later changes, the existing decision-delta contract applies.

---

## 6. Test-sink regression

Use the dedicated non-production test sink.

Send exactly 5 current messages:

1. US market
2. 003690
3. 000660
4. GOOGL
5. RXRX

No production recipient.

Require:

- `TEST_MESSAGE_COUNT = 5`
- `TEST_EXACT_PAYLOAD_MATCH = PASS`
- `TEST_DUPLICATE = 0`
- `TEST_ORPHAN = 0`
- `TEST_PRODUCTION_RECIPIENT_SEND = 0`
- `PRODUCTION_DELIVERY_INTENT_CREATED = 0`

### US market checks

Verify:

- major index block intact
- RSP participation semantics intact
- material SOXX signal shown when warranted
- material IWM signal shown when warranted
- sector policy unchanged
- night-futures safe display/omission
- macro temporal safety

Gate:

`US_MARKET_INTERNALS_MESSAGE_QUALITY = PASS`

### Canary stock checks

Verify:

- decision unchanged on same evidence
- Korean decision prose
- correct BUY/SELL polarity
- Price Structure unchanged
- valuation unchanged
- price labels unchanged
- no order-command language

Gate:

`CANARY_STOCK_MESSAGE_QUALITY = PASS`

---

## 7. Natural-canary counters

This cleanup/test must not count as natural proof.

Read counters before and after.

Hard:

`TEST_INCREMENTED_NATURAL_CANARY_COUNTER = 0`

After PASS, preserve/re-arm the same exact canary scope.

No expansion.

---

## 8. Stop conditions

STOP / do not re-arm if any of these occurs:

- unexpected decision change
- polarity regression
- numeric binding change
- 003690 canonical identity conflict
- sector policy change
- Price Structure or valuation diff
- test-sink failure
- new P0/material P1

---

## 9. Required reports

Create:

1. `docs/reports/20260830-us-market-relative-signal-selection.md`
2. `docs/reports/20260830-soxx-iwm-materiality-controls.md`
3. `docs/reports/20260830-us-decision-korean-localization-contract.md`
4. `docs/reports/20260830-googl-korean-decision-control.md`
5. `docs/reports/20260830-rxrx-korean-decision-control.md`
6. `docs/reports/20260830-003690-identity-correction.md`
7. `docs/reports/20260830-current-canary-cleanup-regression.md`
8. `docs/reports/20260830-cleanup-test-sink.md`
9. `docs/reports/20260830-cleanup-message-quality.md`
10. `docs/reports/20260830-cleanup-readiness.md`
11. `docs/reports/20260830-cleanup-artifact-index.md`

Machine-readable:

`docs/reports/20260830-cleanup-readiness.json`

---

## 10. Required gates

Set exactly:

- `AI_CALCULATED_RELATIVE_SPREAD = 0 / NONZERO`
- `MATERIAL_SOXX_RELATIVE_SIGNAL_OMITTED = 0 / NONZERO`
- `MATERIAL_IWM_RELATIVE_SIGNAL_OMITTED = 0 / NONZERO`
- `RSP_AS_EXCHANGE_BREADTH = 0 / NONZERO`
- `US_MARKET_INTERNALS_OVERLOADED = 0 / NONZERO`
- `US_SECTOR_SELECTION_POLICY_DIFF = 0 / NONZERO`
- `NIGHT_FUTURES_POLICY_DIFF = 0 / NONZERO`
- `POSTHOC_FREEFORM_TRANSLATION_AS_SOURCE_OF_TRUTH = 0 / NONZERO`
- `LOCALIZATION_CHANGED_DECISION_SEMANTICS = 0 / NONZERO`
- `LOCALIZATION_NUMERIC_BINDING_MISMATCH = 0 / NONZERO`
- `GOOGL_KOREAN_DECISION_RENDER = PASS / FAIL`
- `RXRX_KOREAN_DECISION_RENDER = PASS / FAIL`
- `BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS / FAIL`
- `US_DECISION_MIXED_LANGUAGE_CORE_FIELDS = 0 / NONZERO`
- `ORDER_COMMAND_LANGUAGE = 0 / NONZERO`
- `ORDER_SIZING_OUTPUT = 0 / NONZERO`
- `TICKER_003690_IDENTITY = 코리안리 / OTHER`
- `003690_RENDERER_ONLY_NAME_PATCH = 0 / NONZERO`
- `003690_IDENTITY_REGRESSION = PASS / FAIL`
- `CLEANUP_CHANGED_CANARY_DECISION = 0 / NONZERO`
- `CANARY_SCOPE_DIFF = 0 / NONZERO`
- `NON_CANARY_DECISION_BLOCK_VISIBLE = 0 / NONZERO`
- `TEST_INCREMENTED_NATURAL_CANARY_COUNTER = 0 / NONZERO`
- `DECISION_OUTPUT_DIFF_FROM_SAME_EVIDENCE = 0 / NONZERO`
- `PRICE_STRUCTURE_NUMERIC_DIFF = 0 / NONZERO`
- `VALUATION_NUMERIC_DIFF = 0 / NONZERO`
- `TEST_MESSAGE_COUNT = 5 / OTHER`
- `TEST_EXACT_PAYLOAD_MATCH = PASS / FAIL`
- `TEST_DUPLICATE = 0 / NONZERO`
- `TEST_ORPHAN = 0 / NONZERO`
- `TEST_PRODUCTION_RECIPIENT_SEND = 0 / NONZERO`
- `PRODUCTION_DELIVERY_INTENT_CREATED = 0 / NONZERO`
- `US_MARKET_INTERNALS_MESSAGE_QUALITY = PASS / FAIL`
- `CANARY_STOCK_MESSAGE_QUALITY = PASS / FAIL`
- `DECISION_ENGINE_STATE = CANARY / TEST_SINK_READY / OTHER`
- `PRODUCTION_CANARY_ENABLED = true / false`
- `OPEN_P0 = ...`
- `OPEN_MATERIAL_P1 = ...`
- `FINAL_CLEANUP = REARMED_AWAITING_NATURAL_PROOF / FAIL`

---

## 11. PASS rule

Require:

- material SOXX/IWM signals are no longer omitted when warranted
- US market message remains concise
- US decision prose is consistently Korean
- GOOGL/RXRX polarity remains correct
- `003690` identity is `코리안리`
- same-evidence decisions unchanged
- Price Structure/valuation unchanged
- 5/5 exact test-sink PASS
- production recipient 0
- P0/P1 = 0/0

Then:

`FINAL_CLEANUP = REARMED_AWAITING_NATURAL_PROOF`

---

## 12. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

CURRENT_US_SESSION = ...

SOXX_RELATIVE_SIGNAL = ...
IWM_RELATIVE_SIGNAL = ...
RSP_PARTICIPATION_SIGNAL = ...

EXACT_US_MARKET_MESSAGE =
...

GOOGL_KOREAN_DECISION_RENDER = ...
RXRX_KOREAN_DECISION_RENDER = ...

EXACT_GOOGL_DECISION_BLOCK =
...

EXACT_RXRX_DECISION_BLOCK =
...

TICKER_003690_IDENTITY = 코리안리
003690_IDENTITY_REGRESSION = ...

CURRENT_DECISIONS =
003690 ...
000660 ...
GOOGL ...
RXRX ...

CLEANUP_CHANGED_CANARY_DECISION = 0
CANARY_SCOPE_DIFF = 0

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0

TEST_MESSAGE_COUNT = 5
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

US_MARKET_INTERNALS_MESSAGE_QUALITY = ...
CANARY_STOCK_MESSAGE_QUALITY = ...

DECISION_ENGINE_STATE = CANARY
PRODUCTION_CANARY_ENABLED = true

KR_NATURAL_CANARY_CYCLES = ...
US_NATURAL_CANARY_CYCLES = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

FINAL_CLEANUP =
REARMED_AWAITING_NATURAL_PROOF /
FAIL

NEXT_ACTION =
WAIT_FOR_NATURAL_CANARY_CYCLES /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

## 13. Final principle

This is cleanup, not redesign.

Make the US market message more informative, make the US decision prose consistently Korean, and make ticker `003690` correct everywhere.

Then leave the bounded canary unchanged and wait for natural proof.
