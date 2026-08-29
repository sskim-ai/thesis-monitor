# Decision Polarity Test-Sink Proof

- Route: existing dedicated non-production sink; identifiers remain outside git and reports.
- Current messages: `4`
- Historical BUY fixtures: `2`
- Sent / exact received payload: `6 / 6`
- Request retry / duplicate / orphan / unowned retry: `0 / 0 / 0 / 0`
- Production collision / recipient send / delivery intent: `0 / 0 / 0`

Payload SHA equality was checked for every sent row. This test batch does not count toward natural
canary cycles.

`TEST_MESSAGE_COUNT = 6`

`TEST_EXACT_PAYLOAD_MATCH = PASS`
