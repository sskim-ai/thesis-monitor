# KR Final TOP3 Enablement

`KR_MARKET_TOP3_ENABLED = false`

The dedicated test-sink gate did not pass, so the TOP3 enablement stage did not start.

| Gate | Result |
| --- | --- |
| Flag change attempted | `0` |
| `POST_TOP3_ENABLE_MARKET` | `NOT_RUN` |
| `POST_TOP3_ENABLE_STOCK_PRICE_STRUCTURE_LEAK` | `0` |
| Production message generated | `0` |

Rollback command, if a future enablement needs it: set `kr_market_sector_top3_enabled=false` by
the repository's approved configuration procedure. It was not executed in this task.
