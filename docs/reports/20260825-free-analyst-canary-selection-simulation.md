# Free Analyst Canary Selection Simulation

- Instruction commit: `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7`
- Implementation base: `f7d2552185ff2ff6d932337e7555ce02f87fa613`
- US packet: `2026-08-25-us-run-37-7e04812311c2`
- KR packet: `2026-08-24-kr-run-36-e4ac1c029c06`
- Provider recollection: `0`
- Manual Telegram / Task / DB mutation: `0 / 0 / 0`

- Maximum: `market <= 1`, `stock <= 2`, `total <= 3`
- Simulated selected: `3`
- Selected keys: `('market:2026-08-25-us-run-37-7e04812311c2', 'stock:CORZ', 'stock:CRCL')`
- Scoped runtime quality: `PASSED`
- Delivery: `0` (simulation only)

| Message | Eligible | Renderer | Selected | Final simulated mode |
| --- | --- | --- | --- | --- |
| __DAILY_DIGEST__ | True | CONCISE_HYBRID | True | free_analyst_adaptive_canary |
| CORZ | True | CONCISE_HYBRID | True | free_analyst_adaptive_canary |
| CRCL | True | CONCISE_HYBRID | True | free_analyst_adaptive_canary |
| GOOGL | True | CONCISE_HYBRID | False | current production output/fallback |
| HUT | True | CONCISE_HYBRID | False | current production output/fallback |
| IBM | True | CONCISE_HYBRID | False | current production output/fallback |
| MU | True | CONCISE_HYBRID | False | current production output/fallback |
| RXRX | True | CONCISE_HYBRID | False | current production output/fallback |
| SKHY | True | CONCISE_HYBRID | False | current production output/fallback |
| SNDK | True | CONCISE_HYBRID | False | current production output/fallback |
| TSLA | True | CONCISE_HYBRID | False | current production output/fallback |
| TSM | True | CONCISE_HYBRID | False | current production output/fallback |
| WRD | True | CONCISE_HYBRID | False | current production output/fallback |
| WULF | True | CONCISE_HYBRID | False | current production output/fallback |
