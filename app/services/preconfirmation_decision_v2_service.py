from __future__ import annotations

import re
from collections import Counter
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import (
    Confidence,
    Decision,
    DecisionEvidencePacket,
    EvidenceCategory,
    EvidenceClaim,
    FrozenModel,
    Timing,
)
from app.services.evidence_maturity_pricing_service import (
    DriverEvidenceMaturity,
    DriverEvidenceMaturityV2,
    EvidenceMaturity,
    MarketExpectationAssessment,
    MaturityProvenanceStatus,
    OverallMaturityAssessment,
    PricingRequirement,
    PricingRequirementAssessment,
    concrete_evidence_date,
    decisive_maturities,
    project_maturity_provenance,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_language_errors,
    directional_balance_matches_decision,
    render_directional_balance,
)
from app.services.scenario_asymmetry_service import (
    Asymmetry,
    AsymmetryAssessment,
    ConfirmationCostAssessment,
    PreconfirmationErrorCostAssessment,
    ScenarioSet,
)
from app.services.logical_condition_service import (
    logical_condition_errors,
    logical_expression_is_composite,
)
from app.services.three_axis_decision_service import (
    HolderDecisionAxis,
    NewBuyerDecisionAxis,
    ThreeAxisDecision,
)


CONTRACT_VERSION = "preconfirmation-asymmetry-decision-engine-v2"
OUTPUT_CONTRACT = "preconfirmation-asymmetry-decision-output-v2"
VALIDATOR_CONTRACT = "preconfirmation-asymmetry-validator-v2"
RENDERER_CONTRACT = "preconfirmation-asymmetry-shadow-renderer-v2"

PRECONFIRMATION_BUY_STAGE2_PROMPT_RULE = """\
pre_confirmation_buy is an analytical BUY lifecycle flag, not a new-buyer entry stance. For every
candidate with decision=BUY and at least one decisive driver whose maturity is EARLY or PARTIAL,
set pre_confirmation_buy=true and provide all six preconfirmation_buy_explanation claims. Such a
candidate is valid only when asymmetry is FAVORABLE and factual_safety_state is not BLOCKED; if
the evidence does not support those conditions, do not force or rewrite the decision, maturity, or
asymmetry merely to satisfy the flag. For HOLD or SELL, and for BUY with no decisive EARLY or
PARTIAL driver, set pre_confirmation_buy=false and preconfirmation_buy_explanation=null.
pre_confirmation_buy=true may coexist with new_buyer_axis=WAIT, holder_axis=HOLDABLE, and
timing=UNFAVORABLE. Never derive any of those three fields mechanically from another. A configured
price confirmation is an entry/price check and must never set or clear pre_confirmation_buy."""


class FactualSafetyState(StrEnum):
    PASS = "PASS"
    LIMITED = "LIMITED"
    BLOCKED = "BLOCKED"


class PreconfirmationBuyExplanation(FrozenModel):
    not_yet_confirmed: EvidenceClaim
    directionally_credible: EvidenceClaim
    market_already_prices: EvidenceClaim
    favorable_asymmetry: EvidenceClaim
    thesis_break_risk: EvidenceClaim
    buy_to_hold_or_sell: EvidenceClaim


class PostconfirmationHoldExplanation(FrozenModel):
    business_proof: EvidenceClaim
    price_repricing: EvidenceClaim


class PreconfirmationDecisionCandidate(FrozenModel):
    ticker: str
    fundamental_core_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: Decision
    new_buyer_axis: NewBuyerDecisionAxis
    holder_axis: HolderDecisionAxis
    directional_balance: DirectionalBalance
    buy_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    sell_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    balance_summary: str = Field(min_length=1, max_length=500)
    reasoning_grade: Literal["VERY_HIGH"]
    confidence: Confidence
    timing: Timing
    timing_basis: EvidenceClaim
    factual_safety_state: FactualSafetyState
    factual_safety_basis: EvidenceClaim
    driver_maturity: tuple[DriverEvidenceMaturity, ...] = Field(min_length=1, max_length=6)
    overall_maturity: OverallMaturityAssessment
    market_expectation: MarketExpectationAssessment
    pricing_requirement: PricingRequirementAssessment
    scenarios: ScenarioSet
    asymmetry: AsymmetryAssessment
    confirmation_cost: ConfirmationCostAssessment
    preconfirmation_error_cost: PreconfirmationErrorCostAssessment
    pre_confirmation_buy: bool
    preconfirmation_buy_explanation: PreconfirmationBuyExplanation | None
    post_confirmation_hold: bool
    postconfirmation_hold_explanation: PostconfirmationHoldExplanation | None
    decisive_reason: EvidenceClaim
    why_not_buy: EvidenceClaim
    why_not_sell: EvidenceClaim
    opposing_evidence: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    unknowns: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    upgrade_condition: EvidenceClaim
    downgrade_condition: EvidenceClaim

    @model_validator(mode="after")
    def explanation_flags_match_shapes(self) -> PreconfirmationDecisionCandidate:
        if self.pre_confirmation_buy != (self.preconfirmation_buy_explanation is not None):
            raise ValueError("preconfirmation_explanation_flag_mismatch")
        if self.post_confirmation_hold != (self.postconfirmation_hold_explanation is not None):
            raise ValueError("postconfirmation_explanation_flag_mismatch")
        ThreeAxisDecision(
            overall_direction=self.decision,
            new_buyer=self.new_buyer_axis,
            holder=self.holder_axis,
        )
        return self


class PreconfirmationDecisionCandidateV2(PreconfirmationDecisionCandidate):
    driver_maturity: tuple[DriverEvidenceMaturityV2, ...] = Field(
        min_length=1, max_length=6
    )


class PreconfirmationDecisionBatch(FrozenModel):
    contract: Literal[OUTPUT_CONTRACT]
    decisions: tuple[PreconfirmationDecisionCandidate, ...]


class PreconfirmationValidationResult(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]
    numeric_claim_count: int = 0
    automatically_bound_numeric_count: int = 0
    manual_numeric_count: int = 0
    unresolved_numeric_count: int = 0


def requires_preconfirmation_buy(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> bool:
    """Return the canonical lifecycle-flag requirement without changing any decision axis."""
    decisive = decisive_maturities(candidate.driver_maturity)
    return candidate.decision == "BUY" and bool(
        decisive & {EvidenceMaturity.EARLY, EvidenceMaturity.PARTIAL}
    )


STAGE2_FROZEN_CORE_OWNERSHIP_CONTRACT = "stage2-frozen-core-ownership-v1"
STAGE2_FROZEN_CORE_FIELDS = frozenset(
    {
        "ticker",
        "decision",
        "holder_axis",
        "directional_balance",
        "buy_drivers",
        "sell_drivers",
        "balance_summary",
        "confidence",
        "decisive_reason",
    }
)
STAGE2_IDENTITY_FIELDS = frozenset({"fundamental_core_sha256"})
STAGE2_OWNED_FIELDS = frozenset(
    set(PreconfirmationDecisionCandidate.model_fields)
    - STAGE2_FROZEN_CORE_FIELDS
    - STAGE2_IDENTITY_FIELDS
)


def preconfirmation_stage2_field_ownership_inventory() -> tuple[dict[str, object], ...]:
    """Return the complete top-level ownership inventory for the combined candidate."""
    all_fields = tuple(PreconfirmationDecisionCandidate.model_fields)
    rows: list[dict[str, object]] = []
    for field in all_fields:
        if field in STAGE2_FROZEN_CORE_FIELDS:
            owner = "FUNDAMENTAL_CORE"
            frozen = True
            stage2_semantics = False
            immutability = True
            notes = "entire field subtree must exactly copy the validated frozen core"
        elif field in STAGE2_IDENTITY_FIELDS:
            owner = "CROSS_STAGE_IDENTITY"
            frozen = True
            stage2_semantics = False
            immutability = True
            notes = "must equal the canonical SHA-256 of the validated frozen core"
        else:
            owner = "STAGE2"
            frozen = False
            stage2_semantics = True
            immutability = False
            notes = "newly authored or derived by Stage 2"
        rows.append(
            {
                "field_path": f"$.{field}",
                "owner_stage": owner,
                "frozen_at_stage2": frozen,
                "stage2_semantic_validator_applies": stage2_semantics,
                "immutability_validator_applies": immutability,
                "notes": notes,
            }
        )
    if STAGE2_OWNED_FIELDS | STAGE2_FROZEN_CORE_FIELDS | STAGE2_IDENTITY_FIELDS != set(
        all_fields
    ):
        raise RuntimeError("stage2_field_ownership_inventory_incomplete")
    return tuple(rows)


class RenderedPreconfirmationDecision(FrozenModel):
    contract: str = RENDERER_CONTRACT
    ticker: str
    decision: Decision
    text: str
    validation: PreconfirmationValidationResult


_ORDER_LANGUAGE = re.compile(
    r"시장가|지정가|(?:매수|매도)\s*주문|주문\s*실행|전량\s*(?:매도|매수)|"
    r"포지션\s*크기|buy\s+now|sell\s+now",
    re.IGNORECASE,
)
_FIXED_SCORE_LANGUAGE = re.compile(
    r"(?:가중|고정)\s*(?:점수|배점)|점수\s*합산|weighted\s+score",
    re.IGNORECASE,
)
_TARGET_PRICE_LANGUAGE = re.compile(
    r"(?:목표가|적정가|target\s+price)|(?:bear|base|bull)\s*(?:target|목표)",
    re.IGNORECASE,
)
_UNSUPPORTED = re.compile(
    r"FCF\s*(?:yield|수익률|주당)|EV\s*/\s*FCF|P\s*/\s*FCF|"
    r"ROIC|CCC|DSO|DPO|runway\s*(?:개월|months?)",
    re.IGNORECASE,
)
_EXACT_NUMBER = re.compile(
    r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:\.\d+)?\s*(?:%|원|달러|USD|KRW|배|주|MW|GW)"
)
_KOREAN = re.compile(r"[가-힣]")


def _scenario_claims(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> tuple[EvidenceClaim, ...]:
    scenarios = candidate.scenarios
    return tuple(
        claim
        for scenario in (scenarios.bear, scenarios.base, scenarios.bull)
        for claim in (
            scenario.business_and_earnings,
            scenario.expectation_and_valuation,
            scenario.macro_market_conditions,
        )
    )


def candidate_claims(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> tuple[EvidenceClaim, ...]:
    claims: list[EvidenceClaim] = [
        candidate.timing_basis,
        candidate.factual_safety_basis,
        candidate.overall_maturity.basis,
        candidate.market_expectation.basis,
        candidate.pricing_requirement.basis,
        candidate.pricing_requirement.valuation_basis,
        candidate.pricing_requirement.expectation_basis,
        candidate.pricing_requirement.key_assumption,
        *candidate.pricing_requirement.unknowns,
        *_scenario_claims(candidate),
        candidate.asymmetry.basis,
        candidate.asymmetry.downside_permanence,
        candidate.asymmetry.upside_not_priced,
        candidate.confirmation_cost.basis,
        candidate.confirmation_cost.likely_repricing_channel,
        candidate.preconfirmation_error_cost.basis,
        candidate.preconfirmation_error_cost.capital_loss_channel,
        candidate.decisive_reason,
        candidate.new_buyer_axis.reason,
        candidate.holder_axis.reason,
        candidate.why_not_buy,
        candidate.why_not_sell,
        *candidate.opposing_evidence,
        *candidate.unknowns,
        candidate.upgrade_condition,
        candidate.downgrade_condition,
        *candidate.buy_drivers,
        *candidate.sell_drivers,
    ]
    for row in candidate.driver_maturity:
        claims.append(row.what_remains_unproven)
    if candidate.preconfirmation_buy_explanation is not None:
        explanation = candidate.preconfirmation_buy_explanation
        claims.extend(
            (
                explanation.not_yet_confirmed,
                explanation.directionally_credible,
                explanation.market_already_prices,
                explanation.favorable_asymmetry,
                explanation.thesis_break_risk,
                explanation.buy_to_hold_or_sell,
            )
        )
    if candidate.postconfirmation_hold_explanation is not None:
        explanation = candidate.postconfirmation_hold_explanation
        claims.extend((explanation.business_proof, explanation.price_repricing))
    return tuple(claims)


def stage2_owned_candidate_claims(
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> tuple[EvidenceClaim, ...]:
    claims: list[EvidenceClaim] = [
        candidate.timing_basis,
        candidate.factual_safety_basis,
        candidate.overall_maturity.basis,
        candidate.market_expectation.basis,
        candidate.pricing_requirement.basis,
        candidate.pricing_requirement.valuation_basis,
        candidate.pricing_requirement.expectation_basis,
        candidate.pricing_requirement.key_assumption,
        *candidate.pricing_requirement.unknowns,
        *_scenario_claims(candidate),
        candidate.asymmetry.basis,
        candidate.asymmetry.downside_permanence,
        candidate.asymmetry.upside_not_priced,
        candidate.confirmation_cost.basis,
        candidate.confirmation_cost.likely_repricing_channel,
        candidate.preconfirmation_error_cost.basis,
        candidate.preconfirmation_error_cost.capital_loss_channel,
        candidate.new_buyer_axis.reason,
        candidate.why_not_buy,
        candidate.why_not_sell,
        *candidate.opposing_evidence,
        *candidate.unknowns,
        candidate.upgrade_condition,
        candidate.downgrade_condition,
    ]
    for row in candidate.driver_maturity:
        claims.append(row.what_remains_unproven)
    if candidate.preconfirmation_buy_explanation is not None:
        explanation = candidate.preconfirmation_buy_explanation
        claims.extend(
            (
                explanation.not_yet_confirmed,
                explanation.directionally_credible,
                explanation.market_already_prices,
                explanation.favorable_asymmetry,
                explanation.thesis_break_risk,
                explanation.buy_to_hold_or_sell,
            )
        )
    if candidate.postconfirmation_hold_explanation is not None:
        explanation = candidate.postconfirmation_hold_explanation
        claims.extend((explanation.business_proof, explanation.price_repricing))
    return tuple(claims)


def _claim_categories(
    packet: DecisionEvidencePacket, claims: tuple[EvidenceClaim, ...]
) -> set[EvidenceCategory]:
    refs = {row.ref_id: row for row in packet.evidence}
    return {
        refs[ref_id].category
        for claim in claims
        for ref_id in claim.evidence_refs
        if ref_id in refs
    }


def _validate_preconfirmation_candidate(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
    *,
    claim_language_claims: tuple[EvidenceClaim, ...],
    unsupported_metric_claims: tuple[EvidenceClaim, ...],
) -> PreconfirmationValidationResult:
    errors: list[str] = []
    refs = {row.ref_id: row for row in packet.evidence}
    if candidate.ticker != packet.ticker:
        errors.append("ticker_mismatch")
    if not directional_balance_matches_decision(candidate.directional_balance, candidate.decision):
        errors.append("decision_directional_balance_mismatch")
    if not _KOREAN.search(candidate.balance_summary):
        errors.append("balance_summary_not_korean")
    if _EXACT_NUMBER.search(candidate.balance_summary):
        errors.append("directional_balance_unregistered_numeric")
    errors.extend(
        directional_balance_language_errors(
            (
                candidate.balance_summary,
                *(claim.text for claim in candidate.buy_drivers),
                *(claim.text for claim in candidate.sell_drivers),
            )
        )
    )
    if len({row.driver for row in candidate.driver_maturity}) != len(candidate.driver_maturity):
        errors.append("duplicate_maturity_driver")

    directional_categories = _claim_categories(
        packet, (*candidate.buy_drivers, *candidate.sell_drivers)
    )
    directional_fundamental_categories = {
        EvidenceCategory.THESIS,
        EvidenceCategory.EARNINGS,
        EvidenceCategory.EARNINGS_QUALITY,
        EvidenceCategory.EXPECTATIONS,
        EvidenceCategory.VALUATION,
        EvidenceCategory.RISKS,
        EvidenceCategory.QUALITY,
    }
    if not directional_categories & directional_fundamental_categories:
        errors.append("directional_balance_without_fundamental_or_valuation_driver")

    for claim in claim_language_claims:
        if not _KOREAN.search(claim.text):
            errors.append("claim_not_korean")
        if _ORDER_LANGUAGE.search(claim.text):
            errors.append("order_command_language")
        if _FIXED_SCORE_LANGUAGE.search(claim.text):
            errors.append("fixed_score_language")
        if _TARGET_PRICE_LANGUAGE.search(claim.text):
            errors.append("invented_target_price_language")
        if _EXACT_NUMBER.search(claim.text):
            errors.append("freeform_exact_numeric_claim")
        for ref_id in claim.evidence_refs:
            if ref_id not in refs:
                errors.append(f"unknown_evidence_ref:{ref_id}")

    if any(_UNSUPPORTED.search(claim.text) for claim in unsupported_metric_claims):
        errors.append("unsupported_metric_or_inference")

    for row in candidate.driver_maturity:
        cited_refs = (*row.supporting_evidence_refs, *row.contradicting_evidence_refs)
        for ref_id in cited_refs:
            if ref_id not in refs:
                errors.append(f"unknown_maturity_ref:{ref_id}")
        assessment_date = concrete_evidence_date(packet.assessment_date)
        if isinstance(row, DriverEvidenceMaturityV2):
            projection = project_maturity_provenance(refs, cited_refs)
            errors.extend(
                f"maturity_provenance_unresolvable:{row.driver}:{ref_id}"
                for ref_id in projection.invalid_ref_ids
            )
            if projection.provenance_status is None:
                errors.append(f"maturity_evidence_date_unresolvable:{row.driver}")
            else:
                if row.provenance_status != projection.provenance_status:
                    errors.append(f"maturity_provenance_status_mismatch:{row.driver}")
                if row.as_of != projection.as_of:
                    errors.append(f"maturity_evidence_date_not_owned:{row.driver}")
                row_date = concrete_evidence_date(row.as_of)
                if (
                    row.provenance_status
                    == MaturityProvenanceStatus.SYMBOLIC_ONLY_NO_CONCRETE_DATE
                    and row.as_of is not None
                ):
                    errors.append(f"maturity_provenance_status_date_mismatch:{row.driver}")
                if (
                    row.provenance_status
                    != MaturityProvenanceStatus.SYMBOLIC_ONLY_NO_CONCRETE_DATE
                    and row.as_of is None
                ):
                    errors.append(f"maturity_provenance_status_date_mismatch:{row.driver}")
                if (
                    row_date is not None
                    and assessment_date is not None
                    and row_date > assessment_date
                ):
                    errors.append(f"future_maturity_evidence:{row.driver}")
        else:
            cited_dates = {
                resolved
                for ref_id in cited_refs
                if ref_id in refs
                if (resolved := concrete_evidence_date(refs[ref_id].as_of)) is not None
            }
            row_date = concrete_evidence_date(row.as_of)
            if not cited_dates:
                errors.append(f"maturity_evidence_date_unresolvable:{row.driver}")
            elif row_date not in cited_dates:
                errors.append(f"maturity_evidence_date_not_owned:{row.driver}")
            if row_date is not None and assessment_date is not None and row_date > assessment_date:
                errors.append(f"future_maturity_evidence:{row.driver}")

    expectation_categories = _claim_categories(packet, (candidate.market_expectation.basis,))
    if EvidenceCategory.EXPECTATIONS not in expectation_categories:
        errors.append("market_expectation_without_expectation_evidence")

    pricing_claims = (
        candidate.pricing_requirement.basis,
        candidate.pricing_requirement.valuation_basis,
        candidate.pricing_requirement.expectation_basis,
    )
    pricing_categories = _claim_categories(packet, pricing_claims)
    if candidate.pricing_requirement.requirement != PricingRequirement.UNKNOWN and not {
        EvidenceCategory.VALUATION,
        EvidenceCategory.EXPECTATIONS,
    }.issubset(pricing_categories):
        errors.append("pricing_requirement_without_valuation_and_expectation_evidence")

    asymmetry_claims = (
        candidate.asymmetry.basis,
        candidate.asymmetry.downside_permanence,
        candidate.asymmetry.upside_not_priced,
    )
    asymmetry_categories = _claim_categories(packet, asymmetry_claims)
    fundamental_categories = {
        EvidenceCategory.THESIS,
        EvidenceCategory.EARNINGS,
        EvidenceCategory.EARNINGS_QUALITY,
        EvidenceCategory.EXPECTATIONS,
        EvidenceCategory.VALUATION,
        EvidenceCategory.RISKS,
        EvidenceCategory.QUALITY,
    }
    if not (asymmetry_categories & fundamental_categories):
        errors.append("technical_feature_owns_asymmetry")

    decisive = decisive_maturities(candidate.driver_maturity)
    early_or_partial = bool(decisive & {EvidenceMaturity.EARLY, EvidenceMaturity.PARTIAL})
    preconfirmation_required = requires_preconfirmation_buy(candidate)
    if candidate.pre_confirmation_buy:
        if candidate.decision != "BUY":
            errors.append("preconfirmation_buy_without_buy_decision")
        if not early_or_partial:
            errors.append("preconfirmation_buy_without_early_or_partial_driver")
        if candidate.asymmetry.asymmetry != Asymmetry.FAVORABLE:
            errors.append("preconfirmation_buy_without_favorable_asymmetry")
        if candidate.factual_safety_state == FactualSafetyState.BLOCKED:
            errors.append("preconfirmation_logic_bypasses_data_safety")
    elif preconfirmation_required:
        errors.append("preconfirmation_buy_flag_missing")

    if candidate.post_confirmation_hold:
        if candidate.decision != "HOLD":
            errors.append("postconfirmation_hold_without_hold_decision")
        if candidate.overall_maturity.maturity != EvidenceMaturity.CONFIRMED:
            errors.append("postconfirmation_hold_without_confirmed_maturity")
    elif (
        candidate.decision == "HOLD"
        and candidate.overall_maturity.maturity == EvidenceMaturity.CONFIRMED
    ):
        errors.append("postconfirmation_hold_flag_missing")

    if candidate.factual_safety_state == FactualSafetyState.BLOCKED:
        if candidate.pricing_requirement.requirement != PricingRequirement.UNKNOWN:
            errors.append("blocked_safety_with_pricing_requirement")
        if candidate.asymmetry.asymmetry != Asymmetry.UNKNOWN:
            errors.append("blocked_safety_with_asymmetry")
        if candidate.pre_confirmation_buy:
            errors.append("blocked_safety_with_preconfirmation_buy")

    if candidate.upgrade_condition.text.strip() == candidate.downgrade_condition.text.strip():
        errors.append("symmetric_decision_change_conditions")
    for condition_claim in (candidate.upgrade_condition, candidate.downgrade_condition):
        source_conditions = tuple(
            refs[ref_id].logical_condition
            for ref_id in condition_claim.evidence_refs
            if ref_id in refs and refs[ref_id].logical_condition is not None
        )
        composite_sources = tuple(
            item
            for item in source_conditions
            if item is not None and logical_expression_is_composite(item.expression)
        )
        if composite_sources or condition_claim.logical_condition is not None:
            errors.extend(
                logical_condition_errors(
                    subject=packet.ticker,
                    generation_id=packet.packet_id,
                    source_conditions=(item for item in source_conditions if item is not None),
                    claim=condition_claim.logical_condition,
                )
            )

    return PreconfirmationValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
    )


def validate_preconfirmation_candidate(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> PreconfirmationValidationResult:
    return _validate_preconfirmation_candidate(
        packet,
        candidate,
        claim_language_claims=candidate_claims(candidate),
        unsupported_metric_claims=candidate_claims(candidate),
    )


def validate_preconfirmation_stage2_owned_semantics(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate | PreconfirmationDecisionCandidateV2,
) -> PreconfirmationValidationResult:
    """Validate a combined candidate after its frozen core identity is trusted."""
    return _validate_preconfirmation_candidate(
        packet,
        candidate,
        claim_language_claims=stage2_owned_candidate_claims(candidate),
        unsupported_metric_claims=stage2_owned_candidate_claims(candidate),
    )


def render_preconfirmation_shadow(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate,
) -> RenderedPreconfirmationDecision:
    validation = validate_preconfirmation_candidate(packet, candidate)
    if not validation.valid:
        raise ValueError("preconfirmation_candidate_invalid:" + ",".join(validation.errors))
    confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    maturity = {
        "EARLY": "초기",
        "PARTIAL": "부분 확인",
        "CONFIRMED": "확인",
        "MIXED": "혼재",
        "UNKNOWN": "판단 근거 부족",
    }
    asymmetry = {
        "FAVORABLE": "유리",
        "BALANCED": "균형",
        "UNFAVORABLE": "불리",
        "UNKNOWN": "판단 근거 부족",
    }
    lines = [
        "🧪 SHADOW V2 · 비대칭/증거성숙도 검증",
        f"🏢 {packet.company_name}({packet.ticker})",
        f"🧠 AI 종합 판단: {candidate.decision}",
        f"판단 균형: {render_directional_balance(candidate.directional_balance)}",
        f"추론등급: 매우 높음 | 판단 확신도: {confidence[candidate.confidence]}",
        (
            "증거 성숙도: "
            f"{maturity[candidate.overall_maturity.maturity]} | "
            f"가격 비대칭: {asymmetry[candidate.asymmetry.asymmetry]}"
        ),
        "",
        "🎯 판단",
        f"• {candidate.decisive_reason.text}",
    ]
    if candidate.preconfirmation_buy_explanation is not None:
        explanation = candidate.preconfirmation_buy_explanation
        lines.extend(
            [
                "",
                "🔎 완전 확인 전 판단",
                f"• 아직 확인되지 않은 점: {explanation.not_yet_confirmed.text}",
                f"• 확인을 기다리는 비용: {candidate.confirmation_cost.basis.text}",
                f"• 판단 철회 조건: {explanation.buy_to_hold_or_sell.text}",
            ]
        )
    elif candidate.postconfirmation_hold_explanation is not None:
        explanation = candidate.postconfirmation_hold_explanation
        lines.extend(
            [
                "",
                "⚖️ 확인 이후 가격 판단",
                f"• {explanation.business_proof.text}",
                f"• {explanation.price_repricing.text}",
            ]
        )
    lines.extend(
        [
            "",
            "🔄 판단 변경 조건",
            f"• 상향: {candidate.upgrade_condition.text}",
            f"• 하향: {candidate.downgrade_condition.text}",
            "",
            "※ Shadow 연구 분류이며 주문·자동매매 지시가 아닙니다.",
        ]
    )
    return RenderedPreconfirmationDecision(
        ticker=packet.ticker,
        decision=candidate.decision,
        text="\n".join(lines),
        validation=validation,
    )


def preconfirmation_message_quality(
    rendered: tuple[RenderedPreconfirmationDecision, ...],
) -> dict[str, object]:
    errors: list[str] = []
    texts = [row.text for row in rendered]
    if any(not row.validation.valid for row in rendered):
        errors.append("candidate_validation_failed")
    if any(len(text) > 3500 for text in texts):
        errors.append("message_too_long")
    if any(_ORDER_LANGUAGE.search(text) for text in texts):
        errors.append("order_language")
    if any(_TARGET_PRICE_LANGUAGE.search(text) for text in texts):
        errors.append("invented_target_price")
    if any(_FIXED_SCORE_LANGUAGE.search(text) for text in texts):
        errors.append("fixed_score_language")
    substantive: list[str] = []
    for text in texts:
        for line in text.splitlines():
            normalized = re.sub(r"\s+", " ", line.strip().removeprefix("• "))
            if len(normalized) >= 36 and not normalized.startswith("Shadow 연구 분류이며"):
                substantive.append(normalized)
    repeated = [text for text, count in Counter(substantive).items() if count >= 2]
    if repeated:
        errors.append("cross_ticker_substantive_repetition")
    return {
        "contract": "preconfirmation-message-quality-v2",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "message_count": len(texts),
        "average_character_count": round(sum(map(len, texts)) / len(texts), 2) if texts else 0,
        "max_character_count": max(map(len, texts), default=0),
        "numeric_claim_count": 0,
        "automatically_bound_numeric_count": 0,
        "manual_numeric_count": 0,
        "unresolved_numeric_count": 0,
        "repeated_substantive_span_count": len(repeated),
    }
