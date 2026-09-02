# 2026-09-03 HOLD Neutrality Controls

## Controls

The focused suite proves both required historical-state cases:

| Prior accepted | Current balance | Current candidate | Adjudication | Final accepted | Result |
| --- | --- | --- | --- | --- | --- |
| BUY | `5:5` | HOLD | KEEP_V2 | HOLD `5:5` | PASS |
| SELL | `5:5` | HOLD | KEEP_V2 | HOLD `5:5` | PASS |

The prior label triggers the existing material-disagreement adjudication path, but it does not alter the current candidate's deterministic label. Accepted ownership remains explicit and no raw candidate is rendered before resolution.

## Gates

- `HOLD_MEANS_PRIOR_DECISION_CARRY_FORWARD = 0`
- `PRIOR_BUY_FORCES_CURRENT_HOLD_TO_BUY = 0`
- `PRIOR_SELL_FORCES_CURRENT_HOLD_TO_SELL = 0`
- `RAW_CANDIDATE_BALANCE_USED_AS_FINAL = 0`
