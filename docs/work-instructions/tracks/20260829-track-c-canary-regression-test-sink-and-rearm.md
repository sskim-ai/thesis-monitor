# Track C — Canary Regression + Test Sink + Re-arm

Before first natural canary cycle:

- test fresh current messages for 003690 / 000660 / GOOGL / RXRX
- test historical BUY fixture(s)
- exact payload
- decision continuity
- polarity message-quality

No production test sends.

After PASS:
re-arm the exact same 2 KR + 2 US canary.
Natural counters remain 0/2.

No expansion.
