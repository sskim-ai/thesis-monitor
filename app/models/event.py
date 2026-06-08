from datetime import date, datetime, timezone

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
    revenue_guidance_changed: bool = False
    margin_guidance_changed: bool = False
    margin_quality_review: bool = False
    financial_statement_basis_warning: bool = False
    fcf_impact_known: bool = False
    dilution_risk: bool = False
    capex_impact_known: bool = False
    inventory_risk: bool = False
    receivables_risk: bool = False
    requires_review: bool = False
    relevance_score: int = 0
    relevance_reason: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceDocument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    source_type: str
    source: str
    title: str
    url: str
    published_date: date | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
