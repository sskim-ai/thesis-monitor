import asyncio

import pytest

from app.config import get_settings
from app.providers.filings import OpenDARTProvider, SecEdgarProvider
from app.providers.mock import MockProvider
from app.providers.news import GoogleNewsRSSProvider, NewsAPIProvider


def test_keyless_providers_fail_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENDART_API_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
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
