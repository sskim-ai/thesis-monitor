# Phase 9.0D Runtime Shadow Canary Implementation

## Repository Identity

- Work instruction commit: `a24e4f2210f944fa7c43d8dbf8be1d1a8e652164`
- Work instruction SHA-256: `73c5e3b6d5d7842c244051920e6e258a17c43077ca5c3ec01d2ab78de68e798c`
- Implementation branch: `codex/phase-9-0d-selective-cash-flow-runtime-shadow-canary`
- Implementation commit: `578d33e13dbbefe375275c64cd04e631a7141b84`
- Base: exact work instruction commit
- Contract: `cash-flow-runtime-shadow-canary-v1`

## Integration

`app.jobs.ai_review` observes only terminal production delivery results from validate/deliver,
fallback, and persisted delivery retry. It launches a detached child after the archived production
result is final. A validation rejection does not launch because fallback has not completed.

The child verifies packet and delivery-result identities, loads the Phase 9.0B canonical Fact set,
builds the Phase 9.0C sidecar, renders a separate shadow interpretation, binds exact numeric claims,
applies semantic and runtime-quality gates, and writes only the dedicated canary namespace.

## Failure Isolation

Tests cover production success with canary success, generation failure, numeric/semantic validator
failure, archive failure, launcher exception, deterministic fallback, and duplicate invocation.
Every result preserves the packet and production delivery-result SHA. Canary output has no import
or callable path to `TelegramNotifier`, notification dispatch, assessment persistence, warning
lifecycle, fallback eligibility, or Pilot success accounting.

The parent catches even unexpected launcher exceptions. The detached child uses no stdin/stdout
contract with the parent, so its latency and exit code cannot change primary/backup task status.

## Retrospective Deployment Proof

Immutable run-28 and run-29 artifacts were copied to temporary roots; original archives were not
rewritten and these replays do not count as natural proof.

| Control | Result |
|---|---|
| run-28 US positive replay | `COMPLETE_PASS` |
| run-28 exact numeric binding | 10 automatic, 0 manual/rejected/unresolved |
| run-28 semantic / quality errors | 0 / 0 |
| run-28 production influence | 0 |
| run-29 KR negative control | `COMPLETE_PASS` |
| run-29 cash-flow numeric injection | 0 |
| run-29 semantic / quality errors | 0 / 0 |
| run-29 production influence | 0 |

The first run-28 attempt correctly caught shared CORZ/WULF generic HPC prose. The repair uses each
packet's existing thesis mechanism to distinguish colocation billing from HPC lease economics and
makes formal-period alignment cautions industry-specific. No ticker exception or quality-threshold
change was added.

## Runtime Boundary

- Production AI packet/candidate: unchanged
- Telegram/fallback/Public Action/schema 4: unchanged
- Task IDs, prompts, schedules: unchanged
- DB migration/manual mutation: 0
- Manual Telegram/Scheduled Task/Pilot mutation: 0
- Cash-flow user-visible integration: 0
- CCC/ROIC: deferred
- KR OpenDART period recovery: medium follow-up, unchanged

