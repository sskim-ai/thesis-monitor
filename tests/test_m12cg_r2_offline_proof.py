from __future__ import annotations

import json

from scripts.m12cg_r2_offline_proof import (
    aggregate_fixture_rows,
    artifact_manifest,
    dynamic_aggregation_negative_controls,
)


def _row(
    result: str,
    *,
    denominator: int = 1,
    evidence: list[object] | None = None,
) -> dict[str, object]:
    return {
        "fixture_id": "fixture",
        "assertion_result": result,
        "denominator": denominator,
        "evidence": [{}] if evidence is None else evidence,
    }


def test_m12cg_r2_fixture_aggregation_pass_requires_measured_evidence() -> None:
    result = aggregate_fixture_rows([_row("PASS")])

    assert result["status"] == "PASS"
    assert result["proven_count"] == 1
    assert result["unsupported_group_pass_count"] == 0


def test_m12cg_r2_fixture_aggregation_failure_cannot_be_parent_pass() -> None:
    result = aggregate_fixture_rows([_row("FAIL")])

    assert result["status"] == "FAIL"
    assert result["failed_fixtures"] == ["fixture"]


def test_m12cg_r2_fixture_aggregation_not_proven_is_partial() -> None:
    result = aggregate_fixture_rows([_row("NOT_PROVEN")])

    assert result["status"] == "PARTIAL"
    assert result["not_proven_fixtures"] == ["fixture"]


def test_m12cg_r2_fixture_aggregation_pass_without_denominator_fails() -> None:
    result = aggregate_fixture_rows(
        [_row("PASS", denominator=0, evidence=[])]
    )

    assert result["status"] == "FAIL"
    assert result["unsupported_group_pass_fixtures"] == ["fixture"]


def test_m12cg_r2_dynamic_aggregation_negative_controls_all_pass() -> None:
    result = dynamic_aggregation_negative_controls()

    assert result["status"] == "PASS"
    assert {row["case"]: row["observed"] for row in result["cases"]} == {
        "assertion_failure": "FAIL",
        "assertion_skipped": "PARTIAL",
        "assertion_absent": "FAIL",
        "complete_pass": "PASS",
    }


def test_m12cg_r2_artifact_manifest_excludes_itself(tmp_path) -> None:
    (tmp_path / "payload.json").write_text(
        json.dumps({"value": 1}),
        encoding="utf-8",
    )
    (tmp_path / "artifact-manifest.json").write_text(
        "stale manifest",
        encoding="utf-8",
    )

    result = artifact_manifest(tmp_path)

    assert result["manifest_self_excluded"] is True
    assert result["artifact_count"] == 1
    assert [row["path"] for row in result["artifacts"]] == ["payload.json"]
