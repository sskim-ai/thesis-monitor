# 04 Prespawn Guard Code Path Audit

| Field | Value |
| --- | --- |
| active_natural_job_decision | pause while count > 0 |
| contract | prespawn-guard-code-path-audit-v1 |
| exception_mask_path | invoke_model_context -> preserve_context -> transport_receipt_missing |
| guard_constructor | us_price_context_gate_supported_universe_holdout_resume -> bounded runner execute -> LiveWorkloadGuard |
| prespawn_check | GuardedTransportAdapter.invoke -> wait_until_clear |
| previous_process_observation_command | ps -axo command= |
| protected_window_independent | True |
| receipt_expected_boundary | instrumented subprocess invocation created |
| root_cause_result | PRESPAWN_GUARD_ROOT_CAUSE_CONFIRMED |
| running_model_process_decision | pause while count > 0 |
| spawn_boundary | ContinuationTransportAdapter invoke after guard returns |
| status | PASS |

Machine proof: `proofs/04-prespawn-guard-code-path-audit.json`.