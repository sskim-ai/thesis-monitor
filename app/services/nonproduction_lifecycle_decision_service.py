from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import FrozenModel
from app.services.direction_timing_ownership_service import (
    ComposedDecision,
    DirectionalCoreCandidate,
    OwnedEvidencePacket,
    OwnershipValidation,
    PriceTimingCandidate,
    canonical_sha256,
    compose_decision,
    validate_ownership,
)
from app.services.structured_autonomy_shadow_service import (
    RenderedStructuredAutonomy,
    StructuredAutonomyValidation,
    render_structured_autonomy_message,
    unknown_treatment_consistency_issues,
)


CONTRACT_VERSION = "nonproduction-lifecycle-decision-integration-v1"
DERIVATIVE_LABEL = "OFFLINE_NONPRODUCTION_DERIVATIVE"


class LifecycleMode(StrEnum):
    INITIAL_ABSOLUTE = "INITIAL_ABSOLUTE"
    MONITORING_BASELINE = "MONITORING_BASELINE"
    DAILY_DELTA = "DAILY_DELTA"


class SubjectLifecycle(StrEnum):
    NEW_ISSUER = "NEW_ISSUER"
    EXISTING_MONITORED = "EXISTING_MONITORED"


class RefreshState(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"


class PriceEvidenceState(StrEnum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"


class EvidenceChangeScope(StrEnum):
    NONE = "NONE"
    BUSINESS = "BUSINESS"
    PRICE_ONLY = "PRICE_ONLY"
    UNKNOWN = "UNKNOWN"


class DeltaState(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NO_MATERIAL_CHANGE = "NO_MATERIAL_CHANGE"
    STRENGTHENED = "STRENGTHENED"
    WEAKENED = "WEAKENED"
    MIXED = "MIXED"
    INVALIDATED = "INVALIDATED"
    PRICE_ONLY_CONTEXT = "PRICE_ONLY_CONTEXT"
    UNAVAILABLE = "UNAVAILABLE"


class IntentKind(StrEnum):
    REGISTRATION_CONTINUATION = "REGISTRATION_CONTINUATION"
    BASELINE = "BASELINE"
    ONBOARDING_RESUME = "ONBOARDING_RESUME"
    ASSESSMENT = "ASSESSMENT"
    FILE_ONLY_DELIVERY = "FILE_ONLY_DELIVERY"


class NonproductionLifecycleContext(FrozenModel):
    contract: str = CONTRACT_VERSION
    fixture_id: str = Field(min_length=1)
    mode: LifecycleMode
    subject_lifecycle: SubjectLifecycle
    explicit_monitoring_intent: bool = False
    onboarding_complete: bool = False
    refresh_state: RefreshState = RefreshState.AVAILABLE
    price_evidence_state: PriceEvidenceState = PriceEvidenceState.READY
    evidence_change_scope: EvidenceChangeScope = EvidenceChangeScope.NONE
    delta_state: DeltaState = DeltaState.NOT_APPLICABLE
    delta_summary: str | None = None
    baseline_ref: str | None = None
    baseline_cutoff: str | None = None
    bootstrap_enrichment: bool = False

    @model_validator(mode="after")
    def validate_lifecycle_semantics(self) -> NonproductionLifecycleContext:
        daily = self.mode == LifecycleMode.DAILY_DELTA
        if not daily and self.delta_state != DeltaState.NOT_APPLICABLE:
            raise ValueError("absolute_or_baseline_cannot_claim_daily_delta")
        if daily and self.delta_state == DeltaState.NOT_APPLICABLE:
            raise ValueError("daily_delta_state_required")
        if daily and (not self.baseline_ref or not self.baseline_cutoff):
            raise ValueError("daily_delta_requires_baseline_and_cutoff")
        if self.refresh_state in {RefreshState.MISSING, RefreshState.UNAVAILABLE}:
            if self.delta_state != DeltaState.UNAVAILABLE:
                raise ValueError("missing_refresh_cannot_be_no_material_change")
        if self.evidence_change_scope == EvidenceChangeScope.PRICE_ONLY:
            if self.delta_state != DeltaState.PRICE_ONLY_CONTEXT:
                raise ValueError("price_only_change_cannot_be_thesis_delta")
        if self.bootstrap_enrichment and self.delta_state in {
            DeltaState.STRENGTHENED,
            DeltaState.WEAKENED,
            DeltaState.MIXED,
            DeltaState.INVALIDATED,
        }:
            raise ValueError("bootstrap_enrichment_cannot_be_daily_thesis_delta")
        return self

    @property
    def registration_allowed(self) -> bool:
        return self.explicit_monitoring_intent

    @property
    def monitoring_ready(self) -> bool:
        return self.explicit_monitoring_intent and self.onboarding_complete


class NonproductionIntent(FrozenModel):
    kind: IntentKind
    idempotency_key: str
    production_effect: str = "NONE"


class LifecycleCandidateValidation(FrozenModel):
    valid: bool
    errors: tuple[str, ...]


class NonproductionDerivative(FrozenModel):
    contract: str = CONTRACT_VERSION
    label: str = DERIVATIVE_LABEL
    lifecycle: NonproductionLifecycleContext
    composed: ComposedDecision
    ownership: OwnershipValidation
    candidate_validation: StructuredAutonomyValidation
    lifecycle_validation: LifecycleCandidateValidation
    intents: tuple[NonproductionIntent, ...]
    lineage: dict[str, str]
    structured_text: str
    text: str
    production_db_mutations: int = 0
    monitoring_registrations: int = 0
    assessment_persistence_mutations: int = 0
    warning_mutations: int = 0
    notification_queue_writes: int = 0
    production_sends: int = 0


@dataclass
class InMemoryIntentLedger:
    _seen: dict[str, NonproductionIntent] = field(default_factory=dict)

    def apply(self, intents: tuple[NonproductionIntent, ...]) -> tuple[NonproductionIntent, ...]:
        inserted: list[NonproductionIntent] = []
        for intent in intents:
            if intent.idempotency_key in self._seen:
                continue
            self._seen[intent.idempotency_key] = intent
            inserted.append(intent)
        return tuple(inserted)

    @property
    def count(self) -> int:
        return len(self._seen)


def _intent_key(
    lifecycle: NonproductionLifecycleContext,
    packet_id: str,
    kind: IntentKind,
) -> str:
    payload = (
        f"{CONTRACT_VERSION}|{lifecycle.fixture_id}|{lifecycle.mode}|"
        f"{packet_id}|{kind}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def plan_nonproduction_intents(
    lifecycle: NonproductionLifecycleContext,
    *,
    packet_id: str,
) -> tuple[NonproductionIntent, ...]:
    kinds: list[IntentKind] = []
    if lifecycle.registration_allowed:
        kinds.append(IntentKind.REGISTRATION_CONTINUATION)
        if not lifecycle.onboarding_complete:
            kinds.append(IntentKind.ONBOARDING_RESUME)
    if lifecycle.mode == LifecycleMode.MONITORING_BASELINE:
        kinds.append(IntentKind.BASELINE)
    kinds.extend((IntentKind.ASSESSMENT, IntentKind.FILE_ONLY_DELIVERY))
    return tuple(
        NonproductionIntent(
            kind=kind,
            idempotency_key=_intent_key(lifecycle, packet_id, kind),
        )
        for kind in kinds
    )


def validate_lifecycle_candidate(
    lifecycle: NonproductionLifecycleContext,
    core: DirectionalCoreCandidate,
    timing: PriceTimingCandidate,
) -> LifecycleCandidateValidation:
    errors: list[str] = []
    change = core.business_thesis_change
    if lifecycle.mode != LifecycleMode.DAILY_DELTA and change in {
        "STRENGTHENED",
        "WEAKENED",
    }:
        errors.append("absolute_or_baseline_candidate_claims_directional_delta")

    expected_changes = {
        DeltaState.NO_MATERIAL_CHANGE: {"UNCHANGED"},
        DeltaState.STRENGTHENED: {"STRENGTHENED"},
        DeltaState.WEAKENED: {"WEAKENED"},
        DeltaState.MIXED: {"UNRESOLVED"},
        DeltaState.INVALIDATED: {"WEAKENED"},
        DeltaState.PRICE_ONLY_CONTEXT: {"UNCHANGED"},
        DeltaState.UNAVAILABLE: {"UNRESOLVED"},
    }
    expected = expected_changes.get(lifecycle.delta_state)
    if lifecycle.mode == LifecycleMode.DAILY_DELTA and expected and change not in expected:
        errors.append("candidate_business_change_mismatches_lifecycle_delta")

    if (
        lifecycle.price_evidence_state == PriceEvidenceState.UNAVAILABLE
        and timing.technical_state != "UNKNOWN"
    ):
        errors.append("price_unavailable_but_timing_claimed")
    if lifecycle.evidence_change_scope == EvidenceChangeScope.PRICE_ONLY and change != "UNCHANGED":
        errors.append("price_only_change_mutated_business_thesis")

    unknown_issues = unknown_treatment_consistency_issues(core.unknown_treatments)
    errors.extend(issue.code for issue in unknown_issues)
    return LifecycleCandidateValidation(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
    )


def _render_derivative_text(
    lifecycle: NonproductionLifecycleContext,
    rendered: RenderedStructuredAutonomy,
) -> str:
    lines = [
        DERIVATIVE_LABEL,
        f"lifecycle_mode={lifecycle.mode}",
        f"refresh_state={lifecycle.refresh_state}",
        f"registration_allowed={str(lifecycle.registration_allowed).lower()}",
        f"monitoring_ready={str(lifecycle.monitoring_ready).lower()}",
    ]
    if lifecycle.mode == LifecycleMode.DAILY_DELTA:
        lines.extend(
            [
                f"delta_state={lifecycle.delta_state}",
                "",
                "1. 투자 논리 변화",
                f"• {lifecycle.delta_summary or lifecycle.delta_state}",
                "",
                "2. 현재 절대 판단",
            ]
        )
    else:
        lines.extend(["", "현재 절대 판단"])
    lines.append(rendered.text.rstrip())
    return "\n".join(lines).rstrip() + "\n"


def build_nonproduction_derivative(
    *,
    owned: OwnedEvidencePacket,
    core: DirectionalCoreCandidate,
    timing: PriceTimingCandidate,
    lifecycle: NonproductionLifecycleContext,
    price_map: Mapping[str, object],
    industry: str,
    base_detail_text: str = "",
) -> NonproductionDerivative:
    composed = compose_decision(core, timing)
    ownership = validate_ownership(owned, core, timing, composed)
    rendered = render_structured_autonomy_message(
        owned.source_packet,
        composed.candidate,
        price_map=price_map,
        industry=industry,
        base_detail_text=base_detail_text,
    )
    lifecycle_validation = validate_lifecycle_candidate(lifecycle, core, timing)
    intents = plan_nonproduction_intents(
        lifecycle,
        packet_id=owned.source_packet.packet_id,
    )
    text = _render_derivative_text(lifecycle, rendered)
    lineage = {
        "source_packet_id": owned.source_packet.packet_id,
        "source_packet_sha256": canonical_sha256(
            owned.source_packet.model_dump(mode="json")
        ),
        "core_sha256": composed.core_fingerprint,
        "timing_sha256": composed.timing_fingerprint,
        "composed_sha256": canonical_sha256(
            composed.candidate.model_dump(mode="json")
        ),
        "lifecycle_sha256": canonical_sha256(lifecycle.model_dump(mode="json")),
        "rendered_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    return NonproductionDerivative(
        lifecycle=lifecycle,
        composed=composed,
        ownership=ownership,
        candidate_validation=rendered.validation,
        lifecycle_validation=lifecycle_validation,
        intents=intents,
        lineage=lineage,
        structured_text=rendered.text,
        text=text,
    )
