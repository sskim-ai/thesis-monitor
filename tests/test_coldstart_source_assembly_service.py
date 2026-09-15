from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta

import httpx

from app.schemas.thesis import ChartContext, PriceContext, PriceDecisionContext
from app.services.coldstart_source_assembly_service import (
    SourceAssemblyStatus,
    assemble_research_packet,
)
from app.services.packet_owned_technical_context_service import (
    build_packet_owned_technical_context,
)
from scripts.unseen_source_assembly_coldstart import (
    FIXTURE_TICKERS,
    RETIRED_TICKERS,
    ranked_candidates,
)


AS_OF = datetime(2026, 9, 6, 4, 0, tzinfo=UTC)


def _bars(count: int, end: date) -> list[dict[str, object]]:
    start = end - timedelta(days=count - 1)
    return [
        {
            "date": (start + timedelta(days=index)).isoformat(),
            "open": 90 + index,
            "high": 92 + index,
            "low": 89 + index,
            "close": 91 + index,
            "volume": 1_000 + index,
            "bar_state": "FINAL",
        }
        for index in range(count)
    ]


def _price_context(ticker: str, *, price_as_of: date = date(2026, 9, 4)) -> PriceContext:
    periods = {
        "daily": _bars(420, price_as_of),
        "weekly": _bars(180, price_as_of),
        "monthly": _bars(80, price_as_of),
    }
    technical = build_packet_owned_technical_context(
        ticker=ticker,
        market="kr" if ticker.isdigit() else "us",
        session="closed",
        as_of=AS_OF.isoformat(),
        periods=periods,
        cutoff=price_as_of,
        expected_daily_completed=price_as_of.isoformat(),
        acquisition={"request_count": 4, "success_count": 4},
    )
    context = PriceContext(
        available=True,
        decision=PriceDecisionContext(
            current_price=510.0,
            currency="KRW" if ticker.isdigit() else "USD",
            price_as_of=price_as_of.isoformat(),
            exchange_trade_date=price_as_of.isoformat(),
            latest_completed_regular_session_date=price_as_of.isoformat(),
            price_basis="close",
            market_session="closed",
            assessment_state="final",
        ),
        chart=ChartContext(
            available=True,
            as_of_date=price_as_of.isoformat(),
            quality="fresh",
            price_basis="adjusted_close",
            structure={
                "as_of_date": price_as_of.isoformat(),
                "nearest_supports": [
                    {
                        "zone_low": 470.0,
                        "zone_high": 480.0,
                        "timeframe": "weekly",
                        "strength": "Strong",
                    }
                ],
                "nearest_resistance": [
                    {
                        "zone_low": 530.0,
                        "zone_high": 540.0,
                        "timeframe": "weekly",
                        "strength": "Medium",
                    }
                ],
            },
        ),
    )
    context.set_technical_context_payload(technical.model_dump(mode="json"))
    return context


def _unavailable_price_context(ticker: str) -> PriceContext:
    technical = build_packet_owned_technical_context(
        ticker=ticker,
        market="kr" if ticker.isdigit() else "us",
        session="closed",
        as_of=AS_OF.isoformat(),
        periods={},
        cutoff=date(2026, 9, 4),
        expected_daily_completed="2026-09-04",
        acquisition={
            "request_count": 4,
            "success_count": 0,
            "server_error_count": 4,
            "failure_classes": ("HTTP_502",),
        },
    )
    context = PriceContext(
        available=False,
        decision=PriceDecisionContext(
            currency="KRW" if ticker.isdigit() else "USD",
            price_basis="unavailable",
            market_session="closed",
            assessment_state="final",
        ),
        chart=ChartContext(available=False, quality="unavailable"),
        warnings=["daily: HTTPStatusError", "weekly: HTTPStatusError"],
    )
    context.set_technical_context_payload(technical.model_dump(mode="json"))
    return context


class _PriceClient:
    def __init__(self, context: PriceContext | Exception) -> None:
        self.context = context

    async def fetch_price_context(self, *_args, **_kwargs) -> PriceContext:
        if isinstance(self.context, Exception):
            raise self.context
        return self.context


def _identity(ticker: str = "AAPL") -> dict[str, object]:
    return {
        "ticker": ticker,
        "company_name": "Apple Inc.",
        "market": "us",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "security_type": "common_stock",
        "source": "approved_fixture_identity",
        "source_as_of": "2026-09-06",
    }


def test_coldstart_assembly_is_archive_independent_and_deterministic() -> None:
    async def assemble():
        return await assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=_identity(),
            price_client=_PriceClient(_price_context("AAPL")),
        )

    first = asyncio.run(assemble())
    second = asyncio.run(assemble())

    assert first.status == SourceAssemblyStatus.ASSEMBLED
    assert first.packet_sha256 == second.packet_sha256
    assert first.deterministic_base_context_sha256 == second.deterministic_base_context_sha256
    assert first.production_db_mutation == 0
    assert first.monitoring_registration == 0
    assert first.ai_judgment_calls == 0
    assert first.packet is not None
    source = first.packet["source_assembly"]
    assert source["monitoring_baseline_required"] == 0
    assert source["stored_monitoring_state_required"] == 0
    evidence = first.decision_evidence_packet()
    assert evidence.ticker == "AAPL"
    assert evidence.evidence


def test_identity_mismatch_fails_before_price_source_call() -> None:
    result = asyncio.run(
        assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=_identity("MSFT"),
            price_client=_PriceClient(_price_context("AAPL")),
        )
    )

    assert result.status == SourceAssemblyStatus.IDENTITY_UNRESOLVED
    assert result.provider_audit["ohlcv"] == "not_called"
    assert result.packet is None


def test_provider_failure_is_not_relabelled_as_archive_absence() -> None:
    result = asyncio.run(
        assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=_identity(),
            price_client=_PriceClient(httpx.ConnectError("offline")),
        )
    )

    assert result.status == SourceAssemblyStatus.OBJECTIVE_SOURCE_LIMIT
    assert result.provider_audit == {"identity": "success", "ohlcv": "failed"}
    assert result.packet is None


def test_future_price_fact_is_blocked() -> None:
    result = asyncio.run(
        assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=_identity(),
            price_client=_PriceClient(
                _price_context("AAPL", price_as_of=date(2026, 9, 7))
            ),
        )
    )

    assert result.status == SourceAssemblyStatus.VALIDATION_BLOCK
    assert "future_price_fact" in result.validation_errors


def test_safe_price_unavailable_preserves_directional_packet_boundary() -> None:
    result = asyncio.run(
        assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=_identity(),
            price_client=_PriceClient(_unavailable_price_context("AAPL")),
        )
    )

    assert result.status == SourceAssemblyStatus.ASSEMBLED
    assert result.validation_errors == ()
    assert result.packet is not None
    stock = result.packet["stocks"][0]
    assert stock["current_price_context"]["availability"] == "unavailable"
    assert {fact["fact_id"] for fact in stock["fact_catalog"]} == {
        "security_identity:current",
        "industry:classification",
    }
    source = result.packet["source_assembly"]
    assert source["price_context_readiness"] == "UNAVAILABLE"
    assert source["price_timing_readiness"] == "UNAVAILABLE_SAFE"
    assert source["directional_fundamental_readiness"] == (
        "PENDING_FUNDAMENTAL_ENRICHMENT"
    )

    evidence = result.decision_evidence_packet()
    assert evidence.technical_context_status == "UNAVAILABLE"
    assert all(
        ref.category not in {"PRICE_STRUCTURE", "TECHNICAL_FEATURE"} for ref in evidence.evidence
    )


def test_incomplete_price_context_remains_fail_closed() -> None:
    context = _unavailable_price_context("AAPL")
    context.decision.price_as_of = "2026-09-04"

    result = asyncio.run(
        assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=_identity(),
            price_client=_PriceClient(context),
        )
    )

    assert result.status == SourceAssemblyStatus.VALIDATION_BLOCK
    assert "price_context_incomplete" in result.validation_errors


def test_unsupported_security_type_is_fail_closed() -> None:
    identity = {**_identity(), "security_type": "exchange_traded_fund"}
    result = asyncio.run(
        assemble_research_packet(
            "AAPL",
            AS_OF,
            identity=identity,
            price_client=_PriceClient(_price_context("AAPL")),
        )
    )

    assert result.status == SourceAssemblyStatus.UNSUPPORTED_SECURITY
    assert result.validation_errors == ("unsupported_security_type",)


def test_unseen_ranking_is_deterministic_and_excludes_prior_subjects() -> None:
    rows = [
        {
            "ticker": ticker,
            "market": "kr" if ticker.isdigit() else "us",
            "sector": "sector-a" if index % 2 else "sector-b",
        }
        for index, ticker in enumerate(
            (*RETIRED_TICKERS[:2], *FIXTURE_TICKERS[:2], "AAPL", "AMD", "111111", "222222")
        )
    ]

    first = ranked_candidates(rows)
    second = ranked_candidates(list(reversed(rows)))
    tickers = [str(row["ticker"]) for row in first]

    assert first == second
    assert set(tickers) == {"AAPL", "AMD", "111111", "222222"}
    assert not set(tickers) & set(RETIRED_TICKERS)
    assert not set(tickers) & set(FIXTURE_TICKERS)
