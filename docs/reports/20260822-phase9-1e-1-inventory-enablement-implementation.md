# Phase 9.1E.1 Inventory Enablement Implementation

## Repository Lineage

- Base main/operating: `fb445104f491a57ea67f435eab37426b0acd0c63`
- Work-instruction commit: `880e7a9834439971f53b8a7bc0712d0ece26854d`
- Natural-evidence merge: `018af42`
- Initial implementation commit: `85ab01130f34650edca6a0bcba5c5ae52db4edf0`
- Branch: `codex/phase-9-1e-1-inventory-only-user-visible-enablement`

The instruction was committed and pushed before implementation. The morning natural-evidence
branch was merged explicitly after that instruction commit, preserving both histories.

## Implementation

Phase 9.1E.1 reuses `working-capital-user-visible-v1` and the existing family enable gate. It adds:

- a shared read-only canonical working-capital evidence loader;
- Inventory-only preflight enforcement;
- contract-driven total-Inventory selection with no ticker allowlist;
- one exact `%p` relation owned by `business_earnings`;
- production AI packet and deterministic fallback consumption;
- exact AI/fallback context, Fact, relation, period, scope and packet parity;
- delivery receipt metadata and a fail-closed `OFF` kill switch;
- archive/read-only replay and readiness generators.

Trade AR, broad AR, AP, DSO, Inventory Days, DPO and CCC remain disabled. Inventory does not mutate
thesis, warning or valuation state. Phase 9.0E cash flow and the 9.1D detached canary remain
independent.

## Runtime Boundary

With mode `OFF`, production AI and fallback outputs are byte-identical to the previous operating
implementation. With `SELECTIVE_INVENTORY`, only a gate-approved current-formal total-Inventory
relation may be added to the existing business/earnings section. Missing or invalid configuration
resolves to `OFF`.

Machine evidence:

- `20260822-phase9-1e-1-readiness.json`
- `20260822-phase9-1e-1-runtime-replay.json`
- `20260822-phase9-1e-1-natural-proof-evidence.json`

