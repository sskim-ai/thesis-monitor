# KR Final Test Delivery

| Gate | Result |
| --- | --- |
| Test sink | `test:6d6e2ff463bf` |
| Market / stock / total | `1 / 7 / 8` |
| Sent | `8/8` |
| Exact rendered/outbound/received hash | `8/8 PASS` |
| One attempt each | PASS |
| Duplicate / orphan / unowned retry | `0 / 0 / 0` |
| Production-recipient sends | `0` |
| Production delivery intents | `0` |

Telegram `sendMessage` responses returned the exact text for all eight payloads. The receipt stores
only aliases, payload hashes, sequence, route, and redacted remote-message aliases.
