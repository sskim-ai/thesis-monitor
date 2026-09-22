"""Opt-in, exact-occurrence quality for reported business observations.

This does not clear legacy taint or authorize EPS/valuation extrapolation. The
caller supplies frozen existing snapshots; no fetch, persistence or delivery.
"""

from __future__ import annotations

import hashlib
import json
import math
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation

from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.services.financial_amount_period_service import financial_statement_basis_decision
from app.services.financial_quality_service import DECISION_VERSION, PROSE_USABLE_STATES
from app.services.financial_validation import validate_event_financials
from app.services.kr_financial_lineage_service import (
    growth_lineage_compatible,
    stored_financial_lineage,
)


CONTRACT = "m12dr-financial-quality-integrity-vs-corroborated-extreme-v1"
FIELDS = ("revenue", "operating_income", "net_income")
SOFT_DEPENDENCIES = {
    "revenue": set(),
    "operating_income": {
        "operating_income_exceeds_revenue", "unusually_high_or_low_operating_margin",
    },
    "net_income": {"net_income_exceeds_revenue", "unusually_high_or_low_net_margin"},
}
_PRELIM_LABELS = {
    "revenue": {"매출액", "수익(매출액)", "영업수익"},
    "operating_income": {"영업이익"},
    "net_income": {"당기순이익"},
}
_UNIT_SCALES = {"원": Decimal(1), "KRW": Decimal(1), "백만원": Decimal(1000000)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), default=str).encode()).hexdigest()


def _values(value):
    parsed = json.loads(value or "[]")
    if not isinstance(parsed, list):
        raise ValueError("financial_source_list_invalid")
    return parsed


def _number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("financial_amount_not_finite")
    try:
        result = Decimal(str(value).replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError("financial_amount_not_finite") from exc
    if not result.is_finite():
        raise ValueError("financial_amount_not_finite")
    return result


def _snapshot_errors(row, ticker, cutoff):
    errors = list(_values(row.financial_hard_errors))
    if row.ticker != ticker:
        errors.append("issuer_mismatch")
    if row.provider != "opendart" or row.source != "OpenDART":
        errors.append("provider_lineage_unverified")
    receipt = row.source_filing_id or ""
    if len(receipt) != 14 or not receipt.isdigit():
        errors.append("receipt_unverified")
    period = row.financial_period_end
    filed = row.filing_date
    if not period or not filed or not (period <= filed <= cutoff):
        errors.append("availability_or_period_incoherent")
    if filed and receipt[:8] != filed.strftime("%Y%m%d"):
        errors.append("receipt_filing_date_mismatch")
    if row.currency != "KRW" or row.unit_scale != 1:
        errors.append("currency_or_scale_unresolved")
    if row.financial_statement_basis_warning or row.period_mapping_validation_failed or row.margin_quality_review:
        errors.append("statement_or_period_integrity_failure")
    if row.fs_div not in {"CFS", "OFS"}:
        errors.append("statement_basis_unverified")
    return errors


def _occurrence(row, metric, role, ticker, cutoff):
    errors = _snapshot_errors(row, ticker, cutoff)
    matches = [r for r in stored_financial_lineage(row) if r.get("logical_field") == metric
               and r.get("amount_role") == role and r.get("amount_variant") == "standalone"]
    if len(matches) != 1:
        return None, errors + ["exact_occurrence_missing_or_ambiguous"]
    occurrence = matches[0]
    column = "thstrm_amount" if role == "current" else "frmtrm_q_amount"
    expected_identity = ":".join(str(v) for v in (
        row.source_filing_id, occurrence.get("reprt_code"), occurrence.get("bsns_year"),
        row.fs_div, occurrence.get("sj_div"), occurrence.get("account_id"),
        occurrence.get("account_name"), occurrence.get("account_detail"),
        occurrence.get("source_row_ordinal"), column,
    ))
    if (
        row.snapshot_type != "full_statement"
        or occurrence.get("lineage_verified") is not True
        or occurrence.get("source_provider") != row.provider
        or occurrence.get("source_type") != "formal"
        or occurrence.get("source_filing") != row.source_filing_id
        or occurrence.get("rcept_no") != row.source_filing_id
        or occurrence.get("source_row_identity") != expected_identity
        or not occurrence.get("account_id") or occurrence.get("source_row_ordinal") is None
        or occurrence.get("source_column") != column
        or (role == "current" and occurrence.get("selected_for_canonical") is not True)
        or occurrence.get("currency") != row.currency
        or occurrence.get("fs_div") != row.fs_div
        or occurrence.get("sj_div") not in {"IS", "CIS"}
        or occurrence.get("statement_basis_state") != (
            "verified_consolidated" if row.fs_div == "CFS" else "verified_separate")
        or occurrence.get("statement_basis_source") not in {
            "source_row_fs_div", "requested_full_statement_scope"}
    ):
        errors.append("source_occurrence_integrity_failure")
    try:
        start = date.fromisoformat(occurrence["amount_period_start"])
        end = date.fromisoformat(occurrence["amount_period_end"])
        month = {"11013": 3, "11012": 6, "11014": 9}[occurrence["reprt_code"]]
        year = int(occurrence["bsns_year"]) - (role == "comparison")
        if (start, end) != (date(year, month - 2, 1), date(year, month, monthrange(year, month)[1])):
            errors.append("source_column_period_mismatch")
        if start > end or end > row.financial_period_end:
            errors.append("flow_period_incoherent")
        if occurrence.get("amount_period_type") != "single_quarter":
            errors.append("flow_period_not_single_quarter")
        # A half-year filing contains both standalone and cumulative columns.
        # The selected occurrence, not the filing envelope, owns flow duration.
        if role == "current" and end != row.financial_period_end:
            errors.append("current_period_or_scope_mismatch")
        if role == "current" and _number(occurrence["amount"]) != _number(getattr(row, metric)):
            errors.append("reported_amount_lineage_mismatch")
        _number(occurrence["amount"])
    except (KeyError, TypeError, ValueError):
        errors.append("flow_period_or_amount_unverified")
    return occurrence, sorted(set(errors))


def _corroboration(formal, preliminary, metric, occurrence, ticker, cutoff):
    if preliminary is None or occurrence is None:
        return {"status": "UNAVAILABLE", "errors": ["official_corroboration_missing"]}
    errors = _snapshot_errors(preliminary, ticker, cutoff)
    basis_field = "revenue_basis" if metric == "revenue" else "operating_income_basis"
    basis = financial_statement_basis_decision(preliminary, getattr(preliminary, basis_field))
    if (
        preliminary.snapshot_type != "preliminary_earnings"
        or preliminary.source_filing_id == formal.source_filing_id
        or preliminary.financial_period_end != formal.financial_period_end
        or preliminary.fs_div != formal.fs_div or basis["state"] != occurrence["statement_basis_state"]
        or preliminary.period_scope != "single-quarter" or preliminary.is_cumulative
        or preliminary.reporting_period_source != "current_header_quarter"
        or preliminary.reporting_period_confidence != "high"
    ):
        errors.append("corroboration_identity_period_or_basis_mismatch")
    matches = [r for r in _values(preliminary.raw_financial_fields)
               if r.get("raw_label") in _PRELIM_LABELS[metric]
               and r.get("raw_period") == "single_quarter"
               and str(r.get("raw_column_header", "")).startswith("당기실적")]
    witness = matches[0] if len(matches) == 1 else {}
    try:
        if (
            not witness or witness.get("source_receipt_no") != preliminary.source_filing_id
            or witness.get("selected_reporting_period_end") != occurrence["amount_period_end"]
            or witness.get("reporting_period_source") != "current_header_quarter"
            or witness.get("reporting_period_confidence") != "high"
            or witness.get("parse_method") != "html_semantic_table"
            or not witness.get("table_id") or witness.get("row_index") is None
            or not isinstance(witness.get("column_index"), int)
            or witness["column_index"] < 0
            or witness.get("current_period_date_candidates") != [occurrence["amount_period_end"]]
            or _number(witness["raw_value"]) * _UNIT_SCALES[witness["raw_unit"]]
            != _number(occurrence["amount"])
            or _number(getattr(preliminary, metric)) != _number(occurrence["amount"])
        ):
            errors.append("corroboration_exact_row_or_amount_mismatch")
    except (KeyError, ValueError, TypeError):
        errors.append("corroboration_unit_or_row_unverified")
    return {
        "status": "FAIL" if errors else "PASS", "errors": sorted(set(errors)),
        "receipt": preliminary.source_filing_id, "source_type": "preliminary_earnings",
        "snapshot_sha256": digest(preliminary.model_dump(mode="json")),
        "source_row": witness, "source_row_sha256": digest(witness),
        "statement_basis": basis,
    }


def _anomalies(row, occurrences):
    # Reuse the unchanged validator, including its 60% margin threshold.
    amounts = {}
    for metric, occurrence in occurrences.items():
        try:
            amounts[metric] = float(_number(occurrence["amount"])) if occurrence else None
        except (ValueError, KeyError):
            amounts[metric] = None
    event = Event(ticker=row.ticker, date=row.filing_date, source="OpenDART", provider="opendart",
                  title="Exact reported occurrence quality", url="", event_type="financial",
                  confirmed_facts=json.dumps(["OpenDART financial fact: 매출액=1 KRW"]),
                  **amounts)
    result = validate_event_financials(event)
    return result.soft_outliers, result.hard_errors


def build_reported_observation_quality(*, formal: FinancialSnapshot,
                                     preliminary: FinancialSnapshot | None,
                                     ticker: str, cutoff: date) -> dict:
    """Keep formal identity and exact dependency taint; never mutate either row."""
    current, prior, errors = {}, {}, {}
    for role, target in (("current", current), ("comparison", prior)):
        for metric in FIELDS:
            target[metric], errors[role, metric] = _occurrence(formal, metric, role, ticker, cutoff)
    observed_soft, current_hard = _anomalies(formal, current)
    prior_soft, prior_hard = _anomalies(formal, prior)
    soft = sorted(set(observed_soft) | set(_values(formal.financial_soft_outliers)))
    fields = {}
    for role, occurrences, reasons, hard in (
        ("current", current, soft, current_hard), ("comparison", prior, prior_soft, prior_hard)
    ):
        for metric, occurrence in occurrences.items():
            field_errors = list(errors[role, metric])
            if "non_positive_revenue" in hard and metric == "revenue":
                field_errors.append("non_positive_revenue")
            owned = sorted(set(reasons) & SOFT_DEPENDENCIES[metric])
            witness = _corroboration(formal, preliminary, metric, occurrence, ticker, cutoff) \
                if role == "current" else {"status": "UNAVAILABLE", "errors": []}
            unknown = set(reasons) - set().union(*SOFT_DEPENDENCIES.values())
            field_errors.extend(sorted(unknown))
            if owned and witness["status"] != "PASS":
                field_errors.append("extreme_observation_uncorroborated")
            caution = bool(reasons)
            fields[f"{role}.{metric}"] = {
                "decision_version": DECISION_VERSION, "quality_contract": CONTRACT,
                "state": "denied" if field_errors else "caution_usable" if caution else "verified_usable",
                "classification": "INTEGRITY_OR_RECONCILIATION_DENIED" if field_errors else
                    "CORROBORATED_EXTREME" if owned else "EXACT_REPORTED_WITH_CONTEXT_CAUTION"
                    if caution else "EXACT_REPORTED",
                "prose_eligible": not field_errors, "source_type": "formal", "provider": "opendart",
                "quality_reason_codes": reasons, "owned_anomaly_codes": owned,
                "hard_denial_reasons": sorted(set(field_errors)), "lineage": occurrence,
                "dependency_fields": [metric], "corroboration": witness,
                "valuation_or_recurring_profit_eligible": False,
            }
    revenue, operating = fields["current.revenue"], fields["current.operating_income"]
    margin_errors = [e for r in (revenue, operating) for e in r["hard_denial_reasons"]]
    margin = None
    if not margin_errors:
        a, b = revenue["lineage"], operating["lineage"]
        if any(a.get(k) != b.get(k) for k in (
            "amount_period_start", "amount_period_end", "currency", "statement_basis_state")):
            margin_errors.append("margin_dependency_mismatch")
        else:
            margin = float(_number(b["amount"]) / _number(a["amount"]) * 100)
            if formal.operating_margin is not None and not math.isclose(
                margin, formal.operating_margin, rel_tol=1e-12, abs_tol=1e-9
            ):
                margin_errors.append("margin_arithmetic_mismatch")
    fields["current.operating_margin"] = {
        "state": "denied" if margin_errors else "caution_usable" if soft else "verified_usable",
        "value": margin, "quality_reason_codes": soft,
        "dependency_fields": ["current.revenue", "current.operating_income"],
        "hard_denial_reasons": sorted(set(margin_errors)), "recurrence_verified": False,
    }
    comparisons = []
    for metric in ("revenue", "operating_income"):
        a, b = fields[f"current.{metric}"], fields[f"comparison.{metric}"]
        if any(r["state"] not in PROSE_USABLE_STATES for r in (a, b)):
            continue
        if not growth_lineage_compatible(a["lineage"], b["lineage"], comparison_type="yoy"):
            continue
        av, bv = (_number(r["lineage"]["amount"]) for r in (a, b))
        comparisons.append({
            "metric": metric, "current": a, "comparison": b,
            "delta": float(av - bv), "direction": "higher" if av > bv else "lower" if av < bv else "unchanged",
            "growth_pct": float((av - bv) / bv * 100) if bv > 0 else None,
            "formula": "current - prior_year_comparable",
            "dependency_fields": [f"current.{metric}", f"comparison.{metric}"],
        })
    result = {
        "contract": CONTRACT, "ticker": ticker, "cutoff": cutoff.isoformat(),
        "formal_receipt": formal.source_filing_id,
        "formal_snapshot_sha256": digest(formal.model_dump(mode="json")),
        "fields": fields, "comparative_observations": comparisons,
        "quality_reason_codes": soft,
        "historical_preliminary_reason_codes": _values(preliminary.financial_soft_outliers) if preliminary else [],
        "status": "PASS" if comparisons else "FAIL",
        "limitations": ["Reported-value corroboration is not recurring-profit verification.",
                        "No EPS, TTM, forward, PE, PB or valuation eligibility is granted.",
                        "Absolute magnitude and anomaly context do not authorize direction."],
    }
    result["receipt_sha256"] = digest(result)
    return result
