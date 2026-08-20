# Phase 9.0B Canonical Core Implementation

Contract: `cash-flow-capital-efficiency-v1`

Implemented modules:

- `official_cash_flow_service`: exact SEC semantic registry, official occurrence extraction, fiscal-context normalization, deterministic reported Fact identity, version-aware selection.
- `cash_flow_shadow_service`: bounded period derivation, exact period/source pairing, deterministic PPE-only FCF, eligibility and audit serialization.
- `cash_flow_capital_efficiency_service`: explicit `REPORTED`, `DERIVED_PERIOD`, and `DERIVED_METRIC` types plus complete derivation metadata.

The production packet, AI prompt, renderer, fallback, Public Action, and database schema are unchanged. The core is internal shadow evidence only.
