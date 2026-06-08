from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    company_name: str
    exchange: str | None = None
    industry: str | None = None
    sector: str | None = None
    business_units: str | None = None
    revenue_sources: str | None = None
    major_customers: str | None = None
    ir_url: str | None = None
    filings_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

