# Track C — Cross-Market Replay + Test Sink + Message Review

Replay:
- every current monitored US/foreign stock
- KR controls: 000660, 003690, 005490, 005930, 010120, 012450, 086280

Verify:
- current quote vs structure close
- near/major S/R
- completed dynamic Bollinger
- one optional provisional Bollinger line
- no semantic leakage / duplicate clutter

Send all test messages to the dedicated non-production sink and inspect exact payloads.
