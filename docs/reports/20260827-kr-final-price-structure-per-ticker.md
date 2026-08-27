# KR Final Price Structure Per-Ticker Audit

`ALL_KR_STOCK_PRICE_STRUCTURE_REPLAY = NOT_RUN_TRACK_A_BLOCKED`

The last validated monitored-KR baseline contained seven tickers, but the current universe was not
re-resolved after Track A failed. No fresh OHLCV request, eligibility calculation, render, or
message generation occurred.

| Prior validated ticker | Current audit state |
| --- | --- |
| 000660 | `NOT_RUN` |
| 003690 | `NOT_RUN` |
| 005490 | `NOT_RUN` |
| 005930 | `NOT_RUN` |
| 010120 | `NOT_RUN` |
| 012450 | `NOT_RUN` |
| 086280 | `NOT_RUN` |

The canonical daily target remains 1,200 and the official provider cap remains 1,000. No claim is
made that any current ticker passed this final preflight.
