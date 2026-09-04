# US Exact Delivery Results

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Counts

| Category | Count |
| --- | ---: |
| Primary AI market | 0 |
| Primary AI stocks | 0 |
| Backup AI | 0 |
| Fallback market | 1 |
| Fallback stocks | 14 |
| Total sent | 15 |
| Pending | 0 |
| Duplicates | 0 |

Delivery dispatch began `08:40:04.201264 KST`. The digest receipt was `08:40:06.363050`; stock receipts ran from CORZ at `08:40:07.450053` through WULF at `08:40:21.613300`. Every row had `status=sent` and `attempt_count=1`.

| Message | Source | Delivery ID | Sent KST |
| --- | --- | ---: | --- |
| market | FALLBACK | 497 | `2026-09-04T08:40:06.363050+09:00` |
| CORZ | FALLBACK | 498 | `2026-09-04T08:40:07.450053+09:00` |
| CPNG | FALLBACK | 499 | `2026-09-04T08:40:08.589922+09:00` |
| CRCL | FALLBACK | 500 | `2026-09-04T08:40:09.661940+09:00` |
| GOOGL | FALLBACK | 501 | `2026-09-04T08:40:10.725273+09:00` |
| HUT | FALLBACK | 502 | `2026-09-04T08:40:11.817469+09:00` |
| IBM | FALLBACK | 503 | `2026-09-04T08:40:12.908960+09:00` |
| MU | FALLBACK | 504 | `2026-09-04T08:40:14.026708+09:00` |
| RXRX | FALLBACK | 505 | `2026-09-04T08:40:15.101258+09:00` |
| SKHY | FALLBACK | 506 | `2026-09-04T08:40:16.148265+09:00` |
| SNDK | FALLBACK | 507 | `2026-09-04T08:40:17.300196+09:00` |
| TSLA | FALLBACK | 508 | `2026-09-04T08:40:18.400802+09:00` |
| TSM | FALLBACK | 509 | `2026-09-04T08:40:19.471615+09:00` |
| WRD | FALLBACK | 510 | `2026-09-04T08:40:20.527221+09:00` |
| WULF | FALLBACK | 511 | `2026-09-04T08:40:21.613300+09:00` |

Raw UTF-8 bodies are in `docs/reports/messages/20260904-us-natural/`. No resend was performed.
