from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from scripts import experiment_report_closeout_contract as closeout
from scripts import websocket_timeout_runtime_review_first_a_closeout as review


def _source_audit(*, current: bool = True) -> dict[str, object]:
    document: dict[str, object] = {
        "target_count": 2,
        "attempted_count": 3,
        "source_sufficient_count": 2,
        "source_insufficient_count": 1,
        "source_target_status": "PASS",
        "rows": [
            {
                "ticker": "ONE",
                "source_sufficiency_status": "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT",
                "fundamental_source_sufficient": True,
                "final_diagnostic_eligibility": "FUNDAMENTAL_SOURCE_SUFFICIENT",
            },
            {
                "ticker": "TWO",
                "source_sufficiency_status": "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT",
                "fundamental_source_sufficient": True,
                "final_diagnostic_eligibility": "FUNDAMENTAL_SOURCE_SUFFICIENT",
            },
            {
                "ticker": "THREE",
                "source_sufficiency_status": "INSUFFICIENT_FUNDAMENTAL_EVIDENCE",
                "fundamental_source_sufficient": False,
                "final_diagnostic_eligibility": "FUNDAMENTAL_SOURCE_INSUFFICIENT",
            },
        ],
    }
    if not current:
        document.update(
            {
                "pipeline_coverage_gap_count": 0,
                "source_absence_count": 1,
                "unknown_failure_count": 0,
            }
        )
        document.pop("rows")
    return document


def test_current_report_format_normalizes_without_legacy_aliases() -> None:
    result = closeout.normalize_completion_inputs(
        registry={
            "prior_registry_count": 5,
            "reconciled_registry_count": 7,
            "appended_exposed_issuer_count": 2,
            "rows": [{}, {}, {}, {}, {}, {}, {}],
            "all_excluded_issuer_keys": [f"issuer-{index}" for index in range(7)],
        },
        exclusion={
            "prior_count": 5,
            "appended_count": 2,
            "reconciled_count": 7,
            "excluded_issuer_keys": [f"issuer-{index}" for index in range(7)],
        },
        us_audit=_source_audit(),
        kr_audit=_source_audit(),
    )

    assert result["status"] == "PASS"
    assert result["canonical_fields"]["prior_real_issuer_exposure_registry_count"] == 5
    assert result["canonical_fields"]["new_holdout_exclusion_count"] == 7
    assert result["canonical_fields"]["us_source_absence_count"] == 1
    assert result["canonical_fields"]["us_pipeline_coverage_gap_count"] == 0


def test_supported_legacy_report_format_normalizes() -> None:
    result = closeout.normalize_completion_inputs(
        registry={"registry_count": 5},
        exclusion={"new_holdout_exclusion_count": 7},
        us_audit=_source_audit(current=False),
        kr_audit=_source_audit(current=False),
    )

    assert result["canonical_fields"]["prior_real_issuer_exposure_registry_count"] == 5
    assert result["canonical_fields"]["new_holdout_exclusion_count"] == 7
    assert result["canonical_fields"]["kr_unknown_failure_count"] == 0


def test_contradictory_dual_report_keys_fail_closed() -> None:
    with pytest.raises(closeout.ReportInputConflict, match="contradictory_report_count"):
        closeout.normalize_registry_report({"prior_registry_count": 5, "registry_count": 6})


def test_missing_and_explicit_unknown_are_not_numeric_zero() -> None:
    absent = closeout.resolve_count("field", [])
    unknown = closeout.resolve_count("field", [("field", None)])
    zero = closeout.resolve_count("field", [("field", 0)])

    assert absent == {
        "semantic": "field",
        "value": None,
        "status": "UNKNOWN_ABSENT",
        "sources": [],
    }
    assert unknown["status"] == "UNKNOWN_EXPLICIT"
    assert unknown["value"] is None
    assert zero["status"] == "RESOLVED"
    assert zero["value"] == 0


def test_websocket_warning_followed_by_pass_is_pass_with_warning() -> None:
    result = review.classify_runtime_receipt(
        {"status": "PASS", "retry_count": 0},
        "2026-09-07T00:00:01.000000Z  WARN codex_core::responses_retry: "
        "stream disconnected - retrying sampling request (1/5 in 202ms) "
        "WebSocket protocol error",
    )

    assert result["classification"] == "PASS_WITH_WARNING"
    assert result["observed_cli_retry_signal_count"] == 1
    assert result["wrapper_explicit_retry_count"] == 0


def test_websocket_warning_and_watchdog_timeout_preserve_both() -> None:
    result = review.classify_runtime_receipt(
        {
            "status": "TIMEOUT",
            "termination_initiator": "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
            "retry_count": 0,
        },
        "2026-09-07T00:00:01.000000Z  WARN codex_core::responses_retry: "
        "stream disconnected - retrying sampling request (1/5 in 202ms) "
        "WebSocket protocol error",
    )

    assert result["classification"] == ("WATCHDOG_TRANSPORT_TIMEOUT_AFTER_WEBSOCKET_DISCONNECT")
    assert result["observed_websocket_disconnect_signal_count"] == 1
    assert result["observed_cli_retry_signal_count"] == 1


def test_explicit_capacity_and_context_diagnostics_are_distinct() -> None:
    capacity = review.classify_runtime_receipt(
        {"status": "FAILED"},
        "2026-09-07T00:00:01Z ERROR codex_core::responses_retry: insufficient capacity for model",
    )
    context = review.classify_runtime_receipt(
        {"status": "FAILED"},
        "2026-09-07T00:00:01Z ERROR codex_core::responses_retry: maximum context length exceeded",
    )

    assert capacity["classification"] == "EXPLICIT_CAPACITY_DIAGNOSTIC"
    assert context["classification"] == "EXPLICIT_CONTEXT_LENGTH_DIAGNOSTIC"


def test_output_missing_alone_does_not_invent_upstream_cause() -> None:
    result = review.classify_runtime_receipt(
        {"status": "FAILED", "parse_error": "OUTPUT_FILE_MISSING"}, ""
    )

    assert result["classification"] == "OUTPUT_MISSING_CAUSE_UNRESOLVED"
    assert result["upstream_request_attempt_count"] == "UNKNOWN"


def test_prespawn_failure_is_not_postspawn_timeout() -> None:
    result = review.classify_runtime_receipt(
        {"status": "SPAWN_FAILED", "child_cleanup_status": "NO_CHILD_SPAWNED"},
        "",
    )

    assert result["classification"] == "PRESPAWN_FAILURE"


def test_no_retry_evidence_preserves_observability_limit() -> None:
    result = review.classify_runtime_receipt(
        {"status": "PASS", "request_accepted_observability": "UNAVAILABLE"}, ""
    )

    assert result["classification"] == "PASS"
    assert result["observed_cli_retry_signal_count"] == 0
    assert result["request_accepted_observability"] == "UNAVAILABLE"


def test_diagnostic_words_inside_prompt_are_not_runtime_events() -> None:
    prompt = (
        "user\nIf you see insufficient capacity or maximum context length, explain it.\n"
        "WebSocket protocol error and retrying sampling request are fixture words."
    )
    result = review.classify_runtime_receipt({"status": "PASS", "retry_count": 0}, prompt)

    assert result["classification"] == "PASS"
    assert result["runtime_event_count"] == 0
    assert result["observed_cli_retry_signal_count"] == 0


def test_minimal_schema_validator_enforces_const_order_and_extra_fields() -> None:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["contract", "rows"],
        "properties": {
            "contract": {"type": "string", "const": "fixture-v1"},
            "rows": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["ticker"],
                    "properties": {"ticker": {"type": "string", "const": "ONE"}},
                },
            },
        },
    }

    assert (
        review.validate_json_schema({"contract": "fixture-v1", "rows": [{"ticker": "ONE"}]}, schema)
        == []
    )
    assert review.validate_json_schema(
        {"contract": "fixture-v1", "rows": [{"ticker": "TWO", "extra": 1}]},
        schema,
    )


def test_historical_current_format_closes_after_terminal_failure(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source_root = (
        repo_root / "docs/reports/20260907-monitoring-pause-completion-fresh-issuer-ownership-proof"
    )
    destination = tmp_path / "reports/proofs"
    destination.mkdir(parents=True)
    names = (
        "03-prior-real-issuer-exposure-registry.json",
        "04-new-holdout-exclusion-set.json",
        "07-us-source-coverage-audit.json",
        "10-kr-source-coverage-audit.json",
        "62-reporting-closeout-recovery.json",
    )
    for name in names:
        shutil.copyfile(source_root / "proofs" / name, destination / name)
    before = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in names}

    result = review.normalize_historical_report_inputs(tmp_path)
    after = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in names}

    assert result["status"] == "PASS"
    assert result["original_error"].startswith("KeyError: registry_count")
    assert before == after
