# 2026-08-31 KR V2 Live Delivery

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

- Delivery mode: `deterministic_fallback`
- Dispatcher: `2026-08-31T17:10:07.170731+09:00`
- Result: `sent`; 9 sent / 0 pending
- Expected: 1 market + 8 stock = 9
- Exact fallback-to-database payload matches: 9/9
- Attempts: one for every row; errors: zero
- Duplicate/orphan/unowned retry: 0/0/0

| ID | Ticker | Status | Attempts | Sent KST | Text SHA256 | Exact |
| --- | --- | --- | --- | --- | --- | --- |
| 416 | __DAILY_DIGEST_KR__ | sent | 1 | 2026-08-31T17:10:09.430568+09:00 | 7cc80173aad7dd0ffba73c7d18d59e0007fbd777fdb04a6e880b207f836ae3b9 | True |
| 417 | 000660 | sent | 1 | 2026-08-31T17:10:11.440152+09:00 | edd9431384b9e259695f6388492bb36cda2c4f32df03a9015c79b4ffd59c1946 | True |
| 418 | 003690 | sent | 1 | 2026-08-31T17:10:12.613043+09:00 | 4327f26b4d222d509136305c460b040f7f0bf89cea5560f753ce47670df0a035 | True |
| 419 | 005490 | sent | 1 | 2026-08-31T17:10:13.742606+09:00 | dd17c3f8a19aee92c7e5c72e0161a505dab07772703eb99095dc4031a8f0cc03 | True |
| 420 | 005930 | sent | 1 | 2026-08-31T17:10:15.180312+09:00 | 40fd75852b52ccfce8842f973d76aa2b74a522a2ee567d556c2b731c057e1893 | True |
| 421 | 010120 | sent | 1 | 2026-08-31T17:10:16.290176+09:00 | 8c08222a8686ff09b78018b4979554a0eddb51290d080160ceed2a5fa3fe15ce | True |
| 422 | 012450 | sent | 1 | 2026-08-31T17:10:17.395787+09:00 | 3ae3f5ec414f8865ceec737454357aebd58eac43e28a252ee8c3f105a9f1eb87 | True |
| 423 | 047810 | sent | 1 | 2026-08-31T17:10:18.639119+09:00 | 6b7c07fbd327b37b277f036d71218cd15ee87082121f48c012db58687630f1ac | True |
| 424 | 086280 | sent | 1 | 2026-08-31T17:10:19.733510+09:00 | 4d88a19cf9718fffca9f99b8035cbcfc1efc063109443a7ab187050ff041b76b | True |

`KR_SENT_PRODUCTION_MESSAGE_COUNT = 9`. `KR_RECEIVED_PRODUCTION_MESSAGE_COUNT = 9` means nine successful backend transport acknowledgements represented by sent receipts; there is no independent Telegram-client read/arrival telemetry. No recipient identifier is recorded here.

```text
KR_LIVE_EXACT_PAYLOAD = PASS
KR_EXACTLY_ONCE_DELIVERY = PASS
KR_DUPLICATE = 0
KR_ORPHAN = 0
KR_UNOWNED_RETRY = 0
```
