from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class SecurityMaster(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("canonical_security_id"),)

    id: int | None = Field(default=None, primary_key=True)
    canonical_company_id: str = Field(index=True)
    canonical_security_id: str = Field(index=True)
    ticker: str = Field(index=True, unique=True)
    exchange: str | None = None
    country: str | None = None
    company_name: str
    legal_name: str | None = None
    cik: str | None = Field(default=None, index=True)
    corp_code: str | None = Field(default=None, index=True)
    figi: str | None = Field(default=None, index=True)
    security_type: str = "common_stock"
    share_class: str | None = None
    issuer_type: str = "unknown"
    ordinary_share_identifier: str | None = None
    adr_identifier: str | None = None
    adr_ratio: float | None = None
    known_subsidiaries: str = "[]"
    known_products: str = "[]"
    known_brands: str = "[]"
    aliases: str = "[]"
    identity_quality: str = "partial"
    identity_provider: str = "local"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProviderResponseCache(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("provider", "ticker", "data_type"),)

    id: int | None = Field(default=None, primary_key=True)
    provider: str = Field(index=True)
    ticker: str = Field(index=True)
    data_type: str = Field(index=True)
    status: str = "unavailable"
    payload: str = "{}"
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None


class ConsensusEstimate(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("ticker", "provider", "estimate_period", "estimate_as_of"),
    )

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    provider: str = Field(index=True)
    estimate_as_of: datetime = Field(index=True)
    estimate_period: str = Field(index=True)
    estimate_mean: float | None = None
    estimate_high: float | None = None
    estimate_low: float | None = None
    revenue_estimate_mean: float | None = None
    analyst_count: int | None = None
    revision_direction: str = "unknown"
    revision_count: int | None = None
    quality: str = "partial"
    raw_reference: str | None = None


class ShareCountObservation(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "provider", "period"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    provider: str = Field(index=True)
    period: str = Field(index=True)
    basic_shares: float | None = None
    diluted_shares: float | None = None
    quality: str = "partial"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
