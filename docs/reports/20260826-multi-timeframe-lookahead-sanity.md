# Multi-Timeframe Look-Ahead Sanity

Historical cutoffs rebuild daily, weekly, and monthly structures from bars completed by T. Weekly
bars require week completion; monthly bars require the next month boundary. Pivot dates and
confirmation dates must both be on or before T.

| Ticker | Historical cutoff | Violations | Validation |
|---|---|---:|---|
| 000660 | 2026-05-29 | 0 | True |
| 003690 | 2026-05-29 | 0 | True |
| 005490 | 2026-05-29 | 0 | True |
| 005930 | 2026-05-29 | 0 | True |
| 010120 | 2026-05-29 | 0 | True |
| 012450 | 2026-05-29 | 0 | True |
| 086280 | 2026-05-29 | 0 | True |
| CORZ | 2026-05-29 | 0 | True |
| CRCL | 2026-05-29 | 0 | True |
| GOOGL | 2026-05-29 | 0 | True |
| HUT | 2026-05-29 | 0 | True |
| IBM | 2026-05-29 | 0 | True |
| MU | 2026-05-29 | 0 | True |
| RXRX | 2026-05-29 | 0 | True |
| SKHY | 2026-07-10 | 0 | True |
| SNDK | 2026-05-29 | 0 | True |
| TSLA | 2026-05-29 | 0 | True |
| TSM | 2026-05-29 | 0 | True |
| WRD | 2026-05-29 | 0 | True |
| WULF | 2026-05-29 | 0 | True |

`LOOKAHEAD_LEAK = 0`; `LOOKAHEAD_SAFETY = PASS`.
