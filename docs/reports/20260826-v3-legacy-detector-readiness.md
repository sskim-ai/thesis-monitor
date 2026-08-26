# Price Structure v3 Legacy Detector Readiness

- Instruction commit: `97b65fc1d258339563b54961a83acd997867e11e`
- Implementation: `3685aa991589ca0e7cc560104d4ebf8289e3f91d`
- Test run: `v3-legacy-detector-run:9e082343e51115738580`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-legacy-detector-render:a1b39f8917bfcc17ee81`
- Source run: `v3-current-run:ff97be1d62a9810dc315`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

## Gates

| Gate | Value |
| --- | --- |
| code_correctness | PASS |
| next_action | BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT |
| price_structure_v3_legacy_detector_repair | INTEGRATED_READY_NOT_ARMED |
| production_enablement_ready | YES |

## Controls

| Control | Value |
| --- | --- |
| current_sr_stored_rule_separation | PASS |
| hanwha_family_render | PASS |
| legacy_technical_token_policy | PASS |
| mu_stale_legacy_technical_suppression | PASS |
| protected_structural_fields | PASS |
| real_technical_token_detection | PASS |
| rxrx_company_header_preserved | PASS |
| rxrx_header_false_positive_root_cause | PASS |
| semantic_field_scoped_detection | PASS |
| sk_hynix_fib_range_render | PASS |
| tsla_sr_only_preserved | PASS |

## Decision

- `PRICE_STRUCTURE_V3_LEGACY_DETECTOR_REPAIR = INTEGRATED_READY_NOT_ARMED`
- `CODE_CORRECTNESS = PASS`
- `PRODUCTION_ENABLEMENT_READY = YES`
- `NEXT_ACTION = BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT`
- Open P0: `0`
- Open material P1: `0`
