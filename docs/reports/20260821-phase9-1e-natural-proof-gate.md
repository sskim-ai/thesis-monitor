# Phase 9.1E Natural-Proof Gate

Natural proof is read from packet-linked Phase 9.1D receipts; no renderer boolean or manual run can
create it. A valid `LIVE_PASS` requires packet and receipt IDs, canonical Fact and relation IDs,
PIT/current-formal PASS, semantic/causal/numeric PASS, zero production influence, and an immutable
evidence reference.

| Metric family | Proof | Enablement eligible | Block reason | Evidence |
| --- | --- | --- | --- | --- |
| Inventory | `NOT_OBSERVED` | no | `natural_proof_not_observed` | none |
| exact Trade AR | `NOT_OBSERVED` | no | `natural_proof_not_observed` | none |

A combined-mode preflight therefore resolves:

```text
requested = SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR
effective = OFF
accepted = false
```

Tests prove that Inventory-only may pass after Inventory `LIVE_PASS`, exact-Trade-AR-only may pass
after its own `LIVE_PASS`, both are required for combined mode, and `LIVE_FAIL`, incomplete proof,
open P0/material P1, or validator failure blocks the affected mode. Phase 9.1E preview evidence is
explicitly `PREVIEW_ONLY_NOT_ENABLEMENT_EVIDENCE`.

Final states:

- `INVENTORY_USER_VISIBLE_ENABLEMENT_READY = NO_PENDING_NATURAL`
- `TRADE_AR_USER_VISIBLE_ENABLEMENT_READY = NO_PENDING_NATURAL`
