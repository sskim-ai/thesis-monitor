# US Primary and Backup Concurrency

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Classification

`PRIMARY_BACKUP_OVERLAP = OVERLAP_SHARED_STATE`

- Primary outer task: `08:15:45.571..08:36:03.855`.
- Backup outer task: `08:30:15.594..08:42:26.746`.
- Outer overlap: about `5m 48.261s`.
- Primary nested CLI: `08:30:09.290..08:35:15.425`.
- Backup nested CLI: `08:33:37.239..08:37:08.504`.
- Nested model-call overlap: about `1m 38.186s`.

The claim-specific temporary paths differed, but both workers targeted the same packet and final output generation. At `08:30:39.046046`, backup replaced the shared claim owner. The primary was then fenced at validation. No concurrent Telegram send came from either AI worker.

`PRIMARY_COMPLETION_RELATIVE_TO_BACKUP = PRIMARY_COMPLETED_AFTER_BACKUP_TRIGGER`: the draft existed before backup, but primary's terminal validation and task completion occurred after backup activation.
