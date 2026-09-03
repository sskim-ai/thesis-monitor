# Shadow vs Reference: Price Zones

| Ticker | Codex entry | Reference entry | Entry class | Codex trim | Reference trim | Trim class |
| --- | --- | --- | --- | --- | --- | --- |
| CORZ | 12.91-13.46 | 17.45-18.38 | DIFFERENT_BASIS | 17.45-18.38 | 17.45-18.38 | SAME_ZONE |
| CPNG | 14.73-15.22 | 15.45-15.7 | DIFFERENT_BUT_SAME_BASIS | 16.51-17.16 | 16.51-17.16 | SAME_ZONE |
| CRCL | 82.01-86.53 | 82-86.5 | SAME_ZONE | withheld | withheld | SAME_ZONE |
| GOOGL | 312.37-321.88 | 312-322 or 354 | SAME_ZONE | 343.65-353.79 | 344-354 | SAME_ZONE |
| HUT | 97 | withheld | ONE_SIDE_WITHHELD | 84.11-89.67 | 84-90 | SAME_ZONE |
| IBM | 250 | 228-235 | DIFFERENT_BASIS | 237.1-250.26 | 237-250 | SAME_ZONE |
| MU | 867.52-911.75 | 868-912 or 950 | SAME_ZONE | 1,231.15-1,278.85 | 1,231-1,279 | SAME_ZONE |
| RXRX | withheld | 3.37-3.47 | ONE_SIDE_WITHHELD | 3.58-3.68 | 3.58-3.68 | SAME_ZONE |
| SKHY | 163 | 147-151 | DIFFERENT_BASIS | 174.86-182 | 175-182 | SAME_ZONE |
| SNDK | 1,100-1,125 | 1,100-1,125 or 923-1,073 | SAME_ZONE | 2,316.11-2,392.67 | 2,316-2,393 | SAME_ZONE |
| TSLA | withheld | 335-341 | ONE_SIDE_WITHHELD | 358.96-382.68 | 359-383 | SAME_ZONE |
| TSM | 432 | 407-414 | DIFFERENT_BASIS | 432.3-439.78 | 432-440 | SAME_ZONE |
| WRD | 6.68 | 5.9-6.15 | DIFFERENT_BUT_SAME_BASIS | 5.91-6.15 | 5.91-6.15 | SAME_ZONE |
| WULF | 18.4 | 16.2-16.8 | DIFFERENT_BUT_SAME_BASIS | 15.55-16.46 | 15.55-16.46 | SAME_ZONE |

## Summary

- Entry same/overlap: `4/14`
- Trim same/overlap: `14/14` (includes `CRCL` where both sides appropriately withheld a numeric trim zone)
- Independently supported Codex numeric entries: `12`
- Independently supported Codex numeric trim zones: `13`
- Unsupported Codex entry or trim zones: `0`

The relatively low entry agreement is a selector-policy question: Codex often preferred a stricter breakout confirmation where the reference preferred a support/recovery area. It is not evidence of fabricated levels because every rendered Codex number is tied to the frozen price map.
