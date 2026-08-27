
# 2026-08-27 KR Afternoon KRX Cross-Provider Audit

Exact-slot observation: `2026-08-27T16:05:00+09:00`; target/latest completed session: `2026-08-27`.

| Endpoint | HTTP | Rows | State |
|---|---|---|---|
| sto/stk_bydd_trd | 200 | 0 | EMPTY |
| sto/ksq_bydd_trd | 200 | 0 | EMPTY |
| idx/kospi_dd_trd | 200 | 0 | EMPTY |
| idx/kosdaq_dd_trd | 200 | 0 | EMPTY |

All official public endpoints returned HTTP 200 with zero rows. The canonical state is `MARKET_COMPLETED_PROVIDER_PENDING` and `current_snapshot_promotable=false`; no older KRX payload was injected or used to overwrite Kiwoom.

`KRX_CROSS_PROVIDER = PUBLICATION_PENDING`
`STALE_KRX_INJECTION = 0`
