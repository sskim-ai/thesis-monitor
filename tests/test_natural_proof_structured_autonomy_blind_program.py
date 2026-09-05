from __future__ import annotations

import json
from pathlib import Path

from scripts.natural_proof_structured_autonomy_blind_program import (
    COHORT,
    _blind_key_leaks,
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
