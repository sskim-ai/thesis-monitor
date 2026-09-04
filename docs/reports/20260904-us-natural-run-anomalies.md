# US Natural Run Anomalies

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

| Severity | Anomaly | Evidence | Effect |
| --- | --- | --- | --- |
| P0 observation | Natural primary and backup V2 canaries both hit `UnknownIssuer` | claim-scoped CLI logs | zero V2 model results |
| P1 observation | Transport classifier reported local connectivity, not TLS | emitted token `UnknownIssuer` vs configured marker `unknown issuer` | misleading reason class |
| P1 observation | Primary continued beyond 10-minute lease and overlapped backup | session and claim timestamps | primary candidate superseded |
| P1 observation | Backup reused candidate but still failed 26 then 22 validator errors | two validation archives | no accepted AI review |
| Expected safety | 08:40 fallback sent 15/15 with no duplicates | delivery result and DB receipts | user delivery complete |
| Disproved hypothesis | 08:20 primary-missing checker | no component or predicate found | not causal |

Severity labels here describe forensic significance only; no persistent roadmap state is changed by this read-only task.
