# 20 New Holdout Precommit

| Field | Value |
| --- | --- |
| batch_semantics | MODEL_CONTEXT_COUPLED |
| batch_split | 0 |
| context_groups | [["NU", "LNG", "TCI", "WMG"], ["043100", "025000", "131030", "372910"], ["130740", "045340", "006910", "288980"], ["023440", "064820", "001440", "073490"]] |
| contract | fresh-issuer-post-pause-execution-precommit-v1 |
| expected_invocations_per_run | 8 |
| expected_total_model_invocations | 32 |
| hotfix_after_first_output | 0 |
| implementation_commit | a5a485748e08388c3ddfca61559fd5ab6ad56f25 |
| implementation_tree | 1857548c53b1ec08301814c4e23e56104408800c |
| market_by_ticker | {"001440": "kr", "006910": "kr", "023440": "kr", "025000": "kr", "043100": "kr", "045340": "kr", "064820": "kr", "073490": "kr", "130740": "kr", "131030": "kr", "288980": "kr", "372910": "kr", "LNG": "us", "NU": "us", "TCI": "us", "WMG": "us"} |
| model | gpt-5.6-sol |
| model_free_preflight | dict(19) |
| model_retry_count | 0 |
| ordered_cohort | ["NU", "LNG", "TCI", "WMG", "043100", "025000", "131030", "372910", "130740", "045340", "006910", "288980", "023440", "064820", "001440", "073490"] |
| packet_sha256 | dict(16) |
| pre_first_frozen_at | 2026-09-07T09:27:46.934105+00:00 |
| prompt_schema_lock_sha256 | 3ae822a2d21a771a903096ec44050b42dd9844c33fa935215f987f33a0be89cb |
| reasoning_effort | xhigh |
| runs | ["first", "a", "b", "c"] |
| runtime_generation_id | 20260907-fresh-issuer-proof-20260907T090500Z-2fc43e587bfe |
| selective_rerun | 0 |
| source_generation_id | 20260907-fresh-issuer-source-20260907T090500Z-2b1e0d043243 |
| source_lock_sha256 | eee5764bb11218ab080a65ac6179e7b5d6440be11753ce34f8cd292ffc2504ef |
| stages | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN |
| subjects_per_context | 4 |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |

Machine proof: `proofs/20-new-holdout-precommit.json`.
