from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_language_errors,
)
from app.services.structured_autonomy_shadow_service import (
    ActionRole,
    ActionSubject,
    CONFIRMATION_BUSINESS_LANGUAGE_FIXTURES,
    CONFIRMATION_PRICE_STRUCTURE_FIXTURES,
    CRCL_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    KR_047810_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    MU_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    ClassifiedSellDriver,
    CheckpointKind,
    ClaimSemanticMetadata,
    ClaimTimeScope,
    ClaimType,
    HoldLean,
    HolderViewV2,
    MetricDirection,
    NewBuyerViewV2,
    RenderedStructuredAutonomy,
    RepetitionSemanticRole,
    StructuredAutonomyCandidate,
    StructuredAutonomyValidation,
    StructuredEvidenceClaim,
    DirectiveState,
    TradeLanguageSemantic,
    StructuredActionContext,
    StructuredActionStance,
    UnknownTreatment,
    build_structured_actionability,
    confirmation_business_condition_has_price_structure_semantics,
    derive_hold_lean,
    directive_state,
    hold_lean_flip,
    korean_price_subject_action_matches,
    mandatory_trade_directive_matches,
    repetition_semantic_role,
    render_structured_autonomy_message,
    sanitize_detail_body,
    structured_autonomy_message_quality,
    structured_actionability_contradictions,
    trade_language_semantic,
    validate_structured_autonomy_candidate,
)
from app.services.logical_condition_service import (
    LogicalSeverity,
    checkpoint_metric_refs,
    source_logical_condition,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)


def _claim(
    ref: str,
    text: str = "검증된 사업 근거가 판단을 지지합니다.",
) -> StructuredEvidenceClaim:
    return StructuredEvidenceClaim(text=text, evidence_refs=(ref,))


def _future_claim(
    ref: str,
    text: str,
    *,
    kind: CheckpointKind = CheckpointKind.REASSESSMENT,
    direction: MetricDirection = MetricDirection.OBSERVE,
) -> StructuredEvidenceClaim:
    return StructuredEvidenceClaim(
        text=text,
        evidence_refs=(ref,),
        semantic=ClaimSemanticMetadata(
            claim_type=ClaimType.FUTURE_CHECKPOINT,
            metric_refs=checkpoint_metric_refs(text),
            time_scope=ClaimTimeScope.FUTURE_CHECKPOINT,
            checkpoint_kind=kind,
            direction=direction,
        ),
    )


def test_unknown_limit_allows_neutral_observe_without_checkpoint_kind() -> None:
    semantic = ClaimSemanticMetadata(
        claim_type=ClaimType.UNKNOWN_LIMIT,
        time_scope=ClaimTimeScope.CURRENT,
        checkpoint_kind=None,
        direction=MetricDirection.OBSERVE,
    )

    assert semantic.direction == MetricDirection.OBSERVE


@pytest.mark.parametrize(
    ("claim_type", "direction"),
    (
        (ClaimType.EVIDENCE_INTERPRETATION, MetricDirection.OBSERVE),
        (ClaimType.UNKNOWN_LIMIT, MetricDirection.IMPROVE),
        (ClaimType.UNKNOWN_LIMIT, MetricDirection.DETERIORATE),
    ),
)
def test_nonfuture_semantic_direction_remains_bounded(
    claim_type: ClaimType,
    direction: MetricDirection,
) -> None:
    with pytest.raises(ValidationError):
        ClaimSemanticMetadata(
            claim_type=claim_type,
            time_scope=ClaimTimeScope.CURRENT,
            checkpoint_kind=None,
            direction=direction,
        )


@pytest.mark.parametrize(
    ("claim_type", "time_scope", "checkpoint_kind", "direction"),
    (
        (
            ClaimType.EVIDENCE_INTERPRETATION,
            ClaimTimeScope.CURRENT,
            None,
            None,
        ),
        (
            ClaimType.EVIDENCE_INTERPRETATION,
            ClaimTimeScope.HISTORICAL,
            None,
            None,
        ),
        (
            ClaimType.UNKNOWN_LIMIT,
            ClaimTimeScope.CURRENT,
            None,
            MetricDirection.OBSERVE,
        ),
        (
            ClaimType.FUTURE_CHECKPOINT,
            ClaimTimeScope.FUTURE_CHECKPOINT,
            CheckpointKind.STRENGTHEN,
            MetricDirection.IMPROVE,
        ),
        (
            ClaimType.FUTURE_CHECKPOINT,
            ClaimTimeScope.FUTURE_CHECKPOINT,
            CheckpointKind.WEAKEN,
            MetricDirection.DETERIORATE,
        ),
        (
            ClaimType.FUTURE_CHECKPOINT,
            ClaimTimeScope.FUTURE_CHECKPOINT,
            CheckpointKind.REASSESSMENT,
            MetricDirection.OBSERVE,
        ),
    ),
)
def test_normal_claim_type_directional_semantics_remain_available(
    claim_type: ClaimType,
    time_scope: ClaimTimeScope,
    checkpoint_kind: CheckpointKind | None,
    direction: MetricDirection | None,
) -> None:
    semantic = ClaimSemanticMetadata(
        claim_type=claim_type,
        time_scope=time_scope,
        checkpoint_kind=checkpoint_kind,
        direction=direction,
    )

    assert semantic.claim_type == claim_type
    assert semantic.direction == direction


def _packet() -> DecisionEvidencePacket:
    return DecisionEvidencePacket(
        packet_id="packet-shadow-v2",
        ticker="TEST",
        company_name="테스트기업",
        market="us",
        assessment_date="2026-09-03",
        horizon="장기",
        evidence=tuple(
            DecisionEvidenceRef(
                ref_id=f"ref:{name}",
                category=category,
                label=name,
                statement=f"{name} evidence",
                as_of="2026-09-03",
                source_ref="fixture",
            )
            for name, category in (
                ("thesis", EvidenceCategory.THESIS),
                ("earnings", EvidenceCategory.EARNINGS),
                ("expectations", EvidenceCategory.EXPECTATIONS),
                ("valuation", EvidenceCategory.VALUATION),
                ("price", EvidenceCategory.PRICE_STRUCTURE),
                ("risk", EvidenceCategory.RISKS),
                ("unknown", EvidenceCategory.UNKNOWN),
            )
        ),
        prohibited_claims=(),
        evidence_sha256="fixture",
    )


def _price_map() -> dict[str, object]:
    return {
        "currency": "USD",
        "current_close": 100.0,
        "current_price_ref": "ref:price",
        "nearest_supports": [
            {"zone_low": 90.0, "zone_high": 94.0, "basis_ref": "ref:price"}
        ],
        "nearest_resistances": [
            {"zone_low": 108.0, "zone_high": 112.0, "basis_ref": "ref:price"}
        ],
        "major_support": None,
        "major_resistance": None,
        "registered_price_rules": {
            "basis_ref": "ref:price",
            "support_zone_low": 88.0,
            "support_zone_high": 92.0,
            "confirmation_price": 115.0,
            "warning_price": 86.0,
            "invalidation_price": 82.0,
        },
        "chart_invalidation": None,
    }


def _candidate() -> StructuredAutonomyCandidate:
    return StructuredAutonomyCandidate(
        ticker="TEST",
        decision="HOLD",
        directional_balance=DirectionalBalance(buy=5.5, sell=4.5),
        decision_confidence="MEDIUM",
        business_thesis_change="UNCHANGED",
        business_thesis_context=_claim("ref:thesis"),
        earnings_estimate_context=_claim("ref:earnings"),
        market_expectation_context=_claim("ref:expectations"),
        valuation_context=_claim("ref:valuation"),
        price_timing_context=_claim("ref:price"),
        risk_context=_claim("ref:risk"),
        sector_interpretation=_claim("ref:thesis"),
        buy_drivers=(_claim("ref:thesis"),),
        sell_drivers=(
            ClassifiedSellDriver(
                text="실행 위험은 반대 근거로 남아 있습니다.",
                evidence_refs=("ref:risk",),
                classification="STRUCTURAL_RISK",
            ),
        ),
        dominant_evidence=_claim("ref:thesis"),
        uncertainty_limit=_claim("ref:unknown"),
        core_judgment=_claim("ref:thesis", "사업 근거와 위험이 함께 남아 관망이 타당합니다."),
        unknown_treatments=(
            UnknownTreatment(
                summary="경제성의 반복성은 추가 확인이 필요합니다.",
                evidence_refs=("ref:unknown",),
                treatment="CONFIRMATION_REQUIRED",
                directional_negative_basis=(),
            ),
        ),
        new_buyer_view=NewBuyerViewV2(
            stance="WAIT",
            summary="눌림과 추세 확인을 함께 검토합니다.",
            pullback_entry_zone_low=90.0,
            pullback_entry_zone_high=94.0,
            pullback_entry_basis=("ref:price",),
            breakout_confirmation_level=112.0,
            breakout_confirmation_basis=("ref:price",),
            currency="USD",
            preferred_entry_mode="PULLBACK",
            preferred_entry_reason="가격 비대칭이 더 나은 구간을 우선합니다.",
            confirmation_semantics="VERIFIED_RESISTANCE_BREAKOUT",
            confirmation_business_condition="상용화 경제성과 공급 완화를 함께 확인합니다.",
            confirmation_business_condition_refs=("ref:earnings",),
        ),
        holder_view=HolderViewV2(
            stance="HOLDABLE",
            summary="사업 근거가 유지되는 동안 보유 관점은 가능합니다.",
            upside_trim_zone_low=108.0,
            upside_trim_zone_high=112.0,
            upside_trim_basis=("ref:price",),
            downside_review_level=86.0,
            downside_review_basis=("ref:price",),
            currency="USD",
            business_invalidation_condition="핵심 수익화 근거가 구조적으로 훼손되는 경우입니다.",
            business_invalidation_condition_refs=("ref:risk",),
        ),
        reevaluation_up=(
            _future_claim("ref:earnings", "사업 성과 개선 여부를 재평가합니다."),
        ),
        reevaluation_down=(
            _future_claim("ref:risk", "사업 위험 악화 여부를 재평가합니다."),
        ),
    )


def test_hold_lean_and_flip_are_deterministic() -> None:
    assert derive_hold_lean("HOLD", DirectionalBalance(buy=5.5, sell=4.5)) == HoldLean.BUY_LEAN
    assert derive_hold_lean("HOLD", DirectionalBalance(buy=5, sell=5)) == HoldLean.NEUTRAL
    assert derive_hold_lean("HOLD", DirectionalBalance(buy=4.5, sell=5.5)) == HoldLean.SELL_LEAN
    assert derive_hold_lean("BUY", DirectionalBalance(buy=6, sell=4)) == HoldLean.NOT_HOLD
    assert hold_lean_flip(HoldLean.BUY_LEAN, HoldLean.SELL_LEAN) is True
    assert hold_lean_flip(HoldLean.BUY_LEAN, HoldLean.NEUTRAL) is False


def test_dual_entry_and_holder_zones_validate_against_exact_price_map() -> None:
    result = validate_structured_autonomy_candidate(
        _packet(), _candidate(), price_map=_price_map(), industry="Software"
    )

    assert result.valid is True
    assert result.errors == ()


def test_supported_pullback_and_confirmation_cannot_be_silently_dropped() -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={
                    "pullback_entry_zone_low": None,
                    "pullback_entry_zone_high": None,
                    "pullback_entry_basis": (),
                    "breakout_confirmation_level": None,
                    "breakout_confirmation_basis": (),
                    "preferred_entry_mode": "NONE",
                    "confirmation_semantics": "NONE",
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "supported_pullback_zone_not_preserved" in result.errors
    assert "supported_confirmation_level_not_preserved" in result.errors


def test_directional_unknown_requires_economic_absence_basis() -> None:
    candidate = _candidate().model_copy(
        update={
            "unknown_treatments": (
                UnknownTreatment(
                    summary="핵심 증거가 아직 확인되지 않았습니다.",
                    evidence_refs=("ref:unknown",),
                    treatment="DIRECTIONAL_NEGATIVE",
                    directional_negative_basis=(),
                ),
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "unknown_directional_negative_without_economic_basis" in result.errors


def test_biotech_sell_needs_more_than_sector_normal_burn() -> None:
    candidate = _candidate().model_copy(
        update={
            "decision": "SELL",
            "directional_balance": DirectionalBalance(buy=4, sell=6),
            "sell_drivers": (
                ClassifiedSellDriver(
                    text="개발 단계의 현금소모가 이어지고 있습니다.",
                    evidence_refs=("ref:risk",),
                    classification="SECTOR_NORMAL",
                ),
            ),
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Biotechnology"
    )

    assert "biotech_sell_without_deterioration_or_structural_risk" in result.errors


def test_prohibited_language_validator_respects_explicit_negation_and_word_boundaries() -> None:
    candidate = _candidate().model_copy(
        update={
            "holder_view": _candidate().holder_view.model_copy(
                update={
                    "summary": "상단은 자동 매도 사유가 아니며 하단은 손절선이 아니고 재평가 기준입니다.",
                    "business_invalidation_condition": (
                        "Historical midpoint 비교는 가치평가 맥락만 제공합니다."
                    ),
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "mandatory_sell_language" not in result.errors
    assert "invented_stop_loss" not in result.errors
    assert "unsupported_metric_or_inference" not in result.errors


def test_prohibited_language_validator_still_rejects_assertive_trade_rules() -> None:
    candidate = _candidate().model_copy(
        update={
            "holder_view": _candidate().holder_view.model_copy(
                update={
                    "summary": "이 구간에서는 반드시 매도합니다.",
                    "business_invalidation_condition": "하단 가격은 손절선입니다.",
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "mandatory_sell_language" in result.errors
    assert "invented_stop_loss" in result.errors


@pytest.mark.parametrize(
    "text",
    (
        "자동 매도보다 사업 성과 재점검이 우선이다.",
        "상단에서는 자동 매도보다 회복의 질을 평가한다.",
        "무조건 매도할 가격대로 보지는 않는다.",
        "기계적 매도 대신 Valuation 정당화를 확인한다.",
        "자동 축소가 아니라 사업 성과를 확인한다.",
    ),
)
def test_nonmandatory_trade_comparisons_are_not_directives(text: str) -> None:
    assert mandatory_trade_directive_matches(text) == ()


@pytest.mark.parametrize(
    ("text", "semantic"),
    (
        ("즉시 매수가 아니다.", TradeLanguageSemantic.NEGATED),
        ("매도 명령이 아니다.", TradeLanguageSemantic.NEGATED),
        ("자동 손절선이 아니다.", TradeLanguageSemantic.NEGATED),
        ("향후 재검토 조건이다.", TradeLanguageSemantic.NONE),
        ("즉시 매수한다.", TradeLanguageSemantic.ACTIONABLE),
        ("반드시 매도한다.", TradeLanguageSemantic.ACTIONABLE),
    ),
)
def test_trade_language_semantic_distinguishes_action_and_negation(
    text: str,
    semantic: TradeLanguageSemantic,
) -> None:
    assert trade_language_semantic(text) == semantic


def test_trade_negation_does_not_swallow_later_actionable_directive() -> None:
    text = "즉시 매수가 아닌 것 같지만 결국 지금 매수해야 한다."

    assert trade_language_semantic(text) == TradeLanguageSemantic.ACTIONABLE
    assert mandatory_trade_directive_matches(text) == ("매수해야 한다",)


@pytest.mark.parametrize(
    "text",
    (
        "즉시 매수 신호가 아니다.",
        "즉시 매수 신호는 아니다.",
        "즉시 매수 신호가 아니며 향후 재검토 조건이다.",
        "지금 매도하라는 명령이 아니다.",
        "매수의 근거가 아니다.",
        "매수 조건은 아니다.",
        "자동 매도 조건이 아니다.",
        "즉시 진입 사유가 아니다.",
        "즉시 청산 트리거가 아니다.",
        "무조건 비중 축소 권고가 아니다.",
        "자동 손절 지시가 아니다.",
        "포지션 종료의 기준은 아니다.",
    ),
)
def test_ticker_free_nominal_trade_negation_matrix(text: str) -> None:
    assert trade_language_semantic(text) == TradeLanguageSemantic.NEGATED
    assert mandatory_trade_directive_matches(text) == ()


@pytest.mark.parametrize(
    "text",
    (
        "즉시 매수한다.",
        "반드시 매도해야 한다.",
        "무조건 매수하라.",
        "자동으로 매도한다.",
        "기계적으로 비중을 줄인다.",
        "반드시 포지션을 축소한다.",
        "즉시 손절해야 한다.",
        "즉시 진입한다.",
        "반드시 청산한다.",
        "무조건 포지션을 종료한다.",
        "전량 매도하라.",
        "매수 주문을 실행한다.",
    ),
)
def test_ticker_free_actionable_trade_matrix(text: str) -> None:
    assert trade_language_semantic(text) == TradeLanguageSemantic.ACTIONABLE
    assert mandatory_trade_directive_matches(text)


@pytest.mark.parametrize(
    ("text", "semantic"),
    (
        ("매수세와 거래량을 함께 관찰한다.", TradeLanguageSemantic.DESCRIPTIVE),
        ("매도 압력을 계속 관찰한다.", TradeLanguageSemantic.DESCRIPTIVE),
        ("진입 시점은 아직 불확실하다.", TradeLanguageSemantic.DESCRIPTIVE),
        ("향후 사업 성과를 재검토한다.", TradeLanguageSemantic.NONE),
        ("가치평가 근거를 확인한다.", TradeLanguageSemantic.NONE),
        ("실적 발표 뒤 판단을 갱신한다.", TradeLanguageSemantic.NONE),
    ),
)
def test_ticker_free_descriptive_and_none_trade_matrix(
    text: str,
    semantic: TradeLanguageSemantic,
) -> None:
    assert trade_language_semantic(text) == semantic
    assert mandatory_trade_directive_matches(text) == ()


@pytest.mark.parametrize(
    "text",
    (
        "매수 신호가 아니라고 보긴 어렵다.",
        "매도 조건이 아닌 것은 아니다.",
        "즉시 진입 사유가 아니지 않다.",
        "청산 명령이 아니라고 단정하기 어렵다.",
        "손절 기준이 아닌 셈은 아니다.",
        "비중 축소 권고가 아니라고 말하기 어렵다.",
        "포지션 종료 조건이 아니지 않다고 본다.",
        "매수 근거가 전혀 아니라고는 못한다.",
        "매도 신호가 아니라고 판단하기 어렵다.",
        "진입 조건이 아닌 것은 아니라고 설명한다.",
    ),
)
def test_ticker_free_ambiguous_action_language_is_advisory_not_hard_gate(
    text: str,
) -> None:
    assert directive_state(text) != DirectiveState.ACTIONABLE_DIRECTIVE
    assert mandatory_trade_directive_matches(text) == ()


def test_historical_nominal_negation_regression_after_generic_matrix() -> None:
    text = (
        "두 가격 경로 모두 즉시 매수 신호가 아니며 "
        "준공과 청구 확대가 확인된 뒤에만 재고할 조건이다."
    )

    assert trade_language_semantic(text) == TradeLanguageSemantic.NEGATED
    assert mandatory_trade_directive_matches(text) == ()


def test_historical_nominal_negation_still_exposes_later_action() -> None:
    text = "두 가격 경로 모두 즉시 매수 신호가 아니지만 지금은 매수해야 한다."

    assert trade_language_semantic(text) == TradeLanguageSemantic.ACTIONABLE
    assert mandatory_trade_directive_matches(text) == ("매수해야 한다",)


def test_probability_tokens_do_not_match_embedded_rate_metrics() -> None:
    assert directional_balance_language_errors(("승률 70%",)) == (
        "directional_balance_probability_language",
    )
    assert directional_balance_language_errors(("성공확률이 높다",)) == (
        "directional_balance_probability_language",
    )
    for text in (
        "주가 상승률 8%",
        "매출 성장률 20%",
        "하락률과 증가율을 함께 확인합니다.",
        "수익률과 마진율은 비율 지표입니다.",
    ):
        assert directional_balance_language_errors((text,)) == ()


@pytest.mark.parametrize(
    "text",
    (
        "지금 매수해야 한다.",
        "즉시 매수하라.",
        "지금 진입하라.",
        "반드시 매도해야 한다.",
        "전량 매도하라.",
        "무조건 매수.",
        "지금 비중을 늘려라.",
        "매수한다.",
        "매도한다.",
        "청산하라.",
        "손절해야 한다.",
        "비중을 줄여라.",
        "비중을 축소한다.",
        "비중을 감축해야 한다.",
        "비중을 확대하라.",
        "포지션을 종료한다.",
        "포지션을 축소하라.",
        "매수 주문을 실행하라.",
        "must sell.",
        "buy now.",
    ),
)
def test_mandatory_trade_directives_remain_blocked(text: str) -> None:
    assert mandatory_trade_directive_matches(text)


@pytest.mark.parametrize(
    "text",
    (
        "즉시 진입점이 아니라 추후 재검토 조건이다.",
        "즉시 진입 확신은 부족하다.",
        "매수 매력은 낮다.",
        "추격할 근거가 약하다.",
        "매도 명령이 아니다.",
        "현재는 진입보다 확인이 중요하다.",
        "매수 의견의 근거를 검토한다.",
        "매도 압력은 관찰 대상이다.",
        "진입 시점은 불확실하다.",
        "보유 근거를 재점검한다.",
        "매수세와 거래량을 함께 본다.",
        "매도세가 약해졌는지 확인한다.",
        "해당 가격은 손절선이 아니다.",
        "청산 위험은 낮다.",
        "비중 축소 필요성은 낮다.",
        "포지션 종료 조건은 아니다.",
        "현재 매수할 필요가 없다.",
        "기계적 매도를 권고하지 않는다.",
        "자동 매수 대신 사업 성과를 확인한다.",
        "buying interest remains weak.",
    ),
)
def test_safe_action_mentions_do_not_trigger_hard_gate(text: str) -> None:
    assert mandatory_trade_directive_matches(text) == ()


def _action_context(
    subject: ActionSubject,
    stance: StructuredActionStance,
) -> StructuredActionContext:
    return StructuredActionContext(
        action_subject=subject,
        action_stance=stance,
        entry_mode="NONE",
        directive_state=DirectiveState.NO_DIRECTIVE,
        action_role=ActionRole.RATIONALE,
    )


@pytest.mark.parametrize(
    ("context", "text"),
    (
        (_action_context(ActionSubject.NEW_BUYER, "WAIT"), "지금 매수해야 한다."),
        (_action_context(ActionSubject.NEW_BUYER, "AVOID"), "즉시 진입하라."),
        (_action_context(ActionSubject.NEW_BUYER, "WAIT"), "비중을 늘려라."),
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "전량 매도하라."),
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "청산하라."),
        (_action_context(ActionSubject.HOLDER, "HOLDABLE"), "전량 매도하라."),
        (_action_context(ActionSubject.HOLDER, "REVIEW"), "비중을 줄여라."),
        (_action_context(ActionSubject.HOLDER, "REVIEW"), "포지션을 종료하라."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "지금 매수해야 한다."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "비중을 확대하라."),
    ),
)
def test_structured_actionability_contradictions_are_detected(
    context: StructuredActionContext,
    text: str,
) -> None:
    assert structured_actionability_contradictions(context, text)


@pytest.mark.parametrize(
    ("context", "text"),
    (
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "지금 매수해야 한다."),
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "즉시 진입하라."),
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "비중을 늘려라."),
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "무조건 매수."),
        (_action_context(ActionSubject.NEW_BUYER, "ATTRACTIVE"), "매수 주문을 실행하라."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "반드시 매도해야 한다."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "전량 매도하라."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "청산하라."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "비중을 줄여라."),
        (_action_context(ActionSubject.HOLDER, "REDUCE"), "포지션을 종료하라."),
    ),
)
def test_structured_actionability_consistent_directives_do_not_contradict(
    context: StructuredActionContext,
    text: str,
) -> None:
    assert structured_actionability_contradictions(context, text) == ()


def _packet_with_metric_evidence(metric_text: str) -> DecisionEvidencePacket:
    packet = _packet()
    evidence = tuple(
        row.model_copy(
            update={
                "statement": metric_text,
                "metric_refs": checkpoint_metric_refs(metric_text),
            }
        )
        if row.ref_id == "ref:thesis"
        else row
        for row in packet.evidence
    )
    return packet.model_copy(update={"evidence": evidence})


def _packet_with_logical_metric_evidence(
    rows: tuple[tuple[str, str, LogicalSeverity], ...],
) -> DecisionEvidencePacket:
    packet = _packet()
    conditions = {
        ref_id: source_logical_condition(
            subject=packet.ticker,
            generation_id=packet.packet_id,
            evidence_ref=ref_id,
            statement=statement,
            severity=severity,
        )
        for ref_id, statement, severity in rows
    }
    return packet.model_copy(
        update={
            "evidence": tuple(
                evidence.model_copy(
                    update={
                        "statement": conditions[evidence.ref_id].expression.statement,
                        "metric_refs": conditions[evidence.ref_id].metric_refs,
                        "logical_condition": conditions[evidence.ref_id],
                    }
                )
                if evidence.ref_id in conditions
                else evidence
                for evidence in packet.evidence
            )
        }
    )


def _multi_ref_future_claim(
    refs: tuple[str, ...],
    text: str,
    *,
    kind: CheckpointKind,
    direction: MetricDirection,
) -> StructuredEvidenceClaim:
    return StructuredEvidenceClaim(
        text=text,
        evidence_refs=refs,
        semantic=ClaimSemanticMetadata(
            claim_type=ClaimType.FUTURE_CHECKPOINT,
            metric_refs=checkpoint_metric_refs(text),
            time_scope=ClaimTimeScope.FUTURE_CHECKPOINT,
            checkpoint_kind=kind,
            direction=direction,
        ),
    )


def test_same_severity_selected_evidence_metrics_form_bounded_union() -> None:
    packet = _packet_with_logical_metric_evidence(
        (
            ("ref:thesis", "FCF 악화는 무효화 후보입니다.", LogicalSeverity.INVALIDATION_CANDIDATE),
            ("ref:risk", "ROIC 악화는 무효화 후보입니다.", LogicalSeverity.INVALIDATION_CANDIDATE),
        )
    )
    claim = _multi_ref_future_claim(
        ("ref:thesis", "ref:risk"),
        "FCF와 ROIC가 악화되면 논리를 무효화 후보로 재검토한다.",
        kind=CheckpointKind.INVALIDATION,
        direction=MetricDirection.DETERIORATE,
    )
    candidate = _candidate().model_copy(update={"reevaluation_down": (claim,)})

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "future_checkpoint_kind_not_owned" not in result.errors
    assert "unsupported_future_checkpoint_metric" not in result.errors


def test_metric_union_never_crosses_logical_severity() -> None:
    packet = _packet_with_logical_metric_evidence(
        (
            ("ref:thesis", "FCF 개선은 강화 조건입니다.", LogicalSeverity.STRENGTHENING),
            ("ref:risk", "ROIC 악화는 무효화 후보입니다.", LogicalSeverity.INVALIDATION_CANDIDATE),
        )
    )
    claim = _multi_ref_future_claim(
        ("ref:thesis", "ref:risk"),
        "FCF와 ROIC가 개선되면 논리를 강화한다.",
        kind=CheckpointKind.STRENGTHEN,
        direction=MetricDirection.IMPROVE,
    )
    candidate = _candidate().model_copy(update={"reevaluation_up": (claim,)})

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "future_checkpoint_kind_not_owned" in result.errors


def test_metric_owned_without_strengthening_severity_remains_fail_closed() -> None:
    packet = _packet_with_logical_metric_evidence(
        (
            ("ref:thesis", "FCF 악화는 무효화 후보입니다.", LogicalSeverity.INVALIDATION_CANDIDATE),
        )
    )
    claim = _multi_ref_future_claim(
        ("ref:thesis",),
        "FCF가 개선되면 논리를 강화한다.",
        kind=CheckpointKind.STRENGTHEN,
        direction=MetricDirection.IMPROVE,
    )
    candidate = _candidate().model_copy(update={"reevaluation_up": (claim,)})

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "unsupported_future_checkpoint_metric" not in result.errors
    assert "future_checkpoint_kind_not_owned" in result.errors


def test_unselected_packet_evidence_cannot_contribute_metric_ownership() -> None:
    packet = _packet_with_logical_metric_evidence(
        (
            ("ref:thesis", "FCF 개선은 강화 조건입니다.", LogicalSeverity.STRENGTHENING),
            ("ref:risk", "ROIC 개선은 강화 조건입니다.", LogicalSeverity.STRENGTHENING),
        )
    )
    claim = _multi_ref_future_claim(
        ("ref:thesis",),
        "FCF와 ROIC가 개선되면 논리를 강화한다.",
        kind=CheckpointKind.STRENGTHEN,
        direction=MetricDirection.IMPROVE,
    )
    candidate = _candidate().model_copy(update={"reevaluation_up": (claim,)})

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "unsupported_future_checkpoint_metric" in result.errors
    assert "future_checkpoint_kind_not_owned" in result.errors


def test_owned_strengthening_metric_union_remains_eligible() -> None:
    packet = _packet_with_logical_metric_evidence(
        (
            ("ref:thesis", "FCF 개선은 강화 조건입니다.", LogicalSeverity.STRENGTHENING),
            ("ref:risk", "ROIC 개선은 강화 조건입니다.", LogicalSeverity.STRENGTHENING),
        )
    )
    claim = _multi_ref_future_claim(
        ("ref:thesis", "ref:risk"),
        "FCF와 ROIC가 개선되면 논리를 강화한다.",
        kind=CheckpointKind.STRENGTHEN,
        direction=MetricDirection.IMPROVE,
    )
    candidate = _candidate().model_copy(update={"reevaluation_up": (claim,)})

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "future_checkpoint_kind_not_owned" not in result.errors
    assert "unsupported_future_checkpoint_metric" not in result.errors


@pytest.mark.parametrize(
    "text",
    (
        "ROIC가 개선되는지 확인한다.",
        "ROIC 개선이 성장의 질을 확인해준다.",
        "FCF와 ROIC 개선 여부를 함께 본다.",
        "CCC 정상화가 운전자본 개선으로 이어지는지 확인한다.",
    ),
)
def test_future_metric_checkpoint_passes_only_with_owned_evidence(text: str) -> None:
    packet = _packet_with_metric_evidence(
        "FCF와 ROIC 및 CCC 개선 여부는 미래 검증 조건입니다."
    )
    candidate = _candidate().model_copy(
        update={"reevaluation_up": (_future_claim("ref:thesis", text),)}
    )

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "unsupported_future_checkpoint_metric" not in result.errors
    assert "unsupported_metric_or_inference" not in result.errors


@pytest.mark.parametrize(
    "text",
    (
        "CAPEX 이후 현금창출과 ROIC의 지속성을 우선한다.",
        "실제 ROIC와 FCF 증명이 방향을 가를 구간이다.",
        "대규모 CAPEX 이후에도 FCF와 ROIC가 장기 악화되면 논리를 재평가한다.",
        "대규모 CAPEX가 FCF 감소, 순부채 증가와 향후 ROIC 악화로 이어질 수 있다.",
        "선박 투자가 FCF 및 ROIC 개선으로 회수되지 않으면 자본효율을 재점검한다.",
        "AI CAPEX가 Cloud 성장과 FCF 및 ROIC로 전환돼야 정당화된다.",
        "인수 이후 ROIC가 구조적으로 악화될 때 보유 논리를 낮춘다.",
        "FCF와 ROIC가 장기 악화하거나 수익성 확보에 실패하면 재검토한다.",
        "현금 전환과 인수 이후 ROIC가 더 중요하다.",
        "FCF와 ROIC가 높아진 기대를 넘어야 한다.",
        "대규모 인수 이후 ROIC가 구조적으로 악화될 위험이 있다.",
        "향후 ROIC와 가치평가가 구조적으로 압박받을 수 있다.",
        "대규모 투자 뒤 ROIC까지 낮아지면 자본집약 성장의 경제성이 훼손된다.",
        "투자 이후 FCF와 ROIC의 장기 악화는 주당가치 논리를 훼손한다.",
    ),
)
def test_evidence_owned_metric_policy_and_condition_language_is_allowed(
    text: str,
) -> None:
    packet = _packet_with_metric_evidence("FCF와 ROIC는 향후 자본효율 검증 조건입니다.")
    candidate = _candidate().model_copy(
        update={"sector_interpretation": _future_claim("ref:thesis", text)}
    )

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Industrials"
    )

    assert "unsupported_future_checkpoint_metric" not in result.errors
    assert "unsupported_metric_or_inference" not in result.errors


def test_metric_metadata_may_preserve_owned_lineage_superset() -> None:
    packet = _packet_with_metric_evidence("OCF와 PPE CAPEX 및 FCF 근거입니다.")
    candidate = _candidate().model_copy(
        update={
            "earnings_estimate_context": StructuredEvidenceClaim(
                text="FCF는 음수였습니다.",
                evidence_refs=("ref:thesis",),
                semantic=ClaimSemanticMetadata(
                    metric_refs=checkpoint_metric_refs("OCF PPE CAPEX FCF"),
                    time_scope=ClaimTimeScope.HISTORICAL,
                ),
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "checkpoint_metric_metadata_mismatch" not in result.errors
    assert "unsupported_future_checkpoint_metric" not in result.errors


def test_evidence_owned_metric_required_improvement_language_is_allowed() -> None:
    packet = _packet_with_metric_evidence(
        "FCF와 ROIC는 향후 자본효율 검증 조건입니다."
    )
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={
                    "confirmation_business_condition": (
                        "영업이익률이 개선되고 FCF와 ROIC가 함께 나아져야 한다."
                    ),
                    "confirmation_business_condition_refs": ("ref:thesis",),
                    "confirmation_business_condition_semantic": ClaimSemanticMetadata(
                        claim_type=ClaimType.FUTURE_CHECKPOINT,
                        metric_refs=checkpoint_metric_refs(
                            "영업이익률이 개선되고 FCF와 ROIC가 함께 나아져야 한다."
                        ),
                        time_scope=ClaimTimeScope.FUTURE_CHECKPOINT,
                        checkpoint_kind=CheckpointKind.VALIDATION,
                        direction=MetricDirection.IMPROVE,
                    ),
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Industrials"
    )

    assert "unsupported_future_checkpoint_metric" not in result.errors
    assert "unsupported_metric_or_inference" not in result.errors


def test_future_metric_checkpoint_without_owned_evidence_is_rejected() -> None:
    candidate = _candidate().model_copy(
        update={
            "reevaluation_up": (
                _future_claim("ref:thesis", "ROIC 개선 여부를 확인한다."),
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "unsupported_future_checkpoint_metric" in result.errors
    assert "unsupported_metric_or_inference" in result.errors


@pytest.mark.parametrize(
    "text",
    (
        "향후 ROIC 악화로 이어질 수 있다.",
        "AI CAPEX가 ROIC로 전환돼야 정당화된다.",
        "인수 이후 ROIC가 구조적으로 악화될 때 보유 논리를 낮춘다.",
        "ROIC가 장기 악화하거나 수익성 확보에 실패하면 재검토한다.",
        "인수 이후 ROIC가 더 중요하다.",
        "ROIC가 높아진 기대를 넘어야 한다.",
        "대규모 인수 이후 ROIC가 구조적으로 악화될 위험이 있다.",
        "향후 ROIC와 가치평가가 구조적으로 압박받을 수 있다.",
        "대규모 투자 뒤 ROIC까지 낮아지면 자본집약 성장의 경제성이 훼손된다.",
    ),
)
def test_future_metric_policy_without_owned_evidence_is_rejected(text: str) -> None:
    candidate = _candidate().model_copy(
        update={
            "sector_interpretation": _future_claim("ref:thesis", text)
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Industrials"
    )

    assert "unsupported_future_checkpoint_metric" in result.errors
    assert "unsupported_metric_or_inference" in result.errors


@pytest.mark.parametrize(
    "text",
    (
        "현재 ROIC는 12.4%다.",
        "ROIC가 전년 8%에서 14%로 상승했다.",
        "현재 CCC는 31일이다.",
        "DSO는 42일로 개선됐다.",
        "ROIC 개선이 증명됐다.",
        "ROIC 개선이 확인되었다.",
        "현재 ROIC가 낮아졌다.",
    ),
)
def test_current_or_historical_metric_values_remain_rejected(text: str) -> None:
    packet = _packet_with_metric_evidence("ROIC와 CCC 및 DSO는 미래 검증 조건입니다.")
    candidate = _candidate().model_copy(
        update={
            "reevaluation_up": (
                StructuredEvidenceClaim(
                    text=text,
                    evidence_refs=("ref:thesis",),
                    semantic=ClaimSemanticMetadata(
                        metric_refs=checkpoint_metric_refs(text),
                        time_scope=ClaimTimeScope.CURRENT,
                    ),
                ),
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Software"
    )

    assert "unsupported_current_metric_value" in result.errors
    assert "unsupported_metric_or_inference" in result.errors


def test_mixed_language_decision_prose_is_rejected() -> None:
    candidate = _candidate().model_copy(
        update={"core_judgment": _claim("ref:thesis", "This judgment remained English.")}
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "mixed_language_decision_prose" in result.errors


def test_cross_ticker_repetition_scope_excludes_retained_factual_detail() -> None:
    factual = "이 문장은 동일한 동결 기반 메시지에서 보존된 긴 factual detail입니다."
    validation = StructuredAutonomyValidation(valid=True, errors=())
    rendered = (
        RenderedStructuredAutonomy(
            ticker="ONE",
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=f"🧠 AI 분석 판단:\n새 판단 소유 문장은 첫 번째 기업에만 해당합니다.\n\n📐 Valuation\n• {factual}\n",
            validation=validation,
        ),
        RenderedStructuredAutonomy(
            ticker="TWO",
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=f"🧠 AI 분석 판단:\n새 판단 소유 문장은 둘째 번 기업에만 해당합니다.\n\n📈 사업·실적\n• {factual}\n",
            validation=validation,
        ),
    )

    result = structured_autonomy_message_quality(rendered)

    assert result["status"] == "PASS"
    assert result["repeated_substantive_span_count"] == 0


def test_cross_ticker_repetition_still_rejects_new_judgment_template() -> None:
    repeated = "이 판단 문장은 새 structured autonomy 영역에서 반복됩니다."
    validation = StructuredAutonomyValidation(valid=True, errors=())
    rendered = tuple(
        RenderedStructuredAutonomy(
            ticker=ticker,
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=f"🧠 AI 분석 판단:\n{repeated}\n",
            validation=validation,
        )
        for ticker in ("ONE", "TWO")
    )

    result = structured_autonomy_message_quality(rendered)

    assert result["status"] == "FAIL"
    assert "cross_ticker_substantive_repetition" in result["errors"]


def test_repeated_negated_action_wrapper_is_classified_but_not_blocked() -> None:
    repeated = (
        "현재는 진입을 피하며 보존된 두 가격 경로는 모두 "
        "즉시 매수가 아닌 향후 재검토 조건이다."
    )
    validation = StructuredAutonomyValidation(valid=True, errors=())
    rendered = tuple(
        RenderedStructuredAutonomy(
            ticker=ticker,
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=f"🧠 AI 분석 판단:\n{repeated}\n",
            validation=validation,
        )
        for ticker in ("ONE", "TWO")
    )

    result = structured_autonomy_message_quality(rendered)

    assert repetition_semantic_role(repeated) == (
        RepetitionSemanticRole.ACTION_CONTEXT_WRAPPER_REPEAT
    )
    assert result["status"] == "PASS"
    assert result["repeated_substantive_span_count"] == 0
    assert result["repetition_taxonomy"]["ACTION_CONTEXT_WRAPPER_REPEAT"] == 2


def test_repeated_required_safety_sentence_is_not_substantive_spam() -> None:
    repeated = "해당 가격은 자동 손절선이 아닙니다."
    validation = StructuredAutonomyValidation(valid=True, errors=())
    rendered = tuple(
        RenderedStructuredAutonomy(
            ticker=ticker,
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=f"🧠 AI 분석 판단:\n{repeated}\n",
            validation=validation,
        )
        for ticker in ("ONE", "TWO")
    )

    result = structured_autonomy_message_quality(rendered)

    assert repetition_semantic_role(repeated) == (
        RepetitionSemanticRole.REQUIRED_SAFETY_REPEAT
    )
    assert result["status"] == "PASS"


def test_detail_sanitizer_removes_legacy_judgment_authority() -> None:
    detail = """🏢 Test(TEST)

투자 논리: 약화

🎯 핵심
이 문단은 별도 판단을 소유합니다.

📈 사업·실적
• 매출 사실입니다.

📐 Valuation
현재 Valuation: 확인 필요
"""

    sanitized = sanitize_detail_body(detail)

    assert "투자 논리:" not in sanitized
    assert "이 문단은" not in sanitized
    assert "📈 사업·실적" in sanitized
    assert "📐 Valuation" in sanitized


def test_renderer_uses_accepted_plan_once_and_separates_price_roles() -> None:
    rendered = render_structured_autonomy_message(
        _packet(),
        _candidate(),
        price_map=_price_map(),
        industry="Software",
        base_detail_text="""투자 논리: 약화

📈 사업·실적
• 검증된 실적 사실입니다.
""",
    )

    assert rendered.validation.valid is True
    assert rendered.actionability == build_structured_actionability(_candidate())
    assert rendered.text.count("🧠 판단:") == 1
    assert "🧠 판단: HOLD · BUY:SELL 5.5:4.5" in rendered.text
    assert "HOLD 성향: BUY 쪽 HOLD" in rendered.text
    assert "신규 관찰자: WAIT · 진입 방식: 눌림" in rendered.text
    assert "보유자: HOLDABLE" in rendered.text
    assert "가격 재점검 · 눌림: $90~$94" in rendered.text
    assert (
        "가격 재점검 · 확인: $112 저항 상단 돌파 확인 + "
        "상용화 경제성과 공급 완화를 함께 확인합니다."
    ) in rendered.text
    assert "• 확인 조건:" not in rendered.text
    assert "가격 재점검 · 상방: $108~$112" in rendered.text
    assert "가격 재점검 · 하방: $86" in rendered.text
    assert "기업가치 무효화:" in rendered.text
    assert "투자 논리: 약화" not in rendered.text


def test_avoid_renderer_uses_reconsideration_not_actionable_entry() -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={"stance": "AVOID"}
            )
        }
    )

    rendered = render_structured_autonomy_message(
        _packet(),
        candidate,
        price_map=_price_map(),
        industry="Software",
        base_detail_text="",
    )

    assert rendered.validation.valid is True
    assert "신규 관찰자: AVOID · 진입 방식: 눌림" in rendered.text
    assert "가격 재점검 · 눌림: $90~$94" in rendered.text
    assert "가격 재점검 · 확인: $112 저항 상단 돌파 확인" in rendered.text
    assert "눌림 진입 검토:" not in rendered.text


def test_avoid_with_retained_confirmation_cannot_select_none_mode() -> None:
    price_map = {
        **_price_map(),
        "nearest_supports": [],
        "registered_price_rules": {
            "basis_ref": "ref:price",
            "warning_price": 86.0,
            "invalidation_price": 82.0,
        },
    }
    buyer = _candidate().new_buyer_view.model_copy(
        update={
            "stance": "AVOID",
            "pullback_entry_zone_low": None,
            "pullback_entry_zone_high": None,
            "pullback_entry_basis": (),
            "preferred_entry_mode": "NONE",
        }
    )
    candidate = _candidate().model_copy(update={"new_buyer_view": buyer})

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=price_map, industry="Software"
    )

    assert "preferred_entry_mode_inconsistent" in result.errors


def test_avoid_with_retained_confirmation_uses_future_confirmation_mode() -> None:
    price_map = {
        **_price_map(),
        "nearest_supports": [],
        "registered_price_rules": {
            "basis_ref": "ref:price",
            "warning_price": 86.0,
            "invalidation_price": 82.0,
        },
    }
    buyer = _candidate().new_buyer_view.model_copy(
        update={
            "stance": "AVOID",
            "pullback_entry_zone_low": None,
            "pullback_entry_zone_high": None,
            "pullback_entry_basis": (),
            "preferred_entry_mode": "CONFIRMATION",
        }
    )
    candidate = _candidate().model_copy(update={"new_buyer_view": buyer})

    rendered = render_structured_autonomy_message(
        _packet(),
        candidate,
        price_map=price_map,
        industry="Software",
        base_detail_text="",
    )

    assert rendered.validation.valid is True
    assert "신규 관찰자: AVOID · 진입 방식: 추세 확인" in rendered.text
    assert "가격 재점검 · 확인: $112 저항 상단 돌파 확인" in rendered.text
    assert "현재 선호:" not in rendered.text


def test_model_owned_confirmation_business_condition_rejects_price_structure() -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={
                    "confirmation_business_condition": (
                        "저항 돌파와 상용화 경제성을 함께 확인합니다."
                    )
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert (
        "confirmation_business_condition_contains_price_structure_semantics"
        in result.errors
    )


@pytest.mark.parametrize(
    "text",
    CONFIRMATION_BUSINESS_LANGUAGE_FIXTURES,
)
def test_confirmation_business_condition_allows_business_language(text: str) -> None:
    assert confirmation_business_condition_has_price_structure_semantics(text) is False


@pytest.mark.parametrize(
    "text",
    CONFIRMATION_PRICE_STRUCTURE_FIXTURES,
)
def test_confirmation_business_condition_blocks_price_structure(text: str) -> None:
    assert confirmation_business_condition_has_price_structure_semantics(text) is True


@pytest.mark.parametrize(
    "text",
    (
        "수주가 회복되고 영업현금흐름이 개선되는 것",
        "발주가 증가하고 생산 효율이 회복되는 것",
        "신규수주가 확대되고 수익성이 개선되는 것",
        "해외수주가 유지되고 마진이 회복되는 것",
        "최종가격 상승이 수익성 개선을 지지함.",
    ),
)
def test_korean_business_compounds_do_not_match_embedded_price_tokens(
    text: str,
) -> None:
    assert korean_price_subject_action_matches(text) == ()
    assert confirmation_business_condition_has_price_structure_semantics(text) is False


@pytest.mark.parametrize("prefix", ("수", "발", "신규수", "해외수"))
@pytest.mark.parametrize("action", ("확대", "증가", "유지", "개선", "회복"))
def test_korean_compound_collision_corpus_is_deterministically_safe(
    prefix: str,
    action: str,
) -> None:
    text = f"{prefix}주가 {action}되고 영업현금흐름이 회복되는 것"

    assert korean_price_subject_action_matches(text) == ()
    assert confirmation_business_condition_has_price_structure_semantics(text) is False


@pytest.mark.parametrize(
    "subject",
    ("주가", "현재주가", "당일주가", "종가", "전일종가", "정규장종가"),
)
@pytest.mark.parametrize(
    "action",
    ("돌파", "상회", "하회", "회복", "안착", "재지지", "이탈"),
)
def test_recognized_korean_price_subject_action_corpus_is_detected(
    subject: str,
    action: str,
) -> None:
    text = f"{subject}가 확인 구간을 {action}해야 한다."

    assert korean_price_subject_action_matches(text) == ((subject, action),)
    assert confirmation_business_condition_has_price_structure_semantics(text) is True


@pytest.mark.parametrize(
    "text",
    (
        CRCL_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
        MU_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
        KR_047810_PRIOR_CONFIRMATION_BUSINESS_CONDITION,
    ),
    ids=("crcl", "mu", "047810"),
)
def test_exact_business_conditions_pass_candidate_validation(text: str) -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={"confirmation_business_condition": text}
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert result.valid is True
    assert (
        "confirmation_business_condition_contains_price_structure_semantics"
        not in result.errors
    )


def test_confirmation_business_condition_requires_non_price_evidence() -> None:
    price_only = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={"confirmation_business_condition_refs": ("ref:price",)}
            )
        }
    )
    mixed = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={
                    "confirmation_business_condition_refs": (
                        "ref:price",
                        "ref:earnings",
                    )
                }
            )
        }
    )

    price_only_result = validate_structured_autonomy_candidate(
        _packet(), price_only, price_map=_price_map(), industry="Software"
    )
    mixed_result = validate_structured_autonomy_candidate(
        _packet(), mixed, price_map=_price_map(), industry="Software"
    )

    assert "confirmation_business_condition_price_only_evidence" in price_only_result.errors
    assert "confirmation_business_condition_price_only_evidence" not in mixed_result.errors
    assert mixed_result.valid is True


def test_confirmation_business_condition_rejects_numeric_backdoor() -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={
                    "confirmation_business_condition": "$950 돌파 후 재지지가 필요하다."
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "confirmation_business_condition_contains_price_numeric" in result.errors
    assert (
        "confirmation_business_condition_contains_price_structure_semantics"
        in result.errors
    )


def test_evidence_owned_product_identifiers_are_not_price_numerics() -> None:
    packet = _packet_with_metric_evidence(
        "KF-21 양산 인도와 FA-50 신규 수주는 검증할 제품 식별자입니다."
    )
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={
                    "confirmation_business_condition": (
                        "KF-21 양산 인도 확대와 FA-50 신규 수주가 이어지고 "
                        "영업이익률과 현금흐름이 개선되는 것"
                    ),
                    "confirmation_business_condition_refs": ("ref:thesis",),
                }
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        packet, candidate, price_map=_price_map(), industry="Industrials"
    )

    assert "confirmation_business_condition_contains_price_numeric" not in result.errors
    assert "numeric_prose_outside_structured_fields" not in result.errors


def test_confirmation_semantics_must_match_selected_price_basis() -> None:
    candidate = _candidate().model_copy(
        update={
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={"confirmation_semantics": "REGISTERED_PRICE_CONFIRMATION"}
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "confirmation_semantics_basis_mismatch" in result.errors


def test_confirmation_renderer_structure_is_not_substantive_repetition() -> None:
    validation = StructuredAutonomyValidation(valid=True, errors=())
    rendered = (
        RenderedStructuredAutonomy(
            ticker="ONE",
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=(
                "🧠 종합 방향: HOLD\n"
                "• 상향 재검토: $10 종가 상회 확인 + 상용화 경제성을 확인합니다.\n"
            ),
            validation=validation,
        ),
        RenderedStructuredAutonomy(
            ticker="TWO",
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=(
                "🧠 종합 방향: HOLD\n"
                "• 상향 재검토: $20 종가 상회 확인 + 수익성 정상화를 확인합니다.\n"
            ),
            validation=validation,
        ),
    )

    result = structured_autonomy_message_quality(rendered)

    assert result["status"] == "PASS"
    assert result["repeated_substantive_span_count"] == 0


def test_confirmation_renderer_still_rejects_repeated_business_condition() -> None:
    validation = StructuredAutonomyValidation(valid=True, errors=())
    business = "상용화 경제성과 수익성 정상화를 함께 확인합니다."
    rendered = tuple(
        RenderedStructuredAutonomy(
            ticker=ticker,
            decision="HOLD",
            lean=HoldLean.NEUTRAL,
            text=f"🧠 종합 방향: HOLD\n• 상향 재검토: ${level} 종가 상회 확인 + {business}\n",
            validation=validation,
        )
        for ticker, level in (("ONE", 10), ("TWO", 20))
    )

    result = structured_autonomy_message_quality(rendered)

    assert result["status"] == "FAIL"
    assert business in result["repeated_substantive_spans"]


def test_directional_unknown_needs_non_unknown_economic_evidence() -> None:
    candidate = _candidate().model_copy(
        update={
            "unknown_treatments": (
                UnknownTreatment(
                    summary="핵심 증거가 아직 확인되지 않았습니다.",
                    evidence_refs=("ref:unknown",),
                    treatment="DIRECTIONAL_NEGATIVE",
                    directional_negative_basis=("ref:unknown",),
                ),
            )
        }
    )

    result = validate_structured_autonomy_candidate(
        _packet(), candidate, price_map=_price_map(), industry="Software"
    )

    assert "unknown_directional_negative_without_non_unknown_evidence" in result.errors


def test_same_evidence_stability_classification_catches_lean_and_action_reversals() -> None:
    buy_lean = _candidate()
    sell_lean = _candidate().model_copy(
        update={
            "directional_balance": DirectionalBalance(buy=4.5, sell=5.5),
            "new_buyer_view": _candidate().new_buyer_view.model_copy(
                update={"stance": "AVOID"}
            ),
            "holder_view": _candidate().holder_view.model_copy(
                update={"stance": "REDUCE"}
            ),
        }
    )
    neutral = _candidate().model_copy(
        update={"directional_balance": DirectionalBalance(buy=5, sell=5)}
    )

    row = classify_same_evidence_runs((buy_lean, sell_lean, neutral))
    summary = stability_summary((row,))

    assert row["classification"] == "UNSTABLE"
    assert row["unexplained_hold_lean_flip"] is True
    assert summary["unexplained_hold_lean_flip_count"] == 1


def test_same_evidence_stability_allows_half_point_balance_noise() -> None:
    neutral = _candidate().model_copy(
        update={"directional_balance": DirectionalBalance(buy=5, sell=5)}
    )

    row = classify_same_evidence_runs((_candidate(), _candidate(), neutral))

    assert row["classification"] == "BOUNDARY_UNCERTAINTY"
    assert row["max_balance_distance"] == 0.5
