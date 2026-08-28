# 2026-08-29 Korea Night Futures Gate

- Execution time (KST): `2026-08-29T08:27:23+09:00`
- Latest completed US session: `2026-08-28`
- Next relevant KR regular session: `2026-08-31`
- Expected night-futures session (06:00 end-date basis): `2026-08-29`
- KOSPI200: `NOT_READY` (`expected_session_absent`)
- KOSDAQ150: `NOT_READY` (`expected_session_absent`)
- Canonical gate used: `PASS`
- Raw summary bypass: `0`
- Stale prior-session values visible: `0`
- Empty section visible: `0`

| Role | Observed | Expected | Returned night session | Terminal state | Ready |
| --- | --- | --- | --- | --- | --- |
| production_gate_attempt_1 | 2026-08-29T08:06:49.479105+09:00 | 2026-08-29 | 2026-08-28 | STALE_PRIOR_SESSION_PRESENT | 0 |
| production_gate_attempt_2 | 2026-08-29T08:10:05.294475+09:00 | 2026-08-29 | 2026-08-28 | STALE_PRIOR_SESSION_PRESENT | 0 |
| production_gate_attempt_3 | 2026-08-29T08:15:05.302446+09:00 | 2026-08-29 | 2026-08-28 | STALE_PRIOR_SESSION_PRESENT | 0 |
| production_gate_attempt_4 | 2026-08-29T08:20:06.267187+09:00 | 2026-08-29 | 2026-08-28 | STALE_PRIOR_SESSION_PRESENT | 0 |

All four production-gate attempts found only the 2026-08-28 prior night session. The current candidate therefore omits the entire night-futures section.
