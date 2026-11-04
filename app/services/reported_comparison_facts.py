"""Pure original comparative fact constructor, without runtime startup imports."""
from copy import deepcopy
from app.services.financial_observation_quality_service import digest


def comparative_facts(quality, *, ticker, issuer_id, projection=None):
    if quality["status"] != "PASS":
        return []
    if ticker != quality["ticker"] and (
        not projection or projection.get("status") != "PASS"
        or projection.get("security_ticker") != ticker
        or projection.get("underlying_ticker") != quality["ticker"]
        or projection.get("issuer_id") != issuer_id
    ):
        raise ValueError("issuer_business_projection_unverified")
    result = []
    for comparison in quality["comparative_observations"]:
        current, prior = [comparison[key]["lineage"] for key in ("current", "comparison")]
        for occurrence in (current, prior):
            if "issuer_cik" in occurrence and issuer_id != f"CIK:{int(occurrence['issuer_cik']):010d}":
                raise ValueError("sec_comparison_official_issuer_binding_mismatch")
        fields = {
            "metric": comparison["metric"], "current_value": current["amount"],
            "prior_comparable_value": prior["amount"], "delta": comparison["delta"],
            "growth_pct": comparison["growth_pct"], "direction": comparison["direction"],
            "period_start": current["amount_period_start"], "period_end": current["amount_period_end"],
            "prior_period_start": prior["amount_period_start"], "prior_period_end": prior["amount_period_end"],
            "period_type": "half_year" if current.get('occurrence', {}).get('period_scope') == 'half-year' else "single_quarter", "currency": current["currency"],
            "statement_basis": current["statement_basis"], "issuer_id": issuer_id,
            "source_ticker": quality["ticker"], "source_receipt": quality["formal_receipt"],
            "source_occurrences": [current["source_row_identity"], prior["source_row_identity"]],
            "anomaly_cautions": quality["quality_reason_codes"],
            "limitations": quality["limitations"], "recurrence_verified": False,
        }
        if comparison.get('fiscal_comparability'):
            fields['period_type'] = 'annual'
            fields['fiscal_comparability'] = deepcopy(comparison['fiscal_comparability'])
        elif current.get('occurrence', {}).get('period_scope') == 'annual' or comparison.get('reported_period_scope') == 'annual':
            fields['period_type'] = 'annual'
        document_class = (current.get('occurrence') or {}).get('document_evidence_class')
        if document_class:
            fields['document_evidence_class'] = deepcopy(document_class)
        fact = {
            "fact_id": "earnings_comparison:" + ticker + ":" + comparison["metric"] + ":" + digest(fields)[:24],
            "fact_type": "earnings_comparison", "as_of_date": current["amount_period_end"],
            "fields": fields, "quality_contract": quality["contract"],
            "field_dependency_receipts": deepcopy(comparison),
            "quality_receipt_sha256": quality["receipt_sha256"],
            "issuer_projection": deepcopy(projection), "prose_eligible": True,
            "interpretation_eligible": True, "user_visible": False,
        }
        if comparison.get('fiscal_comparability'):
            fact['fiscal_metadata_policy'] = deepcopy(quality['fiscal_metadata_policy'])
        result.append(fact)
    return result
