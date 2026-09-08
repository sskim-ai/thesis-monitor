from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from app.schemas.thesis import AssessmentStatus
from app.services.nonproduction_lifecycle_decision_service import DERIVATIVE_LABEL
from app.services.nonproduction_monitoring_lifecycle_service import (
    DailyEvaluationRequest,
    EvidenceAxis,
    EvidencePolarity,
    InMemoryMonitoringLifecycle,
    LifecycleEvidence,
    LifecycleRequestKind,
    ShadowIntentKind,
    SubjectLifecycle,
    WarningStatus,
)
from app.services.onboarding_readiness_service import OnboardingState
from scripts.nonproduction_integration_decision_message_review import (
    fixture_contract_pair,
)


T0 = datetime(2026, 9, 8, 0, tzinfo=UTC)
TICKER = "SYNTHETIC_M2_REVIEW"


def _evidence(
    evidence_id: str,
    *,
    axis: EvidenceAxis = EvidenceAxis.BUSINESS,
    polarity: EvidencePolarity = EvidencePolarity.NEUTRAL,
    effective_at: datetime | None = None,
    observed_at: datetime | None = None,
    validated: bool = True,
    warning_key: str | None = None,
    resolves_warning_key: str | None = None,
) -> LifecycleEvidence:
    return LifecycleEvidence(
        evidence_id=evidence_id,
        source_id=f"official:{evidence_id}",
        axis=axis,
        polarity=polarity,
        summary=f"Validated fixture evidence {evidence_id}",
        effective_at=effective_at or (T0 + timedelta(hours=1)),
        observed_at=observed_at or (T0 + timedelta(hours=2)),
        validated=validated,
        warning_key=warning_key,
        resolves_warning_key=resolves_warning_key,
    )


def _registered_store(
    *,
    ready: bool,
    subject_lifecycle: SubjectLifecycle = SubjectLifecycle.NEW_ISSUER,
) -> InMemoryMonitoringLifecycle:
    store = InMemoryMonitoringLifecycle()
    store.submit_request(
        request_kind=LifecycleRequestKind.EXPLICIT_MONITORING,
        ticker=TICKER,
        logic_fingerprint="logic-v1",
        requested_at=T0 - timedelta(hours=3),
        subject_lifecycle=subject_lifecycle,
    )
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "baseline-fact",
                effective_at=T0 - timedelta(days=1),
                observed_at=T0 - timedelta(hours=2),
            ),
        ),
    )
    store.create_baseline(
        TICKER,
        cutoff=T0,
        established_at=T0,
    )
    if ready:
        store.complete_bootstrap(
            TICKER,
            completed_at=T0 + timedelta(minutes=30),
            source_ready=True,
        )
    return store


def _evaluate(
    store: InMemoryMonitoringLifecycle,
    *,
    day: int = 8,
    evidence_ids: tuple[str, ...] = (),
    refresh_state: str = "AVAILABLE",
    valuation_context: str = "neutral",
    market_expectation_level: str = "balanced",
):
    return store.evaluate_daily_delta(
        DailyEvaluationRequest(
            ticker=TICKER,
            assessment_date=date(2026, 9, day),
            evaluated_at=T0 + timedelta(days=day - 8, hours=12),
            refresh_state=refresh_state,
            evidence_ids=evidence_ids,
            valuation_context=valuation_context,
            market_expectation_level=market_expectation_level,
        )
    )


@pytest.mark.parametrize(
    "request_kind",
    (
        LifecycleRequestKind.INITIAL_ANALYSIS,
        LifecycleRequestKind.READ_ONLY_SNAPSHOT,
        LifecycleRequestKind.CURRENT_THESIS_REVIEW,
    ),
)
def test_nonexplicit_requests_never_register(request_kind: LifecycleRequestKind) -> None:
    store = InMemoryMonitoringLifecycle()

    result = store.submit_request(
        request_kind=request_kind,
        ticker=TICKER,
        logic_fingerprint="logic-v1",
        requested_at=T0,
    )

    assert result.registration_allowed is False
    assert result.subject is None
    assert result.registration_intent_created is False
    assert not store.intents
    store.assert_side_effect_firewall()


def test_explicit_registration_is_pending_and_idempotent() -> None:
    store = InMemoryMonitoringLifecycle()
    first = store.submit_request(
        request_kind=LifecycleRequestKind.EXPLICIT_MONITORING,
        ticker=TICKER,
        logic_fingerprint="logic-v1",
        requested_at=T0,
    )
    repeat = store.submit_request(
        request_kind=LifecycleRequestKind.EXPLICIT_MONITORING,
        ticker=TICKER,
        logic_fingerprint="logic-v1",
        requested_at=T0 + timedelta(minutes=1),
    )

    assert first.registration_allowed is True
    assert first.registration_intent_created is True
    assert first.thesis_version_created is True
    assert first.subject is not None
    assert first.subject.onboarding_state == OnboardingState.PENDING_ONBOARDING
    assert first.subject.monitoring_ready is False
    assert repeat.registration_intent_created is False
    assert repeat.thesis_version_created is False
    assert len(repeat.subject.thesis_versions) == 1  # type: ignore[union-attr]


def test_changed_logic_creates_version_and_preserves_history() -> None:
    store = _registered_store(ready=True)

    changed = store.submit_request(
        request_kind=LifecycleRequestKind.EXPLICIT_MONITORING,
        ticker=TICKER,
        logic_fingerprint="logic-v2",
        requested_at=T0 + timedelta(days=1),
    )

    assert changed.thesis_version_created is True
    assert changed.subject is not None
    assert [(row.version, row.status) for row in changed.subject.thesis_versions] == [
        (1, "superseded"),
        (2, "active"),
    ]
    assert changed.subject.baseline is None
    assert changed.subject.monitoring_ready is False
    assert changed.subject.onboarding_state == OnboardingState.PENDING_ONBOARDING


def test_baseline_without_bootstrap_is_not_monitoring_ready() -> None:
    store = _registered_store(ready=False)
    snapshot = store.snapshot(TICKER)

    assert snapshot.baseline is not None
    assert snapshot.bootstrap_complete is False
    assert snapshot.monitoring_ready is False
    with pytest.raises(ValueError, match="subject_not_monitoring_ready"):
        _evaluate(store)


def test_bootstrap_enrichment_is_baseline_only_not_daily_delta() -> None:
    store = _registered_store(ready=False)
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "late-bootstrap-history",
                effective_at=T0 - timedelta(hours=1),
                observed_at=T0 + timedelta(hours=1),
            ),
        ),
    )

    snapshot = store.complete_bootstrap(
        TICKER,
        completed_at=T0 + timedelta(hours=2),
        source_ready=True,
    )

    assert snapshot.monitoring_ready is True
    assert snapshot.onboarding_state == OnboardingState.READY
    assert snapshot.baseline is not None
    assert snapshot.baseline.historical_enrichment_ids == ("late-bootstrap-history",)
    assert store.assessment_count == 0
    assert not any(row.kind == ShadowIntentKind.ASSESSMENT for row in store.intents)


def test_source_not_ready_keeps_subject_pending() -> None:
    store = _registered_store(ready=False)

    snapshot = store.complete_bootstrap(
        TICKER,
        completed_at=T0 + timedelta(hours=1),
        source_ready=False,
    )

    assert snapshot.bootstrap_complete is True
    assert snapshot.source_ready is False
    assert snapshot.monitoring_ready is False
    assert snapshot.onboarding_state == OnboardingState.PENDING_ONBOARDING


def test_baseline_and_onboarding_resume_are_idempotent() -> None:
    store = _registered_store(ready=False)
    baseline = store.snapshot(TICKER).baseline

    repeated_baseline = store.create_baseline(
        TICKER,
        cutoff=T0,
        established_at=T0 + timedelta(minutes=1),
    )
    first_ready = store.complete_bootstrap(
        TICKER,
        completed_at=T0 + timedelta(hours=1),
        source_ready=True,
    )
    repeated_ready = store.complete_bootstrap(
        TICKER,
        completed_at=T0 + timedelta(hours=2),
        source_ready=True,
    )

    assert repeated_baseline == baseline
    assert first_ready == repeated_ready
    assert sum(row.kind == ShadowIntentKind.BASELINE for row in store.intents) == 1
    assert sum(row.kind == ShadowIntentKind.ONBOARDING_RESUME for row in store.intents) == 1


def test_cutoff_separates_late_history_from_true_daily_delta() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "late-prebaseline",
                polarity=EvidencePolarity.NEGATIVE,
                effective_at=T0 - timedelta(hours=2),
                observed_at=T0 + timedelta(hours=2),
            ),
            _evidence(
                "postbaseline-positive",
                polarity=EvidencePolarity.POSITIVE,
                effective_at=T0 + timedelta(hours=1),
                observed_at=T0 + timedelta(hours=2),
            ),
        ),
    )

    result = _evaluate(
        store,
        evidence_ids=("late-prebaseline", "postbaseline-positive"),
    ).assessment

    assert result.status == AssessmentStatus.strengthened
    assert result.business_evidence_ids == ("postbaseline-positive",)
    assert result.lineage.prebaseline_enrichment_ids == ("late-prebaseline",)
    assert result.lineage.genuinely_new_evidence_ids == ("postbaseline-positive",)
    assert "late-prebaseline" in store.snapshot(TICKER).baseline.historical_enrichment_ids  # type: ignore[union-attr]


def test_future_effective_evidence_is_excluded() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "future-negative",
                polarity=EvidencePolarity.NEGATIVE,
                effective_at=T0 + timedelta(days=3),
                observed_at=T0 + timedelta(hours=1),
            ),
        ),
    )

    result = _evaluate(store, evidence_ids=("future-negative",)).assessment

    assert result.status == AssessmentStatus.no_material_change
    assert result.business_evidence_ids == ()
    assert result.lineage.excluded_evidence_ids == ("future-negative",)


def test_fresh_no_change_and_missing_refresh_are_distinct() -> None:
    store = _registered_store(ready=True)

    fresh = _evaluate(store, day=8).assessment
    missing = _evaluate(store, day=9, refresh_state="MISSING").assessment

    assert fresh.status == AssessmentStatus.no_material_change
    assert fresh.directional_core_change == "UNCHANGED"
    assert missing.status == AssessmentStatus.needs_review
    assert missing.directional_core_change == "UNRESOLVED"


def test_price_only_without_business_refresh_is_needs_review() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence("price-move", axis=EvidenceAxis.PRICE),
        ),
    )

    assessment = _evaluate(
        store,
        evidence_ids=("price-move",),
        refresh_state="MISSING",
    ).assessment

    assert assessment.status == AssessmentStatus.needs_review
    assert assessment.business_evidence_ids == ()
    assert assessment.price_evidence_ids == ("price-move",)


@pytest.mark.parametrize(
    ("axis", "field"),
    (
        (EvidenceAxis.PRICE, "price_evidence_ids"),
        (EvidenceAxis.SUPPLY, "supply_evidence_ids"),
        (EvidenceAxis.VALUATION, "valuation_evidence_ids"),
    ),
)
def test_nonbusiness_axes_do_not_rewrite_business_delta(
    axis: EvidenceAxis,
    field: str,
) -> None:
    store = _registered_store(ready=True)
    evidence_id = f"{axis.value.lower()}-only"
    store.add_evidence(TICKER, (_evidence(evidence_id, axis=axis),))

    assessment = _evaluate(
        store,
        evidence_ids=(evidence_id,),
        valuation_context="compression" if axis == EvidenceAxis.VALUATION else "neutral",
        market_expectation_level=(
            "elevated" if axis == EvidenceAxis.VALUATION else "balanced"
        ),
    ).assessment

    assert assessment.status == AssessmentStatus.no_material_change
    assert assessment.directional_core_change == "UNCHANGED"
    assert getattr(assessment, field) == (evidence_id,)
    if axis == EvidenceAxis.VALUATION:
        assert assessment.valuation_context == "compression"
        assert assessment.market_expectation_level == "elevated"


def test_business_strength_and_valuation_change_remain_separate() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence("business-positive", polarity=EvidencePolarity.POSITIVE),
            _evidence("valuation-negative", axis=EvidenceAxis.VALUATION),
        ),
    )

    assessment = _evaluate(
        store,
        evidence_ids=("business-positive", "valuation-negative"),
        valuation_context="compression",
        market_expectation_level="elevated",
    ).assessment

    assert assessment.status == AssessmentStatus.strengthened
    assert assessment.business_evidence_ids == ("business-positive",)
    assert assessment.valuation_evidence_ids == ("valuation-negative",)
    assert assessment.valuation_context == "compression"
    assert assessment.market_expectation_level == "elevated"


def test_nonbusiness_evidence_cannot_own_fundamental_warning() -> None:
    with pytest.raises(ValueError, match="fundamental_warning_requires_business_evidence"):
        _evidence(
            "price-warning",
            axis=EvidenceAxis.PRICE,
            polarity=EvidencePolarity.NEGATIVE,
            warning_key="price_drop",
        )


@pytest.mark.parametrize(
    ("polarity", "expected_status", "directional_change"),
    (
        (EvidencePolarity.POSITIVE, AssessmentStatus.strengthened, "STRENGTHENED"),
        (EvidencePolarity.NEGATIVE, AssessmentStatus.weakened, "WEAKENED"),
        (
            EvidencePolarity.INVALIDATION,
            AssessmentStatus.invalidation_candidate,
            "WEAKENED",
        ),
    ),
)
def test_postbaseline_fundamental_evidence_drives_canonical_delta(
    polarity: EvidencePolarity,
    expected_status: AssessmentStatus,
    directional_change: str,
) -> None:
    store = _registered_store(ready=True)
    store.add_evidence(TICKER, (_evidence("business-change", polarity=polarity),))

    assessment = _evaluate(store, evidence_ids=("business-change",)).assessment

    assert assessment.status == expected_status
    assert assessment.directional_core_change == directional_change
    assert assessment.business_evidence_ids == ("business-change",)


def test_unvalidated_invalidation_cannot_create_candidate() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "unvalidated-invalidation",
                polarity=EvidencePolarity.INVALIDATION,
                validated=False,
            ),
        ),
    )

    assessment = _evaluate(
        store,
        evidence_ids=("unvalidated-invalidation",),
    ).assessment

    assert assessment.status == AssessmentStatus.no_material_change
    assert assessment.business_evidence_ids == ()
    assert assessment.lineage.excluded_evidence_ids == ("unvalidated-invalidation",)


def test_assessment_and_warning_open_are_idempotent() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "warning-negative",
                polarity=EvidencePolarity.NEGATIVE,
                warning_key="order_decline",
            ),
        ),
    )

    first = _evaluate(store, evidence_ids=("warning-negative",))
    repeat = _evaluate(store, evidence_ids=("warning-negative",))

    assert first.assessment_created is True
    assert repeat.assessment_created is False
    assert first.assessment == repeat.assessment
    assert store.assessment_count == 1
    assert store.warning(TICKER, "order_decline").status == WarningStatus.OPEN  # type: ignore[union-attr]
    assert sum(row.kind == ShadowIntentKind.WARNING_OPEN for row in store.intents) == 1


def test_repeated_warning_and_resolution_are_idempotent() -> None:
    store = _registered_store(ready=True)
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "warning-1",
                polarity=EvidencePolarity.NEGATIVE,
                warning_key="margin_pressure",
            ),
            _evidence(
                "warning-2",
                polarity=EvidencePolarity.NEGATIVE,
                warning_key="margin_pressure",
                effective_at=T0 + timedelta(days=1),
                observed_at=T0 + timedelta(days=1, hours=1),
            ),
            _evidence(
                "warning-resolved",
                polarity=EvidencePolarity.RESOLUTION,
                resolves_warning_key="margin_pressure",
                effective_at=T0 + timedelta(days=2),
                observed_at=T0 + timedelta(days=2, hours=1),
            ),
        ),
    )

    _evaluate(store, day=8, evidence_ids=("warning-1",))
    _evaluate(store, day=9, evidence_ids=("warning-2",))
    resolved = _evaluate(store, day=10, evidence_ids=("warning-resolved",))
    repeat = _evaluate(store, day=10, evidence_ids=("warning-resolved",))

    assert resolved.assessment_created is True
    assert repeat.assessment_created is False
    assert store.warning(TICKER, "margin_pressure").status == WarningStatus.RESOLVED  # type: ignore[union-attr]
    assert sum(row.kind == ShadowIntentKind.WARNING_OPEN for row in store.intents) == 1
    assert sum(row.kind == ShadowIntentKind.WARNING_RESOLVE for row in store.intents) == 1


def test_new_and_existing_subjects_share_decision_and_message_contract() -> None:
    owned, core, timing = fixture_contract_pair()
    hashes: list[str] = []
    for lifecycle in (SubjectLifecycle.NEW_ISSUER, SubjectLifecycle.EXISTING_MONITORED):
        store = _registered_store(ready=True, subject_lifecycle=lifecycle)
        assessment = _evaluate(store).assessment
        message = store.render_file_only_message(
            fixture_id=f"contract-{lifecycle}",
            ticker=TICKER,
            owned=owned,
            core=core,
            timing=timing,
            price_map={},
            industry="Software",
            assessment=assessment,
        )
        hashes.append(message.lineage["shared_composed_sha256"])
        assert "1. 투자 논리 변화" in message.text
        assert "2. 현재 절대 판단" in message.text
        assert "3. Price-Timing" in message.text
        assert message.text.startswith(DERIVATIVE_LABEL)

    assert hashes[0] == hashes[1]


def test_file_only_delivery_has_no_production_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def forbidden(*_args, **_kwargs):
        calls.append("sync")
        raise AssertionError("production boundary called")

    async def forbidden_async(*_args, **_kwargs):
        calls.append("async")
        raise AssertionError("production boundary called")

    monkeypatch.setattr(
        "app.services.monitoring_service.register_monitoring_item_with_continuation",
        forbidden_async,
    )
    monkeypatch.setattr("app.services.monitoring_service.record_assessment", forbidden)
    monkeypatch.setattr(
        "app.services.notification_service.queue_daily_stock_notification",
        forbidden,
    )
    monkeypatch.setattr(
        "app.services.notification_service.dispatch_pending_notifications",
        forbidden_async,
    )
    owned, core, timing = fixture_contract_pair()
    store = _registered_store(ready=True)
    assessment = _evaluate(store).assessment

    first = store.render_file_only_message(
        fixture_id="file-only",
        ticker=TICKER,
        owned=owned,
        core=core,
        timing=timing,
        price_map={},
        industry="Software",
        assessment=assessment,
    )
    repeat = store.render_file_only_message(
        fixture_id="file-only",
        ticker=TICKER,
        owned=owned,
        core=core,
        timing=timing,
        price_map={},
        industry="Software",
        assessment=assessment,
    )
    output = store.write_file_only_message(first, tmp_path / "message.txt")

    assert output.read_text(encoding="utf-8") == first.text
    assert first.delivery_intent_created is True
    assert repeat.delivery_intent_created is False
    assert store.message_count == 1
    assert calls == []
    assert store.side_effects.clean is True
    store.assert_side_effect_firewall()
