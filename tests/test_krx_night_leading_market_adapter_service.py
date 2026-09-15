from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.krx_night_leading_market_adapter_service import (
    adapt_krx_night_quote_to_leading_market,
)
from app.services.krx_night_session_contract_service import (
    KrxNightFuturesSessionQuote,
    NightMarketState,
    RollState,
    krx_night_session_window,
    quote_from_human_acceptance_fixture,
)
from app.services.leading_market_snapshot_service import render_leading_market_block
from app.services.night_futures_session_mapping_service import KST


FIXTURE_PATH = Path("fixtures/20260905-kiwoom-kospi200-night-futures-fixture.json")


def _open_quote():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return quote_from_human_acceptance_fixture(
        fixture,
        observed_at=datetime(2026, 9, 4, 23, 0, tzinfo=KST),
    )


def test_historical_contract_maps_to_current_leading_market_snapshot() -> None:
    quote = _open_quote()
    collected_at = quote.observed_at + timedelta(seconds=30)

    context = adapt_krx_night_quote_to_leading_market(
        quote,
        collected_at=collected_at,
        allow_human_fixture=True,
    )
    rendered = render_leading_market_block(
        context.snapshot,
        context.source_contract,
        now=collected_at,
    )

    observation = context.snapshot.observations[0]
    assert observation.instrument_id == "XKRX:KOSPI200:FUTURES"
    assert observation.reference_basis == "PRIOR_COMPARABLE_NIGHT_CLOSE"
    assert observation.change_pct == 4.28
    assert rendered.status == "VISIBLE"
    assert "KOSPI200 야간선물 +4.28%" in rendered.text


@pytest.mark.parametrize("session_date", ("2026-09-01", "2026-09-02", "2026-09-03"))
def test_historical_sessions_replay_into_level_only_snapshot(session_date: str) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    row = next(item for item in fixture["historical_sessions"] if item["date"] == session_date)
    business_date = date.fromisoformat(session_date)
    start, end = krx_night_session_window(business_date)
    observed_at = datetime.combine(
        business_date,
        datetime.min.time().replace(hour=23),
        tzinfo=KST,
    )
    quote = KrxNightFuturesSessionQuote(
        contract_month="202609",
        session_business_date=business_date,
        session_start_kst=start,
        session_end_kst=end,
        observed_at=observed_at,
        market_state=NightMarketState.OPEN,
        open=Decimal(str(row["open"])),
        high=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        last=Decimal(str(row["close"])),
        volume=int(row["volume"]),
        source="frozen Kiwoom historical acceptance fixture",
        source_quality="HUMAN_FIXTURE",
        is_delayed=None,
        stale_reason=None,
        last_trading_date=None,
        days_to_expiry=None,
        roll_state=RollState.UNKNOWN,
    )
    collected_at = observed_at + timedelta(seconds=30)

    context = adapt_krx_night_quote_to_leading_market(
        quote,
        collected_at=collected_at,
        allow_human_fixture=True,
    )
    rendered = render_leading_market_block(
        context.snapshot,
        context.source_contract,
        now=collected_at,
    )

    assert rendered.status == "VISIBLE"
    assert session_date in context.snapshot.observations[0].session_id
    assert context.snapshot.observations[0].current_price == float(row["close"])
    assert context.snapshot.observations[0].change_pct is None
    assert "%" not in rendered.text


def test_unknown_reference_is_not_promoted_and_level_only_is_rendered() -> None:
    quote = _open_quote().model_copy(update={"comparisons": (_open_quote().comparisons[0],)})
    collected_at = quote.observed_at + timedelta(seconds=30)

    context = adapt_krx_night_quote_to_leading_market(
        quote,
        collected_at=collected_at,
        allow_human_fixture=True,
    )
    rendered = render_leading_market_block(
        context.snapshot,
        context.source_contract,
        now=collected_at,
    )

    observation = context.snapshot.observations[0]
    assert observation.reference_price is None
    assert observation.change_pct is None
    assert "1,093.90" in rendered.text
    assert "%" not in rendered.text


def test_human_fixture_requires_explicit_local_proof_opt_in() -> None:
    quote = _open_quote()

    with pytest.raises(ValueError, match="krx_night_human_fixture_not_runtime_eligible"):
        adapt_krx_night_quote_to_leading_market(
            quote,
            collected_at=quote.observed_at + timedelta(seconds=30),
        )


def test_adapter_has_no_fundamental_or_holder_output_surface() -> None:
    quote = _open_quote()
    context = adapt_krx_night_quote_to_leading_market(
        quote,
        collected_at=quote.observed_at + timedelta(seconds=30),
        allow_human_fixture=True,
    )
    payload = context.model_dump(mode="json")

    assert "business_delta" not in payload
    assert "holder_axis" not in payload
    assert "fundamental_direction" not in payload
