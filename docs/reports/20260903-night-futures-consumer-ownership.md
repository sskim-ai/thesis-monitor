# Night-Futures Consumer Ownership

The two run-53 night-futures facts remain in `market_context.fact_catalog`, including their raw
reference values. Their ownership is:

| Consumer | Allowed |
| --- | --- |
| `ARCHIVE_ONLY` | yes |
| `NIGHT_FUTURES_MODULE` | yes |
| `STOCK_V2` | no |
| `DAILY_REVIEW` | no |
| `MARKET_RENDERER` | no while temporary suppression is active |

Both failing `reference_price` occurrences are diagnosed as `NOT_IN_CONSUMER_SCOPE`. Collection,
source/session identity, near-month selection, history, and D/W/M logic were not modified.

