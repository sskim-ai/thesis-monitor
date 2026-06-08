from app.providers.base import IRProvider, RawEvent


class CompanyIRProvider(IRProvider):
    name = "company_ir"

    async def fetch_company_profile(self, ticker: str):
        return None

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        # TODO: Add per-company IR page discovery and crawling with robots.txt-aware fetching.
        return []
