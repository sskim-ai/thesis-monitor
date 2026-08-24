# KR Shadow Gate Negative Controls

| Fixture | Expected | Result |
|---|---|---|
| Unsupported market/target | block | PASS: `invalid_production_target` |
| Invalid packet schema | block | PASS: `packet_schema_invalid` |
| Incomplete source run | block | PASS: builder/persistence fail closed |
| Deterministic fallback unavailable | block | PASS |
| Unsafe numeric provenance | block | PASS: production safety failure |
| Explicit production P0 | block | PASS: production safety failure |
| Packet atomic-write error | no packet/no intent | PASS |
| Profile cohort incomplete | packet persists, AI suppressed | PASS |
| Numeric shadow validation false | packet persists, AI suppressed | PASS |
| Shadow timeout/runtime exception | packet persists, error audited | PASS |
| Shadow state changes on retry | same packet identity | PASS |
| Inventory selected | packet persists | PASS |
| Inventory mode on, no selection | packet persists | PASS |
| Trade AR | absent/off | PASS |
| Insurance/feature sidecars | no gate promotion | PASS via unchanged regressions |

There is no independent canary availability check in packet persistence. Existing detached canaries
remain post-terminal and best effort, so adding a synthetic canary gate would create a new coupling
rather than test the incident path.
