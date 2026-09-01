from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator


class AssessmentStatus(StrEnum):
    strengthened = "strengthened"
    weakened = "weakened"
    mixed = "mixed"
    no_material_change = "no_material_change"
    invalidation_candidate = "invalidation_candidate"
    invalidated = "invalidated"
    needs_review = "needs_review"


class ExpectationLevel(StrEnum):
    depressed = "depressed"
    low = "low"
    balanced = "balanced"
    elevated = "elevated"
    very_high = "very_high"
    speculative = "speculative"
    unknown = "unknown"


class ValuationImpact(StrEnum):
    expansion = "expansion"
    compression = "compression"
    mixed = "mixed"
    neutral = "neutral"
    unknown = "unknown"


class ValuationRelativePosition(StrEnum):
    discounted = "discounted"
    somewhat_discounted = "somewhat_discounted"
    neutral = "neutral"
    somewhat_premium = "somewhat_premium"
    premium = "premium"
    unknown = "unknown"


class EarningsEstimateImpact(StrEnum):
    up = "up"
    down = "down"
    unchanged = "unchanged"
    mixed = "mixed"
    unknown = "unknown"


class StructuralRiskLevel(StrEnum):
    low = "low"
    normal = "normal"
    elevated = "elevated"
    high = "high"
    critical = "critical"


class AssessmentState(StrEnum):
    provisional = "provisional"
    final = "final"


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


class MarketExpectationsInput(BaseModel):
    as_of_date: date | None = None
    level: ExpectationLevel = ExpectationLevel.unknown
    summary: str = ""
    priced_in: list[str] = Field(default_factory=list)
    upside_surprises: list[str] = Field(default_factory=list)
    downside_surprises: list[str] = Field(default_factory=list)
    evidence_basis: list[str] = Field(default_factory=list)


class ValuationFrameworkInput(BaseModel):
    primary_method: str = ""
    secondary_methods: list[str] = Field(default_factory=list)
    rationale: str = ""
    key_inputs: list[str] = Field(default_factory=list)
    peer_or_historical_basis: list[str] = Field(default_factory=list)
    valuation_caveats: list[str] = Field(default_factory=list)


class MarketExpectationAssessment(BaseModel):
    level: ExpectationLevel = ExpectationLevel.unknown
    assessment: str = "unknown"
    summary: str = ""
    evidence_basis: list[str] = Field(default_factory=list)


class MonitoringItemCreate(BaseModel):
    ticker: str = Field(
        description="Ticker, stock code, or supported Korean company name.", min_length=1
    )
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
    market_expectations: MarketExpectationsInput | None = Field(
        default=None,
        description="Dated baseline of what the market already appears to expect.",
    )
    valuation_framework: ValuationFrameworkInput | None = Field(
        default=None,
        description="Company-specific methods and inputs for judging fair valuation.",
    )
    multiple_expansion_signals: list[str] = Field(
        default_factory=list,
        description="Independent facts that could justify a higher valuation multiple.",
    )
    multiple_compression_signals: list[str] = Field(
        default_factory=list,
        description="Independent facts that could justify a lower valuation multiple.",
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
    market_expectations: MarketExpectationsInput | None
    valuation_framework: ValuationFrameworkInput | None
    multiple_expansion_signals: list[str]
    multiple_compression_signals: list[str]
    macro_exposures: list[MacroExposureInput]
    status: str
    source: str
    created_at: datetime


class MonitoringItemRead(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None
    active: bool
    monitoring_requested: bool = True
    onboarding_state: str = "ACTIVE"
    production_eligible: bool = True
    onboarding_blockers: list[str] = Field(default_factory=list)
    onboarding_retry_class: str = "NONE"
    onboarding_next_retry_at: datetime | None = None
    registration_status_message: str = ""
    first_eligible_session: date | None = None
    thesis: InvestmentThesisRead | None
    latest_status: AssessmentStatus | None = None
    latest_assessment_date: date | None = None
    latest_valuation_context: ValuationImpact | None = None
    latest_earnings_estimate_impact: EarningsEstimateImpact | None = None
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
    market_expectation_level: str
    market_expectation_summary: str
    valuation_primary_method: str
    multiple_expansion_signals: list[str]
    multiple_compression_signals: list[str]
    latest_status: str
    latest_assessment_date: str
    latest_valuation_context: str
    latest_earnings_estimate_impact: str


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


class PriceLevelCheck(BaseModel):
    rule: str
    label: str
    meaning: str
    source: str = "registered_price_rule"
    price: float | None = None
    price_low: float | None = None
    price_high: float | None = None


class HistoricalPricePoint(BaseModel):
    date: date
    close: float = Field(gt=0)


class PriceDecisionContext(BaseModel):
    current_price: float | None = None
    currency: str | None = None
    price_as_of: str | None = None
    exchange_trade_date: str | None = None
    latest_completed_regular_session_date: str | None = None
    price_observed_at: str | None = None
    price_observed_timezone: str | None = None
    price_basis: str = "unavailable"
    market_session: str = "unknown"
    assessment_state: AssessmentState = AssessmentState.final
    current_position: str = "가격 위치 자료 없음"
    price_state: str = "no_price_rule"
    price_state_confirmation: str = "unavailable"
    new_observer_checks: list[PriceLevelCheck] = Field(default_factory=list)
    holder_checks: list[PriceLevelCheck] = Field(default_factory=list)
    registered_rules_available: bool = False


class InvestorSupplyContext(BaseModel):
    _reconciliation_payload: dict[str, object] = PrivateAttr(default_factory=dict)

    available: bool = False
    as_of_date: str | None = None
    foreign_net_buy_qty: int | None = None
    institution_net_buy_qty: int | None = None
    individual_net_buy_qty: int | None = None
    foreign_net_buy_qty_5: int | None = None
    institution_net_buy_qty_5: int | None = None
    individual_net_buy_qty_5: int | None = None
    foreign_net_buy_qty_20: int | None = None
    institution_net_buy_qty_20: int | None = None
    individual_net_buy_qty_20: int | None = None
    foreign_holding_qty: int | None = None
    foreign_holding_ratio: float | None = None
    score: float | None = None
    quality: str | None = None
    quality_detail: str | None = None
    primary_signal: str | None = None
    foreign_flow_direction_20: str | None = None
    institution_flow_direction_20: str | None = None
    individual_flow_direction_20: str | None = None
    confidence: str | None = None
    validation_status: str | None = None
    data_scope: str | None = None
    investor_20d_validation_status: str | None = None
    investor_20d_diff_ratio: float | None = None
    signals: list[str] = Field(default_factory=list)

    def set_reconciliation_payload(self, payload: dict[str, object]) -> None:
        self._reconciliation_payload = payload

    def reconciliation_payload(self) -> dict[str, object]:
        return dict(self._reconciliation_payload)


class ChartCandleContext(BaseModel):
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    trading_value: float | None = None
    body_pct: float | None = None
    range_pct: float | None = None
    close_location_pct: float | None = None
    upper_wick_pct: float | None = None
    lower_wick_pct: float | None = None


class ChartTimeframeContext(BaseModel):
    timeframe: str
    as_of_date: str | None = None
    quality: str = "unavailable"
    price_basis: str = "adjusted"
    candle: ChartCandleContext = Field(default_factory=ChartCandleContext)
    period_return_pct: float | None = None
    range_position_pct: float | None = None
    bollinger_upper: dict[str, float] = Field(default_factory=dict)
    bollinger_distance_pct: dict[str, float] = Field(default_factory=dict)
    volume_ratio_20: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None


class ChartContext(BaseModel):
    available: bool = False
    source: str = "ohlcv_analyst"
    as_of_date: str | None = None
    quality: str = "unavailable"
    price_basis: str = "adjusted"
    timeframes: dict[str, ChartTimeframeContext] = Field(default_factory=dict)
    dynamic_levels: dict[str, object] = Field(default_factory=dict)
    structure: dict[str, object] = Field(default_factory=dict)
    unavailable_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PriceContext(BaseModel):
    available: bool = False
    periods: dict[str, PricePeriodSummary] = Field(default_factory=dict)
    rule_evaluation: PriceRuleEvaluation | None = None
    decision: PriceDecisionContext = Field(default_factory=PriceDecisionContext)
    supply: InvestorSupplyContext = Field(default_factory=InvestorSupplyContext)
    chart: ChartContext = Field(default_factory=ChartContext)
    monitoring_state: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    daily_history: list[HistoricalPricePoint] = Field(default_factory=list, exclude=True)
    valuation_history: list[HistoricalPricePoint] = Field(default_factory=list, exclude=True)
    _technical_context_payload: dict[str, object] = PrivateAttr(default_factory=dict)

    def set_technical_context_payload(self, payload: dict[str, object]) -> None:
        self._technical_context_payload = dict(payload)

    def technical_context_payload(self) -> dict[str, object]:
        return dict(self._technical_context_payload)


class HistoricalValuationStatistics(BaseModel):
    metric: str
    current_value: float | None = None
    historical_median: float | None = None
    historical_mean: float | None = None
    percentile_10: float | None = None
    percentile_25: float | None = None
    percentile_50: float | None = None
    percentile_75: float | None = None
    percentile_90: float | None = None
    current_percentile: float | None = None
    observation_count: int = 0
    lookback_years: float = 0.0
    history_start_date: str | None = None
    history_end_date: str | None = None
    target_lookback_years: float = 5.0
    history_coverage_ratio: float = 0.0
    raw_observation_count: int = 0
    deduplicated_observation_count: int = 0
    sampling_frequency: str = "weekly"
    history_quality: str = "insufficient"


class DataCoverage(BaseModel):
    issuer_type: str = "unknown"
    financial_coverage_status: str = "unavailable"
    financials: str = "unavailable"
    earnings: str = "unavailable"
    price: str = "unavailable"
    valuation: str = "unavailable"
    dividend: str = "unavailable"
    capital_actions: str = "unavailable"
    foreign_filing: str = "not_applicable"
    financial_freshness: str = "unavailable"
    business_thesis_confidence: float = 0.0
    valuation_confidence: float = 0.0
    price_confidence: float = 0.0
    macro_impact_confidence: float = 0.0
    reason_codes: list[str] = Field(default_factory=list)
    identity_mapping: str = "unavailable"
    event_relevance: str = "unavailable"
    financial_full: str = "unavailable"
    financial_preliminary: str = "unavailable"
    consensus: str = "unavailable"
    shares: str = "unavailable"
    buyback: str = "unavailable"
    historical_valuation: str = "unavailable"
    forward_valuation: str = "unavailable"
    filing_discovery_coverage: str = "not_applicable"
    document_fetch_coverage: str = "not_applicable"
    exhibit_discovery_coverage: str = "not_applicable"
    statement_parsing_coverage: str = "not_applicable"
    per_share_mapping_coverage: str = "not_applicable"
    valuation_coverage: str = "unavailable"
    price_quality: str = "unavailable"
    financial_quality: str = "unavailable"
    full_financial_availability: str = "unavailable"
    full_financial_freshness: str = "unavailable"
    preliminary_financial_freshness: str = "unavailable"
    full_financial_quality: str = "unavailable"
    preliminary_financial_quality: str = "unavailable"
    event_quality: str = "unavailable"
    current_event_quality: str = "unavailable"
    quarantined_event_count: int = 0
    rejected_candidate_count: int = 0
    identity_audit_status: str = "clean"
    consensus_quality: str = "unavailable"
    historical_valuation_quality: str = "unavailable"
    forward_valuation_quality: str = "unavailable"
    share_count_quality: str = "unavailable"
    dividend_quality: str = "unavailable"
    foreign_filing_quality: str = "not_applicable"
    foreign_parsing_result: str = "not_applicable"
    foreign_latest_filing_result: str = "not_applicable"
    any_foreign_statement_parsed: bool = False
    latest_foreign_filing_parse_result: str = "not_applicable"
    latest_foreign_financial_period: str | None = None
    latest_foreign_financial_filing_date: str | None = None
    overall_data_quality: str = "unavailable"
    overall_quality_reason: str | None = None


class ValuationSnapshot(BaseModel):
    current_price: float | None = None
    currency: str | None = None
    price_as_of: str | None = None
    exchange_trade_date: str | None = None
    latest_completed_regular_session_date: str | None = None
    price_observed_at: str | None = None
    price_observed_timezone: str | None = None
    price_basis: str = "unavailable"
    ttm_eps: float | None = None
    raw_ttm_eps: float | None = None
    bvps: float | None = None
    raw_bvps: float | None = None
    forward_eps: float | None = None
    forward_bvps: float | None = None
    trailing_pe: float | None = None
    trailing_pe_status: str = "unavailable"
    trailing_pe_source: str = "unavailable"
    trailing_pe_method: str | None = None
    forward_pe: float | None = None
    forward_pe_status: str = "unavailable"
    forward_pe_source: str = "unavailable"
    forward_pe_method: str | None = None
    price_to_book: float | None = None
    price_to_book_status: str = "unavailable"
    price_to_book_source: str = "unavailable"
    price_to_book_method: str | None = None
    forward_price_to_book: float | None = None
    forward_price_to_book_status: str = "unavailable"
    forward_price_to_book_source: str = "unavailable"
    forward_price_to_book_method: str | None = None
    trailing_basis: str = "LTM EPS"
    forward_basis: str | None = None
    book_basis: str = "latest reported book value"
    forward_book_basis: str | None = None
    provider: str = "unavailable"
    valuation_data_as_of: str | None = None
    denominator_as_of: str | None = None
    trailing_pe_denominator_period_end: str | None = None
    trailing_pe_denominator_filing_date: str | None = None
    pbr_denominator_period_end: str | None = None
    pbr_denominator_filing_date: str | None = None
    forward_pe_input_period: str | None = None
    forward_pb_input_period: str | None = None
    latest_preliminary_context_period: str | None = None
    financials_as_of: str | None = None
    financial_period_end: str | None = None
    filing_date: str | None = None
    valuation_calculated_at: str | None = None
    ttm_period_start: str | None = None
    ttm_period_end: str | None = None
    ttm_source_filings: list[str] = Field(default_factory=list)
    ttm_contains_preliminary: bool = False
    preliminary_quarter_count: int = 0
    latest_earnings_period: str | None = None
    latest_earnings_period_type: str | None = None
    latest_earnings_fiscal_year: int | None = None
    latest_earnings_period_scope: str | None = None
    latest_earnings_is_cumulative: bool = False
    financial_currency: str | None = None
    resolved_issuer_type: str = "unknown"
    resolved_security_type: str = "unknown"
    is_depositary_security: bool = False
    resolved_adr_ratio: float | None = None
    adr_ratio_used: float | None = None
    adr_ratio_source: str | None = None
    adr_ratio_direction: str | None = None
    eps_currency: str | None = None
    eps_security_basis: str = "unknown"
    book_currency: str | None = None
    share_count_security_basis: str = "unknown"
    trailing_pe_basis_status: str = "not_applicable"
    price_to_book_basis_status: str = "not_applicable"
    forward_pe_basis_status: str = "not_applicable"
    forward_price_to_book_basis_status: str = "not_applicable"
    historical_per_share_basis_status: str = "not_applicable"
    earnings_context_source: str | None = None
    earnings_context_is_preliminary: bool = False
    earnings_context_usable: bool = False
    latest_eps_usable: bool = False
    ttm_eps_usable: bool = False
    # Backward-compatible alias for ttm_eps_usable.
    eps_per_usable: bool = False
    latest_revenue: float | None = None
    latest_operating_income: float | None = None
    earnings_basis: str | None = None
    share_basis: str | None = None
    earnings_quarter_series: list[dict[str, object]] = Field(default_factory=list)
    financial_quality_source_metadata: dict[str, object] = Field(default_factory=dict)
    latest_operating_margin: float | None = None
    latest_revenue_qoq: float | None = None
    latest_revenue_yoy: float | None = None
    latest_operating_income_qoq: float | None = None
    latest_operating_income_yoy: float | None = None
    latest_operating_margin_delta_qoq: float | None = None
    quality: str = "unavailable"
    trailing_valuation_confidence: float = 0.0
    forward_valuation_confidence: float = 0.0
    forecast_method: str | None = None
    valuation_relative_position: ValuationRelativePosition = ValuationRelativePosition.unknown
    valuation_relative_basis: str | None = None
    valuation_relative_position_confidence: str = "low"
    valuation_relative_position_reason: str | None = None
    valuation_signal_summary: str | None = None
    valuation_signal_conflict: bool = False
    valuation_primary_signal: str | None = None
    valuation_secondary_signals: list[str] = Field(default_factory=list)
    valuation_relative_position_reason_codes: list[str] = Field(default_factory=list)
    historical_comparability: str = "normal"
    historical_pe_statistics: HistoricalValuationStatistics | None = None
    historical_pb_statistics: HistoricalValuationStatistics | None = None
    dividend_forecast_method: str | None = None
    dividend_forecast_quality: str = "unavailable"
    dividend_assumption: str | None = None
    buyback_forecast_method: str | None = None
    buyback_assumption_quality: str = "unavailable"
    buyback_assumption: str | None = None
    financial_refresh_required: bool = False
    latest_material_financial_event_date: str | None = None
    financial_freshness: str = "unavailable"
    latest_full_financial_period: str | None = None
    latest_preliminary_financial_period: str | None = None
    latest_full_filing_date: str | None = None
    latest_preliminary_filing_date: str | None = None
    latest_guidance_date: str | None = None
    financial_refresh_result: str = "unavailable"
    financial_refresh_reason: str | None = None
    financial_refresh_trigger_event_id: int | None = None
    estimate_provider: str | None = None
    estimate_as_of: str | None = None
    estimate_period: str | None = None
    estimate_mean: float | None = None
    estimate_high: float | None = None
    estimate_low: float | None = None
    estimate_analyst_count: int | None = None
    estimate_revision_direction: str = "unknown"
    consensus_status: str = "unavailable"
    consensus_disagreement: bool = False
    share_count_discrepancy_warning: bool = False
    historical_distribution_confidence: float = 0.0
    current_multiple_confidence: float = 0.0
    forward_multiple_confidence: float = 0.0
    data_coverage: DataCoverage = Field(default_factory=DataCoverage)
    valuation_discrepancy_warning: bool = False
    trailing_pe_basis_conflict: bool = False
    price_to_book_basis_conflict: bool = False
    forward_pe_basis_conflict: bool = False
    forward_price_to_book_basis_conflict: bool = False
    provider_trailing_pe: float | None = None
    derived_trailing_pe: float | None = None
    provider_price_to_book: float | None = None
    derived_price_to_book: float | None = None
    provider_forward_pe: float | None = None
    derived_forward_pe: float | None = None
    provider_forward_price_to_book: float | None = None
    derived_forward_price_to_book: float | None = None
    trailing_pe_comparability: str = "insufficient_metadata"
    trailing_pe_comparability_reason: str | None = None
    price_to_book_comparability: str = "insufficient_metadata"
    price_to_book_comparability_reason: str | None = None
    forward_pe_comparability: str = "insufficient_metadata"
    forward_pe_comparability_reason: str | None = None
    forward_pe_reference_caution: bool = False
    forward_pe_reference_caution_reason: str | None = None
    forward_pe_reference_difference_pct: float | None = None
    forward_price_to_book_comparability: str = "insufficient_metadata"
    forward_price_to_book_comparability_reason: str | None = None
    multiple_basis_conflicts: list[str] = Field(default_factory=list)
    valuation_calculation_warning: bool = False
    warnings: list[str] = Field(default_factory=list)


class ValuationContext(BaseModel):
    impact: ValuationImpact = ValuationImpact.unknown
    summary: str = ""
    market_expectation_level: ExpectationLevel = ExpectationLevel.unknown
    market_expectation_summary: str = ""
    primary_method: str = ""
    configured_expansion_signals: list[str] = Field(default_factory=list)
    configured_compression_signals: list[str] = Field(default_factory=list)
    matched_expansion_signals: list[str] = Field(default_factory=list)
    matched_compression_signals: list[str] = Field(default_factory=list)
    matched_expansion_conditions: list[str] = Field(default_factory=list)
    matched_compression_conditions: list[str] = Field(default_factory=list)
    macro_valuation_effect: str = "neutral"
    macro_valuation_effects: list[str] = Field(default_factory=list)
    valuation_evidence: list[str] = Field(default_factory=list)
    previous_impact: ValuationImpact | None = None
    valuation_relative_position: ValuationRelativePosition = ValuationRelativePosition.unknown
    valuation_relative_basis: str | None = None
    evidence_count: int = 0


class ThesisSnapshot(BaseModel):
    base_thesis: str
    thesis_version: int
    effective_date: date
    status: AssessmentStatus
    current_thesis: str
    thesis_drivers: list[str] = Field(default_factory=list)
    validation_metrics: list[str] = Field(default_factory=list)
    price_rules: PriceRulesInput | None = None
    market_expectations: MarketExpectationsInput | None = None
    valuation_framework: ValuationFrameworkInput | None = None
    multiple_expansion_signals: list[str] = Field(default_factory=list)
    multiple_compression_signals: list[str] = Field(default_factory=list)
    valuation_context: ValuationContext = Field(default_factory=ValuationContext)
    supporting_evidence: list[dict[str, object]] = Field(default_factory=list)
    weakening_evidence: list[dict[str, object]] = Field(default_factory=list)
    invalidation_evidence: list[dict[str, object]] = Field(default_factory=list)


class ThesisAssessmentRead(BaseModel):
    ticker: str
    thesis_version: int
    assessment_date: date
    status: AssessmentStatus
    business_thesis_change: AssessmentStatus
    valuation_change: ValuationImpact
    earnings_estimate_impact: EarningsEstimateImpact
    market_expectation_assessment: MarketExpectationAssessment
    confirmed_facts: list[str]
    background_confirmed_facts: list[str] = Field(default_factory=list)
    inferred_implications: list[str]
    unknowns: list[str]
    confirmed_warnings: list[str] = Field(default_factory=list)
    new_warnings: list[str] = Field(default_factory=list)
    open_warnings: list[str] = Field(default_factory=list)
    open_confirmed_warnings: list[str] = Field(default_factory=list)
    persistent_watch_risks: list[str] = Field(default_factory=list)
    warning_states: list[dict[str, object]] = Field(default_factory=list)
    watch_items: list[str] = Field(default_factory=list)
    used_event_fingerprints: list[str] = Field(default_factory=list)
    score: int
    confidence: float
    summary: str
    new_buyer_view: str
    holder_view: str
    price_view: str
    risk_level: str
    daily_change_severity: str = "none"
    structural_risk_level: StructuralRiskLevel = StructuralRiskLevel.normal
    assessment_state: AssessmentState = AssessmentState.final
    market_session: str = "unknown"
    evidence: list[dict[str, object]]
    price_context: PriceContext
    new_buyer_price_view: str = ""
    holder_price_view: str = ""
    valuation_snapshot: ValuationSnapshot = Field(default_factory=ValuationSnapshot)
    valuation_context: ValuationContext = Field(default_factory=ValuationContext)
    thesis_snapshot: ThesisSnapshot
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThesisAssessmentCreate(BaseModel):
    assessment_date: date
    business_thesis_change: AssessmentStatus
    valuation_context: ValuationImpact
    earnings_estimate_impact: EarningsEstimateImpact = EarningsEstimateImpact.unknown
    market_expectation_assessment: MarketExpectationAssessment | None = None
    confirmed_facts: list[str] = Field(default_factory=list)
    inferred_implications: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    summary: str = ""
    new_buyer_view: str = ""
    holder_view: str = ""
    price_view: str = ""
    risk_level: str = "review"
    confidence: float = Field(default=0.0, ge=0, le=1)


class DailyMonitorResponse(BaseModel):
    run_date: date
    status: str
    ticker_count: int
    success_count: int
    failure_count: int
    assessments: list[ThesisAssessmentRead] = Field(default_factory=list)
