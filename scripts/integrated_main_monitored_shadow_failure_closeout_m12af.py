"""Close out an M12AF generation stopped by an objective semantic gate.

This reporter does not alter or rerun the frozen experiment. It records the
partial evidence as incomplete and emits the reports required for bundling.
"""

from __future__ import annotations

from collections.abc import Mapping

from scripts import directional_financial_context_m12 as m12
from scripts import integrated_main_monitored_shadow_diagnostic_m12af as task


NEXT_SCOPE = "BUSINESS_THESIS_DELTA_SEMANTICS_REVIEW_ON_INTEGRATED_MAIN"
ARCHITECTURE = "TWO_STAGE_COMPATIBILITY_INCOMPLETE"
COMBINED = "INSUFFICIENT_REAL_ANALOG_COVERAGE"


def _partial_rows(run_document: Mapping[str, object]) -> list[dict[str, object]]:
    rows = run_document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("partial_run_rows_missing")
    result: list[dict[str, object]] = []
    for source in rows:
        if not isinstance(source, Mapping):
            raise ValueError("partial_run_row_invalid")
        core = source.get("core")
        core = core if isinstance(core, Mapping) else {}
        result.append(
            {
                "ticker": source.get("ticker"),
                "status": source.get("status"),
                "errors": source.get("errors", []),
                "overall_direction": core.get("overall_direction"),
                "business_thesis_change": core.get("business_thesis_change"),
                "new_buyer_stance": (
                    core.get("fundamental_new_buyer", {}).get("stance")
                    if isinstance(core.get("fundamental_new_buyer"), Mapping)
                    else None
                ),
                "holder_stance": (
                    core.get("fundamental_holder", {}).get("stance")
                    if isinstance(core.get("fundamental_holder"), Mapping)
                    else None
                ),
                "business_delta": source.get("business_delta"),
                "financial_semantics": source.get("financial_semantics"),
            }
        )
    return result


def closeout() -> None:
    state = task.read_json(task.OUTPUT / "shadow" / "program-state.json")
    stop = task.read_json(task.OUTPUT / "shadow" / "stop.json")
    run_path = (
        task.OUTPUT
        / "shadow/model-calls/context-01/monolithic/run-document.json"
    )
    receipt_path = (
        task.OUTPUT / "shadow/model-calls/context-01/monolithic/receipt.json"
    )
    run_document = task.read_json(run_path)
    receipt = task.read_json(receipt_path)
    partial_rows = _partial_rows(run_document)
    generation_id = str(state["generation_id"])

    if stop.get("status") != "FAIL":
        raise ValueError("m12af_stop_receipt_not_failed")
    if stop.get("completed_model_calls") != 1:
        raise ValueError("m12af_failure_closeout_requires_one_completed_call")
    if receipt.get("status") != "PASS":
        raise ValueError("m12af_transport_was_not_successful")
    if run_document.get("generation_id") != generation_id:
        raise ValueError("m12af_generation_mismatch")
    if run_document.get("status") != "FAIL":
        raise ValueError("m12af_semantic_failure_missing")

    audit = run_document.get("audit")
    if not isinstance(audit, Mapping):
        raise ValueError("m12af_run_audit_missing")
    semantic_failures = [row for row in partial_rows if row["status"] != "PASS"]
    business_delta_failures = int(audit.get("business_delta_violation_count", 0))
    financial_semantic_failures = int(audit.get("partial_debt_total_claim_count", 0))
    objective_failure_count = business_delta_failures + financial_semantic_failures

    reason = (
        "The first frozen monolithic context produced four schema-valid rows, "
        "but three rows failed objective semantic validation. The generation "
        "therefore stopped before Stage 1 and Stage 2, with no retry."
    )
    not_measured = {
        "status": "NOT_MEASURED_HARD_STOP",
        "reason": reason,
        "generation_id": generation_id,
        "comparison_complete_ticker_count": 0,
    }

    task.report(
        16,
        "shadow-per-ticker-comparison-table",
        {
            **not_measured,
            "rows": [],
            "partial_monolithic_rows": partial_rows,
        },
    )
    for number, slug in (
        (17, "shadow-core-direction-differences"),
        (18, "shadow-business-delta-differences"),
        (19, "shadow-new-buyer-differences"),
        (20, "shadow-holder-differences"),
        (21, "shadow-same-direction-calibration-differences"),
        (22, "shadow-expected-contract-corrections"),
        (23, "shadow-potential-architecture-regressions"),
        (24, "shadow-unresolved-review-required"),
    ):
        task.report(number, slug, {**not_measured, "count": "NOT_MEASURED", "rows": []})

    universe = state.get("universe")
    universe = universe if isinstance(universe, list) else []
    attempted = {str(row["ticker"]) for row in partial_rows}
    attempted_universe = [
        row
        for row in universe
        if isinstance(row, Mapping) and str(row.get("ticker")) in attempted
    ]
    attempted_sectors = sorted(
        {
            str(row.get("industry") or row.get("sector") or "unspecified")
            for row in attempted_universe
        }
    )
    task.report(
        25,
        "shadow-sector-coverage",
        {
            "status": "INCOMPLETE_HARD_STOP",
            "task_start_active_count": len(state["all_active_tickers"]),
            "attempted_ticker_count": len(partial_rows),
            "attempted_kr_count": len(partial_rows),
            "attempted_us_count": 0,
            "comparison_complete_ticker_count": 0,
            "attempted_sector_coverage_count": len(attempted_sectors),
            "attempted_sectors": attempted_sectors,
            "rows": attempted_universe,
        },
    )
    financial_row = next(
        (row for row in partial_rows if row["ticker"] == "003690"), None
    )
    task.report(
        26,
        "shadow-financial-sector-audit",
        {
            "status": "INCOMPLETE_HARD_STOP",
            "ticker": "003690",
            "generic_industrial_framework_failure_count": 0,
            "business_delta_unsupported_change_violation_count": 1,
            "two_stage_comparison_available": False,
            "partial_monolithic_row": financial_row,
        },
    )
    task.report(
        27,
        "shadow-adr-security-basis-audit",
        {
            **not_measured,
            "ticker": "SKHY",
            "security_basis_failure_count": "NOT_MEASURED",
            "denominator_reconstruction": 0,
            "provider_multiple_backsolving": 0,
        },
    )
    task.report(
        28,
        "shadow-cyclical-valuation-framework-audit",
        {
            "status": "INCOMPLETE_HARD_STOP",
            "attempted_tickers": ["000660", "005490", "005930"],
            "cyclical_valuation_framework_failure_count": 0,
            "other_objective_semantic_failure_count": 2,
            "rows": [
                row
                for row in partial_rows
                if row["ticker"] in {"000660", "005490", "005930"}
            ],
        },
    )
    task.report(
        29,
        "shadow-core-immutability-audit",
        {
            **not_measured,
            "core_mutation_after_stance_count": "NOT_MEASURED",
            "stage2_model_calls": 0,
            "rows": [],
        },
    )
    task.report(
        30,
        "shadow-runtime-audit",
        {
            "status": "FAIL_OBJECTIVE_SEMANTIC",
            "transport_status": "PASS",
            "completed_model_calls": 1,
            "monolithic_model_calls": 1,
            "stage1_model_calls": 0,
            "stage2_model_calls": 0,
            "timeout_count": 0,
            "capacity_failure_count": 0,
            "orphan_process_count": int(receipt.get("orphan_process_count", 0)),
            "wrapper_retry_count": int(receipt.get("wrapper_retry_count", 0)),
            "packet_mismatch_count": 0,
            "objective_semantic_hard_failure_count": objective_failure_count,
            "failed_subject_count": len(semantic_failures),
            "failed_context_count": 1,
            "stop": stop,
            "receipt": receipt,
        },
    )
    task.report(
        31,
        "shadow-aggregate-summary",
        {
            "status": "INCOMPLETE_HARD_STOP",
            "active_monitored_count": len(state["all_active_tickers"]),
            "packet_available_count": len(state["tickers"]),
            "packet_unavailable_count": len(state["unavailable"]),
            "planned_context_count": state["context_count"],
            "attempted_context_count": 1,
            "completed_comparison_context_count": 0,
            "planned_model_call_count": state["planned_model_calls"],
            "completed_model_call_count": 1,
            "monolithic_output_ticker_count": len(partial_rows),
            "monolithic_semantic_pass_ticker_count": sum(
                row["status"] == "PASS" for row in partial_rows
            ),
            "monolithic_semantic_fail_ticker_count": len(semantic_failures),
            "comparison_complete_ticker_count": 0,
            "business_delta_violation_count": business_delta_failures,
            "partial_debt_total_claim_count": financial_semantic_failures,
            "rows": partial_rows,
        },
    )
    task.report(
        32,
        "shadow-architecture-decision",
        {
            "status": "CLASSIFIED_INCOMPLETE",
            "two_stage_shadow_compatibility_classification": ARCHITECTURE,
            "rationale": (
                "The frozen monolithic control failed objective semantics in the "
                "first context, so the two-stage path was never called and no "
                "architecture comparison can be inferred."
            ),
            "diagnostic_only": True,
            "fresh_real_proof_implication": "NONE",
        },
    )

    task.report(
        33,
        "fic-fin-05-boundary-vs-monitored-leverage-analogs",
        {
            "status": "INCOMPLETE",
            "classification": COMBINED,
            "analog_tickers": [],
            "rationale": "No same-packet monolithic/two-stage monitored comparison completed.",
            "majority_vote": 0,
            "balance_averaging": 0,
        },
    )
    task.report(
        34,
        "fic-fin-06-operating-signal-vs-thesis-delta-review",
        {
            "status": "INCOMPLETE_WITH_DIRECT_MONITORED_SIGNAL",
            "frozen_observation": ["STRENGTHENED", "STRENGTHENED", "UNCHANGED"],
            "monitored_signal": (
                "003690 asserted STRENGTHENED and 005930 asserted UNRESOLVED "
                "without evidence supporting those business-thesis deltas."
            ),
            "prompt_or_contract_change": 0,
            "recommended_follow_up": NEXT_SCOPE,
        },
    )
    task.report(
        35,
        "fic-fin-06-vs-monitored-growth-quality-analogs",
        {
            "status": "INCOMPLETE",
            "classification": COMBINED,
            "analog_tickers": ["003690", "005930"],
            "rationale": (
                "Related business-delta failures were observed, but no two-stage "
                "comparison completed, so they are signals rather than valid analog proofs."
            ),
        },
    )
    task.report(
        36,
        "fic-fin-08-holder-risk-severity-review",
        {
            "status": "NOT_MEASURED_HARD_STOP",
            "frozen_observation": ["HOLDABLE", "HOLDABLE", "REVIEW"],
            "prompt_or_contract_change": 0,
            "recommended_follow_up": NEXT_SCOPE,
        },
    )
    task.report(
        37,
        "fic-fin-08-vs-monitored-financial-sector-analogs",
        {
            "status": "INCOMPLETE",
            "classification": COMBINED,
            "analog_tickers": ["003690"],
            "rationale": (
                "The real financial-sector name failed the monolithic business-delta "
                "gate before Stage 2 holder comparison."
            ),
        },
    )
    task.report(
        38,
        "combined-fictional-monitored-root-cause-summary",
        {
            "status": "INCOMPLETE_HARD_STOP",
            "fic_fin_05": COMBINED,
            "fic_fin_06": COMBINED,
            "fic_fin_08": COMBINED,
            "architecture": ARCHITECTURE,
            "root_causes": [
                {
                    "tickers": ["003690", "005930"],
                    "error": "UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA",
                    "count": business_delta_failures,
                },
                {
                    "tickers": ["005490"],
                    "error": "net_debt_claim_without_complete_net_debt_evidence",
                    "count": financial_semantic_failures,
                },
            ],
            "transport_failure_count": 0,
            "schema_failure_count": 0,
        },
    )
    task.report(
        39,
        "next-bounded-repair-decision",
        {
            "status": "SELECTED_AFTER_HARD_STOP",
            "next_scope": NEXT_SCOPE,
            "rationale": (
                "Repair the observed absolute-state-to-business-delta boundary first, "
                "while retaining the independent 005490 incomplete-net-debt evidence "
                "case as a bounded semantic regression. Then start a new generation; "
                "do not resume or stitch this one."
            ),
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
        },
    )
    task.report(
        40,
        "existing-monitored-impact-summary",
        {
            "status": "INCOMPLETE_HARD_STOP",
            "compatibility_cohort_not_unseen": True,
            "attempted_ticker_count": len(partial_rows),
            "monolithic_semantic_pass_ticker_count": 1,
            "monolithic_semantic_fail_ticker_count": 3,
            "comparison_complete_ticker_count": 0,
            "production_persistence": 0,
        },
    )
    task.report(
        41,
        "two-stage-shadow-compatibility-readiness",
        {
            "status": "NOT_READY",
            "two_stage_shadow_compatibility_classification": ARCHITECTURE,
            "full_monitored_universe_compatibility_claimed": False,
            "fresh_real_generalization_claimed": False,
        },
    )
    task.report(
        42,
        "fresh-real-proof-readiness-decision",
        {
            "status": "NOT_READY",
            "fresh_real_proof_readiness": "NOT_READY",
            "model_calls_real_fresh_unseen": 0,
            "reason": "M12AF stopped on an objective semantic hard failure.",
        },
    )
    task.report(
        43,
        "final-main-merge-readiness-note",
        {
            "status": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "main_merges": 0,
            "reason": "The monitored comparison is incomplete and fresh unseen proof did not occur.",
        },
    )
    no_change = {
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "automatic_monitoring_resume": 0,
    }
    task.report(
        44,
        "production-no-change",
        {"status": "PASS", **no_change, "production_readiness": "NOT_READY"},
    )
    schedule_end = m12._schedule_observation()
    task.report(
        45,
        "schedule-pause-observation",
        {
            "status": (
                "PASS"
                if schedule_end["observed_paused_schedule_count"] >= 4
                else "REVIEW"
            ),
            "start": state["schedule_start"],
            "end": schedule_end,
            "observed_paused_schedule_count": schedule_end[
                "observed_paused_schedule_count"
            ],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    task.report(
        46,
        "hosted-ci-portability-handoff",
        {
            "status": "NOT_RUN_DIAGNOSTIC_BRANCH",
            "hosted_ci_pass_claimed": False,
            "historical_backlog_carried": True,
            "new_hosted_ci_failure_count": "NOT_MEASURED",
        },
    )
    task.report(
        47,
        "astra-future-experiment-handoff",
        {
            "status": "DEFERRED",
            "astra_calls": 0,
            "proof_model": task.MODEL,
            "reasoning_effort": task.EFFORT,
            "future_experiment_must_be_separate": True,
        },
    )
    task.report(
        48,
        "master-workflow-update",
        {
            "status": "RECORDED_IN_REPORT_ONLY",
            "phase": "M12AF",
            "two_stage_shadow_compatibility_classification": ARCHITECTURE,
            "fresh_real_proof_readiness": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "next_scope": NEXT_SCOPE,
            "persistent_master_workflow_mutation": 0,
        },
    )

    reference_diff = task.read_json(
        task.REPORTS / "10-reference-vs-task-start-universe-diff.json"
    )
    completion: dict[str, object] = {
        "status": "STOPPED_OBJECTIVE_SEMANTIC_HARD_FAILURE",
        "base_integration_head_sha": task.BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": task.git("branch", "--show-current"),
        "generation_id": generation_id,
        "monolithic_control_prompt_sha256": task.EXPECTED_CONTROL_PROMPT_SHA256,
        "monolithic_control_schema_sha256": task.EXPECTED_CONTROL_SCHEMA_SHA256,
        "two_stage_service_sha256": task.EXPECTED_TWO_STAGE_SERVICE_SHA256,
        "investment_judgment_model_target": task.MODEL,
        "investment_judgment_reasoning_effort": task.EFFORT,
        "task_start_active_monitor_count": len(state["all_active_tickers"]),
        "task_start_active_monitor_tickers": state["all_active_tickers"],
        "reference_added_tickers": reference_diff["reference_added_tickers"],
        "reference_removed_tickers": reference_diff["reference_removed_tickers"],
        "shadow_packet_available_count": len(state["tickers"]),
        "shadow_packet_unavailable_count": len(state["unavailable"]),
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": state["context_count"],
        "shadow_attempted_context_count": 1,
        "shadow_completed_context_count": 0,
        "shadow_monolithic_model_calls": 1,
        "shadow_stage1_model_calls": 0,
        "shadow_stage2_model_calls": 0,
        "shadow_model_calls_total": 1,
        "shadow_completed_ticker_count": 0,
        "shadow_attempted_ticker_count": len(partial_rows),
        "shadow_monolithic_output_ticker_count": len(partial_rows),
        "shadow_monolithic_semantic_pass_ticker_count": 1,
        "shadow_monolithic_semantic_fail_ticker_count": 3,
        "shadow_no_decision_material_change_count": "NOT_MEASURED",
        "shadow_same_direction_calibration_change_count": "NOT_MEASURED",
        "shadow_primary_direction_change_count": "NOT_MEASURED",
        "shadow_business_delta_change_count": "NOT_MEASURED",
        "shadow_new_buyer_change_count": "NOT_MEASURED",
        "shadow_holder_change_count": "NOT_MEASURED",
        "shadow_multi_field_change_count": "NOT_MEASURED",
        "shadow_expected_contract_correction_count": "NOT_MEASURED",
        "shadow_potential_architecture_regression_count": "NOT_MEASURED",
        "shadow_unresolved_review_required_count": "NOT_MEASURED",
        "shadow_kr_count": 0,
        "shadow_us_count": 0,
        "shadow_attempted_kr_count": len(partial_rows),
        "shadow_attempted_us_count": 0,
        "shadow_sector_coverage_count": 0,
        "shadow_attempted_sector_coverage_count": len(attempted_sectors),
        "shadow_financial_sector_framework_failure_count": 0,
        "shadow_adr_security_basis_failure_count": "NOT_MEASURED",
        "shadow_cyclical_valuation_framework_failure_count": 0,
        "shadow_core_mutation_after_stance_count": "NOT_MEASURED",
        "shadow_objective_semantic_hard_failure_count": objective_failure_count,
        "shadow_business_delta_violation_count": business_delta_failures,
        "shadow_partial_debt_total_claim_count": financial_semantic_failures,
        "shadow_runtime_timeout_count": 0,
        "shadow_runtime_capacity_failure_count": 0,
        "shadow_runtime_orphan_count": int(receipt.get("orphan_process_count", 0)),
        "shadow_wrapper_retry_count": int(receipt.get("wrapper_retry_count", 0)),
        "provider_source_fetches": 0,
        **no_change,
        "observed_paused_schedule_count": schedule_end[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "fic_fin_05_combined_diagnostic_classification": COMBINED,
        "fic_fin_06_combined_diagnostic_classification": COMBINED,
        "fic_fin_08_combined_diagnostic_classification": COMBINED,
        "two_stage_shadow_compatibility_classification": ARCHITECTURE,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "stop_reason": stop["stop_reason"],
        "stop_detail": stop["detail"],
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    task.report(49, "program-completion", completion)
    task.write_json(task.OUTPUT / "program-completion.json", completion)
    task.write_json(
        task.OUTPUT / "shadow" / "failure-closeout.json",
        {
            "status": completion["status"],
            "generation_id": generation_id,
            "stop": stop,
            "partial_rows": partial_rows,
            "architecture": ARCHITECTURE,
            "next_scope": NEXT_SCOPE,
            "experiment_code_or_config_changed_after_start": 0,
            "selective_retry_count": 0,
        },
    )


if __name__ == "__main__":
    closeout()
