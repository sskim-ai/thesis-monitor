# Unified Production Adapter Parity

## R5F-R2 Outcome

`M12DS_R6_R5F_R2_ADAPTER_PARITY_GAP_REMAINS`.

R5F-R1 is the accepted orchestration foundation. The R5F-R2 instruction is
frozen at `e5ba55cdedb0926ea0d264885e1f2db3c7c979ab`. The operating checkout
remains `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.

Section 8 fails on real source evidence, so Section 9 is **not run**. No
concrete production adapter is registered. `UnqualifiedAdapter`, disabled
feature defaults, and inactive scheduler templates are unchanged. This is
not a new AI engine, a provider-policy change, or scheduler authorization.

## Implemented Boundary

`app/services/unified_source_replay.py` replays an individual frozen OHLCV
source role through the existing `OhlcvClient._decode_period_payload` and
`inspect_normalized_ohlcv_rows` owners. It checks run/attempt/market identity,
aware request/response timestamps, request hash and role, exact artifact
bytes, payload symbol/provider/adjustment metadata, latest row, OHLC integrity,
and normalized hash. Missing identity cannot be silently supplied by parser
defaults. A `valid=true` field is not proof. Source paths cannot escape the
declared attempt root or follow a symlink. There is no fallback or network.

The role descriptor must come from an independently frozen acquisition
manifest; it is not authorization by an untrusted caller. Successful output
is labelled `ROLE_ONLY_NOT_PRODUCTION_ADAPTER`. This component does not prove
completeness of the financial, macro, event, or downstream model adapters.

`scripts/unified_adapter_preflight.py` audits the existing two-market historical
archive layout without mutating it. It is a historical diagnostic, not the
single-market production runtime. The current universe is read through
`production_universe_snapshot` using a SQLite read-only/query-only connection.

## Canonical Universe

US: CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF.

KR: 000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280.

US message IDs: `MARKET_US` plus those 14 tickers. KR message IDs:
`MARKET_KR` plus those 8 tickers. Counts are 15 and 9, not 24 in a single run.

## Source Owner Inventory

This inventory is derived from source owners, not prompt fields. "Consumed"
means any value retained in the analysis packet must have source binding.
An optional role may remain explicitly unavailable under its existing owner;
it must not acquire invented values or silently become mandatory. Existing
owner availability policy is not expanded in this task.

| Role / Market | Canonical Owner | Provider / Route | Universe / Date / Basis | Requirement and Validator | Existing Fallback / R2 Treatment |
|---|---|---|---|---|---|
| Universe and thesis / both | `production_universe_snapshot`; `run_daily_monitor` | read-only watchlist/security/thesis records | exact eligible market roster at cutoff; versioned stored business logic | mandatory; onboarding eligibility and thesis version | no cross-market union; freeze metadata separately from fresh observations |
| Stock chart / both | `OhlcvClient._request_period`, `fetch_price_context` | OHLCV gateway `/ohlcv` | each ticker; daily/weekly/monthly adjusted history; latest row and market session | mandatory for retained price/technical evidence; decoder, OHLC integrity, completed-bar finality, technical context gates | retry/cache paths exist; fresh attempt must explicitly exclude inherited caches; response-level proof required |
| Stock valuation quote / both | `ValuationSnapshotService.fetch` | OHLCV gateway weekly unadjusted valuation read | each ticker; raw/unadjusted security currency | consumed; typed valuation/security basis and source freshness | cannot reuse an adjusted chart price as raw quote |
| Issuer financials / US | `SecFinancialSnapshotService.refresh` | SEC companyfacts / foreign filing documents | official occurrence, filing availability, entity/currency/period | consumed; selected-source quality, canonical financial lineage | persisted snapshots may be reused by old controller; acquired artifact identity required |
| Issuer financials / KR | `backfill_financial_snapshots`; OpenDART source owner | OpenDART statements / filings | corporate identity, receipt and report period, consolidated/separate | consumed; canonical financial/quality/period validators | no inferred periods, no missing-to-zero; whole operating DB copy is not acquisition proof |
| Cash flow / working capital / both | existing canonical financial domains in decision evidence builder | derived from preceding official occurrences | compatible period/entity/currency and input fact refs | consumed; existing cash-flow, domain and typed-evidence gates | no new source or recalculation in adapter |
| Multiples / estimates / US | `ValuationSnapshotService.fetch` | Finnhub stock metrics; Alpha estimates/shares/overview/dividends | reported/provider period and security basis, not chart basis | optional availability, mandatory lineage if consumed; typed valuation/source-use gates | Alpha collection AND reads of persisted Alpha estimates exist; disabling a key alone does not remove cached consumption |
| Events / both | `CollectionService.collect_events`; `provider_priority` | Google News RSS, Naver, SEC, OpenDART, optional NewsAPI, CompanyIR; Alpha events | ticker/event publication time at cutoff | optional event availability; identity/materiality/semantic ownership | registry includes Alpha and optional mock; R2 must explicitly exclude prohibited providers before dispatch |
| US indices/style/sectors/big tech | `OhlcvMarketProvider.collect` | OHLCV gateway `/ohlcv` | SPY/QQQ/IWM/RSP/SOXX/XLB/XLC/XLF/XLE/XLI/XLK/XLP/XLRE/XLU/XLV/XLY/NVDA/MSFT/AAPL/GOOGL/AMZN/META; adjusted daily | declared market role, unavailable tracked; market session/temporal and numeric registry | owner currently discards HTTP raw response after normalizing observations; per-request role receipt absent |
| US exchange breadth | `collect_and_persist_us_exchange_breadth` | Nasdaq Trader official daily files | exchange scope/session, exchange membership and counts | optional availability, mandatory source binding if consumed; official breadth and cross-section types | local archived source retained; must bind the selected artifact to current attempt |
| Rates/credit/liquidity/risk | `macro_providers`, `FredProvider.collect` | FRED series registry | observation date + publication/as-of, units and native frequency | configured optional roles; macro temporal eligibility | past DB observations are not newly acquired merely because packet is rebuilt |
| Energy | `EiaProvider.collect` | EIA series registry | provider date/frequency/unit | configured optional; macro temporal eligibility | no undocumented secondary source |
| Korea macro | `EcosProvider.collect` | BOK ECOS series registry | publication/observation period, unit | configured optional; macro temporal eligibility | no replacement with unrelated quote date |
| Central-bank events | `FederalReserveProvider.collect` | official Federal Reserve | publication time | optional events; macro eligibility | no source substitution |
| Earnings calendar | `FinnhubEarningsProvider.collect` | Finnhub earnings calendar | event dates; forward-event context only | optional; source-use and temporal gates | not actual reported business results |
| US-window night futures | `KrxNightFuturesProvider.collect`; morning gate | KRX night rows, existing product identities | two products, role-target session/reference basis and query time | required when part of run contract; existing night source/numeric gates | historical controller pre-acquires a separate night snapshot; raw KRX files exist but current-attempt ownership is not established |
| KR indices/size/sectors/breadth | `KiwoomKrMarketContextService.collect` | Kiwoom `ka20001`, `ka20003`, `ka20009`, `/api/dostk/sect` | KOSPI/KOSDAQ and returned sector universe; matched target-date/session | declared local market roles; `_validate_session_identity`, typed cross-section quality | raw archive exists; inherited archive may not silently fill this attempt |
| KR market/investor flows | same Kiwoom owner | `ka10051`, paged `ka10066`; sector/market-condition routes | KOSPI/KOSDAQ aggregates and constituents, explicit KRW scale | consumed; aggregate identity, pagination, reconciliation and concentration guards | preserve complete page set and role hashes, never mix attempts |
| KR close FX | `run_kr_close_market_briefing` | **AlphaVantageKrCloseFxProvider by default** | KR cutoff FX series and quote/provider timestamp | explicitly unavailable permitted by old warning path; consumed facts need validation | cannot call this default under R2 Alpha=0; no alternative provider may be invented |
| KR overnight cross-assets | `_market_packet` and KR adapter | stored US macro source observations | previous completed US session, explicitly overnight context | consumed; per-market session/temporal gate | explicit prior-session source role is different from requiring a second live US run |

## Real Evidence Result

Two independently sealed real archives were inspected:

- `20260922-m12ds-r4-r4-current-20260922T165106+0900`
- `20260923-m12ds-r6-0805-fresh-20260923T080654+0900`

For both: US14/KR8 exact; original/projected packet manifest hashes PASS;
existing market-session validator PASS. These are valid historical packet
checks, **not new single-attempt source adapter qualification**.

For each archive, all 22 stocks retain technical acquisition summaries and
normalized bar fingerprints, but no standalone OHLCV HTTP response was found
in the declared source archive areas. Four roles per stock (adjusted D/W/M and
unadjusted valuation) lack request-to-response-to-normalization binding. A
normalized `raw_bar_fingerprint` is not a hash of the original HTTP response.
The collector `m12ds_r4_collect` also copies the operating database/state and
imports a pre-acquired night snapshot. We do not retroactively stamp those
values with a new attempt identity.

Each archive reports 26 historical Alpha telemetry rows with positive success
or failure deltas. These are **telemetry events, not exact HTTP call counts**.
They are not calls made by R2. They establish that the old acquisition route
does not itself prove a zero-Alpha acquisition policy. Not every Alpha event
necessarily contributes a retained value; that dependency cannot be declared
absent from aggregate telemetry alone.

## Downstream Owners and Gate

| Stage | Existing Owner | R2 Status |
|---|---|---|
| Market | `m12ds_r4_r4_market` context/schema/PROMPT/validator | identified, no new request or model execution |
| Core | `m12ds_r4_r4_schemas` core schema/PROMPT; `m12ds_r4_r4_policy.materialize_core` | unchanged; gated by source proof |
| A | `m12dr_fresh_blind_reproof.Reproof.pass_a` and existing request/authority owners | unchanged; fixed topology not migrated after source failure |
| B | `m12ds_r2_shadow_reproof.Reproof.before_b/pass_b` plus R4R4 schemas/policy | unchanged; fixed manifests not migrated after source failure |
| Validator | original source authority, typed capability, schema, numeric and policy owners | no threshold/policy changes |
| Renderer | `render_accepted_v2_production`, `render_daily_digest`, `render_us_full_market_message` | unchanged; no new 24-message corpus claimed |
| Delivery | `m12ds_r4_offline_capture.capture_payload` / existing delivery payload builder | not invoked; production recipient intent zero |

Source gate failure prevents honest end-to-end parity. Reusing historical
accepted AI outputs would not repair missing source receipts. No new model
authorization is requested because it would not solve the source blocker.

## Next Bounded Repair

See the R5F-R2a instruction in `docs/work-instructions`. Close owner-bound
acquisition receipts, explicit provider exclusions including cache reads,
and attempt-local metadata seeding first. Do not jump to scheduler R5F-R3.
