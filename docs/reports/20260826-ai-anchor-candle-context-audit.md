# AI Anchor Candle-Context Audit

The compact-rich packet carries bounded raw bars plus range/body/wick, close location, gap,
volume/trading-value ratios, HH/LH/HL/LL, breakout, reclaim, rejection, pivot neighborhoods, and
swing segments. Defaults remain monthly `36 ±2`, weekly `52 ±3`, daily `90 ±5`; candidate
neighborhoods may add older bars without omitting eligible canonical pivots.

| Ticker | TF | Available | Recent | Included | Pivots | Neighborhoods | Omitted | Bytes |
|---|---|---|---|---|---|---|---|---|
| 000660 | monthly | 299 | 36 | 41 | 4 | 4 | 0 | 33619 |
| 000660 | weekly | 299 | 52 | 84 | 6 | 6 | 0 | 68405 |
| 000660 | daily | 300 | 90 | 145 | 5 | 5 | 0 | 112187 |
| 003690 | monthly | 299 | 36 | 41 | 2 | 2 | 0 | 32415 |
| 003690 | weekly | 299 | 52 | 64 | 4 | 4 | 0 | 53360 |
| 003690 | daily | 300 | 90 | 155 | 7 | 7 | 0 | 116678 |
| 005490 | monthly | 299 | 36 | 44 | 4 | 4 | 0 | 35973 |
| 005490 | weekly | 299 | 52 | 99 | 9 | 9 | 0 | 78390 |
| 005490 | daily | 300 | 90 | 134 | 5 | 5 | 0 | 102228 |
| 005930 | monthly | 299 | 36 | 41 | 4 | 4 | 0 | 32350 |
| 005930 | weekly | 299 | 52 | 86 | 6 | 6 | 0 | 67919 |
| 005930 | daily | 300 | 90 | 156 | 6 | 6 | 0 | 117734 |
| 010120 | monthly | 299 | 36 | 44 | 8 | 8 | 0 | 40223 |
| 010120 | weekly | 299 | 52 | 87 | 6 | 6 | 0 | 70206 |
| 010120 | daily | 300 | 90 | 165 | 7 | 7 | 0 | 123384 |
| 012450 | monthly | 299 | 36 | 44 | 4 | 4 | 0 | 36969 |
| 012450 | weekly | 299 | 52 | 77 | 4 | 4 | 0 | 62296 |
| 012450 | daily | 300 | 90 | 178 | 8 | 8 | 0 | 133907 |
| 086280 | monthly | 248 | 36 | 41 | 4 | 4 | 0 | 34697 |
| 086280 | weekly | 299 | 52 | 82 | 5 | 5 | 0 | 62387 |
| 086280 | daily | 300 | 90 | 188 | 11 | 11 | 0 | 144899 |
| CORZ | monthly | 55 | 36 | 36 | 5 | 5 | 0 | 30061 |
| CORZ | weekly | 240 | 52 | 66 | 2 | 2 | 0 | 46744 |
| CORZ | daily | 300 | 90 | 145 | 7 | 7 | 0 | 113794 |
| CRCL | monthly | 14 | 14 | 14 | 0 | 0 | 0 | 9277 |
| CRCL | weekly | 64 | 52 | 52 | 2 | 2 | 0 | 36413 |
| CRCL | daily | 300 | 90 | 178 | 10 | 10 | 0 | 134104 |
| GOOGL | monthly | 264 | 36 | 41 | 3 | 3 | 0 | 31858 |
| GOOGL | weekly | 299 | 52 | 87 | 8 | 8 | 0 | 71533 |
| GOOGL | daily | 300 | 90 | 145 | 8 | 8 | 0 | 113536 |
| HUT | monthly | 62 | 36 | 36 | 2 | 2 | 0 | 26882 |
| HUT | weekly | 271 | 52 | 91 | 9 | 9 | 0 | 73599 |
| HUT | daily | 300 | 90 | 145 | 5 | 5 | 0 | 108591 |
| IBM | monthly | 299 | 36 | 41 | 3 | 3 | 0 | 32803 |
| IBM | weekly | 299 | 52 | 80 | 4 | 4 | 0 | 59722 |
| IBM | daily | 300 | 90 | 156 | 10 | 10 | 0 | 121101 |
| MU | monthly | 299 | 36 | 41 | 4 | 4 | 0 | 31696 |
| MU | weekly | 299 | 52 | 73 | 6 | 6 | 0 | 61175 |
| MU | daily | 300 | 90 | 123 | 3 | 3 | 0 | 90975 |
| RXRX | monthly | 64 | 36 | 41 | 2 | 2 | 0 | 28882 |
| RXRX | weekly | 280 | 52 | 69 | 3 | 3 | 0 | 52044 |
| RXRX | daily | 300 | 90 | 188 | 11 | 11 | 0 | 140256 |
| SKHY | monthly | 1 | 1 | 1 | 0 | 0 | 0 | 1062 |
| SKHY | weekly | 7 | 7 | 7 | 0 | 0 | 0 | 4842 |
| SKHY | daily | 33 | 33 | 33 | 0 | 0 | 0 | 22062 |
| SNDK | monthly | 18 | 18 | 18 | 2 | 2 | 0 | 13483 |
| SNDK | weekly | 78 | 52 | 59 | 2 | 2 | 0 | 42089 |
| SNDK | daily | 300 | 90 | 123 | 3 | 3 | 0 | 91124 |
| TSLA | monthly | 194 | 36 | 45 | 5 | 5 | 0 | 36505 |
| TSLA | weekly | 299 | 52 | 91 | 9 | 9 | 0 | 74509 |
| TSLA | daily | 299 | 90 | 112 | 3 | 3 | 0 | 85885 |
| TSM | monthly | 260 | 36 | 41 | 3 | 3 | 0 | 31688 |
| TSM | weekly | 299 | 52 | 98 | 9 | 9 | 0 | 78795 |
| TSM | daily | 300 | 90 | 145 | 5 | 5 | 0 | 105793 |
| WRD | monthly | 22 | 22 | 22 | 0 | 0 | 0 | 14152 |
| WRD | weekly | 96 | 52 | 63 | 2 | 2 | 0 | 43134 |
| WRD | daily | 300 | 90 | 148 | 7 | 7 | 0 | 111132 |
| WULF | monthly | 56 | 36 | 41 | 6 | 6 | 0 | 33958 |
| WULF | weekly | 245 | 52 | 63 | 2 | 2 | 0 | 46173 |
| WULF | daily | 300 | 90 | 112 | 2 | 2 | 0 | 81937 |

`RICH_CANDLE_CONTEXT_PACKET = PASS`

`RICH_PACKET_SUFFICIENCY = PARTIAL`
