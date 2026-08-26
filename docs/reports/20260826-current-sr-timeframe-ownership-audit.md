# Current SR Timeframe Ownership Audit

## Finding

`CURRENT_SR_ARCHITECTURE = MULTI_TIMEFRAME_COLLAPSED`.

`ohlcv-structure-v2` extracts local pivots and zones separately for daily, weekly, and monthly, then
`score_price_zones` combines them and `select_nearest_meaningful_zones` chooses one support and one
resistance across the combined classified pool. The compact AI packet keeps those collapsed nearest
zones. The original timeframe label survives, but the analytical hierarchy is not rendered.

The v2 shadow layer selects inside each timeframe first and preserves monthly structural, weekly
intermediate, and daily tactical ownership through synthesis.

## Replay

- Active universe: `20` (`KR 7`, `US 13`).
- Shadow validation: `20/20` PASS.
- Timeframe availability: monthly `17`, weekly `19`, daily `19`.
- Fibonacci calculation availability: monthly `16`, weekly `19`, daily `19`.
- Subjects with strict cross-timeframe confluence: `10`.
- Compact/full parity: `20/20`.
- Historical look-ahead leaks: `0`.


| Ticker | Market | M/W/D | Selected Fib | Confluence | Compact | Stability | Value |
|---|---|---:|---:|---:|---|---|---|
| 000660 | KR | Y/Y/Y | 4 | 2 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| 003690 | KR | Y/Y/Y | 1 | 0 | PASS | STABLE | MINOR_IMPROVEMENT |
| 005490 | KR | Y/Y/Y | 3 | 3 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| 005930 | KR | Y/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| 010120 | KR | Y/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| 012450 | KR | Y/Y/Y | 1 | 0 | PASS | STABLE | MINOR_IMPROVEMENT |
| 086280 | KR | Y/Y/Y | 1 | 2 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| CORZ | US | Y/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| CRCL | US | N/Y/Y | 2 | 1 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| GOOGL | US | Y/Y/Y | 5 | 2 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| HUT | US | Y/Y/Y | 1 | 1 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| IBM | US | Y/Y/Y | 4 | 2 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| MU | US | Y/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| RXRX | US | Y/Y/Y | 3 | 1 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| SKHY | US | N/N/N | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| SNDK | US | Y/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| TSLA | US | Y/Y/Y | 2 | 1 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| TSM | US | Y/Y/Y | 4 | 2 | PASS | STABLE | MATERIAL_IMPROVEMENT |
| WRD | US | N/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
| WULF | US | Y/Y/Y | 0 | 0 | PASS | STABLE | NO_ADDED_VALUE |
