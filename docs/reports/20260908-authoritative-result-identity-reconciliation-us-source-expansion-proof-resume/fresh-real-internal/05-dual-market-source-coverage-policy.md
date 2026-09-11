# 05 Dual Market Source Coverage Policy

| Field | Value |
| --- | --- |
| candidate_identities_sha256 | 5357b84bf15caf1009b23bddc6cb28c236d09d03a1baae789949548b4910b891 |
| candidate_universe_sha256 | 09b8be8abf86c04c0da3e1941aa3b4cca9dcea5d0106bc8eb3ff658c8f809ed2 |
| contract | extended-us-source-attemptable-selection-policy-v1 |
| exclusion_registry_count | 149 |
| exclusion_registry_sha256 | 8d9f121ff6fc4749ef5da5cecad4e8f731a991a051e771cdeb5512fe34b63f6b |
| market_policies | dict(2) |
| market_targets | {"kr": 12, "us": 4} |
| model_calls | 0 |
| ordering_method | SHA256(selection_salt\|market\|canonical_issuer_key\|canonical_security_id), one deterministic representative per issuer |
| price_contract | READY_OR_UNAVAILABLE_SAFE_WITHOUT_FABRICATION |
| reference_snapshot_sha256 | 2ad88b455499f2fe104d155fa26a829a1b8aec4393b907c11ae8807cc6be4a14 |
| selection_rule | remove all 149 exposed canonical issuers; preserve identity/security-class gates; admit route-supported or route-candidate issuers to the official fundamental source test; accept first source-eligible US4 and KR12 in the frozen order |
| selection_salt | 20260907-bounded-us-universe-expansion-issuer-reconciliation-v1 |
| source_evaluation_performed | 0 |
| source_sufficiency_mutation | 0 |
| status | FROZEN_PRE_SOURCE_EVALUATION |
| ticker_specific_exception_count | 0 |
| verified_reference_snapshot | dict(4) |

Machine proof: `proofs/05-dual-market-source-coverage-policy.json`.
