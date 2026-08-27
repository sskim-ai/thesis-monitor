# KR-Only Enablement Action

- `KR_MARKET_TOP3_ENABLEMENT = DO_NOT_ENABLE`
- `KR_PRICE_STRUCTURE_ENABLEMENT = DO_NOT_ENABLE`
- `US_PRICE_STRUCTURE_ENABLED = 0`
- `KR_ROLLOUT = NOT_ENABLED`

The implementation introduces two default-OFF KR guards. Track C did not pass because no dedicated
test sink exists, so neither guard was enabled. Rollback is a single setting change back to OFF; no
DB cleanup is needed.
