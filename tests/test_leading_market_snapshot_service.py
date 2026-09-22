from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.services.leading_market_snapshot_service import (
    LeadingMarketObservation,
    LeadingMarketSessionState,
    LeadingMarketSnapshot,
    LeadingMarketSourceContract,
    leading_market_block_from_context,
    render_leading_market_block,
)


NOW = datetime(2026, 9, 15, 0, 30, tzinfo=UTC)


def _source(*, market: str = "us") -> LeadingMarketSourceContract:
    return LeadingMarketSourceContract(
        contract_id=f"fixture-{market}-v1",
        provider="fixture-official",
        market=market,
        instrument_ids=("ES", "NQ") if market == "us" else ("KOSPI200-NIGHT",),
        reference_basis="PRIOR_OFFICIAL_SETTLEMENT",
        active_max_age_seconds=120,
        preopen_max_age_seconds=300,
        source_timezone="America/Chicago" if market == "us" else "Asia/Seoul",
        official_or_existing_supported_free=True,
    )


def _observation(
    instrument_id: str = "ES",
    *,
    as_of: datetime | None = None,
) -> LeadingMarketObservation:
    return LeadingMarketObservation(
        instrument_id=instrument_id,
        display_name="S&P 500 선물" if instrument_id == "ES" else "Nasdaq-100 선물",
        provider="fixture-official",
        session_id="2026-09-14-CME-GLOBEX",
        current_price=5010.0,
        reference_price=5000.0,
        change_pct=0.2,
        reference_basis="PRIOR_OFFICIAL_SETTLEMENT",
        as_of=as_of or NOW - timedelta(seconds=30),
        source_timezone="America/Chicago",
        source_document_or_endpoint="official-fixture-endpoint",
    )


def _snapshot(*observations: LeadingMarketObservation) -> LeadingMarketSnapshot:
    return LeadingMarketSnapshot(
        market="us",
        session_state=LeadingMarketSessionState.ACTIVE_FUTURES_SESSION,
        observations=observations or (_observation(),),
        collected_at=NOW - timedelta(seconds=10),
    )


def test_current_snapshot_renders_as_separate_kst_leading_signal() -> None:
    rendered = render_leading_market_block(
        _snapshot(_observation("ES"), _observation("NQ")),
        _source(),
        now=NOW,
    )

    assert rendered.status == "VISIBLE"
    assert rendered.fact_count == 2
    assert "현재 선행시장" in rendered.text
    assert "2026-09-15 09:29 KST" in rendered.text
    assert "완료된 정규장 신호가 아닙니다" in rendered.text


def test_change_must_use_the_declared_futures_reference_basis() -> None:
    payload = _observation().model_dump()
    payload["change_pct"] = 3.0

    with pytest.raises(ValidationError, match="leading_market_change_basis_mismatch"):
        LeadingMarketObservation.model_validate(payload)


def test_level_only_observation_renders_without_fabricated_change() -> None:
    source = _source(market="kr").model_copy(update={"reference_basis": None})
    observation = _observation("KOSPI200-NIGHT").model_copy(
        update={
            "display_name": "KOSPI200 야간선물",
            "current_price": 1093.9,
            "reference_price": None,
            "change_pct": None,
            "reference_basis": None,
            "source_timezone": "Asia/Seoul",
        }
    )
    snapshot = LeadingMarketSnapshot(
        market="kr",
        session_state=LeadingMarketSessionState.ACTIVE_FUTURES_SESSION,
        observations=(observation,),
        collected_at=NOW - timedelta(seconds=10),
    )

    rendered = render_leading_market_block(snapshot, source, now=NOW)

    assert rendered.status == "VISIBLE"
    assert "KOSPI200 야간선물 1,093.90" in rendered.text
    assert "%" not in rendered.text


def test_partial_comparison_is_rejected() -> None:
    payload = _observation().model_dump()
    payload["change_pct"] = None

    with pytest.raises(ValidationError, match="leading_market_partial_comparison_forbidden"):
        LeadingMarketObservation.model_validate(payload)


def test_stale_and_closed_sessions_never_render_as_current() -> None:
    stale = _snapshot(_observation(as_of=NOW - timedelta(minutes=10)))
    closed = LeadingMarketSnapshot(
        market="us",
        session_state=LeadingMarketSessionState.CLOSED_NO_CURRENT_FUTURES,
        observations=(),
        collected_at=NOW,
    )

    stale_render = render_leading_market_block(stale, _source(), now=NOW)
    closed_render = render_leading_market_block(closed, _source(), now=NOW)

    assert stale_render.status == "OMITTED_STALE"
    assert stale_render.text == ""
    assert closed_render.status == "OMITTED_CLOSED"
    assert closed_render.text == ""


def test_future_or_unapproved_source_is_invalid_and_omitted() -> None:
    future = _snapshot(_observation(as_of=NOW + timedelta(seconds=1)))
    source = _source().model_copy(update={"official_or_existing_supported_free": False})

    rendered = render_leading_market_block(future, source, now=NOW)

    assert rendered.status == "INVALID"
    assert rendered.text == ""
    assert "leading_market_source_not_eligible" in rendered.validation.errors
    assert "leading_market_future_observation:ES" in rendered.validation.errors


def test_context_adapter_is_market_bound_and_deterministic() -> None:
    payload = {
        "leading_market_context": {
            "source_contract": _source().model_dump(mode="json"),
            "snapshot": _snapshot().model_dump(mode="json"),
            "validation_as_of": NOW.isoformat(),
        }
    }

    first = leading_market_block_from_context(payload, expected_market="us")
    second = leading_market_block_from_context(payload, expected_market="us")

    assert first == second
    with pytest.raises(ValueError, match="leading_market_render_market_mismatch"):
        leading_market_block_from_context(payload, expected_market="kr")
