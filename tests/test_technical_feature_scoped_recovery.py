from __future__ import annotations

from datetime import date, timedelta

from app.services.ohlcv_completed_bar_finality_service import (
    COMPLETED_CLOSE_KEY,
    SEMANTICS_KEY,
    BarFinality,
    annotate_normalized_bar,
    assess_completed_bar_finality,
)
from app.services.ohlcv_feature_engine_service import (
    build_multi_timeframe_feature_packet,
)
from app.services.ohlcv_secondary_recovery_service import (
    SecondaryRecoveryStatus,
    SecondarySourcePolicy,
    recover_exact_bad_row,
)
from app.services.packet_owned_technical_context_service import (
    TechnicalContextStatus,
    build_packet_owned_technical_context,
)
from app.services.technical_feature_dependency_service import (
    DependencyClassification,
)


def _bars(count: int = 420) -> list[dict[str, object]]:
    start = date(2025, 1, 1)
    return [
        {
            "date": (start + timedelta(days=index)).isoformat(),
            "open": 99 + index,
            "high": 102 + index,
            "low": 98 + index,
            "close": 100 + index,
            "volume": 1_000 + index,
        }
        for index in range(count)
    ]


def _context(periods: dict[str, list[dict[str, object]]]):
    return build_packet_owned_technical_context(
        ticker="TEST",
        market="us",
        session="after_hours",
        as_of="2026-02-24T18:00:00-05:00",
        periods=periods,
        cutoff=date(2026, 2, 24),
        expected_daily_completed="2026-02-24",
    )


def _semantics(*, has_later: bool, settled_field: str | None = None) -> dict[str, object]:
    return {
        "provider": "kiwoom",
        "market": "US",
        "endpoint": "usa06012",
        "normalized_close_field": "cur_prc",
        "normalized_close_owner": "CURRENT_QUOTE",
        "settled_regular_close_field": settled_field,
        "current_quote_field": "cur_prc",
        "provider_finality_field": None,
        "has_later_chart_row": has_later,
    }


def _policy(**overrides: bool) -> SecondarySourcePolicy:
    values = {
        "provider": "approved_fixture",
        "approved_for_production_ohlcv": True,
        "security_identity_exact": True,
        "session_exact": True,
        "currency_exact": True,
        "adjustment_basis_compatible": True,
        "timestamp_safe": True,
        "scale_compatible": True,
    }
    values.update(overrides)
    return SecondarySourcePolicy(**values)


def test_old_bad_row_recovers_only_exact_independent_features_with_numeric_parity() -> None:
    clean = _bars()
    malformed = [dict(row) for row in clean]
    malformed[20]["high"] = 1
    bad_date = malformed[20]["date"]
    clean_without_bad = [row for row in clean if row["date"] != bad_date]

    recovered = build_multi_timeframe_feature_packet(
        ticker="CPNG",
        periods={"daily": malformed},
        cutoff=date(2026, 2, 24),
    ).daily
    expected = build_multi_timeframe_feature_packet(
        ticker="CPNG",
        periods={"daily": clean_without_bad},
        cutoff=date(2026, 2, 24),
    ).daily

    recovered_by_semantic = {fact.semantic: fact for fact in recovered.facts}
    expected_by_semantic = {fact.semantic: fact for fact in expected.facts}
    assert recovered.invalid_source_row_count == 1
    assert recovered.safe_feature_count > 0
    assert recovered.dependency_blocked_count > 0
    assert "sma_20" in recovered_by_semantic
    assert "ema_20" not in recovered_by_semantic
    assert "ema_20" in recovered.blocked_features
    assert recovered_by_semantic["sma_20"].value == expected_by_semantic["sma_20"].value
    assert (
        recovered_by_semantic["sma_20"].dependency_classification
        == DependencyClassification.SAFE_INDEPENDENT_OF_BAD_ROW
    )


def test_recent_bad_row_reduces_safe_feature_coverage() -> None:
    old_bad = _bars()
    recent_bad = _bars()
    old_bad[20]["high"] = 1
    recent_bad[-10]["high"] = 1

    old_result = build_multi_timeframe_feature_packet(
        ticker="CPNG", periods={"daily": old_bad}, cutoff=date(2026, 2, 24)
    ).daily
    recent_result = build_multi_timeframe_feature_packet(
        ticker="CPNG", periods={"daily": recent_bad}, cutoff=date(2026, 2, 24)
    ).daily

    assert recent_result.safe_feature_count < old_result.safe_feature_count
    assert "sma_20" in recent_result.blocked_features


def test_historical_bad_row_is_partial_safe_and_current_bad_timeframe_is_invalid() -> None:
    historical = _bars(420)
    historical[20]["high"] = 1
    current = _bars(420)
    current[-1]["high"] = 1
    other = _bars(80)

    historical_context = _context(
        {"daily": historical, "weekly": _bars(300), "monthly": other}
    )
    current_context = _context(
        {"daily": current, "weekly": _bars(300), "monthly": other}
    )

    assert historical_context.status == TechnicalContextStatus.PARTIAL_SAFE
    assert historical_context.quality["D"].status == TechnicalContextStatus.PARTIAL_SAFE
    assert historical_context.quality["D"].usable_for_current_reasoning is True
    assert current_context.status == TechnicalContextStatus.PARTIAL_SAFE
    assert current_context.quality["D"].status == TechnicalContextStatus.INVALID
    assert current_context.quality["D"].usable_for_current_reasoning is False
    assert current_context.quality["M"].status == TechnicalContextStatus.FULL


def test_current_quote_cannot_silently_own_completed_close() -> None:
    row = annotate_normalized_bar(
        {
            "date": "2026-08-31",
            "open": "79.43",
            "high": "79.99",
            "low": "75.71",
            "close": "81.94",
            "volume": 4_201_466,
        },
        provider="kiwoom",
        market="US",
        timeframe="daily",
    )

    result = assess_completed_bar_finality(row, cutoff=date(2026, 8, 31))

    assert result.state == BarFinality.UNCONFIRMED
    assert result.completed_close_field is None
    assert result.current_quote_silently_owns_completed_close is False


def test_safe_settled_close_owns_candle_while_quote_remains_separate() -> None:
    row = {
        "date": "2026-08-31",
        "open": "79.43",
        "high": "79.99",
        "low": "75.71",
        "close": "81.94",
        "volume": 4_201_466,
        COMPLETED_CLOSE_KEY: "79.50",
        SEMANTICS_KEY: _semantics(has_later=False, settled_field="regular_close"),
    }

    result = assess_completed_bar_finality(row, cutoff=date(2026, 8, 31))
    packet = build_multi_timeframe_feature_packet(
        ticker="HUT", periods={"daily": [row]}, cutoff=date(2026, 8, 31)
    )

    assert result.state == BarFinality.FINAL
    assert result.completed_close_value is not None
    close_fact = next(fact for fact in packet.daily.facts if fact.semantic == "close")
    assert str(close_fact.value) == "79.500000"


def test_later_valid_chart_row_automatically_finalizes_prior_row() -> None:
    prior = annotate_normalized_bar(
        {
            "date": "2026-08-31",
            "open": 79.43,
            "high": 79.99,
            "low": 75.71,
            "close": 79.50,
            "volume": 4_201_466,
        },
        provider="kiwoom",
        market="US",
        timeframe="daily",
        has_later_chart_row=True,
    )

    result = assess_completed_bar_finality(prior, cutoff=date(2026, 9, 1))

    assert result.state == BarFinality.FINAL
    assert result.source == "later_chart_row_proves_historical_finality"


def test_date_without_field_semantics_is_not_finality_proof() -> None:
    result = assess_completed_bar_finality(
        {
            "date": "2026-08-31",
            "open": 10,
            "high": 12,
            "low": 9,
            "close": 11,
        },
        cutoff=date(2026, 8, 31),
    )

    assert result.state == BarFinality.UNCONFIRMED


def test_hut_invalid_daily_weekly_preserve_independent_monthly_safe_context() -> None:
    periods: dict[str, list[dict[str, object]]] = {}
    for timeframe in ("daily", "weekly", "monthly"):
        raw = _bars(80)
        annotated = [
            annotate_normalized_bar(
                row,
                provider="kiwoom",
                market="US",
                timeframe=timeframe,
                has_later_chart_row=index < len(raw) - 1,
            )
            for index, row in enumerate(raw)
        ]
        periods[timeframe] = annotated
    for timeframe in ("daily", "weekly"):
        periods[timeframe][-1]["close"] = periods[timeframe][-1]["high"] + 10  # type: ignore[operator]

    context = _context(periods)

    assert context.status == TechnicalContextStatus.PARTIAL_SAFE
    assert context.quality["D"].status == TechnicalContextStatus.INVALID
    assert context.quality["W"].status == TechnicalContextStatus.INVALID
    assert context.quality["M"].status == TechnicalContextStatus.PARTIAL_SAFE
    assert context.quality["M"].usable_for_current_reasoning is True
    assert context.features is not None
    assert context.quality["D"].invalid_source_row_count == 0


def test_secondary_exact_row_recovery_is_strict_and_provenance_bound() -> None:
    bad = {"date": "2023-06-05", "open": 16.35, "high": 15.8, "low": 15.43, "close": 15.66}
    safe = {"date": "2023-06-05", "open": 16.35, "high": 16.5, "low": 15.43, "close": 15.66}

    recovered = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row=safe,
        timeframe="daily",
        policy=_policy(),
    )
    mismatch = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row={**safe, "date": "2023-06-06"},
        timeframe="daily",
        policy=_policy(),
    )
    malformed = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row={**safe, "high": 1},
        timeframe="daily",
        policy=_policy(),
    )
    unapproved = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row=safe,
        timeframe="daily",
        policy=_policy(approved_for_production_ohlcv=False),
    )

    assert recovered.status == SecondaryRecoveryStatus.RECOVERED
    assert recovered.recovered_row is not None
    assert recovered.recovered_row["_recovery_provenance"]["whole_series_swap"] is False
    assert mismatch.status == SecondaryRecoveryStatus.NOT_COMPARABLE
    assert malformed.status == SecondaryRecoveryStatus.SECONDARY_INVALID
    assert unapproved.status == SecondaryRecoveryStatus.NO_APPROVED_SOURCE


def test_secondary_security_and_adjustment_mismatch_are_rejected() -> None:
    bad = {"date": "2023-06-05", "open": 16.35, "high": 15.8, "low": 15.43, "close": 15.66}
    safe = {"date": "2023-06-05", "open": 16.35, "high": 16.5, "low": 15.43, "close": 15.66}

    security = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row=safe,
        timeframe="daily",
        policy=_policy(security_identity_exact=False),
    )
    adjustment = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row=safe,
        timeframe="daily",
        policy=_policy(adjustment_basis_compatible=False),
    )
    scale = recover_exact_bad_row(
        primary_bad_row=bad,
        secondary_row=safe,
        timeframe="daily",
        policy=_policy(scale_compatible=False),
    )

    assert security.status == SecondaryRecoveryStatus.NOT_COMPARABLE
    assert adjustment.status == SecondaryRecoveryStatus.NOT_COMPARABLE
    assert scale.status == SecondaryRecoveryStatus.NOT_COMPARABLE
