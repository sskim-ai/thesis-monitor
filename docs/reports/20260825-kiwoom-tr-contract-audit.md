# Kiwoom TR Contract Audit

## Result

`KIWOOM_TR_CONTRACT = PASS`

Implementation SHA: `32178dc5b2cd4a5fd38af51514b4ac5d12d1cbd0`

Official source: Kiwoom REST API documentation and official example repository. No paid provider
or new subscription was used.

| TR | Endpoint | Request contract | Accepted output |
| --- | --- | --- | --- |
| ka20001 | /api/dostk/sect | mrkt_tp 0/1, inds_cd 001/101 | index and breadth |
| ka20003 | /api/dostk/sect | inds_cd 001/101 | composite, size, sector |
| ka20009 | /api/dostk/sect | mrkt_tp and inds_cd | target-date session proof |
| ka10051 | /api/dostk/sect | amt_qty_tp=0, base_dt, stex_tp=3 | market amount |
| ka10066 | /api/dostk/mrkcond | amt_qty_tp=1, trde_tp=0, stex_tp=3 | stock amount pages |

`ka10051` aggregate ownership is foreign/institution/retail market-wide flow. `ka10066` owns the
complete stock decomposition. Generic investing, account, and order endpoints are outside the
allowlist. Missing fields fail closed. Tokens, app keys, secret keys, and auth headers are absent
from all artifacts.
