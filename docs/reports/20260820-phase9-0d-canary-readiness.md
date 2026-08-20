# Phase 9.0D Pre-Natural Canary Readiness

- `RUNTIME_CANARY_DEPLOYED = YES` after clean main/operating promotion
- `READY_FOR_NEXT_NATURAL_US_CANARY = YES`
- Runtime plumbing state: `IMPLEMENTED_PENDING_NATURAL`
- Natural US canary state: `NOT_OBSERVED`
- Natural KR negative control state: `NOT_OBSERVED`
- Production isolation: `PASS`
- Idempotency and artifact isolation: `PASS`
- Four AI task IDs/prompts/schedules: unchanged at 08:15/08:30/16:15/16:55 KST
- KRX telemetry scheduler: unchanged at 08:05/16:05 KST
- Expected next primary US slot: `2026-08-21 08:15 KST`
- Expected backup slot: `2026-08-21 08:30 KST`
- Deterministic fallback deadline: `2026-08-21 08:40 KST`
- Production Assist: `OFF`
- Cash-flow user-visible: `NOT_ENABLED`

Expected artifacts are under the natural packet's production history directory in the separate
`cash-flow-shadow-canary/<canary-id>` namespace. A completion marker alone is not enough: the
follow-up review must verify scheduled source, production result/receipt integrity, cash-flow value
add, numeric/semantic/quality gates, influence count zero, and idempotency.

Open P0: `0`

Open P1: `0`

P2 backlog remains management-defined FCF reconciliation, optional wording polish, CCC, standard
ROIC, and KR OpenDART period-context recovery. None authorizes user-visible integration.

`PHASE_9_0E_READY = NO`

Reason: the required first natural US runtime canary has not occurred. This is an observation gate,
not an unresolved architecture or correctness blocker.

