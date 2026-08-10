from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssessmentStatus(StrEnum):
    strengthened = "strengthened"
    weakened = "weakened"
    mixed = "mixed"
    no_material_change = "no_material_change"
    invalidation_candidate = "invalidation_candidate"
    invalidated = "invalidated"
    needs_review = "needs_review"


class MacroExposureInput(BaseModel):
    factor: str = Field(min_length=1)
    direction: str = Field(pattern="^(positive|negative|mixed)$")
    weight: int = Field(default=1, ge=1, le=5)
    channel: str = Field(min_length=1)
    horizon: str | None = None
    condition: str | None = None
    review_required: bool = False


class PriceRulesInput(BaseModel):
    currency: str | None = None
    basis: str = Field(default="close", pattern="^close$")
    confirmation_price: float | None = Field(default=None, gt=0)
    support_zone_low: float | None = Field(default=None, gt=0)
    support_zone_high: float | None = Field(default=None, gt=0)
    warning_price: float | None = Field(default=None, gt=0)
    invalidation_price: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_support_zone(self) -> "PriceRulesInput":
        if (self.support_zone_low is None) != (self.support_zone_high is None):
            raise ValueError("support_zone_low and support_zone_high must be provided together")
        if (
            self.support_zone_low is not None
            and self.support_zone_high is not None
            and self.support_zone_low > self.support_zone_high
        ):
            raise ValueError("support_zone_low must not exceed support_zone_high")
        return self


class MonitoringItemCreate(BaseModel):
    ticker: str = Field(description="Ticker, stock code, or supported Korean company name.", min_length=1)
    company_name: str = Field(description="Canonical company display name.", min_length=1)
    exchange: str | None = Field(default=None, description="Exchange such as KRX or NASDAQ.")
    core_thesis: str = Field(description="Current one-paragraph investment thesis.", min_length=1)
    time_horizon: str | None = Field(default=None, description="Expected investment horizon.")
    thesis_drivers: list[str] = Field(
        default_factory=list,
        description="Detailed and independently stated reasons supporting the thesis.",
    )
    validation_metrics: list[str] = Field(
        default_factory=list,
        description="Measurable company or industry facts that validate the thesis.",
    )
    strengthen_signals: list[str] = Field(
        default_factory=list,
        description="Concrete future facts that would strengthen the thesis.",
    )
    weaken_signals: list[str] = Field(
        default_factory=list,
        description="Concrete future facts that would weaken the thesis.",
    )
    invalidation_signals: list[str] = Field(
        default_factory=list,
        description="Explicit facts that would invalidate the thesis.",
    )
    price_rules: PriceRulesInput | None = Field(
        default=None,
        description="Structured close-price confirmation, support, warning, and invalidation rules.",
    )
    macro_exposures: list[MacroExposureInput] = Field(
        default_factory=list,
        description="Conditional macro factors and transmission channels for this thesis.",
    )


class InvestmentThesisRead(BaseModel):
    ticker: str
    version: int
    core_thesis: str
    time_horizon: str | None
    thesis_drivers: list[str]
    validation_metrics: list[str]
    strengthen_signals: list[str]
    weaken_signals: list[str]
    invalidation_signals: list[str]
    price_rules: PriceRulesInput | None
    macro_exposures: list[MacroExposureInput]
    status: str
    source: str
    created_at: datetime


class MonitoringItemRead(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None
    active: bool
    thesis: InvestmentThesisRead | None
    latest_status: AssessmentStatus | None = None
    latest_assessment_date: date | None = None
    current_thesis_summary: str | None = None


class MonitoringItemSummaryRead(BaseModel):
    ticker: str
    company_name: str
    exchange: str
    active: bool
    thesis_version: int
    core_thesis: str
    thesis_drivers: list[str]
    validation_metrics: list[str]
    price_rules_summary: list[str]
    latest_status: str
    latest_assessment_date: str


class PricePeriodSummary(BaseModel):
    requested_count: int
    actual_count: int
    latest_date: str | None = None
    previous_close: float | None = None
    latest_close: float | None = None
    latest_high: float | None = None
    latest_low: float | None = None
    period_return_pct: float | None = None
    range_position_pct: float | None = None


class PriceRuleEvaluation(BaseModel):
    status: str = "not_configured"
    latest_close: float | None = None
    previous_close: float | None = None
    triggered_rules: list[str] = Field(default_factory=list)
    active_rules: list[str] = Field(default_factory=list)


class PriceContext(BaseModel):
    available: bool = False
    periods: dict[str, PricePeriodSummary] = Field(default_factory=dict)
    rule_evaluation: PriceRuleEvaluation | None = None
    warnings: list[str] = Field(default_factory=list)


class ThesisSnapshot(BaseModel):
    base_thesis: str
    thesis_version: int
    effective_date: date
    status: AssessmentStatus
    current_thesis: str
    thesis_drivers: list[str] = Field(default_factory=list)
    validation_metrics: list[str] = Field(default_factory=list)
    price_rules: PriceRulesInput | None = None
    supporting_evidence: list[dict[str, object]] = Field(default_factory=list)
    weakening_evidence: list[dict[str, object]] = Field(default_factory=list)
    invalidation_evidence: list[dict[str, object]] = Field(default_factory=list)


class ThesisAssessmentRead(BaseModel):
    ticker: str
    thesis_version: int
    assessment_date: date
    status: AssessmentStatus
    score: int
    confidence: float
    summary: str
    new_buyer_view: str
    holder_view: str
    price_view: str
    risk_level: str
    evidence: list[dict[str, object]]
    price_context: PriceContext
    thesis_snapshot: ThesisSnapshot
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailyMonitorResponse(BaseModel):
    run_date: date
    status: str
    ticker_count: int
    success_count: int
    failure_count: int
    assessments: list[ThesisAssessmentRead] = Field(default_factory=list)
