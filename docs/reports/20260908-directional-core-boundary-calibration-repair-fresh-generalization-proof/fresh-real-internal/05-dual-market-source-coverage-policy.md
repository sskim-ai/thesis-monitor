# 05 Dual Market Source Coverage Policy

| Field | Value |
| --- | --- |
| calibration_freeze_seal_sha256 | 8214ee6e7fbc5fa29e5569dac5c01ab466744e4f343bab4a9d689231cdc6837d |
| candidate_identities_sha256 | f85788f13e60f8131f82074e6bf2331056ff3bdcffde30e3d1c7249adf12ec2c |
| context_size | 4 |
| contract | directional-calibration-fresh-selection-policy-v1 |
| exclusion_registry_count | 149 |
| exclusion_registry_sha256 | 8d9f121ff6fc4749ef5da5cecad4e8f731a991a051e771cdeb5512fe34b63f6b |
| exclusion_shrink_count | 0 |
| expected_invocations_per_run | 8 |
| expected_total_invocations | 32 |
| market_policies | {"kr": {"bounded_evaluation_limit": 24, "candidate_order": ["024110", "082800", "298060", "066900", "079370", "247540", "183300", "950200", "014820", "318060", "106240", "263750", "170900", "039980", "026960", "251970", "053580", "094170", "003010", "365900", "033250", "000390", "439580", "002070"]}, "us": {"bounded_evaluation_limit": 9, "candidate_order": ["YARW", "DMII", "ISOU", "SHOT", "PBLS", "DXYZ", "RMD", "VRAX", "MSFT"]}} |
| market_targets | {"kr": 12, "us": 4} |
| maximum_fresh_real_cohorts | 1 |
| model | gpt-5.6-sol |
| model_calls | 0 |
| newly_retired_issuer_count | 16 |
| objective_pre_model_replacement_only | True |
| outcome_based_selection | 0 |
| reasoning_effort | xhigh |
| reference_snapshot_sha256 | c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a |
| replacement_after_model_start | 0 |
| retry_count | 0 |
| runs | ["first", "a", "b", "c"] |
| selection_rule | reuse the verified supported-reference order; remove every canonical issuer key in the reconciled real-exposure registry; accept the first source-eligible unique US4 and KR12 |
| selection_salt | 20260907-bounded-us-universe-expansion-issuer-reconciliation-v1 |
| source_evaluation_performed | 0 |
| stages | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN_PRE_SOURCE_EVALUATION |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| verified_reference_snapshot | dict(4) |

Machine proof: `proofs/05-dual-market-source-coverage-policy.json`.
