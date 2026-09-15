from __future__ import annotations

import json
from pathlib import Path

from app.services.directional_balance_service import (
    DirectionalBalance,
    ORDINAL_CALIBRATION_CONTRACT_VERSION,
    decision_from_directional_balance,
    directional_balance_ordinal_calibration_prompt,
)
from scripts import directional_core_price_timing_holdout as holdout


FIXTURE_PATH = Path("fixtures/directional_core_ordinal_calibration_v1.json")


def test_ordinal_calibration_contract_is_symmetric_and_conservative() -> None:
    prompt = directional_balance_ordinal_calibration_prompt()

    assert ORDINAL_CALIBRATION_CONTRACT_VERSION == (
        "directional-balance-ordinal-calibration-v1"
    )
    assert "5.0:5.0" in prompt
    assert "5.5:4.5" in prompt
    assert "6.0:4.0 is the minimum BUY" in prompt
    assert "4.5:5.5, 4.0:6.0, and 3.5:6.5" in prompt
    assert "choose the less directional bucket toward 5.0:5.0" in prompt
    assert "Missing evidence limits conviction but is not negative evidence" in prompt
    assert "LOW confidence does not mechanically require HOLD" in prompt


def test_existing_thresholds_and_precision_remain_unchanged() -> None:
    assert decision_from_directional_balance(DirectionalBalance(buy=6, sell=4)) == "BUY"
    assert decision_from_directional_balance(DirectionalBalance(buy=5.5, sell=4.5)) == "HOLD"
    assert decision_from_directional_balance(DirectionalBalance(buy=4.5, sell=5.5)) == "HOLD"
    assert decision_from_directional_balance(DirectionalBalance(buy=4, sell=6)) == "SELL"


def test_directional_core_prompt_uses_shared_ordinal_contract() -> None:
    prompt = holdout._core_prompt(
        packet_id="fictional-generation",
        tickers=("FICUS01",),
        contexts=({"ticker": "FICUS01", "evidence": []},),
    )

    assert directional_balance_ordinal_calibration_prompt() in prompt
    assert "overall_direction is BUY when buy >= 6" in prompt
    assert "SELL when sell >= 6" in prompt
    assert "buy and sell sum to 10 in 0.5 increments" in prompt
    assert "keep it empty for CONFIDENCE_LIMIT and CONFIRMATION_REQUIRED" in prompt


def test_fictional_fixture_manifest_covers_required_calibration_classes() -> None:
    manifest = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    rows = manifest["fixtures"]

    assert len(rows) == 8
    assert {row["fixture_id"] for row in rows} == {
        "F1_BALANCED_INCOMPLETE",
        "F2_POSITIVE_LEAN_INCOMPLETE",
        "F3_MINIMUM_POSITIVE_DIRECTION",
        "F4_STRONG_POSITIVE",
        "F5_NEGATIVE_LEAN_INCOMPLETE",
        "F6_MINIMUM_NEGATIVE_DIRECTION",
        "F7_STRONG_NEGATIVE",
        "F8_UNKNOWN_NOT_NEGATIVE",
    }
    assert len({row["ticker"] for row in rows}) == 8
    assert {row["market"] for row in rows} == {"us", "kr"}
    assert all(row["ticker"].startswith("FIC") for row in rows)
    assert all(row["evidence"] for row in rows)
    assert rows[-1]["expected"]["forbidden_direction"] == "SELL"
