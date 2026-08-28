# 2026-08-29 US Morning Data Quality

| Component | Expected | Actual | State | Impact |
| --- | --- | --- | --- | --- |
| core indices | 5 current | 5 current | NONE | none |
| RSP | participation proxy | current; not promoted to breadth | NONE | none |
| SOXX | current relative input | current; relative weakness | NONE | none |
| sector universe | 11 current | 11 current | NONE | none |
| Nasdaq breadth | 2026-08-28 | 2026-08-26 | PUBLICATION_PENDING | safe omission |
| NYSE breadth | official/free supported source | unavailable | SAFE_OMISSION | no synthetic substitute |
| night futures | 2026-08-29 | prior session only | STALE | entire section omitted |
| macro | specific/material/current | none selected | SAFE_OMISSION | current market evidence retained |
| natural run | 1 market + 13 stock | 14/14 sent | NONE | deterministic route delivered |
| AI stock candidate | validator pass | 37 primary errors | MATERIAL_P1 | AI output rejected; safe deterministic delivery already complete |

- Open P0: `0`
- Open material P1: `1`
- Review state: `PARTIAL_SAFE`

The P1 is bounded to the rejected full-stock AI candidate. The requested current market-data extraction and exact delivered market message are evidence-consistent.
