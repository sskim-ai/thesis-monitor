from __future__ import annotations

from pathlib import Path

from scripts.nonproduction_integration_decision_message_review import (
    DERIVATIVE_LABEL,
    artifact_index,
    classify_repetition_root_cause,
    file_only_comparison,
)


def test_file_only_comparison_covers_lifecycle_and_negative_controls(
    tmp_path: Path,
) -> None:
    result = file_only_comparison(tmp_path)
    names = {row["name"] for row in result["rows"]}

    assert result["status"] == "PASS"
    assert result["failure_count"] == 0
    assert {
        "initial-absolute-new-issuer",
        "monitoring-baseline-existing-issuer",
        "daily-no-material-change",
        "daily-strengthened",
        "daily-weakened",
        "daily-price-only",
        "daily-refresh-missing",
        "initial-price-unavailable",
        "initial-unknown-confidence-limit",
        "initial-confirmed-risk",
    }.issubset(names)
    for row in result["rows"]:
        message = (tmp_path / row["message_path"]).read_text(encoding="utf-8")
        assert message.startswith(DERIVATIVE_LABEL)
        assert row["queue_writes"] == 0
        assert row["production_sends"] == 0


def test_repetition_root_cause_preserves_model_renderer_ownership() -> None:
    model = classify_repetition_root_cause(
        {
            "span": "BUY 쪽: 후속 공식 공시에서 이익을 확인합니다.",
            "ownership_counts": {"MODEL_CONTENT_WITH_RENDERER_WRAPPER": 3},
        }
    )
    renderer = classify_repetition_root_cause(
        {
            "span": "고정된 구조 문구",
            "ownership_counts": {"RENDERER_INTRODUCED_OR_UNRESOLVED": 2},
        }
    )
    mixed = classify_repetition_root_cause(
        {
            "span": "현재 실적 근거는 확인됐습니다.",
            "ownership_counts": {"MODEL_OWNED_SUBSTANTIVE": 2},
        }
    )

    assert model == "MODEL_GENERIC_REEVALUATION_LANGUAGE"
    assert renderer == "RENDERER_TEMPLATE_REPETITION"
    assert mixed == "MIXED"


def test_artifact_index_excludes_itself_and_hashes_payloads(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "artifact-index.json").write_text("stale", encoding="utf-8")

    index = artifact_index(tmp_path)

    assert index["status"] == "PASS"
    assert index["payload_count"] == 1
    assert index["rows"][0]["path"] == "a.txt"
    assert index["rows"][0]["bytes"] == 1
