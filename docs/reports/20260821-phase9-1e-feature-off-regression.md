# Phase 9.1E Feature-OFF Regression

`WORKING_CAPITAL_USER_VISIBLE_MODE` is absent or resolves to `OFF`. The new service is not imported
by production AI review, notification, or job paths.

| Surface | Diff / mutation |
| --- | ---: |
| production AI input | 0 |
| production fallback | 0 |
| Telegram | 0 |
| Public Action | 0 |
| public snapshot/schema | 0 |
| assessment DB | 0 |
| warning lifecycle | 0 |
| Scheduled Task configuration | 0 |

Public Action remains `0.4.5`, output schema remains `4`, and the operationId set remains 20/20
unique. Phase 9.0E cash-flow behavior remains independently governed by
`CASH_FLOW_USER_VISIBLE_MODE`; working-capital OFF does not disable it. Phase 9.1D canary evidence
also remains independent.

No manual Telegram, Scheduled Task, Pilot mutation, DB mutation, archive rewrite, or Production
Assist enablement was performed.
