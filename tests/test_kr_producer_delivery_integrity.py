import json
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.jobs.monitor_daily import _run_market_job
from app.models.thesis import MonitorRun, NotificationDelivery
from app.services.ai_assisted_delivery_service import (
    _pending_pilot_packets,
    dispatch_due_deterministic_fallbacks,
)
from app.services.notification_delivery_integrity_service import (
    KR_DAILY_DIGEST_MARKER,
    KR_ORPHAN_RECONCILIATION_REASON,
    KrOrphanIncident,
    OrphanReconciliationError,
    reconcile_kr_orphan_incident,
)
from app.services.daily_monitor_service import _queue_scoped_notifications
from app.services.notification_service import (
    AI_ASSISTED_PILOT_METADATA_KEY,
    PACKET_BOUND_DELIVERY_INTENT_CONTRACT,
)
from app.services.xkrx_role_target_service import resolve_xkrx_role_target


KST = ZoneInfo("Asia/Seoul")
SATURDAY = date(2026, 8, 22)
PACKET_ID = "2026-08-22-kr-run-33-c2491c2e78ad"
STOCK_TICKERS = [
    "000660",
    "003690",
    "005490",
    "005930",
    "010120",
    "012450",
    "086280",
]


def _engine():
    value = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(value)
    return value


@pytest.mark.anyio
@pytest.mark.parametrize("minute", [5, 20, 50])
async def test_saturday_producer_attempts_stop_before_stateful_work(
    monkeypatch,
    minute: int,
) -> None:
    async def forbidden(*args, **kwargs):
        raise AssertionError("non-trading-day guard must run first")

    monkeypatch.setattr(
        "app.jobs.monitor_daily.run_kr_close_market_briefing", forbidden
    )
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", forbidden)
    monkeypatch.setattr("app.jobs.monitor_daily.run_macro_monitor", forbidden)
    with Session(_engine()) as session:
        output = await _run_market_job(
            session,
            SATURDAY,
            "kr",
            as_of=datetime(2026, 8, 22, 16, minute, tzinfo=KST),
        )
        assert session.exec(select(MonitorRun)).all() == []
        assert session.exec(select(NotificationDelivery)).all() == []

    assert output["analysis_action"] == "safe_noop"
    assert output["delivery_action"] == "safe_noop"
    assert output["skip_reason"] == "no_valid_role_target"
    assert output["producer_role_target"]["production_eligible"] is False


@pytest.mark.anyio
async def test_target_resolver_failure_fails_closed(monkeypatch) -> None:
    def unavailable(*args, **kwargs):
        raise RuntimeError("calendar unavailable")

    async def forbidden(*args, **kwargs):
        raise AssertionError("analysis must not start")

    monkeypatch.setattr(
        "app.jobs.monitor_daily.resolve_xkrx_role_target", unavailable
    )
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", forbidden)
    with Session(_engine()) as session:
        output = await _run_market_job(
            session,
            date(2026, 8, 21),
            "kr",
            as_of=datetime(2026, 8, 21, 16, 5, tzinfo=KST),
        )

    assert output["analysis_action"] == "safe_noop"
    assert output["skip_reason"] == "target_resolver_unavailable"


def test_weekend_holiday_and_normal_production_role_matrix() -> None:
    cases = [
        (datetime(2026, 8, 22, 16, 5, tzinfo=KST), False),
        (datetime(2026, 8, 23, 16, 5, tzinfo=KST), False),
        (datetime(2026, 8, 17, 16, 5, tzinfo=KST), False),
        (datetime(2026, 9, 24, 16, 5, tzinfo=KST), False),
        (datetime(2026, 9, 25, 16, 5, tzinfo=KST), False),
        (datetime(2026, 8, 24, 16, 5, tzinfo=KST), True),
        (datetime(2026, 8, 18, 16, 5, tzinfo=KST), True),
        (datetime(2026, 12, 31, 16, 5, tzinfo=KST), False),
    ]
    for observed_at, expected in cases:
        target = resolve_xkrx_role_target(observed_at, "kr_daily_production")
        assert target.observation_eligible is expected
        assert target.target_xkrx_business_date == (
            observed_at.date() if expected else None
        )


@pytest.mark.anyio
async def test_packet_failure_leaves_no_delivery_intent(monkeypatch) -> None:
    async def close_result(*args, **kwargs):
        return SimpleNamespace(
            model_dump=lambda mode: {"status": "ready", "action": "fresh"}
        )

    async def daily_result(*args, **kwargs):
        assert kwargs["queue_notifications"] is False
        assert kwargs["dispatch_notifications"] is False
        return SimpleNamespace(
            status="success",
            model_dump=lambda mode: {"status": "success"},
        )

    def forbidden(*args, **kwargs):
        raise AssertionError("no delivery intent may be created or held")

    monkeypatch.setattr(
        "app.jobs.monitor_daily.run_kr_close_market_briefing", close_result
    )
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", daily_result)
    monkeypatch.setattr(
        "app.jobs.monitor_daily.ai_assisted_pilot_active", lambda market: True
    )
    monkeypatch.setattr(
        "app.jobs.monitor_daily.try_write_ai_review_packet",
        lambda *args, **kwargs: SimpleNamespace(
            status="failed",
            packet_id=PACKET_ID,
            path=None,
            reason="OSError",
        ),
    )
    monkeypatch.setattr(
        "app.jobs.monitor_daily.queue_daily_monitor_notifications", forbidden
    )
    monkeypatch.setattr(
        "app.jobs.monitor_daily.hold_ai_assisted_pilot_session", forbidden
    )
    with Session(_engine()) as session:
        output = await _run_market_job(
            session,
            date(2026, 8, 21),
            "kr",
            as_of=datetime(2026, 8, 21, 16, 5, tzinfo=KST),
        )

    assert output["delivery_action"] == "packet_not_ready"
    assert output["ai_assisted_pilot"]["pending_count"] == 0


@pytest.mark.anyio
async def test_packet_persists_before_bound_delivery_and_hold(
    monkeypatch,
    tmp_path: Path,
) -> None:
    events: list[str] = []
    packet_path = tmp_path / f"{PACKET_ID}.json"
    packet_path.write_text("{}", encoding="utf-8")

    async def close_result(*args, **kwargs):
        events.append("close")
        return SimpleNamespace(
            model_dump=lambda mode: {"status": "ready", "action": "fresh"}
        )

    async def daily_result(*args, **kwargs):
        events.append("analysis")
        return SimpleNamespace(
            status="success",
            model_dump=lambda mode: {"status": "success"},
        )

    def write_packet(*args, **kwargs):
        events.append("packet")
        return SimpleNamespace(
            status="created",
            packet_id=PACKET_ID,
            path=str(packet_path),
            reason=None,
        )

    def queue_bound(*args, **kwargs):
        assert kwargs["packet_id"] == PACKET_ID
        events.append("delivery_intent")
        return {1}

    def hold(*args, **kwargs):
        events.append("hold")
        return SimpleNamespace(as_dict=lambda: {"status": "held"})

    monkeypatch.setattr(
        "app.jobs.monitor_daily.run_kr_close_market_briefing", close_result
    )
    monkeypatch.setattr("app.jobs.monitor_daily.run_daily_monitor", daily_result)
    monkeypatch.setattr(
        "app.jobs.monitor_daily.ai_assisted_pilot_active", lambda market: True
    )
    monkeypatch.setattr(
        "app.jobs.monitor_daily.try_write_ai_review_packet", write_packet
    )
    monkeypatch.setattr(
        "app.jobs.monitor_daily.queue_daily_monitor_notifications", queue_bound
    )
    monkeypatch.setattr(
        "app.jobs.monitor_daily.hold_ai_assisted_pilot_session", hold
    )
    with Session(_engine()) as session:
        output = await _run_market_job(
            session,
            date(2026, 8, 21),
            "kr",
            as_of=datetime(2026, 8, 21, 16, 5, tzinfo=KST),
        )

    assert events == ["close", "analysis", "packet", "delivery_intent", "hold"]
    assert output["delivery_action"] == "held_for_ai_review"


@pytest.mark.anyio
async def test_raw_or_missing_packet_pending_is_not_deliverable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.services.ai_assisted_delivery_service.get_settings",
        lambda: SimpleNamespace(
            notification_channel="telegram",
            data_dir=str(tmp_path),
            ai_review_pilot_kr_fallback_time="17:10",
        ),
    )
    run_date = date(2026, 8, 22)
    payloads = [
        {"type": "daily_stock_analysis"},
        {
            "type": "daily_stock_analysis",
            AI_ASSISTED_PILOT_METADATA_KEY: {
                "market": "kr",
                "packet_id": "missing-packet",
                "state": "held",
            },
        },
    ]
    with Session(_engine()) as session:
        for index, payload in enumerate(payloads):
            session.add(
                NotificationDelivery(
                    ticker=f"T{index}",
                    assessment_date=run_date,
                    status="pending",
                    payload=json.dumps(payload),
                )
            )
        session.commit()

        assert _pending_pilot_packets(session, "kr", run_date) == []
        result = await dispatch_due_deterministic_fallbacks(
            session,
            market="kr",
            run_date=run_date,
            now=datetime(2026, 8, 22, 17, 10, tzinfo=KST),
        )

    assert result[0].status == "no_held_session"
    assert result[0].pending_count == 0


def test_packet_bound_intent_is_provisional_until_hold(
    monkeypatch,
) -> None:
    def queue_digest(session, run_date, **kwargs):
        delivery = NotificationDelivery(
            ticker=KR_DAILY_DIGEST_MARKER,
            assessment_date=run_date,
            channel="telegram",
            status="pending",
            payload=json.dumps({"type": "daily_monitoring_digest"}),
        )
        session.add(delivery)
        return delivery

    monkeypatch.setattr(
        "app.services.daily_monitor_service.queue_daily_digest_notification",
        queue_digest,
    )
    with Session(_engine()) as session:
        ids = _queue_scoped_notifications(
            session,
            date(2026, 8, 21),
            [],
            "kr",
            None,
            packet_id="persisted-packet",
        )
        delivery = session.exec(select(NotificationDelivery)).one()

    metadata = json.loads(delivery.payload)[AI_ASSISTED_PILOT_METADATA_KEY]
    assert ids == {delivery.id}
    assert metadata == {
        "delivery_intent_contract": PACKET_BOUND_DELIVERY_INTENT_CONTRACT,
        "packet_id": "persisted-packet",
        "market": "kr",
        "assessment_date": "2026-08-21",
        "state": "packet_bound_pending_hold",
        "fallback_eligible": False,
    }


def test_valid_packet_bound_pending_is_deliverable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.services.ai_assisted_delivery_service.get_settings",
        lambda: SimpleNamespace(notification_channel="telegram", data_dir=str(tmp_path)),
    )
    run_date = date(2026, 8, 21)
    packet_id = "valid-packet"
    packet_path = tmp_path / "ai_review" / "inbox" / f"{packet_id}.json"
    packet_path.parent.mkdir(parents=True)
    packet_path.write_text(
        json.dumps(
            {
                "packet_id": packet_id,
                "market": "kr",
                "assessment_date": run_date.isoformat(),
                "ready_for_ai": True,
            }
        ),
        encoding="utf-8",
    )
    with Session(_engine()) as session:
        session.add(
            NotificationDelivery(
                ticker="000660",
                assessment_date=run_date,
                channel="telegram",
                status="pending",
                payload=json.dumps(
                    {
                        AI_ASSISTED_PILOT_METADATA_KEY: {
                            "market": "kr",
                            "packet_id": packet_id,
                            "state": "held",
                        }
                    }
                ),
            )
        )
        session.commit()
        assert _pending_pilot_packets(session, "kr", run_date) == [packet_id]


def _seed_incident(session: Session) -> None:
    session.add(
        MonitorRun(
            id=33,
            run_date=SATURDAY,
            run_type="daily_kr",
            status="success",
            ticker_count=7,
            success_count=7,
            failure_count=0,
            started_at=datetime(2026, 8, 22, 7, 5, tzinfo=timezone.utc),
            completed_at=datetime(2026, 8, 22, 7, 6, tzinfo=timezone.utc),
            details=json.dumps(
                {
                    "market_scope": "kr",
                    "tickers": {
                        ticker: {"status": "no_material_change"}
                        for ticker in STOCK_TICKERS
                    },
                }
            ),
        )
    )
    for ticker in [KR_DAILY_DIGEST_MARKER, *STOCK_TICKERS]:
        session.add(
            NotificationDelivery(
                ticker=ticker,
                assessment_date=SATURDAY,
                channel="telegram",
                status="pending",
                payload=json.dumps(
                    {
                        "type": (
                            "daily_monitoring_digest"
                            if ticker == KR_DAILY_DIGEST_MARKER
                            else "daily_stock_analysis"
                        )
                    }
                ),
            )
        )
    session.add(
        NotificationDelivery(
            ticker="UNRELATED",
            assessment_date=SATURDAY,
            channel="telegram",
            status="pending",
            payload=json.dumps({"type": "unrelated"}),
        )
    )
    session.commit()


def _incident() -> KrOrphanIncident:
    return KrOrphanIncident(
        run_id=33,
        run_date=SATURDAY,
        packet_id=PACKET_ID,
        expected_stock_count=7,
        expected_digest_count=1,
    )


def test_orphan_reconciliation_is_exact_audited_and_idempotent(
    tmp_path: Path,
) -> None:
    with Session(_engine()) as session:
        _seed_incident(session)
        dry_run = reconcile_kr_orphan_incident(
            session, _incident(), data_dir=tmp_path
        )
        assert dry_run["result"] == "dry_run_ready"
        assert dry_run["expected_stock_count"] == 7
        assert dry_run["expected_digest_count"] == 1
        assert dry_run["target_row_count"] == 8

        applied = reconcile_kr_orphan_incident(
            session, _incident(), data_dir=tmp_path, apply=True
        )
        assert applied["result"] == "reconciled"
        assert applied["changed_count"] == 8
        assert all(row["sent_at"] is None for row in applied["rows"])

        second = reconcile_kr_orphan_incident(
            session, _incident(), data_dir=tmp_path, apply=True
        )
        assert second["result"] == "already_reconciled"
        assert second["changed_count"] == 0
        unrelated = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == "UNRELATED"
            )
        ).one()
        assert unrelated.status == "pending"
        assert unrelated.last_error is None
        targets = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker != "UNRELATED"
            )
        ).all()
        assert {item.status for item in targets} == {"failed"}
        assert {item.last_error for item in targets} == {
            KR_ORPHAN_RECONCILIATION_REASON
        }


def test_orphan_reconciliation_aborts_on_count_sent_or_packet_mismatch(
    tmp_path: Path,
) -> None:
    with Session(_engine()) as session:
        _seed_incident(session)
        with pytest.raises(OrphanReconciliationError, match="stock_count_mismatch"):
            reconcile_kr_orphan_incident(
                session,
                KrOrphanIncident(33, SATURDAY, PACKET_ID, 6),
                data_dir=tmp_path,
            )

        sent = session.exec(
            select(NotificationDelivery).where(
                NotificationDelivery.ticker == STOCK_TICKERS[0]
            )
        ).one()
        sent.status = "sent"
        session.add(sent)
        session.commit()
        with pytest.raises(OrphanReconciliationError, match="already_sent"):
            reconcile_kr_orphan_incident(session, _incident(), data_dir=tmp_path)

        sent.status = "pending"
        session.add(sent)
        session.commit()
        packet = tmp_path / "ai_review" / "inbox" / f"{PACKET_ID}.json"
        packet.parent.mkdir(parents=True)
        packet.write_text("{}", encoding="utf-8")
        with pytest.raises(OrphanReconciliationError, match="valid_packet"):
            reconcile_kr_orphan_incident(session, _incident(), data_dir=tmp_path)
