from dataclasses import dataclass

from app.config import get_settings
from app.providers.base import BaseProvider
from app.providers.filings import OpenDARTProvider, SecEdgarProvider
from app.providers.ir import CompanyIRProvider
from app.providers.mock import MockProvider
from app.providers.naver_news import NaverNewsProvider
from app.providers.news import GoogleNewsRSSProvider, NewsAPIProvider
from app.providers.prices import AlphaVantageProvider


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    enabled: bool
    configured: bool
    required_settings: list[str]
    mode: str


def provider_priority(
    include_live_news: bool = False,
    include_mock_provider: bool = True,
) -> list[BaseProvider]:
    """Return providers in execution order."""
    settings = get_settings()
    providers: list[BaseProvider] = []
    if include_mock_provider:
        providers.append(MockProvider())
    if include_live_news:
        providers.extend(
            [
                GoogleNewsRSSProvider(
                    timeout_seconds=settings.live_provider_timeout_seconds,
                    max_items=settings.google_news_display,
                ),
                NaverNewsProvider(
                    timeout_seconds=settings.live_provider_timeout_seconds,
                    display=settings.naver_news_display,
                ),
                NewsAPIProvider(),
                OpenDARTProvider(),
                SecEdgarProvider(),
                AlphaVantageProvider(),
                CompanyIRProvider(),
            ]
        )
    return providers


def provider_statuses() -> list[ProviderStatus]:
    settings = get_settings()
    live_enabled = settings.enable_live_providers
    return [
        ProviderStatus(
            name="mock",
            enabled=settings.include_mock_provider,
            configured=True,
            required_settings=[],
            mode="mock",
        ),
        ProviderStatus(
            name="google_news_rss",
            enabled=live_enabled,
            configured=True,
            required_settings=[],
            mode="live",
        ),
        ProviderStatus(
            name="naver_news",
            enabled=live_enabled,
            configured=bool(settings.naver_client_id and settings.naver_client_secret),
            required_settings=["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"],
            mode="live",
        ),
        ProviderStatus(
            name="newsapi",
            enabled=live_enabled,
            configured=bool(settings.newsapi_api_key),
            required_settings=["NEWSAPI_API_KEY"],
            mode="live_skeleton",
        ),
        ProviderStatus(
            name="opendart",
            enabled=live_enabled,
            configured=bool(settings.opendart_api_key),
            required_settings=["OPENDART_API_KEY"],
            mode="live_seed_mapping",
        ),
        ProviderStatus(
            name="sec_edgar",
            enabled=live_enabled,
            configured=bool(settings.sec_user_agent),
            required_settings=["SEC_USER_AGENT"],
            mode="live_seed_mapping",
        ),
        ProviderStatus(
            name="alpha_vantage",
            enabled=live_enabled,
            configured=bool(settings.alpha_vantage_api_key),
            required_settings=["ALPHA_VANTAGE_API_KEY"],
            mode="skeleton",
        ),
        ProviderStatus(
            name="company_ir",
            enabled=live_enabled,
            configured=False,
            required_settings=[],
            mode="skeleton",
        ),
    ]
