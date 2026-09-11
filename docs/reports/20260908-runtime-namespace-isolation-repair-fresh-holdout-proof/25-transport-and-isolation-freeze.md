# 25-transport-and-isolation-freeze

| Field | Value |
| --- | --- |
| contract | "transport-and-isolation-freeze-v1" |
| model_context | {"context_groups": [["WYNN", "DOX", "NWS", "ASTI"], ["064850", "053270", "078860", "145720"], ["199730", "065510", "396470", "299900"], ["020180", "122310", "417200", "023910"]], "contract": "model-context-freeze-v1", "expected_invocations_per_run": 8, "expected_total_model_invocations": 32, "market_grouping": ["US4", "KR4", "KR4", "KR4"], "runs": ["first", "a", "b", "c"], "stage_order": ["DIRECTIONAL_CORE", "PRICE_TIMING"], "status": "FROZEN"} |
| transport | 17 keys; sha256=ba6ee7da85ee30479c52aec9f9283e3f4596f7b91f509d1a2a9cb3efb1862305 |
| namespace_preflight | 22 keys; sha256=24fba8c8fbbe00ea55caa5d6752df5b11a45817f4c71ad53b41fd4fb79954b0a |
| namespace_policy | "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE" |
| runtime_isolation_contract | "codex-model-context-runtime-isolation-v1" |
| ticker_specific_runtime_exception_count | 0 |
| status | "FROZEN" |
