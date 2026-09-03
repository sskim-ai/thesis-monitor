# Shadow vs Reference: Label / Balance

The manual view is an independent comparator, not ground truth.

| Ticker | Codex | Reference | Label match | Codex balance | Reference balance | BUY delta | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CORZ | HOLD | HOLD | YES | 5.0:5.0 | 4.5:5.5 | 0.5 | BALANCE_NEAR |
| CPNG | HOLD | HOLD | YES | 4.5:5.5 | 5.5:4.5 | 1.0 | BALANCE_MODERATE |
| CRCL | HOLD | HOLD | YES | 4.5:5.5 | 5.0:5.0 | 0.5 | BALANCE_NEAR |
| GOOGL | HOLD | HOLD | YES | 5.0:5.0 | 4.5:5.5 | 0.5 | BALANCE_NEAR |
| HUT | SELL | SELL | YES | 3.5:6.5 | 3.0:7.0 | 0.5 | BALANCE_NEAR |
| IBM | HOLD | HOLD | YES | 5.5:4.5 | 5.5:4.5 | 0.0 | BALANCE_NEAR |
| MU | HOLD | BUY | NO | 5.5:4.5 | 6.5:3.5 | 1.0 | BALANCE_MODERATE |
| RXRX | SELL | HOLD | NO | 4.0:6.0 | 5.0:5.0 | 1.0 | BALANCE_MODERATE |
| SKHY | HOLD | HOLD | YES | 5.0:5.0 | 5.0:5.0 | 0.0 | BALANCE_NEAR |
| SNDK | HOLD | HOLD | YES | 5.5:4.5 | 4.5:5.5 | 1.0 | BALANCE_MODERATE |
| TSLA | SELL | SELL | YES | 3.0:7.0 | 2.5:7.5 | 0.5 | BALANCE_NEAR |
| TSM | HOLD | HOLD | YES | 5.5:4.5 | 5.5:4.5 | 0.0 | BALANCE_NEAR |
| WRD | HOLD | SELL | NO | 4.5:5.5 | 3.5:6.5 | 1.0 | BALANCE_MODERATE |
| WULF | SELL | SELL | YES | 3.5:6.5 | 2.5:7.5 | 1.0 | BALANCE_MODERATE |

## Summary

- Label matches: `11/14`
- Balance near: `8`
- Balance moderate: `6`
- Balance material: `0`
- Codex distribution: `BUY 0 / HOLD 10 / SELL 4`
- Reference distribution: `BUY 1 / HOLD 9 / SELL 4`
