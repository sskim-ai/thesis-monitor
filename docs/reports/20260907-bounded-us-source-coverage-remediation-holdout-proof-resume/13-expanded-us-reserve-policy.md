# 13 Expanded Us Reserve Policy

| Field | Value |
| --- | --- |
| bounded_additional_reserve_limit | 20 |
| canonical_supported_unexposed_us_count | 5 |
| contract | expanded-us-reserve-policy-v1 |
| exclusion_registry_hash | fcffb2ae8b00eba24c4890888871bcf7ec7c3e6a50bdbd0ec5a39ec9713dbdef |
| original_ranks | ["NVDA", "JPM", "WMT", "BRK-B", "MSFT"] |
| original_ranks_excluded_from_extension | ["NVDA", "JPM", "WMT", "BRK-B", "MSFT"] |
| reserve_extension_count | 0 |
| reserve_order | [] |
| selection_rule | sector-stratified round robin ordered by SHA256(selection_salt\|market\|canonical_sector_or_industry\|ticker) |
| selection_rule_hash | a1dec0f291e2680ae414f9b6ca2488048cf2f75fb51151b50bd0a296d6af48b0 |
| selection_salt | 20260907-new-issuer-holdout-selection-ownership-proof-v1 |
| selection_uses_model_output | 0 |
| selection_uses_source_outcome | 0 |
| status | FROZEN |
| zero_extension_reason | CANONICAL_SUPPORTED_UNEXPOSED_UNIVERSE_EXHAUSTED |

Machine proof: `proofs/13-expanded-us-reserve-policy.json`.
