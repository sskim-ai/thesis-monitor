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


class AIMarketReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts_used: list[str] = Field(default_factory=list)
    interpretation: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    summary: str


class AIStockReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    thesis_version: int = Field(ge=1)
    ai_thesis_assessment: ThesisAssessmentValue
    earnings_estimate_view: EarningsViewValue
    valuation_view: ValuationViewValue
    facts_used: list[str] = Field(default_factory=list)
    interpretation: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    summary: str
    holder_view: str
    new_buyer_view: str
    next_checks: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class AIDailyReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"]
    packet_id: str
    analysis_policy_version: str
    market: Literal["us", "kr"]
    assessment_date: str
    market_review: AIMarketReview
    stock_reviews: list[AIStockReview]
