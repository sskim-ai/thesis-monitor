# 05 Dual Market Source Coverage Policy

| Field | Value |
| --- | --- |
| candidate_identities_sha256 | 81246812c3b537ab37199bd3a0a361d38522db4db2a3223a33785d2520d9d4ba |
| context_size | 4 |
| contract | fresh-issuer-risk-carried-selection-policy-v1 |
| exclusion_registry_count | 117 |
| exclusion_registry_sha256 | 7ffd6fed1125e88073efb867d3d5adc4024a0f22485e0c376151fbe5e3b6b437 |
| exclusion_shrink_count | 0 |
| expected_invocations_per_run | 8 |
| expected_total_invocations | 32 |
| market_policies | dict(2) |
| market_targets | {"kr": 12, "us": 4} |
| maximum_fresh_real_cohorts | 1 |
| model | gpt-5.6-sol |
| model_calls | 0 |
| objective_pre_model_replacement_only | True |
| reasoning_effort | xhigh |
| reference_snapshot_sha256 | c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a |
| replacement_after_model_start | 0 |
| retry_count | 0 |
| runs | ["first", "a", "b", "c"] |
| selection_rule | reuse the verified supported-reference order; remove all canonical issuer keys in the reconciled 117-issuer exposure registry; accept the first source-eligible unique US4 and KR12 |
| selection_salt | 20260907-bounded-us-universe-expansion-issuer-reconciliation-v1 |
| source_evaluation_performed | 0 |
| stages | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN_PRE_SOURCE_EVALUATION |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| verified_reference_snapshot | dict(4) |

Machine proof: `proofs/05-dual-market-source-coverage-policy.json`.
