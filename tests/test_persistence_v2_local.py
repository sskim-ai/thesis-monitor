from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select, text, update
from sqlmodel import Session, SQLModel

from app.config import Settings
from app.jobs.migrate_accepted_assessment_v2 import (
    persistence_v2_schema_snapshot,
    run_local_v2_migration,
)
from app.models.accepted_assessment import (
    PERSISTENCE_V2_TABLE_NAMES,
    accepted_assessment_v2,
    assessment_source_registry_v2,
    canonical_acceptance_receipt_v1,
    monitoring_current_state_v2,
    notification_outbox_v2,
    warning_state_v2,
    warning_transition_v2,
)
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.accepted_assessment_v2 import (
    CanonicalWarningObservationV1,
    DailySummaryNotificationV1,
    MaterialTransitionNotificationV1,
    PersistenceEligibility,
    PersistenceSourceDomain,
)
from app.schemas.thesis import ThesisAssessmentCreate
from app.services.accepted_assessment_persistence_service import (
    CanonicalAssessmentPersistenceV2,
    FakeOutboxSender,
    PersistenceV2Error,
    PersistenceV2IntegrityError,
    PersistenceV2LocalGateError,
    accepted_assessment_row,
    dispatch_pending_outbox,
    validate_extract_consistency,
)
from app.services.accepted_assessment_read_service import (
    project_canonical_business_delta_to_legacy,
    read_assessment_history_v2,
    read_current_assessment_v2,
)
from app.services.assessment_source_registry_service import (
    AssessmentSourceRegistryError,
    classify_legacy_assessment,
)
from app.services import monitoring_service
from app.services.canonical_acceptance_receipt_service import (
    CanonicalReceiptError,
    acceptance_id_for,
    canonical_sha256,
    issue_canonical_acceptance_receipt,
    parse_receipt,
    source_evidence_snapshot_identity,
    trusted_finalization_result,
    verify_canonical_acceptance_receipt,
)
from app.services.direction_timing_ownership_service import DirectionalCoreCandidate
from app.services.directional_balance_service import DirectionalBalance
from app.services.direction_timing_ownership_service import (
    CoreHolderView,
    CoreNewBuyerView,
    DirectionalClaim,
    DirectionalSellDriver,
    DirectionalUnknown,
)


M12BJ_ROOT = Path(
    "/Users/sskim/Documents/Codex/local-only-shadow/"
    "20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff/"
    "proof-runtime/shadow"
)
M12BJ_IDENTITY_REPORT = Path(
    "docs/reports/"
    "20260914-canonical-acceptance-persistence-contract-schema-lifecycle-design/"
    "49-m12bj-22-positive-receipt-fixture-spec.json"
)
M12BJ_GENERATION_MANIFEST = Path(
    "docs/reports/"
    "20260914-converged-semantic-single-source-full-monitored-shadow-policy-handoff/"
    "018-new-shadow-generation-manifest.json"
)
HISTORICAL_NEGATIVE_REPORT = Path(
    "docs/reports/20260914-bounded-semantic-single-source-convergence-repair/"
    "036-latest-fresh-output-canonical-offline-reaudit.json"
)


def _claim(text_value: str, ref: str) -> DirectionalClaim:
    return DirectionalClaim(text=text_value, evidence_refs=(ref,))


def _candidate(
    ticker: str = "TEST",
    *,
    business_delta: str = "UNCHANGED",
) -> DirectionalCoreCandidate:
    ref = f"canonical:fundamental:{ticker}:business_current:fixture"
    return DirectionalCoreCandidate(
        ticker=ticker,
        overall_direction="HOLD",
        directional_balance=DirectionalBalance(buy=5, sell=5),
        hold_lean="NEUTRAL",
        directional_confidence="MEDIUM",
        business_thesis_change=business_delta,
        business_thesis_context=_claim("Business evidence.", ref),
        earnings_estimate_context=_claim("Earnings evidence.", ref),
        market_expectation_context=_claim("Expectation evidence.", ref),
        valuation_context=_claim("Valuation evidence.", ref),
        risk_context=_claim("Risk evidence.", ref),
        sector_interpretation=_claim("Sector evidence.", ref),
        buy_drivers=(_claim("Buy evidence.", ref),),
        sell_drivers=(
            DirectionalSellDriver(
                text="Sell evidence.",
                evidence_refs=(ref,),
                classification="STRUCTURAL_RISK",
            ),
        ),
        dominant_evidence=_claim("Dominant evidence.", ref),
        uncertainty_limit=_claim("Uncertainty evidence.", ref),
        core_investment_judgment=_claim("Core judgment.", ref),
        unknown_treatments=(
            DirectionalUnknown(
                summary="Remaining unknown.",
                evidence_refs=(ref,),
                treatment="CONFIDENCE_LIMIT",
                directional_negative_basis=(),
            ),
        ),
        material_directional_anchor_basis=(ref,),
        fundamental_new_buyer=CoreNewBuyerView(
            stance="WAIT",
            summary="Wait for business confirmation.",
            confirmation_business_condition="Business confirmation is required.",
            confirmation_business_condition_refs=(ref,),
        ),
        fundamental_holder=CoreHolderView(
            stance="HOLDABLE",
            summary="The holding case remains intact.",
            business_invalidation_condition="Business deterioration invalidates the case.",
            business_invalidation_condition_refs=(ref,),
        ),
        business_reevaluation_up=(_claim("Business improves.", ref),),
        business_reevaluation_down=(_claim("Business deteriorates.", ref),),
    )


def _trusted_result(
    ticker: str = "TEST",
    *,
    generation_id: str = "generation-001",
    generated_at: datetime | None = None,
    effective_at: datetime | None = None,
    business_delta: str = "UNCHANGED",
):
    payload = _candidate(ticker, business_delta=business_delta)
    security_basis = {
        "contract": "security-basis-provenance-fixture-v1",
        "ticker": ticker,
        "issuer_type": None,
        "security_type": None,
    }
    packet = json.dumps(
        {"packet_id": f"packet-{ticker}", "ticker": ticker},
        sort_keys=True,
    ).encode()
    snapshot = source_evidence_snapshot_identity(
        packet_bytes=packet,
        packet_contract="test-source-packet-v1",
        ticker=ticker,
        component_hashes={
            "evidence": canonical_sha256({"ticker": ticker}),
            "security_basis_provenance_sha256": canonical_sha256(security_basis),
        },
    )
    return trusted_finalization_result(
        generation_id=generation_id,
        generation_generated_at=generated_at
        or datetime(2026, 9, 14, 2, 47, 41, tzinfo=UTC),
        ticker=ticker,
        thesis_version=4,
        assessment_date=date(2026, 9, 14),
        effective_at=effective_at or datetime(2026, 9, 14, 3, 0, tzinfo=UTC),
        source_packet_id=f"packet-{ticker}",
        source_packet_bytes=packet,
        source_snapshot=snapshot,
        accepted_payload=payload,
        canonical_semantic_audit_contract="directional-core-semantic-audit-v1",
        canonical_semantic_audit_status="PASS",
        finalization_status="PASS",
        core_immutability_status="PASS",
        core_hash=canonical_sha256({"core": payload.model_dump(mode="json")}),
        stance_hash=canonical_sha256(
            {
                "new_buyer": payload.fundamental_new_buyer.model_dump(mode="json"),
                "holder": payload.fundamental_holder.model_dump(mode="json"),
            }
        ),
        security_basis_provenance=security_basis,
    )


def _engine(tmp_path: Path, name: str = "proof.sqlite"):
    engine = create_engine(
        f"sqlite:///{tmp_path / name}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    run_local_v2_migration(engine, allow_local_ephemeral=True)
    return engine


def _count(engine, table) -> int:
    with engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(table)).scalar_one())


def _observation(value: str) -> CanonicalWarningObservationV1:
    return CanonicalWarningObservationV1(
        warning_type="fundamental-condition",
        condition_contract_version="condition-v1",
        condition_identity="margin-condition",
        observation=value,
        transition_reason_code=f"fixture-{value.lower()}",
        transition_reason_version="warning-reason-v1",
        evidence_refs=("canonical:fundamental:TEST:business_current:fixture",),
    )


def test_v2_tables_are_not_in_legacy_sqlmodel_metadata() -> None:
    assert set(PERSISTENCE_V2_TABLE_NAMES).isdisjoint(SQLModel.metadata.tables)


def test_migration_creates_exact_schema_and_is_idempotent(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.sqlite'}")
    first = run_local_v2_migration(engine, allow_local_ephemeral=True)
    second = run_local_v2_migration(engine, allow_local_ephemeral=True)
    snapshot = persistence_v2_schema_snapshot(engine)

    assert first.table_count == 7
    assert set(first.tables_created) == set(PERSISTENCE_V2_TABLE_NAMES)
    assert second.tables_created == ()
    assert second.legacy_registry_inserted == 0
    assert set(snapshot["tables"]) == set(PERSISTENCE_V2_TABLE_NAMES)
    assert all(not row.get("missing") for row in snapshot["tables"].values())
    assert snapshot["tables"]["accepted_assessment_v2"]["foreign_keys"]
    assert snapshot["tables"]["warning_state_v2"]["foreign_keys"]


def test_migration_preserves_and_classifies_existing_legacy_rows(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.sqlite'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE thesisassessment ("
                "id INTEGER PRIMARY KEY, ticker VARCHAR NOT NULL, "
                "assessment_date DATE NOT NULL, status VARCHAR, "
                "business_thesis_change VARCHAR)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO thesisassessment "
                "(id, ticker, assessment_date, status, business_thesis_change) "
                "VALUES (1, 'TEST', '2026-09-13', 'unchanged', 'unchanged')"
            )
        )
    first = run_local_v2_migration(engine, allow_local_ephemeral=True)
    second = run_local_v2_migration(engine, allow_local_ephemeral=True)

    with engine.connect() as connection:
        legacy = connection.execute(text("SELECT * FROM thesisassessment")).mappings().all()
        registry = connection.execute(select(assessment_source_registry_v2)).mappings().all()
    assert first.legacy_registry_inserted == 1
    assert second.legacy_registry_inserted == 0
    assert len(legacy) == 1
    assert registry[0]["source_domain"] == "LEGACY_UNVERIFIED"
    assert registry[0]["automation_eligible"] is False
    assert _count(engine, canonical_acceptance_receipt_v1) == 0


def test_local_gate_rejects_disabled_non_sqlite_and_non_ephemeral(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'local.sqlite'}")
    with pytest.raises(PersistenceV2LocalGateError, match="local_gate_disabled"):
        run_local_v2_migration(engine)

    workspace_engine = create_engine("sqlite:///./not-ephemeral.sqlite")
    with pytest.raises(PersistenceV2LocalGateError, match="ephemeral_path_required"):
        run_local_v2_migration(workspace_engine, allow_local_ephemeral=True)

    settings = Settings()
    assert settings.persistence_v2_writer_enabled is False
    assert settings.persistence_v2_read_preference_enabled is False
    assert settings.persistence_v2_manual_registry_enabled is False
    assert settings.persistence_v2_warning_enabled is False
    assert settings.persistence_v2_outbox_delivery_enabled is False


def test_receipt_contract_repeat_and_pure_verification() -> None:
    result = _trusted_result()
    accepted_at = datetime(2026, 9, 14, 4, 0, tzinfo=UTC)
    first = issue_canonical_acceptance_receipt(result, accepted_at=accepted_at)
    second = issue_canonical_acceptance_receipt(
        result,
        accepted_at=accepted_at + timedelta(hours=1),
        existing_receipt=first,
    )

    assert len(type(first).model_fields) == 25
    assert acceptance_id_for(result) == first.acceptance_id
    assert second.acceptance_id == first.acceptance_id
    assert second.accepted_at == first.accepted_at
    assert second.receipt_hash == first.receipt_hash
    assert verify_canonical_acceptance_receipt(
        first,
        trusted_result=result,
        accepted_payload=result.accepted_payload.model_dump(mode="json"),
    ).valid

    with pytest.raises(CanonicalReceiptError, match="trusted_finalization_result_type_required"):
        issue_canonical_acceptance_receipt({"ticker": "TEST"})  # type: ignore[arg-type]
    with pytest.raises(CanonicalReceiptError, match="canonical_receipt_envelope_invalid"):
        parse_receipt({"ticker": "TEST"})


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    (
        ("ticker", "OTHER", "acceptance_id_mismatch"),
        ("receipt_hash", "0" * 64, "receipt_hash_mismatch"),
        ("trusted_issuer_id", "external", "trusted_issuer_not_allowed"),
        ("packet_hash", "1" * 64, "acceptance_id_mismatch"),
        (
            "accepted_payload_contract_version",
            "unsupported-output-v0",
            "accepted_payload_contract_unsupported",
        ),
    ),
)
def test_receipt_tampering_is_rejected(field: str, value: object, expected_error: str) -> None:
    receipt = issue_canonical_acceptance_receipt(_trusted_result())
    tampered = receipt.model_copy(update={field: value})
    verification = verify_canonical_acceptance_receipt(tampered)
    assert verification.valid is False
    assert expected_error in verification.errors


def test_failed_quarantined_and_naive_results_cannot_reach_issuance() -> None:
    valid = _trusted_result()
    for invalid in (
        replace(valid, finalization_status="FAIL"),
        replace(valid, core_immutability_status="FAIL"),
        replace(valid, canonical_semantic_audit_status="FAIL"),
        replace(valid, quarantine_reason_codes=("fixture-quarantine",)),
        replace(valid, effective_at=valid.effective_at.replace(tzinfo=None)),
    ):
        with pytest.raises(CanonicalReceiptError):
            acceptance_id_for(invalid)


def test_persist_readback_duplicate_and_extract_integrity(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    result = _trusted_result()
    first = service.apply(result, accepted_at=datetime(2026, 9, 14, 4, 0, tzinfo=UTC))
    duplicate = service.apply(
        result,
        accepted_at=datetime(2026, 9, 14, 5, 0, tzinfo=UTC),
    )
    current = read_current_assessment_v2(engine, "TEST", allow_local_ephemeral=True)

    assert first.eligibility == PersistenceEligibility.ELIGIBLE_CANONICAL
    assert duplicate.eligibility == PersistenceEligibility.IDEMPOTENT_ALREADY_APPLIED
    assert duplicate.receipt_hash == first.receipt_hash
    assert _count(engine, canonical_acceptance_receipt_v1) == 1
    assert _count(engine, accepted_assessment_v2) == 1
    assert _count(engine, monitoring_current_state_v2) == 1
    assert current.status == "AVAILABLE"
    assert current.canonical_payload == result.accepted_payload.model_dump(mode="json")

    receipt = issue_canonical_acceptance_receipt(result)
    row = accepted_assessment_row(result, receipt)
    row["core_judgment_json"] = json.dumps({"text": "tampered"})
    with pytest.raises(PersistenceV2IntegrityError, match="accepted_extract_mismatch"):
        validate_extract_consistency(row)


def test_same_date_distinct_generation_and_stale_replay(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    base_time = datetime(2026, 9, 14, 3, 0, tzinfo=UTC)
    older = _trusted_result(
        generation_id="generation-001",
        generated_at=base_time,
        effective_at=base_time,
    )
    newer = _trusted_result(
        generation_id="generation-002",
        generated_at=base_time + timedelta(minutes=1),
        effective_at=base_time,
    )
    newest = _trusted_result(
        generation_id="generation-003",
        generated_at=base_time + timedelta(minutes=2),
        effective_at=base_time,
    )

    assert service.apply(newer).current_advanced
    stale = service.apply(older)
    assert stale.eligibility == PersistenceEligibility.REJECTED_STALE
    assert stale.history_inserted
    assert service.apply(newest).current_advanced

    with engine.connect() as connection:
        current = connection.execute(select(monitoring_current_state_v2)).mappings().one()
    assert current["latest_generation_id"] == "generation-003"
    assert int(current["row_version"]) == 2
    assert _count(engine, accepted_assessment_v2) == 3


def test_warning_lifecycle_and_stale_guards(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    base = datetime(2026, 9, 14, 3, 0, tzinfo=UTC)

    def apply(index: int, value: str):
        at = base + timedelta(minutes=index)
        return service.apply(
            _trusted_result(
                generation_id=f"generation-{index:03d}",
                generated_at=at,
                effective_at=at,
            ),
            warning_observations=(_observation(value),),
        )

    opened_result = _trusted_result(
        generation_id="generation-001",
        generated_at=base + timedelta(minutes=1),
        effective_at=base + timedelta(minutes=1),
    )
    opened = service.apply(
        opened_result,
        warning_observations=(_observation("CONFIRMED"),),
    )
    replay = service.apply(
        opened_result,
        warning_observations=(_observation("WORSENED"),),
    )
    confirmed = apply(2, "CONFIRMED")
    escalated = apply(3, "WORSENED")
    recovered = apply(4, "RECOVERED")
    recurred = apply(5, "CONFIRMED")

    assert len(opened.warning_transition_ids) == 1
    assert replay.eligibility == PersistenceEligibility.IDEMPOTENT_ALREADY_APPLIED
    assert confirmed.warning_transition_ids == ()
    assert len(escalated.warning_transition_ids) == 1
    assert len(recovered.warning_transition_ids) == 1
    assert len(recurred.warning_transition_ids) == 1
    with engine.connect() as connection:
        state = connection.execute(select(warning_state_v2)).mappings().one()
    assert state["state"] == "open"
    assert state["episode"] == 2
    assert _count(engine, warning_transition_v2) == 4

    stale = service.apply(
        _trusted_result(
            generation_id="generation-000",
            generated_at=base,
            effective_at=base,
        ),
        warning_observations=(_observation("WORSENED"),),
        material_notification=MaterialTransitionNotificationV1(
            channel="fake-test",
            payload_contract_version="material-warning-v1",
            payload={"kind": "warning"},
        ),
    )
    assert stale.eligibility == PersistenceEligibility.REJECTED_STALE
    assert _count(engine, warning_transition_v2) == 4
    assert _count(engine, notification_outbox_v2) == 0

    stale_recovery = service.apply(
        _trusted_result(
            generation_id="generation-stale-recovery",
            generated_at=base - timedelta(minutes=1),
            effective_at=base - timedelta(minutes=1),
        ),
        warning_observations=(_observation("RECOVERED"),),
    )
    assert stale_recovery.eligibility == PersistenceEligibility.REJECTED_STALE
    assert _count(engine, warning_transition_v2) == 4


def test_outbox_dedupe_postcommit_retry_and_dead_letter(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    daily = DailySummaryNotificationV1(
        schedule_run_id="schedule-slot-001",
        channel="fake-test",
        payload_contract_version="daily-summary-v1",
        payload={"ticker": "TEST"},
    )
    result = service.apply(
        _trusted_result(),
        daily_notification=daily,
        accepted_at=datetime(2026, 9, 14, 4, 0, tzinfo=UTC),
    )
    assert len(result.outbox_event_ids) == 1
    assert _count(engine, notification_outbox_v2) == 1
    duplicate = service.apply(
        _trusted_result(),
        daily_notification=daily,
        accepted_at=datetime(2026, 9, 14, 5, 0, tzinfo=UTC),
    )
    assert duplicate.eligibility == PersistenceEligibility.IDEMPOTENT_ALREADY_APPLIED
    assert _count(engine, notification_outbox_v2) == 1

    failed_sender = FakeOutboxSender(fail=True)
    first_retry = dispatch_pending_outbox(
        engine,
        failed_sender,
        allow_local_ephemeral=True,
        now=datetime(2026, 9, 14, 6, 0, tzinfo=UTC),
    )
    second_retry = dispatch_pending_outbox(
        engine,
        failed_sender,
        allow_local_ephemeral=True,
        now=datetime(2026, 9, 14, 6, 2, tzinfo=UTC),
    )
    dead = dispatch_pending_outbox(
        engine,
        failed_sender,
        allow_local_ephemeral=True,
        now=datetime(2026, 9, 14, 6, 5, tzinfo=UTC),
    )
    assert first_retry == {"sent": 0, "retry": 1, "dead_letter": 0}
    assert second_retry == {"sent": 0, "retry": 1, "dead_letter": 0}
    assert dead == {"sent": 0, "retry": 0, "dead_letter": 1}

    with engine.connect() as connection:
        row = connection.execute(select(notification_outbox_v2)).mappings().one()
    assert row["outbox_event_id"] == result.outbox_event_ids[0]
    assert row["status"] == "dead_letter"
    assert row["attempt_count"] == 3

    with pytest.raises(PersistenceV2LocalGateError, match="fake_sender_instance_required"):
        dispatch_pending_outbox(
            engine,
            lambda _row: None,  # type: ignore[arg-type]
            allow_local_ephemeral=True,
        )


def test_material_outbox_exists_only_for_material_transition(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    material = MaterialTransitionNotificationV1(
        channel="fake-test",
        payload_contract_version="material-warning-v1",
        payload={"ticker": "TEST"},
    )
    base = datetime(2026, 9, 14, 3, 0, tzinfo=UTC)
    opened = service.apply(
        _trusted_result(generation_id="generation-001", generated_at=base),
        warning_observations=(_observation("CONFIRMED"),),
        material_notification=material,
        accepted_at=datetime(2026, 9, 14, 4, 0, tzinfo=UTC),
    )
    confirmed = service.apply(
        _trusted_result(
            generation_id="generation-002",
            generated_at=base + timedelta(minutes=1),
            effective_at=base + timedelta(minutes=1),
        ),
        warning_observations=(_observation("CONFIRMED"),),
        material_notification=material,
    )
    assert len(opened.outbox_event_ids) == 1
    assert confirmed.outbox_event_ids == ()
    assert _count(engine, notification_outbox_v2) == 1

    sender = FakeOutboxSender()
    sent = dispatch_pending_outbox(
        engine,
        sender,
        allow_local_ephemeral=True,
        now=datetime(2026, 9, 14, 8, 0, tzinfo=UTC),
    )
    assert sent["sent"] == 1
    assert sender.sent_event_ids == list(opened.outbox_event_ids)


@pytest.mark.parametrize(
    "failure_point",
    ("history_insert", "current_state_cas", "warning_transition", "outbox_insert"),
)
def test_precommit_failure_injection_rolls_back_everything(
    tmp_path: Path,
    failure_point: str,
) -> None:
    engine = _engine(tmp_path, f"failure-{failure_point}.sqlite")
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    kwargs: dict[str, object] = {}
    if failure_point in {"warning_transition", "outbox_insert"}:
        kwargs["warning_observations"] = (_observation("CONFIRMED"),)
    if failure_point == "outbox_insert":
        kwargs["daily_notification"] = DailySummaryNotificationV1(
            schedule_run_id="schedule-slot-failure",
            channel="fake-test",
            payload_contract_version="daily-summary-v1",
            payload={"ticker": "TEST"},
        )
    with pytest.raises(PersistenceV2Error, match="injected"):
        service.apply(_trusted_result(), failure_injection=failure_point, **kwargs)
    for table in (
        canonical_acceptance_receipt_v1,
        accepted_assessment_v2,
        monitoring_current_state_v2,
        warning_state_v2,
        warning_transition_v2,
        notification_outbox_v2,
    ):
        assert _count(engine, table) == 0


def test_after_commit_failure_preserves_atomic_state(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    daily = DailySummaryNotificationV1(
        schedule_run_id="schedule-slot-after-commit",
        channel="fake-test",
        payload_contract_version="daily-summary-v1",
        payload={"ticker": "TEST"},
    )
    with pytest.raises(PersistenceV2Error, match="after_commit"):
        service.apply(
            _trusted_result(),
            daily_notification=daily,
            failure_injection="after_commit_before_send",
        )
    assert _count(engine, canonical_acceptance_receipt_v1) == 1
    assert _count(engine, accepted_assessment_v2) == 1
    assert _count(engine, monitoring_current_state_v2) == 1
    assert _count(engine, notification_outbox_v2) == 1


def test_concurrent_identical_and_distinct_writers_keep_max_order(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    base = datetime(2026, 9, 14, 3, 0, tzinfo=UTC)
    identical = _trusted_result(generation_id="generation-001", generated_at=base)

    def apply(result):
        return CanonicalAssessmentPersistenceV2(
            engine,
            allow_local_ephemeral=True,
        ).apply(result)

    with ThreadPoolExecutor(max_workers=2) as executor:
        same_results = tuple(executor.map(apply, (identical, identical)))
    assert {row.eligibility for row in same_results} == {
        PersistenceEligibility.ELIGIBLE_CANONICAL,
        PersistenceEligibility.IDEMPOTENT_ALREADY_APPLIED,
    }
    assert _count(engine, accepted_assessment_v2) == 1

    older = _trusted_result(
        generation_id="generation-002",
        generated_at=base + timedelta(minutes=1),
        effective_at=base + timedelta(minutes=1),
    )
    newer = _trusted_result(
        generation_id="generation-003",
        generated_at=base + timedelta(minutes=1),
        effective_at=base + timedelta(minutes=1),
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        tuple(executor.map(apply, (newer, older)))
    with engine.connect() as connection:
        current = connection.execute(select(monitoring_current_state_v2)).mappings().one()
    assert current["latest_generation_id"] == "generation-003"
    assert _count(engine, accepted_assessment_v2) == 3


def test_current_state_cas_conflict_is_reread_and_boundedly_retried(
    tmp_path: Path,
) -> None:
    engine = _engine(tmp_path)
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    base = datetime(2026, 9, 14, 3, 0, tzinfo=UTC)
    service.apply(_trusted_result(generation_id="generation-001", generated_at=base))
    newer = _trusted_result(
        generation_id="generation-002",
        generated_at=base + timedelta(minutes=1),
        effective_at=base + timedelta(minutes=1),
    )
    receipt = issue_canonical_acceptance_receipt(newer)

    with engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")

        class ConflictOnce:
            def __init__(self) -> None:
                self.conflict_count = 0

            def execute(self, statement, *args, **kwargs):
                if (
                    getattr(statement, "is_update", False)
                    and getattr(getattr(statement, "table", None), "name", None)
                    == monitoring_current_state_v2.name
                    and self.conflict_count == 0
                ):
                    self.conflict_count += 1
                    return SimpleNamespace(rowcount=0)
                return connection.execute(statement, *args, **kwargs)

        proxy = ConflictOnce()
        advanced = service._advance_current_state(
            proxy,  # type: ignore[arg-type]
            result=newer,
            receipt=receipt,
            now=datetime(2026, 9, 14, 4, 0, tzinfo=UTC),
        )
        connection.commit()

    with engine.connect() as connection:
        current = connection.execute(select(monitoring_current_state_v2)).mappings().one()
    assert proxy.conflict_count == 1
    assert advanced is True
    assert current["latest_generation_id"] == "generation-002"
    assert current["row_version"] == 2


def test_manual_boundary_registry_and_dual_reads(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="reserved_canonical_acceptance_fields"):
        ThesisAssessmentCreate.model_validate(
            {
                "assessment_date": "2026-09-14",
                "business_thesis_change": "unchanged",
                "valuation_context": "neutral",
                "acceptance_id": "spoof",
            }
        )

    engine = create_engine(f"sqlite:///{tmp_path / 'dual.sqlite'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE thesisassessment ("
                "id INTEGER PRIMARY KEY, ticker VARCHAR NOT NULL, "
                "assessment_date DATE NOT NULL, status VARCHAR, "
                "business_thesis_change VARCHAR)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO thesisassessment "
                "(id, ticker, assessment_date, status, business_thesis_change) "
                "VALUES (1, 'TEST', '2026-09-13', 'unchanged', 'unchanged')"
            )
        )
    run_local_v2_migration(engine, allow_local_ephemeral=True)
    with engine.begin() as connection:
        changed = classify_legacy_assessment(
            connection,
            assessment_id=1,
            source_domain=PersistenceSourceDomain.MANUAL_USER_AUTHORED,
        )
    assert changed

    legacy_current = read_current_assessment_v2(
        engine,
        "TEST",
        allow_local_ephemeral=True,
    )
    assert legacy_current.source_domain == PersistenceSourceDomain.MANUAL_USER_AUTHORED
    assert legacy_current.automation_eligible is False

    CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True).apply(
        _trusted_result()
    )
    current = read_current_assessment_v2(engine, "TEST", allow_local_ephemeral=True)
    history = read_assessment_history_v2(engine, "TEST", allow_local_ephemeral=True)
    assert current.source_domain == PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED
    assert current.automation_eligible is True
    assert [row.source_domain for row in history] == [
        PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED,
        PersistenceSourceDomain.MANUAL_USER_AUTHORED,
    ]

    with engine.begin() as connection:
        with pytest.raises(AssessmentSourceRegistryError, match="canonical_source_not_allowed"):
            classify_legacy_assessment(
                connection,
                assessment_id=1,
                source_domain=PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED,
            )


def test_future_manual_write_is_classified_in_record_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'manual-integration.sqlite'}")
    SQLModel.metadata.create_all(engine)
    run_local_v2_migration(engine, allow_local_ephemeral=True)
    monkeypatch.setattr(
        monitoring_service,
        "get_settings",
        lambda: SimpleNamespace(persistence_v2_manual_registry_enabled=True),
    )
    monkeypatch.setattr(monitoring_service, "reconcile_onboarding", lambda *_args: None)
    monkeypatch.setattr(monitoring_service, "export_assessment_history", lambda *_args: None)
    with Session(engine) as session:
        session.add(
            WatchlistItem(
                ticker="TEST",
                company_name="Test",
                exchange="NYSE",
                active=True,
                monitoring_requested=True,
                onboarding_state="ACTIVE",
                production_eligible=True,
            )
        )
        session.add(
            InvestmentThesis(
                ticker="TEST",
                version=1,
                core_thesis="Local fixture thesis",
                status="active",
            )
        )
        session.commit()
        monitoring_service.record_assessment(
            session,
            "TEST",
            ThesisAssessmentCreate(
                assessment_date=date(2026, 9, 14),
                business_thesis_change="no_material_change",
                valuation_context="neutral",
            ),
        )
        assessment = session.execute(
            select(ThesisAssessment).where(ThesisAssessment.ticker == "TEST")
        ).scalars().one()
        registry = session.execute(
            select(assessment_source_registry_v2).where(
                assessment_source_registry_v2.c.legacy_assessment_id == assessment.id
            )
        ).mappings().one()
    assert assessment.id is not None
    assert registry["source_domain"] == "MANUAL_USER_AUTHORED"
    assert registry["automation_eligible"] is False


def test_corrupt_v2_current_pointer_fails_closed_without_legacy_fallback(
    tmp_path: Path,
) -> None:
    engine = _engine(tmp_path)
    CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True).apply(
        _trusted_result()
    )
    with engine.begin() as connection:
        connection.execute(
            update(accepted_assessment_v2).values(canonical_payload_sha256="0" * 64)
        )
    current = read_current_assessment_v2(engine, "TEST", allow_local_ephemeral=True)
    assert current.status == "UNAVAILABLE"
    assert current.reason == "corrupt_v2_current_pointer"
    assert current.canonical_payload is None


def test_corrupt_v2_history_receipt_fails_closed(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True).apply(
        _trusted_result()
    )
    with engine.begin() as connection:
        connection.execute(
            update(canonical_acceptance_receipt_v1).values(receipt_hash="0" * 64)
        )
    with pytest.raises(PersistenceV2IntegrityError, match="v2_history_integrity_failure"):
        read_assessment_history_v2(engine, "TEST", allow_local_ephemeral=True)


def test_business_delta_projection_and_ticker_timezone_boundaries() -> None:
    assert project_canonical_business_delta_to_legacy("STRENGTHENED") == (
        "strengthened",
        "SUPPORTED",
    )
    assert project_canonical_business_delta_to_legacy("UNCHANGED") == (
        "no_material_change",
        "SUPPORTED",
    )
    assert project_canonical_business_delta_to_legacy("WEAKENED") == (
        "weakened",
        "SUPPORTED",
    )
    assert project_canonical_business_delta_to_legacy("UNRESOLVED") == (
        None,
        "UNSUPPORTED",
    )
    with pytest.raises(CanonicalReceiptError, match="ticker_not_canonical"):
        _trusted_result("bad ticker")
    with pytest.raises(CanonicalReceiptError, match="source_snapshot_ticker_not_canonical"):
        source_evidence_snapshot_identity(
            packet_bytes=b"{}",
            packet_contract="packet-v1",
            ticker="bad ticker",
        )
    kr_result = _trusted_result("000660")
    assert kr_result.ticker == "000660"
    with pytest.raises(CanonicalReceiptError, match="source_snapshot_ticker_not_canonical"):
        _trusted_result("660")
    with pytest.raises(CanonicalReceiptError, match="source_snapshot_ticker_not_canonical"):
        _trusted_result("ibm")
    with pytest.raises(CanonicalReceiptError, match="source_snapshot_ticker_not_canonical"):
        source_evidence_snapshot_identity(
            packet_bytes=b"{}",
            packet_contract="packet-v1",
            ticker=660,  # type: ignore[arg-type]
        )

    offset_result = _trusted_result(
        generated_at=datetime.fromisoformat("2026-09-14T11:47:41+09:00"),
        effective_at=datetime.fromisoformat("2026-09-14T12:00:00+09:00"),
    )
    utc_result = _trusted_result(
        generated_at=datetime.fromisoformat("2026-09-14T02:47:41+00:00"),
        effective_at=datetime.fromisoformat("2026-09-14T03:00:00+00:00"),
    )
    assert acceptance_id_for(offset_result) == acceptance_id_for(utc_result)


def _load_m12bj_rows() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    identities = json.loads(M12BJ_IDENTITY_REPORT.read_text())["frozen_identities"]
    by_ticker = {str(row["ticker"]): row for row in identities}
    rows: list[dict[str, object]] = []
    for path in sorted((M12BJ_ROOT / "model-calls").glob("context-*/stage2/run-document.json")):
        run = json.loads(path.read_text())
        for final, composition in zip(run["final_rows"], run["compositions"], strict=True):
            rows.append(
                {
                    "run": run,
                    "final": final,
                    "composition": composition,
                }
            )
    return rows, by_ticker


def _real_trusted_result(row: dict[str, object], identity: dict[str, object]):
    final = row["final"]
    composition = row["composition"]
    run = row["run"]
    ticker = str(final["ticker"])
    packet_path = M12BJ_ROOT / "frozen-packets" / f"{ticker}.json"
    packet_bytes = packet_path.read_bytes()
    packet = json.loads(packet_bytes)
    stock = packet["stocks"][0]
    generated_at = json.loads(M12BJ_GENERATION_MANIFEST.read_text())["generated_at"]
    security_basis = {
        "contract": "security-basis-provenance-v1",
        "ticker": ticker,
        "market": packet["market"],
        "financial_currency": stock.get("valuation", {}).get("financial_currency"),
        "price_currency": stock.get("valuation", {}).get("currency"),
        "issuer_type": stock.get("valuation", {}).get("resolved_issuer_type"),
        "security_type": stock.get("valuation", {}).get("resolved_security_type"),
        "is_depositary_security": stock.get("valuation", {}).get(
            "is_depositary_security"
        ),
        "eps_security_basis": stock.get("valuation", {}).get("eps_security_basis"),
        "identity_status": stock.get("valuation", {}).get(
            "security_identity_verification_status"
        ),
        "identity_as_of": stock.get("valuation", {}).get("security_identity_as_of"),
    }
    snapshot = source_evidence_snapshot_identity(
        packet_bytes=packet_bytes,
        packet_contract=f"daily-monitor-packet-v{packet['schema_version']}",
        ticker=ticker,
        component_hashes={
            "security_basis_provenance_sha256": canonical_sha256(security_basis),
        },
    )
    assert snapshot.packet_digest == identity["packet_sha256"]
    assert canonical_sha256(final["core"]) == identity["final_composed_candidate_sha256"]
    assert composition["core_snapshot_sha256"] == identity["core_sha256"]
    assert canonical_sha256(composition["stance"]) == identity["stance_sha256"]
    return trusted_finalization_result(
        generation_id=str(run["generation_id"]),
        generation_generated_at=datetime.fromisoformat(generated_at),
        ticker=ticker,
        thesis_version=int(stock["thesis_version"]),
        assessment_date=date.fromisoformat(packet["assessment_date"]),
        effective_at=datetime.fromisoformat(packet["generated_at"]),
        source_packet_id=str(packet["packet_id"]),
        source_packet_bytes=packet_bytes,
        source_snapshot=snapshot,
        accepted_payload=DirectionalCoreCandidate.model_validate(final["core"]),
        canonical_semantic_audit_contract=str(final["canonical_semantic_audit"]["contract"]),
        canonical_semantic_audit_status=str(final["canonical_semantic_audit"]["status"]),
        finalization_status=str(final["status"]),
        core_immutability_status=(
            "PASS"
            if composition["core_snapshot_sha256"]
            == composition["post_compose_core_sha256"]
            else "FAIL"
        ),
        core_hash=str(composition["core_snapshot_sha256"]),
        stance_hash=canonical_sha256(composition["stance"]),
        security_basis_provenance=security_basis,
    )


@pytest.mark.skipif(not M12BJ_ROOT.is_dir(), reason="local frozen M12BJ source unavailable")
def test_frozen_m12bj_22_receipt_persistence_readback_and_provenance(
    tmp_path: Path,
) -> None:
    rows, identities = _load_m12bj_rows()
    assert len(rows) == 22
    assert len(identities) == 22
    engine = _engine(tmp_path, "m12bj-22.sqlite")
    service = CanonicalAssessmentPersistenceV2(engine, allow_local_ephemeral=True)
    accepted_ids: set[str] = set()
    for row in rows:
        ticker = str(row["final"]["ticker"])
        result = _real_trusted_result(row, identities[ticker])
        applied = service.apply(result)
        current = read_current_assessment_v2(engine, ticker, allow_local_ephemeral=True)
        assert applied.eligibility == PersistenceEligibility.ELIGIBLE_CANONICAL
        assert current.status == "AVAILABLE"
        assert current.canonical_payload == result.accepted_payload.model_dump(mode="json")
        assert current.receipt_hash == applied.receipt_hash
        accepted_ids.add(str(applied.acceptance_id))
    assert len(accepted_ids) == 22
    assert _count(engine, canonical_acceptance_receipt_v1) == 22
    assert _count(engine, accepted_assessment_v2) == 22
    assert _count(engine, monitoring_current_state_v2) == 22


def test_historical_fresh_16_failed_rows_cannot_mint_receipts() -> None:
    audit = json.loads(HISTORICAL_NEGATIVE_REPORT.read_text())
    rows = audit["rows"]
    assert len(rows) == 16
    rejected = 0
    for index, row in enumerate(rows):
        assert row["canonical_status"] == "FAIL"
        assert "BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY" in row[
            "canonical_hard_errors"
        ]
        valid = _trusted_result(
            str(row["ticker"]),
            generation_id=f"historical-negative-{index:02d}",
        )
        invalid = replace(valid, canonical_semantic_audit_status="FAIL")
        with pytest.raises(CanonicalReceiptError, match="canonical_semantic_audit_not_pass"):
            issue_canonical_acceptance_receipt(invalid)
        rejected += 1
    assert rejected == 16
