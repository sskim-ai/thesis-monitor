from datetime import date, datetime, timezone

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class WatchlistItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    company_name: str
    exchange: str | None = None
    issuer_type: str | None = None
    ordinary_share_identifier: str | None = None
    adr_ratio: float | None = None
    adr_currency: str | None = None
    underlying_currency: str | None = None
    notes: str | None = None
    active: bool = True
    monitoring_requested: bool = True
    onboarding_state: str = Field(default="ACTIVE", index=True)
    production_eligible: bool = True
    onboarding_readiness: str = Field(default="{}", sa_column=Column(Text))
    onboarding_failure_stage: str | None = None
    registration_requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    onboarding_ready_at: datetime | None = None
    activated_at: datetime | None = None
    first_eligible_session: date | None = None
    latest_status: str | None = Field(default=None, index=True)
    latest_assessment_date: date | None = Field(default=None, index=True)
    latest_valuation_context: str | None = None
    latest_earnings_estimate_impact: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
