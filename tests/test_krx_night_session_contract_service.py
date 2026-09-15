from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.krx_night_session_contract_service import (
    ChangeReferenceType,
    NightMarketState,
    krx_night_market_state,
    quote_from_human_acceptance_fixture,
    reference_comparisons_conflict,
    render_krx_night_futures_shadow,
    same_contract_night_return,
)
from app.services.night_futures_session_mapping_service import KST


FIXTURE_PATH = Path("fixtures/20260905-kiwoom-kospi200-night-futures-fixture.json")


def _fixture() -> dict[str, object]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _closed_quote():
    return quote_from_human_acceptance_fixture(
        _fixture(),
        observed_at=datetime(2026, 9, 5, 6, 1, tzinfo=KST),
    )


def test_night_session_crosses_midnight_and_preserves_business_date() -> None:
    quote = _closed_quote()

    assert quote.session_business_date == date(2026, 9, 4)
    assert quote.session_start_kst == datetime(2026, 9, 4, 18, 0, tzinfo=KST)
    assert quote.session_end_kst == datetime(2026, 9, 5, 6, 0, tzinfo=KST)
    assert quote.market_state == NightMarketState.CLOSED


def test_market_state_handles_cross_midnight_weekend_and_holiday() -> None:
    assert krx_night_market_state(datetime(2026, 9, 4, 23, 0, tzinfo=KST)) == (
        NightMarketState.OPEN,
        date(2026, 9, 4),
    )
    assert krx_night_market_state(datetime(2026, 9, 5, 1, 0, tzinfo=KST)) == (
        NightMarketState.OPEN,
        date(2026, 9, 4),
    )
    assert krx_night_market_state(datetime(2026, 9, 5, 22, 0, tzinfo=KST)) == (
        NightMarketState.CLOSED,
        None,
    )
    assert krx_night_market_state(datetime(2026, 9, 24, 20, 0, tzinfo=KST)) == (
        NightMarketState.CLOSED,
        None,
    )


def test_kiwoom_acceptance_fixture_preserves_same_session_ohlcv_and_contract() -> None:
    quote = _closed_quote()

    assert quote.contract_month == "202609"
    assert quote.open == Decimal("1055.65")
    assert quote.high == Decimal("1097.65")
    assert quote.low == Decimal("1043.85")
    assert quote.last == Decimal("1093.9")
    assert quote.volume == 32666


def test_kiwoom_acceptance_fixture_preserves_historical_session_identity() -> None:
    rows = _fixture()["historical_sessions"]

    assert [row["date"] for row in rows] == [
        "2026-08-28",
        "2026-08-31",
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
        "2026-09-04",
    ]
    assert rows[-2]["close"] == 1049.05
    assert rows[-1] == {
        "date": "2026-09-04",
        "open": 1055.65,
        "high": 1097.65,
        "low": 1043.85,
        "close": 1093.9,
        "volume": 32666,
    }


def test_header_and_prior_night_references_are_distinct_not_conflicting() -> None:
    quote = _closed_quote()
    header, prior = quote.comparisons

    assert header.reference_type == ChangeReferenceType.UNKNOWN
    assert header.reference_price == Decimal("1052.5")
    assert header.change == Decimal("41.40")
    assert header.change_pct == Decimal("3.93")
    assert header.source_semantic_explicit is False
    assert prior.reference_type == ChangeReferenceType.PRIOR_NIGHT_CLOSE
    assert prior.reference_price == Decimal("1049.05")
    assert prior.change == Decimal("44.85")
    assert prior.change_pct == Decimal("4.28")
    assert reference_comparisons_conflict(quote.comparisons) is False


def test_cross_contract_raw_return_is_forbidden() -> None:
    current = _closed_quote()
    prior = current.model_copy(update={"contract_month": "202606"})

    with pytest.raises(ValueError, match="cross_contract_raw_return_forbidden"):
        same_contract_night_return(current=current, prior=prior)


def test_same_contract_return_remains_typed() -> None:
    current = _closed_quote()
    prior = current.model_copy(
        update={
            "session_business_date": date(2026, 9, 3),
            "last": Decimal("1049.05"),
        }
    )

    comparison = same_contract_night_return(current=current, prior=prior)

    assert comparison.reference_type == ChangeReferenceType.PRIOR_NIGHT_CLOSE
    assert comparison.change == Decimal("44.85")
    assert comparison.change_pct == Decimal("4.28")


def test_closed_or_stale_quote_never_renders_as_live() -> None:
    quote = _closed_quote()
    rendered = render_krx_night_futures_shadow(
        quote,
        rendered_at=datetime(2026, 9, 5, 22, 0, tzinfo=KST),
    )

    assert "최근 KOSPI200 야간선물" in rendered
    assert "9/4 야간 세션 종가 1,093.90" in rendered
    assert "202609 계약" in rendered
    assert "전 야간 종가 대비 +4.28%" in rendered
    assert "+3.93%" not in rendered
    assert "현재 실시간" not in rendered


def test_unknown_reference_type_cannot_be_promoted_by_arithmetic() -> None:
    header = _closed_quote().comparisons[0]

    assert header.reference_type == ChangeReferenceType.UNKNOWN
    assert header.source_semantic_explicit is False
