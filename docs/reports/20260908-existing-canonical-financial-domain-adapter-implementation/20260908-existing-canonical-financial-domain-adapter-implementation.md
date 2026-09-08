# M6 Existing Canonical Financial Domain Adapter Implementation

## Result

- Status: `M6_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `29fb88be197c50b0da0eead886c89f27e823d3b4`
- Work-instruction commit: `35da4e7f1dd57194c3f5f6532ff91a13994f2448`
- Implementation commit: `bcad2ae16836a12ff208a110856575931bfbeb08`
- Adapter contract: `existing-canonical-financial-domain-adapter-v1`

## Implementation

The shared packet builder now attaches optional typed `financial_context` only to existing
`canonical_cash_flow_fact` evidence. M6 supports compatible prior-year comparison lineage,
direct reported OCF, direct reported PPE-only cash outflow, and deterministic
`ocf_less_ppe_capex` context. It adds no SEC/OpenDART/provider mappings.

The preserved Phase 9 archive contains 606 canonical rows.
The adapter emitted 330 contexts: 122 OCF, 104 PPE, and
104 OCF-less-PPE contexts. It attached 130 compatible
prior-year comparison lineages. It suppressed 276 rows whose
derived-period lineage projection is incomplete.

## Safety

- Compact AI context changed fixtures: `0 / 4`
- Directional prompt changes: `0`
- Price-Timing prompt changes: `0`
- Source-sufficiency semantic changes: `0`
- Daily Delta semantic changes: `0`
- Model/provider calls: `0`
- Production mutations/sends/deployments: `0`
- Monitoring paths observed paused: `8 / 8`; mutations: `0`

KR ambiguous-period OCF/PPE remains fail-closed. Growth-versus-maintenance capex remains
unknown, no FX or ad hoc scale conversion is performed, and OCF less PPE is not labeled as
canonical or management-defined free cash flow.

## Validation

- Focused: `482 passed`
- Full repository: `2887 passed`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Positive fixtures: `12 / 12`
- Negative fixtures: `23 / 23` rejected or suppressed
- Historical packet parse/hash compatibility: `14 / 14`

## Next Scope

`ADDITIONAL_FINANCIAL_SOURCE_MAPPING_SUBPACKAGES`

Prioritize complete prior-comparable and derived-period lineage projection, KR OpenDART
duration context, the bounded HUT/SKHY gaps, then debt/liquidity, working capital, and
non-operating effects as separate packages. Directional specificity remains inactive.
