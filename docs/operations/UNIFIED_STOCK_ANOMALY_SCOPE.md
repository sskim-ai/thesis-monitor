# Consumer-Scoped Historical OHLCV Integrity

R2B0-R1 is an offline extension, not a production rollout. Contract:
`stock-consumer-anomaly-scope-v1`. The R2B0 ZIP and request-plan hashes in the
instruction are verified before loading any of the 88 roles. Source bytes and
the original root-cause receipt remain unchanged. Historical whole-payload
`validate_role` remains reproducible; the new path uses `load_owned_role` for
the same receipt/hash/provider/session ownership, then separate consumer gates.

## Policy

- Source integrity is still evaluated by `inspect_normalized_ohlcv_rows`.
  No malformed row becomes valid, is repaired, or disappears from the audit.
- Current/latest malformed rows block the entire role, including close-only
  consumers. A stale daily close cannot replace the required completed session.
- Historical relational defects are scoped to the actual rows and fields used.
  Date/order/duplicate uncertainty fails all selections closed.
- Existing feature-engine row-integrity prerequisites are preserved even for
  its close-based recursive features. The valuation history owner is different:
  it projects `HistoricalPricePoint(date, close)` without reading open/high/low.
- Unknown selection is ineligible. Normalizers that skip bad rows are not a
  waiver: selected date spans and the owner's raw tail retain malformed holes.
- The analysis-only view projects completion markers from the existing V3
  exchange-calendar owner. Unmarked native current-month rows cannot become
  completed monthly features. Raw OHLCV and source fingerprints stay unchanged;
  projected finality metadata is recorded separately.
- Optional-component availability is not a claim that a full Core/A/B packet
  meets its requirements. No mandatory field is made optional.

## Real Consumer Graph

All paths below are relative to `app/services` unless stated otherwise. The
machine-readable matrix includes each selected date, row fingerprint, violation,
field dependency, selection rule, owner and eligibility. Owner-source hashes
are in the report. No invented common lookback is used.

| Consumer | Existing owner / rows | Integrity and downstream behavior |
|---|---|---|
| Current price | `ohlcv_client._summarize_bars`, `fetch_price_context`: latest adjusted daily close | Mandatory current input; latest defect/session mismatch fails it |
| Range/position | `_summarize_bars`: all returned highs/lows plus latest close | Whole returned range; unavailable on relevant defect |
| Candle/volume/value | `_chart_timeframe_context`: latest OHLC/body/wicks, volume/value | Separate from embedded indicator dependencies |
| Native-provider MAs/BB/RSI/MACD | source owner's `app/indicators/technical.py:add_indicators`: rolling MA 33/111/144/222/288; BB 36/50/60/144/288/300; RSI rolling 14 changes, MACD EWM all close history | Source-owner audit only, not recomputed/materialized by R1; no assumption that latest indicator uses one row |
| Canonical SMA/returns/range/trend/volume | `ohlcv_feature_engine_service._feature_facts.add`: actual `minimum_history` and dependency assessment | Existing finite dependency contract; audit callback records real executed decisions, changes no facts |
| Canonical RSI/EMA/MACD/ATR/ADX/DMI/OBV | `technical_feature_dependency_service`: recursive full normalized history | Bad dates in recursive span block those features, no invented warmup tolerance |
| Legacy local pivots/SR | `ohlcv_structure_service.detect_local_pivots`: D300/W120/M60, shared `LOCAL_PIVOT_LOOKBACKS` | Constants extracted without changing values; actual selector parity tested |
| Legacy major swings/ATR/Fib/wave/invalidation | `analyze_chart_structure`: `MAJOR_CONFIG` D300/W156/M60; Wilder seed uses entire selected span | Relevant OHLC defect blocks dependent component |
| Legacy boxes | `detect_boxes`: `LOCAL_CONFIG.box_lookback` D20/W12/M6 plus local-pivot-derived zones | Includes both dependencies, not only box tail |
| V3 pivot/wave/long cycle/SR | `price_structure_wave_fibonacci_v3_service.prepare_long_history`: `HISTORY_REQUESTS`, complete tail plus partial bars, market calendar | Full selected long history; malformed holes remain relevant despite normalizer exclusion |
| Valuation history | `ohlcv_client` unadjusted weekly -> `HistoricalPricePoint(date, close)` -> `historical_valuation_service._weekly_prices`/`update_cache` PIT denominators | All sampled closes, not OHLC; unused historical high/open defect does not taint close. No valuation cache writes or multiples generated |
| Core fact catalog/numeric registry | `ai_review_service._fact_catalog`, `_chart_facts`, `_numeric_registry` | Reads assembled fields, not raw rows. Pure source-only assembly/binding still absent; not invoked with synthetic assessment |
| Owned evidence / A/B | `cross_market_decision_engine_service.build_decision_evidence_packet`, `direction_timing_ownership_service.build_owned_evidence_packet`; `scripts/m12cq_two_pass_contract.py` | Pass A forbids technical/current-price keys. B can consume eligible typed technical inputs; full pass binding not qualified here |
| Renderer-visible structure | `price_structure_v3_renderer_service.render_current_price_structure`, `structured_autonomy_shadow_service.render_structured_autonomy_message` | Derived zone/price/candidate consumers, no direct raw rows; render calls 0. No unsafe V3 summary supplied |

## Sealed CPNG Result

All three original 2023-06-05 HIGH_LT_OPEN anomalies remain. Source daily
16.35/15.80/15.43/15.66 and weekly 16.35/16.20/15.43/16.01 are unchanged.

- Current daily price, latest candles, unadjusted weekly close history: eligible
  for the examined source consumption; not full valuation qualification.
- Legacy daily local/major windows start 2025-07-18; weekly local starts
  2024-06-10 and major starts 2023-10-02. The bad row is outside these spans.
- Full period-range calculations, recursive canonical indicators, and V3
  daily/weekly long histories remain blocked. V3 spans start 2022-09-30 and
  2021-03-11 respectively, so the malformed row cannot be waved away.
- Monthly source has no integrity anomaly. Current typed technical status is
  `PARTIAL_SAFE`; exact safe feature counts are recorded in the final proof after
  the existing calendar-finality projection excludes partial monthly bars.

## Remaining Integration Blocker

Outcome C: `M12DS_R6_R5F_R2B0_R1_COMPLETE_STOCK_OWNER_BINDING_NOT_IMPLEMENTED`.
R5's `UNIFIED_TWO_BLOCKER_PREQUALIFICATION.md` explicitly says the pure stock
materializer was not implemented. Its script emits blocked rows instead of
assembling stock packets; R2B0 also never reached that owner. R1 closes source
consumer scoping and materializes real typed technical components, not a fake
stock-packet dictionary.

All 22 component projections reproduce identically; 22 current prices are
eligible. Complete stock packet count remains zero, all stock packet hashes
remain null, and observed-business union is not qualified. The sealed source-
only corpus has no selected current-formal Class-C financial/event projection
bound to the new complete stock owner. Existing Class-C projection functions
remain available, not replaced with old AI outputs or empty observed business.

Smallest next repair: complete that explicit source-only stock assembly owner,
bind read-only Class-C/local seed projections to this exact 88-role acquisition,
project only eligible technical fields, and run nonempty business-union,
financial/PIT/taint, typed evidence and numeric registry negative tests. Do not
recollect the 88 roles or reopen KRX historical-envelope closure. R2B generation
requires the resulting full prequalification PASS; it is not reached here.

Production wiring, settings, public schema, renderers, providers, models,
Telegram, database, schedulers, main/push/deploy/restart are unchanged.
