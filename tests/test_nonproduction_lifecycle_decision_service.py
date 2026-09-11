from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.direction_timing_ownership_service import (
    DirectionalCoreCandidate,
    PriceTimingCandidate,
)
from app.services.nonproduction_lifecycle_decision_service import (
    DERIVATIVE_LABEL,
    DeltaState,
    InMemoryIntentLedger,
    IntentKind,
    NonproductionLifecycleContext,
    build_nonproduction_derivative,
    plan_nonproduction_intents,
)
from scripts.synthetic_canary_fixture_repair_ownership_resume import (
    fictional_owned,
    fixture_core,
    fixture_timing,
)


def _claim(value: object, text: str):
    return value.model_copy(update={"text": text})


def _korean_core(ticker: str = "SYNTHETIC_M2"):
    owned = fictional_owned(ticker, market="us")
    base = fixture_core(owned)
    buyer = base.fundamental_new_buyer.model_copy(
        update={
            "summary": "확인된 사업 근거는 균형적이어서 추가 확인 전에는 기다립니다.",
            "confirmation_business_condition": (
                "후속 공식 자료에서 계약 이행과 영업 성과가 함께 확인돼야 합니다."
            ),
        }
    )
    holder = base.fundamental_holder.model_copy(
        update={
            "summary": "현재 사업 근거가 유지되는 동안 보유 관점은 유지할 수 있습니다.",
            "business_invalidation_condition": (
                "계약 이행 훼손과 영업 성과 악화가 공식 자료에서 확인되면 재검토합니다."
            ),
        }
    )
    core = base.model_copy(
        update={
            "business_thesis_context": _claim(
                base.business_thesis_context,
                "현재 사업 근거는 안정적이지만 후속 실행 확인이 필요합니다.",
            ),
            "earnings_estimate_context": _claim(
                base.earnings_estimate_context,
                "공식 영업 실적은 양수이나 추정치 변화는 별도로 확인해야 합니다.",
            ),
            "market_expectation_context": _claim(
                base.market_expectation_context,
                "시장 기대를 충족하려면 계약 실행의 지속성이 필요합니다.",
            ),
            "valuation_context": _claim(
                base.valuation_context,
                "안전한 가치평가 근거가 없어 가격 매력도는 판단하지 않습니다.",
            ),
            "risk_context": _claim(
                base.risk_context,
                "고객 집중은 확인된 구조적 위험으로 남아 있습니다.",
            ),
            "sector_interpretation": _claim(
                base.sector_interpretation,
                "업종 수요는 혼재해 기업 실행 근거와 분리해 봅니다.",
            ),
            "buy_drivers": (
                _claim(base.buy_drivers[0], "안정적인 수요와 계약 실행이 긍정 근거입니다."),
            ),
            "sell_drivers": (
                base.sell_drivers[0].model_copy(
                    update={"text": "고객 집중이 판단 확신도를 제한하는 구조적 위험입니다."}
                ),
            ),
            "dominant_evidence": _claim(
                base.dominant_evidence,
                "현재 판단은 가격보다 사업 실행과 영업 실적 근거가 지배합니다.",
            ),
            "uncertainty_limit": _claim(
                base.uncertainty_limit,
                "향후 계약 이행의 지속성은 아직 확인되지 않았습니다.",
            ),
            "core_investment_judgment": _claim(
                base.core_investment_judgment,
                "사업 근거와 위험이 균형을 이뤄 현재 절대 판단은 중립입니다.",
            ),
            "unknown_treatments": (
                base.unknown_treatments[0].model_copy(
                    update={"summary": "향후 계약 이행의 지속성은 미확인입니다."}
                ),
            ),
            "fundamental_new_buyer": buyer,
            "fundamental_holder": holder,
            "business_reevaluation_up": (
                _claim(
                    base.business_reevaluation_up[0],
                    "후속 공식 자료에서 계약 이행과 영업 성과가 개선되면 상향 재평가합니다.",
                ),
            ),
            "business_reevaluation_down": (
                _claim(
                    base.business_reevaluation_down[0],
                    "후속 공식 자료에서 계약 이행과 영업 성과가 악화되면 하향 재평가합니다.",
                ),
            ),
        }
    )
    return owned, core


def _korean_timing(owned, core: DirectionalCoreCandidate) -> PriceTimingCandidate:
    base = fixture_timing(owned, core)
    return base.model_copy(
        update={
            "entry_reason": "검증된 진입 가격이 없어 현재는 가격 조건을 제시하지 않습니다.",
            "price_review_context": _claim(
                base.price_review_context,
                "확인된 지지 구간은 가격 재점검의 맥락으로만 사용합니다.",
            ),
            "price_confirmation_context": _claim(
                base.price_confirmation_context,
                "기술적 확인은 중립이며 사업 판단을 바꾸지 않습니다.",
            ),
            "price_support_context": _claim(
                base.price_support_context,
                "지지 구간은 사업 근거가 아닌 가격 맥락입니다.",
            ),
            "technical_rationale": _claim(
                base.technical_rationale,
                "기술 지표는 중립 상태로 가격 판단만 제한합니다.",
            ),
            "supply_positioning_rationale": _claim(
                base.supply_positioning_rationale,
                "수급은 균형적이며 사업 방향 근거로 사용하지 않습니다.",
            ),
        }
    )


def _derivative(lifecycle: NonproductionLifecycleContext):
    owned, core = _korean_core()
    timing = _korean_timing(owned, core)
    if lifecycle.delta_state == DeltaState.STRENGTHENED:
        core = core.model_copy(update={"business_thesis_change": "STRENGTHENED"})
        timing = _korean_timing(owned, core)
    elif lifecycle.delta_state == DeltaState.WEAKENED:
        core = core.model_copy(update={"business_thesis_change": "WEAKENED"})
        timing = _korean_timing(owned, core)
    elif lifecycle.delta_state == DeltaState.UNAVAILABLE:
        core = core.model_copy(update={"business_thesis_change": "UNRESOLVED"})
        timing = _korean_timing(owned, core)
    return build_nonproduction_derivative(
        owned=owned,
        core=core,
        timing=timing,
        lifecycle=lifecycle,
        price_map={},
        industry="Software",
    )


def test_initial_absolute_and_baseline_are_not_daily_delta() -> None:
    initial = _derivative(
        NonproductionLifecycleContext(
            fixture_id="initial-new",
            mode="INITIAL_ABSOLUTE",
            subject_lifecycle="NEW_ISSUER",
            bootstrap_enrichment=True,
        )
    )
    baseline = _derivative(
        NonproductionLifecycleContext(
            fixture_id="baseline-existing",
            mode="MONITORING_BASELINE",
            subject_lifecycle="EXISTING_MONITORED",
            explicit_monitoring_intent=True,
            onboarding_complete=True,
            bootstrap_enrichment=True,
        )
    )

    assert "1. 투자 논리 변화" not in initial.text
    assert "1. 투자 논리 변화" not in baseline.text
    assert initial.lifecycle.delta_state == DeltaState.NOT_APPLICABLE
    assert baseline.lifecycle.delta_state == DeltaState.NOT_APPLICABLE
    assert initial.candidate_validation.valid is True
    assert baseline.candidate_validation.valid is True


def test_explicit_registration_intent_and_incomplete_onboarding() -> None:
    analysis = NonproductionLifecycleContext(
        fixture_id="analysis-only",
        mode="INITIAL_ABSOLUTE",
        subject_lifecycle="NEW_ISSUER",
    )
    pending = NonproductionLifecycleContext(
        fixture_id="explicit-pending",
        mode="MONITORING_BASELINE",
        subject_lifecycle="NEW_ISSUER",
        explicit_monitoring_intent=True,
        onboarding_complete=False,
    )

    analysis_kinds = {row.kind for row in plan_nonproduction_intents(analysis, packet_id="p")}
    pending_kinds = {row.kind for row in plan_nonproduction_intents(pending, packet_id="p")}
    assert IntentKind.REGISTRATION_CONTINUATION not in analysis_kinds
    assert IntentKind.REGISTRATION_CONTINUATION in pending_kinds
    assert IntentKind.ONBOARDING_RESUME in pending_kinds
    assert analysis.registration_allowed is False
    assert pending.monitoring_ready is False


@pytest.mark.parametrize(
    "updates,error",
    [
        (
            {
                "refresh_state": "MISSING",
                "delta_state": "NO_MATERIAL_CHANGE",
                "evidence_change_scope": "NONE",
            },
            "missing_refresh_cannot_be_no_material_change",
        ),
        (
            {
                "refresh_state": "AVAILABLE",
                "delta_state": "STRENGTHENED",
                "evidence_change_scope": "BUSINESS",
                "bootstrap_enrichment": True,
            },
            "bootstrap_enrichment_cannot_be_daily_thesis_delta",
        ),
        (
            {
                "refresh_state": "AVAILABLE",
                "delta_state": "WEAKENED",
                "evidence_change_scope": "PRICE_ONLY",
            },
            "price_only_change_cannot_be_thesis_delta",
        ),
    ],
)
def test_invalid_daily_semantic_collapses_are_rejected(updates, error: str) -> None:
    with pytest.raises(ValidationError, match=error):
        NonproductionLifecycleContext(
            fixture_id="bad-daily",
            mode="DAILY_DELTA",
            subject_lifecycle="EXISTING_MONITORED",
            baseline_ref="baseline-1",
            baseline_cutoff="2026-09-07T00:00:00Z",
            **updates,
        )


def test_missing_refresh_is_unavailable_and_price_only_is_not_thesis_delta() -> None:
    missing = _derivative(
        NonproductionLifecycleContext(
            fixture_id="missing-refresh",
            mode="DAILY_DELTA",
            subject_lifecycle="EXISTING_MONITORED",
            explicit_monitoring_intent=True,
            onboarding_complete=True,
            refresh_state="MISSING",
            evidence_change_scope="UNKNOWN",
            delta_state="UNAVAILABLE",
            delta_summary="자료 갱신 부재로 오늘의 변화는 판정하지 않습니다.",
            baseline_ref="baseline-1",
            baseline_cutoff="2026-09-07T00:00:00Z",
        )
    )
    price_only = _derivative(
        NonproductionLifecycleContext(
            fixture_id="price-only",
            mode="DAILY_DELTA",
            subject_lifecycle="EXISTING_MONITORED",
            refresh_state="AVAILABLE",
            evidence_change_scope="PRICE_ONLY",
            delta_state="PRICE_ONLY_CONTEXT",
            delta_summary="가격 변화는 확인됐지만 사업 논리 변화로 보지 않습니다.",
            baseline_ref="baseline-1",
            baseline_cutoff="2026-09-07T00:00:00Z",
        )
    )

    assert missing.lifecycle_validation.valid is True
    assert missing.composed.core.business_thesis_change == "UNRESOLVED"
    assert "delta_state=UNAVAILABLE" in missing.text
    assert price_only.lifecycle_validation.valid is True
    assert price_only.composed.core.business_thesis_change == "UNCHANGED"


def test_unknown_is_not_negative_without_confirmed_basis() -> None:
    owned, core = _korean_core()
    timing = _korean_timing(owned, core)
    lifecycle = NonproductionLifecycleContext(
        fixture_id="unknown",
        mode="INITIAL_ABSOLUTE",
        subject_lifecycle="NEW_ISSUER",
    )
    safe = build_nonproduction_derivative(
        owned=owned,
        core=core,
        timing=timing,
        lifecycle=lifecycle,
        price_map={},
        industry="Software",
    )
    invalid_unknown = core.unknown_treatments[0].model_copy(
        update={"treatment": "DIRECTIONAL_NEGATIVE", "directional_negative_basis": ()}
    )
    invalid_core = core.model_copy(update={"unknown_treatments": (invalid_unknown,)})
    invalid_timing = _korean_timing(owned, invalid_core)
    invalid = build_nonproduction_derivative(
        owned=owned,
        core=invalid_core,
        timing=invalid_timing,
        lifecycle=lifecycle,
        price_map={},
        industry="Software",
    )

    assert safe.lifecycle_validation.valid is True
    assert invalid.lifecycle_validation.valid is False
    assert "unknown_directional_negative_without_economic_basis" in (
        invalid.lifecycle_validation.errors
    )


def test_existing_and_new_issuer_share_decision_contract() -> None:
    new = _derivative(
        NonproductionLifecycleContext(
            fixture_id="new",
            mode="INITIAL_ABSOLUTE",
            subject_lifecycle="NEW_ISSUER",
        )
    )
    existing = _derivative(
        NonproductionLifecycleContext(
            fixture_id="existing",
            mode="MONITORING_BASELINE",
            subject_lifecycle="EXISTING_MONITORED",
            explicit_monitoring_intent=True,
            onboarding_complete=True,
        )
    )

    assert new.composed.candidate == existing.composed.candidate
    assert new.composed.contract == existing.composed.contract
    assert new.lineage["composed_sha256"] == existing.lineage["composed_sha256"]
    assert new.lifecycle.mode != existing.lifecycle.mode


def test_nonproduction_intents_are_idempotent() -> None:
    lifecycle = NonproductionLifecycleContext(
        fixture_id="idempotent",
        mode="MONITORING_BASELINE",
        subject_lifecycle="NEW_ISSUER",
        explicit_monitoring_intent=True,
        onboarding_complete=False,
    )
    first_plan = plan_nonproduction_intents(lifecycle, packet_id="packet-1")
    second_plan = plan_nonproduction_intents(lifecycle, packet_id="packet-1")
    ledger = InMemoryIntentLedger()

    first_insert = ledger.apply(first_plan)
    second_insert = ledger.apply(second_plan)

    assert first_plan == second_plan
    assert {row.kind for row in first_insert} == {
        IntentKind.REGISTRATION_CONTINUATION,
        IntentKind.ONBOARDING_RESUME,
        IntentKind.BASELINE,
        IntentKind.ASSESSMENT,
        IntentKind.FILE_ONLY_DELIVERY,
    }
    assert second_insert == ()
    assert ledger.count == len(first_insert)


def test_file_only_renderer_has_no_queue_or_send_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"queue": 0, "send": 0}

    def fail_queue(*_args, **_kwargs):
        calls["queue"] += 1
        raise AssertionError("production queue called")

    async def fail_send(*_args, **_kwargs):
        calls["send"] += 1
        raise AssertionError("production send called")

    monkeypatch.setattr(
        "app.services.notification_service.queue_daily_stock_notification",
        fail_queue,
    )
    monkeypatch.setattr(
        "app.services.notification_service.dispatch_pending_notifications",
        fail_send,
    )
    derivative = _derivative(
        NonproductionLifecycleContext(
            fixture_id="file-only",
            mode="INITIAL_ABSOLUTE",
            subject_lifecycle="NEW_ISSUER",
        )
    )
    output = tmp_path / "message.txt"
    output.write_text(derivative.text, encoding="utf-8")

    assert output.read_text(encoding="utf-8").startswith(DERIVATIVE_LABEL)
    assert calls == {"queue": 0, "send": 0}
    assert derivative.notification_queue_writes == 0
    assert derivative.production_sends == 0
    assert derivative.production_db_mutations == 0
