# 2026-08-26 US Market Digest Evidence Utilization

| Evidence | Before | After |
|---|---|---|
| SPY/QQQ/SOXX | used | used unchanged |
| RSP level 221.77 | dropped | structured context retained; prose suppressed |
| XLE -1.6638% / XLF +0.1546% | dropped | selected as sector dispersion |
| Other first-observation sector levels | dropped | retained as level-only; prose suppressed |
| XLC | provider error | `SOURCE_UNAVAILABLE` |
| Nasdaq official breadth | publication pending | publication pending, no synthetic values |
| DGS10/DFII10/VIX 8/24 | temporal metadata present | date-labeled if selected |
| WTI 8/18 | lagging | suppressed |

The digest no longer says “no other large change” while a canonical -1.7% versus +0.2% sector split is available. It also does not use the split as exchange breadth or as proof of a broad market regime.

```text
US_MARKET_DIGEST_MATERIAL_INFORMATION_LOSS = 0
BROAD_RISK_ON_WITHOUT_BREADTH_SUPPORT = 0
US_MARKET_DIGEST_BREADTH_BOUNDARY = PASS
```
