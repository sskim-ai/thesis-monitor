# thesis-monitor — Run-51 Frozen Live-Path Actual-Send Validation v2
## Add Night-Futures Daily / Weekly / Monthly Bars
## Add US 10Y Real-Yield Level + Observation-to-Observation Delta
## Then execute the real production decision/render/Telegram path to the dedicated TEST recipient

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-02 KST`
- Historical source run: `RUN_ID=51`
- Historical source packet: `2026-09-02-us-run-51-39a4d4eec53e`
- Canonical US regular session: `2026-09-01`
- Historical observation date: `2026-09-02 KST`
- Task class: `CONTROLLED_LIVE_PATH_ACTUAL_SEND_TEST_WITH_MARKET_MESSAGE_ENRICHMENT`
- Fresh market/company/OHLCV collection: `0`
- Production recipient send: `0`
- Dedicated test-recipient actual Telegram send: `YES`
- Historical production resend: `0`
- Production packet/claim/accepted/assessment/delivery-ledger mutation: `0`
- Scheduler timing/ownership mutation: `0`
- Production Assist: preserve `OFF`
- Decision policy retuning: `0`
- Valuation algorithm change: `0`
- Stock Price Structure change: `0`

This instruction supersedes the earlier:

```text
20260902-run51-frozen-live-path-actual-send-validation.md
```

for the actual-send proof.

---

# 1. Already repaired behavior to preserve

Preserve all accepted repairs already merged before this task:

```text
Codex natural runtime-state writable/parity repair
V2 natural CLI path repair
canonical identifier numeric-provenance repair
daily-review schema/provenance/quality convergence
CPNG/HUT packet-owned technical recovery
US-morning previous-XKRX-business-day night-futures date contract
```

At task start:

```text
git fetch origin
resolve actual origin/main
resolve operating HEAD
resolve runtime/deployed SHA
verify ancestry/clean worktrees
```

Do not branch from a stale SHA.

Hard:

```text
CODEX_RUNTIME_STATE_REPAIR_REGRESSION = 0
V2_NATURAL_PATH_REPAIR_REGRESSION = 0
DAILY_REVIEW_QUALITY_REPAIR_REGRESSION = 0
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0
CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
NIGHT_REFERENCE_DATE_REPAIR_REGRESSION = 0
```

---

# 2. Normative product behavior — contract identity vs timeframe

Do NOT confuse:

```text
futures contract month
```

with:

```text
chart/bar timeframe
```

For night futures:

```text
contract identity
= current/selected near-month contract
e.g. 202609

analysis/display timeframe
= Daily / Weekly / Monthly bars
```

The user-facing market message should use the near-month contract as identity metadata only.

The analytical content must expose:

```text
D = daily bar
W = weekly bar
M = monthly bar
```

Hard:

```text
CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME = 0
```

---

# 3. Source screenshot control

User-provided Kiwoom screenshot shows:

```text
instrument =
KOSPI200

contract =
202609

selected daily date =
2026/09/01

Daily OHLC:
Open  = 1,061.00
High  = 1,061.40
Low   = 1,031.30
Close = 1,040.50
```

The screenshot is a visual control for the `KOSPI200 202609` daily bar.

Use repository/provider frozen data as the machine authority for replay.

Required comparison:

```text
RUN51_KOSPI200_DAILY_SCREENSHOT_PARITY =
PASS / FAIL / NOT_COMPARABLE
```

Do not infer weekly/monthly values from the screenshot; it does not provide them.

---

# 4. Frozen source only

Use only the canonical frozen run-51 source/evidence artifacts.

Forbidden:

```text
fresh source monitor
fresh market-index fetch
fresh macro fetch
fresh night-futures fetch
fresh OHLCV fetch
fresh earnings/events/news
```

Required:

```text
RUN51_FROZEN_SOURCE_REUSED = PASS
FRESH_SOURCE_COLLECTION_DURING_TEST = 0
POST_RUN51_FRESH_FACT_LEAKAGE = 0
```

If the frozen packet does not contain enough historical night-futures bars to construct D/W/M safely:

use only already archived provider/raw artifacts that were part of the run-51 evidence lineage.

Do NOT call the live provider merely to fill the test.

If frozen/archived lineage is insufficient:

```text
timeframe = UNAVAILABLE
```

and stop the send gate if the required new market-message contract cannot be proven.

---

# 5. Frozen cohort

Use exact run-51 frozen stock cohort:

```text
CORZ
CPNG
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

Required:

```text
RUN51_FROZEN_COHORT_COUNT = 14
RUN51_FROZEN_COHORT_MUTATION = 0
```

---

# 6. Frozen market facts

Preserve run-51 non-night market facts exactly:

```text
SPY  -0.69%
QQQ  -1.27%
IWM  -1.14%
SOXX -2.10%
RSP  -0.82%

sector strongest:
energy +1.27%

sector weakest:
consumer discretionary -1.72%
```

Preserve all existing run-51 macro temporal roles and provenance.

Required:

```text
RUN51_NON_NIGHT_MARKET_NUMERIC_DIFF = 0
RUN51_NON_NIGHT_MARKET_SELECTION_DIFF = 0
```

Except:

```text
new real-yield delta rendering
```

which is an intentional addition using already frozen macro observations.

---

# 7. Night-futures reference-date contract

For the US morning digest:

```text
expected night-futures reference date
= latest valid XKRX business date strictly before observation_date_kst
```

Run-51:

```text
observation date = 2026-09-02
expected reference = 2026-09-01
provider date = 2026-09-01
```

Required:

```text
RUN51_EXPECTED_NIGHT_REFERENCE_DATE = 2026-09-01
RUN51_PROVIDER_NIGHT_BAS_DD = 2026-09-01
RUN51_NIGHT_DATE_MATCH_COUNT = 2
```

No regression to the old `expected=2026-09-02` behavior.

---

# 8. Night-futures instruments

Reference run-51 controls:

```text
KOSPI200 current/selected near-month
contract = A0169000 / 202609

KOSDAQ150 current/selected near-month
contract = A0669000 / 202609
```

Verify actual frozen security/contract identity.

Do not hardcode 202609 for future natural runs.

The production resolver must select the correct near-month according to the existing contract-roll policy.

Hard:

```text
NEAR_MONTH_CONTRACT_HARDCODED_TO_202609 = 0
```

---

# 9. Night-futures D/W/M data contract

For each configured night-futures instrument, construct one structured timeframe packet:

```json
{
  "instrument": "...",
  "contract": "...",
  "reference_date": "YYYY-MM-DD",
  "daily": {},
  "weekly": {},
  "monthly": {}
}
```

Use repository-native equivalent fields if available.

Each timeframe must separately carry:

```text
open
high
low
close
bar_start_date
bar_end/reference_date
finality
return/change semantics
source lineage
quality
```

No cross-timeframe value copying.

---

# 10. Daily bar semantics

For run-51:

```text
daily bar
= completed night-session bar associated with reference date 2026-09-01
```

For KOSPI200, screenshot control expects:

```text
O 1061.00
H 1061.40
L 1031.30
C 1040.50
```

Verify against frozen provider lineage.

Do not overwrite provider values merely to match the screenshot.

If provider/frozen lineage differs:
- classify the difference
- identify whether screenshot uses adjusted/unadjusted/other chart convention
- do not silently reconcile

Required:

```text
RUN51_KOSPI200_DAILY_OHLC_VALID = PASS / FAIL
RUN51_KOSDAQ150_DAILY_OHLC_VALID = PASS / FAIL
```

---

# 11. Weekly bar semantics

Weekly bar for the US morning message must be built from night-session daily bars belonging to the XKRX trading week containing the `reference_date`.

For run-51:

```text
reference date = 2026-09-01
```

This is not the end of the trading week.

Therefore the weekly bar should normally be:

```text
IN_PROGRESS
```

with aggregation from the first valid XKRX business session of that week through 2026-09-01.

Required aggregation:

```text
weekly open  = open of first included valid night daily bar
weekly high  = max(high)
weekly low   = min(low)
weekly close = close of reference-date night daily bar
```

Do not label it completed unless the XKRX week is actually complete under the configured finality/calendar contract.

Hard:

```text
IN_PROGRESS_WEEKLY_BAR_LABELED_FINAL = 0
```

---

# 12. Monthly bar semantics

Monthly bar must be built from night-session daily bars in the XKRX calendar month containing the reference date.

For run-51:

```text
reference date = 2026-09-01
```

This is the first XKRX business session in September 2026.

Therefore the monthly bar is:

```text
IN_PROGRESS
```

unless provider semantics prove otherwise.

Aggregation:

```text
monthly open  = open of first included valid night daily bar
monthly high  = max(high)
monthly low   = min(low)
monthly close = close of reference-date night daily bar
```

Hard:

```text
IN_PROGRESS_MONTHLY_BAR_LABELED_FINAL = 0
```

---

# 13. D/W/M dependency integrity

Weekly/monthly OHLC may only aggregate valid daily source bars.

Forbidden:

```text
using regular-session OHLC as night OHLC
copying the latest daily bar to create weekly/monthly without aggregation
using current quote as completed close
dropping an invalid constituent bar and still calling the aggregate complete
```

Required:

```text
NIGHT_DWM_SYNTHETIC_OHLC = 0
NIGHT_DWM_CURRENT_QUOTE_OWNS_CLOSE = 0
```

If one constituent is invalid:
- block/qualify only the affected timeframe
- do not invent replacement values

---

# 14. D/W/M return/change semantics

For each timeframe, define exactly what the displayed percentage means.

Preferred:

```text
Daily:
reference-date night close vs the existing validated comparison baseline
used by the current night-futures contract

Weekly:
weekly close vs prior completed week's close

Monthly:
monthly close vs prior completed month's close
```

If frozen lineage lacks the prior completed W/M baseline:

do NOT fabricate returns.

The message may render OHLC plus:

```text
주봉 수익률: 자료 부족
월봉 수익률: 자료 부족
```

or omit only the unavailable return metric while keeping safe OHLC.

Hard:

```text
NIGHT_DWM_RETURN_BASELINE_INVENTED = 0
```

---

# 15. User-facing night-futures market section

The market message should make the distinction clear.

Recommended repository-style structure:

```text
🌙 한국 야간선물 · 기준 09/01

• KOSPI200 202609
  - 일봉: O 1,061.00 · H 1,061.40 · L 1,031.30 · C 1,040.50 ...
  - 주봉(진행중): O ... · H ... · L ... · C ... · 주간 ...
  - 월봉(진행중): O ... · H ... · L ... · C ... · 월간 ...

• KOSDAQ150 202609
  - 일봉: ...
  - 주봉(진행중): ...
  - 월봉(진행중): ...
```

Exact typography may follow existing production style.

Do not print raw contract codes unless product style already does so.

The near-month label is identity metadata, not the analytical timeframe.

Required:

```text
NIGHT_DAILY_VISIBLE_COUNT = 2
NIGHT_WEEKLY_VISIBLE_COUNT = 2
NIGHT_MONTHLY_VISIBLE_COUNT = 2
```

If a timeframe is unavailable from frozen lineage:
the pre-send acceptance must decide whether the new contract allows an explicit `자료 부족` rendering.
Do not silently omit the requested timeframe.

---

# 16. Real-yield display contract

US market analysis must show both:

```text
current/latest safe 10Y real-yield level
and
change versus the immediately previous valid observation
```

Use the same authoritative real-yield series already used by the market packet.

Do not substitute nominal yield or breakeven.

Required structured facts:

```text
real_yield_current
real_yield_current_observation_date
real_yield_previous
real_yield_previous_observation_date
real_yield_delta_percentage_points
real_yield_delta_basis_points
```

---

# 17. Real-yield delta calculation

Calculate:

```text
delta_pp = current_yield_pct - previous_yield_pct
delta_bp = delta_pp * 100
```

Example only:

```text
1.82% vs 1.78%
→ +0.04%p
→ +4bp
```

Do not confuse:

```text
percentage change %
```

with:

```text
percentage-point change %p
```

Hard:

```text
REAL_YIELD_DELTA_RENDERED_AS_PERCENT_RETURN = 0
```

---

# 18. Real-yield observation-to-observation semantics

The delta is between:

```text
latest safe observation
and
immediately previous valid observation in the same series
```

NOT necessarily:
- same US equity session
- previous KST calendar day

This matters because the real-yield source may publish with a lag.

Required:

```text
REAL_YIELD_DELTA_OBSERVATION_PAIR_VALID = PASS
```

---

# 19. Real-yield temporal safety

If the latest safe real-yield observation date is older than the US equity session:

render the actual observation date.

Example:

```text
미 10년 실질금리 1.82% (08/31 관측)
· 직전 관측 대비 +0.04%p (+4bp)
```

Do NOT write:

```text
오늘 +4bp
```

unless the observation truly corresponds to the same target market date under the temporal contract.

Hard:

```text
STALE_REAL_YIELD_DELTA_LABELED_SAME_DAY = 0
```

---

# 20. Real-yield rounding

Use one consistent contract.

Recommended:

```text
level = 2 decimal places in %
delta_pp = 2 decimal places in %p
delta_bp = integer bp when mathematically exact after source precision;
otherwise preserve one decimal bp if needed
```

Do not create false precision beyond source precision.

Store unrounded canonical delta and separately rendered values.

Required:

```text
REAL_YIELD_ROUNDING_CONTRACT = PASS
```

---

# 21. Real-yield direction words

Direction must follow the signed delta:

```text
delta > 0 → 상승
delta < 0 → 하락
delta = 0 → 변화 없음
```

Use:

```text
+0.04%p (+4bp)
-0.03%p (-3bp)
```

with sign.

Hard:

```text
REAL_YIELD_DIRECTION_SIGN_MISMATCH = 0
```

---

# 22. Real-yield message placement

Add the real-yield line to the normal US market analysis message.

Preferred placement:

```text
시장 내부 / 시장환경
```

or the existing deterministic macro section.

Do not make stock-level AI candidates own this number.

The market packet must own:
- level
- observation date
- delta
- previous observation

Required:

```text
REAL_YIELD_FACT_PACKET_OWNED = PASS
```

---

# 23. Run-51 real-yield frozen control

Use the real-yield observations already archived with run-51.

Extract:

```text
current value/date
previous valid value/date
calculated delta_pp
calculated delta_bp
```

Do not use current-day web/provider data.

Required report:

```text
RUN51_REAL_YIELD_CURRENT = ...
RUN51_REAL_YIELD_CURRENT_DATE = ...
RUN51_REAL_YIELD_PREVIOUS = ...
RUN51_REAL_YIELD_PREVIOUS_DATE = ...
RUN51_REAL_YIELD_DELTA_PP = ...
RUN51_REAL_YIELD_DELTA_BP = ...
```

If the immediately previous valid observation is not present in the frozen/archived run-51 lineage:
- do not fetch fresh data
- classify `DELTA_UNAVAILABLE_FROZEN_SOURCE`
- fail this actual-send enrichment test rather than fabricate

---

# 24. Market numeric provenance

Both new feature groups must enter the market numeric registry:

```text
night D/W/M OHLC and returns
real-yield level and delta
```

Each rendered number must bind to:
- canonical source facts
- exact semantic type
- date/timeframe role

Required:

```text
NIGHT_DWM_NUMERIC_PROVENANCE = PASS
REAL_YIELD_DELTA_NUMERIC_PROVENANCE = PASS
MARKET_PHANTOM_NUMERIC_ERRORS = 0
```

---

# 25. Market replay before actual send

Before any Telegram send, replay the frozen run-51 market message.

Require:
- old non-night facts unchanged
- night D/W/M present
- real-yield level + delta present
- temporal labels correct
- final validator PASS

Required:

```text
RUN51_MARKET_REPLAY = PASS
MARKET_FINAL_VALIDATION = PASS
```

No test send if this fails.

---

# 26. Real production live path for stocks

For the same frozen run-51 stock evidence execute:

```text
packet-owned technical context
→ V2 prepare_context
→ production path builder
→ repaired scheduler-equivalent Codex runtime
→ actual signed-in model call
→ candidate
→ candidate validation
→ adjudication if required
→ accepted_decision_plan
→ V2 accepted renderer
→ final validator
```

Forbidden:

```text
pre-baked model response
pre-baked candidate
pre-baked accepted decision
validator bypass
```

---

# 27. V2 targets

Required:

```text
V2_CONTEXT_READY_COUNT = 14
V2_MODEL_CALL_REACHED = PASS
V2_CANDIDATE_GENERATED_COUNT = 14
CANDIDATE_VALIDATION_PASS_COUNT = 14
REQUIRED_ADJUDICATION_MISSING = 0
ACCEPTED_READY_COUNT = 14
EXPLICIT_V2_DECISION_COUNT = 14
FALLBACK_STOCK_COUNT = 0
```

No fixed BUY/HOLD/SELL distribution.

---

# 28. Technical regression

Use frozen run-51 technical context.

Reference:

```text
PARTIAL_SAFE = 14
```

Preserve:
- CPNG bad rows
- feature-scoped safety
- HUT quote vs completed close
- invalid numeric leakage 0

Required:

```text
TECHNICAL_PARTIAL_SAFE_FORCED_TO_FULL = 0
CPNG_INVALID_TECHNICAL_NUMERIC_VISIBLE_TO_V2 = 0
HUT_CURRENT_QUOTE_OWNS_COMPLETED_CLOSE = 0
```

---

# 29. Daily-review secondary path

Require:

```text
DAILY_REVIEW_QUALITY = PASS
DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED = 0
```

Do not send secondary daily-review messages separately.

---

# 30. Test execution namespace

Create a separate test execution ID.

Use the original packet read-only.

Required:

```text
RUN51_PRODUCTION_PACKET_MUTATION = 0
RUN51_PRODUCTION_CLAIM_MUTATION = 0
RUN51_PRODUCTION_DELIVERY_LEDGER_MUTATION = 0
DELIVERY_NAMESPACE = TEST
```

---

# 31. Test-recipient safety

Actual Telegram send is authorized ONLY to the existing dedicated non-production TEST recipient.

The production recipient must be structurally unavailable.

Required:

```text
PRODUCTION_RECIPIENT_RESOLUTION_DISABLED = PASS
TEST_RECIPIENT_RESOLUTION = PASS
PRODUCTION_RECIPIENT_SEND = 0
```

Never expose recipient IDs.

---

# 32. Atomic pre-send gate

Before the first actual send, require all 15 final messages ready:

```text
market = 1
stocks = 14
total = 15
```

Market message must already contain:
- night D/W/M
- real-yield level + delta

Required:

```text
PRE_SEND_ATOMIC_READINESS = PASS
TEST_EXPECTED_MESSAGE_COUNT = 15
```

If any message is not ready:

```text
ACTUAL_SEND_COUNT = 0
```

---

# 33. Real Telegram transport

Use the actual production Telegram transport adapter.

Do not mock:
- HTTP
- Telegram acknowledgement
- rate-limit handling

Only routing difference:
`dedicated TEST recipient`.

Required:

```text
REAL_TELEGRAM_TRANSPORT = PASS
```

---

# 34. Exactly-once

Required:

```text
TEST_SENT_COUNT = 15
TEST_ACKNOWLEDGED_COUNT = 15
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_UNOWNED_RETRY = 0
ACKNOWLEDGED_MESSAGE_RESEND = 0
```

If rate limited:
resume only unacknowledged remainder.

---

# 35. Exact payload

Compare per message:

```text
final validated renderer text
frozen send payload
actual outbound request
test delivery ledger
acknowledged/recorded payload if available
```

Required:

```text
TEST_LIVE_EXACT_PAYLOAD = PASS
```

Store sanitized SHA-256 per message.

---

# 36. Production-state mutation audit

Required:

```text
PRODUCTION_ACCEPTED_DECISION_MUTATION = 0
PRODUCTION_ASSESSMENT_MUTATION = 0
PRODUCTION_NOTIFICATION_STATE_MUTATION = 0
PRODUCTION_PACKET_STATE_MUTATION = 0
PRODUCTION_DELIVERY_LEDGER_MUTATION = 0
```

Test delivery must not suppress next natural send:

```text
TEST_DELIVERY_SUPPRESSES_NEXT_NATURAL_SEND = 0
```

---

# 37. Idempotency

The exact test execution ID must be idempotent.

Do not prove it by sending 15 messages twice.

Required:

```text
TEST_EXECUTION_IDEMPOTENCY = PASS
```

---

# 38. Cross-market/code regression

Before actual send require:
- focused night D/W/M tests
- real-yield delta tests
- market replay
- V2 runtime regression
- US14 production-equivalent
- KR8 production-equivalent
- full pytest
- Ruff
- git diff --check
- GitHub Actions

Reference counts only if active frozen fixtures remain unchanged.

Required:

```text
US_PRODUCTION_EQUIVALENT_V2 = PASS
KR_PRODUCTION_EQUIVALENT_V2 = PASS
```

---

# 39. Success definition

Declare:

```text
RUN51_FROZEN_LIVE_PATH_ACTUAL_SEND_V2 = PASS
```

only if:

```text
frozen run-51 data only
night reference date 2026-09-01
night D/W/M safe and visible for both instruments
KOSPI200 screenshot daily control resolved
real-yield latest safe level visible
real-yield previous-observation delta visible in %p and bp
market final validation PASS
Codex app-server PASS
actual V2 model reached
candidate 14/14
accepted 14/14
explicit V2 14/14
fallback 0
test recipient only
real Telegram transport
15/15 acknowledged
exact payload PASS
no production-state mutation
no fresh-data leakage
```

This remains a controlled live-path proof, not the final natural-scheduler US LIVE_PASS.

---

# 40. Required reports

Create at minimum:

1. `docs/reports/20260902-run51-v2-frozen-source-lock.md`
2. `docs/reports/20260902-night-dwm-contract.md`
3. `docs/reports/20260902-run51-kospi200-screenshot-daily-control.md`
4. `docs/reports/20260902-run51-night-daily-bars.md`
5. `docs/reports/20260902-run51-night-weekly-bars.md`
6. `docs/reports/20260902-run51-night-monthly-bars.md`
7. `docs/reports/20260902-run51-night-dwm-return-provenance.md`
8. `docs/reports/20260902-real-yield-delta-contract.md`
9. `docs/reports/20260902-run51-real-yield-observation-pair.md`
10. `docs/reports/20260902-run51-market-message-enriched-replay.md`
11. `docs/reports/20260902-run51-market-numeric-provenance.md`
12. `docs/reports/20260902-run51-live-path-runtime-lineage.md`
13. `docs/reports/20260902-run51-live-path-v2-model-candidates.md`
14. `docs/reports/20260902-run51-live-path-adjudication-accepted.md`
15. `docs/reports/20260902-run51-live-path-renderer-validator.md`
16. `docs/reports/20260902-run51-live-path-pre-send-gate.md`
17. `docs/reports/20260902-run51-live-path-test-recipient-routing.md`
18. `docs/reports/20260902-run51-live-path-actual-send-receipts.md`
19. `docs/reports/20260902-run51-live-path-exact-payload.md`
20. `docs/reports/20260902-run51-live-path-production-mutation-audit.md`
21. `docs/reports/20260902-run51-live-path-idempotency.md`
22. `docs/reports/20260902-run51-frozen-live-path-actual-send-v2-proof.md`
23. `docs/reports/20260902-run51-frozen-live-path-v2-artifact-index.md`

Machine-readable:

```text
docs/reports/20260902-run51-night-dwm.json
docs/reports/20260902-run51-real-yield-delta.json
docs/reports/20260902-run51-market-enriched.json
docs/reports/20260902-run51-live-path-stage-matrix.json
docs/reports/20260902-run51-live-path-delivery.json
docs/reports/20260902-run51-live-path-v2-proof.json
```

---

# 41. Required gates

Set exactly:

```text
BASE_SHA =
...

ORIGIN_MAIN =
...

OPERATING =
...

RUNTIME_CODE_SHA =
...

RUN51_SOURCE_PACKET_ID =
2026-09-02-us-run-51-39a4d4eec53e

TEST_EXECUTION_ID =
...

RUN51_FROZEN_SOURCE_REUSED =
PASS / FAIL

FRESH_SOURCE_COLLECTION_DURING_TEST =
0 / NONZERO

POST_RUN51_FRESH_FACT_LEAKAGE =
0 / NONZERO

RUN51_FROZEN_COHORT_COUNT =
14 / OTHER

RUN51_EXPECTED_NIGHT_REFERENCE_DATE =
2026-09-01 / OTHER

RUN51_PROVIDER_NIGHT_BAS_DD =
2026-09-01 / OTHER

RUN51_NIGHT_DATE_MATCH_COUNT =
2 / OTHER

CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME =
0 / NONZERO

NEAR_MONTH_CONTRACT_HARDCODED_TO_202609 =
0 / NONZERO

RUN51_KOSPI200_DAILY_SCREENSHOT_PARITY =
PASS / FAIL / NOT_COMPARABLE

RUN51_KOSPI200_DAILY_OHLC_VALID =
PASS / FAIL

RUN51_KOSDAQ150_DAILY_OHLC_VALID =
PASS / FAIL

NIGHT_DAILY_VISIBLE_COUNT =
2 / OTHER

NIGHT_WEEKLY_VISIBLE_COUNT =
2 / OTHER

NIGHT_MONTHLY_VISIBLE_COUNT =
2 / OTHER

IN_PROGRESS_WEEKLY_BAR_LABELED_FINAL =
0 / NONZERO

IN_PROGRESS_MONTHLY_BAR_LABELED_FINAL =
0 / NONZERO

NIGHT_DWM_SYNTHETIC_OHLC =
0 / NONZERO

NIGHT_DWM_CURRENT_QUOTE_OWNS_CLOSE =
0 / NONZERO

NIGHT_DWM_RETURN_BASELINE_INVENTED =
0 / NONZERO

NIGHT_DWM_NUMERIC_PROVENANCE =
PASS / FAIL

REAL_YIELD_DELTA_OBSERVATION_PAIR_VALID =
PASS / FAIL

RUN51_REAL_YIELD_CURRENT =
...

RUN51_REAL_YIELD_CURRENT_DATE =
...

RUN51_REAL_YIELD_PREVIOUS =
...

RUN51_REAL_YIELD_PREVIOUS_DATE =
...

RUN51_REAL_YIELD_DELTA_PP =
...

RUN51_REAL_YIELD_DELTA_BP =
...

REAL_YIELD_DELTA_RENDERED_AS_PERCENT_RETURN =
0 / NONZERO

STALE_REAL_YIELD_DELTA_LABELED_SAME_DAY =
0 / NONZERO

REAL_YIELD_ROUNDING_CONTRACT =
PASS / FAIL

REAL_YIELD_DIRECTION_SIGN_MISMATCH =
0 / NONZERO

REAL_YIELD_FACT_PACKET_OWNED =
PASS / FAIL

REAL_YIELD_DELTA_NUMERIC_PROVENANCE =
PASS / FAIL

MARKET_PHANTOM_NUMERIC_ERRORS =
0 / NONZERO

RUN51_NON_NIGHT_MARKET_NUMERIC_DIFF =
0 / NONZERO

RUN51_NON_NIGHT_MARKET_SELECTION_DIFF =
0 / NONZERO

RUN51_MARKET_REPLAY =
PASS / FAIL

MARKET_FINAL_VALIDATION =
PASS / FAIL

CODEX_RUNTIME_STATE_PREFLIGHT =
PASS / FAIL

CODEX_APP_SERVER_INITIALIZATION =
PASS / FAIL

V2_CONTEXT_READY_COUNT =
14 / OTHER

V2_MODEL_CALL_REACHED =
PASS / FAIL

V2_CANDIDATE_GENERATED_COUNT =
14 / OTHER

CANDIDATE_VALIDATION_PASS_COUNT =
14 / OTHER

REQUIRED_ADJUDICATION_MISSING =
0 / NONZERO

ACCEPTED_READY_COUNT =
14 / OTHER

EXPLICIT_V2_DECISION_COUNT =
14 / OTHER

FALLBACK_STOCK_COUNT =
0 / NONZERO

DAILY_REVIEW_QUALITY =
PASS / FAIL

DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED =
0 / NONZERO

STOCK_FINAL_VALIDATION_PASS_COUNT =
14 / OTHER

FINAL_VALIDATION_REJECT_COUNT =
0 / NONZERO

PRE_SEND_ATOMIC_READINESS =
PASS / FAIL

TEST_EXPECTED_MESSAGE_COUNT =
15 / OTHER

PRODUCTION_RECIPIENT_RESOLUTION_DISABLED =
PASS / FAIL

TEST_RECIPIENT_RESOLUTION =
PASS / FAIL

REAL_TELEGRAM_TRANSPORT =
PASS / FAIL

TEST_SENT_COUNT =
15 / OTHER

TEST_ACKNOWLEDGED_COUNT =
15 / OTHER

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_UNOWNED_RETRY =
0 / NONZERO

ACKNOWLEDGED_MESSAGE_RESEND =
0 / NONZERO

TEST_LIVE_EXACT_PAYLOAD =
PASS / FAIL

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_ACCEPTED_DECISION_MUTATION =
0 / NONZERO

PRODUCTION_ASSESSMENT_MUTATION =
0 / NONZERO

PRODUCTION_NOTIFICATION_STATE_MUTATION =
0 / NONZERO

PRODUCTION_PACKET_STATE_MUTATION =
0 / NONZERO

PRODUCTION_DELIVERY_LEDGER_MUTATION =
0 / NONZERO

DELIVERY_NAMESPACE =
TEST / OTHER

TEST_DELIVERY_SUPPRESSES_NEXT_NATURAL_SEND =
0 / NONZERO

TEST_EXECUTION_IDEMPOTENCY =
PASS / FAIL

US_PRODUCTION_EQUIVALENT_V2 =
PASS / FAIL

KR_PRODUCTION_EQUIVALENT_V2 =
PASS / FAIL

CODEX_RUNTIME_STATE_REPAIR_REGRESSION =
0 / NONZERO

V2_NATURAL_PATH_REPAIR_REGRESSION =
0 / NONZERO

DAILY_REVIEW_QUALITY_REPAIR_REGRESSION =
0 / NONZERO

PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION =
0 / NONZERO

CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION =
0 / NONZERO

NIGHT_REFERENCE_DATE_REPAIR_REGRESSION =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OPEN_P2 =
...

RUN51_FROZEN_LIVE_PATH_ACTUAL_SEND_V2 =
PASS / FAIL
```

---

# 42. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

RUN51_SOURCE_PACKET_ID =
2026-09-02-us-run-51-39a4d4eec53e

TEST_EXECUTION_ID = ...

RUN51_FROZEN_SOURCE_REUSED = ...
FRESH_SOURCE_COLLECTION_DURING_TEST = 0

NIGHT_FUTURES =
reference date ...
KOSPI200 contract ...
KOSPI200 daily ...
KOSPI200 weekly ...
KOSPI200 monthly ...
KOSDAQ150 contract ...
KOSDAQ150 daily ...
KOSDAQ150 weekly ...
KOSDAQ150 monthly ...

RUN51_KOSPI200_DAILY_SCREENSHOT_PARITY = ...

REAL_YIELD =
current ...
current date ...
previous ...
previous date ...
delta %p ...
delta bp ...
rendered line ...

MARKET =
non-night parity ...
market validation ...

V2 =
context ...
app-server ...
model ...
candidate ...
candidate validation ...
adjudication ...
accepted ...
BUY/HOLD/SELL distribution ...

DECISIONS =
CORZ ...
CPNG ...
CRCL ...
GOOGL ...
HUT ...
IBM ...
MU ...
RXRX ...
SKHY ...
SNDK ...
TSLA ...
TSM ...
WRD ...
WULF ...

RENDERER =
explicit V2 ...
fallback ...

PRE_SEND_ATOMIC_READINESS = ...

DELIVERY =
expected 15
sent ...
acknowledged ...
duplicate ...
orphan ...
unowned retry ...
exact payload ...

PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_STATE_MUTATIONS = 0
DELIVERY_NAMESPACE = TEST

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

RUN51_FROZEN_LIVE_PATH_ACTUAL_SEND_V2 =
PASS / FAIL

NATURAL_US_LIVE_STATUS =
STILL_AWAITING_NEXT_SCHEDULED_RUN

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_LIVE /
BOUNDED_REPAIR /
ROLLBACK_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

# 43. Mandatory completion ZIP

Create:

`20260902-run51-frozen-live-path-actual-send-with-night-dwm-real-yield-delta-bundle.zip`

Include:
- exact master instruction
- all track instructions
- frozen source lock
- user screenshot control report (no need to redistribute original image unless repo policy permits)
- night D/W/M facts and aggregation provenance
- real-yield observation pair/delta proof
- enriched market replay
- actual model/candidate/adjudication/accepted traces
- exact validated market + 14 stock messages
- test-recipient routing proof
- actual Telegram send receipts
- exact payload hashes
- production mutation audit
- idempotency
- CI/main/runtime lineage
- machine-readable JSON
- artifact index

Exclude:
- Telegram recipient IDs
- tokens/auth headers
- Codex credentials/state DB contents
- account identifiers
- secrets
- hidden chain-of-thought

Compute SHA-256.

---

# 44. Final principle

This v2 actual-send proof must demonstrate:

```text
same frozen run-51 data
→ night futures using near-month contract identity
→ Daily / Weekly / Monthly bar context
→ US real-yield level + previous-observation change in %p and bp
→ packet-owned market message
→ actual V2 model
→ accepted decision
→ explicit V2 stock messages
→ final validators
→ real Telegram transport
→ dedicated TEST recipient
→ exactly 15/15
```

Do not confuse contract month with monthly timeframe.

For 2026-09-02 morning:

```text
night reference date = 2026-09-01
```

For real yield:

```text
show the level
+
show how many percentage points / basis points it moved
versus the immediately previous valid observation
+
show observation date when temporal lag exists
```

No fresh data.
No pre-baked AI result.
No fallback to claim success.
No production recipient.
No production-state mutation.
