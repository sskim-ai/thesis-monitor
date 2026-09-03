# Run-53 Directional-Balance Regression

The consumer-scope repair does not alter the `v2-directional-balance-v1` decision contract:

| BUY | SELL | Derived label |
| ---: | ---: | --- |
| 6 | 4 | BUY |
| 5 | 5 | HOLD |
| 4 | 6 | SELL |

Every accepted result must use 0.5 increments, remain within 0 through 10, and sum to exactly 10.
`HOLD` is current neutrality and does not inherit a prior BUY or SELL. When adjudication is
required, the accepted plan owns the final label, balance, directional drivers, and renderer
payload; a raw candidate cannot bypass that owner.

Focused schema, label derivation, prior-decision independence, same-evidence stability, and
accepted-renderer ownership controls pass. The final run-53 production-equivalent artifact has 14
accepted blocks, 14 exact sums, and one visible balance line per stock. Its distribution is HOLD 9
and SELL 5; no target distribution was imposed.

- `RUN53_BALANCE_SCHEMA = PASS`
- `ACCEPTED_DECISION_PLAN_REMAINS_AUTHORITY = PASS`
- `FIXED_FACTOR_WEIGHTED_SCORE_INTRODUCED = 0`
- `DECISION_POLICY_RETUNING = 0`
