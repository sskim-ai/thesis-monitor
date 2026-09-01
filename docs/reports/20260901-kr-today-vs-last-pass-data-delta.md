# KR Today Versus Last Pass Data Delta

## Comparison

Passing test packet: `2026-08-31-kr-run-48-a573c2a6f245`. Natural live packet: `2026-09-01-kr-run-50-44156fe0fa76`.

| Ticker | Test price/date | Live price/date | Test tech | Live tech | Evidence changed | Trigger |
| --- | --- | --- | --- | --- | --- | --- |
| 000660 | 1674000.0 / 2026-08-31 | 1693000.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 003690 | 14280.0 / 2026-08-31 | 14680.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 005490 | 338500.0 / 2026-08-31 | 341000.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 005930 | 260000.0 / 2026-08-31 | 261000.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 010120 | 207500.0 / 2026-08-31 | 204500.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 012450 | 1102000.0 / 2026-08-31 | 1058000.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 047810 | 131000.0 / 2026-08-31 | 127200.0 / 2026-09-01 | FULL | FULL | YES | NO |
| 086280 | 207500.0 / 2026-08-31 | 209500.0 / 2026-09-01 | FULL | FULL | YES | NO |

Market data changed normally between August 31 and September 1, so evidence fingerprints changed for every subject. Both paths had FULL technical context for 8/8. In the natural path the CLI failed while resolving the schema before it read the prompt or called the model; therefore no changed fact can be the trigger.

`KR_FAILURE_TRIGGER_EXACTLY_LOCALIZED = NOT_DATA_TRIGGERED`
