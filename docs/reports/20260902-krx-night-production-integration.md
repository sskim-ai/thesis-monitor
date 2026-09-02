# KRX Night Production Integration

The existing official KRX provider now preserves successful raw response bytes, incrementally stores valid FINAL NIGHT bars, and attaches same-contract D/W/M sidecars when available. Source/history failures are warnings and never block stock V2. No scheduler timing or ownership changed. Retention remains the repository data lifecycle; no destructive cleanup was introduced.

`KRX_NIGHT_COLLECTOR_FAILURE_BLOCKS_STOCK_V2 = 0`
`NIGHT_DWM_FRESHNESS_CONTRACT = PASS`
