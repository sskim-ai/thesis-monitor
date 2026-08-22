# KR Orphan Reconciliation Dry Run

Command contract: `kr-orphan-delivery-reconciliation-v1`; dry-run is the default.

Production preconditions passed:

- run ID/date/type/status: 33 / 2026-08-22 / `daily_kr` / success
- expected stock count: 7; actual: 7
- expected digest count: 1; actual: 1
- target rows: 8
- packet artifacts: 0
- packet references: 0
- sent rows: 0
- non-null `sent_at`: 0
- state: all pending

Result: `dry_run_ready`, changed count 0.

The same command was tested on a production DB copy. Apply changed exactly eight rows; a second
copy-only apply returned `already_reconciled` with zero changes. Count mismatch, sent row, packet
artifact, mixed state, and unrelated-row controls abort or remain unchanged.
