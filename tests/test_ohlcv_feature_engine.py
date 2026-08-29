from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.services.ohlcv_feature_engine_service import (
    FeatureStatus,
    build_multi_timeframe_feature_packet,
)


def _bars(count: int, *, start: date = date(2025, 1, 1)) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = Decimal("100") + Decimal(index) / Decimal("10")
        rows.append(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": close - Decimal("0.2"),
                "high": close + Decimal("1"),
                "low": close - Decimal("1"),
                "close": close,
                "volume": 1_000_000 + index * 100,
                "is_complete": True,
            }
        )
    return rows


def test_feature_engine_builds_dwm_completed_bar_facts_without_lookahead() -> None:
    daily = _bars(260)
    daily.append(
        {
            "date": "2026-01-01",
            "open": 999,
            "high": 1000,
            "low": 998,
            "close": 999,
            "volume": 1,
            "is_complete": False,
        }
    )
    packet = build_multi_timeframe_feature_packet(
        ticker="TEST",
        periods={"daily": daily, "weekly": _bars(220), "monthly": _bars(80)},
        cutoff=date(2026, 1, 1),
    )

    daily_facts = {fact.semantic: fact for fact in packet.daily.facts}
    assert packet.contract == "ohlcv-multi-timeframe-feature-engine-v1"
    assert packet.daily.provisional_count == 1
    assert packet.daily.completed_count == 260
    assert packet.daily.status == FeatureStatus.PARTIAL
    assert packet.daily.source_limitation == "provider_request_cap_1000"
    assert daily_facts["return_252"].completed_bar_only is True
    assert str(daily_facts["macd_state"].value).endswith("_ABOVE_ZERO")
    assert "adx_14" in daily_facts
    assert "mfi_14" in daily_facts
    assert "donchian_breakout_20" in daily_facts
    assert daily_facts["close"].value != Decimal(999)


def test_missing_volume_suppresses_volume_family_without_blocking_price_features() -> None:
    rows = _bars(60)
    for row in rows:
        row["volume"] = None
    packet = build_multi_timeframe_feature_packet(
        ticker="TEST",
        periods={"daily": rows},
        cutoff=date(2026, 1, 1),
    )
    semantics = {fact.semantic for fact in packet.daily.facts}
    assert "return_20" in semantics
    assert "volume_ratio_20" not in semantics
    assert packet.weekly.status == FeatureStatus.UNAVAILABLE


def test_cutoff_excludes_future_completed_bars() -> None:
    rows = _bars(40)
    cutoff = date(2025, 1, 20)
    packet = build_multi_timeframe_feature_packet(
        ticker="TEST",
        periods={"daily": rows},
        cutoff=cutoff,
    )
    assert packet.daily.completed_count == 20
    assert packet.daily.as_of == cutoff.isoformat()
