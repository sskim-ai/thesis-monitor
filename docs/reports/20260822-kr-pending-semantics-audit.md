# KR Pending Semantics Audit

## Definitions

- `raw_pending_rows`: database rows where `NotificationDelivery.status == pending`.
- `deliverable_pending`: raw pending rows with a retryable AI state and an existing identity-matching
  packet file.
- `held_session_pending`: packet-bound held/AI-pending/fallback-pending rows counted by the AI
  retry/fallback result.

The 17:10 `pending_count` is `held_session_pending`, not a SQL count of all raw pending rows.

## Saturday Reconciliation

The Stage A report stated seven pending rows because it counted the seven stock rows. Direct
evidence lock found the companion `__DAILY_DIGEST_KR__` row, so the database had eight raw pending
rows. All had no AI packet metadata and the packet artifact count was zero.

Therefore:

```text
raw_pending_rows = 8
deliverable_pending = 0
held_session_pending = 0
fallback pending_count = 0
```

The fallback result was semantically correct but the shared word `pending` obscured the distinction.
The architecture document now names each state explicitly, and selection requires a valid packet
binding.
