# Batch Semantics Audit

| Gate | Value |
| --- | --- |
| batch_semantics | MODEL_CONTEXT_COUPLED |
| batch_size | 4 |
| code_path | batches(cohort) -> one _core_prompt(contexts[4]) -> one model output |
| contract | model-batch-semantics-audit-v1 |
| per_subject_independent_prompt | 0 |
| status | PASS |

Machine proof: `20260906-model-transport-continuation-proofs/batch-semantics-audit.json`.
