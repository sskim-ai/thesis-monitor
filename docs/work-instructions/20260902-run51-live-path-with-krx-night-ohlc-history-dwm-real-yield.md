# thesis-monitor — Run-51 Live-Path Validation with KRX Night OHLC History
## Official KRX NIGHT Daily OHLC Collector
## Same-Contract Daily / Weekly / Monthly Aggregation
## US 10Y Real-Yield Level + Observation Delta
## Real V2 Production Path + Dedicated TEST Telegram Send

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-02 KST`
- Historical source run: `RUN_ID=51`
- Historical source packet: `2026-09-02-us-run-51-39a4d4eec53e`
- Canonical US regular session: `2026-09-01`
- Historical US-morning observation date: `2026-09-02 KST`
- Task class: `SOURCE_CONTRACT_ENRICHMENT + CONTROLLED_LIVE_PATH_ACTUAL_SEND`
- Production Assist: preserve `OFF`
- Automated trading/order sizing: `0`
- Production recipient send: `0`
- Dedicated TEST recipient actual Telegram send: `YES`
- Historical production resend: `0`
- Production packet/claim/accepted/assessment/delivery mutation: `0`
- Decision-policy retuning: `0`
- Valuation algorithm change: `0`
- Stock Price Structure change: `0`
- Scheduler timing/ownership change: `0`

This instruction supersedes:

```text
20260902-run51-frozen-live-path-actual-send-with-night-dwm-real-yield-delta.md
```

for the controlled actual-send proof.

---

# 1. Preserve all already-passing repairs

At task start:

```text
git fetch origin
resolve latest origin/main
resolve operating HEAD
resolve runtime/deployed SHA
verify clean worktrees
```

Verify ancestry contains:

```text
Codex natural runtime-state writable/parity repair
V2 natural CLI absolute-path repair
canonical product/model identifier numeric-provenance repair
daily-review schema/provenance/message-quality repair
CPNG/HUT packet-owned technical-recovery repair
US-morning previous-XKRX-business-day night-reference repair
```

Hard:

```text
CODEX_RUNTIME_STATE_REPAIR_REGRESSION = 0
V2_NATURAL_PATH_REPAIR_REGRESSION = 0
DAILY_REVIEW_QUALITY_REPAIR_REGRESSION = 0
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0
CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
NIGHT_REFERENCE_DATE_REPAIR_REGRESSION = 0
```

Do not branch from a stale pre-repair SHA.

---

# 2. Product objective

The user wants the US morning market message to distinguish:

```text
which futures contract?
```

from:

```text
what chart timeframe?
```

Therefore:

```text
near-month contract
= identity

Daily / Weekly / Monthly
= analytical bar timeframes
```

The target source architecture:

```text
official KRX NIGHT daily OHLC
→ immutable/raw receipt
→ normalized daily-bar history store
→ same-contract D/W/M aggregator
→ packet-owned market facts
→ deterministic market renderer
```

Hard:

```text
CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME = 0
```

---

# 3. KRX source verification before implementation

Locate the existing KRX night-futures source path used by the repository.

Verify the actual endpoint/service and schema.

Reference endpoint family currently discussed:

```text
fut_bydd_trd
```

Do not rely solely on this instruction's label.

From the actual KRX response/schema, prove the daily NIGHT row exposes or can safely map:

```text
trading/reference date
instrument/product
contract/maturity
market/session = NIGHT
open
high
low
close
volume if available
official change/change-rate fields if available
```

If KRX does not provide one of these fields:
- record it
- do not fabricate
- adapt the contract to the real schema

Required:

```text
KRX_NIGHT_DAILY_OHLC_SCHEMA =
PROVEN / FAIL
```

---

# 4. KRX field mapping

Create one explicit mapping document.

Expected semantic fields:

```text
date
instrument_root
contract
session
open
high
low
close
volume
official_change
official_change_pct
source_row_identity
```

If KRX native fields include names such as:

```text
TDD_OPNPRC
TDD_HGPRC
TDD_LWPRC
TDD_CLSPRC
```

verify them from the actual schema before binding.

Do not guess column semantics from names alone.

Hard:

```text
UNVERIFIED_KRX_FIELD_SEMANTICS_USED = 0
```

---

# 5. Raw KRX response preservation

Every successful daily NIGHT acquisition must preserve immutable/raw provenance:

```text
request identity
response timestamp
reference date
source contract
raw response SHA-256
normalized row fingerprint
source/provider version if available
```

Do not rewrite the raw provider row.

Required:

```text
KRX_RAW_RESPONSE_PRESERVED = PASS
RAW_KRX_OHLC_REWRITTEN = 0
```

---

# 6. Normalized daily night-bar identity

Store normalized daily bars keyed by a stable identity such as:

```text
instrument_root
contract
reference_date
session = NIGHT
```

Required fields:

```text
open
high
low
close
bar_finality
quality
source_raw_sha
normalized_fingerprint
```

Do not key only by instrument root; different contract months must not overwrite each other.

Hard:

```text
CONTRACT_IDENTITY_COLLISION = 0
```

---

# 7. Daily OHLC validation

Before storing a bar as valid:

```text
open/high/low/close finite
positive when required by product convention
low <= open <= high
low <= close <= high
low <= high
date valid
contract valid
instrument valid
session NIGHT
```

If official exchange semantics allow zero/missing special cases:
handle them explicitly.

Do not "repair" malformed OHLC by:

```text
high = max(open, close, high)
low = min(...)
swapping fields
clipping
interpolation
copying another session
```

Hard:

```text
SYNTHETIC_KRX_OHLC_REPAIR = 0
```

---

# 8. Daily bar finality

Separate:

```text
row available
```

from:

```text
row final/completed
```

A daily NIGHT bar enters D/W/M aggregation only when final under the validated KRX/provider contract.

Keep the already-repaired US-morning reference rule:

```text
observation on KST date D
→ expected night reference date =
  latest valid XKRX business date strictly before D
```

Run-51:

```text
2026-09-02 morning
→ expected 2026-09-01
```

Required:

```text
RUN51_EXPECTED_NIGHT_REFERENCE_DATE = 2026-09-01
```

---

# 9. Run-51 KOSPI200 screenshot control

User-provided Kiwoom screenshot is a visual cross-check.

Visible control:

```text
instrument = KOSPI200
contract = 202609
date = 2026/09/01

Open  = 1,061.00
High  = 1,061.40
Low   = 1,031.30
Close = 1,040.50
```

Compare the normalized KRX NIGHT daily bar against this screenshot.

Set:

```text
RUN51_KOSPI200_DAILY_SCREENSHOT_PARITY =
PASS /
FAIL /
NOT_COMPARABLE
```

If mismatch:
- do not force KRX to match screenshot
- determine whether the screenshot and KRX rows use different session/adjustment/chart conventions
- document exact difference

The machine authority remains the verified KRX source contract.

---

# 10. KOSDAQ150 daily control

Build the equivalent run-51 KOSDAQ150 NIGHT daily bar from KRX source lineage.

Required:

```text
RUN51_KOSDAQ150_DAILY_OHLC_VALID = PASS
```

Do not infer its OHLC from the previously rendered close/change only.

---

# 11. Historical daily-bar store

Production going forward must retain enough same-contract KRX NIGHT daily history to construct:

```text
current daily
current weekly
current monthly
prior completed weekly close
prior completed monthly close
```

Use a bounded retention appropriate for these features.

Do not fetch the full exchange history every morning.

Preferred:

```text
incremental acquisition
+
bounded repair/backfill for missing dates
```

Required:

```text
KRX_NIGHT_HISTORY_INCREMENTAL = PASS
```

---

# 12. Historical backfill policy

For implementation/testing, first use already archived KRX raw/history artifacts.

If run-51 does not contain enough constituent daily NIGHT rows to form the requested W/M bars:

a bounded KRX historical backfill is allowed ONLY under these conditions:

```text
TEST/HISTORICAL namespace only
requested dates <= run-51 evidence cutoff
no date after 2026-09-01 for the run-51 replay
same official KRX source
raw responses preserved
backfill clearly labeled as HISTORICAL_BACKFILL
production run-51 packet remains immutable
```

This backfill is:

```text
not original run-51 evidence
```

and must be disclosed separately.

Hard:

```text
POST_CUTOFF_MARKET_DATA_USED_IN_RUN51_REPLAY = 0
PRODUCTION_RUN51_PACKET_BACKFILLED_IN_PLACE = 0
```

If the user-facing controlled test requires true original-frozen-only evidence:
prefer archived data and report any backfill separately.

---

# 13. Missing-business-day reconciliation

Use the XKRX calendar to determine which daily NIGHT rows are expected.

For each expected XKRX business date in the requested aggregation period:

```text
expected?
row present?
row final?
row valid?
```

Do not treat:
- weekend
- XKRX holiday

as missing bars.

Required:

```text
KRX_NIGHT_HISTORY_CALENDAR_RECONCILIATION = PASS
```

---

# 14. Near-month selection

Use the repository's actual near-month/roll policy.

For every reference date, resolve:

```text
selected contract
```

Do not hardcode:

```text
202609
```

Hard:

```text
NEAR_MONTH_CONTRACT_HARDCODED_TO_202609 = 0
```

Store the selected contract in packet provenance.

---

# 15. No continuous-contract splicing by default

For user-facing D/W/M:

```text
use the same selected contract as the reference-date near-month
```

Do NOT silently splice:

```text
old near-month + new near-month
```

into a synthetic continuous series.

Hard:

```text
MULTI_CONTRACT_DWM_SPLICING = 0
```

If continuous-contract charts are ever added later:
they require a separate explicit adjustment/roll contract.

---

# 16. Same-contract timeframe dependency

For reference date `D` and selected contract `C`:

```text
Daily
= the completed NIGHT daily bar for D, contract C

Weekly
= valid NIGHT daily bars in D's XKRX trading week
  with contract C only

Monthly
= valid NIGHT daily bars in D's XKRX calendar month
  with contract C only
```

No other contract may enter.

Required:

```text
DWM_SAME_CONTRACT_ONLY = PASS
```

---

# 17. Weekly aggregation

For the set of valid same-contract constituent daily bars:

```text
weekly open  = first constituent open
weekly high  = max(constituent high)
weekly low   = min(constituent low)
weekly close = last constituent close
```

Record:

```text
period start
period expected business dates
included dates
missing dates
finality
```

If the week is not complete at the reference date:

```text
status = IN_PROGRESS
```

Hard:

```text
IN_PROGRESS_WEEKLY_BAR_LABELED_FINAL = 0
```

---

# 18. Monthly aggregation

For valid same-contract constituent daily bars in the reference month:

```text
monthly open  = first constituent open
monthly high  = max(high)
monthly low   = min(low)
monthly close = last constituent close
```

If the month is incomplete:

```text
status = IN_PROGRESS
```

Hard:

```text
IN_PROGRESS_MONTHLY_BAR_LABELED_FINAL = 0
```

---

# 19. Contract-roll partial-period semantics

If the selected near-month contract became active after the beginning of the current week/month:

do not pretend the same-contract W/M bar covers the full calendar period.

Use a state such as:

```text
SAME_CONTRACT_PARTIAL_PERIOD
```

and expose:

```text
aggregation_start_date
```

Hard:

```text
PARTIAL_CONTRACT_PERIOD_LABELED_FULL = 0
```

---

# 20. Missing/invalid constituent semantics

If an expected same-contract constituent daily bar is missing or invalid:

```text
weekly/monthly quality = PARTIAL_SAFE or INVALID
```

according to the actual dependency.

Do not drop the bad day and call the aggregate complete.

Hard:

```text
INVALID_CONSTITUENT_SILENTLY_DROPPED = 0
```

---

# 21. D/W/M return semantics

Keep OHLC and return semantics separate.

Daily:
- preserve the currently validated night-futures daily change baseline if safe
- record exact comparison source

Weekly:
```text
current weekly close
vs
previous completed same-contract weekly close
```

Monthly:
```text
current monthly close
vs
previous completed same-contract monthly close
```

If the prior same-contract baseline does not exist because of contract roll/history limits:

```text
return = UNAVAILABLE
```

Do not splice the previous contract.

Hard:

```text
DWM_RETURN_BASELINE_INVENTED = 0
```

---

# 22. Packet-owned night D/W/M facts

Create structured market facts for each instrument/timeframe:

```text
instrument
contract
timeframe
bar_start_date
reference_date
open
high
low
close
status/finality
return/change if valid
source fact IDs
raw-source fingerprints
quality
```

The renderer may only display packet-owned validated facts.

Required:

```text
NIGHT_DWM_PACKET_OWNERSHIP = PASS
```

---

# 23. Market message night-futures section

User-facing target:

```text
🌙 한국 야간선물 · 기준 09/01

• KOSPI200 최근월물 (202609)
  - 일봉: O ... · H ... · L ... · C ...
  - 주봉(진행중): O ... · H ... · L ... · C ... · 주간 ...
  - 월봉(진행중): O ... · H ... · L ... · C ... · 월간 ...

• KOSDAQ150 최근월물 (202609)
  - 일봉: ...
  - 주봉(진행중): ...
  - 월봉(진행중): ...
```

Exact style may follow production conventions.

Contract month is metadata.

Required:

```text
NIGHT_DAILY_VISIBLE_COUNT = 2
NIGHT_WEEKLY_VISIBLE_COUNT = 2
NIGHT_MONTHLY_VISIBLE_COUNT = 2
```

If a safe W/M return is unavailable:
render OHLC and explicitly mark return unavailable rather than inventing it.

---

# 24. Real-yield level + delta

US market analysis must show:

```text
latest safe US 10Y real-yield level
latest observation date
immediately previous valid observation level/date
delta in percentage points
delta in basis points
```

Use the same authoritative real-yield series already present in the market packet.

Do not substitute nominal yield or breakeven.

---

# 25. Real-yield calculation

Canonical:

```text
delta_pp = current_yield_pct - previous_yield_pct
delta_bp = delta_pp * 100
```

Example only:

```text
1.82% → 1.86%
delta = +0.04%p = +4bp
```

Hard:

```text
REAL_YIELD_DELTA_RENDERED_AS_PERCENT_RETURN = 0
```

---

# 26. Real-yield observation pair

Use:

```text
latest safe observation
vs
immediately previous valid observation
```

not:
- previous KST calendar day
- previous equity session by assumption

Required:

```text
REAL_YIELD_OBSERVATION_PAIR_VALID = PASS
```

---

# 27. Real-yield temporal labeling

If the latest real-yield observation is lagged relative to the US equity session:

render the observation date.

Example:

```text
미 10년 실질금리 1.82% (08/31 관측)
· 직전 관측 대비 +0.04%p (+4bp)
```

Do not say `오늘 +4bp` unless same-day semantics are truly valid.

Hard:

```text
STALE_REAL_YIELD_DELTA_LABELED_SAME_DAY = 0
```

---

# 28. Real-yield precision

Use source-aware precision.

Recommended:

```text
level = 2 decimals %
delta = 2 decimals %p
bp = integer when source precision supports it
```

Do not create false precision.

Required:

```text
REAL_YIELD_ROUNDING_CONTRACT = PASS
```

---

# 29. Market numeric provenance

Add to the market numeric registry:

```text
night D/W/M OHLC
night D/W/M returns
real-yield level
real-yield previous level
real-yield delta_pp
real-yield delta_bp
```

Required:

```text
NIGHT_DWM_NUMERIC_PROVENANCE = PASS
REAL_YIELD_DELTA_NUMERIC_PROVENANCE = PASS
MARKET_PHANTOM_NUMERIC_ERRORS = 0
```

---

# 30. Run-51 market replay

Before actual send:

build a controlled run-51 market replay.

Preserve frozen non-night facts:

```text
SPY  -0.69%
QQQ  -1.27%
IWM  -1.14%
SOXX -2.10%
RSP  -0.82%

energy +1.27%
consumer discretionary -1.72%
```

Intentional additions:

```text
night D/W/M
real-yield level + previous-observation delta
```

Required:

```text
RUN51_NON_NIGHT_MARKET_NUMERIC_DIFF = 0
RUN51_NON_NIGHT_MARKET_SELECTION_DIFF = 0
RUN51_MARKET_REPLAY = PASS
MARKET_FINAL_VALIDATION = PASS
```

---

# 31. Run-51 stock evidence remains frozen

For stocks, use the exact canonical run-51 packet/evidence.

No fresh:
- price
- OHLCV
- news
- earnings
- company events
- macro
- positioning

Required:

```text
RUN51_STOCK_FROZEN_SOURCE_REUSED = PASS
POST_RUN51_STOCK_FACT_LEAKAGE = 0
```

---

# 32. Run-51 technical context

Use frozen packet-owned technical context.

Reference:

```text
PARTIAL_SAFE = 14
FULL = 0
INVALID = 0
UNAVAILABLE = 0
```

Preserve:

```text
CPNG invalid historical rows
feature-scoped safety
HUT current quote != completed close
```

Hard:

```text
TECHNICAL_PARTIAL_SAFE_FORCED_TO_FULL = 0
CPNG_INVALID_TECHNICAL_NUMERIC_VISIBLE_TO_V2 = 0
HUT_CURRENT_QUOTE_OWNS_COMPLETED_CLOSE = 0
```

---

# 33. Actual V2 production path

Execute the actual production-equivalent path:

```text
frozen run-51 stock evidence
→ V2 prepare_context
→ production path builder
→ repaired scheduler-equivalent Codex runtime
→ signed-in app-server
→ actual model call
→ candidate
→ candidate validation
→ adjudication
→ accepted_decision_plan
→ V2 accepted renderer
→ final validator
```

Forbidden:

```text
pre-baked model response
pre-baked candidate
pre-baked accepted plan
validator bypass
```

---

# 34. V2 acceptance

Required:

```text
CODEX_RUNTIME_STATE_PREFLIGHT = PASS
CODEX_APP_SERVER_INITIALIZATION = PASS

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

# 35. Daily-review secondary path

Preserve:

```text
DAILY_REVIEW_QUALITY = PASS
DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED = 0
```

Do not send daily-review messages separately.

---

# 36. Test execution identity

Use:

```text
source packet = original run-51 read-only
test execution = new isolated test ID
delivery namespace = TEST
```

Hard:

```text
RUN51_PRODUCTION_PACKET_MUTATION = 0
RUN51_PRODUCTION_CLAIM_MUTATION = 0
RUN51_PRODUCTION_DELIVERY_LEDGER_MUTATION = 0
```

---

# 37. Production recipient safety

Actual Telegram send is authorized ONLY to the existing dedicated non-production test recipient.

Production destination must be structurally unavailable.

Required:

```text
PRODUCTION_RECIPIENT_RESOLUTION_DISABLED = PASS
TEST_RECIPIENT_RESOLUTION = PASS
PRODUCTION_RECIPIENT_SEND = 0
```

Never expose IDs.

---

# 38. Atomic pre-send gate

Expected:

```text
market = 1
stocks = 14
total = 15
```

Before first send, all must be final-validation PASS.

Market must include:
- D/W/M for KOSPI200
- D/W/M for KOSDAQ150
- real-yield level + delta

Required:

```text
TEST_EXPECTED_MESSAGE_COUNT = 15
PRE_SEND_ATOMIC_READINESS = PASS
```

If any required message fails:

```text
ACTUAL_SEND_COUNT = 0
```

---

# 39. Real Telegram transport

Use the actual production Telegram transport adapter.

Do not mock:
- HTTP
- Telegram acknowledgements
- rate-limit behavior

Only destination differs.

Required:

```text
REAL_TELEGRAM_TRANSPORT = PASS
```

---

# 40. Exactly-once

Required:

```text
TEST_SENT_COUNT = 15
TEST_ACKNOWLEDGED_COUNT = 15
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_UNOWNED_RETRY = 0
ACKNOWLEDGED_MESSAGE_RESEND = 0
```

On rate limit:
resume unacknowledged remainder only.

---

# 41. Exact payload

Per message compare:

```text
final validated renderer text
frozen send payload
actual outbound request
test delivery ledger
acknowledged payload if available
```

Required:

```text
TEST_LIVE_EXACT_PAYLOAD = PASS
```

Store sanitized per-message SHA-256.

---

# 42. Production-state mutation audit

Required:

```text
PRODUCTION_ACCEPTED_DECISION_MUTATION = 0
PRODUCTION_ASSESSMENT_MUTATION = 0
PRODUCTION_NOTIFICATION_STATE_MUTATION = 0
PRODUCTION_PACKET_STATE_MUTATION = 0
PRODUCTION_DELIVERY_LEDGER_MUTATION = 0
```

Test delivery must not suppress next natural run:

```text
TEST_DELIVERY_SUPPRESSES_NEXT_NATURAL_SEND = 0
```

---

# 43. Idempotency

The test execution ID must be idempotent.

Do not prove by sending 15 messages twice.

Required:

```text
TEST_EXECUTION_IDEMPOTENCY = PASS
```

---

# 44. Production collector integration

After the run-51 controlled proof:

wire the KRX NIGHT daily collector into the normal source-monitor/market-packet flow for future runs.

The future natural flow should be:

```text
source monitor
→ acquire latest expected KRX NIGHT daily row
→ validate/store raw + normalized daily
→ update same-contract history
→ build D/W/M packet
→ market packet
→ market message
```

Do not perform full historical backfill on every natural run.

---

# 45. Collector failure isolation

If KRX night-history acquisition fails on a future run:

```text
stock V2 path must continue
```

Market message:
- render last safe permitted night context only if freshness policy allows
- otherwise mark/omit only the affected night subsection

Hard:

```text
KRX_NIGHT_COLLECTOR_FAILURE_BLOCKS_STOCK_V2 = 0
```

---

# 46. Source freshness

Every D/W/M fact must carry:

```text
reference date
constituent range
finality
```

Do not render stale old same-contract bars as current without explicit labeling.

Required:

```text
NIGHT_DWM_FRESHNESS_CONTRACT = PASS
```

---

# 47. Cross-market regression

Run:

```text
US production-equivalent V2
KR production-equivalent V2
```

Reference active fixture counts if unchanged:

```text
US = 14
KR = 8
```

Required:

```text
US_PRODUCTION_EQUIVALENT_V2 = PASS
KR_PRODUCTION_EQUIVALENT_V2 = PASS
```

---

# 48. Full validation

Require:

```text
KRX source/schema tests PASS
raw-preservation tests PASS
daily OHLC validation tests PASS
same-contract aggregation tests PASS
contract-roll tests PASS
XKRX calendar tests PASS
missing constituent tests PASS
run-51 screenshot control completed
run-51 night D/W/M replay PASS
real-yield delta tests PASS
run-51 market replay PASS
V2 live-path tests PASS
actual TEST-recipient send PASS
US/KR production-equivalent PASS
full pytest PASS
Ruff PASS
git diff --check PASS
GitHub Actions Test/Lint PASS
```

---

# 49. Main merge gate

Merge only if:

```text
KRX NIGHT daily OHLC schema proven
raw response preservation PASS
daily OHLC validation PASS
same-contract D/W/M PASS
no continuous-contract splicing
in-progress W/M labeling correct
no invented return baselines
run-51 KOSPI screenshot control resolved
run-51 KOSDAQ daily valid
night D/W/M visible 2/2/2
real-yield level+delta provenance PASS
market replay PASS
V2 candidate/accepted/explicit 14/14
fallback 0
pre-send atomic gate PASS
TEST Telegram 15/15
production recipient 0
production mutations 0
US/KR regressions PASS
P0 = 0
material P1 = 0
```

---

# 50. Natural-live guard

Controlled actual-send PASS is not yet natural US LIVE_PASS.

After merge/deploy, wait for the next ordinary US morning run.

Natural proof must show:

```text
KRX NIGHT latest expected daily acquired
D/W/M built from stored same-contract history
real-yield level+delta rendered
V2 actual model path
explicit decisions
exactly-once production delivery
```

No manual production replay.

---

# 51. Required architecture docs

Create/update:

```text
docs/architecture/KRX_NIGHT_DAILY_OHLC_SOURCE_CONTRACT.md
docs/architecture/KRX_NIGHT_HISTORY_STORE.md
docs/architecture/KRX_NIGHT_DWM_AGGREGATION.md
docs/architecture/US_MORNING_NIGHT_FUTURES_REFERENCE_DATE_CONTRACT.md
docs/architecture/US_MARKET_REAL_YIELD_DELTA_CONTRACT.md
docs/architecture/MARKET_PACKET_TEMPORAL_ROLES.md
```

---

# 52. Required reports

Create at minimum:

1. `docs/reports/20260902-krx-night-source-schema-proof.md`
2. `docs/reports/20260902-krx-night-field-mapping.md`
3. `docs/reports/20260902-krx-night-raw-preservation.md`
4. `docs/reports/20260902-krx-night-history-store.md`
5. `docs/reports/20260902-krx-night-history-calendar-reconciliation.md`
6. `docs/reports/20260902-night-near-month-selection.md`
7. `docs/reports/20260902-night-same-contract-dwm-contract.md`
8. `docs/reports/20260902-night-contract-roll-partial-period.md`
9. `docs/reports/20260902-run51-kospi200-screenshot-control.md`
10. `docs/reports/20260902-run51-kospi200-night-daily.md`
11. `docs/reports/20260902-run51-kosdaq150-night-daily.md`
12. `docs/reports/20260902-run51-night-weekly-monthly.md`
13. `docs/reports/20260902-run51-night-return-provenance.md`
14. `docs/reports/20260902-run51-historical-backfill-disclosure.md`
15. `docs/reports/20260902-real-yield-delta-contract.md`
16. `docs/reports/20260902-run51-real-yield-observation-pair.md`
17. `docs/reports/20260902-run51-market-enriched-replay.md`
18. `docs/reports/20260902-run51-market-numeric-provenance.md`
19. `docs/reports/20260902-run51-v2-live-path.md`
20. `docs/reports/20260902-run51-test-recipient-routing.md`
21. `docs/reports/20260902-run51-actual-send-receipts.md`
22. `docs/reports/20260902-run51-exact-payload.md`
23. `docs/reports/20260902-run51-production-mutation-audit.md`
24. `docs/reports/20260902-run51-actual-send-idempotency.md`
25. `docs/reports/20260902-krx-night-production-integration.md`
26. `docs/reports/20260902-run51-live-path-with-krx-night-proof.md`
27. `docs/reports/20260902-run51-live-path-with-krx-night-artifact-index.md`

Machine-readable:

```text
docs/reports/20260902-krx-night-source-contract.json
docs/reports/20260902-krx-night-history.json
docs/reports/20260902-run51-night-dwm.json
docs/reports/20260902-run51-real-yield-delta.json
docs/reports/20260902-run51-market-enriched.json
docs/reports/20260902-run51-live-path-stage-matrix.json
docs/reports/20260902-run51-live-path-delivery.json
docs/reports/20260902-run51-live-path-with-krx-night-proof.json
```

---

# 53. Required gates

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

KRX_NIGHT_DAILY_OHLC_SCHEMA =
PROVEN / FAIL

UNVERIFIED_KRX_FIELD_SEMANTICS_USED =
0 / NONZERO

KRX_RAW_RESPONSE_PRESERVED =
PASS / FAIL

RAW_KRX_OHLC_REWRITTEN =
0 / NONZERO

CONTRACT_IDENTITY_COLLISION =
0 / NONZERO

SYNTHETIC_KRX_OHLC_REPAIR =
0 / NONZERO

KRX_NIGHT_HISTORY_INCREMENTAL =
PASS / FAIL

KRX_NIGHT_HISTORY_CALENDAR_RECONCILIATION =
PASS / FAIL

POST_CUTOFF_MARKET_DATA_USED_IN_RUN51_REPLAY =
0 / NONZERO

PRODUCTION_RUN51_PACKET_BACKFILLED_IN_PLACE =
0 / NONZERO

NEAR_MONTH_CONTRACT_HARDCODED_TO_202609 =
0 / NONZERO

MULTI_CONTRACT_DWM_SPLICING =
0 / NONZERO

DWM_SAME_CONTRACT_ONLY =
PASS / FAIL

IN_PROGRESS_WEEKLY_BAR_LABELED_FINAL =
0 / NONZERO

IN_PROGRESS_MONTHLY_BAR_LABELED_FINAL =
0 / NONZERO

PARTIAL_CONTRACT_PERIOD_LABELED_FULL =
0 / NONZERO

INVALID_CONSTITUENT_SILENTLY_DROPPED =
0 / NONZERO

DWM_RETURN_BASELINE_INVENTED =
0 / NONZERO

NIGHT_DWM_PACKET_OWNERSHIP =
PASS / FAIL

CONTRACT_MONTH_PRESENTED_AS_MONTHLY_TIMEFRAME =
0 / NONZERO

RUN51_EXPECTED_NIGHT_REFERENCE_DATE =
2026-09-01 / OTHER

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

NIGHT_DWM_NUMERIC_PROVENANCE =
PASS / FAIL

REAL_YIELD_OBSERVATION_PAIR_VALID =
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

RUN51_STOCK_FROZEN_SOURCE_REUSED =
PASS / FAIL

POST_RUN51_STOCK_FACT_LEAKAGE =
0 / NONZERO

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

TEST_EXPECTED_MESSAGE_COUNT =
15 / OTHER

PRE_SEND_ATOMIC_READINESS =
PASS / FAIL

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

TEST_DELIVERY_SUPPRESSES_NEXT_NATURAL_SEND =
0 / NONZERO

TEST_EXECUTION_IDEMPOTENCY =
PASS / FAIL

KRX_NIGHT_COLLECTOR_FAILURE_BLOCKS_STOCK_V2 =
0 / NONZERO

NIGHT_DWM_FRESHNESS_CONTRACT =
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

RUN51_KRX_NIGHT_LIVE_PATH_ACTUAL_SEND =
PASS / FAIL
```

---

# 54. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

KRX_NIGHT_SOURCE =
endpoint/service ...
schema proof ...
field mapping ...
raw preservation ...

KRX_HISTORY =
daily store ...
retention ...
backfill used? ...
calendar reconciliation ...

RUN51_NIGHT =
reference date 2026-09-01

KOSPI200 =
contract ...
daily O/H/L/C ...
screenshot parity ...
weekly O/H/L/C/status/return ...
monthly O/H/L/C/status/return ...

KOSDAQ150 =
contract ...
daily O/H/L/C ...
weekly O/H/L/C/status/return ...
monthly O/H/L/C/status/return ...

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
market final validation ...

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

US_PRODUCTION_EQUIVALENT_V2 = ...
KR_PRODUCTION_EQUIVALENT_V2 = ...

FULL_TESTS = ...
RUFF = ...
GIT_DIFF_CHECK = ...
ACTIONS = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

RUN51_KRX_NIGHT_LIVE_PATH_ACTUAL_SEND =
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

# 55. Mandatory completion ZIP

Create:

`20260902-run51-live-path-with-krx-night-ohlc-history-dwm-real-yield-bundle.zip`

Include:
- exact master instruction
- all track instructions
- KRX source schema proof
- raw-response examples/hashes
- normalized daily-store proof
- calendar reconciliation
- near-month resolver proof
- same-contract D/W/M aggregation
- roll/partial-period tests
- run-51 screenshot comparison
- KOSPI200/KOSDAQ150 D/W/M facts
- any historical-backfill disclosure
- real-yield observation/delta proof
- enriched run-51 market message
- V2 model/candidate/adjudication/accepted evidence
- exact 15 messages
- test-recipient routing
- real Telegram receipts
- exact payload hashes
- production mutation audit
- CI/main/runtime evidence
- machine-readable JSON
- artifact index

Exclude:
- recipient IDs
- auth/session tokens
- Codex credentials/state DB contents
- account identifiers
- secrets
- hidden chain-of-thought

Compute SHA-256.

---

# 56. Final principle

The target production architecture is:

```text
KRX official NIGHT daily OHLC
→ raw immutable provenance
→ same-contract daily history
→ D/W/M aggregation
→ packet-owned market facts

US real yield
→ latest safe observation
→ immediately previous valid observation
→ level + Δ%p + Δbp

run-51 stock evidence
→ actual V2 model
→ candidate
→ accepted
→ explicit stock messages

all final messages
→ real Telegram transport
→ dedicated TEST recipient
→ 15/15 exactly once
```

Do not confuse:
- contract month with monthly timeframe
- historical contract splicing with same-contract bars
- percent return with percentage-point yield change
- a test recipient with production delivery

No synthetic OHLC.
No silent cross-contract stitching.
No invented W/M return baseline.
No production state mutation.
