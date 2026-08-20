# Phase 9.0C Freshness Audit

No day-count threshold is introduced. Freshness is period alignment against Phase 9.0A official formal evidence and newer validated preliminary periods.

| State | Count |
|---|---:|
| CURRENT_FORMAL | 10 |
| FORMAL_LAGGING_PROVISIONAL | 2 |
| STALE_FORMAL | 0 |
| FORMAL_ALIGNMENT_UNAVAILABLE | 0 |
| BLOCKED | 7 |
| NOT_APPLICABLE | 1 |

| Ticker | Industry | Canonical | Freshness | Usage | Rendered | Suppression |
|---|---|---|---|---|---|---|
| 000660 | memory_semiconductor | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 003690 | insurance_reinsurance | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NO | financial_industry_not_applicable |
| 005490 | steel_materials | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 005930 | memory_semiconductor | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 010120 | industrial_epc | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 012450 | aerospace_epc | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| 086280 | transport_logistics | PARTIAL | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| CORZ | hpc_data_center | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| CRCL | general_non_financial | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| GOOGL | cloud_platform_software | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| HUT | hpc_data_center | PARTIAL | CURRENT_FORMAL | OCF_ONLY_CONTEXT | YES | - |
| IBM | cloud_platform_software | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| MU | memory_semiconductor | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| RXRX | biotech | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| SKHY | memory_semiconductor | BLOCKED | BLOCKED | SUPPRESSED | NO | canonical_cash_flow_fact_unavailable |
| SNDK | memory_semiconductor | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| TSLA | automotive | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |
| TSM | memory_semiconductor | ELIGIBLE | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | NO | newer_provisional_period_not_cash_flow_aligned |
| WRD | general_non_financial | ELIGIBLE | FORMAL_LAGGING_PROVISIONAL | LATEST_FORMAL_CONTEXT_ONLY | NO | newer_provisional_period_not_cash_flow_aligned |
| WULF | hpc_data_center | ELIGIBLE | CURRENT_FORMAL | FULL_FCF_CONTEXT | YES | - |

TSM and WRD remain `LATEST_FORMAL_CONTEXT_ONLY` because a later preliminary period exists. They are not rendered as current. KR period-context cases and SKHY remain blocked; Korean Re remains not applicable.
