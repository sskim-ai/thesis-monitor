# Chart Knowledge Routing Index

Read [stock-chart-value-analysis-knowledge-v1.md](stock-chart-value-analysis-knowledge-v1.md) only when the packet's `chart_knowledge_routing.available` is true. Backend facts and Investment Knowledge v3 always take precedence.

## Core Route

- `chart_principles`: Sections 0-2. Good company, good chart, and good entry price are distinct.
- `chart_holder_new_buyer`: Section 2. Separate a new observer's entry risk from a holder's thesis management.
- `chart_multi_timeframe`: Section 19. Use only available daily, weekly, and monthly summaries.
- `chart_supply`: Section 16. Combine verified 1-day, 5-day, and 20-day horizons.
- `chart_data_quality`: Sections 0 and 55. Missing or stale data remains Unknown.

## Selective Route

- `chart_bollinger`: Sections 4-6. Use provider values and user-friendly band names; do not recalculate.
- `chart_candle_volume`: Sections 9-10. Interpret candle and volume jointly.
- `chart_rsi`: Section 11. Overbought and oversold are not automatic orders.
- `chart_macd`: Section 12. Separate short and long timeframes when both exist.
- `chart_threshold_transition`: Sections 20-21 only as interpretation vocabulary. State names are not user commands.

## Unavailable Route

Do not load or apply support/resistance, box, ATR, Elliott, Fibonacci, risk/reward, or chart-state sections unless the packet explicitly provides validated outputs. Never derive fair PBR, expected return, value price, target, stop, or invalidation from this reference.
