import asyncio
from datetime import date

import pytest
from sqlmodel import Session

from app.config import get_settings
from app.database import engine, init_db
from app.providers.base import BaseProvider, RawEvent
from app.providers.filings import OpenDARTProvider, SecEdgarProvider
from app.providers.mock import MockProvider
from app.providers.naver_news import NaverNewsProvider
from app.providers.news import GoogleNewsRSSProvider, NewsAPIProvider
from app.providers.registry import provider_priority
from app.services.collection_service import CollectionService


def test_keyless_providers_fail_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENDART_API_KEY", "")
    monkeypatch.setenv("NEWSAPI_API_KEY", "")
    monkeypatch.setenv("SEC_USER_AGENT", "")
    get_settings.cache_clear()

    async def run() -> None:
        assert await OpenDARTProvider().fetch_events("000660.KS", 30) == []
        assert await NewsAPIProvider().fetch_events("NVDA", 30) == []
        assert await SecEdgarProvider().fetch_events("NVDA", 30) == []

    asyncio.run(run())


def test_mock_provider_fact_implication_unknown_separation() -> None:
    events = asyncio.run(MockProvider().fetch_events("NVDA", 30))

    assert events
    event = events[0]
    assert event.confirmed_facts
    assert event.inferred_implications
    assert event.unknowns
    assert not any("revenue contribution" in fact.lower() for fact in event.confirmed_facts)
    assert any("revenue contribution" in item.lower() for item in event.inferred_implications)


def test_google_news_rss_provider_returns_raw_event_list(monkeypatch: pytest.MonkeyPatch) -> None:
    rss = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss><channel><item>
      <title>NVDA announces product update</title>
      <link>https://example.com/news</link>
      <pubDate>Mon, 08 Jun 2026 12:00:00 GMT</pubDate>
      <source>Example News</source>
      <description>Headline summary only.</description>
    </item></channel></rss>
    """

    class FakeResponse:
        text = rss

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr("app.providers.news.httpx.AsyncClient", FakeClient)

    events = asyncio.run(GoogleNewsRSSProvider().fetch_events("NVDA", 30))

    assert len(events) == 1
    assert events[0].ticker == "NVDA"
    assert events[0].source == "Example News"
    assert events[0].confirmed_facts
    assert events[0].unknowns


def test_enable_live_provider_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_LIVE_PROVIDERS", "false")
    get_settings.cache_clear()
    assert [provider.name for provider in provider_priority(False)] == ["mock"]

    monkeypatch.setenv("ENABLE_LIVE_PROVIDERS", "true")
    get_settings.cache_clear()
    assert [provider.name for provider in provider_priority(True)] == [
        "mock",
        "google_news_rss",
        "naver_news",
        "newsapi",
        "opendart",
        "sec_edgar",
        "alpha_vantage",
        "company_ir",
    ]


def test_naver_provider_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAVER_CLIENT_ID", "client-id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "client-secret")
    get_settings.cache_clear()

    payload = {
        "items": [
            {
                "title": "<b>NVDA</b> supply update",
                "originallink": "https://example.com/naver",
                "description": "<b>NVDA</b> headline summary",
                "pubDate": "Mon, 08 Jun 2026 12:00:00 +0900",
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback) -> None:
            return None

        async def get(self, url: str, params: dict, headers: dict) -> FakeResponse:
            assert headers["X-Naver-Client-Id"] == "client-id"
            assert params["sort"] == "date"
            return FakeResponse()

    monkeypatch.setattr("app.providers.news.httpx.AsyncClient", FakeClient)

    events = asyncio.run(NaverNewsProvider().fetch_events("NVDA", 30))

    assert len(events) == 1
    assert events[0].provider == "naver_news"
    assert events[0].source == "Naver News"
    assert events[0].title == "NVDA supply update"
    assert events[0].confirmed_facts
    assert events[0].unknowns


class FailingProvider(BaseProvider):
    name = "failing"

    async def fetch_company_profile(self, ticker: str):
        return None

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        raise RuntimeError("boom")

    async def fetch_earnings(self, ticker: str):
        return None


class DuplicateProvider(BaseProvider):
    name = "duplicate"

    async def fetch_company_profile(self, ticker: str):
        return None

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        event = RawEvent(
            ticker=ticker,
            company_name="Duplicate Co",
            date=date(2026, 6, 8),
            source="Unit Test",
            provider=self.name,
            title="Duplicate production order",
            url="https://example.com/duplicate",
            summary="A production order was disclosed.",
            keywords=["production order"],
            confirmed_facts=["Production order was disclosed"],
            inferred_implications=[],
            unknowns=["Order size is unknown"],
        )
        return [event, event]

    async def fetch_earnings(self, ticker: str):
        return None


def test_provider_failure_fallback_and_duplicate_removal() -> None:
    init_db()
    service = CollectionService()
    service.providers = [FailingProvider(), DuplicateProvider()]

    with Session(engine) as session:
        events = asyncio.run(service.collect_events(session, "UNITTEST", 30))
        providers = [event.provider for event in events]

    assert len(events) <= 1
    if providers:
        assert providers[0] == "duplicate"
