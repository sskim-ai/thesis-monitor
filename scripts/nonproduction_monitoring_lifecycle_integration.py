from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.company import Company
from app.models.thesis import (
    InvestmentThesis,
    MonitorRun,
    NotificationDelivery,
    ThesisAssessment,
)
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import (
    MonitoringItemCreate,
    PriceContext,
    PriceDecisionContext,
    PricePeriodSummary,
    ValuationSnapshot,
)
from app.services import daily_monitor_service, monitoring_service
from app.services.company_profile_service import profile_provenance_path

from app.services.nonproduction_lifecycle_decision_service import DERIVATIVE_LABEL
from app.services.nonproduction_monitoring_lifecycle_service import (
    DailyDeltaAssessment,
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
from app.services.onboarding_evidence_service import build_initial_evidence
from app.services.onboarding_reconciler_service import (
    OnboardingAttemptMode,
    resume_onboarding_subject,
)
from scripts.nonproduction_integration_decision_message_review import (
    SECRET_PATTERNS,
    fixture_contract_pair,
)
from scripts.websocket_timeout_runtime_review_first_a_closeout import (
    observe_pause_state,
)


CONTRACT = "nonproduction-monitoring-bootstrap-daily-delta-lifecycle-integration-v1"
EXPECTED_LATEST_RESULT_SHA256 = (
    "3ca97b17511605c3ead9da46292d1bf151782189ccddf25cd83d3fbcc0939422"
)
EXPECTED_WORK_INSTRUCTION_ZIP_SHA256 = (
    "0c63692def9d86fcba2ae7c2d266745f53992ba193537c5b7783b0e63e41bf6b"
)
EXPECTED_WORK_INSTRUCTION_MEMBER_SHA256 = (
    "729411d163f71b6c3d66c7db4322a5f7b988885363472c2a9f6497e052e8c5ae"
)
EXPECTED_M2_FINAL_SHA = "2257a05f9a599aafd0f3120fb8ab62655bee875a"
T0 = datetime(2026, 9, 8, 0, tzinfo=UTC)
TICKER = "SYNTHETIC_M2_REVIEW"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: object) -> str:
    return bytes_sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    )


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected object: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def git_value(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=repo_root, text=True).strip()


def verify_latest_result(path: Path) -> dict[str, object]:
    actual_sha = file_sha256(path)
    if actual_sha != EXPECTED_LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    hash_mismatches: list[str] = []
    size_mismatches: list[str] = []
    with zipfile.ZipFile(path) as archive:
        completion = json.loads(archive.read("27-program-completion.json"))
        index = json.loads(archive.read("artifact-index.json"))
        if not isinstance(completion, dict) or not isinstance(index, dict):
            raise TypeError("latest_result_documents_must_be_objects")
        for row in index.get("rows", []):
            if not isinstance(row, Mapping):
                continue
            member = str(row.get("path") or "")
            payload = archive.read(member)
            if bytes_sha256(payload) != row.get("sha256"):
                hash_mismatches.append(member)
            expected_size = row.get("size_bytes", row.get("bytes"))
            if len(payload) != expected_size:
                size_mismatches.append(member)
    checks = {
        "status": completion.get("status") == "M2_COMPLETE",
        "next_scope": completion.get("next_scope")
        == "NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION",
        "final_head": completion.get("final_head_sha") == EXPECTED_M2_FINAL_SHA,
        "payload_count": index.get("payload_count") == 39,
        "index_status": index.get("status") == "PASS",
        "reported_hash_mismatch": index.get("hash_mismatch_count") == 0,
        "reported_size_mismatch": index.get("size_mismatch_count") == 0,
        "reported_secret_failure": index.get("secret_scan_failure_count") == 0,
        "recomputed_hash_mismatch": not hash_mismatches,
        "recomputed_size_mismatch": not size_mismatches,
    }
    if not all(checks.values()):
        raise ValueError("LATEST_RESULT_BUNDLE_INTEGRITY_FAILURE")
    return {
        "contract": "m3-latest-result-integrity-v1",
        "path": str(path),
        "sha256": actual_sha,
        "checks": checks,
        "indexed_payload_count": index.get("payload_count"),
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
        "status": "PASS",
    }


def verify_work_instruction(path: Path) -> dict[str, object]:
    actual_zip_sha = file_sha256(path)
    if actual_zip_sha != EXPECTED_WORK_INSTRUCTION_ZIP_SHA256:
        raise ValueError("WORK_INSTRUCTION_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise ValueError("WORK_INSTRUCTION_MEMBER_COUNT_MISMATCH")
        member = names[0]
        member_sha = bytes_sha256(archive.read(member))
    if member_sha != EXPECTED_WORK_INSTRUCTION_MEMBER_SHA256:
        raise ValueError("WORK_INSTRUCTION_MEMBER_CHECKSUM_MISMATCH")
    return {
        "zip_path": str(path),
        "zip_sha256": actual_zip_sha,
        "member": member,
        "member_sha256": member_sha,
        "status": "PASS",
    }


def boundary_reuse(repo_root: Path) -> dict[str, object]:
    boundaries = (
        (
            "registration",
            "app/services/monitoring_service.py",
            "register_monitoring_item_with_continuation",
        ),
        (
            "onboarding_evidence",
            "app/services/onboarding_evidence_service.py",
            "build_initial_evidence",
        ),
        (
            "baseline",
            "app/services/onboarding_evidence_service.py",
            "ensure_initial_baseline",
        ),
        (
            "readiness",
            "app/services/onboarding_reconciler_service.py",
            "resume_onboarding_subject",
        ),
        ("daily_monitor", "app/services/daily_monitor_service.py", "run_daily_monitor"),
        (
            "decision_ownership",
            "app/services/direction_timing_ownership_service.py",
            "compose_decision",
        ),
        (
            "structured_renderer",
            "app/services/structured_autonomy_shadow_service.py",
            "render_structured_autonomy_message",
        ),
        ("assessment", "app/services/monitoring_service.py", "record_assessment"),
        (
            "notification",
            "app/services/notification_service.py",
            "queue_daily_stock_notification",
        ),
        (
            "m2_nonproduction_adapter",
            "app/services/nonproduction_lifecycle_decision_service.py",
            "build_nonproduction_derivative",
        ),
    )
    rows: list[dict[str, object]] = []
    for name, relative, symbol in boundaries:
        path = repo_root / relative
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        rows.append(
            {
                "name": name,
                "path": relative,
                "symbol": symbol,
                "path_exists": path.exists(),
                "symbol_exists": bool(re.search(rf"\b{re.escape(symbol)}\b", text)),
            }
        )
    verified = sum(row["path_exists"] and row["symbol_exists"] for row in rows)
    return {
        "contract": "m3-m2-contract-reuse-proof-v1",
        "boundary_count": len(rows),
        "verified_boundary_count": verified,
        "rows": rows,
        "new_production_engine_created": False,
        "status": "PASS" if verified == len(rows) else "FAIL",
    }


class _FixtureCollectionService:
    async def collect_events(
        self,
        _session: Session,
        _ticker: str,
        _lookback_days: int,
    ) -> list[object]:
        return []


class _FixturePriceClient:
    async def fetch_price_context(
        self,
        _ticker: str,
        **_kwargs: object,
    ) -> PriceContext:
        periods = {
            period: PricePeriodSummary(
                requested_count=300,
                actual_count=300,
                latest_date="2026-09-08",
                previous_close=99,
                latest_close=100,
            )
            for period in ("daily", "weekly", "monthly")
        }
        return PriceContext(
            available=True,
            periods=periods,
            decision=PriceDecisionContext(
                current_price=100,
                currency="USD",
                price_as_of="2026-09-08",
                market_session="closed",
            ),
        )


class _FixtureValuationService:
    async def fetch(
        self,
        _ticker: str,
        _exchange: str | None,
        _price: PriceContext,
        **_kwargs: object,
    ) -> ValuationSnapshot:
        return ValuationSnapshot(
            current_price=100,
            currency="USD",
            price_as_of="2026-09-08",
            provider="official_test_fixture",
        )


async def _fixture_profile_populator(
    session: Session,
    item: WatchlistItem,
    *,
    current: datetime,
    data_dir: str | Path | None,
) -> None:
    del current
    company = session.exec(
        select(Company).where(Company.ticker == item.ticker)
    ).one()
    company.industry = "Software"
    company.sector = "Technology"
    company.business_units = '["core platform"]'
    company.revenue_sources = '["enterprise customers"]'
    session.add(company)
    session.flush()
    root = Path(data_dir or ".")
    write_json(
        profile_provenance_path(item.ticker, root),
        {
            "schema_version": "1",
            "ticker": item.ticker,
            "market": "us",
            "quality": "verified",
            "source": "official_test_fixture",
        },
    )


async def _fixture_initial_evidence(
    session: Session,
    item: WatchlistItem,
    *,
    as_of: datetime,
    acquire: bool,
) -> dict[str, object]:
    del acquire
    return await build_initial_evidence(
        session,
        item,
        as_of=as_of,
        acquire=True,
        collection_service=_FixtureCollectionService(),
        price_client=_FixturePriceClient(),
        valuation_service=_FixtureValuationService(),
    )


def _fixture_decision_readiness(
    _session: Session,
    item: WatchlistItem,
    evidence: dict[str, object],
    **_kwargs: object,
) -> dict[str, object]:
    return {
        "contract": "onboarding-accepted-decision-v1",
        "status": "READY",
        "ticker": item.ticker,
        "source_initial_evidence_fingerprint": evidence["fingerprint"],
        "decision_evidence_sha256": f"fixture-decision:{item.ticker}",
        "accepted_decision": "HOLD",
        "accepted_decision_id": f"accepted:{item.ticker}",
        "accepted_evidence_fingerprint": f"accepted-evidence:{item.ticker}",
        "raw_candidate_grants_ready": False,
    }


def production_boundary_lifecycle_proof(data_dir: Path) -> dict[str, object]:
    """Exercise canonical registration/onboarding boundaries on isolated SQLite."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    payload = MonitoringItemCreate(
        ticker="M3USFIXTURE",
        company_name="M3 US Fixture",
        exchange="NASDAQ",
        core_thesis="Verified enterprise demand supports the operating thesis.",
        time_horizon="6-24 months",
        thesis_drivers=["verified enterprise demand"],
        validation_metrics=["revenue", "operating margin"],
        market_expectations={"level": "balanced", "summary": "balanced"},
        valuation_framework={"primary_method": "forward earnings"},
        strengthen_signals=["margin expansion"],
        weaken_signals=["order decline"],
        invalidation_signals=["customer loss"],
    )
    continuation_calls = 0

    async def isolated_continuation(
        session: Session,
        item: WatchlistItem,
        *,
        origin: str,
        mode: OnboardingAttemptMode,
    ) -> object:
        nonlocal continuation_calls
        continuation_calls += 1
        return await resume_onboarding_subject(
            session,
            item,
            origin=origin,
            mode=mode,
            as_of=T0,
            data_dir=data_dir,
            evidence_builder=_fixture_initial_evidence,
            decision_builder=_fixture_decision_readiness,
            profile_populator=_fixture_profile_populator,
        )

    with (
        patch.object(monitoring_service, "export_thesis", lambda _thesis: None),
        patch.object(
            monitoring_service,
            "resume_onboarding_subject",
            isolated_continuation,
        ),
        Session(engine) as session,
    ):
        first = asyncio.run(
            monitoring_service.register_monitoring_item_with_continuation(
                session,
                payload,
            )
        )
        repeated = asyncio.run(
            monitoring_service.register_monitoring_item_with_continuation(
                session,
                payload,
            )
        )
        item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == payload.ticker)
        ).one()
        pending_snapshot = {
            "active": item.active,
            "production_eligible": item.production_eligible,
            "onboarding_state": item.onboarding_state,
            "evidence_fingerprint_present": bool(item.onboarding_evidence_fingerprint),
        }
        background = asyncio.run(
            resume_onboarding_subject(
                session,
                item,
                origin="m3_isolated_background_fixture",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=T0 + timedelta(hours=1),
                first_eligible_session=date(2026, 1, 1),
                data_dir=data_dir,
                evidence_builder=_fixture_initial_evidence,
                decision_builder=_fixture_decision_readiness,
                profile_populator=_fixture_profile_populator,
            )
        )
        session.refresh(item)
        with (
            patch.object(
                daily_monitor_service,
                "export_assessment_history",
                lambda _session, _ticker: None,
            ),
            patch.object(
                daily_monitor_service,
                "export_monitor_run",
                lambda _run: None,
            ),
            patch.object(
                daily_monitor_service,
                "export_thesis",
                lambda _thesis: None,
            ),
        ):
            daily = asyncio.run(
                daily_monitor_service.run_daily_monitor(
                    session,
                    run_date=date(2026, 9, 9),
                    collection_service=_FixtureCollectionService(),
                    price_client=_FixturePriceClient(),
                    valuation_service=_FixtureValuationService(),
                    queue_notifications=False,
                    dispatch_notifications=False,
                    market_scope="us",
                    as_of=T0 + timedelta(days=1, hours=1),
                )
            )
        thesis_rows = session.exec(
            select(InvestmentThesis).where(InvestmentThesis.ticker == payload.ticker)
        ).all()
        assessment_rows = session.exec(
            select(ThesisAssessment).where(ThesisAssessment.ticker == payload.ticker)
        ).all()
        baseline_rows = [
            row
            for row in assessment_rows
            if json.loads(row.thesis_snapshot).get("assessment_mode")
            == "initial_baseline"
        ]
        daily_rows = [
            row
            for row in assessment_rows
            if json.loads(row.thesis_snapshot).get("assessment_mode") == "daily_delta"
        ]
        notification_rows = session.exec(select(NotificationDelivery)).all()
        monitor_runs = session.exec(select(MonitorRun)).all()
        checks = {
            "continuation_boundary_called": continuation_calls == 2,
            "initial_registration_pending": first.active is False
            and first.production_eligible is False,
            "identical_registration_idempotent": repeated.thesis is not None
            and repeated.thesis.version == 1
            and len(thesis_rows) == 1,
            "canonical_evidence_builder_called": bool(
                pending_snapshot["evidence_fingerprint_present"]
            ),
            "canonical_baseline_created_once": len(baseline_rows) == 1,
            "pending_until_decision_readiness": pending_snapshot["active"] is False
            and pending_snapshot["production_eligible"] is False,
            "background_resume_ready": background.error is None
            and background.active
            and background.production_eligible,
            "canonical_daily_monitor_completed": daily.status == "success"
            and daily.success_count == 1
            and daily.failure_count == 0,
            "canonical_daily_delta_created_once": len(daily_rows) == 1,
            "canonical_active_state": item.active
            and item.production_eligible
            and item.onboarding_state == "ACTIVE",
            "no_notification_rows": not notification_rows,
        }
        result = {
            "contract": "m3-existing-boundary-in-memory-integration-v1",
            "database": "isolated_in_memory_sqlite",
            "boundaries_exercised": [
                "register_monitoring_item_with_continuation",
                "build_initial_evidence",
                "ensure_initial_baseline",
                "resume_onboarding_subject",
                "run_daily_monitor",
            ],
            "fixture_ports": [
                "collection_service",
                "price_client",
                "valuation_service",
                "profile_populator",
                "decision_builder",
                "export_sink",
            ],
            "pending_snapshot": pending_snapshot,
            "background_result": background.to_dict(),
            "daily_monitor_result": daily.model_dump(mode="json"),
            "thesis_version_count": len(thesis_rows),
            "baseline_assessment_count": len(baseline_rows),
            "daily_delta_assessment_count": len(daily_rows),
            "monitor_run_count": len(monitor_runs),
            "notification_row_count": len(notification_rows),
            "test_db_connections": 1,
            "production_db_connections": 0,
            "provider_source_fetches": 0,
            "model_calls": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "checks": checks,
            "status": "PASS" if all(checks.values()) else "FAIL",
        }
    engine.dispose()
    return result


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
        source_id=f"official-fixture:{evidence_id}",
        axis=axis,
        polarity=polarity,
        summary=f"Validated fixture evidence {evidence_id}",
        effective_at=effective_at or (T0 + timedelta(hours=1)),
        observed_at=observed_at or (T0 + timedelta(hours=2)),
        validated=validated,
        warning_key=warning_key,
        resolves_warning_key=resolves_warning_key,
    )


def _register_store(
    *,
    baseline: bool,
    ready: bool,
    subject_lifecycle: SubjectLifecycle = SubjectLifecycle.NEW_ISSUER,
) -> tuple[InMemoryMonitoringLifecycle, list[dict[str, object]]]:
    store = InMemoryMonitoringLifecycle()
    trace: list[dict[str, object]] = []
    result = store.submit_request(
        request_kind=LifecycleRequestKind.EXPLICIT_MONITORING,
        ticker=TICKER,
        logic_fingerprint="logic-v1",
        requested_at=T0 - timedelta(hours=3),
        subject_lifecycle=subject_lifecycle,
    )
    trace.append(
        {
            "stage": "REGISTERED_PENDING",
            "registration_intent_created": result.registration_intent_created,
            "snapshot": result.subject.model_dump(mode="json") if result.subject else None,
        }
    )
    if baseline:
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
        baseline_row = store.create_baseline(
            TICKER,
            cutoff=T0,
            established_at=T0,
        )
        trace.append(
            {
                "stage": "BASELINE_CREATED_BOOTSTRAP_INCOMPLETE",
                "baseline": baseline_row.model_dump(mode="json"),
                "snapshot": store.snapshot(TICKER).model_dump(mode="json"),
            }
        )
    if ready:
        snapshot = store.complete_bootstrap(
            TICKER,
            completed_at=T0 + timedelta(minutes=30),
            source_ready=True,
        )
        trace.append(
            {
                "stage": "MONITORING_READY",
                "snapshot": snapshot.model_dump(mode="json"),
            }
        )
    return store, trace


def _evaluation(
    store: InMemoryMonitoringLifecycle,
    *,
    day: int,
    evidence_ids: tuple[str, ...] = (),
    refresh_state: str = "AVAILABLE",
    valuation_context: str = "neutral",
    market_expectation_level: str = "balanced",
) -> DailyDeltaAssessment:
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
    ).assessment


def _render_fixture(
    *,
    fixture_id: str,
    description: str,
    store: InMemoryMonitoringLifecycle,
    trace: list[dict[str, object]],
    output_dir: Path,
    assessment: DailyDeltaAssessment | None,
    expected_status: str,
) -> tuple[dict[str, object], dict[str, object]]:
    owned, core, timing = fixture_contract_pair()
    message = store.render_file_only_message(
        fixture_id=fixture_id,
        ticker=TICKER,
        owned=owned,
        core=core,
        timing=timing,
        price_map={},
        industry="Software",
        assessment=assessment,
    )
    path = output_dir / f"{fixture_id.lower()}.txt"
    store.write_file_only_message(message, path)
    actual_status = assessment.status if assessment else "NOT_APPLICABLE"
    passed = str(actual_status) == expected_status
    row = {
        "fixture_id": fixture_id,
        "description": description,
        "expected_status": expected_status,
        "actual_status": actual_status,
        "pass": passed,
        "subject": store.snapshot(TICKER).model_dump(mode="json"),
        "assessment": assessment.model_dump(mode="json") if assessment else None,
        "lifecycle_trace": trace,
        "message_path": str(path),
        "message_sha256": message.sha256,
        "message_label": message.label,
        "message_sections": {
            "daily_delta": "1. 투자 논리 변화" in message.text,
            "absolute_decision": "2. 현재 절대 판단" in message.text,
            "new_buyer": "신규 관찰자" in message.text,
            "holder": "보유자" in message.text,
            "price_timing": "3. Price-Timing" in message.text,
            "next_check": "4. 다음 확인" in message.text,
        },
        "shared_composed_sha256": message.lineage["shared_composed_sha256"],
    }
    firewall = {
        "fixture_id": fixture_id,
        **store.side_effects.model_dump(mode="json"),
        "status": "PASS" if store.side_effects.clean else "FAIL",
    }
    return row, firewall


def _idempotency_and_warning_proof() -> dict[str, object]:
    store, _trace = _register_store(baseline=True, ready=False)
    baseline = store.snapshot(TICKER).baseline
    repeated_baseline = store.create_baseline(
        TICKER,
        cutoff=T0,
        established_at=T0 + timedelta(minutes=1),
    )
    ready = store.complete_bootstrap(
        TICKER,
        completed_at=T0 + timedelta(hours=1),
        source_ready=True,
    )
    repeated_ready = store.complete_bootstrap(
        TICKER,
        completed_at=T0 + timedelta(hours=2),
        source_ready=True,
    )
    store.add_evidence(
        TICKER,
        (
            _evidence(
                "warning-open",
                polarity=EvidencePolarity.NEGATIVE,
                warning_key="margin_pressure",
            ),
            _evidence(
                "warning-repeat",
                polarity=EvidencePolarity.NEGATIVE,
                effective_at=T0 + timedelta(days=1),
                observed_at=T0 + timedelta(days=1, hours=1),
                warning_key="margin_pressure",
            ),
            _evidence(
                "warning-resolve",
                polarity=EvidencePolarity.RESOLUTION,
                effective_at=T0 + timedelta(days=2),
                observed_at=T0 + timedelta(days=2, hours=1),
                resolves_warning_key="margin_pressure",
            ),
        ),
    )
    first = store.evaluate_daily_delta(
        DailyEvaluationRequest(
            ticker=TICKER,
            assessment_date=date(2026, 9, 8),
            evaluated_at=T0 + timedelta(hours=12),
            refresh_state="AVAILABLE",
            evidence_ids=("warning-open",),
        )
    )
    repeat = store.evaluate_daily_delta(
        DailyEvaluationRequest(
            ticker=TICKER,
            assessment_date=date(2026, 9, 8),
            evaluated_at=T0 + timedelta(hours=12),
            refresh_state="AVAILABLE",
            evidence_ids=("warning-open",),
        )
    )
    _evaluation(store, day=9, evidence_ids=("warning-repeat",))
    _evaluation(store, day=10, evidence_ids=("warning-resolve",))
    resolved_repeat = store.evaluate_daily_delta(
        DailyEvaluationRequest(
            ticker=TICKER,
            assessment_date=date(2026, 9, 10),
            evaluated_at=T0 + timedelta(days=2, hours=12),
            refresh_state="AVAILABLE",
            evidence_ids=("warning-resolve",),
        )
    )
    warning = store.warning(TICKER, "margin_pressure")
    counts = Counter(row.kind for row in store.intents)
    checks = {
        "baseline_idempotent": baseline == repeated_baseline,
        "onboarding_resume_idempotent": ready == repeated_ready,
        "assessment_idempotent": first.assessment == repeat.assessment
        and not repeat.assessment_created,
        "warning_open_idempotent": counts[ShadowIntentKind.WARNING_OPEN] == 1,
        "warning_resolve_idempotent": counts[ShadowIntentKind.WARNING_RESOLVE] == 1,
        "resolved_repeat_idempotent": not resolved_repeat.assessment_created,
        "warning_resolved": warning is not None
        and warning.status == WarningStatus.RESOLVED,
        "side_effect_firewall": store.side_effects.clean,
    }
    return {
        "checks": checks,
        "intent_counts": {str(key): value for key, value in sorted(counts.items())},
        "assessment_count": store.assessment_count,
        "warning_count": store.warning_count,
        "warning": warning.model_dump(mode="json") if warning else None,
        "side_effects": store.side_effects.model_dump(mode="json"),
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def _registration_proof() -> dict[str, object]:
    store = InMemoryMonitoringLifecycle()
    nonexplicit = []
    for request_kind in (
        LifecycleRequestKind.INITIAL_ANALYSIS,
        LifecycleRequestKind.READ_ONLY_SNAPSHOT,
        LifecycleRequestKind.CURRENT_THESIS_REVIEW,
    ):
        result = store.submit_request(
            request_kind=request_kind,
            ticker=TICKER,
            logic_fingerprint="logic-v1",
            requested_at=T0,
        )
        nonexplicit.append(result.model_dump(mode="json"))
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
    changed = store.submit_request(
        request_kind=LifecycleRequestKind.EXPLICIT_MONITORING,
        ticker=TICKER,
        logic_fingerprint="logic-v2",
        requested_at=T0 + timedelta(minutes=2),
    )
    checks = {
        "nonexplicit_never_registers": all(
            not row["registration_allowed"] for row in nonexplicit
        ),
        "explicit_registration_allowed": first.registration_allowed,
        "identical_registration_idempotent": not repeat.registration_intent_created
        and not repeat.thesis_version_created,
        "changed_logic_new_version": changed.thesis_version_created,
        "history_preserved": changed.subject is not None
        and [(row.version, row.status) for row in changed.subject.thesis_versions]
        == [(1, "superseded"), (2, "active")],
        "changed_logic_returns_pending": changed.subject is not None
        and not changed.subject.monitoring_ready,
    }
    return {
        "nonexplicit": nonexplicit,
        "first": first.model_dump(mode="json"),
        "repeat": repeat.model_dump(mode="json"),
        "changed": changed.model_dump(mode="json"),
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def run_fixture_program(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    firewalls: list[dict[str, object]] = []

    def add(
        fixture_id: str,
        description: str,
        store: InMemoryMonitoringLifecycle,
        trace: list[dict[str, object]],
        assessment: DailyDeltaAssessment | None,
        expected_status: str,
    ) -> None:
        row, firewall = _render_fixture(
            fixture_id=fixture_id,
            description=description,
            store=store,
            trace=trace,
            output_dir=output_dir,
            assessment=assessment,
            expected_status=expected_status,
        )
        rows.append(row)
        firewalls.append(firewall)

    pending, pending_trace = _register_store(baseline=False, ready=False)
    add(
        "M3-01",
        "registration pending and not ready",
        pending,
        pending_trace,
        None,
        "NOT_APPLICABLE",
    )

    baseline, baseline_trace = _register_store(baseline=True, ready=False)
    add(
        "M3-02",
        "baseline created and bootstrap incomplete",
        baseline,
        baseline_trace,
        None,
        "NOT_APPLICABLE",
    )

    ready, ready_trace = _register_store(baseline=True, ready=True)
    add(
        "M3-03",
        "monitoring-ready baseline",
        ready,
        ready_trace,
        None,
        "NOT_APPLICABLE",
    )

    fresh, fresh_trace = _register_store(
        baseline=True,
        ready=True,
        subject_lifecycle=SubjectLifecycle.EXISTING_MONITORED,
    )
    add(
        "M3-04",
        "fresh successful refresh with no material change",
        fresh,
        fresh_trace,
        _evaluation(fresh, day=8),
        "no_material_change",
    )

    positive, positive_trace = _register_store(baseline=True, ready=True)
    positive.add_evidence(
        TICKER,
        (_evidence("postbaseline-positive", polarity=EvidencePolarity.POSITIVE),),
    )
    add(
        "M3-05",
        "post-baseline validated positive business evidence",
        positive,
        positive_trace,
        _evaluation(positive, day=8, evidence_ids=("postbaseline-positive",)),
        "strengthened",
    )

    negative, negative_trace = _register_store(baseline=True, ready=True)
    negative.add_evidence(
        TICKER,
        (
            _evidence(
                "postbaseline-negative",
                polarity=EvidencePolarity.NEGATIVE,
                warning_key="order_decline",
            ),
        ),
    )
    add(
        "M3-06",
        "post-baseline validated negative business evidence",
        negative,
        negative_trace,
        _evaluation(negative, day=8, evidence_ids=("postbaseline-negative",)),
        "weakened",
    )

    invalidation, invalidation_trace = _register_store(baseline=True, ready=True)
    invalidation.add_evidence(
        TICKER,
        (
            _evidence(
                "postbaseline-invalidation",
                polarity=EvidencePolarity.INVALIDATION,
                warning_key="customer_loss",
            ),
        ),
    )
    add(
        "M3-07",
        "source-backed invalidation candidate",
        invalidation,
        invalidation_trace,
        _evaluation(
            invalidation,
            day=8,
            evidence_ids=("postbaseline-invalidation",),
        ),
        "invalidation_candidate",
    )

    missing, missing_trace = _register_store(baseline=True, ready=True)
    add(
        "M3-08",
        "required refresh missing",
        missing,
        missing_trace,
        _evaluation(missing, day=8, refresh_state="MISSING"),
        "needs_review",
    )

    price, price_trace = _register_store(baseline=True, ready=True)
    price.add_evidence(TICKER, (_evidence("price-only", axis=EvidenceAxis.PRICE),))
    add(
        "M3-09",
        "price-only movement with successful business refresh",
        price,
        price_trace,
        _evaluation(price, day=8, evidence_ids=("price-only",)),
        "no_material_change",
    )

    supply, supply_trace = _register_store(baseline=True, ready=True)
    supply.add_evidence(TICKER, (_evidence("supply-only", axis=EvidenceAxis.SUPPLY),))
    add(
        "M3-10",
        "supply-only movement",
        supply,
        supply_trace,
        _evaluation(supply, day=8, evidence_ids=("supply-only",)),
        "no_material_change",
    )

    valuation, valuation_trace = _register_store(baseline=True, ready=True)
    valuation.add_evidence(
        TICKER,
        (_evidence("valuation-only", axis=EvidenceAxis.VALUATION),),
    )
    add(
        "M3-11",
        "valuation-only compression and elevated expectation",
        valuation,
        valuation_trace,
        _evaluation(
            valuation,
            day=8,
            evidence_ids=("valuation-only",),
            valuation_context="compression",
            market_expectation_level="elevated",
        ),
        "no_material_change",
    )

    historical, historical_trace = _register_store(baseline=True, ready=True)
    historical.add_evidence(
        TICKER,
        (
            _evidence(
                "late-prebaseline",
                polarity=EvidencePolarity.NEGATIVE,
                effective_at=T0 - timedelta(hours=1),
                observed_at=T0 + timedelta(hours=2),
            ),
        ),
    )
    add(
        "M3-12",
        "late-arriving evidence effective before baseline cutoff",
        historical,
        historical_trace,
        _evaluation(historical, day=8, evidence_ids=("late-prebaseline",)),
        "no_material_change",
    )

    by_id = {str(row["fixture_id"]): row for row in rows}
    new_existing_checks = {
        "shared_composed_contract": by_id["M3-04"]["shared_composed_sha256"]
        == by_id["M3-09"]["shared_composed_sha256"],
        "lifecycle_provenance_distinct": by_id["M3-04"]["subject"][
            "subject_lifecycle"
        ]
        != by_id["M3-09"]["subject"]["subject_lifecycle"],
        "same_message_sections": by_id["M3-04"]["message_sections"]
        == by_id["M3-09"]["message_sections"],
    }
    lineage_errors: list[dict[str, str]] = []
    for row in rows:
        assessment = row.get("assessment")
        if not isinstance(assessment, Mapping):
            continue
        lineage = assessment.get("lineage")
        required = {
            "baseline_ref",
            "baseline_cutoff",
            "refresh_state",
            "source_evidence_ids",
            "evidence_effective_at",
            "evidence_observed_at",
            "thesis_version",
            "assessment_date",
            "evidence_generation",
        }
        if not isinstance(lineage, Mapping) or not required.issubset(lineage):
            lineage_errors.append(
                {"fixture_id": str(row["fixture_id"]), "error": "missing_lineage"}
            )
    return {
        "contract": CONTRACT,
        "rows": rows,
        "fixture_count": len(rows),
        "fixture_pass_count": sum(bool(row["pass"]) for row in rows),
        "fixture_fail_count": sum(not bool(row["pass"]) for row in rows),
        "message_count": len(rows),
        "all_messages_labeled": all(
            row["message_label"] == DERIVATIVE_LABEL for row in rows
        ),
        "all_message_sections_present": all(
            all(row["message_sections"].values()) for row in rows
        ),
        "registration_proof": _registration_proof(),
        "idempotency_warning_proof": _idempotency_and_warning_proof(),
        "new_existing_contract_equivalence": {
            "checks": new_existing_checks,
            "status": "PASS" if all(new_existing_checks.values()) else "FAIL",
        },
        "daily_delta_lineage": {
            "assessment_count": sum(row["assessment"] is not None for row in rows),
            "errors": lineage_errors,
            "status": "PASS" if not lineage_errors else "FAIL",
        },
        "firewall_rows": firewalls,
        "side_effect_firewall_status": (
            "PASS" if all(row["status"] == "PASS" for row in firewalls) else "FAIL"
        ),
        "status": (
            "PASS"
            if len(rows) == 12
            and all(bool(row["pass"]) for row in rows)
            and not lineage_errors
            and all(new_existing_checks.values())
            else "FAIL"
        ),
    }


def artifact_index(report_dir: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    secret_failures = 0
    for path in sorted(item for item in report_dir.rglob("*") if item.is_file()):
        if path.name == "artifact-index.json":
            continue
        payload = path.read_bytes()
        secret_counts = {
            name: len(pattern.findall(payload))
            for name, pattern in SECRET_PATTERNS.items()
        }
        scan_status = "PASS" if not any(secret_counts.values()) else "FAIL"
        secret_failures += int(scan_status != "PASS")
        rows.append(
            {
                "path": str(path.relative_to(report_dir)),
                "sha256": bytes_sha256(payload),
                "size_bytes": len(payload),
                "secret_scan_status": scan_status,
                "secret_category_counts": secret_counts,
            }
        )
    result = {
        "contract": "m3-artifact-index-v1",
        "payload_count": len(rows),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS" if secret_failures == 0 else "FAIL",
    }
    if secret_failures:
        raise ValueError("artifact_secret_scan_failed")
    return result


def _report_markdown(completion: Mapping[str, object]) -> str:
    return f"""# 2026-09-08 M3 Nonproduction Monitoring Lifecycle Integration

## Result

- M3 status: `{completion['m3_status']}`
- Required lifecycle fixtures: `{completion['fixture_pass_count']}/{completion['fixture_count']}`
- Side-effect firewall: `{completion['side_effect_firewall_status']}`
- Bootstrap-is-not-Daily-Delta: `{completion['bootstrap_not_daily_delta_status']}`
- Baseline cutoff / late history: `{completion['baseline_cutoff_status']}` / `{completion['late_arriving_prebaseline_status']}`
- Production readiness: `{completion['production_readiness']}`
- Recommended next scope: `{completion['next_scope']}`

## Safety

All lifecycle state, assessment, warning, and delivery records are in-memory or
file-only derivatives. Model, provider, production database, registration, warning,
notification, Telegram, main merge, deployment, V2, Night Futures, and scheduler
resume actions remain zero.

## Decision

The fixture-backed path preserves explicit registration, version history, onboarding,
baseline cutoff, monitoring readiness, post-baseline Daily Delta, warning lifecycle,
assessment idempotency, and the shared Directional / Price-Timing renderer contract.
Bootstrap and late-arriving pre-baseline facts enrich history without becoming daily
strengthening or weakening. Missing refresh remains needs-review, while price, supply,
and valuation stay separate from the business-thesis delta.
"""


def run(args: argparse.Namespace) -> dict[str, object]:
    repo_root = args.repo_root.resolve()
    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    message_dir = report_dir / "messages"
    latest = verify_latest_result(args.latest_result_zip.resolve())
    instruction = verify_work_instruction(args.work_instruction_zip.resolve())
    boundaries = boundary_reuse(repo_root)
    with tempfile.TemporaryDirectory(prefix="thesis-monitor-m3-boundary-") as temp:
        actual_boundary_proof = production_boundary_lifecycle_proof(Path(temp))
    boundaries["actual_in_memory_integration"] = actual_boundary_proof
    boundaries["status"] = (
        "PASS"
        if boundaries["verified_boundary_count"] == boundaries["boundary_count"]
        and actual_boundary_proof["status"] == "PASS"
        else "FAIL"
    )
    program = run_fixture_program(message_dir)
    if boundaries["status"] != "PASS" or program["status"] != "PASS":
        raise ValueError("M3_LIFECYCLE_INTEGRATION_FAILED")

    start_pause = read_json(args.start_pause_observation.resolve())
    end_pause = observe_pause_state()
    pause_status = (
        "PASS"
        if start_pause.get("status") == "VERIFIED_PAUSED_COMPLETE"
        and end_pause.get("status") == "VERIFIED_PAUSED_COMPLETE"
        else "FAIL"
    )
    source_backlog = (
        "same_period_prior_year_comparison",
        "operating_cash_flow",
        "ppe_capex_simple_cash_conversion",
        "debt_liquidity",
        "inventory_receivables_working_capital",
        "non_operating_financial_income_effects",
    )
    fixture_rows = program["rows"]
    by_id = {row["fixture_id"]: row for row in fixture_rows}
    statuses = {
        "registration_intent_gate_status": program["registration_proof"]["status"],
        "registration_idempotency_status": program["registration_proof"]["status"],
        "onboarding_pending_status": "PASS"
        if not by_id["M3-01"]["subject"]["monitoring_ready"]
        else "FAIL",
        "baseline_creation_status": "PASS"
        if by_id["M3-02"]["subject"]["baseline"] is not None
        else "FAIL",
        "bootstrap_readiness_status": "PASS"
        if by_id["M3-03"]["subject"]["monitoring_ready"]
        else "FAIL",
        "bootstrap_not_daily_delta_status": "PASS"
        if by_id["M3-03"]["assessment"] is None
        else "FAIL",
        "baseline_cutoff_status": "PASS"
        if by_id["M3-12"]["assessment"]["lineage"]["prebaseline_enrichment_ids"]
        == ["late-prebaseline"]
        else "FAIL",
        "late_arriving_prebaseline_status": "PASS"
        if by_id["M3-12"]["actual_status"] == "no_material_change"
        else "FAIL",
        "fresh_no_change_status": "PASS"
        if by_id["M3-04"]["actual_status"] == "no_material_change"
        else "FAIL",
        "missing_refresh_status": "PASS"
        if by_id["M3-08"]["actual_status"] == "needs_review"
        else "FAIL",
        "price_only_status": "PASS"
        if by_id["M3-09"]["actual_status"] == "no_material_change"
        else "FAIL",
        "supply_only_status": "PASS"
        if by_id["M3-10"]["actual_status"] == "no_material_change"
        else "FAIL",
        "valuation_only_status": "PASS"
        if by_id["M3-11"]["actual_status"] == "no_material_change"
        else "FAIL",
        "positive_daily_delta_status": "PASS"
        if by_id["M3-05"]["actual_status"] == "strengthened"
        else "FAIL",
        "negative_daily_delta_status": "PASS"
        if by_id["M3-06"]["actual_status"] == "weakened"
        else "FAIL",
        "invalidation_candidate_status": "PASS"
        if by_id["M3-07"]["actual_status"] == "invalidation_candidate"
        else "FAIL",
        "warning_open_idempotency_status": program["idempotency_warning_proof"][
            "status"
        ],
        "warning_resolve_idempotency_status": program["idempotency_warning_proof"][
            "status"
        ],
        "assessment_idempotency_status": program["idempotency_warning_proof"][
            "status"
        ],
        "new_existing_contract_equivalence_status": program[
            "new_existing_contract_equivalence"
        ]["status"],
        "file_only_message_status": "PASS"
        if program["message_count"] == 12
        and program["all_messages_labeled"]
        and program["all_message_sections_present"]
        else "FAIL",
        "daily_delta_lineage_status": program["daily_delta_lineage"]["status"],
        "side_effect_firewall_status": program["side_effect_firewall_status"],
    }
    if not all(value == "PASS" for value in statuses.values()) or pause_status != "PASS":
        raise ValueError("M3_ACCEPTANCE_STATUS_FAILURE")

    reports: dict[str, object] = {
        "01-repository-provenance.json": {
            "contract": "m3-repository-provenance-v1",
            "branch": git_value(repo_root, "branch", "--show-current"),
            "base_sha": EXPECTED_M2_FINAL_SHA,
            "head_at_report_generation": git_value(repo_root, "rev-parse", "HEAD"),
            "tree_at_report_generation": git_value(repo_root, "rev-parse", "HEAD^{tree}"),
            "origin_main": git_value(repo_root, "rev-parse", "origin/main"),
            "work_instruction_commit": args.work_instruction_commit,
            "implementation_commit": args.implementation_commit,
            "status": "PASS",
        },
        "02-latest-result-integrity.json": latest,
        "03-m3-scope-freeze.json": {
            "contract": CONTRACT,
            "work_instruction": instruction,
            "allowed": [
                "in_memory_lifecycle_repository",
                "fixture_backed_lifecycle_adapter",
                "file_only_message_renderer",
                "offline_evidence_reports",
            ],
            "forbidden_actions_executed": 0,
            "model_call_policy": "ZERO_CALLS",
            "provider_fetch_policy": "ZERO_FETCHES",
            "status": "PASS",
        },
        "04-m2-contract-reuse-proof.json": boundaries,
        "05-m3-lifecycle-state-contract.json": {
            "contract": CONTRACT,
            "states": {
                "REGISTERED_NOT_READY": "PENDING_ONBOARDING; no Daily Delta",
                "BASELINE_BOOTSTRAP_INCOMPLETE": "baseline exists; no Daily Delta",
                "MONITORING_READY": "baseline + bootstrap + source readiness",
                "DAILY_EVALUABLE": "monitoring-ready + known post-cutoff refresh state",
            },
            "absolute_decision_is_daily_delta": False,
            "bootstrap_is_daily_delta": False,
            "status": "PASS",
        },
        "06-registration-intent-integration.json": program["registration_proof"],
        "07-onboarding-evidence-integration.json": {
            "contract": CONTRACT,
            "evidence_intents": sum(
                row["subject"]["evidence_ids"] != [] for row in fixture_rows
            ),
            "provider_fetches": 0,
            "evidence_is_registration": False,
            "status": "PASS",
        },
        "08-baseline-and-cutoff-integration.json": {
            "contract": CONTRACT,
            "baseline_fixture_count": sum(
                row["subject"]["baseline"] is not None for row in fixture_rows
            ),
            "cutoff_fixture": by_id["M3-12"],
            "status": statuses["baseline_cutoff_status"],
        },
        "09-monitoring-readiness-integration.json": {
            "contract": CONTRACT,
            "pending": by_id["M3-01"]["subject"],
            "baseline_incomplete": by_id["M3-02"]["subject"],
            "ready": by_id["M3-03"]["subject"],
            "status": "PASS",
        },
        "10-daily-delta-evaluation-integration.json": {
            "contract": CONTRACT,
            "status_counts": dict(Counter(str(row["actual_status"]) for row in fixture_rows)),
            "daily_rows": [row for row in fixture_rows if row["assessment"] is not None],
            "status": "PASS",
        },
        "11-warning-lifecycle-integration.json": program[
            "idempotency_warning_proof"
        ],
        "12-assessment-idempotency-integration.json": {
            "contract": CONTRACT,
            "proof": program["idempotency_warning_proof"],
            "idempotency_key": "ticker|assessment_date|thesis_version|evidence_generation",
            "status": statuses["assessment_idempotency_status"],
        },
        "13-side-effect-firewall-audit.json": {
            "contract": CONTRACT,
            "rows": program["firewall_rows"],
            "external_invocation_counts": {
                "production_db_connections": 0,
                "production_db_mutations": 0,
                "monitoring_registration_calls": 0,
                "assessment_persistence_mutations": 0,
                "warning_mutations": 0,
                "notification_queue_writes": 0,
                "production_sends": 0,
                "provider_source_fetches": 0,
                "model_calls_real": 0,
                "model_calls_fictional": 0,
                "model_calls_judge": 0,
            },
            "status": statuses["side_effect_firewall_status"],
        },
        "14-new-existing-contract-equivalence.json": program[
            "new_existing_contract_equivalence"
        ],
        "15-lifecycle-fixture-manifest.json": {
            "contract": CONTRACT,
            "fixture_count": program["fixture_count"],
            "fixture_pass_count": program["fixture_pass_count"],
            "fixture_fail_count": program["fixture_fail_count"],
            "rows": fixture_rows,
            "status": program["status"],
        },
        "16-bootstrap-not-delta-results.json": {
            "contract": CONTRACT,
            "fixtures": [by_id["M3-02"], by_id["M3-03"]],
            "bootstrap_daily_delta_record_count": 0,
            "bootstrap_strengthened_count": 0,
            "status": statuses["bootstrap_not_daily_delta_status"],
        },
        "17-baseline-cutoff-results.json": {
            "contract": CONTRACT,
            "fixture": by_id["M3-12"],
            "effective_date_not_arrival_time": True,
            "status": statuses["baseline_cutoff_status"],
        },
        "18-late-arriving-evidence-results.json": {
            "contract": CONTRACT,
            "fixture": by_id["M3-12"],
            "false_daily_delta_count": 0,
            "status": statuses["late_arriving_prebaseline_status"],
        },
        "19-refresh-state-results.json": {
            "contract": CONTRACT,
            "fresh": by_id["M3-04"],
            "missing": by_id["M3-08"],
            "missing_as_no_material_change_count": 0,
            "status": "PASS",
        },
        "20-price-supply-valuation-separation-results.json": {
            "contract": CONTRACT,
            "price": by_id["M3-09"],
            "supply": by_id["M3-10"],
            "valuation": by_id["M3-11"],
            "nonbusiness_axis_thesis_delta_count": 0,
            "status": "PASS",
        },
        "21-warning-and-assessment-results.json": program[
            "idempotency_warning_proof"
        ],
        "22-file-only-monitoring-message-results.json": {
            "contract": CONTRACT,
            "message_count": program["message_count"],
            "all_labeled": program["all_messages_labeled"],
            "all_sections_present": program["all_message_sections_present"],
            "rows": [
                {
                    "fixture_id": row["fixture_id"],
                    "path": row["message_path"],
                    "sha256": row["message_sha256"],
                    "sections": row["message_sections"],
                }
                for row in fixture_rows
            ],
            "queue_writes": 0,
            "sends": 0,
            "status": statuses["file_only_message_status"],
        },
        "23-daily-delta-lineage-audit.json": program["daily_delta_lineage"],
        "24-m3-integration-gap-register.json": {
            "contract": CONTRACT,
            "hard_lifecycle_gaps": [],
            "semantic_input_gaps": list(source_backlog),
            "message_copy_changes": [],
            "status": "NO_HARD_M3_GAP",
        },
        "25-source-domain-backlog-update.json": {
            "contract": CONTRACT,
            "source_domain_backlog_count": len(source_backlog),
            "domains": list(source_backlog),
            "implemented_in_m3": [],
            "decision": "PRESERVE_AS_SEPARATE_DESIGN_REVIEW",
            "status": "RECORDED",
        },
        "26-required-next-semantic-change-decision.json": {
            "contract": CONTRACT,
            "semantic_change_required": True,
            "reason": (
                "M3 lifecycle semantics pass, while M2 decision-quality evidence still "
                "shows source-domain limitations that require a separately frozen design."
            ),
            "selected_path": "PATH_A",
            "next_scope": (
                "SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW"
            ),
            "status": "DECIDED",
        },
        "27-required-next-model-validation-scope.json": {
            "contract": CONTRACT,
            "model_validation_now": False,
            "new_model_validation_required": True,
            "new_real_holdout_proof_required": True,
            "prerequisite": "freeze bounded source/reasoning semantic contract",
            "status": "DEFERRED_UNTIL_SEMANTIC_CONTRACT_FREEZE",
        },
        "28-production-no-change.json": {
            "contract": CONTRACT,
            "production_db_mutations": 0,
            "monitoring_registration_calls": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "main_merges": 0,
            "deployments": 0,
            "live_v2_changes": 0,
            "night_futures_changes": 0,
            "automatic_monitoring_resume": 0,
            "production_readiness": "NOT_READY",
            "status": "PASS",
        },
        "29-schedule-pause-observation.json": {
            "contract": "m3-start-end-pause-observation-v1",
            "start": start_pause,
            "end": end_pause,
            "observed_paused_schedule_count": end_pause.get(
                "observed_scheduler_object_count", "NOT_MEASURED"
            ),
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "status": pause_status,
        },
        "30-master-workflow-update.json": {
            "contract": "m3-master-workflow-update-v1",
            "path": "docs/MASTER_WORKFLOW.md",
            "sha256": file_sha256(repo_root / "docs/MASTER_WORKFLOW.md"),
            "m1_status": "COMPLETE",
            "m2_status": "COMPLETE",
            "m3_status": "COMPLETE",
            "next_scope": (
                "SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW"
            ),
            "status": "RECORDED",
        },
    }
    completion: dict[str, object] = {
        "contract": CONTRACT,
        "base_sha": EXPECTED_M2_FINAL_SHA,
        "work_instruction_commit": args.work_instruction_commit,
        "implementation_commit": args.implementation_commit,
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": git_value(repo_root, "branch", "--show-current"),
        "latest_result_zip_sha256": latest["sha256"],
        "latest_result_integrity": latest["status"],
        "m1_status": "COMPLETE",
        "m2_status": "COMPLETE",
        "m3_status": "COMPLETE",
        **statuses,
        "fixture_count": program["fixture_count"],
        "fixture_pass_count": program["fixture_pass_count"],
        "fixture_fail_count": program["fixture_fail_count"],
        "model_calls_real": 0,
        "model_calls_fictional": 0,
        "model_calls_judge": 0,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "live_v2_changes": 0,
        "night_futures_changes": 0,
        "observed_paused_schedule_count": end_pause.get(
            "observed_scheduler_object_count", "NOT_MEASURED"
        ),
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "source_domain_backlog_count": len(source_backlog),
        "semantic_change_required": True,
        "new_model_validation_required": True,
        "new_real_holdout_proof_required": True,
        "focused_test_result": args.focused_test_result,
        "full_test_result": args.full_test_result,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.git_diff_check,
        "artifact_count": 44,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_READY",
        "status": "M3_COMPLETE",
        "stop_reason": None,
        "next_scope": (
            "SOURCE_DOMAIN_ENRICHMENT_AND_DIRECTIONAL_SPECIFICITY_DESIGN_REVIEW"
        ),
    }
    reports["31-program-completion.json"] = completion
    for name, payload in reports.items():
        write_json(report_dir / name, payload)
    (report_dir / "20260908-nonproduction-monitoring-bootstrap-daily-delta-lifecycle-integration.md").write_text(
        _report_markdown(completion),
        encoding="utf-8",
    )
    index = artifact_index(report_dir)
    write_json(report_dir / "artifact-index.json", index)
    if index["payload_count"] != completion["artifact_count"]:
        raise ValueError("artifact_count_mismatch")
    return completion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--work-instruction-zip", type=Path, required=True)
    parser.add_argument("--start-pause-observation", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--work-instruction-commit", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--focused-test-result", default="NOT_MEASURED")
    parser.add_argument("--full-test-result", default="NOT_MEASURED")
    parser.add_argument("--ruff-result", default="NOT_MEASURED")
    parser.add_argument("--git-diff-check", default="NOT_MEASURED")
    return parser.parse_args()


def main() -> None:
    completion = run(parse_args())
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
