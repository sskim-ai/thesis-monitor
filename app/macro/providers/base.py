from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class CollectedObservation:
    series_code: str
    category: str
    observed_at: datetime
    value: float
    source_url: str
    unit: str | None = None
    frequency: str | None = None
    market_session: str | None = None
    previous_value: float | None = None
    change_value: float | None = None
    change_pct: float | None = None
    is_preliminary: bool = False
    is_revised: bool = False
    raw_payload: dict[str, object] = field(default_factory=dict)


@dataclass
class CollectedEvent:
    event_key: str
    event_type: str
    category: str
    title: str
    source_url: str
    event_status: str = "released"
    country: str | None = None
    region: str | None = None
    scheduled_at: datetime | None = None
    released_at: datetime | None = None
    actual: float | None = None
    consensus: float | None = None
    previous: float | None = None
    revised_previous: float | None = None
    unit: str | None = None
    impact_level: int = 1
    confirmed_facts: list[str] = field(default_factory=list)
    inferred_implications: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    source_reliability: float = 0.8


@dataclass
class MacroProviderResult:
    provider: str
    observations: list[CollectedObservation] = field(default_factory=list)
    events: list[CollectedEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MacroProvider(Protocol):
    name: str

    async def collect(self, as_of: datetime) -> MacroProviderResult: ...
