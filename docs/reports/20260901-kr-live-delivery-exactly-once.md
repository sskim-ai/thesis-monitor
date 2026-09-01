# KR Live Delivery Exactly Once

## Exactly-once result

| Ledger ID | Ticker | Status | Attempt | Chunk | Sent KST |
| --- | --- | --- | --- | --- | --- |
| 440 | __DAILY_DIGEST_KR__ | sent | 1 | 1/1 | 2026-09-01T17:10:08.749557+09:00 |
| 441 | 000660 | sent | 1 | 1/1 | 2026-09-01T17:10:09.731815+09:00 |
| 442 | 003690 | sent | 1 | 1/1 | 2026-09-01T17:10:10.861715+09:00 |
| 443 | 005490 | sent | 1 | 1/1 | 2026-09-01T17:10:11.991152+09:00 |
| 444 | 005930 | sent | 1 | 1/1 | 2026-09-01T17:10:13.017214+09:00 |
| 445 | 010120 | sent | 1 | 1/1 | 2026-09-01T17:10:14.039069+09:00 |
| 446 | 012450 | sent | 1 | 1/1 | 2026-09-01T17:10:15.088026+09:00 |
| 447 | 047810 | sent | 1 | 1/1 | 2026-09-01T17:10:16.076473+09:00 |
| 448 | 086280 | sent | 1 | 1/1 | 2026-09-01T17:10:17.090544+09:00 |

- Expected/sent/recorded: `9/9/9`
- Attempt count: `1` for every row
- Duplicate/orphan/unowned retry: `0/0/0`
- Manual send: `0`

`KR_EXACTLY_ONCE_DELIVERY = PASS`
