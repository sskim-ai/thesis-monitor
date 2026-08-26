from __future__ import annotations

from datetime import date
from decimal import Decimal

import exchange_calendars as exchange_calendar

from app.services.ohlcv_history_cache_service import (
    HistoryCacheIdentity,
    HistoryPage,
    merge_history_pages,
    update_cached_history,
)
from app.services.price_structure_wave_fibonacci_v3_service import (
    PivotPoint,
    PriceBar,
    WaveHypothesisSelection,
    WaveSelectionStatus,
    apply_wave_selection_feedback,
    build_price_structure_wave_fib_v3,
    detect_pivots,
    generate_primary_monthly_hypotheses,
    normalize_completed_bars,
)


def _raw(bar_date: str, close: int, spread: int = 2) -> dict[str, object]:
    return {
        "date": bar_date,
        "open": close,
        "high": close + spread,
        "low": close - spread,
        "close": close,
        "volume": 1000,
        "value": 100_000,
    }


def _pivot(identifier: str, bar_date: str, price: int, kind: str) -> PivotPoint:
    return PivotPoint(
        pivot_id=identifier,
        ticker="TEST",
        timeframe="monthly",
        bar_date=bar_date,
        pivot_bar_date=bar_date,
        required_right_bar_count=2,
        confirmation_date=bar_date,
        pivot_confirmation_date=bar_date,
        confirmation_bar_ids=(f"confirm:{identifier}:1", f"confirm:{identifier}:2"),
        kind=kind,
        price=Decimal(price),
        atr14=Decimal(5),
        status="CONFIRMED",
        adjustment_basis="adjusted_close",
        source_ref=f"ohlcv:monthly:{bar_date}",
    )


def test_kr_partial_daily_weekly_monthly_bars_are_explicit() -> None:
    observed_at = "2026-08-26T13:19:36+09:00"
    daily = normalize_completed_bars(
        [_raw("2026-08-25", 100), _raw("2026-08-26", 105)],
        cutoff="2026-08-26",
        timeframe="daily",
        market="KR",
        observed_at=observed_at,
    )
    weekly = normalize_completed_bars(
        [_raw("2026-08-18", 100), _raw("2026-08-24", 105)],
        cutoff="2026-08-26",
        timeframe="weekly",
        market="KR",
        observed_at=observed_at,
    )
    monthly = normalize_completed_bars(
        [_raw("2026-07-01", 100), _raw("2026-08-03", 105)],
        cutoff="2026-08-26",
        timeframe="monthly",
        market="KR",
        observed_at=observed_at,
    )
    assert [bar.bar_state for bar in daily] == ["COMPLETE", "PARTIAL"]
    assert [bar.bar_state for bar in weekly] == ["COMPLETE", "PARTIAL"]
    assert [bar.bar_state for bar in monthly] == ["COMPLETE", "PARTIAL"]
    assert monthly[-1].period_start == "2026-08-03"
    assert monthly[-1].period_end == "2026-08-31"
    assert all(bar.observed_at and bar.market_calendar == "XKRX" for bar in monthly)


def test_partial_monthly_bar_cannot_confirm_prior_pivot() -> None:
    bars = normalize_completed_bars(
        [
            _raw("2026-04-01", 90),
            _raw("2026-05-04", 100),
            _raw("2026-06-01", 200),
            _raw("2026-07-01", 140),
            _raw("2026-08-03", 150),
        ],
        cutoff="2026-08-26",
        timeframe="monthly",
        market="KR",
        observed_at="2026-08-26T13:19:36+09:00",
    )
    pivots = detect_pivots(
        bars,
        ticker="000660",
        timeframe="monthly",
        adjustment_basis="adjusted_close",
    )
    june = next(item for item in pivots if item.kind == "HIGH" and item.bar_date == "2026-06-01")
    assert june.status == "PROVISIONAL"
    assert june.pivot_confirmation_date is None
    assert june.required_right_bar_count == 2
    assert june.confirmation_bar_ids == ()


def test_history_cache_stitches_overlap_to_true_1200_without_duplicates() -> None:
    calendar = exchange_calendar.get_calendar(
        "XNYS", start=date(2020, 1, 1), end=date(2026, 12, 31)
    )
    sessions = [item.date().isoformat() for item in calendar.sessions][-1200:]
    rows = tuple(_raw(item, 100 + index) for index, item in enumerate(sessions))
    identity = HistoryCacheIdentity(
        security_id="MU:NASDAQ",
        listing_id="MU:NASDAQ",
        timeframe="daily",
        adjustment_basis="adjusted_close",
        currency="USD",
    )
    pages = (
        HistoryPage(
            page_id="page:new",
            provider="kiwoom",
            identity=identity,
            observed_at="2026-08-26T13:20:00+09:00",
            rows=rows[-1000:],
        ),
        HistoryPage(
            page_id="page:old",
            provider="kiwoom",
            identity=identity,
            observed_at="2026-08-26T13:20:01+09:00",
            rows=rows[:400],
        ),
    )
    result = merge_history_pages(
        pages,
        identity=identity,
        market="US",
        requested_count=1200,
        cutoff=sessions[-1],
    )
    assert result.status == "PASS"
    assert result.actual_count == 1200
    assert result.chronology_valid is True
    assert result.missing_expected_dates == ()
    assert len(result.duplicate_dates_deduplicated) == 200
    assert result.cache_key == identity.cache_key


def test_history_cache_incremental_append_and_revision_are_explicit() -> None:
    identity = HistoryCacheIdentity(
        security_id="TEST:NASDAQ",
        listing_id="TEST:NASDAQ",
        timeframe="daily",
        adjustment_basis="adjusted_close",
        currency="USD",
    )
    initial = HistoryPage(
        page_id="initial",
        provider="fixture",
        identity=identity,
        observed_at="2026-08-25T17:00:00-04:00",
        rows=(_raw("2026-08-24", 100), _raw("2026-08-25", 101)),
    )
    cached = merge_history_pages(
        (initial,),
        identity=identity,
        market="US",
        requested_count=3,
        cutoff="2026-08-25",
    )
    update = HistoryPage(
        page_id="incremental",
        provider="fixture",
        identity=identity,
        observed_at="2026-08-26T17:00:00-04:00",
        rows=(_raw("2026-08-25", 102), _raw("2026-08-26", 103)),
    )
    audit = update_cached_history(
        cached,
        update,
        market="US",
        cutoff="2026-08-26",
    )
    assert audit.cache_hit is True
    assert audit.revised_dates == ("2026-08-25",)
    assert audit.appended_dates == ("2026-08-26",)
    assert audit.result.last_bar_date == "2026-08-26"
    assert audit.result.revision_timestamp == "2026-08-26T17:00:00-04:00"


def test_latest_valid_w0_is_visible_as_current_cycle_not_hidden_by_magnitude() -> None:
    bars_list: list[PriceBar] = []
    for index in range(144):
        bar_date = f"{2015 + index // 12:04d}-{index % 12 + 1:02d}-01"
        low, high = Decimal(90), Decimal(220)
        if bar_date == "2016-05-01":
            low = Decimal(25)
        elif bar_date == "2023-01-01":
            low = Decimal(73)
        elif "2023-01-01" < bar_date < "2024-07-01":
            low = Decimal(90)
        elif bar_date == "2024-07-01":
            high = Decimal(248)
            low = Decimal(180)
        elif bar_date == "2024-09-01":
            low = Decimal(145)
        elif "2024-07-01" < bar_date < "2026-06-01":
            low = Decimal(160)
        elif bar_date == "2026-06-01":
            high = Decimal(300)
            low = Decimal(280)
        elif bar_date == "2026-07-01":
            high = Decimal(280)
            low = Decimal(260)
        close = (low + high) / 2
        bars_list.append(
            PriceBar(
                date=bar_date,
                open=close,
                high=high,
                low=low,
                close=close,
            )
        )
    bars = tuple(bars_list)
    pivots = (
        _pivot("old-w0", "2016-05-01", 25, "LOW"),
        _pivot("current-w0", "2023-01-01", 73, "LOW"),
        _pivot("w1", "2024-07-01", 248, "HIGH"),
        _pivot("w2", "2024-09-01", 145, "LOW"),
        _pivot("w3", "2026-06-01", 300, "HIGH"),
        _pivot("w4", "2026-07-01", 260, "LOW"),
    )
    hypotheses = generate_primary_monthly_hypotheses(
        bars,
        pivots,
        (),
        ticker="TEST",
        search_horizon=144,
    )
    assert any(
        item.source_degree == "PRIMARY_CURRENT_CYCLE"
        and next(point.date for point in item.endpoints if point.label == "W0") == "2023-01-01"
        for item in hypotheses
    )
    assert any(item.source_degree == "GRAND_CYCLE" for item in hypotheses)


def test_valid_ai_selection_is_fed_to_fib_and_invalid_selection_preserves_sr() -> None:
    closes = [150, 130, 100, 110, 150, 200, 180, 145, 170, 240, 320, 280, 230, 260, 270]
    raw = [
        _raw(f"{2024 + index // 12:04d}-{index % 12 + 1:02d}-01", close)
        for index, close in enumerate(closes)
    ]
    raw_by_timeframe = {"daily": raw, "weekly": raw, "monthly": raw}
    base = build_price_structure_wave_fib_v3(
        ticker="TEST",
        security_id="TEST:NASDAQ",
        market="US",
        currency="USD",
        adjustment_basis="adjusted_close",
        cutoff="2026-08-26",
        raw_by_timeframe=raw_by_timeframe,
        provider_limit=None,
    )
    hypothesis = base.primary_monthly_hypotheses[0]
    selection = WaveHypothesisSelection(
        status=WaveSelectionStatus.SELECTED,
        hypothesis_id=hypothesis.hypothesis_id,
        confidence="MEDIUM",
        reason_categories=("STRUCTURE_FIT",),
        ticker="TEST",
        source_degree=hypothesis.source_degree,
        cutoff="2026-08-26",
        adjustment_basis="adjusted_close",
        endpoint_refs=tuple(point.pivot_ref for point in hypothesis.endpoints),
    )
    applied = apply_wave_selection_feedback(
        base,
        selection,
        raw_by_timeframe=raw_by_timeframe,
        provider_limit=None,
    )
    assert applied.feedback_audit is not None
    assert applied.feedback_audit.selected_hypothesis_fed_to_engine is True
    assert applied.fibonacci
    assert {item.wave_hypothesis_id for item in applied.fibonacci} == {
        hypothesis.hypothesis_id
    }

    invalid = selection.model_copy(update={"ticker": "OTHER"})
    rejected = apply_wave_selection_feedback(
        base,
        invalid,
        raw_by_timeframe=raw_by_timeframe,
        provider_limit=None,
    )
    assert rejected.feedback_audit is not None
    assert rejected.feedback_audit.validation.errors == ("ticker_mismatch",)
    assert rejected.fibonacci == ()
    assert rejected.sr_maps == base.sr_maps
