
# 2026-08-27 KR Afternoon ka20003 Size And Sector Audit

## Size And Style

| Scope | Index | Return | Advance / decline / unchanged | Listed | Metric role |
|---|---|---|---|---|---|
| KOSPI | 대형주 | +1.66% | 58 / 39 / 3 | 100 | actual_sector_breadth |
| KOSPI | 중형주 | +0.22% | 63 / 127 / 5 | 198 | actual_sector_breadth |
| KOSPI | 소형주 | -0.13% | 149 / 318 / 31 | 529 | actual_sector_breadth |
| KOSDAQ | KOSDAQ 100 | +1.94% | 67 / 30 / 3 | 100 | actual_sector_breadth |
| KOSDAQ | KOSDAQ MID 300 | +0.76% | 149 / 136 / 8 | 299 | actual_sector_breadth |
| KOSDAQ | KOSDAQ SMALL | +0.44% | 588 / 587 / 81 | 1341 | actual_sector_breadth |

## Safe Sector Extremes

| Scope | Role | Sector | Return | Advance / decline / unchanged | Source |
|---|---|---|---|---|---|
| KOSPI | leader | 전기/전자 | +2.62% | 54 / 26 / 1 | kiwoom:ka20003:KOSPI:013:2026-08-27 |
| KOSPI | laggard | 유통 | -2.36% | 15 / 41 / 6 | kiwoom:ka20003:KOSPI:016:2026-08-27 |
| KOSDAQ | leader | 금융 | +3.21% | 49 / 33 / 19 | kiwoom:ka20003:KOSDAQ:111:2026-08-27 |
| KOSDAQ | laggard | 오락/문화 | -1.29% | 20 / 31 / 2 | kiwoom:ka20003:KOSDAQ:141:2026-08-27 |

The rows retain both sector-index return and component counts under `actual_sector_breadth`; neither is substituted for the other. The natural AI digest omitted size and sector detail to stay concise, while the deterministic fallback retained the bounded KOSPI/KOSDAQ leaders and laggards.

`KIWOOM_KA20003 = PASS`
`KR_SIZE_STYLE_CONTEXT = PASS`
`SECTOR_RETURN_AS_SECTOR_BREADTH = 0`
