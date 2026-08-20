# KRX Exact-Slot Telemetry Operating State

Date: 2026-08-20 KST
Previous main: `006a997789d3e5ebac85ef867ae31296d175056c`
Implementation/main/operating: `18bc7c3e456c723b2d0359219c517e5eb02ee4e0`
Branch: `codex/krx-exact-slot-telemetry-capture`
Status: OPERATING TELEMETRY ONLY / NATURAL EVIDENCE PENDING

## Promotion

The implementation is a clean linear descendant of the previous operating main. GitHub Actions run
`32323452853` passed Test and Lint for the exact implementation SHA. `origin/main` and the operating
checkout fast-forwarded to that commit without a merge commit, rebase, force push, or history
rewrite.

The API was not restarted because no API route or resident message process imports the new telemetry
modules. The telemetry LaunchAgent starts a fresh Python process for each natural slot.

## LaunchAgent

Installed label: `com.seungsoo.thesis-monitor.krx-publication-telemetry`

| Item | State after registration |
|---|---|
| 08:05 KST trigger | active |
| 16:05 KST trigger | active |
| `RunAtLoad` | absent |
| `kickstart` / manual execution | 0 |
| launch count | 0 |
| last exit | never exited |
| telemetry files | 0 |
| telemetry logs | 0 |
| KRX credential readiness | configured, value not exposed |

Source and installed plist bytes match. Registration occurred at approximately 11:10 KST, outside
both exact slots, and created no provider call or catch-up observation.

## Capture Boundary

- 08:05 naturally observes the preceding XKRX session as `NEXT_MORNING_0805`.
- 16:05 naturally observes the current completed XKRX session as `SAME_DAY_CLOSE_1605`.
- Wrong minute, weekend, holiday, and calendar failure stop before provider access.
- A T+1 exact clock is not defined, so no T+1 schedule or inferred evidence was created.
- Even a complete result is telemetry only and cannot enter a digest, packet, renderer, or Telegram
  message.

The next expected capture is the natural 2026-08-20 16:05 KST slot. This report does not wait for,
simulate, or manually invoke that observation.

## Existing Operating Schedules

The four Codex AI-review tasks remain ACTIVE and unchanged:

| Task | Time KST |
|---|---:|
| US Primary | 08:15 |
| US Backup | 08:30 |
| KR Primary | 16:15 |
| KR Backup | 16:55 |

Phase 8.5.5.1 natural proof therefore continues with today's natural KR cycle and the next natural
US cycle. KRX telemetry is independent and cannot delay, release, or replace those messages.

## Validation

- Focused implementation/docs tests: `25 passed`.
- Full pytest: `1,107 passed`, one existing Starlette/httpx deprecation warning.
- Ruff: PASS.
- `git diff --check`: PASS.
- LaunchAgent plist lint and source/installed parity: PASS.
- Exact implementation SHA GitHub Actions Test/Lint: PASS.
- Knowledge checksum parity, Public Action `0.4.5`, and operationId `20/20`: PASS.

## Persistent State

| Area | State |
|---|---|
| Natural AI-Assisted Delivery | `PARTIAL` |
| Phase 8.5.5.1 natural proof | pending |
| KRX 16:05 role | `NOT_YET_PROVEN` |
| KRX 08:05 role | `NOT_YET_PROVEN` |
| KRX T+1 role | `NOT_YET_PROVEN`, exact clock undefined |
| KRX exact-slot capture | `OPERATING_TELEMETRY_ONLY_PENDING_NATURAL` |
| KRX user-visible integration | `NO` |
| Cash Flow / Capital Efficiency | `PENDING` |

## Safety

| Mutation | Count |
|---|---:|
| Manual KRX/provider calls | 0 |
| Manual Scheduled Task/LaunchAgent runs | 0 |
| Existing AI task configuration changes | 0 |
| User-visible KRX integration | 0 |
| Telegram sends | 0 |
| Pilot mutations | 0 |
| DB migrations/manual mutations | 0 |
| Archive/receipt rewrites | 0 |
| Production Assist changes | 0 |

The next decision is evidence-driven: accumulate clean natural KRX observations, continue Phase
8.5.5.1 natural AI review, and evaluate digest integration only after the relevant role gate closes.
Cash Flow / Capital Efficiency begins only after Natural AI-assisted delivery stabilizes.
