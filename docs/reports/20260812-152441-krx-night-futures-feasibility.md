# KRX Night Futures Feasibility

## Source

- Official service: KRX Open API 선물 일별매매정보 (주식선물外)
- Endpoint identifier: `fut_bydd_trd`
- Authentication: `AUTH_KEY` request header only
- Source URL stored without credentials: `https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd`

## Probe Result

- Status: `ok`
- Queried dates: 2026-08-12, 2026-08-11
- Source date: `2026-08-11`
- Rows: 385
- Session values: 야간, 정규
- Field names: ACC_OPNINT_QTY, ACC_TRDVAL, ACC_TRDVOL, BAS_DD, CMPPREVDD_PRC, ISU_CD, ISU_NM, MKT_NM, PROD_NM, SETL_PRC, SPOT_PRC, TDD_CLSPRC, TDD_HGPRC, TDD_LWPRC, TDD_OPNPRC
- Night/day separation usable: `true`

## Contract Evidence

- KOSPI200: A0169000, 2026-09, regular 989.8, night 974.95, -14.85 (-1.5003%)
- KOSDAQ150: A0669000, 2026-09, regular 1485.3, night 1489, +3.7 (+0.2491%)

Only rows with explicit regular/night session metadata, the same contract code, and an
interpretable maturity were paired. Spot-index comparisons, cross-expiry comparisons,
row-order inference, and volume-based front-month inference were not used.

## Production Decision

**production enabled**

Reason: `verified explicit session and contract semantics`
