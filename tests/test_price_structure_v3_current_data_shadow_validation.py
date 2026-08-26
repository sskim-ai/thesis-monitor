from scripts.phase20260826_price_structure_v3_current_data_validation import (
    _business_surface,
    _insert_kr_price_surface,
    _merge_daily,
    _replace_us_price_surface,
    _safe_partial_periods,
)


def _bar(
    bar_date: str,
    close: float,
    *,
    high: float | None = None,
    low: float | None = None,
    volume: float = 10.0,
    value: float = 100.0,
) -> dict[str, object]:
    return {
        "date": bar_date,
        "open": close,
        "high": high if high is not None else close,
        "low": low if low is not None else close,
        "close": close,
        "volume": volume,
        "value": value,
    }


def test_completed_session_gate_overrides_safe_date_and_excludes_future_stub() -> None:
    archived = [_bar("2026-08-24", 10), _bar("2026-08-25", 11)]
    live = [_bar("2026-08-25", 12), _bar("2026-08-26", 9)]

    safe, excluded = _merge_daily(
        archived,
        live,
        target_session="2026-08-25",
    )

    assert [row["date"] for row in safe] == ["2026-08-24", "2026-08-25"]
    assert safe[-1]["close"] == 12
    assert [row["date"] for row in excluded] == ["2026-08-26"]


def test_partial_week_context_removes_future_stub_contribution() -> None:
    weekly = [
        _bar(
            "2026-08-24",
            9,
            high=13,
            low=8,
            volume=35,
            value=350,
        )
    ]
    safe_daily = [
        _bar("2026-08-24", 10, high=11, low=9, volume=10, value=100),
        _bar("2026-08-25", 12, high=13, low=10, volume=20, value=200),
    ]
    excluded = [_bar("2026-08-26", 9, volume=5, value=50)]

    result = _safe_partial_periods(
        weekly,
        safe_daily,
        excluded,
        timeframe="weekly",
    )

    assert result[-1]["open"] == 10
    assert result[-1]["high"] == 13
    assert result[-1]["low"] == 9
    assert result[-1]["close"] == 12
    assert result[-1]["volume"] == 30
    assert result[-1]["value"] == 300


def test_us_candidate_replaces_only_bounded_price_surface() -> None:
    baseline = """🏢 Example(EX)

🎯 핵심
Business fact.

💰 가격
현재가: $10.00 · 2026-08-25 미국장 종가
현재 구조: old
신규 관찰자:
• 동적 지지: $9.00~$9.50
보유자:
• 차트 무효화 가격: $8.00

📐 Valuation
PER: 10배
"""
    section = "📐 가격 구조\n• 가까운 지지: 약 $9.5~$9.8"

    candidate = _replace_us_price_surface(
        baseline,
        section,
        current_price=10.25,
        target_session="2026-08-25",
    )

    assert "현재가: $10.25" in candidate
    assert section in candidate
    assert "동적 지지" not in candidate
    assert "차트 무효화 가격: $8.00" in candidate
    assert _business_surface(candidate) == _business_surface(baseline)


def test_kr_candidate_inserts_price_structure_without_business_change() -> None:
    baseline = """🏢 예시(000000)

🎯 판단
Business fact.

📌 다음 확인
• 다음 실적
"""
    section = "📐 가격 구조\n• 가까운 지지: 약 1만~1.1만원"

    candidate = _insert_kr_price_surface(baseline, section)

    assert section in candidate
    assert _business_surface(candidate) == _business_surface(baseline)
