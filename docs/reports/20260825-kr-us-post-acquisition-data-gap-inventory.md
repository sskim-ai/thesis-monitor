# KR/US Post-Acquisition Data Gap Inventory

| Market | Field | Available | Source | Same day | Next morning | Production integrated | User-visible value | Limitation | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KR | KOSPI/KOSDAQ indices | capability yes, target pending | KRX | publication-dependent | yes candidate | yes fail-closed | none on 8/25 | repeated timing proof pending | P2 |
| KR | KOSPI/KOSDAQ breadth | capability yes, target pending | KRX stock rows | publication-dependent | yes candidate | yes fail-closed | none on 8/25 | official row publication | P2 |
| KR | market-wide participant flow | no | none verified | no | no | Unknown | none | source unsupported | P2 |
| KR | sector/size structure | partial | index/price proxies only | partial | partial | schema ready | selective | no full taxonomy breadth | P2 |
| US | SPY/QQQ/IWM/SOXX | yes | OHLCV analyst | after close | yes | yes | existing | price proxies | closed |
| US | RSP equal-weight | yes | OHLCV analyst | after close | yes | yes | selective | not exchange breadth | closed |
| US | 11 sector proxies | yes | OHLCV analyst | after close | yes | yes | selective | not sector breadth | closed |
| US | exchange advance/decline | no | none configured | no | no | Unknown | none | provider absent | P2 |
| US | participant flow | no/not supported | none | no | no | explicit unavailable | none | no KR semantic mapping | P2 |

No field in this inventory defaults to zero. Optional P2 gaps do not block the safe structured
subset or Message Quality v2.
