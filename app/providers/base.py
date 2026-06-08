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
