from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from app.services.cross_market_decision_engine_service import (
    Decision,
    EvidenceClaim,
    FrozenModel,
)


CONTRACT_VERSION = "three-axis-decision-v1"

NewBuyerStance = Literal["ATTRACTIVE", "WAIT", "AVOID"]
HolderStance = Literal["HOLDABLE", "REVIEW", "REDUCE"]


class NewBuyerDecisionAxis(FrozenModel):
    stance: NewBuyerStance
    reason: EvidenceClaim


class HolderDecisionAxis(FrozenModel):
    stance: HolderStance
    reason: EvidenceClaim


class ThreeAxisDecision(FrozenModel):
    contract: Literal["three-axis-decision-v1"] = CONTRACT_VERSION
    overall_direction: Decision
    new_buyer: NewBuyerDecisionAxis
    holder: HolderDecisionAxis

    @model_validator(mode="after")
    def require_independent_reasons(self) -> ThreeAxisDecision:
        if self.new_buyer.reason.text.strip() == self.holder.reason.text.strip():
            raise ValueError("three_axis_reason_reuse")
        return self


NEW_BUYER_LABELS: dict[NewBuyerStance, str] = {
    "ATTRACTIVE": "신규 진입 매력 있음",
    "WAIT": "확인 대기",
    "AVOID": "신규 진입 보류",
}

HOLDER_LABELS: dict[HolderStance, str] = {
    "HOLDABLE": "보유 유지 가능",
    "REVIEW": "보유 근거 재검토",
    "REDUCE": "노출 축소 검토",
}


def render_three_axis_header(decision: ThreeAxisDecision) -> tuple[str, ...]:
    """Render the supplied axes without deriving one stance from another."""

    return (
        f"종합 방향: {decision.overall_direction}",
        (
            "신규 관찰자: "
            f"{NEW_BUYER_LABELS[decision.new_buyer.stance]} "
            f"({decision.new_buyer.stance})"
        ),
        f"보유자: {HOLDER_LABELS[decision.holder.stance]} ({decision.holder.stance})",
    )
