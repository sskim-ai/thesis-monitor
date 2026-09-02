# US Macro Temporal Safety

| Series | Value/change | Observation | Source | Quality | Temporal role |
| --- | --- | --- | --- | --- | --- |
| 미국 기대인플레이션 | 2.35 | 2026-09-01 00:00:00 | verified_macro_briefing | fresh | CURRENT_OBSERVATION |
| 미국 하이일드 신용스프레드 | 2.63 | 2026-08-31 00:00:00 | verified_macro_briefing | fresh | CURRENT_OBSERVATION |
| 원/달러 환율 | 1370.4 | 2026-09-01 00:00:00 | verified_macro_briefing | fresh | REFERENCE_LAGGING |
| 미국 10년물 금리 | 4.75 | 2026-08-31 00:00:00 | verified_macro_briefing | fresh | CURRENT_OBSERVATION |
| WTI 유가 | 83.9 | 2026-08-25 00:00:00 | verified_macro_briefing | fresh | REFERENCE_LAGGING |
| 미국 10년물 실질금리 | 2.44 | 2026-08-31 00:00:00 | verified_macro_briefing | fresh | CURRENT_OBSERVATION |
| VIX | 14.92 | 2026-08-31 00:00:00 | verified_macro_briefing | fresh | CURRENT_OBSERVATION |

Real yield used the official `DFII10` observation dated `2026-08-31`, marked `CURRENT_OBSERVATION` and eligible for today's signal. Lagging WTI and USD/KRW were reference-only and were not promoted to current directional claims.

`US_REAL_YIELD_TEMPORAL_SAFETY = PASS`
