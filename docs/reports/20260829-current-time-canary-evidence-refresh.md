# Current-Time Canary Evidence Refresh

- Execution time (KST): `2026-08-29T21:16:59.579875+09:00`
- Mode: read-only current-time E2E test

## Provider Calls

| Provider | Requests | Success | Failure |
|---|---:|---:|---:|
| Local OHLCV | 4 | 4 | 0 |
| SEC | 0 | 0 | 0 |
| OpenDART | 0 | 0 | 0 |
| Paid provider | 0 | 0 | 0 |

## Evidence Packets

| Ticker | Market | Cutoff | Evidence SHA-256 | Feature SHA-256 | Reasoning grade |
|---|---|---|---|---|---|
| 003690 | kr | 2026-08-28 | `510a7b157d4247a9c611e38dfd96dd34851434323907b1bc10955299d8c92b6b` | `c423a7485b470e08b33226ee79a2838f8056654a9c9deceaabd7ed0558bd5783` | VERY_HIGH |
| 000660 | kr | 2026-08-28 | `899971b974ad32c206398254e726d48c7c92079bd6ce96af5274d95ce7e9fb41` | `59c34e2db56c2c06a5a9425f99bdc9c065b81e1e130a3110c644e03dc60fd86c` | VERY_HIGH |
| GOOGL | us | 2026-08-29 | `ca42efbaae98cd548a4e1b82e5bfb141b4c768eb78ca7342539900eae6b98b66` | `1b9c828736ef4482805989e309f30d70a890ced1270417a6eaee23703ec8a859` | VERY_HIGH |
| RXRX | us | 2026-08-29 | `841dc9cd32476470ede419acd6600f68f83b88c0f559144539ede0d6680307d5` | `b219a1bbbd7c36b43edfa3ff903f1386f33424e3413fd630ad53d711fa40d1d7` | VERY_HIGH |

The canonical database was queried directly with zero mutation: all four subject audits passed. High-level snapshot telemetry writes were intentionally blocked by the query-only guard and did not invalidate the fresh evidence packets.
