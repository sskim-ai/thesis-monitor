# 14-fresh-selection-policy

| Field | Value |
| --- | --- |
| candidate_identities_sha256 | "b547bc7a0940a37409a40dbf0aa6a31b26e2331432e1f253c25e8b71c9d1eed9" |
| context_size | 4 |
| contract | "runtime-isolation-repair-fresh-selection-policy-v1" |
| exclusion_registry_count | 133 |
| exclusion_registry_sha256 | "6e729964feaaea89e6e19c41db33797589c60932324907829aa38191421daf6b" |
| exclusion_shrink_count | 0 |
| expected_invocations_per_run | 8 |
| expected_total_invocations | 32 |
| market_policies | {"kr": {"bounded_evaluation_limit": 36, "candidate_order": ["024110", "064850", "053270", "078860", "145720", "199730", "065510", "396470", "082800", "299900", "020180", "122310", "298060", "417200", "023910", "066900", "079370", "247540", "183300", "950200", "014820", "318060", "106240", "263750", "170900", "039980", "026960", "251970", "053580", "094170", "003010", "365900", "033250", "000390", "439580", "002070"]}, "us": {"bounded_evaluation_limit": 13, "candidate_order": ["YARW", "DMII", "ISOU", "SHOT", "PBLS", "WYNN", "DOX", "DXYZ", "NWS", "ASTI", "RMD", "VRAX", "MSFT"]}} |
| market_targets | {"kr": 12, "us": 4} |
| maximum_fresh_real_cohorts | 1 |
| model | "gpt-5.6-sol" |
| model_calls | 0 |
| objective_pre_model_replacement_only | true |
| reasoning_effort | "xhigh" |
| reference_snapshot_sha256 | "c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a" |
| replacement_after_model_start | 0 |
| retry_count | 0 |
| runs | 4 rows; sha256=4386cdf7c84a0528583adf978e4bf4ee636a1879edd76e300cf5f35b85e5e63f |
| selection_rule | "reuse the verified supported-reference order; remove all canonical issuer keys in the reconciled 133-issuer exposure registry; accept the first source-eligible unique US4 and KR12" |
| selection_salt | "20260907-bounded-us-universe-expansion-issuer-reconciliation-v1" |
| source_evaluation_performed | 0 |
| stages | 2 rows; sha256=b1b6496fb51683e061edc3f71671473aec7102276d902fa10f85afd2e44ec55f |
| status | "FROZEN_PRE_SOURCE_EVALUATION" |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| verified_reference_snapshot | {"reference_request_counts": {"nasdaq_trader_nasdaqlisted": 1, "nasdaq_trader_otherlisted": 1, "opendart_corpcode": 1, "sec_company_tickers": 1}, "retrieved_at": "2026-09-07T03:04:36.018549+00:00", "retry_count": 0, "snapshots": [{"byte_size": 347010, "file": "nasdaqlisted.txt", "sha256": "491337a821469a830093aca740849358982960c46f0192537f5de898f59e9200"}, {"byte_size": 3601634, "file": "opendart-corp-code.zip", "sha256": "43903ff88932f2a1a2dc606b4169b1d3e6f6831019d2defa16e81e67c7ba0bdb"}, {"byte_size": 538961, "file": "otherlisted.txt", "sha256": "0e7be707f683443160a78e85139d8af18f786270c9ed82de8402d1d72538a319"}, {"byte_size": 796994, "file": "sec-company-tickers.json", "sha256": "f987a9fba01e1c1858ddcf0c032d77be301843860d7a0571efaa92ec3f938926"}]} |
| newly_retired_issuer_count | 16 |
