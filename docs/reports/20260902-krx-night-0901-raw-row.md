# KRX Night 2026-09-01 Raw-Row Proof

Official `fut_bydd_trd?basDd=20260901` returned HTTP 200, 385 rows, 120255 bytes, and raw SHA `485fe0dea1649c735c709fcad2cd87df5f4ee76d34a46a3545f0eaad9eb40881`. The supplemental extraction returned the identical SHA, proving response stability.

| Product | Session | ISU_CD | ISU_NM | O | H | L | C | Change | Volume | OI |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| KOSPI200 | NIGHT | `A0169000` | 코스피200 F 202609 (야간) | 1067.00 | 1072.45 | 1053.80 | 1064.50 | -3.35 | 22349 | 156205 |
| KOSPI200 | DAY control | `A0169000` | 코스피200 F 202609 (주간) | 1068.65 | 1080.25 | 1056.95 | 1078.15 | 10.30 | 101957 | 155736 |
| KOSDAQ150 | NIGHT | `A0669000` | 코스닥150 F 202609 (야간) | 1440.00 | 1447.00 | 1415.50 | 1432.80 | -7.30 | 1885 | 421415 |
| KOSDAQ150 | DAY control | `A0669000` | 코스닥150 F 202609 (주간) | 1439.50 | 1445.30 | 1396.80 | 1402.50 | -37.60 | 167402 | 431072 |

The NIGHT normalized fingerprints are `c15e7e951bbcff286edb717acdf5a72132989c3aa70fec6ba949bf2b6811b5bc` (KOSPI200) and `02de2670aec86c6dc1f3eef97ca29a9e7297bc9902c441c4af75daa97ce80567` (KOSDAQ150). DAY rows are controls only.

`KRX_0901_NIGHT_ROW_FOUND = PASS`

`CROSS_CONTRACT_COMPARISON = 0`

`DAY_ROW_COMPARED_AS_NIGHT = 0`
