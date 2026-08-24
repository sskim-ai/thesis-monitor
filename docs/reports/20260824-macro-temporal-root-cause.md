# 2026-08-24 Macro Temporal Root Cause

## Trigger Identity

- Packet: `2026-08-24-us-run-35-d2db44ff620a`
- Packet generated: `2026-08-23T23:20:06.238019+00:00`
- Macro briefing as-of: `2026-08-23 23:05:01.178827`
- Market session: `closed`, assessment state `final`
- Delivery: deterministic fallback, 14/14 sent at `2026-08-24T08:40:05.378920+09:00`
- AI sent: 0; later validation receipt recorded a separate unsupported TSLA numeric semantic error
- Immutable archive writes by this repair: 0

## Root Cause

`ROOT_CAUSE_BRANCH = B`

The observation layer had exact dates, provider identity, market session, and source-level
freshness. The missing concept was **new since the prior briefing for this message role**. The
digest, thesis daily signal, shocks, ticker impacts, market Fact ranking, and renderer checked only
`quality_status in {fresh,revised}`. Consequently valid but unchanged observations were replayed as
new daily movements.

On the Sunday-night cutoff, the latest cash-equity observations were Friday 8/21, while VIX was
8/20 and WTI was 8/18. All remained provider-`fresh`, so the fallback emitted them under `오늘` and
`중요한 변화`, and old regime-axis values generated non-neutral market-thesis daily signals.

## Repair

- New derived contract: `macro-digest-temporal-eligibility-v1`.
- Per-series roles: current, prior market session, reference lagging, stale for daily signal, or
  unavailable.
- Session-bound prices compare with the XNYS completed-session calendar and prior briefing.
- Release-bound series compare official occurrence identity with the prior briefing.
- ECOS KeyStatistic USD/KRW is reference-only because its stored date is collection date.
- Daily axes, shocks, thesis signals, ticker impacts, key-change Facts, and transmissions use
  current observations only.
- Prior session prices remain available with `직전 거래일(M/D)` labeling.
- Regime/state remains available as background.
- AI and fallback consume the same decision, and semantic validation enforces wording role.

No validator threshold, price/RR logic, valuation rule, night-futures contract, KRX integration,
working-capital mode, or production operation was changed.

## Changed Runtime Functions

- `app/macro/temporal.py`: role classification, context aggregation, daily axes, previous-briefing
  comparison.
- `app/macro/service.py::run_macro_monitor`: one context fan-out to shocks, theses, impacts, briefing.
- `app/macro/theses.py::update_macro_theses`: current-only daily axes.
- `app/macro/shocks.py::assess_macro_shocks` and
  `app/macro/impact.py::assess_thesis_macro_impacts`: current-series gate.
- `app/macro/briefing.py::build_macro_briefing`: preserve frequency, role, context, safe daily signal.
- `app/services/daily_digest.py::_important_changes/_macro_interpretation`: temporal selection,
  labeling, no-new-signal path.
- deterministic/notification/AI renderers: dynamic current/prior headings.
- `app/services/market_intelligence_service.py`: temporal Fact fields, current key/transmission IDs.
- `app/services/ai_review_service.py::_macro_temporal_semantic_errors`: wording-role hard gate.
- `app/services/market_session.py::us_market_session`: authoritative XNYS early-close completion.
