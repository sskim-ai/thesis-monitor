# Phase 8.5.3.2 RXRX Valuation Label Validation

## Result

- RXRX label collisions: 1 -> 0.
- Portfolio legacy same-label/different-role collisions: 2 -> 0; RXRX and WULF are both repaired
  by the same field-role contract.
- Numeric provenance: 100% exact coverage.
- Typed valuation errors: 0.
- Biotech valuation misuse: 0.
- US/KR full validator: PASS / PASS.
- US/KR runtime quality: PASS / PASS.
- Output schema 4, industry reasoning, RR, language/dedup, and fallback contracts unchanged.

## Root Cause

The numeric semantic registry collapsed historical-distribution `current_value`,
`historical_median`, `historical_mean`, and percentile cut values into one
`historical_pb_multiple` label family. The binder therefore retained valid values and provenance
but lost their comparison roles at display time. Phase 8.5.3.2 preserves a deterministic
`comparison_role`, applies role-aware labels to both new and legacy schema-4 packets, and rejects
same-label/different-role collisions.

## Operations

- Telegram sends: 0.
- Scheduled Task manual executions: 0.
- Pilot mutations: 0.
- Production Assist: OFF.
- AI mode: shadow.
