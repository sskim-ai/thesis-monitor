from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Sequence

from pydantic import Field, model_validator

from app.schemas.thesis import AssessmentStatus, ExpectationLevel, ValuationImpact
from app.services.cross_market_decision_engine_service import FrozenModel
from app.services.direction_timing_ownership_service import (
    DirectionalCoreCandidate,
    OwnedEvidencePacket,
    PriceTimingCandidate,
    core_fingerprint,
)
from app.services.nonproduction_lifecycle_decision_service import (
    DERIVATIVE_LABEL,
    DeltaState,
    EvidenceChangeScope,
    LifecycleMode,
    NonproductionLifecycleContext,
    PriceEvidenceState,
    RefreshState,
    SubjectLifecycle,
    build_nonproduction_derivative,
)
from app.services.onboarding_readiness_service import OnboardingState
from app.utils.tickers import normalize_ticker


CONTRACT_VERSION = "nonproduction-monitoring-lifecycle-integration-v1"


class LifecycleRequestKind(StrEnum):
    INITIAL_ANALYSIS = "INITIAL_ANALYSIS"
    READ_ONLY_SNAPSHOT = "READ_ONLY_SNAPSHOT"
    CURRENT_THESIS_REVIEW = "CURRENT_THESIS_REVIEW"
    EXPLICIT_MONITORING = "EXPLICIT_MONITORING"


class EvidenceAxis(StrEnum):
    BUSINESS = "BUSINESS"
    PRICE = "PRICE"
    SUPPLY = "SUPPLY"
    VALUATION = "VALUATION"


class EvidencePolarity(StrEnum):
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    INVALIDATION = "INVALIDATION"
    RESOLUTION = "RESOLUTION"


class ShadowIntentKind(StrEnum):
    REGISTRATION = "REGISTRATION"
    ONBOARDING_EVIDENCE = "ONBOARDING_EVIDENCE"
    BASELINE = "BASELINE"
    ONBOARDING_RESUME = "ONBOARDING_RESUME"
    ASSESSMENT = "ASSESSMENT"
    WARNING_OPEN = "WARNING_OPEN"
    WARNING_RESOLVE = "WARNING_RESOLVE"
    FILE_ONLY_DELIVERY = "FILE_ONLY_DELIVERY"


class WarningStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class LifecycleEvidence(FrozenModel):
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    axis: EvidenceAxis
    polarity: EvidencePolarity = EvidencePolarity.NEUTRAL
    summary: str = Field(min_length=1)
    effective_at: datetime
    observed_at: datetime
    validated: bool = True
    warning_key: str | None = None
    resolves_warning_key: str | None = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> LifecycleEvidence:
        if self.effective_at.tzinfo is None or self.observed_at.tzinfo is None:
            raise ValueError("lifecycle_evidence_requires_aware_timestamps")
        if self.warning_key and self.axis != EvidenceAxis.BUSINESS:
            raise ValueError("fundamental_warning_requires_business_evidence")
        if self.resolves_warning_key and self.axis != EvidenceAxis.BUSINESS:
            raise ValueError("warning_resolution_requires_business_evidence")
        return self


class ThesisVersionRecord(FrozenModel):
    version: int = Field(ge=1)
    logic_fingerprint: str = Field(min_length=1)
    created_at: datetime
    status: str = Field(pattern="^(active|superseded)$")


class BaselineRecord(FrozenModel):
    baseline_ref: str = Field(min_length=1)
    thesis_version: int = Field(ge=1)
    cutoff: datetime
    established_at: datetime
    original_evidence_ids: tuple[str, ...]
    historical_enrichment_ids: tuple[str, ...] = ()

    @property
    def all_evidence_ids(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((*self.original_evidence_ids, *self.historical_enrichment_ids))
        )


class SubjectSnapshot(FrozenModel):
    ticker: str
    subject_lifecycle: SubjectLifecycle
    monitoring_requested: bool
    onboarding_state: OnboardingState
    monitoring_ready: bool
    bootstrap_complete: bool
    source_ready: bool
    thesis_versions: tuple[ThesisVersionRecord, ...]
    baseline: BaselineRecord | None
    evidence_ids: tuple[str, ...]

    @property
    def active_thesis_version(self) -> int:
        active = [row.version for row in self.thesis_versions if row.status == "active"]
        if len(active) != 1:
            raise ValueError("subject_requires_one_active_thesis_version")
        return active[0]


class ShadowIntent(FrozenModel):
    kind: ShadowIntentKind
    idempotency_key: str
    ticker: str
    subject_ref: str
    production_effect: str = "NONE"


class RegistrationResult(FrozenModel):
    request_kind: LifecycleRequestKind
    registration_allowed: bool
    registration_intent_created: bool
    thesis_version_created: bool
    subject: SubjectSnapshot | None


class DailyEvaluationRequest(FrozenModel):
    ticker: str
    assessment_date: date
    evaluated_at: datetime
    refresh_state: RefreshState
    evidence_ids: tuple[str, ...] = ()
    price_evidence_state: PriceEvidenceState = PriceEvidenceState.READY
    valuation_context: ValuationImpact = ValuationImpact.neutral
    market_expectation_level: ExpectationLevel = ExpectationLevel.balanced

    @model_validator(mode="after")
    def validate_evaluation_time(self) -> DailyEvaluationRequest:
        if self.evaluated_at.tzinfo is None:
            raise ValueError("daily_evaluation_requires_aware_timestamp")
        return self


class DailyDeltaLineage(FrozenModel):
    baseline_ref: str
    baseline_cutoff: datetime
    refresh_state: RefreshState
    source_evidence_ids: tuple[str, ...]
    genuinely_new_evidence_ids: tuple[str, ...]
    prebaseline_enrichment_ids: tuple[str, ...]
    excluded_evidence_ids: tuple[str, ...]
    evidence_effective_at: dict[str, str]
    evidence_observed_at: dict[str, str]
    thesis_version: int
    assessment_date: date
    evidence_generation: str


class DailyDeltaAssessment(FrozenModel):
    assessment_id: str
    ticker: str
    thesis_version: int
    assessment_date: date
    status: AssessmentStatus
    directional_core_change: str = Field(
        pattern="^(STRENGTHENED|UNCHANGED|WEAKENED|UNRESOLVED)$"
    )
    valuation_context: ValuationImpact
    market_expectation_level: ExpectationLevel
    price_evidence_state: PriceEvidenceState
    business_evidence_ids: tuple[str, ...]
    price_evidence_ids: tuple[str, ...]
    supply_evidence_ids: tuple[str, ...]
    valuation_evidence_ids: tuple[str, ...]
    warning_intent_ids: tuple[str, ...]
    lineage: DailyDeltaLineage


class DailyEvaluationResult(FrozenModel):
    assessment: DailyDeltaAssessment
    assessment_created: bool


class WarningRecord(FrozenModel):
    warning_key: str
    status: WarningStatus
    opened_by_evidence_id: str
    resolved_by_evidence_id: str | None = None


class FileOnlyMonitoringMessage(FrozenModel):
    fixture_id: str
    label: str = DERIVATIVE_LABEL
    text: str
    sha256: str
    lineage: dict[str, str]
    delivery_intent_created: bool


class SideEffectAudit(FrozenModel):
    production_db_connections: int = 0
    production_db_mutations: int = 0
    monitoring_registration_calls: int = 0
    assessment_persistence_mutations: int = 0
    warning_mutations: int = 0
    notification_queue_writes: int = 0
    production_sends: int = 0
    provider_source_fetches: int = 0
    model_calls_real: int = 0
    model_calls_fictional: int = 0
    model_calls_judge: int = 0

    @property
    def clean(self) -> bool:
        return all(value == 0 for value in self.model_dump().values())


@dataclass
class _MutableSubject:
    ticker: str
    subject_lifecycle: SubjectLifecycle
    monitoring_requested: bool
    onboarding_state: OnboardingState
    thesis_versions: list[ThesisVersionRecord]
    evidence: dict[str, LifecycleEvidence] = field(default_factory=dict)
    baseline: BaselineRecord | None = None
    bootstrap_complete: bool = False
    source_ready: bool = False

    @property
    def monitoring_ready(self) -> bool:
        return bool(
            self.monitoring_requested
            and self.baseline is not None
            and self.bootstrap_complete
            and self.source_ready
            and self.onboarding_state in {OnboardingState.READY, OnboardingState.ACTIVE}
        )

    @property
    def active_version(self) -> ThesisVersionRecord:
        active = [row for row in self.thesis_versions if row.status == "active"]
        if len(active) != 1:
            raise ValueError("subject_requires_one_active_thesis_version")
        return active[0]


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("aware_timestamp_required")
    return value.astimezone(UTC)


def _directional_change(status: AssessmentStatus) -> str:
    return {
        AssessmentStatus.strengthened: "STRENGTHENED",
        AssessmentStatus.no_material_change: "UNCHANGED",
        AssessmentStatus.weakened: "WEAKENED",
        AssessmentStatus.invalidation_candidate: "WEAKENED",
        AssessmentStatus.invalidated: "WEAKENED",
        AssessmentStatus.mixed: "UNRESOLVED",
        AssessmentStatus.needs_review: "UNRESOLVED",
    }[status]


class InMemoryMonitoringLifecycle:
    """Fixture-backed adapter over the repository's existing lifecycle semantics."""

    def __init__(self) -> None:
        self._subjects: dict[str, _MutableSubject] = {}
        self._intents: dict[str, ShadowIntent] = {}
        self._assessments: dict[str, DailyDeltaAssessment] = {}
        self._warnings: dict[tuple[str, str], WarningRecord] = {}
        self._messages: dict[str, FileOnlyMonitoringMessage] = {}
        self._side_effects = SideEffectAudit()

    @property
    def side_effects(self) -> SideEffectAudit:
        return self._side_effects

    @property
    def intents(self) -> tuple[ShadowIntent, ...]:
        return tuple(self._intents[key] for key in sorted(self._intents))

    @property
    def assessment_count(self) -> int:
        return len(self._assessments)

    @property
    def warning_count(self) -> int:
        return len(self._warnings)

    @property
    def message_count(self) -> int:
        return len(self._messages)

    def assert_side_effect_firewall(self) -> None:
        if not self._side_effects.clean:
            raise AssertionError("nonproduction_side_effect_firewall_breached")

    def _record_intent(
        self,
        kind: ShadowIntentKind,
        *,
        ticker: str,
        subject_ref: str,
    ) -> tuple[ShadowIntent, bool]:
        key = _canonical_sha256(
            {
                "contract": CONTRACT_VERSION,
                "kind": kind,
                "ticker": ticker,
                "subject_ref": subject_ref,
            }
        )
        current = self._intents.get(key)
        if current is not None:
            return current, False
        intent = ShadowIntent(
            kind=kind,
            idempotency_key=key,
            ticker=ticker,
            subject_ref=subject_ref,
        )
        self._intents[key] = intent
        return intent, True

    def _subject(self, ticker: str) -> _MutableSubject:
        canonical = normalize_ticker(ticker)
        subject = self._subjects.get(canonical)
        if subject is None:
            raise ValueError("monitoring_subject_not_registered")
        return subject

    def _snapshot(self, subject: _MutableSubject) -> SubjectSnapshot:
        return SubjectSnapshot(
            ticker=subject.ticker,
            subject_lifecycle=subject.subject_lifecycle,
            monitoring_requested=subject.monitoring_requested,
            onboarding_state=subject.onboarding_state,
            monitoring_ready=subject.monitoring_ready,
            bootstrap_complete=subject.bootstrap_complete,
            source_ready=subject.source_ready,
            thesis_versions=tuple(subject.thesis_versions),
            baseline=subject.baseline,
            evidence_ids=tuple(sorted(subject.evidence)),
        )

    def snapshot(self, ticker: str) -> SubjectSnapshot:
        return self._snapshot(self._subject(ticker))

    def submit_request(
        self,
        *,
        request_kind: LifecycleRequestKind,
        ticker: str,
        logic_fingerprint: str,
        requested_at: datetime,
        subject_lifecycle: SubjectLifecycle = SubjectLifecycle.NEW_ISSUER,
    ) -> RegistrationResult:
        self.assert_side_effect_firewall()
        canonical = normalize_ticker(ticker)
        current = self._subjects.get(canonical)
        if request_kind != LifecycleRequestKind.EXPLICIT_MONITORING:
            return RegistrationResult(
                request_kind=request_kind,
                registration_allowed=False,
                registration_intent_created=False,
                thesis_version_created=False,
                subject=self._snapshot(current) if current else None,
            )

        created_at = _aware_utc(requested_at)
        version_created = False
        if current is None:
            version = ThesisVersionRecord(
                version=1,
                logic_fingerprint=logic_fingerprint,
                created_at=created_at,
                status="active",
            )
            current = _MutableSubject(
                ticker=canonical,
                subject_lifecycle=subject_lifecycle,
                monitoring_requested=True,
                onboarding_state=OnboardingState.PENDING_ONBOARDING,
                thesis_versions=[version],
            )
            self._subjects[canonical] = current
            version_created = True
        else:
            current.monitoring_requested = True
            if current.active_version.logic_fingerprint != logic_fingerprint:
                current.thesis_versions = [
                    row.model_copy(update={"status": "superseded"})
                    if row.status == "active"
                    else row
                    for row in current.thesis_versions
                ]
                current.thesis_versions.append(
                    ThesisVersionRecord(
                        version=max(row.version for row in current.thesis_versions) + 1,
                        logic_fingerprint=logic_fingerprint,
                        created_at=created_at,
                        status="active",
                    )
                )
                current.onboarding_state = OnboardingState.PENDING_ONBOARDING
                current.baseline = None
                current.bootstrap_complete = False
                current.source_ready = False
                version_created = True

        _intent, intent_created = self._record_intent(
            ShadowIntentKind.REGISTRATION,
            ticker=canonical,
            subject_ref=logic_fingerprint,
        )
        self.assert_side_effect_firewall()
        return RegistrationResult(
            request_kind=request_kind,
            registration_allowed=True,
            registration_intent_created=intent_created,
            thesis_version_created=version_created,
            subject=self._snapshot(current),
        )

    def add_evidence(
        self,
        ticker: str,
        evidence: Sequence[LifecycleEvidence],
    ) -> tuple[str, ...]:
        self.assert_side_effect_firewall()
        subject = self._subject(ticker)
        inserted: list[str] = []
        for row in evidence:
            existing = subject.evidence.get(row.evidence_id)
            if existing is not None:
                if existing != row:
                    raise ValueError("conflicting_lifecycle_evidence_identity")
                continue
            subject.evidence[row.evidence_id] = row
            inserted.append(row.evidence_id)
            self._record_intent(
                ShadowIntentKind.ONBOARDING_EVIDENCE,
                ticker=subject.ticker,
                subject_ref=row.evidence_id,
            )
        self.assert_side_effect_firewall()
        return tuple(inserted)

    def create_baseline(
        self,
        ticker: str,
        *,
        cutoff: datetime,
        established_at: datetime,
    ) -> BaselineRecord:
        self.assert_side_effect_firewall()
        subject = self._subject(ticker)
        cutoff_utc = _aware_utc(cutoff)
        established_utc = _aware_utc(established_at)
        if subject.baseline is not None:
            if (
                subject.baseline.thesis_version != subject.active_version.version
                or subject.baseline.cutoff != cutoff_utc
            ):
                raise ValueError("baseline_identity_conflict")
            return subject.baseline
        evidence_ids = tuple(
            sorted(
                row.evidence_id
                for row in subject.evidence.values()
                if row.validated
                and _aware_utc(row.effective_at) <= cutoff_utc
                and _aware_utc(row.observed_at) <= established_utc
            )
        )
        if not evidence_ids:
            raise ValueError("baseline_requires_valid_initial_evidence")
        baseline_ref = _canonical_sha256(
            {
                "ticker": subject.ticker,
                "thesis_version": subject.active_version.version,
                "cutoff": cutoff_utc.isoformat(),
            }
        )
        subject.baseline = BaselineRecord(
            baseline_ref=baseline_ref,
            thesis_version=subject.active_version.version,
            cutoff=cutoff_utc,
            established_at=established_utc,
            original_evidence_ids=evidence_ids,
        )
        self._record_intent(
            ShadowIntentKind.BASELINE,
            ticker=subject.ticker,
            subject_ref=baseline_ref,
        )
        self.assert_side_effect_firewall()
        return subject.baseline

    def complete_bootstrap(
        self,
        ticker: str,
        *,
        completed_at: datetime,
        source_ready: bool,
    ) -> SubjectSnapshot:
        self.assert_side_effect_firewall()
        subject = self._subject(ticker)
        if subject.baseline is None:
            raise ValueError("bootstrap_requires_baseline")
        completed_utc = _aware_utc(completed_at)
        historical = tuple(
            sorted(
                row.evidence_id
                for row in subject.evidence.values()
                if row.validated
                and _aware_utc(row.effective_at) <= subject.baseline.cutoff
                and _aware_utc(row.observed_at) <= completed_utc
                and row.evidence_id not in subject.baseline.original_evidence_ids
            )
        )
        subject.baseline = subject.baseline.model_copy(
            update={"historical_enrichment_ids": historical}
        )
        subject.bootstrap_complete = True
        subject.source_ready = source_ready
        subject.onboarding_state = (
            OnboardingState.READY if source_ready else OnboardingState.PENDING_ONBOARDING
        )
        self._record_intent(
            ShadowIntentKind.ONBOARDING_RESUME,
            ticker=subject.ticker,
            subject_ref=f"{subject.baseline.baseline_ref}|{source_ready}",
        )
        self.assert_side_effect_firewall()
        return self._snapshot(subject)

    def _warning_intents(
        self,
        subject: _MutableSubject,
        business: Sequence[LifecycleEvidence],
    ) -> tuple[str, ...]:
        intent_ids: list[str] = []
        for row in business:
            if row.warning_key and row.polarity in {
                EvidencePolarity.NEGATIVE,
                EvidencePolarity.INVALIDATION,
            }:
                key = (subject.ticker, row.warning_key)
                previous = self._warnings.get(key)
                if previous is None or previous.status == WarningStatus.RESOLVED:
                    self._warnings[key] = WarningRecord(
                        warning_key=row.warning_key,
                        status=WarningStatus.OPEN,
                        opened_by_evidence_id=row.evidence_id,
                    )
                    intent, _created = self._record_intent(
                        ShadowIntentKind.WARNING_OPEN,
                        ticker=subject.ticker,
                        subject_ref=row.warning_key,
                    )
                    intent_ids.append(intent.idempotency_key)
            if row.resolves_warning_key and row.polarity in {
                EvidencePolarity.POSITIVE,
                EvidencePolarity.RESOLUTION,
            }:
                key = (subject.ticker, row.resolves_warning_key)
                previous = self._warnings.get(key)
                if previous is not None and previous.status == WarningStatus.OPEN:
                    self._warnings[key] = previous.model_copy(
                        update={
                            "status": WarningStatus.RESOLVED,
                            "resolved_by_evidence_id": row.evidence_id,
                        }
                    )
                    intent, _created = self._record_intent(
                        ShadowIntentKind.WARNING_RESOLVE,
                        ticker=subject.ticker,
                        subject_ref=row.resolves_warning_key,
                    )
                    intent_ids.append(intent.idempotency_key)
        return tuple(intent_ids)

    def evaluate_daily_delta(
        self,
        request: DailyEvaluationRequest,
    ) -> DailyEvaluationResult:
        self.assert_side_effect_firewall()
        subject = self._subject(request.ticker)
        if not subject.monitoring_ready or subject.baseline is None:
            raise ValueError("subject_not_monitoring_ready")
        unknown_ids = sorted(set(request.evidence_ids) - set(subject.evidence))
        if unknown_ids:
            raise ValueError(f"unknown_lifecycle_evidence:{','.join(unknown_ids)}")

        evaluated_at = _aware_utc(request.evaluated_at)
        rows = [
            subject.evidence[evidence_id]
            for evidence_id in dict.fromkeys(request.evidence_ids)
        ]
        observable = [
            row
            for row in rows
            if _aware_utc(row.observed_at) <= evaluated_at
            and _aware_utc(row.effective_at) <= evaluated_at
        ]
        excluded = [row for row in rows if row not in observable or not row.validated]
        prebaseline = [
            row
            for row in observable
            if row.validated and _aware_utc(row.effective_at) <= subject.baseline.cutoff
        ]
        postbaseline = [
            row
            for row in observable
            if row.validated and _aware_utc(row.effective_at) > subject.baseline.cutoff
        ]
        historical_ids = tuple(
            dict.fromkeys(
                (
                    *subject.baseline.historical_enrichment_ids,
                    *(
                        row.evidence_id
                        for row in prebaseline
                        if row.evidence_id
                        not in subject.baseline.original_evidence_ids
                    ),
                )
            )
        )
        subject.baseline = subject.baseline.model_copy(
            update={"historical_enrichment_ids": historical_ids}
        )
        business = [row for row in postbaseline if row.axis == EvidenceAxis.BUSINESS]

        if request.refresh_state != RefreshState.AVAILABLE:
            status = AssessmentStatus.needs_review
            evaluated_business: list[LifecycleEvidence] = []
        else:
            evaluated_business = business
            polarities = {row.polarity for row in business}
            if EvidencePolarity.INVALIDATION in polarities:
                status = AssessmentStatus.invalidation_candidate
            elif {EvidencePolarity.POSITIVE, EvidencePolarity.NEGATIVE}.issubset(
                polarities
            ):
                status = AssessmentStatus.mixed
            elif EvidencePolarity.NEGATIVE in polarities:
                status = AssessmentStatus.weakened
            elif EvidencePolarity.POSITIVE in polarities:
                status = AssessmentStatus.strengthened
            else:
                status = AssessmentStatus.no_material_change

        source_ids = tuple(row.evidence_id for row in observable)
        generation = _canonical_sha256(
            {
                "ticker": subject.ticker,
                "thesis_version": subject.active_version.version,
                "assessment_date": request.assessment_date,
                "refresh_state": request.refresh_state,
                "evidence_ids": sorted(source_ids),
                "valuation_context": request.valuation_context,
                "market_expectation_level": request.market_expectation_level,
            }
        )
        assessment_id = _canonical_sha256(
            {
                "ticker": subject.ticker,
                "assessment_date": request.assessment_date,
                "thesis_version": subject.active_version.version,
                "evidence_generation": generation,
            }
        )
        current = self._assessments.get(assessment_id)
        if current is not None:
            return DailyEvaluationResult(assessment=current, assessment_created=False)

        warning_intents = (
            self._warning_intents(subject, evaluated_business)
            if request.refresh_state == RefreshState.AVAILABLE
            else ()
        )
        lineage = DailyDeltaLineage(
            baseline_ref=subject.baseline.baseline_ref,
            baseline_cutoff=subject.baseline.cutoff,
            refresh_state=request.refresh_state,
            source_evidence_ids=source_ids,
            genuinely_new_evidence_ids=tuple(row.evidence_id for row in postbaseline),
            prebaseline_enrichment_ids=tuple(row.evidence_id for row in prebaseline),
            excluded_evidence_ids=tuple(row.evidence_id for row in excluded),
            evidence_effective_at={
                row.evidence_id: _aware_utc(row.effective_at).isoformat() for row in rows
            },
            evidence_observed_at={
                row.evidence_id: _aware_utc(row.observed_at).isoformat() for row in rows
            },
            thesis_version=subject.active_version.version,
            assessment_date=request.assessment_date,
            evidence_generation=generation,
        )
        assessment = DailyDeltaAssessment(
            assessment_id=assessment_id,
            ticker=subject.ticker,
            thesis_version=subject.active_version.version,
            assessment_date=request.assessment_date,
            status=status,
            directional_core_change=_directional_change(status),
            valuation_context=request.valuation_context,
            market_expectation_level=request.market_expectation_level,
            price_evidence_state=request.price_evidence_state,
            business_evidence_ids=tuple(row.evidence_id for row in evaluated_business),
            price_evidence_ids=tuple(
                row.evidence_id for row in postbaseline if row.axis == EvidenceAxis.PRICE
            ),
            supply_evidence_ids=tuple(
                row.evidence_id for row in postbaseline if row.axis == EvidenceAxis.SUPPLY
            ),
            valuation_evidence_ids=tuple(
                row.evidence_id
                for row in postbaseline
                if row.axis == EvidenceAxis.VALUATION
            ),
            warning_intent_ids=warning_intents,
            lineage=lineage,
        )
        self._assessments[assessment_id] = assessment
        self._record_intent(
            ShadowIntentKind.ASSESSMENT,
            ticker=subject.ticker,
            subject_ref=assessment_id,
        )
        self.assert_side_effect_firewall()
        return DailyEvaluationResult(assessment=assessment, assessment_created=True)

    def warning(self, ticker: str, warning_key: str) -> WarningRecord | None:
        return self._warnings.get((normalize_ticker(ticker), warning_key))

    def render_file_only_message(
        self,
        *,
        fixture_id: str,
        ticker: str,
        owned: OwnedEvidencePacket,
        core: DirectionalCoreCandidate,
        timing: PriceTimingCandidate,
        price_map: Mapping[str, object],
        industry: str,
        assessment: DailyDeltaAssessment | None = None,
        next_check: str = "후속 공식 사업 근거와 기준선 이후 유효일을 확인합니다.",
    ) -> FileOnlyMonitoringMessage:
        self.assert_side_effect_firewall()
        subject = self._subject(ticker)
        snapshot = self._snapshot(subject)
        if assessment is None:
            mode = LifecycleMode.MONITORING_BASELINE
            refresh = RefreshState.AVAILABLE
            delta = DeltaState.NOT_APPLICABLE
            scope = EvidenceChangeScope.NONE
            directional_change = "UNCHANGED"
        else:
            mode = LifecycleMode.DAILY_DELTA
            refresh = assessment.lineage.refresh_state
            directional_change = assessment.directional_core_change
            if assessment.status == AssessmentStatus.no_material_change:
                if assessment.price_evidence_ids and not assessment.business_evidence_ids:
                    delta = DeltaState.PRICE_ONLY_CONTEXT
                    scope = EvidenceChangeScope.PRICE_ONLY
                else:
                    delta = DeltaState.NO_MATERIAL_CHANGE
                    scope = EvidenceChangeScope.NONE
            elif assessment.status == AssessmentStatus.strengthened:
                delta = DeltaState.STRENGTHENED
                scope = EvidenceChangeScope.BUSINESS
            elif assessment.status in {
                AssessmentStatus.weakened,
                AssessmentStatus.invalidation_candidate,
                AssessmentStatus.invalidated,
            }:
                delta = DeltaState.WEAKENED
                scope = EvidenceChangeScope.BUSINESS
            elif assessment.status == AssessmentStatus.mixed:
                delta = DeltaState.MIXED
                scope = EvidenceChangeScope.BUSINESS
            else:
                delta = DeltaState.UNAVAILABLE
                scope = EvidenceChangeScope.UNKNOWN

        adjusted_core = core.model_copy(
            update={"business_thesis_change": directional_change}
        )
        adjusted_timing = timing.model_copy(
            update={"core_fingerprint": core_fingerprint(adjusted_core)}
        )
        lifecycle = NonproductionLifecycleContext(
            fixture_id=fixture_id,
            mode=mode,
            subject_lifecycle=subject.subject_lifecycle,
            explicit_monitoring_intent=subject.monitoring_requested,
            onboarding_complete=subject.monitoring_ready,
            refresh_state=refresh,
            price_evidence_state=(
                PriceEvidenceState.READY
                if assessment is None
                else assessment.price_evidence_state
            ),
            evidence_change_scope=scope,
            delta_state=delta,
            baseline_ref=subject.baseline.baseline_ref if assessment else None,
            baseline_cutoff=(
                subject.baseline.cutoff.isoformat()
                if assessment and subject.baseline is not None
                else None
            ),
            bootstrap_enrichment=assessment is None and subject.baseline is not None,
        )
        derivative = build_nonproduction_derivative(
            owned=owned,
            core=adjusted_core,
            timing=adjusted_timing,
            lifecycle=lifecycle,
            price_map=price_map,
            industry=industry,
        )
        if not derivative.ownership.valid:
            raise ValueError("shared_ownership_validation_failed")
        if not derivative.candidate_validation.valid:
            raise ValueError("shared_structured_validation_failed")
        if not derivative.lifecycle_validation.valid:
            raise ValueError("shared_lifecycle_validation_failed")

        delta_text = _delta_message(snapshot, assessment)
        price_text = _price_timing_message(assessment)
        lines = [
            DERIVATIVE_LABEL,
            f"fixture_id={fixture_id}",
            f"onboarding_state={snapshot.onboarding_state}",
            f"monitoring_ready={str(snapshot.monitoring_ready).lower()}",
            f"thesis_version={snapshot.active_thesis_version}",
            f"baseline_ref={snapshot.baseline.baseline_ref if snapshot.baseline else 'NOT_ESTABLISHED'}",
            f"baseline_cutoff={snapshot.baseline.cutoff.isoformat() if snapshot.baseline else 'NOT_ESTABLISHED'}",
            f"refresh_state={assessment.lineage.refresh_state if assessment else 'NOT_APPLICABLE'}",
            "",
            "1. 투자 논리 변화",
            f"• {delta_text}",
            "",
            "2. 현재 절대 판단",
            derivative.structured_text.rstrip(),
            "",
            "3. Price-Timing",
            f"• {price_text}",
            "",
            "4. 다음 확인",
            f"• {next_check}",
        ]
        text = "\n".join(lines).rstrip() + "\n"
        message_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        subject_ref = assessment.assessment_id if assessment else (
            snapshot.baseline.baseline_ref if snapshot.baseline else fixture_id
        )
        _intent, created = self._record_intent(
            ShadowIntentKind.FILE_ONLY_DELIVERY,
            ticker=subject.ticker,
            subject_ref=f"{subject_ref}|{message_sha}",
        )
        existing = self._messages.get(message_sha)
        if existing is not None:
            return existing.model_copy(update={"delivery_intent_created": False})
        message = FileOnlyMonitoringMessage(
            fixture_id=fixture_id,
            text=text,
            sha256=message_sha,
            lineage={
                "subject": subject.ticker,
                "thesis_version": str(snapshot.active_thesis_version),
                "baseline_ref": snapshot.baseline.baseline_ref if snapshot.baseline else "",
                "assessment_id": assessment.assessment_id if assessment else "",
                "shared_composed_sha256": derivative.lineage["composed_sha256"],
                "shared_rendered_sha256": derivative.lineage["rendered_sha256"],
            },
            delivery_intent_created=created,
        )
        self._messages[message_sha] = message
        self.assert_side_effect_firewall()
        return message

    def write_file_only_message(
        self,
        message: FileOnlyMonitoringMessage,
        path: Path,
    ) -> Path:
        self.assert_side_effect_firewall()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(message.text, encoding="utf-8")
        self.assert_side_effect_firewall()
        return path


def _delta_message(
    snapshot: SubjectSnapshot,
    assessment: DailyDeltaAssessment | None,
) -> str:
    if assessment is None:
        if snapshot.baseline is None:
            return "모니터링 기준선을 설정 중이어서 Daily Delta는 아직 적용하지 않습니다."
        if not snapshot.monitoring_ready:
            return "기준선은 있으나 bootstrap/source readiness가 미완료여서 Daily Delta는 적용하지 않습니다."
        return "모니터링 기준선이 준비됐으며 다음 유효한 갱신부터 Daily Delta를 평가합니다."
    return {
        AssessmentStatus.no_material_change: (
            "필수 사업 근거 갱신은 완료됐고 기준선 이후 중대한 사업 논리 변화는 없습니다."
        ),
        AssessmentStatus.strengthened: (
            "기준선 이후 검증된 사업 근거가 투자 논리의 강화 조건과 일치합니다."
        ),
        AssessmentStatus.weakened: (
            "기준선 이후 검증된 사업 근거가 투자 논리의 약화 조건과 일치합니다."
        ),
        AssessmentStatus.mixed: (
            "기준선 이후 강화와 약화 근거가 함께 확인돼 변화 방향을 혼합으로 유지합니다."
        ),
        AssessmentStatus.invalidation_candidate: (
            "기준선 이후 검증된 사업 근거가 무효화 후보 조건과 일치하지만 확정 무효화로 승격하지 않습니다."
        ),
        AssessmentStatus.invalidated: "검증된 무효화 근거가 확정됐습니다.",
        AssessmentStatus.needs_review: (
            "필수 사업 근거 갱신이 없어 오늘의 사업 논리 변화를 판정하지 않습니다."
        ),
    }[assessment.status]


def _price_timing_message(assessment: DailyDeltaAssessment | None) -> str:
    if assessment is None:
        return "가격 판단은 현재 절대 판단과 분리하며 Daily Delta로 사용하지 않습니다."
    if assessment.price_evidence_ids:
        return "가격 변화는 별도 timing 맥락으로만 보존하며 사업 논리 변화를 만들지 않습니다."
    if assessment.supply_evidence_ids:
        return "수급 변화는 별도 positioning 맥락으로만 보존하며 사업 논리 변화를 만들지 않습니다."
    return "가격·수급 근거가 없으면 사업 논리 변화와 결합하지 않습니다."
