# 05 Dual Market Source Coverage Policy

| Field | Value |
| --- | --- |
| candidate_identities_sha256 | b547bc7a0940a37409a40dbf0aa6a31b26e2331432e1f253c25e8b71c9d1eed9 |
| context_size | 4 |
| contract | runtime-isolation-repair-fresh-selection-policy-v1 |
| exclusion_registry_count | 133 |
| exclusion_registry_sha256 | 6e729964feaaea89e6e19c41db33797589c60932324907829aa38191421daf6b |
| exclusion_shrink_count | 0 |
| expected_invocations_per_run | 8 |
| expected_total_invocations | 32 |
| market_policies | {"kr": {"bounded_evaluation_limit": 36, "candidate_order": ["024110", "064850", "053270", "078860", "145720", "199730", "065510", "396470", "082800", "299900", "020180", "122310", "298060", "417200", "023910", "066900", "079370", "247540", "183300", "950200", "014820", "318060", "106240", "263750", "170900", "039980", "026960", "251970", "053580", "094170", "003010", "365900", "033250", "000390", "439580", "002070"]}, "us": {"bounded_evaluation_limit": 13, "candidate_order": ["YARW", "DMII", "ISOU", "SHOT", "PBLS", "WYNN", "DOX", "DXYZ", "NWS", "ASTI", "RMD", "VRAX", "MSFT"]}} |
| market_targets | {"kr": 12, "us": 4} |
| maximum_fresh_real_cohorts | 1 |
| model | gpt-5.6-sol |
| model_calls | 0 |
| newly_retired_issuer_count | 16 |
| objective_pre_model_replacement_only | True |
| reasoning_effort | xhigh |
| reference_snapshot_sha256 | c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a |
| replacement_after_model_start | 0 |
| retry_count | 0 |
| runs | ["first", "a", "b", "c"] |
| selection_rule | reuse the verified supported-reference order; remove all canonical issuer keys in the reconciled 133-issuer exposure registry; accept the first source-eligible unique US4 and KR12 |
| selection_salt | 20260907-bounded-us-universe-expansion-issuer-reconciliation-v1 |
| source_evaluation_performed | 0 |
| stages | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN_PRE_SOURCE_EVALUATION |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| verified_reference_snapshot | dict(4) |

Machine proof: `proofs/05-dual-market-source-coverage-policy.json`.
