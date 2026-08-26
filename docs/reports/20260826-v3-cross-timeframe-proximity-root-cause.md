# Price Structure v3 Cross-Timeframe Proximity Root Cause

- Instruction commit: `7267ca1d3e518d39986941bfda1d6447560db344`
- Implementation: `176f3e73eb097fac99f4038a8987b610954804cc`
- Immutable replay: `20` subjects; live calls `0`.

Root causes: `DISTANCE_NOT_IN_RANK`, `STRUCTURAL_SCORE_DOMINATES_DISTANCE`, `CROSS_TF_SOURCE_COUNT_DOMINANCE`. The old renderer ranked distance only after structurally ranked map truncation and had no active-relevance gate.

| Ticker | Before cross | After nearest support | Result |
| --- | --- | --- | --- |
| 010120 | 약 5.4만~5.6만원 / None / None / 72.590337% | 약 19.9만~20.1만원 / daily / NEAR / 0.544059% | PASS |
| MU | 약 $87~$89.04 / None / None / 90.461171% | 약 $900.13~$914.52 / daily / NEAR / 2.027628% | PASS |
| TSM | 약 $185.04~$189.28 / None / None / 54.788274% | 약 $414.07~$416.16 / weekly / NEAR / 0.596971% | PASS |
| SNDK | 약 $995.69~$1,000.69 / None / None / 32.695354% | 약 $1,407.87~$1,420.1 / daily / NEAR / 4.486483% | PASS |
