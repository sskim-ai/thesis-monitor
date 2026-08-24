# Shadow Numeric Registry

## Boundary

The numeric semantic registry classifies every numeric field exposed to AI/shadow review. It does
not make a number true, and it does not control production packet persistence. It decides whether a
known canonical value may support prose, is retained only for audit, or must block AI readiness.

## Registry Classes

| Class | Registered | Prose allowed | Purpose |
|---|---:|---:|---|
| `REGISTERED_PROSE_ELIGIBLE` | yes | yes | Canonical facts with an approved semantic claim role |
| `REGISTERED_AUDIT_ONLY` | yes | no | Diagnostics and helpers retained for validation |
| `REGISTERED_INTERNAL_DERIVED` | yes | no | Deterministic reconciliation values not owned by prose |
| unsupported | no | no | Unknown path; AI readiness fails closed |

The investor-flow reconciliation contract registers exactly 30 paths per KR stock: ten fields for
each `1d`, `5d`, and `20d` window. Participant-flow entries preserve actor and window identity;
displayed/omitted/all-participant totals, constituent count, and display coverage retain their
specific audit semantics. All 30 are non-prose.

There is no wildcard registration. A newly appearing numeric path remains unsupported until an
exact semantic entry is added and tested. Residual or absorber arithmetic therefore cannot become
a participant attribution claim merely because the value is numerically available.

## Consumer Separation

The canonical foreign/institution supply facts already approved for structured prose remain
prose-eligible. Reconciliation fields support parity and integrity checks only. The numeric binder
rejects direct prose references to non-prose fields, while packet persistence and deterministic
fallback remain governed by their own production safety contract.
