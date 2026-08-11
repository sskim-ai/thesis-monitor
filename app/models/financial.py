from datetime import date, datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class FinancialSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    period: str
    snapshot_type: str = Field(default="full_statement", index=True)
    source_event_date: date | None = Field(default=None, index=True)
    source_filing_id: str | None = Field(default=None, index=True)
    period_type: str | None = Field(default=None, index=True)
    fiscal_year: int | None = Field(default=None, index=True)
    period_scope: str | None = None
    is_cumulative: bool = False
    normalization_method: str | None = None
    financials_as_of: date | None = None
    reported_date: date | None = None
    financial_period_end: date | None = None
    filing_date: date | None = None
    source: str | None = None
    provider: str | None = None
    currency: str | None = None
    unit_scale: float | None = None
    fs_div: str | None = None
    sj_div: str | None = None
    revenue_basis: str | None = None
    operating_income_basis: str | None = None
    balance_sheet_basis: str | None = None
    quality_warnings: str | None = None
    raw_financial_fields: str = "[]"
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    eps: float | None = None
    basic_eps: float | None = None
    diluted_eps: float | None = None
    owners_parent_net_income: float | None = None
    common_net_income: float | None = None
    cumulative_revenue: float | None = None
    cumulative_operating_income: float | None = None
    cumulative_net_income: float | None = None
    cumulative_basic_eps: float | None = None
    cumulative_diluted_eps: float | None = None
    operating_cash_flow: float | None = None
    fcf: float | None = None
    capex: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    yoy_growth: float | None = None
    qoq_growth: float | None = None
    guidance: str | None = None
    backlog: float | None = None
    inventory: float | None = None
    accounts_receivable: float | None = None
    debt: float | None = None
    cash: float | None = None
    total_equity: float | None = None
    owners_parent_equity: float | None = None
    common_equity: float | None = None
    issued_common_shares: float | None = None
    treasury_shares: float | None = None
    common_shares_outstanding: float | None = None
    diluted_shares: float | None = None
    dividends: float | None = None
    common_dividends: float | None = None
    buybacks: float | None = None
    equity_issuance: float | None = None
    other_comprehensive_income: float | None = None
    financial_statement_basis_warning: bool = False
    margin_quality_review: bool = False
    stock_based_compensation: float | None = None
    dilution_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HistoricalValuationObservation(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "observation_date"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    observation_date: date = Field(index=True)
    price: float
    financial_filing_id: int | None = Field(default=None, index=True)
    filing_date: date | None = Field(default=None, index=True)
    financial_period_end: date | None = None
    ttm_period_start: date | None = None
    ttm_period_end: date | None = None
    ttm_source_filings: str = "[]"
    ttm_eps: float | None = None
    bvps: float | None = None
    trailing_pe: float | None = None
    price_to_book: float | None = None
    quality: str = "unavailable"
    sampling_frequency: str = "weekly"
    iso_year: int | None = Field(default=None, index=True)
    iso_week: int | None = Field(default=None, index=True)
    warnings: str = "[]"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DividendHistory(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("ticker", "fiscal_year", "record_date", "source_filing_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    fiscal_year: int | None = Field(default=None, index=True)
    payment_date: date | None = None
    record_date: date | None = Field(default=None, index=True)
    dividend_per_share: float | None = None
    total_dividend: float | None = None
    payout_ratio: float | None = None
    dividend_type: str = "cash_common"
    source: str
    provider: str
    source_filing_id: str | None = Field(default=None, index=True)
    quality: str = "partial"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CapitalReturnHistory(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("ticker", "period_end", "return_type", "source_filing_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    period_start: date | None = None
    period_end: date | None = Field(default=None, index=True)
    return_type: str = Field(index=True)
    authorization_amount: float | None = None
    actual_amount: float | None = None
    shares: float | None = None
    source: str
    provider: str
    source_filing_id: str | None = Field(default=None, index=True)
    quality: str = "partial"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DataBackfillState(SQLModel, table=True):
    ticker: str = Field(primary_key=True)
    backfill_status: str = "pending"
    backfill_started_at: datetime | None = None
    backfill_completed_at: datetime | None = None
    backfill_years_requested: int = 5
    backfill_years_available: float = 0.0
    backfill_gap_reason: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
