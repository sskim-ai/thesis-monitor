from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from enum import StrEnum
from typing import Literal

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    Confidence,
    Decision,
    DecisionEvidencePacket,
    EvidenceClaim,
    FrozenModel,
)
from app.services.evidence_maturity_pricing_service import (
    EvidenceMaturity,
    PricingRequirement,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_language_errors,
    directional_balance_matches_decision,
    render_directional_balance,
)
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate,
)
from app.services.scenario_asymmetry_service import Asymmetry
from app.services.logical_condition_service import logical_condition_errors
from app.services.production_validation_policy_service import (
    RepetitionClass,
    classify_repeated_span,
)


CONTRACT_VERSION = "v2-accepted-decision-ownership-v1"
VALIDATOR_CONTRACT = "v2-accepted-decision-validator-v1"
RENDERER_CONTRACT = "v2-accepted-decision-shadow-renderer-v1"
CHANGE_CONDITION_CONTRACT = "decision-aware-change-condition-v1"


class AcceptedDecisionStatus(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class AcceptedDecisionSource(StrEnum):
    CANDIDATE = "CANDIDATE"
    ADJUDICATION_KEEP_V1 = "ADJUDICATION_KEEP_V1"
    ADJUDICATION_KEEP_V2 = "ADJUDICATION_KEEP_V2"


class AdjudicationRecommendation(StrEnum):
    KEEP_V1 = "KEEP_V1"
    KEEP_V2 = "KEEP_V2"
    NEEDS_REPAIR = "NEEDS_REPAIR"


class AcceptedV2Adjudication(FrozenModel):
    ticker: str
    v1_decision: Decision
    v2_decision: Decision
    accepted_decision: Decision
    recommendation: AdjudicationRecommendation
    v1_overrequired_confirmation: Literal["YES", "NO", "UNCERTAIN"]
    v2_underweighted_execution_risk: Literal["YES", "NO", "UNCERTAIN"]
    v1_ignored_confirmation_cost: Literal["YES", "NO", "UNCERTAIN"]
    v2_overstated_favorable_asymmetry: Literal["YES", "NO", "UNCERTAIN"]
    valuation_or_expectation_misuse: Literal["V1", "V2", "BOTH", "NEITHER", "UNCERTAIN"]
    data_quality_comparison_safe: bool
    accepted_directional_balance: DirectionalBalance
    accepted_buy_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    accepted_sell_drivers: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)
    accepted_balance_summary: str = Field(min_length=1, max_length=500)
    decisive_basis: EvidenceClaim
    bounded_repair: str


class AcceptedDecisionPlan(FrozenModel):
    contract: str = CONTRACT_VERSION
    status: AcceptedDecisionStatus
    ticker: str
    candidate_decision_id: str
    candidate_decision: Decision
    candidate_evidence_fingerprint: str
    material_disagreement: bool
    adjudication_id: str | None
    adjudication_status: str
    adjudication_recommendation: AdjudicationRecommendation | None
    adjudication_reason: EvidenceClaim | None
    accepted_decision_id: str | None
    accepted_decision: Decision | None
    accepted_source: AcceptedDecisionSource | None
    accepted_evidence_fingerprint: str | None
    accepted_as_of: str | None
    accepted_reason: EvidenceClaim | None
    accepted_confidence: Confidence | None
    accepted_overall_maturity: EvidenceMaturity | None
    accepted_pricing_requirement: PricingRequirement | None
    accepted_asymmetry: Asymmetry | None
    accepted_preconfirmation_buy: bool
    accepted_postconfirmation_hold: bool
    accepted_confirmation_cost_basis: EvidenceClaim | None
    accepted_upgrade_condition: EvidenceClaim | None
    accepted_downgrade_condition: EvidenceClaim | None
    denial_reason: str | None
    candidate_directional_balance: DirectionalBalance | None = None
    candidate_buy_drivers: tuple[EvidenceClaim, ...] = ()
    candidate_sell_drivers: tuple[EvidenceClaim, ...] = ()
    candidate_balance_summary: str | None = None
    accepted_directional_balance: DirectionalBalance | None = None
    accepted_buy_drivers: tuple[EvidenceClaim, ...] = ()
    accepted_sell_drivers: tuple[EvidenceClaim, ...] = ()
    accepted_balance_summary: str | None = None


class AcceptedDecisionValidationResult(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]


class AcceptedRenderValidationResult(FrozenModel):
    contract: str = "v2-accepted-decision-render-validator-v1"
    valid: bool
    errors: tuple[str, ...]


class RenderedAcceptedDecision(FrozenModel):
    contract: str = RENDERER_CONTRACT
    ticker: str
    candidate_decision: Decision
    accepted_decision: Decision
    accepted_source: AcceptedDecisionSource
    accepted_directional_balance: DirectionalBalance
    text: str
    validation: AcceptedRenderValidationResult


class RenderedProductionAcceptedDecision(FrozenModel):
    contract: str = "v2-accepted-decision-production-renderer-v1"
    ticker: str
    accepted_decision: Decision
    accepted_source: AcceptedDecisionSource
    accepted_directional_balance: DirectionalBalance
    text: str
    validation: AcceptedRenderValidationResult


_ORDER_LANGUAGE = re.compile(
    r"시장가|지정가|(?:매수|매도)\s*주문|주문\s*실행|전량\s*(?:매도|매수)|"
    r"포지션\s*크기|buy\s+now|sell\s+now",
    re.IGNORECASE,
)
_EXACT_NUMBER = re.compile(
    r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:\.\d+)?\s*(?:%|원|달러|USD|KRW|배|주|MW|GW)"
)

_SELF_TRANSITION = {
    ("BUY", "UPGRADE"): re.compile(
        r"(?:매수|BUY)\s*(?:판단\s*)?(?:으로|로)\s*(?:상향|높|전환)",
        re.IGNORECASE,
    ),
    ("HOLD", "UPGRADE"): re.compile(
        r"(?:보유|HOLD)\s*(?:판단\s*)?(?:으로|로)\s*(?:상향|높|전환)",
        re.IGNORECASE,
    ),
    ("HOLD", "DOWNGRADE"): re.compile(
        r"(?:보유|HOLD)\s*(?:판단\s*)?(?:으로|로)\s*(?:하향|낮|전환)",
        re.IGNORECASE,
    ),
    ("SELL", "DOWNGRADE"): re.compile(
        r"(?:매도|SELL)\s*(?:판단\s*)?(?:으로|로)\s*(?:하향|낮|전환)",
        re.IGNORECASE,
    ),
}


def normalize_decision_change_condition(
    decision: Decision,
    direction: Literal["UPGRADE", "DOWNGRADE"],
    claim: EvidenceClaim,
) -> EvidenceClaim:
    """Remove impossible top-level self transitions without changing evidence."""
    text = claim.text
    replacements: dict[tuple[Decision, str], tuple[tuple[str, str], ...]] = {
        ("BUY", "UPGRADE"): (
            (r"매수 판단으로 높인다", "BUY 확신을 높인다"),
            (r"매수 판단으로 상향한다", "BUY 확신을 높인다"),
            (r"매수로 상향한다", "BUY 확신을 높인다"),
        ),
        ("HOLD", "UPGRADE"): (
            (r"보유 판단으로 높인다", "BUY 재평가 조건으로 삼는다"),
            (r"보유 판단으로 상향한다", "BUY 재평가 조건으로 삼는다"),
            (r"보유로 상향한다", "BUY 재평가 조건으로 삼는다"),
        ),
        ("HOLD", "DOWNGRADE"): (
            (r"보유 판단으로 낮추고", "HOLD 확신을 낮추고"),
            (r"보유 판단으로 낮춘다", "HOLD 확신을 낮춘다"),
            (r"보유 판단으로 하향한다", "SELL 재평가 조건으로 삼는다"),
            (r"보유로 하향한다", "SELL 재평가 조건으로 삼는다"),
        ),
        ("SELL", "DOWNGRADE"): (
            (r"매도 판단으로 낮춘다", "SELL 확신을 높인다"),
            (r"매도 판단으로 하향한다", "SELL 확신을 높인다"),
            (r"매도로 하향한다", "SELL 확신을 높인다"),
        ),
    }
    for source, target in replacements.get((decision, direction), ()):
        text = re.sub(source, target, text, flags=re.IGNORECASE)
    return claim.model_copy(update={"text": text})


def decision_change_condition_errors(
    decision: Decision,
    *,
    upgrade_text: str,
    downgrade_text: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    for direction, text in (
        ("UPGRADE", upgrade_text),
        ("DOWNGRADE", downgrade_text),
    ):
        pattern = _SELF_TRANSITION.get((decision, direction))
        if pattern is not None and pattern.search(text):
            errors.append(f"self_transition_wording:{decision}:{direction}")
    return tuple(errors)


def _canonical_fingerprint(prefix: str, value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()}"


def _not_ready_plan(
    *,
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate,
    candidate_decision_id: str,
    material_disagreement: bool,
    adjudication_id: str | None,
    adjudication_status: str,
    adjudication: AcceptedV2Adjudication | None,
    denial_reason: str,
) -> AcceptedDecisionPlan:
    return AcceptedDecisionPlan(
        status=AcceptedDecisionStatus.NOT_READY,
        ticker=packet.ticker,
        candidate_decision_id=candidate_decision_id,
        candidate_decision=candidate.decision,
        candidate_evidence_fingerprint=packet.evidence_sha256,
        material_disagreement=material_disagreement,
        adjudication_id=adjudication_id,
        adjudication_status=adjudication_status,
        adjudication_recommendation=(adjudication.recommendation if adjudication else None),
        adjudication_reason=(adjudication.decisive_basis if adjudication else None),
        accepted_decision_id=None,
        accepted_decision=None,
        accepted_source=None,
        accepted_evidence_fingerprint=None,
        accepted_as_of=None,
        accepted_reason=None,
        accepted_confidence=None,
        accepted_overall_maturity=None,
        accepted_pricing_requirement=None,
        accepted_asymmetry=None,
        accepted_preconfirmation_buy=False,
        accepted_postconfirmation_hold=False,
        accepted_confirmation_cost_basis=None,
        accepted_upgrade_condition=None,
        accepted_downgrade_condition=None,
        denial_reason=denial_reason,
        candidate_directional_balance=candidate.directional_balance,
        candidate_buy_drivers=candidate.buy_drivers,
        candidate_sell_drivers=candidate.sell_drivers,
        candidate_balance_summary=candidate.balance_summary,
    )


def resolve_accepted_v2_decision(
    packet: DecisionEvidencePacket,
    candidate: PreconfirmationDecisionCandidate,
    *,
    v1_decision: Decision,
    material_disagreement: bool,
    adjudication: AcceptedV2Adjudication | None,
    v1_directional_balance: DirectionalBalance | None = None,
    v1_buy_drivers: tuple[EvidenceClaim, ...] = (),
    v1_sell_drivers: tuple[EvidenceClaim, ...] = (),
    v1_balance_summary: str | None = None,
) -> AcceptedDecisionPlan:
    candidate_payload = candidate.model_dump(mode="json")
    candidate_decision_id = _canonical_fingerprint(
        "v2-candidate",
        {
            "ticker": packet.ticker,
            "evidence_fingerprint": packet.evidence_sha256,
            "candidate": candidate_payload,
        },
    )
    adjudication_id = (
        _canonical_fingerprint("v2-adjudication", adjudication.model_dump(mode="json"))
        if adjudication is not None
        else None
    )

    if candidate.ticker != packet.ticker:
        return _not_ready_plan(
            packet=packet,
            candidate=candidate,
            candidate_decision_id=candidate_decision_id,
            material_disagreement=material_disagreement,
            adjudication_id=adjudication_id,
            adjudication_status="INVALID",
            adjudication=adjudication,
            denial_reason="candidate_ticker_mismatch",
        )

    if not material_disagreement:
        accepted_decision = candidate.decision
        accepted_source = AcceptedDecisionSource.CANDIDATE
        accepted_reason = candidate.decisive_reason
        accepted_directional_balance = candidate.directional_balance
        accepted_buy_drivers = candidate.buy_drivers
        accepted_sell_drivers = candidate.sell_drivers
        accepted_balance_summary = candidate.balance_summary
        adjudication_status = "NOT_REQUIRED"
    else:
        if adjudication is None:
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=True,
                adjudication_id=None,
                adjudication_status="MISSING_REQUIRED",
                adjudication=None,
                denial_reason="material_disagreement_without_final_adjudication",
            )
        if adjudication.recommendation == AdjudicationRecommendation.NEEDS_REPAIR:
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=True,
                adjudication_id=adjudication_id,
                adjudication_status="NEEDS_REPAIR",
                adjudication=adjudication,
                denial_reason="adjudication_not_final",
            )
        expected = (
            v1_decision
            if adjudication.recommendation == AdjudicationRecommendation.KEEP_V1
            else candidate.decision
        )
        if (
            adjudication.ticker != packet.ticker
            or adjudication.v1_decision != v1_decision
            or adjudication.v2_decision != candidate.decision
            or adjudication.accepted_decision != expected
        ):
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=True,
                adjudication_id=adjudication_id,
                adjudication_status="INVALID",
                adjudication=adjudication,
                denial_reason="adjudication_decision_mismatch",
            )
        accepted_decision = expected
        accepted_source = (
            AcceptedDecisionSource.ADJUDICATION_KEEP_V1
            if adjudication.recommendation == AdjudicationRecommendation.KEEP_V1
            else AcceptedDecisionSource.ADJUDICATION_KEEP_V2
        )
        accepted_reason = adjudication.decisive_basis
        accepted_directional_balance = adjudication.accepted_directional_balance
        accepted_buy_drivers = adjudication.accepted_buy_drivers
        accepted_sell_drivers = adjudication.accepted_sell_drivers
        accepted_balance_summary = adjudication.accepted_balance_summary
        adjudication_status = "FINAL"

    if not directional_balance_matches_decision(accepted_directional_balance, accepted_decision):
        return _not_ready_plan(
            packet=packet,
            candidate=candidate,
            candidate_decision_id=candidate_decision_id,
            material_disagreement=material_disagreement,
            adjudication_id=adjudication_id,
            adjudication_status="INVALID",
            adjudication=adjudication,
            denial_reason="accepted_decision_balance_mismatch",
        )
    if accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V2 and (
        accepted_directional_balance != candidate.directional_balance
        or accepted_buy_drivers != candidate.buy_drivers
        or accepted_sell_drivers != candidate.sell_drivers
        or accepted_balance_summary != candidate.balance_summary
    ):
        return _not_ready_plan(
            packet=packet,
            candidate=candidate,
            candidate_decision_id=candidate_decision_id,
            material_disagreement=material_disagreement,
            adjudication_id=adjudication_id,
            adjudication_status="INVALID",
            adjudication=adjudication,
            denial_reason="keep_v2_balance_or_driver_mismatch",
        )
    if accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1:
        prior_mismatch = bool(
            v1_directional_balance is not None
            and accepted_directional_balance != v1_directional_balance
        )
        prior_mismatch = prior_mismatch or bool(
            v1_buy_drivers and accepted_buy_drivers != v1_buy_drivers
        )
        prior_mismatch = prior_mismatch or bool(
            v1_sell_drivers and accepted_sell_drivers != v1_sell_drivers
        )
        prior_mismatch = prior_mismatch or bool(
            v1_balance_summary is not None and accepted_balance_summary != v1_balance_summary
        )
        if prior_mismatch:
            return _not_ready_plan(
                packet=packet,
                candidate=candidate,
                candidate_decision_id=candidate_decision_id,
                material_disagreement=material_disagreement,
                adjudication_id=adjudication_id,
                adjudication_status="INVALID",
                adjudication=adjudication,
                denial_reason="keep_v1_balance_or_driver_mismatch",
            )

    accepted_preconfirmation_buy = bool(
        accepted_decision == "BUY"
        and candidate.decision == accepted_decision
        and accepted_source != AcceptedDecisionSource.ADJUDICATION_KEEP_V1
        and candidate.pre_confirmation_buy
    )
    accepted_postconfirmation_hold = bool(
        accepted_decision == "HOLD"
        and candidate.decision == accepted_decision
        and candidate.post_confirmation_hold
    )
    accepted_asymmetry = (
        Asymmetry.UNKNOWN
        if accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1
        else candidate.asymmetry.asymmetry
    )
    accepted_evidence_fingerprint = _canonical_fingerprint(
        "v2-accepted-evidence",
        {
            "packet": packet.evidence_sha256,
            "candidate_decision_id": candidate_decision_id,
            "adjudication_id": adjudication_id,
            "accepted_reason_refs": accepted_reason.evidence_refs,
            "accepted_balance": accepted_directional_balance.model_dump(mode="json"),
            "accepted_buy_driver_refs": [
                list(claim.evidence_refs) for claim in accepted_buy_drivers
            ],
            "accepted_sell_driver_refs": [
                list(claim.evidence_refs) for claim in accepted_sell_drivers
            ],
        },
    )
    accepted_decision_id = _canonical_fingerprint(
        "v2-accepted-decision",
        {
            "ticker": packet.ticker,
            "accepted_decision": accepted_decision,
            "accepted_source": accepted_source,
            "accepted_evidence_fingerprint": accepted_evidence_fingerprint,
            "accepted_as_of": packet.assessment_date,
            "accepted_balance": accepted_directional_balance.model_dump(mode="json"),
        },
    )
    return AcceptedDecisionPlan(
        status=AcceptedDecisionStatus.READY,
        ticker=packet.ticker,
        candidate_decision_id=candidate_decision_id,
        candidate_decision=candidate.decision,
        candidate_evidence_fingerprint=packet.evidence_sha256,
        material_disagreement=material_disagreement,
        adjudication_id=adjudication_id,
        adjudication_status=adjudication_status,
        adjudication_recommendation=(adjudication.recommendation if adjudication else None),
        adjudication_reason=(adjudication.decisive_basis if adjudication else None),
        accepted_decision_id=accepted_decision_id,
        accepted_decision=accepted_decision,
        accepted_source=accepted_source,
        accepted_evidence_fingerprint=accepted_evidence_fingerprint,
        accepted_as_of=packet.assessment_date,
        accepted_reason=accepted_reason,
        accepted_confidence=candidate.confidence,
        accepted_overall_maturity=candidate.overall_maturity.maturity,
        accepted_pricing_requirement=candidate.pricing_requirement.requirement,
        accepted_asymmetry=accepted_asymmetry,
        accepted_preconfirmation_buy=accepted_preconfirmation_buy,
        accepted_postconfirmation_hold=accepted_postconfirmation_hold,
        accepted_confirmation_cost_basis=(
            candidate.confirmation_cost.basis if accepted_preconfirmation_buy else None
        ),
        accepted_upgrade_condition=normalize_decision_change_condition(
            accepted_decision, "UPGRADE", candidate.upgrade_condition
        ),
        accepted_downgrade_condition=normalize_decision_change_condition(
            accepted_decision, "DOWNGRADE", candidate.downgrade_condition
        ),
        denial_reason=None,
        candidate_directional_balance=candidate.directional_balance,
        candidate_buy_drivers=candidate.buy_drivers,
        candidate_sell_drivers=candidate.sell_drivers,
        candidate_balance_summary=candidate.balance_summary,
        accepted_directional_balance=accepted_directional_balance,
        accepted_buy_drivers=accepted_buy_drivers,
        accepted_sell_drivers=accepted_sell_drivers,
        accepted_balance_summary=accepted_balance_summary,
    )


def validate_accepted_v2_decision(
    packet: DecisionEvidencePacket,
    plan: AcceptedDecisionPlan,
) -> AcceptedDecisionValidationResult:
    errors: list[str] = []
    if plan.status != AcceptedDecisionStatus.READY:
        errors.append(plan.denial_reason or "accepted_decision_not_ready")
        return AcceptedDecisionValidationResult(valid=False, errors=tuple(errors))
    if plan.ticker != packet.ticker:
        errors.append("accepted_ticker_mismatch")
    if not plan.accepted_decision or not plan.accepted_decision_id or not plan.accepted_source:
        errors.append("accepted_identity_missing")
    if not plan.accepted_evidence_fingerprint or not plan.accepted_as_of:
        errors.append("accepted_lineage_missing")
    if plan.accepted_confidence is None:
        errors.append("accepted_confidence_missing")
    if plan.accepted_directional_balance is None:
        errors.append("accepted_directional_balance_missing")
    elif plan.accepted_decision is not None and not directional_balance_matches_decision(
        plan.accepted_directional_balance, plan.accepted_decision
    ):
        errors.append("accepted_decision_balance_mismatch")
    if not plan.accepted_buy_drivers or not plan.accepted_sell_drivers:
        errors.append("accepted_directional_drivers_missing")
    if not plan.accepted_balance_summary:
        errors.append("accepted_balance_summary_missing")
    else:
        if _EXACT_NUMBER.search(plan.accepted_balance_summary):
            errors.append("adjudication_introduced_unregistered_numeric")
        errors.extend(
            directional_balance_language_errors(
                (
                    plan.accepted_balance_summary,
                    *(claim.text for claim in plan.accepted_buy_drivers),
                    *(claim.text for claim in plan.accepted_sell_drivers),
                )
            )
        )
    if plan.accepted_preconfirmation_buy and plan.accepted_decision != "BUY":
        errors.append("rejected_preconfirmation_buy_leaked_to_accepted")
    if plan.accepted_postconfirmation_hold and plan.accepted_decision != "HOLD":
        errors.append("postconfirmation_hold_decision_mismatch")
    if plan.accepted_decision == "SELL" and plan.accepted_asymmetry == Asymmetry.FAVORABLE:
        errors.append("accepted_decision_reason_conflict")
    if (
        plan.accepted_source == AcceptedDecisionSource.ADJUDICATION_KEEP_V1
        and plan.accepted_decision == plan.candidate_decision
        and plan.accepted_directional_balance == plan.candidate_directional_balance
    ):
        errors.append("keep_v1_did_not_replace_candidate_or_balance")
    claims = tuple(
        claim
        for claim in (
            plan.accepted_reason,
            plan.accepted_confirmation_cost_basis,
            plan.accepted_upgrade_condition,
            plan.accepted_downgrade_condition,
            *plan.accepted_buy_drivers,
            *plan.accepted_sell_drivers,
        )
        if claim is not None
    )
    allowed_refs = {row.ref_id for row in packet.evidence}
    for claim in claims:
        if _ORDER_LANGUAGE.search(claim.text):
            errors.append("order_command_language")
        if _EXACT_NUMBER.search(claim.text):
            errors.append("adjudication_introduced_unregistered_numeric")
        for ref_id in claim.evidence_refs:
            if ref_id not in allowed_refs:
                errors.append(f"unknown_accepted_evidence_ref:{ref_id}")
    refs = {row.ref_id: row for row in packet.evidence}
    for condition_claim in (
        plan.accepted_upgrade_condition,
        plan.accepted_downgrade_condition,
    ):
        if condition_claim is None:
            continue
        source_conditions = tuple(
            refs[ref_id].logical_condition
            for ref_id in condition_claim.evidence_refs
            if ref_id in refs and refs[ref_id].logical_condition is not None
        )
        composite_sources = tuple(
            item for item in source_conditions if item is not None and item.expression.children
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
    if plan.accepted_decision is not None:
        errors.extend(
            decision_change_condition_errors(
                plan.accepted_decision,
                upgrade_text=(
                    plan.accepted_upgrade_condition.text if plan.accepted_upgrade_condition else ""
                ),
                downgrade_text=(
                    plan.accepted_downgrade_condition.text
                    if plan.accepted_downgrade_condition
                    else ""
                ),
            )
        )
    return AcceptedDecisionValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
    )


def validate_accepted_v2_render(
    plan: AcceptedDecisionPlan,
    *,
    rendered_decision: Decision,
    text: str,
    render_mode: Literal["shadow", "production"] = "shadow",
) -> AcceptedRenderValidationResult:
    errors: list[str] = []
    if plan.status != AcceptedDecisionStatus.READY or plan.accepted_decision is None:
        errors.append("accepted_decision_not_ready")
    elif rendered_decision != plan.accepted_decision:
        errors.append("rendered_decision_not_accepted_decision")
    required_label = (
        "🧪 SHADOW V2 · accepted decision 검증" if render_mode == "shadow" else "🧠 AI 분석 판단:"
    )
    if required_label not in text:
        errors.append(f"accepted_{render_mode}_label_missing")
    if plan.accepted_reason is not None and plan.accepted_reason.text not in text:
        errors.append("accepted_reason_missing")
    if plan.accepted_directional_balance is None:
        errors.append("accepted_directional_balance_missing")
    elif f"판단 균형: {render_directional_balance(plan.accepted_directional_balance)}" not in text:
        errors.append("accepted_directional_balance_missing_from_render")
    if _ORDER_LANGUAGE.search(text):
        errors.append("order_command_language")
    return AcceptedRenderValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
    )


def normalize_accepted_plan_conditions(
    plan: AcceptedDecisionPlan,
) -> AcceptedDecisionPlan:
    if plan.accepted_decision is None:
        return plan
    updates: dict[str, EvidenceClaim] = {}
    if plan.accepted_upgrade_condition is not None:
        updates["accepted_upgrade_condition"] = normalize_decision_change_condition(
            plan.accepted_decision,
            "UPGRADE",
            plan.accepted_upgrade_condition,
        )
    if plan.accepted_downgrade_condition is not None:
        updates["accepted_downgrade_condition"] = normalize_decision_change_condition(
            plan.accepted_decision,
            "DOWNGRADE",
            plan.accepted_downgrade_condition,
        )
    return plan.model_copy(update=updates) if updates else plan


def render_accepted_v2_shadow(
    packet: DecisionEvidencePacket,
    plan: AcceptedDecisionPlan,
) -> RenderedAcceptedDecision:
    accepted_validation = validate_accepted_v2_decision(packet, plan)
    if not accepted_validation.valid or plan.accepted_decision is None:
        raise ValueError("accepted_decision_invalid:" + ",".join(accepted_validation.errors))
    if plan.accepted_source is None or plan.accepted_reason is None:
        raise ValueError("accepted_decision_lineage_missing")
    if plan.accepted_directional_balance is None:
        raise ValueError("accepted_directional_balance_missing")
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
        "UNKNOWN": "판단 보류",
    }
    lines = [
        "🧪 SHADOW V2 · accepted decision 검증",
        f"🏢 {packet.company_name}({packet.ticker})",
        f"🧠 AI 수용 판단: {plan.accepted_decision}",
        f"판단 균형: {render_directional_balance(plan.accepted_directional_balance)}",
        f"추론등급: 매우 높음 | 판단 확신도: {confidence[str(plan.accepted_confidence)]}",
        (
            "증거 성숙도: "
            f"{maturity[str(plan.accepted_overall_maturity)]} | "
            f"가격 비대칭: {asymmetry[str(plan.accepted_asymmetry)]}"
        ),
        "",
        "🎯 판단",
        f"• {plan.accepted_reason.text}",
    ]
    if plan.accepted_preconfirmation_buy and plan.accepted_confirmation_cost_basis is not None:
        lines.extend(
            [
                "",
                "🔎 완전 확인 전 BUY",
                f"• 확인을 기다리는 비용: {plan.accepted_confirmation_cost_basis.text}",
            ]
        )
    lines.extend(
        [
            "",
            "🔄 판단 변경 조건",
            f"• 상향: {plan.accepted_upgrade_condition.text}",
            f"• 하향: {plan.accepted_downgrade_condition.text}",
            "",
            "※ Shadow 연구 분류이며 주문·자동매매 지시가 아닙니다.",
        ]
    )
    text = "\n".join(lines)
    validation = validate_accepted_v2_render(
        plan,
        rendered_decision=plan.accepted_decision,
        text=text,
    )
    if not validation.valid:
        raise ValueError("accepted_render_invalid:" + ",".join(validation.errors))
    return RenderedAcceptedDecision(
        ticker=packet.ticker,
        candidate_decision=plan.candidate_decision,
        accepted_decision=plan.accepted_decision,
        accepted_source=plan.accepted_source,
        accepted_directional_balance=plan.accepted_directional_balance,
        text=text,
        validation=validation,
    )


def render_accepted_v2_production(
    packet: DecisionEvidencePacket,
    plan: AcceptedDecisionPlan,
) -> RenderedProductionAcceptedDecision:
    plan = normalize_accepted_plan_conditions(plan)
    accepted_validation = validate_accepted_v2_decision(packet, plan)
    if not accepted_validation.valid or plan.accepted_decision is None:
        raise ValueError("accepted_decision_invalid:" + ",".join(accepted_validation.errors))
    if plan.accepted_source is None or plan.accepted_reason is None:
        raise ValueError("accepted_decision_lineage_missing")
    if plan.accepted_directional_balance is None:
        raise ValueError("accepted_directional_balance_missing")
    if plan.accepted_upgrade_condition is None or plan.accepted_downgrade_condition is None:
        raise ValueError("accepted_change_condition_missing")
    confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    maturity = {
        "EARLY": "초기",
        "PARTIAL": "부분 확인",
        "CONFIRMED": "확인",
        "MIXED": "혼재",
        "UNKNOWN": "판단 근거 부족",
    }
    lines = [
        f"🧠 AI 분석 판단: {plan.accepted_decision}",
        f"판단 균형: {render_directional_balance(plan.accepted_directional_balance)}",
        (
            f"판단 확신도: {confidence[str(plan.accepted_confidence)]} | "
            f"증거 성숙도: {maturity[str(plan.accepted_overall_maturity)]}"
        ),
        "",
        "🎯 핵심 판단",
        f"• {plan.accepted_reason.text}",
        "",
        "🔄 재평가 조건",
        f"• 상향 재평가: {plan.accepted_upgrade_condition.text}",
        f"• 하향 재평가: {plan.accepted_downgrade_condition.text}",
    ]
    text = "\n".join(lines)
    validation = validate_accepted_v2_render(
        plan,
        rendered_decision=plan.accepted_decision,
        text=text,
        render_mode="production",
    )
    if not validation.valid:
        raise ValueError("accepted_render_invalid:" + ",".join(validation.errors))
    return RenderedProductionAcceptedDecision(
        ticker=packet.ticker,
        accepted_decision=plan.accepted_decision,
        accepted_source=plan.accepted_source,
        accepted_directional_balance=plan.accepted_directional_balance,
        text=text,
        validation=validation,
    )


def accepted_message_quality(
    rendered: tuple[RenderedAcceptedDecision, ...],
) -> dict[str, object]:
    errors: list[str] = []
    texts = [row.text for row in rendered]
    if any(not row.validation.valid for row in rendered):
        errors.append("accepted_render_validation_failed")
    if any(len(text) > 3500 for text in texts):
        errors.append("message_too_long")
    if any(_ORDER_LANGUAGE.search(text) for text in texts):
        errors.append("order_command_language")
    substantive: list[str] = []
    for text in texts:
        for line in text.splitlines():
            normalized = re.sub(r"\s+", " ", line.strip().removeprefix("• "))
            if len(normalized) >= 36 and not normalized.startswith("Shadow 연구 분류이며"):
                substantive.append(normalized)
    repeated = [(text, count) for text, count in Counter(substantive).items() if count >= 2]
    repetition_assessments = [
        {
            "span": text,
            "stock_count": count,
            "classification": classify_repeated_span(
                text,
                stock_count=count,
                evidence_signature_count=count,
            ),
        }
        for text, count in repeated
    ]
    if any(
        item["classification"] == RepetitionClass.MATERIAL_SPAM_REPEAT
        for item in repetition_assessments
    ):
        errors.append("cross_ticker_material_spam_repetition")
    return {
        "contract": "v2-accepted-decision-message-quality-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "message_count": len(texts),
        "average_character_count": (round(sum(map(len, texts)) / len(texts), 2) if texts else 0),
        "max_character_count": max(map(len, texts), default=0),
        "numeric_claim_count": 0,
        "manual_numeric_count": 0,
        "unresolved_numeric_count": 0,
        "repeated_substantive_span_count": len(repeated),
        "repetition_assessments": repetition_assessments,
    }
