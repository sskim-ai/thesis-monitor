from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine, init_db
from app.models.watchlist import WatchlistItem
from app.services.company_profile_service import CompanyProfilePopulationService
from app.services.onboarding_readiness_service import (
    OnboardingState,
    evaluate_onboarding_readiness,
    reconcile_onboarding,
)
from app.services.security_master_service import SecurityMasterService


CONTROL_SUBJECTS = ("047810", "CPNG")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def _populate_missing_profiles(
    session: Session,
    items: list[WatchlistItem],
    *,
    data_dir: Path,
    current: datetime,
) -> list[dict[str, object]]:
    missing: list[WatchlistItem] = []
    security_service = SecurityMasterService()
    for item in items:
        security_service.ensure(session, item.ticker)
        readiness = evaluate_onboarding_readiness(
            session, item, data_dir=data_dir, as_of=current
        )
        if "COMPANY_PROFILE" in readiness.blocking_requirements:
            missing.append(item)
    session.commit()
    if not missing:
        return []
    results = await CompanyProfilePopulationService(data_dir=data_dir).populate_items(
        session,
        missing,
        verified_at=current,
    )
    return [
        {
            "ticker": result.ticker,
            "market": result.market,
            "quality": result.quality,
            "status": result.status,
            "source": result.source,
            "reason": result.reason,
        }
        for result in results
    ]


def _projected_state(ready: bool, monitoring_requested: bool) -> str:
    if not monitoring_requested:
        return OnboardingState.INACTIVE
    return OnboardingState.ACTIVE if ready else OnboardingState.PENDING_ONBOARDING


def run(args: argparse.Namespace) -> dict[str, object]:
    init_db()
    settings = get_settings()
    data_dir = Path(args.data_dir or settings.data_dir)
    output_dir = Path(args.output_dir)
    current = datetime.now(UTC)
    next_session = (
        date.fromisoformat(args.next_eligible_session)
        if args.next_eligible_session
        else None
    )

    with Session(engine) as session:
        items = list(
            session.exec(select(WatchlistItem).order_by(WatchlistItem.ticker)).all()
        )
        for item in items:
            if (
                args.apply
                and not item.active
                and item.onboarding_state == OnboardingState.ACTIVE
                and not json.loads(item.onboarding_readiness or "{}")
            ):
                item.monitoring_requested = False
                item.production_eligible = False
                item.onboarding_state = OnboardingState.INACTIVE
                session.add(item)
        if args.apply:
            session.commit()
        requested = [item for item in items if item.monitoring_requested or item.active]
        pre_profile_readiness = {
            item.ticker: evaluate_onboarding_readiness(
                session, item, data_dir=data_dir, as_of=current
            )
            for item in requested
        }
        provider_results: list[dict[str, object]] = []
        if args.apply and args.populate_profiles:
            provider_results = asyncio.run(
                _populate_missing_profiles(
                    session,
                    requested,
                    data_dir=data_dir,
                    current=current,
                )
            )

        rows: list[dict[str, object]] = []
        for item in items:
            was_active = item.active
            before_state = item.onboarding_state
            legacy_inactive = bool(
                not was_active
                and before_state == OnboardingState.ACTIVE
                and not json.loads(item.onboarding_readiness or "{}")
            )
            if args.apply and legacy_inactive:
                item.monitoring_requested = False
            before = evaluate_onboarding_readiness(
                session, item, data_dir=data_dir, as_of=current
            )
            selected_first_session = item.first_eligible_session
            if selected_first_session is None and before.onboarding_ready:
                pre_profile = pre_profile_readiness.get(item.ticker)
                selected_first_session = (
                    item.latest_assessment_date
                    if was_active
                    and pre_profile is not None
                    and pre_profile.onboarding_ready
                    else next_session
                )
            if args.apply:
                if item.monitoring_requested or was_active:
                    after = reconcile_onboarding(
                        session,
                        item,
                        data_dir=data_dir,
                        as_of=current,
                        first_eligible_session=selected_first_session,
                    )
                else:
                    after = before
                    item.active = False
                    item.production_eligible = False
                    item.onboarding_state = OnboardingState.INACTIVE
                    session.add(item)
            else:
                after = before
            rows.append(
                {
                    "ticker": item.ticker,
                    "company_name": item.company_name,
                    "exchange": item.exchange,
                    "monitoring_requested": item.monitoring_requested,
                    "before": {
                        "active": was_active,
                        "state": before_state,
                        "onboarding_ready": before.onboarding_ready,
                        "blockers": list(before.blocking_requirements),
                    },
                    "after": {
                        "active": (
                            item.active
                            if args.apply
                            else bool(after.onboarding_ready and item.monitoring_requested)
                        ),
                        "state": (
                            item.onboarding_state
                            if args.apply
                            else _projected_state(
                                after.onboarding_ready, item.monitoring_requested
                            )
                        ),
                        "production_eligible": (
                            item.production_eligible
                            if args.apply
                            else bool(after.onboarding_ready and item.monitoring_requested)
                        ),
                        "onboarding_ready": after.onboarding_ready,
                        "blockers": list(after.blocking_requirements),
                        "safe_unavailable": list(
                            after.safe_unavailable_requirements
                        ),
                        "completed": list(after.completed_requirements),
                        "failure_stage": after.failure_stage,
                        "first_eligible_session": (
                            item.first_eligible_session
                            if args.apply
                            else selected_first_session
                        ),
                    },
                }
            )
        if args.apply:
            session.commit()

    active_rows = [row for row in rows if row["after"]["active"] is True]
    active_incomplete = [
        row
        for row in active_rows
        if row["after"]["onboarding_ready"] is not True
    ]
    controls = {
        ticker: next((row for row in rows if row["ticker"] == ticker), None)
        for ticker in CONTROL_SUBJECTS
    }
    audit = {
        "contract": "active-onboarding-readiness-audit-v1",
        "generated_at": current.isoformat(),
        "applied": bool(args.apply),
        "subject_count": len(rows),
        "requested_count": sum(row["monitoring_requested"] is True for row in rows),
        "active_count": len(active_rows),
        "ready_active_count": len(active_rows) - len(active_incomplete),
        "active_incomplete_count": len(active_incomplete),
        "active_incomplete_subjects": [row["ticker"] for row in active_incomplete],
        "provider_profile_calls": {
            "request_count": len(provider_results),
            "success_count": sum(
                row["status"] in {"populated", "preserved", "partial"}
                for row in provider_results
            ),
            "failure_count": sum(
                row["status"] not in {"populated", "preserved", "partial"}
                for row in provider_results
            ),
            "results": provider_results,
        },
        "subjects": rows,
    }
    new_subjects = {
        "contract": "new-subject-onboarding-readiness-v1",
        "generated_at": current.isoformat(),
        "subjects": controls,
    }
    deployment = {
        "contract": "onboarding-readiness-deployment-v1",
        "generated_at": current.isoformat(),
        "mode": "APPLIED" if args.apply else "PROJECTED",
        "active_implies_onboarding_ready": not active_incomplete,
        "active_subject_missing_required_prerequisite": len(active_incomplete),
        "current_active_subject_count": len(active_rows),
        "current_ready_active_subject_count": len(active_rows) - len(active_incomplete),
        "active_incomplete_subject_count": len(active_incomplete),
        "open_p0": [] if not active_incomplete else ["active_incomplete_subject"],
        "open_material_p1": [],
    }
    paths = {
        "audit": output_dir / "20260831-active-onboarding-readiness-audit.json",
        "new_subjects": output_dir / "20260831-new-subject-readiness.json",
        "deployment": output_dir / "20260831-onboarding-readiness-deployment.json",
    }
    _write_json(paths["audit"], audit)
    _write_json(paths["new_subjects"], new_subjects)
    _write_json(paths["deployment"], deployment)
    return {
        "status": "PASS" if not active_incomplete else "FAIL",
        "outputs": {
            key: {"path": str(path), "sha256": _sha256(path)}
            for key, path in paths.items()
        },
        "summary": deployment,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--populate-profiles", action="store_true")
    parser.add_argument("--data-dir")
    parser.add_argument("--output-dir", default="docs/reports")
    parser.add_argument("--next-eligible-session")
    args = parser.parse_args()
    print(json.dumps(run(args), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
