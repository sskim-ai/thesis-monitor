from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime

from sqlmodel import Session

from app.database import engine, init_db
from app.services.onboarding_reconciler_service import (
    OnboardingAttemptMode,
    reconcile_pending_onboarding,
)


async def _run(args: argparse.Namespace) -> None:
    init_db()
    with Session(engine) as session:
        result = await reconcile_pending_onboarding(
            session,
            market=args.market,
            origin=args.origin,
            mode=OnboardingAttemptMode.BACKGROUND,
            as_of=datetime.now(UTC),
            force_due=args.force_due,
            max_subjects=args.max_subjects,
        )
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume requested pending onboarding subjects without delivery side effects."
    )
    parser.add_argument("--market", choices=("all", "kr", "us"), default="all")
    parser.add_argument(
        "--origin",
        choices=("background_scheduler", "deployment_smoke"),
        default="background_scheduler",
    )
    parser.add_argument("--force-due", action="store_true")
    parser.add_argument("--max-subjects", type=int, default=20)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
