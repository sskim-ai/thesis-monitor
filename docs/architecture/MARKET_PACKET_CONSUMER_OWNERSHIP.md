# Market Packet Consumer Ownership

Contract: `packet-fact-consumer-scope-v1`.

## Standalone Market Surface

Market intelligence and FX facts remain in `market_context.fact_catalog`. Their standalone
copies are owned by `DAILY_REVIEW` and `MARKET_RENDERER`, not by `STOCK_V2`.

## Stock Transmission Surface

The market-intelligence selector continues to decide which market facts are relevant to each
stock. Only those selected copies are appended to the stock fact catalog, where they receive
`STOCK_V2` ownership. This preserves the existing transmission decision while preventing the
entire raw market catalog from becoming stock-decision input.

## Night-Futures Surface

Night-futures source rows, reference values, and any future timeframe facts remain canonical
and available to archival and dedicated night-futures processing. While the temporary session
convention gate is active, they have no `STOCK_V2`, `DAILY_REVIEW`, or `MARKET_RENDERER`
ownership and cannot be required by legacy market AI validation.

The collection, session fields, near-month selection, history, and D/W/M calculations are not
changed by this contract.

