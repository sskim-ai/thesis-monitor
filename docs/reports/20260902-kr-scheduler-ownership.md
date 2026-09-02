# KR Scheduler Ownership

| Role | Natural time | Packet | Owner | Claim time | Outcome |
| --- | --- | --- | --- | --- | --- |
| source monitor | 16:05 KST | `2026-09-02-kr-run-52-fb35c544f33a` | `kr_daily_production` | n/a | held 9 |
| source monitor refresh | 16:20 KST | `2026-09-02-kr-run-52-1b83c3e7e18e` | `kr_daily_production` | n/a | unclaimed |
| source monitor refresh | 16:50 KST | `2026-09-02-kr-run-52-d077cd42b44c` | `kr_daily_production` | n/a | held 9 |
| primary AI | 16:15 schedule | `2026-09-02-kr-run-52-fb35c544f33a` | `codex-kr-primary` | `2026-09-02T07:18:02.049979+00:00` | validation rejected after delivery cutoff |
| backup AI | 16:55 schedule | `2026-09-02-kr-run-52-d077cd42b44c` | `codex-kr-backup` | `2026-09-02T07:56:45.049056+00:00` | validation rejected; fallback preserved |
| fallback | 17:10 KST | `2026-09-02-kr-run-52-d077cd42b44c` | deterministic dispatcher | n/a | sent 9/9 |

Both claims owned different immutable packets. No manual task, resend, requeue, orphan reconciliation, or unowned retry occurred.
