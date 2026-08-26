# Price Structure v3 Generalization Bounded Repair

The common contract replayed `20/20` subjects: KR `7/7`, US/foreign `13/13`. A missing valid impulse
remains an allowed abstention; it does not trigger ticker-specific fallback or a forced wave.

| Ticker | Daily | Weekly | Monthly | Grand | Current | Intermediate |
| --- | --- | --- | --- | --- | --- | --- |
| 000660 | 1200 | 600 | 300 | 8 | 8 | 1 |
| 003690 | 1200 | 600 | 300 | 8 | 8 | 0 |
| 005490 | 1200 | 600 | 300 | 8 | 0 | 0 |
| 005930 | 1200 | 600 | 300 | 8 | 5 | 0 |
| 010120 | 1200 | 600 | 300 | 8 | 8 | 1 |
| 012450 | 1200 | 600 | 300 | 8 | 8 | 0 |
| 086280 | 1200 | 600 | 248 | 8 | 8 | 0 |
| CORZ | 1153 | 240 | 55 | 0 | 0 | 0 |
| CRCL | 307 | 64 | 14 | 0 | 0 | 0 |
| GOOGL | 1200 | 600 | 264 | 8 | 8 | 0 |
| HUT | 1200 | 271 | 62 | 0 | 8 | 4 |
| IBM | 1200 | 600 | 300 | 8 | 8 | 0 |
| MU | 1200 | 600 | 300 | 8 | 0 | 0 |
| RXRX | 1200 | 280 | 64 | 0 | 0 | 0 |
| SKHY | 33 | 7 | 1 | 0 | 0 | 0 |
| SNDK | 378 | 78 | 18 | 0 | 0 | 0 |
| TSLA | 1200 | 600 | 194 | 8 | 8 | 0 |
| TSM | 1200 | 600 | 260 | 8 | 8 | 2 |
| WRD | 458 | 96 | 22 | 0 | 0 | 0 |
| WULF | 1178 | 245 | 56 | 0 | 8 | 0 |

```text
NO_FORCED_ELLIOTT = PASS
KR_SHADOW_REPLAY = 7/7
US_SHADOW_REPLAY = 13/13
CURRENT_USER_VISIBLE_MESSAGE_DIFF = 0
```
