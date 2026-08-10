from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class WatchlistItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    company_name: str
    exchange: str | None = None
    notes: str | None = None
    active: bool = True
    latest_status: str | None = Field(default=None, index=True)
    latest_assessment_date: date | None = Field(default=None, index=True)
    latest_valuation_context: str | None = None
    latest_earnings_estimate_impact: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
