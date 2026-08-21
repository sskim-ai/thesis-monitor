from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.config import get_settings
from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
from app.macro.briefing import market_observation_to_dict
from app.macro.providers.base import MacroProvider
from app.macro.providers.krx import KrxNightFuturesProvider
from app.macro.storage import persist_observation
from app.models.macro import MacroBriefing
from app.models.security import SecurityMaster
from app.models.thesis import NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.market_session import market_scope_for_security
from app.services.night_futures import NIGHT_FUTURES_SERIES, summarize_night_futures
from app.services.night_futures_publication_telemetry_service import (
    record_attempt_best_effort,
)
from app.services.ai_review_service import try_write_ai_review_packet
from app.services.ai_assisted_delivery_service import (
    ai_assisted_pilot_active,
    hold_ai_assisted_pilot_session,
)
from app.services.notification_service import (
    MORNING_GATE_METADATA_KEY,
    dispatch_pending_notifications,
    queue_daily_digest_notification,
)


KST = ZoneInfo("Asia/Seoul")
MORNING_GATE_START = time(8, 5)
MORNING_GATE_DEADLINE = time(8, 20)
MORNING_GATE_INTERVAL_MINUTES = 5
MORNING_DIGEST_TICKER = "__DAILY_DIGEST__"


@dataclass(frozen=True)
class MorningGateResult:
    status: str
    expected_session: date | None
    retry_count: int
    ready_products: list[str]
    deadline_reached: bool
    refresh_performed: bool
    dispatch_action: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "expected_session": (
                self.expected_session.isoformat() if self.expected_session else None
            ),
            "retry_count": self.retry_count,
            "ready_products": self.ready_products,
            "deadline_reached": self.deadline_reached,
            "refresh_performed": self.refresh_performed,
            "dispatch_action": self.dispatch_action,
        }


def morning_gate_start(run_date: date) -> datetime:
    return datetime.combine(run_date, MORNING_GATE_START, tzinfo=KST)


def morning_gate_deadline(run_date: date) -> datetime:
    return datetime.combine(run_date, MORNING_GATE_DEADLINE, tzinfo=KST)


def _as_kst(value: datetime) -> datetime:
    return value.replace(tzinfo=KST) if value.tzinfo is None else value.astimezone(KST)


def _json_dict(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _briefing(session: Session, run_date: date) -> MacroBriefing | None:
    return session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "morning",
        )
    ).first()


def _digest_delivery(session: Session, run_date: date) -> NotificationDelivery | None:
    channel = get_settings().notification_channel.strip().lower()
    return session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == MORNING_DIGEST_TICKER,
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel == channel,
        )
    ).first()


def _gate_metadata(session: Session, run_date: date) -> dict[str, object]:
    briefing = _briefing(session, run_date)
    if briefing is not None:
        market = _json_dict(briefing.market_summary)
        value = market.get("night_futures_gate")
        if isinstance(value, dict):
            return dict(value)
    delivery = _digest_delivery(session, run_date)
    if delivery is not None:
        payload = _json_dict(delivery.payload)
        value = payload.get(MORNING_GATE_METADATA_KEY)
        if isinstance(value, dict):
            return dict(value)
    return {}


def _write_gate_metadata(
    session: Session,
    run_date: date,
    metadata: dict[str, object],
) -> None:
    briefing = _briefing(session, run_date)
    if briefing is not None:
        market = _json_dict(briefing.market_summary)
        market["night_futures_gate"] = metadata
        briefing.market_summary = json.dumps(market, ensure_ascii=False, default=str)
        session.add(briefing)
    delivery = _digest_delivery(session, run_date)
    if delivery is not None:
        payload = _json_dict(delivery.payload)
        payload[MORNING_GATE_METADATA_KEY] = metadata
        delivery.payload = json.dumps(payload, ensure_ascii=False, default=str)
        session.add(delivery)
    session.commit()


def initialize_morning_gate(
    session: Session,
    run_date: date,
    as_of: datetime,
    *,
    reset: bool,
) -> dict[str, object]:
    current = {} if reset else _gate_metadata(session, run_date)
    if current.get("state") == "dispatched" and not reset:
        return current
    expected = expected_latest_completed_krx_session(run_date)
    metadata = {
        **current,
        "state": "waiting",
        "expected_session": expected.isoformat() if expected else None,
        "initialized_at": _as_kst(as_of).isoformat(),
        "query_attempted": False,
        "first_query_at": None,
        "first_complete_at": None,
        "KOSPI200_first_available_at": None,
        "KOSDAQ150_first_available_at": None,
        "retry_count": 0,
        "deadline_reached": False,
        "dispatch_at": None,
        "last_error": None,
    }
    _write_gate_metadata(session, run_date, metadata)
    return metadata


def _replace_night_observations(
    session: Session,
    run_date: date,
    rows: list[dict[str, object]],
) -> None:
    briefing = _briefing(session, run_date)
    if briefing is None:
        return
    market = _json_dict(briefing.market_summary)
    observations = market.get("observations", [])
    existing = observations if isinstance(observations, list) else []
    by_series = {
        str(item.get("series_code")): item
        for item in existing
        if isinstance(item, dict) and item.get("series_code") in NIGHT_FUTURES_SERIES
    }
    by_series.update(
        {
            str(item.get("series_code")): item
            for item in rows
            if item.get("series_code") in NIGHT_FUTURES_SERIES
        }
    )
    market["observations"] = [
        item
        for item in existing
        if not isinstance(item, dict) or item.get("series_code") not in NIGHT_FUTURES_SERIES
    ] + [by_series[series] for series in NIGHT_FUTURES_SERIES if series in by_series]
    briefing.market_summary = json.dumps(market, ensure_ascii=False, default=str)
    session.add(briefing)
    session.commit()


def _us_tickers_for_date(session: Session, run_date: date) -> set[str]:
    tickers: set[str] = set()
    assessments = session.exec(
        select(ThesisAssessment).where(ThesisAssessment.assessment_date == run_date)
    ).all()
    for assessment in assessments:
        item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
        ).first()
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == assessment.ticker)
        ).first()
        exchange = (item.exchange if item is not None else None) or (
            security.exchange if security is not None else None
        )
        if market_scope_for_security(assessment.ticker, exchange) == "us":
            tickers.add(assessment.ticker)
    return tickers


def _morning_delivery_ids(session: Session, run_date: date) -> set[int]:
    channel = get_settings().notification_channel.strip().lower()
    tickers = _us_tickers_for_date(session, run_date) | {MORNING_DIGEST_TICKER}
    deliveries = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel == channel,
            NotificationDelivery.ticker.in_(tickers),
        )
    ).all()
    return {item.id for item in deliveries if item.id is not None}


def _all_deliveries_sent(
    session: Session,
    delivery_ids: set[int],
) -> bool:
    if not delivery_ids:
        return False
    deliveries = session.exec(
        select(NotificationDelivery).where(NotificationDelivery.id.in_(delivery_ids))
    ).all()
    return len(deliveries) == len(delivery_ids) and all(
        item.status == "sent" for item in deliveries
    )


async def run_morning_night_futures_gate(
    session: Session,
    run_date: date,
    as_of: datetime,
    *,
    provider: MacroProvider | None = None,
    notifier: object | None = None,
) -> MorningGateResult:
    current_as_of = _as_kst(as_of)
    expected_session = expected_latest_completed_krx_session(run_date)
    metadata = _gate_metadata(session, run_date)
    if not metadata:
        metadata = initialize_morning_gate(
            session,
            run_date,
            current_as_of,
            reset=False,
        )

    state = str(metadata.get("state") or "waiting")
    retry_count = int(metadata.get("retry_count") or 0)
    if state == "ai_review_hold":
        delivery_ids = _morning_delivery_ids(session, run_date)
        if _all_deliveries_sent(session, delivery_ids):
            metadata["state"] = "dispatched"
            metadata["dispatch_at"] = current_as_of.isoformat()
            _write_gate_metadata(session, run_date, metadata)
            return MorningGateResult(
                status="dispatched",
                expected_session=expected_session,
                retry_count=retry_count,
                ready_products=list(metadata.get("ready_products") or []),
                deadline_reached=bool(metadata.get("deadline_reached")),
                refresh_performed=False,
                dispatch_action="already_dispatched",
            )
        return MorningGateResult(
            status="ai_review_hold",
            expected_session=expected_session,
            retry_count=retry_count,
            ready_products=list(metadata.get("ready_products") or []),
            deadline_reached=bool(metadata.get("deadline_reached")),
            refresh_performed=False,
            dispatch_action="held_for_ai_review",
        )
    if state == "dispatched":
        try_write_ai_review_packet(
            session,
            run_date,
            "us",
            generated_at=current_as_of,
        )
        return MorningGateResult(
            status="dispatched",
            expected_session=expected_session,
            retry_count=retry_count,
            ready_products=list(metadata.get("ready_products") or []),
            deadline_reached=bool(metadata.get("deadline_reached")),
            refresh_performed=False,
            dispatch_action="already_dispatched",
        )
    if current_as_of < morning_gate_start(run_date):
        return MorningGateResult(
            status="waiting",
            expected_session=expected_session,
            retry_count=retry_count,
            ready_products=list(metadata.get("ready_products") or []),
            deadline_reached=False,
            refresh_performed=False,
            dispatch_action="held_until_08:05",
        )

    delivery_ids = _morning_delivery_ids(session, run_date)
    if state in {"ready", "deadline_reached"}:
        packet_result = try_write_ai_review_packet(
            session,
            run_date,
            "us",
            generated_at=current_as_of,
        )
        if ai_assisted_pilot_active("us") and packet_result.packet_id:
            hold_ai_assisted_pilot_session(
                session,
                packet_result.packet_id,
                held_at=current_as_of,
            )
            metadata["state"] = "ai_review_hold"
            _write_gate_metadata(session, run_date, metadata)
            return MorningGateResult(
                status="ai_review_hold",
                expected_session=expected_session,
                retry_count=retry_count,
                ready_products=list(metadata.get("ready_products") or []),
                deadline_reached=bool(metadata.get("deadline_reached")),
                refresh_performed=False,
                dispatch_action="held_for_ai_review",
            )
        await dispatch_pending_notifications(
            session,
            notifier=notifier,  # type: ignore[arg-type]
            delivery_ids=delivery_ids,
        )
        if _all_deliveries_sent(session, delivery_ids):
            metadata["state"] = "dispatched"
            metadata["dispatch_at"] = current_as_of.isoformat()
            _write_gate_metadata(session, run_date, metadata)
            state = "dispatched"
        return MorningGateResult(
            status=state,
            expected_session=expected_session,
            retry_count=retry_count,
            ready_products=list(metadata.get("ready_products") or []),
            deadline_reached=bool(metadata.get("deadline_reached")),
            refresh_performed=False,
            dispatch_action="retry_pending" if state != "dispatched" else "dispatched",
        )

    query_time = current_as_of.isoformat()
    metadata["query_attempted"] = True
    metadata["first_query_at"] = metadata.get("first_query_at") or query_time
    metadata["last_query_at"] = query_time
    metadata["retry_count"] = retry_count + 1
    metadata["last_error"] = None
    rows: list[dict[str, object]] = []
    selected_provider = provider or KrxNightFuturesProvider()
    telemetry_started_at = datetime.now(tz=KST)
    telemetry_result = None
    telemetry_error = None
    try:
        result = await selected_provider.collect(current_as_of)
        telemetry_result = result
        metadata["provider_warnings"] = list(result.warnings)
        for observation in result.observations:
            row, _ = persist_observation(
                session,
                selected_provider.name,
                observation,
                current_as_of,
            )
            serialized = market_observation_to_dict(row)
            serialized["expected_latest_session_date"] = (
                expected_session.isoformat() if expected_session else None
            )
            if (
                expected_session is None
                or serialized.get("trade_date") != expected_session.isoformat()
            ):
                serialized["session_freshness"] = "stale"
                serialized["quality_status"] = "stale"
            rows.append(serialized)
    except Exception as exc:  # noqa: BLE001
        telemetry_error = type(exc).__name__
        metadata["last_error"] = type(exc).__name__
        metadata["provider_warnings"] = [f"provider_error:{type(exc).__name__}"]
    if provider is None:
        record_attempt_best_effort(
            market_date=run_date,
            started_at=telemetry_started_at,
            ended_at=datetime.now(tz=KST),
            role=f"production_gate_attempt_{retry_count + 1}",
            production_or_observer="production",
            expected_session=expected_session,
            result=telemetry_result,
            error=telemetry_error,
        )
    _replace_night_observations(session, run_date, rows)

    briefing = _briefing(session, run_date)
    market = _json_dict(briefing.market_summary) if briefing is not None else {}
    summary = summarize_night_futures(market)
    ready_products = [item.series_code for item in summary.items]
    metadata["ready_products"] = ready_products
    for series_code, field in (
        ("KRX_KOSPI200_NIGHT_FUT", "KOSPI200_first_available_at"),
        ("KRX_KOSDAQ150_NIGHT_FUT", "KOSDAQ150_first_available_at"),
    ):
        if series_code in ready_products and not metadata.get(field):
            metadata[field] = query_time

    ready = set(ready_products) == set(NIGHT_FUTURES_SERIES)
    deadline_reached = current_as_of >= morning_gate_deadline(run_date)
    metadata["deadline_reached"] = deadline_reached
    if ready:
        metadata["state"] = "ready"
        metadata["first_complete_at"] = metadata.get("first_complete_at") or query_time
    elif deadline_reached:
        metadata["state"] = "deadline_reached"
    else:
        metadata["state"] = "waiting"
    _write_gate_metadata(session, run_date, metadata)

    digest = queue_daily_digest_notification(session, run_date, market_scope="us")
    if digest is not None:
        _write_gate_metadata(session, run_date, metadata)
    if not ready and not deadline_reached:
        return MorningGateResult(
            status="waiting",
            expected_session=expected_session,
            retry_count=int(metadata["retry_count"]),
            ready_products=ready_products,
            deadline_reached=False,
            refresh_performed=True,
            dispatch_action="held_for_complete_snapshot",
        )

    packet_result = try_write_ai_review_packet(
        session,
        run_date,
        "us",
        generated_at=current_as_of,
    )
    if ai_assisted_pilot_active("us") and packet_result.packet_id:
        hold_ai_assisted_pilot_session(
            session,
            packet_result.packet_id,
            held_at=current_as_of,
        )
        metadata["state"] = "ai_review_hold"
        _write_gate_metadata(session, run_date, metadata)
        return MorningGateResult(
            status="ai_review_hold",
            expected_session=expected_session,
            retry_count=int(metadata["retry_count"]),
            ready_products=ready_products,
            deadline_reached=deadline_reached,
            refresh_performed=True,
            dispatch_action="held_for_ai_review",
        )
    delivery_ids = _morning_delivery_ids(session, run_date)
    await dispatch_pending_notifications(
        session,
        notifier=notifier,  # type: ignore[arg-type]
        delivery_ids=delivery_ids,
    )
    if _all_deliveries_sent(session, delivery_ids):
        metadata["state"] = "dispatched"
        metadata["dispatch_at"] = current_as_of.isoformat()
        _write_gate_metadata(session, run_date, metadata)
        status = "dispatched"
    else:
        status = str(metadata["state"])
    return MorningGateResult(
        status=status,
        expected_session=expected_session,
        retry_count=int(metadata["retry_count"]),
        ready_products=ready_products,
        deadline_reached=deadline_reached,
        refresh_performed=True,
        dispatch_action="dispatched" if status == "dispatched" else "dispatch_pending",
    )
