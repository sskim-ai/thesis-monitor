import json
from datetime import date, datetime, time

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.models.macro import MacroBriefing
from app.models.thesis import (
    InvestmentThesis,
    MonitorRun,
    NotificationDelivery,
    ThesisAssessment,
)
from app.models.watchlist import WatchlistItem
from app.services.morning_gate import (
    KST,
    initialize_morning_gate,
    run_morning_night_futures_gate,
)
from app.services.notification_service import MORNING_GATE_METADATA_KEY


EXPECTED_SESSION = date(2026, 8, 13)


@pytest.fixture(autouse=True)
def isolate_ai_review_packet(monkeypatch):
    calls: list[tuple[date, str]] = []

    def record(_session, run_date, market, **_kwargs):
        calls.append((run_date, market))

    monkeypatch.setattr("app.services.morning_gate.try_write_ai_review_packet", record)
    return calls


class ScriptedKrxProvider:
    name = "krx_night_futures"

    def __init__(self, responses: list[MacroProviderResult | Exception]) -> None:
        self.responses = responses
        self.calls: list[datetime] = []

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        self.calls.append(as_of)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class RecordingNotifier:
    def __init__(self, *, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.payloads: list[dict[str, object]] = []

    async def send(self, payload: dict[str, object]) -> str:
        self.payloads.append(payload)
        if self.fail_first and len(self.payloads) == 1:
            raise RuntimeError("scripted outage")
        return "sent"


def _engine():
    value = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(value)
    return value


def _at(hour: int, minute: int) -> datetime:
    return datetime.combine(date(2026, 8, 14), time(hour, minute), tzinfo=KST)


def _observation(series_code: str) -> CollectedObservation:
    is_kospi = "KOSPI200" in series_code
    return CollectedObservation(
        series_code=series_code,
        category="kr_night_futures",
        observed_at=datetime.combine(EXPECTED_SESSION, time.min, tzinfo=KST),
        value=431.25 if is_kospi else 1432.5,
        unit="index_points",
        frequency="daily",
        market_session="kr_night",
        previous_value=428.4 if is_kospi else 1436.7,
        change_value=2.85 if is_kospi else -4.2,
        change_pct=0.67 if is_kospi else -0.29,
        source_url="https://data-dbg.krx.co.kr/",
        quality_status="fresh",
        raw_payload={
            "trade_date": EXPECTED_SESSION.isoformat(),
            "expected_latest_session_date": EXPECTED_SESSION.isoformat(),
            "session_freshness": "fresh",
        },
    )


def _provider_result(*series_codes: str) -> MacroProviderResult:
    return MacroProviderResult(
        provider="krx_night_futures",
        observations=[_observation(item) for item in series_codes],
    )


def _seed_morning(session: Session) -> None:
    run_date = date(2026, 8, 14)
    ticker = "GATEUS"
    session.add(
        MacroBriefing(
            briefing_date=run_date,
            briefing_type="morning",
            as_of=_at(7, 50),
            headline="mixed",
            market_summary=json.dumps({"items": [], "observations": []}),
            regime_summary=json.dumps(
                {
                    "label": "mixed",
                    "summary": "signals mixed",
                    "confidence": 0.5,
                    "growth_momentum": 0,
                    "inflation_pressure": 0,
                    "liquidity_condition": 0,
                    "financial_conditions": 0,
                    "risk_appetite": 0,
                    "earnings_momentum": 0,
                }
            ),
            today_calendar="[]",
            macro_theses="[]",
            ticker_impacts="[]",
            data_quality="[]",
            kakao_text="legacy",
            status="ready",
            dedupe_key="macro:2026-08-14:morning",
        )
    )
    session.add(WatchlistItem(ticker=ticker, company_name="Gate US", exchange="NASDAQ"))
    session.add(InvestmentThesis(ticker=ticker, version=1, core_thesis="Gate thesis"))
    session.add(
        ThesisAssessment(
            ticker=ticker,
            thesis_version=1,
            assessment_date=run_date,
            status="no_material_change",
            business_thesis_change="no_material_change",
            valuation_change="neutral",
            earnings_estimate_impact="unchanged",
            summary="No material change",
            new_buyer_view="Wait for evidence",
            holder_view="Maintain monitoring",
            price_view="No price conclusion",
            risk_level="normal",
            evidence="[]",
            thesis_snapshot=json.dumps({"assessment_mode": "daily_delta"}),
        )
    )
    session.add(
        MonitorRun(
            run_date=run_date,
            run_type="daily_us",
            status="success",
            started_at=_at(7, 50),
            completed_at=_at(7, 55),
            ticker_count=1,
            success_count=1,
        )
    )
    session.add(
        NotificationDelivery(
            ticker="__DAILY_DIGEST__",
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "old digest", "type": "daily_monitoring_digest"}),
        )
    )
    session.add(
        NotificationDelivery(
            ticker=ticker,
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "stock report", "type": "daily_stock_analysis"}),
        )
    )
    session.add(
        NotificationDelivery(
            ticker="005930",
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"text": "KR report", "type": "daily_stock_analysis"}),
        )
    )
    session.commit()
    initialize_morning_gate(session, run_date, _at(7, 55), reset=True)


def _gate_metadata(session: Session) -> dict[str, object]:
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == "__DAILY_DIGEST__"
        )
    ).one()
    return json.loads(delivery.payload)[MORNING_GATE_METADATA_KEY]


@pytest.mark.anyio
async def test_gate_holds_until_0800_without_querying_krx(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider([_provider_result()])
    with Session(_engine()) as session:
        _seed_morning(session)

        result = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(7, 59),
            provider=provider,
        )

    assert result.status == "waiting"
    assert result.dispatch_action == "held_until_08:00"
    assert provider.calls == []


@pytest.mark.anyio
async def test_gate_dispatches_immediately_when_both_contracts_are_ready(
    monkeypatch,
    isolate_ai_review_packet,
) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider(
        [
            _provider_result(
                "KRX_KOSPI200_NIGHT_FUT",
                "KRX_KOSDAQ150_NIGHT_FUT",
            )
        ]
    )
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)

        result = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 0),
            provider=provider,
            notifier=notifier,
        )
        metadata = _gate_metadata(session)
        kr_delivery = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "005930")
        ).one()

    assert result.status == "dispatched"
    assert result.retry_count == 1
    assert [item["type"] for item in notifier.payloads] == [
        "daily_monitoring_digest",
        "daily_stock_analysis",
    ]
    assert "🌙 한국 야간선물 · 08/13 기준" in str(notifier.payloads[0]["text"])
    assert metadata["first_query_at"].endswith("08:00:00+09:00")
    assert metadata["first_complete_at"].endswith("08:00:00+09:00")
    assert metadata["dispatch_at"].endswith("08:00:00+09:00")
    assert kr_delivery.status == "pending"
    assert isolate_ai_review_packet == [(date(2026, 8, 14), "us")]


@pytest.mark.anyio
async def test_gate_holds_for_ai_pilot_after_both_contracts_are_ready(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    monkeypatch.setattr(
        "app.services.morning_gate.ai_assisted_pilot_active", lambda market: True
    )
    monkeypatch.setattr(
        "app.services.morning_gate.try_write_ai_review_packet",
        lambda *args, **kwargs: type("Packet", (), {"packet_id": "us-packet"})(),
    )
    held: list[str] = []
    monkeypatch.setattr(
        "app.services.morning_gate.hold_ai_assisted_pilot_session",
        lambda session, packet_id, held_at: held.append(packet_id),
    )
    provider = ScriptedKrxProvider(
        [
            _provider_result(
                "KRX_KOSPI200_NIGHT_FUT",
                "KRX_KOSDAQ150_NIGHT_FUT",
            )
        ]
    )
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)
        result = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 0),
            provider=provider,
            notifier=notifier,
        )
        metadata = _gate_metadata(session)

    assert result.status == "ai_review_hold"
    assert result.dispatch_action == "held_for_ai_review"
    assert held == ["us-packet"]
    assert notifier.payloads == []
    assert metadata["state"] == "ai_review_hold"


@pytest.mark.anyio
async def test_gate_retries_only_krx_until_both_are_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider(
        [
            _provider_result(),
            _provider_result(),
            _provider_result(),
            _provider_result("KRX_KOSPI200_NIGHT_FUT"),
            _provider_result(
                "KRX_KOSPI200_NIGHT_FUT",
                "KRX_KOSDAQ150_NIGHT_FUT",
            ),
        ]
    )
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)

        for minute in (0, 5, 10, 15):
            result = await run_morning_night_futures_gate(
                session,
                date(2026, 8, 14),
                _at(8, minute),
                provider=provider,
                notifier=notifier,
            )
            assert result.status == "waiting"
            assert notifier.payloads == []
        result = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 20),
            provider=provider,
            notifier=notifier,
        )
        metadata = _gate_metadata(session)

    assert result.status == "dispatched"
    assert len(provider.calls) == 5
    assert metadata["KOSPI200_first_available_at"].endswith("08:15:00+09:00")
    assert metadata["KOSDAQ150_first_available_at"].endswith("08:20:00+09:00")
    assert metadata["first_complete_at"].endswith("08:20:00+09:00")
    assert metadata["retry_count"] == 5


@pytest.mark.anyio
async def test_deadline_dispatches_partial_contract_with_caution(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider(
        [_provider_result("KRX_KOSPI200_NIGHT_FUT")]
    )
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)

        result = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 45),
            provider=provider,
            notifier=notifier,
        )

    digest = str(notifier.payloads[0]["text"])
    assert result.status == "dispatched"
    assert result.deadline_reached is True
    assert "KOSPI200 최근월물" in digest
    assert "KOSDAQ150 최근월물" not in digest
    assert "KOSDAQ150 야간선물은 최신 세션 확인이 되지 않아 제외했습니다." in digest


@pytest.mark.anyio
async def test_deadline_excludes_all_stale_values_with_one_caution(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider([_provider_result()])
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)

        result = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 45),
            provider=provider,
            notifier=notifier,
        )

    digest = str(notifier.payloads[0]["text"])
    assert result.status == "dispatched"
    assert "🌙 한국 야간선물" not in digest
    assert digest.count("한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해") == 1


@pytest.mark.anyio
async def test_provider_error_recovers_without_duplicate_dispatch(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider(
        [
            RuntimeError("timeout"),
            RuntimeError("timeout"),
            _provider_result(
                "KRX_KOSPI200_NIGHT_FUT",
                "KRX_KOSDAQ150_NIGHT_FUT",
            ),
        ]
    )
    notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)

        for minute in (0, 5, 10):
            result = await run_morning_night_futures_gate(
                session,
                date(2026, 8, 14),
                _at(8, minute),
                provider=provider,
                notifier=notifier,
            )
        duplicate = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 10),
            provider=provider,
            notifier=notifier,
        )

    assert result.status == "dispatched"
    assert duplicate.dispatch_action == "already_dispatched"
    assert len(provider.calls) == 3
    assert len(notifier.payloads) == 2


@pytest.mark.anyio
async def test_released_gate_retries_telegram_without_refetching_krx(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    provider = ScriptedKrxProvider(
        [
            _provider_result(
                "KRX_KOSPI200_NIGHT_FUT",
                "KRX_KOSDAQ150_NIGHT_FUT",
            )
        ]
    )
    failed_notifier = RecordingNotifier(fail_first=True)
    recovered_notifier = RecordingNotifier()
    with Session(_engine()) as session:
        _seed_morning(session)

        first = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 0),
            provider=provider,
            notifier=failed_notifier,
        )
        second = await run_morning_night_futures_gate(
            session,
            date(2026, 8, 14),
            _at(8, 5),
            provider=provider,
            notifier=recovered_notifier,
        )

    assert first.status == "ready"
    assert second.status == "dispatched"
    assert len(provider.calls) == 1
    assert [item["type"] for item in recovered_notifier.payloads] == [
        "daily_monitoring_digest"
    ]


def test_gate_metadata_is_internal_only(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.morning_gate.expected_latest_completed_krx_session",
        lambda run_date: EXPECTED_SESSION,
    )
    with Session(_engine()) as session:
        _seed_morning(session)
        delivery = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == "__DAILY_DIGEST__"
            )
        ).one()
        payload = json.loads(delivery.payload)

    text = str(payload["text"])
    assert MORNING_GATE_METADATA_KEY in payload
    for token in (
        "retry_count",
        "first_complete_at",
        "deadline_reached",
        "expected_session=",
    ):
        assert token not in text
