# SOXX / IWM Materiality Controls

The existing material-relative threshold of `0.50pp` is reused for IWM:SPY and SOXX:SPY. No new portfolio score or AI-side arithmetic was introduced.

| Control | Expected | Result |
|---|---|---|
| absolute spread below 0.50pp | omit safely | PASS |
| current-session date/role mismatch | temporal omission | PASS |
| missing subject or SPY | unavailable | PASS |
| material negative IWM spread | one risk-appetite line | PASS |
| material negative SOXX spread | one semiconductor line | PASS |
| relative refs not consumed | validator rejection | PASS |

RSP remains an equal-weight participation/style proxy. When official breadth is also present, participation/style stays within the 1-2 line budget; semiconductor has a separate 0-1 line budget. Sector leader/laggard and night-futures policy were not changed.

- `US_MARKET_INTERNALS_OVERLOADED = 0`
- `US_SECTOR_SELECTION_POLICY_DIFF = 0`
- `NIGHT_FUTURES_POLICY_DIFF = 0`
