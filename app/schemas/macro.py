from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MacroObservationRead(BaseModel):
    series_code: str
    category: str
    provider: str
    observed_at: datetime
    market_session: str | None
    value: float
    unit: str | None
    frequency: str | None
    previous_value: float | None
    change_value: float | None
    change_pct: float | None
    quality_status: str
    source_url: str
    retrieved_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MacroEventRead(BaseModel):
    event_key: str
    event_type: str
    category: str
    title: str
    country: str | None
    scheduled_at: datetime | None
    released_at: datetime | None
    event_status: str
    actual: float | None
    consensus: float | None
    previous: float | None
    revised_previous: float | None
    unit: str | None
    surprise_value: float | None
    surprise_score: float | None
    impact_level: int
    confirmed_facts: list[str]
    inferred_implications: list[str]
    unknowns: list[str]
    provider: str
    source_url: str
    source_reliability: float


class MacroRegimeRead(BaseModel):
    assessment_date: date
    growth_momentum: int
    inflation_pressure: int
    liquidity_condition: int
    financial_conditions: int
    risk_appetite: int
    earnings_momentum: int
    regime_label: str
    confidence: float
    persistence_days: int
    provisional: bool
    market_session: str = "unknown"
    assessment_state: str = "final"
    summary: str
    evidence: list[dict[str, object]]


class MacroThesisRead(BaseModel):
    thesis_key: str
    version: int
    title: str
    description: str
    region: str
    horizon: str
    status: str
    today_signal: str = "neutral"
    today_signal_strength: str = "none"
    today_signal_evidence: list[str] = Field(default_factory=list)
    today_signal_rationale: str = ""
    today_signal_date: date | None = None
    confidence: float
    base_case_probability: float
    bull_case: str
    base_case: str
    bear_case: str
    expected_evidence: list[str]
    weakening_evidence: list[str]
    kill_conditions: list[str]
    valuation_channels: list[str]
    affected_assets: list[str]
    last_reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ThesisMacroImpactRead(BaseModel):
    ticker: str
    thesis_version: int
    assessment_date: date
    direction: str
    magnitude: int
    persistence: str
    confidence: float
    channels: list[str]
    affected_thesis_pillars: list[str]
    earnings_effect: str
    valuation_effect: str
    rationale: str
    evidence: list[dict[str, object]]


class MacroBriefingRead(BaseModel):
    briefing_date: date
    briefing_type: str
    as_of: datetime
    headline: str
    market_summary: dict[str, object]
    regime_summary: dict[str, object]
    today_calendar: list[dict[str, object]]
    macro_theses: list[dict[str, object]]
    ticker_impacts: list[dict[str, object]]
    data_quality: list[dict[str, object]]
    kakao_text: str
    status: str
    market_session: str = "unknown"
    assessment_state: str = "final"


class MacroProviderStatusRead(BaseModel):
    name: str
    enabled: bool
    configured: bool
    required_settings: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class MacroMonitorResponse(BaseModel):
    run_date: date
    status: str
    observation_count: int
    event_count: int
    impact_count: int
    provider_warnings: list[str] = Field(default_factory=list)
    briefing: MacroBriefingRead | None = None
