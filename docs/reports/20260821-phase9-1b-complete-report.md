# Phase 9.1B Complete Report

## Repository

- Contract: `working-capital-evidence-v1`
- Derivation: `working-capital-evidence-v1:canonical-core-v1`
- Active universe: `20` (`KR 7`, `US/foreign 13`)
- Provider calls: SEC `0`, OpenDART `0`, paid `0`
- Runtime/user-visible diff: `0`

## Coverage

| Family | Eligible | Partial | Blocked | N/A |
|---|---:|---:|---:|---:|
| inventory | 11 | 3 | 5 | 1 |
| trade_ar | 6 | 1 | 12 | 1 |
| broad_ar | 9 | 3 | 7 | 1 |
| trade_ap | 8 | 1 | 10 | 1 |
| broad_ap | 10 | 1 | 8 | 1 |

## Relations

| Relation family | Eligible | Blocked | N/A |
|---|---:|---:|---:|
| trade_ar_vs_revenue | 6 | 13 | 1 |
| broad_ar_vs_revenue | 8 | 11 | 1 |
| inventory_vs_revenue | 11 | 8 | 1 |
| inventory_vs_cogs | 11 | 8 | 1 |
| trade_ap_vs_cogs | 8 | 11 | 1 |
| broad_ap_vs_cogs | 9 | 10 | 1 |

## Safety

- Derived input lineage complete: `True`
- Eligible relation lineage complete: `True`
- Arithmetic errors: `0`
- Provenance errors: `0`
- Idempotency errors: `0`
- Metric newly blocked: `0`
- Telegram/manual tasks/Pilot/DB/Public Action/fallback mutations: `0`
- Production Assist: `OFF`

## Validation

- Focused: `37 passed`
- Broader regression: `260 passed, 1 existing third-party warning`
- Full pytest: `1301 passed, 1 existing third-party warning`
- Deterministic evidence: PASS
- Ruff / diff / Knowledge / Chart / Public Action / operationId: PASS
- Exact-SHA Actions: pending implementation and final commits

## Deferred

DSO / Inventory Days / DPO / CCC / ROIC: `DEFER`. Contract assets, accrued-liability decomposition, inventory component aggregation, and prior-quarter lifecycle remain outside 9.1B.

## Promotion

`PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`

## Final Gate

`PHASE_9_1C_READY = YES`

`PHASE_9_1C_SCOPE = WORKING_CAPITAL_SHADOW_CONSUMPTION_EARNINGS_QUALITY`
