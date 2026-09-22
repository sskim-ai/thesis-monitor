"""Field-owned SEC ambiguity, without clearing snapshot or valuation taint."""

import hashlib
import json
import math
from datetime import date


CONTRACT = "sec-business-field-quality-v1"
FIELDS = ("revenue", "operating_income")
LOCAL_ERRORS = {"sec_business_occurrence_conflict"}
SEMANTICS = {
    ("us-gaap", "Revenues"): "BROAD_REVENUE",
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"): "CUSTOMER_CONTRACT_REVENUE",
    ("ifrs-full", "Revenue"): "BROAD_REVENUE",
    ("us-gaap", "OperatingIncomeLoss"): "OPERATING_INCOME",
}


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def field_quality_receipt(*, ticker, issuer, field, errors, selected, occurrence_ids):
    value = {"contract": CONTRACT, "ticker": ticker, "issuer_cik": issuer,
             "field": field, "errors": errors, "selected_occurrence": selected,
             "candidate_occurrences": occurrence_ids,
             "semantic_role": "UNRESOLVED"}
    # Roles describe taxonomy meaning, not a verified issuer statement total.
    if selected:
        value["semantic_role"] = SEMANTICS.get(tuple(selected["taxonomy_concept"]), "UNRESOLVED")
    value["receipt_sha256"] = sha(value)
    return value


def field_errors(row, field):
    """Only a bound receipt can narrow legacy snapshot taint for a direct field."""
    original = json.loads(row.financial_hard_errors or "[]")
    normalized = field.removeprefix("latest_").removesuffix("_qoq").removesuffix("_yoy")
    if row.provider != "sec_companyfacts" or normalized not in FIELDS:
        return original
    try:
        raw = json.loads(row.raw_financial_fields)
        receipts = [r["field_quality"] for r in raw if r.get("field") == "sec_business_quality"]
        by_field = {r["field"]: r for r in receipts}
        if len(receipts) != 2 or set(by_field) != set(FIELDS):
            return original or ["sec_field_lineage_unverified"]
        for receipt in receipts:
            if (receipt["contract"] != CONTRACT or receipt["ticker"] != row.ticker
                    or sha({k: v for k, v in receipt.items() if k != "receipt_sha256"}) != receipt["receipt_sha256"]):
                return original or ["sec_field_lineage_unverified"]
        owned = set().union(*(set(r["errors"]) for r in receipts))
        if set(original) != owned or not owned <= LOCAL_ERRORS:
            return original or ["sec_field_lineage_unverified"]
        receipt = by_field[normalized]
        if receipt["errors"]:
            return original
        selected = receipt["selected_occurrence"]
        witnesses = [r for r in raw if r.get("field") == normalized]
        if len(witnesses) != 1 or not selected:
            return original or ["sec_field_lineage_unverified"]
        witness = witnesses[0]
        expected = {
            "source_row_identity": witness["source_row_identity"],
            "source_payload_sha256": witness["source_payload_sha256"],
            "value": witness["source_reported_value"], "start": witness["period_start"],
            "end": witness["period_end"], "filed": witness["source_filing_date"],
            "accn": witness["source_document_id"], "currency": witness["currency"],
            "taxonomy_concept": [witness["taxonomy"], witness["concept"]],
        }
        start, end, filed = [date.fromisoformat(selected[k]) for k in ("start", "end", "filed")]
        if (selected != expected or str(receipt["issuer_cik"]) != str(witness["issuer_cik"])
                or not str(receipt["issuer_cik"] or "").isdigit()
                or witness["projection_contract"] != "sec-business-field-projection-v1"
                or witness["source_document_type"] not in {"10-Q", "10-K", "20-F", "6-K"}
                or selected["source_row_identity"] not in receipt["candidate_occurrences"]
                or selected["accn"] != row.source_filing_id
                or filed != row.filing_date or end != row.financial_period_end
                or not start < end <= filed or selected["currency"] != row.currency
                or selected["value"] != getattr(row, normalized)
                or isinstance(selected["value"], bool) or not math.isfinite(selected["value"])
                or (row.period_scope == "single-quarter" and not 1 <= (end - start).days <= 130)
                or row.normalization_method or row.financial_statement_basis_warning
                or row.period_mapping_validation_failed or row.margin_quality_review):
            return original or ["sec_field_lineage_unverified"]
        return []
    except (KeyError, TypeError, ValueError):
        return original or ["sec_field_lineage_unverified"]


def independently_usable_business(row):
    return any(getattr(row, field) is not None and not field_errors(row, field) for field in FIELDS)


def reported_comparison_quality(*, formal, comparison, ticker, cutoff):
    """An absolute observation is insufficient; require same-filing annual comparison."""
    fields, comparisons = {}, []
    for role, row in (("current", formal), ("comparison", comparison)):
        for metric in FIELDS:
            errors = field_errors(row, metric) if row else ["missing_comparison"]
            raw = json.loads(row.raw_financial_fields) if row else []
            selected = [r for r in raw if r.get("field") == metric]
            witness = selected[0] if len(selected) == 1 else None
            if (row is None or row.ticker != ticker or row.provider != "sec_companyfacts"
                    or row.filing_date is None or row.filing_date > cutoff or not witness
                    or not any(r.get("field") == "sec_business_quality" for r in raw)):
                errors = [*errors, "exact_sec_occurrence_missing"]
            lineage = None if not witness else {
                "amount": witness["source_reported_value"],
                "amount_period_start": witness["period_start"],
                "amount_period_end": witness["period_end"], "currency": witness["currency"],
                "statement_basis": "sec_companyfacts_entity_wide",
                "source_row_identity": witness["source_row_identity"],
                "source_payload_sha256": witness["source_payload_sha256"],
                "issuer_cik": witness["issuer_cik"], "concept": witness["concept"],
                "taxonomy": witness["taxonomy"], "receipt": witness["source_document_id"],
            }
            fields[f"{role}.{metric}"] = {"state": "denied" if errors else "verified_usable",
                "hard_denial_reasons": sorted(set(errors)), "lineage": lineage,
                "prose_eligible": not errors, "valuation_or_recurring_profit_eligible": False}
    for metric in FIELDS:
        current, prior = [fields[f"{r}.{metric}"] for r in ("current", "comparison")]
        if current["hard_denial_reasons"] or prior["hard_denial_reasons"]:
            continue
        a, b = current["lineage"], prior["lineage"]
        try:
            starts = [date.fromisoformat(x["amount_period_start"]) for x in (a, b)]
            ends = [date.fromisoformat(x["amount_period_end"]) for x in (a, b)]
            compatible = (all(a[k] == b[k] for k in (
                "issuer_cik", "currency", "statement_basis", "concept", "taxonomy", "receipt", "source_payload_sha256"))
                and (ends[0] - starts[0]).days == (ends[1] - starts[1]).days
                and 330 <= (ends[0] - ends[1]).days <= 400
                and formal.period_scope == comparison.period_scope == "single-quarter")
        except (TypeError, ValueError):
            compatible = False
        if not compatible:
            continue
        av, bv = a["amount"], b["amount"]
        comparisons.append({"metric": metric, "current": current, "comparison": prior,
            "delta": av - bv, "direction": "higher" if av > bv else "lower" if av < bv else "unchanged",
            "growth_pct": (av - bv) / bv * 100 if bv > 0 else None,
            "formula": "current - prior_year_comparable"})
    result = {"contract": CONTRACT, "ticker": ticker, "cutoff": cutoff.isoformat(),
        "formal_receipt": formal.source_filing_id, "fields": fields,
        "comparative_observations": comparisons, "quality_reason_codes": [],
        "status": "PASS" if comparisons else "FAIL",
        "limitations": ["Revenue ambiguity is not resolved by independent operating income.",
                        "No recurring-profit, EPS, margin or valuation authority.",
                        "Absolute amounts alone do not authorize direction."]}
    result["receipt_sha256"] = sha(result)
    return result
