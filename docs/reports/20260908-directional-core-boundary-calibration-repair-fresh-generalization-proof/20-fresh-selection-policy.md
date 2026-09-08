# 20-fresh-selection-policy

| Field | Value |
| --- | --- |
| calibration_freeze_seal_sha256 | "8214ee6e7fbc5fa29e5569dac5c01ab466744e4f343bab4a9d689231cdc6837d" |
| candidate_identities_sha256 | "f85788f13e60f8131f82074e6bf2331056ff3bdcffde30e3d1c7249adf12ec2c" |
| context_size | 4 |
| contract | "directional-calibration-fresh-selection-policy-v1" |
| exclusion_registry_count | 149 |
| exclusion_registry_sha256 | "8d9f121ff6fc4749ef5da5cecad4e8f731a991a051e771cdeb5512fe34b63f6b" |
| exclusion_shrink_count | 0 |
| expected_invocations_per_run | 8 |
| expected_total_invocations | 32 |
| market_policies | {"kr": {"bounded_evaluation_limit": 24, "candidate_order": ["024110", "082800", "298060", "066900", "079370", "247540", "183300", "950200", "014820", "318060", "106240", "263750", "170900", "039980", "026960", "251970", "053580", "094170", "003010", "365900", "033250", "000390", "439580", "002070"]}, "us": {"bounded_evaluation_limit": 9, "candidate_order": ["YARW", "DMII", "ISOU", "SHOT", "PBLS", "DXYZ", "RMD", "VRAX", "MSFT"]}} |
| market_targets | {"kr": 12, "us": 4} |
| maximum_fresh_real_cohorts | 1 |
| model | "gpt-5.6-sol" |
| model_calls | 0 |
| newly_retired_issuer_count | 16 |
| objective_pre_model_replacement_only | true |
| outcome_based_selection | 0 |
| reasoning_effort | "xhigh" |
| reference_snapshot_sha256 | "c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a" |
| replacement_after_model_start | 0 |
| retry_count | 0 |
| runs | 4 rows; sha256=4386cdf7c84a0528583adf978e4bf4ee636a1879edd76e300cf5f35b85e5e63f |
| selection_rule | "reuse the verified supported-reference order; remove every canonical issuer key in the reconciled real-exposure registry; accept the first source-eligible unique US4 and KR12" |
| selection_salt | "20260907-bounded-us-universe-expansion-issuer-reconciliation-v1" |
| source_evaluation_performed | 0 |
| stages | 2 rows; sha256=b1b6496fb51683e061edc3f71671473aec7102276d902fa10f85afd2e44ec55f |
| status | "FROZEN_PRE_SOURCE_EVALUATION" |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| verified_reference_snapshot | {"reference_request_counts": {"nasdaq_trader_nasdaqlisted": 1, "nasdaq_trader_otherlisted": 1, "opendart_corpcode": 1, "sec_company_tickers": 1}, "retrieved_at": "2026-09-07T03:04:36.018549+00:00", "retry_count": 0, "snapshots": [{"byte_size": 347010, "file": "nasdaqlisted.txt", "sha256": "491337a821469a830093aca740849358982960c46f0192537f5de898f59e9200"}, {"byte_size": 3601634, "file": "opendart-corp-code.zip", "sha256": "43903ff88932f2a1a2dc606b4169b1d3e6f6831019d2defa16e81e67c7ba0bdb"}, {"byte_size": 538961, "file": "otherlisted.txt", "sha256": "0e7be707f683443160a78e85139d8af18f786270c9ed82de8402d1d72538a319"}, {"byte_size": 796994, "file": "sec-company-tickers.json", "sha256": "f987a9fba01e1c1858ddcf0c032d77be301843860d7a0571efaa92ec3f938926"}]} |
