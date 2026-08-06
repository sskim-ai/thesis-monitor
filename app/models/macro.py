from datetime import date, datetime, timezone

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MacroThesis(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("thesis_key", "version"),)

    id: int | None = Field(default=None, primary_key=True)
    thesis_key: str = Field(index=True)
    version: int = Field(default=1, index=True)
    title: str
    description: str = Field(sa_column=Column(Text))
    region: str = "global"
    horizon: str = "medium"
    status: str = Field(default="intact", index=True)
    confidence: float = 0.5
    base_case_probability: float = 0.5
    bull_case: str = Field(default="", sa_column=Column(Text))
    base_case: str = Field(default="", sa_column=Column(Text))
    bear_case: str = Field(default="", sa_column=Column(Text))
    expected_evidence: str = Field(default="[]", sa_column=Column(Text))
    weakening_evidence: str = Field(default="[]", sa_column=Column(Text))
    kill_conditions: str = Field(default="[]", sa_column=Column(Text))
    valuation_channels: str = Field(default="[]", sa_column=Column(Text))
    affected_assets: str = Field(default="[]", sa_column=Column(Text))
    last_reviewed_at: datetime | None = None
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class MacroThesisEvidence(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    macro_thesis_id: int = Field(index=True)
    observation_id: int | None = Field(default=None, index=True)
    event_id: int | None = Field(default=None, index=True)
    direction: str
    weight: int = 1
    persistence: str = "temporary"
    confidence: float = 0.5
    half_life_days: int = 30
    rationale: str = Field(default="", sa_column=Column(Text))
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)


class MacroObservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dedupe_key: str = Field(unique=True, index=True)
    series_code: str = Field(index=True)
    category: str = Field(index=True)
    provider: str = Field(index=True)
    observed_at: datetime = Field(index=True)
    market_session: str | None = None
    value: float
    unit: str | None = None
    frequency: str | None = None
    previous_value: float | None = None
    change_value: float | None = None
    change_pct: float | None = None
    zscore_20d: float | None = None
    zscore_1y: float | None = None
    source_url: str
    retrieved_at: datetime = Field(default_factory=_utcnow)
    vintage_at: datetime | None = None
    is_preliminary: bool = False
    is_revised: bool = False
    quality_status: str = Field(default="fresh", index=True)
    raw_payload: str = Field(default="{}", sa_column=Column(Text))
    schema_version: int = 1


class MacroEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_key: str = Field(unique=True, index=True)
    event_type: str = Field(index=True)
    category: str = Field(index=True)
    title: str
    country: str | None = None
    region: str | None = None
    scheduled_at: datetime | None = Field(default=None, index=True)
    released_at: datetime | None = Field(default=None, index=True)
    event_status: str = Field(default="released", index=True)
    actual: float | None = None
    consensus: float | None = None
    previous: float | None = None
    revised_previous: float | None = None
    unit: str | None = None
    surprise_value: float | None = None
    surprise_score: float | None = None
    impact_level: int = 1
    confirmed_facts: str = Field(default="[]", sa_column=Column(Text))
    inferred_implications: str = Field(default="[]", sa_column=Column(Text))
    unknowns: str = Field(default="[]", sa_column=Column(Text))
    provider: str = Field(index=True)
    source_url: str
    source_reliability: float = 0.8
    retrieved_at: datetime = Field(default_factory=_utcnow)
    schema_version: int = 1


class MacroExpectationSnapshot(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("event_key", "captured_at", "source"),)

    id: int | None = Field(default=None, primary_key=True)
    event_key: str = Field(index=True)
    captured_at: datetime = Field(index=True)
    expectation_type: str
    expected_value: float | None = None
    expected_range_low: float | None = None
    expected_range_high: float | None = None
    probability_distribution: str = Field(default="{}", sa_column=Column(Text))
    source: str
    source_url: str | None = None
    confidence: float = 0.5
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)


class MacroMarketReaction(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("event_id", "asset_code", "reaction_window"),)

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(index=True)
    asset_code: str = Field(index=True)
    reaction_window: str
    price_before: float | None = None
    price_after: float | None = None
    return_pct: float | None = None
    yield_change_bp: float | None = None
    volume_ratio: float | None = None
    volatility_change: float | None = None
    direction: str = "neutral"
    is_reversal: bool = False
    schema_version: int = 1
    retrieved_at: datetime = Field(default_factory=_utcnow)


class MacroShockAssessment(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("assessment_date", "event_id"),)

    id: int | None = Field(default=None, primary_key=True)
    assessment_date: date = Field(index=True)
    event_id: int | None = Field(default=None, index=True)
    shock_type: str = Field(index=True)
    direction: str
    magnitude: int = 1
    persistence: str = "temporary"
    confidence: float = 0.5
    evidence: str = Field(default="[]", sa_column=Column(Text))
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)


class MacroRegimeAssessment(SQLModel, table=True):
    assessment_date: date = Field(primary_key=True)
    growth_momentum: int = 0
    inflation_pressure: int = 0
    liquidity_condition: int = 0
    financial_conditions: int = 0
    risk_appetite: int = 0
    earnings_momentum: int = 0
    regime_label: str = "mixed"
    confidence: float = 0.0
    persistence_days: int = 1
    provisional: bool = False
    summary: str = Field(sa_column=Column(Text))
    evidence: str = Field(default="[]", sa_column=Column(Text))
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)


class ThesisMacroImpact(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "thesis_version", "assessment_date"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    thesis_version: int
    assessment_date: date = Field(index=True)
    direction: str = Field(default="neutral", index=True)
    magnitude: int = 0
    persistence: str = "temporary"
    confidence: float = 0.0
    channels: str = Field(default="[]", sa_column=Column(Text))
    affected_thesis_pillars: str = Field(default="[]", sa_column=Column(Text))
    earnings_effect: str = Field(default="neutral", sa_column=Column(Text))
    valuation_effect: str = Field(default="neutral", sa_column=Column(Text))
    rationale: str = Field(default="", sa_column=Column(Text))
    evidence: str = Field(default="[]", sa_column=Column(Text))
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)


class MacroBriefing(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("briefing_date", "briefing_type"),)

    id: int | None = Field(default=None, primary_key=True)
    briefing_date: date = Field(index=True)
    briefing_type: str = Field(default="morning")
    as_of: datetime
    headline: str
    market_summary: str = Field(default="{}", sa_column=Column(Text))
    regime_summary: str = Field(default="{}", sa_column=Column(Text))
    today_calendar: str = Field(default="[]", sa_column=Column(Text))
    macro_theses: str = Field(default="[]", sa_column=Column(Text))
    ticker_impacts: str = Field(default="[]", sa_column=Column(Text))
    data_quality: str = Field(default="[]", sa_column=Column(Text))
    kakao_text: str = Field(sa_column=Column(Text))
    status: str = Field(default="ready", index=True)
    dedupe_key: str = Field(unique=True, index=True)
    schema_version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)
