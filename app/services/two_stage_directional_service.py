"""Internal two-stage Directional contract with immutable core composition."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import (
    Confidence,
    Decision,
    FrozenModel,
)
from app.services.direction_timing_ownership_service import (
    CoreHolderView,
    CoreNewBuyerView,
    DirectionalClaim,
    DirectionalCoreCandidate,
    DirectionalSellDriver,
    DirectionalUnknown,
    canonical_sha256,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
)
from app.services.structured_autonomy_shadow_service import (
    BusinessThesisChange,
    HoldLean,
    derive_hold_lean,
)


CONTRACT_VERSION = "two-stage-directional-v1"
CORE_JUDGMENT_OUTPUT_CONTRACT = "directional-core-judgment-output-v1"
FUNDAMENTAL_STANCE_OUTPUT_CONTRACT = "fundamental-stance-output-v1"
COMPOSITION_CONTRACT = "two-stage-directional-composition-v1"
NEW_BUYER_STANCE_PROMPT = (
    "New-buyer stance contract: ATTRACTIVE requires a sufficiently supported issuer-level "
    "fundamental case for initiating exposure before price or timing overlays, without a "
    "material unresolved confirmation, durability, source-quality, or valuation constraint "
    "that makes entry premature. WAIT means the fundamental case remains investable but a "
    "material confirmation, durability, source-quality, or valuation question should be "
    "resolved before initiating exposure. AVOID means confirmed fundamental downside makes "
    "new exposure unjustified before price or timing overlays. BUY/HOLD/SELL and a directional "
    "balance do not mechanically determine this stance."
)


class DirectionalCoreJudgment(FrozenModel):
    """Stage 1 output, deliberately excluding all writable stance fields."""

    ticker: str
    overall_direction: Decision
    directional_balance: DirectionalBalance
    hold_lean: HoldLean
    directional_confidence: Confidence
    business_thesis_change: BusinessThesisChange
    business_thesis_context: DirectionalClaim
    earnings_estimate_context: DirectionalClaim
    market_expectation_context: DirectionalClaim
    valuation_context: DirectionalClaim
    risk_context: DirectionalClaim
    sector_interpretation: DirectionalClaim
    buy_drivers: tuple[DirectionalClaim, ...] = Field(min_length=1, max_length=4)
    sell_drivers: tuple[DirectionalSellDriver, ...] = Field(min_length=1, max_length=4)
    dominant_evidence: DirectionalClaim
    uncertainty_limit: DirectionalClaim
    core_investment_judgment: DirectionalClaim
    unknown_treatments: tuple[DirectionalUnknown, ...] = Field(min_length=1, max_length=4)
    material_directional_anchor_basis: tuple[str, ...] = Field(max_length=6)
    business_reevaluation_up: tuple[DirectionalClaim, ...] = Field(
        min_length=1, max_length=3
    )
    business_reevaluation_down: tuple[DirectionalClaim, ...] = Field(
        min_length=1, max_length=3
    )

    @model_validator(mode="after")
    def validate_directional_identity(self) -> DirectionalCoreJudgment:
        if decision_from_directional_balance(self.directional_balance) != self.overall_direction:
            raise ValueError("directional_core_decision_balance_mismatch")
        expected = derive_hold_lean(self.overall_direction, self.directional_balance)
        if self.hold_lean != expected:
            raise ValueError("directional_core_hold_lean_mismatch")
        return self


class DirectionalCoreJudgmentBatch(FrozenModel):
    contract: Literal["directional-core-judgment-output-v1"] = (
        CORE_JUDGMENT_OUTPUT_CONTRACT
    )
    packet_id: str
    candidates: tuple[DirectionalCoreJudgment, ...] = Field(min_length=1, max_length=4)


class FundamentalStanceCandidate(FrozenModel):
    """Stage 2 output, deliberately excluding all writable core fields."""

    ticker: str
    fundamental_new_buyer: CoreNewBuyerView
    fundamental_holder: CoreHolderView


class FundamentalStanceBatch(FrozenModel):
    contract: Literal["fundamental-stance-output-v1"] = FUNDAMENTAL_STANCE_OUTPUT_CONTRACT
    packet_id: str
    candidates: tuple[FundamentalStanceCandidate, ...] = Field(min_length=1, max_length=4)


class TwoStageDirectionalComposition(FrozenModel):
    contract: str = COMPOSITION_CONTRACT
    core: DirectionalCoreJudgment
    stance: FundamentalStanceCandidate
    candidate: DirectionalCoreCandidate
    core_snapshot_sha256: str
    post_compose_core_sha256: str


def extract_core_judgment(candidate: DirectionalCoreCandidate) -> DirectionalCoreJudgment:
    payload = candidate.model_dump(mode="json")
    return DirectionalCoreJudgment.model_validate(
        {name: payload[name] for name in DirectionalCoreJudgment.model_fields}
    )


def core_snapshot_sha256(core: DirectionalCoreJudgment) -> str:
    return canonical_sha256(core.model_dump(mode="json"))


def stage2_forbidden_core_fields(value: Mapping[str, object]) -> tuple[str, ...]:
    allowed = set(FundamentalStanceCandidate.model_fields)
    return tuple(sorted(set(value) - allowed))


def compose_directional_core(
    core: DirectionalCoreJudgment,
    stance: FundamentalStanceCandidate,
) -> TwoStageDirectionalComposition:
    if core.ticker != stance.ticker:
        raise ValueError("cross_subject_core_stance_composition")
    before = core_snapshot_sha256(core)
    payload = core.model_dump(mode="json")
    payload.update(
        fundamental_new_buyer=stance.fundamental_new_buyer.model_dump(mode="json"),
        fundamental_holder=stance.fundamental_holder.model_dump(mode="json"),
    )
    candidate = DirectionalCoreCandidate.model_validate(payload)
    after = core_snapshot_sha256(extract_core_judgment(candidate))
    if before != after:
        raise ValueError("directional_core_mutated_during_stance_composition")
    return TwoStageDirectionalComposition(
        core=core,
        stance=stance,
        candidate=candidate,
        core_snapshot_sha256=before,
        post_compose_core_sha256=after,
    )
