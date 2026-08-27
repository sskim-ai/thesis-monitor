# KR Market Internal Test Delivery

- Route: dedicated non-production test sink
- Packet: `2026-08-27-kr-run-42-5d8d23e6fbd6`
- Planned / sent market messages: `1 / 1`
- Stock messages: `0`
- Send attempts: `1`
- Character count: `555`
- Renderer / outbound / received SHA-256:
  `fe3cf7e04f0e0163106cbfea61d7c7e6af9fbf6563443665d0776cd255af9f3a`
- Exact payload match: `PASS`

The sender revalidated that the secret-backed test recipient differed from the production
recipient before sending. No recipient ID, token, auth header, or account identifier is retained in
this report.

`TEST_MARKET_MESSAGE_COUNT = 1`  
`TEST_DUPLICATE = 0`  
`TEST_ORPHAN = 0`  
`TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0`  
`PRODUCTION_DELIVERY_INTENT_CREATED = 0`  
`TEST_EXACT_PAYLOAD_MATCH = PASS`

