# Next Session Prompt

Repository: `sskim-ai/thesis-monitor`

First run `git fetch origin`, `git status`, `git rev-parse HEAD`, and
`git rev-parse origin/main`. Compare the development checkout with the clean operating checkout.
Repository and immutable runtime evidence override stale conversation claims.

Read, in order:

1. `docs/project-state.json`
2. `docs/MASTER_WORKFLOW.md`
3. `docs/PROJECT_HANDOFF.md`
4. `docs/architecture/CASH_FLOW_BASELINE_CONSISTENCY.md`
5. `docs/reports/20260821-phase9-0d-1-validation.md`
6. `docs/reports/20260821-phase9-0d-1-cross-artifact-consistency-audit.md`
7. `docs/reports/20260821-phase9-0e-readiness.md`
8. `docs/architecture/CASH_FLOW_RUNTIME_SHADOW_CANARY.md`
9. `docs/BRANCH_DEPENDENCY.md`

Current state:

- Phase 9.0A: `ARCHITECTURE_CLOSED`
- Phase 9.0B: `CANONICAL_CORE_IMPLEMENTED_SHADOW`
- Phase 9.0C: `CLOSED_RETROSPECTIVE`
- Phase 9.0D: `LIVE_PASS_SELECTIVE_SUBSET`
- Phase 9.0D.1: `BASELINE_CASH_FLOW_CONSISTENCY_CLOSED`
- `PHASE_9_0E_READY = YES`
- Phase 9.0E scope: `SELECTIVE_CURRENT_FORMAL_FULL_FCF_USER_VISIBLE_INTEGRATION`
- Cash-flow user-visible integration: `NOT_ENABLED`
- Natural AI-Assisted Delivery: `PARTIAL`, tracked independently
- KR OpenDART period recovery: `MEDIUM_FOLLOWUP`
- CCC / standard ROIC: `DEFERRED / DEFERRED`
- Production Assist: `OFF`

Natural US run `2026-08-21-us-run-30-5a3b7c1c4390` delivered fallback `14/14` and produced canary
`cf-canary-f5ce3f836df99c546cf6f696`, which passed nine full-FCF, one OCF-only, two
formal-lagging-provisional, and one blocked paths with zero production influence. Do not demand a
second arbitrary natural run for Phase 9.0D.1.

Phase 9.0D.1 found TSLA's saved version-5 generic `FCF 적자` prose had no financial Fact, period,
or scope. The system now suppresses that current-state clause and its prose-only backfilled warning
in packet/fallback rendering, and the detached canary validates production qualitative claims
against canonical context. Stored history remains unchanged and no canonical number is injected.

The next major task may begin Phase 9.0E. Keep the first rollout narrow:

- current-formal full-FCF contexts only;
- dynamic eligibility, no ticker allowlist;
- business/earnings-quality exact numeric ownership;
- replace resolved or contradictory prose instead of append-only duplication;
- KR and formal-lagging-provisional numeric display excluded;
- no FCF yield/share/EV, CCC, ROIC, DB mutation, task change, or Production Assist.

Natural AI delivery and KRX telemetry continue in parallel. Apply Phase Advancement Rule v1: a new
P0 pauses implementation for targeted repair, material P1 receives a bounded repair, and P2 remains
backlog. Do not manually run Scheduled Tasks, Telegram, KRX capture, or Pilot.
