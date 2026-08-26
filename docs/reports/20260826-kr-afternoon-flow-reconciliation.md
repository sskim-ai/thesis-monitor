# 2026-08-26 KR Afternoon Flow Reconciliation

`ka10051` aggregate amounts and full-pagination `ka10066` sums did not share a reconciled basis. The existing classifier returned `UNRESOLVED_BASIS_OR_TAXONOMY` for all six actor/market pairs; no tolerance was changed.

| Market | Actor | ka10051 | ka10066 sum | Difference | Abs difference / aggregate |
|---|---|---:|---:|---:|---:|
| KOSPI | Foreign | +111.500bn | -4,000.274bn | +4,111.774bn | 3,687.69% |
| KOSPI | Institution | +818.100bn | +1,255.845bn | -437.745bn | 53.51% |
| KOSPI | Retail | -2,503.000bn | +1,155.005bn | -3,658.005bn | 146.14% |
| KOSDAQ | Foreign | -129.600bn | +136.098bn | -265.698bn | 205.01% |
| KOSDAQ | Institution | -108.700bn | +21.158bn | -129.858bn | 119.46% |
| KOSDAQ | Retail | +233.300bn | -147.223bn | +380.523bn | 163.10% |

Because the basis/taxonomy remains unresolved, `ka10051` stays the aggregate-flow owner and `ka10066` is not promoted to concentration prose.
