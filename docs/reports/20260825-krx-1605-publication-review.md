# 2026-08-25 KRX 16:05 Publication Review

| Item | Value |
| --- | --- |
| Observation ID | Not supplied; identity tuple `2026-08-25T16:05+09:00 / SAME_DAY_CLOSE_1605 / 2026-08-25` |
| Scheduled / actual | `2026-08-25 16:05:00 KST` / `2026-08-25 16:05:04.773041 KST` |
| Role target | `SAME_DAY_CLOSE_1605` |
| Target XKRX session | `2026-08-25` |
| Readiness | `MARKET_COMPLETED_PROVIDER_PENDING` |
| Promotable | `false` |
| Reason | `all_core_endpoints_returned_empty_200` |
| Natural terminal state | `RECORDED` |

| Endpoint | HTTP | State | Rows | Provider dates | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- |
| sto/stk_bydd_trd | 200 | EMPTY | 0 | none | 82c0031bc13af348ac1e1304aca28f309632975110f2508534e93216791dfa90 |
| sto/ksq_bydd_trd | 200 | EMPTY | 0 | none | 82c0031bc13af348ac1e1304aca28f309632975110f2508534e93216791dfa90 |
| idx/kospi_dd_trd | 200 | EMPTY | 0 | none | 82c0031bc13af348ac1e1304aca28f309632975110f2508534e93216791dfa90 |
| idx/kosdaq_dd_trd | 200 | EMPTY | 0 | none | 82c0031bc13af348ac1e1304aca28f309632975110f2508534e93216791dfa90 |

The role target is correct even though the provider had not published rows. No manual refetch was
performed.

```text
KRX_1605_ROLE_TARGET_NATURAL = LIVE_PASS
KRX_1605_PUBLICATION_READINESS = MARKET_COMPLETED_PROVIDER_PENDING
```
