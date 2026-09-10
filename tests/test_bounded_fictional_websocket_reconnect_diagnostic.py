from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import bounded_fictional_websocket_reconnect_diagnostic as diagnostic


def receipt(
    *,
    status: str = "PASS",
    exit_code: int | None = 0,
    termination: str = "NONE",
) -> dict[str, object]:
    return {
        "status": status,
        "exit_code": exit_code,
        "termination_initiator": termination,
        "child_cleanup_status": "NOT_NEEDED",
        "retry_count": 0,
        "request_accepted_observability": "UNAVAILABLE",
    }


def classify(value: dict[str, object], stderr: str = "") -> dict[str, object]:
    return diagnostic.classify_attempt(
        value,
        stderr,
        schema_valid=True,
        identity_valid=True,
        preservation_valid=True,
    )


def test_classifies_ordinary_success_without_runtime_warning() -> None:
    result = classify(receipt())

    assert result["outcome"] == "VALID_OUTPUT_NO_DISCONNECT"
    assert result["usable"] is True
    assert result["observed_cli_retry_signal_count"] == 0
    assert result["observed_websocket_disconnect_signal_count"] == 0


def test_classifies_disconnect_warning_followed_by_success() -> None:
    stderr = (
        "2026-09-07T01:02:03.000000Z WARN codex_core::responses_retry: "
        "stream disconnected before completion: websocket reset; retrying sampling request\n"
    )

    result = classify(receipt(), stderr)

    assert result["outcome"] == "DISCONNECT_THEN_SUCCESS_OBSERVED"
    assert result["usable"] is True
    assert result["observed_cli_retry_signal_count"] == 1
    assert result["observed_websocket_disconnect_signal_count"] == 1


def test_classifies_disconnect_warning_followed_by_watchdog_timeout() -> None:
    stderr = (
        "2026-09-07T01:02:03.000000Z WARN codex_core::responses_retry: "
        "websocket stream disconnected; retrying sampling request\n"
    )
    timed_out = receipt(
        status="TIMEOUT",
        exit_code=-15,
        termination="PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
    )

    result = classify(timed_out, stderr)

    assert result["outcome"] == "DISCONNECT_THEN_WATCHDOG_TIMEOUT_OBSERVED"
    assert result["stop_remaining_calls"] is True


@pytest.mark.parametrize(
    ("message", "outcome"),
    (
        ("model capacity exhausted", "EXPLICIT_CAPACITY_FAILURE_OBSERVED"),
        ("maximum context length exceeded", "EXPLICIT_CONTEXT_FAILURE_OBSERVED"),
    ),
)
def test_classifies_explicit_capacity_and_context_diagnostics(message: str, outcome: str) -> None:
    stderr = f"2026-09-07T01:02:03.000000Z ERROR codex_core::client: {message}\n"

    result = classify(receipt(status="FAILED", exit_code=1), stderr)

    assert result["outcome"] == outcome
    assert result["stop_remaining_calls"] is True


def test_quoted_or_echoed_warning_is_not_a_runtime_event() -> None:
    stderr = (
        "Prompt example: 2026-09-07T01:02:03.000000Z WARN "
        "codex_core::responses_retry: websocket disconnected; retrying sampling request\n"
        '{"text":"websocket disconnected; retrying sampling request"}\n'
    )

    result = classify(receipt(), stderr)

    assert result["outcome"] == "VALID_OUTPUT_NO_DISCONNECT"
    assert result["observed_cli_retry_signal_count"] == 0
    assert result["observed_websocket_disconnect_signal_count"] == 0


class BusyObserver:
    backend = "TEST_BUSY_OBSERVER"
    capabilities = {"protected_window_observable": True}

    def observe(self) -> dict[str, object]:
        return {
            "active_natural_job_count": 1,
            "running_model_process_count": 0,
        }


def test_pre_spawn_guard_rejection_creates_no_transport_receipt(tmp_path: Path) -> None:
    audit = tmp_path / "guard.json"
    guard = diagnostic.SingleObservationWorkloadGuard(audit, observer=BusyObserver())

    result = guard.preflight(stage="DIRECTIONAL_CORE", batch_id="call-01", subject_count=4)

    assert result["status"] == "DEFER"
    assert result["safe_to_spawn"] == 0
    assert not list(tmp_path.glob("*receipt*"))
    proof = json.loads(audit.read_text(encoding="utf-8"))
    assert proof["events"][0]["action"] == "PAUSE"


def test_preserves_exact_safe_attempt_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    source_receipt = source / "receipt.json"
    source_stdout = source / "stdout.log"
    source_stderr = source / "stderr.log"
    source_output = source / "output.json"
    source_receipt.write_text('{"status":"PASS"}\n', encoding="utf-8")
    source_stdout.write_text("ordinary stdout\n", encoding="utf-8")
    source_stderr.write_text("ordinary stderr\n", encoding="utf-8")
    source_output.write_text('{"contract":"fixture"}\n', encoding="utf-8")

    result = diagnostic.preserve_attempt_artifacts(
        source_receipt=source_receipt,
        source_stdout=source_stdout,
        source_stderr=source_stderr,
        source_output=source_output,
        destination=destination,
        require_receipt=True,
    )

    assert result["status"] == "PASS"
    assert (destination / "transport_receipt.json").read_bytes() == source_receipt.read_bytes()
    assert (destination / "output.raw.json").read_bytes() == source_output.read_bytes()
    assert all(row["exact_bytes"] is True for row in result["rows"])


def test_missing_required_receipt_is_preservation_failure_and_stop(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    result = diagnostic.preserve_attempt_artifacts(
        source_receipt=source / "missing.json",
        source_stdout=source / "missing.stdout",
        source_stderr=source / "missing.stderr",
        source_output=source / "missing.output",
        destination=tmp_path / "destination",
        require_receipt=True,
    )
    classification = diagnostic.classify_attempt(
        receipt(),
        "",
        schema_valid=True,
        identity_valid=True,
        preservation_valid=result["status"] == "PASS",
    )

    assert result["status"] == "FAIL"
    assert result["evidence_preservation_failure_count"] == 1
    assert classification["outcome"] == "EVIDENCE_PRESERVATION_FAILURE"
    assert classification["stop_remaining_calls"] is True


def test_fixed_fixture_is_fictional_us4_and_comparable_core_size(monkeypatch) -> None:
    # This historical transport comparison holds its pre-M12E/M12Y prompt fixed.
    prior = Path("fixtures/pre_m12e_ordinal_calibration_prompt.txt").read_text().strip()
    current_core_prompt = diagnostic.frozen._core_prompt
    monkeypatch.setattr(
        diagnostic.frozen, "directional_balance_ordinal_calibration_prompt", lambda: prior
    )
    monkeypatch.setattr(
        diagnostic.frozen,
        "_core_prompt",
        lambda **kwargs: current_core_prompt(**kwargs).replace(
            "\n\n" + diagnostic.frozen.BUSINESS_THESIS_CHANGE_PROMPT + "\n\n",
            "\n\n",
        ),
    )
    generation = "20260907-fictional-websocket-diagnostic-20260907T000000Z-000000000000"

    owned, _catalogs, prompt, schema = diagnostic.build_fixture(generation)
    audit = diagnostic.fixture_audit(owned)

    assert audit["status"] == "PASS"
    assert tuple(owned) == diagnostic.SUBJECTS
    assert 15_000 <= len(prompt.encode("utf-8")) <= 20_000
    assert schema["properties"]["packet_id"]["const"] == generation
    assert set(diagnostic.SUBJECTS).isdisjoint(diagnostic.HISTORICAL_REAL_COHORT)


def test_schema_or_identity_failure_stops() -> None:
    schema_failure = diagnostic.classify_attempt(
        receipt(),
        "",
        schema_valid=False,
        identity_valid=True,
        preservation_valid=True,
    )
    identity_failure = diagnostic.classify_attempt(
        receipt(),
        "",
        schema_valid=True,
        identity_valid=False,
        preservation_valid=True,
    )

    assert schema_failure["outcome"] == "SCHEMA_INVALID_RESULT"
    assert identity_failure["outcome"] == "IDENTITY_INVALID_RESULT"
    assert schema_failure["stop_remaining_calls"] is True
    assert identity_failure["stop_remaining_calls"] is True
