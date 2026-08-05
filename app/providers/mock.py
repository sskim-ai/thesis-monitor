from datetime import date, timedelta

from app.providers.base import BaseProvider, RawEvent
from app.schemas.company import CompanyProfile
from app.schemas.financial import EarningsCheckpointResponse


class MockProvider(BaseProvider):
    name = "mock"

    _profiles = {
        "NVDA": CompanyProfile(
            ticker="NVDA",
            company_name="NVIDIA",
            exchange="NASDAQ",
            sector="Technology",
            industry="Semiconductors",
            business_units=["Data Center", "Gaming", "Professional Visualization", "Automotive"],
            major_revenue_sources=["Data center GPUs", "Networking", "Gaming GPUs"],
            major_customers=["Hyperscale cloud providers", "Enterprise AI customers"],
            ir_url="https://investor.nvidia.com/",
            filings_url="https://www.sec.gov/edgar/browse/?CIK=1045810",
        ),
        "AMD": CompanyProfile(
            ticker="AMD",
            company_name="Advanced Micro Devices",
            exchange="NASDAQ",
            sector="Technology",
            industry="Semiconductors",
            business_units=["Data Center", "Client", "Gaming", "Embedded"],
            major_revenue_sources=["Server CPUs", "AI accelerators", "Client processors"],
            major_customers=["Cloud providers", "PC OEMs", "Embedded customers"],
            ir_url="https://ir.amd.com/",
            filings_url="https://www.sec.gov/edgar/browse/?CIK=2488",
        ),
        "000660.KS": CompanyProfile(
            ticker="000660.KS",
            company_name="SK hynix",
            exchange="KRX",
            sector="Technology",
            industry="Memory Semiconductors",
            business_units=["DRAM", "NAND", "HBM"],
            major_revenue_sources=["Memory chips", "HBM", "Enterprise SSD"],
            major_customers=["AI accelerator vendors", "Cloud providers", "Device OEMs"],
            ir_url="https://www.skhynix.com/ir",
            filings_url="https://dart.fss.or.kr/",
        ),
    }

    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        return self._profiles.get(ticker.upper())

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        ticker = ticker.upper()
        today = date.today()
        company_name = self._profiles.get(ticker).company_name if ticker in self._profiles else ticker
        events = {
            "NVDA": [
                RawEvent(
                    ticker=ticker,
                    company_name=company_name,
                    date=today,
                    source="Company IR",
                    provider=self.name,
                    title="Example production order with named hyperscale customer",
                    url="https://example.com/nvda-production-order",
                    summary="Company disclosed a production order scheduled to start in Q3.",
                    keywords=["production order", "customer name was disclosed", "Q3"],
                    confirmed_facts=[
                        "Customer name was disclosed",
                        "Production schedule starts in Q3",
                    ],
                    inferred_implications=[
                        "Potential revenue contribution, but margin impact is not confirmed",
                    ],
                    unknowns=["Order size", "Gross margin impact"],
                ),
                RawEvent(
                    ticker=ticker,
                    company_name=company_name,
                    date=today - timedelta(days=3),
                    source="Financial Media",
                    provider=self.name,
                    title="Analyst raises price target after conference presentation",
                    url="https://example.com/nvda-price-target",
                    summary="Analyst commentary changed target price without new confirmed operating data.",
                    keywords=["price target", "conference"],
                    confirmed_facts=["Analyst changed price target"],
                    unknowns=["No new customer, guidance, or order details were reported"],
                ),
            ],
            "AMD": [
                RawEvent(
                    ticker=ticker,
                    company_name=company_name,
                    date=today - timedelta(days=1),
                    source="Mock News",
                    provider=self.name,
                    title="AMD announces new customer for AI accelerator program",
                    url="https://example.com/amd-new-customer",
                    summary="A new customer was disclosed, but production volume was not provided.",
                    keywords=["new customer", "customer name was disclosed"],
                    confirmed_facts=["New customer was disclosed"],
                    inferred_implications=["Customer traction may support AI accelerator demand thesis"],
                    unknowns=["Production order size", "Revenue timing"],
                )
            ],
            "000660.KS": [
                RawEvent(
                    ticker=ticker,
                    company_name=company_name,
                    date=today - timedelta(days=2),
                    source="Mock Filing",
                    provider=self.name,
                    title="SK hynix notes inventory normalization in memory business",
                    url="https://example.com/skhynix-inventory",
                    summary="Management described inventory normalization in the memory segment.",
                    keywords=["inventory normalization", "memory"],
                    confirmed_facts=["Management described inventory normalization"],
                    inferred_implications=["Inventory normalization may reduce pricing pressure"],
                    unknowns=["Customer-level HBM demand", "Quarterly margin impact"],
                )
            ],
        }
        return events.get(ticker, [])

    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        ticker = ticker.upper()
        if ticker not in self._profiles:
            return None
        return EarningsCheckpointResponse(
            ticker=ticker,
            checkpoints=[
                "Revenue growth vs guidance",
                "Gross margin and operating margin",
                "FCF after capex",
                "Inventory and receivables trend",
                "Customer concentration and demand signals",
            ],
        )


MockNewsProvider = MockProvider
MockFilingProvider = MockProvider
MockEarningsProvider = MockProvider
MockIRProvider = MockProvider
