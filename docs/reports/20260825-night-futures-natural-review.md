# 2026-08-25 Night-Futures Natural Review

- Expected NIGHT BAS_DD: `2026-08-25`
- Preceding eligible DAY: `2026-08-24`
- Terminal: `NOT_READY_WITHIN_OBSERVER_HORIZON`

| Start | Role | HTTP | Returned dates | Raw | Parsed | Candidates | Ready | Product result |
|---|---|---|---|---:|---:|---:|---:|---|
| 2026-08-25T08:06:30.050656+09:00 | production_gate_attempt_1 | 200 | 2026-08-21,2026-08-24 | 770 | 16 | 0 | 0 | KOSPI200 A0169000 2026-09 expected_session_absent; KOSDAQ150 A0669000 2026-09 expected_session_absent |
| 2026-08-25T08:10:05.583824+09:00 | production_gate_attempt_2 | 200 | 2026-08-21,2026-08-24 | 770 | 16 | 0 | 0 | KOSPI200 A0169000 2026-09 expected_session_absent; KOSDAQ150 A0669000 2026-09 expected_session_absent |
| 2026-08-25T08:15:07.102535+09:00 | production_gate_attempt_3 | 200 | 2026-08-21,2026-08-24 | 770 | 16 | 0 | 0 | KOSPI200 A0169000 2026-09 expected_session_absent; KOSDAQ150 A0669000 2026-09 expected_session_absent |
| 2026-08-25T08:20:06.543338+09:00 | production_gate_attempt_4 | 200 | 2026-08-21,2026-08-24 | 770 | 16 | 0 | 0 | KOSPI200 A0169000 2026-09 expected_session_absent; KOSDAQ150 A0669000 2026-09 expected_session_absent |
| 2026-08-25T08:45:06.073682+09:00 | observer_post_deadline_0845 | 200 | 2026-08-21,2026-08-24 | 770 | 16 | 0 | 0 | KOSPI200 A0169000 2026-09 expected_session_absent; KOSDAQ150 A0669000 2026-09 expected_session_absent |
| 2026-08-25T09:15:03.585706+09:00 | observer_horizon_0915 | 200 | 2026-08-21,2026-08-24 | 770 | 16 | 0 | 0 | KOSPI200 A0169000 2026-09 expected_session_absent; KOSDAQ150 A0669000 2026-09 expected_session_absent |

All six attempts preserved raw references and SHA values. The provider returned only stale NIGHT dates `2026-08-24` and `2026-08-21`; the expected `2026-08-25` session was absent. No stale value entered the digest.

`NIGHT_FUTURES_TELEMETRY_GAP = LIVE_EVIDENCE_CAPTURE_PASS`

`FAIL_CLOSED_SAFETY = PASS`

`DEADLINE_VERDICT = DEADLINE_UNPROVEN`
