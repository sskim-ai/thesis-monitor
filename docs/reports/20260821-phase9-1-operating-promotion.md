# 2026-08-21 Phase 9.1 Operating Promotion

## Repository

| Field | Result |
|---|---|
| Previous main / operating | `33c2f8be376b2cbb2961ecf9dc3c873715e0a034` |
| Phase 9.1A final | `d4a4daf08ff5f68bc1072cc065e69ca5de5da145` |
| Phase 9.1B final | `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6` |
| Phase 9.1C final | `d0dc76a2446ee5ef9188d1b06dcb241df004c143` |
| Final `origin/main` | `d0dc76a2446ee5ef9188d1b06dcb241df004c143` |
| Final operating HEAD | `d0dc76a2446ee5ef9188d1b06dcb241df004c143` |
| Promotion method | clean fast-forward of exact Phase 9.1C final |
| Operating worktree | clean, `main...origin/main` |
| Runtime/user-visible diff | `0` |

Only the Phase 9.1 chain was promoted. The review instruction and review reports remain on `codex/20260821-combined-natural-review-promotion-gate`.

## Post-promotion smoke

- Working-capital focused suites: `60 passed in 0.30s`
- API restart: `NO`; new modules are not imported by production runtime paths
- API `/health`: `{"status":"ok"}`
- Public Action: `0.4.5`
- Output schema: `4`
- operationId: `20/20` unique
- Phase 9.0E mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- AI schedules: unchanged
- KRX telemetry schedule: unchanged
- Night-futures collector configuration: unchanged

Configuration hashes before and after promotion were identical:

```text
020df8c4d3c2a9bfe5e49dea3cff506552c1798fcd4916f07155a68a600505ee  com.seungsoo.thesis-monitor.daily.plist
d80181cb5f54d5e2d9758047fe2dea8f2aaf1fae6f9c1f120b97a5b7400813b9  com.seungsoo.thesis-monitor.krx-publication-telemetry.plist
```

## Operating safety

- Manual Telegram: `0`
- Manual Scheduled Task: `0`
- Manual natural run: `0`
- Pilot mutation: `0`
- DB mutation: `0`
- Archive rewrite: `0`
- Provider reconstruction call: `0`

Promotion: **PASS**.
