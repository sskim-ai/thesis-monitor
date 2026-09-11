# 08-full-path-32-context-namespace-preflight

| Field | Value |
| --- | --- |
| contract | "full-path-namespace-isolation-preflight-v1" |
| namespace_policy | "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE" |
| runtime_isolation_contract | "codex-model-context-runtime-isolation-v1" |
| planned_context_count | 32 |
| unique_invocation_count | 32 |
| unique_runtime_namespace_count | 32 |
| unique_working_directory_count | 32 |
| session_uniqueness | "NOT_MEASURED_PRESPAWN" |
| model_call_count | 0 |
| collision_negative_proof | "PASS_STOPPED_BEFORE_SPAWN" |
| resumed_generation_namespace_isolation | "PASS" |
| input_hashes_before | {"experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02/prompt.txt": "d3aecb57455019be1e041f15575c4a9635eb7bec522ee2bfc4462b761bba59b2", "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02/schema.json": "c597a60a08a8770125769bba12f7da4450c2b141a678777915b0aae587a372c1", "experiment/packets/095720.json": "8719c17f0790aa635e545e801b3e8c06c1900df588325db25b122f305dd1a02a"} |
| input_hashes_after | {"experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02/prompt.txt": "d3aecb57455019be1e041f15575c4a9635eb7bec522ee2bfc4462b761bba59b2", "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02/schema.json": "c597a60a08a8770125769bba12f7da4450c2b141a678777915b0aae587a372c1", "experiment/packets/095720.json": "8719c17f0790aa635e545e801b3e8c06c1900df588325db25b122f305dd1a02a"} |
| input_byte_mutation_count | 0 |
| model | "gpt-5.6-sol" |
| reasoning_effort | "xhigh" |
| timeout_seconds | 1800 |
| timeout_owner_count | 1 |
| subjects_per_context | 4 |
| rows | 32 rows; sha256=ff6278d51a95132ca86107c43e11ff7b484cc391361a8fbb716aa4e7b587dde0 |
| full_path_namespace_isolation_preflight | "PASS" |
| status | "PASS" |
