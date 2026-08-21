# Phase 9.0E Kill-Switch Validation

## Modes

| Input | Resolved | Selected in run-30 replay | User-visible cash-flow block |
|---|---|---:|---:|
| missing/default | OFF | 0 | 0 |
| `OFF` | OFF | 0 | 0 |
| invalid value | OFF | 0 | 0 |
| `SELECTIVE_CURRENT_FORMAL_FULL_FCF` | SELECTIVE | 9 | 9 first-exposure blocks |

The selector is evaluated for each packet/fallback build. A unit test selects a context, changes the
mode to OFF in the same process, and verifies no Fact, context ID, or rendered text survives. An
unchanged prior sent context suppresses its next exact number while keeping a resolved false Unknown
removed.

Per-ticker selector and renderer exceptions return audited suppression and do not raise into the
rest of the delivery set. AI/fallback context mismatch raises before delivery. The detached canary
records parity but has `production_delivery_influence = 0`.

The operating disable/enable procedure is documented in
`docs/operations/CASH_FLOW_USER_VISIBLE_KILL_SWITCH.md`. Imported runtime configuration requires an
API process restart after changing the operating `.env`; no Scheduled Task or Telegram send is used
for verification.

Kill-switch test result: PASS.

