from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlmodel import Session

from app.database import engine
from app.services.official_security_identity_service import (
    OfficialSecurityIdentityEvidence,
    OfficialSecurityIdentityService,
)


def run(*, evidence_path: Path, apply: bool) -> dict[str, object]:
    payload = json.loads(evidence_path.read_text())
    evidence = OfficialSecurityIdentityEvidence.from_payload(payload)
    with Session(engine) as session:
        result = OfficialSecurityIdentityService().ingest(
            session,
            evidence,
            dry_run=not apply,
        )
        if apply and result["mutated"]:
            session.commit()
        else:
            session.rollback()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan or apply authoritative security identity evidence."
    )
    parser.add_argument("--evidence-json", required=True, type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the idempotent plan. Without this flag the command is read-only.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            run(evidence_path=args.evidence_json, apply=args.apply),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
