import asyncio
from datetime import date, datetime, timezone
import json

import httpx
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.macro.kr_close import (
    previous_kr_close_observation,
    run_kr_close_market_briefing,
)
from app.macro.providers.alpha_vantage_fx import (
    ALPHA_VANTAGE_SOURCE_URL,
    AlphaVantageKrCloseFxProvider,
)
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.models.macro import MacroBriefing, MacroObservation
from app.models.thesis import NotificationDelivery
from app.services.notification_service import _macro_report, queue_macro_notification


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _alpha_payload(currency: str, rate: float) -> dict[str, object]:
    return {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": currency,
            "3. To_Currency Code": "KRW",
            "5. Exchange Rate": str(rate),
            "6. Last Refreshed": "2026-08-12 06:58:00",
            "7. Time Zone": "UTC",
        }
    }


def test_alpha_fx_collects_three_pairs_sequentially_and_scales_100_jpy() -> None:
    requests: list[httpx.Request] = []
    rates = {"USD": 1386.2, "JPY": 9.264, "EUR": 1611.7}

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        currency = request.url.params["from_currency"]
        return httpx.Response(200, json=_alpha_payload(currency, rates[currency]))

    provider = AlphaVantageKrCloseFxProvider(
        transport=httpx.MockTransport(handler), request_interval_seconds=0
    )
    provider.settings = provider.settings.model_copy(
        update={"alpha_vantage_api_key": "secret-alpha-key"}
    )
    result = asyncio.run(provider.collect(datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc)))

    assert [request.url.params["from_currency"] for request in requests] == [
        "USD",
        "JPY",
        "EUR",
    ]
    assert all(request.url.params["function"] == "CURRENCY_EXCHANGE_RATE" for request in requests)
    by_series = {item.series_code: item for item in result.observations}
    assert by_series["USDKRW_KR_CLOSE"].value == 1386.2
    assert by_series["JPYKRW100_KR_CLOSE"].value == pytest.approx(926.4)
    assert by_series["EURKRW_KR_CLOSE"].value == 1611.7
    assert by_series["USDKRW_KR_CLOSE"].observed_at == datetime(
        2026, 8, 12, 6, 58, tzinfo=timezone.utc
    )
    serialized = json.dumps(
        [item.raw_payload | {"source_url": item.source_url} for item in result.observations]
    )
    assert "secret-alpha-key" not in serialized
    assert all(item.source_url == ALPHA_VANTAGE_SOURCE_URL for item in result.observations)


def test_alpha_http_200_information_body_and_one_pair_failure_are_partial() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        currency = request.url.params["from_currency"]
        if currency == "EUR":
            return httpx.Response(200, json={"Information": "API rate limit reached"})
        rate = 1386.2 if currency == "USD" else 9.264
        return httpx.Response(200, json=_alpha_payload(currency, rate))

    provider = AlphaVantageKrCloseFxProvider(
        transport=httpx.MockTransport(handler), request_interval_seconds=0
    )
    provider.settings = provider.settings.model_copy(
        update={"alpha_vantage_api_key": "dummy"}
    )
    result = asyncio.run(provider.collect(datetime(2026, 8, 12, tzinfo=timezone.utc)))

    assert len(result.observations) == 2
    assert result.warnings == ["EUR/KRW:rate_limit"]


class FakeFxProvider:
    name = "alpha_vantage_fx_close"

    def __init__(self, values: dict[str, float]) -> None:
        self.values = values
        self.calls = 0

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        self.calls += 1
        observations = [
            CollectedObservation(
                series_code=series_code,
                category="fx_close",
                observed_at=datetime(2026, 8, 12, 6, 58, tzinfo=timezone.utc),
                value=value,
                unit="KRW",
                frequency="daily",
                market_session="kr_close",
                source_url=ALPHA_VANTAGE_SOURCE_URL,
                raw_payload={
                    "provider_last_refreshed": "2026-08-12 06:58:00",
                    "provider_timezone": "UTC",
                },
            )
            for series_code, value in self.values.items()
        ]
        return MacroProviderResult(provider=self.name, observations=observations)


class FailingFxProvider:
    name = "alpha_vantage_fx_close"

    def __init__(self) -> None:
        self.calls = 0

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        self.calls += 1
        raise RuntimeError("provider unavailable")


def _previous_row(
    series_code: str,
    value: float,
    retrieved_at: datetime,
    key: str,
) -> MacroObservation:
    return MacroObservation(
        dedupe_key=key,
        series_code=series_code,
        category="fx_close",
        provider="alpha_vantage_fx_close",
        observed_at=retrieved_at,
        market_session="kr_close",
        value=value,
        unit="KRW",
        frequency="daily",
        source_url=ALPHA_VANTAGE_SOURCE_URL,
        retrieved_at=retrieved_at,
    )


@pytest.mark.anyio
async def test_kr_close_change_uses_prior_kst_date_and_excludes_same_day() -> None:
    engine = _engine()
    provider = FakeFxProvider(
        {
            "USDKRW_KR_CLOSE": 1386.2,
            "JPYKRW100_KR_CLOSE": 926.4,
            "EURKRW_KR_CLOSE": 1611.7,
        }
    )
    with Session(engine) as session:
        session.add_all(
            [
                _previous_row(
                    "USDKRW_KR_CLOSE",
                    1379.1,
                    datetime(2026, 8, 11, 7, 5, tzinfo=timezone.utc),
                    "prior-usd",
                ),
                _previous_row(
                    "USDKRW_KR_CLOSE",
                    1400.0,
                    datetime(2026, 8, 12, 1, 0, tzinfo=timezone.utc),
                    "same-day-usd",
                ),
            ]
        )
        session.commit()

        result = await run_kr_close_market_briefing(
            session,
            date(2026, 8, 12),
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=provider,
            queue_notifications=False,
            dispatch_notifications=False,
        )

        assert result.status == "ready"
        current = session.exec(
            select(MacroObservation).where(
                MacroObservation.series_code == "USDKRW_KR_CLOSE",
                MacroObservation.retrieved_at == datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            )
        ).one()
        assert current.previous_value == 1379.1
        assert current.change_value == pytest.approx(7.1)
        assert current.change_pct == pytest.approx(0.5148285)
        market = json.loads(result.briefing.market_summary)
        usd = next(item for item in market["fx"] if item["series_code"] == "USDKRW_KR_CLOSE")
        assert usd["comparison_date"] == "2026-08-11"


def test_previous_close_is_none_on_first_day() -> None:
    engine = _engine()
    with Session(engine) as session:
        assert (
            previous_kr_close_observation(
                session, "alpha_vantage_fx_close", "USDKRW_KR_CLOSE", date(2026, 8, 12)
            )
            is None
        )


@pytest.mark.anyio
async def test_ready_briefing_retry_reuses_row_without_alpha_calls() -> None:
    engine = _engine()
    provider = FakeFxProvider(
        {
            "USDKRW_KR_CLOSE": 1386.2,
            "JPYKRW100_KR_CLOSE": 926.4,
            "EURKRW_KR_CLOSE": 1611.7,
        }
    )
    with Session(engine) as session:
        first = await run_kr_close_market_briefing(
            session,
            date(2026, 8, 12),
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=provider,
            dispatch_notifications=False,
        )
        second = await run_kr_close_market_briefing(
            session,
            date(2026, 8, 12),
            as_of=datetime(2026, 8, 12, 7, 20, tzinfo=timezone.utc),
            provider=provider,
            dispatch_notifications=False,
        )

        assert first.status == "ready"
        assert second.status == "already_completed"
        assert second.action == "reuse"
        assert provider.calls == 1
        deliveries = session.exec(select(NotificationDelivery)).all()
        assert [item.ticker for item in deliveries] == ["__MACRO_KR_CLOSE__"]


@pytest.mark.anyio
async def test_partial_pair_retry_merges_same_day_rows_and_requeues_recovered_message() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    with Session(engine) as session:
        first = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=FakeFxProvider({"USDKRW_KR_CLOSE": 1386.2}),
            dispatch_notifications=False,
        )
        delivery = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == "__MACRO_KR_CLOSE__"
            )
        ).one()
        delivery.status = "sent"
        delivery.sent_at = datetime(2026, 8, 12, 7, 6, tzinfo=timezone.utc)
        delivery.attempt_count = 1
        session.add(delivery)
        session.commit()

        second = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 20, tzinfo=timezone.utc),
            provider=FakeFxProvider(
                {
                    "JPYKRW100_KR_CLOSE": 926.4,
                    "EURKRW_KR_CLOSE": 1611.7,
                }
            ),
            dispatch_notifications=False,
        )
        session.refresh(delivery)
        market = json.loads(second.briefing.market_summary)

    assert first.status == "partial"
    assert second.status == "ready"
    assert second.action == "recovered_after_partial"
    assert {item["series_code"] for item in market["fx"]} == {
        "USDKRW_KR_CLOSE",
        "JPYKRW100_KR_CLOSE",
        "EURKRW_KR_CLOSE",
    }
    assert delivery.status == "pending"
    assert delivery.sent_at is None
    assert delivery.attempt_count == 0


@pytest.mark.anyio
async def test_pre_cutoff_ready_is_refreshed_for_production_window() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    provider = FakeFxProvider(
        {
            "USDKRW_KR_CLOSE": 1380.0,
            "JPYKRW100_KR_CLOSE": 920.0,
            "EURKRW_KR_CLOSE": 1600.0,
        }
    )
    with Session(engine) as session:
        first = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 6, 40, tzinfo=timezone.utc),
            provider=provider,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        provider.values = {
            "USDKRW_KR_CLOSE": 1386.2,
            "JPYKRW100_KR_CLOSE": 926.4,
            "EURKRW_KR_CLOSE": 1611.7,
        }
        second = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=provider,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        market = json.loads(second.briefing.market_summary)

    assert first.status == "ready"
    assert second.status == "ready"
    assert second.action == "refresh_after_pre_cutoff"
    assert provider.calls == 2
    assert {item["value"] for item in market["fx"]} == {1386.2, 926.4, 1611.7}
    assert all(item["retrieved_at"].startswith("2026-08-12T07:05") for item in market["fx"])


@pytest.mark.anyio
async def test_post_cutoff_briefing_time_does_not_mask_pre_cutoff_fx_observations() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    provider = FakeFxProvider(
        {
            "USDKRW_KR_CLOSE": 1380.0,
            "JPYKRW100_KR_CLOSE": 920.0,
            "EURKRW_KR_CLOSE": 1600.0,
        }
    )
    with Session(engine) as session:
        first = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 6, 40, tzinfo=timezone.utc),
            provider=provider,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        first.briefing.as_of = datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc)
        session.add(first.briefing)
        session.commit()

        provider.values = {
            "USDKRW_KR_CLOSE": 1386.2,
            "JPYKRW100_KR_CLOSE": 926.4,
            "EURKRW_KR_CLOSE": 1611.7,
        }
        second = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 20, tzinfo=timezone.utc),
            provider=provider,
            queue_notifications=False,
            dispatch_notifications=False,
        )

    assert provider.calls == 2
    assert second.action == "refresh_after_pre_cutoff"


@pytest.mark.anyio
async def test_pre_cutoff_sent_close_message_is_requeued_with_production_values() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    provider = FakeFxProvider(
        {
            "USDKRW_KR_CLOSE": 1380.0,
            "JPYKRW100_KR_CLOSE": 920.0,
            "EURKRW_KR_CLOSE": 1600.0,
        }
    )
    with Session(engine) as session:
        await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 6, 40, tzinfo=timezone.utc),
            provider=provider,
            dispatch_notifications=False,
        )
        delivery = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == "__MACRO_KR_CLOSE__"
            )
        ).one()
        delivery.status = "sent"
        delivery.sent_at = datetime(2026, 8, 12, 6, 41, tzinfo=timezone.utc)
        delivery.attempt_count = 1
        session.add(delivery)
        session.commit()

        provider.values = {
            "USDKRW_KR_CLOSE": 1401.0,
            "JPYKRW100_KR_CLOSE": 930.0,
            "EURKRW_KR_CLOSE": 1620.0,
        }
        result = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=provider,
            dispatch_notifications=False,
        )
        session.refresh(delivery)
        payload = json.loads(delivery.payload)

    assert result.action == "refresh_after_pre_cutoff"
    assert delivery.status == "pending"
    assert delivery.sent_at is None
    assert delivery.attempt_count == 0
    assert "1,401.0원" in payload["text"]


@pytest.mark.anyio
async def test_pre_cutoff_observations_cannot_make_failed_production_refresh_ready() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    with Session(engine) as session:
        await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 6, 40, tzinfo=timezone.utc),
            provider=FakeFxProvider(
                {
                    "USDKRW_KR_CLOSE": 1380.0,
                    "JPYKRW100_KR_CLOSE": 920.0,
                    "EURKRW_KR_CLOSE": 1600.0,
                }
            ),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        failing = FailingFxProvider()
        result = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=failing,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        market = json.loads(result.briefing.market_summary)

    assert failing.calls == 1
    assert result.status == "partial"
    assert result.action == "refresh_after_pre_cutoff"
    assert market["fx"] == []
    assert "provider_failed:RuntimeError" in result.warnings
    assert all(f"{series}:unavailable" in result.warnings for series in (
        "USDKRW_KR_CLOSE",
        "JPYKRW100_KR_CLOSE",
        "EURKRW_KR_CLOSE",
    ))


@pytest.mark.anyio
async def test_production_refresh_does_not_merge_pre_cutoff_missing_pair() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    with Session(engine) as session:
        await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 6, 40, tzinfo=timezone.utc),
            provider=FakeFxProvider(
                {
                    "USDKRW_KR_CLOSE": 1380.0,
                    "JPYKRW100_KR_CLOSE": 920.0,
                    "EURKRW_KR_CLOSE": 1600.0,
                }
            ),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        result = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=FakeFxProvider(
                {
                    "USDKRW_KR_CLOSE": 1386.2,
                    "JPYKRW100_KR_CLOSE": 926.4,
                }
            ),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        market = json.loads(result.briefing.market_summary)

    assert result.status == "partial"
    assert {item["series_code"] for item in market["fx"]} == {
        "USDKRW_KR_CLOSE",
        "JPYKRW100_KR_CLOSE",
    }
    assert "EURKRW_KR_CLOSE:unavailable" in result.warnings


@pytest.mark.anyio
async def test_force_refresh_collects_again_even_after_production_ready() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    provider = FakeFxProvider(
        {
            "USDKRW_KR_CLOSE": 1386.2,
            "JPYKRW100_KR_CLOSE": 926.4,
            "EURKRW_KR_CLOSE": 1611.7,
        }
    )
    with Session(engine) as session:
        await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            provider=provider,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        provider.values["USDKRW_KR_CLOSE"] = 1390.0
        result = await run_kr_close_market_briefing(
            session,
            run_date,
            as_of=datetime(2026, 8, 12, 7, 20, tzinfo=timezone.utc),
            provider=provider,
            force=True,
            queue_notifications=False,
            dispatch_notifications=False,
        )
        market = json.loads(result.briefing.market_summary)

    assert provider.calls == 2
    assert result.action == "forced_refresh"
    assert next(
        item["value"] for item in market["fx"] if item["series_code"] == "USDKRW_KR_CLOSE"
    ) == 1390.0


def test_morning_and_kr_close_notifications_have_independent_markers() -> None:
    engine = _engine()
    run_date = date(2026, 8, 12)
    with Session(engine) as session:
        morning = MacroBriefing(
            briefing_date=run_date,
            briefing_type="morning",
            as_of=datetime(2026, 8, 12, tzinfo=timezone.utc),
            headline="morning",
            kakao_text="morning",
            dedupe_key="morning",
        )
        close = MacroBriefing(
            briefing_date=run_date,
            briefing_type="kr_close",
            as_of=datetime(2026, 8, 12, 7, 5, tzinfo=timezone.utc),
            headline="close",
            market_summary=json.dumps(
                {
                    "fx": [
                        {
                            "series_code": "USDKRW_KR_CLOSE",
                            "value": 1386.2,
                            "previous_value": 1379.1,
                            "change_value": 7.1,
                            "change_pct": 0.5148,
                            "quality_status": "fresh",
                        }
                    ]
                }
            ),
            kakao_text="close",
            dedupe_key="close",
        )
        session.add_all([morning, close])
        session.commit()

        queue_macro_notification(session, morning)
        queue_macro_notification(session, close)
        session.commit()
        markers = {item.ticker for item in session.exec(select(NotificationDelivery)).all()}
        message, context = _macro_report(close)

    assert markers == {"__MACRO__", "__MACRO_KR_CLOSE__"}
    assert "🇰🇷 한국 시장환경 점검" in message
    assert "원/달러 1,386.2원 · +7.1원 (+0.51%)" in message
    assert context["analysis_type"] == "macro_kr_close"


def test_morning_report_renders_verified_night_futures_as_context() -> None:
    briefing = MacroBriefing(
        briefing_date=date(2026, 8, 12),
        briefing_type="morning",
        as_of=datetime(2026, 8, 12, tzinfo=timezone.utc),
        headline="mixed",
        market_summary=json.dumps(
            {
                "observations": [
                    {
                        "series_code": "KRX_KOSPI200_NIGHT_FUT",
                        "value": 974.95,
                        "change_value": -14.85,
                        "change_pct": -1.5003,
                        "observed_at": "2026-08-11T00:00:00+09:00",
                        "trade_date": "2026-08-11",
                        "expected_latest_session_date": "2026-08-11",
                        "session_freshness": "fresh",
                        "quality_status": "fresh",
                    },
                    {
                        "series_code": "KRX_KOSDAQ150_NIGHT_FUT",
                        "value": 1489.0,
                        "change_value": 3.7,
                        "change_pct": 0.2491,
                        "observed_at": "2026-08-11T00:00:00+09:00",
                        "trade_date": "2026-08-11",
                        "expected_latest_session_date": "2026-08-11",
                        "session_freshness": "fresh",
                        "quality_status": "fresh",
                    },
                ]
            }
        ),
        kakao_text="morning",
        dedupe_key="night-futures-morning",
    )

    message, _context = _macro_report(briefing)

    assert "🌙 한국 야간선물 · 08/11 기준" in message
    assert "KOSPI200 최근월물 974.95 · -14.85pt (-1.50%)" in message
    assert "KOSDAQ150 최근월물 1,489.00 · +3.70pt (+0.25%)" in message
    assert message.index("📈 오늘 가장 중요한 변화") < message.index("🌙 한국 야간선물")


def test_morning_report_excludes_stale_night_futures_with_compact_caution() -> None:
    rows = [
        {
            "series_code": series_code,
            "value": 974.95,
            "change_value": -14.85,
            "change_pct": -1.5003,
            "observed_at": "2026-08-11T00:00:00+09:00",
            "trade_date": "2026-08-11",
            "expected_latest_session_date": "2026-08-12",
            "session_freshness": "stale",
            "quality_status": "stale",
        }
        for series_code in (
            "KRX_KOSPI200_NIGHT_FUT",
            "KRX_KOSDAQ150_NIGHT_FUT",
        )
    ]
    briefing = MacroBriefing(
        briefing_date=date(2026, 8, 13),
        briefing_type="morning",
        as_of=datetime(2026, 8, 12, 22, 50, tzinfo=timezone.utc),
        headline="mixed",
        market_summary=json.dumps({"observations": rows}),
        data_quality=json.dumps(
            [
                {
                    "series_code": row["series_code"],
                    "quality_status": "stale",
                    "observed_at": row["observed_at"],
                }
                for row in rows
            ]
        ),
        kakao_text="morning",
        dedupe_key="stale-night-futures-morning",
    )

    message, _context = _macro_report(briefing)

    assert "🌙 한국 야간선물" not in message
    assert message.count("한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해") == 1
    assert "KRX_KOSPI200_NIGHT_FUT" not in message
    assert "session_freshness" not in message
