from datetime import date, datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    company_name: str | None = None
    date: date
    source: str
    provider: str = "unknown"
    title: str
    url: str
    raw_summary: str | None = None
    event_type: str = Field(index=True)
    keywords: str | None = None
    importance_candidate: str | None = None
    thesis_impact_candidate: str | None = None
    confirmed_facts: str = "[]"
    inferred_implications: str = "[]"
    unknowns: str = "[]"
    revenue: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    operating_margin: float | None = None
    yoy_growth: float | None = None
    qoq_growth: float | None = None
    capex_amount: float | None = None
    financing_amount: float | None = None
    dilution_amount: float | None = None
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
    requires_review: bool = False
    relevance_score: int = 0
    relevance_reason: str = ""
    issue_id: str | None = Field(default=None, index=True)
    corporate_action_id: str | None = Field(default=None, index=True)
    classification_override_reason: str | None = None
    financial_refresh_required: bool = False
    identity_validated: bool = False
    identity_status: str = "unvalidated"
    subject_company_id: str | None = None
    relevance_evidence: str = "[]"
    rejected_reason: str | None = None
    buyback_candidate: bool = False
    confirmed_buyback: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CanonicalIssue(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "issue_key"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    issue_key: str = Field(index=True)
    issue_type: str = Field(index=True)
    status: str = "opened"
    execution_status: str = "announced"
    economic_status: str = "open"
    opened_date: date
    updated_date: date
    latest_event_date: date
    event_ids: str = "[]"
    title: str
    pre_action_share_count: float | None = None
    new_shares: float | None = None
    post_action_share_count: float | None = None
    dilution_pct: float | None = None
    issue_price: float | None = None
    proceeds: float | None = None
    use_of_proceeds: str | None = None
    business_thesis_impact: str = "unknown"
    earnings_impact: str = "unknown"
    valuation_impact: str = "unknown"
    price_management_impact: str = "review"
    warnings: str = "[]"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceDocument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    source_type: str
    source: str
    title: str
    url: str
    published_date: date | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
