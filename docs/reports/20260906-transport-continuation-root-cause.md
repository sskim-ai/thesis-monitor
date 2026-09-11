# Transport Continuation Root Cause

| Gate | Value |
| --- | --- |
| contract | transport-continuation-root-cause-v1 |
| continuation_observation | CLI process smoke started, emitted valid structured output, and exited; architecture-scale transport remained unmeasured because the next synthetic fixture failed local schema validation before invocation |
| final_classification | UNKNOWN_MODEL_TRANSPORT |
| initial_blocker_class | MODEL_TRANSPORT_OR_INVOCATION_TIMEOUT |
| prior_cleanup_observability | INSUFFICIENT |
| prior_model_output_documents | 0 |
| prior_output_parse_started | 0 |
| prior_process_exit_before_timeout | 0 |
| prior_process_spawned | 1 |
| prior_prompt_echo_observed | 1 |
| prior_request_accepted_observability | UNAVAILABLE |
| prior_stderr_began | 1 |

The prior 1,800-second stop produced no model document, so it did not measure ownership semantics. This continuation changes only process lifecycle observability and cleanup.

Machine proof: `20260906-model-transport-continuation-proofs/transport-continuation-root-cause.json`.
