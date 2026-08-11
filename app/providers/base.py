from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from app.schemas.company import CompanyProfile
from app.schemas.financial import EarningsCheckpointResponse


class ProviderNotConfigured(RuntimeError):
    """Raised when an external provider is called without required configuration."""


@dataclass
class RawEvent:
    ticker: str
    company_name: str | None
    date: date
    source: str
    title: str
    url: str
    summary: str
    provider: str
    keywords: list[str] = field(default_factory=list)
    confirmed_facts: list[str] = field(default_factory=list)
    inferred_implications: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    source_document_id: str | None = None
    document_identity_status: str = "unvalidated"
    claim_actor: str | None = None
    claim_actor_type: str = "unknown"
    raw_financial_fields: list[dict[str, object]] = field(default_factory=list)
    reporting_period_end: date | None = None
    document_type: str | None = None
    financial_scope: str | None = None
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    operating_margin: float | None = None
    yoy_growth: float | None = None
    qoq_growth: float | None = None
    capex_amount: float | None = None
    financing_amount: float | None = None
    dilution_amount: float | None = None
    margin_guidance_changed: bool = False
    revenue_guidance_changed: bool = False
    earnings_guidance_changed: bool = False
    cash_flow_guidance_changed: bool = False
    major_order_change: bool = False
    production_delay: bool = False
    fcf_impact_known: bool = False
    guidance_changed: bool = False
    material_customer_change: bool = False
    dilution_risk: bool = False
    debt_liquidity_risk: bool = False
    accounting_issue: bool = False
    regulatory_material: bool = False
    financial_report_filed: bool = False
    operating_cash_flow_impact_known: bool = False
    buyback_candidate: bool = False
    confirmed_buyback: bool = False
    subject_company_name: str | None = None
    subject_ticker: str | None = None
    identity_validated: bool = False
    identity_status: str = "unvalidated"
    relevance_evidence: list[str] = field(default_factory=list)
    rejected_reason: str | None = None


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        raise NotImplementedError


class NewsProvider(BaseProvider):
    @abstractmethod
    async def fetch_events(
        self,
        ticker: str,
        lookback_days: int,
        *,
        search_aliases: list[str] | None = None,
    ) -> list[RawEvent]:
        raise NotImplementedError

    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        raise NotImplementedError

    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        raise NotImplementedError


class FilingProvider(BaseProvider):
    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        raise NotImplementedError

    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        raise NotImplementedError


class EarningsProvider(BaseProvider):
    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        raise NotImplementedError


class IRProvider(BaseProvider):
    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        raise NotImplementedError


class PriceProvider(BaseProvider):
    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        raise NotImplementedError

    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        raise NotImplementedError

    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        raise NotImplementedError


class CompetitorProvider(BaseProvider):
    async def fetch_company_profile(self, ticker: str) -> CompanyProfile | None:
        raise NotImplementedError

    async def fetch_earnings(self, ticker: str) -> EarningsCheckpointResponse | None:
        raise NotImplementedError
