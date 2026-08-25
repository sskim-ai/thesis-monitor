# 2026-08-25 KRX 08:05 Natural Review

- Contract: `krx-publication-readiness-v1`
- Scheduled: `2026-08-25T08:05:00+09:00`
- Observed: `2026-08-24T23:05:03.282941Z`
- Role target: `NEXT_MORNING_0805`
- Target XKRX date: `2026-08-24`
- Readiness: `PROVIDER_COMPLETE`
- Promotable: `True`

| Endpoint | HTTP | Provider date | Rows | Status | SHA-256 |
|---|---:|---|---:|---|---|
| sto/stk_bydd_trd | 200 | 2026-08-24 | 942 | READY | 2879eb8373d6ff3f7c542a5ba8b92087b6739fe6a00ef0896ad8e4c789a7b932 |
| sto/ksq_bydd_trd | 200 | 2026-08-24 | 1823 | READY | 8c19faf4357fd8383afa166c5690f44d6040550538ce9f39bed8e0a24e4a37bc |
| idx/kospi_dd_trd | 200 | 2026-08-24 | 51 | READY | 30ad0e0ede0aba12a38d1832bdc2ece5fe9d2bb3194b25deeacdef045fa45094 |
| idx/kosdaq_dd_trd | 200 | 2026-08-24 | 40 | READY | 5bc3a822cda21d9b9065a3869cab9931089a2f3d0dd8fa2b8a9a9ce3ad2c9d65 |

- Eligible rows: `942 KOSPI stocks + 1,823 KOSDAQ stocks + 51 KOSPI indexes + 40 KOSDAQ indexes`
- Duplicate observations for the role target: `0`

`KRX_0805_ROLE_TARGET_NATURAL = LIVE_PASS`

`KRX_0805_PUBLICATION_READINESS = PROVIDER_COMPLETE`
