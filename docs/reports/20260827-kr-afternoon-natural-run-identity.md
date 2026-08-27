
# 2026-08-27 KR Afternoon Natural Run Identity

## Verdict

`KR_AFTERNOON_NATURAL = LIVE_PASS`

The natural KR close producer, backup reviewer, and 17:10 deadline dispatcher all completed without a manual run. The final immutable packet represented the completed 2026-08-27 XKRX session and delivered eight AI-assisted messages.

## Identity

| Item | Value |
|---|---|
| Work-instruction SHA | `107f40b0b6b7e794f420534e71b69af0c969e643` |
| Natural producer / operating SHA | `a1fb1a7006109f8699e03997662bde27db5ad464` |
| Producer LaunchAgent | `com.seungsoo.thesis-monitor.kr-close` |
| Producer schedule | `16:05`, `16:20`, `16:50 KST` |
| AI task | `thesis-monitor-ai-review-kr-backup`, 16:55 KST |
| AI claim owner / ID | `codex-kr-backup` / `c5eb6c5c-c618-4a5c-9c29-546e3e0cfcd6` |
| Deadline dispatcher | `com.seungsoo.thesis-monitor.ai-review-fallback`, 17:10 KST |
| Monitor run | `42`, `daily_kr`, success `7/7` |
| Natural start / completion | `2026-08-27T16:05:30.969552+09:00` / `2026-08-27T16:06:11.413129+09:00` |
| Target session | `2026-08-27` completed session |
| Final packet | `2026-08-27-kr-run-42-5d8d23e6fbd6` |
| Packet generated | `2026-08-27T07:50:05.896365+00:00` |
| Packet ready | `2026-08-27T17:05:34.983787+09:00` |
| Route / delivery | `AI` / `ai_assisted`, `8/8` |
| Kiwoom provider calls | `42` requests, `42` successes, `0` failures, `0` retries |

## Immutable Packet Refreshes

| Packet | Generated | ready_for_ai | Disposition |
|---|---|---|---|
| 2026-08-27-kr-run-42-6d4c6aa909c1 | 2026-08-27T07:06:11.422161+00:00 | true | HELD_SUPERSEDED |
| 2026-08-27-kr-run-42-8c8b4c0e254d | 2026-08-27T07:20:04.742060+00:00 | true | HELD_SUPERSEDED |
| 2026-08-27-kr-run-42-5d8d23e6fbd6 | 2026-08-27T07:50:05.896365+00:00 | true | DELIVERED |

The three snapshots are expected producer refreshes over completed run 42. Only the 16:50 snapshot became the delivery owner; the prior two were never sent.
