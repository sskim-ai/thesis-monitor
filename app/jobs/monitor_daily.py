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


KST = ZoneInfo("Asia/Seoul")
MORNING_REQUEUE_CUTOFF = time(7, 45)


def _morning_cutoff(run_date: date) -> datetime:
    return datetime.combine(run_date, MORNING_REQUEUE_CUTOFF, tzinfo=KST).astimezone(
        timezone.utc
    )


def _sent_after_cutoff(
    session: Session,
    run_date: date,
    cutoff: datetime,
) -> bool:
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == "__DAILY_DIGEST__",
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


async def main() -> None:
    init_db()
    run_date = date.today()
    cutoff = _morning_cutoff(run_date)
    with Session(engine) as session:
        morning_already_sent = _sent_after_cutoff(session, run_date, cutoff)
        force_refresh = not morning_already_sent
        try:
            macro_result: dict[str, object] = (
                await run_macro_monitor(
                    session,
                    run_date=run_date,
                    force=force_refresh,
                    queue_notifications=False,
                    dispatch_notifications=False,
                )
            ).model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            macro_result = {
                "run_date": date.today().isoformat(),
                "status": "failed",
                "error": type(exc).__name__,
            }
        result = await run_daily_monitor(
            session,
            run_date=run_date,
            force=force_refresh,
            requeue_sent_before=cutoff if force_refresh else None,
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
