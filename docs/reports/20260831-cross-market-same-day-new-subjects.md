# 2026-08-31 Cross-Market Same-Day New Subjects

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

| Ticker | Market | Active since KST | Packet-cycle result | V2 readiness |
| --- | --- | --- | --- | --- |
| 047810 | KR | 2026-08-31T15:21:26.575706+09:00 | Included in monitor, all three packet snapshots, fallback render, delivery intent, and exact live delivery | NOT_READY: company profile missing |
| CPNG | US | 2026-08-31T15:36:49.568475+09:00 | Correctly excluded from KR; expected in next US universe | NOT_READY_SAFE: no security master, profile, or assessment |

The two missing profiles exactly explain the packet profile gate count. This is one cross-market onboarding synchronization defect: newly active subjects became production-universe members before profile readiness was complete, and the global gate suppressed V2 generation for all eight KR stocks.

Gates:

```text
KR_NEW_SUBJECT_047810 = FULLY_INCLUDED
US_NEW_SUBJECT_CPNG_NEXT_LIVE_ELIGIBILITY = NOT_READY_SAFE
```
