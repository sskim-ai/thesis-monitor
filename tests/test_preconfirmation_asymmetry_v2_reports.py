from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"


def _read(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def test_committed_v2_shadow_is_complete_and_not_distribution_forced() -> None:
    value = _read("20260830-current-20-v2-shadow-decisions.json")
    assert value["status"] == "PASS"
    assert value["subject_count"] == 20
    assert value["decision_distribution"] == {"BUY": 2, "HOLD": 14, "SELL": 4}
    assert value["preconfirmation_buy_count"] == 2
    assert value["postconfirmation_hold_count"] == 0
    assert value["material_disagreement_count"] == 5
    assert value["parse_errors"] == []
    assert value["validation_errors"] == []
    assert value["message_quality"]["status"] == "PASS"
    assert value["production_packet_changed"] is False
    assert value["production_canary_state_mutated"] is False


def test_every_material_disagreement_is_adjudicated() -> None:
    value = _read("20260830-v1-v2-decision-agreement.json")
    assert value["subject_count"] == 20
    assert value["agreement_count"] == 15
    assert value["material_disagreement_count"] == 5
    assert value["adjudication_count"] == 5
    disagreements = [row for row in value["rows"] if row["material_disagreement"]]
    assert {row["ticker"] for row in disagreements} == {
        "003690",
        "GOOGL",
        "HUT",
        "RXRX",
        "SNDK",
    }
    assert all(row["adjudication"]["bounded_repair"] == "NONE" for row in disagreements)


def test_readiness_gates_keep_v2_shadow_only_and_v1_canary_unchanged() -> None:
    value = _read("20260830-v2-migration-readiness.json")
    gates = value["gates"]
    zero_gates = (
        "PRECONFIRMATION_DECISION_FROM_FIXED_RULE",
        "FINAL_DECISION_FROM_FIXED_WEIGHT_SUM",
        "MATURITY_HARD_MAPS_TO_CONFIDENCE",
        "MATURITY_HARD_MAPS_TO_DECISION",
        "PRICING_REQUIREMENT_WITHOUT_EVIDENCE",
        "AI_INVENTED_SCENARIO_TARGET_PRICE",
        "TECHNICAL_FEATURE_OWNS_ASYMMETRY",
        "PRECONFIRMATION_LOGIC_BYPASSES_DATA_SAFETY",
        "FORCED_PRECONFIRMATION_BUY_COUNT",
        "HISTORICAL_REPLAY_LOOKAHEAD_LEAK",
        "PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA",
        "POLARITY_REGRESSION",
        "US_DECISION_LOCALIZATION_REGRESSION",
        "V2_PRODUCTION_DECISION_BLOCK_VISIBLE",
        "V2_MUTATED_CANARY_STATE",
        "V2_TEST_PRODUCTION_RECIPIENT_SEND",
        "PRODUCTION_DELIVERY_INTENT_CREATED",
        "OPEN_P0",
        "OPEN_MATERIAL_P1",
    )
    assert all(gates[key] == 0 for key in zero_gates)
    assert gates["TICKER_003690_IDENTITY"] == "코리안리"
    assert gates["CURRENT_V1_DECISION_ENGINE_STATE"] == "CANARY"
    assert gates["V2_TEST_MESSAGE_COUNT"] == 20
    assert gates["V2_TEST_MESSAGE_QUALITY"] == "PASS"
    assert gates["V2_TEST_EXACT_PAYLOAD"] == "PASS"
    assert value["migration_recommendation"] == "READY_WITH_OBSERVATION"
    assert value["production_v2_exposure"] == 0


def test_test_sink_receipt_is_exact_and_contains_no_raw_recipient() -> None:
    path = REPORTS / "20260830-v2-test-sink-receipt.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["status"] == "PASS"
    assert value["sent_message_count"] == 20
    assert value["exact_payload_match"] is True
    assert value["duplicate_count"] == 0
    assert value["orphan_count"] == 0
    assert value["production_recipient_send_count"] == 0
    lowered = path.read_text(encoding="utf-8").lower()
    assert "chat_id" not in lowered
    assert "telegram_bot_token" not in lowered
