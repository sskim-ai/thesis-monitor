# KRX 08:05 Natural Telemetry Review

## 2026-08-22 result

- Scheduled slot: `2026-08-22 08:05 KST`
- LaunchAgent: loaded, runs 4 total, last exit code 0; log modified at `08:05:05 KST`.
- Job result: `SKIPPED`
- Reason: `not_normal_xkrx_session`
- Intended preceding XKRX target: `2026-08-21`; constructed request target: null because the current-date session check returned first.
- Observation ID: null
- Provider calls / HTTP / provider dates / row counts / eligible rows: `0 / null / null / null / null`
- Readiness / promotability: `SKIPPED / null`
- Raw refs and SHA: null
- Telemetry write: 0; duplicate write: 0; user-visible integration: false

The exact-slot job checks whether the current calendar date is an XKRX session before applying the `NEXT_MORNING_0805` preceding-session rule. Saturday 08:05 was therefore skipped even though the intended subject was Friday's completed session. This is the same date-gate defect observed in the night-futures observers.

## Prior natural comparison

- 2026-08-21 16:05 for target 2026-08-21: all four official endpoints HTTP 200 with zero rows; `MARKET_COMPLETED_PROVIDER_PENDING`; artifact SHA `39cb67d26602b5da2e1272711a00721f5f0c0e59e2c527d1ee6ae5440ce88b7e`.
- 2026-08-21 08:05 for target 2026-08-20: `PROVIDER_COMPLETE`; KOSPI stocks 942, KOSDAQ stocks 1,821, KOSPI indices 51, KOSDAQ indices 40.
- Today's missing capture cannot strengthen or contradict the provider publication pattern.

`KRX_CAPTURE_PLUMBING = FAIL`

`KRX_PUBLICATION_PATTERN = UNCHANGED`

This is a material P1 capture-plumbing issue. It is fail-closed, caused no user-visible KRX output, and is not a data-correctness P0.
