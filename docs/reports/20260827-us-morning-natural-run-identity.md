# 2026-08-27 US Morning Natural Run Identity

## Verdict

The naturally scheduled US run was observed. It completed the `2026-08-26` US regular session, created one current packet, and delivered one 14-message set. This proof is read-only.

| Field | Evidence |
|---|---|
| Work instruction commit | `5377d5e4f15a82e01ac40b6d50d47eee9ef0a30c` |
| Natural monitor run | `41` / `daily_us` / `success` |
| Natural start | `2026-08-27 08:05:32.498218 KST` |
| Natural completion | `2026-08-27 08:06:28.979332 KST` |
| Producer / operating SHA | `95553b931150f4dd61573888e9fa94198eb43041` |
| Target completed session | `2026-08-26` |
| Subjects | `13/13` success, `0` failures |
| Packet | `2026-08-27-us-run-41-ae4f42c23abc` |
| Packet generated | `2026-08-27 08:20:05.622361 KST` |
| Packet persisted / ready | `2026-08-27 08:20:09 KST` |
| Final claim | `47434507-ac80-48ed-95f0-ea1fb91abe83` by `codex-us-backup` |
| Route | `AI` / `ai_assisted` |
| Dispatch | `2026-08-27 08:40:06.173291 KST` |
| Delivery IDs | `330` through `343` |
| Receipt | message-quality SHA `7ccd87d606ab37d1658f3d4799094cced2b0d21f8e1fe7b3041a588d63846082` |

The canonical `main` reflog proves `95553b9` was operating from `00:44:35 KST`; `ae4d22a` was not fast-forwarded until `08:56:59 KST`. The run therefore exercised the already-promoted Track A code in `95553b9`, not a later report commit.

## Schedule Identity

- Producer LaunchAgent: `python -m app.jobs.monitor_daily --market us`, configured at `08:05`, `08:10`, `08:15`, and `08:20` KST.
- US primary automation: `thesis-monitor-ai-review-us-primary`, configured `08:15` KST.
- US backup automation: `thesis-monitor-ai-review-us-backup`, configured `08:30` KST.
- Deterministic fallback deadline: `08:40` KST.

No task was manually triggered for this review.

`US_MORNING_NATURAL = MATERIAL_P1_FOUND_STOP` because delivery occurred correctly but omitted material same-session market evidence. See the evidence-utilization and readiness reports.
