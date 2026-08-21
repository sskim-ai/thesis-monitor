# Phase 9.0E Operating Promotion

## Code Promotion

- Previous main/operating: `86f41870a17fc4bec8ec43b1395323e211450fa2`
- Work-instruction commit: `309f5f1756d39d5972c5d4b48faaeab4862d8077`
- Cumulative implementation SHA: `cf3194981124de2a6f85fbe81b145ef06e1db08d`
- Implementation Actions: run `32443322364`, Test/Lint PASS
- Promotion: clean linear fast-forward to `main`
- Operating checkout: clean and equal to promoted main
- Final documentation SHA/Actions: resolve from Git at final promotion

## OFF Staging

The operating checkout was first synchronized with no `.env` key. Runtime resolution returned
`OFF`. The API LaunchAgent was restarted because imported runtime/config code changed; `/health`
returned `{"status":"ok"}`. No cash-flow message was sent.

## Selective Enablement

- Config key: `CASH_FLOW_USER_VISIBLE_MODE`
- Previous resolved mode: `OFF`
- New mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Config source: operating `.env`, one key occurrence
- Activation: `2026-08-21 12:31:47 KST`
- Restart required/performed: YES/YES
- Post-restart health: PASS
- Non-delivery selector smoke: TSLA SELECTED on canonical Fact
  `cashflow:68666c261434dab50ab88a8d`
- Explicit OFF smoke: state OFF, Fact count `0`
- Operating focused regression: `396 passed`

The first health probe immediately after restart raced process startup and could not connect. The
LaunchAgent was already running; startup logs reached application-ready, and the repeated probe
passed. No delivery or task was triggered during that interval.

## Schedules And Safety

Four Codex tasks remain ACTIVE and target the operating checkout:

- US primary 08:15 KST
- US backup 08:30 KST
- KR primary 16:15 KST
- KR backup 16:55 KST

The KRX telemetry LaunchAgent remains calendar-loaded at 08:05 and 16:05 with last exit code `0`.
AI mode remains `shadow`; Production Assist remains OFF. Manual Telegram `0`, manual Scheduled Task
`0`, Pilot mutation `0`, DB mutation/migration `0`, archive/receipt rewrite `0`, force/history
rewrite `0`.

State: `DEPLOYED_SELECTIVE_PENDING_NATURAL`. The next natural US run is reviewed separately.

