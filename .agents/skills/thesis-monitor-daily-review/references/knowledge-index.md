# Investment Knowledge Routing Index

Read the full source at [investment-thesis-analysis-monitoring-knowledge.md](investment-thesis-analysis-monitoring-knowledge.md) selectively. The packet's `knowledge_routing` is the runtime reading plan; do not substitute general model knowledge for a routed section.

## Always Read

- Sections 1-3: system purpose, Fact / Interpretation / Unknown, and initial thesis framework.
- Section 6: market expectations and surprise.
- Sections 10-12: risk and kill conditions, multiple expansion/compression, and macro transmission.
- Sections 14 and 16: valuation basis comparability and monitoring data quality.

Stable framework names: `fact_interpretation_unknown`, `initial_thesis`, `market_expectations`, `risk_kill_condition`, `multiple_expansion_compression`, `macro_transmission`, `valuation_basis_comparability`, `monitoring_data_quality`.

## Event Routing

- Earnings or guidance: Sections 4, 5, and 13. Use `financial_calculation_safety`, `earnings_quality`, and `provisional_earnings`.
- Material price or positioning: Sections 8 and 9. Use `price_ohlcv` and `holder_new_buyer`.
- Material macro transmission: Section 12. Use `macro_transmission`.

## Industry Routing

- Semiconductor: Section 7 `semiconductor_valuation`.
- Memory: Section 7 `memory_valuation`; use mid-cycle earnings, PBR, FCF, inventory, ASP, supply discipline, and capex. A low peak-cycle PER is not sufficient.
- Automotive: Section 7 `automotive_valuation`.
- Bank: Section 7 `bank_valuation`.
- Insurance or reinsurance: Section 7 `insurance_reinsurance_valuation`; do not use SaaS NRR or Rule of 40.
- Shipping or transport: Section 7 `shipping_transport_valuation`.
- Holding company: Section 7 `holding_company_valuation`.
- Consumer: Section 7 `consumer_valuation`.
- EPC or construction: Section 7 `epc_construction_valuation`; contract margin, collections, and contract assets remain Unknown unless packet facts support them.
- SaaS or recurring revenue: Section 7 `saas_recurring_revenue_valuation`; do not claim ARR or NRR changes when absent.
- Cloud or platform: Section 7 `cloud_platform_valuation`.
- Biotech: Section 7 `biotech_valuation`; do not force PER onto a pre-profit company.
- Robotaxi or other pre-profit model: Section 7 `pre_profit_valuation`.

## Basis-Safety Routing

- Preliminary earnings: Section 13 `provisional_earnings`; do not infer balance sheet, FCF, inventory, or ROIC changes.
- ADR or share-basis uncertainty: Sections 4 and 14 `adr_share_basis`; never infer a conversion ratio or recompute PER.
- Historical comparability withheld: Section 14 only; current multiples may remain usable, historical percentile and range may not.
