# US Night-Futures Summary Canonicalization

Implementation `f6bc769f823429426474a38f007dc8196b4e5f43` removes all raw/legacy night-futures summary entries and
reprojects only rows accepted by `night_futures_gate`. Fixed ownership is KOSPI200
`market:night_futures:1` and KOSDAQ150 `market:night_futures:2`, both at
`fields.change_pct` with `CURRENT_DIRECTIONAL` state.

Negative fixture: ready products `0`, canonical summary rows `0`, rendered section omitted.
Positive fixture: two canonical rows, exact fact/field/value/session/state parity.

- `NIGHT_FUTURES_SUMMARY_CANONICALIZATION = PASS`
- `NIGHT_FUTURES_SUMMARY_CANONICAL_PARITY = PASS`
- `SUMMARY_NIGHT_FUTURES_VALUE_CONFLICT = 0`
- `SUMMARY_NIGHT_FUTURES_SESSION_CONFLICT = 0`
- `STALE_NIGHT_FUTURES_SUMMARY_ITEM = 0`
