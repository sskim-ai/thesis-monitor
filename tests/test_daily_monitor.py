import json
import plistlib
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.database import engine, init_db
from app.jobs.monitor_daily import (
    _analysis_completed_after_cutoff,
    _analysis_decision,
    _macro_result_for_scope,
    _requeue_cutoff,
    _run_market_job,
)
from app.models.event import Event
from app.models.macro import MacroBriefing
from app.models.thesis import (
    InvestmentThesis,
    MonitorRun,
    NotificationDelivery,
    ThesisAssessment,
)
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import (
    MonitoringItemCreate,
    PriceContext,
    PricePeriodSummary,
    PriceRulesInput,
    ValuationSnapshot,
)
from app.services.daily_monitor_service import run_daily_monitor
from app.services.market_session import market_scope_for_security
from app.services.monitoring_service import register_monitoring_item
from app.services.notification_service import (
    TELEGRAM_DELIVERY_METADATA_KEY,
    TelegramChunkResult,
    TelegramDeliveryError,
    TelegramNotifier,
    dispatch_pending_notifications,
    queue_daily_digest_notification,
)


class FakeCollectionService:
    async def collect_events(self, session: Session, ticker: str, lookback_days: int) -> list[Event]:
        event = Event(
            ticker=ticker,
            company_name="Test Company",
            date=date(2030, 1, 2),
            source="Company filing",
            provider="sec_edgar",
            title="Test Company confirms a new customer production order",
            url="https://example.com/test-production-order",
            event_type="production_order",
            confirmed_facts=json.dumps(["New customer production order was confirmed"]),
            inferred_implications=json.dumps(["Demand thesis may strengthen"]),
            unknowns="[]",
            requires_review=True,
            relevance_score=70,
            relevance_reason="production order",
        )
        session.add(event)
        session.commit()
        return [event]


class FakePriceClient:
    async def fetch_price_context(self, ticker: str) -> PriceContext:
        return PriceContext(
            available=True,
            periods={
                "daily": PricePeriodSummary(
                    requested_count=500,
                    actual_count=420,
                    latest_date="2030-01-02",
                    latest_close=120,
                    period_return_pct=20,
                    range_position_pct=60,
                ),
                "weekly": PricePeriodSummary(requested_count=300, actual_count=240),
                "monthly": PricePeriodSummary(requested_count=100, actual_count=84),
            },
        )


class EmptyCollectionService:
    async def collect_events(self, session: Session, ticker: str, lookback_days: int) -> list[Event]:
        return []


class FailCollectionService:
    async def collect_events(self, *args, **kwargs):
        raise AssertionError("delivery retry must not recollect events")


class FailPriceClient:
    async def fetch_price_context(self, *args, **kwargs):
        raise AssertionError("delivery retry must not refresh OHLCV")


class FailValuationService:
    async def fetch(self, *args, **kwargs):
        raise AssertionError("delivery retry must not recalculate valuation")


class RulePriceClient:
    def __init__(self, previous_close: float, latest_close: float) -> None:
        self.previous_close = previous_close
        self.latest_close = latest_close

    async def fetch_price_context(self, ticker: str) -> PriceContext:
        return PriceContext(
            available=True,
            periods={
                "daily": PricePeriodSummary(
                    requested_count=500,
                    actual_count=500,
                    latest_date="2030-01-03",
                    previous_close=self.previous_close,
                    latest_close=self.latest_close,
                    latest_high=max(self.previous_close, self.latest_close),
                    latest_low=min(self.previous_close, self.latest_close),
                    range_position_pct=60,
                )
            },
        )


class EmptyValuationService:
    async def fetch(self, ticker, exchange, price_context, *, session, thesis):
        return ValuationSnapshot(
            current_price=price_context.periods.get("daily", PricePeriodSummary(
                requested_count=500, actual_count=0
            )).latest_close,
            currency="KRW" if ticker.isdigit() else "USD",
        )


def test_market_scope_classification_uses_exchange_then_numeric_fallback() -> None:
    assert market_scope_for_security("005930", "KRX") == "kr"
    assert market_scope_for_security("GOOGL", "NASDAQ") == "us"
    assert market_scope_for_security("005930", None) == "kr"
    assert market_scope_for_security("UNKNOWN", None) == "unknown"


def test_launch_agents_define_market_specific_schedules() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "ops/com.seungsoo.thesis-monitor.daily.plist").open("rb") as stream:
        us = plistlib.load(stream)
    with (root / "ops/com.seungsoo.thesis-monitor.kr-close.plist").open("rb") as stream:
        kr = plistlib.load(stream)

    assert us["ProgramArguments"][-1].endswith("--market us")
    assert us["StartCalendarInterval"] == [
        {"Hour": 7, "Minute": 50},
        {"Hour": 8, "Minute": 5},
        {"Hour": 8, "Minute": 35},
    ]
    assert kr["ProgramArguments"][-1].endswith("--market kr")
    assert kr["StartCalendarInterval"] == [
        {"Hour": 16, "Minute": 5},
        {"Hour": 16, "Minute": 20},
        {"Hour": 16, "Minute": 50},
    ]
    assert "RunAtLoad" not in kr


def test_analysis_completion_uses_scoped_run_after_cutoff() -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2040, 8, 13)
    with Session(isolated_engine) as session:
        session.add(
            MonitorRun(
                run_date=run_date,
                run_type="daily_us",
                status="success",
                started_at=datetime(2040, 8, 12, 22, 46, tzinfo=timezone.utc),
                completed_at=datetime(2040, 8, 12, 22, 50, tzinfo=timezone.utc),
            )
        )
        session.add(
            MonitorRun(
                run_date=run_date,
                run_type="daily_kr",
                status="success",
                started_at=datetime(2040, 8, 13, 6, 58, tzinfo=timezone.utc),
                completed_at=datetime(2040, 8, 13, 6, 59, tzinfo=timezone.utc),
            )
        )
        session.commit()

        assert _analysis_completed_after_cutoff(
            session, run_date, _requeue_cutoff(run_date, "us"), "us"
        ) is True
        assert _analysis_completed_after_cutoff(
            session, run_date, _requeue_cutoff(run_date, "kr"), "kr"
        ) is False
        assert _analysis_decision(
            session, run_date, _requeue_cutoff(run_date, "us"), "us"
        ).action == "reuse"
        assert _analysis_decision(
            session, run_date, _requeue_cutoff(run_date, "kr"), "kr"
        ).action == "refresh_after_pre_cutoff_run"


@pytest.mark.parametrize(
    ("market_scope", "started_at", "completed_at", "expected_action"),
    [
        (
            "us",
            datetime(2040, 8, 12, 22, 44, tzinfo=timezone.utc),
            datetime(2040, 8, 12, 22, 46, tzinfo=timezone.utc),
            "refresh_after_pre_cutoff_run",
        ),
        (
            "us",
            datetime(2040, 8, 12, 22, 45, tzinfo=timezone.utc),
            datetime(2040, 8, 12, 22, 48, tzinfo=timezone.utc),
            "reuse",
        ),
        (
            "kr",
            datetime(2040, 8, 13, 6, 59, tzinfo=timezone.utc),
            datetime(2040, 8, 13, 7, 3, tzinfo=timezone.utc),
            "refresh_after_pre_cutoff_run",
        ),
        (
            "kr",
            datetime(2040, 8, 13, 7, 0, tzinfo=timezone.utc),
            datetime(2040, 8, 13, 7, 4, tzinfo=timezone.utc),
            "reuse",
        ),
    ],
)
def test_analysis_cutoff_requires_start_and_completion_in_production_window(
    market_scope: str,
    started_at: datetime,
    completed_at: datetime,
    expected_action: str,
) -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2040, 8, 13)
    with Session(isolated_engine) as session:
        session.add(
            MonitorRun(
                run_date=run_date,
                run_type=f"daily_{market_scope}",
                status="success",
                started_at=started_at,
                completed_at=completed_at,
            )
        )
        session.commit()
        cutoff = _requeue_cutoff(run_date, market_scope)

        decision = _analysis_decision(session, run_date, cutoff, market_scope)

        assert decision.action == expected_action
        assert decision.refresh is (expected_action != "reuse")


def test_analysis_decision_handles_missing_failed_and_running_runs() -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    cutoff_date = date(2041, 8, 13)
    with Session(isolated_engine) as session:
        cutoff = _requeue_cutoff(cutoff_date, "us")
        assert _analysis_decision(session, cutoff_date, cutoff, "us").action == "fresh"

        run = MonitorRun(run_date=cutoff_date, run_type="daily_us", status="failed")
        session.add(run)
        session.commit()
        assert _analysis_decision(
            session, cutoff_date, cutoff, "us"
        ).action == "retry_after_failure"

        run.status = "running"
        session.commit()
        decision = _analysis_decision(session, cutoff_date, cutoff, "us")
        assert decision.action == "refresh_after_pre_cutoff_run"
        assert decision.refresh is True

        run.started_at = datetime(2041, 8, 12, 22, 50, tzinfo=timezone.utc)
        session.commit()
        decision = _analysis_decision(session, cutoff_date, cutoff, "us")
        assert decision.action == "in_progress"
        assert decision.refresh is False


def test_analysis_completion_rejects_missing_timestamps() -> None:
    class QueryResult:
        def __init__(self, run) -> None:
            self.run = run

        def first(self):
            return self.run

    class FakeSession:
        def __init__(self, run) -> None:
            self.run = run

        def exec(self, _query):
            return QueryResult(self.run)

    run_date = date(2041, 8, 14)
    cutoff = _requeue_cutoff(run_date, "kr")
    for run in (
        SimpleNamespace(
            status="success",
            started_at=None,
            completed_at=datetime(2041, 8, 14, 7, 4, tzinfo=timezone.utc),
        ),
        SimpleNamespace(
            status="success",
            started_at=datetime(2041, 8, 14, 7, 1, tzinfo=timezone.utc),
            completed_at=None,
        ),
    ):
        assert _analysis_completed_after_cutoff(
            FakeSession(run),  # type: ignore[arg-type]
            run_date,
            cutoff,
            "kr",
        ) is False


@pytest.mark.anyio
async def test_kr_scope_reuses_macro_without_collecting(monkeypatch) -> None:
    async def fail_if_called(*args, **kwargs):
        raise AssertionError("KR close run must not recollect macro providers")

    monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", fail_if_called)
    run_date = date(2040, 8, 14)
    init_db()
    with Session(engine) as session:
        session.add(
            MacroBriefing(
                briefing_date=run_date,
                as_of=datetime(2040, 8, 14, tzinfo=timezone.utc),
                headline="stored",
                kakao_text="legacy",
                dedupe_key="macro:2040-08-14:morning",
            )
        )
        session.commit()
        result = await _macro_result_for_scope(
            session,
            run_date,
            "kr",
            True,
        )

    assert result == {"run_date": "2040-08-14", "status": "reused"}


@pytest.mark.anyio
async def test_macro_reuse_reports_unavailable_without_same_date_data(monkeypatch) -> None:
    async def fail_if_called(*args, **kwargs):
        raise AssertionError("delivery retry must not recollect macro providers")

    monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", fail_if_called)
    init_db()
    with Session(engine) as session:
        result = await _macro_result_for_scope(
            session,
            date(2040, 8, 15),
            "us",
            False,
        )

    assert result == {"run_date": "2040-08-15", "status": "unavailable"}


@pytest.mark.anyio
async def test_us_scope_collects_macro(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class MacroResult:
        def model_dump(self, mode: str) -> dict[str, object]:
            return {"run_date": "2040-08-14", "status": "success"}

    async def record_call(session, **kwargs):
        calls.append(kwargs)
        return MacroResult()

    monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", record_call)
    with Session(engine) as session:
        result = await _macro_result_for_scope(
            session,
            date(2040, 8, 14),
            "us",
            True,
        )

    assert result["status"] == "success"
    assert calls == [
        {
            "run_date": date(2040, 8, 14),
            "force": True,
            "queue_notifications": False,
            "dispatch_notifications": False,
        }
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("market_scope", "run_type", "completed_at", "ticker_count"),
    [
        ("us", "daily_us", datetime(2042, 8, 12, 22, 50, tzinfo=timezone.utc), 9),
        ("kr", "daily_kr", datetime(2042, 8, 13, 7, 8, tzinfo=timezone.utc), 5),
    ],
)
async def test_market_job_reuses_successful_analysis_for_delivery_retry(
    monkeypatch,
    market_scope: str,
    run_type: str,
    completed_at: datetime,
    ticker_count: int,
) -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2042, 8, 13)
    calls: list[dict[str, object]] = []

    async def fail_macro(*args, **kwargs):
        raise AssertionError("delivery retry must not recollect macro providers")

    async def record_daily(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            status="already_completed",
            model_dump=lambda mode: {"status": "already_completed"},
        )

    monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", fail_macro)
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", record_daily)
    with Session(isolated_engine) as session:
        run = MonitorRun(
            run_date=run_date,
            run_type=run_type,
            status="success",
            started_at=completed_at,
            completed_at=completed_at,
            ticker_count=ticker_count,
            success_count=ticker_count,
        )
        session.add(run)
        session.commit()
        started_at = run.started_at
        completed_at = run.completed_at

        output = await _run_market_job(session, run_date, market_scope)
        session.refresh(run)

        assert output["analysis_action"] == "reuse"
        assert output["delivery_action"] == "retry"
        assert calls == [
            {
                "run_date": run_date,
                "force": False,
                "requeue_sent_before": None,
                "market_scope": market_scope,
            }
        ]
        assert run.started_at == started_at
        assert run.completed_at == completed_at
        assert run.success_count == ticker_count


@pytest.mark.anyio
async def test_kr_market_job_embeds_close_briefing_without_separate_delivery(
    monkeypatch,
) -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2042, 8, 15)
    close_calls: list[dict[str, object]] = []

    async def record_close(session, requested_date, **kwargs):
        close_calls.append({"run_date": requested_date, **kwargs})
        return SimpleNamespace(
            model_dump=lambda mode: {
                "status": "ready",
                "action": "fresh",
            }
        )

    async def record_daily(*args, **kwargs):
        return SimpleNamespace(
            status="success",
            model_dump=lambda mode: {"status": "success"},
        )

    monkeypatch.setattr(
        "app.jobs.monitor_daily.run_kr_close_market_briefing", record_close
    )
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", record_daily)
    with Session(isolated_engine) as session:
        output = await _run_market_job(session, run_date, "kr")

    assert output["kr_close_market"] == {"status": "ready", "action": "fresh"}
    assert close_calls == [
        {
            "run_date": run_date,
            "queue_notifications": False,
            "dispatch_notifications": False,
        }
    ]


@pytest.mark.anyio
async def test_market_job_does_not_overlap_running_analysis(monkeypatch) -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2042, 8, 14)

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("running analysis must not be started again")

    monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", fail_if_called)
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", fail_if_called)
    with Session(isolated_engine) as session:
        session.add(
            MonitorRun(
                run_date=run_date,
                run_type="daily_us",
                status="running",
                started_at=datetime(2042, 8, 13, 22, 50, tzinfo=timezone.utc),
            )
        )
        session.commit()

        output = await _run_market_job(session, run_date, "us")

    assert output["analysis_action"] == "in_progress"
    assert output["delivery_action"] == "deferred"
    assert output["theses"] is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("market_scope", "ticker", "exchange", "completed_at"),
    [
        ("us", "USRETRY", "NASDAQ", datetime(2043, 8, 12, 22, 50, tzinfo=timezone.utc)),
        ("kr", "204301", "KRX", datetime(2043, 8, 13, 7, 8, tzinfo=timezone.utc)),
    ],
)
async def test_post_cutoff_retry_reuses_assessment_and_dispatches_only_pending_digest(
    monkeypatch,
    market_scope: str,
    ticker: str,
    exchange: str,
    completed_at: datetime,
) -> None:
    class ThreeChunkNotifier(TelegramNotifier):
        def __init__(self, fail_on_call: int | None = None) -> None:
            super().__init__()
            self.settings = self.settings.model_copy(
                update={"notification_dry_run": False, "telegram_message_max_chars": 100}
            )
            self.fail_on_call = fail_on_call
            self.calls: list[str] = []

        async def prepare_text(self, payload: dict[str, object]) -> str:
            return str(payload["text"])

        def build_chunks(self, text: str, max_chars: int) -> list[str]:
            return ["first", "second", "third"]

        async def send_chunk(self, text: str) -> TelegramChunkResult:
            self.calls.append(text)
            if self.fail_on_call == len(self.calls):
                raise TelegramDeliveryError("scripted partial failure")
            return TelegramChunkResult(message_id=len(self.calls))

    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    run_date = date(2043, 8, 13)
    run_type = f"daily_{market_scope}"
    digest_ticker = "__DAILY_DIGEST_KR__" if market_scope == "kr" else "__DAILY_DIGEST__"

    with Session(isolated_engine) as session:
        session.add(
            WatchlistItem(
                ticker=ticker,
                company_name="Retry Fixture",
                exchange=exchange,
            )
        )
        session.add(
            InvestmentThesis(ticker=ticker, version=1, core_thesis="Retry fixture thesis")
        )
        session.commit()
        primary = await run_daily_monitor(
            session,
            run_date=run_date,
            market_scope=market_scope,
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            valuation_service=EmptyValuationService(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        assert primary.status == "success"

        run = session.exec(
            select(MonitorRun).where(
                MonitorRun.run_date == run_date,
                MonitorRun.run_type == run_type,
            )
        ).one()
        assessment = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == ticker,
                ThesisAssessment.assessment_date == run_date,
            )
        ).one()
        run.started_at = completed_at
        run.completed_at = completed_at
        digest = queue_daily_digest_notification(
            session,
            run_date,
            market_scope=market_scope,
        )
        assert digest is not None
        assert digest.ticker == digest_ticker
        first_notifier = ThreeChunkNotifier(fail_on_call=2)
        await dispatch_pending_notifications(
            session,
            notifier=first_notifier,
            delivery_ids={digest.id},
        )
        session.refresh(digest)
        assert first_notifier.calls == ["[1/3]\nfirst", "[2/3]\nsecond"]
        assert digest.status == "pending"
        assert (
            json.loads(digest.payload)[TELEGRAM_DELIVERY_METADATA_KEY]["next_chunk_index"]
            == 1
        )
        stock = NotificationDelivery(
            ticker=ticker,
            assessment_date=run_date,
            channel="telegram",
            status="sent",
            payload="{}",
            attempt_count=1,
            sent_at=completed_at,
        )
        session.add(stock)
        session.commit()
        session.refresh(assessment)
        original_run_times = (run.started_at, run.completed_at)
        original_assessment = assessment.model_dump()

        def fail_provider_init(*args, **kwargs):
            raise AssertionError("delivery retry must not initialize analysis providers")

        def fail_evaluation(*args, **kwargs):
            raise AssertionError("delivery retry must not evaluate the thesis")

        async def fail_macro(*args, **kwargs):
            raise AssertionError("delivery retry must not recollect macro providers")

        async def reuse_close(*args, **kwargs):
            return SimpleNamespace(
                model_dump=lambda mode: {
                    "status": "already_completed",
                    "action": "reuse",
                }
            )

        retry_notifier = ThreeChunkNotifier()

        monkeypatch.setattr(
            "app.services.daily_monitor_service.CollectionService", fail_provider_init
        )
        monkeypatch.setattr(
            "app.services.daily_monitor_service.OhlcvClient", fail_provider_init
        )
        monkeypatch.setattr(
            "app.services.daily_monitor_service.ValuationSnapshotService",
            fail_provider_init,
        )
        monkeypatch.setattr(
            "app.services.daily_monitor_service.evaluate_thesis", fail_evaluation
        )
        monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", fail_macro)
        monkeypatch.setattr(
            "app.jobs.monitor_daily.run_kr_close_market_briefing",
            reuse_close,
        )
        monkeypatch.setattr(
            "app.services.notification_service._notifier_for_channel",
            lambda channel: retry_notifier,
        )

        output = await _run_market_job(session, run_date, market_scope)
        session.refresh(run)
        session.refresh(assessment)
        session.refresh(digest)
        session.refresh(stock)

        assert output["analysis_action"] == "reuse"
        assert output["delivery_action"] == "retry"
        assert (run.started_at, run.completed_at) == original_run_times
        assert assessment.model_dump() == original_assessment
        assert retry_notifier.calls == ["[2/3]\nsecond", "[3/3]\nthird"]
        assert digest.status == "sent"
        assert digest.attempt_count == 2
        assert (
            json.loads(digest.payload)[TELEGRAM_DELIVERY_METADATA_KEY]["next_chunk_index"]
            == 3
        )
        assert stock.status == "sent"
        assert stock.attempt_count == 1


@pytest.mark.anyio
async def test_daily_monitor_keeps_us_and_kr_runs_independent() -> None:
    run_date = date(2040, 8, 12)
    kr_tickers = ["100001", "100002", "100003", "100004", "100005"]
    us_tickers = [f"USFIX{index}" for index in range(1, 10)]
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    with Session(isolated_engine) as session:
        for ticker in kr_tickers:
            session.add(
                WatchlistItem(
                    ticker=ticker,
                    company_name=ticker,
                    exchange="KRX",
                )
            )
            session.add(
                InvestmentThesis(ticker=ticker, version=1, core_thesis="Scoped KR thesis")
            )
        for ticker in us_tickers:
            session.add(
                WatchlistItem(
                    ticker=ticker,
                    company_name=ticker,
                    exchange="NASDAQ",
                )
            )
            session.add(
                InvestmentThesis(ticker=ticker, version=1, core_thesis="Scoped US thesis")
            )
        session.commit()

        us_result = await run_daily_monitor(
            session,
            run_date=run_date,
            market_scope="us",
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            valuation_service=EmptyValuationService(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        kr_result = await run_daily_monitor(
            session,
            run_date=run_date,
            market_scope="kr",
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            valuation_service=EmptyValuationService(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        us_run = session.exec(
            select(MonitorRun).where(
                MonitorRun.run_date == run_date,
                MonitorRun.run_type == "daily_us",
            )
        ).one()
        original_started_at = us_run.started_at
        original_completed_at = us_run.completed_at
        original_price_contexts = {
            item.ticker: item.price_context
            for item in session.exec(
                select(ThesisAssessment).where(
                    ThesisAssessment.assessment_date == run_date,
                    ThesisAssessment.ticker.in_(set(us_tickers)),
                )
            ).all()
        }
        retry = await run_daily_monitor(
            session,
            run_date=run_date,
            market_scope="us",
            collection_service=FailCollectionService(),
            price_client=FailPriceClient(),
            valuation_service=FailValuationService(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        session.refresh(us_run)
        retry_price_contexts = {
            item.ticker: item.price_context
            for item in session.exec(
                select(ThesisAssessment).where(
                    ThesisAssessment.assessment_date == run_date,
                    ThesisAssessment.ticker.in_(set(us_tickers)),
                )
            ).all()
        }
        runs = session.exec(
            select(MonitorRun).where(MonitorRun.run_date == run_date)
        ).all()

    assert us_result.ticker_count == 9
    assert us_result.success_count == 9
    assert {item.ticker for item in us_result.assessments} == set(us_tickers)
    assert kr_result.ticker_count == 5
    assert kr_result.success_count == 5
    assert {item.ticker for item in kr_result.assessments} == set(kr_tickers)
    assert retry.status == "already_completed"
    assert {item.ticker for item in retry.assessments} == set(us_tickers)
    assert {run.run_type for run in runs} == {"daily_us", "daily_kr"}
    assert us_run.started_at == original_started_at
    assert us_run.completed_at == original_completed_at
    assert retry_price_contexts == original_price_contexts


@pytest.mark.anyio
async def test_daily_monitor_can_run_without_queuing_notifications() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="NOSEND1",
                company_name="No Send Company",
                core_thesis="A test thesis",
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2029, 12, 31),
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        deliveries = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.assessment_date == date(2029, 12, 31)
            )
        ).all()
        assert result.status == "success"
        assert deliveries == []


@pytest.mark.anyio
async def test_daily_monitor_assesses_and_queues_dry_run_notification() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="TST1",
                company_name="Test Company",
                core_thesis="New production customers support growth",
                market_expectations={
                    "level": "elevated",
                    "summary": "A new customer ramp is partly reflected",
                },
                valuation_framework={"primary_method": "forward P/E"},
                multiple_expansion_signals=["new customer production order"],
                strengthen_signals=["new customer production order"],
                weaken_signals=["customer loss"],
                invalidation_signals=["largest customer terminates all orders"],
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 2),
            collection_service=FakeCollectionService(),
            price_client=FakePriceClient(),
        )

        monitor_run = session.exec(select(MonitorRun).where(MonitorRun.run_date == date(2030, 1, 2))).one()
        assert result.status == "success", monitor_run.details
        assessment = next(item for item in result.assessments if item.ticker == "TST1")
        assert assessment.status == "no_material_change"
        assert assessment.price_context.periods["daily"].actual_count == 420
        assert assessment.valuation_context.impact == "neutral"
        assert assessment.thesis_snapshot.valuation_context.impact == "neutral"
        assert "현재 평가" in assessment.thesis_snapshot.current_thesis
        stored = session.exec(
            select(ThesisAssessment).where(ThesisAssessment.ticker == "TST1")
        ).one()
        stored_snapshot = json.loads(stored.thesis_snapshot)
        assert stored_snapshot["assessment_mode"] == "initial_baseline"
        assert stored_snapshot["baseline_event_count"] == 1
        delivery = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "TST1")
        ).one()
        assert delivery.status == "dry_run"
        assert json.loads(delivery.payload)["type"] == "daily_stock_analysis"

        delivery.status = "pending"
        delivery.attempt_count = 4
        session.commit()
        retry_result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 2),
            collection_service=FailCollectionService(),
            price_client=FailPriceClient(),
            valuation_service=FailValuationService(),
        )
        session.refresh(delivery)
        assert retry_result.status == "already_completed"
        assert delivery.status == "dry_run"
        assert delivery.attempt_count == 5


@pytest.mark.anyio
async def test_baseline_consumes_backfill_then_only_new_events_drive_delta() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="BASE1",
                company_name="Baseline Company",
                core_thesis="New customer production orders support growth",
                strengthen_signals=["new customer production order"],
            ),
        )
        first_date = date(2032, 1, 2)
        first = await run_daily_monitor(
            session,
            run_date=first_date,
            collection_service=FakeCollectionService(),
            price_client=FakePriceClient(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        first_stored = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "BASE1",
                ThesisAssessment.assessment_date == first_date,
            )
        ).one()
        first_fingerprints = json.loads(first_stored.used_event_fingerprints)

        second = await run_daily_monitor(
            session,
            run_date=date(2032, 1, 3),
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        session.add(
            Event(
                ticker="BASE1",
                company_name="Baseline Company",
                date=date(2032, 1, 4),
                source="Company filing",
                provider="sec_edgar",
                title="New customer production order confirmed",
                url="https://example.com/base1-new-order",
                event_type="production_order",
                confirmed_facts=json.dumps(
                    ["New customer production order confirmed"]
                ),
                relevance_score=70,
            )
        )
        session.commit()
        third = await run_daily_monitor(
            session,
            run_date=date(2032, 1, 4),
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            queue_notifications=False,
            dispatch_notifications=False,
        )

    first_assessment = next(item for item in first.assessments if item.ticker == "BASE1")
    second_assessment = next(item for item in second.assessments if item.ticker == "BASE1")
    third_assessment = next(item for item in third.assessments if item.ticker == "BASE1")
    assert first_assessment.status == "no_material_change"
    assert first_fingerprints
    assert second_assessment.status == "no_material_change"
    assert second_assessment.evidence == []
    assert third_assessment.status == "strengthened"
    assert len(third_assessment.evidence) == 1


@pytest.mark.anyio
async def test_first_assessment_of_new_thesis_version_is_a_new_baseline() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="BASE2",
                company_name="Versioned Baseline Company",
                core_thesis="Original thesis",
            ),
        )
        await run_daily_monitor(
            session,
            run_date=date(2033, 1, 2),
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        original = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == "BASE2",
                InvestmentThesis.status == "active",
            )
        ).one()
        original.status = "superseded"
        session.add(original)
        session.add(
            InvestmentThesis(
                ticker="BASE2",
                version=2,
                core_thesis="Materially revised thesis",
                status="active",
            )
        )
        session.commit()

        result = await run_daily_monitor(
            session,
            run_date=date(2033, 1, 3),
            collection_service=EmptyCollectionService(),
            price_client=FakePriceClient(),
            queue_notifications=False,
            dispatch_notifications=False,
        )
        stored = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.ticker == "BASE2",
                ThesisAssessment.assessment_date == date(2033, 1, 3),
            )
        ).one()
        stored_version = stored.thesis_version
        stored_mode = json.loads(stored.thesis_snapshot)["assessment_mode"]

    result_assessment = next(
        item for item in result.assessments if item.ticker == "BASE2"
    )
    assert result_assessment.status == "no_material_change"
    assert stored_version == 2
    assert stored_mode == "initial_baseline"


@pytest.mark.anyio
async def test_daily_monitor_uses_structured_price_rules() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="PRC1",
                company_name="Price Rule Company",
                core_thesis="Price confirmation supports the operating thesis",
                price_rules=PriceRulesInput(
                    currency="USD",
                    confirmation_price=100,
                    support_zone_low=90,
                    support_zone_high=95,
                    warning_price=88,
                    invalidation_price=80,
                ),
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 3),
            collection_service=EmptyCollectionService(),
            price_client=RulePriceClient(previous_close=99, latest_close=101),
        )

        assessment = next(item for item in result.assessments if item.ticker == "PRC1")
        assert assessment.status == "no_material_change"
        assert assessment.price_context.rule_evaluation.status == "confirmation_triggered"
        assert "상향 돌파" in assessment.price_view
        assert not any(item["event_type"] == "price_rule" for item in assessment.evidence)
        delivery = session.exec(
            select(NotificationDelivery).where(NotificationDelivery.ticker == "PRC1")
        ).one()
        assert delivery.status == "dry_run"
        assert json.loads(delivery.payload)["type"] == "daily_stock_analysis"


@pytest.mark.anyio
async def test_price_invalidation_requires_review_without_automatic_deactivation() -> None:
    init_db()
    with Session(engine) as session:
        register_monitoring_item(
            session,
            MonitoringItemCreate(
                ticker="PRC2",
                company_name="Invalidated Price Company",
                core_thesis="The thesis requires the structural price floor to hold",
                price_rules=PriceRulesInput(
                    currency="USD",
                    warning_price=95,
                    invalidation_price=90,
                ),
            ),
        )
        result = await run_daily_monitor(
            session,
            run_date=date(2030, 1, 4),
            collection_service=EmptyCollectionService(),
            price_client=RulePriceClient(previous_close=96, latest_close=89),
        )

        assessment = next(item for item in result.assessments if item.ticker == "PRC2")
        assert assessment.status == "no_material_change"
        assert assessment.price_context.rule_evaluation.status == "invalidation_triggered"
        item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == "PRC2")).one()
        assert item.active is True
