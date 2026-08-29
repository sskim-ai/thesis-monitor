# Current-Time Canary Decision Delta

- Execution time (KST): `2026-08-29T21:16:59.579875+09:00`
- Mode: read-only current-time E2E test

## Continuity

| Ticker | Previous | Current | Confidence | Timing | Evidence changed | Decision changed |
|---|---|---|---|---|---|---|
| 003690 | HOLD | HOLD | MEDIUM | NEUTRAL | NO | NO |
| 000660 | HOLD | HOLD | LOW | UNFAVORABLE | NO | NO |
| GOOGL | HOLD | HOLD | MEDIUM | UNFAVORABLE | NO | NO |
| RXRX | SELL | SELL | MEDIUM | UNFAVORABLE | NO | NO |

- Unexplained current decision churn: `0`
- Final distribution: `HOLD 3 / SELL 1`
- Continuity source SHA-256: `f89a748431cdb649ac5d816756584221a9aba8f5fc6ef9ec17631e1a3c383e3d`

The xhigh trial initially proposed two no-evidence-delta changes; the existing continuity contract retained the prior canonical decisions, leaving zero unexplained final churn.
