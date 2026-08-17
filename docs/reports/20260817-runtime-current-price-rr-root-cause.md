# Runtime Current-Price RR Root Cause

## Incident

Natural KR packet `2026-08-17-kr-run-23-378ee562573e` was rejected before AI delivery. POSCO
Holdings, LS ELECTRIC, Hanwha Aerospace, and Hyundai Glovis each produced:

- `current_price_structure_fact_missing:chart:structure:risk_reward:current_price`
- `current_price_structure_numeric_missing:...:fields.ratio`

Rejected AI sends were zero. Fallback eligibility was preserved and the deterministic fallback
later delivered 8/8. Pilot remained KR 3/5 and US 3/5.

## Root Cause

The four RR values were calculated correctly and persisted in current monitoring state, but chart
Facts were suppressed before packet registration. The exact classification for all four was
`CALCULATED_BUT_NOT_CANONICALIZED`.

`market_session.py` used weekdays rather than exchange sessions. It treated Monday 2026-08-17 as a
completed KRX trading day. `ohlcv_client.py` therefore compared the actual latest bar, 2026-08-14,
with an incorrect expected date of 2026-08-17 and marked the chart `stale`.

2026-08-17 was an XKRX substitute holiday. The correct latest completed session was 2026-08-14.
The chart date, current close, structure date, and RR entry were therefore compatible.

The downstream mismatch was deterministic:

1. `monitoring_state_service.build_monitoring_state()` retained the already calculated RR.
2. `ai_review_service._state_grounding_requirements()` correctly required current RR when the
   monitoring-state ratio was available.
3. `ai_review_service._chart_facts()` correctly refused to expose a chart marked `stale`.
4. The packet consequently required a Fact that its own incorrectly stale chart filter omitted.

The stale-data gate was not the bug and remains unchanged. The upstream session date was wrong.

## Pipeline Trace

| Layer | Module / function | Input | Output | Nullable or fail condition |
|---|---|---|---|---|
| Raw OHLCV | `OhlcvClient.fetch_price_context` | adjusted daily/weekly/monthly bars | price and chart context | provider failure or no bars |
| Zone selection | `select_nearest_meaningful_zones` | classified zones | nearest Strong/Medium support/resistance | no valid zone |
| Invalidation | `calculate_invalidation` | nearest support, ATR, bars | chart invalidation | monthly-only/unsupported or no support |
| RR calculation | `calculate_risk_reward` | current price, nearest resistance, invalidation | current and support scenarios | missing resistance/invalidation or non-positive dimensions |
| Monitoring state | `build_monitoring_state` | deterministic price structure | current/previous/delta RR | preserves current and previous separately |
| Canonical Fact | `_chart_facts` | usable chart structure | `chart:structure:risk_reward:current_price` | stale/unavailable chart is denied |
| Packet | `_fact_catalog` / `build_ai_review_packet` | canonical Facts and state | immutable stock packet | no alternate RR calculation |
| Registry | `build_numeric_registry` | exact Fact field | semantic, unit, display variants | unknown field semantic denied |
| Binder | `bind_numeric_fact_references` | packet registry and draft refs | schema-4 numeric claims | exact Fact/field/semantic required |
| Validator | `_validate_stock_review` | claims and grounding requirements | PASS/reject | missing required Fact or numeric claim rejects |
| Renderer | `_render_ai_stock_message` | validated schema-4 review | Telegram-style text | does not calculate or repair RR |

## Natural Versus Prior Packet

The previous packet `2026-08-16-kr-run-21-049f367f0274` used the same 2026-08-14 chart context and
the same RR values, but the weekday logic still considered 2026-08-14 current and marked it fresh.
That path emitted both current-price and support-entry scenario Facts.

| Ticker | Run-23 current price | Current RR | Run-21 Fact | Run-23 Fact before |
|---|---:|---:|---|---|
| 005490 POSCO Holdings | 334,000 | 0.167780 | present | missing |
| 010120 LS ELECTRIC | 206,500 | 0.318131 | present | missing |
| 012450 Hanwha Aerospace | 1,160,000 | 0.152999 | present | missing |
| 086280 Hyundai Glovis | 211,000 | 0.466189 | present | missing |

## Unaffected Controls

Samsung Electronics had no valid support/invalidation, Korean Re had no valid resistance, and SK
hynix had no valid support/invalidation. All three remain `UNAVAILABLE_BY_CONTRACT`; no RR Fact is
required and no value is fabricated.

## Fix

`market_session.py` now uses XKRX and XNYS exchange calendars for session and previous-session
dates. On 2026-08-17 it returns `closed` with latest completed KRX session 2026-08-14. The existing
freshness logic then emits the already calculated RR Fact and the existing semantic registry builds
the exact numeric path. No validator, renderer, RR formula, zone selection, or stale-data policy was
relaxed.
