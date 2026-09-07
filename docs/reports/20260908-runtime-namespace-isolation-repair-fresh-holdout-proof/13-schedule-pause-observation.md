# 13-schedule-pause-observation

| Field | Value |
| --- | --- |
| contract | "runtime-isolation-proof-schedule-pause-observation-v1" |
| pause | {"auto_resume_executed": 0, "codex_automations": [{"active": false, "name": "Thesis Monitor AI Review US Primary", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review US Backup", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review KR Primary", "state": "PAUSED"}, {"active": false, "name": "Thesis Monitor AI Review KR Backup", "state": "PAUSED"}], "contract": "current-monitoring-pause-observation-v1", "launch_agents": [{"active": false, "name": "com.seungsoo.thesis-monitor.daily", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.kr-close", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.ai-review-fallback", "state": "PAUSED_DISABLED_UNLOADED"}, {"active": false, "name": "com.seungsoo.thesis-monitor.ai-review-delivery-retry", "state": "PAUSED_DISABLED_UNLOADED"}], "observation_only": true, "observed_at": "2026-09-07T18:19:04.186544+00:00", "observed_scheduler_object_count": 8, "scheduler_mutation_count": 0, "status": "VERIFIED_PAUSED_COMPLETE", "unexpected_active_paths": []} |
| process_observation | {"active_natural_job_count": 0, "model_execution_pids": [], "natural_job_rows": [], "observation_capabilities": {"model_execution_observable": true, "natural_process_observable": true, "paused_schedule_registry_observable": true, "protected_window_observable": true, "scheduler_mutation": false}, "pause_observed_at": "2026-09-07T18:19:04.204730+00:00", "paused_schedule_count": 8, "running_model_process_count": 0, "unexpected_active_monitoring_paths": [], "workload_observation_backend": "PAUSE_REGISTRY_PLUS_PS_NATURAL_MARKERS_PLUS_LSOF_CODEX_RUNTIME_STATE"} |
| observed_paused_schedule_count | 8 |
| approved_pause_scheduler_mutation_count | 0 |
| automatic_monitoring_resume | 0 |
| status | "PASS" |
