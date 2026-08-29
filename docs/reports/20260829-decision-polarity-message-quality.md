# Decision Polarity Message Quality

Current production-equivalent test message lengths:

| Ticker | Characters | Result |
|---|---:|---|
| 003690 | 1,937 | PASS |
| 000660 | 1,808 | PASS |
| GOOGL | 2,697 | PASS |
| RXRX | 2,110 | PASS |

Historical fixture lengths are 569 and 942. Every payload contains one selected BULLISH and one
selected BEARISH claim; neutral context remains structured and unrendered. Existing base message
text remains byte-intact around the inserted block.

- Exact numeric claims newly introduced in current canary blocks: `0`
- Cross-side duplicate evidence refs: `0`
- Order/sizing language: `0`
- Existing quality threshold change: `0`

`BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS`
