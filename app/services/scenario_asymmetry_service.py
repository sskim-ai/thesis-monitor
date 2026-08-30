from __future__ import annotations

from enum import StrEnum

from pydantic import model_validator

from app.services.cross_market_decision_engine_service import EvidenceClaim, FrozenModel


CONTRACT_VERSION = "scenario-asymmetry-confirmation-cost-v2"


class ScenarioName(StrEnum):
    BEAR = "BEAR"
    BASE = "BASE"
    BULL = "BULL"


class Asymmetry(StrEnum):
    FAVORABLE = "FAVORABLE"
    BALANCED = "BALANCED"
    UNFAVORABLE = "UNFAVORABLE"
    UNKNOWN = "UNKNOWN"


class ConfirmationCost(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class PreconfirmationErrorCost(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class ScenarioInterpretation(FrozenModel):
    scenario: ScenarioName
    business_and_earnings: EvidenceClaim
    expectation_and_valuation: EvidenceClaim
    macro_market_conditions: EvidenceClaim


class ScenarioSet(FrozenModel):
    bear: ScenarioInterpretation
    base: ScenarioInterpretation
    bull: ScenarioInterpretation

    @model_validator(mode="after")
    def scenario_names_match_slots(self) -> ScenarioSet:
        if self.bear.scenario != ScenarioName.BEAR:
            raise ValueError("bear_scenario_slot_mismatch")
        if self.base.scenario != ScenarioName.BASE:
            raise ValueError("base_scenario_slot_mismatch")
        if self.bull.scenario != ScenarioName.BULL:
            raise ValueError("bull_scenario_slot_mismatch")
        return self


class AsymmetryAssessment(FrozenModel):
    asymmetry: Asymmetry
    basis: EvidenceClaim
    downside_permanence: EvidenceClaim
    upside_not_priced: EvidenceClaim


class ConfirmationCostAssessment(FrozenModel):
    cost: ConfirmationCost
    basis: EvidenceClaim
    likely_repricing_channel: EvidenceClaim


class PreconfirmationErrorCostAssessment(FrozenModel):
    cost: PreconfirmationErrorCost
    basis: EvidenceClaim
    capital_loss_channel: EvidenceClaim
