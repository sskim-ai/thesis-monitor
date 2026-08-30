# US Market Relative-Signal Selection

- Session: `2026-08-28`
- Implementation: `d44b624200791bef69b56a60c74b7388d91d0346`
- Backend contract: `us-market-digest-plan-v1`

| Signal | Subject | SPY | Spread | Result |
|---|---:|---:|---:|---|
| IWM vs SPY | -1.3542% | -0.2269% | -1.1273pp | material relative weakness |
| SOXX vs SPY | -3.1993% | -0.2269% | -2.9724pp | material relative weakness |
| RSP vs SPY | -0.3432% | -0.2269% | -0.1163pp | participation/style context |

The backend computes spreads. The AI receives selected claims and canonical refs; it does not perform subtraction. The current exact message retains SPY, QQQ, IWM, SOXX, and RSP, then renders one IWM line and one SOXX line.

- `AI_CALCULATED_RELATIVE_SPREAD = 0`
- `MATERIAL_SOXX_RELATIVE_SIGNAL_OMITTED = 0`
- `MATERIAL_IWM_RELATIVE_SIGNAL_OMITTED = 0`
- `RSP_AS_EXCHANGE_BREADTH = 0`
