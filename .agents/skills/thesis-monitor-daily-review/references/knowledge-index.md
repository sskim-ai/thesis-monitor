# Investment Knowledge Routing Index

Read the full source at [investment-thesis-analysis-monitoring-knowledge.md](investment-thesis-analysis-monitoring-knowledge.md) selectively. The packet's `knowledge_routing` is the runtime reading plan; do not substitute general model knowledge for a routed section.

## Always Read

- Sections 1-3: system lifecycle, Fact / Interpretation / Unknown, source hierarchy, and initial thesis framework.
- Section 6: market expectations and surprise.
- Sections 10-12: risk and kill conditions, multiple expansion/compression, and macro transmission.
- Sections 13-16: provisional earnings, valuation comparability, optional scoring, and monitoring data quality.
- Section 18: the initial-analysis response structure.

Stable framework names: `fact_interpretation_unknown`, `initial_thesis`, `market_expectations`, `risk_kill_condition`, `multiple_expansion_compression`, `macro_transmission`, `valuation_basis_comparability`, `monitoring_data_quality`.

`monitoring_data_quality` is completed by `daily-review-policy.md`; provider freshness, schedules, and packet lifecycle are runtime policy rather than additions to the canonical investment Knowledge.

## Event Routing

- Earnings or guidance: Sections 4, 5, and 13. Use `financial_calculation_safety`, `earnings_quality`, and `provisional_earnings`.
- Material price or positioning: Sections 8-9. Use `price_ohlcv` and `holder_new_buyer`.
- Material macro transmission: Section 12. Use `macro_transmission`.
- FOMC evidence: Section 12.3. Use `fomc_interpretation`; missing Decision, Statement, Dot Plot, SEP, Press Conference, or Market Reaction components stay Unknown.
- Hyperscaler CAPEX evidence: Section 12.4. Use `hyperscaler_capex_transmission`; a budget announcement is not a supplier order.

## Industry Routing

- All existing industry framework names route to Section 7. Keep the packet's current industry routing unchanged in this phase.
- Memory `memory_valuation`: use mid-cycle earnings, PBR, FCF, inventory, ASP, supply discipline, and capex. A low peak-cycle PER is not sufficient.
- Insurance or reinsurance `insurance_reinsurance_valuation`: do not use SaaS NRR or Rule of 40.
- EPC or construction `epc_construction_valuation`: contract margin, collections, and contract assets remain Unknown unless packet facts support them.
- SaaS or recurring revenue `saas_recurring_revenue_valuation`: do not claim ARR or NRR changes when absent.
- Biotech and other pre-profit frameworks: do not force PER onto a pre-profit company.

## Basis-Safety Routing

- Preliminary earnings: Section 13 `provisional_earnings`; do not infer balance sheet, FCF, inventory, or ROIC changes.
- ADR or share-basis uncertainty: Sections 4 and 14 `adr_share_basis`; never infer a conversion ratio or recompute PER.
- Historical comparability withheld: Section 14 only; current multiples may remain usable, historical percentile and range may not.
