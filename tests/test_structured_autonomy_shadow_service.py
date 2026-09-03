from __future__ import annotations

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
)
from app.services.directional_balance_service import DirectionalBalance
from app.services.structured_autonomy_shadow_service import (
    ClassifiedSellDriver,
    HoldLean,
    HolderViewV2,
    NewBuyerViewV2,
    StructuredAutonomyCandidate,
    RenderedStructuredAutonomy,
    StructuredAutonomyValidation,
    UnknownTreatment,
    derive_hold_lean,
    hold_lean_flip,
    render_structured_autonomy_message,
    sanitize_detail_body,
    structured_autonomy_message_quality,
    validate_structured_autonomy_candidate,
)


def _claim(ref: str, text: str = "검증된 사업 근거가 판단을 지지합니다.") -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=(ref,))


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
            confirmation_condition="사업 근거와 가격 방어를 함께 확인합니다.",
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
        ),
        reevaluation_up=(_claim("ref:earnings"),),
        reevaluation_down=(_claim("ref:risk"),),
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
    assert rendered.text.count("🧠 AI 분석 판단:") == 1
    assert "판단 방향: BUY 쪽 HOLD" in rendered.text
    assert "눌림 진입 검토: $90~$94" in rendered.text
    assert "추세 확인 가격: $112" in rendered.text
    assert "상방 매도·축소 검토: $108~$112" in rendered.text
    assert "하방 재점검: $86" in rendered.text
    assert "투자 논리: 약화" not in rendered.text
