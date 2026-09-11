# 23-fresh-proof-precommit

| Field | Value |
| --- | --- |
| acceptance_protocol | {"core_partial_audit_sha256": "beb7ce7950ccd59f25970c143612d88ffc1f06c02658f2ac2c196c70eaad79a5", "core_stability_sha256": "dac6ab2a09ff00c49f912028ab8e00788fc2948a8a86c2ad3b47cc575b6422a8", "message_quality_sha256": "1b8e944512b9fd2dda0669f135b72181ae7b6b5f41af136bba2f91ebc6499d6f", "quality_gate_role": "ADVISORY_NOT_INCLUDED_IN_RUN_STATUS_OR_PROGRESS_SEQUENCE", "run_gate_documents_sha256": "d311905e8648bad3f9f83d960ef99ec45cbd9be2f3b4fe6b5f3da93cc50d79d8", "status_mapping": {"advisory_message_quality_failure": "REPORT_WITHOUT_PROGRESS_BLOCK", "four_valid_runs_required_for_stability": true, "hard_context_or_run_failure": "STOP_REMAINING_CALLS"}, "timing_partial_audit_sha256": "a76cec0729f33aa64ac84820e7b843b631f4879b01adf93af1afb6fab516fab3", "timing_stability_sha256": "d81eb366e6be40653937e65af64cf86f0fcf95458b14e3e0be8a1aeff1b99666"} |
| acceptance_protocol_sha256 | "939459e6efc6b21cb8b14f2c256e6e56364724ae1f76a2a5cdb518ce66a77c17" |
| batch_semantics | "MODEL_CONTEXT_COUPLED" |
| batch_split | 0 |
| capacity_or_health_model_smoke_calls | 0 |
| carried_runtime_risk | "RUNTIME_NAMESPACE_ISOLATION_REPAIRED_AND_PREFLIGHT_PROVEN" |
| context_groups | 4 rows; sha256=6370d48953cfabe33cab79ab4765b2bbfc450111c5db3ce321bdb4a124d386bd |
| contract | "runtime-isolation-repair-fresh-proof-precommit-v1" |
| exclusion_registry_count | 133 |
| exclusion_registry_sha256 | "6e729964feaaea89e6e19c41db33797589c60932324907829aa38191421daf6b" |
| expected_invocations_per_run | 8 |
| expected_total_model_invocations | 32 |
| failed_call_replacements | 0 |
| frozen_evaluation_cutoff | "2026-09-07T18:16:51+00:00" |
| historical_cohort_reuse_allowed | 0 |
| historical_retired_cohort | 16 rows; sha256=9bc48f1da24cafac6d5fc408fc30518a99b805c71513f8960bbfe63d00a99902 |
| hotfix_after_first_output | 0 |
| implementation_commit | "0379cd604a0c305147585835e399f40e1e8d5933" |
| implementation_tree | "b1ec2985063bd8299feef071a09fe8c231127c7c" |
| market_by_ticker | 16 keys; sha256=858744487fa28ee73cfc0e57bda16114ea82d98b9d77a7f658359d0ca90f2a5b |
| maximum_fresh_real_cohorts | 1 |
| maximum_real_model_subprocess_attempts | 32 |
| model | "gpt-5.6-sol" |
| model_free_preflight | 19 keys; sha256=4108b0736a2d5a2a83d0be4c7beb21bda3bb060390aeb4920712d4a8db3b6399 |
| model_retry_count | 0 |
| namespace_collision_action | "STOP_BEFORE_SPAWN" |
| namespace_isolation_implementation_identity | {"proof_orchestrator_sha256": "861f2b4ad03f70ebb17e020a5177409e36d3520ac3c7ebb7615d7b1926eca645", "runtime_state_service_sha256": "68452f34293a9c1bbb208a3ee82d3b4aacfa6705e18f4e99d10cfded44bc08d7", "transport_adapter_sha256": "cfc9e4843956349601392ee1e4c5f0fe4ef937f251c657914f6e0d30c72ddcbb"} |
| namespace_isolation_preflight_sha256 | "24fba8c8fbbe00ea55caa5d6752df5b11a45817f4c71ad53b41fd4fb79954b0a" |
| namespace_policy | "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE" |
| new_fictional_model_calls | 0 |
| ordered_cohort | 16 rows; sha256=a3396c27ff908484c263e6322f2b5c05030da10b31fb7307f717efd9519862d2 |
| packet_sha256 | 16 keys; sha256=9d845f32490a4a5b3b2a72bf39ea468f293c884755d5324f312caa47bb9618ee |
| pause_observation | {"auto_resume_executed": 0, "codex_automations": [{"active": false, "name": "Thesis Monitor AI Review US Primary", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review US Backup", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review KR Primary", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review KR Backup", "state": "PAUSED"}], "contract": "current-monitoring-pause-observation-v1", "launch_agents": [{"active": false, "name": "com.seungsoo.thesis-monitor.daily", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.kr-close", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.ai-review-fallback", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.ai-review-delivery-retry", "state": "PAUSED_DISABLED_UNLOADED"}], "observation_only": true, "observed_at": "2026-09-07T18:36:55.155764+00:00", "observed_scheduler_object_count": 8, "scheduler_mutation_count": 0, "status": "VERIFIED_PAUSED_COMPLETE", "unexpected_active_paths": []} |
| pre_first_frozen_at | "2026-09-07T18:36:55.121198+00:00" |
| prespawn_isolation_assertions | 3 rows; sha256=309ad261a38b12a6986d5e2dbf5cf0042646c9b8241141b7059aa2e1e873777c |
| process_observation | {"active_natural_job_count": 0, "model_execution_pids": [], "natural_job_rows": [], "observation_capabilities": {"model_execution_observable": true, "natural_process_observable": true, "paused_schedule_registry_observable": true, "protected_window_observable": true, "scheduler_mutation": false}, "pause_observed_at": "2026-09-07T18:36:55.186402+00:00", "paused_schedule_count": 8, "running_model_process_count": 0, "unexpected_active_monitoring_paths": [], "workload_observation_backend": "PAUSE_REGISTRY_PLUS_PS_NATURAL_MARKERS_PLUS_LSOF_CODEX_RUNTIME_STATE"} |
| prompt_schema_lock_sha256 | "091178da8d5b23bf88d45d88e96ddf154a2752d82a9050f8bf393ef57d74e307" |
| reasoning_effort | "xhigh" |
| reconnect_path_exercised | "NOT_OBSERVED" |
| reference_snapshot_sha256 | "c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a" |
| replacement_cohort_attempts | 0 |
| reserve_order_sha256 | "206a02a269ad45d5ac430272ed2b25682f12e6968d41b659b99cd7fa049d9057" |
| run_order | 4 rows; sha256=4386cdf7c84a0528583adf978e4bf4ee636a1879edd76e300cf5f35b85e5e63f |
| runs | 4 rows; sha256=4386cdf7c84a0528583adf978e4bf4ee636a1879edd76e300cf5f35b85e5e63f |
| runtime_generation_id | "20260907-fresh-issuer-proof-20260907T181651Z-695d9f8eaacc" |
| runtime_isolation_contract | "codex-model-context-runtime-isolation-v1" |
| runtime_isolation_evidence_per_context | "runtime-isolation-preflight.json" |
| runtime_reliability_status | "NOT_ESTABLISHED" |
| selection_policy_sha256 | "c6a7c4609690a228f37d8f73d7b97c4915489894e20eb908a4694929a364f6f1" |
| selective_rerun | 0 |
| signed_in_cli_identity | {"checks": {"sha256": true, "version": true}, "path": "/Applications/ChatGPT.app/Contents/Resources/codex", "sha256": "7645c3caf5607e4528eb3a15b12496c284c2a918939aed34e863c760c1b421e7", "status": "PASS", "version": "codex-cli 0.148.0-alpha.15"} |
| source_generation_id | "20260907-fresh-issuer-source-20260907T181651Z-c5cb0cee45e8" |
| source_lock_sha256 | "d66f7425646512e1eb6916b61912e52660ce3fc2449fd9d6af59e5e3dd15210b" |
| stage_and_context_order | 8 rows; sha256=91ed400481b3a0811265f1fc742e463a775be50cd21fa91ccd78e0011f4d1f76 |
| stages | 2 rows; sha256=b1b6496fb51683e061edc3f71671473aec7102276d902fa10f85afd2e44ec55f |
| status | "FROZEN" |
| stop_matrix | {"advisory_message_quality_failure": "REPORT_AND_CONTINUE", "hard_semantic_or_safety_failure": "STOP_ALL_REMAINING", "preservation_failure": "STOP_ALL_REMAINING", "schema_identity_order_alias_failure": "STOP_ALL_REMAINING", "terminal_transport_failure": "STOP_ALL_REMAINING"} |
| subjects_per_context | 4 |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| wrapper_explicit_retries | 0 |
