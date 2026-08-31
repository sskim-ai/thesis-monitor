# 2026-08-31 KR V2 Dispatch Timing

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

```text
KR_PRIMARY_ACTUAL_TIME = 2026-08-31T16:16:09.010+09:00
KR_BACKUP_ACTUAL_TIME = 2026-08-31T16:57:11.283+09:00
KR_PACKET_CLAIM_TIME = NOT_CLAIMED
KR_DISPATCHER_ACTUAL_TIME = 2026-08-31T17:10:07.170731+09:00
KR_FIRST_DELIVERY_TIME = 2026-08-31T17:10:09.430568+09:00
KR_LAST_DELIVERY_TIME = 2026-08-31T17:10:19.733510+09:00
KR_DELIVERY_TIMING = NORMAL_1710_DISPATCH
```

The 16:05/16:20/16:50 producer snapshots are distinct from the 16:15/16:55 AI claim tasks. Primary and backup both exited 0 with no eligible packet. The existing 17:10 fallback dispatcher naturally owned delivery; no manual retry relationship exists.
