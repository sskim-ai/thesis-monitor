from datetime import date

from pydantic import BaseModel, Field


class EarningsCheckpointResponse(BaseModel):
    ticker: str
    checkpoints: list[str]
    latest: "EarningsCheckpoint | None" = None
    provider_status: str = "unknown"
    unavailable_reason: str | None = None


class EarningsCheckpoint(BaseModel):
    ticker: str
    period: str
    reported_date: date | None = None
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    eps: float | None = None
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
    stock_based_compensation: float | None = None
    dilution_notes: str | None = None
    revenue_growth: float | None = None
    free_cash_flow: float | None = None
    guidance_change: str | None = None
    important_segment_metrics: list[str] = Field(default_factory=list)
