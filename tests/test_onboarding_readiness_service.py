import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.company import Company
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import MonitoringItemCreate
from app.services.company_profile_service import profile_provenance_path
from app.services.monitoring_service import register_monitoring_item
from app.services.onboarding_readiness_service import (
    OnboardingState,
    begin_onboarding,
    evaluate_onboarding_readiness,
    production_universe_snapshot,
    reconcile_onboarding,
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


def _write_profile(data_dir: Path, ticker: str, market: str) -> None:
    path = profile_provenance_path(ticker, data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "ticker": ticker,
                "market": market,
                "quality": "verified",
                "source": "official_test_fixture",
                "industry": "Industrials",
                "sector": "Industrials",
            }
        ),
        encoding="utf-8",
    )


def _seed_ready_prerequisites(
    session: Session,
    data_dir: Path,
    *,
    ticker: str,
    exchange: str,
    company_name: str,
) -> WatchlistItem:
    item = WatchlistItem(
        ticker=ticker,
        company_name=company_name,
        exchange=exchange,
        active=False,
        monitoring_requested=True,
        onboarding_state=OnboardingState.PENDING_ONBOARDING,
        production_eligible=False,
    )
    begin_onboarding(item, requested_at=datetime(2026, 8, 31, 1, tzinfo=UTC))
    session.add(item)
    session.add(
        Company(
            ticker=ticker,
            company_name=company_name,
            exchange=exchange,
            industry="Aerospace Manufacturing",
            sector="Industrials",
            business_units='["core business"]',
            revenue_sources='["customer contracts"]',
        )
    )
    session.add(
        InvestmentThesis(
            ticker=ticker,
            version=1,
            core_thesis="Verified operating evidence supports the monitored thesis.",
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
            summary="Initial evidence baseline is established.",
            new_buyer_view="Wait for the next operating confirmation.",
            holder_view="Monitor the validation metrics.",
            price_view="Price evidence is available without an order instruction.",
            risk_level="normal",
            confidence=0.7,
            assessment_state="final",
            price_context='{"decision":{"current_price":100}}',
            valuation_snapshot='{"method":"forward earnings"}',
            thesis_snapshot=(
                '{"assessment_mode":"initial_baseline","base_thesis":"verified",'
                '"thesis_version":1,"effective_date":"2026-08-31",'
                '"status":"no_material_change","current_thesis":"verified"}'
            ),
        )
    )
    session.commit()
    SecurityMasterService().ensure(session, ticker)
    session.commit()
    _write_profile(data_dir, ticker, "kr" if ticker.isdigit() else "us")
    return item


def test_registration_is_pending_and_idempotent_until_prerequisites_pass() -> None:
    engine = _engine()
    payload = MonitoringItemCreate(
        ticker="NEW1",
        company_name="New Subject",
        exchange="NASDAQ",
        core_thesis="A complete onboarding must precede production eligibility.",
        thesis_drivers=["verified demand"],
        validation_metrics=["revenue"],
        market_expectations={"level": "balanced"},
        valuation_framework={"primary_method": "forward earnings"},
        strengthen_signals=["margin expansion"],
        weaken_signals=["order decline"],
        invalidation_signals=["customer loss"],
    )
    with Session(engine) as session:
        first = register_monitoring_item(session, payload)
        second = register_monitoring_item(session, payload)
        rows = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == "NEW1")
        ).all()

    assert first.onboarding_state == OnboardingState.PENDING_ONBOARDING
    assert first.active is False
    assert first.production_eligible is False
    assert second.thesis is not None and second.thesis.version == 1
    assert len(rows) == 1


def test_complete_prerequisites_transition_pending_ready_active(tmp_path: Path) -> None:
    engine = _engine()
    with Session(engine) as session:
        item = _seed_ready_prerequisites(
            session,
            tmp_path,
            ticker="047810",
            exchange="KRX",
            company_name="Korea Aerospace Industries",
        )
        readiness = reconcile_onboarding(
            session,
            item,
            data_dir=tmp_path,
            as_of=datetime(2026, 8, 31, 7, tzinfo=UTC),
            first_eligible_session=date(2026, 9, 1),
        )
        session.commit()
        state = item.onboarding_state
        active = item.active
        production_eligible = item.production_eligible
        first_session = item.first_eligible_session

    assert readiness.onboarding_ready is True
    assert readiness.blocking_requirements == ()
    assert state == OnboardingState.ACTIVE
    assert active is True
    assert production_eligible is True
    assert first_session == date(2026, 9, 1)


def test_placeholder_profile_does_not_activate(tmp_path: Path) -> None:
    engine = _engine()
    with Session(engine) as session:
        item = _seed_ready_prerequisites(
            session,
            tmp_path,
            ticker="CPNG",
            exchange="NYSE",
            company_name="Coupang",
        )
        profile_provenance_path("CPNG", tmp_path).write_text(
            json.dumps(
                {
                    "quality": "unavailable",
                    "reason": "official_profile_unavailable",
                }
            ),
            encoding="utf-8",
        )
        company = session.exec(select(Company).where(Company.ticker == "CPNG")).one()
        company.industry = None
        company.sector = None
        company.business_units = "[]"
        company.revenue_sources = "[]"
        session.commit()
        readiness = reconcile_onboarding(session, item, data_dir=tmp_path)
        session.commit()
        state = item.onboarding_state
        active = item.active
        production_eligible = item.production_eligible

    assert readiness.onboarding_ready is False
    assert "COMPANY_PROFILE" in readiness.blocking_requirements
    assert state == OnboardingState.PENDING_ONBOARDING
    assert active is False
    assert production_eligible is False


def test_market_subject_isolation_and_cutoff_snapshot(tmp_path: Path) -> None:
    engine = _engine()
    cutoff = datetime(2026, 8, 31, 7, tzinfo=UTC)
    with Session(engine) as session:
        kr_ready = _seed_ready_prerequisites(
            session,
            tmp_path,
            ticker="003690",
            exchange="KRX",
            company_name="Korean Re",
        )
        us_ready = _seed_ready_prerequisites(
            session,
            tmp_path,
            ticker="GOOGL",
            exchange="NASDAQ",
            company_name="Alphabet",
        )
        kr_pending = WatchlistItem(
            ticker="047810",
            company_name="Korea Aerospace Industries",
            exchange="KRX",
            active=False,
            monitoring_requested=True,
            onboarding_state=OnboardingState.PENDING_ONBOARDING,
            production_eligible=False,
        )
        us_late = _seed_ready_prerequisites(
            session,
            tmp_path,
            ticker="CPNG",
            exchange="NYSE",
            company_name="Coupang",
        )
        session.add(kr_pending)
        session.commit()
        reconcile_onboarding(
            session,
            kr_ready,
            data_dir=tmp_path,
            as_of=cutoff - timedelta(minutes=5),
        )
        reconcile_onboarding(
            session,
            us_ready,
            data_dir=tmp_path,
            as_of=cutoff - timedelta(minutes=5),
        )
        reconcile_onboarding(
            session,
            us_late,
            data_dir=tmp_path,
            as_of=cutoff + timedelta(minutes=5),
        )
        session.commit()
        kr_snapshot = production_universe_snapshot(
            session,
            "kr",
            cutoff=cutoff,
            session_key="daily_kr",
        )
        us_snapshot = production_universe_snapshot(
            session,
            "us",
            cutoff=cutoff,
            session_key="daily_us",
        )
        next_us = production_universe_snapshot(
            session,
            "us",
            cutoff=cutoff + timedelta(minutes=10),
            session_key="daily_us_next",
        )

    assert [item.ticker for item in kr_snapshot.eligible_items] == ["003690"]
    assert [item.ticker for item in us_snapshot.eligible_items] == ["GOOGL"]
    assert [item.ticker for item in next_us.eligible_items] == ["CPNG", "GOOGL"]
    assert any(
        row["ticker"] == "047810" for row in kr_snapshot.excluded_subjects
    )
    assert any(
        row["ticker"] == "CPNG"
        and "activated_after_packet_cutoff" in row["reasons"]
        for row in us_snapshot.excluded_subjects
    )


def test_evaluator_is_read_only_until_coordinator_applies_state(tmp_path: Path) -> None:
    engine = _engine()
    with Session(engine) as session:
        item = _seed_ready_prerequisites(
            session,
            tmp_path,
            ticker="READY1",
            exchange="NASDAQ",
            company_name="Ready Subject",
        )
        readiness = evaluate_onboarding_readiness(
            session, item, data_dir=tmp_path
        )

    assert readiness.onboarding_ready is True
    assert item.onboarding_state == OnboardingState.PENDING_ONBOARDING
    assert item.active is False
