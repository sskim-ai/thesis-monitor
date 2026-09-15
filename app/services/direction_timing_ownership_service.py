from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import (
    Confidence,
    Decision,
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    FrozenModel,
)
from app.services.directional_balance_service import (
    DirectionalBalance,
    decision_from_directional_balance,
)
from app.services.directional_financial_context_service import (
    FinancialDecisionContext,
    build_financial_decision_context,
    normalize_sector_framework,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    build_evidence_alias_catalog,
)
from app.services.structured_autonomy_shadow_service import (
    BusinessThesisChange,
    CheckpointKind,
    ClassifiedSellDriver,
    ConfirmationSemantics,
    HolderStance,
    HolderViewV2,
    HoldLean,
    MetricDirection,
    NewBuyerStance,
    NewBuyerViewV2,
    PreferredEntryMode,
    ClaimSemanticMetadata,
    ClaimTimeScope,
    ClaimType,
    SellDriverClass,
    StructuredAutonomyCandidate,
    StructuredEvidenceClaim,
    UnknownTreatmentKind,
    UnknownTreatment,
    derive_hold_lean,
)


CONTRACT_VERSION = "direction-timing-ownership-v1"
CORE_OUTPUT_CONTRACT = "directional-core-output-v1"
TIMING_OUTPUT_CONTRACT = "price-timing-overlay-output-v1"
COMPOSED_OUTPUT_CONTRACT = "direction-timing-composed-shadow-v1"
VALIDATOR_CONTRACT = "direction-timing-ownership-validator-v1"
OWNERSHIP_EXECUTION_MODE = "TWO_STAGE_FENCED"


class EvidenceDomain(StrEnum):
    IDENTITY_SECURITY = "IDENTITY_SECURITY"
    BUSINESS_CURRENT = "BUSINESS_CURRENT"
    EARNINGS_FINANCIAL_CURRENT = "EARNINGS_FINANCIAL_CURRENT"
    LIQUIDITY_CASHFLOW_CURRENT = "LIQUIDITY_CASHFLOW_CURRENT"
    SECTOR_OPERATING_CURRENT = "SECTOR_OPERATING_CURRENT"
    REGULATORY_CAPITAL_CURRENT = "REGULATORY_CAPITAL_CURRENT"
    CLINICAL_REGULATORY_CURRENT = "CLINICAL_REGULATORY_CURRENT"
    CAPITAL_ALLOCATION_CURRENT = "CAPITAL_ALLOCATION_CURRENT"
    VALUATION_SAFE = "VALUATION_SAFE"
    MARKET_EXPECTATIONS = "MARKET_EXPECTATIONS"
    STRUCTURAL_RISK = "STRUCTURAL_RISK"
    MACRO_TRANSMISSION = "MACRO_TRANSMISSION"
    DATA_QUALITY_LIMIT = "DATA_QUALITY_LIMIT"
    PRICE_CONTEXT = "PRICE_CONTEXT"
    OHLCV_TECHNICAL = "OHLCV_TECHNICAL"
    SUPPORT_RESISTANCE = "SUPPORT_RESISTANCE"
    VOLUME_LIQUIDITY = "VOLUME_LIQUIDITY"
    TECHNICAL_STATE = "TECHNICAL_STATE"
    RISK_REWARD_PRICE = "RISK_REWARD_PRICE"
    SUPPLY_POSITIONING = "SUPPLY_POSITIONING"
    AUDIT_TELEMETRY = "AUDIT_TELEMETRY"


class MonitoringTransitionSourceClass(StrEnum):
    PRICE_CONFIRMATION_TRANSITION = "PRICE_CONFIRMATION_TRANSITION"
    PRICE_RISK_REWARD_TRANSITION = "PRICE_RISK_REWARD_TRANSITION"
    PRICE_SUPPORT_RESISTANCE_TRANSITION = "PRICE_SUPPORT_RESISTANCE_TRANSITION"
    SUPPLY_FLOW_TRANSITION = "SUPPLY_FLOW_TRANSITION"
    FUNDAMENTAL_BUSINESS_TRANSITION = "FUNDAMENTAL_BUSINESS_TRANSITION"
    FUNDAMENTAL_FINANCIAL_TRANSITION = "FUNDAMENTAL_FINANCIAL_TRANSITION"
    UNKNOWN_MONITORING_TRANSITION = "UNKNOWN_MONITORING_TRANSITION"


CORE_DOMAINS = frozenset(
    {
        EvidenceDomain.IDENTITY_SECURITY,
        EvidenceDomain.BUSINESS_CURRENT,
        EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
        EvidenceDomain.LIQUIDITY_CASHFLOW_CURRENT,
        EvidenceDomain.SECTOR_OPERATING_CURRENT,
        EvidenceDomain.REGULATORY_CAPITAL_CURRENT,
        EvidenceDomain.CLINICAL_REGULATORY_CURRENT,
        EvidenceDomain.CAPITAL_ALLOCATION_CURRENT,
        EvidenceDomain.VALUATION_SAFE,
        EvidenceDomain.MARKET_EXPECTATIONS,
        EvidenceDomain.STRUCTURAL_RISK,
        EvidenceDomain.MACRO_TRANSMISSION,
        EvidenceDomain.DATA_QUALITY_LIMIT,
    }
)
TIMING_DOMAINS = frozenset(
    {
        EvidenceDomain.PRICE_CONTEXT,
        EvidenceDomain.OHLCV_TECHNICAL,
        EvidenceDomain.SUPPORT_RESISTANCE,
        EvidenceDomain.VOLUME_LIQUIDITY,
        EvidenceDomain.TECHNICAL_STATE,
        EvidenceDomain.RISK_REWARD_PRICE,
        EvidenceDomain.SUPPLY_POSITIONING,
    }
)
MATERIAL_DIRECTIONAL_DOMAINS = frozenset(
    {
        EvidenceDomain.BUSINESS_CURRENT,
        EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
        EvidenceDomain.LIQUIDITY_CASHFLOW_CURRENT,
        EvidenceDomain.SECTOR_OPERATING_CURRENT,
        EvidenceDomain.REGULATORY_CAPITAL_CURRENT,
        EvidenceDomain.CLINICAL_REGULATORY_CURRENT,
        EvidenceDomain.CAPITAL_ALLOCATION_CURRENT,
        EvidenceDomain.VALUATION_SAFE,
        EvidenceDomain.MARKET_EXPECTATIONS,
        EvidenceDomain.STRUCTURAL_RISK,
    }
)


_FAMILY_DOMAINS: dict[str, EvidenceDomain] = {
    domain.value: domain
    for domain in EvidenceDomain
    if domain
    not in {EvidenceDomain.DATA_QUALITY_LIMIT, EvidenceDomain.AUDIT_TELEMETRY}
}

_FUNDAMENTAL_BUSINESS_TRANSITION_FAMILIES = frozenset(
    {
        EvidenceDomain.BUSINESS_CURRENT.value,
        EvidenceDomain.SECTOR_OPERATING_CURRENT.value,
        EvidenceDomain.REGULATORY_CAPITAL_CURRENT.value,
        EvidenceDomain.CLINICAL_REGULATORY_CURRENT.value,
        EvidenceDomain.CAPITAL_ALLOCATION_CURRENT.value,
    }
)
_FUNDAMENTAL_FINANCIAL_TRANSITION_FAMILIES = frozenset(
    {
        EvidenceDomain.EARNINGS_FINANCIAL_CURRENT.value,
        EvidenceDomain.LIQUIDITY_CASHFLOW_CURRENT.value,
    }
)


class OwnedEvidenceRef(FrozenModel):
    ref: DecisionEvidenceRef
    domain: EvidenceDomain
    source_owned_domain: bool = True


class OwnedEvidencePacket(FrozenModel):
    contract: str = CONTRACT_VERSION
    source_packet: DecisionEvidencePacket
    evidence: tuple[OwnedEvidenceRef, ...]
    sector_framework: str = "unspecified"

    @property
    def domain_by_ref(self) -> dict[str, EvidenceDomain]:
        return {row.ref.ref_id: row.domain for row in self.evidence}

    @property
    def core_refs(self) -> frozenset[str]:
        return frozenset(
            row.ref.ref_id for row in self.evidence if row.domain in CORE_DOMAINS
        )

    @property
    def timing_refs(self) -> frozenset[str]:
        return frozenset(
            row.ref.ref_id for row in self.evidence if row.domain in TIMING_DOMAINS
        )


class CoreNewBuyerView(FrozenModel):
    stance: NewBuyerStance
    summary: str = Field(min_length=1, max_length=420)
    confirmation_business_condition: str = Field(min_length=1, max_length=420)
    confirmation_business_condition_refs: tuple[str, ...] = Field(
        min_length=1, max_length=6
    )


class CoreHolderView(FrozenModel):
    stance: HolderStance
    summary: str = Field(min_length=1, max_length=420)
    business_invalidation_condition: str = Field(min_length=1, max_length=420)
    business_invalidation_condition_refs: tuple[str, ...] = Field(
        min_length=1, max_length=6
    )


class DirectionalClaim(FrozenModel):
    text: str = Field(min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)


class DirectionalSellDriver(DirectionalClaim):
    classification: SellDriverClass


class DirectionalUnknown(FrozenModel):
    summary: str = Field(min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    treatment: UnknownTreatmentKind
    directional_negative_basis: tuple[str, ...] = Field(max_length=6)


class DirectionalCoreCandidate(FrozenModel):
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
    fundamental_new_buyer: CoreNewBuyerView
    fundamental_holder: CoreHolderView
    business_reevaluation_up: tuple[DirectionalClaim, ...] = Field(
        min_length=1, max_length=3
    )
    business_reevaluation_down: tuple[DirectionalClaim, ...] = Field(
        min_length=1, max_length=3
    )

    @model_validator(mode="after")
    def validate_directional_identity(self) -> DirectionalCoreCandidate:
        if decision_from_directional_balance(self.directional_balance) != self.overall_direction:
            raise ValueError("directional_core_decision_balance_mismatch")
        expected = derive_hold_lean(self.overall_direction, self.directional_balance)
        if self.hold_lean != expected:
            raise ValueError("directional_core_hold_lean_mismatch")
        return self


class DirectionalCoreBatch(FrozenModel):
    contract: Literal["directional-core-output-v1"] = CORE_OUTPUT_CONTRACT
    packet_id: str
    candidates: tuple[DirectionalCoreCandidate, ...] = Field(min_length=1, max_length=4)


class TechnicalState(StrEnum):
    FAVORABLE = "FAVORABLE"
    NEUTRAL = "NEUTRAL"
    CAUTION = "CAUTION"
    ADVERSE = "ADVERSE"
    UNKNOWN = "UNKNOWN"


class TimingNewBuyerModifier(StrEnum):
    ALLOW = "ALLOW"
    WAIT = "WAIT"
    AVOID = "AVOID"


class HolderPriceReview(StrEnum):
    NONE = "NONE"
    REVIEW = "REVIEW"


class TimingClaim(FrozenModel):
    text: str = Field(min_length=1, max_length=420)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)


class PriceTimingCandidate(FrozenModel):
    ticker: str
    core_fingerprint: str
    technical_state: TechnicalState
    timing_new_buyer_modifier: TimingNewBuyerModifier
    entry_mode: PreferredEntryMode
    entry_reason: str = Field(min_length=1, max_length=420)
    pullback_entry_zone_low: float | None
    pullback_entry_zone_high: float | None
    pullback_entry_basis: tuple[str, ...] = Field(max_length=6)
    breakout_confirmation_level: float | None
    breakout_confirmation_basis: tuple[str, ...] = Field(max_length=6)
    confirmation_semantics: ConfirmationSemantics
    holder_price_review: HolderPriceReview
    upside_trim_zone_low: float | None
    upside_trim_zone_high: float | None
    upside_trim_basis: tuple[str, ...] = Field(max_length=6)
    downside_review_level: float | None
    downside_review_basis: tuple[str, ...] = Field(max_length=6)
    currency: str | None
    price_review_context: TimingClaim
    price_confirmation_context: TimingClaim
    price_support_context: TimingClaim
    technical_rationale: TimingClaim
    supply_positioning_rationale: TimingClaim | None


class PriceTimingBatch(FrozenModel):
    contract: Literal["price-timing-overlay-output-v1"] = TIMING_OUTPUT_CONTRACT
    packet_id: str
    candidates: tuple[PriceTimingCandidate, ...] = Field(min_length=1, max_length=4)


class ComposedDecision(FrozenModel):
    contract: str = COMPOSED_OUTPUT_CONTRACT
    core: DirectionalCoreCandidate
    timing: PriceTimingCandidate
    candidate: StructuredAutonomyCandidate
    core_fingerprint: str
    timing_fingerprint: str


class OwnershipValidation(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]
    directional_core_price_technical_refs: int
    directional_core_supply_refs: int
    buy_without_nonprice_material_anchor: int
    sell_without_nonprice_material_anchor: int
    timing_stage_direction_mutation: int = 0
    timing_stage_balance_mutation: int = 0
    timing_stage_hold_lean_mutation: int = 0
    price_timing_new_buyer_upgrade: int
    price_only_holder_reduce: int


class DirectionalCoreOwnershipValidation(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...]
    directional_core_price_technical_refs: int
    directional_core_supply_refs: int
    directional_core_unknown_refs: int
    buy_without_nonprice_material_anchor: int
    sell_without_nonprice_material_anchor: int


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _fact_family_by_id(stock: Mapping[str, object]) -> dict[str, str]:
    rows = stock.get("fact_catalog")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return {}
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("fact_id"):
            continue
        family = row.get("evidence_family")
        if family:
            result[str(row["fact_id"])] = str(family)
    return result


def _feature_name(ref: DecisionEvidenceRef) -> str:
    if ref.ref_id.startswith("technical-feature:"):
        return ref.source_ref.rsplit(".", 1)[-1].lower()
    return ""


def _fact_id_for_ref(ref: DecisionEvidenceRef) -> str | None:
    prefix = "stock.fact_catalog."
    if not ref.source_ref.startswith(prefix):
        return None
    return ref.source_ref.removeprefix(prefix)


def monitoring_transition_source_class(
    ref: DecisionEvidenceRef,
    *,
    fact_family_by_id: Mapping[str, str],
) -> MonitoringTransitionSourceClass | None:
    """Classify monitoring transitions from canonical lineage, not display wording."""

    fact_id = _fact_id_for_ref(ref)
    if fact_id is None:
        return None
    label = ref.label.casefold()
    is_transition = fact_id.startswith("monitoring:") or label in {
        "monitoring_transition",
        "monitoring_metric_transition",
    }
    if not is_transition:
        return None

    if fact_id == "monitoring:confirmation_transition":
        return MonitoringTransitionSourceClass.PRICE_CONFIRMATION_TRANSITION
    if fact_id == "monitoring:risk_reward_transition":
        return MonitoringTransitionSourceClass.PRICE_RISK_REWARD_TRANSITION

    family = fact_family_by_id.get(fact_id)
    identity = f"{fact_id}|{ref.source_ref}".casefold()
    if family == EvidenceDomain.PRICE_CONTEXT.value and any(
        token in identity for token in ("support", "resistance", "invalidation")
    ):
        return MonitoringTransitionSourceClass.PRICE_SUPPORT_RESISTANCE_TRANSITION
    if family == EvidenceDomain.SUPPLY_POSITIONING.value:
        return MonitoringTransitionSourceClass.SUPPLY_FLOW_TRANSITION
    if family in _FUNDAMENTAL_BUSINESS_TRANSITION_FAMILIES:
        return MonitoringTransitionSourceClass.FUNDAMENTAL_BUSINESS_TRANSITION
    if family in _FUNDAMENTAL_FINANCIAL_TRANSITION_FAMILIES:
        return MonitoringTransitionSourceClass.FUNDAMENTAL_FINANCIAL_TRANSITION
    return MonitoringTransitionSourceClass.UNKNOWN_MONITORING_TRANSITION


def _monitoring_transition_domain(
    source_class: MonitoringTransitionSourceClass,
    *,
    fact_id: str,
    fact_family_by_id: Mapping[str, str],
) -> EvidenceDomain:
    if source_class == MonitoringTransitionSourceClass.PRICE_CONFIRMATION_TRANSITION:
        return EvidenceDomain.TECHNICAL_STATE
    if source_class == MonitoringTransitionSourceClass.PRICE_RISK_REWARD_TRANSITION:
        return EvidenceDomain.RISK_REWARD_PRICE
    if source_class == MonitoringTransitionSourceClass.PRICE_SUPPORT_RESISTANCE_TRANSITION:
        return EvidenceDomain.SUPPORT_RESISTANCE
    if source_class == MonitoringTransitionSourceClass.SUPPLY_FLOW_TRANSITION:
        return EvidenceDomain.SUPPLY_POSITIONING
    if source_class in {
        MonitoringTransitionSourceClass.FUNDAMENTAL_BUSINESS_TRANSITION,
        MonitoringTransitionSourceClass.FUNDAMENTAL_FINANCIAL_TRANSITION,
    }:
        family = fact_family_by_id.get(fact_id)
        if family in _FAMILY_DOMAINS:
            return _FAMILY_DOMAINS[family]
    return EvidenceDomain.AUDIT_TELEMETRY


def evidence_domain(
    ref: DecisionEvidenceRef,
    *,
    fact_family_by_id: Mapping[str, str],
) -> EvidenceDomain:
    prefix = "stock.fact_catalog."
    if ref.source_ref.startswith(prefix):
        fact_id = ref.source_ref.removeprefix(prefix)
        transition_class = monitoring_transition_source_class(
            ref,
            fact_family_by_id=fact_family_by_id,
        )
        if transition_class is not None:
            return _monitoring_transition_domain(
                transition_class,
                fact_id=fact_id,
                fact_family_by_id=fact_family_by_id,
            )
        family = fact_family_by_id.get(fact_id)
        if family in _FAMILY_DOMAINS:
            return _FAMILY_DOMAINS[family]

    if ref.category == EvidenceCategory.TECHNICAL_FEATURE:
        feature = _feature_name(ref)
        if any(token in feature for token in ("volume", "obv", "cmf", "mfi")):
            return EvidenceDomain.VOLUME_LIQUIDITY
        return EvidenceDomain.OHLCV_TECHNICAL
    if ref.category == EvidenceCategory.PRICE_STRUCTURE:
        identity = f"{ref.ref_id}|{ref.source_ref}".lower()
        if "risk_reward" in identity:
            return EvidenceDomain.RISK_REWARD_PRICE
        if any(
            token in identity
            for token in ("support", "resistance", "zone", "box", "fibonacci", "invalidation")
        ):
            return EvidenceDomain.SUPPORT_RESISTANCE
        if "price:current" in identity or "current_price_context" in identity:
            return EvidenceDomain.PRICE_CONTEXT
        return EvidenceDomain.TECHNICAL_STATE
    if ref.category == EvidenceCategory.FLOWS:
        return EvidenceDomain.SUPPLY_POSITIONING
    if ref.ref_id.startswith("technical-context:"):
        return EvidenceDomain.TECHNICAL_STATE
    if ref.source_ref == "stock.market_transmission":
        return EvidenceDomain.MACRO_TRANSMISSION
    if ref.source_ref == "stock.thesis.market_expectations":
        return EvidenceDomain.MARKET_EXPECTATIONS
    if ref.category == EvidenceCategory.THESIS:
        return EvidenceDomain.BUSINESS_CURRENT
    if ref.category == EvidenceCategory.EARNINGS:
        return EvidenceDomain.EARNINGS_FINANCIAL_CURRENT
    if ref.category == EvidenceCategory.EARNINGS_QUALITY:
        return EvidenceDomain.SECTOR_OPERATING_CURRENT
    if ref.category == EvidenceCategory.EXPECTATIONS:
        return EvidenceDomain.MARKET_EXPECTATIONS
    if ref.category == EvidenceCategory.VALUATION:
        return EvidenceDomain.VALUATION_SAFE
    if ref.category == EvidenceCategory.CATALYSTS:
        return EvidenceDomain.BUSINESS_CURRENT
    if ref.category == EvidenceCategory.RISKS:
        return EvidenceDomain.STRUCTURAL_RISK
    if ref.category == EvidenceCategory.MACRO:
        return EvidenceDomain.MACRO_TRANSMISSION
    if ref.category == EvidenceCategory.MARKET:
        return EvidenceDomain.MACRO_TRANSMISSION
    if ref.category == EvidenceCategory.UNKNOWN:
        return EvidenceDomain.DATA_QUALITY_LIMIT
    if ref.category == EvidenceCategory.QUALITY:
        identity = f"{ref.ref_id}|{ref.source_ref}".lower()
        if "security" in identity or "identity" in identity:
            return EvidenceDomain.IDENTITY_SECURITY
        return EvidenceDomain.DATA_QUALITY_LIMIT
    raise ValueError(f"unclassified_evidence_domain:{ref.ref_id}:{ref.category}")


def build_owned_evidence_packet(
    packet: DecisionEvidencePacket,
    *,
    stock: Mapping[str, object],
) -> OwnedEvidencePacket:
    families = _fact_family_by_id(stock)
    rows = tuple(
        OwnedEvidenceRef(
            ref=ref,
            domain=evidence_domain(ref, fact_family_by_id=families),
        )
        for ref in packet.evidence
    )
    if len(rows) != len(packet.evidence):
        raise ValueError("evidence_domain_registry_incomplete")
    source_sufficiency = stock.get("source_sufficiency")
    source_sufficiency = (
        source_sufficiency if isinstance(source_sufficiency, Mapping) else {}
    )
    framework = (
        stock.get("analysis_framework")
        or stock.get("sector_framework")
        or source_sufficiency.get("framework")
    )
    return OwnedEvidencePacket(
        source_packet=packet,
        evidence=rows,
        sector_framework=normalize_sector_framework(framework),
    )


def financial_decision_context_for_owned(
    owned: OwnedEvidencePacket,
) -> FinancialDecisionContext | None:
    return build_financial_decision_context(
        tuple(row.ref for row in owned.evidence if row.domain in CORE_DOMAINS),
        sector_framework=owned.sector_framework,
    )


def stage_alias_catalogs(
    owned: OwnedEvidencePacket,
) -> tuple[EvidenceAliasCatalog, EvidenceAliasCatalog]:
    packet = owned.source_packet
    financial_context = financial_decision_context_for_owned(owned)
    selected_financial_refs = (
        {item.evidence_id for item in financial_context.evidence_items}
        if financial_context is not None
        else set()
    )
    core_packet = packet.model_copy(
        update={
            "evidence": tuple(
                row.ref
                for row in owned.evidence
                if row.domain in CORE_DOMAINS
                and (
                    row.ref.financial_context is None
                    or row.ref.ref_id in selected_financial_refs
                )
            )
        }
    )
    timing_packet = packet.model_copy(
        update={"evidence": tuple(row.ref for row in owned.evidence if row.domain in TIMING_DOMAINS)}
    )
    return build_evidence_alias_catalog(core_packet), build_evidence_alias_catalog(timing_packet)


def core_fingerprint(core: DirectionalCoreCandidate) -> str:
    return canonical_sha256(core.model_dump(mode="json"))


def _claim_refs(value: object) -> set[str]:
    refs: set[str] = set()

    def collect(item: object, key: str | None = None) -> None:
        if isinstance(item, Mapping):
            for child_key, child in item.items():
                collect(child, str(child_key))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            if key == "evidence_refs" or key == "material_directional_anchor_basis" or (
                key is not None and key.endswith("_basis")
            ):
                refs.update(str(child) for child in item)
            else:
                for child in item:
                    collect(child, key)

    collect(value)
    return refs


def _new_buyer_stance(
    stance: NewBuyerStance, modifier: TimingNewBuyerModifier
) -> NewBuyerStance:
    if stance == "AVOID" or modifier == TimingNewBuyerModifier.AVOID:
        return "AVOID"
    if stance == "WAIT" or modifier == TimingNewBuyerModifier.WAIT:
        return "WAIT"
    return "ATTRACTIVE"


def _holder_stance(
    stance: HolderStance, price_review: HolderPriceReview
) -> HolderStance:
    if stance == "REDUCE":
        return "REDUCE"
    if stance == "REVIEW" or price_review == HolderPriceReview.REVIEW:
        return "REVIEW"
    return "HOLDABLE"


def _structured_claim(value: DirectionalClaim | TimingClaim) -> StructuredEvidenceClaim:
    return StructuredEvidenceClaim(text=value.text, evidence_refs=value.evidence_refs)


def _future_claim(
    value: DirectionalClaim,
    *,
    kind: CheckpointKind,
    direction: MetricDirection,
) -> StructuredEvidenceClaim:
    return StructuredEvidenceClaim(
        text=value.text,
        evidence_refs=value.evidence_refs,
        semantic=ClaimSemanticMetadata(
            claim_type=ClaimType.FUTURE_CHECKPOINT,
            time_scope=ClaimTimeScope.FUTURE_CHECKPOINT,
            checkpoint_kind=kind,
            direction=direction,
        ),
    )


def compose_decision(
    core: DirectionalCoreCandidate,
    timing: PriceTimingCandidate,
) -> ComposedDecision:
    fingerprint = core_fingerprint(core)
    if core.ticker != timing.ticker:
        raise ValueError("cross_subject_direction_timing_composition")
    if timing.core_fingerprint != fingerprint:
        raise ValueError("price_timing_core_fingerprint_mismatch")
    buyer_stance = _new_buyer_stance(
        core.fundamental_new_buyer.stance, timing.timing_new_buyer_modifier
    )
    holder_stance = _holder_stance(
        core.fundamental_holder.stance, timing.holder_price_review
    )
    candidate = StructuredAutonomyCandidate(
        ticker=core.ticker,
        decision=core.overall_direction,
        directional_balance=core.directional_balance,
        decision_confidence=core.directional_confidence,
        business_thesis_change=core.business_thesis_change,
        business_thesis_context=_structured_claim(core.business_thesis_context),
        earnings_estimate_context=_structured_claim(core.earnings_estimate_context),
        market_expectation_context=_structured_claim(core.market_expectation_context),
        valuation_context=_structured_claim(core.valuation_context),
        price_timing_context=_structured_claim(timing.price_review_context),
        risk_context=_structured_claim(core.risk_context),
        sector_interpretation=_structured_claim(core.sector_interpretation),
        buy_drivers=tuple(_structured_claim(row) for row in core.buy_drivers),
        sell_drivers=tuple(
            ClassifiedSellDriver(
                text=row.text,
                evidence_refs=row.evidence_refs,
                classification=row.classification,
            )
            for row in core.sell_drivers
        ),
        dominant_evidence=_structured_claim(core.dominant_evidence),
        uncertainty_limit=_structured_claim(core.uncertainty_limit),
        core_judgment=_structured_claim(core.core_investment_judgment),
        unknown_treatments=tuple(
            UnknownTreatment(
                summary=row.summary,
                evidence_refs=row.evidence_refs,
                treatment=row.treatment,
                directional_negative_basis=row.directional_negative_basis,
            )
            for row in core.unknown_treatments
        ),
        new_buyer_view=NewBuyerViewV2(
            stance=buyer_stance,
            summary=core.fundamental_new_buyer.summary,
            pullback_entry_zone_low=timing.pullback_entry_zone_low,
            pullback_entry_zone_high=timing.pullback_entry_zone_high,
            pullback_entry_basis=timing.pullback_entry_basis,
            breakout_confirmation_level=timing.breakout_confirmation_level,
            breakout_confirmation_basis=timing.breakout_confirmation_basis,
            currency=timing.currency,
            preferred_entry_mode=timing.entry_mode,
            preferred_entry_reason=timing.entry_reason,
            confirmation_semantics=timing.confirmation_semantics,
            confirmation_business_condition=(
                core.fundamental_new_buyer.confirmation_business_condition
            ),
            confirmation_business_condition_refs=(
                core.fundamental_new_buyer.confirmation_business_condition_refs
            ),
        ),
        holder_view=HolderViewV2(
            stance=holder_stance,
            summary=core.fundamental_holder.summary,
            upside_trim_zone_low=timing.upside_trim_zone_low,
            upside_trim_zone_high=timing.upside_trim_zone_high,
            upside_trim_basis=timing.upside_trim_basis,
            downside_review_level=timing.downside_review_level,
            downside_review_basis=timing.downside_review_basis,
            currency=timing.currency,
            business_invalidation_condition=(
                core.fundamental_holder.business_invalidation_condition
            ),
            business_invalidation_condition_refs=(
                core.fundamental_holder.business_invalidation_condition_refs
            ),
        ),
        reevaluation_up=tuple(
            _future_claim(
                row,
                kind=CheckpointKind.STRENGTHEN,
                direction=MetricDirection.IMPROVE,
            )
            for row in core.business_reevaluation_up
        ),
        reevaluation_down=tuple(
            _future_claim(
                row,
                kind=CheckpointKind.WEAKEN,
                direction=MetricDirection.DETERIORATE,
            )
            for row in core.business_reevaluation_down
        ),
    )
    return ComposedDecision(
        core=core,
        timing=timing,
        candidate=candidate,
        core_fingerprint=fingerprint,
        timing_fingerprint=canonical_sha256(timing.model_dump(mode="json")),
    )


def validate_ownership(
    owned: OwnedEvidencePacket,
    core: DirectionalCoreCandidate,
    timing: PriceTimingCandidate,
    composed: ComposedDecision | None = None,
) -> OwnershipValidation:
    errors: list[str] = []
    domains = owned.domain_by_ref
    core_refs = _claim_refs(core.model_dump(mode="json"))
    timing_refs = _claim_refs(timing.model_dump(mode="json"))
    price_refs = sorted(
        ref
        for ref in core_refs
        if domains.get(ref) in TIMING_DOMAINS
        and domains.get(ref) != EvidenceDomain.SUPPLY_POSITIONING
    )
    supply_refs = sorted(
        ref for ref in core_refs if domains.get(ref) == EvidenceDomain.SUPPLY_POSITIONING
    )
    unsupported_core = sorted(ref for ref in core_refs if domains.get(ref) not in CORE_DOMAINS)
    unsupported_timing = sorted(
        ref for ref in timing_refs if domains.get(ref) not in TIMING_DOMAINS
    )
    if price_refs:
        errors.append("directional_core_contains_price_or_technical_ref")
    if supply_refs:
        errors.append("directional_core_contains_supply_ref")
    if unsupported_core:
        errors.append("directional_core_ref_outside_domain_registry")
    if unsupported_timing:
        errors.append("price_timing_ref_outside_domain_registry")
    if timing.core_fingerprint != core_fingerprint(core):
        errors.append("price_timing_core_fingerprint_mismatch")
    if timing.supply_positioning_rationale is not None and any(
        domains.get(ref) != EvidenceDomain.SUPPLY_POSITIONING
        for ref in timing.supply_positioning_rationale.evidence_refs
    ):
        errors.append("supply_rationale_without_supply_owned_evidence")

    material_anchors = {
        ref
        for ref in core.material_directional_anchor_basis
        if domains.get(ref) in MATERIAL_DIRECTIONAL_DOMAINS
    }
    buy_missing = int(core.overall_direction == "BUY" and not material_anchors)
    sell_missing = int(core.overall_direction == "SELL" and not material_anchors)
    if buy_missing:
        errors.append("buy_without_nonprice_material_anchor")
    if sell_missing:
        errors.append("sell_without_nonprice_material_anchor")

    expected_buyer = _new_buyer_stance(
        core.fundamental_new_buyer.stance, timing.timing_new_buyer_modifier
    )
    expected_holder = _holder_stance(
        core.fundamental_holder.stance, timing.holder_price_review
    )
    upgrade = 0
    reduce = 0
    if composed is not None:
        candidate = composed.candidate
        if candidate.decision != core.overall_direction:
            errors.append("timing_stage_direction_mutation")
        if candidate.directional_balance != core.directional_balance:
            errors.append("timing_stage_balance_mutation")
        if derive_hold_lean(candidate.decision, candidate.directional_balance) != core.hold_lean:
            errors.append("timing_stage_hold_lean_mutation")
        if candidate.new_buyer_view.stance != expected_buyer:
            upgrade = 1
            errors.append("price_timing_new_buyer_upgrade")
        if candidate.holder_view.stance != expected_holder:
            errors.append("holder_composition_mismatch")
        if (
            candidate.holder_view.stance == "REDUCE"
            and core.fundamental_holder.stance != "REDUCE"
        ):
            reduce = 1
            errors.append("price_only_holder_reduce")
        if (
            candidate.holder_view.business_invalidation_condition
            != core.fundamental_holder.business_invalidation_condition
            or candidate.holder_view.business_invalidation_condition_refs
            != core.fundamental_holder.business_invalidation_condition_refs
        ):
            errors.append("technical_breakdown_mapped_to_business_invalidation")
    return OwnershipValidation(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
        directional_core_price_technical_refs=len(price_refs),
        directional_core_supply_refs=len(supply_refs),
        buy_without_nonprice_material_anchor=buy_missing,
        sell_without_nonprice_material_anchor=sell_missing,
        price_timing_new_buyer_upgrade=upgrade,
        price_only_holder_reduce=reduce,
    )


def validate_directional_core_ownership(
    owned: OwnedEvidencePacket,
    core: DirectionalCoreCandidate,
    *,
    allowed_core_ref_ids: Sequence[str] | None = None,
) -> DirectionalCoreOwnershipValidation:
    errors: list[str] = []
    domains = owned.domain_by_ref
    core_refs = _claim_refs(core.model_dump(mode="json"))
    allowed = set(allowed_core_ref_ids or owned.core_refs)
    price_refs = sorted(
        ref
        for ref in core_refs
        if domains.get(ref) in TIMING_DOMAINS
        and domains.get(ref) != EvidenceDomain.SUPPLY_POSITIONING
    )
    supply_refs = sorted(
        ref for ref in core_refs if domains.get(ref) == EvidenceDomain.SUPPLY_POSITIONING
    )
    unknown_refs = sorted(ref for ref in core_refs if ref not in allowed)
    unsupported_core = sorted(
        ref for ref in core_refs if domains.get(ref) not in CORE_DOMAINS
    )
    if price_refs:
        errors.append("directional_core_contains_price_or_technical_ref")
    if supply_refs:
        errors.append("directional_core_contains_supply_ref")
    if unknown_refs:
        errors.append("directional_core_ref_not_supplied_to_stage")
    if unsupported_core:
        errors.append("directional_core_ref_outside_domain_registry")

    material_anchors = {
        ref
        for ref in core.material_directional_anchor_basis
        if domains.get(ref) in MATERIAL_DIRECTIONAL_DOMAINS and ref in allowed
    }
    buy_missing = int(core.overall_direction == "BUY" and not material_anchors)
    sell_missing = int(core.overall_direction == "SELL" and not material_anchors)
    if buy_missing:
        errors.append("buy_without_nonprice_material_anchor")
    if sell_missing:
        errors.append("sell_without_nonprice_material_anchor")
    return DirectionalCoreOwnershipValidation(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
        directional_core_price_technical_refs=len(price_refs),
        directional_core_supply_refs=len(supply_refs),
        directional_core_unknown_refs=len(unknown_refs),
        buy_without_nonprice_material_anchor=buy_missing,
        sell_without_nonprice_material_anchor=sell_missing,
    )


def technical_feature_inventory(owned: OwnedEvidencePacket) -> dict[str, object]:
    rows = [row for row in owned.evidence if row.domain in TIMING_DOMAINS]
    names = sorted({_feature_name(row.ref) for row in rows if _feature_name(row.ref)})
    def available(*tokens: str) -> bool:
        return any(any(token in name for token in tokens) for name in names)
    return {
        "technical_ref_count": len(rows),
        "feature_count": len(names),
        "support_resistance": any(
            row.domain == EvidenceDomain.SUPPORT_RESISTANCE for row in rows
        ),
        "volume": available("volume", "obv", "cmf", "mfi"),
        "rsi": available("rsi"),
        "macd": available("macd"),
        "bollinger": available("bollinger"),
        "moving_average": available("sma", "ema"),
        "risk_reward": any(row.domain == EvidenceDomain.RISK_REWARD_PRICE for row in rows),
        "supply_positioning": any(
            row.domain == EvidenceDomain.SUPPLY_POSITIONING for row in rows
        ),
        "unavailable_is_zero": False,
        "invented_feature_count": 0,
    }
