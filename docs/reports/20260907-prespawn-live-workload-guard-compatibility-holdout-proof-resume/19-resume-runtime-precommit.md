# 19 Resume Runtime Precommit

| Field | Value |
| --- | --- |
| authorized_guard_adapter_hash | 6ec23b4f66348535ef47d31691cb9b9d55d1942dc076d391ad6e9f213374094c |
| batch_semantics | MODEL_CONTEXT_COUPLED |
| canonical_transport_hashes | {"ContinuationTransportAdapter": "05e8910008bec06fa592aeeb2df3c204b87a2a45a43b17607946b5c32355f9f1", "instrumented_runner": "10df1482dd937278ebe450ab82631ae3abf2bcb5b1b41a56bdabee1eea7ebbfd", "invoke_instrumented_codex": "e5fc8e00b99e5330b31502ad2d975970a4e0ce7da7aed5c9baa8ba9f8df94e13"} |
| context_grouping | [["NVDA", "JPM", "WMT", "BRK-B"], ["142210", "060900", "002680", "035420"], ["216050", "100700", "001530", "487580"], ["038870", "342870", "060230", "415380"]] |
| context_size | 4 |
| contract | prespawn-guard-resume-runtime-precommit-v1 |
| model | gpt-5.6-sol |
| ordered_cohort | ["NVDA", "JPM", "WMT", "BRK-B", "142210", "060900", "002680", "035420", "216050", "100700", "001530", "487580", "038870", "342870", "060230", "415380"] |
| packet_hashes | dict(16) |
| prompt_schema_freeze_sha256 | 9a895663474cddedb31185a967644d63886416008a3a86d2cc587c643afeebc4 |
| reasoning_effort | xhigh |
| runtime_generation_id | 20260907-prespawn-guard-resume-20260907T012700Z-1f19aa40aef6 |
| source_generation_id | 20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a |
| source_lock_sha256 | d4bd0b51d9cc543ebe03088047cce375db41d3d9a9f21c07d4fd5646bdf9b1ef |
| status | FROZEN |
| stop_rules | FIRST then gated A/B/C; no retry, split, or hotfix |
| timeout | 1800 |
| timeout_owner_count | 1 |

Machine proof: `proofs/19-resume-runtime-precommit.json`.