"""Offline canonical consumption verdicts; never render or create financial facts.

These functions take explicit canonical inputs. Binding the formal-period input
to the complete source packet remains the caller's responsibility; a local
verdict alone is not whole-adapter qualification.
"""

from __future__ import annotations

from datetime import date, datetime
import re

from pydantic import TypeAdapter

from app.services.cash_flow_capital_efficiency_service import FinancialFact
from app.services.cash_flow_shadow_consumption_service import (
    build_cash_flow_reasoning_context, context_to_dict as cash_context,
)
from app.services.cash_flow_user_visible_service import _lineage_error
from app.services.unified_persisted_projection import _fingerprints
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.working_capital_core_service import WorkingCapitalCoreSnapshot
from app.services.working_capital_shadow_consumption_service import (
    build_working_capital_reasoning_context, context_to_dict as working_context,
)


def _fact_inventory(facts, issuer_id, policy):
    ids = [f.fact_id for f in facts]
    if len(ids) != len(set(ids)):
        raise ValueError("canonical_fact_identity_conflict")
    for fact in facts:
        policy.require(fact.source_provider)
        if (fact.issuer_id != issuer_id or not fact.fact_id or not fact.source_document_id
                or not fact.source_occurrence_id or not fact.currency or not fact.unit
                or not re.fullmatch(r"[a-f0-9]{64}", fact.raw_payload_sha256)):
            raise ValueError("canonical_source_ownership_incomplete")
    return {f.fact_id: f for f in facts}


def _projection(domain, facts, selected, verdict, inputs, modules, extra_denials=()):
    by_id = {f.fact_id: f for f in facts}
    denials = list(extra_denials)
    visited, active = set(), set()

    def check_cycle(identity):
        if identity in active:
            raise ValueError("canonical_derivation_cycle")
        if identity in visited or identity not in by_id:
            return
        active.add(identity)
        for child in by_id[identity].input_fact_ids:
            check_cycle(child)
        active.remove(identity)
        visited.add(identity)

    for identity in selected:
        check_cycle(identity)
    pending, closure = list(selected), set()
    while pending:
        identity = pending.pop()
        if identity in closure:
            continue
        fact = by_id.get(identity)
        if fact is None:
            denials.append("canonical_input_fact_missing")
            continue
        closure.add(identity)
        pending.extend(fact.input_fact_ids)
    rows = TypeAdapter(list[FinancialFact]).dump_python(
        [by_id[fid] for fid in sorted(closure)], mode="json")
    cutoff = date.fromisoformat(inputs["cutoff"][:10])
    for fid in closure:
        fact = by_id[fid]
        if (fact.filing_date is None or fact.filing_date > cutoff
                or (fact.source_available_at and fact.source_available_at > cutoff)):
            denials.append("canonical_source_after_cutoff_or_missing")
        if (fact.eligibility != "ELIGIBLE" or fact.denial_reason
                or fact.quality not in {"REPORTED_VERIFIED", "DERIVED_SAFE"}):
            denials.append("canonical_input_tainted")
    eligible = verdict["consumption_eligible"] and not denials
    value = {
        "contract": "unified-canonical-consumption-projection-v1", "domain": domain,
        "input_inventory_sha256": digest(TypeAdapter(list[FinancialFact]).dump_python(list(facts), mode="json")),
        "selection_inputs": inputs, "selection_inputs_sha256": digest(inputs),
        "existing_owner_verdict": verdict, "consumption_eligible": eligible,
        "availability": "AVAILABLE" if eligible else "UNAVAILABLE",
        "selected_fact_ids": sorted(selected) if eligible else [],
        "input_fact_ids": sorted(closure), "facts": rows if eligible else [],
        "fact_versions": {row["fact_id"]: digest(row) for row in rows},
        "denials": sorted(set(denials + (verdict.get("suppression_reasons", []) if not eligible else []))),
        "owner_fingerprints": _fingerprints("app/services/unified_consumption_projection.py", *modules),
        "complete_source_adapter_qualified": False,
        "formal_source_binding_verified": False,
    }
    return {**value, "projection_sha256": digest(value)}


def project_cash_flow_consumption(*, facts: tuple[FinancialFact, ...], issuer_id: str,
        ticker: str, industry: str, financial_type: str, core_status: str,
        cutoff: datetime, latest_formal_period: date | None,
        policy: UnifiedSourcePolicy, latest_provisional_period: date | None = None,
        materiality_signals: tuple[str, ...] = ()) -> dict:
    if cutoff.utcoffset() is None:
        raise ValueError("source_timezone_required")
    by_id = _fact_inventory(facts, issuer_id, policy)
    context = build_cash_flow_reasoning_context(ticker=ticker, industry=industry,
        financial_type=financial_type, core_status=core_status, facts=facts,
        cutoff=cutoff.date(), latest_formal_period=latest_formal_period,
        latest_provisional_period=latest_provisional_period, materiality_signals=materiality_signals)
    selected = {fid for fid in (context.ocf_fact_id, context.capex_fact_id, context.fcf_fact_id,
                                *context.prior_comparable_refs) if fid}
    denials = []
    if context.fcf_fact_id:
        error = _lineage_error(context, by_id)
        if error:
            denials.append(error)
    for fid in selected:
        fact = by_id[fid]
        if (fact.eligibility != "ELIGIBLE" or fact.denial_reason
                or fact.quality not in {"REPORTED_VERIFIED", "DERIVED_SAFE"}):
            denials.append("canonical_input_tainted")
        if fact.source_available_at and fact.source_available_at > cutoff.date():
            denials.append("canonical_source_after_cutoff")
    inputs = {"issuer_id": issuer_id, "ticker": ticker, "cutoff": cutoff.isoformat(),
        "latest_formal_period": str(latest_formal_period) if latest_formal_period else None,
        "latest_provisional_period": str(latest_provisional_period) if latest_provisional_period else None,
        "industry": industry, "financial_type": financial_type, "core_status": core_status,
        "materiality_signals": list(materiality_signals)}
    return _projection("cash_flow", facts, selected, cash_context(context), inputs,
        ("app/services/cash_flow_shadow_consumption_service.py",
         "app/services/cash_flow_user_visible_service.py",
         "app/services/cash_flow_capital_efficiency_service.py"), denials)


def project_working_capital_consumption(*, snapshot: WorkingCapitalCoreSnapshot,
        issuer_id: str, ticker: str, market: str, packet_id: str, industry: str,
        cutoff: datetime, latest_formal_balance_date: date | None,
        policy: UnifiedSourcePolicy, monitoring_text: str = "",
        latest_provisional_period_end: date | None = None) -> dict:
    if cutoff.utcoffset() is None:
        raise ValueError("source_timezone_required")
    if snapshot.issuer_id != issuer_id or snapshot.as_of_date > cutoff.date():
        raise ValueError("canonical_snapshot_identity_or_time_mismatch")
    _fact_inventory(snapshot.canonical_facts, issuer_id, policy)
    context = build_working_capital_reasoning_context(snapshot, ticker=ticker, market=market,
        packet_id=packet_id, assessment_date=cutoff.date(), cutoff=cutoff.date(), industry=industry,
        monitoring_text=monitoring_text, latest_formal_balance_date=latest_formal_balance_date,
        latest_provisional_period_end=latest_provisional_period_end)
    selected = set(context.selected_relation.input_fact_ids) if context.selected_relation else set()
    inputs = {"issuer_id": issuer_id, "ticker": ticker, "market": market, "packet_id": packet_id,
        "cutoff": cutoff.isoformat(), "industry": industry, "monitoring_text": monitoring_text,
        "latest_formal_balance_date": str(latest_formal_balance_date) if latest_formal_balance_date else None,
        "latest_provisional_period_end": str(latest_provisional_period_end) if latest_provisional_period_end else None,
        "canonical_snapshot_sha256": digest(TypeAdapter(WorkingCapitalCoreSnapshot).dump_python(snapshot, mode="json"))}
    # The source adapter cannot prove freshness from its own selected safe date.
    denials = ["independent_latest_formal_balance_missing"] if latest_formal_balance_date is None else []
    return _projection("working_capital", snapshot.canonical_facts, selected,
        working_context(context), inputs,
        ("app/services/working_capital_shadow_consumption_service.py",
         "app/services/working_capital_core_service.py"), denials)
