# Next Session Prompt

Repository: `sskim-ai/thesis-monitor`

Latest bounded repair: natural KR run 36 exposed `ROOT_CAUSE_BRANCH = C`. The historical
company-profile/numeric-semantic Shadow gate correctly blocks unsupported AI claims but incorrectly
blocked the production packet needed by deterministic fallback. Read
`docs/architecture/KR_PRODUCTION_PACKET_AND_SHADOW_GATE_SEPARATION.md` and the bundled 2026-08-24
reports. Instruction commit is `7da8d8866a9b7aafc8c010424cdbc4192de46cbb`; implementation commit
is `64086c4af7735dcbe2fd3f5093f4167952a280e0`. State is `DEPLOYED_PENDING_NATURAL` with P0/P1 0/0.

At the next natural eligible KR close, inspect read-only evidence for one immutable packet, digest
plus seven packet-bound intents, AI or fallback delivery, exactly-once receipt, and zero duplicates
or orphans. Do not run KR production manually or send Telegram. `shadow-cohort-readiness-v1` may
remain false while `kr-production-packet-persistence-v1` passes; that is expected and AI must remain
unclaimable until its own gate passes.

Latest bounded repair: `macro-digest-temporal-eligibility-v1` follows instruction commit
`951558c0ec79f84b739eff1cbafd2870eb6f3fba` and implementation commit
`68a6c39a098380d8a22de5b4d784c730818e9b04`. Branch B was confirmed: source freshness existed but
daily-current eligibility did not. Immutable run-35 replay is PASS and the normal 8/22 replay
preserves valid current signals. State is `DEPLOYED_PENDING_NATURAL`; inspect the next natural US
digest read-only for current/prior/reference role parity, no false today wording, ticker-impact
gating, receipts, and exactly-once delivery. Do not manually run the task or send Telegram.

First fetch and compare `origin/main`, the development checkout, and the clean operating checkout.
Read `docs/project-state.json`, `docs/MASTER_WORKFLOW.md`, `docs/PROJECT_HANDOFF.md`,
`docs/architecture/WORKING_CAPITAL_RUNTIME_SHADOW_CANARY.md`, and the Phase 9.1D complete report and
readiness JSON. Read `docs/architecture/WORKING_CAPITAL_USER_VISIBLE_PREINTEGRATION.md`, the
Phase 9.1E readiness JSON, and all Phase 9.1E.1 rollout reports/JSON. Also read
`docs/architecture/NIGHT_FUTURES_PUBLICATION_TELEMETRY.md` and the
night-futures telemetry complete report/readiness JSON. Repository and immutable runtime evidence
override conversation summaries.

Also read `docs/architecture/KR_PRODUCER_SESSION_AND_DELIVERY_INTEGRITY.md` and the bundled
2026-08-22 KR producer repair reports. The repair follows docs-only instruction commit
`2125562a863d858ee1ab62675c31c7c13be33506` and implementation commit
`c26c9359b134df0a4cd697fd97e7616cc508e885`. Run 33 produced no immutable packet but left eight raw
pending rows: seven stocks plus one digest. The exact reconciler terminalized only those rows as
`failed` with reason `non_trading_day_orphan_no_packet`; it did not send, delete, set `sent_at`, or
change payloads. `kr_daily_production` now resolves the shared XKRX role target before providers,
run state, or delivery state, and packet-bound delivery intents are created only after a real packet
file exists. State is `DEPLOYED_PENDING_NATURAL`; inspect the next weekend/holiday naturally and
read-only. Do not run KR production manually.

Phase 9.1E.1 follows instruction commit `880e7a9834439971f53b8a7bc0712d0ece26854d` and explicit
morning-evidence merge `018af42`. Inventory natural proof is `LIVE_PASS_RUN32`; exact Trade AR is
`NOT_OBSERVED`. The Inventory-only implementation and preflight pass with open P0/material P1 zero.
Operating activation completed safely with `WORKING_CAPITAL_USER_VISIBLE_MODE=SELECTIVE_INVENTORY`.
Inventory is `ENABLED_PENDING_NATURAL`; Trade AR and combined modes remain OFF.

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
- canary state: `INVENTORY_LIVE_PASS_TRADE_AR_NOT_OBSERVED`
- approved scope: total Inventory and exact Trade AR only
- Inventory natural proof: `LIVE_PASS_RUN32`
- exact Trade AR natural proof: `NOT_OBSERVED`
- working-capital user-visible output: Inventory enabled pending natural proof
- `PHASE_9_1E_ARCHITECTURE_READY = YES`
- open P0/P1: 0/0

Observe the next natural user-visible Inventory selection without manually running a Scheduled Task
or sending Telegram. An empty eligible set is `NOT_OBSERVED`, not failure. Any P0 turns the mode OFF
and gets a bounded repair with immutable evidence preserved.

The next major action remains the first eligible Inventory packet. The independent KR producer
weekend/holiday proof continues in parallel and does not block that observation.

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
