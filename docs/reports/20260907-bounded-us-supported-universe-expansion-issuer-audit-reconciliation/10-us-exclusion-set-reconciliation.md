# 10-us-exclusion-set-reconciliation

| Field | Value |
| --- | --- |
| raw_reference_row_count | 13188 |
| supported_security_count | 52 |
| supported_issuer_count | 52 |
| global_exclusion_issuer_count | 85 |
| within_universe_exclusion_issuer_count | 27 |
| unseen_supported_issuer_count | 25 |
| supported_security_ids | 52 rows; sha256=175ecb8b9b4d832ea19fa2062aea59d0f477622ede2c2769c1b1b1a5679831b4 |
| exclusion_reasons_by_issuer | 85 keys; sha256=1f70119bd9f55b94328ccb81927fdec5eaa8eb0d42925628af3cb69181ba833b |
| ambiguous_or_unresolved_reference_rows | 6033 rows; sha256=83869bc54743b6e5d1ad9495499c6f32c6dfd03361cb56dd0ec17e8a71418675 |
| invariants | {"issuer_lte_security": true, "unseen_equals_supported_minus_exclusions": true, "unseen_intersection_exclusions_empty": true, "unseen_lte_supported_issuer": true} |
| global_actual_output_exclusion_issuer_count | 65 |
| global_whole_cohort_retirement_issuer_count | 48 |
| global_canonical_exclusion_issuer_count | 85 |
| membership_path | evidence/membership/us-set-reconciliation.json |
| status | PASS |
