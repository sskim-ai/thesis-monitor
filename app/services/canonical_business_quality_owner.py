"""Detached, source-owned financial quality. No acquisition or persistence.

Replays existing reported-comparison owners, then the unchanged financial
quality validator. The consumer never supplies a desired quality state.
"""
from copy import deepcopy
import json

from app.models.financial import FinancialSnapshot
from app.services.financial_quality_service import build_financial_quality_state
from app.services.sec_business_field_quality_service import field_errors as sec_errors
from app.services.sec_foreign_comparison_service import field_errors as foreign_errors
from app.services.unified_snapshot_contract import digest
from app.services.versioned_business_stock_owner import _identity, replay_version
from scripts.m12dr_financial_source_authority import source_quality

CONTRACT = "canonical-reported-business-quality-owner-v1"
MISSING = "EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def aggregate_state(quality):
    # Same precedence as the canonical financial_quality fact in ai_review_service.
    states = {r.get("state", "unknown") for r in quality["fields"].values()}
    return next((state for state in ("denied", "caution_usable", "verified_usable")
                 if state in states), "unknown")


def _replay_quality(bundle):
    quality = source_quality(bundle)
    require(quality == bundle["quality"], "quality_original_replay_mismatch")
    inputs = bundle["source_inputs"]
    formal = FinancialSnapshot.model_validate(inputs["formal"])
    direct, values = {}, {}
    # Match the existing unified_stock_owner metadata projection. Exact
    # comparison receipts own lineage; source flags still own all taint.
    common = dict(period=str(formal.financial_period_end), source_type=formal.snapshot_type,
        provider=formal.provider, filing_date=str(formal.filing_date),
        quality_reason_codes=quality.get("quality_reason_codes", []),
        soft_outliers=json.loads(formal.financial_soft_outliers),
        financial_statement_basis_warning=formal.financial_statement_basis_warning,
        period_mapping_validation_failed=formal.period_mapping_validation_failed,
        margin_quality_review=formal.margin_quality_review)
    comparisons = {o["metric"]: o for o in quality["comparative_observations"]}
    owner_denials = []
    for metric in ("revenue", "operating_income"):
        field = "latest_" + metric
        amount = getattr(formal, metric)
        if formal.provider == "sec_companyfacts":
            errors = sec_errors(formal, metric)
        elif formal.provider == "sec_foreign_filing":
            errors = foreign_errors(formal, metric)
        else:
            errors = quality["fields"]["current." + metric]["hard_denial_reasons"]
        # A missing/nonselected field remains outside this reported source's
        # scope, never becomes verified or transferred to a sibling field.
        owner_denials.extend(errors)
        if amount is None:
            continue
        values[field] = amount
        comparison = comparisons.get(metric)
        direct[field] = [{**common, "hard_errors": errors,
            "lineage_verified": comparison is not None and not errors,
            "source_row_identity": (comparison or {}).get("current", {}).get("lineage", {}).get("source_row_identity")}]
    require(values, MISSING + ":no_reported_financial_values")
    metadata = {**common, "hard_errors": sorted(set(owner_denials)), "direct_field_sources": direct}
    result = build_financial_quality_state(values, source_metadata=metadata)
    require(result["fields"], MISSING + ":canonical_quality_fields_empty")
    return dict(source_quality=quality, quality=result, metadata=metadata, values=values,
        input_sha256=bundle["source_inputs_sha256"], formal_sha256=digest(inputs["formal"]),
        original_source_ticker=inputs["ticker"], source_generation_id=bundle["source_generation_id"])


def derive(*, stock, versions, version_hashes, local_seeds, cutoff, policy):
    """Create a supplement only from an exact replay of the sealed business version."""
    ticker = stock["ticker"]
    existing = [f for f in stock["packet"]["stocks"][0]["fact_catalog"] if f["fact_type"] == "financial_quality"]
    require(not existing, "existing_quality_must_not_be_replaced")
    replay = replay_version(ticker=ticker, versions=versions, version_hashes=version_hashes,
                            local_seeds=local_seeds, cutoff=cutoff, policy=policy)
    require(replay["facts"], MISSING + ":no_reported_comparison_contract")
    stock_facts = {f["fact_id"]: f for f in stock["packet"]["stocks"][0]["fact_catalog"]}
    require(all(stock_facts.get(f["fact_id"]) == f for f in replay["facts"]), "quality_consumed_comparison_mismatch")
    bridge = replay["bridge"]
    source_ticker = bridge["underlying_ticker"] if bridge else ticker
    source_doc = json.loads(versions[source_ticker])
    wanted = {f["quality_receipt_sha256"] for f in replay["facts"]}
    bundles = [b for b in source_doc["quality_bundles"] if b["quality"]["receipt_sha256"] in wanted]
    require({b["quality"]["receipt_sha256"] for b in bundles} == wanted, MISSING + ":source_quality_bundle")
    outputs = [_replay_quality(b) for b in bundles]
    periods = {f["fields"]["period_end"] for f in replay["facts"]}
    providers = {o["metadata"]["provider"] for o in outputs}
    types = {o["metadata"]["source_type"] for o in outputs}
    require(len(periods) == len(providers) == len(types) == 1, "quality_source_tuple_ambiguous")
    period = next(iter(periods))
    require(all(o["metadata"]["period"] == period and o["original_source_ticker"] == source_ticker for o in outputs),
            "quality_source_subject_or_period_mismatch")
    identity = _identity(local_seeds, ticker)
    issuer = {f["fields"]["issuer_id"] for f in replay["facts"]}
    require(len(issuer) == 1, "quality_issuer_mismatch")
    # Preserve every selected source's field-level verdict. No competing source
    # erases a denial; foreign split-field receipts remain separately inspectable.
    merged = {"fields": {str(i) + ":" + k: v for i, out in enumerate(outputs)
                         for k, v in out["quality"]["fields"].items()}}
    reasons = sorted({r for o in outputs for r in o["quality"]["quality_reason_codes"]})
    fields = dict(state=aggregate_state(merged), reason_codes=reasons,
        source_type=next(iter(types)), source_period=period, provider=next(iter(providers)),
        decision_version=outputs[0]["quality"]["decision_version"],
        quality_scope="selected_reported_business_source_inputs")
    inputs = [{"source_inputs_sha256": o["input_sha256"], "formal_sha256": o["formal_sha256"],
               "quality_receipt_sha256": o["source_quality"]["receipt_sha256"],
               "source_generation_id": o["source_generation_id"]} for o in outputs]
    fact = dict(fact_id="financial_quality:" + period, fact_type="financial_quality", as_of_date=period,
        source="deterministic_financial_validation", fields=fields, prose_eligible=True,
        interpretation_eligible=False, numeric_registry_eligible=False,
        ticker=ticker, source_ticker=source_ticker, issuer_id=next(iter(issuer)),
        canonical_security_id=identity["canonical_security_id"],
        derivation_owner=CONTRACT, source_input_bindings=inputs,
        input_fact_ids=sorted(f["fact_id"] for f in replay["facts"]),
        issuer_business_bridge=deepcopy(bridge))
    receipt = dict(contract=CONTRACT, ticker=ticker, original_source_ticker=source_ticker,
        canonical_ref="canonical:" + fact["fact_id"], fact_sha256=digest(fact),
        original_stock_sha256=digest(stock), business_version_sha256=replay["version_sha256"],
        source_version_sha256=version_hashes["class-c/business-versioned-" + source_ticker + ".json"],
        source_replay_sha256=digest(replay), inputs=inputs, owner_outputs=outputs,
        input_fact_sha256={f["fact_id"]: digest(f) for f in replay["facts"]},
        directional_use_allowed=False, security_valuation_transfer=False,
        derivation_version=CONTRACT, state_owner="financial-quality-taint-v2")
    receipt["receipt_sha256"] = digest(receipt)
    return dict(fact=fact, receipt=receipt)


def verify(supplement, **inputs):
    require(supplement == derive(**inputs), "derived_quality_not_reproducible")
    return True
