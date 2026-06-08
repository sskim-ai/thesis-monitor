from datetime import date

from app.providers.base import EarningsProvider, FilingProvider, IRProvider, NewsProvider, RawEvent


class MockNewsProvider(NewsProvider):
    name = "mock_news"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        return [
            RawEvent(
                ticker=ticker,
                company_name="NVIDIA" if ticker.upper() == "NVDA" else None,
                date=date(2026, 6, 8),
                source="Company IR",
                title="Example production order with named hyperscale customer",
                url="https://example.com/production-order",
                summary="Company disclosed a production order scheduled to start in Q3.",
                keywords=["production order", "customer disclosed", "Q3"],
                confirmed_facts=[
                    "Customer name was disclosed",
                    "Production schedule starts in Q3",
                ],
                inferred_implications=[
                    "Potential revenue contribution, but margin impact is not yet confirmed",
                ],
                unknowns=["Order size and margin profile were not disclosed"],
            ),
            RawEvent(
                ticker=ticker,
                company_name="NVIDIA" if ticker.upper() == "NVDA" else None,
                date=date(2026, 6, 5),
                source="Financial Media",
                title="Analyst raises price target after conference presentation",
                url="https://example.com/price-target",
                summary="Analyst commentary changed target price without new confirmed operating data.",
                keywords=["price target", "conference"],
                confirmed_facts=["Analyst changed price target"],
                inferred_implications=[],
                unknowns=["No new customer, guidance, or order details were reported"],
            ),
        ]


class MockFilingProvider(FilingProvider):
    name = "mock_filings"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        return []


class MockEarningsProvider(EarningsProvider):
    name = "mock_earnings"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        return []


class MockIRProvider(IRProvider):
    name = "mock_ir"

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        return []

