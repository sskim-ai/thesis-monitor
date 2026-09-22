from __future__ import annotations

from copy import deepcopy

import pytest

from scripts import m12dc_fresh_source_use_two_pass_reproof as m12dc


def _context() -> dict[str, object]:
    return {
        "ticker": "TEST",
        "eligible_claim_refs": ["claim:one"],
        "premium_eligible_claim_refs": ["claim:one"],
        "data_quality_catalog": {"evidence_refs": []},
        "source_use_projection": {
            "execution_generation_id": "execution-a",
            "projection_sha256": "projection-a",
            "binding_sha256": "binding-a",
            "current_input_expectation_sha256": "expectation-a",
            "model_permission_view_sha256": "permission-view-a",
            "economic_permission": "ALLOW",
        },
        "source_evidence_binding": {
            "actual_final_view_sha256": "actual-a",
            "expected_final_view_sha256": "expected-a",
            "intermediate_receipt_sha256": "intermediate-a",
            "model_permission_view_sha256": "permission-view-a",
            "source_use_binding_sha256": "source-binding-a",
            "view_stage": "FINAL_POST_TYPED_QUALITY_FILTER",
        },
    }


def _chain() -> dict[str, object]:
    return {
        "source_generation_id": "source-generation",
        "authority": {"authority_manifest_sha256": "authority"},
        "expectation": {"expectation_sha256": "expectation"},
        "projection": {
            "projection_sha256": "projection",
            "permission_derivation_sha256": "permission",
        },
        "binding": {"binding_sha256": "binding"},
    }


def test_substantive_a_view_excludes_only_explicit_runtime_fields() -> None:
    original = _context()
    cleaned = m12dc._substantive_a_view(original)

    assert cleaned["source_use_projection"] == {"economic_permission": "ALLOW"}
    assert cleaned["source_evidence_binding"] == {"view_stage": "FINAL_POST_TYPED_QUALITY_FILTER"}
    assert original["source_use_projection"]["execution_generation_id"] == "execution-a"


def test_a_semantic_parity_ignores_runtime_receipts_but_detects_semantics(
    monkeypatch,
) -> None:
    monkeypatch.setattr(m12dc, "_expected_tickers", lambda: ["TEST"])
    baseline = _context()
    runtime_only = deepcopy(baseline)
    runtime_only["source_use_projection"]["execution_generation_id"] = "execution-b"
    runtime_only["source_use_projection"]["model_permission_view_sha256"] = "permission-view-b"
    runtime_only["source_evidence_binding"]["actual_final_view_sha256"] = "actual-b"
    runtime_only["source_evidence_binding"]["model_permission_view_sha256"] = "permission-view-b"

    assert m12dc._a_semantic_parity({"TEST": runtime_only}, {"TEST": baseline})["status"] == "PASS"

    changed = deepcopy(runtime_only)
    changed["source_use_projection"]["economic_permission"] = "DENY"
    assert m12dc._a_semantic_parity({"TEST": changed}, {"TEST": baseline})["status"] == "FAIL"


def test_planned_ledger_is_exactly_sixteen_unattempted_calls() -> None:
    ledger = m12dc._planned_ledger()

    assert len(ledger) == 16
    assert [row["ordinal"] for row in ledger] == list(range(1, 17))
    assert [row["stage"] for row in ledger].count("pass-a") == 8
    assert [row["stage"] for row in ledger].count("pass-b") == 8
    assert all(row["status"] == "PLANNED" for row in ledger)
    assert not any(row["wrapper_attempted"] for row in ledger)


def test_request_capture_freezes_provider_wire_not_internal_schema(tmp_path, monkeypatch) -> None:
    internal_schema = {
        "type": "object",
        "properties": {"classifications": {"type": "array"}},
    }
    wire_schema = {
        "type": "object",
        "properties": {"classifications": {"type": "array"}},
        "required": ["classifications"],
        "additionalProperties": False,
    }
    monkeypatch.setattr(m12dc, "future_pass_a_batch_schema", lambda **_: internal_schema)
    monkeypatch.setattr(
        m12dc,
        "schema_completeness_and_parity_scan",
        lambda *_args, **_kwargs: {"status": "PASS"},
    )
    monkeypatch.setattr(
        m12dc,
        "project_provider_wire_schema",
        lambda schema: (wire_schema, {"source_sha256": m12dc.canonical_sha256(schema)}),
    )
    monkeypatch.setattr(
        m12dc,
        "scan_provider_structured_output_schema",
        lambda _schema: {
            "status": "PASS",
            "unsupported_keyword_count": 0,
            "unique_items_count": 0,
        },
    )
    monkeypatch.setattr(m12dc, "future_pass_a_prompt_template", lambda: "template")
    monkeypatch.setattr(
        m12dc.m12db,
        "_prompt",
        lambda template, **_: f"prompt::{template}",
    )

    capture = m12dc._request_capture(
        root=tmp_path,
        stage="pass-a",
        market="us",
        batch=1,
        subjects=("TEST",),
        contexts={"TEST": _context()},
        catalogs={"TEST": {}},
        chains={"TEST": _chain()},
        generation_id="generation",
        fixture_only=False,
    )

    directory = tmp_path / "pass-a/us/batch-01"
    assert capture["status"] == "PASS"
    assert capture["transport_prompt"].endswith("prompt.txt")
    assert capture["transport_wire_schema"].endswith("provider-wire-schema.json")
    assert capture["internal_schema_not_submitted"] is True
    assert m12dc.read_json(directory / "internal-semantic-schema.json") == internal_schema
    assert m12dc.read_json(directory / "provider-wire-schema.json") == wire_schema
    with pytest.raises(m12dc.M12DCFailure, match="request_directory_already_frozen"):
        m12dc._request_capture(
            root=tmp_path,
            stage="pass-a",
            market="us",
            batch=1,
            subjects=("TEST",),
            contexts={"TEST": _context()},
            catalogs={"TEST": {}},
            chains={"TEST": _chain()},
            generation_id="generation",
            fixture_only=False,
        )


def test_b_only_ledger_never_plans_a_or_reuses_old_b() -> None:
    ledger = m12dc._planned_ledger(b_only=True)
    assert len(ledger) == 8
    assert all(row["stage"] == "pass-b" and row["status"] == "PLANNED" for row in ledger)
    assert sum(len(row["subjects"]) for row in ledger) == 22
    assert not any(row["semantic_accepted"] or row["wrapper_attempted"] for row in ledger)


def test_capture_does_not_allow_candidate_to_disable_source_use(tmp_path) -> None:
    cap = {"source_use_required": False}
    with pytest.raises(m12dc.M12DCFailure, match="pass_b_source_use_required"):
        m12dc._request_capture(
            root=tmp_path,
            stage="pass-b",
            market="us",
            batch=1,
            subjects=("TEST",),
            contexts={"TEST": {"pass_b_capability_catalog": cap}},
            catalogs={"TEST": {}},
            capabilities={"TEST": cap},
            chains={},
            generation_id="new",
            fixture_only=True,
        )


def test_transport_rejects_modified_captured_wire_before_attempt(tmp_path, monkeypatch) -> None:
    request = tmp_path / "request"
    request.mkdir()
    m12dc.write_text(request / "prompt.txt", "frozen prompt")
    m12dc.write_json(request / "provider-wire-schema.json", {"changed": True})
    m12dc.write_json(
        request / "request-receipt.json",
        {
            "file_sha256": {
                "prompt": m12dc.sha256_file(request / "prompt.txt"),
                "wire_schema": "frozen-original",
            }
        },
    )
    monkeypatch.setattr(m12dc, "_assert_execution_freeze", lambda *_: None)
    ledger = m12dc._planned_ledger(b_only=True)
    with pytest.raises(m12dc.M12DCFailure, match="outbound_capture_changed:wire_schema"):
        m12dc._invoke(
            stage="pass-b",
            market="us",
            batch=1,
            request_dir=request,
            result_root=tmp_path / "result",
            generation_id="test",
            runtime=None,
            codex_bin="unused",
            expected_head="test",
            code_hashes={},
            ledger=ledger,
        )
    assert not any(row["wrapper_attempted"] for row in ledger)


def test_b_only_report_distinguishes_fixture_partial_and_final_counts() -> None:
    ledger = m12dc._planned_ledger(b_only=True)
    ledger[0]["status"] = "PASS"
    report = m12dc._report(
        completion={
            "terminal": "M12DC_R1_PASS_B_FAILED",
            "mode": m12dc.R1_MODE,
            "accepted_a_fixture_subjects": 22,
            "newly_accepted_b_subjects": 3,
            "subject_count": 0,
            "wrapper_attempted_calls": 2,
        },
        ledger=ledger,
        distribution=None,
        comparison=None,
        validation=None,
    )
    assert "Accepted frozen M12DC A: `22/22`" in report
    assert "Newly accepted B subjects: `3/22`" in report
    assert "Complete final aggregate subjects: `0/22`" in report
    assert "Wrapper attempts: `2/8`" in report


def test_source_as_of_preserves_source_time_without_execution_substitution() -> None:
    source_packet = {
        "decision_evidence": [
            {"as_of": "2026-08-31", "period_end": "2026-06-30"},
            {"filing_date": "2026-09-02", "source_date": "2026-09-01"},
        ],
        "current_price": {"as_of": "2026-09-18T20:00:00Z"},
    }

    value = m12dc._source_as_of(source_packet)

    assert value["evidence_dates"] == [
        "2026-06-30",
        "2026-08-31",
        "2026-09-01",
        "2026-09-02",
    ]
    assert value["current_price_as_of"] == "2026-09-18T20:00:00Z"
    assert value["execution_time_is_not_source_time"] is True


def test_report_uses_terminal_and_actual_ledger_state() -> None:
    ledger = m12dc._planned_ledger()
    ledger[0]["status"] = "PASS"
    ledger[8]["status"] = "FAIL"
    completion = {
        "terminal": m12dc.PASS_B_FAILED,
        "generation_id": "generation",
        "implementation_commit": "implementation",
        "work_instruction_commit": "instruction",
        "subject_count": 0,
        "wrapper_attempted_calls": 2,
        "blocker": {"stage": "PASS_B", "safe_error_code": "semantic_failure"},
    }

    report = m12dc._report(
        completion=completion,
        ledger=ledger,
        distribution=None,
        comparison=None,
        validation=None,
    )

    assert f"Terminal: `{m12dc.PASS_B_FAILED}`" in report
    assert "Pass A: `1/8` batches" in report
    assert "Pass B: `0/8` batches" in report
    assert "Wrapper attempts: `2/16`" in report
    assert '"stage": "PASS_B"' in report


@pytest.mark.parametrize(
    "drift",
    [
        "prompt",
        "wire_schema",
        "context",
        "internal_schema",
        "ref_catalog",
        "source_binding",
        "capability_catalog",
        "request_identity",
    ],
)
def test_b_frozen_surface_drift_stops_before_transport(tmp_path, monkeypatch, drift):
    request = tmp_path / "request"
    request.mkdir()
    files = {
        "prompt": "prompt.txt",
        "wire_schema": "provider-wire-schema.json",
        "context": "subject-context.json",
        "internal_schema": "internal-semantic-schema.json",
        "ref_catalog": "ref-catalog.json",
        "source_binding": "source-use-and-consumed-source-binding.json",
        "capability_catalog": "capability-catalog.json",
    }
    for filename in files.values():
        (request / filename).write_text("frozen")
    receipt = {
        "stage": "pass-b",
        "market": "us",
        "batch": 1,
        "subjects": ["TEST"],
        "model": "gpt-5.6-sol",
        "effort": "xhigh",
        "timeout_seconds": 1200,
        "execution_generation_id": "generation",
        "request_composition": "CAPABILITY_AWARE_FINAL",
        "file_sha256": {k: m12dc.sha256_file(request / v) for k, v in files.items()},
    }
    receipt["request_sha256"] = m12dc.canonical_sha256(receipt)
    if drift == "request_identity":
        receipt["request_sha256"] = "changed"
    else:
        (request / files[drift]).write_text("changed")
    m12dc.write_json(request / "request-receipt.json", receipt)
    monkeypatch.setattr(m12dc, "_assert_execution_freeze", lambda *_: None)
    ledger = m12dc._planned_ledger(b_only=True)
    with pytest.raises(
        m12dc.M12DCFailure,
        match="request_identity_drift"
        if drift == "request_identity"
        else f"outbound_capture_changed:{drift}",
    ):
        m12dc._invoke(
            stage="pass-b",
            market="us",
            batch=1,
            request_dir=request,
            result_root=tmp_path / "result",
            generation_id="generation",
            runtime=None,
            codex_bin="unused",
            expected_head="test",
            code_hashes={},
            ledger=ledger,
            official_binding=object(),
        )
    assert not any(row["wrapper_attempted"] for row in ledger)
