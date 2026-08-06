from dataclasses import dataclass

from app.config import get_settings
from app.macro.providers.base import MacroProvider
from app.macro.providers.ecos import EcosProvider
from app.macro.providers.eia import EiaProvider
from app.macro.providers.fed import FederalReserveProvider
from app.macro.providers.finnhub import FinnhubEarningsProvider
from app.macro.providers.fred import FredProvider
from app.macro.providers.market import OhlcvMarketProvider


@dataclass(frozen=True)
class MacroProviderStatus:
    name: str
    enabled: bool
    configured: bool
    required_settings: list[str]
    capabilities: list[str]


def macro_providers() -> list[MacroProvider]:
    settings = get_settings()
    if not settings.macro_monitor_enabled:
        return []
    providers: list[MacroProvider] = [FederalReserveProvider()]
    if settings.fred_api_key:
        providers.append(FredProvider())
    if settings.eia_api_key:
        providers.append(EiaProvider())
    if settings.ecos_api_key:
        providers.append(EcosProvider())
    if settings.ohlcv_api_key or settings.action_api_key:
        providers.append(OhlcvMarketProvider())
    if settings.finnhub_api_key:
        providers.append(FinnhubEarningsProvider())
    return providers


def macro_provider_statuses() -> list[MacroProviderStatus]:
    settings = get_settings()
    enabled = settings.macro_monitor_enabled
    return [
        MacroProviderStatus(
            "federal_reserve", enabled, True, [], ["central_bank_events"]
        ),
        MacroProviderStatus(
            "fred", enabled, bool(settings.fred_api_key), ["FRED_API_KEY"], ["macro_series"]
        ),
        MacroProviderStatus(
            "eia", enabled, bool(settings.eia_api_key), ["EIA_API_KEY"], ["energy"]
        ),
        MacroProviderStatus(
            "ecos", enabled, bool(settings.ecos_api_key), ["ECOS_API_KEY"], ["korea_macro"]
        ),
        MacroProviderStatus(
            "ohlcv_analyst",
            enabled,
            bool(settings.ohlcv_api_key or settings.action_api_key),
            ["OHLCV_API_KEY or ACTION_API_KEY"],
            ["us_equities", "etf_daily"],
        ),
        MacroProviderStatus(
            "finnhub_earnings",
            enabled,
            bool(settings.finnhub_api_key),
            ["FINNHUB_API_KEY"],
            ["big_tech_earnings"],
        ),
    ]
