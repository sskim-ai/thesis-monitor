from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class FinancialSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    period: str
    period_type: str | None = Field(default=None, index=True)
    fiscal_year: int | None = Field(default=None, index=True)
    period_scope: str | None = None
    is_cumulative: bool = False
    normalization_method: str | None = None
    financials_as_of: date | None = None
    reported_date: date | None = None
    source: str | None = None
    provider: str | None = None
    fs_div: str | None = None
    sj_div: str | None = None
    revenue_basis: str | None = None
    operating_income_basis: str | None = None
    balance_sheet_basis: str | None = None
    quality_warnings: str | None = None
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
    financial_statement_basis_warning: bool = False
    margin_quality_review: bool = False
    stock_based_compensation: float | None = None
    dilution_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
