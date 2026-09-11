"""Generic pre-timing holder stance contract for bounded shadow experiments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


CONTRACT_VERSION = "fundamental-holder-stance-v1"
HOLDER_STANCE_PROMPT = (
    " Holder stance contract: HOLDABLE means no material confirmed fundamental reason "
    "to reconsider the holding. REVIEW means a material confirmed fundamental risk "
    "exists, but a critical severity, persistence, or reversibility question remains "
    "unresolved, so reducing exposure is not uniquely justified. REDUCE means confirmed "
    "fundamental downside is sufficiently severe or persistent that maintaining the same "
    "exposure is no longer justified even before price or timing overlays. SELL balance "
    "alone does not force REDUCE, and UNCHANGED business thesis alone does not force "
    "REVIEW. Price, technical, and supply evidence cannot create REDUCE."
)


class FundamentalHolderStance(StrEnum):
    HOLDABLE = "HOLDABLE"
    REVIEW = "REVIEW"
    REDUCE = "REDUCE"


@dataclass(frozen=True)
class FundamentalHolderRiskProfile:
    material_confirmed_fundamental_risk: bool
    confirmed_structural_impairment_or_severe_financial_stress: bool = False
    critical_severity_persistence_or_reversibility_unknown: bool = False
    material_counterevidence: bool = False
    fundamental_basis_available: bool = True
    price_or_technical_only: bool = False


@dataclass(frozen=True)
class FundamentalHolderDecision:
    contract: str
    stance: FundamentalHolderStance
    reason: str


def derive_fundamental_holder_stance(
    profile: FundamentalHolderRiskProfile,
) -> FundamentalHolderDecision:
    """Apply the generic holder boundary without scores or direction mapping."""

    if profile.price_or_technical_only and not profile.material_confirmed_fundamental_risk:
        return FundamentalHolderDecision(
            CONTRACT_VERSION,
            FundamentalHolderStance.HOLDABLE,
            "price_or_technical_only_cannot_create_fundamental_reduction",
        )
    if (
        not profile.fundamental_basis_available
        or not profile.material_confirmed_fundamental_risk
    ):
        return FundamentalHolderDecision(
            CONTRACT_VERSION,
            FundamentalHolderStance.HOLDABLE,
            "no_material_confirmed_fundamental_reconsideration_basis",
        )
    if profile.critical_severity_persistence_or_reversibility_unknown:
        return FundamentalHolderDecision(
            CONTRACT_VERSION,
            FundamentalHolderStance.REVIEW,
            "material_risk_confirmed_but_reduction_not_uniquely_justified",
        )
    if (
        profile.confirmed_structural_impairment_or_severe_financial_stress
        and not profile.material_counterevidence
    ):
        return FundamentalHolderDecision(
            CONTRACT_VERSION,
            FundamentalHolderStance.REDUCE,
            "confirmed_severe_or_structural_downside_overrides_holding_case",
        )
    return FundamentalHolderDecision(
        CONTRACT_VERSION,
        FundamentalHolderStance.REVIEW,
        "material_risk_requires_review_but_reduce_threshold_is_not_met",
    )
