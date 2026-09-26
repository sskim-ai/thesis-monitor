from datetime import date
from email.utils import parsedate_to_datetime
import html
import re
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

from app.config import get_settings
from app.providers.base import NewsProvider, RawEvent


TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = TAG_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_title(value: str) -> str:
    cleaned = clean_text(value).lower()
    cleaned = re.sub(r"\s+-\s+[^-]+$", "", cleaned)
    return re.sub(r"[^a-z0-9가-힣]+", " ", cleaned).strip()


def _parse_rss_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, IndexError):
        return date.today()


class GoogleNewsRSSProvider(NewsProvider):
    name = "google_news_rss"

    def __init__(self, timeout_seconds: float = 5.0, max_items: int = 10, *, transport=None, as_of=None) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_items = max_items
        self.transport, self.as_of = transport, as_of

    async def fetch_events(
        self,
        ticker: str,
        lookback_days: int,
        *,
        search_aliases: list[str] | None = None,
    ) -> list[RawEvent]:
        url = self.request_url(ticker, lookback_days, search_aliases=search_aliases)
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=self.as_of is None,
                                     transport=self.transport) as client:
            response = await client.get(url)
            response.raise_for_status()
        return self.parse_response(response, ticker=ticker)

    @staticmethod
    def request_url(ticker, lookback_days, *, search_aliases=None):
        terms = search_aliases or [ticker]
        query_text = " OR ".join(f'"{term}"' for term in terms[:4])
        query = quote_plus(f"({query_text}) company stock")
        return (
            "https://news.google.com/rss/search"
            f"?q={query}+when:{lookback_days}d&hl=en-US&gl=US&ceid=US:en"
        )
    def parse_response(self, response, *, ticker):
        url = str(response.url)
        seen: set[tuple[str, str]] = set()
        try:
            root = ElementTree.fromstring(response.text)
        except ElementTree.ParseError:
            return []

        events: list[RawEvent] = []
        for item in root.findall(".//item"):
            if len(events) >= self.max_items:
                break
            title = clean_text(item.findtext("title")) or "Untitled news item"
            link = item.findtext("link") or url
            dedupe_key = (link, normalize_title(title))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            published = _parse_rss_date(item.findtext("pubDate"))
            if self.as_of is not None:
                try:
                    published = parsedate_to_datetime(item.findtext("pubDate")).date()
                except (TypeError, ValueError, IndexError):
                    continue
            source_node = item.find("source")
            source = source_node.text if source_node is not None and source_node.text else "Google News RSS"
            summary = clean_text(item.findtext("description")) or title
            events.append(
                RawEvent(
                    ticker=ticker.upper(),
                    company_name=None,
                    date=published,
                    source=source,
                    provider=self.name,
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

    async def fetch_events(
        self,
        ticker: str,
        lookback_days: int,
        *,
        search_aliases: list[str] | None = None,
    ) -> list[RawEvent]:
        settings = get_settings()
        if not settings.newsapi_api_key:
            return []
        # TODO: Implement /v2/everything mapping to RawEvent when NEWSAPI_API_KEY is configured.
        return []


class NaverNewsProvider(NewsProvider):
    name = "naver_news"
    endpoint = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self, timeout_seconds: float = 5.0, display: int = 10, *, transport=None, as_of=None) -> None:
        self.timeout_seconds = timeout_seconds
        self.display = min(max(display, 1), 100)
        self.transport, self.as_of = transport, as_of

    async def fetch_events(
        self,
        ticker: str,
        lookback_days: int,
        *,
        search_aliases: list[str] | None = None,
    ) -> list[RawEvent]:
        settings = get_settings()
        if not settings.naver_client_id or not settings.naver_client_secret:
            return []

        params = self.request_params(ticker, search_aliases=search_aliases)
        headers = {
            "X-Naver-Client-Id": settings.naver_client_id,
            "X-Naver-Client-Secret": settings.naver_client_secret,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
            response = await client.get(self.endpoint, params=params, headers=headers)
            response.raise_for_status()
        return self.parse_response(response, ticker=ticker)

    def request_params(self, ticker, *, search_aliases=None):
        terms = search_aliases or [ticker]
        query = " OR ".join(f'"{term}"' for term in terms[:4])
        return {"query": query, "display": self.display, "start": 1, "sort": "date"}

    def parse_response(self, response, *, ticker):
        payload = response.json()
        events: list[RawEvent] = []
        seen: set[tuple[str, str]] = set()
        for item in payload.get("items", []):
            if self.as_of is not None:
                try:
                    parsedate_to_datetime(item.get("pubDate"))
                except (TypeError, ValueError, IndexError):
                    continue
            title = clean_text(item.get("title")) or "Untitled Naver news item"
            link = item.get("originallink") or item.get("link") or self.endpoint
            dedupe_key = (link, normalize_title(title))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            summary = clean_text(item.get("description")) or title
            events.append(
                RawEvent(
                    ticker=ticker.upper(),
                    company_name=None,
                    date=_parse_rss_date(item.get("pubDate")),
                    source="Naver News",
                    provider=self.name,
                    title=title,
                    url=link,
                    summary=summary,
                    keywords=[ticker.upper(), "naver_news"],
                    confirmed_facts=[
                        "Naver News search returned the linked source item",
                        "The item contains a published news headline",
                    ],
                    inferred_implications=[],
                    unknowns=[
                        "Customer names are not confirmed unless disclosed in the source text",
                        "Order size is unknown",
                        "Revenue impact is unknown",
                        "Margin impact is unknown",
                        "FCF impact is unknown",
                    ],
                )
            )
        return events
