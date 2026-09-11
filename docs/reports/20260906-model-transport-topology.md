# Model Transport Topology

| Gate | Value |
| --- | --- |
| continuation_path | ["network_preflight", "subprocess.Popen_start_new_session", "stdin_writer_thread", "stdout_reader_thread", "stderr_reader_thread", "single_monotonic_watchdog", "process_group_cleanup", "output_file_parse", "single_receipt"] |
| contract | model-transport-topology-v1 |
| prior_path | ["network_preflight", "subprocess.run", "combined_stdout_stderr_file", "subprocess_timeout", "direct_child_kill_and_wait", "output_file_parse"] |
| production_runtime_path_change | 0 |
| semantic_input_change | 0 |

The continuation separates stdin, stdout, and stderr lifecycle events, uses one monotonic deadline, and owns the full process group.

Machine proof: `20260906-model-transport-continuation-proofs/model-transport-topology.json`.
