# XKRX Role-target Matrix

| Observed KST | Role | Target | Eligible | Reason |
| --- | --- | --- | --- | --- |
| 2026-08-21 08:05 | KRX next morning | 2026-08-20 | yes | preceding completed session |
| 2026-08-21 16:05 | KRX same day | 2026-08-21 | yes | same-day session completed |
| 2026-08-22 08:20 | night production | NIGHT 2026-08-22 / business 2026-08-21 | yes | canonical night basis |
| 2026-08-22 08:45 | night observer | NIGHT 2026-08-22 / business 2026-08-21 | yes | canonical night basis |
| 2026-08-22 09:15 | night observer | NIGHT 2026-08-22 / business 2026-08-21 | yes before dedup | canonical night basis |
| 2026-08-23 08:45 | night observer | NIGHT 2026-08-22 / business 2026-08-21 | yes before dedup | canonical night basis |
| 2026-08-22 08:05 | KRX next morning | 2026-08-21 | yes | preceding completed session |
| 2026-08-23 08:05 | KRX next morning | 2026-08-21 | yes before dedup | preceding completed session |
| 2026-08-24 08:05 | KRX next morning | 2026-08-21 | yes before dedup | preceding completed session |
| 2026-08-22 16:05 | KRX same day | none | no | `no_valid_role_target` |
| 2026-08-17 08:05 | KRX next morning | 2026-08-14 | yes | holiday traversal |
| 2026-08-18 08:05 | KRX next morning | 2026-08-14 | yes before dedup | day-after-holiday traversal |
| 2026-09-26/28 08:05 | KRX next morning | 2026-09-23 | yes | consecutive-holiday traversal |
| 2026-12-31 08:05 | KRX next morning | 2026-12-30 | yes | special closure |
| 2026-12-31 16:05 | KRX same day | none | no | `no_valid_role_target` |

Terminal/dedup gates run after target resolution and before provider access.
