# Phase 9.1B Derived Relations Audit

| Relation family | Eligible | Blocked | N/A |
|---|---:|---:|---:|
| trade_ar_vs_revenue | 6 | 13 | 1 |
| broad_ar_vs_revenue | 8 | 11 | 1 |
| inventory_vs_revenue | 11 | 8 | 1 |
| inventory_vs_cogs | 11 | 8 | 1 |
| trade_ap_vs_cogs | 8 | 11 | 1 |
| broad_ap_vs_cogs | 9 | 10 | 1 |

Each relation is `YOY_GROWTH_COMPARISON` with `GREATER`, `LOWER`, or `EQUAL` direction and exact percentage-point gap. The six explicit families keep trade/broad AR and AP distinct. They are factual relations only: no collection-quality, demand, liquidity, causality, thesis, warning, DSO, DPO, Inventory Days, CCC, or ROIC verdict is generated.
