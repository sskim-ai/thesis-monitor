from pydantic import BaseModel, ConfigDict, Field


class CompanyProfile(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None = None
    industry: str | None = None
    sector: str | None = None
    business_units: list[str] = []
    major_revenue_sources: list[str] = []
    major_customers: list[str] = []
    ir_url: str | None = None
    filings_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisPricePeriod(BaseModel):
    latest_close: float | None = None
    period_return_pct: float | None = None
    range_position_pct: float | None = None
    actual_count: int = 0


class AnalysisPriceSnapshot(BaseModel):
    available: bool = False
    current_price: float | None = None
    currency: str | None = None
    price_as_of: str | None = None
    market_session: str = "unknown"
    current_position: str | None = None
    periods: dict[str, AnalysisPricePeriod] = Field(default_factory=dict)


class AnalysisEarningsSnapshot(BaseModel):
    latest_period: str | None = None
    is_preliminary: bool = False
    revenue: float | None = None
    operating_income: float | None = None
    operating_margin: float | None = None
    qoq_revenue_growth: float | None = None
    qoq_operating_income_growth: float | None = None
    yoy_revenue_growth: float | None = None
    yoy_operating_income_growth: float | None = None
    ttm_eps: float | None = None
    ttm_contains_preliminary: bool = False


class AnalysisHistoricalValuation(BaseModel):
    current_value: float | None = None
    median: float | None = None
    current_percentile: float | None = None
    lookback_years: float = 0.0


class AnalysisValuationSnapshot(BaseModel):
    current_price: float | None = None
    ttm_eps: float | None = None
    bvps: float | None = None
    forward_eps: float | None = None
    forward_bvps: float | None = None
    trailing_pe: float | None = None
    price_to_book: float | None = None
    forward_pe: float | None = None
    forward_price_to_book: float | None = None
    valuation_relative_position: str = "unknown"
    valuation_relative_position_confidence: str = "low"
    historical_pe: AnalysisHistoricalValuation | None = None
    historical_pb: AnalysisHistoricalValuation | None = None


class AnalysisDataStatus(BaseModel):
    price: str = "unavailable"
    earnings: str = "unavailable"
    valuation: str = "unavailable"
    financial_freshness: str = "unavailable"


class TickerAnalysisSnapshot(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None = None
    as_of: str
    price: AnalysisPriceSnapshot = Field(default_factory=AnalysisPriceSnapshot)
    earnings: AnalysisEarningsSnapshot = Field(
        default_factory=AnalysisEarningsSnapshot
    )
    valuation: AnalysisValuationSnapshot = Field(
        default_factory=AnalysisValuationSnapshot
    )
    data_status: AnalysisDataStatus = Field(default_factory=AnalysisDataStatus)
    cautions: list[str] = Field(default_factory=list)
