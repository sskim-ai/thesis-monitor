from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts import scheduled_monitoring_pause_capacity_closeout as closeout


def _receipt(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "status": "FAILED",
        "exit_code": 1,
        "parse_error": "OUTPUT_FILE_MISSING",
        "termination_initiator": "NONE",
        "termination_signal": None,
        "configured_timeout_seconds": 1800,
        "elapsed_to_exit_seconds": 382.0,
        "stdout_bytes": 0,
        "output_bytes": 0,
        "output_parsed": False,
        "request_accepted_observability": "UNAVAILABLE",
    }
    value.update(overrides)
    return value


def test_explicit_terminal_capacity_error_is_non_timeout_failure() -> None:
    result = closeout.classify_transport_failure(
        _receipt(), f"diagnostic\n{closeout.CAPACITY_DIAGNOSTIC}\n"
    )

    assert result["failure_category"] == "CLI_REPORTED_MODEL_CAPACITY_FAILURE"
    assert result["failure_lifecycle"] == "POST_SPAWN_NON_TIMEOUT_FAILURE"
    assert result["watchdog_termination"] is False


def test_prompt_echo_does_not_create_capacity_classification() -> None:
    stderr = (
        f"prompt says: {closeout.CAPACITY_DIAGNOSTIC}\n"
        "runtime ended without a primary diagnostic\n"
    )

    result = closeout.classify_transport_failure(_receipt(), stderr)

    assert result["failure_category"] == "GENERIC_POST_SPAWN_NONZERO_EXIT"
    assert result["terminal_capacity_diagnostic_count"] == 0


def test_generic_nonzero_exit_is_preserved() -> None:
    result = closeout.classify_transport_failure(_receipt(), "generic failure\n")

    assert result["failure_category"] == "GENERIC_POST_SPAWN_NONZERO_EXIT"
    assert result["original_exit_code"] == 1


def test_watchdog_timeout_takes_precedence_over_capacity_text() -> None:
    result = closeout.classify_transport_failure(
        _receipt(
            termination_initiator="PARENT_WATCHDOG",
            elapsed_to_exit_seconds=1800,
        ),
        f"{closeout.CAPACITY_DIAGNOSTIC}\n",
    )

    assert result["failure_category"] == "WATCHDOG_TIMEOUT"
    assert result["failure_lifecycle"] == "POST_SPAWN_TIMEOUT_FAILURE"


def test_pre_spawn_guard_does_not_expect_transport_receipt() -> None:
    result = closeout.classify_transport_failure(
        None, "", pre_spawn_guard_failure=True
    )

    assert result["failure_category"] == "PRE_SPAWN_GUARD_FAILURE"
    assert result["transport_receipt_expected"] is False


def test_missing_output_without_primary_diagnostic_is_classified() -> None:
    result = closeout.classify_transport_failure(
        _receipt(exit_code=0), "runtime completed without output\n"
    )

    assert (
        result["failure_category"]
        == "OUTPUT_MISSING_WITHOUT_PRIMARY_DIAGNOSTIC"
    )


def _write_json_member(
    archive: zipfile.ZipFile, member: str, value: object
) -> None:
    archive.writestr(member, json.dumps(value, sort_keys=True))


def _partial_first_fixture(path: Path) -> None:
    cohort = list(closeout.COHORT)
    contexts = [
        ("DIRECTIONAL_CORE", 1, cohort[0:4], True),
        ("DIRECTIONAL_CORE", 2, cohort[4:8], True),
        ("DIRECTIONAL_CORE", 3, cohort[8:12], True),
        ("DIRECTIONAL_CORE", 4, cohort[12:16], True),
        ("PRICE_TIMING", 1, cohort[0:4], True),
        ("PRICE_TIMING", 2, cohort[4:8], True),
        ("PRICE_TIMING", 3, cohort[8:12], False),
    ]
    with zipfile.ZipFile(path, "w") as archive:
        for stage, batch, subjects, succeeded in contexts:
            prefix = f"experiment/model-contexts/FIRST/{stage}/batch-{batch:02d}"
            _write_json_member(
                archive,
                f"{prefix}/context_manifest.json",
                {"stage": stage, "subjects": subjects},
            )
            _write_json_member(
                archive,
                f"{prefix}/transport_receipt.json",
                {
                    "invocation_id": f"{stage}:{batch}",
                    "stage": stage,
                    "batch_id": f"{batch:02d}",
                    "status": "PASS" if succeeded else "FAILED",
                },
            )
            if succeeded:
                _write_json_member(
                    archive,
                    f"{prefix}/output.raw.json",
                    {"candidates": [{"ticker": ticker} for ticker in subjects]},
                )


def test_partial_execution_reconciles_attempts_outputs_and_exposure(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "partial.zip"
    _partial_first_fixture(fixture)

    with zipfile.ZipFile(fixture) as archive:
        result = closeout.reconcile_partial_execution(archive)

    assert result["first_status"] == "FAILED"
    assert result["attempted_context_count"] == 7
    assert result["usable_output_context_count"] == 6
    assert result["failed_context_count"] == 1
    assert result["raw_stage_row_count"] == 24
    assert result["unique_exposed_issuer_count"] == 16
    assert result["per_stage"]["PRICE_TIMING"] == {
        "attempted_context_count": 3,
        "successful_context_count": 2,
        "output_subject_count": 8,
    }


def test_schedule_pause_state_classification_is_pure() -> None:
    assert (
        closeout.classify_schedule_pause_action(
            enabled=False, loaded=False, running=False
        )
        == "ALREADY_PAUSED"
    )
    assert (
        closeout.classify_schedule_pause_action(
            enabled=True, loaded=True, running=False
        )
        == "PAUSED_BY_TASK"
    )
    assert (
        closeout.classify_schedule_pause_action(
            enabled=True, loaded=True, running=True
        )
        == "BLOCKED_ACTIVE_RUN"
    )
    assert (
        closeout.classify_schedule_pause_action(
            enabled=True,
            loaded=True,
            running=False,
            out_of_scope_dependency=True,
        )
        == "BLOCKED_OUT_OF_SCOPE_DEPENDENCY"
    )


def test_production_accounting_counts_only_authorized_pause_objects() -> None:
    result = closeout.production_pause_accounting(
        {
            "pause_result": {
                "scheduler_objects_changed_count": 6,
                "authorized_schedule_change_count": 6,
                "unauthorized_schedule_change_count": 0,
            },
            "pause_transition_observation": {
                "scheduled_invocation_count": 1,
                "database_write_scope": "UNKNOWN_WITHIN_EXISTING_SAME_DAY_RUN",
            },
        }
    )

    assert result["authorized_logical_schedule_count"] == 2
    assert result["production_scheduler_change"] is True
    assert result["production_scheduler_change_count"] == 6
    assert result["unauthorized_schedule_change_count"] == 0
    assert result["investment_state_db_mutation"] == 0
    assert result["pause_transition_scheduled_invocation_count"] == 1
    assert result["production_telegram_send_initiated_by_task"] == 0
