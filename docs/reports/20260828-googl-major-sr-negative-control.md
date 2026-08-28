# GOOGL Major S/R Negative Control

| Field | Before | After |
|---|---|---|
| Major support | `약 $267.08~$268.43` / `BOLLINGER_MONTHLY` | `omitted` |
| Major resistance | `약 $424.82~$426.96` / `BOLLINGER_MONTHLY` | `약 $359.84~$361.66` / `BALANCE_BOX` |
| Resistance anchor | none | `v3-balance-box:f9459a3f3cd44b427f10` |
| Last price interaction | indicator date misused as `2026-08-03` | `2026-08-03` |

`GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE = 0`

`GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE = 0`

The old support and resistance were monthly Bollinger-only projections. The repaired support is
omitted because no qualifying observed-price anchor exists. Resistance is replaced by a confirmed
balance-box zone. This is a contract outcome, not a GOOGL exception.
