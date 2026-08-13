# OHLCV Chart Knowledge Integration Validation

## Scope

- Base: `e97eaaca4d3dc454628b9303f216395e96ab3e37`
- Analysis policy: `daily-review-v3.3`
- AI output schema: `3`
- Delivery renderer: `ai-assisted-pilot-renderer-v2`
- Investment Knowledge: v3.0, unchanged SHA
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge: v1.0, SHA
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

The user-provided 2,472-line, 51,132-byte Chart Knowledge source was copied byte-identically to:

- `docs/knowledge/stock-chart-value-analysis-knowledge-v1.md`
- `.agents/skills/thesis-monitor-daily-review/references/stock-chart-value-analysis-knowledge-v1.md`

It was not merged into Investment Knowledge v3.

## Precedence

1. Backend validated facts and calculations
2. Investment Knowledge v3 data-safety and valuation rules
3. OHLCV Analyst validated outputs
4. Chart Knowledge interpretation framework
5. Examples and implementation suggestions

Codex does not calculate indicators, support/resistance, valuation, target/stop levels, or new derived
metrics. Chart Knowledge fair-value and risk/reward examples cannot override backend valuation or the
Investment Knowledge safety rules.

## Production Contract Inventory

Live read-only probe: 2026-08-13 KST, active universe discovered dynamically from the operational DB.

| Field | Result | Detail |
| --- | --- | --- |
| Daily / weekly / monthly | Available | All three timeframes for 20/20 active tickers |
| Current OHLC candle | Available | Open, high, low, close, volume, raw trading value |
| Price basis | Available | Adjusted chart context; unadjusted weekly history remains valuation-only |
| Bollinger bands | Partial | 19/20; `SKHY` lacks sufficient long-band output |
| Candle features | Available | Body, range, close location, upper/lower wick calculated deterministically from provider OHLC |
| Volume ratio | Available | Provider `VOLUME_RATIO_20` |
| Trading-value ratio | Unavailable | Raw value exists, ratio does not; raw value is prose-denied |
| RSI | Available | Provider `RSI14` |
| MACD | Available | MACD, signal, histogram |
| Korean supply | Available | 1-day, 5-day, 20-day flows for 7/7 KR tickers |
| US supply | Unavailable | Not supplied by the current OHLCV contract |
| Dynamic support/resistance | Unavailable | No contract field; not inferred |
| Box ranges | Unavailable | No contract field; not inferred |
| ATR | Unavailable | No contract field; not calculated in AI review |
| Elliott / Fibonacci | Unavailable | No validated contract output |
| Risk/reward | Unavailable | No validated entry/target/stop contract |
| Chart state machine | Unavailable | No validated contract output |

## Active-Universe Smoke

- Active: 20
- KR: 7
- US: 13
- Full daily/weekly/monthly chart contract: 20
- Partial: 0
- Unavailable: 0
- Fresh completed-session chart context: 20
- Korean supply context: 7

Tickers probed: `000660`, `003690`, `005490`, `005930`, `010120`, `012450`, `086280`,
`CORZ`, `CRCL`, `GOOGL`, `HUT`, `IBM`, `MU`, `RXRX`, `SKHY`, `SNDK`, `TSLA`, `TSM`,
`WRD`, `WULF`.

## Packet and Routing

Each stock packet now contains compact `chart_context` with source, as-of date, quality, adjusted price
basis, daily/weekly/monthly summaries, explicit unavailable fields, persistent thesis price rules, and a
deterministic price transition. Raw bar arrays are not included.

Fresh or provisional chart context routes only the available Chart Knowledge sections. Stale chart
timeframes are retained as audit context but do not create chart facts, numeric registry entries, or
required chart frameworks. Missing optional indicators stay unknown.

Price-rule transitions are thesis-version isolated. Supported events include confirmation crossed or
failed, support entered/reclaimed/broken, warning crossed, and invalidation crossed. A transition changes
the price discussion, not the deterministic business-thesis status. Persistent thesis rules are never
written by Codex.

## Numeric Semantics

Chart open/high/low/close, candle percentages, Bollinger levels/distances, volume ratio, RSI, MACD,
stored price rules, and rule distances have explicit fail-closed semantic registrations. Flow semantics
are distinct for investor and 1/5/20-day horizon. Unknown chart semantics and raw trading value cannot
appear in prose.

KRW compact display is limited to amount semantics such as revenue, operating income, contract amount,
and market cap. Per-share values and chart prices cannot be rendered as nonsensical `0억원` variants.
Backend-approved multiple rounding permits a provider ratio such as `0.805318...` to display as `0.81배`.

## Regression Result

- Focused Phase 4 tests: 70 passed
- Full test suite: 525 passed, 1 third-party deprecation warning
- No DB migration
- Public Action schema unchanged
- Investment Knowledge v3 unchanged
- Deterministic assessment and Telegram remain the official source of truth
