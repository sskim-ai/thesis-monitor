# New Issuer Holdout Selection Policy

| Gate | Value |
| --- | --- |
| candidate_audit_size | 64 |
| contract | new-issuer-holdout-selection-policy-v1 |
| expected_available_us_after_exclusion | 7 |
| issuer_exclusion | ticker plus normalized issuer name and known share-class aliases |
| known_share_class_aliases | {"Alphabet": ["GOOG", "GOOGL"]} |
| maximum | 20 |
| minimum | 12 |
| preferred_per_market | 8 |
| selection_salt | directional-core-price-timing-ownership-new-holdout-v1 |
| selection_uses_expected_decision | 0 |
| supported_universe | frozen canonical supported-security universe |
| target_count | 16 |

Machine proof: `20260906-direction-timing-ownership-proofs/new-issuer-holdout-selection-policy.json`.
