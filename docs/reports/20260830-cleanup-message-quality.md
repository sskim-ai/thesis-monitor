# Cleanup Message Quality

| Message | Characters | Result |
|---|---:|---|
| US market | 318 | PASS |
| 003690 | 1,937 | PASS |
| 000660 | 1,808 | PASS |
| GOOGL | 1,893 | PASS |
| RXRX | 1,452 | PASS |

US market internals contain two participation/style lines, one semiconductor line, and the unchanged sector leader/laggard pair. IWM and SOXX claims appear exactly once. GOOGL/RXRX core claims are Korean, polarity is preserved, and no imperative order or sizing language appears.

Validation:

- Focused: `47 passed`
- Full pytest: `1911 passed, 1 warning`
- Full Ruff: `PASS`
- `git diff --check`: `PASS`
- Investment Knowledge checksum/mirror: `PASS`
- Chart Knowledge checksum/mirror: `PASS`
- Public Action: `0.4.5`
- Output schema: `4`
- operationId: `20/20 unique`

- `US_MARKET_INTERNALS_MESSAGE_QUALITY = PASS`
- `CANARY_STOCK_MESSAGE_QUALITY = PASS`
- `BUY_SELL_POLARITY_MESSAGE_QUALITY = PASS`
