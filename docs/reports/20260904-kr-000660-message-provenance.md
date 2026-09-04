# 2026-09-04 KR 000660 Message Provenance

| Delivered claim | Canonical owner / fact | Source field / binding | Result |
|---|---|---|---|
| HBM4 / AI server demand | `thesis.core_thesis` | stored thesis v6; no new exact number | PASS |
| Inventory vs COGS | `working-capital-relation:38a9a0707d38e538ccdb2e7e` | gap `-2.06191700664683180124383042` p.p.; display `2.1%p`; `exact_total_inventory` | PASS |
| ASP / product-mix caveat | `industry_reasoning_plan` + thesis drivers | semiconductor causal boundary | PASS |
| Regular-session close | `price:current.fields.current_price` and `price-basis:000660:2026-09-04` | 1,647,000 KRW; structure basis completed regular-session close | PASS |
| Near support | `v3-zone:635b2679e802f1af740b` | `1607684.687500`-`1644565.312500` KRW; daily `BALANCE_BOX` + `BOLLINGER_DAILY`; COMPLETE | PASS |
| Monthly provisional resistance | `v3-zone:dc9e4f02d51702baafda` | `2360186.744814`-`2372017.254814` KRW; monthly partial bar; authoritative=false | PASS |
| Foreign/institution 1d/5d/20d | `positioning:2026-09-04` | actor-specific registered share-quantity fields | PASS |

## Supply Values

| Actor | 1d | 5d | 20d | Unit / as-of |
|---|---:|---:|---:|---|
| Foreign | +318,180 | -682,505 | -2,435,345 | shares / 2026-09-04 |
| Institution | +96,776 | -842,694 | -1,897,952 | shares / 2026-09-04 |

The renderer preserved the exact actor/horizon labels. The monthly zone explicitly carried `PARTIAL`, observation timestamp, expected close 2026-09-30, and “봉 마감 전 변동 가능” wording.

## Accounting / Valuation Safety

- `KR_ACCOUNTING_SAFETY=PASS`
- `KR_ACCOUNTING_VALUATION_SAFETY=PASS`
- The 2026-06-30 profitability tuple was tainted by `net_income_exceeds_revenue`, `preliminary_profitability_outlier`, and `unusually_high_or_low_operating_margin`.
- Revenue, operating income/margin, TTM EPS/PER, and modeled forward earnings fields were denied for prose.
- BVPS/PBR remained separately verified and comparable, but the final adaptive 000660 message omitted valuation rather than leaking denied earnings values.
