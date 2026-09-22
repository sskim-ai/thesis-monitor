from copy import deepcopy

import pytest

from scripts.m12da_source_use_contract import canonical_sha256
from scripts.m12dk_current_source_authority import freeze_current_source_binding
from scripts.m12dp_observed_business_coverage import READY, evaluate_cohort, evaluate_subject
from tests.test_m12dk_current_source_authority import PERIOD, inputs


def subject(*paths, ticker="FICTIONAL_RENAMED", mutate_fact=None):
    data = inputs(paths or ("stock.fact_catalog.earnings:" + PERIOD,),
                  ticker=ticker, mutate_fact=mutate_fact)
    mapping = {
        "contract": "m12dp-existing-provider-issuer-binding-v1", "ticker": ticker,
        "source_generation_id": "source-frozen", "market": "us", "status": "PASS",
        "owner": "SecFinancialSnapshotService._resolve_cik", "provider": "sec_edgar",
        "issuer_id": "CIK:0000000001", "source_record": {"ticker": ticker, "cik": "0000000001"},
        "observed_at": "2026-09-21T00:00:00+00:00", "security_denominator_inferred": False,
    }
    mapping["binding_sha256"] = canonical_sha256(mapping)
    data.update(issuer_binding=mapping, expected_issuer_binding_sha256=canonical_sha256(mapping))
    return data


def rebind(data):
    data["frozen_binding"] = freeze_current_source_binding(
        source_generation_id=data["source_generation_id"], source_packet=data["source_packet"],
        evidence_packet=data["evidence_packet"],
    )
    mapping = data["issuer_binding"]
    mapping.pop("binding_sha256")
    mapping["binding_sha256"] = canonical_sha256(mapping)
    data["expected_issuer_binding_sha256"] = canonical_sha256(mapping)


def test_verified_past_report_is_not_relabelled_current_and_inputs_immutable():
    data = subject()
    before = deepcopy(data)
    result = evaluate_subject(**data)
    assert result["status"] == READY
    assert result["sources"][0]["as_of"] == PERIOD
    assert result["sources"][0]["field_lineage"]["status"] == "PASS"
    assert result["issuer_binding"]["issuer_id"] == "CIK:0000000001"
    assert data == before


@pytest.mark.parametrize("path", [
    "stock.thesis.core_thesis", "stock.thesis.market_expectations",
    "stock.fact_catalog.financial_quality:latest", "stock.fact_catalog.security_basis:latest",
    "stock.fact_catalog.price_structure:latest", "unknown.business.source",
    "stock.thesis.strengthen_signals", "stock.thesis.macro_exposures",
    "stock.fact_catalog.working-capital-relation:latest",
])
def test_context_or_unknown_never_becomes_observed_direction(path):
    result = evaluate_subject(**subject(path))
    assert result["status"] == "ONLY_CONTEXT_OR_BASELINE_THESIS"
    assert result["directional_source_refs"] == []


@pytest.mark.parametrize("change", ["quality", "provider", "future", "period", "value"])
def test_bad_financial_source_fails_closed(change):
    def mutate(fact):
        quality = fact["field_quality"]["fields.revenue.value"]
        if change == "quality":
            quality["prose_eligible"] = False
        elif change == "provider":
            quality["provider"] = "unknown"
        elif change == "future":
            fact["financial_quality"]["source_snapshot"]["filing_date"] = "2027-01-01"
        elif change == "period":
            quality["source_period"] = "2026-03-31"
        else:
            fact["fields"]["revenue"]["value"] = None
    result = evaluate_subject(**subject(mutate_fact=mutate))
    assert result["status"] == "SOURCE_QUALITY_UNUSABLE"
    assert not result["directional_source_refs"]


@pytest.mark.parametrize("change", ["ticker", "generation", "raw", "issuer", "digest"])
def test_binding_drift_is_not_a_coverage_pass(change):
    data = subject()
    if change == "ticker":
        data["ticker"] = "OTHER"
    elif change == "generation":
        data["source_generation_id"] = "new-generation"
    elif change == "raw":
        data["source_metadata"][0]["statement"] = "unbound"
    elif change == "issuer":
        data["issuer_binding"]["source_record"]["ticker"] = "OTHER"
        rebind(data)
    else:
        data["expected_issuer_binding_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        evaluate_subject(**data)


def test_issuer_only_mapping_does_not_require_adr_denominator():
    data = subject()
    data["source_packet"]["stocks"][0]["valuation"] = {
        "resolved_issuer_type": "adr", "adr_ratio": None,
        "security_identity_state": "unknown", "security_identity_verification_status": "unverified",
    }
    rebind(data)
    assert evaluate_subject(**data)["status"] == READY


def test_failed_mapping_cannot_borrow_another_issuer():
    data = subject()
    data["issuer_binding"]["status"] = "FAIL"
    rebind(data)
    result = evaluate_subject(**data)
    assert result["status"] == "ISSUER_SECURITY_BINDING_UNRESOLVED"
    assert not result["directional_source_refs"]


def test_whole_cohort_failure_prevents_any_core_calls():
    good = subject(ticker="GOOD")
    missing = subject("stock.thesis.core_thesis", ticker="MISSING")
    bad = subject(ticker="DRIFT")
    bad["frozen_binding"]["binding_sha256"] = "0" * 64
    gate = evaluate_cohort([missing, bad, good], expected_subjects=["GOOD", "DRIFT", "MISSING"])
    assert len(gate["subjects"]) == 3
    assert gate["ready_count"] == 1
    assert gate["terminal"] == "M12DP_CURRENT_SOURCE_COLLECTION_OR_BINDING_FAILED"
    assert not gate["allow_core_preflight"] and not gate["allow_model_calls"]


def test_coverage_pass_still_requires_core_schema_gate():
    data = subject()
    result = evaluate_cohort([data], expected_subjects=[data["ticker"]])
    assert result["allow_core_preflight"]
    assert not result["allow_model_calls"]


def test_cohort_cannot_combine_independently_bound_different_generations():
    first, second = subject(ticker="ONE"), subject(ticker="TWO")
    second["source_generation_id"] = "different-generation"
    second["issuer_binding"]["source_generation_id"] = "different-generation"
    rebind(second)
    assert evaluate_subject(**second)["status"] == READY
    with pytest.raises(ValueError, match="coverage_cohort_generation_mismatch"):
        evaluate_cohort([first, second], expected_subjects=["ONE", "TWO"])


@pytest.mark.parametrize("expected", [[], ["OTHER"], ["FICTIONAL_RENAMED", "FICTIONAL_RENAMED"]])
def test_registry_not_forced_to_static_expected_22(expected):
    with pytest.raises(ValueError, match="coverage_active_population_mismatch"):
        evaluate_cohort([subject()], expected_subjects=expected)
