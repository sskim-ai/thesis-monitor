from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from app.services import canonical_business_quality_owner as owner
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from scripts import r2b_r3_quality as binding
from scripts import r2b_r2_preflight as previous
from scripts.m12da_source_use_contract import build_trusted_source_authority_manifest
from scripts.m12dr_financial_source_authority import source_quality, comparative_facts
from tests.test_m12ds_r4_r1_sec_field_quality import fixture
from tests.test_financial_observation_quality import snapshots


def bundle_for(provider):
    if provider == "sec_companyfacts":
        prior, current = fixture("FICTIVE")
        preliminary = None
    else:
        current, _ = snapshots()
        preliminary = prior = None
    inputs = dict(ticker="FICTIVE", cutoff="2026-09-27", formal=current.model_dump(mode="json"),
        comparison=prior.model_dump(mode="json") if prior else None, preliminary=preliminary, foreign_candidates=[])
    bundle = dict(source_inputs=inputs, source_inputs_sha256=digest(inputs), source_generation_id="synthetic-source")
    bundle["quality"] = source_quality(bundle)
    return bundle


def derive_inputs():
    bundle = bundle_for("sec_companyfacts")
    facts = comparative_facts(bundle["quality"], ticker="FICTIVE", issuer_id="CIK:0000001234")
    doc = dict(contract="frozen-accepted-reported-comparison-input-v1", ticker="FICTIVE",
        frozen_at="2026-09-27T01:00:00+00:00", original_cutoff="2026-09-27T00:00:00+00:00",
        source_artifact_sha256="a" * 64, parent_zip_sha256="b" * 64, quality_bundles=[bundle], facts=facts,
        financial_source_graph={}, issuer_business_bridge=None, scope="issuer_business_only",
        old_class_a_values_consumed=False, prior_event_reused_as_class_b=False)
    raw = json.dumps(doc).encode()
    local = dict(roles={"identity": {"records": [dict(table="securitymaster", record=dict(ticker="FICTIVE",
        canonical_security_id="fictional-security", canonical_company_id="fictional-issuer", cik="0000001234"))]}})
    return dict(stock=dict(ticker="FICTIVE", packet={"stocks": [{"fact_catalog": facts}]}),
        versions={"FICTIVE": raw}, version_hashes={"class-c/business-versioned-FICTIVE.json": sha256_bytes(raw)},
        local_seeds=[local], cutoff=datetime(2026, 9, 27, 2, tzinfo=timezone.utc),
        policy=UnifiedSourcePolicy(frozenset({"sec_companyfacts"})))


@pytest.mark.parametrize("provider", ["sec_companyfacts", "opendart"])
def test_original_owners_replayed_without_threshold_changes(provider):
    bundle = bundle_for(provider)
    before = deepcopy(bundle)
    result = owner._replay_quality(bundle)
    assert before == bundle
    assert result == owner._replay_quality(bundle)
    assert result["quality"]["decision_version"] == "financial-quality-taint-v2"
    if provider == "sec_companyfacts":
        assert "sec_business_occurrence_conflict" in result["quality"]["quality_reason_codes"]
        assert result["quality"]["fields"]["latest_operating_income"]["state"] == "verified_usable"
        assert "latest_revenue" not in result["quality"]["fields"]
    else:
        assert owner.aggregate_state(result["quality"]) == "denied"
        assert "net_income_exceeds_revenue" in result["quality"]["quality_reason_codes"]


def test_canonical_identity_lineage_idempotency_and_no_mutation():
    inputs = derive_inputs()
    before = deepcopy(inputs["stock"])
    result = owner.derive(**inputs)
    assert result == owner.derive(**inputs)
    assert inputs["stock"] == before
    assert owner.verify(result, **inputs)
    assert result["fact"]["fields"]["source_period"] == "2026-06-30"
    assert result["fact"]["source_input_bindings"]
    assert result["receipt"]["input_fact_sha256"]
    assert result["receipt"]["directional_use_allowed"] is False


@pytest.mark.parametrize("field,value", [("ticker", "OTHER"), ("source_ticker", "OTHER"),
    ("issuer_id", "OTHER"), ("canonical_security_id", "OTHER"), ("as_of_date", "2025-06-30"),
    ("derivation_owner", "FAKE")])
def test_derived_fact_wrong_ownership_fails_exact_replay(field, value):
    inputs = derive_inputs()
    result = owner.derive(**inputs)
    result["fact"][field] = value
    with pytest.raises(ValueError, match="not_reproducible"):
        owner.verify(result, **inputs)


@pytest.mark.parametrize("mutation", ["input_hash", "quality_output", "source_provider", "source_period"])
def test_no_forged_owner_output_or_input(mutation):
    bundle = bundle_for("sec_companyfacts")
    if mutation == "input_hash":
        bundle["source_inputs_sha256"] = "0" * 64
    elif mutation == "quality_output":
        bundle["quality"]["fields"]["current.revenue"]["state"] = "verified_usable"
    else:
        bundle["source_inputs"]["formal"]["provider" if mutation == "source_provider" else "financial_period_end"] = (
            "opendart" if mutation == "source_provider" else "2025-06-30")
        bundle["source_inputs_sha256"] = digest(bundle["source_inputs"])
    with pytest.raises(ValueError):
        owner._replay_quality(bundle)


def strict_source(state="verified_usable", reasons=()):
    ref = "canonical:financial_quality:2026-06-30"
    fields = dict(state=state, reason_codes=list(reasons), source_period="2026-06-30",
                  source_type="formal", decision_version="financial-quality-taint-v2")
    fact = dict(fact_id=ref.removeprefix("canonical:"), fact_type="financial_quality", as_of_date="2026-06-30", fields=fields)
    row = dict(ref_id=ref, label="financial_quality", category="earnings", as_of="2026-06-30",
               statement=json.dumps(fields))
    authority = build_trusted_source_authority_manifest(ticker="FICTIVE", source_generation_id="source",
        catalog=dict(ticker="FICTIVE", all_evidence_refs=[ref]), source_metadata=[row])
    return dict(ticker="FICTIVE", packet={"stocks": [{"fact_catalog": [fact]}]}, evidence_packet={"evidence": [row]}), {"authority": authority}


@pytest.mark.parametrize("state,effect", [("verified_usable", "NONE"), ("caution_usable", "CONFIDENCE_ONLY"),
                                       ("denied", "CONFIDENCE_ONLY"), ("unknown", "CONFIDENCE_ONLY")])
def test_present_quality_actual_a_materializer(state, effect):
    stock, authority = strict_source(state)
    projected = binding.require_quality_owner(stock, authority, decision_mode="EVIDENCE_BASED")
    assert projected["effect"] == effect and projected["directional_use_allowed"] is False
    ctx = dict(ticker="FICTIVE", business_evidence_quality_state=projected,
        eligible_claim_refs=["claim:synthetic"], premium_eligible_claim_refs=[], accepted_fundamental_claims=[],
        eligible_non_price_evidence=stock["evidence_packet"]["evidence"], data_quality_catalog=dict(
            evidence_refs=[projected["record_ref"]], positive_quality_refs=[], material_disclosure_failure_refs=[]))
    schema = previous.owner.future_pass_a_batch_schema(subjects=["FICTIVE"], subject_contexts={"FICTIVE": ctx})
    _, receipt = previous.materialization_probe("FICTIVE", schema, ctx)
    assert receipt["legacy_semantic"]["status"] == "PASS"


@pytest.mark.parametrize("mutation", ["absent", "fake_ref", "period", "subject", "direction", "security"])
def test_unowned_quality_blocked_upstream(mutation):
    stock, authority = strict_source("denied")
    record = authority["authority"]["authority_records"][0]
    if mutation == "absent":
        stock["packet"]["stocks"][0]["fact_catalog"] = []
    elif mutation == "fake_ref":
        stock["evidence_packet"]["evidence"][0]["ref_id"] += ":FAKE"
    elif mutation == "period":
        record["source_period"] = "2025-06-30"
    elif mutation == "subject":
        record["ticker"] = "OTHER"
    elif mutation == "direction":
        record["allowed_uses"].append("OVERALL_DIRECTION")
    else:
        record["source_family"] = "security_valuation"
    with pytest.raises(ValueError):
        binding.require_quality_owner(stock, authority, decision_mode="EVIDENCE_BASED")


def test_unknown_no_quality_effect_requires_zero_entitlement():
    stock = dict(ticker="FICTIONAL", packet={"stocks": [{"fact_catalog": []}]})
    authority = {"authority": {"authority_records": []}}
    assert binding.require_quality_owner(stock, authority, decision_mode="UNKNOWN_LIMIT")["effect"] is None
    authority["authority"]["authority_records"] = [{"allowed_uses": ["HOLDER_STANCE"]}]
    with pytest.raises(ValueError):
        binding.require_quality_owner(stock, authority, decision_mode="UNKNOWN_LIMIT")


def test_blind_source_materiality_blocks_new_diagnosis_not_name_match():
    inputs = derive_inputs()
    supplement = owner.derive(**inputs)
    blind = {"source_packet": inputs["stock"]["packet"], "unrelated_text": "sec_business_occurrence_conflict"}
    assert binding.blind_materiality(supplement, blind)["status"] == "MATERIAL_SOURCE_VIEW_CHANGED"
    blind["reason_codes"] = supplement["fact"]["fields"]["reason_codes"]
    assert binding.blind_materiality(supplement, blind)["status"] == "ANNOTATION_ONLY"
    blind["source_packet"] = {"stocks": [{"fact_catalog": []}]}
    assert binding.blind_materiality(supplement, blind)["missing_or_changed_input_facts"]


@pytest.mark.parametrize("states,expected", [(["verified_usable"], "verified_usable"),
    (["verified_usable", "caution_usable"], "caution_usable"),
    (["caution_usable", "denied"], "denied"), (["unknown"], "unknown")])
def test_existing_canonical_precedence(states, expected):
    assert owner.aggregate_state({"fields": {str(i): {"state": s} for i, s in enumerate(states)}}) == expected
