# 05-runtime-namespace-contract

| Field | Value |
| --- | --- |
| contract | "codex-model-context-runtime-isolation-v1" |
| policy | "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE" |
| isolation_unit | "MODEL_CONTEXT" |
| required_unique_components | 3 rows; sha256=b40bb72eb356436aa436f3115c436f575246971f7fdc5b9dc3ba1f40ebd96034 |
| session_identity_separate | true |
| generation_identity_does_not_authorize_namespace_reuse | true |
| collision_action | "STOP_BEFORE_SPAWN" |
| status | "FROZEN" |
