from __future__ import annotations

import json
import zipfile
from pathlib import Path

from pydantic import BaseModel, ValidationError

from scripts.natural_proof_structured_autonomy_blind_program import (
    COHORT,
    _blind_key_leaks,
    _safe_validation_failure,
    _write_incomplete_reports,
    directory_payload_sha256,
    external_template,
)


def test_blind_key_leak_scan_rejects_ai_judgment_fields() -> None:
    document = {
        "identity": {"ticker": "TEST"},
        "facts": [{"fact_id": "F1", "statement": "reported revenue"}],
        "new_buyer_view": {"stance": "WAIT"},
    }

    assert _blind_key_leaks(document) == ["$.new_buyer_view"]


def test_blind_key_leak_scan_allows_raw_fact_shape() -> None:
    document = {
        "identity": {"ticker": "TEST", "market": "us"},
        "facts": [
            {
                "fact_id": "F1",
                "category": "earnings",
                "statement": "reported revenue",
                "value": "100",
                "unit_or_currency": "USD",
            }
        ],
    }

    assert _blind_key_leaks(document) == []


def test_external_template_has_neutral_complete_cohort() -> None:
    document = external_template("generation-test")

    assert document["status"] == "DRAFT_NOT_FROZEN"
    assert [row["ticker"] for row in document["subjects"]] == sorted(COHORT)
    assert all(row["overall_direction"] is None for row in document["subjects"])
    assert all(row["core_positive_evidence_fact_ids"] == [] for row in document["subjects"])


def test_directory_payload_sha_ignores_manifest(tmp_path: Path) -> None:
    subject = tmp_path / "subjects" / "TEST.json"
    subject.parent.mkdir()
    subject.write_text(json.dumps({"fact_id": "F1"}), encoding="utf-8")
    before = directory_payload_sha256(tmp_path)
    (tmp_path / "manifest.json").write_text(
        json.dumps({"self_hash": "different"}), encoding="utf-8"
    )

    assert directory_payload_sha256(tmp_path) == before


def test_safe_validation_failure_omits_input_payload() -> None:
    class Document(BaseModel):
        value: int

    try:
        Document.model_validate({"value": "secret-not-an-integer"})
    except ValidationError as exc:
        receipt = _safe_validation_failure(exc)
    else:  # pragma: no cover - pydantic must reject the fixture
        raise AssertionError("validation error expected")

    assert receipt["exception_type"] == "ValidationError"
    assert receipt["details"] == [
        {
            "location": "value",
            "type": "int_parsing",
            "message": "Input should be a valid integer, unable to parse string as an integer",
        }
    ]
    assert "secret-not-an-integer" not in json.dumps(receipt)


def test_incomplete_reports_close_blind_bundle_without_ai_pack(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    public_reports = tmp_path / "public"
    sealed_reports = output_root / "sealed" / "reports"
    machine_dir = output_root / "machine"
    review_root = output_root / "review-intake"
    blind_root = review_root / "BLIND_FACT_PACK"
    blind_root.mkdir(parents=True)
    (blind_root / "manifest.json").write_text("{}", encoding="utf-8")
    (review_root / "COMPARISON_PROTOCOL.md").write_text("blind", encoding="utf-8")
    (review_root / "external-comparison-template.json").write_text(
        "{}", encoding="utf-8"
    )
    run_document = {
        "validation_pass_count": 22,
        "validation": [{"status": "PASS"}],
        "message_quality": {"status": "PASS"},
    }
    result = _write_incomplete_reports(
        output_root=output_root,
        public_reports=public_reports,
        sealed_reports=sealed_reports,
        machine_dir=machine_dir,
        review_root=review_root,
        generation_id="generation-test",
        source_lock={
            "sources": {
                "us": {"assessment_date": "2026-09-05"},
                "kr": {"assessment_date": "2026-09-04"},
            }
        },
        run_documents={
            "first": run_document,
            "a": run_document,
            "b": run_document,
        },
        failed_run="c",
        failure={"exception_type": "ValidationError", "details": []},
        blind_manifest={
            "blind_pack_sha256": "blind-sha",
            "ai_judgment_leakage_count": 0,
        },
        ai_manifest={"ai_decision_pack_sha256": "ai-sha"},
    )

    promotion = json.loads((machine_dir / "promotion-review.json").read_text())
    assert promotion["a_b_c_gate"] == "RUN_INCOMPLETE"
    assert promotion["run_c_validated"] == "OTHER"
    assert promotion["validation_triggered_rerun"] == 0
    assert promotion["approved_infrastructure_resume_count"] == 1
    assert promotion["promotion_readiness"] == "NEEDS_MORE_SHADOW_WORK"
    assert (public_reports / "20260905-run-c.md").is_file()
    assert json.loads((machine_dir / "run-c.json").read_text())["status"] == (
        "FAILED_SCHEMA_VALIDATION"
    )
    with zipfile.ZipFile(result["blind_intake_zip"]) as archive:
        names = archive.namelist()
    assert "BLIND_FACT_PACK/manifest.json" in names
    assert all(not name.startswith("AI_DECISION_PACK/") for name in names)
    first_zip = Path(result["blind_intake_zip"]).read_bytes()

    repeated = _write_incomplete_reports(
        output_root=output_root,
        public_reports=public_reports,
        sealed_reports=sealed_reports,
        machine_dir=machine_dir,
        review_root=review_root,
        generation_id="generation-test",
        source_lock={
            "sources": {
                "us": {"assessment_date": "2026-09-05"},
                "kr": {"assessment_date": "2026-09-04"},
            }
        },
        run_documents={
            "first": run_document,
            "a": run_document,
            "b": run_document,
        },
        failed_run="c",
        failure={"exception_type": "ValidationError", "details": []},
        blind_manifest={
            "blind_pack_sha256": "blind-sha",
            "ai_judgment_leakage_count": 0,
        },
        ai_manifest={"ai_decision_pack_sha256": "ai-sha"},
    )
    assert Path(repeated["blind_intake_zip"]).read_bytes() == first_zip
