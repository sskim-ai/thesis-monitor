from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    new_customer = "new_customer"
    large_order = "large_order"
    production_order = "production_order"
    mass_production_change = "mass_production_change"
    revenue_guidance_up = "revenue_guidance_up"
    revenue_guidance_down = "revenue_guidance_down"
    margin_improvement = "margin_improvement"
    margin_deterioration = "margin_deterioration"
    fcf_deterioration = "fcf_deterioration"
    inventory_increase = "inventory_increase"
    inventory_normalization = "inventory_normalization"
    receivables_increase = "receivables_increase"
    dilution_risk = "dilution_risk"
    capital_raise = "capital_raise"
    convertible_bond = "convertible_bond"
    warrant = "warrant"
    stock_compensation_increase = "stock_compensation_increase"
    buyback = "buyback"
    share_retirement = "share_retirement"
    dividend = "dividend"
    stock_split = "stock_split"
    reverse_split = "reverse_split"
    capital_reduction = "capital_reduction"
    partnership = "partnership"
    partnership_to_revenue = "partnership_to_revenue"
    customer_loss = "customer_loss"
    customer_concentration_risk = "customer_concentration_risk"
    market_share_change = "market_share_change"
    competitor_price_cut = "competitor_price_cut"
    competitor_new_product = "competitor_new_product"
    technology_competition = "technology_competition"
    regulatory_risk = "regulatory_risk"
    export_control = "export_control"
    antitrust = "antitrust"
    accounting_issue = "accounting_issue"
    debt_liquidity_risk = "debt_liquidity_risk"
    credit_rating_change = "credit_rating_change"
    management_governance = "management_governance"
    capital_allocation = "capital_allocation"
    facility_investment = "facility_investment"
    disclosure_inquiry = "disclosure_inquiry"
    disclosure_clarification = "disclosure_clarification"
    earnings_surprise = "earnings_surprise"
    earnings_beat = "earnings_beat"
    earnings_miss = "earnings_miss"
    guidance_change = "guidance_change"
    revenue_guidance_change = "revenue_guidance_change"
    margin_guidance_change = "margin_guidance_change"
    fcf_change = "fcf_change"
    operating_cash_flow_change = "operating_cash_flow_change"
    capex_change = "capex_change"
    major_customer_win = "major_customer_win"
    order_change = "order_change"
    production_delay = "production_delay"
    dilution = "dilution"
    debt_liquidity = "debt_liquidity"
    regulatory_material = "regulatory_material"
    financial_report = "financial_report"
    valuation_recalculation_needed = "valuation_recalculation_needed"
    non_thesis_noise = "non_thesis_noise"


class FinancialImpact(BaseModel):
    revenue_guidance_changed: bool = False
    margin_guidance_changed: bool = False
    guidance_changed: bool = False
    earnings_guidance_changed: bool = False
    cash_flow_guidance_changed: bool = False
    major_order_change: bool = False
    production_delay: bool = False
    material_customer_change: bool = False
    operating_cash_flow_impact_known: bool = False
    margin_quality_review: bool = False
    financial_statement_basis_warning: bool = False
    fcf_impact_known: bool = False
    dilution_risk: bool = False
    debt_liquidity_risk: bool = False
    accounting_issue: bool = False
    regulatory_material: bool = False
    financial_report_filed: bool = False
    capex_impact_known: bool = False
    inventory_risk: bool = False
    receivables_risk: bool = False
    buyback_candidate: bool = False
    confirmed_buyback: bool = False


class EventFinancialMetrics(BaseModel):
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    operating_margin: float | None = None
    yoy_growth: float | None = None
    qoq_growth: float | None = None
    capex_amount: float | None = None
    financing_amount: float | None = None
    dilution_amount: float | None = None


class ThesisRelevance(BaseModel):
    requires_review: bool
    relevance_score: int = Field(ge=0, le=100)
    reason: str


class SourceDocument(BaseModel):
    source_type: str
    source: str
    title: str
    url: str
    published_date: date | None = None


class BackfillStatus(BaseModel):
    requested: bool = False
    executed: bool = False
    skipped: bool = False
    reason: str = "not_requested"
    provider: str | None = None
    years: int | None = None
    snapshot_count_before: int = 0
    snapshot_count_after: int = 0
    backfilled_count: int = 0
    report_count: int = 0
    warnings: list[str] = []


class ThesisEvent(BaseModel):
    date: date
    source: str
    provider: str
    title: str
    url: str
    event_type: EventType
    confirmed_facts: list[str]
    inferred_implications: list[str]
    unknowns: list[str]
    financial_metrics: EventFinancialMetrics = Field(default_factory=EventFinancialMetrics)
    financial_impact: FinancialImpact
    thesis_relevance: ThesisRelevance


class ThesisEventResponse(BaseModel):
    ticker: str
    company_name: str | None = None
    lookback_days: int
    backfill_status: BackfillStatus | None = None
    events: list[ThesisEvent]
