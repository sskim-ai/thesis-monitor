from datetime import date
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

from app.config import get_settings
from app.providers.base import NewsProvider, RawEvent


def _parse_rss_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, IndexError):
        return date.today()


class GoogleNewsRSSProvider(NewsProvider):
    name = "google_news_rss"

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        query = quote_plus(f"{ticker} stock company news")
        url = (
            "https://news.google.com/rss/search"
            f"?q={query}+when:{lookback_days}d&hl=en-US&gl=US&ceid=US:en"
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError:
            return []

        root = ElementTree.fromstring(response.text)
        events: list[RawEvent] = []
        for item in root.findall(".//item"):
            title = item.findtext("title") or "Untitled news item"
            link = item.findtext("link") or url
            published = _parse_rss_date(item.findtext("pubDate"))
            source_node = item.find("source")
            source = source_node.text if source_node is not None and source_node.text else "Google News RSS"
            summary = item.findtext("description") or title
            events.append(
                RawEvent(
                    ticker=ticker.upper(),
                    company_name=None,
                    date=published,
                    source=source,
                    title=title,
                    url=link,
                    summary=summary,
                    keywords=[ticker.upper(), "news"],
                    confirmed_facts=[
                        f"News headline published by {source}",
                        "Google News RSS returned the linked source item",
                    ],
                    inferred_implications=[],
                    unknowns=[
                        "Customer names are not confirmed unless disclosed in the source text",
                        "Order size is unknown",
                        "Revenue impact is unknown",
                        "Margin impact is unknown",
                    ],
                )
            )
        return events


class NewsAPIProvider(NewsProvider):
    name = "newsapi"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.newsapi_api_key:
            return []
        # TODO: Implement /v2/everything mapping to RawEvent when NEWSAPI_API_KEY is configured.
        return []
