from __future__ import annotations

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
)
from app.services.evidence_maturity_pricing_service import (
    DriverEvidenceMaturity,
    EvidenceMaturity,
    MarketExpectation,
    MarketExpectationAssessment,
    OverallMaturityAssessment,
    PricingRequirement,
    PricingRequirementAssessment,
)
from app.services.preconfirmation_decision_v2_service import (
    FactualSafetyState,
    PostconfirmationHoldExplanation,
    PreconfirmationBuyExplanation,
    PreconfirmationDecisionCandidate,
    preconfirmation_message_quality,
    render_preconfirmation_shadow,
    validate_preconfirmation_candidate,
)
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
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionSource,
    AcceptedDecisionStatus,
    AcceptedV2Adjudication,
    accepted_message_quality,
    render_accepted_v2_shadow,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
    validate_accepted_v2_render,
)


def _claim(ref: str, text: str = "검증된 근거가 이 해석을 지지합니다.") -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=(ref,))


def _packet() -> DecisionEvidencePacket:
    categories = {
        "thesis": EvidenceCategory.THESIS,
        "earnings": EvidenceCategory.EARNINGS,
        "expectations": EvidenceCategory.EXPECTATIONS,
        "valuation": EvidenceCategory.VALUATION,
        "risks": EvidenceCategory.RISKS,
        "market": EvidenceCategory.MARKET,
        "price": EvidenceCategory.PRICE_STRUCTURE,
        "quality": EvidenceCategory.QUALITY,
        "unknown": EvidenceCategory.UNKNOWN,
    }
    return DecisionEvidencePacket(
        packet_id="packet-v2",
        ticker="TEST",
        company_name="테스트기업",
        market="us",
        assessment_date="2026-08-30",
        horizon="장기",
        evidence=tuple(
            DecisionEvidenceRef(
                ref_id=f"ref:{name}",
                category=category,
                label=name,
                statement=f"{name} canonical evidence",
                as_of="2026-08-30",
                source_ref="fixture",
            )
            for name, category in categories.items()
        ),
        prohibited_claims=(),
        evidence_sha256="fixture",
    )


def _scenario(name: ScenarioName) -> ScenarioInterpretation:
    return ScenarioInterpretation(
        scenario=name,
        business_and_earnings=_claim("ref:earnings", f"{name} 사업과 이익 가정입니다."),
        expectation_and_valuation=_claim("ref:valuation", f"{name} 기대와 평가 가정입니다."),
        macro_market_conditions=_claim("ref:market", f"{name} 시장 조건입니다."),
    )


def _candidate() -> PreconfirmationDecisionCandidate:
    return PreconfirmationDecisionCandidate(
        ticker="TEST",
        decision="BUY",
        reasoning_grade="VERY_HIGH",
        confidence="MEDIUM",
        timing="NEUTRAL",
        timing_basis=_claim("ref:price", "가격 구조는 단기 진입을 막지 않습니다."),
        factual_safety_state=FactualSafetyState.PASS,
        factual_safety_basis=_claim("ref:quality", "핵심 사실 기준은 검증됐습니다."),
        driver_maturity=(
            DriverEvidenceMaturity(
                driver="신규 제품 수익화",
                decisive=True,
                maturity=EvidenceMaturity.PARTIAL,
                supporting_evidence_refs=("ref:thesis", "ref:earnings"),
                contradicting_evidence_refs=("ref:risks",),
                what_remains_unproven=_claim(
                    "ref:unknown", "반복 가능한 경제성은 아직 확인되지 않았습니다."
                ),
                as_of="2026-08-30",
            ),
        ),
        overall_maturity=OverallMaturityAssessment(
            maturity=EvidenceMaturity.PARTIAL,
            basis=_claim("ref:thesis", "방향성은 보이지만 경제성 증명은 부분적입니다."),
        ),
        market_expectation=MarketExpectationAssessment(
            level=MarketExpectation.LOW,
            basis=_claim("ref:expectations", "시장 기대는 낮은 편으로 해석됩니다."),
        ),
        pricing_requirement=PricingRequirementAssessment(
            requirement=PricingRequirement.CONSERVATIVE_OUTCOME_SUFFICIENT,
            basis=_claim("ref:valuation", "강한 낙관 없이도 현재 평가를 설명할 수 있습니다."),
            valuation_basis=_claim("ref:valuation", "검증된 평가 근거를 사용했습니다."),
            expectation_basis=_claim("ref:expectations", "낮은 기대가 불확실성을 반영합니다."),
            key_assumption=_claim("ref:thesis", "기존 사업의 내구성이 핵심 가정입니다."),
            unknowns=(_claim("ref:unknown", "신규 수익화의 반복성은 미확인입니다."),),
        ),
        scenarios=ScenarioSet(
            bear=_scenario(ScenarioName.BEAR),
            base=_scenario(ScenarioName.BASE),
            bull=_scenario(ScenarioName.BULL),
        ),
        asymmetry=AsymmetryAssessment(
            asymmetry=Asymmetry.FAVORABLE,
            basis=_claim("ref:valuation", "보수적 결과 대비 상방 선택지가 더 큽니다."),
            downside_permanence=_claim("ref:risks", "하방의 영구 손실 경로는 제한적입니다."),
            upside_not_priced=_claim("ref:expectations", "상방 가능성은 전부 반영되지 않았습니다."),
        ),
        confirmation_cost=ConfirmationCostAssessment(
            cost=ConfirmationCost.HIGH,
            basis=_claim("ref:expectations", "완전 확인과 가격 재평가가 함께 올 수 있습니다."),
            likely_repricing_channel=_claim("ref:earnings", "이익 추정 개선이 재평가 경로입니다."),
        ),
        preconfirmation_error_cost=PreconfirmationErrorCostAssessment(
            cost=PreconfirmationErrorCost.MEDIUM,
            basis=_claim("ref:risks", "초기 가정 실패의 손실 경로는 관리 가능하지만 남아 있습니다."),
            capital_loss_channel=_claim("ref:quality", "사업 내구성 훼손이 영구 손실 경로입니다."),
        ),
        pre_confirmation_buy=True,
        preconfirmation_buy_explanation=PreconfirmationBuyExplanation(
            not_yet_confirmed=_claim("ref:unknown", "신규 수익화의 반복성은 아직 미확인입니다."),
            directionally_credible=_claim("ref:earnings", "현재 실적 방향은 초기 논리와 일치합니다."),
            market_already_prices=_claim("ref:expectations", "시장은 상당한 불확실성을 반영합니다."),
            favorable_asymmetry=_claim("ref:valuation", "현재 평가는 보수적 결과도 수용합니다."),
            thesis_break_risk=_claim("ref:risks", "기존 사업 훼손은 초기 논리를 깨뜨립니다."),
            buy_to_hold_or_sell=_claim("ref:risks", "방향성 증거가 반전되면 판단을 낮춥니다."),
        ),
        post_confirmation_hold=False,
        postconfirmation_hold_explanation=None,
        decisive_reason=_claim(
            "ref:valuation", "부분 증명 상태지만 현재 기대가 불확실성을 충분히 보상합니다."
        ),
        why_not_buy=_claim("ref:risks", "실행 실패 위험은 BUY 확신도를 제한합니다."),
        why_not_sell=_claim("ref:thesis", "기존 사업과 초기 수익화 방향은 하방 우위를 막습니다."),
        opposing_evidence=(_claim("ref:risks", "실행 반복성은 아직 반대 근거로 남습니다."),),
        unknowns=(_claim("ref:unknown", "경제성의 지속 기간은 확인되지 않았습니다."),),
        upgrade_condition=_claim("ref:earnings", "경제성의 반복 증거가 쌓이면 확신을 높입니다."),
        downgrade_condition=_claim("ref:risks", "기존 사업까지 약화되면 판단을 낮춥니다."),
    )


def test_partial_maturity_can_be_medium_confidence_preconfirmation_buy() -> None:
    packet = _packet()
    candidate = _candidate()
    validation = validate_preconfirmation_candidate(packet, candidate)
    assert validation.valid is True
    assert candidate.confidence == "MEDIUM"
    assert candidate.overall_maturity.maturity == "PARTIAL"
    assert candidate.pre_confirmation_buy is True

    rendered = render_preconfirmation_shadow(packet, candidate)
    quality = preconfirmation_message_quality((rendered,))
    assert quality["status"] == "PASS"
    assert "완전 확인 전 판단" in rendered.text


def test_confirmed_business_can_be_postconfirmation_hold() -> None:
    candidate = _candidate().model_copy(
        update={
            "decision": "HOLD",
            "pre_confirmation_buy": False,
            "preconfirmation_buy_explanation": None,
            "post_confirmation_hold": True,
            "postconfirmation_hold_explanation": PostconfirmationHoldExplanation(
                business_proof=_claim("ref:earnings", "사업 증거는 충분히 확인됐습니다."),
                price_repricing=_claim("ref:valuation", "가격도 함께 재평가돼 상방 여유가 줄었습니다."),
            ),
            "driver_maturity": (
                _candidate().driver_maturity[0].model_copy(
                    update={"maturity": EvidenceMaturity.CONFIRMED}
                ),
            ),
            "overall_maturity": OverallMaturityAssessment(
                maturity=EvidenceMaturity.CONFIRMED,
                basis=_claim("ref:earnings", "핵심 경제성은 반복 증거로 확인됐습니다."),
            ),
            "asymmetry": _candidate().asymmetry.model_copy(
                update={"asymmetry": Asymmetry.BALANCED}
            ),
        }
    )
    assert validate_preconfirmation_candidate(_packet(), candidate).valid is True


def test_factual_safety_block_cannot_be_priced_as_investment_uncertainty() -> None:
    candidate = _candidate().model_copy(
        update={"factual_safety_state": FactualSafetyState.BLOCKED}
    )
    errors = validate_preconfirmation_candidate(_packet(), candidate).errors
    assert "preconfirmation_logic_bypasses_data_safety" in errors
    assert "blocked_safety_with_pricing_requirement" in errors
    assert "blocked_safety_with_asymmetry" in errors


def test_technical_evidence_cannot_own_asymmetry() -> None:
    technical = _candidate().asymmetry.model_copy(
        update={
            "basis": _claim("ref:price", "가격 구조만으로 비대칭을 판단했습니다."),
            "downside_permanence": _claim("ref:price", "가격 구조가 하방을 설명합니다."),
            "upside_not_priced": _claim("ref:market", "시장 흐름이 상방을 설명합니다."),
        }
    )
    candidate = _candidate().model_copy(update={"asymmetry": technical})
    assert "technical_feature_owns_asymmetry" in validate_preconfirmation_candidate(
        _packet(), candidate
    ).errors


def test_target_price_fixed_score_and_order_language_are_rejected() -> None:
    candidate = _candidate().model_copy(
        update={
            "decisive_reason": _claim(
                "ref:valuation", "목표가를 고정 점수 합산으로 정했으니 시장가 매수 주문이 적절합니다."
            )
        }
    )
    errors = validate_preconfirmation_candidate(_packet(), candidate).errors
    assert "invented_target_price_language" in errors
    assert "fixed_score_language" in errors
    assert "order_command_language" in errors


def _adjudication(
    *, recommendation: str, accepted_decision: str
) -> AcceptedV2Adjudication:
    return AcceptedV2Adjudication(
        ticker="TEST",
        v1_decision="HOLD",
        v2_decision="BUY",
        accepted_decision=accepted_decision,
        recommendation=recommendation,
        v1_overrequired_confirmation="NO",
        v2_underweighted_execution_risk="YES",
        v1_ignored_confirmation_cost="NO",
        v2_overstated_favorable_asymmetry="YES",
        valuation_or_expectation_misuse="NEITHER",
        data_quality_comparison_safe=True,
        decisive_basis=_claim(
            "ref:risks", "실행 위험이 남아 현재는 보유 판단이 더 적절합니다."
        ),
        bounded_repair="NONE",
    )


def test_no_disagreement_accepts_candidate_as_single_authority() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate().model_copy(update={"decision": "HOLD", "pre_confirmation_buy": False,
                                        "preconfirmation_buy_explanation": None}),
        v1_decision="HOLD",
        material_disagreement=False,
        adjudication=None,
    )
    assert plan.status == AcceptedDecisionStatus.READY
    assert plan.accepted_decision == "HOLD"
    assert plan.accepted_source == AcceptedDecisionSource.CANDIDATE
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_keep_v1_replaces_candidate_and_suppresses_rejected_prebuy() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    assert plan.status == AcceptedDecisionStatus.READY
    assert plan.candidate_decision == "BUY"
    assert plan.accepted_decision == "HOLD"
    assert plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1
    assert plan.accepted_preconfirmation_buy is False
    assert plan.accepted_asymmetry == "UNKNOWN"
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_keep_v2_preserves_candidate_decision_and_prebuy() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V2", accepted_decision="BUY"),
    )
    assert plan.accepted_decision == "BUY"
    assert plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V2
    assert plan.accepted_preconfirmation_buy is True
    assert validate_accepted_v2_decision(packet, plan).valid is True


def test_missing_material_adjudication_fails_closed_without_candidate_fallback() -> None:
    plan = resolve_accepted_v2_decision(
        _packet(),
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=None,
    )
    assert plan.status == AcceptedDecisionStatus.NOT_READY
    assert plan.accepted_decision is None
    assert plan.denial_reason == "material_disagreement_without_final_adjudication"


def test_accepted_resolution_is_idempotent() -> None:
    packet = _packet()
    adjudication = _adjudication(recommendation="KEEP_V1", accepted_decision="HOLD")
    first = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=adjudication,
    )
    second = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=adjudication,
    )
    assert first == second
    assert first.accepted_decision_id == second.accepted_decision_id
    assert first.accepted_evidence_fingerprint == second.accepted_evidence_fingerprint


def test_accepted_renderer_uses_keep_v1_hold_not_raw_candidate_buy() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    rendered = render_accepted_v2_shadow(packet, plan)
    assert rendered.candidate_decision == "BUY"
    assert rendered.accepted_decision == "HOLD"
    assert "AI 수용 판단: HOLD" in rendered.text
    assert "AI 수용 판단: BUY" not in rendered.text
    assert "완전 확인 전 BUY" not in rendered.text
    assert accepted_message_quality((rendered,))["status"] == "PASS"


def test_accepted_render_validator_rejects_candidate_label_leak() -> None:
    packet = _packet()
    plan = resolve_accepted_v2_decision(
        packet,
        _candidate(),
        v1_decision="HOLD",
        material_disagreement=True,
        adjudication=_adjudication(recommendation="KEEP_V1", accepted_decision="HOLD"),
    )
    rendered = render_accepted_v2_shadow(packet, plan)
    validation = validate_accepted_v2_render(
        plan,
        rendered_decision="BUY",
        text=rendered.text.replace("AI 수용 판단: HOLD", "AI 수용 판단: BUY"),
    )
    assert validation.valid is False
    assert "rendered_decision_not_accepted_decision" in validation.errors
