from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ThesisAssessmentValue = Literal[
    "strengthened",
    "weakened",
    "mixed",
    "no_material_change",
    "needs_review",
    "invalidation_candidate",
    "invalidated",
]
EarningsViewValue = Literal["up", "down", "mixed", "unchanged", "unknown"]
ValuationViewValue = Literal["expansion", "compression", "mixed", "neutral", "unknown"]


class AIInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    fact_ids: list[str] = Field(default_factory=list)


class AINumericClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str
    field_path: str
    value: float
    unit: str
    semantic_type: str
    text_ref: str
    usage: str


class AIReasoningSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    fact_ids: list[str] = Field(default_factory=list)


class AIPricePositioningSection(AIReasoningSection):
    new_observer_view: str
    holder_view: str


class AIMarketTransmission(AIInterpretation):
    portfolio_group: str = Field(min_length=1)


class AIMarketReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts_used: list[str] = Field(default_factory=list)
    frameworks_used: list[str] = Field(default_factory=list)
    core_judgment: AIReasoningSection
    important_changes: list[AIInterpretation] = Field(default_factory=list)
    market_context: AIReasoningSection
    market_assumptions: AIReasoningSection
    portfolio_transmission: list[AIMarketTransmission] = Field(default_factory=list)
    next_checks: list[AIInterpretation] = Field(default_factory=list)
    numeric_claims: list[AINumericClaim] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class AIStockReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    thesis_version: int = Field(ge=1)
    ai_thesis_assessment: ThesisAssessmentValue
    earnings_estimate_view: EarningsViewValue
    valuation_view: ValuationViewValue
    facts_used: list[str] = Field(default_factory=list)
    frameworks_used: list[str] = Field(default_factory=list)
    core_judgment: AIReasoningSection
    business_earnings: AIReasoningSection
    price_positioning: AIPricePositioningSection
    supply_analysis: AIReasoningSection
    valuation_analysis: AIReasoningSection
    numeric_claims: list[AINumericClaim] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    priority_watch: list[str] = Field(default_factory=list)
    next_checks: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class AIDailyReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["4"]
    packet_id: str
    claim_id: str
    analysis_policy_version: str
    knowledge_version: str
    knowledge_sha256: str
    chart_knowledge_version: str
    chart_knowledge_sha256: str
    market: Literal["us", "kr"]
    assessment_date: str
    market_review: AIMarketReview
    stock_reviews: list[AIStockReview]
