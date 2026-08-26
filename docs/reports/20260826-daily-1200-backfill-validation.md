# Daily 1200 Backfill Validation

```text
DAILY_1200 = PASS
OHLCV_1200_BACKFILL = PASS
LONG_LISTED_PASS = 14
SHORT_LISTING_SAFE_PARTIAL = 6
OHLCV_DUPLICATE_DATE = 0
OHLCV_STITCH_BASIS_CONFLICT = 0
OHLCV_SECURITY_MISMATCH = 0
```

The seven-stock KR cross-section identified two provider-wide market-closure dates absent from the
packaged future calendar (`2026-06-03`, `2026-07-17`). They are explicit audit exclusions, not
silent per-ticker gap suppression. Incremental append and revision behavior is covered by a cache-hit
fixture; the initial frozen backfill correctly has cache hits `0`.

| Ticker | Cache | Cached | Complete D | Complete W | Complete M |
| --- | --- | --- | --- | --- | --- |
| 000660 | PASS | 1200 | 1200 | 600 | 300 |
| 003690 | PASS | 1200 | 1200 | 600 | 300 |
| 005490 | PASS | 1200 | 1200 | 600 | 300 |
| 005930 | PASS | 1200 | 1200 | 600 | 300 |
| 010120 | PASS | 1200 | 1200 | 600 | 300 |
| 012450 | PASS | 1200 | 1200 | 600 | 300 |
| 086280 | PASS | 1200 | 1200 | 600 | 248 |
| CORZ | PARTIAL | 1153 | 1153 | 240 | 55 |
| CRCL | PARTIAL | 307 | 307 | 64 | 14 |
| GOOGL | PASS | 1200 | 1200 | 600 | 264 |
| HUT | PASS | 1200 | 1200 | 271 | 62 |
| IBM | PASS | 1200 | 1200 | 600 | 300 |
| MU | PASS | 1200 | 1200 | 600 | 300 |
| RXRX | PASS | 1200 | 1200 | 280 | 64 |
| SKHY | PARTIAL | 33 | 33 | 7 | 1 |
| SNDK | PARTIAL | 378 | 378 | 78 | 18 |
| TSLA | PASS | 1200 | 1200 | 600 | 194 |
| TSM | PASS | 1200 | 1200 | 600 | 260 |
| WRD | PARTIAL | 458 | 458 | 96 | 22 |
| WULF | PARTIAL | 1178 | 1178 | 245 | 56 |
