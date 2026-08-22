# KR Orphan Reconciliation Result

- Validated implementation SHA: `c26c9359b134df0a4cd697fd97e7616cc508e885`
- Command mode: controlled `--apply`, one production invocation
- Transaction target: stock 7 plus companion KR digest 1
- Changed rows: 8
- Terminal status: existing supported `failed`
- Reason: `non_trading_day_orphan_no_packet`
- Marked sent: 0
- `sent_at` set: 0
- Deleted rows: 0
- Attempt count changes: 0
- Payload changes: 0
- Packet artifacts fabricated: 0
- Other rows with reconciliation reason: 0

Read-only postcondition query returned eight `failed` rows, eight matching reasons, and zero
non-null `sent_at`. The exact-copy idempotency test returned zero changes on the second apply; the
production command was intentionally invoked with `--apply` only once.

`KR_ORPHAN_DELIVERY_RECONCILIATION = PASS`.
