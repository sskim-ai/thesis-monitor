# 2026-08-28 US Morning Natural Run Identity

## Verdict

The naturally scheduled US run was observed and completed the `2026-08-27` regular session. Operating SHA `910e2f7e78b3d5445e5caa46c605fa85a76c43b2` produced one current packet and one final 14-message set. This review was read-only.

| Field | Evidence |
|---|---|
| Work instruction commit | `18d36852f74a6a1609365cbcb5dc093feb293e71` |
| Natural monitor run | `43` / `daily_us` / `success` |
| Natural start | `2026-08-28 08:05:33.497001 KST` |
| Natural completion | `2026-08-28 08:06:34.221788 KST` |
| Subjects | `13/13` success, `0` failures |
| Target completed session | `2026-08-27` |
| Packet | `2026-08-28-us-run-43-c086d78415ac` |
| Packet generated | `2026-08-28 08:20:04.853188 KST` |
| Packet persisted / ready | `2026-08-28 08:20:09 KST` |
| Final claim | `350f0a86-3294-4231-bfd7-bdb4f983647a` by `codex-us-primary` |
| AI automation | `08:16:32` to `08:31:29 KST` |
| Route | `AI` / `ai_assisted` / Pilot `5/5` |
| Dispatch window | `08:30:01` to `08:30:19 KST` |
| Delivery IDs | `352` through `365` |
| Runtime receipt | `88100d19851a17b9e414f620cb1c9b222b57eb1f81f6337c3f6ecc9e7db382d4` |

The `main` reflog moved to `910e2f7` at `02:52:12 KST`, before the run. No later main promotion preceded the `08:05` producer. Scheduler identity was the US daily LaunchAgent at `08:05/08:10/08:15/08:20`; the AI owner was the `08:15` primary automation and the fallback deadline remained `08:40`.

```text
US_MORNING_NATURAL = LIVE_PASS
TARGET_SESSION = 2026-08-27
```
