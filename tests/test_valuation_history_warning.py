import json
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, SQLModel, create_engine

from app.models.event import Event
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import HistoricalPricePoint, ValuationSnapshot
from app.services.historical_valuation_service import (
    HistoricalValuationService,
    point_in_time_denominators,
)
from app.services.thesis_evaluation_service import evaluate_thesis
from app.services.valuation_snapshot_service import ValuationSnapshotService
from app.services.warning_backfill_service import backfill_confirmed_warning_states
from tests.test_integrated_accuracy import _price, _quarter


def _memory_engine():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def test_point_in_time_does_not_use_future_filing() -> None:
    rows = [
        _quarter("PIT", 2024, "H1", 8, eps=1),
        _quarter("PIT", 2024, "Q3", 11, eps=1),
        _quarter("PIT", 2024, "FY", 12, eps=1),
        _quarter("PIT", 2025, "Q1", 5, eps=1),
        _quarter("PIT", 2025, "H1", 7, eps=100),
    ]
    rows[-1].reported_date = date(2025, 7, 15)
    rows[-1].filing_date = date(2025, 7, 15)

    before, _, before_rows, _ = point_in_time_denominators(rows, date(2025, 6, 1))
    after, _, after_rows, _ = point_in_time_denominators(rows, date(2025, 7, 16))

    assert before == 4
    assert rows[-1] not in before_rows
    assert after == 103
    assert rows[-1] in after_rows


def test_filing_date_not_period_end_controls_availability() -> None:
    row = _quarter("FILED", 2025, "Q1", 5, eps=1)
    row.financial_period_end = date(2025, 3, 31)
    row.filing_date = date(2025, 5, 15)

    assert point_in_time_denominators([row], date(2025, 4, 20))[2] == []
    assert point_in_time_denominators([row], date(2025, 5, 16))[2] == [row]


def test_historical_percentile_uses_weekly_point_in_time_cache() -> None:
    engine = _memory_engine()
    ticker = "HIST"
    rows = [
        _quarter(ticker, 2023, "Q1", 5, eps=1, equity=100),
        _quarter(ticker, 2023, "H1", 8, eps=1, equity=100),
        _quarter(ticker, 2023, "Q3", 11, eps=1, equity=100),
        _quarter(ticker, 2023, "FY", 12, eps=1, equity=100),
    ]
    prices = [HistoricalPricePoint(date=date(2024, 1, day), close=40 + day) for day in range(1, 29)]
    with Session(engine) as session:
        session.add_all(rows)
        session.commit()
        observations = HistoricalValuationService().update_cache(session, ticker, prices, rows)
        snapshot = ValuationSnapshot(trailing_pe=20, price_to_book=5)
        service = HistoricalValuationService()
        service.settings.valuation_history_min_observations = 1
        service.apply(snapshot, observations, {"primary_method": "forward P/E"}, ticker)

    assert len(observations) <= 5
    assert snapshot.historical_pe_statistics is not None
    assert snapshot.historical_pe_statistics.current_percentile is not None


def test_cycle_low_per_does_not_automatically_mean_discounted() -> None:
    snapshot = ValuationSnapshot(trailing_pe=5, price_to_book=5)
    service = HistoricalValuationService()
    service.settings.valuation_history_min_observations = 1
    engine = _memory_engine()
    with Session(engine) as session:
        rows = [
            _quarter("000660", 2023, "Q1", 5, eps=1, equity=100),
            _quarter("000660", 2023, "H1", 8, eps=1, equity=100),
            _quarter("000660", 2023, "Q3", 11, eps=1, equity=100),
            _quarter("000660", 2023, "FY", 12, eps=1, equity=100),
        ]
        session.add_all(rows)
        session.commit()
        prices = [
            HistoricalPricePoint(
                date=date(2024, 1, 1) + timedelta(days=7 * index),
                close=10 + index,
            )
            for index in range(90)
        ]
        observations = service.update_cache(session, "000660", prices, rows)
        service.apply(snapshot, observations, {"primary_method": "cycle-adjusted forward P/E"}, "000660")

    assert snapshot.valuation_relative_position.value != "discounted"
    assert "사이클" in (snapshot.valuation_relative_position_reason or "")


def test_insurer_without_dividend_history_does_not_get_modeled_fpbr() -> None:
    rows = []
    for year in (2053, 2054):
        for period_type, month in (("Q1", 3), ("H1", 6), ("Q3", 9), ("FY", 12)):
            rows.append(_quarter("003690", year, period_type, month, equity=1_000))
    service = ValuationSnapshotService()
    snapshot = ValuationSnapshot(
        current_price=100,
        forward_pe=20,
        forward_pe_status="value",
        forward_pe_source="consensus_forward",
    )
    service._apply_forward_model(snapshot, rows, "003690", {"primary_method": "P/B-ROE"})

    assert snapshot.forward_price_to_book_status == "unavailable"
    assert snapshot.dividend_forecast_quality == "unavailable"
    assert all("배당 0" not in warning for warning in snapshot.warnings)


def test_three_year_dividend_history_enables_modeled_fpbr() -> None:
    rows = []
    for year in (2051, 2052, 2053, 2054):
        for period_type, month in (("Q1", 3), ("H1", 6), ("Q3", 9), ("FY", 12)):
            rows.append(
                _quarter(
                    "DIV3Y", year, period_type, month, equity=1_000,
                    dividends=2 if period_type == "FY" else None,
                )
            )
    service = ValuationSnapshotService()
    snapshot = ValuationSnapshot(current_price=100)
    service._apply_forward_model(snapshot, rows, "DIV3Y", {"primary_method": "forward P/E"})

    assert snapshot.forward_price_to_book_status == "value"
    assert snapshot.dividend_forecast_method == "median_3y_payout_ratio"


def test_us_fpbr_fallback_uses_dividend_and_buyback_history() -> None:
    rows = []
    for year in (2051, 2052, 2053, 2054):
        for period_type, month in (("Q1", 3), ("H1", 6), ("Q3", 9), ("FY", 12)):
            row = _quarter(
                "GOOGL", year, period_type, month, equity=1_000,
                dividends=1 if period_type == "FY" else None,
            )
            if period_type == "FY":
                row.buybacks = 2
            rows.append(row)
    service = ValuationSnapshotService()
    snapshot = ValuationSnapshot(
        current_price=100,
        forward_pe=20,
        forward_pe_status="value",
        forward_pe_source="consensus_forward",
    )
    service._apply_forward_model(snapshot, rows, "GOOGL", {"primary_method": "forward P/E"})

    assert snapshot.forward_price_to_book_status == "value"
    assert snapshot.forward_price_to_book_source == "modeled_forward"
    assert snapshot.forward_pe == 20
    assert snapshot.forward_pe_source == "consensus_forward"
    assert snapshot.dividend_forecast_method == "median_3y_payout_ratio"
    assert snapshot.buyback_forecast_method == "historical_normalized_buyback"


def test_tesla_confirmed_margin_and_fcf_are_backfilled_not_new() -> None:
    engine = _memory_engine()
    thesis = InvestmentThesis(
        ticker="TSLA",
        version=1,
        core_thesis="현재는 영업이익률 저하와 FCF 적자로 초기 균열이 있다. Robotaxi 경제성은 미증명이다.",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    with Session(engine) as session:
        session.add(thesis)
        session.commit()
        states = backfill_confirmed_warning_states(session, thesis, date(2025, 2, 1))
        result = evaluate_thesis(
            thesis,
            [],
            _price(100),
            baseline_warning_states=states,
        )

    assert result.new_warnings == []
    assert "영업이익률 저하 확인" in result.open_confirmed_warnings
    assert "FCF 적자 확인" in result.open_confirmed_warnings
    assert all("미증명" not in warning for warning in result.open_confirmed_warnings)


def test_warning_backfill_excludes_filing_receipt_metadata() -> None:
    engine = _memory_engine()
    thesis = InvestmentThesis(ticker="META", version=1, core_thesis="현금흐름을 확인한다.")
    event = Event(
        ticker="META",
        date=date(2025, 1, 1),
        source="OpenDART",
        provider="opendart",
        title="주요사항보고서(유상증자결정)",
        url="https://example.com/filing",
        event_type="capital_raise",
        confirmed_facts=json.dumps([
            "OpenDART filing title: 주요사항보고서(유상증자결정)",
            "OpenDART receipt number: 20250101000001",
        ]),
    )
    with Session(engine) as session:
        session.add(thesis)
        session.add(event)
        session.commit()
        states = backfill_confirmed_warning_states(session, thesis, date(2025, 1, 2))

    warnings = [str(item["warning"]) for item in states]
    assert warnings == ["주요사항보고서(유상증자결정) 공시 확인"]
    assert all("receipt" not in warning.lower() for warning in warnings)
