# 2026-09-03 US Natural Delivery Proof

## Terminal Result

At `08:40:08-08:40:24 KST`, the natural deterministic fallback delivered one
market message and 14 stock messages.

| Check | Result |
| --- | ---: |
| Planned messages | 15 |
| Sent messages | 15 |
| Pending | 0 |
| Failed | 0 |
| Attempt count per message | 1 |
| Duplicate deliveries | 0 |
| Archive-to-ledger exact text matches | 15/15 |
| AI-assisted messages | 0 |
| V2 balance lines | 0 |

The terminal archive reports `delivery_mode=deterministic_fallback` and
`status=sent`. Fallback safety worked exactly; the intended V2 natural proof did
not.

- `US_DELIVERY = PASS_FALLBACK`
- `US_DELIVERY_EXACTLY_ONCE = PASS`
- `US_FALLBACK_COUNT = 15`
- `US_SENT_MESSAGE_COUNT = 15`
- `US_ACKNOWLEDGED_MESSAGE_COUNT = 15`
- `US_DUPLICATE = 0`
- `US_ORPHAN = 0`
- `US_UNOWNED_RETRY = 0`
- `US_EXACTLY_ONCE = PASS`
- `US_EXACT_PAYLOAD = PASS`
- `MANUAL_TASK_RUN = 0`
- `MANUAL_TELEGRAM_SEND = 0`
