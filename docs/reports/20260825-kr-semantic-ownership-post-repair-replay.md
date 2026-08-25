# KR Semantic Ownership Post-Repair Replay

- Packet: `2026-08-25-kr-run-38-6cd8c5d5091b`
- Packet SHA-256: `ef456b24b036fcc1b6926489c5e8058eed8a70f570f5df1d49e9c93fe35f487d`
- Messages: `8`
- Eligible safe terminal outputs: `8/8`
- Validation issues: `0`
- Runtime quality: `PASS`
- Selected: `market:2026-08-25-kr-run-38-6cd8c5d5091b, stock:012450, stock:000660`
- Hanwha selected / ownership PASS: `True / PASS`
- Provider recollection / delivery / DB mutation: `0 / 0 / 0`

Hanwha HBM, memory ASP, memory product-mix, and wrong expectation-level leaks are all `0`. KR valuation repair, Inventory semantics, investor-flow reconciliation, macro temporal handling, and Market Adapter safe-PARTIAL behavior remain covered by the full regression suite.

`KR_SEMANTIC_OWNERSHIP_REPLAY = PASS`
