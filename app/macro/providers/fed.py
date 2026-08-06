from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedEvent, MacroProviderResult


class FederalReserveProvider:
    name = "federal_reserve"
    feed_url = "https://www.federalreserve.gov/feeds/press_monetary.xml"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.macro_provider_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(self.feed_url)
                response.raise_for_status()
            root = ElementTree.fromstring(response.text)
            cutoff = as_of.astimezone(timezone.utc) - timedelta(days=7)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                published_text = (item.findtext("pubDate") or "").strip()
                if not title or not link or not published_text:
                    continue
                published = parsedate_to_datetime(published_text).astimezone(timezone.utc)
                if published < cutoff:
                    continue
                result.events.append(
                    CollectedEvent(
                        event_key=f"fed:{link.rsplit('/', 1)[-1]}",
                        event_type="central_bank",
                        category="monetary_policy",
                        title=title,
                        country="US",
                        region="US",
                        released_at=published,
                        source_url=link,
                        impact_level=4 if "FOMC" in title.upper() else 2,
                        confirmed_facts=[title],
                        source_reliability=1.0,
                    )
                )
        except (httpx.HTTPError, ElementTree.ParseError, TypeError, ValueError) as exc:
            result.warnings.append(f"monetary feed: {type(exc).__name__}")
        return result
