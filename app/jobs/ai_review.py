import argparse
import asyncio
import json
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlmodel import Session

from app.database import engine, init_db
from app.services.ai_review_service import (
    ANALYSIS_POLICY_VERSION,
    ai_review_health,
    claim_next_ai_review_packet,
    finalize_ai_review_output,
)
from app.services.ai_assisted_delivery_service import (
    deliver_validated_ai_review,
    dispatch_due_deterministic_fallbacks,
    record_ai_validation_rejection,
    retry_pending_ai_assisted_deliveries,
)
from app.services.cash_flow_runtime_shadow_canary_service import (
    launch_cash_flow_runtime_shadow_canary,
)


KST = ZoneInfo("Asia/Seoul")


def _launch_terminal_canaries(values: list[dict[str, object]]) -> None:
    for value in values:
        try:
            launch_cash_flow_runtime_shadow_canary(value)
        except Exception:
            # The canary is observational. Its failure must never change this job's exit path.
            continue


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Manage local Codex daily-review packets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    claim = subparsers.add_parser("claim")
    claim.add_argument("--market", choices=("us", "kr"), required=True)
    claim.add_argument("--owner", default=None)
    claim.add_argument("--wait-seconds", type=int, default=0)
    claim.add_argument("--poll-seconds", type=int, default=15)
    claim.add_argument("--lease-minutes", type=int, default=None)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--packet-id", required=True)
    validate.add_argument("--claim-id", required=True)
    validate.add_argument("--policy-version", default=ANALYSIS_POLICY_VERSION)

    health = subparsers.add_parser("health")
    health.add_argument("--market", choices=("us", "kr"), required=True)
    health.add_argument("--date", default=None)

    deliver = subparsers.add_parser("deliver")
    deliver.add_argument("--packet-id", required=True)
    deliver.add_argument("--allow-duplicate", action="store_true")

    fallback = subparsers.add_parser("fallback")
    fallback.add_argument("--market", choices=("us", "kr", "all"), default="all")
    fallback.add_argument("--date", default=None)

    retry_delivery = subparsers.add_parser("retry-delivery")
    retry_delivery.add_argument("--market", choices=("us", "kr", "all"), default="all")
    retry_delivery.add_argument("--date", default=None)

    args = parser.parse_args()
    init_db()
    if args.command == "claim":
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(0, args.wait_seconds)
        while True:
            result = claim_next_ai_review_packet(
                args.market,
                owner=args.owner,
                lease_minutes=args.lease_minutes,
            )
            if result.status != "no_pending_packet" or loop.time() >= deadline:
                break
            await asyncio.sleep(
                min(max(1, args.poll_seconds), max(0.0, deadline - loop.time()))
            )
        print(json.dumps(result.__dict__, ensure_ascii=False))
        return
    if args.command == "health":
        review_date = date.fromisoformat(args.date) if args.date else datetime.now(UTC).date()
        print(json.dumps(ai_review_health(review_date, args.market), ensure_ascii=False))
        return
    if args.command == "deliver":
        with Session(engine) as session:
            result = await deliver_validated_ai_review(
                session,
                args.packet_id,
                allow_duplicate=args.allow_duplicate,
            )
        _launch_terminal_canaries([result.as_dict()])
        print(json.dumps(result.as_dict(), ensure_ascii=False))
        return
    if args.command == "fallback":
        run_date = date.fromisoformat(args.date) if args.date else datetime.now(KST).date()
        markets = ("us", "kr") if args.market == "all" else (args.market,)
        results = []
        with Session(engine) as session:
            for market in markets:
                values = await dispatch_due_deterministic_fallbacks(
                    session,
                    market=market,
                    run_date=run_date,
                )
                results.extend(item.as_dict() for item in values)
        _launch_terminal_canaries(results)
        print(json.dumps(results, ensure_ascii=False))
        return
    if args.command == "retry-delivery":
        run_date = date.fromisoformat(args.date) if args.date else datetime.now(KST).date()
        markets = ("us", "kr") if args.market == "all" else (args.market,)
        results = []
        with Session(engine) as session:
            for market in markets:
                values = await retry_pending_ai_assisted_deliveries(
                    session,
                    market=market,
                    run_date=run_date,
                )
                results.extend(item.as_dict() for item in values)
        _launch_terminal_canaries(results)
        print(json.dumps(results, ensure_ascii=False))
        return
    with Session(engine) as session:
        result = finalize_ai_review_output(
            session,
            args.packet_id,
            claim_id=args.claim_id,
            policy_version=args.policy_version,
        )
        delivery = None
        if result.status in {"completed", "already_completed"}:
            delivery = await deliver_validated_ai_review(session, args.packet_id)
        elif result.status == "rejected":
            delivery = record_ai_validation_rejection(
                session,
                args.packet_id,
                errors=result.errors,
            )
    payload = dict(result.__dict__)
    if delivery is not None:
        payload["pilot_delivery"] = delivery.as_dict()
        _launch_terminal_canaries([delivery.as_dict()])
    print(json.dumps(payload, ensure_ascii=False))
    if result.status == "rejected":
        raise SystemExit(1)


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
