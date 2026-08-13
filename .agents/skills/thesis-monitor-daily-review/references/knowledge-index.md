# Investment Knowledge Routing Index

Read the full source at [investment-thesis-analysis-monitoring-knowledge.md](investment-thesis-analysis-monitoring-knowledge.md) selectively. The packet's `knowledge_routing` is the runtime reading plan; do not substitute general model knowledge for a routed section.

## Always Read

- Sections 0-3: document purpose, data hierarchy, Fact / Interpretation / Unknowns, and source hierarchy.
- Section 8: market expectations and surprise.
- Sections 13-16: thesis state, risk and kill conditions, multiple expansion/compression, and macro transmission.
- Sections 20-22: provisional earnings, valuation comparability, and ADR/share-basis safety.
- Sections 25-26: the initial-analysis response structure and final operating philosophy.

Stable framework names: `fact_interpretation_unknown`, `initial_thesis`, `market_expectations`, `risk_kill_condition`, `multiple_expansion_compression`, `macro_transmission`, `valuation_basis_comparability`, `monitoring_data_quality`.

`monitoring_data_quality` is completed by `daily-review-policy.md`; provider freshness, schedules, and packet lifecycle are runtime policy rather than additions to the canonical investment Knowledge.

## Event Routing

- Earnings or guidance: Sections 5, 7, and 20. Use `financial_calculation_safety`, `earnings_quality`, and `provisional_earnings`.
- Material price or positioning: Sections 9-12. Use `price_ohlcv` and `holder_new_buyer`.
- Material macro transmission: Sections 16-19. Use `macro_transmission`.

## Industry Routing

- All existing industry framework names route to Section 6. Keep the packet's current industry routing unchanged in this phase.
- Memory `memory_valuation`: use mid-cycle earnings, PBR, FCF, inventory, ASP, supply discipline, and capex. A low peak-cycle PER is not sufficient.
- Insurance or reinsurance `insurance_reinsurance_valuation`: do not use SaaS NRR or Rule of 40.
- EPC or construction `epc_construction_valuation`: contract margin, collections, and contract assets remain Unknown unless packet facts support them.
- SaaS or recurring revenue `saas_recurring_revenue_valuation`: do not claim ARR or NRR changes when absent.
- Biotech and other pre-profit frameworks: do not force PER onto a pre-profit company.

## Basis-Safety Routing

- Preliminary earnings: Section 20 `provisional_earnings`; do not infer balance sheet, FCF, inventory, or ROIC changes.
- ADR or share-basis uncertainty: Sections 5, 21, and 22 `adr_share_basis`; never infer a conversion ratio or recompute PER.
- Historical comparability withheld: Section 21 only; current multiples may remain usable, historical percentile and range may not.
