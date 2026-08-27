import json
from pathlib import Path


REPORTS = Path(__file__).parents[1] / "docs" / "reports"


def _read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def test_blocked_track_a_prevents_delivery_and_enablement() -> None:
    readiness = _read_json("20260827-kr-final-rollout-readiness.json")
    delivery = _read_json("20260827-kr-final-test-delivery.json")

    assert readiness["track_a"]["test_sink_available"] is False
    assert readiness["track_a"]["state"] == "BLOCKED_NO_TEST_SINK"
    assert readiness["track_b"]["state"] == "NOT_RUN_TRACK_A_BLOCKED"
    assert readiness["track_c"]["state"] == "NOT_RUN_TRACK_A_BLOCKED"
    assert readiness["track_c"]["operating_promotion"] == "NOT_RUN"
    assert readiness["track_c"]["kr_market_top3_enabled"] is False
    assert readiness["track_c"]["kr_price_structure_enabled"] is False
    assert readiness["kr_rollout"] == "NOT_ENABLED"
    assert readiness["open_p0"] == []
    assert readiness["open_material_p1"] == ["dedicated_test_sink_not_configured"]

    assert delivery["delivery_state"] == "NOT_SENT_TRACK_A_BLOCKED"
    assert delivery["total_message_count"] == 0
    assert delivery["production_delivery_intent_created"] == 0
    assert delivery["test_message_sent_to_production_recipient"] == 0
    assert delivery["receipts"] == []


def test_all_required_blocked_path_reports_exist() -> None:
    names = [
        "test-sink-configuration",
        "test-sink-isolation",
        "preflight-target-session",
        "market-data",
        "market-top3-message",
        "price-structure-per-ticker",
        "ai-fallback-parity",
        "test-delivery",
        "exact-test-messages",
        "test-message-quality",
        "operating-promotion",
        "top3-enablement",
        "price-structure-enablement",
        "post-enable-smoke",
        "natural-proof-status",
        "rollout-safety-parity",
        "rollout-readiness",
        "rollout-artifact-index",
    ]

    for name in names:
        assert (REPORTS / f"20260827-kr-final-{name}.md").is_file()
