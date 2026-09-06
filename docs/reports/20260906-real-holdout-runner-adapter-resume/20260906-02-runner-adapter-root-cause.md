# 02 Runner Adapter Root Cause

| Field | Value |
| --- | --- |
| adapter_callable_location | scripts/model_transport_revalidation_ownership_continuation.py:ContinuationTransportAdapter.invoke |
| canonical_adapter_parameters | ["prompt", "output", "log", "schema", "cwd", "timeout", "state_namespace", "invocation_id", "stage", "batch_id", "subject_count"] |
| codex_bin_classification | RUNNER_OWNED_LEGACY_TRANSPORT_CONFIGURATION |
| contract | runner-adapter-root-cause-v1 |
| defect_location | REAL_HOLDOUT_RUNNER_ARGUMENT_BRIDGE |
| missing_required_parameters | [] |
| passed_canary_invocation_shape | DIRECT_CANONICAL_ADAPTER_INVOKE |
| pre_repair_bind_error | got an unexpected keyword argument 'codex_bin' |
| result | RUNNER_ADAPTER_BINDING_ROOT_CAUSE_CONFIRMED |
| runner_call_site_location | scripts/directional_core_price_timing_holdout.py:execute_two_stage_run |
| runner_supplied_parameters | ["codex_bin", "prompt", "output", "log", "schema", "cwd", "timeout", "state_namespace"] |
| status | PASS |
| unexpected_parameters | ["codex_bin"] |

Machine proof: `proofs/02-runner-adapter-root-cause.json`.
