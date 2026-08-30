from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"
REQUIRED_REPORTS = (
    "20260830-v2-accepted-decision-root-cause.md",
    "20260830-v2-accepted-decision-contract.md",
    "20260830-v2-candidate-vs-accepted-20.md",
    "20260830-v2-five-adjudication-ownership-controls.md",
    "20260830-v2-accepted-reasoning-controls.md",
    "20260830-v2-accepted-distribution.md",
    "20260830-v2-completion-summary-errata.md",
    "20260830-v2-accepted-renderer-validator.md",
    "20260830-v2-accepted-test-sink.md",
    "20260830-v2-accepted-message-quality.md",
    "20260830-v2-accepted-migration-readiness.md",
    "20260830-v2-accepted-artifact-index.md",
    "20260830-v2-accepted-decisions.json",
    "20260830-v2-accepted-migration-readiness.json",
    "20260830-v2-accepted-test-sink-receipt.json",
)
SOURCE_SHA256 = {
    "20260830-current-20-v2-shadow-decisions.json": (
        "723580ff3fe926eb1507ed066afefbb276cabee3a99bd555dd56df57e3eb7583"
    ),
    "20260830-v1-v2-decision-agreement.json": (
        "bbbbb4c6303a18296c510eddbf47eda50f40b2a958668851069600698d79befb"
    ),
}


def _json(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_required_accepted_ownership_artifacts_exist() -> None:
    assert all((REPORTS / name).is_file() for name in REQUIRED_REPORTS)
    assert (ROOT / "docs/architecture/V2_ACCEPTED_DECISION_OWNERSHIP.md").is_file()
    assert (ROOT / "docs/architecture/DECISION_ENGINE_V2_SHADOW_MIGRATION.md").is_file()


def test_accepted_decisions_are_explicit_and_complete() -> None:
    artifact = _json("20260830-v2-accepted-decisions.json")
    assert artifact["status"] == "PASS"
    assert artifact["subject_count"] == 20
    assert artifact["candidate_distribution"] == {"BUY": 2, "HOLD": 14, "SELL": 4}
    assert artifact["accepted_distribution"] == {"BUY": 1, "HOLD": 16, "SELL": 3}

    rows = artifact["rows"]
    assert isinstance(rows, list) and len(rows) == 20
    by_ticker = {row["ticker"]: row for row in rows}
    expected = {
        "003690": ("BUY", "HOLD", "KEEP_V1", "ADJUDICATION_KEEP_V1"),
        "GOOGL": ("BUY", "BUY", "KEEP_V2", "ADJUDICATION_KEEP_V2"),
        "HUT": ("SELL", "SELL", "KEEP_V2", "ADJUDICATION_KEEP_V2"),
        "RXRX": ("HOLD", "HOLD", "KEEP_V2", "ADJUDICATION_KEEP_V2"),
        "SNDK": ("SELL", "HOLD", "KEEP_V1", "ADJUDICATION_KEEP_V1"),
    }
    for ticker, values in expected.items():
        row = by_ticker[ticker]
        assert (
            row["candidate_history"]["candidate_decision"],
            row["accepted_plan"]["accepted_decision"],
            row["adjudication_history"]["recommendation"],
            row["accepted_plan"]["accepted_source"],
        ) == values

    assert by_ticker["003690"]["accepted_plan"]["accepted_preconfirmation_buy"] is False
    assert by_ticker["GOOGL"]["accepted_plan"]["accepted_preconfirmation_buy"] is True
    assert len({row["accepted_plan"]["accepted_decision_id"] for row in rows}) == 20
    assert all("decision" not in row for row in rows)
    assert all(
        row["rendered"]["accepted_decision"]
        == row["accepted_plan"]["accepted_decision"]
        for row in rows
    )


def test_readiness_and_test_sink_use_accepted_authority_without_secrets() -> None:
    readiness = _json("20260830-v2-accepted-migration-readiness.json")
    receipt = _json("20260830-v2-accepted-test-sink-receipt.json")
    assert readiness["status"] == "PASS"
    assert readiness["accepted_distribution"] == {"BUY": 1, "HOLD": 16, "SELL": 3}
    assert readiness["open_p0"] == []
    assert readiness["open_material_p1"] == []
    assert readiness["migration_recommendation"] == "READY_WITH_OBSERVATION"
    assert readiness["next_action"] == "REVIEW_ACCEPTED_V2_MESSAGES"
    assert all(
        value not in {"FAIL", "NOT_READY"} for value in readiness["gates"].values()
    )

    assert receipt["status"] == "PASS"
    assert receipt["planned_message_count"] == 20
    assert receipt["sent_message_count"] == 20
    assert receipt["receipt_count"] == 2
    assert len(receipt["rows"]) == 20
    assert receipt["exact_payload_match"] is True
    assert receipt["production_recipient_send_count"] == 0
    assert receipt["production_intent_created"] == 0
    serialized = json.dumps(receipt, sort_keys=True).lower()
    assert "chat_id" not in serialized
    assert "bot_token" not in serialized
    assert "telegram_token" not in serialized


def test_frozen_candidate_and_adjudication_artifacts_are_immutable() -> None:
    for name, expected in SOURCE_SHA256.items():
        assert _sha256(REPORTS / name) == expected
