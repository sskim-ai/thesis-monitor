import asyncio
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.company import Company
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services import onboarding_decision_service
from app.services.company_profile_service import profile_provenance_path
from app.services.onboarding_decision_service import (
    build_onboarding_decision_evidence_packet,
    validate_onboarding_decision_readiness,
)
from app.services.cross_market_decision_engine_service import EvidenceCategory
from app.services.onboarding_evidence_service import initial_evidence_fingerprint
from app.services.onboarding_readiness_service import (
    OnboardingState,
    production_universe_snapshot,
)
from app.services.onboarding_reconciler_service import (
    OnboardingAttemptMode,
    OnboardingRetryClass,
    reconcile_pending_onboarding,
    market_preflight_onboarding_resume,
    resume_onboarding_subject,
)
from app.services.security_master_service import SecurityMasterService


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _write_profile(data_dir: Path, ticker: str) -> None:
    path = profile_provenance_path(ticker, data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "ticker": ticker,
                "market": "kr" if ticker.isdigit() else "us",
                "quality": "verified",
                "source": "official_test_fixture",
            }
        ),
        encoding="utf-8",
    )


def _seed_pending(
    session: Session,
    data_dir: Path,
    *,
    ticker: str,
    exchange: str,
) -> WatchlistItem:
    item = WatchlistItem(
        ticker=ticker,
        company_name=f"{ticker} Test Company",
        exchange=exchange,
        active=False,
        monitoring_requested=True,
        onboarding_state=OnboardingState.PENDING_ONBOARDING,
        production_eligible=False,
        registration_requested_at=datetime(2026, 8, 31, 0, tzinfo=UTC),
    )
    session.add(item)
    session.add(
        Company(
            ticker=ticker,
            company_name=item.company_name,
            exchange=exchange,
            industry="Industrials",
            sector="Industrials",
            business_units='["core"]',
            revenue_sources='["customers"]',
        )
    )
    session.add(
        InvestmentThesis(
            ticker=ticker,
            version=1,
            core_thesis="Verified demand supports the operating thesis.",
            time_horizon="6-24개월",
            thesis_drivers='["verified demand"]',
            validation_metrics='["revenue", "margin"]',
            market_expectations='{"level":"balanced"}',
            valuation_framework='{"primary_method":"forward earnings"}',
            strengthen_signals='["margin expansion"]',
            weaken_signals='["order decline"]',
            invalidation_signals='["customer loss"]',
            status="active",
        )
    )
    session.add(
        ThesisAssessment(
            ticker=ticker,
            thesis_version=1,
            assessment_date=date(2026, 8, 31),
            status="no_material_change",
            summary="Final initial baseline retained for reconciliation.",
            new_buyer_view="Wait for the next operating confirmation.",
            holder_view="Monitor current validation metrics.",
            price_view="Use the canonical price context.",
            risk_level="normal",
            confidence=0.7,
            assessment_state="final",
            thesis_snapshot=json.dumps(
                {
                    "assessment_mode": "initial_baseline",
                    "base_thesis": "verified",
                    "thesis_version": 1,
                    "effective_date": "2026-08-31",
                    "status": "no_material_change",
                    "current_thesis": "verified",
                }
            ),
        )
    )
    session.commit()
    SecurityMasterService().ensure(session, ticker)
    session.commit()
    _write_profile(data_dir, ticker)
    return item


def _evidence(ticker: str) -> dict[str, object]:
    value: dict[str, object] = {
        "contract": "initial-onboarding-evidence-v1",
        "ticker": ticker,
        "market": "kr" if ticker.isdigit() else "us",
        "thesis_version": 1,
        "as_of": "2026-08-31T01:00:00+00:00",
        "current_thesis": {"core_thesis": "verified demand"},
        "latest_safe_earnings_checkpoint": {"status": "AVAILABLE"},
        "market_expectations": {"level": "balanced"},
        "relevant_events": [],
        "valuation_context": {"provider": "official_test_fixture"},
        "current_price": 100,
        "price_as_of": "2026-08-31",
        "price_currency": "KRW" if ticker.isdigit() else "USD",
        "ohlcv_feature_availability": {
            period: {
                "available": True,
                "actual_count": 100,
                "latest_date": "2026-08-31",
            }
            for period in ("daily", "weekly", "monthly")
        },
        "price_structure": {
            "available": True,
            "timeframes": ["daily", "weekly", "monthly"],
        },
        "material_market_context": {"status": "AVAILABLE"},
        "material_unknowns": ["next earnings confirmation"],
    }
    value["fingerprint"] = initial_evidence_fingerprint(value)
    return value


async def _evidence_builder(
    _session: Session,
    item: WatchlistItem,
    **_kwargs: object,
) -> dict[str, object]:
    return _evidence(item.ticker)


def _decision_builder(
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
        "decision_evidence_sha256": f"decision-evidence:{item.ticker}",
        "accepted_decision": "HOLD",
        "accepted_decision_id": f"accepted:{item.ticker}",
        "accepted_evidence_fingerprint": f"accepted-evidence:{item.ticker}",
        "raw_candidate_grants_ready": False,
    }


def test_generic_kr_and_us_pending_registration_auto_complete(tmp_path: Path) -> None:
    engine = _engine()
    with Session(engine) as session:
        _seed_pending(session, tmp_path, ticker="111111", exchange="KRX")
        _seed_pending(session, tmp_path, ticker="AUTOUSE", exchange="NASDAQ")
        run = asyncio.run(
            reconcile_pending_onboarding(
                session,
                market="all",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 1, tzinfo=UTC),
                force_due=True,
                first_eligible_session=date(2026, 9, 1),
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
            )
        )
        rows = session.exec(select(WatchlistItem).order_by(WatchlistItem.ticker)).all()

    assert run.attempted_this_run == 2
    assert run.completed_this_run == 2
    assert all(row.active and row.production_eligible for row in rows)
    assert all(row.onboarding_state == OnboardingState.ACTIVE for row in rows)
    assert all(row.first_eligible_session == date(2026, 9, 1) for row in rows)


def test_subject_failure_isolated_and_retryable(tmp_path: Path) -> None:
    engine = _engine()

    async def one_fails(
        _session: Session,
        item: WatchlistItem,
        **_kwargs: object,
    ) -> dict[str, object]:
        if item.ticker == "AAAFAIL":
            raise TimeoutError("temporary provider timeout")
        return _evidence(item.ticker)

    with Session(engine) as session:
        failed = _seed_pending(session, tmp_path, ticker="AAAFAIL", exchange="NASDAQ")
        completed = _seed_pending(session, tmp_path, ticker="ZZZPASS", exchange="NYSE")
        run = asyncio.run(
            reconcile_pending_onboarding(
                session,
                market="us",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 1, tzinfo=UTC),
                force_due=True,
                data_dir=tmp_path,
                evidence_builder=one_fails,
                decision_builder=_decision_builder,
            )
        )
        session.refresh(failed)
        session.refresh(completed)

    assert run.attempted_this_run == 2
    assert failed.active is False
    assert failed.onboarding_retry_class == OnboardingRetryClass.RETRYABLE
    assert failed.onboarding_next_retry_at is not None
    assert completed.active is True


def test_profile_temporary_failure_retries_then_completes(tmp_path: Path) -> None:
    engine = _engine()
    attempts = 0

    async def profile_retry(
        _session: Session,
        item: WatchlistItem,
        **_kwargs: object,
    ) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("temporary profile provider failure")
        _write_profile(tmp_path, item.ticker)

    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker="PROFILE", exchange="NASDAQ")
        profile_provenance_path(item.ticker, tmp_path).unlink()
        first = asyncio.run(
            reconcile_pending_onboarding(
                session,
                market="us",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 1, tzinfo=UTC),
                force_due=True,
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
                profile_populator=profile_retry,
            )
        )
        second = asyncio.run(
            reconcile_pending_onboarding(
                session,
                market="us",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 2, tzinfo=UTC),
                force_due=True,
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
                profile_populator=profile_retry,
            )
        )
        session.refresh(item)

    assert first.completed_this_run == 0
    assert second.completed_this_run == 1
    assert attempts == 2
    assert item.active is True


def test_assessment_failure_retries_without_losing_evidence(tmp_path: Path) -> None:
    engine = _engine()
    attempts = 0

    def baseline_retry(
        session: Session,
        item: WatchlistItem,
        _evidence_value: dict[str, object],
        **_kwargs: object,
    ) -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("temporary baseline assessment failure")
        row = ThesisAssessment(
            ticker=item.ticker,
            thesis_version=1,
            assessment_date=date(2026, 8, 31),
            status="no_material_change",
            summary="Retried initial baseline.",
            new_buyer_view="Wait for evidence.",
            holder_view="Monitor evidence.",
            price_view="Use canonical price evidence.",
            risk_level="normal",
            confidence=0.7,
            assessment_state="final",
            thesis_snapshot=json.dumps(
                {
                    "assessment_mode": "initial_baseline",
                    "thesis_version": 1,
                    "base_thesis": "verified",
                }
            ),
        )
        session.add(row)
        session.flush()
        return row

    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker="ASSESS", exchange="NYSE")
        baseline = session.exec(
            select(ThesisAssessment).where(ThesisAssessment.ticker == item.ticker)
        ).one()
        session.delete(baseline)
        session.commit()
        first = asyncio.run(
            reconcile_pending_onboarding(
                session,
                market="us",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 1, tzinfo=UTC),
                force_due=True,
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
                baseline_builder=baseline_retry,
            )
        )
        fingerprint_after_failure = item.onboarding_evidence_fingerprint
        second = asyncio.run(
            reconcile_pending_onboarding(
                session,
                market="us",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 2, tzinfo=UTC),
                force_due=True,
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
                baseline_builder=baseline_retry,
            )
        )
        session.refresh(item)

    assert first.completed_this_run == 0
    assert second.completed_this_run == 1
    assert fingerprint_after_failure == item.onboarding_evidence_fingerprint
    assert attempts == 2
    assert item.active is True


def test_review_required_does_not_retry_forever(tmp_path: Path) -> None:
    engine = _engine()

    async def conflict(
        _session: Session,
        _item: WatchlistItem,
        **_kwargs: object,
    ) -> dict[str, object]:
        raise ValueError("security_conflict:canonical identity mismatch")

    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker="CONFLICT", exchange="NASDAQ")
        asyncio.run(
            resume_onboarding_subject(
                session,
                item,
                origin="test",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=datetime(2026, 8, 31, 1, tzinfo=UTC),
                data_dir=tmp_path,
                evidence_builder=conflict,
                decision_builder=_decision_builder,
            )
        )
        session.refresh(item)

    assert item.active is False
    assert item.onboarding_state == OnboardingState.ONBOARDING_FAILED
    assert item.onboarding_retry_class == OnboardingRetryClass.REVIEW_REQUIRED
    assert item.onboarding_next_retry_at is None


def test_cross_market_and_same_market_pending_isolation(tmp_path: Path) -> None:
    engine = _engine()
    cutoff = datetime(2026, 8, 31, 7, tzinfo=UTC)
    with Session(engine) as session:
        kr_ready = _seed_pending(session, tmp_path, ticker="222222", exchange="KRX")
        asyncio.run(
            resume_onboarding_subject(
                session,
                kr_ready,
                origin="test",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=cutoff - timedelta(minutes=5),
                first_eligible_session=date(2026, 8, 31),
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
            )
        )
        us_ready = _seed_pending(session, tmp_path, ticker="USREADY", exchange="NASDAQ")
        asyncio.run(
            resume_onboarding_subject(
                session,
                us_ready,
                origin="test",
                mode=OnboardingAttemptMode.BACKGROUND,
                as_of=cutoff - timedelta(minutes=5),
                first_eligible_session=date(2026, 8, 31),
                data_dir=tmp_path,
                evidence_builder=_evidence_builder,
                decision_builder=_decision_builder,
            )
        )
        _seed_pending(session, tmp_path, ticker="USPENDING", exchange="NYSE")
        _seed_pending(session, tmp_path, ticker="333333", exchange="KRX")
        kr_snapshot = production_universe_snapshot(
            session, "kr", cutoff=cutoff, session_key="daily_kr"
        )
        us_snapshot = production_universe_snapshot(
            session, "us", cutoff=cutoff, session_key="daily_us"
        )

    assert [row.ticker for row in kr_snapshot.eligible_items] == ["222222"]
    assert [row.ticker for row in us_snapshot.eligible_items] == ["USREADY"]
    assert {row["ticker"] for row in kr_snapshot.excluded_subjects} == {"333333"}
    assert {row["ticker"] for row in us_snapshot.excluded_subjects} == {"USPENDING"}


def test_cutoff_and_first_eligible_session_are_fail_closed(tmp_path: Path) -> None:
    engine = _engine()
    cutoff = datetime(2026, 8, 31, 7, tzinfo=UTC)
    with Session(engine) as session:
        current = _seed_pending(session, tmp_path, ticker="CURRENT", exchange="NASDAQ")
        future = _seed_pending(session, tmp_path, ticker="FUTURE", exchange="NYSE")
        for item, first_session in (
            (current, date(2026, 8, 31)),
            (future, date(2026, 9, 1)),
        ):
            asyncio.run(
                resume_onboarding_subject(
                    session,
                    item,
                    origin="market_preflight_us",
                    mode=OnboardingAttemptMode.BACKGROUND,
                    as_of=cutoff - timedelta(minutes=1),
                    first_eligible_session=first_session,
                    market_packet_cutoff=cutoff,
                    data_dir=tmp_path,
                    evidence_builder=_evidence_builder,
                    decision_builder=_decision_builder,
                )
            )
        snapshot = production_universe_snapshot(
            session, "us", cutoff=cutoff, session_key="daily_us"
        )

    assert [row.ticker for row in snapshot.eligible_items] == ["CURRENT"]
    assert any(
        row["ticker"] == "FUTURE"
        and "first_eligible_session_not_reached" in row["reasons"]
        for row in snapshot.excluded_subjects
    )


def test_market_preflight_activates_only_persisted_ready_subject(tmp_path: Path) -> None:
    engine = _engine()
    cutoff = datetime(2026, 8, 31, 7, tzinfo=UTC)
    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker="PREFLIGHT", exchange="NASDAQ")
        evidence = _evidence(item.ticker)
        item.onboarding_initial_evidence = json.dumps(evidence)
        item.onboarding_evidence_fingerprint = str(evidence["fingerprint"])
        item.onboarding_decision_readiness = json.dumps(
            _decision_builder(session, item, evidence)
        )
        session.add(item)
        session.commit()
        result = asyncio.run(
            market_preflight_onboarding_resume(
                session,
                market="us",
                run_date=date(2026, 8, 31),
                cutoff=cutoff,
                current_cycle_eligible=True,
                data_dir=tmp_path,
            )
        )
        session.refresh(item)
        repeat = asyncio.run(
            market_preflight_onboarding_resume(
                session,
                market="us",
                run_date=date(2026, 8, 31),
                cutoff=cutoff + timedelta(minutes=5),
                current_cycle_eligible=True,
                data_dir=tmp_path,
            )
        )

    assert result["attempted_this_run"] == 1
    assert result["completed_this_run"] == 1
    assert item.active is True
    assert item.first_eligible_session == date(2026, 8, 31)
    assert repeat["attempted_this_run"] == 0


def test_raw_candidate_cannot_satisfy_decision_readiness() -> None:
    valid, reason = validate_onboarding_decision_readiness(
        {
            "contract": "onboarding-accepted-decision-v1",
            "status": "READY",
            "ticker": "RAW",
            "source_initial_evidence_fingerprint": "evidence",
            "accepted_decision": "HOLD",
            "accepted_decision_id": "accepted",
            "accepted_evidence_fingerprint": "accepted-evidence",
            "raw_candidate_grants_ready": True,
        },
        ticker="RAW",
        initial_evidence_fingerprint="evidence",
    )

    assert valid is False
    assert reason == "raw_candidate_grants_ready"


def test_decision_packet_binds_market_expectations_to_expected_category(
    tmp_path: Path,
) -> None:
    engine = _engine()
    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker="EXPECT", exchange="NASDAQ")
        packet = build_onboarding_decision_evidence_packet(
            session, item, _evidence(item.ticker)
        )

    expectation_refs = [
        ref for ref in packet.evidence if ref.category == EvidenceCategory.EXPECTATIONS
    ]
    assert len(expectation_refs) == 1
    assert expectation_refs[0].label == "market_expectations"


def test_signed_in_codex_uses_absolute_artifact_paths(
    tmp_path: Path, monkeypatch
) -> None:
    artifact_dir = tmp_path / "data" / "onboarding" / "TEST"
    artifact_dir.mkdir(parents=True)
    prompt = artifact_dir / "prompt.txt"
    output = artifact_dir / "output.json"
    log = artifact_dir / "cli.log"
    schema = artifact_dir / "schema.json"
    prompt.write_text("prompt\n", encoding="utf-8")
    schema.write_text("{}\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        Path(command[command.index("-o") + 1]).write_text("{}\n", encoding="utf-8")
        return type("Result", (), {"returncode": 0})()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        onboarding_decision_service, "_signed_in_codex_bin", lambda: "/tmp/codex"
    )
    monkeypatch.setattr(onboarding_decision_service.subprocess, "run", fake_run)

    onboarding_decision_service._invoke_signed_in_codex(
        prompt=prompt.relative_to(tmp_path),
        output=output.relative_to(tmp_path),
        log=log.relative_to(tmp_path),
        schema=schema.relative_to(tmp_path),
        timeout=30,
    )

    command = captured["command"]
    assert isinstance(command, list)
    schema_arg = Path(command[command.index("--output-schema") + 1])
    output_arg = Path(command[command.index("-o") + 1])
    assert schema_arg.is_absolute() and schema_arg == schema
    assert output_arg.is_absolute() and output_arg == output
    assert captured["cwd"] == artifact_dir
