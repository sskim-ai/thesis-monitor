"""Financial amounts need source-owned comparison, not a favorable sign."""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation

from scripts.m12da_source_use_contract import SourceUse

CONTRACT = "absolute-financial-direction-eligibility-v1"
DENIAL = "ABSOLUTE_CURRENT_FINANCIAL_AMOUNT_NOT_DIRECTIONAL"
DIRECTION_USES = frozenset({
    SourceUse.OVERALL_DIRECTION.value, SourceUse.HOLDER_STANCE.value,
    SourceUse.NEW_BUYER_EXECUTION_RISK.value, SourceUse.ENTRY.value,
})


def is_financial(record, metadata):
    return (record.get("fact_kind") in {"earnings", "earnings_comparison"}
            or record.get("source_family") in {
                "OBSERVED_EARNINGS_FACT", "OBSERVED_COMPARATIVE_FINANCIAL_FACT"}
            or metadata.get("source_ref", "").startswith("stock.fact_catalog.earnings:"))


def comparable(fields):
    """Preserve the existing explicit current/prior duration and basis contract."""
    current, prior = fields.get("current_period"), fields.get("prior_period")
    if not isinstance(current, dict) or not isinstance(prior, dict):
        return False
    try:
        dates = [date.fromisoformat(p[k]) for p in (current, prior) for k in ("start", "end")]
        return (dates[0] <= dates[1] and dates[2] <= dates[3] < dates[1]
                and fields.get("comparison_type") in ("YOY", "QOQ", "SAME_DURATION_BASELINE")
                and (dates[1] - dates[0]).days == (dates[3] - dates[2]).days
                and all(current.get(k) and current[k] == prior.get(k)
                        for k in ("period_type", "currency", "unit", "entity_scope", "statement_basis")))
    except (ValueError, TypeError, KeyError):
        return False


def comparison_eligible(record, binding):
    fields = (binding or {}).get("fields", {})
    try:
        for key in ("current_value", "prior_comparable_value"):
            value = fields.get(key)
            if isinstance(value, bool) or value is None or not Decimal(str(value)).is_finite():
                return False
    except (InvalidOperation, ValueError):
        return False
    # The existing comparative owner validates exact filing occurrences, including
    # fiscal calendars. Do not replace it with an invented generic day tolerance.
    from scripts.m12dr_financial_source_authority import FAMILY, CONTRACT as COMPARISON_CONTRACT
    owned = (record.get("source_family") == FAMILY
             and record.get("authority_basis") == COMPARISON_CONTRACT
             and record.get("source_scope") == "exact_comparative_issuer_business_no_valuation"
             and bool((binding or {}).get("fact_sha256")))
    return owned or comparable(fields)


def direction_allowed(record, metadata, binding=None):
    entitled = (record.get("authority_state") == "RESOLVED"
                and SourceUse.OVERALL_DIRECTION in record.get("allowed_uses", [])
                and SourceUse.OVERALL_DIRECTION not in record.get("prohibited_uses", [])
                and record.get("financial_direction_eligibility", {}).get("direction_eligible") is not False)
    return bool(entitled and (not is_financial(record, metadata) or comparison_eligible(record, binding)))


def narrow_financial_authority(record, metadata, binding=None):
    """Narrow a derivative only; keep the immutable source record and fact intact."""
    result = deepcopy(record)
    if is_financial(record, metadata) and not comparison_eligible(record, binding):
        result["allowed_uses"] = sorted(set(record["allowed_uses"]) - DIRECTION_USES)
        result["prohibited_uses"] = sorted(set(record["prohibited_uses"]) | DIRECTION_USES)
        result["denial_reasons"] = sorted(set(record["denial_reasons"]) | {DENIAL})
        result["financial_direction_eligibility"] = {
            "contract": CONTRACT, "direction_eligible": False,
            "state": "ABSOLUTE_CONTEXT_ELIGIBLE", "reason": DENIAL,
        }
    return result


def validate_atomic_direction(atomic, metadata, authority, fact_fields=None):
    """Typed eligibility owns polarity; prose/keywords cannot grant permission."""
    records = {r["ref_id"]: r for r in authority["authority_records"]}
    rows = {r["ref_id"]: r for r in metadata}
    for item in atomic:
        if item["claim"].get("polarity") not in {"BULLISH", "BEARISH"}:
            continue
        refs = item["parent_source_refs"]
        if not any(ref in records and ref in rows and direction_allowed(
            records[ref], rows[ref], (fact_fields or {}).get(ref)) for ref in refs):
            raise ValueError("directional_claim_without_eligible_observed_source")
