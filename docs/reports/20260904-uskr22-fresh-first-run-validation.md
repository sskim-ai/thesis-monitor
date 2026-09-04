# USKR22 Fresh First-Run Validation

| Ticker | Status | Errors | Unsupported refs |
| --- | --- | --- | --- |
| CORZ | PASS | none | none |
| CPNG | PASS | none | none |
| CRCL | PASS | none | none |
| GOOGL | FAIL | unsupported_future_checkpoint_metric, unsupported_metric_or_inference | none |
| HUT | PASS | none | none |
| IBM | PASS | none | none |
| MU | FAIL | unsupported_current_metric_value, unsupported_metric_or_inference | none |
| RXRX | PASS | none | none |
| SKHY | PASS | none | none |
| SNDK | PASS | none | none |
| TSLA | PASS | none | none |
| TSM | PASS | none | none |
| WRD | PASS | none | none |
| WULF | PASS | none | none |
| 000660 | PASS | none | none |
| 003690 | PASS | none | none |
| 005490 | PASS | none | none |
| 005930 | PASS | none | none |
| 010120 | PASS | none | none |
| 012450 | PASS | none | none |
| 047810 | PASS | none | none |
| 086280 | PASS | none | none |

Validated: `20/22`. A/B/C gate: `NOT_RUN_FIRST_GATE_FAILED`.

The failed candidates were not retried or edited. `GOOGL` used the evidence-owned future phrase
`ROIC로 회수돼야`, which the future grammar did not recognize. `MU` contrasted `현재 수익성`
with `향후 FCF와 ROIC`, but the sentence-wide current-marker check incorrectly treated ROIC as a
current claim. The prior v3 candidates remain `22/22` under the current validator because they used
different, already-recognized future constructions.
