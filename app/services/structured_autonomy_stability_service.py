from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

from app.services.structured_autonomy_shadow_service import (
    StructuredAutonomyCandidate,
    derive_hold_lean,
    hold_lean_flip,
)


CONTRACT_VERSION = "structured-autonomy-same-evidence-stability-v1"


class StabilityClass(StrEnum):
    STABLE = "STABLE"
    BOUNDARY_UNCERTAINTY = "BOUNDARY_UNCERTAINTY"
    UNSTABLE = "UNSTABLE"


def _price_scenario(candidate: StructuredAutonomyCandidate) -> dict[str, object]:
    buyer = candidate.new_buyer_view
    holder = candidate.holder_view
    return {
        "pullback": [buyer.pullback_entry_zone_low, buyer.pullback_entry_zone_high],
        "confirmation": buyer.breakout_confirmation_level,
        "trim": [holder.upside_trim_zone_low, holder.upside_trim_zone_high],
        "downside_review": holder.downside_review_level,
    }


def classify_same_evidence_runs(
    candidates: Sequence[StructuredAutonomyCandidate],
) -> dict[str, object]:
    if len(candidates) != 3:
        raise ValueError("three_same_evidence_candidates_required")
    tickers = {candidate.ticker for candidate in candidates}
    if len(tickers) != 1:
        raise ValueError("same_ticker_required")

    labels = [candidate.decision for candidate in candidates]
    buys = [candidate.directional_balance.buy for candidate in candidates]
    balances = [candidate.directional_balance.model_dump(mode="json") for candidate in candidates]
    leans = [derive_hold_lean(candidate.decision, candidate.directional_balance) for candidate in candidates]
    confidence = [candidate.decision_confidence for candidate in candidates]
    new_buyer = [candidate.new_buyer_view.stance for candidate in candidates]
    holder = [candidate.holder_view.stance for candidate in candidates]
    entry_modes = [candidate.new_buyer_view.preferred_entry_mode for candidate in candidates]
    price_scenarios = [_price_scenario(candidate) for candidate in candidates]

    spread = max(buys) - min(buys)
    buy_sell_reversal = "BUY" in labels and "SELL" in labels
    lean_flip = any(
        hold_lean_flip(left, right)
        for index, left in enumerate(leans)
        for right in leans[index + 1 :]
    )
    new_buyer_extreme = "ATTRACTIVE" in new_buyer and "AVOID" in new_buyer
    holder_extreme = "HOLDABLE" in holder and "REDUCE" in holder
    action_context_changed = len(set(new_buyer)) > 1 or len(set(holder)) > 1
    entry_mode_changed = len(set(entry_modes)) > 1
    price_selection_variance = any(row != price_scenarios[0] for row in price_scenarios[1:])

    reasons: list[str] = []
    if buy_sell_reversal:
        reasons.append("BUY_SELL_REVERSAL")
    if lean_flip:
        reasons.append("BUY_LEAN_SELL_LEAN_FLIP")
    if new_buyer_extreme:
        reasons.append("ATTRACTIVE_AVOID_REVERSAL")
    if holder_extreme:
        reasons.append("HOLDABLE_REDUCE_REVERSAL")
    if spread >= 1.5:
        reasons.append("BALANCE_SPREAD_AT_LEAST_1_5")

    if reasons:
        classification = StabilityClass.UNSTABLE
    elif (
        spread > 0.5
        or len(set(labels)) > 1
        or len(set(leans)) > 1
        or action_context_changed
        or entry_mode_changed
    ):
        classification = StabilityClass.BOUNDARY_UNCERTAINTY
        if spread > 0.5:
            reasons.append("BALANCE_BOUNDARY_VARIANCE")
        if len(set(labels)) > 1:
            reasons.append("LABEL_THRESHOLD_VARIANCE")
        if len(set(leans)) > 1:
            reasons.append("HOLD_LEAN_BOUNDARY_VARIANCE")
        if action_context_changed:
            reasons.append("ACTION_CONTEXT_VARIANCE")
        if entry_mode_changed:
            reasons.append("ENTRY_MODE_VARIANCE")
    else:
        classification = StabilityClass.STABLE
    if price_selection_variance:
        reasons.append("VALID_SELECTION_VARIANCE")

    return {
        "contract": CONTRACT_VERSION,
        "ticker": candidates[0].ticker,
        "classification": classification,
        "label_sequence": labels,
        "balance_sequence": balances,
        "max_balance_distance": spread,
        "lean_sequence": leans,
        "confidence_sequence": confidence,
        "new_buyer_sequence": new_buyer,
        "holder_sequence": holder,
        "entry_mode_sequence": entry_modes,
        "price_scenarios": price_scenarios,
        "buy_sell_reversal": buy_sell_reversal,
        "unexplained_hold_lean_flip": lean_flip,
        "action_context_changed": action_context_changed,
        "price_selection_variance": price_selection_variance,
        "reasons": reasons,
    }


def stability_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts = {classification.value: 0 for classification in StabilityClass}
    for row in rows:
        counts[str(row["classification"])] += 1
    return {
        "contract": CONTRACT_VERSION,
        "counts": counts,
        "buy_sell_reversal_count": sum(bool(row["buy_sell_reversal"]) for row in rows),
        "unexplained_hold_lean_flip_count": sum(
            bool(row["unexplained_hold_lean_flip"]) for row in rows
        ),
        "action_context_variance_count": sum(
            bool(row["action_context_changed"]) for row in rows
        ),
        "valid_selection_variance_count": sum(
            bool(row["price_selection_variance"]) for row in rows
        ),
    }
