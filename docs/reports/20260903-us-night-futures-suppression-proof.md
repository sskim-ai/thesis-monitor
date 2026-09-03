# 2026-09-03 US Night-Futures Suppression Proof

The delivered US market message contains no user-facing night-futures section.
Collection, history, D/W/M aggregation, and raw packet facts remained enabled.

That intentional split exposed the P1: two preserved raw `reference_price`
fields remained in the shadow numeric-semantic readiness surface even though the
night-futures block was not consumable by prose. The fields blocked AI readiness;
they did not leak into the message.

- `US_NIGHT_FUTURES_USER_FACING_COUNT = 0`
- `US_NIGHT_FUTURES_SECTION_ABSENT = PASS`
- `NIGHT_FUTURES_COLLECTION_DISABLED = 0`
- `NIGHT_FUTURES_HISTORY_DISABLED = 0`
- `NIGHT_FUTURES_DWM_DISABLED = 0`
- `NIGHT_FUTURES_SESSION_CONVENTION_CHANGED = 0`

