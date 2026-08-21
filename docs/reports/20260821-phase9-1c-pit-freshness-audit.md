# Phase 9.1C PIT / Freshness Audit

- Active universe: `20`
- Current formal: `7`
- Formal lagging provisional: `1`
- Stale context only: `0`
- Blocked: `11`
- N/A: `1`
- Future facts consumed: `0`
- PIT/freshness violations: `0`

Every selected relation requires all six canonical input Facts to satisfy `source_available_at <= packet cutoff`. A newer formal period blocks older substitution. A newer provisional period makes the formal balance context-only and suppresses current-quarter wording.

| Ticker | Industry | Freshness | Usage | Relation | Human quality |
|---|---|---|---|---|---|
| 000660 | memory_semiconductor | CURRENT_FORMAL | INVENTORY_RELATION | inventory_vs_cogs | MATERIAL_IMPROVEMENT |
| 003690 | insurance_reinsurance | NOT_APPLICABLE | NOT_APPLICABLE | - | NO_MEANINGFUL_CHANGE |
| 005490 | steel_materials | CURRENT_FORMAL | INVENTORY_RELATION | inventory_vs_revenue | MATERIAL_IMPROVEMENT |
| 005930 | memory_semiconductor | CURRENT_FORMAL | INVENTORY_RELATION | inventory_vs_cogs | MATERIAL_IMPROVEMENT |
| 010120 | industrial_epc | CURRENT_FORMAL | TRADE_AR_RELATION | trade_ar_vs_revenue | MATERIAL_IMPROVEMENT |
| 012450 | aerospace_epc | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| 086280 | transport_logistics | CURRENT_FORMAL | TRADE_AR_RELATION | trade_ar_vs_revenue | MATERIAL_IMPROVEMENT |
| CORZ | hpc_data_center | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| CRCL | special_financial_like | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| GOOGL | cloud_platform_software | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| HUT | hpc_data_center | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| IBM | cloud_platform_software | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| MU | memory_semiconductor | CURRENT_FORMAL | INVENTORY_RELATION | inventory_vs_cogs | MATERIAL_IMPROVEMENT |
| RXRX | biotech | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| SKHY | memory_semiconductor | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| SNDK | memory_semiconductor | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| TSLA | automotive | CURRENT_FORMAL | INVENTORY_RELATION | inventory_vs_revenue | MATERIAL_IMPROVEMENT |
| TSM | memory_semiconductor | FORMAL_LAGGING_PROVISIONAL | CONTEXT_ONLY | inventory_vs_cogs | NO_MEANINGFUL_CHANGE |
| WRD | general_non_financial | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
| WULF | hpc_data_center | BLOCKED | SUPPRESSED | - | NO_MEANINGFUL_CHANGE |
