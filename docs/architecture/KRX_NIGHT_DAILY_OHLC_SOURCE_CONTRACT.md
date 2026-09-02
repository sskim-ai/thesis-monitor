# KRX Night Daily OHLC Source Contract

Contract: `krx-night-daily-ohlc-v1`.

The only source is official KRX service `fut_bydd_trd` at `https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd`. A row is eligible only when `MKT_NM` resolves to NIGHT, the product resolves to KOSPI200 or KOSDAQ150 futures, `BAS_DD` equals the query date, contract code and parsed maturity exist, and all OHLC fields are finite, positive, and internally ordered.

| Canonical | KRX field |
| --- | --- |
| Date | `BAS_DD` |
| Contract | `ISU_CD` plus `ISU_NM` maturity |
| Session | `MKT_NM` |
| Open / High / Low / Close | `TDD_OPNPRC` / `TDD_HGPRC` / `TDD_LWPRC` / `TDD_CLSPRC` |
| Volume | `ACC_TRDVOL` |
| Official change | `CMPPREVDD_PRC` |

Missing or malformed OHLC is rejected; no synthetic repair or broad investing proxy exists.
