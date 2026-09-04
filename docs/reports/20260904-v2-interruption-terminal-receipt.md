# 2026-09-04 V2 Interruption Terminal Receipt

## Contract

Authorized interruption reasons are explicit:

- `COMMAND_TIMEOUT`
- `AUTHORIZED_CANCEL`
- `PRODUCTION_DEADLINE`
- `CLAIM_OWNERSHIP_LOST`
- `PROCESS_SHUTDOWN`
- `OTHER_INTERRUPTION`

A non-accepted terminal receipt records generation and fencing identity,
terminal state, reason, candidate persistence, acceptance, delivery eligibility,
and compatibility/fallback eligibility. It never promotes a partial candidate.

## Proof

- Signal return codes are classified as interruption, not transport failure.
- Authorized cancellation persists `INTERRUPTED` with fallback eligibility.
- Model timeout persists `TIMED_OUT` with `COMMAND_TIMEOUT`.
- Task cancellation persists a terminal interruption receipt.
- Unexpected runtime defects persist `FAILED` before re-raising.
- A valid accepted artifact wins over a later timeout/suppression attempt.

The initial US total-deadline experiment also produced an actual terminal
`TIMED_OUT` receipt with a persisted partial candidate, 30 lease renewals,
delivery disabled, and compatibility fallback preserved. No message was sent.

`INTERRUPTED_CHILD_AMBIGUOUS_IN_PROGRESS = 0`

`TRACEBACK_ONLY_TERMINAL_STATE = 0`
