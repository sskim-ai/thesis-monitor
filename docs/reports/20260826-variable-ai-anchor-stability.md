# Variable AI Anchor Stability

| Timeframe | Stable | Minor | Material |
|---|---|---|---|
| monthly | 17 | 0 | 3 |
| weekly | 9 | 0 | 11 |
| daily | 9 | 1 | 10 |

- Eligible stocks: `8`.
- Ineligible stocks: `12`.
- Timeframe Fibonacci fallbacks: `24`.
- Runtime failures: `0`.
- Semantically rejected timeframes: `4`.
- Benchmark runs per packet: `5`; wider universe runs per packet: `3`.

- Monthly material: `IBM, MU, RXRX`.
- Weekly material: `000660, 003690, 005490, 005930, GOOGL, IBM, RXRX, SNDK, TSLA, WRD, WULF`.
- Daily material: `003690, 005490, 010120, 086280, GOOGL, IBM, RXRX, SNDK, TSM, WULF`.
- Daily minor variation: `012450`.

Monthly/weekly material variation blocks the first enablement pool. Daily-only material variation
retains deterministic daily SR and omits only daily Fibonacci.
