# 2026-09-04 KR Natural Event Timeline

All times are KST.

| Time | Event | Evidence / identity |
|---:|---|---|
| 16:05:31.183 | KR producer started | `monitorrun.id=56` |
| 16:06:27.403 | Run 56 completed: 8/8 | `data/runs/2026-09-04.json` |
| 16:06:27.418 | Authoritative packet persisted | `2026-09-04-kr-run-56-ea785fbd2c9e` |
| 16:06:36.942 | 9 deliveries pending | `delivery-state-receipt.json` |
| 16:15:49.771 | KR primary automation started | `` |
| 16:16:05.738 | Claim acquired; 30-minute lease | `` |
| 16:20:06.338 | Second producer packet persisted | `2026-09-04-kr-run-56-128e4097e823` |
| 16:24:14 | Initial regular schema-4 draft persisted | `` |
| 16:25:31.825 | Primary invoked stock_decision V2 | `` |
| 16:25:32.525 | V2 batch 1 model invocation started | `` |
| 16:28:20.151 | Outer automation sent Ctrl-C | `PRIMARY_ROOT_CAUSE` |
| 16:28:20.679 | stock_decision exited 1 | `` |
| 16:28:33.867 | Regular validation rejected | `` |
| 16:29:41.720 | Corrected regular review finalized and delivery claimed | `` |
| 16:29:43.606 | KR market digest sent | `` |
| 16:29:44.689 | First stock sent | `` |
| 16:29:52.653 | Last stock sent; 9/9 complete | `` |
| 16:31:12.905 | Primary automation completed | `` |
| 16:50:07.237 | Third producer packet persisted | `2026-09-04-kr-run-56-6a9ef43bb878` |
| 16:50:16.430 | Third packet deduped against authoritative send | `` |
| 16:56:49 | KR backup automation started | `` |
| 17:02:32.005 | Backup V2 generation began | `` |
| 17:30:19.026 | Backup V2 accepted artifact created | `` |
| 17:31:34.084 | Backup completed archive-only; no send | `` |

The first material divergence occurred at 16:28:20.151 when the outer automation sent `Ctrl-C` to the still-running V2 subprocess. The regular review then continued, corrected its separate validation errors, and delivered exactly once.
