# 29 New Holdout Precommit

| Field | Value |
| --- | --- |
| batch_semantics | MODEL_CONTEXT_COUPLED |
| cohort_mutation_after_precommit | 0 |
| context_evidence_preservation_policy | exact-byte-output-stdout-stderr-receipt-prompt-schema-v1 |
| context_grouping | [["NVDA", "JPM", "WMT", "BRK-B"], ["142210", "060900", "002680", "035420"], ["216050", "100700", "001530", "487580"], ["038870", "342870", "060230", "415380"]] |
| context_grouping_mutation_after_precommit | 0 |
| context_size | 4 |
| contract | new-holdout-precommit-v1 |
| expanded_us_reserve_policy_hash | 693c6fd2c4c73300844883ad3f2b5959af1e16c43bab04f5ec1333fb9b4847a9 |
| market_mix | {"kr": 12, "us": 4} |
| model | gpt-5.6-sol |
| ordered_cohort | ["NVDA", "JPM", "WMT", "BRK-B", "142210", "060900", "002680", "035420", "216050", "100700", "001530", "487580", "038870", "342870", "060230", "415380"] |
| per_context_partial_semantic_audit_policy | direction-timing-ownership-early-stop-v1 |
| per_issuer_packet_hashes | dict(16) |
| prior_exposure_registry_hash | fcffb2ae8b00eba24c4890888871bcf7ec7c3e6a50bdbd0ec5a39ec9713dbdef |
| prompt_schema_lock_sha256 | 88461737d30111f9aff33f8c12b8060dfa0eb9c228913ebfb02b235a3c6a8b42 |
| reasoning_effort | xhigh |
| source_generation_id | 20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a |
| source_lock_sha256 | d4bd0b51d9cc543ebe03088047cce375db41d3d9a9f21c07d4fd5646bdf9b1ef |
| source_mutation_after_precommit | 0 |
| status | FROZEN |
| stop_rules | FIRST then gated A/B/C; no retry, split, or hotfix |
| timeout | 1800 |
| timeout_owner_count | 1 |
| transport_topology_identity | edcdaab1f4b8671e5db658809c83dbdce655f8508567e66ae10394479bbd7837 |

Machine proof: `proofs/29-new-holdout-precommit.json`.
