from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Callable, Literal
from zoneinfo import ZoneInfo

from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
from app.services.market_session import (
    is_exchange_session_date,
    preceding_exchange_session_date,
)


XKRX_ROLE_TARGET_CONTRACT = "xkrx-role-target-v1"
KST = ZoneInfo("Asia/Seoul")
XkrxRole = Literal[
    "kr_daily_production",
    "night_futures_production",
    "night_futures_post_deadline_observer",
    "krx_next_morning_publication",
    "krx_same_day_publication",
]


@dataclass(frozen=True)
class XkrxRoleTarget:
    role: XkrxRole
    observed_at_kst: datetime
    target_kind: str
    target_session_date: date | None
    target_xkrx_business_date: date | None
    target_completed: bool
    observation_eligible: bool
    skip_reason: str | None
    calendar_evidence: dict[str, object]


def resolve_xkrx_role_target(
    observed_at: datetime,
    role: XkrxRole,
    *,
    night_session_resolver: Callable[[date], date | None] = (
        expected_latest_completed_krx_session
    ),
) -> XkrxRoleTarget:
    if observed_at.tzinfo is None:
        return XkrxRoleTarget(
            role=role,
            observed_at_kst=observed_at.replace(tzinfo=KST),
            target_kind="UNRESOLVED",
            target_session_date=None,
            target_xkrx_business_date=None,
            target_completed=False,
            observation_eligible=False,
            skip_reason="timezone_unverified",
            calendar_evidence={"timezone_verified": False},
        )
    current = observed_at.astimezone(KST)
    wallclock_session = is_exchange_session_date("XKRX", current.date())
    evidence: dict[str, object] = {
        "timezone_verified": True,
        "wallclock_date": current.date().isoformat(),
        "wallclock_is_xkrx_session": wallclock_session,
    }
    if role in {
        "night_futures_production",
        "night_futures_post_deadline_observer",
    }:
        target = night_session_resolver(current.date())
        business_date = (
            preceding_exchange_session_date("XKRX", target) if target else None
        )
        completed = bool(
            target
            and target <= current.date()
            and (target < current.date() or current.time() >= time(6, 0))
        )
        evidence.update(
            {
                "target_basis": "us-morning-night-reference-date-v3",
                "reference_rule": (
                    "latest_valid_xkrx_business_date_strictly_before_kst_date"
                ),
                "comparison_day_basis": "preceding_eligible_xkrx_day",
                "night_session_end_time_kst": "06:00",
            }
        )
        return XkrxRoleTarget(
            role=role,
            observed_at_kst=current,
            target_kind="US_MORNING_NIGHT_REFERENCE_DATE",
            target_session_date=target,
            target_xkrx_business_date=business_date,
            target_completed=completed,
            observation_eligible=bool(target and business_date and completed),
            skip_reason=(
                None
                if target and business_date and completed
                else "target_not_completed"
                if target and business_date
                else "no_valid_role_target"
            ),
            calendar_evidence=evidence,
        )
    if role == "krx_next_morning_publication":
        target = preceding_exchange_session_date("XKRX", current.date())
        evidence["target_basis"] = "preceding_completed_xkrx_session"
        return XkrxRoleTarget(
            role=role,
            observed_at_kst=current,
            target_kind="XKRX_SESSION_DATE",
            target_session_date=target,
            target_xkrx_business_date=target,
            target_completed=target is not None,
            observation_eligible=target is not None,
            skip_reason=None if target else "no_valid_role_target",
            calendar_evidence=evidence,
        )
    target = current.date() if wallclock_session else None
    completed = bool(target and current.time() >= time(15, 30))
    evidence["target_basis"] = "same_day_completed_xkrx_session"
    return XkrxRoleTarget(
        role=role,
        observed_at_kst=current,
        target_kind="XKRX_SESSION_DATE",
        target_session_date=target,
        target_xkrx_business_date=target,
        target_completed=completed,
        observation_eligible=bool(target and completed),
        skip_reason=(
            None
            if target and completed
            else "target_not_completed"
            if target
            else "no_valid_role_target"
        ),
        calendar_evidence=evidence,
    )
