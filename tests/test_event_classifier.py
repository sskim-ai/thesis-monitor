from datetime import date

from app.providers.base import RawEvent
from app.services.event_classifier import classify_event
from app.services.thesis_scoring import score_event


def test_production_order_classification_and_review_score() -> None:
    raw_event = RawEvent(
        ticker="NVDA",
        company_name="NVIDIA",
        date=date(2026, 6, 8),
        source="Company IR",
        provider="test",
        title="Production order with named customer",
        url="https://example.com",
        summary="Customer name was disclosed and production order starts in Q3.",
        keywords=["production order", "customer disclosed"],
    )

    event_type = classify_event(raw_event)
    relevance = score_event(raw_event, event_type)

    assert event_type == "production_order"
    assert relevance.relevance_score >= 40
    assert relevance.requires_review is True


def test_noise_classification_low_score() -> None:
    raw_event = RawEvent(
        ticker="NVDA",
        company_name="NVIDIA",
        date=date(2026, 6, 8),
        source="Financial Media",
        provider="test",
        title="Analyst raises price target after conference",
        url="https://example.com",
        summary="No new operating data was reported.",
        keywords=["price target", "conference"],
    )

    event_type = classify_event(raw_event)
    relevance = score_event(raw_event, event_type)

    assert event_type == "non_thesis_noise"
    assert relevance.relevance_score == 0
    assert relevance.requires_review is False
