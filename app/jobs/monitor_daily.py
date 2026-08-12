import argparse
import asyncio
import json
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine, init_db
from app.macro.service import run_macro_monitor
from app.models.thesis import NotificationDelivery
from app.services.daily_monitor_service import run_daily_monitor
from app.services.market_session import MarketScope


KST = ZoneInfo("Asia/Seoul")
MORNING_REQUEUE_CUTOFF = time(7, 45)
KR_CLOSE_REQUEUE_CUTOFF = time(16, 0)


def _requeue_cutoff(run_date: date, market_scope: str) -> datetime:
    cutoff = KR_CLOSE_REQUEUE_CUTOFF if market_scope == "kr" else MORNING_REQUEUE_CUTOFF
    return datetime.combine(run_date, cutoff, tzinfo=KST).astimezone(
        timezone.utc
    )


def _sent_after_cutoff(
    session: Session,
    run_date: date,
    cutoff: datetime,
    digest_ticker: str = "__DAILY_DIGEST__",
) -> bool:
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == digest_ticker,
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel
            == get_settings().notification_channel.strip().lower(),
            NotificationDelivery.status == "sent",
        )
    ).first()
    if delivery is None or delivery.sent_at is None:
        return False
    sent_at = delivery.sent_at
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    return sent_at >= cutoff


async def _macro_result_for_scope(
    session: Session,
    run_date: date,
    market_scope: MarketScope,
    force_refresh: bool,
) -> dict[str, object]:
    if market_scope == "kr":
        return {"run_date": run_date.isoformat(), "status": "reused"}
    try:
        return (
            await run_macro_monitor(
                session,
                run_date=run_date,
                force=force_refresh,
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


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run market-scoped daily thesis monitoring.")
    parser.add_argument("--market", choices=("us", "kr", "all"), default="all")
    args = parser.parse_args()
    init_db()
    run_date = date.today()
    cutoff = _requeue_cutoff(run_date, args.market)
    digest_ticker = "__DAILY_DIGEST_KR__" if args.market == "kr" else "__DAILY_DIGEST__"
    with Session(engine) as session:
        already_sent = _sent_after_cutoff(session, run_date, cutoff, digest_ticker)
        force_refresh = not already_sent
        macro_result = await _macro_result_for_scope(
            session,
            run_date,
            args.market,
            force_refresh,
        )
        result = await run_daily_monitor(
            session,
            run_date=run_date,
            force=force_refresh,
            requeue_sent_before=cutoff if force_refresh else None,
            market_scope=args.market,
        )
    print(
        json.dumps(
            {
                "macro": macro_result,
                "theses": result.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
