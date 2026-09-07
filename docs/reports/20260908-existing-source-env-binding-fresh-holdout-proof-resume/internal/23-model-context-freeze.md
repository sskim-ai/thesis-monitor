# 23 Model Context Freeze

| Field | Value |
| --- | --- |
| context_groups | [["ACHR", "BNED", "CROX", "AWX"], ["095720", "000250", "389030", "009310"], ["042700", "002690", "103590", "025750"], ["084680", "377330", "024840", "360070"]] |
| contract | model-context-freeze-v1 |
| expected_invocations_per_run | 8 |
| expected_total_model_invocations | 32 |
| market_grouping | ["US4", "KR4", "KR4", "KR4"] |
| runs | ["first", "a", "b", "c"] |
| stage_order | ["DIRECTIONAL_CORE", "PRICE_TIMING"] |
| status | FROZEN |

Machine proof: `proofs/23-model-context-freeze.json`.
