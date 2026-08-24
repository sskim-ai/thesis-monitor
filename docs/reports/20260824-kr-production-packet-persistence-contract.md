# KR Production Packet Persistence Contract

## Contract

`kr-production-packet-persistence-v1`

A packet is persistence-eligible only when all conditions are true:

1. Market is supported and the upstream XKRX producer role target has already admitted the run.
2. Packet schema version, output schema, packet ID, assessment date, market context, and stock list
   are present.
3. Source run is successful and complete: positive ticker count, success count equals ticker count,
   failure count zero, and one stock payload per successful ticker.
4. Deterministic fallback is available.
5. Explicit production hard errors are empty.

Shadow readiness is not an input. The decision records
`shadow_readiness_influence=none`.

## Denials

| Reason | Meaning |
|---|---|
| `invalid_production_target` | unsupported production market/target |
| `packet_schema_invalid` | required packet structure absent or incompatible |
| `successful_complete_run_required` | analysis is absent, partial, or inconsistent |
| `deterministic_fallback_unavailable` | no safe terminal delivery path |
| `production_safety_gate_failed` | explicit production P0/hard error |
| write exception type | atomic persistence failed; no intent may be created |

Missing or unsafe conditions are never converted to zero/default facts. Atomic-write failure leaves
no partial packet and the producer preserves the packet-before-intent invariant.
