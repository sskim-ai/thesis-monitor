"""TEST_ONLY denied-recovery proofs; no admitted financial or direction fixture."""
from copy import deepcopy

import pytest

from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import (
    build_owned_evidence_packet, verified_owned_packet_view,
)
from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_contract as contract


def _fixture(*, fact_type="earnings_comparison", market="us"):
    ticker, generation = "FICTIONAL_RECOVERY", "test-only-recovery-generation"
    fact = {
        "fact_id": fact_type + ":unadmitted", "fact_type": fact_type,
        "as_of_date": "2026-06-30", "source": "test_only_unadmitted_projection",
        "fields": {"current_value": 100, "prior_comparable_value": 80},
    }
    source = {"ticker": ticker, "company_name": "Fictional recovery source",
              "fact_catalog": [fact], "thesis": {},
              "current_price_context": {"availability": "unavailable", "current_price": None}}
    packet = {"packet_id": generation + ":" + market, "market": market,
              "generated_at": "2026-10-08T08:10:00+09:00", "assessment_date": "2026-10-08",
              "stocks": [source]}
    evidence = build_decision_evidence_packet(packet=packet, stock=source)
    owned = build_owned_evidence_packet(evidence, stock=source)
    stock = {"contract": "fresh-financial-stock-owner-v1",
             "ticker": ticker, "market": market, "fresh_run_id": generation,
             "packet": packet, "evidence_packet": evidence.model_dump(mode="json"),
             "ownership": owned.model_dump(mode="json"), "financial_state": {"denials": []},
             "status": "PASS", "mandatory_missing": [], "component_binding": [
                 {"requirement": "MANDATORY", "eligible": True, "selected_value_in_packet": True}]}
    authority = {"ticker": ticker, "source_generation_id": generation, "status": "PASS",
                 "authority_errors": [], "authority_records": [
                     {"ref_id": "quality:current_price_context", "authority_state": "RESOLVED",
                      "allowed_uses": ["CONTEXT"], "prohibited_uses": ["OVERALL_DIRECTION", "HOLDER_STANCE"],
                      "denial_reasons": ["quality_limit_not_directional_evidence"]}]}
    return stock, authority


@pytest.mark.parametrize("market", ("us", "kr"))
@pytest.mark.parametrize("fact_type", ("earnings", "earnings_comparison"))
def test_sealed_unadmitted_financial_source_has_denied_recovery_only(market, fact_type):
    stock, authority = _fixture(fact_type=fact_type, market=market)
    before = deepcopy((stock, authority))
    owned = verified_owned_packet_view(stock)
    ref = "canonical:" + fact_type + ":unadmitted"
    assert ref not in owned.core_refs | owned.timing_refs
    assert contract.decision_mode(stock, authority, {}) == "UNKNOWN_LIMIT"
    recovery = contract.limitation_catalog(stock, authority)
    assert recovery == contract.limitation_catalog(stock, authority)
    assert len(recovery) == 1
    row = next(iter(recovery.values()))
    assert row["source_ref"] == ref
    assert row["state"] == "DENIED" and row["allowed_uses"] == []
    assert row["directional_use_allowed"] is False
    assert row["source_denial"] == ["CANONICAL_COMPATIBILITY_REQUIRES_SOURCE_ADMISSION"]
    assert row["recovery_primitive"] == "SOURCE_OWNER_FIELD_AND_CONSUMER_USE_RECEIPT"
    assert row["owned_packet_sha256"] == digest(stock["ownership"])
    assert not {"current_value", "prior_comparable_value", "delta", "growth_pct"} & row.keys()
    assert (stock, authority) == before
    raw = {"decision_mode": "UNKNOWN_LIMIT", "overall_direction": "OBSERVE",
           "new_buyer": "OBSERVE", "holder": "OBSERVE", "directional_buy_score": None,
           "directional_sell_score": None, "confidence": None,
           "limitation_reason": "ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE",
           "unknowns": list(recovery), "required_next_evidence": list(recovery)}
    capability = {bucket: [] for bucket in contract.DIRECTION_BUCKETS}
    assert contract.validate_unknown(raw, mode="UNKNOWN_LIMIT", recovery=recovery,
                                     capability=capability)["status"] == "PASS"
    with pytest.raises(ValueError):
        contract.validate_unknown({**raw, "overall_direction": "BUY"}, mode="UNKNOWN_LIMIT",
                                  recovery=recovery, capability=capability)
    capability["positive"] = [ref]
    with pytest.raises(ValueError, match="unknown_limit_directional_capability"):
        contract.validate_unknown(raw, mode="UNKNOWN_LIMIT", recovery=recovery, capability=capability)


@pytest.mark.parametrize("mutation", ("missing_seal", "owned_statement", "raw_packet", "fact", "clock",
                                    "assessment", "duplicate_fact", "missing_fact"))
def test_recovery_rejects_tampered_parent_or_source(mutation):
    stock, authority = _fixture()
    if mutation == "missing_seal":
        stock["ownership"]["backend_seal"] = None
    elif mutation == "owned_statement":
        stock["ownership"]["evidence"][0]["ref"]["statement"] = "caller replacement"
    elif mutation == "raw_packet":
        stock["evidence_packet"]["evidence"][0]["statement"] = "caller replacement"
    elif mutation == "fact":
        stock["packet"]["stocks"][0]["fact_catalog"][0]["fields"]["current_value"] = 101
    elif mutation == "clock":
        stock["packet"]["generated_at"] = "2026-10-09T08:10:00+09:00"
    elif mutation == "assessment":
        stock["packet"]["assessment_date"] = "2026-10-09"
    elif mutation == "duplicate_fact":
        facts = stock["packet"]["stocks"][0]["fact_catalog"]
        facts.append(deepcopy(facts[0]))
    else:
        stock["packet"]["stocks"][0]["fact_catalog"] = []
    with pytest.raises(ValueError):
        contract.limitation_catalog(stock, authority)


@pytest.mark.parametrize("mutation", ("ticker", "generation", "direction", "holder", "no_denial"))
def test_recovery_requires_same_subject_generation_and_denied_authority(mutation):
    stock, authority = _fixture()
    if mutation == "ticker":
        authority["ticker"] = "OTHER_FICTIONAL_SUBJECT"
    elif mutation == "generation":
        authority["source_generation_id"] = "different-generation"
    elif mutation == "no_denial":
        authority["authority_records"][0]["denial_reasons"] = []
    else:
        use = "OVERALL_DIRECTION" if mutation == "direction" else "HOLDER_STANCE"
        authority["authority_records"][0]["allowed_uses"].append(use)
        authority["authority_records"][0]["prohibited_uses"].remove(use)
    with pytest.raises(ValueError, match="unknown_recovery_requires_denied_same_subject_source"):
        contract.limitation_catalog(stock, authority)


@pytest.mark.parametrize("fact_type", ("event", "financial_quality", "chart", "fundamental"))
def test_other_audit_families_are_not_financial_recovery(fact_type):
    stock, authority = _fixture(fact_type=fact_type)
    with pytest.raises(ValueError, match="unknown_limit_source_recovery_missing"):
        contract.limitation_catalog(stock, authority)


def test_no_owned_source_does_not_create_generic_missing_evidence_recovery():
    stock, authority = _fixture()
    stock.pop("ownership")
    with pytest.raises(ValueError, match="unknown_limit_source_recovery_missing"):
        contract.limitation_catalog(stock, authority)


def test_caller_rebound_generation_cannot_replace_sealed_native_packet_identity():
    stock, authority = _fixture()
    stock["fresh_run_id"] = authority["source_generation_id"] = "caller-rebound-generation"
    authority["authority_manifest_sha256"] = digest(authority)
    with pytest.raises(ValueError, match="unknown_recovery_source_packet_mismatch"):
        contract.limitation_catalog(stock, authority)


@pytest.mark.parametrize("mutation", ("future", "missing_source_time"))
def test_newly_built_unqualified_time_cannot_supply_recovery(mutation):
    stock, authority = _fixture()
    source = stock["packet"]["stocks"][0]
    if mutation == "future":
        source["fact_catalog"][0]["as_of_date"] = "2027-06-30"
    evidence = build_decision_evidence_packet(packet=stock["packet"], stock=source)
    if mutation == "missing_source_time":
        evidence = evidence.model_copy(update={"evidence": tuple(
            row.model_copy(update={"source_time": None}) for row in evidence.evidence)})
    owned = build_owned_evidence_packet(evidence, stock=source)
    stock.update(evidence_packet=evidence.model_dump(mode="json"), ownership=owned.model_dump(mode="json"))
    with pytest.raises(ValueError, match="unknown_recovery_(source_time_mismatch|exact_financial_source_required)"):
        contract.limitation_catalog(stock, authority)


def test_existing_explicit_recovery_is_unchanged():
    stock = {"ticker": "FICTIONAL_RECOVERY", "financial_state": {"denials": ["missing_lineage"]}}
    authority = {"authority_records": []}
    key = "source-recovery:" + digest({"ticker": stock["ticker"], "denial": "missing_lineage"})
    assert contract.limitation_catalog(stock, authority) == {
        key: {"kind": "QUALIFIED_FINANCIAL_LINEAGE", "source_denial": "missing_lineage",
              "authority_sha256": digest(authority)}}
