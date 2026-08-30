from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.scenario_asymmetry_service import (
    Asymmetry,
    AsymmetryAssessment,
    ConfirmationCost,
    ConfirmationCostAssessment,
    PreconfirmationErrorCost,
    PreconfirmationErrorCostAssessment,
    ScenarioInterpretation,
    ScenarioName,
    ScenarioSet,
)


def _claim(ref: str, text: str) -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=(ref,))


def _scenario(name: ScenarioName) -> ScenarioInterpretation:
    return ScenarioInterpretation(
        scenario=name,
        business_and_earnings=_claim("ref:thesis", f"{name} 사업 가정입니다."),
        expectation_and_valuation=_claim("ref:valuation", f"{name} 기대 해석입니다."),
        macro_market_conditions=_claim("ref:macro", f"{name} 거시 조건입니다."),
    )


def test_scenario_set_requires_exact_bear_base_bull_slots() -> None:
    scenarios = ScenarioSet(
        bear=_scenario(ScenarioName.BEAR),
        base=_scenario(ScenarioName.BASE),
        bull=_scenario(ScenarioName.BULL),
    )
    assert {scenarios.bear.scenario, scenarios.base.scenario, scenarios.bull.scenario} == {
        ScenarioName.BEAR,
        ScenarioName.BASE,
        ScenarioName.BULL,
    }

    with pytest.raises(ValidationError, match="bear_scenario_slot_mismatch"):
        ScenarioSet(
            bear=_scenario(ScenarioName.BASE),
            base=_scenario(ScenarioName.BASE),
            bull=_scenario(ScenarioName.BULL),
        )


def test_asymmetry_confirmation_cost_and_error_cost_are_independent() -> None:
    asymmetry = AsymmetryAssessment(
        asymmetry=Asymmetry.FAVORABLE,
        basis=_claim("ref:valuation", "보수적 결과도 현재 평가를 지지할 수 있습니다."),
        downside_permanence=_claim("ref:risk", "하방의 영구 손실 경로를 분리합니다."),
        upside_not_priced=_claim("ref:expectation", "상방 선택지는 전부 반영되지 않았습니다."),
    )
    confirmation = ConfirmationCostAssessment(
        cost=ConfirmationCost.HIGH,
        basis=_claim("ref:catalyst", "증거 확인과 재평가가 동시에 진행될 수 있습니다."),
        likely_repricing_channel=_claim("ref:earnings", "이익 추정 변경이 재평가 경로입니다."),
    )
    error = PreconfirmationErrorCostAssessment(
        cost=PreconfirmationErrorCost.HIGH,
        basis=_claim("ref:risk", "초기 가정 실패 시 손실 폭이 클 수 있습니다."),
        capital_loss_channel=_claim("ref:quality", "재무 취약성이 영구 손실 경로입니다."),
    )

    assert asymmetry.asymmetry == "FAVORABLE"
    assert confirmation.cost == "HIGH"
    assert error.cost == "HIGH"
    assert not hasattr(asymmetry, "decision")
