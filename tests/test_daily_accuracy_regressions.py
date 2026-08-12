import json
from datetime import date

from sqlmodel import Session

from app.database import engine, init_db
from app.macro.theses import update_macro_theses
from app.providers.filings import _filter_items_by_receipt
from app.models.event import Event
from app.models.macro import MacroRegimeAssessment, ThesisMacroImpact
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.schemas.thesis import AssessmentStatus, InvestorSupplyContext, PriceContext
from app.schemas.thesis import PricePeriodSummary, PriceRulesInput
from app.services.daily_digest import _macro_paths
from app.services.financial_validation import (
    normalize_financial_number,
    validate_event_financials,
)
from app.services.thesis_evaluation_service import evaluate_thesis, recent_events_for_assessment


def _thesis() -> InvestmentThesis:
    return InvestmentThesis(
        ticker="DELTA",
        version=1,
        core_thesis="새 고객과 반복 가능한 현금흐름이 성장을 지지한다.",
        strengthen_signals=json.dumps(["new customer production order"]),
        weaken_signals=json.dumps(["free cash flow deterioration"]),
        invalidation_signals=json.dumps(["largest customer terminates all orders"]),
        valuation_framework=json.dumps({"primary_method": "forward P/E"}),
    )


def _event(**updates: object) -> Event:
    values: dict[str, object] = {
        "ticker": "DELTA",
        "date": date(2051, 1, 2),
        "source": "Company filing",
        "provider": "sec_edgar",
        "title": "New customer production order confirmed",
        "url": "https://example.com/delta-order",
        "event_type": "production_order",
        "confirmed_facts": json.dumps(["New customer production order was confirmed"]),
        "inferred_implications": "[]",
        "unknowns": "[]",
        "relevance_score": 70,
        "relevance_reason": "material customer evidence",
    }
    values.update(updates)
    return Event(**values)


def _previous(status: str = "strengthened") -> ThesisAssessment:
    return ThesisAssessment(
        ticker="DELTA",
        thesis_version=1,
        assessment_date=date(2051, 1, 2),
        status=status,
        business_thesis_change=status,
        summary="previous",
        new_buyer_view="previous",
        holder_view="previous",
        price_view="previous",
        risk_level="normal",
        confirmed_facts=json.dumps(["New customer production order was confirmed"]),
    )


def test_case_a_previously_used_earnings_or_order_is_not_strengthened_again() -> None:
    result = evaluate_thesis(
        _thesis(),
        [],
        PriceContext(),
        previous_assessment=_previous(),
    )
    assert result.status == AssessmentStatus.no_material_change
    assert result.confirmed_facts == []
    assert result.background_confirmed_facts == [
        "New customer production order was confirmed"
    ]


def test_case_b_real_yield_changes_valuation_not_business_thesis() -> None:
    macro = ThesisMacroImpact(
        ticker="DELTA",
        thesis_version=1,
        assessment_date=date(2051, 1, 3),
        direction="weaken",
        magnitude=3,
        earnings_effect="neutral",
        valuation_effect="weaken",
        rationale="Real yield rose 5bp through discount_rate",
    )
    result = evaluate_thesis(_thesis(), [], PriceContext(), macro_impact=macro)
    assert result.status == AssessmentStatus.no_material_change
    assert result.valuation_context.impact == "compression"
    assert result.earnings_estimate_impact == "unchanged"


def test_supply_context_does_not_change_fundamental_evaluation() -> None:
    accumulating = evaluate_thesis(
        _thesis(),
        [],
        PriceContext(
            supply=InvestorSupplyContext(
                available=True,
                score=90,
                quality="accumulation",
                primary_signal="foreign_institution_joint_accumulation",
            )
        ),
    )
    distributing = evaluate_thesis(
        _thesis(),
        [],
        PriceContext(
            supply=InvestorSupplyContext(
                available=True,
                score=10,
                quality="distribution",
                primary_signal="foreign_exit_retail_absorption",
            )
        ),
    )

    assert accumulating.status == distributing.status
    assert accumulating.earnings_estimate_impact == distributing.earnings_estimate_impact
    assert accumulating.valuation_context == distributing.valuation_context
    assert accumulating.warning_states == distributing.warning_states


def test_unverified_market_article_cannot_trigger_business_invalidation() -> None:
    thesis = _thesis()
    event = _event(
        provider="naver_news",
        event_type="large_order",
        title="Analyst expects memory shortage to continue",
        confirmed_facts=json.dumps(["Search result headline was returned"]),
        relevance_score=50,
        relevance_reason="unverified market commentary",
        requires_review=True,
    )
    thesis.invalidation_signals = json.dumps(["memory demand slowdown"])
    event.raw_summary = "Memory demand slowdown remains a scenario, not a confirmed fact."

    result = evaluate_thesis(thesis, [event], PriceContext())

    assert result.status == AssessmentStatus.no_material_change
    assert result.confirmed_facts == []


def test_case_c_vix_does_not_raise_earnings_estimate() -> None:
    macro = ThesisMacroImpact(
        ticker="DELTA",
        thesis_version=1,
        assessment_date=date(2051, 1, 3),
        direction="strengthen",
        magnitude=4,
        earnings_effect="neutral",
        valuation_effect="strengthen",
        rationale="VIX fell through risk appetite",
        evidence=json.dumps(
            [
                {
                    "factor": "market_volatility",
                    "contribution": 16,
                    "earnings_link_validated": False,
                    "exposure": {"channel": "risk_appetite"},
                }
            ]
        ),
    )
    result = evaluate_thesis(_thesis(), [], PriceContext(), macro_impact=macro)
    assert result.status == AssessmentStatus.no_material_change
    assert result.earnings_estimate_impact != "up"
    assert "Valuation·센티먼트" in _macro_paths(macro)[0]


def test_case_d_invalid_financial_numbers_are_removed_from_confirmed_facts() -> None:
    basis = "(손익계산서; fs_div=CFS; sj_div=IS; thstrm_nm=당기; unit=KRW; period_scope=quarter)"
    event = _event(
        provider="opendart",
        event_type="guidance_change",
        confirmed_facts=json.dumps(
            [
                f"OpenDART financial fact: 매출액 = 100 KRW {basis}",
                f"OpenDART financial fact: 영업이익 = 200 KRW {basis}",
            ]
        ),
        revenue=100,
        operating_income=200,
        operating_margin=20,
    )
    validation = validate_event_financials(event)
    assert validation.valid is False
    assert event.revenue is None
    assert not any("financial fact" in item.lower() for item in json.loads(event.confirmed_facts))
    assert any("단위 또는 기간 검증" in item for item in json.loads(event.unknowns))


def test_financial_unit_normalization_is_explicit() -> None:
    normalized = normalize_financial_number(2.5, "trillion KRW")
    assert normalized is not None
    assert normalized.value == 2_500_000_000_000
    assert normalize_financial_number(10, "ambiguous units") is None


def test_case_e_soft_landing_inflation_warning_is_not_strengthening() -> None:
    init_db()
    with Session(engine) as session:
        regime = MacroRegimeAssessment(
            assessment_date=date(2051, 1, 4),
            growth_momentum=0,
            inflation_pressure=1,
            liquidity_condition=0,
            financial_conditions=0,
            risk_appetite=0,
            earnings_momentum=0,
            regime_label="mixed",
            confidence=0.8,
            persistence_days=3,
            summary="inflation reacceleration warning",
        )
        session.add(regime)
        session.commit()
        theses = update_macro_theses(session, regime)
        soft_landing = next(
            item for item in theses if item.thesis_key == "us_soft_landing_disinflation"
        )
        assert soft_landing.status != "strengthening"


def test_case_f_unknown_metric_is_rendered_as_watch_item() -> None:
    event = _event(
        event_type="other",
        confirmed_facts="[]",
        unknowns=json.dumps(["FCF 감소 여부"]),
    )
    result = evaluate_thesis(_thesis(), [event], PriceContext())
    assert "FCF 감소 여부 확인 필요" in result.watch_items
    assert "FCF 감소" not in result.confirmed_warnings


def test_price_confirmation_changes_action_context_not_business_thesis() -> None:
    thesis = _thesis()
    thesis.price_rules = PriceRulesInput(
        currency="USD",
        confirmation_price=100,
    ).model_dump_json(exclude_none=True)
    context = PriceContext(
        available=True,
        periods={
            "daily": PricePeriodSummary(
                requested_count=500,
                actual_count=500,
                previous_close=99,
                latest_close=101,
                latest_date="2051-01-03",
            )
        },
    )
    result = evaluate_thesis(thesis, [], context)
    assert result.status == AssessmentStatus.no_material_change
    assert context.rule_evaluation is not None
    assert context.rule_evaluation.status == "confirmation_triggered"


def test_non_thesis_noise_cannot_become_invalidation_candidate() -> None:
    event = _event(
        provider="naver_news",
        event_type="non_thesis_noise",
        relevance_score=0,
        title="AI search discussion with overlapping words",
        confirmed_facts=json.dumps(["Unverified article headline"]),
    )
    thesis = _thesis()
    thesis.invalidation_signals = json.dumps(["AI search discussion"])
    result = evaluate_thesis(thesis, [event], PriceContext())
    assert result.status == AssessmentStatus.no_material_change


def test_late_backfill_before_previous_assessment_is_background_not_delta() -> None:
    init_db()
    with Session(engine) as session:
        previous = _previous("no_material_change")
        previous.assessment_date = date(2051, 1, 10)
        session.add(previous)
        session.commit()
        old_event = _event(date=date(2051, 1, 2), url="https://example.com/late-backfill")
        session.add(old_event)
        session.commit()
        assert recent_events_for_assessment(session, "DELTA", date(2051, 1, 11)) == []


def test_opendart_detail_does_not_fallback_to_another_receipt() -> None:
    items = [
        {"rcept_no": "A", "amount": "100"},
        {"rcept_no": "B", "amount": "200"},
    ]
    assert _filter_items_by_receipt(items, "MISSING") == []


def test_mixed_fx_exposure_is_rendered_as_direction_unknown() -> None:
    impact = ThesisMacroImpact(
        ticker="DELTA",
        thesis_version=1,
        assessment_date=date(2051, 1, 3),
        evidence=json.dumps(
            [
                {
                    "factor": "usdkrw",
                    "series_code": "USDKRW",
                    "contribution": 0,
                    "exposure": {"channel": "fx", "direction": "mixed"},
                }
            ]
        ),
    )
    assert "순효과 혼재·방향 판단 보류" in _macro_paths(impact)[0]


def test_macro_thesis_confidence_is_idempotent_within_same_day() -> None:
    init_db()
    with Session(engine) as session:
        regime = MacroRegimeAssessment(
            assessment_date=date(2060, 1, 5),
            growth_momentum=-1,
            inflation_pressure=1,
            liquidity_condition=0,
            financial_conditions=-1,
            risk_appetite=-1,
            earnings_momentum=-1,
            regime_label="mixed",
            confidence=0.8,
            persistence_days=4,
            summary="persistent warning",
        )
        first = update_macro_theses(session, regime)
        first_confidence = {
            item.thesis_key: item.confidence for item in first
        }
        second = update_macro_theses(session, regime)
        assert {item.thesis_key: item.confidence for item in second} == first_confidence
