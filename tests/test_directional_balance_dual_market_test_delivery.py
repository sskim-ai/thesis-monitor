import pytest

from scripts.directional_balance_dual_market_test_delivery import (
    _received_quality,
    _treasury_facts,
)


def test_received_stock_balance_requires_exact_sum_ten() -> None:
    valid = _received_quality("판단 균형: BUY 5.5 : SELL 4.5")
    invalid = _received_quality("판단 균형: BUY 5.5 : SELL 5.5")

    assert valid["status"] == "PASS"
    assert invalid["status"] == "FAIL"


def test_treasury_fixture_requires_all_four_nominal_series() -> None:
    observations = [
        {
            "series_code": series,
            "label": series,
            "current_date": "2026-09-01",
            "current_pct": 4.2,
            "previous_date": "2026-08-31",
            "previous_pct": 4.1,
        }
        for series in ("DGS3", "DGS5", "DGS10", "DGS30")
    ]

    assert len(_treasury_facts({"observations": observations})) == 4
    with pytest.raises(ValueError, match="treasury_fixture_incomplete"):
        _treasury_facts({"observations": observations[:-1]})
