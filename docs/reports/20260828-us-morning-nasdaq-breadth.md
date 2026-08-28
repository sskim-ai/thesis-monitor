# 2026-08-28 US Morning Nasdaq Breadth Boundary

The production packet safely represented exchange breadth as unavailable and did not substitute RSP. One review-time, read-only query to the existing official Nasdaq file cross-checked target session `2026-08-27` after delivery.

| Field | Result |
|---|---|
| Contract | `nasdaq-official-exchange-breadth-v1` |
| Official source | `https://www.nasdaqtrader.com/dynamic/dailyfiles/daily2026.csv` |
| Retrieved | `2026-08-28 09:13:12 KST` |
| Source last modified | `2026-08-27T17:30:06Z` |
| Source ETag | `"5d9498b34936dd1:0"` |
| Payload SHA-256 | `9222fd157f546adc24a32d52956caee51736526fc4398c3d5235d8968ea6232c` |
| Latest valid source session | `2026-08-25` |
| Exact 2026-08-27 row | not published |
| Advances / declines / unchanged | unavailable, not zero |
| Canonical state | `PUBLICATION_PENDING` |

The query did not modify packet, database, assessment, delivery, or archive state.

```text
NASDAQ_BREADTH_BOUNDARY = PASS
PRIOR_BREADTH_AS_CURRENT = 0
PUBLICATION_PENDING_AS_ZERO = 0
FABRICATED_EXCHANGE_BREADTH = 0
TRADING_ACTIVITY_AS_BREADTH = 0
```
