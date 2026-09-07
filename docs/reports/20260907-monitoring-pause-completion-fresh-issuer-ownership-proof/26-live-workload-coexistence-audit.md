# 26 Live Workload Coexistence Audit

| Field | Value |
| --- | --- |
| contract | natural-live-workload-coexistence-guard-v1 |
| events | list(2) |
| live_workload_contention_risk | 0 |
| natural_live_cancel_count | 0 |
| observation_capabilities | {"disabled_unloaded_natural_job_observable": true, "disabled_unloaded_treated_as_active": false, "model_execution_observable": true, "model_execution_signal": "open /codex_runtime_state/ files", "natural_job_observable": true, "natural_job_signal": "loaded LaunchAgent state", "protected_window_observable": true, "ps_dependency": false} |
| observation_unavailable_fail_closed_count | 1 |
| observation_unavailable_fail_open_count | 0 |
| scheduler_mutation | 0 |
| shadow_pause_for_natural_live | 0 |
| status | PASS |
| workload_observation_backend | LAUNCHCTL_ACTIVE_OR_DISABLED_UNLOADED_PLUS_LSOF_CODEX_RUNTIME_STATE |

Machine proof: `proofs/26-live-workload-coexistence-audit.json`.
