from app.config import get_settings
from app.providers.base import PriceProvider, RawEvent


class AlphaVantageProvider(PriceProvider):
    name = "alpha_vantage"

    async def fetch_company_profile(self, ticker: str):
        return None

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.alpha_vantage_api_key:
            return []
        # TODO: Map earnings, overview, and price signals to RawEvent/FinancialSnapshot.
        return []

    async def fetch_earnings(self, ticker: str):
        return None
