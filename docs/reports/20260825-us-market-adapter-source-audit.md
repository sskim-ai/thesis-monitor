# US Market Adapter Source Audit

## Priority

The adapter reuses repository-supported validated market observations and official Fed, Treasury,
BLS, BEA, SEC, issuer, exchange, and regulator sources. It adds no paid provider or live query.

## Immutable Evidence

- Packet: `2026-08-25-us-run-37-7e04812311c2`
- Packet SHA-256: `17e14c4c7fd04017574f60057176c8e0560b0351ec9f3c865ba5dd543ae7e6cc`
- Index/style Facts: SPY, QQQ, IWM
- Sector proxy: SOXX
- Verified relative-return Facts: `2`
- Breadth: unavailable
- Market-wide participant flow: unsupported/unavailable
- Provider recollection/live calls: `0`

SOXX remains a sector price proxy, not sector breadth. Existing rates, FX, oil, volatility, and
credit Facts remain under the macro temporal contract and are not duplicated by the adapter.

Result: `US_MARKET_ADAPTER = PARTIAL`.

