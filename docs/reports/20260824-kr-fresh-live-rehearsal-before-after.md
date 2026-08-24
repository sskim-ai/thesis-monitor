# KR Natural Failure vs Fresh Rehearsal

| Stage | 16:xx natural run 36 | 19:34 fresh rehearsal |
|---|---|---|
| Evidence class | `NATURAL_FAILED_IMMUTABLE` | `MANUAL_LIVE_REHEARSAL_NO_DELIVERY` |
| Data snapshot | original 16:xx | new cutoff and one fresh collection pass |
| Analysis | 7/7 | 7/7 |
| Packet | 0 | 1 |
| Packet-bound intents | 0 | 8 isolated dry-run intents |
| Duplicate / orphan | 0 / 0 | 0 / 0 |
| Shadow AI | denied | denied; same 210 audit-only unsupported paths |
| Fallback reachability | no packet | full 1+7 bundle reachable |
| Sent | 0 | 0 by design |

The packet-persistence repair works on fresh provider data: shadow ineligibility no longer denies the
production-safe packet or fallback reachability. The rehearsal also exposed an independent macro
legacy-briefing temporal P0. Raw market values are not compared because the data snapshots are not
numerically comparable.

The natural failure archive, run row, receipts, and production packet directories were unchanged.
