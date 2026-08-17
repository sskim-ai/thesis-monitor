from datetime import UTC, date, datetime

import pytest

from app.services.market_cross_section_service import (
    MarketCrossSection,
    MarketCrossSectionQuality,
    NormalizedMarketRow,
    calculate_market_breadth,
    concentration_from_proxy,
    reconcile_cross_sections,
)


SESSION = date(2026, 8, 14)


def _row(ticker: str, close: float, previous: float, volume: float = 10) -> NormalizedMarketRow:
    return NormalizedMarketRow(
        ticker=ticker,
        session_date=SESSION,
        close=close,
        previous_close=previous,
        volume=volume,
        eligible=True,
    )


def test_breadth_is_deterministic_and_reconciles_counts() -> None:
    breadth = calculate_market_breadth(
        [_row("ADV", 110, 100), _row("DEC", 90, 100), _row("FLAT", 100, 100)]
    )

    assert breadth.eligible_count == 3
    assert breadth.advance_count == breadth.decline_count == breadth.unchanged_count == 1
    assert breadth.advance_ratio == pytest.approx(1 / 3)
    assert breadth.ad_ratio == 1
    assert breadth.median_return_pct == 0
    assert breadth.equal_weight_return_pct == pytest.approx(0)
    assert breadth.total_trading_volume == 30
    assert breadth.total_trading_value == 3000


def test_missing_previous_close_is_excluded_instead_of_filled_with_zero() -> None:
    missing = NormalizedMarketRow(
        ticker="NEW",
        session_date=SESSION,
        close=10,
        previous_close=None,
        eligible=False,
        exclusion_reasons=["previous_adjusted_close_missing"],
    )

    assert calculate_market_breadth([missing]).eligible_count == 0


def test_concentration_calls_spy_a_proxy_not_whole_market() -> None:
    value = concentration_from_proxy(
        proxy_symbol="SPY", proxy_return_pct=1.2, equal_weight_return_pct=0.3
    )

    assert value["concentration_gap_pct"] == pytest.approx(0.9)
    assert value["metric_role"] == "broad_cap_weight_proxy_gap"
    assert "not a market-cap-weighted whole-market" in value["limitations"][0]


def _section(provider: str, universe: str) -> MarketCrossSection:
    breadth = calculate_market_breadth([_row("ADV", 110, 100)])
    return MarketCrossSection(
        market="US",
        session_date=SESSION,
        as_of=datetime(2026, 8, 15, tzinfo=UTC),
        breadth=breadth,
        quality=MarketCrossSectionQuality(
            provider=provider,
            provider_role="shadow",
            coverage="full",
            freshness="fresh",
            universe_version=universe,
            raw_count=1,
            eligible_count=1,
            excluded_count=0,
        ),
        source_payload_sha256="a" * 64,
    )


def test_reconciliation_fails_closed_for_different_universes() -> None:
    result = reconcile_cross_sections(_section("krx", "krx-v1"), _section("kiwoom", "kiwoom-v1"))

    assert result.comparable is False
    assert "universe_version_mismatch" in result.reason_codes
