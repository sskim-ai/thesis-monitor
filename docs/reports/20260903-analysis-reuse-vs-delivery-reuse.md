# Analysis Reuse Versus Delivery Reuse

Analysis may be reused for the same source monitor run. Delivery may not be regenerated merely
because a backup invocation emitted another packet ID.

The queue now preserves any AI-owned metadata, appends the observed reuse packet ID, and leaves
the original owner and state unchanged. The hold service backfills generation metadata from the
owner packet and records an explicit conflict if the source analysis generation differs.

The isolated real entrypoint was executed after AI send. It reported:

- `analysis_action=reuse`
- `delivery_action=already_delivered_deduped`
- AI state `already_sent`, sent `9`, pending `0`
- additional Telegram sends `0`

This is backup/dedupe evidence, not a new natural production run.
