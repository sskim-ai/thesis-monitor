"""Decision-material stability views for repeated Directional Core outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

from app.services.structured_autonomy_shadow_service import hold_lean_flip


CONTRACT_VERSION = "directional-decision-material-stability-v1"
LEGACY_VIEW_VERSION = "directional-core-legacy-formal-stability-view-v1"


class DecisionMaterialStabilityClass(StrEnum):
    DECISION_STABLE = "DECISION_STABLE"
    CALIBRATION_VARIANCE_SAME_DIRECTION = "CALIBRATION_VARIANCE_SAME_DIRECTION"
    PRIMARY_DIRECTION_UNSTABLE = "PRIMARY_DIRECTION_UNSTABLE"
    BUSINESS_DELTA_UNSTABLE = "BUSINESS_DELTA_UNSTABLE"
    NEW_BUYER_STANCE_UNSTABLE = "NEW_BUYER_STANCE_UNSTABLE"
    HOLDER_STANCE_UNSTABLE = "HOLDER_STANCE_UNSTABLE"
    MULTI_FIELD_MATERIAL_UNSTABLE = "MULTI_FIELD_MATERIAL_UNSTABLE"


class LegacyFormalStabilityClass(StrEnum):
    STABLE = "STABLE"
    BOUNDARY_UNCERTAINTY = "BOUNDARY_UNCERTAINTY"
    UNSTABLE = "UNSTABLE"


def _payload(value: object) -> Mapping[str, object]:
    payload = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    if not isinstance(payload, Mapping):
        raise TypeError("directional_core_mapping_required")
    return payload


def _stance(core: Mapping[str, object], field: str) -> str:
    value = core[field]
    if not isinstance(value, Mapping):
        raise TypeError(f"{field}_mapping_required")
    return str(value["stance"])


def _validated_cores(values: Sequence[object]) -> list[Mapping[str, object]]:
    if len(values) != 3:
        raise ValueError("three_directional_core_outputs_required")
    cores = [_payload(value) for value in values]
    tickers = {str(core["ticker"]) for core in cores}
    if len(tickers) != 1:
        raise ValueError("same_ticker_required")
    return cores


def classify_directional_core_legacy_stability(
    values: Sequence[object],
) -> dict[str, object]:
    """Project the existing frozen formal semantics onto core-only outputs."""

    cores = _validated_cores(values)
    labels = [str(core["overall_direction"]) for core in cores]
    buys = [float(core["directional_balance"]["buy"]) for core in cores]
    leans = [str(core["hold_lean"]) for core in cores]
    buyers = [_stance(core, "fundamental_new_buyer") for core in cores]
    holders = [_stance(core, "fundamental_holder") for core in cores]
    spread = max(buys) - min(buys)
    reasons: list[str] = []
    if "BUY" in labels and "SELL" in labels:
        reasons.append("BUY_SELL_REVERSAL")
    if any(
        hold_lean_flip(left, right)
        for index, left in enumerate(leans)
        for right in leans[index + 1 :]
    ):
        reasons.append("BUY_LEAN_SELL_LEAN_FLIP")
    if "ATTRACTIVE" in buyers and "AVOID" in buyers:
        reasons.append("ATTRACTIVE_AVOID_REVERSAL")
    if "HOLDABLE" in holders and "REDUCE" in holders:
        reasons.append("HOLDABLE_REDUCE_REVERSAL")
    if spread >= 1.5:
        reasons.append("BALANCE_SPREAD_AT_LEAST_1_5")
    if reasons:
        classification = LegacyFormalStabilityClass.UNSTABLE
    elif (
        spread > 0.5
        or len(set(labels)) > 1
        or len(set(leans)) > 1
        or len(set(buyers)) > 1
        or len(set(holders)) > 1
    ):
        classification = LegacyFormalStabilityClass.BOUNDARY_UNCERTAINTY
        if spread > 0.5:
            reasons.append("BALANCE_BOUNDARY_VARIANCE")
        if len(set(labels)) > 1:
            reasons.append("LABEL_THRESHOLD_VARIANCE")
        if len(set(leans)) > 1:
            reasons.append("HOLD_LEAN_BOUNDARY_VARIANCE")
        if len(set(buyers)) > 1 or len(set(holders)) > 1:
            reasons.append("ACTION_CONTEXT_VARIANCE")
    else:
        classification = LegacyFormalStabilityClass.STABLE
    return {
        "contract": LEGACY_VIEW_VERSION,
        "ticker": cores[0]["ticker"],
        "classification": classification.value,
        "reasons": reasons,
        "label_sequence": labels,
        "buy_balance_sequence": buys,
        "hold_lean_sequence": leans,
        "new_buyer_sequence": buyers,
        "holder_sequence": holders,
    }


def classify_directional_core_decision_material_stability(
    values: Sequence[object],
) -> dict[str, object]:
    """Separate primary action stability from calibration and confidence variance."""

    cores = _validated_cores(values)
    directions = [str(core["overall_direction"]) for core in cores]
    deltas = [str(core["business_thesis_change"]) for core in cores]
    buyers = [_stance(core, "fundamental_new_buyer") for core in cores]
    holders = [_stance(core, "fundamental_holder") for core in cores]
    confidences = [str(core["directional_confidence"]) for core in cores]
    raw = [
        (
            core["overall_direction"],
            float(core["directional_balance"]["buy"]),
            float(core["directional_balance"]["sell"]),
            core["hold_lean"],
        )
        for core in cores
    ]
    material_variance = []
    if len(set(directions)) > 1:
        material_variance.append("overall_direction")
    if len(set(deltas)) > 1:
        material_variance.append("business_thesis_change")
    if len(set(buyers)) > 1:
        material_variance.append("fundamental_new_buyer.stance")
    if len(set(holders)) > 1:
        material_variance.append("fundamental_holder.stance")

    if len(material_variance) > 1:
        classification = DecisionMaterialStabilityClass.MULTI_FIELD_MATERIAL_UNSTABLE
    elif material_variance == ["overall_direction"]:
        classification = DecisionMaterialStabilityClass.PRIMARY_DIRECTION_UNSTABLE
    elif material_variance == ["business_thesis_change"]:
        classification = DecisionMaterialStabilityClass.BUSINESS_DELTA_UNSTABLE
    elif material_variance == ["fundamental_new_buyer.stance"]:
        classification = DecisionMaterialStabilityClass.NEW_BUYER_STANCE_UNSTABLE
    elif material_variance == ["fundamental_holder.stance"]:
        classification = DecisionMaterialStabilityClass.HOLDER_STANCE_UNSTABLE
    elif len(set(raw)) > 1:
        spread = max(value[1] for value in raw) - min(value[1] for value in raw)
        classification = (
            DecisionMaterialStabilityClass.CALIBRATION_VARIANCE_SAME_DIRECTION
            if spread <= 0.5
            else DecisionMaterialStabilityClass.MULTI_FIELD_MATERIAL_UNSTABLE
        )
    else:
        classification = DecisionMaterialStabilityClass.DECISION_STABLE

    blocking = classification not in {
        DecisionMaterialStabilityClass.DECISION_STABLE,
        DecisionMaterialStabilityClass.CALIBRATION_VARIANCE_SAME_DIRECTION,
    }
    return {
        "contract": CONTRACT_VERSION,
        "ticker": cores[0]["ticker"],
        "classification": classification.value,
        "readiness_blocking": blocking,
        "material_variance_fields": material_variance,
        "overall_direction_values": directions,
        "business_delta_values": deltas,
        "new_buyer_values": buyers,
        "holder_values": holders,
        "directional_confidence_values": confidences,
        "exact_raw_state_values": [
            {
                "overall_direction": value[0],
                "buy": value[1],
                "sell": value[2],
                "hold_lean": value[3],
            }
            for value in raw
        ],
        "exact_raw_state_variance": len(set(raw)) > 1,
        "confidence_variance_advisory": len(set(confidences)) > 1,
    }
