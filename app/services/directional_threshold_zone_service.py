"""Deterministic shadow metadata for directional threshold proximity."""

from __future__ import annotations

from enum import StrEnum

from pydantic import model_validator

from app.services.cross_market_decision_engine_service import Decision, FrozenModel
from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
)
from app.services.structured_autonomy_shadow_service import HoldLean, derive_hold_lean


CONTRACT_VERSION = "directional-threshold-zone-v1"


class DirectionalThresholdZone(StrEnum):
    OUTSIDE_THRESHOLD_ZONE_POSITIVE = "OUTSIDE_THRESHOLD_ZONE_POSITIVE"
    POSITIVE_THRESHOLD_ZONE = "POSITIVE_THRESHOLD_ZONE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE_THRESHOLD_ZONE = "NEGATIVE_THRESHOLD_ZONE"
    OUTSIDE_THRESHOLD_ZONE_NEGATIVE = "OUTSIDE_THRESHOLD_ZONE_NEGATIVE"


class DirectionalThresholdZoneObservation(FrozenModel):
    contract: str = CONTRACT_VERSION
    overall_direction: Decision
    directional_balance: DirectionalBalance
    hold_lean: HoldLean
    decision_threshold_zone: DirectionalThresholdZone

    @model_validator(mode="after")
    def validate_raw_state(self) -> DirectionalThresholdZoneObservation:
        expected_direction = decision_from_directional_balance(self.directional_balance)
        if self.overall_direction != expected_direction:
            raise ValueError("threshold_zone_direction_balance_mismatch")
        expected_lean = derive_hold_lean(self.overall_direction, self.directional_balance)
        if self.hold_lean != expected_lean:
            raise ValueError("threshold_zone_hold_lean_mismatch")
        return self


def derive_directional_threshold_zone(
    *,
    overall_direction: Decision,
    directional_balance: DirectionalBalance,
    hold_lean: HoldLean,
) -> DirectionalThresholdZoneObservation:
    buy = directional_balance.buy
    if buy > 6:
        zone = DirectionalThresholdZone.OUTSIDE_THRESHOLD_ZONE_POSITIVE
    elif buy >= 5.5:
        zone = DirectionalThresholdZone.POSITIVE_THRESHOLD_ZONE
    elif buy == 5:
        zone = DirectionalThresholdZone.NEUTRAL
    elif buy >= 4:
        zone = DirectionalThresholdZone.NEGATIVE_THRESHOLD_ZONE
    else:
        zone = DirectionalThresholdZone.OUTSIDE_THRESHOLD_ZONE_NEGATIVE
    return DirectionalThresholdZoneObservation(
        overall_direction=overall_direction,
        directional_balance=directional_balance,
        hold_lean=hold_lean,
        decision_threshold_zone=zone,
    )
