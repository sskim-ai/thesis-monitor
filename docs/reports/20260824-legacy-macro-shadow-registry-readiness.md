# Legacy Macro / Shadow Registry Readiness

## Repository

- Instruction: `docs/work-instructions/20260824-legacy-macro-temporal-rehydration-and-shadow-registry-closure.md`
- Instruction version: 1.0
- Instruction commit: `2ddec88382f0aff32fcae68a87d1aff62f60f2ef`
- Branch: `codex/legacy-macro-temporal-shadow-registry-closure`
- Previous main: `96825de767f8ff25b59ab4451df305df5dd873cc`
- Implementation: `5c58f32e23db7a817f5f9947d2af509f6021f4ff`
- Implementation Actions: run `32725115091`, Test/Lint PASS

## Decision

`LEGACY_MACRO_AND_SHADOW_REGISTRY_REPAIR_READY = YES`

- Open P0: 0
- Open material P1: 0
- P2: first natural eligible KR proof; exact Trade AR natural proof; natural Inventory confirmation
- Optional fresh rehearsal: skipped to preserve the immutable 19:34 evidence lock

## Final State

```text
LEGACY_MACRO_TEMPORAL_REHYDRATION = PASS
SHADOW_INVESTOR_FLOW_NUMERIC_REGISTRY = PASS
KR_PRODUCTION_REPAIRED_LIVE_REHEARSAL = PASS
KR_PACKET_DELIVERY_DRY_RUN = PASS
AI_CANDIDATE_REHEARSAL = PASS
INVENTORY_USER_VISIBLE_REHEARSAL = PASS
KR_INVESTOR_FLOW_REHEARSAL = PASS
MACRO_TEMPORAL_REHEARSAL = PASS
TRADE_AR_USER_VISIBLE = OFF_PENDING_NATURAL_PROOF
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
LEGACY_MACRO_AND_SHADOW_REGISTRY_REPAIR = DEPLOYED_PENDING_NATURAL
NEXT_ACTION = WAIT_FOR_FIRST_SUCCESSFUL_KR_NATURAL_PACKET
```

Promotion is permitted after the final documentation SHA passes Actions and ancestry remains a
clean linear descendant. Replay proof does not become natural proof.
