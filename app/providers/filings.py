from app.config import get_settings
from app.providers.base import FilingProvider, RawEvent


class OpenDARTProvider(FilingProvider):
    name = "opendart"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.opendart_api_key:
            return []
        # TODO: Map Korean ticker codes to DART corp_code before calling list.json.
        # The corp_code zip file should be downloaded and cached by a future job.
        return []


class SecEdgarProvider(FilingProvider):
    name = "sec_edgar"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        settings = get_settings()
        if not settings.sec_user_agent:
            return []
        # TODO: Resolve ticker to CIK, call SEC submissions JSON, and map recent filings to RawEvent.
        return []
