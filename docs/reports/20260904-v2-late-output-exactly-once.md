# 2026-09-04 V2 Late Output and Exactly-Once Proof

The terminal suppression writer first checks for a matching accepted receipt or
accepted claim-bound artifact. If one exists, it preserves that artifact and
returns `ACCEPTED`; a late timeout cannot replace it.

Existing claim and delivery tests also prove:

- a fresh primary heartbeat blocks backup reclaim
- an expired claim can be reclaimed
- the stale primary finalizer is rejected
- late validation after deterministic fallback is receipt-only
- repeated delivery attempts do not create another sent row

The real KR TEST run produced nine sends, zero duplicates, and
`SAFE_NOOP_PRIMARY_ACTIVE` for the backup probe.

| Gate | Result |
|---|---|
| Healthy primary backup reclaim | 0 |
| Stale primary reclaim | PASS |
| Stale primary finalize | REJECTED |
| Late accepted artifact overwrite | 0 |
| Duplicate delivery | 0 |
