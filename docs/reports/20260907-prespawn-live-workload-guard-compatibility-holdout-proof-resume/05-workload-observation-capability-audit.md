# 05 Workload Observation Capability Audit

| Field | Value |
| --- | --- |
| contract | workload-observation-capability-audit-v1 |
| model_execution_observable | True |
| model_execution_registry | lsof open /codex_runtime_state/ paths |
| model_execution_signal | open /codex_runtime_state/ files |
| natural_job_observable | True |
| natural_job_registry | LaunchAgent ProgramArguments + launchctl state |
| natural_job_signal | loaded LaunchAgent state |
| protected_window_observable | True |
| ps_dependency | False |
| status | PASS |

Machine proof: `proofs/05-workload-observation-capability-audit.json`.