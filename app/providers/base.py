from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class RawEvent:
    ticker: str
    company_name: str | None
    date: date
    source: str
    title: str
    url: str
    summary: str
    keywords: list[str] = field(default_factory=list)
    confirmed_facts: list[str] = field(default_factory=list)
    inferred_implications: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def fetch_events(self, ticker: str, lookback_days: int) -> list[RawEvent]:
        raise NotImplementedError


class NewsProvider(BaseProvider):
    pass


class FilingProvider(BaseProvider):
    pass


class EarningsProvider(BaseProvider):
    pass


class IRProvider(BaseProvider):
    pass


class PriceProvider(BaseProvider):
    pass


class CompetitorProvider(BaseProvider):
    pass

