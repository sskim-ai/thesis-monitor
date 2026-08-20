# Phase 9.0B Eligibility Results

Eligibility is contract-driven, not ticker-driven. The implementation reproduces the Phase 9.0A selective subset without status drift.

- KR non-financial: `PARTIAL/BLOCKED`, reason `period_context_unresolved`, canonical promotion `0`.
- Insurance/reinsurance: generic enterprise PPE CAPEX/FCF `NOT_APPLICABLE`.
- Foreign/ADR: issuer-level OCF/PPE CAPEX/FCF may be eligible; per-share/yield/market-cap arithmetic is absent.
- HUT: OCF remains eligible, PPE CAPEX and FCF remain blocked.
- SKHY: official registered OCF/PPE semantics remain unavailable, so all core metrics fail closed.
