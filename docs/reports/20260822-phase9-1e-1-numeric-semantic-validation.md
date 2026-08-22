# Phase 9.1E.1 Numeric And Semantic Validation

## Numeric Binding

- Semantic type: `inventory_growth_gap_pct_point`
- Unit: `pct_point`
- Automatic: `3`
- Manual: `0`
- Rejected: `0`
- Unresolved: `0`

Each displayed `%p` is bound to the selected canonical relation. Input Inventory and revenue/COGS
Fact IDs are retained for lineage, but the renderer does not recalculate or display raw balances.
Signs remain in the canonical relation; prose renders the absolute value with the typed direction.

## Semantic Safety

- Total Inventory scope only: PASS
- Current-formal and PIT-safe balance date: PASS
- `business_earnings` numeric ownership: PASS
- Exact number cross-section duplicates: `0`
- Unsupported causal claims: `0`
- Broad AR/Trade AR semantic leakage: `0`
- DSO/Inventory Days/DPO/CCC claims: `0`
- Thesis/warning/valuation mutations: `0`
- AI/fallback context mismatches: `0`

Runtime quality uses existing thresholds without relaxation.

