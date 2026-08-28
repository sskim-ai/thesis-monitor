# US Current-Time Market Test Delivery

One current market message was sent only to `test:6d6e2ff463bf`. The production
alias was distinct; collision, production intent, production-recipient send, duplicate, orphan,
retry, and unowned retry counts were all `0`. Rendered, outbound, and Telegram response hashes
matched; exact received-payload quality was PASS.

`TEST_CURRENT_MARKET_MESSAGE_COUNT = 1`
`TEST_EXACT_PAYLOAD_MATCH = PASS`
