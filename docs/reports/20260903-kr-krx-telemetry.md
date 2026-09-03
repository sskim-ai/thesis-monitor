# 2026-09-03 KR KRX Telemetry

## Exact-Slot Observation

- Scheduler: `com.seungsoo.thesis-monitor.krx-publication-telemetry`
- Slot: `SAME_DAY_CLOSE_1605`
- Scheduled: `2026-09-03T16:05:00+09:00`
- Observed: `2026-09-03T07:05:05.526690Z`
- Exit code: 0
- State: `MARKET_COMPLETED_PROVIDER_PENDING`
- Current snapshot promotable: false
- Reason: `all_core_endpoints_returned_empty_200`

| Endpoint | HTTP | Rows | Provider dates | State |
|---|---:|---:|---|---|
| `sto/stk_bydd_trd` | 200 | 0 | none | EMPTY |
| `sto/ksq_bydd_trd` | 200 | 0 | none | EMPTY |
| `idx/kospi_dd_trd` | 200 | 0 | none | EMPTY |
| `idx/kosdaq_dd_trd` | 200 | 0 | none | EMPTY |

The independent KRX publication telemetry therefore had transport success 4/4 but publication completeness 0/4 at 16:05. Production continued with current Kiwoom structured market context; the primary invocation recorded 42 requests, 42 successes, 0 failures, and 0 retries.

## Night Futures

The natural packet's night-futures audit expected session `2026-09-02`. Both `KRX_KOSPI200_NIGHT_FUT` and `KRX_KOSDAQ150_NIGHT_FUT` were unavailable, had no source session or fact ID, and were neither selected nor rendered.

- `BAS_DD=20260903 NIGHT`: not present in the telemetry artifacts
- Raw provider date labels: empty
- User-visible night futures: 0

No session-date mapping was changed and no provider was called by this extraction.

