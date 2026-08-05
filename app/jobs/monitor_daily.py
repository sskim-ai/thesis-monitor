import asyncio
import json

from sqlmodel import Session

from app.database import engine, init_db
from app.services.daily_monitor_service import run_daily_monitor


async def main() -> None:
    init_db()
    with Session(engine) as session:
        result = await run_daily_monitor(session)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
