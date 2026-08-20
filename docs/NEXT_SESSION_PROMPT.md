# Next Session Prompt

Repository: `sskim-ai/thesis-monitor`

First run `git fetch origin`, `git status`, `git rev-parse HEAD`, and
`git rev-parse origin/main`. Compare the development checkout with the clean operating checkout.
Repository and immutable runtime evidence override stale conversation claims.

Read, in order:

1. `docs/project-state.json`
2. `docs/MASTER_WORKFLOW.md`
3. `docs/PROJECT_HANDOFF.md`
4. `docs/architecture/CASH_FLOW_CAPITAL_EFFICIENCY.md`
5. `docs/reports/20260820-phase9-0a-complete-report-bundle.md`
6. `docs/reports/20260820-phase9-0a-coverage.json`
7. `docs/reports/20260820-phase9-0a-readiness.json`
8. `docs/BRANCH_DEPENDENCY.md`

Current major state:

- Phase 9.0A: `ARCHITECTURE_CLOSED`
- `PHASE_9_0B_READY = YES`
- `PHASE_9_0B_SCOPE = SELECTIVE_ELIGIBLE_SUBSET_OCF_CAPEX_FCF_CORE`
- Natural AI-Assisted Delivery: `PARTIAL`, observed independently
- KRX exact-slot telemetry: operating capture only, observed independently
- Production Assist: `OFF`

The next major task is Phase 9.0B Canonical OCF / PPE-CAPEX / FCF Core Implementation. Implement
only the evidence-eligible subset and fail closed elsewhere. Do not expose cash-flow numbers in
Telegram, the AI packet, fallback, or any user-visible renderer until a later explicit integration
gate.

Preserve these Phase 9.0A decisions:

- OCF is exact net cash from operating activities; no EBITDA/earnings proxy.
- Baseline CAPEX is positive-magnitude PPE cash outflow only.
- Intangibles and capitalized software remain separate components.
- Baseline FCF is OCF less PPE-only CAPEX under identical period, unit, entity, and statement basis.
- Q2/Q3 QTD requires adjacent compatible YTD subtraction.
- TTM requires prior FY plus current YTD less prior comparable YTD.
- No annualization, CFS/OFS mixing, currency mixing, restatement mixing, or reverse engineering.
- Foreign issuer-level margins may be eligible without ADR ratio; per-share/yield/EV arithmetic may
  not.
- Insurance generic FCF/CCC/ROIC is not applicable.
- DSO/inventory days/DPO/CCC and standard ROIC are deferred from Phase 9.0B.

In parallel, review any newly completed natural US/KR packets for AI delivery, runtime quality,
receipt, archive, exactly-once, night futures, and fallback. Let KRX 08:05/16:05 telemetry accumulate
naturally. Do not run Scheduled Tasks, KRX capture, or Telegram manually.

Apply Phase Advancement Rule v1: a new P0 pauses 9.0B for a targeted repair; material P1 receives a
bounded repair; P2 remains backlog. Natural AI partial status or pending KRX publication evidence
alone does not block Phase 9.0B.
