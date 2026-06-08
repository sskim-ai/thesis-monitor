from datetime import date

from pydantic import BaseModel


class EarningsCheckpoint(BaseModel):
    ticker: str
    period: str
    reported_date: date | None = None
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    eps: float | None = None
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None
    capex: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    guidance: str | None = None
    backlog: float | None = None
    inventory: float | None = None
    receivables: float | None = None
    debt: float | None = None
    cash: float | None = None
    stock_compensation: float | None = None
    dilution_notes: str | None = None

