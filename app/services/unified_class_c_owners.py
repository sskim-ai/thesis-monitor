"""Read-only persisted evidence projections, with explicit remaining owner gaps.

These are source records, not reconstructed HTTP responses. Presence of a
projection is deliberately distinct from downstream consumption qualification.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json

from pydantic import TypeAdapter
from sqlmodel import Session, select

from app.macro.temporal import classify_observation, SESSION_BOUND_SERIES
from app.models.financial import FinancialSnapshot
from app.models.event import Event
from app.models.macro import MacroEvent, MacroObservation
from app.models.security import ConsensusEstimate, SecurityMaster
from app.services.financial_amount_period_service import financial_amount_period_lineage
from app.services.financial_context_adapter_service import adapt_fact_catalog_financial_context
from app.services.financial_freshness_service import evaluate_financial_freshness_records
from app.services.sec_business_field_quality_service import field_errors
from app.services.unified_persisted_projection import _at_or_before, _fingerprints, _records, project_local_seed
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy


LOCAL_ROLES = ("universe", "security_identity", "stored_thesis_and_business_metadata")
FINANCIAL_ROLES = {
    "sec_financial_fundamental_domains": "sec_companyfacts",
    "opendart_financial_fundamental_domains": "opendart",
}
MACRO_ROLES = {
    "rates_credit_liquidity_risk": ("fred",),
    "energy": ("eia",),
    "korea_macro": ("ecos",),
    "kr_overnight_cross_assets": ("ohlcv_analyst",),
}
CLASS_C_ROLES = (*LOCAL_ROLES, *FINANCIAL_ROLES, "canonical_cashflow_working_capital",
                 "eligible_valuation_estimates", *MACRO_ROLES, "central_bank_published_events")


def _clean(session: Session, cutoff: datetime):
    if cutoff.utcoffset() is None:
        raise ValueError("source_timezone_required")
    if session.new or session.dirty or session.deleted:
        raise ValueError("clean_read_session_required")


def _result(role, records, values, denials, cutoff, *owners, qualification="OWNER_PROJECTED"):
    values = TypeAdapter(list).dump_python(values, mode="json")
    payload = {"contract": "unified-class-c-owner-projection-v1", "role": role,
        "records": records, "version": digest(records), "values": values,
        "normalized_sha256": digest(values), "cutoff": cutoff.isoformat(),
        "eligible": bool(values), "denials": denials, "qualification": qualification,
        "source_receipt": None, "source_receipt_status": "NOT_RECONSTRUCTED_FROM_PERSISTED_RECORD",
        "owner_fingerprints": _fingerprints("app/services/unified_class_c_owners.py", *owners),
        "production_seed_qualified": False}
    return {**payload, "projection_sha256": digest(payload)}


def project_reported_financial(session: Session, *, role: str, ticker: str,
                               cutoff: datetime, policy: UnifiedSourcePolicy) -> dict:
    _clean(session, cutoff)
    provider = FINANCIAL_ROLES[role]
    policy.require(provider)
    with session.no_autoflush:
        security = session.exec(select(SecurityMaster).where(SecurityMaster.ticker == ticker)).first()
        rows = list(session.exec(select(FinancialSnapshot).where(
            FinancialSnapshot.ticker == ticker, FinancialSnapshot.provider == provider)
            .order_by(FinancialSnapshot.financial_period_end.desc(), FinancialSnapshot.filing_date.desc(),
                      FinancialSnapshot.id.desc())).all())
        events = list(session.exec(select(Event).where(Event.ticker == ticker,
            Event.provider.in_((provider, "sec_edgar") if provider == "sec_companyfacts" else (provider,)))
            .order_by(Event.date.desc())).all())
    if security is None or not _at_or_before(security.updated_at, cutoff):
        return _result(role, [], [], ["security_identity_missing_or_future"], cutoff)
    policy.require(security.identity_provider)
    admitted = [r for r in rows if r.filing_date and r.filing_date <= cutoff.date()
                and r.financial_period_end and r.financial_period_end <= r.filing_date]
    allowed_events = [e for e in events if policy.permits(e.provider) and e.date <= cutoff.date()]
    records = _records([security, *admitted, *allowed_events])
    # No old safe period is substituted for the latest recorded formal period.
    latest = admitted[0].financial_period_end if admitted else None
    candidates = [r for r in admitted if r.financial_period_end == latest]
    decision, _, copies = evaluate_financial_freshness_records(allowed_events, admitted, as_of=cutoff.date())
    copy_by_id = {r.id: r for r in copies}
    values, denials = [], []
    for metric in ("revenue", "operating_income", "net_income"):
        for row in candidates:
            current = copy_by_id[row.id]
            value = getattr(current, metric)
            errors = field_errors(current, metric)
            if value is None or errors or not row.source_filing_id or not row.currency:
                continue
            if provider == "opendart":
                lineage = financial_amount_period_lineage(current, "latest_" + metric)
                if not lineage.get("lineage_verified") or not security.corp_code or row.unit_scale != 1:
                    continue
                issuer = security.corp_code
            else:
                raw = json.loads(current.raw_financial_fields)
                policy.check_lineage(raw)
                matches = [x for x in raw if x.get("field") == metric
                           and x.get("projection_contract") == "sec-business-field-projection-v1"]
                if len(matches) != 1 or not security.cik:
                    continue
                lineage = matches[0]
                if lineage.get("unit") != row.currency:
                    continue
                if str(lineage.get("issuer_cik")).lstrip("0") != str(security.cik).lstrip("0"):
                    continue
                issuer = security.cik
            if decision.refresh_required:
                denials.append({"metric": metric, "reason": "existing_freshness_requires_refresh"})
                break
            values.append({"ticker": ticker, "issuer_id": issuer,
                "canonical_security_id": security.canonical_security_id,
                "record_id": str(row.id), "record_sha256": digest(row.model_dump(mode="json")),
                "provider": provider, "metric": metric, "value": value,
                "currency": row.currency, "unit_scale": row.unit_scale,
                "source_unit": lineage.get("unit") if provider == "sec_companyfacts" else row.currency,
                "period_end": latest.isoformat(), "filing_date": row.filing_date.isoformat(),
                "filing_id": row.source_filing_id, "lineage": lineage,
                "freshness": asdict(decision), "usage": "DIRECT_REPORTED_NOT_DERIVED_VALUATION"})
            break
        else:
            denials.append({"metric": metric, "reason": "selected_metric_lineage_not_qualified"})
    return _result(role, records, values, denials, cutoff,
        "app/services/financial_amount_period_service.py", "app/services/financial_freshness_service.py",
        "app/services/sec_business_field_quality_service.py", "app/services/kr_financial_lineage_service.py")


def project_macro_records(session: Session, *, role: str, cutoff: datetime,
                          policy: UnifiedSourcePolicy) -> dict:
    _clean(session, cutoff)
    providers = MACRO_ROLES[role]
    for provider in providers:
        policy.require(provider)
    with session.no_autoflush:
        rows = list(session.exec(select(MacroObservation).where(MacroObservation.provider.in_(providers))
            .order_by(MacroObservation.series_code, MacroObservation.observed_at.desc(),
                      MacroObservation.retrieved_at.desc(), MacroObservation.id.desc())).all())
    values, denials, selected, seen = [], [], [], set()
    for row in rows:
        if not _at_or_before(row.observed_at, cutoff) or not _at_or_before(row.retrieved_at, cutoff):
            denials.append({"record_id": row.id, "reason": "observation_or_retrieval_after_cutoff"})
            continue
        if row.series_code in seen:
            continue
        seen.add(row.series_code)
        selected.append(row)
        value = row.model_dump(mode="json", exclude={"raw_payload"})
        policy.check_lineage(json.loads(row.raw_payload))
        temporal = classify_observation(value, None, as_of=cutoff)
        if (not row.unit or temporal.temporal_role in {"STALE_FOR_DAILY_SIGNAL", "UNAVAILABLE"}
                or (role == "kr_overnight_cross_assets" and row.series_code not in SESSION_BOUND_SERIES)):
            denials.append({"record_id": row.id, "reason": temporal.reason})
            continue
        values.append({"observation": value, "temporal": asdict(temporal),
            "usage": "PREVIOUS_US_SESSION_CONTEXT" if role == "kr_overnight_cross_assets"
                     else "PUBLICATION_CONTEXT_NOT_QUERY_TIME_PRICE",
            "original_record_sha256": digest(row.model_dump(mode="json"))})
    return _result(role, _records(selected), values, denials, cutoff, "app/macro/temporal.py",
                   "app/services/market_session.py")


def project_published_events(session: Session, *, cutoff: datetime, policy: UnifiedSourcePolicy) -> dict:
    _clean(session, cutoff)
    policy.require("federal_reserve")
    with session.no_autoflush:
        rows = list(session.exec(select(MacroEvent).where(MacroEvent.provider == "federal_reserve")
                    .order_by(MacroEvent.id)).all())
    selected = [r for r in rows if r.event_status == "released" and r.source_url
                and _at_or_before(r.released_at, cutoff) and _at_or_before(r.retrieved_at, cutoff)]
    # Published facts are preserved; model-written implication/unknown fields are not inputs.
    values = [r.model_dump(mode="json", exclude={"inferred_implications", "unknowns"}) for r in selected]
    return _result("central_bank_published_events", _records(selected, fields=set(MacroEvent.model_fields)
                   - {"inferred_implications", "unknowns"}), values,
        [{"record_id": r.id, "reason": "not_released_at_cutoff"} for r in rows if r not in selected],
        cutoff, "app/macro/providers/fed.py", qualification="PUBLISHED_CONTEXT_ONLY_NO_DAILY_SIGNAL_AUTHORITY")


def project_estimate_inventory(session: Session, *, ticker: str, cutoff: datetime,
                               policy: UnifiedSourcePolicy) -> dict:
    _clean(session, cutoff)
    policy.require("finnhub")
    with session.no_autoflush:
        rows = list(session.exec(select(ConsensusEstimate).where(ConsensusEstimate.ticker == ticker,
            ConsensusEstimate.provider == "finnhub").order_by(ConsensusEstimate.id)).all())
    # Existing fetch only writes provider-defined Finnhub consensus. There is no
    # existing read-only persisted estimate eligibility owner to invoke safely.
    return _result("eligible_valuation_estimates", _records(rows), [],
        [{"record_id": r.id, "reason": "persisted_estimate_basis_owner_not_closed"} for r in rows]
        or ["no_allowed_persisted_estimate"], cutoff, "app/services/valuation_snapshot_service.py",
        qualification="GAP_PERSISTED_ESTIMATE_OWNER_NOT_IMPLEMENTED")


def project_canonical_catalog(rows: list[dict], *, cutoff: datetime,
                              policy: UnifiedSourcePolicy) -> dict:
    if cutoff.utcoffset() is None:
        raise ValueError("source_timezone_required")
    ids = [row.get("fact_id") for row in rows]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("unique_canonical_fact_identity_required")
    values, denials = [], []
    for row in rows:
        lineage = row.get("canonical_financial_lineage") or {}
        policy.require(lineage.get("source_provider"))
        filed = lineage.get("filing_date")
        if not filed or str(filed) > cutoff.date().isoformat():
            denials.append({"fact_id": row["fact_id"], "reason": "filing_unavailable_at_cutoff"})
            continue
        adapted = adapt_fact_catalog_financial_context(row, rows)
        if adapted.context is None:
            denials.append({"fact_id": row["fact_id"], "reason": list(adapted.denial_reasons)})
        else:
            values.append(adapted.context)
    result = _result("canonical_cashflow_working_capital",
        [{"fact_id": r["fact_id"], "version": digest(r), "record": r} for r in rows], values, denials,
        cutoff, "app/services/financial_context_adapter_service.py",
        "app/services/financial_lineage_projection_service.py",
        qualification="LINEAGE_ONLY_CONSUMPTION_FRESHNESS_BRIDGE_REQUIRED")
    result.pop("projection_sha256")
    result["lineage_eligible"] = bool(values)
    result["eligible"] = False
    result["consumption_eligible"] = False
    return {**result, "projection_sha256": digest(result)}


def class_c_owner_inventory() -> dict:
    """Never promote partial coverage to network-free full qualification."""
    return {"roles": list(CLASS_C_ROLES), "count": len(CLASS_C_ROLES),
        "network_free_source_adapter_prequalified": False,
        "remaining_owner_gaps": ["eligible_valuation_estimates",
            "canonical_cashflow_working_capital:current_consumption_freshness_bridge"]}


__all__ = ["project_local_seed", "project_reported_financial", "project_macro_records",
           "project_published_events", "project_estimate_inventory", "project_canonical_catalog",
           "class_c_owner_inventory"]
