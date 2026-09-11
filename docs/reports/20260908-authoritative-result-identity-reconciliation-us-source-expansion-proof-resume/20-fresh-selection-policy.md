# 20-fresh-selection-policy

| Field | Value |
| --- | --- |
| candidate_identities_sha256 | "5357b84bf15caf1009b23bddc6cb28c236d09d03a1baae789949548b4910b891" |
| candidate_universe_sha256 | "09b8be8abf86c04c0da3e1941aa3b4cca9dcea5d0106bc8eb3ff658c8f809ed2" |
| contract | "extended-us-source-attemptable-selection-policy-v1" |
| exclusion_registry_count | 149 |
| exclusion_registry_sha256 | "8d9f121ff6fc4749ef5da5cecad4e8f731a991a051e771cdeb5512fe34b63f6b" |
| market_policies | {"kr": {"bounded_evaluation_limit": 24, "candidate_order": ["024110", "082800", "298060", "066900", "079370", "247540", "183300", "950200", "014820", "318060", "106240", "263750", "170900", "039980", "026960", "251970", "053580", "094170", "003010", "365900", "033250", "000390", "439580", "002070"]}, "us": {"bounded_evaluation_limit": 48, "candidate_order": ["YARW", "DMII", "ISOU", "SHOT", "PBLS", "DXYZ", "RMD", "VRAX", "NEON", "AA", "TDW", "SAMG", "KLAC", "SFIX", "RPID", "TTEK", "AMCR", "FVRR", "AHMA", "AII", "MH", "LPTH", "STKH", "ANPA", "SMWB", "AMPY", "APMC", "CMC", "VINP", "IX", "BBY", "SMID", "ALGS", "HCWC", "KLTR", "NABL", "CMRC", "UGI", "GYGY", "ACET", "MBIO", "ATTO", "BEEP", "FSEA", "BFLY", "HPK", "MOB", "COLM"], "full_source_attemptable_issuer_count": 5059}} |
| market_targets | {"kr": 12, "us": 4} |
| model_calls | 0 |
| ordering_method | "SHA256(selection_salt/market/canonical_issuer_key/canonical_security_id), one deterministic representative per issuer" |
| price_contract | "READY_OR_UNAVAILABLE_SAFE_WITHOUT_FABRICATION" |
| reference_snapshot_sha256 | "2ad88b455499f2fe104d155fa26a829a1b8aec4393b907c11ae8807cc6be4a14" |
| selection_rule | "remove all 149 exposed canonical issuers; preserve identity/security-class gates; admit route-supported or route-candidate issuers to the official fundamental source test; accept first source-eligible US4 and KR12 in the frozen order" |
| selection_salt | "20260907-bounded-us-universe-expansion-issuer-reconciliation-v1" |
| source_evaluation_performed | 0 |
| source_sufficiency_mutation | 0 |
| status | "FROZEN_PRE_SOURCE_EVALUATION" |
| ticker_specific_exception_count | 0 |
| verified_reference_snapshot | {"reference_request_counts": {"nasdaq_trader_nasdaqlisted": 1, "nasdaq_trader_otherlisted": 1, "opendart_corpcode": 1, "sec_company_tickers": 1}, "retrieved_at": "2026-09-07T03:04:36.018549+00:00", "retry_count": 0, "snapshots": [{"byte_size": 347010, "file": "nasdaqlisted.txt", "sha256": "491337a821469a830093aca740849358982960c46f0192537f5de898f59e9200"}, {"byte_size": 3601634, "file": "opendart-corp-code.zip", "sha256": "43903ff88932f2a1a2dc606b4169b1d3e6f6831019d2defa16e81e67c7ba0bdb"}, {"byte_size": 538961, "file": "otherlisted.txt", "sha256": "0e7be707f683443160a78e85139d8af18f786270c9ed82de8402d1d72538a319"}, {"byte_size": 796994, "file": "sec-company-tickers.json", "sha256": "f987a9fba01e1c1858ddcf0c032d77be301843860d7a0571efaa92ec3f938926"}]} |
