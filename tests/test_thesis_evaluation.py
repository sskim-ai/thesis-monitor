import json
from datetime import date

from app.models.event import Event
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
