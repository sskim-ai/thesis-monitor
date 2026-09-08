# 26 Live Workload Coexistence Audit

| Field | Value |
| --- | --- |
| contract | risk-carried-live-workload-coexistence-audit-v1 |
| pause | dict(10) |
| process_observation | {"active_natural_job_count": 0, "model_execution_pids": [], "natural_job_rows": [], "observation_capabilities": {"model_execution_observable": true, "natural_process_observable": true, "paused_schedule_registry_observable": true, "protected_window_observable": true, "scheduler_mutation": false}, "pause_observed_at": "2026-09-07T16:54:05.086793+00:00", "paused_schedule_count": 8, "running_model_process_count": 0, "unexpected_active_monitoring_paths": [], "workload_observation_backend": "PAUSE_REGISTRY_PLUS_PS_NATURAL_MARKERS_PLUS_LSOF_CODEX_RUNTIME_STATE"} |
| scheduler_mutation | 0 |
| status | PASS |

Machine proof: `proofs/26-live-workload-coexistence-audit.json`.
