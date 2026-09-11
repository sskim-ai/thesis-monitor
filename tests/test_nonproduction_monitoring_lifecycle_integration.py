from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from scripts import nonproduction_monitoring_lifecycle_integration as lifecycle_script
from scripts.nonproduction_monitoring_lifecycle_integration import (
    artifact_index,
    production_boundary_lifecycle_proof,
    run_fixture_program,
)


def test_latest_result_verifier_accepts_prior_bytes_size_field(
    tmp_path: Path,
    monkeypatch,
) -> None:
    completion = {
        "status": "M2_COMPLETE",
        "next_scope": (
            "NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION"
        ),
        "final_head_sha": lifecycle_script.EXPECTED_M2_FINAL_SHA,
    }
    payloads = {
        "27-program-completion.json": json.dumps(completion).encode(),
        **{
            f"payload-{number:02d}.json": json.dumps({"number": number}).encode()
            for number in range(38)
        },
    }
    index = {
        "status": "PASS",
        "payload_count": len(payloads),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": 0,
        "rows": [
            {
                "path": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
            }
            for name, payload in payloads.items()
        ],
    }
    path = tmp_path / "m2.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr("artifact-index.json", json.dumps(index).encode())
    monkeypatch.setattr(
        lifecycle_script,
        "EXPECTED_LATEST_RESULT_SHA256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )

    result = lifecycle_script.verify_latest_result(path)

    assert result["status"] == "PASS"
    assert result["size_mismatches"] == []


def test_required_fixture_program_passes_without_side_effects(tmp_path: Path) -> None:
    result = run_fixture_program(tmp_path / "messages")

    assert result["status"] == "PASS"
    assert result["fixture_count"] == 12
    assert result["fixture_pass_count"] == 12
    assert result["fixture_fail_count"] == 0
    assert result["message_count"] == 12
    assert result["all_messages_labeled"] is True
    assert result["all_message_sections_present"] is True
    assert result["side_effect_firewall_status"] == "PASS"
    assert result["registration_proof"]["status"] == "PASS"
    assert result["idempotency_warning_proof"]["status"] == "PASS"
    assert result["new_existing_contract_equivalence"]["status"] == "PASS"
    assert result["daily_delta_lineage"]["status"] == "PASS"


def test_existing_registration_and_onboarding_boundaries_run_on_isolated_sqlite(
    tmp_path: Path,
) -> None:
    proof = production_boundary_lifecycle_proof(tmp_path)

    assert proof["status"] == "PASS"
    assert proof["thesis_version_count"] == 1
    assert proof["baseline_assessment_count"] == 1
    assert proof["daily_delta_assessment_count"] == 1
    assert proof["monitor_run_count"] == 1
    assert proof["notification_row_count"] == 0
    assert proof["production_db_connections"] == 0
    assert proof["provider_source_fetches"] == 0
    assert proof["model_calls"] == 0
    assert proof["notification_queue_writes"] == 0
    assert proof["production_sends"] == 0


def test_fixture_messages_cover_required_semantics(tmp_path: Path) -> None:
    result = run_fixture_program(tmp_path / "messages")
    rows = {row["fixture_id"]: row for row in result["rows"]}

    assert rows["M3-01"]["subject"]["monitoring_ready"] is False
    assert rows["M3-02"]["assessment"] is None
    assert rows["M3-03"]["subject"]["monitoring_ready"] is True
    assert rows["M3-04"]["actual_status"] == "no_material_change"
    assert rows["M3-05"]["actual_status"] == "strengthened"
    assert rows["M3-06"]["actual_status"] == "weakened"
    assert rows["M3-07"]["actual_status"] == "invalidation_candidate"
    assert rows["M3-08"]["actual_status"] == "needs_review"
    assert rows["M3-09"]["assessment"]["price_evidence_ids"] == ["price-only"]
    assert rows["M3-10"]["assessment"]["supply_evidence_ids"] == ["supply-only"]
    assert rows["M3-11"]["assessment"]["valuation_context"] == "compression"
    assert rows["M3-12"]["assessment"]["business_evidence_ids"] == []
    assert rows["M3-12"]["assessment"]["lineage"]["prebaseline_enrichment_ids"] == [
        "late-prebaseline"
    ]


def test_artifact_index_hashes_payloads_and_excludes_itself(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    (tmp_path / "message.txt").write_text("safe derivative\n", encoding="utf-8")
    (tmp_path / "artifact-index.json").write_text("stale", encoding="utf-8")

    index = artifact_index(tmp_path)

    assert index["status"] == "PASS"
    assert index["payload_count"] == 2
    assert {row["path"] for row in index["rows"]} == {"a.json", "message.txt"}
    assert index["secret_scan_failure_count"] == 0
