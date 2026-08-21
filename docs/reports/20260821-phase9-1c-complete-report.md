# Phase 9.1C Complete Report

## Repository

- Instruction: `docs/work-instructions/20260821-phase-9-1c-working-capital-shadow-consumption.md`
- Instruction version: `1.0`
- Instruction commit: `613d91d74d3a91c43ed61f98a13a2ca57b7a90ae`
- Dependency base: `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6`
- Branch: `codex/phase-9-1c-working-capital-shadow-consumption`
- Implementation/final branch: pending exact-SHA commits
- Main/operating: `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Promotion: `PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`
- Runtime/user-visible working-capital diff: `0`

## Consumption Coverage

| Metric | Eligible | Consumed | Eligible suppressed | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|---:|---:|
| Inventory | 11 | 5 | 6 | 3 | 5 | 1 |
| Trade AR | 6 | 2 | 4 | 1 | 12 | 1 |
| Broad AR | 9 | 0 | 9 | 3 | 7 | 1 |
| Trade AP | 8 | 0 | 8 | 1 | 10 | 1 |
| Broad AP | 10 | 0 | 10 | 1 | 8 | 1 |

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

## Relation Usage

| Relation | Eligible | Selected | Suppressed | Semantic scope | Value add |
|---|---:|---:|---:|---|---|
| trade_ar_vs_revenue | 6 | 2 | 4 | exact_trade | MATERIAL_IMPROVEMENT=2 |
| broad_ar_vs_revenue | 8 | 0 | 8 | broad | - |
| inventory_vs_revenue | 11 | 2 | 9 | total_inventory | MATERIAL_IMPROVEMENT=2 |
| inventory_vs_cogs | 11 | 3 | 8 | total_inventory | MATERIAL_IMPROVEMENT=3 |
| trade_ap_vs_cogs | 8 | 0 | 8 | exact_trade | - |
| broad_ap_vs_cogs | 9 | 0 | 9 | broad | - |

| Ticker | Semantic scope | Direction | Gap | Cash-flow cross-link |
|---|---|---|---:|---|
| 000660 | inventory | LOWER | -2.1%p | NOT_PROVIDED |
| 005490 | inventory | GREATER | 7.1%p | NOT_PROVIDED |
| 005930 | inventory | GREATER | 35.8%p | NOT_PROVIDED |
| 010120 | trade_accounts_receivable | GREATER | 18.0%p | NOT_PROVIDED |
| 086280 | trade_accounts_receivable | GREATER | 40.0%p | NOT_PROVIDED |
| MU | inventory | LOWER | -15.7%p | COMPATIBLE_FORMAL_PERIOD |
| TSLA | inventory | LOWER | -26.6%p | COMPATIBLE_FORMAL_PERIOD |

## PIT / Freshness

- PIT-valid consumed relations: `7`
- Future Facts consumed: `0`
- Formal-lagging-provisional: `1`
- Stale context only: `0`
- Blocked / N/A: `11 / 1`
- Violations: `0`

## Cash-Flow Cross-Link

- Compatible periods: `3`
- Selected cross-links: `2`
- Incompatible periods suppressed: `0`
- Causal claims: `0`
- OCF/FCF recomputation: `0`

## Unknown Resolution

- Before: `4`
- Exact resolved: `4`
- Broad-only narrowed: `0`
- Still valid / stale / N/A: `0 / 0 / 0`
- Contradictions: `0`

## Safety

- PIT-valid numeric claims: `7`
- Manual/rejected/unresolved/arithmetic: `0 / 0 / 0 / 0`
- Broad-to-trade / contract-asset / accrued-liability / advanced-ratio leakage: `0 / 0 / 0 / 0`
- Unsupported causal claims: `0`
- Unknown contradictions: `0`
- Cash-flow cross-link causal claims: `0`
- Thesis/valuation/warning persistence: `0`
- Telegram/manual task/Pilot/DB/archive/receipt/force-push mutations: `0`
- Production Assist: `OFF`
- Phase 9.0E mode changed: `NO`

## Human Quality

- Material improvement: `7`
- Minor improvement: `0`
- No meaningful change: `13`
- Degraded: `0`
- Average message length delta: `32.1` characters across all 20 subjects
- Shadow quality: `PASS`

## Parallel Tracks

- Natural AI: independent operating track; no manual run
- KRX telemetry: unchanged
- KR OpenDART cash-flow period recovery: `MEDIUM` follow-up, unchanged
- Natural KR promotion review: separate from 9.1C retrospective evidence

## P0 / P1 / P2

- Open P0: `0`
- Open P1: `0`
- P2: prior-quarter working-capital relation lifecycle, inventory component decomposition, contract-assets separate evidence family, AP relation value-add remains excluded from initial canary

## Validation

Focused and evidence validation: PASS. Full exact-SHA validation and Actions are recorded in the final validation update.

## Natural KR Gate

Natural KR review remains a separate operating-safety input. No manual run or report mutation was performed; promotion is deferred for that review.

## Final Gate

`PHASE_9_1D_READY = YES`

`PHASE_9_1D_SCOPE = SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR`

`DSO_READY_FOR_IMPLEMENTATION = DEFER`

`INVENTORY_DAYS_READY_FOR_IMPLEMENTATION = DEFER`

`DPO_READY_FOR_IMPLEMENTATION = DEFER`

`CCC_READY_FOR_IMPLEMENTATION = DEFER`
