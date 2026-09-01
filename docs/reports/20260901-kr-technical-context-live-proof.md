# KR Technical Context Live Proof

## Result

- FULL: `8`
- PARTIAL_SAFE / UNAVAILABLE / INVALID: `0 / 0 / 0`
- Packet-owned requests/success: `24 / 24`
- Local OHLCV HTTP during V2 decision stage: `0`

| Ticker | State | D | W | M | Bars D/W/M | Features D/W/M |
| --- | --- | --- | --- | --- | --- | --- |
| 000660 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/300 | 78/78/78 |
| 003690 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/300 | 78/78/78 |
| 005490 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/300 | 78/78/78 |
| 005930 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/300 | 78/78/78 |
| 010120 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/300 | 78/78/78 |
| 012450 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/300 | 78/78/78 |
| 047810 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/184 | 78/78/69 |
| 086280 | FULL | 2026-09-01 | 2026-08-31 | 2026-09-01 | 1000/600/250 | 78/78/72 |

047810's shorter monthly history (`184` bars, `69` features) still satisfied the declared FULL contract. No single technical context blocked a peer.
