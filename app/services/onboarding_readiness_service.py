from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from sqlmodel import Session, select

from app.config import get_settings
from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.company_profile_service import read_profile_provenance
from app.services.market_session import market_scope_for_security
from app.services.security_master_service import SecurityMasterService
from app.utils.tickers import normalize_ticker


ONBOARDING_READINESS_CONTRACT = "monitoring-onboarding-readiness-v1"
PRODUCTION_UNIVERSE_CONTRACT = "production-packet-universe-v1"


class OnboardingState(StrEnum):
    PENDING_ONBOARDING = "PENDING_ONBOARDING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    ONBOARDING_FAILED = "ONBOARDING_FAILED"
    INACTIVE = "INACTIVE"


class OnboardingRequirement(StrEnum):
    IDENTITY = "IDENTITY"
    SECURITY_MASTER = "SECURITY_MASTER"
    COMPANY_PROFILE = "COMPANY_PROFILE"
    INVESTMENT_LOGIC = "INVESTMENT_LOGIC"
    INITIAL_EVIDENCE = "INITIAL_EVIDENCE"
    INITIAL_BASELINE_ASSESSMENT = "INITIAL_BASELINE_ASSESSMENT"
    DECISION_READINESS = "DECISION_READINESS"


@dataclass(frozen=True)
class OnboardingReadiness:
    contract: str
    ticker: str
    market: str
    onboarding_ready: bool
    blocking_requirements: tuple[str, ...]
    safe_unavailable_requirements: tuple[str, ...]
    completed_requirements: tuple[str, ...]
    failure_stage: str | None
    requirement_details: dict[str, dict[str, object]]
    as_of: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProductionUniverseSnapshot:
    market: str
    session: str
    cutoff: datetime
    eligible_items: tuple[WatchlistItem, ...]
    excluded_subjects: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": PRODUCTION_UNIVERSE_CONTRACT,
            "market": self.market,
            "session": self.session,
            "cutoff": self.cutoff.astimezone(UTC).isoformat(),
            "eligible_subjects": [item.ticker for item in self.eligible_items],
            "excluded_subjects": list(self.excluded_subjects),
        }


def _json_dict(value: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str | None) -> list[object]:
    try:
        parsed = json.loads(value or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _latest_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def _latest_assessment(session: Session, ticker: str) -> ThesisAssessment | None:
    return session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.ticker == ticker)
        .order_by(ThesisAssessment.assessment_date.desc())
    ).first()


def _baseline_assessment(
    session: Session,
    ticker: str,
    thesis_version: int | None,
) -> ThesisAssessment | None:
    query = select(ThesisAssessment).where(ThesisAssessment.ticker == ticker)
    if thesis_version is not None:
        query = query.where(ThesisAssessment.thesis_version == thesis_version)
    rows = session.exec(query.order_by(ThesisAssessment.assessment_date)).all()
    for row in rows:
        snapshot = _json_dict(row.thesis_snapshot)
        if snapshot.get("assessment_mode") == "initial_baseline":
            return row
    # Assessments created before the explicit mode field are preserved as legacy baselines.
    return rows[0] if rows else None


def _profile_readiness(
    session: Session,
    item: WatchlistItem,
    data_dir: str | Path,
) -> tuple[bool, dict[str, object]]:
    company = session.exec(select(Company).where(Company.ticker == item.ticker)).first()
    provenance = read_profile_provenance(item.ticker, data_dir)
    quality = str((provenance or {}).get("quality") or "missing")
    structured_fields = {
        "industry": bool(company and company.industry),
        "sector": bool(company and company.sector),
        "business_units": bool(company and _json_list(company.business_units)),
        "revenue_sources": bool(company and _json_list(company.revenue_sources)),
    }
    has_structured_identity = any(structured_fields.values())
    ready = bool(
        provenance
        and quality in {"verified", "partial", "ambiguous"}
        and has_structured_identity
    )
    return ready, {
        "quality": quality,
        "has_structured_identity": has_structured_identity,
        "structured_fields": structured_fields,
        "source": (provenance or {}).get("source"),
        "reason": (provenance or {}).get("reason"),
    }


def _security_readiness(
    item: WatchlistItem,
    security: SecurityMaster | None,
    market: str,
) -> tuple[bool, list[str], dict[str, object]]:
    if security is None:
        return False, [], {"reason": "security_master_missing"}
    security_type = str(security.security_type or "").strip()
    issuer_type = str(security.issuer_type or "").strip()
    required = {
        "canonical_ticker": security.ticker == item.ticker,
        "canonical_company_id": bool(security.canonical_company_id),
        "canonical_security_id": bool(security.canonical_security_id),
        "exchange": bool(security.exchange or item.exchange),
        "market_country": market in {"kr", "us"} and bool(security.country),
        "security_type": bool(security_type),
        "issuer_type": bool(issuer_type and issuer_type != "unknown"),
        "company_linkage": bool(security.company_name),
    }
    safe_unavailable: list[str] = []
    depositary = issuer_type in {"adr", "foreign_private_issuer"} or any(
        marker in security_type.lower() for marker in ("adr", "ads", "depositary")
    )
    if depositary and not (security.adr_ratio and security.ordinary_share_identifier):
        safe_unavailable.append("SECURITY_MASTER:per_share_depositary_basis")
    return all(required.values()), safe_unavailable, {
        "required_fields": required,
        "identity_quality": security.identity_quality,
        "depositary_security": depositary,
        "per_share_basis_ready": not depositary
        or bool(security.adr_ratio and security.ordinary_share_identifier),
        "per_share_metrics_policy": "blocked_when_basis_unavailable",
    }


def evaluate_onboarding_readiness(
    session: Session,
    item: WatchlistItem,
    *,
    data_dir: str | Path | None = None,
    as_of: datetime | None = None,
) -> OnboardingReadiness:
    current = (as_of or datetime.now(UTC)).astimezone(UTC)
    root = Path(data_dir or get_settings().data_dir)
    security = session.exec(
        select(SecurityMaster).where(SecurityMaster.ticker == item.ticker)
    ).first()
    exchange = item.exchange or (security.exchange if security else None)
    market = market_scope_for_security(item.ticker, exchange)
    thesis = _latest_thesis(session, item.ticker)
    baseline = _baseline_assessment(
        session,
        item.ticker,
        thesis.version if thesis is not None else None,
    )

    details: dict[str, dict[str, object]] = {}
    identity_ready = bool(
        item.ticker == normalize_ticker(item.ticker)
        and item.company_name.strip()
        and exchange
        and market in {"kr", "us"}
    )
    details[OnboardingRequirement.IDENTITY] = {
        "ready": identity_ready,
        "normalized_ticker": item.ticker == normalize_ticker(item.ticker),
        "exchange_present": bool(exchange),
        "market": market,
    }

    security_ready, security_safe, security_details = _security_readiness(
        item, security, market
    )
    details[OnboardingRequirement.SECURITY_MASTER] = {
        "ready": security_ready,
        **security_details,
    }

    profile_ready, profile_details = _profile_readiness(session, item, root)
    details[OnboardingRequirement.COMPANY_PROFILE] = {
        "ready": profile_ready,
        **profile_details,
    }

    logic_fields = {
        "core_thesis": bool(thesis and thesis.core_thesis.strip()),
        "thesis_drivers": bool(thesis and _json_list(thesis.thesis_drivers)),
        "validation_metrics": bool(thesis and _json_list(thesis.validation_metrics)),
        "strengthen_signals": bool(thesis and _json_list(thesis.strengthen_signals)),
        "weaken_signals": bool(thesis and _json_list(thesis.weaken_signals)),
        "invalidation_signals": bool(thesis and _json_list(thesis.invalidation_signals)),
        "market_expectations": bool(thesis and _json_dict(thesis.market_expectations)),
        "valuation_framework": bool(thesis and _json_dict(thesis.valuation_framework)),
    }
    logic_ready = all(logic_fields.values())
    details[OnboardingRequirement.INVESTMENT_LOGIC] = {
        "ready": logic_ready,
        "required_fields": logic_fields,
        "thesis_version": thesis.version if thesis else None,
    }

    price_context = _json_dict(baseline.price_context) if baseline else {}
    valuation = _json_dict(baseline.valuation_snapshot) if baseline else {}
    thesis_snapshot = _json_dict(baseline.thesis_snapshot) if baseline else {}
    evidence_ready = bool(
        baseline
        and price_context
        and valuation
        and thesis_snapshot
        and baseline.assessment_state == "final"
    )
    details[OnboardingRequirement.INITIAL_EVIDENCE] = {
        "ready": evidence_ready,
        "assessment_date": (
            baseline.assessment_date.isoformat() if baseline else None
        ),
        "price_context": bool(price_context),
        "valuation_context": bool(valuation),
        "thesis_snapshot": bool(thesis_snapshot),
        "assessment_final": bool(
            baseline and baseline.assessment_state == "final"
        ),
    }

    baseline_snapshot = _json_dict(baseline.thesis_snapshot) if baseline else {}
    baseline_ready = bool(
        baseline
        and baseline_snapshot
        and baseline.thesis_version == (thesis.version if thesis else None)
    )
    details[OnboardingRequirement.INITIAL_BASELINE_ASSESSMENT] = {
        "ready": baseline_ready,
        "assessment_date": baseline.assessment_date.isoformat() if baseline else None,
        "assessment_mode": baseline_snapshot.get("assessment_mode") or "legacy_baseline",
        "thesis_version": baseline.thesis_version if baseline else None,
    }

    decision_ready = bool(
        baseline
        and baseline.assessment_state == "final"
        and baseline.summary.strip()
        and baseline.new_buyer_view.strip()
        and baseline.holder_view.strip()
        and baseline.risk_level.strip()
        and baseline.confidence >= 0
    )
    details[OnboardingRequirement.DECISION_READINESS] = {
        "ready": decision_ready,
        "accepted_decision_required_for_activation": False,
        "policy": "final_baseline_evidence_ready; accepted decision remains downstream",
    }

    completed = tuple(
        requirement.value
        for requirement in OnboardingRequirement
        if details[requirement].get("ready") is True
    )
    blocked = tuple(
        requirement.value
        for requirement in OnboardingRequirement
        if details[requirement].get("ready") is not True
    )
    return OnboardingReadiness(
        contract=ONBOARDING_READINESS_CONTRACT,
        ticker=item.ticker,
        market=market,
        onboarding_ready=not blocked,
        blocking_requirements=blocked,
        safe_unavailable_requirements=tuple(security_safe),
        completed_requirements=completed,
        failure_stage=blocked[0] if blocked else None,
        requirement_details=details,
        as_of=current.isoformat(),
    )


def begin_onboarding(
    item: WatchlistItem,
    *,
    requested_at: datetime | None = None,
) -> None:
    current = (requested_at or datetime.now(UTC)).astimezone(UTC)
    renew_request = (
        not item.monitoring_requested
        or item.onboarding_state
        in {OnboardingState.ACTIVE, OnboardingState.ONBOARDING_FAILED, OnboardingState.INACTIVE}
    )
    item.monitoring_requested = True
    item.active = False
    item.production_eligible = False
    item.onboarding_state = OnboardingState.PENDING_ONBOARDING
    item.onboarding_readiness = "{}"
    item.onboarding_failure_stage = None
    if renew_request:
        item.registration_requested_at = current
    item.onboarding_ready_at = None
    item.activated_at = None
    item.first_eligible_session = None


def reconcile_onboarding(
    session: Session,
    item: WatchlistItem,
    *,
    data_dir: str | Path | None = None,
    as_of: datetime | None = None,
    activate: bool = True,
    first_eligible_session: date | None = None,
) -> OnboardingReadiness:
    current = (as_of or datetime.now(UTC)).astimezone(UTC)
    SecurityMasterService().ensure(session, item.ticker)
    readiness = evaluate_onboarding_readiness(
        session,
        item,
        data_dir=data_dir,
        as_of=current,
    )
    item.onboarding_readiness = json.dumps(
        readiness.to_dict(), ensure_ascii=False, sort_keys=True
    )
    item.onboarding_failure_stage = readiness.failure_stage
    if readiness.onboarding_ready:
        item.onboarding_state = OnboardingState.READY
        item.onboarding_ready_at = item.onboarding_ready_at or current
        if activate and item.monitoring_requested:
            item.onboarding_state = OnboardingState.ACTIVE
            item.active = True
            item.production_eligible = True
            item.activated_at = item.activated_at or current
            item.first_eligible_session = (
                item.first_eligible_session or first_eligible_session
            )
        else:
            item.active = False
            item.production_eligible = False
    else:
        item.onboarding_state = OnboardingState.PENDING_ONBOARDING
        item.active = False
        item.production_eligible = False
        item.onboarding_ready_at = None
        item.activated_at = None
        item.first_eligible_session = None
    session.add(item)
    session.flush()
    return readiness


def deactivate_onboarding(item: WatchlistItem) -> None:
    item.monitoring_requested = False
    item.active = False
    item.production_eligible = False
    item.onboarding_state = OnboardingState.INACTIVE


def production_universe_snapshot(
    session: Session,
    market: Literal["kr", "us", "all"],
    *,
    cutoff: datetime,
    session_key: str,
) -> ProductionUniverseSnapshot:
    cutoff_utc = (
        cutoff.replace(tzinfo=UTC) if cutoff.tzinfo is None else cutoff.astimezone(UTC)
    )
    items = list(session.exec(select(WatchlistItem).order_by(WatchlistItem.ticker)).all())
    eligible: list[WatchlistItem] = []
    excluded: list[dict[str, object]] = []
    for item in items:
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == item.ticker)
        ).first()
        item_market = market_scope_for_security(
            item.ticker,
            item.exchange or (security.exchange if security else None),
        )
        if market != "all" and item_market != market:
            continue
        reasons: list[str] = []
        if not item.monitoring_requested:
            reasons.append("monitoring_not_requested")
        if not item.active:
            reasons.append("monitoring_not_active")
        if item.onboarding_state != OnboardingState.ACTIVE:
            reasons.append("onboarding_not_active")
        if not item.production_eligible:
            reasons.append("production_not_eligible")
        if item.activated_at is not None:
            activated_at = item.activated_at
            if activated_at.tzinfo is None:
                activated_at = activated_at.replace(tzinfo=UTC)
            if activated_at.astimezone(UTC) > cutoff_utc:
                reasons.append("activated_after_packet_cutoff")
        if reasons:
            excluded.append(
                {
                    "ticker": item.ticker,
                    "market": item_market,
                    "onboarding_state": item.onboarding_state,
                    "reasons": reasons,
                }
            )
        else:
            eligible.append(item)
    return ProductionUniverseSnapshot(
        market=market,
        session=session_key,
        cutoff=cutoff_utc,
        eligible_items=tuple(eligible),
        excluded_subjects=tuple(excluded),
    )
