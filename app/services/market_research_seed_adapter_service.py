from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


RESEARCH_SEED_ADAPTER_VERSION = "market-research-seed-adapter-v1"
RESEARCH_CONNECTOR_AUDIT_VERSION = "production-research-connector-boundary-v1"


class MarketResearchSeedAdapter(BaseModel):
    contract_version: Literal["market-research-seed-adapter-v1"] = (
        RESEARCH_SEED_ADAPTER_VERSION
    )
    market: Literal["KR", "US"]
    seed_vocabulary: list[str]
    primary_source_hints: list[str]
    common_semantics: list[str] = Field(
        default_factory=lambda: [
            "source_validation",
            "entity_validation",
            "time_validation",
            "competing_hypotheses",
            "negative_evidence",
            "event_attribution",
        ]
    )
    conclusions: list[str] = Field(default_factory=list)
    ticker_rules: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_hints(self) -> "MarketResearchSeedAdapter":
        if self.conclusions or self.ticker_rules:
            raise ValueError("research seeds cannot contain conclusions or ticker rules")
        return self


class ProductionResearchConnectorAudit(BaseModel):
    contract_version: Literal["production-research-connector-boundary-v1"] = (
        RESEARCH_CONNECTOR_AUDIT_VERSION
    )
    status: Literal["AVAILABLE", "NOT_AVAILABLE", "AMBIGUOUS"]
    free: bool
    source_refs_preserved: bool
    bounded_query_budget: bool
    non_interactive: bool
    production_timeout: bool
    secret_safe: bool
    reasons: list[str]


def research_seed_adapter(market: str) -> MarketResearchSeedAdapter:
    normalized = market.strip().upper()
    if normalized == "KR":
        return MarketResearchSeedAdapter(
            market="KR",
            seed_vocabulary=[
                "급락/급등",
                "공시",
                "주주환원/자사주/소각",
                "유상증자",
                "외국인/기관 수급",
                "코스피/코스닥/업종",
                "거버넌스",
                "정책/규제",
            ],
            primary_source_hints=["OpenDART", "KRX", "company_ir", "regulator"],
        )
    if normalized == "US":
        return MarketResearchSeedAdapter(
            market="US",
            seed_vocabulary=[
                "shares fall/rise",
                "earnings/guidance",
                "SEC filing",
                "premarket/after hours",
                "sector/peer",
                "Treasury yields/macro release",
                "analyst day",
                "regulatory",
            ],
            primary_source_hints=[
                "SEC",
                "company_ir",
                "Federal_Reserve",
                "US_Treasury",
                "BLS",
                "BEA",
                "regulator_or_exchange",
            ],
        )
    raise ValueError(f"unsupported market: {market}")


def audit_production_research_connector(
    capabilities: dict[str, object] | None = None,
) -> ProductionResearchConnectorAudit:
    values = capabilities or {}
    required = {
        "free": values.get("free") is True,
        "source_refs_preserved": values.get("source_refs_preserved") is True,
        "bounded_query_budget": values.get("bounded_query_budget") is True,
        "non_interactive": values.get("non_interactive") is True,
        "production_timeout": values.get("production_timeout") is True,
        "secret_safe": values.get("secret_safe") is True,
    }
    if not capabilities:
        status = "NOT_AVAILABLE"
        reasons = ["no production research/search connector is imported or configured"]
    elif all(required.values()):
        status = "AVAILABLE"
        reasons = []
    else:
        status = "AMBIGUOUS"
        reasons = [name for name, passed in required.items() if not passed]
    return ProductionResearchConnectorAudit(
        status=status,
        reasons=reasons,
        **required,
    )
