# 23 Model Context Freeze

| Field | Value |
| --- | --- |
| context_groups | [["NU", "LNG", "TCI", "WMG"], ["043100", "025000", "131030", "372910"], ["130740", "045340", "006910", "288980"], ["023440", "064820", "001440", "073490"]] |
| contract | model-context-freeze-v1 |
| expected_invocations_per_run | 8 |
| expected_total_model_invocations | 32 |
| market_grouping | ["US4", "KR4", "KR4", "KR4"] |
| runs | ["first", "a", "b", "c"] |
| stage_order | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN |

Machine proof: `proofs/23-model-context-freeze.json`.
