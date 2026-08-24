# 2026-08-24 KR Shadow Gate Condition Inventory

| Condition | Source | Run-36 value | Production | Shadow | Repaired behavior |
|---|---|---:|---|---|---|
| XKRX target | `resolve_xkrx_role_target` | valid 2026-08-24 | blocking | no | pass before analysis |
| Analysis completeness | `MonitorRun` | 7/7, failures 0 | blocking | input | pass |
| Packet schema/identity | packet builder | constructible | blocking | input | validate before write |
| Profile coverage | `company_profile_coverage` | 20/20 | no | blocking | record; AI suppressed only |
| Numeric registry | `numeric_registry_coverage` | 210 unsupported | no | blocking | record; AI suppressed only |
| Deterministic fallback | notification renderer | available | blocking | no | required |
| Production hard errors | persistence sidecar | none | blocking | no | fail closed if present |
| Shadow cohort membership | `shadow_cohort` | ineligible | no | blocking | `ready_for_ai=false` |
| Detached canary | post-terminal jobs | not a packet gate | no | separate | no persistence influence |
| Inventory mode | settings/selector | `SELECTIVE_INVENTORY` | evidence only | evidence only | unchanged |
| Trade AR mode | settings/selector | OFF | no | no | unchanged |
| Production Assist | settings | OFF | no | no | unchanged |
| Previous natural proof | persistent state | pending | no | observation | no serial gate |
| Packet persistence | atomic JSON write | failed before repair | blocking | no | succeeds when production safe |
| Delivery hold | packet-bound intent | unreachable before | blocking ordering | no | after packet only |

The only failed run-36 gate was the shadow numeric-semantic gate. No evidence identifies a malformed
production target, incomplete analysis, unsafe deterministic payload, write error, or production P0.
