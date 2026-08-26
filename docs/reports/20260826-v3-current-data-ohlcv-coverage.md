# Price Structure v3 Current-Data OHLCV Coverage

- Instruction commit: `688c17280a10e91214d4bd9888522fdc6f9bc0c5`
- Implementation: `ef586c3816ff76417d2620636975d054935533d4`
- Test run: `v3-current-run:ff97be1d62a9810dc315`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-current-render:f6152bc2c61ced3eeffa`
- Observed at: `2026-08-26T19:49:57+09:00`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

Daily history combines the existing official 1200-bar cache with the newly collected current provider page; no padding is used. Short listings remain partial.

| Ticker | TF | Requested | Returned | Completed | Used | First | Last | Last state | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000660 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 000660 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 000660 | monthly | 300 | 357 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| 003690 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 003690 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 003690 | monthly | 300 | 500 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| 005490 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 005490 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 005490 | monthly | 300 | 459 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| 005930 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 005930 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 005930 | monthly | 300 | 500 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| 010120 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 010120 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 010120 | monthly | 300 | 386 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| 012450 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 012450 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 012450 | monthly | 300 | 472 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| 086280 | daily | 1200 | 1201 | 1200 | 1200 | 2021-09-30 | 2026-08-26 | COMPLETE | PASS |
| 086280 | weekly | 600 | 1000 | 600 | 601 | 2015-02-16 | 2026-08-24 | PARTIAL | PASS |
| 086280 | monthly | 300 | 249 | 248 | 249 | 2005-12-26 | 2026-08-03 | PARTIAL | PARTIAL |
| CORZ | daily | 1200 | 1153 | 1153 | 1153 | 2022-01-20 | 2026-08-25 | COMPLETE | PARTIAL |
| CORZ | weekly | 600 | 241 | 240 | 241 | 2022-01-20 | 2026-08-24 | PARTIAL | PARTIAL |
| CORZ | monthly | 300 | 56 | 55 | 56 | 2022-01-20 | 2026-08-03 | PARTIAL | PARTIAL |
| CRCL | daily | 1200 | 307 | 307 | 307 | 2025-06-05 | 2026-08-25 | COMPLETE | PARTIAL |
| CRCL | weekly | 600 | 65 | 64 | 65 | 2025-06-05 | 2026-08-24 | PARTIAL | PARTIAL |
| CRCL | monthly | 300 | 15 | 14 | 15 | 2025-06-05 | 2026-08-03 | PARTIAL | PARTIAL |
| GOOGL | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| GOOGL | weekly | 600 | 1000 | 600 | 601 | 2015-02-23 | 2026-08-24 | PARTIAL | PASS |
| GOOGL | monthly | 300 | 265 | 264 | 265 | 2004-08-19 | 2026-08-03 | PARTIAL | PARTIAL |
| HUT | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| HUT | weekly | 600 | 272 | 271 | 272 | 2021-06-15 | 2026-08-24 | PARTIAL | PARTIAL |
| HUT | monthly | 300 | 63 | 62 | 63 | 2021-06-15 | 2026-08-03 | PARTIAL | PARTIAL |
| IBM | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| IBM | weekly | 600 | 1000 | 600 | 601 | 2015-02-23 | 2026-08-24 | PARTIAL | PASS |
| IBM | monthly | 300 | 680 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| MU | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| MU | weekly | 600 | 1000 | 600 | 601 | 2015-02-23 | 2026-08-24 | PARTIAL | PASS |
| MU | monthly | 300 | 448 | 300 | 301 | 2001-08-01 | 2026-08-03 | PARTIAL | PASS |
| RXRX | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| RXRX | weekly | 600 | 281 | 280 | 281 | 2021-04-16 | 2026-08-24 | PARTIAL | PARTIAL |
| RXRX | monthly | 300 | 65 | 64 | 65 | 2021-04-16 | 2026-08-03 | PARTIAL | PARTIAL |
| SKHY | daily | 1200 | 33 | 33 | 33 | 2026-07-10 | 2026-08-25 | COMPLETE | PARTIAL |
| SKHY | weekly | 600 | 8 | 7 | 8 | 2026-07-10 | 2026-08-24 | PARTIAL | FAIL |
| SKHY | monthly | 300 | 2 | 1 | 2 | 2026-07-10 | 2026-08-03 | PARTIAL | FAIL |
| SNDK | daily | 1200 | 378 | 378 | 378 | 2025-02-24 | 2026-08-25 | COMPLETE | PARTIAL |
| SNDK | weekly | 600 | 79 | 78 | 79 | 2025-02-24 | 2026-08-24 | PARTIAL | PARTIAL |
| SNDK | monthly | 300 | 19 | 18 | 19 | 2025-02-24 | 2026-08-03 | PARTIAL | PARTIAL |
| TSLA | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| TSLA | weekly | 600 | 844 | 600 | 601 | 2015-02-23 | 2026-08-24 | PARTIAL | PASS |
| TSLA | monthly | 300 | 195 | 194 | 195 | 2010-06-29 | 2026-08-03 | PARTIAL | PARTIAL |
| TSM | daily | 1200 | 1200 | 1200 | 1200 | 2021-11-11 | 2026-08-25 | COMPLETE | PASS |
| TSM | weekly | 600 | 1000 | 600 | 601 | 2015-02-23 | 2026-08-24 | PARTIAL | PASS |
| TSM | monthly | 300 | 261 | 260 | 261 | 2004-12-21 | 2026-08-03 | PARTIAL | PARTIAL |
| WRD | daily | 1200 | 458 | 458 | 458 | 2024-10-25 | 2026-08-25 | COMPLETE | PARTIAL |
| WRD | weekly | 600 | 97 | 96 | 97 | 2024-10-25 | 2026-08-24 | PARTIAL | PARTIAL |
| WRD | monthly | 300 | 23 | 22 | 23 | 2024-10-25 | 2026-08-03 | PARTIAL | PARTIAL |
| WULF | daily | 1200 | 1178 | 1178 | 1178 | 2021-12-14 | 2026-08-25 | COMPLETE | PARTIAL |
| WULF | weekly | 600 | 246 | 245 | 246 | 2021-12-14 | 2026-08-24 | PARTIAL | PARTIAL |
| WULF | monthly | 300 | 57 | 56 | 57 | 2021-12-14 | 2026-08-03 | PARTIAL | PARTIAL |
