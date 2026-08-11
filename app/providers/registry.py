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
    markets: list[str]
    asset_types: list[str]
    supported_data: list[str]
    freshness_expectation: str
    historical_depth_years: int | None = None
    forward_data_available: bool = False


def _status(
    *,
    name: str,
    enabled: bool,
    configured: bool,
    required_settings: list[str],
    mode: str,
    markets: list[str],
    supported_data: list[str],
    freshness: str,
    depth: int | None = None,
    forward: bool = False,
) -> ProviderStatus:
    return ProviderStatus(
        name=name,
        enabled=enabled,
        configured=configured,
        required_settings=required_settings,
        mode=mode,
        markets=markets,
        asset_types=["equity"],
        supported_data=supported_data,
        freshness_expectation=freshness,
        historical_depth_years=depth,
        forward_data_available=forward,
    )


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
        _status(
            name="mock",
            enabled=settings.include_mock_provider,
            configured=True,
            required_settings=[],
            mode="mock",
            markets=["KR", "US"], supported_data=["events", "company_profile"], freshness="fixture",
        ),
        _status(
            name="google_news_rss",
            enabled=live_enabled,
            configured=True,
            required_settings=[],
            mode="live",
            markets=["KR", "US"], supported_data=["news"], freshness="intraday",
        ),
        _status(
            name="naver_news",
            enabled=live_enabled,
            configured=bool(settings.naver_client_id and settings.naver_client_secret),
            required_settings=["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"],
            mode="live",
            markets=["KR"], supported_data=["news"], freshness="intraday",
        ),
        _status(
            name="newsapi",
            enabled=live_enabled,
            configured=bool(settings.newsapi_api_key),
            required_settings=["NEWSAPI_API_KEY"],
            mode="live_skeleton",
            markets=["US"], supported_data=["news"], freshness="intraday",
        ),
        _status(
            name="opendart",
            enabled=live_enabled,
            configured=bool(settings.opendart_api_key),
            required_settings=["OPENDART_API_KEY"],
            mode="live_seed_mapping",
            markets=["KR"], supported_data=["financial_statements", "dividend_events", "capital_actions", "share_count"], freshness="filing_time", depth=5,
        ),
        _status(
            name="sec_edgar",
            enabled=live_enabled,
            configured=bool(settings.sec_user_agent),
            required_settings=["SEC_USER_AGENT"],
            mode="live_seed_mapping",
            markets=["US", "foreign_issuer"], supported_data=["financial_statements", "shares", "equity", "income", "filings"], freshness="filing_time", depth=5,
        ),
        _status(
            name="alpha_vantage",
            enabled=live_enabled,
            configured=bool(settings.alpha_vantage_api_key),
            required_settings=["ALPHA_VANTAGE_API_KEY"],
            mode="skeleton",
            markets=["US"], supported_data=["price", "multiples"], freshness="daily", forward=True,
        ),
        _status(
            name="company_ir",
            enabled=live_enabled,
            configured=False,
            required_settings=[],
            mode="skeleton",
            markets=["KR", "US", "foreign_issuer"], supported_data=["earnings", "guidance", "dividend_policy"], freshness="event_time",
        ),
        _status(
            name="ohlcv_analyst",
            enabled=True,
            configured=bool(settings.ohlcv_base_url),
            required_settings=["OHLCV_BASE_URL"],
            mode="local_service",
            markets=["KR", "US"],
            supported_data=["price", "price_history", "technical_reference"],
            freshness="market_session",
            depth=5,
        ),
        _status(
            name="finnhub",
            enabled=live_enabled,
            configured=bool(settings.finnhub_api_key),
            required_settings=["FINNHUB_API_KEY"],
            mode="live",
            markets=["US"],
            supported_data=["multiples", "forward_estimates"],
            freshness="daily",
            forward=True,
        ),
    ]
