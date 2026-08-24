# KR Production Packet And Shadow Gate Separation

## Decision

`ROOT_CAUSE_BRANCH = C`

The original `shadow_cohort` gate was introduced by commit
`108a93721d267e8c6e1acf0693aa1e1e8e9bb6b4` to start an AI Shadow quality window only after
company-profile and numeric-semantic coverage were complete. Its `ready_for_ai` result remains a
legitimate fail-closed boundary for AI claims. The defect was using that same result to deny the
immutable production packet required by the deterministic fallback path.

## Separate Contracts

`kr-production-packet-persistence-v1` owns production persistence. It requires a supported market,
schema-valid packet, a complete successful source run, an available deterministic fallback, and no
explicit production hard error. Its denial reasons are `invalid_production_target`,
`packet_schema_invalid`, `successful_complete_run_required`,
`deterministic_fallback_unavailable`, and `production_safety_gate_failed`.

`shadow-cohort-readiness-v1` owns company-profile and numeric-semantic readiness for AI Shadow. A
false result records `shadow_profile_gate_not_ready`,
`shadow_numeric_semantic_gate_not_ready`, or `shadow_readiness_evaluation_failed`; it keeps
`ready_for_ai=false` and is never promoted into production eligibility.

## Ordering

```text
valid production target
-> complete deterministic analysis
-> production persistence decision
-> immutable packet
-> packet-bound provisional intents
-> held AI/fallback session
-> AI claim only when shadow ready
-> deterministic fallback when AI is unavailable
```

Packet identity is derived from production content, excluding transient shadow readiness and its
error metadata. A shadow timeout followed by a successful retry therefore cannot create a second
packet identity or duplicate delivery intents.

## Blocking Boundary

Production-blocking conditions remain the XKRX role-target guard, incomplete analysis, malformed
packet identity/schema, unavailable deterministic fallback, explicit production P0/hard errors,
atomic packet-write failure, and packet-binding failure before intent creation.

Non-blocking shadow conditions are profile cohort incompleteness, unregistered AI prose semantics,
shadow validator unavailability, timeout, and exception. There is no separate canary activation
condition in packet persistence; detached canaries remain post-terminal and best effort.

## Feature Isolation

`SELECTIVE_INVENTORY` remains unchanged and may contribute already-approved packet context. Exact
Trade AR stays OFF. Macro temporal eligibility and investor-flow reconciliation retain their
existing contracts. The repair changes neither their selectors nor public wording.

## Natural Proof

Retrospective replay proves production reachability only. After promotion:

```text
KR_SHADOW_GATE_PACKET_REPAIR = DEPLOYED_PENDING_NATURAL
KR_PRODUCTION_NATURAL = PENDING
```

LIVE PASS requires the first natural eligible KR run to persist one packet, bind eight intents,
deliver through AI or deterministic fallback exactly once, and leave zero duplicates or orphans.
