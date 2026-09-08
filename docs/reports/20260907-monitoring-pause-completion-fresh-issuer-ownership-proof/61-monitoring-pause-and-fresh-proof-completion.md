# 61 Monitoring Pause And Fresh Proof Completion

| Field | Value |
| --- | --- |
| contract | monitoring-pause-completion-fresh-issuer-ownership-proof-v1 |
| operational_pause_status | PAUSED_COMPLETE |
| operational_pause_us_status | PAUSED_COMPLETE |
| operational_pause_kr_status | PAUSED_COMPLETE |
| restoration_requires_explicit_user_request | True |
| historical_changed_scheduler_object_count | 6 |
| current_task_new_scheduler_mutation_count | 2 |
| current_paused_scheduler_object_count | 8 |
| transition_backlog_observation | dict(6) |
| source_generation_id | 20260907-fresh-issuer-source-20260907T090500Z-2b1e0d043243 |
| runtime_generation_id | 20260907-fresh-issuer-proof-20260907T090500Z-2fc43e587bfe |
| ordered_cohort | ["NU", "LNG", "TCI", "WMG", "043100", "025000", "131030", "372910", "130740", "045340", "006910", "288980", "023440", "064820", "001440", "073490"] |
| market_mix | {"kr": 12, "us": 4} |
| model | gpt-5.6-sol |
| reasoning_effort | xhigh |
| model_timeout_seconds | 1800 |
| model_timeout_owner_count | 1 |
| actual_model_invocation_count | 17 |
| model_retry_count | 0 |
| run_results | {"a": "16/16", "b": "FAILED_0/16", "c": "NOT_RUN", "first": "16/16"} |
| exposure | {"output_exposure_state": "FULLY_EXPOSED", "raw_subject_row_count": 64, "stage_context_counts": {"DIRECTIONAL_CORE": 8, "PRICE_TIMING": 8}, "unique_exposed_issuer_count": 16, "unique_exposed_issuers": ["001440", "006910", "023440", "025000", "043100", "045340", "064820", "073490", "130740", "131030", "288980", "372910", "LNG", "NU", "TCI", "WMG"]} |
| ownership_generalization_verdict | NOT_ESTABLISHED |
| production_change | {"additional_dependencies_paused": ["com.seungsoo.thesis-monitor.ai-review-fallback", "com.seungsoo.thesis-monitor.ai-review-delivery-retry"], "auto_resume_configured": false, "contract": "production-change-accounting-v1", "current_paused_scheduler_objects": 8, "current_task_new_scheduler_mutations": 2, "deployment": 0, "forced_termination_count": 0, "historical_transition_activity": null, "main_merge": 0, "night_futures_change": 0, "prior_task_changed_scheduler_objects": 6, "production_db_mutation_task_initiated": 0, "production_scheduler_change": 1, "production_telegram_send_task_initiated": 0, "status": "PASS", "stock_registration_change": 0, "unauthorized_scheduler_change": 0} |
| readiness | NOT_READY_TRANSPORT_TIMEOUT |
| next_scope | BOUNDED_TRANSPORT_RUNTIME_REVIEW |
| stop_reason | InstrumentedTransportError:TIMEOUT:20260907-fresh-issuer-proof-20260907T090500Z-2fc43e587bfe:b:DIRECTIONAL_CORE:01 |
| status | STOPPED |
| final_head_sha | 46e09b999d6c5834fa5f5adf7ec1ff0df159bfb1 |
| focused_tests | PASS |
| full_tests | PASS |
| ruff | PASS |
| diff_check | PASS |

Machine proof: `proofs/61-monitoring-pause-and-fresh-proof-completion.json`.
