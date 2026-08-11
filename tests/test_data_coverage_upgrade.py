import json
from datetime import date, timedelta

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import DividendHistory, FinancialSnapshot, HistoricalValuationObservation
from app.models.watchlist import WatchlistItem
from app.providers.base import RawEvent
from app.schemas.thesis import ValuationSnapshot
from app.services.capital_action_service import CapitalActionService
from app.services.daily_digest import _axis_explanations
from app.services.data_coverage_service import DataCoverageService
from app.services.dividend_history_service import DividendHistoryService
from app.services.event_classifier import classify_event
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.historical_valuation_service import HistoricalValuationService


def _engine():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def _event(ticker: str, title: str, event_type: str, when: date) -> Event:
    return Event(
        ticker=ticker,
        date=when,
        source="OpenDART",
        provider="opendart",
        title=title,
        url=f"https://example.com/{title}",
        event_type=event_type,
        confirmed_facts="[]",
    )


def test_dividend_event_is_connected_to_history() -> None:
    engine = _engine()
    event = _event("DIV", "현금ㆍ현물배당결정", "capital_allocation", date(2025, 3, 1))
    event.confirmed_facts = json.dumps(
        [
            "OpenDART receipt number: 202503010001",
            "OpenDART dividend fact: dps = 500 KRW",
            "OpenDART dividend fact: total_dividend = 5000000000 KRW",
            "OpenDART dividend fact: payout_ratio = 35 percent",
        ]
    )
    with Session(engine) as session:
        session.add(event)
        session.commit()
        DividendHistoryService().ingest_event(session, event)
        session.commit()
        row = session.exec(select(DividendHistory)).one()

    assert row.dividend_per_share == 500
    assert row.total_dividend == 5_000_000_000
    assert row.payout_ratio == 0.35


def test_capital_action_documents_create_one_canonical_issue() -> None:
    engine = _engine()
    first = _event("CAP", "주요사항보고서(유상증자결정)", "capital_raise", date(2025, 1, 1))
    first.confirmed_facts = json.dumps(["OpenDART capital raise fact: new_shares = 100 shares"])
    second = _event("CAP", "증권발행실적보고서(유상증자)", "capital_raise", date(2025, 2, 1))
    second.confirmed_facts = first.confirmed_facts
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="CAP",
                period="2024-FY",
                provider="opendart",
                filing_date=date(2024, 12, 31),
                common_shares_outstanding=1_000,
            )
        )
        session.add(first)
        session.add(second)
        session.commit()
        service = CapitalActionService()
        one = service.canonicalize(session, first)
        two = service.canonicalize(session, second)
        session.commit()
        issues = session.exec(select(CanonicalIssue)).all()

    assert one is not None and two is not None
    assert one.issue_key == two.issue_key
    assert len(issues) == 1
    assert issues[0].dilution_pct == 10
    assert issues[0].execution_status == "completed"


def test_material_structured_flag_overrides_noise_classification() -> None:
    raw = RawEvent(
        ticker="SNDK",
        company_name="SanDisk",
        date=date.today(),
        source="Company IR",
        title="SanDisk updates outlook",
        url="https://example.com/sndk",
        summary="SanDisk published an outlook update.",
        provider="company_ir",
        revenue_guidance_changed=True,
        guidance_changed=True,
    )

    assert classify_event(raw).value == "revenue_guidance_change"


def test_new_financial_event_marks_snapshot_refresh_pending() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="FRESH",
                period="2025-Q1",
                provider="fixture",
                filing_date=date(2025, 5, 1),
                financial_period_end=date(2025, 3, 31),
            )
        )
        event = _event("FRESH", "Quarterly report", "financial_report", date(2025, 8, 1))
        event.financial_report_filed = True
        session.add(event)
        session.commit()
        result = FinancialFreshnessService().assess(session, "FRESH")

    assert result.refresh_required is True
    assert result.status == "refresh_pending"
    assert event.financial_refresh_required is True


def test_foreign_issuer_without_adr_mapping_returns_reason_code() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(
            WatchlistItem(
                ticker="FPI",
                company_name="Foreign Issuer",
                exchange="NYSE",
                issuer_type="foreign_private_issuer",
            )
        )
        session.commit()
        coverage = DataCoverageService().build(session, "FPI", ValuationSnapshot())

    assert coverage.issuer_type == "foreign_private_issuer"
    assert "missing_adr_ratio" in coverage.reason_codes


def test_conflicting_pe_pb_signals_are_not_high_confidence_directional() -> None:
    engine = _engine()
    observations = [
        HistoricalValuationObservation(
            ticker="CONFLICT",
            observation_date=date(2020, 1, 1) + timedelta(days=7 * index),
            price=10,
            trailing_pe=float(index + 1),
            price_to_book=float(index + 1),
        )
        for index in range(40)
    ]
    snapshot = ValuationSnapshot(trailing_pe=39, price_to_book=2)
    service = HistoricalValuationService()
    service.settings.valuation_history_min_observations = 1
    with Session(engine) as session:
        session.add_all(observations)
        session.commit()
        service.apply(snapshot, observations, {"primary_method": "forward P/E"}, "CONFLICT")

    assert snapshot.valuation_signal_conflict is True
    assert snapshot.valuation_relative_position.value == "neutral"
    assert snapshot.valuation_relative_position_confidence != "high"
    assert "엇갈" in (snapshot.valuation_signal_summary or "")


def test_short_internal_history_is_not_called_short_listing_history() -> None:
    observations = [
        HistoricalValuationObservation(
            ticker="OLDCO",
            observation_date=date(2024, 1, 1) + timedelta(days=7 * index),
            price=10,
            trailing_pe=10 + index,
        )
        for index in range(30)
    ]
    snapshot = ValuationSnapshot(trailing_pe=20)
    service = HistoricalValuationService()
    service.settings.valuation_history_min_observations = 1
    service.apply(snapshot, observations, {"primary_method": "forward P/E"}, "OLDCO")

    assert "상장 이력" not in (snapshot.valuation_relative_position_reason or "")
    assert "point-in-time 재무 이력" in (snapshot.valuation_relative_position_reason or "")


def test_price_proxy_macro_wording_does_not_confirm_growth_slowdown() -> None:
    explanations = dict(
        _axis_explanations(
            {
                "growth_momentum": -1,
                "inflation_pressure": 0,
                "liquidity_condition": 0,
                "financial_conditions": 0,
                "risk_appetite": 0,
                "earnings_momentum": 0,
            },
            {},
        )
    )

    assert "실제 경기지표 악화가 확인된 것은 아닙니다" in explanations["경기"]
    assert "성장 둔화 확인" not in explanations["경기"]
