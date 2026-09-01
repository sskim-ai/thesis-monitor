# KR Scheduler Ownership

## Natural ownership

| Producer | Schedule / claim | Packet |
| --- | --- | --- |
| KR source producer | LaunchAgent `16:05`, `16:20`, `16:50` | run 50 packets |
| Primary AI task | scheduled `16:15`; claimed `2026-09-01T16:17:05.091880+09:00` | `2026-09-01-kr-run-50-a601ddc0620a` |
| Backup AI task | scheduled `16:55`; claimed `2026-09-01T16:56:06.980559+09:00` | `2026-09-01-kr-run-50-44156fe0fa76` |
| Fallback | LaunchAgent `17:10` | `2026-09-01-kr-run-50-44156fe0fa76` |

- Same packet owned by multiple producers: `0`
- Unowned retry: `0`
- Manual task trigger: `0`
- Manual Telegram send: `0`

The intermediate 16:20 packet was not claimed. Primary and backup owned different immutable packet IDs, so there was no claim collision.
