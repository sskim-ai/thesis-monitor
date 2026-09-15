from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import Decision, FrozenModel
from app.services.direction_timing_ownership_service import DirectionalCoreCandidate
from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
)
from app.services.structured_autonomy_shadow_service import HoldLean, derive_hold_lean


BOUNDARY_OUTPUT_CONTRACT = "directional-core-boundary-output-v1"
BOUNDARY_RESOLUTION_CONTRACT = "directional-boundary-resolution-v1"
NON_HOLD_CANONICAL = "NOT_HOLD"


class AdjacentBoundaryStatus(StrEnum):
    NONE = "NONE"
    ADJACENT_BUCKETS_REASONABLE = "ADJACENT_BUCKETS_REASONABLE"


class AdjacentDirectionalBoundary(FrozenModel):
    status: AdjacentBoundaryStatus = AdjacentBoundaryStatus.NONE
    less_directional_balance: DirectionalBalance | None = None
    more_directional_balance: DirectionalBalance | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=6)

    @model_validator(mode="after")
    def validate_shape(self) -> AdjacentDirectionalBoundary:
        if self.status == AdjacentBoundaryStatus.NONE:
            if (
                self.less_directional_balance is not None
                or self.more_directional_balance is not None
                or self.reason is not None
                or self.evidence_refs
            ):
                raise ValueError("inactive_boundary_metadata_forbidden")
            return self
        if self.less_directional_balance is None:
            raise ValueError("active_boundary_less_directional_balance_required")
        if self.more_directional_balance is None:
            raise ValueError("active_boundary_more_directional_balance_required")
        if self.reason is None:
            raise ValueError("active_boundary_reason_required")
        if not self.evidence_refs:
            raise ValueError("active_boundary_evidence_refs_required")
        return self


class BoundaryAwareDirectionalCoreCandidate(DirectionalCoreCandidate):
    adjacent_boundary: AdjacentDirectionalBoundary = Field(
        default_factory=AdjacentDirectionalBoundary
    )


class BoundaryAwareDirectionalCoreBatch(FrozenModel):
    contract: Literal["directional-core-boundary-output-v1"] = BOUNDARY_OUTPUT_CONTRACT
    packet_id: str
    candidates: tuple[BoundaryAwareDirectionalCoreCandidate, ...] = Field(
        min_length=1, max_length=4
    )


class DirectionalCoreState(FrozenModel):
    overall_direction: Decision
    directional_balance: DirectionalBalance
    hold_lean: HoldLean


class DirectionalBoundaryResolution(FrozenModel):
    contract: str = BOUNDARY_RESOLUTION_CONTRACT
    status: Literal["UNCHANGED", "RESOLVED_TOWARD_5_0"]
    raw_state: DirectionalCoreState
    resolved_state: DirectionalCoreState
    boundary: AdjacentDirectionalBoundary
    resolution_rule: Literal["NONE", "LESS_DIRECTIONAL_ADJACENT_TOWARD_5_0"]
    selected_evidence_refs: tuple[str, ...]


def normalize_boundary_lean(direction: object, lean: object) -> str:
    if str(direction).upper() != "HOLD":
        return NON_HOLD_CANONICAL
    return str(lean).upper()


def _state(candidate: DirectionalCoreCandidate) -> DirectionalCoreState:
    return DirectionalCoreState(
        overall_direction=candidate.overall_direction,
        directional_balance=candidate.directional_balance,
        hold_lean=candidate.hold_lean,
    )


def _distance_from_neutral(balance: DirectionalBalance) -> Decimal:
    return abs(Decimal(str(balance.buy)) - Decimal("5"))


def _validate_adjacent_pair(
    less: DirectionalBalance,
    more: DirectionalBalance,
) -> None:
    less_buy = Decimal(str(less.buy))
    more_buy = Decimal(str(more.buy))
    if less_buy == more_buy:
        raise ValueError("boundary_identical_balance")
    if abs(less_buy - more_buy) != Decimal("0.5"):
        raise ValueError("boundary_non_adjacent_balance")
    if _distance_from_neutral(less) >= _distance_from_neutral(more):
        raise ValueError("boundary_endpoint_order_not_toward_5_0")
    less_polarity = less_buy - Decimal("5")
    more_polarity = more_buy - Decimal("5")
    if less_polarity * more_polarity < 0:
        raise ValueError("boundary_polarity_contradiction")


def resolve_adjacent_boundary(
    candidate: BoundaryAwareDirectionalCoreCandidate,
    *,
    allowed_ref_ids: Sequence[str],
) -> tuple[DirectionalCoreCandidate, DirectionalBoundaryResolution]:
    raw_state = _state(candidate)
    boundary = candidate.adjacent_boundary
    if boundary.status == AdjacentBoundaryStatus.NONE:
        base = DirectionalCoreCandidate.model_validate(
            candidate.model_dump(mode="python", exclude={"adjacent_boundary"})
        )
        return base, DirectionalBoundaryResolution(
            status="UNCHANGED",
            raw_state=raw_state,
            resolved_state=raw_state,
            boundary=boundary,
            resolution_rule="NONE",
            selected_evidence_refs=(),
        )

    invalid_refs = sorted(set(boundary.evidence_refs) - set(allowed_ref_ids))
    if invalid_refs:
        raise ValueError(f"boundary_invalid_evidence_refs:{','.join(invalid_refs)}")
    if boundary.less_directional_balance is None:
        raise ValueError("active_boundary_less_directional_balance_required")
    if boundary.more_directional_balance is None:
        raise ValueError("active_boundary_more_directional_balance_required")
    _validate_adjacent_pair(
        boundary.less_directional_balance,
        boundary.more_directional_balance,
    )
    raw_pair = (candidate.directional_balance.buy, candidate.directional_balance.sell)
    declared_pairs = {
        (
            boundary.less_directional_balance.buy,
            boundary.less_directional_balance.sell,
        ),
        (
            boundary.more_directional_balance.buy,
            boundary.more_directional_balance.sell,
        ),
    }
    if raw_pair not in declared_pairs:
        raise ValueError("raw_balance_not_in_declared_boundary")

    resolved_balance = boundary.less_directional_balance
    resolved_direction = decision_from_directional_balance(resolved_balance)
    resolved_lean = derive_hold_lean(resolved_direction, resolved_balance)
    resolved_payload = candidate.model_dump(mode="python", exclude={"adjacent_boundary"})
    resolved_payload.update(
        {
            "overall_direction": resolved_direction,
            "directional_balance": resolved_balance,
            "hold_lean": resolved_lean,
        }
    )
    resolved = DirectionalCoreCandidate.model_validate(resolved_payload)
    resolved_state = _state(resolved)
    return resolved, DirectionalBoundaryResolution(
        status="RESOLVED_TOWARD_5_0",
        raw_state=raw_state,
        resolved_state=resolved_state,
        boundary=boundary,
        resolution_rule="LESS_DIRECTIONAL_ADJACENT_TOWARD_5_0",
        selected_evidence_refs=boundary.evidence_refs,
    )
