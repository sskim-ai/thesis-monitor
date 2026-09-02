# 2026-09-03 Directional Balance Label Derivation

## Deterministic Rules

| BUY | SELL | Derived label | Result |
| ---: | ---: | --- | --- |
| 6 | 4 | BUY | PASS |
| 5 | 5 | HOLD | PASS |
| 4 | 6 | SELL | PASS |
| 5.5 | 4.5 | HOLD | PASS |

BUY is derived only when BUY is at least 6. SELL is derived only when SELL is at least 6. Every other valid pair is HOLD. Because the pair sums to 10, BUY and SELL cannot both cross their threshold.

Candidate validation and accepted-plan validation independently reject a label that disagrees with its balance. Negative FCF, valuation, price, and prior accepted state do not participate in this label function.

## Gates

- `BALANCE_SUM_NOT_10 = 0`
- `FALSE_BALANCE_PRECISION = 0`
- `FIXED_FACTOR_WEIGHTED_SCORE_INTRODUCED = 0`
- `TRACK_A_DIRECTIONAL_BALANCE = PASS`
