# 19-fresh-holdout-precommit

| Field | Value |
| --- | --- |
| acceptance_protocol | {"core_partial_audit_sha256": "beb7ce7950ccd59f25970c143612d88ffc1f06c02658f2ac2c196c70eaad79a5", "core_stability_sha256": "dac6ab2a09ff00c49f912028ab8e00788fc2948a8a86c2ad3b47cc575b6422a8", "message_quality_sha256": "1b8e944512b9fd2dda0669f135b72181ae7b6b5f41af136bba2f91ebc6499d6f", "quality_gate_role": "ADVISORY_NOT_INCLUDED_IN_RUN_STATUS_OR_PROGRESS_SEQUENCE", "run_gate_documents_sha256": "d311905e8648bad3f9f83d960ef99ec45cbd9be2f3b4fe6b5f3da93cc50d79d8", "status_mapping": {"advisory_message_quality_failure": "REPORT_WITHOUT_PROGRESS_BLOCK", "four_valid_runs_required_for_stability": true, "hard_context_or_run_failure": "STOP_REMAINING_CALLS"}, "timing_partial_audit_sha256": "a76cec0729f33aa64ac84820e7b843b631f4879b01adf93af1afb6fab516fab3", "timing_stability_sha256": "d81eb366e6be40653937e65af64cf86f0fcf95458b14e3e0be8a1aeff1b99666"} |
| acceptance_protocol_sha256 | 939459e6efc6b21cb8b14f2c256e6e56364724ae1f76a2a5cdb518ce66a77c17 |
| batch_semantics | MODEL_CONTEXT_COUPLED |
| batch_split | 0 |
| capacity_or_health_model_smoke_calls | 0 |
| carried_runtime_risk | UNRESOLVED_RUNTIME_RELIABILITY_NOT_ESTABLISHED |
| context_groups | 4 rows; sha256=b7e4a59bc85f72ff1f4742f48174d3b7c9b2aa595ba6d0d6854e01573a284243 |
| contract | fresh-issuer-risk-carried-execution-precommit-v1 |
| exclusion_registry_count | 117 |
| exclusion_registry_sha256 | 7ffd6fed1125e88073efb867d3d5adc4024a0f22485e0c376151fbe5e3b6b437 |
| expected_invocations_per_run | 8 |
| expected_total_model_invocations | 32 |
| failed_call_replacements | 0 |
| frozen_evaluation_cutoff | 2026-09-07T15:27:51+00:00 |
| hotfix_after_first_output | 0 |
| implementation_commit | 0ef6c9ea9a82d1a761701b5ee91cc81a15530bd4 |
| implementation_tree | f24ab725802fc99935f67064a7b5b15fb77487ed |
| market_by_ticker | 16 keys; sha256=d1aa76f0a7bdf8743c19640c405f64707a1182ba5bbc5ceabd7fb3dcabcd822e |
| maximum_fresh_real_cohorts | 1 |
| maximum_real_model_subprocess_attempts | 32 |
| model | gpt-5.6-sol |
| model_free_preflight | 19 keys; sha256=51008ea85e8b77f32b22647a43636e3bb34e9ab4dbdef70f4b61bc64eb43b668 |
| model_retry_count | 0 |
| namespace_policy | one isolated signed-in Codex CLI subprocess, temporary working directory and runtime-state namespace per model context |
| new_fictional_model_calls | 0 |
| ordered_cohort | 16 rows; sha256=9bc48f1da24cafac6d5fc408fc30518a99b805c71513f8960bbfe63d00a99902 |
| packet_sha256 | 16 keys; sha256=1b0db3220cfc3892b477f3bc46e4b4c8dde888938c0bc23ddeec87b25ad9a1eb |
| pause_observation | {"auto_resume_executed": 0, "codex_automations": [{"active": false, "name": "Thesis Monitor AI Review US Primary", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review US Backup", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review KR Primary", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review KR Backup", "state": "PAUSED"}], "contract": "current-monitoring-pause-observation-v1", "launch_agents": [{"active": false, "name": "com.seungsoo.thesis-monitor.daily", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.kr-close", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.ai-review-fallback", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.ai-review-delivery-retry", "state": "PAUSED_DISABLED_UNLOADED"}], "observation_only": true, "observed_at": "2026-09-07T16:54:05.055155+00:00", "observed_scheduler_object_count": 8, "scheduler_mutation_count": 0, "status": "VERIFIED_PAUSED_COMPLETE", "unexpected_active_paths": []} |
| pre_first_frozen_at | 2026-09-07T16:54:05.021783+00:00 |
| process_observation | {"active_natural_job_count": 0, "model_execution_pids": [], "natural_job_rows": [], "observation_capabilities": {"model_execution_observable": true, "natural_process_observable": true, "paused_schedule_registry_observable": true, "protected_window_observable": true, "scheduler_mutation": false}, "pause_observed_at": "2026-09-07T16:54:05.086793+00:00", "paused_schedule_count": 8, "running_model_process_count": 0, "unexpected_active_monitoring_paths": [], "workload_observation_backend": "PAUSE_REGISTRY_PLUS_PS_NATURAL_MARKERS_PLUS_LSOF_CODEX_RUNTIME_STATE"} |
| prompt_schema_lock_sha256 | 6b53836e40c99f4db6ec883bdc270ee67433c19bc7312c13154da54bddbbb9a9 |
| reasoning_effort | xhigh |
| reconnect_path_exercised | NOT_OBSERVED |
| reference_snapshot_sha256 | c64c01f9576c4f2d0acf8dfe2b82dc4da89dd46d5fd76d9d90055c51fc9aea7a |
| replacement_cohort_attempts | 0 |
| reserve_order_sha256 | e6e7dd34f4b859554ccf611e646f173ac5a06e62950bbbbb3b6fd820bf82b048 |
| run_order | 4 rows; sha256=4386cdf7c84a0528583adf978e4bf4ee636a1879edd76e300cf5f35b85e5e63f |
| runs | 4 rows; sha256=4386cdf7c84a0528583adf978e4bf4ee636a1879edd76e300cf5f35b85e5e63f |
| runtime_generation_id | 20260907-fresh-issuer-proof-20260907T152751Z-78228f940e3c |
| runtime_reliability_status | NOT_ESTABLISHED |
| selection_policy_sha256 | 07defbbe29042495ebaa08cb24ca5fcc57cd42c859bfbf80ccc5d984068b2f8f |
| selective_rerun | 0 |
| signed_in_cli_identity | {"checks": {"sha256": true, "version": true}, "path": "/Applications/ChatGPT.app/Contents/Resources/codex", "sha256": "7645c3caf5607e4528eb3a15b12496c284c2a918939aed34e863c760c1b421e7", "status": "PASS", "version": "codex-cli 0.148.0-alpha.15"} |
| source_generation_id | 20260907-fresh-issuer-source-20260907T152751Z-3f4af1225c1c |
| source_lock_sha256 | 74dbadf1f826891e45ee86d47d8071d5a6deb512f1f06e89b397011ac478af92 |
| stage_and_context_order | 8 rows; sha256=91ed400481b3a0811265f1fc742e463a775be50cd21fa91ccd78e0011f4d1f76 |
| stages | 2 rows; sha256=b1b6496fb51683e061edc3f71671473aec7102276d902fa10f85afd2e44ec55f |
| status | FROZEN |
| stop_matrix | {"advisory_message_quality_failure": "REPORT_AND_CONTINUE", "hard_semantic_or_safety_failure": "STOP_ALL_REMAINING", "preservation_failure": "STOP_ALL_REMAINING", "schema_identity_order_alias_failure": "STOP_ALL_REMAINING", "terminal_transport_failure": "STOP_ALL_REMAINING"} |
| subjects_per_context | 4 |
| timeout_owner_count | 1 |
| timeout_seconds | 1800 |
| wrapper_explicit_retries | 0 |
