
# 2026-08-27 KR Afternoon Exactly-Once Audit

## Counts

| Metric | Result |
|---|---:|
| Immutable producer packet snapshots | 3 |
| Unique delivery intents | 8 |
| Terminal deliveries | 8 |
| Receipt-linked persisted rows | 8 |
| Duplicate deliveries | 0 |
| Orphan deliveries | 0 |
| Unowned retries | 0 |

| ID | Ticker | Status | Attempts | Last error | Sent UTC | Payload parity |
|---|---|---|---|---|---|---|
| 344 | __DAILY_DIGEST_KR__ | sent | 2 | none | 2026-08-27 08:10:05.808727 | PASS |
| 345 | 000660 | sent | 2 | none | 2026-08-27 08:10:06.885146 | PASS |
| 346 | 003690 | sent | 2 | none | 2026-08-27 08:10:07.957707 | PASS |
| 347 | 005490 | sent | 2 | none | 2026-08-27 08:10:09.083414 | PASS |
| 348 | 005930 | sent | 2 | none | 2026-08-27 08:10:10.268626 | PASS |
| 349 | 010120 | sent | 2 | none | 2026-08-27 08:10:11.396589 | PASS |
| 350 | 012450 | sent | 2 | none | 2026-08-27 08:10:12.559718 | PASS |
| 351 | 086280 | sent | 2 | none | 2026-08-27 08:10:13.674010 | PASS |

`attempt_count=2` is the expected held-intent plus terminal dispatcher attempt. The repository does not persist a separate Telegram remote message ID; notification IDs `344` through `351` are the receipt-linked persistent delivery identities. All eight archive, persisted, and rendered payloads match byte-for-byte.

`KR_PACKET_INTEGRITY = PASS`
`KR_EXACTLY_ONCE = PASS`
