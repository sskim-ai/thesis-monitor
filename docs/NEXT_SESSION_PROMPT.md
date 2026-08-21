# Next Session Prompt

Repository: `sskim-ai/thesis-monitor`

First run `git fetch origin`, `git status`, `git rev-parse HEAD`, and
`git rev-parse origin/main`. Compare the development checkout with the clean operating checkout.
Repository and immutable runtime evidence override stale conversation claims.

Read, in order:

1. `docs/project-state.json`
2. `docs/MASTER_WORKFLOW.md`
3. `docs/PROJECT_HANDOFF.md`
4. `docs/architecture/WORKING_CAPITAL_SHADOW_CONSUMPTION.md`
5. `docs/reports/20260821-phase9-1c-complete-report.md`
6. `docs/reports/20260821-phase9-1c-readiness.md`
7. `docs/reports/20260821-phase9-1c-shadow-context.json`
8. `docs/reports/20260821-phase9-1b-canonical-facts.json`
9. `docs/BRANCH_DEPENDENCY.md`

Current development state:

- Phase 9.1A: `COMPLETE_PENDING_PROMOTION`
- Phase 9.1B: `COMPLETE_PENDING_PROMOTION`
- Phase 9.1C: `SHADOW_CONSUMPTION_CLOSED_RETROSPECTIVE_PENDING_PROMOTION`
- Contract: `working-capital-evidence-v1`
- Derivation: `working-capital-evidence-v1:canonical-core-v1`
- Consumption contract: `working-capital-shadow-consumption-v1`
- 9.1C work-instruction commit: `613d91d74d3a91c43ed61f98a13a2ca57b7a90ae`
- Implementation commit: `aba64e85c34db620416ea9ee5cae36c0fe6b31d0`; Actions run `32454469417` Test/Lint PASS
- Final documentation commit: resolve from Git and exact-SHA Actions
- `PHASE_9_1D_READY = YES`
- `PHASE_9_1D_SCOPE = SELECTIVE_RUNTIME_SHADOW_CANARY_INVENTORY_EXACT_TRADE_AR`
- Promotion: `PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`
- Runtime/user-visible behavior diff: `0`
- Open P0/material P1: `0 / 0`

Operating remains on Phase 9.0E main SHA `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
with mode `SELECTIVE_CURRENT_FORMAL_FULL_FCF`. Before promoting 9.1A, inspect the separate KR natural
review after the protected window. Do not promote across a newly observed P0. Do not run a task or
send Telegram manually.

Phase 9.1B implements the evidence-supported canonical core:

- total Inventory, without silent component aggregation;
- exact trade AR/AP and separate broad AR/AP, never collapsed;
- source balance scope and issuer-reported net/gross scope;
- same-fiscal-quarter prior-year point-in-time comparables;
- deterministic canonical absolute delta and balance/flow YoY Facts;
- six trade/broad-preserving AR/revenue, Inventory/revenue, Inventory/COGS, and AP/COGS relations;
- explicit fail-closed states for missing or incompatible evidence.

Implementation coverage is unchanged from Phase 9.1A. The audit contains 160 selected reported
Facts, 44 delta, 44 balance YoY, 31 flow YoY Facts, and 53 eligible structured relations with zero
arithmetic, provenance, idempotency, or coverage-regression errors.

Phase 9.1C selects seven current-formal, material relations from that store: five Inventory and two
exact Trade AR. TSM is formal-lagging-provisional; insurance is N/A. Automatic binding is 7/7 and
PIT, semantic, causal, arithmetic, Unknown, repetition, and human-quality degradation errors are
zero. Broad AR/AP and AP relations are excluded from the initial canary on observed value-add.

The next default phase is a delivery-isolated runtime shadow canary for only the approved Inventory
and exact Trade AR scope. Do not expose working-capital text to actual AI/Telegram, change Public
Action/schema/fallback, mutate assessments, add DSO/Inventory Days/DPO/CCC/ROIC, recover KR
cash-flow periods, or integrate KRX breadth/peers unless a separate instruction explicitly
authorizes it. First consume the separate KR natural review before promoting 9.1A -> 9.1B -> 9.1C.
The next natural US cash-flow proof and KRX telemetry continue in parallel under Phase Advancement
Rule v1.
