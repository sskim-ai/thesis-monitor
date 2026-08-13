import argparse
import json
from datetime import UTC, date, datetime

from sqlmodel import Session

from app.database import engine, init_db
from app.services.ai_review_service import (
    ANALYSIS_POLICY_VERSION,
    ai_review_health,
    claim_next_ai_review_packet,
    finalize_ai_review_output,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage local Codex daily-review packets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    claim = subparsers.add_parser("claim")
    claim.add_argument("--market", choices=("us", "kr"), required=True)
    claim.add_argument("--owner", default=None)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--packet-id", required=True)
    validate.add_argument("--policy-version", default=ANALYSIS_POLICY_VERSION)

    health = subparsers.add_parser("health")
    health.add_argument("--market", choices=("us", "kr"), required=True)
    health.add_argument("--date", default=None)

    args = parser.parse_args()
    init_db()
    if args.command == "claim":
        result = claim_next_ai_review_packet(args.market, owner=args.owner)
        print(json.dumps(result.__dict__, ensure_ascii=False))
        return
    if args.command == "health":
        review_date = date.fromisoformat(args.date) if args.date else datetime.now(UTC).date()
        print(json.dumps(ai_review_health(review_date, args.market), ensure_ascii=False))
        return
    with Session(engine) as session:
        result = finalize_ai_review_output(
            session,
            args.packet_id,
            policy_version=args.policy_version,
        )
    print(json.dumps(result.__dict__, ensure_ascii=False))
    if result.status == "rejected":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
