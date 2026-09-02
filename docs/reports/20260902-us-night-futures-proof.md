# US Night Futures Proof

| Attempt | Start | Instrument | Target | Returned | Row state | Ready | Rendered |
| --- | --- | --- | --- | --- | --- | --- | --- |
| production_gate_attempt_3 | 2026-09-02T08:15:06.748799+09:00 | KOSPI200 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_3 | 2026-09-02T08:15:06.748799+09:00 | KOSDAQ150 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| observer_post_deadline_0845 | 2026-09-02T08:45:06.350257+09:00 | KOSPI200 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| observer_post_deadline_0845 | 2026-09-02T08:45:06.350257+09:00 | KOSDAQ150 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_1 | 2026-09-02T08:06:49.595589+09:00 | KOSPI200 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_1 | 2026-09-02T08:06:49.595589+09:00 | KOSDAQ150 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_2 | 2026-09-02T08:10:07.717614+09:00 | KOSPI200 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_2 | 2026-09-02T08:10:07.717614+09:00 | KOSDAQ150 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_4 | 2026-09-02T08:20:07.631395+09:00 | KOSPI200 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |
| production_gate_attempt_4 | 2026-09-02T08:20:07.631395+09:00 | KOSDAQ150 | 2026-09-02 | 2026-09-01 | STALE_PRIOR_SESSION_PRESENT | NOT_READY | NO |

All four production gates received HTTP 200 and only stale prior-session rows for both configured products. No current product became eligible; omission was correct. The 08:45 observer reproduced the same source limitation without production mutation.

- `US_NIGHT_FUTURES_EXPECTED_COUNT = 2`
- `US_NIGHT_FUTURES_READY_COUNT = 0`
- `US_NIGHT_FUTURES_RENDERED_COUNT = 0`
- `US_NIGHT_FUTURES_STATUS = SOURCE_LIMITATION_SAFE`
