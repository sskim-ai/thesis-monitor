from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.config import get_settings
from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.models.macro import ThesisMacroImpact
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import PriceContext, ValuationSnapshot
from app.services.collection_service import CollectionService
from app.services.event_identity import event_fingerprint
from app.services.ohlcv_client import OhlcvClient
from app.services.thesis_evaluation_service import (
    evaluate_thesis,
    recent_events_for_assessment,
)
from app.services.valuation_snapshot_service import ValuationSnapshotService


INITIAL_EVIDENCE_CONTRACT = "initial-onboarding-evidence-v1"
REQUIRED_PRICE_PERIODS = ("daily", "weekly", "monthly")


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


def _canonical_sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def initial_evidence_fingerprint(evidence: Mapping[str, object]) -> str:
    material = {key: value for key, value in evidence.items() if key != "fingerprint"}
    return f"onboarding-evidence:sha256:{_canonical_sha(material)}"


def _latest_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def _baseline(
    session: Session,
    ticker: str,
    thesis_version: int,
) -> ThesisAssessment | None:
    rows = session.exec(
        select(ThesisAssessment)
        .where(
            ThesisAssessment.ticker == ticker,
            ThesisAssessment.thesis_version == thesis_version,
        )
        .order_by(ThesisAssessment.assessment_date)
    ).all()
    for row in rows:
        if _json_dict(row.thesis_snapshot).get("assessment_mode") == "initial_baseline":
            return row
    return next((row for row in rows if row.assessment_state == "final"), None)


def _latest_financial_checkpoint(
    session: Session,
    ticker: str,
) -> dict[str, object]:
    rows = session.exec(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.ticker == ticker)
        .order_by(FinancialSnapshot.financial_period_end.desc())
    ).all()
    for row in rows:
        hard_errors = [str(value) for value in _json_list(row.financial_hard_errors)]
        if hard_errors or row.financial_statement_basis_warning:
            continue
        return {
            "status": "AVAILABLE",
            "period_end": str(row.financial_period_end or row.reported_date or ""),
            "filing_date": str(row.filing_date or row.reported_date or ""),
            "period_type": row.period_type,
            "snapshot_type": row.snapshot_type,
            "provider": row.provider,
            "currency": row.currency,
            "source_document_id": row.source_filing_id,
        }
    return {"status": "UNAVAILABLE", "reason": "safe_financial_checkpoint_missing"}


def _event_refs(
    session: Session,
    ticker: str,
    current: datetime,
) -> list[dict[str, object]]:
    start = current.date() - timedelta(days=max(30, get_settings().monitor_lookback_days))
    rows = session.exec(
        select(Event)
        .where(Event.ticker == ticker, Event.date >= start, Event.date <= current.date())
        .order_by(Event.date.desc())
    ).all()
    return [
        {
            "event_fingerprint": event_fingerprint(row),
            "date": row.date.isoformat(),
            "title": row.title,
            "provider": row.provider,
            "source_document_id": row.source_document_id,
            "identity_status": row.document_identity_status,
        }
        for row in rows[:20]
    ]


def _market_context(
    session: Session,
    ticker: str,
    thesis_version: int,
    current: datetime,
) -> dict[str, object]:
    row = session.exec(
        select(ThesisMacroImpact)
        .where(
            ThesisMacroImpact.ticker == ticker,
            ThesisMacroImpact.thesis_version == thesis_version,
            ThesisMacroImpact.assessment_date <= current.date(),
        )
        .order_by(ThesisMacroImpact.assessment_date.desc())
    ).first()
    if row is None:
        return {"status": "UNAVAILABLE", "reason": "material_macro_context_missing"}
    return {
        "status": "AVAILABLE",
        "assessment_date": row.assessment_date.isoformat(),
        "direction": row.direction,
        "magnitude": row.magnitude,
        "confidence": row.confidence,
        "channels": _json_list(row.channels),
        "rationale": row.rationale,
    }


def _price_periods(price: PriceContext) -> dict[str, dict[str, object]]:
    return {
        period: {
            "available": bool(summary.actual_count > 0),
            "actual_count": summary.actual_count,
            "latest_date": summary.latest_date,
        }
        for period in REQUIRED_PRICE_PERIODS
        if (summary := price.periods.get(period)) is not None
    }


def _price_structure(price: PriceContext) -> dict[str, object]:
    return {
        "available": price.chart.available,
        "as_of_date": price.chart.as_of_date,
        "quality": price.chart.quality,
        "timeframes": sorted(price.chart.timeframes),
        "dynamic_levels": price.chart.dynamic_levels,
        "structure": price.chart.structure,
        "warnings": price.chart.warnings,
    }


def validate_initial_evidence(
    evidence: Mapping[str, object],
    *,
    ticker: str,
    thesis_version: int,
) -> tuple[bool, str | None]:
    if evidence.get("contract") != INITIAL_EVIDENCE_CONTRACT:
        return False, "initial_evidence_contract_missing"
    if evidence.get("ticker") != ticker or evidence.get("thesis_version") != thesis_version:
        return False, "initial_evidence_identity_mismatch"
    fingerprint = str(evidence.get("fingerprint") or "")
    if not fingerprint or fingerprint != initial_evidence_fingerprint(evidence):
        return False, "initial_evidence_fingerprint_mismatch"
    current_price = evidence.get("current_price")
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        return False, "initial_evidence_current_price_missing"
    periods = evidence.get("ohlcv_feature_availability")
    if not isinstance(periods, Mapping):
        return False, "initial_evidence_ohlcv_availability_missing"
    if any(
        not isinstance(periods.get(period), Mapping)
        or periods[period].get("available") is not True
        for period in REQUIRED_PRICE_PERIODS
    ):
        return False, "initial_evidence_dwm_unavailable"
    if not isinstance(evidence.get("price_structure"), Mapping):
        return False, "initial_evidence_price_structure_unbound"
    if not isinstance(evidence.get("valuation_context"), Mapping):
        return False, "initial_evidence_valuation_unbound"
    if not isinstance(evidence.get("market_expectations"), Mapping) or not evidence.get(
        "market_expectations"
    ):
        return False, "initial_evidence_expectations_unbound"
    if not isinstance(evidence.get("latest_safe_earnings_checkpoint"), Mapping):
        return False, "initial_evidence_earnings_unbound"
    if not isinstance(evidence.get("relevant_events"), list):
        return False, "initial_evidence_events_unbound"
    if not isinstance(evidence.get("material_unknowns"), list):
        return False, "initial_evidence_unknowns_unbound"
    return True, None


async def build_initial_evidence(
    session: Session,
    item: WatchlistItem,
    *,
    as_of: datetime,
    acquire: bool,
    collection_service: CollectionService | None = None,
    price_client: OhlcvClient | None = None,
    valuation_service: ValuationSnapshotService | None = None,
) -> dict[str, object]:
    current = as_of.astimezone(UTC)
    thesis = _latest_thesis(session, item.ticker)
    if thesis is None:
        raise ValueError("investment_logic_missing")
    baseline = _baseline(session, item.ticker, thesis.version)
    if acquire:
        collector = collection_service or CollectionService()
        await collector.collect_events(
            session,
            item.ticker,
            get_settings().monitor_lookback_days,
        )
        price = await (price_client or OhlcvClient()).fetch_price_context(
            item.ticker,
            as_of=current,
            session=session,
        )
        valuation = await (valuation_service or ValuationSnapshotService()).fetch(
            item.ticker,
            item.exchange,
            price,
            session=session,
            thesis=thesis,
        )
    else:
        price = PriceContext.model_validate(_json_dict(baseline.price_context) if baseline else {})
        valuation = ValuationSnapshot.model_validate(
            _json_dict(baseline.valuation_snapshot) if baseline else {}
        )
    periods = _price_periods(price)
    unknowns = [str(value) for value in _json_list(baseline.unknowns if baseline else None)]
    evidence: dict[str, object] = {
        "contract": INITIAL_EVIDENCE_CONTRACT,
        "ticker": item.ticker,
        "market": "kr" if item.ticker.isdigit() else "us",
        "thesis_version": thesis.version,
        "as_of": current.isoformat(),
        "current_thesis": {
            "core_thesis": thesis.core_thesis,
            "validation_metrics": _json_list(thesis.validation_metrics),
            "strengthen_signals": _json_list(thesis.strengthen_signals),
            "weaken_signals": _json_list(thesis.weaken_signals),
            "invalidation_signals": _json_list(thesis.invalidation_signals),
        },
        "latest_safe_earnings_checkpoint": _latest_financial_checkpoint(
            session, item.ticker
        ),
        "relevant_events": _event_refs(session, item.ticker, current),
        "market_expectations": _json_dict(thesis.market_expectations),
        "valuation_context": valuation.model_dump(
            mode="json",
            exclude={"earnings_quarter_series", "data_coverage"},
        ),
        "current_price": price.decision.current_price,
        "price_as_of": price.decision.price_as_of,
        "price_currency": valuation.currency,
        "ohlcv_feature_availability": periods,
        "price_structure": _price_structure(price),
        "material_market_context": _market_context(
            session, item.ticker, thesis.version, current
        ),
        "material_unknowns": unknowns,
        "price_context": price.model_dump(mode="json"),
        "baseline_identity": {
            "assessment_date": baseline.assessment_date.isoformat() if baseline else None,
            "assessment_state": baseline.assessment_state if baseline else None,
            "thesis_version": baseline.thesis_version if baseline else None,
            "preserved_existing": baseline is not None,
        },
    }
    evidence["fingerprint"] = initial_evidence_fingerprint(evidence)
    valid, reason = validate_initial_evidence(
        evidence,
        ticker=item.ticker,
        thesis_version=thesis.version,
    )
    if not valid:
        raise ValueError(reason or "initial_evidence_invalid")
    return evidence


def ensure_initial_baseline(
    session: Session,
    item: WatchlistItem,
    evidence: Mapping[str, object],
    *,
    as_of: datetime,
) -> ThesisAssessment:
    thesis = _latest_thesis(session, item.ticker)
    if thesis is None:
        raise ValueError("investment_logic_missing")
    existing = _baseline(session, item.ticker, thesis.version)
    if existing is not None:
        if existing.assessment_state != "final":
            raise ValueError("initial_baseline_not_final")
        if existing.assessment_date > as_of.date():
            raise ValueError("initial_baseline_future_dated")
        return existing
    price_payload = evidence.get("price_context")
    valuation_payload = evidence.get("valuation_context")
    if not isinstance(price_payload, Mapping) or not isinstance(valuation_payload, Mapping):
        raise ValueError("initial_baseline_evidence_unavailable")
    price = PriceContext.model_validate(price_payload)
    valuation = ValuationSnapshot.model_validate(valuation_payload)
    events = recent_events_for_assessment(
        session,
        item.ticker,
        as_of.date(),
        thesis.version,
    )
    result = evaluate_thesis(
        thesis,
        events,
        price,
        valuation_snapshot=valuation,
        assessment_mode="initial_baseline",
    )
    if result.assessment_state.value != "final":
        raise ValueError("initial_baseline_wait_for_final_session")
    event_fingerprints = [event_fingerprint(event) for event in events]
    valuation_context = result.valuation_context.model_dump(mode="json")
    thesis_snapshot = {
        "base_thesis": thesis.core_thesis,
        "thesis_version": thesis.version,
        "effective_date": as_of.date().isoformat(),
        "status": result.status,
        "assessment_mode": "initial_baseline",
        "baseline_established": True,
        "baseline_event_count": len(events),
        "baseline_event_fingerprints": event_fingerprints,
        "initial_evidence_fingerprint": evidence.get("fingerprint"),
        "current_thesis": f"{thesis.core_thesis} 현재 평가: {result.summary}",
        "thesis_drivers": _json_list(thesis.thesis_drivers),
        "validation_metrics": _json_list(thesis.validation_metrics),
        "market_expectations": _json_dict(thesis.market_expectations),
        "valuation_framework": _json_dict(thesis.valuation_framework),
        "valuation_context": valuation_context,
        "supporting_evidence": [],
        "weakening_evidence": [],
        "invalidation_evidence": [],
    }
    row = ThesisAssessment(
        ticker=item.ticker,
        thesis_version=thesis.version,
        assessment_date=as_of.date(),
        status=result.status,
        business_thesis_change=result.status.value,
        valuation_change=result.valuation_context.impact.value,
        earnings_estimate_impact=result.earnings_estimate_impact.value,
        market_expectation_assessment=result.market_expectation_assessment.model_dump_json(),
        confirmed_facts=json.dumps(result.confirmed_facts, ensure_ascii=False),
        background_confirmed_facts=json.dumps(
            result.background_confirmed_facts, ensure_ascii=False
        ),
        inferred_implications=json.dumps(result.inferred_implications, ensure_ascii=False),
        unknowns=json.dumps(result.unknowns, ensure_ascii=False),
        confirmed_warnings=json.dumps(result.confirmed_warnings, ensure_ascii=False),
        new_warnings=json.dumps(result.new_warnings, ensure_ascii=False),
        open_warnings=json.dumps(result.open_warnings, ensure_ascii=False),
        open_confirmed_warnings=json.dumps(
            result.open_confirmed_warnings, ensure_ascii=False
        ),
        persistent_watch_risks=json.dumps(
            result.persistent_watch_risks, ensure_ascii=False
        ),
        warning_states=json.dumps(result.warning_states, ensure_ascii=False),
        watch_items=json.dumps(result.watch_items, ensure_ascii=False),
        used_event_fingerprints=json.dumps(event_fingerprints, ensure_ascii=False),
        score=result.score,
        confidence=result.confidence,
        summary=result.summary,
        new_buyer_view=result.new_buyer_view,
        holder_view=result.holder_view,
        price_view=result.price_view,
        risk_level=result.risk_level,
        daily_change_severity="none",
        structural_risk_level=result.structural_risk_level.value,
        assessment_state="final",
        market_session=result.market_session,
        new_buyer_price_view=result.new_buyer_price_view,
        holder_price_view=result.holder_price_view,
        evidence=json.dumps(result.evidence, ensure_ascii=False),
        price_context=json.dumps(price_payload, ensure_ascii=False),
        valuation_snapshot=json.dumps(valuation_payload, ensure_ascii=False),
        valuation_context=json.dumps(valuation_context, ensure_ascii=False),
        thesis_snapshot=json.dumps(thesis_snapshot, ensure_ascii=False),
    )
    session.add(row)
    session.flush()
    return row
