# 05 Dual Market Source Coverage Policy

| Field | Value |
| --- | --- |
| candidate_snapshot | dict(3) |
| context_size | 4 |
| contract | fresh-issuer-post-pause-selection-policy-v1 |
| exclusion_registry_count | 101 |
| exclusion_registry_sha256 | bc573ed0f759888d1c1ace1b8725758d81b38533884f68be34c47749edb15a12 |
| exclusion_shrink_count | 0 |
| expected_invocations_per_run | 8 |
| expected_total_invocations | 32 |
| forbidden_selection_inputs | ["model output", "anticipated BUY HOLD SELL", "price trend", "valuation appearance", "desired stability"] |
| hotfix_after_first_real_output | 0 |
| market_policies | dict(2) |
| market_targets | {"kr": 12, "us": 4} |
| model | gpt-5.6-sol |
| model_calls | 0 |
| objective_replacement_reasons | ["identity validation failure", "unsupported source path", "duplicate canonical issuer", "source validation or sufficiency failure", "missing canonical packet"] |
| reasoning_effort | xhigh |
| retry_count | 0 |
| runs | ["first", "a", "b", "c"] |
| selection_rule | reuse verified expansion handoff order; remove canonical issuer keys in the reconciled 101-issuer exposure registry; accept the first source-eligible unique US4 and KR12 |
| selection_salt | 20260907-bounded-us-universe-expansion-issuer-reconciliation-v1 |
| selective_rerun | 0 |
| source_evaluation_performed | 0 |
| stages | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN_PRE_SOURCE_EVALUATION |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |

Machine proof: `proofs/05-dual-market-source-coverage-policy.json`.
