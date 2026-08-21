# Phase 9.1A Readiness

## Closed Decisions

- Inventory: total inventory only; no silent component aggregation.
- AR: `TRADE_PLUS_SEPARATE_BROAD`.
- AP: `TRADE_PLUS_SEPARATE_BROAD`.
- Balance scope: source current/total scope preserved; no automatic summation.
- Comparable date: prior fiscal-year same fiscal quarter, exact semantic/basis/currency/unit.
- Revenue: same filing and comparable flow period; YTD preferred for Q2/Q3.
- COGS: `INCLUDE_SELECTIVELY_EXACT_SEMANTIC`.
- PIT/freshness: source availability retained; provisional-only periods do not relabel formal balances.
- DSO / Inventory Days / DPO / CCC: `DEFER / DEFER / DEFER / DEFER`.

Open P0: `0`. Open material P1: `0`.

P2 backlog: prior-quarter relations, inventory components, contract assets, and advanced ratio prerequisites.

Runtime/user-visible behavior diff: `0`.

`PHASE_9_1B_READY = YES`

`PHASE_9_1B_SCOPE = SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE`

Recommended next phase: Phase 9.1B canonical working-capital core for the selected Inventory/AR subset, preserving exact trade versus separate broad semantics and fail-closing unsupported AP/COGS relations.
