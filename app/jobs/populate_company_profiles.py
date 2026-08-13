import argparse
import asyncio
import json

from sqlmodel import Session

from app.database import engine, init_db
from app.services.company_profile_service import (
    CompanyProfilePopulationService,
    profile_population_summary,
)


async def run(*, dry_run: bool = False) -> dict[str, object]:
    init_db()
    with Session(engine) as session:
        results = await CompanyProfilePopulationService().populate_active(
            session,
            dry_run=dry_run,
        )
    return profile_population_summary(results)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate verified company profiles for the active monitored universe."
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(dry_run=args.dry_run)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
