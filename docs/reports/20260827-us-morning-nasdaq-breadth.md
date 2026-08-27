# 2026-08-27 US Morning Nasdaq Breadth Boundary

The production packet safely represented exchange breadth as unavailable and did not substitute RSP. A single review-time, read-only request to the already-supported official Nasdaq daily file cross-checked the exact session.

| Field | Result |
|---|---|
| Contract | `nasdaq-official-exchange-breadth-v1` |
| Target session | `2026-08-26` |
| Official source | `https://www.nasdaqtrader.com/dynamic/dailyfiles/daily2026.csv` |
| Source last modified | `2026-08-26T17:30:08Z` |
| Source ETag | `"ae184e8a8035dd1:0"` |
| Payload SHA-256 | `a62dda39ae1ab4066c3cff14103139072b63c23fc137427f0b1fc05ecf2f438f` |
| Latest valid source session | `2026-08-24` |
| Exact 2026-08-26 row | not published |
| Canonical state | `PUBLICATION_PENDING` |
| Advances / declines / unchanged | unavailable, not zero |

The query occurred at `2026-08-27 11:07:02 KST`, after delivery, and was used only as a secondary boundary cross-check. It did not rewrite the production packet or database. Trading activity fields were not treated as breadth.

```text
NASDAQ_BREADTH_BOUNDARY = PASS
PRIOR_BREADTH_AS_CURRENT = 0
PUBLICATION_PENDING_AS_ZERO = 0
FABRICATED_EXCHANGE_BREADTH = 0
TRADING_ACTIVITY_AS_BREADTH = 0
```
