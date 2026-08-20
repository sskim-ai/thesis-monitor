# KRX Exact-Slot Telemetry Capture

Date: 2026-08-20 KST
Branch: `codex/krx-exact-slot-telemetry-capture`
Base: `006a997789d3e5ebac85ef867ae31296d175056c`
Implementation: `18bc7c3e456c723b2d0359219c517e5eb02ee4e0`
Status: ENGINEERING PASS / OPERATING TELEMETRY-ONLY PROMOTED

## Purpose

Close only the KRX publication telemetry capture gap. This change starts natural exact-slot evidence
collection without exposing KRX breadth to market packets, AI, deterministic rendering, Telegram,
or any other user-visible path.

## Implementation

- `krx-publication-readiness-v1` is implemented as a four-endpoint metadata-only provider probe.
- `krx-publication-telemetry-v1` persists sanitized append-only JSONL with payload hashes and mode
  `0600`.
- `krx-exact-slot-capture-v1` accepts only a normal XKRX session at exactly 08:05 or 16:05 KST.
- 08:05 targets the preceding XKRX session and records `NEXT_MORNING_0805`.
- 16:05 targets the current completed XKRX session and records `SAME_DAY_CLOSE_1605`.
- Weekend, holiday, calendar failure, and wrong-minute paths exit before provider access.
- Only `capture_origin=launchd_calendar` records enter role evidence; manual records receive zero
  role credit.
- The dedicated LaunchAgent has no `RunAtLoad`, market-monitor, DB, AI-review, or notification
  command.

The existing T+1 role has no exact clock in `krx-time-slot-provider-role-v1`. This repair does not
invent a clock and does not reuse an 08:05 record as two independent observations. T+1 remains
`NOT_YET_PROVEN`.

## Readiness Semantics

| Provider result | Canonical readiness | User-visible promotion |
|---|---|---:|
| Four HTTP 200 empty payloads | `MARKET_COMPLETED_PROVIDER_PENDING` | 0 |
| Mixed ready/empty or missing required index | `PROVIDER_PARTIAL` | 0 |
| Provider date mismatch | `STALE_PROVIDER_DATE` | 0 |
| HTTP/network/schema failure | `PROVIDER_ERROR` | 0 |
| Four exact-date complete endpoints | `PROVIDER_COMPLETE` | 0 |

`PROVIDER_COMPLETE` can contribute only to a future role decision. It is not imported by
`monitor_daily`, market intelligence, packet assembly, or notification code.

## Schedule

New template: `ops/com.seungsoo.thesis-monitor.krx-publication-telemetry.plist`

| Natural slot | Calls | Target |
|---|---:|---|
| 08:05 KST | 4 | preceding XKRX session |
| 16:05 KST | 4 | current XKRX session |

Maximum normal-session request cost is eight calls, or 0.08% of the documented 10,000 daily key
limit. Existing US/KR market LaunchAgents and four Codex AI-review Scheduled Tasks are unchanged.

## Validation

- Focused KRX provider/service/job/calendar tests: `21 passed`.
- Full `pytest -q`: `1,107 passed`, one existing Starlette/httpx deprecation warning.
- Ruff: PASS.
- `git diff --check`: PASS.
- LaunchAgent `plutil -lint`: PASS.
- Investment Knowledge canonical/runtime parity: PASS,
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.
- Chart Knowledge canonical/runtime parity: PASS,
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.
- Public Action `0.4.5`; operationId `20/20` unique: PASS through the full regression suite.

No provider endpoint was called during development or validation; all provider fixtures used
`httpx.MockTransport`.

## Promotion Result

Natural capture was enabled only after:

1. exact implementation SHA GitHub Actions Test/Lint passed in run `32323452853`;
2. main remained the clean linear parent;
3. origin/main and the operating checkout fast-forwarded cleanly;
4. the LaunchAgent was copied and bootstrapped without `kickstart` or manual execution;
5. `launchctl print` showed the 08:05/16:05 calendar triggers and no `RunAtLoad`;
6. registration left launch count, provider calls, logs, and telemetry files at zero.

## Safety

| Mutation | Count through promotion |
|---|---:|
| Provider calls | 0 |
| User-visible KRX integration | 0 |
| Telegram sends | 0 |
| Scheduled Task manual runs | 0 |
| Pilot mutations | 0 |
| DB migrations/mutations | 0 |
| Archive/receipt rewrites | 0 |
| Production Assist changes | 0 |

Phase 8.5.5.1 natural AI proof remains the immediate operating review. Cash Flow / Capital
Efficiency remains pending until natural AI-assisted delivery stabilizes.
