import json
from datetime import date

from app.models.event import Event
from app.models.macro import ThesisMacroImpact
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import AssessmentStatus, PriceContext
from app.services.thesis_evaluation_service import evaluate_thesis


def _thesis() -> InvestmentThesis:
    return InvestmentThesis(
        ticker="TEST",
        version=1,
        core_thesis="A major customer supports recurring demand",
        strengthen_signals="[]",
        weaken_signals="[]",
        invalidation_signals=json.dumps(["major customer terminates all orders"]),
    )


def _event(provider: str) -> Event:
    return Event(
        ticker="TEST",
        date=date.today(),
        source="Company filing",
        provider=provider,
        title="Major customer terminates all orders",
        url="https://example.com/customer-termination",
        event_type="customer_loss",
        confirmed_facts=json.dumps(["Major customer terminated all orders"]),
        inferred_implications="[]",
        unknowns="[]",
        relevance_score=90,
        relevance_reason="customer loss",
        requires_review=True,
    )


def test_trusted_explicit_invalidation_deactivates() -> None:
    result = evaluate_thesis(_thesis(), [_event("sec_edgar")], PriceContext())

    assert result.status == AssessmentStatus.invalidated
    assert result.should_deactivate is True


def test_untrusted_invalidation_requires_review() -> None:
    result = evaluate_thesis(_thesis(), [_event("google_news_rss")], PriceContext())

    assert result.status == AssessmentStatus.invalidation_candidate
    assert result.should_deactivate is False


def test_valuation_signal_is_separate_from_operating_thesis_status() -> None:
    thesis = _thesis()
    thesis.market_expectations = json.dumps(
        {"level": "elevated", "summary": "Strong growth is already expected"}
    )
    thesis.valuation_framework = json.dumps(
        {"primary_method": "forward P/E", "key_inputs": ["normalized EPS"]}
    )
    thesis.multiple_expansion_signals = json.dumps(["new customer production order"])
    event = Event(
        ticker="TEST",
        date=date.today(),
        source="Company filing",
        provider="sec_edgar",
        title="New customer production order confirmed",
        url="https://example.com/new-order",
        event_type="other",
        confirmed_facts=json.dumps(["New customer production order confirmed"]),
        inferred_implications="[]",
        unknowns="[]",
        relevance_score=70,
        relevance_reason="new order",
        requires_review=False,
    )

    result = evaluate_thesis(thesis, [event], PriceContext())

    assert result.status == AssessmentStatus.no_material_change
    assert result.valuation_context.impact == "expansion"
    assert result.valuation_context.market_expectation_level == "elevated"
    assert result.valuation_context.matched_expansion_conditions == [
        "new customer production order"
    ]


def test_macro_can_compress_valuation_without_weakening_business_thesis() -> None:
    thesis = _thesis()
    thesis.market_expectations = json.dumps(
        {"level": "very_high", "summary": "Growth is already highly expected"}
    )
    thesis.valuation_framework = json.dumps({"primary_method": "forward P/E"})
    macro = ThesisMacroImpact(
        ticker="TEST",
        thesis_version=1,
        assessment_date=date.today(),
        direction="neutral",
        magnitude=3,
        valuation_effect="weaken",
        rationale="Higher real yields raise the discount rate",
    )

    result = evaluate_thesis(thesis, [], PriceContext(), macro_impact=macro)

    assert result.status == AssessmentStatus.no_material_change
    assert result.valuation_context.impact == "compression"
    assert result.earnings_estimate_impact == "unknown"
