import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.database import engine, init_db
from app.macro.service import run_macro_monitor
from app.macro.kr_close import run_kr_close_market_briefing
from app.models.macro import MacroBriefing
from app.models.thesis import MonitorRun
from app.services.daily_monitor_service import run_daily_monitor
from app.services.ai_review_service import try_write_ai_review_packet
from app.services.ai_assisted_delivery_service import (
    ai_assisted_pilot_active,
    hold_ai_assisted_pilot_session,
)
from app.services.market_session import MarketScope
from app.services.morning_gate import (
    initialize_morning_gate,
    run_morning_night_futures_gate,
)


KST = ZoneInfo("Asia/Seoul")
MORNING_REQUEUE_CUTOFF = time(7, 45)
KR_CLOSE_REQUEUE_CUTOFF = time(16, 0)


@dataclass(frozen=True)
class AnalysisDecision:
    action: str
    refresh: bool
    run_status: str


def _requeue_cutoff(run_date: date, market_scope: str) -> datetime:
    cutoff = KR_CLOSE_REQUEUE_CUTOFF if market_scope == "kr" else MORNING_REQUEUE_CUTOFF
    return datetime.combine(run_date, cutoff, tzinfo=KST).astimezone(
        timezone.utc
    )


def _run_type(market_scope: MarketScope) -> str:
    return "daily" if market_scope == "all" else f"daily_{market_scope}"


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _analysis_completed_after_cutoff(
    session: Session,
    run_date: date,
    cutoff: datetime,
    market_scope: MarketScope,
) -> bool:
    """Return whether a successful run both started and finished in production time."""
    run = session.exec(
        select(MonitorRun).where(
            MonitorRun.run_date == run_date,
            MonitorRun.run_type == _run_type(market_scope),
        )
    ).first()
    return bool(
        run is not None
        and run.status == "success"
        and run.started_at is not None
        and run.completed_at is not None
        and _as_utc(run.started_at) >= _as_utc(cutoff)
        and _as_utc(run.completed_at) >= _as_utc(cutoff)
    )


def _analysis_decision(
    session: Session,
    run_date: date,
    cutoff: datetime,
    market_scope: MarketScope,
) -> AnalysisDecision:
    run = session.exec(
        select(MonitorRun).where(
            MonitorRun.run_date == run_date,
            MonitorRun.run_type == _run_type(market_scope),
        )
    ).first()
    if run is None:
        return AnalysisDecision("fresh", True, "not_started")
    if run.status == "running":
        if run.started_at is not None and _as_utc(run.started_at) < _as_utc(cutoff):
            return AnalysisDecision("refresh_after_pre_cutoff_run", True, "running")
        return AnalysisDecision("in_progress", False, "running")
    if _analysis_completed_after_cutoff(session, run_date, cutoff, market_scope):
        return AnalysisDecision("reuse", False, "success")
    if run.status == "success":
        return AnalysisDecision("refresh_after_pre_cutoff_run", True, "success")
    return AnalysisDecision("retry_after_failure", True, run.status)


def _stored_macro_result(session: Session, run_date: date) -> dict[str, object]:
    briefing = session.exec(
        select(MacroBriefing).where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "morning",
        )
    ).first()
    return {
        "run_date": run_date.isoformat(),
        "status": "reused" if briefing is not None else "unavailable",
    }


async def _macro_result_for_scope(
    session: Session,
    run_date: date,
    market_scope: MarketScope,
    analysis_refresh: bool,
) -> dict[str, object]:
    if market_scope == "kr" or not analysis_refresh:
        return _stored_macro_result(session, run_date)
    try:
        return (
            await run_macro_monitor(
                session,
                run_date=run_date,
                force=True,
                excluded_provider_names={"krx_night_futures"},
                queue_notifications=False,
                dispatch_notifications=False,
            )
        ).model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return {
            "run_date": run_date.isoformat(),
            "status": "failed",
            "error": type(exc).__name__,
        }


async def _run_market_job(
    session: Session,
    run_date: date,
    market_scope: MarketScope,
    *,
    as_of: datetime | None = None,
) -> dict[str, object]:
    current_as_of = as_of
    cutoff = _requeue_cutoff(run_date, market_scope)
    decision = _analysis_decision(session, run_date, cutoff, market_scope)
    kr_close_result: dict[str, object] | None = None
    if market_scope == "kr":
        try:
            close_run = await run_kr_close_market_briefing(
                session,
                run_date,
                queue_notifications=False,
                dispatch_notifications=False,
            )
            kr_close_result = close_run.model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            kr_close_result = {
                "run_date": run_date.isoformat(),
                "status": "failed",
                "action": "isolated_failure",
                "error": type(exc).__name__,
            }
    if decision.action == "in_progress":
        return {
            "market_scope": market_scope,
            "production_cutoff": cutoff.isoformat(),
            "analysis_action": decision.action,
            "analysis_run_status": decision.run_status,
            "delivery_action": "deferred",
            "macro": _stored_macro_result(session, run_date),
            "kr_close_market": kr_close_result,
            "theses": None,
        }

    if market_scope == "us" and decision.action == "reuse":
        gate = await run_morning_night_futures_gate(
            session,
            run_date,
            current_as_of or datetime.now(KST),
        )
        return {
            "market_scope": market_scope,
            "production_cutoff": cutoff.isoformat(),
            "analysis_action": decision.action,
            "analysis_run_status": decision.run_status,
            "delivery_action": gate.dispatch_action,
            "morning_gate": gate.as_dict(),
            "macro": _stored_macro_result(session, run_date),
            "kr_close_market": None,
            "theses": None,
        }

    macro_result = await _macro_result_for_scope(
        session,
        run_date,
        market_scope,
        decision.refresh,
    )
    daily_kwargs: dict[str, object] = {
        "run_date": run_date,
        "force": decision.refresh,
        "requeue_sent_before": cutoff if decision.refresh else None,
        "market_scope": market_scope,
    }
    pilot_active = market_scope in {"us", "kr"} and ai_assisted_pilot_active(
        market_scope
    )
    if market_scope == "us" or pilot_active:
        daily_kwargs["dispatch_notifications"] = False
    result = await run_daily_monitor(session, **daily_kwargs)
    pilot_hold: dict[str, object] | None = None
    if market_scope == "kr" and result.status in {"success", "already_completed"}:
        packet_result = try_write_ai_review_packet(
            session,
            run_date,
            "kr",
            generated_at=current_as_of or datetime.now(KST),
        )
        if pilot_active and packet_result.packet_id:
            pilot_hold = hold_ai_assisted_pilot_session(
                session,
                packet_result.packet_id,
                held_at=current_as_of or datetime.now(KST),
            ).as_dict()
    gate_result: dict[str, object] | None = None
    if market_scope == "us" and result.status not in {
        "failed",
        "analysis_in_progress",
    }:
        initialize_morning_gate(
            session,
            run_date,
            current_as_of or datetime.now(KST),
            reset=decision.refresh,
        )
        gate_result = (
            await run_morning_night_futures_gate(
                session,
                run_date,
                current_as_of or datetime.now(KST),
            )
        ).as_dict()
    delivery_action = {
        "reuse": "retry",
        "retry_after_failure": "recovery",
    }.get(decision.action, "primary")
    if gate_result is not None:
        delivery_action = str(gate_result["dispatch_action"])
    elif pilot_hold is not None:
        delivery_action = "held_for_ai_review"
    return {
        "market_scope": market_scope,
        "production_cutoff": cutoff.isoformat(),
        "analysis_action": decision.action,
        "analysis_run_status": result.status,
        "delivery_action": delivery_action,
        "morning_gate": gate_result,
        "ai_assisted_pilot": pilot_hold,
        "macro": macro_result,
        "kr_close_market": kr_close_result,
        "theses": result.model_dump(mode="json"),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run market-scoped daily thesis monitoring.")
    parser.add_argument("--market", choices=("us", "kr", "all"), default="all")
    args = parser.parse_args()
    init_db()
    run_date = datetime.now(KST).date()
    with Session(engine) as session:
        output = await _run_market_job(session, run_date, args.market)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
