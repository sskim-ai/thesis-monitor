"""Shadow-only comparison authority, layered after the unchanged M12DK owner."""

from copy import deepcopy
from datetime import date
from urllib.parse import urlparse

from app.models.financial import FinancialSnapshot
from app.services.cross_market_decision_engine_service import _compact
from app.services.financial_observation_quality_service import (
    CONTRACT,
    build_reported_observation_quality,
    digest,
)
from app.services.sec_business_field_quality_service import reported_comparison_quality
from scripts.m12da_source_use_contract import SourceUse, canonical_sha256
from scripts.m12dk_current_source_authority import build_current_source_authority
from scripts.m12dp_observed_business_coverage import _validate_issuer_binding


FAMILY = "OBSERVED_COMPARATIVE_FINANCIAL_FACT"
_ALLOWED = {SourceUse.CONTEXT.value, SourceUse.BUSINESS_CONTEXT.value,
            SourceUse.PASS_A_ARCHETYPE.value, SourceUse.OVERALL_DIRECTION.value}


def source_quality(bundle):
    """Recompute from declared immutable source inputs, never trust a PASS flag."""
    expected = bundle["source_inputs_sha256"]
    inputs = bundle["source_inputs"]
    if digest(inputs) != expected:
        raise ValueError("reported_quality_frozen_source_digest_mismatch")
    if bundle.get("selected_source_identity"):
        from scripts.m12ds_r4_r2_selected_source_quality import identity
        if identity(FinancialSnapshot.model_validate(inputs["formal"])) != bundle["selected_source_identity"]:
            raise ValueError("reported_quality_selected_source_identity_mismatch")
    if inputs["formal"].get("provider") == "sec_companyfacts":
        return reported_comparison_quality(
            formal=FinancialSnapshot.model_validate(inputs["formal"]),
            comparison=(FinancialSnapshot.model_validate(inputs["comparison"])
                        if inputs.get("comparison") else None),
            ticker=inputs["ticker"], cutoff=date.fromisoformat(inputs["cutoff"]),
        )
    if inputs["formal"].get("provider") == "sec_foreign_filing":
        from app.services.sec_foreign_comparison_service import foreign_comparison_quality
        return foreign_comparison_quality(
            formal=FinancialSnapshot.model_validate(inputs["formal"]),
            candidates=[FinancialSnapshot.model_validate(r) for r in inputs.get("foreign_candidates", [])],
            ticker=inputs["ticker"], cutoff=date.fromisoformat(inputs["cutoff"]),
        )
    return build_reported_observation_quality(
        formal=FinancialSnapshot.model_validate(inputs["formal"]),
        preliminary=(FinancialSnapshot.model_validate(inputs["preliminary"])
                     if inputs.get("preliminary") else None),
        ticker=inputs["ticker"], cutoff=date.fromisoformat(inputs["cutoff"]),
    )


def issuer_projection_receipt(*, security_stock, underlying_ticker, issuer_binding, cutoff):
    """Bind issuer business only; never copy an ADR ratio or denominator."""
    valuation = security_stock.get("valuation") or {}
    provenance = valuation.get("security_identity_provenance") or {}
    evidence = provenance.get("evidence") or {}
    fields = provenance.get("field_provenance") or {}
    errors = []
    try:
        issuer_ok = _validate_issuer_binding(
            issuer_binding, expected_sha256=canonical_sha256(issuer_binding), ticker=underlying_ticker,
            generation=issuer_binding.get("source_generation_id"), market="kr")
    except (ValueError, KeyError, TypeError):
        issuer_ok = False
    if (
        valuation.get("security_identity_state") != "verified_depositary"
        or valuation.get("security_identity_conflict_reasons")
        or provenance.get("contract_version") != "authoritative-security-identity-v1"
        or provenance.get("provider") != "sec_official_identity"
        or provenance.get("source_tier") != "tier_a_authoritative"
        or not issuer_ok
        or issuer_binding.get("ticker") != underlying_ticker
        or issuer_binding.get("source_record", {}).get("ticker") != underlying_ticker
    ):
        errors.append("issuer_projection_owner_unverified")
    expected = {"ticker": security_stock["ticker"], "ordinary_share_identifier": underlying_ticker,
                "cik": evidence.get("cik")}
    for key, value in expected.items():
        row = fields.get(key) or {}
        url = urlparse(str(row.get("source_url") or ""))
        try:
            temporal = date.fromisoformat(row["as_of"]) <= date.fromisoformat(cutoff)
        except (KeyError, TypeError, ValueError):
            temporal = False
        if (
            not value or row.get("value") != value or evidence.get(key) != value
            or row.get("verification_status") != "verified"
            or row.get("provider") != "sec_official_identity"
            or row.get("source_tier") != "tier_a_authoritative"
            or not temporal or row.get("filing_accession") != evidence.get("filing_accession")
            or not row.get("filing_accession") or url.scheme != "https"
            or url.hostname != "www.sec.gov" or not url.path.startswith("/Archives/edgar/data/")
            or row.get("source_url") != evidence.get("source_url")
        ):
            errors.append("issuer_projection_field_unverified:" + key)
    return {
        "contract": CONTRACT, "status": "FAIL" if errors else "PASS", "errors": errors,
        "security_ticker": security_stock["ticker"], "underlying_ticker": underlying_ticker,
        "issuer_id": issuer_binding.get("issuer_id"),
        "identity_provenance_sha256": digest(provenance),
        "issuer_binding_sha256": canonical_sha256(issuer_binding),
        "source_refs": [fields.get(k, {}).get("source_reference") for k in expected],
        "scope": "issuer_business_only", "security_valuation_transfer": False,
    }


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
            "period_type": "single_quarter", "currency": current["currency"],
            "statement_basis": current["statement_basis"], "issuer_id": issuer_id,
            "source_ticker": quality["ticker"], "source_receipt": quality["formal_receipt"],
            "source_occurrences": [current["source_row_identity"], prior["source_row_identity"]],
            "anomaly_cautions": quality["quality_reason_codes"],
            "limitations": quality["limitations"], "recurrence_verified": False,
        }
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
        result.append(fact)
    return result


def build_source_authority(*, quality_bundles, issuer_bindings, **kwargs):
    current = build_current_source_authority(**kwargs)
    ticker = kwargs["ticker"]
    packet = kwargs["source_packet"]
    stock = next(s for s in packet["stocks"] if s["ticker"] == ticker)
    metadata = {r["ref_id"]: r for r in kwargs["source_metadata"]}
    records = {r["ref_id"]: r for r in current["authority"]["authority_records"]}
    quality = None
    projection = None
    if ticker in quality_bundles:
        source_ticker = ticker
    else:
        source_ticker = ((stock.get("valuation") or {}).get("security_identity_provenance") or {}).get(
            "evidence", {}).get("ordinary_share_identifier")
    if source_ticker in quality_bundles:
        bundle = quality_bundles[source_ticker]
        if (bundle.get("source_generation_id") != kwargs["source_generation_id"]
                or bundle["source_inputs"].get("ticker") != source_ticker
                or bundle["source_inputs"].get("cutoff") != packet["assessment_date"]):
            raise ValueError("quality_source_generation_subject_or_cutoff_mismatch")
        quality = source_quality(bundle)
        if ticker != source_ticker:
            projection = issuer_projection_receipt(
                security_stock=stock, underlying_ticker=source_ticker,
                issuer_binding=issuer_bindings[source_ticker], cutoff=packet["assessment_date"])
        expected_facts = comparative_facts(quality, ticker=ticker,
                                          issuer_id=issuer_bindings[source_ticker]["issuer_id"],
                                          projection=projection)
    else:
        expected_facts = []
    expected = {"canonical:" + f["fact_id"]: f for f in expected_facts}
    actual = {"canonical:" + f["fact_id"]: f for f in stock.get("fact_catalog", ())
              if f.get("fact_type") == "earnings_comparison"}
    for receipt in current["family_receipts"]:
        ref = receipt["ref_id"]
        row, record = metadata[ref], records[ref]
        if not str(row.get("source_ref", "")).startswith("stock.fact_catalog.earnings_comparison:"):
            continue
        errors = []
        fact = expected.get(ref)
        if not fact or actual.get(ref) != fact or row.get("statement") != _compact(fact["fields"]):
            errors.append("comparative_fact_frozen_derivation_mismatch")
        if row.get("category") != "earnings" or (fact and row.get("as_of") != fact["as_of_date"]):
            errors.append("comparative_fact_typed_period_mismatch")
        if record["source_family"] != "unclassified":
            errors.append("existing_restrictive_family_cannot_be_rebound")
        owner = quality["contract"] if quality else CONTRACT
        receipt.update(source_family=FAMILY, errors=errors, quality_contract=owner,
                       quality_receipt_sha256=quality["receipt_sha256"] if quality else None)
        if not errors:
            record.update(authority_state="RESOLVED", authority_basis=CONTRACT,
                          source_type=FAMILY, source_family=FAMILY,
                          source_scope="exact_comparative_issuer_business_no_valuation",
                          allowed_uses=sorted(_ALLOWED),
                          prohibited_uses=sorted({u.value for u in SourceUse} - _ALLOWED),
                          denial_reasons=["no_recurring_profit_or_security_valuation_authority"],
                          compatible_source_versions=[CONTRACT, owner] if owner != CONTRACT else [CONTRACT])
        receipt.update(allowed_uses=record["allowed_uses"], authority_state=record["authority_state"],
                       authority_basis=record["authority_basis"])
    manifest = current["authority"]
    manifest.update(reported_quality_owner_contract=CONTRACT,
                    current_source_family_receipts_sha256=canonical_sha256(current["family_receipts"]))
    manifest.pop("authority_manifest_sha256")
    manifest["authority_manifest_sha256"] = canonical_sha256(manifest)
    return current
