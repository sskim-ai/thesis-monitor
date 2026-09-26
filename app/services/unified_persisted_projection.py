"""Read-only owner inventory, not an inferred raw-source or production seed.

Version is the content hash of the exact persisted records. Missing source
receipts stay missing. Financial freshness is deliberately not promoted to full
metric lineage/consumption eligibility.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from pydantic import TypeAdapter
from sqlmodel import Session, select

from app.models.company import Company
from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.services.financial_freshness_service import evaluate_financial_freshness_records
from app.services.onboarding_readiness_service import (
    _security_readiness, production_universe_snapshot,
)
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy


def _fingerprints(*modules: str) -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in modules}


def _at_or_before(value: datetime | None, cutoff: datetime) -> bool:
    # Persisted SQLite ORM timestamps use the repository's UTC storage convention.
    return value is not None and (value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                                 else value) <= cutoff


def _records(rows: list, *, fields: set[str] | None = None) -> list[dict]:
    if any(row.id is None for row in rows):
        raise ValueError("persisted_record_identity_required")
    result = []
    for row in rows:
        original = row.model_dump(mode="json")
        result.append({"table": row.__tablename__, "record_id": str(row.id),
            "original_record_sha256": digest(original),
            "record": original if fields is None else {k: v for k, v in original.items() if k in fields}})
    return result


def project_local_seed(session: Session, *, market: str, session_key: str,
                       cutoff: datetime, policy: UnifiedSourcePolicy) -> dict:
    """Canonical universe/security/thesis owner reads; no ensure/refresh/write."""
    if cutoff.utcoffset() is None or market not in {"us", "kr"}:
        raise ValueError("explicit_market_cutoff_required")
    if session.new or session.dirty or session.deleted:
        raise ValueError("clean_read_session_required")
    policy.require("canonical_local")
    with session.no_autoflush:
        universe = production_universe_snapshot(session, market, cutoff=cutoff,
                                                session_key=session_key)
        items = list(universe.eligible_items)
        item_records = _records(items, fields={"id", "ticker", "company_name", "exchange",
            "monitoring_requested", "active", "onboarding_state", "production_eligible",
            "activated_at", "first_eligible_session", "created_at"})
        identity_rows, theses, companies, denials = [], [], [], []
        for item in items:
            security = session.exec(select(SecurityMaster).where(
                SecurityMaster.ticker == item.ticker)).first()
            valid, _safe, details = _security_readiness(item, security, market)
            if security is None or not valid or not _at_or_before(security.updated_at, cutoff):
                denials.append({"role": "security_identity", "ticker": item.ticker,
                                "reason": "identity_ineligible_at_cutoff", "details": details})
            else:
                policy.require(security.identity_provider)
                identity_rows.append(security)
            thesis = session.exec(select(InvestmentThesis).where(
                InvestmentThesis.ticker == item.ticker, InvestmentThesis.status == "active")
                .order_by(InvestmentThesis.version.desc())).first()
            company = session.exec(select(Company).where(Company.ticker == item.ticker)).first()
            if thesis is None or not _at_or_before(thesis.created_at, cutoff):
                denials.append({"role": "stored_thesis_and_business_metadata", "ticker": item.ticker,
                                "reason": "active_thesis_unavailable_at_cutoff"})
            else:
                theses.append(thesis)
                if company is not None and _at_or_before(company.created_at, cutoff):
                    companies.append(company)
                elif company is not None:
                    denials.append({"role": "stored_thesis_and_business_metadata", "ticker": item.ticker,
                                    "reason": "business_metadata_after_cutoff"})
        values = {"universe": item_records, "security_identity": _records(identity_rows),
                  "stored_thesis_and_business_metadata": _records([*theses, *companies])}
    owners = _fingerprints("app/services/onboarding_readiness_service.py",
                           "app/services/daily_monitor_service.py", "app/models/security.py")
    return {"contract": "unified-local-seed-projection-v1", "market": market,
        "session": session_key, "cutoff": cutoff.isoformat(), "owner_fingerprints": owners,
        "universe": universe.to_dict(), "denials": denials,
        "roles": {role: {"records": records, "version": digest(records),
            "provider": "canonical_local", "source_receipt": None,
            "source_receipt_status": "LOCAL_RECORD_NOT_PROVIDER_RESPONSE",
            "eligible": bool(items) and not any(d["role"] == role for d in denials)}
            for role, records in values.items()},
        "production_seed_qualified": False}


def project_financial_freshness(session: Session, *, ticker: str, cutoff: datetime,
                                policy: UnifiedSourcePolicy) -> dict:
    if cutoff.utcoffset() is None:
        raise ValueError("source_timezone_required")
    if session.new or session.dirty or session.deleted:
        raise ValueError("clean_read_session_required")
    with session.no_autoflush:
        rows = list(session.exec(select(FinancialSnapshot).where(
            FinancialSnapshot.ticker == ticker).order_by(
                FinancialSnapshot.financial_period_end.desc(), FinancialSnapshot.filing_date.desc())).all())
        events = list(session.exec(select(Event).where(Event.ticker == ticker)
                                  .order_by(Event.date.desc())).all())
        admitted = [row for row in rows if policy.permits(row.provider)
            and (row.filing_date or row.reported_date) is not None
            and (row.filing_date or row.reported_date) <= cutoff.date()]
        admitted_events = [e for e in events if policy.permits(e.provider) and e.date <= cutoff.date()]
        original = _records([*admitted, *admitted_events])
        decision, _events, _rows = evaluate_financial_freshness_records(
            admitted_events, admitted, as_of=cutoff.date())
    return {"contract": "unified-financial-freshness-projection-v1", "ticker": ticker,
        "cutoff": cutoff.isoformat(), "records": original, "version": digest(original),
        "freshness": TypeAdapter(dict).dump_python(asdict(decision), mode="json"),
        "excluded_record_count": len(rows) + len(events) - len(admitted) - len(admitted_events),
        "source_receipt": None, "source_receipt_status": "NOT_RECONSTRUCTED_FROM_ORM",
        "owner_fingerprints": _fingerprints("app/services/financial_freshness_service.py",
                                             "app/services/financial_validation.py"),
        "qualification": "FRESHNESS_ONLY_METRIC_LINEAGE_PROJECTION_REMAINS_REQUIRED",
        "production_seed_qualified": False}
