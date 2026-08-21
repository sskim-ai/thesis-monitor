# Next Session Prompt

Repository: `sskim-ai/thesis-monitor`

First fetch and compare `origin/main`, the development checkout, and the clean operating checkout.
Read `docs/project-state.json`, `docs/MASTER_WORKFLOW.md`, `docs/PROJECT_HANDOFF.md`,
`docs/architecture/WORKING_CAPITAL_RUNTIME_SHADOW_CANARY.md`, and the Phase 9.1D complete report and
readiness JSON. Read `docs/architecture/WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md` and the
Phase 9.1E readiness JSON. Also read `docs/architecture/NIGHT_FUTURES_PUBLICATION_TELEMETRY.md` and the
night-futures telemetry complete report/readiness JSON. Repository and immutable runtime evidence
override conversation summaries.

Phase 9.1E pre-integration is complete after instruction commit
`99f7e86f3ae40cc86a4865ef70dc89abf79d5a37` and implementation commit
`a4f8570130d1fd33f802d391c6a196d1c5579278`. `WORKING_CAPITAL_USER_VISIBLE_MODE` remains `OFF`.
Inventory and exact Trade AR natural proof remain independently `NOT_OBSERVED`; their enablement
states are `NO_PENDING_NATURAL`. Do not enable either family, manufacture proof, or rerun a task.
After a natural Phase 9.1D receipt gives one family `LIVE_PASS`, prepare only a small enablement-only
instruction for that proven family and retain all Phase 9.1E guards.

The KR investor-flow reconciliation repair is complete after immutable instruction commit
`e9d7c73cf6f25b2423b55a6899465e86441316d1`; implementation
`47fc87e2a9189556a7206065fdb759f3603ce497` passed Actions run `32480802390`. Preserve
`kr-investor-flow-participants-v1` and `kr-investor-flow-reconciliation-v1`: top-level foreign,
institution, individual, other corporation, and domestic foreign reconcile separately, while
institution subclasses remain diagnostics only. Do not derive residual participants or restore
unsafe absorber attribution. Natural confirmation remains parallel.

Current state after clean Phase 9.1D promotion:

- Phase 9.1A architecture: COMPLETE and promoted
- Phase 9.1B canonical core: COMPLETE and promoted
- Phase 9.1C shadow consumption: CLOSED_RETROSPECTIVE and promoted
- Phase 9.1D contract: `working-capital-runtime-shadow-canary-v1`
- instruction commit: `dc4e1cf14faa7cebf78eb8ba5a5e73b6369c991c`
- implementation commit: `5316113062782b09595a495ec9a903a4973f9df5`
- canary state: `DEPLOYED_PENDING_NATURAL`
- approved scope: total Inventory and exact Trade AR only
- Inventory natural proof: `NOT_OBSERVED`
- exact Trade AR natural proof: `NOT_OBSERVED`
- working-capital user-visible output: NOT ENABLED
- `PHASE_9_1E_ARCHITECTURE_READY = YES`
- open P0/P1: 0/0

Observe the next natural US and KR canary archives without manually running a Scheduled Task or
sending Telegram. Classify each metric family independently. An empty eligible set is
`NOT_OBSERVED`, not failure. Any P0 stays isolated from production and receives a bounded repair.

Phase 9.1E architecture is complete, but no working-capital family may become user-visible before
its intended natural mechanism proof. Keep broad AR/AP, exact AP, DSO,
Inventory Days, DPO, CCC, standard ROIC, KR cash-flow period recovery, KRX breadth integration,
Pilot mutation, and Production Assist outside scope unless separately instructed.

The independent night-futures publication telemetry repair is deployed with instruction commit
`b7cf6a2f413e309bb637e524aeb7c1436e4c5b1b`, implementation commit
`d54f1102c02c9ff1c6a8ddd18fc40d1aea059caf`, and contracts
`night-futures-attempt-archive-v1` / `night-futures-publication-telemetry-v1`. Production attempts
remain 08:05/10/15/20; the detached observer is 08:45/09:15. Do not run either manually. After a
natural horizon, inspect stored evidence only. Until multi-day evidence supports otherwise,
`P1_TELEMETRY_GAP=REPAIR_DEPLOYED_PENDING_NATURAL` and
`DEADLINE_VERDICT=DEADLINE_UNPROVEN`.
