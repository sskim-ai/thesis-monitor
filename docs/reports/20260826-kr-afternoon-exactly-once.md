# 2026-08-26 KR Afternoon Exactly-Once Audit

| Measure | Result |
|---|---:|
| Immutable packet snapshots | 3 |
| Active packet owners | 1 |
| Delivery intents | 8 |
| Sent deliveries / receipt-linked rows | 8 / 8 |
| `attempt_count=1` | 8 |
| `last_error` non-null | 0 |
| Duplicate ticker/type delivery | 0 |
| Orphan delivery | 0 |
| Unowned retry | 0 |

The active packet was `2026-08-26-kr-run-40-706bc3003536`. Delivery rows `322` through `329` were held at 16:50, claimed by the deadline fallback at 17:10, and sent once between 17:10:04 and 17:10:12 KST. The delivery result records `delivery_count=8`, `sent_count=8`, and `pending_count=0`.

For all eight rows, the SHA-256 of `_telegram_delivery.rendered_text` exactly matched `_telegram_delivery.content_sha256`. `KR_EXACT_MESSAGE_PAYLOAD_MATCH = PASS`.
