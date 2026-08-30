# Cleanup Test-Sink Receipt

Exactly five messages were sent to the dedicated non-production test sink in this order:

1. US market
2. 003690
3. 000660
4. GOOGL
5. RXRX

| Gate | Result |
|---|---|
| sent | 5/5 |
| exact outbound/received SHA | PASS |
| duplicate | 0 |
| orphan | 0 |
| request retry | 0 |
| unowned retry | 0 |
| production recipient send | 0 |
| production intent | 0 |

No raw Telegram ID or token is present in repository artifacts or this report.

- `TEST_MESSAGE_COUNT = 5`
- `TEST_EXACT_PAYLOAD_MATCH = PASS`
- `TEST_DUPLICATE = 0`
- `TEST_ORPHAN = 0`
- `TEST_PRODUCTION_RECIPIENT_SEND = 0`
- `PRODUCTION_DELIVERY_INTENT_CREATED = 0`
