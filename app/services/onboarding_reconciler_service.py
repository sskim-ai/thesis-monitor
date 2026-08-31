from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.config import get_settings
from app.models.security import SecurityMaster
from app.models.watchlist import WatchlistItem
from app.services.company_profile_service import CompanyProfilePopulationService
from app.services.market_session import market_scope_for_security
from app.services.onboarding_decision_service import (
    generate_onboarding_accepted_decision,
)
from app.services.onboarding_evidence_service import (
    build_initial_evidence,
    ensure_initial_baseline,
)
from app.services.onboarding_readiness_service import (
    OnboardingReadiness,
    OnboardingRequirement,
    OnboardingState,
    evaluate_onboarding_readiness,
    reconcile_onboarding,
)
from app.services.security_master_service import SecurityMasterService


RECONCILER_CONTRACT = "pending-onboarding-reconciler-v1"
PREFLIGHT_CONTRACT = "market-preflight-onboarding-resume-v1"
KST = ZoneInfo("Asia/Seoul")


class OnboardingRetryClass(StrEnum):
    NONE = "NONE"
    RETRYABLE = "RETRYABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    WAIT_FOR_DATA = "WAIT_FOR_DATA"


class OnboardingAttemptMode(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    BACKGROUND = "BACKGROUND"
    PREFLIGHT = "PREFLIGHT"


EvidenceBuilder = Callable[..., Awaitable[dict[str, object]]]
DecisionBuilder = Callable[..., dict[str, object]]
ProfilePopulator = Callable[..., Awaitable[None]]
BaselineBuilder = Callable[..., object]


@dataclass(frozen=True)
class OnboardingAttemptResult:
    ticker: str
    market: str
    origin: str
    mode: str
    before_blockers: tuple[str, ...]
    attempted_stages: tuple[str, ...]
    completed_stages: tuple[str, ...]
    remaining_blockers: tuple[str, ...]
    state: str
    retry_class: str
    next_retry_at: str | None
    active: bool
    production_eligible: bool
    first_eligible_session: str | None
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OnboardingReconcilerRun:
    contract: str
    origin: str
    mode: str
    market: str
    started_at: str
    pending_subject_count: int
    retryable_count: int
    review_required_count: int
    oldest_pending_age_hours: float | None
    attempted_this_run: int
    completed_this_run: int
    remaining_pending: int
    systemic_error: str | None
    warnings: tuple[str, ...]
    results: tuple[OnboardingAttemptResult, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["results"] = [row.to_dict() for row in self.results]
        return payload


def _json_dict(value: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _item_market(session: Session, item: WatchlistItem) -> str:
    security = session.exec(
        select(SecurityMaster).where(SecurityMaster.ticker == item.ticker)
    ).first()
    return market_scope_for_security(
        item.ticker,
        item.exchange or (security.exchange if security else None),
    )


def _next_cycle_date(market: str, current: datetime) -> date:
    local = current.astimezone(KST)
    cutoff = time(16, 5) if market == "kr" else time(8, 5)
    return local.date() if local.time() < cutoff else local.date() + timedelta(days=1)


def _safe_error(exc: BaseException) -> str:
    detail = str(exc).splitlines()[0].strip().replace("\t", " ")[:180]
    return f"{type(exc).__name__}:{detail}" if detail else type(exc).__name__


def classify_onboarding_retry(
    readiness: OnboardingReadiness,
    *,
    error: str | None,
) -> OnboardingRetryClass:
    text = (error or "").lower()
    if any(
        token in text
        for token in (
            "identity_mismatch",
            "security_conflict",
            "currency_mismatch",
            "adr_ratio",
            "irreconcilable",
            "accepted_decision_evidence_mismatch",
            "future_dated",
        )
    ):
        return OnboardingRetryClass.REVIEW_REQUIRED
    blocker = readiness.failure_stage
    if blocker == OnboardingRequirement.SECURITY_MASTER and "conflict" in text:
        return OnboardingRetryClass.REVIEW_REQUIRED
    if any(
        token in text
        for token in (
            "wait_for",
            "dwm_unavailable",
            "current_price_missing",
            "safe_financial_checkpoint_missing",
            "required_session_data",
        )
    ):
        return OnboardingRetryClass.WAIT_FOR_DATA
    if blocker in {
        OnboardingRequirement.INITIAL_EVIDENCE,
        OnboardingRequirement.INITIAL_BASELINE_ASSESSMENT,
    } and error is None:
        return OnboardingRetryClass.WAIT_FOR_DATA
    return OnboardingRetryClass.RETRYABLE


def _next_retry_at(
    item: WatchlistItem,
    retry_class: OnboardingRetryClass,
    current: datetime,
) -> datetime | None:
    if retry_class in {OnboardingRetryClass.NONE, OnboardingRetryClass.REVIEW_REQUIRED}:
        return None
    settings = get_settings()
    exponent = min(max(0, item.onboarding_attempt_count - 1), 8)
    minutes = min(
        settings.onboarding_retry_max_minutes,
        settings.onboarding_retry_base_minutes * (2**exponent),
    )
    if retry_class == OnboardingRetryClass.WAIT_FOR_DATA:
        minutes = max(minutes, settings.onboarding_retry_base_minutes * 2)
    return current + timedelta(minutes=minutes)


def _persist_attempt_state(
    session: Session,
    item: WatchlistItem,
    readiness: OnboardingReadiness,
    *,
    current: datetime,
    origin: str,
    error: str | None,
) -> OnboardingRetryClass:
    if readiness.onboarding_ready:
        retry_class = OnboardingRetryClass.NONE
        item.onboarding_next_retry_at = None
        item.onboarding_last_error = None
    else:
        retry_class = classify_onboarding_retry(readiness, error=error)
        item.onboarding_next_retry_at = _next_retry_at(item, retry_class, current)
        item.onboarding_last_error = error
        item.onboarding_state = (
            OnboardingState.ONBOARDING_FAILED
            if retry_class == OnboardingRetryClass.REVIEW_REQUIRED
            else OnboardingState.PENDING_ONBOARDING
        )
        item.active = False
        item.production_eligible = False
    item.onboarding_retry_class = retry_class
    item.onboarding_last_attempt_at = current
    item.onboarding_last_attempt_origin = origin
    session.add(item)
    session.commit()
    return retry_class


async def _populate_company_profile(
    session: Session,
    item: WatchlistItem,
    *,
    current: datetime,
    data_dir: str | Path | None,
) -> None:
    await CompanyProfilePopulationService(data_dir=data_dir).populate_items(
        session,
        [item],
        verified_at=current,
    )


async def resume_onboarding_subject(
    session: Session,
    item: WatchlistItem,
    *,
    origin: str,
    mode: OnboardingAttemptMode,
    as_of: datetime | None = None,
    first_eligible_session: date | None = None,
    market_packet_cutoff: datetime | None = None,
    data_dir: str | Path | None = None,
    evidence_builder: EvidenceBuilder = build_initial_evidence,
    decision_builder: DecisionBuilder = generate_onboarding_accepted_decision,
    profile_populator: ProfilePopulator = _populate_company_profile,
    baseline_builder: BaselineBuilder = ensure_initial_baseline,
) -> OnboardingAttemptResult:
    current = (as_of or datetime.now(UTC)).astimezone(UTC)
    market = _item_market(session, item)
    before = evaluate_onboarding_readiness(session, item, data_dir=data_dir, as_of=current)
    attempted: list[str] = []
    error: str | None = None
    item.onboarding_attempt_count += 1
    item.onboarding_last_attempt_at = current
    item.onboarding_last_attempt_origin = origin
    if market_packet_cutoff is not None:
        item.onboarding_market_packet_cutoff = market_packet_cutoff.astimezone(UTC)
    session.add(item)
    session.commit()
    try:
        readiness = before
        if OnboardingRequirement.SECURITY_MASTER in readiness.blocking_requirements:
            attempted.append(OnboardingRequirement.SECURITY_MASTER)
            SecurityMasterService().ensure(session, item.ticker)
            session.commit()
            readiness = evaluate_onboarding_readiness(
                session, item, data_dir=data_dir, as_of=current
            )

        if (
            OnboardingRequirement.COMPANY_PROFILE in readiness.blocking_requirements
            and mode != OnboardingAttemptMode.PREFLIGHT
        ):
            attempted.append(OnboardingRequirement.COMPANY_PROFILE)
            await profile_populator(
                session,
                item,
                current=current,
                data_dir=data_dir,
            )
            readiness = evaluate_onboarding_readiness(
                session, item, data_dir=data_dir, as_of=current
            )

        evidence_prerequisites = {
            OnboardingRequirement.IDENTITY,
            OnboardingRequirement.SECURITY_MASTER,
            OnboardingRequirement.COMPANY_PROFILE,
            OnboardingRequirement.INVESTMENT_LOGIC,
        }
        if (
            OnboardingRequirement.INITIAL_EVIDENCE in readiness.blocking_requirements
            and evidence_prerequisites.issubset(set(readiness.completed_requirements))
        ):
            attempted.append(OnboardingRequirement.INITIAL_EVIDENCE)
            evidence = await evidence_builder(
                session,
                item,
                as_of=current,
                acquire=mode != OnboardingAttemptMode.PREFLIGHT,
            )
            item.onboarding_initial_evidence = json.dumps(
                evidence, ensure_ascii=False, sort_keys=True, default=str
            )
            item.onboarding_evidence_fingerprint = str(evidence.get("fingerprint") or "")
            session.add(item)
            session.commit()
            readiness = evaluate_onboarding_readiness(
                session, item, data_dir=data_dir, as_of=current
            )

        evidence = _json_dict(item.onboarding_initial_evidence)
        if (
            OnboardingRequirement.INITIAL_BASELINE_ASSESSMENT
            in readiness.blocking_requirements
            and evidence
        ):
            attempted.append(OnboardingRequirement.INITIAL_BASELINE_ASSESSMENT)
            baseline_builder(session, item, evidence, as_of=current)
            session.commit()
            readiness = evaluate_onboarding_readiness(
                session, item, data_dir=data_dir, as_of=current
            )

        if (
            OnboardingRequirement.DECISION_READINESS in readiness.blocking_requirements
            and evidence
            and mode == OnboardingAttemptMode.BACKGROUND
        ):
            attempted.append(OnboardingRequirement.DECISION_READINESS)
            decision = decision_builder(
                session,
                item,
                evidence,
                timeout=int(get_settings().onboarding_background_timeout_seconds),
                data_dir=data_dir,
            )
            item.onboarding_decision_readiness = json.dumps(
                decision, ensure_ascii=False, sort_keys=True, default=str
            )
            session.add(item)
            session.commit()

        selected_first_session = first_eligible_session or _next_cycle_date(
            market, current
        )
        readiness = reconcile_onboarding(
            session,
            item,
            data_dir=data_dir,
            as_of=current,
            first_eligible_session=selected_first_session,
        )
        session.commit()
    except Exception as exc:  # noqa: BLE001 - subject failure is isolated by contract.
        session.rollback()
        error = _safe_error(exc)
        item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == item.ticker)
        ).one()
        readiness = reconcile_onboarding(
            session,
            item,
            data_dir=data_dir,
            as_of=current,
            activate=False,
        )
        session.commit()

    retry_class = _persist_attempt_state(
        session,
        item,
        readiness,
        current=current,
        origin=origin,
        error=error,
    )
    return OnboardingAttemptResult(
        ticker=item.ticker,
        market=market,
        origin=origin,
        mode=mode,
        before_blockers=before.blocking_requirements,
        attempted_stages=tuple(str(value) for value in attempted),
        completed_stages=readiness.completed_requirements,
        remaining_blockers=readiness.blocking_requirements,
        state=item.onboarding_state,
        retry_class=retry_class,
        next_retry_at=(normalized_retry.isoformat() if (normalized_retry := _utc(item.onboarding_next_retry_at)) else None),
        active=item.active,
        production_eligible=item.production_eligible,
        first_eligible_session=(
            item.first_eligible_session.isoformat()
            if item.first_eligible_session is not None
            else None
        ),
        error=error,
    )


def _pending_items(
    session: Session,
    market: str,
    *,
    current: datetime,
    force_due: bool,
) -> list[WatchlistItem]:
    rows = session.exec(
        select(WatchlistItem)
        .where(
            WatchlistItem.monitoring_requested.is_(True),
            WatchlistItem.active.is_(False),
            WatchlistItem.onboarding_state.in_(
                [OnboardingState.PENDING_ONBOARDING, OnboardingState.ONBOARDING_FAILED]
            ),
        )
        .order_by(WatchlistItem.registration_requested_at, WatchlistItem.ticker)
    ).all()
    selected: list[WatchlistItem] = []
    for item in rows:
        if market != "all" and _item_market(session, item) != market:
            continue
        if item.onboarding_retry_class == OnboardingRetryClass.REVIEW_REQUIRED:
            continue
        next_retry = _utc(item.onboarding_next_retry_at)
        if not force_due and next_retry is not None and next_retry > current:
            continue
        selected.append(item)
    return selected


async def reconcile_pending_onboarding(
    session: Session,
    *,
    market: str = "all",
    origin: str = "background_scheduler",
    mode: OnboardingAttemptMode = OnboardingAttemptMode.BACKGROUND,
    as_of: datetime | None = None,
    force_due: bool = False,
    first_eligible_session: date | None = None,
    market_packet_cutoff: datetime | None = None,
    max_subjects: int = 20,
    data_dir: str | Path | None = None,
    evidence_builder: EvidenceBuilder = build_initial_evidence,
    decision_builder: DecisionBuilder = generate_onboarding_accepted_decision,
    profile_populator: ProfilePopulator = _populate_company_profile,
    baseline_builder: BaselineBuilder = ensure_initial_baseline,
) -> OnboardingReconcilerRun:
    current = (as_of or datetime.now(UTC)).astimezone(UTC)
    all_pending = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.monitoring_requested.is_(True),
            WatchlistItem.active.is_(False),
            WatchlistItem.onboarding_state.in_(
                [OnboardingState.PENDING_ONBOARDING, OnboardingState.ONBOARDING_FAILED]
            ),
        )
    ).all()
    scoped_pending = [
        item
        for item in all_pending
        if market == "all" or _item_market(session, item) == market
    ]
    candidates = (
        _pending_items(
            session,
            market,
            current=current,
            force_due=force_due,
        )[:max_subjects]
        if get_settings().onboarding_reconciler_enabled
        else []
    )
    if mode == OnboardingAttemptMode.PREFLIGHT and market_packet_cutoff is not None:
        cutoff_date = market_packet_cutoff.astimezone(KST).date()
        candidates = [
            item
            for item in candidates
            if not (
                item.onboarding_last_attempt_origin == f"market_preflight_{market}"
                and (previous_cutoff := _utc(item.onboarding_market_packet_cutoff))
                is not None
                and previous_cutoff.astimezone(KST).date() == cutoff_date
            )
        ]
    timeout_seconds = {
        OnboardingAttemptMode.IMMEDIATE: get_settings().onboarding_immediate_timeout_seconds,
        OnboardingAttemptMode.BACKGROUND: get_settings().onboarding_background_timeout_seconds,
        OnboardingAttemptMode.PREFLIGHT: get_settings().onboarding_preflight_timeout_seconds,
    }[mode]
    results: list[OnboardingAttemptResult] = []
    systemic_error: str | None = None
    for item in candidates:
        try:
            async with asyncio.timeout(timeout_seconds):
                result = await resume_onboarding_subject(
                    session,
                    item,
                    origin=origin,
                    mode=mode,
                    as_of=current,
                    first_eligible_session=first_eligible_session,
                    market_packet_cutoff=market_packet_cutoff,
                    data_dir=data_dir,
                    evidence_builder=evidence_builder,
                    decision_builder=decision_builder,
                    profile_populator=profile_populator,
                    baseline_builder=baseline_builder,
                )
        except Exception as exc:  # noqa: BLE001 - continue with the next subject.
            session.rollback()
            persisted = session.exec(
                select(WatchlistItem).where(WatchlistItem.ticker == item.ticker)
            ).one()
            readiness = reconcile_onboarding(
                session,
                persisted,
                data_dir=data_dir,
                as_of=current,
                first_eligible_session=first_eligible_session,
            )
            retry_class = _persist_attempt_state(
                session,
                persisted,
                readiness,
                current=current,
                origin=origin,
                error=_safe_error(exc),
            )
            result = OnboardingAttemptResult(
                ticker=persisted.ticker,
                market=_item_market(session, persisted),
                origin=origin,
                mode=mode,
                before_blockers=(),
                attempted_stages=(),
                completed_stages=readiness.completed_requirements,
                remaining_blockers=readiness.blocking_requirements,
                state=persisted.onboarding_state,
                retry_class=retry_class,
                next_retry_at=(
                    normalized.isoformat()
                    if (normalized := _utc(persisted.onboarding_next_retry_at))
                    else None
                ),
                active=False,
                production_eligible=False,
                first_eligible_session=None,
                error=_safe_error(exc),
            )
        results.append(result)
    remaining = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.monitoring_requested.is_(True),
            WatchlistItem.active.is_(False),
            WatchlistItem.onboarding_state.in_(
                [OnboardingState.PENDING_ONBOARDING, OnboardingState.ONBOARDING_FAILED]
            ),
        )
    ).all()
    scoped_remaining = [
        item
        for item in remaining
        if market == "all" or _item_market(session, item) == market
    ]
    ages = [
        (current - requested).total_seconds() / 3600
        for item in scoped_remaining
        if (requested := _utc(item.registration_requested_at)) is not None
    ]
    warnings: list[str] = []
    if ages and max(ages) > get_settings().onboarding_pending_sla_hours:
        warnings.append("pending_onboarding_sla_exceeded")
    if any(
        item.onboarding_attempt_count
        >= get_settings().onboarding_repeated_failure_warning_threshold
        and item.onboarding_retry_class == OnboardingRetryClass.RETRYABLE
        for item in scoped_remaining
    ):
        warnings.append("repeated_retryable_failure_threshold_exceeded")
    if any(
        item.onboarding_retry_class == OnboardingRetryClass.REVIEW_REQUIRED
        for item in scoped_remaining
    ):
        warnings.append("review_required_pending")
    return OnboardingReconcilerRun(
        contract=RECONCILER_CONTRACT,
        origin=origin,
        mode=mode,
        market=market,
        started_at=current.isoformat(),
        pending_subject_count=len(scoped_pending),
        retryable_count=sum(
            item.onboarding_retry_class
            in {OnboardingRetryClass.RETRYABLE, OnboardingRetryClass.WAIT_FOR_DATA, "NONE"}
            for item in scoped_pending
        ),
        review_required_count=sum(
            item.onboarding_retry_class == OnboardingRetryClass.REVIEW_REQUIRED
            for item in scoped_pending
        ),
        oldest_pending_age_hours=round(max(ages), 2) if ages else None,
        attempted_this_run=len(results),
        completed_this_run=sum(row.active for row in results),
        remaining_pending=len(scoped_remaining),
        systemic_error=systemic_error,
        warnings=tuple(warnings),
        results=tuple(results),
    )


async def market_preflight_onboarding_resume(
    session: Session,
    *,
    market: str,
    run_date: date,
    cutoff: datetime,
    current_cycle_eligible: bool,
    data_dir: str | Path | None = None,
    evidence_builder: EvidenceBuilder = build_initial_evidence,
    decision_builder: DecisionBuilder = generate_onboarding_accepted_decision,
) -> dict[str, object]:
    first_session = run_date if current_cycle_eligible else run_date + timedelta(days=1)
    run = await reconcile_pending_onboarding(
        session,
        market=market,
        origin=f"market_preflight_{market}",
        mode=OnboardingAttemptMode.PREFLIGHT,
        as_of=cutoff,
        force_due=True,
        first_eligible_session=first_session,
        market_packet_cutoff=cutoff,
        data_dir=data_dir,
        evidence_builder=evidence_builder,
        decision_builder=decision_builder,
    )
    return {
        **run.to_dict(),
        "contract": PREFLIGHT_CONTRACT,
        "market": market,
        "cutoff": cutoff.astimezone(UTC).isoformat(),
        "current_cycle_eligible": current_cycle_eligible,
        "first_eligible_session": first_session.isoformat(),
    }
