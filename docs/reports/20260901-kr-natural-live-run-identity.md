# KR Natural Live Run Identity

## Identity

- Run ID: `50` (`daily_kr`)
- Canonical session: `2026-09-01`, after-hours
- Source monitor: `2026-09-01 07:05:31.662051Z` to `2026-09-01 07:06:32.443168Z`
- Source result: `success`, `8/8`, failures `0`
- Evidence cutoff: `2026-09-01T07:05:31.662051+00:00`

## Natural packets

| Role | Packet | Generated KST | Claim owner | Claimed KST |
| --- | --- | --- | --- | --- |
| Primary source packet | `2026-09-01-kr-run-50-a601ddc0620a` | `2026-09-01T16:06:32.456960+09:00` | `codex-kr-primary` | `2026-09-01T16:17:05.091880+09:00` |
| Intermediate retry packet | `2026-09-01-kr-run-50-a90e46db30c9` | `2026-09-01T16:20:06.889180+09:00` | unclaimed | - |
| Backup/dispatch packet | `2026-09-01-kr-run-50-44156fe0fa76` | `2026-09-01T16:50:07.017282+09:00` | `codex-kr-backup` | `2026-09-01T16:56:06.980559+09:00` |

Final dispatch used `2026-09-01-kr-run-50-44156fe0fa76`. The production cohort was frozen once at the run-50 cutoff; all three packet instances contain the same eight tickers.
