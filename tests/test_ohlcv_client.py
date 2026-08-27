import json
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.schemas.thesis import PriceContext
from app.services.ohlcv_client import OhlcvClient, _investor_supply_context


KR_PRICE_STRUCTURE_CONTROLS = (
    "000660",
    "003690",
    "005490",
    "005930",
    "010120",
    "012450",
    "086280",
)


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
async def test_historical_valuation_uses_separate_unadjusted_weekly_prices() -> None:
    requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        adjusted = request.url.params["adjusted"]
        requests.append((period, adjusted))
        close = 55_400 if period == "weekly" and adjusted == "false" else 11_080
        return httpx.Response(
            200,
            json={"periods": {period: [{"date": "2020-11-16", "close": close}]}},
        )

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context("010120")

    assert ("weekly", "true") in requests
    assert ("weekly", "false") in requests
    assert context.periods["weekly"].latest_close == 11_080
    assert context.valuation_history[0].close == 55_400


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
async def test_kr_price_structure_gate_requests_long_history_and_builds_sidecar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[tuple[str, int, str]] = []
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        count = int(request.url.params["count"])
        adjusted = request.url.params["adjusted"]
        requests.append((period, count, adjusted))
        return httpx.Response(
            200,
            json={
                "periods": {
                    period: [
                        {
                            "date": "2026-08-27",
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

    def fake_sidecar(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"contract": "kr-price-structure-runtime-context-v1"}

    monkeypatch.setattr(
        "app.services.ohlcv_client.build_kr_price_structure_runtime_context",
        fake_sidecar,
    )
    client = OhlcvClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(client.settings, "kr_price_structure_v3_enabled", True)

    context = await client.fetch_price_context(
        "005930",
        as_of=datetime(2026, 8, 27, 16, 5, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert ("daily", 1000, "true") in requests
    assert ("weekly", 600, "true") in requests
    assert ("monthly", 300, "true") in requests
    assert context.periods["daily"].requested_count == 1200
    assert captured["ticker"] == "005930"
    assert captured["cutoff"] == "2026-08-27"
    assert captured["provider_limit"] == 1000
    assert context.chart.structure["price_structure_v3"] == {
        "contract": "kr-price-structure-runtime-context-v1"
    }


@pytest.mark.anyio
@pytest.mark.parametrize("ticker", KR_PRICE_STRUCTURE_CONTROLS)
async def test_kr_price_structure_controls_respect_provider_count_limit(
    ticker: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[tuple[str, int]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        count = int(request.url.params["count"])
        requests.append((period, count))
        if count > 1000:
            return httpx.Response(422, json={"detail": "count exceeds provider limit"})
        return httpx.Response(
            200,
            json={
                "periods": {
                    period: [
                        {
                            "date": "2026-08-27",
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

    monkeypatch.setattr(
        "app.services.ohlcv_client.build_kr_price_structure_runtime_context",
        lambda **_: {"contract": "kr-price-structure-runtime-context-v1"},
    )
    client = OhlcvClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(client.settings, "kr_price_structure_v3_enabled", True)

    context = await client.fetch_price_context(
        ticker,
        as_of=datetime(2026, 8, 27, 16, 5, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert ("daily", 1000) in requests
    assert all(count <= 1000 for _, count in requests)
    assert context.periods["daily"].requested_count == 1200
    assert context.periods["daily"].actual_count == 1


@pytest.mark.anyio
async def test_kr_holiday_keeps_latest_exchange_session_chart_fresh() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        return httpx.Response(
            200,
            json={
                "periods": {
                    period: [
                        {
                            "date": "2026-08-14",
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
        "086280",
        as_of=datetime(2026, 8, 17, 16, 5, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert context.decision.market_session == "closed"
    assert context.decision.exchange_trade_date == "2026-08-14"
    assert context.decision.latest_completed_regular_session_date == "2026-08-14"
    assert context.chart.quality == "fresh"
    assert context.chart.timeframes["daily"].quality == "fresh"


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
        "other_corp_net_buy_qty": 0,
        "other_corp_net_buy_qty_5": 0,
        "other_corp_net_buy_qty_20": 0,
        "domestic_foreign_net_buy_qty": 0,
        "domestic_foreign_net_buy_qty_5": 0,
        "domestic_foreign_net_buy_qty_20": 0,
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
    reconciliation = context.supply.reconciliation_payload()
    assert reconciliation["provider_primary_signal"] == "foreign_exit_retail_absorption"
    assert reconciliation["signal_basis_window"] == "20d"
    assert reconciliation["attribution_safe"] is True
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
async def test_chart_context_uses_provider_indicators_and_preserves_price_basis() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        adjusted = request.url.params["adjusted"]
        if adjusted == "false":
            return httpx.Response(
                200,
                json={"periods": {period: [{"date": "2026-08-12", "close": 125}]}},
            )
        indicators = {
            "VOLUME_RATIO_20": 1.25,
            "RSI14": 61.4,
            "MACD": 3.2,
            "MACD_SIGNAL": 2.7,
            "MACD_HIST": 0.5,
        }
        if period == "daily":
            indicators.update(
                {
                    "BB_36_1.541_UPPER": 110,
                    "BB_60_1.541_UPPER": 112,
                    "BB_50_2.25_UPPER": 114,
                    "BB_144_1.541_UPPER": 116,
                    "BB_288_1.541_UPPER": 118,
                    "BB_300_3.33_UPPER": 120,
                }
            )
        return httpx.Response(
            200,
            json={
                "periods": {
                    period: [
                        {
                            "date": "2026-08-12",
                            "open": 100,
                            "high": 110,
                            "low": 95,
                            "close": 105,
                            "volume": 1_000,
                            "value": 105_000,
                            "indicators": indicators,
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

    daily = context.chart.timeframes["daily"]
    assert context.chart.available is True
    assert context.chart.source == "ohlcv_analyst"
    assert context.chart.quality == "fresh"
    assert context.chart.price_basis == "adjusted_close"
    assert daily.candle.body_pct == 5.0
    assert daily.candle.range_pct == 15.0
    assert daily.candle.close_location_pct == pytest.approx(66.666667)
    assert daily.bollinger_upper["3_month"] == 110
    assert daily.bollinger_upper["54_month"] == 120
    assert daily.bollinger_distance_pct["3_month"] == pytest.approx(-4.5455)
    assert daily.volume_ratio_20 == 1.25
    assert daily.rsi_14 == 61.4
    assert daily.macd_histogram == 0.5
    assert context.valuation_history[0].close == 125
    assert context.chart.structure["algorithm_version"] == "ohlcv-structure-v2"
    assert "support_resistance" in context.chart.unavailable_fields
    assert "atr" in context.chart.unavailable_fields
    assert "elliott_wave" in context.chart.unavailable_fields


@pytest.mark.anyio
async def test_chart_context_populates_structure_from_sufficient_adjusted_history() -> None:
    counts = {"daily": 240, "weekly": 100, "monthly": 60}
    spacing = {"daily": 1, "weekly": 7, "monthly": 30}

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        count = counts[period]
        bars = []
        for index in range(count):
            cycle = 16 if period == "daily" else 10 if period == "weekly" else 8
            center = 100 + index * 0.03 + 14 * math.sin(index * 2 * math.pi / cycle)
            bars.append(
                {
                    "date": (
                        datetime(2018, 1, 1) + timedelta(days=index * spacing[period])
                    ).date().isoformat(),
                    "open": center - 0.5,
                    "high": center + 2,
                    "low": center - 2,
                    "close": center + 0.5,
                    "volume": 1_000 + (index % cycle) * 50,
                    "indicators": {"VOLUME_RATIO_20": 1.0},
                }
            )
        return httpx.Response(200, json={"periods": {period: bars}})

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context("NVDA")

    structure = context.chart.structure
    assert structure["algorithm_version"] == "ohlcv-structure-v2"
    assert structure["availability"]["atr"] is True
    assert structure["availability"]["support_resistance"] is True
    assert structure["availability"]["major_swings"] is True
    assert structure["atr"]["daily"]["method"] == "wilder_recursive"
    assert structure["major_swings"]["primary_timeframe"] == "weekly"
    assert (
        structure["local_pivots"]["weekly"]
        != structure["major_swings"]["by_timeframe"]["weekly"]
    )
    assert context.chart.price_basis == "adjusted_close"
    assert "atr" not in context.chart.unavailable_fields


@pytest.mark.anyio
async def test_chart_context_marks_stale_daily_and_keeps_partial_timeframes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        bars = [] if period in {"weekly", "monthly"} else [
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
        "005930",
        as_of=datetime(2026, 8, 12, 16, 5, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert context.chart.quality == "stale"
    assert context.chart.timeframes["daily"].quality == "stale"
    assert context.chart.timeframes["weekly"].quality == "unavailable"
    assert context.chart.timeframes["monthly"].quality == "unavailable"


def test_chart_context_survives_price_context_json_round_trip() -> None:
    original = PriceContext.model_validate(
        {
            "available": True,
            "chart": {
                "available": True,
                "source": "ohlcv_analyst",
                "as_of_date": "2026-08-12",
                "quality": "fresh",
                "price_basis": "adjusted_close",
                "timeframes": {
                    "daily": {
                        "timeframe": "daily",
                        "as_of_date": "2026-08-12",
                        "quality": "fresh",
                        "candle": {"close": 105},
                        "rsi_14": 61.4,
                    }
                },
            },
        }
    )

    restored = PriceContext.model_validate_json(original.model_dump_json())

    assert restored.chart.source == "ohlcv_analyst"
    assert restored.chart.price_basis == "adjusted_close"
    assert restored.chart.timeframes["daily"].rsi_14 == 61.4


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
    assert context.supply.primary_signal == "unavailable"
    reconciliation = context.supply.reconciliation_payload()
    assert reconciliation["provider_primary_signal"] == "foreign_exit_retail_absorption"
    assert reconciliation["attribution_safe"] is False
    assert context.supply.foreign_flow_direction_20 == "distribution"
    assert context.supply.signals == ["foreign_exit_retail_absorption"]
