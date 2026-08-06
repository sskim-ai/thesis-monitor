import asyncio
import json
from datetime import date

from sqlmodel import Session

from app.database import engine, init_db
from app.macro.service import run_macro_monitor
from app.services.daily_monitor_service import run_daily_monitor


async def main() -> None:
    init_db()
    with Session(engine) as session:
        try:
            macro_result: dict[str, object] = (
                await run_macro_monitor(session)
            ).model_dump(mode="json")
        except Exception as exc:  # noqa: BLE001
            macro_result = {
                "run_date": date.today().isoformat(),
                "status": "failed",
                "error": type(exc).__name__,
            }
        result = await run_daily_monitor(session)
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
