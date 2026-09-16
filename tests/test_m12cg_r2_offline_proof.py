from __future__ import annotations

import json

from scripts.m12cg_r2_offline_proof import (
    aggregate_fixture_rows,
    artifact_manifest,
    dynamic_aggregation_negative_controls,
    matching_nodes,
    semantic_loss_proof,
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


def test_m12cg_r2_matching_nodes_deduplicates_focused_and_full_results() -> None:
    node = {
        "node_id": "tests/test_example.py::test_case[value]",
        "status": "PASS",
    }

    result = matching_nodes([node, dict(node)], ["test_case"])

    assert result == [node]


def test_m12cg_r2_semantic_loss_uses_full_candidate_payload(tmp_path) -> None:
    probe_root = tmp_path / "runtime-probes" / "after-r2"
    candidate_path = probe_root / "fresh" / "SKHY.candidate.json"
    candidate_path.parent.mkdir(parents=True)
    candidate = {
        "ticker": "SKHY",
        "driver_maturity": [
            {
                "driver": "symbolic limitation",
                "supporting_evidence_refs": ["financial-quality:SKHY"],
                "contradicting_evidence_refs": [],
                "as_of": None,
                "provenance_status": "SYMBOLIC_ONLY_NO_CONCRETE_DATE",
            },
            {
                "driver": "concrete row",
                "supporting_evidence_refs": ["price:SKHY"],
                "contradicting_evidence_refs": [],
                "as_of": "2026-09-15",
                "provenance_status": "CONCRETE_ONLY",
            },
        ],
    }
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    probe = {
        "fresh": {
            "candidates": [
                {
                    "ticker": "SKHY",
                    "payload": {"path": candidate_path.name},
                    "rows": [
                        {
                            "row_index": 0,
                            "driver": "symbolic limitation",
                            "provenance_status": (
                                "SYMBOLIC_ONLY_NO_CONCRETE_DATE"
                            ),
                        },
                        {
                            "row_index": 1,
                            "driver": "concrete row",
                            "provenance_status": "CONCRETE_ONLY",
                        },
                    ],
                }
            ]
        }
    }

    result = semantic_loss_proof(
        probe,
        current_probe_root=probe_root,
        out=tmp_path / "report",
    )

    assert result["status"] == "PASS"
    assert result["original_row_count"] == 2
    assert result["mutated_row_count"] == 1
    assert result["deleted_row"]["supporting_evidence_refs"] == [
        "financial-quality:SKHY"
    ]
    assert result["source_candidate_sha256"] != result[
        "mutated_candidate_sha256"
    ]
