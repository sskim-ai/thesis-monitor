# 14 Batch03 Lifecycle Forensics

Contract: `historical-batch03-lifecycle-forensics-v1`

Status: `PASS`

```json
{
  "child_cleanup_status": "PROCESS_GROUP_TERMINATED",
  "cli_binary_path": "/Applications/ChatGPT.app/Contents/Resources/codex",
  "cli_binary_sha256": "7645c3caf5607e4528eb3a15b12496c284c2a918939aed34e863c760c1b421e7",
  "cli_version": "codex-cli 0.148.0-alpha.15",
  "configured_timeout_seconds": 1800,
  "confirmed_facts": [
    "child_process_spawned",
    "stdin_completed",
    "startup_stderr_burst_only",
    "no_stdout",
    "no_output_file",
    "same_runtime_state_namespace_as_batches01_02",
    "same_cli_binary_version_model_effort",
    "single_watchdog_terminated_process_group",
    "orphan_process_count_zero",
    "network_readiness_probe_equal_to_prior_batches"
  ],
  "contract": "historical-batch03-lifecycle-forensics-v1",
  "elapsed_to_exit_seconds": 1800.03276,
  "exit_code": -15,
  "first_stderr_seconds": 0.284216,
  "first_stdout_seconds": null,
  "generation_id": "20260906-real-holdout-adapter-resume-20260906T133003Z-585c983a57d9",
  "inferred_hypotheses": [
    "state_namespace_sequence_correlation_possible",
    "local_cli_runtime_stall_possible",
    "backend_or_model_stall_possible",
    "prompt_context_pathological_latency_possible"
  ],
  "input_bytes": 17896,
  "invocation_id": "20260906-real-holdout-adapter-resume-20260906T133003Z-585c983a57d9:run-first:DIRECTIONAL_CORE:03",
  "last_stderr_seconds": 0.284341,
  "model": "gpt-5.6-sol",
  "network_probe_attempts": 1,
  "network_resolved_address_count": 4,
  "orphan_model_process_count": 0,
  "output_bytes": 0,
  "output_file_created": false,
  "output_parsed": false,
  "parse_error": "OUTPUT_FILE_MISSING",
  "preservation": {
    "receipt": {
      "category_counts": {
        "bearer_token": 0,
        "named_secret": 0,
        "openai_key": 0
      },
      "copied_bytes": 2887,
      "copied_sha256": "1d2ce5155f3e22667a9e42c099b654401b42464cfa508b31dd8f291f2a1207bb",
      "preservation_status": "EXACT_BYTES_PRESERVED",
      "secret_exposure_count": 0,
      "secret_scan_status": "PASS",
      "source_bytes": 2887,
      "source_sha256": "1d2ce5155f3e22667a9e42c099b654401b42464cfa508b31dd8f291f2a1207bb"
    },
    "stderr": {
      "category_counts": {
        "bearer_token": 0,
        "named_secret": 0,
        "openai_key": 0
      },
      "copied_bytes": 18244,
      "copied_sha256": "bc979fc7abe1e95da40a3e00333b71d71a1b7784146006357b6aea8464c2d281",
      "preservation_status": "EXACT_BYTES_PRESERVED",
      "secret_exposure_count": 0,
      "secret_scan_status": "PASS",
      "source_bytes": 18244,
      "source_sha256": "bc979fc7abe1e95da40a3e00333b71d71a1b7784146006357b6aea8464c2d281"
    },
    "stdout": {
      "category_counts": {
        "bearer_token": 0,
        "named_secret": 0,
        "openai_key": 0
      },
      "copied_bytes": 0,
      "copied_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "preservation_status": "EXACT_BYTES_PRESERVED",
      "secret_exposure_count": 0,
      "secret_scan_status": "PASS",
      "source_bytes": 0,
      "source_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "transport_log": {
      "category_counts": {
        "bearer_token": 0,
        "named_secret": 0,
        "openai_key": 0
      },
      "copied_bytes": 18245,
      "copied_sha256": "0ee619d14656971a70ae5a74589cf84934f9ad3526ef62974bb6022239e4baa8",
      "preservation_status": "EXACT_BYTES_PRESERVED",
      "secret_exposure_count": 0,
      "secret_scan_status": "PASS",
      "source_bytes": 18245,
      "source_sha256": "0ee619d14656971a70ae5a74589cf84934f9ad3526ef62974bb6022239e4baa8"
    }
  },
  "prompt_sha256": "20e674c7ad0bf8bcae3e3e41f55b1a08387cd6ef5ccc7aa50912fe999587620d",
  "raw_stderr_recovery_status": "EXACT_BYTES_PRESERVED",
  "raw_transport_log_recovery_status": "EXACT_BYTES_PRESERVED",
  "reasoning_effort": "xhigh",
  "request_accepted_observability": "UNAVAILABLE",
  "root_cause_classification": "ROOT_CAUSE_UNRESOLVED",
  "root_cause_confidence": "DIRECT_FACTS_STRONG_CAUSAL_ATTRIBUTION_UNAVAILABLE",
  "schema_sha256": "6b009e4fec4444b11e6847326b4f25631cca81db63a4fb7d6078a18b9e030f0e",
  "silent_interval_before_exit_seconds": 1799.748419,
  "state_namespace_hash": "109349399ebbd66080e41cf4",
  "status": "PASS",
  "stderr_burst_duration_seconds": 0.000125,
  "stderr_bytes": 18244,
  "stdin_complete": true,
  "stdout_bytes": 0,
  "termination_initiator": "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
  "termination_signal": 15,
  "timeout_owner": "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
  "timeout_owner_count": 1,
  "tls_trust_source": "ROOT_OWNED_SYSTEM_CA_BUNDLE",
  "unknowns": [
    "remote_request_acceptance",
    "remote_model_compute_state",
    "local_cli_event_loop_state_after_startup",
    "causal_role_of_shared_state_namespace",
    "causal_role_of_batch03_prompt_content"
  ],
  "working_directory_identity": "42507c2b24e78589d7831ece4f1c24bbdfb63c207923713f544dc612d37f8788"
}
```
