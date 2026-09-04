# 2026-09-04 US Backup Reclaim and Fencing Contract

## Healthy primary

A fresh primary heartbeat extends the lease. A backup claim attempt sees no reclaimable packet and performs `SAFE_NOOP_PRIMARY_ACTIVE`; it does not start a second model call or replace delivery ownership.

## Dead or stale primary

When heartbeat renewal stops and the lease becomes stale, the backup can claim the packet with a new fencing token and incremented generation. The old primary's finalization is rejected as `stale_claim_output`; the backup output remains authoritative.

| Controlled gate | Result |
|---|---|
| Fresh primary blocks backup | `PASS` |
| Stale primary allows reclaim | `PASS` |
| New fencing token on reclaim | `PASS` |
| Stale finalizer rejected | `PASS` |
| Backup can finalize | `PASS` |
| Duplicate delivery | `0` |

The real TEST E2E also observed `SAFE_NOOP_PRIMARY_ACTIVE` after a production-equivalent run that exceeded the original 10-minute lease boundary.
