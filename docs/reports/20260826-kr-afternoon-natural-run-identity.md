# 2026-08-26 KR Afternoon Natural Run Identity

## Verdict

`KR_AFTERNOON_NATURAL = MATERIAL_P1_FOUND_STOP`

The scheduler, monitor run, three natural packet refreshes, and deadline fallback all occurred without a manual run. The natural market digest was not KR local-first, so this track cannot claim `LIVE_PASS`.

## Identity

| Item | Value |
|---|---|
| Work-instruction SHA | `e76a7d6b5e8ddc110d3228cfd5e55f26dbdb1e1d` |
| Natural producer SHA | `2984d7658b79d9c09d43e23929b71719f88a8c82` |
| Monitor LaunchAgent | `com.seungsoo.thesis-monitor.kr-close` |
| Monitor schedule | `16:05`, `16:20`, `16:50 KST` |
| AI primary / backup | `thesis-monitor-ai-review-kr-primary` 16:15 / `thesis-monitor-ai-review-kr-backup` 16:55 KST |
| Monitor run | `40`, `daily_kr`, success `7/7` |
| Start / finish | `2026-08-26 16:05:32.199228` / `16:06:11.541547 KST` |
| Target session | `2026-08-26` |
| Active packet | `2026-08-26-kr-run-40-706bc3003536` |
| Active packet generated | `2026-08-26 16:50:05.381887 KST` |
| Fallback start | `2026-08-26 17:10:02.717493 KST` |
| Final delivery | deterministic fallback, `8/8` |

The producer SHA was the operating `main` from 15:03:13 until 17:10:01 KST. The 16:05 monitor and 16:55 reviewer therefore started from that checkout; the later promotion occurred after both starts.

Three immutable packet snapshots were generated from run 40 at 16:06, 16:20, and 16:50. Only the latest snapshot owned the held delivery intent. All three had `ready_for_ai=false` because the shadow numeric-semantic gate was incomplete; deterministic delivery eligibility remained true.
