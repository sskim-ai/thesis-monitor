from datetime import date

from app.providers.base import RawEvent
from app.services.event_classifier import classify_event
from app.services.event_interpreter import enrich_raw_event
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


def _opendart_event(title: str) -> RawEvent:
    return RawEvent(
        ticker="000660",
        company_name="SK하이닉스",
        date=date(2026, 8, 10),
        source="OpenDART",
        provider="opendart",
        title=title,
        url="https://dart.fss.or.kr/example",
        summary=f"OpenDART filing title: {title}",
        keywords=["opendart", "filing"],
        confirmed_facts=[f"OpenDART filing title: {title}"],
    )


def test_facility_investment_is_reviewable() -> None:
    raw_event = enrich_raw_event(_opendart_event("신규시설투자등"))
    event_type = classify_event(raw_event)
    relevance = score_event(raw_event, event_type)

    assert event_type == "facility_investment"
    assert relevance.requires_review is True
    assert any("Investment amount" in item for item in raw_event.unknowns)


def test_disclosure_inquiry_does_not_confirm_rumor() -> None:
    raw_event = enrich_raw_event(_opendart_event("조회공시요구(풍문또는보도)"))
    event_type = classify_event(raw_event)
    relevance = score_event(raw_event, event_type)

    assert event_type == "disclosure_inquiry"
    assert relevance.requires_review is True
    assert any("not that the underlying rumor is true" in item for item in raw_event.inferred_implications)


def test_unconfirmed_disclosure_response_preserves_uncertainty() -> None:
    raw_event = enrich_raw_event(
        _opendart_event("조회공시요구(풍문또는보도)에대한답변(미확정)")
    )
    event_type = classify_event(raw_event)
    relevance = score_event(raw_event, event_type)

    assert event_type == "disclosure_clarification"
    assert relevance.requires_review is True
    assert any("remains unconfirmed" in item for item in raw_event.inferred_implications)
    assert any("follow-up disclosure" in item for item in raw_event.unknowns)


def test_rumor_clarification_is_reviewable() -> None:
    raw_event = enrich_raw_event(_opendart_event("풍문또는보도에대한해명(미확정)"))

    assert classify_event(raw_event) == "disclosure_clarification"
