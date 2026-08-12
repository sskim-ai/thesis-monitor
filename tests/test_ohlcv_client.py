import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.schemas.thesis import PriceContext
from app.services.ohlcv_client import OhlcvClient, _investor_supply_context


@pytest.mark.anyio
async def test_ohlcv_client_requests_each_period_and_accepts_shorter_history() -> None:
    requested: dict[str, int] = {}
    actual_counts = {"daily": 420, "weekly": 240, "monthly": 84}

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        count = int(request.url.params["count"])
        requested[period] = count
        bars = [
            {
                "date": f"2026-01-{(index % 28) + 1:02d}",
                "open": 100 + index,
                "high": 102 + index,
                "low": 98 + index,
                "close": 101 + index,
                "volume": 1000,
                "indicators": {},
            }
            for index in range(actual_counts[period])
        ]
        return httpx.Response(
            200,
            content=json.dumps({"periods": {period: bars}}).encode(),
            headers={"Content-Type": "application/json"},
        )

    context = await OhlcvClient(transport=httpx.MockTransport(handler)).fetch_price_context("NVDA")

    assert requested == {"daily": 500, "weekly": 300, "monthly": 100}
    assert context.available is True
    assert context.periods["daily"].actual_count == 420
    assert context.periods["daily"].previous_close == 519
    assert context.periods["daily"].latest_close == 520
    assert context.periods["daily"].latest_high == 521
    assert context.periods["daily"].latest_low == 517
    assert context.periods["weekly"].actual_count == 240
    assert context.periods["monthly"].actual_count == 84


@pytest.mark.anyio
async def test_us_premarket_uses_latest_completed_regular_close_date() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        bars = [
            {
                "date": "2026-08-11",
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100,
                "volume": 1_000,
                "indicators": {},
            }
        ]
        return httpx.Response(200, json={"periods": {period: bars}})

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context(
        "GOOGL",
        as_of=datetime(2026, 8, 11, 17, 20, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert context.decision.market_session == "pre_market"
    assert context.decision.price_basis == "close"
    assert context.decision.exchange_trade_date == "2026-08-10"
    assert context.decision.latest_completed_regular_session_date == "2026-08-10"


@pytest.mark.anyio
async def test_kr_close_run_uses_same_day_completed_close() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        return httpx.Response(
            200,
            json={
                "periods": {
                    period: [
                        {
                            "date": "2026-08-12",
                            "open": 100,
                            "high": 101,
                            "low": 99,
                            "close": 100,
                            "volume": 1_000,
                        }
                    ]
                }
            },
        )

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context(
        "005930",
        as_of=datetime(2026, 8, 12, 16, 5, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert context.decision.market_session == "after_hours"
    assert context.decision.assessment_state == "final"
    assert context.decision.exchange_trade_date == "2026-08-12"
    assert context.decision.latest_completed_regular_session_date == "2026-08-12"
    assert context.decision.price_basis == "close"


@pytest.mark.anyio
async def test_latest_daily_bar_maps_investor_supply_without_using_weekly_summary() -> None:
    sample = {
        "date": "2026-08-12",
        "close": 120,
        "foreign_net_buy_qty": -153_000,
        "institution_net_buy_qty": 205_000,
        "individual_net_buy_qty": 0,
        "foreign_net_buy_qty_5": -6_981_054,
        "institution_net_buy_qty_5": -34_386,
        "individual_net_buy_qty_5": 5_829_492,
        "foreign_net_buy_qty_20": -8_108_432,
        "institution_net_buy_qty_20": -11_716_549,
        "individual_net_buy_qty_20": 18_403_424,
        "foreign_holding_qty": 2_724_356_859,
        "foreign_holding_ratio": 46.60,
        "indicators": {
            "supply_score": 29,
            "supply_quality": "distribution",
            "supply_quality_detail": "foreign_holding_up_net_sell",
            "supply_primary_signal": "foreign_exit_retail_absorption",
            "supply_validation_status": "validated",
            "supply_confidence": "high",
            "investor_net_buy_20_validation_status": "validated",
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        if period == "daily":
            bars = [sample]
        else:
            bars = [
                {
                    "date": "2026-08-12",
                    "close": 120,
                    "foreign_net_buy_qty": 999_999,
                    "supply_score": 99,
                }
            ]
        return httpx.Response(200, json={"periods": {period: bars}})

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context("005930")

    assert context.supply.available is True
    assert context.supply.as_of_date == "2026-08-12"
    assert context.supply.foreign_net_buy_qty == -153_000
    assert context.supply.institution_net_buy_qty_20 == -11_716_549
    assert context.supply.foreign_holding_qty == 2_724_356_859
    assert context.supply.foreign_holding_ratio == 46.6
    assert context.supply.score == 29
    assert context.supply.quality == "distribution"
    assert context.supply.primary_signal == "foreign_exit_retail_absorption"
    assert context.supply.validation_status == "validated"


def test_investor_supply_ignores_non_finite_values_and_keeps_actual_date() -> None:
    supply = _investor_supply_context(
        [
            {
                "date": "2026-08-11",
                "foreign_net_buy_qty": 10,
                "supply_score": 20,
            },
            {
                "date": "2026-08-12",
                "foreign_net_buy_qty": math.nan,
                "institution_net_buy_qty": math.inf,
                "individual_net_buy_qty": -math.inf,
                "supply_validation_status": "failed",
            },
        ]
    )

    assert supply.available is True
    assert supply.as_of_date == "2026-08-11"
    assert supply.foreign_net_buy_qty == 10
    assert supply.institution_net_buy_qty is None
    assert supply.individual_net_buy_qty is None
    assert supply.validation_status is None


def test_investor_supply_survives_price_context_json_round_trip() -> None:
    original = PriceContext(
        available=True,
        supply=_investor_supply_context(
            [
                {
                    "date": "2026-08-12",
                    "foreign_net_buy_qty": -153_000,
                    "supply_score": 29,
                    "supply_quality": "distribution",
                }
            ]
        ),
    )

    restored = PriceContext.model_validate_json(original.model_dump_json())

    assert restored.supply.available is True
    assert restored.supply.as_of_date == "2026-08-12"
    assert restored.supply.foreign_net_buy_qty == -153_000
    assert restored.supply.score == 29


@pytest.mark.anyio
async def test_nested_ohlcv_supply_contract_is_mapped_from_latest_daily_bar() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        bar = {"date": "2026-08-12", "close": 120}
        payload: dict[str, object] = {"periods": {period: [bar]}}
        if period == "daily":
            bar["investor_flow"] = {
                "foreign_net_buy_qty": -153_000,
                "institution_net_buy_qty_5": -34_386,
                "individual_net_buy_qty_20": 18_403_424,
                "foreign_holding_qty": 2_724_356_859,
                "foreign_holding_ratio": 46.6,
                "investor_net_buy_20_validation_status": "validated",
            }
            payload["supply_demand"] = {
                "score": 29,
                "quality": "distribution",
                "primary_signal": "foreign_exit_retail_absorption",
                "confidence": "high",
                "validation_status": "validated",
                "foreign_flow_direction_20": "distribution",
                "foreign_exit_retail_absorption": True,
            }
        return httpx.Response(200, json=payload)

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context("005930")

    assert context.supply.available is True
    assert context.supply.foreign_net_buy_qty == -153_000
    assert context.supply.institution_net_buy_qty_5 == -34_386
    assert context.supply.individual_net_buy_qty_20 == 18_403_424
    assert context.supply.foreign_holding_qty == 2_724_356_859
    assert context.supply.score == 29
    assert context.supply.quality == "distribution"
    assert context.supply.primary_signal == "foreign_exit_retail_absorption"
    assert context.supply.foreign_flow_direction_20 == "distribution"
    assert context.supply.signals == ["foreign_exit_retail_absorption"]
