# 05 New Holdout Selection Policy

| Field | Value |
| --- | --- |
| candidate_universe | frozen canonical supported-security universe |
| contract | new-issuer-holdout-selection-policy-v1 |
| deterministic_ordering_rule | sector-stratified round robin ordered by SHA256(selection_salt\|market\|canonical_sector_or_industry\|ticker) |
| diversity_rule | canonical sector/industry strata round robin; unclassified remains one stratum |
| eligibility_criteria | ["supported common stock identity", "not previously model exposed", "not in retired partial cohort", "not in consumed regression cohort", "unique canonical issuer identity"] |
| exclusion_registry_sha256 | fcffb2ae8b00eba24c4890888871bcf7ec7c3e6a50bdbd0ec5a39ec9713dbdef |
| finalization_rule | first source-sufficient unique 4 US and 12 KR in precommitted order |
| model_calls | 0 |
| reserve_replacement_rule | ordered reserve only for objective pre-model identity/source/schema failure |
| selection_seed_or_rule | 20260907-new-issuer-holdout-selection-ownership-proof-v1 |
| selection_uses_expected_direction | 0 |
| selection_uses_model_output | 0 |
| source_sufficiency_criteria | frozen official enrichment and assembled packet directional eligibility |
| status | FROZEN |
| supported_universe_count | 2571 |
| target_cohort_size | 16 |
| target_market_mix | {"kr": 12, "us": 4} |

Machine proof: `proofs/05-new-holdout-selection-policy.json`.
