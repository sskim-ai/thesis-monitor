# US V2 Message Quality

| Ticker | Length | Explicit decision | Empty sections | Order command | Renderer quality | V2 quality |
| --- | --- | --- | --- | --- | --- | --- |
| CORZ | 1059 | False | 0 | False | PASS | FAIL |
| CPNG | 1077 | False | 0 | False | PASS | FAIL |
| CRCL | 974 | False | 0 | False | PASS | FAIL |
| GOOGL | 1012 | False | 0 | False | PASS | FAIL |
| HUT | 1018 | False | 0 | False | PASS | FAIL |
| IBM | 1246 | False | 0 | False | PASS | FAIL |
| MU | 1288 | False | 0 | False | PASS | FAIL |
| RXRX | 878 | False | 0 | False | PASS | FAIL |
| SKHY | 849 | False | 0 | False | PASS | FAIL |
| SNDK | 854 | False | 0 | False | PASS | FAIL |
| TSLA | 945 | False | 0 | False | PASS | FAIL |
| TSM | 792 | False | 0 | False | PASS | FAIL |
| WRD | 785 | False | 0 | False | PASS | FAIL |
| WULF | 1083 | False | 0 | False | PASS | FAIL |

The deterministic messages were readable and structurally complete, but all 14 lacked the required accepted BUY/HOLD/SELL block. `투자 논리: 유지` was not counted as HOLD. Raw candidate visibility and unadjudicated material decision visibility were both zero.

- `US_EMPTY_VISIBLE_SECTION_COUNT = 0`
- `US_V2_MESSAGE_QUALITY = FAIL`
