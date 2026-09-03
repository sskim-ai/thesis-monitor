# 2026-09-03 US Renderer and Message Consistency

No accepted-ready V2 stock message was rendered. The deterministic fallback
produced 14 stock messages without synthetic V2 decision or balance lines.

| Metric | Count |
| --- | ---: |
| accepted-ready stock messages | 0 |
| explicit V2 decisions | 0 |
| visible BUY:SELL balances | 0 |
| fallback stock messages | 14 |
| common order disclaimer occurrences | 0 |

The exact fallback payload passed its own quality and archive equality checks.
This proves fail-safe consistency, not V2 renderer readiness.

- `COMMON_ORDER_DISCLAIMER_OCCURRENCE = 0`
- `US_RENDERER_V2_NATURAL = NOT_REACHED`
- `US_FALLBACK_RENDERER = PASS`

