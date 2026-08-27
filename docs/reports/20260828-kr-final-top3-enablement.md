# KR Final TOP3 Enablement

`KR_MARKET_TOP3_ENABLED = false`

The TOP3 stage did not start because pre-enable remained blocked.

| Gate | Result |
| --- | --- |
| Flag write | `0` |
| `POST_TOP3_ENABLE_MARKET` | `NOT_RUN` |
| `POST_TOP3_ENABLE_PRICE_STRUCTURE_LEAK` | `0` |
| Production message | `0` |

Future rollback is independent: set `kr_market_sector_top3_enabled=false` through the approved
configuration procedure. No rollback command was executed here.
