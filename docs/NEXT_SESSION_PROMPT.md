# Next Session Prompt

Repository: `sskim-ai/thesis-monitor`

First run `git fetch origin`, `git status`, `git rev-parse HEAD`, and
`git rev-parse origin/main`. Compare the development checkout with the clean operating checkout.
Repository and immutable runtime evidence override stale conversation claims.

Read, in order:

1. `docs/project-state.json`
2. `docs/MASTER_WORKFLOW.md`
3. `docs/PROJECT_HANDOFF.md`
4. `docs/architecture/WORKING_CAPITAL_EVIDENCE.md`
5. `docs/reports/20260821-phase9-1a-complete-report.md`
6. `docs/reports/20260821-phase9-1a-readiness.md`
7. `docs/reports/20260821-phase9-1a-coverage.json`
8. `docs/BRANCH_DEPENDENCY.md`

Current development state:

- Phase 9.1A: `ARCHITECTURE_CLOSED_READY_FOR_PHASE_9_1B`
- Contract: `working-capital-evidence-v1`
- Work-instruction commit: `eaaadb1ac4fb5c9a7d3486ecc8274708c285ff79`
- Implementation commit: `0d3b42715fc8964fe053d72e0ecc979fb78b14cc`
- Actions run `32447178183`: Test/Lint PASS
- `PHASE_9_1B_READY = YES`
- `PHASE_9_1B_SCOPE = SELECTIVE_INVENTORY_AR_AP_CANONICAL_CORE`
- Promotion: `PROMOTION_DEFERRED_FOR_KR_NATURAL_WINDOW`
- Runtime/user-visible behavior diff: `0`
- Open P0/material P1: `0 / 0`

Operating remains on Phase 9.0E main SHA `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
with mode `SELECTIVE_CURRENT_FORMAL_FULL_FCF`. Before promoting 9.1A, inspect the separate KR natural
review after the protected window. Do not promote across a newly observed P0. Do not run a task or
send Telegram manually.

Phase 9.1B may implement only the evidence-supported canonical core:

- total Inventory, without silent component aggregation;
- exact trade AR/AP and separate broad AR/AP, never collapsed;
- source balance scope and issuer-reported net/gross scope;
- same-fiscal-quarter prior-year point-in-time comparables;
- deterministic absolute delta and YoY growth;
- selective AR/revenue, Inventory/revenue, Inventory/COGS, and AP/COGS relations;
- explicit fail-closed states for missing or incompatible evidence.

Keep DSO, Inventory Days, DPO, CCC, standard ROIC, AI/Telegram consumption, Public Action/schema,
fallback rendering, assessment mutation, KR cash-flow period recovery, KRX breadth, and peer
integration out of Phase 9.1B. The next natural US cash-flow proof and KRX telemetry continue in
parallel under Phase Advancement Rule v1.
