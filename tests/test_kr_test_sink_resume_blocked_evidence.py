import json
from pathlib import Path


REPORTS = Path(__file__).parents[1] / "docs" / "reports"


def _read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def test_no_real_test_chat_blocks_all_dependent_stages() -> None:
    readiness = _read_json("20260828-kr-final-rollout-readiness.json")
    delivery = _read_json("20260828-kr-final-test-delivery.json")

    assert readiness["test_sink"]["available"] is False
    assert readiness["test_sink"]["reason"] == "dedicated_test_sink_not_configured"
    assert readiness["kr_final_preenable"] == "BLOCKED_NO_TEST_SINK"
    assert readiness["preenable"]["data_collection"] == "NOT_RUN"
    assert readiness["enablement"]["operating_promotion"] == "NOT_RUN"
    assert readiness["enablement"]["kr_market_top3_enabled"] is False
    assert readiness["enablement"]["kr_price_structure_enabled"] is False
    assert readiness["kr_rollout"] == "NOT_ENABLED"
    assert readiness["open_p0"] == []
    assert readiness["open_material_p1"] == [
        "dedicated_test_sink_not_configured"
    ]
    assert readiness["next_action"] == "OPERATOR_PROVIDE_DEDICATED_TEST_CHAT"

    assert delivery["total_message_count"] == 0
    assert delivery["production_delivery_intent_created"] == 0
    assert delivery["test_message_sent_to_production_recipient"] == 0
    assert delivery["receipts"] == []


def test_all_required_resume_reports_exist() -> None:
    names = [
        "kr-test-sink-config",
        "kr-test-sink-isolation",
        "kr-final-preflight-session",
        "kr-final-market-packet",
        "kr-final-top3-message",
        "kr-final-price-structure-per-ticker",
        "kr-final-ai-fallback-parity",
        "kr-final-test-delivery",
        "kr-final-exact-test-messages",
        "kr-final-message-quality",
        "kr-final-operating-promotion",
        "kr-final-top3-enablement",
        "kr-final-price-structure-enablement",
        "kr-final-post-enable-smoke",
        "kr-final-natural-proof-status",
        "kr-final-rollout-readiness",
        "kr-final-artifact-index",
    ]

    for name in names:
        assert (REPORTS / f"20260828-{name}.md").is_file()
