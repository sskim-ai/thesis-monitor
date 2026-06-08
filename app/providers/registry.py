from app.providers.base import BaseProvider
from app.providers.filings import OpenDARTProvider, SecEdgarProvider
from app.providers.ir import CompanyIRProvider
from app.providers.mock import MockProvider
from app.providers.news import GoogleNewsRSSProvider, NewsAPIProvider
from app.providers.prices import AlphaVantageProvider


def provider_priority(include_live_news: bool = False) -> list[BaseProvider]:
    """Return the intended provider order without forcing live calls by default."""
    providers: list[BaseProvider] = [MockProvider()]
    if include_live_news:
        providers.extend(
            [
                GoogleNewsRSSProvider(),
                NewsAPIProvider(),
                OpenDARTProvider(),
                SecEdgarProvider(),
                AlphaVantageProvider(),
                CompanyIRProvider(),
            ]
        )
    return providers
