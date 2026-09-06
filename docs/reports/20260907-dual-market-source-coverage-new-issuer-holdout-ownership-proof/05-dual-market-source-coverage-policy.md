# 05 Dual Market Source Coverage Policy

| Field | Value |
| --- | --- |
| MARKET_FAILURE_DOES_NOT_ABORT_OTHER_MARKET_DIAGNOSTIC | 1 |
| candidate_universe | frozen canonical supported-security universe |
| contract | dual-market-source-coverage-policy-v1 |
| deterministic_ordering_rule | sector-stratified round robin ordered by SHA256(selection_salt\|market\|canonical_sector_or_industry\|ticker) |
| diversity_rule | canonical sector/industry strata round robin; unclassified remains one stratum |
| exclusion_registry_sha256 | fcffb2ae8b00eba24c4890888871bcf7ec7c3e6a50bdbd0ec5a39ec9713dbdef |
| finalization_rule | first source-sufficient unique 4 US and 12 KR in precommitted order |
| market_policies | dict(2) |
| model_calls | 0 |
| objective_eligibility_rules | ["supported common stock identity", "not previously model exposed", "not in retired partial cohort", "not in consumed regression cohort", "unique canonical issuer identity"] |
| replacement_forbidden_reasons | ["valuation appearance", "price trend", "expected direction or ownership result", "transport result"] |
| replacement_rules | ["ordered reserve only", "identity validation failure", "unsupported market or duplicate issuer", "source insufficiency or hard source validation failure", "missing required evidence packet"] |
| selection_seed_or_rule | 20260907-new-issuer-holdout-selection-ownership-proof-v1 |
| selection_uses_expected_direction | 0 |
| selection_uses_model_output | 0 |
| source_sufficiency_rules | ["frozen official enrichment directional eligibility", "assembled canonical packet directional eligibility", "required identity, fundamental, valuation, and price validation gates"] |
| status | FROZEN |
| stop_condition | complete both bounded market diagnostics; freeze only when both targets pass |
| supported_universe_count | 2571 |
| target_cohort_size | 16 |
| target_market_mix | {"kr": 12, "us": 4} |

Machine proof: `proofs/05-dual-market-source-coverage-policy.json`.
