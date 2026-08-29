# Decision Continuity Regression

Fresh local OHLCV collection against the immutable run-44/run-45 packets reproduced all four
accepted evidence SHA values exactly. The continuity gate therefore required classifications to
remain unchanged.

| Ticker | Before | After |
|---|---:|---:|
| 003690 | HOLD | HOLD |
| 000660 | HOLD | HOLD |
| GOOGL | HOLD | HOLD |
| RXRX | SELL | SELL |

The existing test also rejects same-evidence unexplained churn. Evidence SHA changes remain free to
enter the existing decision-delta path.

`POLARITY_REPAIR_CHANGED_DECISION = 0`

`POLARITY_REPAIR_DECISION_CONTINUITY = PASS`

`CONTINUITY_GATE_BLOCKS_REAL_EVIDENCE_CHANGE = 0`
