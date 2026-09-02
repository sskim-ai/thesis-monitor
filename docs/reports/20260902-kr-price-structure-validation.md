# KR Price Structure Validation

| ticker | close | as-of | chart state | registered confirmation | result |
| --- | --- | --- | --- | --- | --- |
| 000660 | 1,613,000 | 2026-09-02 | WAIT | holding_above | PASS |
| 003690 | 14,850 | 2026-09-02 | WAIT | holding_above | PASS |
| 005490 | 330,000 | 2026-09-02 | WAIT | not_reached | PASS |
| 005930 | 250,500 | 2026-09-02 | WAIT | failed_breakout | PASS |
| 010120 | 195,700 | 2026-09-02 | WAIT | N/A | PASS |
| 012450 | 1,025,000 | 2026-09-02 | HOLD | N/A | PASS |
| 047810 | 122,600 | 2026-09-02 | WAIT | not_reached | PASS |
| 086280 | 195,000 | 2026-09-02 | WAIT | failed_breakout | PASS |

All displayed closes, support/resistance zones, Bollinger levels, and registered rules were selected from packet-owned canonical facts. Monthly in-progress bands were labeled provisional and mutable until close. No invented level or decision-stage local OHLCV call was found. `KR_PRICE_STRUCTURE_VALIDATION = PASS`.
