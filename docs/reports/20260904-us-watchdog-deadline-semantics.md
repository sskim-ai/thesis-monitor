# US Watchdog and Deadline Semantics

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

| Timer | Configuration | Actual basis/result | Expired at 08:20? |
| --- | --- | --- | --- |
| Primary readiness poll | up to 300s, 15s polling | packet already ready; claim returned immediately | no |
| Primary claim lease | 10 minutes | claim write bounded by `08:16:05.870..08:16:08.184`; expiry bounded by `08:26:05.870..08:26:08.184` | no |
| Backup activation | daily at 08:30 | task `08:30:15.594`, new claim `08:30:39.046046` | no |
| Backup lease | default 30 minutes | expires `09:00:39.046046` | no |
| V2 canary subprocess | default command timeout 1800s | both were manually interrupted after repeated network waits | no |
| Hard fallback | daily at 08:40 | dispatch `08:40:04.201264` | no |
| Telegram timeout | not present in captured natural artifacts | sends completed sequentially | unknown |

Lease expiry did not invalidate primary by itself. It became stale only when backup wrote a new claim. There is no liveness grace or heartbeat predicate in this path.
