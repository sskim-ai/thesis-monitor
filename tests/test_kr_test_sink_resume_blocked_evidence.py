import json
from pathlib import Path


REPORTS = Path(__file__).parents[1] / "docs" / "reports"


def _read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def test_dedicated_test_chat_unblocks_isolated_preenable_and_rollout() -> None:
    readiness = _read_json("20260828-kr-final-rollout-readiness.json")
    delivery = _read_json("20260828-kr-final-test-delivery.json")

    assert readiness["test_sink"]["available"] is True
    assert readiness["test_sink"]["selected_key"] == "TELEGRAM_TEST_CHAT_ID"
    assert readiness["test_sink"]["production_sink_collision"] == 0
    assert readiness["test_sink"]["production_intent_collision"] == 0
    assert readiness["test_sink"]["secret_in_repo"] == 0
    assert readiness["kr_final_preenable"] == "PASS"
    assert readiness["preenable"]["data_collection"] == "PASS_STORED_RUN42_42_OF_42"
    assert readiness["preenable"]["exact_payload_match"] == "PASS_8_OF_8"
    assert readiness["enablement"]["operating_promotion"] == "PASS"
    assert readiness["enablement"]["kr_market_top3_enabled"] is True
    assert readiness["enablement"]["kr_price_structure_enabled"] is True
    assert readiness["enablement"]["us_price_structure_enabled"] == 0
    assert readiness["kr_rollout"] == "ENABLED_AWAITING_NATURAL_PROOF"
    assert readiness["open_p0"] == []
    assert readiness["open_material_p1"] == []
    assert readiness["next_action"] == "WAIT_FOR_NEXT_NATURAL_KR_MESSAGES"

    assert delivery["status"] == "sent"
    assert delivery["planned_message_count"] == 8
    assert delivery["sent_message_count"] == 8
    assert delivery["exact_payload_match"] is True
    assert delivery["production_collision"] == 0
    assert delivery["production_intent_created"] == 0
    assert delivery["production_recipient_send_count"] == 0
    assert delivery["duplicate_count"] == 0
    assert delivery["orphan_count"] == 0
    assert delivery["unowned_retry_count"] == 0
    assert len(delivery["rows"]) == 8
    assert all(row["send_attempts"] == 1 for row in delivery["rows"])
    assert all(row["exact_payload_match"] is True for row in delivery["rows"])


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
