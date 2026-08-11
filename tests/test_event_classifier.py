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


def test_material_flag_takes_priority_over_noise_keyword() -> None:
    raw_event = RawEvent(
        ticker="TSLA",
        company_name="Tesla",
        date=date(2026, 8, 10),
        source="Company IR",
        provider="company_ir",
        title="Tesla conference update",
        url="https://example.com/tesla-margin",
        summary="The company changed margin guidance.",
        margin_guidance_changed=True,
    )

    assert classify_event(raw_event) == "margin_guidance_change"


def test_unrelated_news_is_not_promoted_by_material_keyword() -> None:
    raw_event = RawEvent(
        ticker="IBM",
        company_name="IBM",
        date=date(2026, 8, 10),
        source="Financial Media",
        provider="news_api",
        title="Another company reports an earnings beat",
        url="https://example.com/unrelated",
        summary="No target-company reference appears in the article metadata.",
    )

    assert classify_event(raw_event) == "non_thesis_noise"


def test_berkshire_article_is_rejected_for_googl_even_with_query_keyword() -> None:
    raw_event = RawEvent(
        ticker="GOOGL",
        company_name="Alphabet A",
        date=date(2026, 8, 11),
        source="Financial Media",
        provider="google_news_rss",
        title="Berkshire reaches a new high after leadership transition",
        url="https://example.com/berkshire",
        summary="The article discusses Berkshire Hathaway and Abel.",
        keywords=["GOOGL", "news"],
    )

    assert classify_event(raw_event) == "non_thesis_noise"


def test_financial_metrics_are_structured_without_inventing_growth() -> None:
    raw_event = _opendart_event("영업(잠정)실적")
    raw_event.confirmed_facts.extend(
        [
            "OpenDART financial fact: 매출액 = 1,000,000 KRW",
            "OpenDART financial fact: 영업이익 = 100,000 KRW",
            "OpenDART financial fact: 당기순이익 = 70,000 KRW",
            "OpenDART facility investment fact: amount = 300,000 KRW",
            "OpenDART capital raise fact: amount = 500,000 KRW",
            "OpenDART capital raise fact: new_shares = 12,000 shares",
        ]
    )

    enriched = enrich_raw_event(raw_event)

    assert enriched.revenue == 1_000_000
    assert enriched.operating_income == 100_000
    assert enriched.net_income == 70_000
    assert enriched.operating_margin == 10
    assert enriched.capex_amount == 300_000
    assert enriched.financing_amount == 500_000
    assert enriched.dilution_amount == 12_000
    assert enriched.yoy_growth is None
    assert enriched.qoq_growth is None
