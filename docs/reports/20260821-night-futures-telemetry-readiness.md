# Night-Futures Telemetry Readiness

## Gate

- Attempt contract and archive: PASS.
- Full NIGHT date inventory: PASS.
- Independent product readiness/rejection: PASS.
- Production best-effort isolation: PASS.
- Detached two-slot observer and stop rule: PASS.
- Existing session basis/stale suppression: PASS.
- Focused tests: 61 passed.
- Full tests: 1,337 passed, 1 unrelated deprecation warning.
- Ruff and `git diff --check`: PASS.
- Implementation exact-SHA Actions: run `32469373051`, Test/Lint PASS.
- Live provider calls/manual task/Telegram/Pilot/DB mutation: 0.
- User-visible behavior change: 0.

Implementation deployment makes future evidence observable but does not answer the publication
deadline question by itself. The known 2026-08-21 production record remains four attempts around
08:06:30-08:20:05, expected 2026-08-21 NIGHT absent, stale 2026-08-20 pair suppressed, and later
availability unknown.

## Decision

- Open P0: 0.
- Open implementation P1: 0.
- Natural telemetry P1: deployed pending natural evidence.
- P2: optional report formatting and future multi-day policy presentation only.

`NIGHT_FUTURES_TELEMETRY_REPAIR_DEPLOYED = YES`

`P1_TELEMETRY_GAP = REPAIR_DEPLOYED_PENDING_NATURAL`

`DEADLINE_VERDICT = DEADLINE_UNPROVEN`

`FAIL_CLOSED_SAFETY = PASS`
