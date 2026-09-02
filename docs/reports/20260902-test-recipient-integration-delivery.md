# 2026-09-02 Test Recipient Integration Delivery

- Dedicated non-production sink isolation: `PASS`
- Planned / sent: `22/22`
- Initial / continuation: `20/2`
- Rate-limit recovery: `True`
- Exact payload match: `True`
- Duplicate / orphan: `0/0`
- Production collision / intent / send: `0/0/0`
- Raw recipient IDs retained: `0`

Telegram returned HTTP 429 after 20 exact messages. The continuation contract selected only the
two unsent logical identities and closed the final 22-message set without duplicate delivery.
