from copy import deepcopy
import json

import pytest

from scripts import r2b_r2_contract as c
from scripts.r2b_r2_preflight import schema_check
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema


def unknown_fixture():
    recovery = {"source-recovery:fictional": {"kind": "QUALIFIED_FINANCIAL_LINEAGE"}}
    row = dict(decision_mode="UNKNOWN_LIMIT", overall_direction="OBSERVE", new_buyer="OBSERVE", holder="OBSERVE",
        directional_buy_score=None, directional_sell_score=None, confidence=None,
        limitation_reason="ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE",
        unknowns=list(recovery), required_next_evidence=list(recovery))
    return row, recovery, {k: [] for k in c.DIRECTION_BUCKETS}


def test_unknown_is_whole_decision_not_balanced_hold():
    row, recovery, cap = unknown_fixture()
    assert c.validate_unknown(row, mode="UNKNOWN_LIMIT", recovery=recovery, capability=cap)["status"] == "PASS"
    schema_check(c.unknown_schema(recovery))
    assert not validate_json_schema(row, c.unknown_schema(recovery))
    message = c.render_unknown("FICTIONAL", row, recovery=recovery, capability=cap)
    assert "판단 근거 제한" in message and "보유 권고를 뜻하지 않습니다" in message
    assert "5:5" not in message and "매수 관점" not in message


@pytest.mark.parametrize("key,value", [
    ("overall_direction", "HOLD"), ("overall_direction", "BUY"), ("overall_direction", "SELL"),
    ("holder", "HOLDABLE"), ("holder", "REDUCE"), ("holder", "REVIEW"),
    ("new_buyer", "WAIT"), ("new_buyer", "ATTRACTIVE"), ("new_buyer", "AVOID"),
    ("directional_buy_score", 5), ("directional_sell_score", 5), ("confidence", "LOW"),
    ("limitation_reason", ""), ("unknowns", []), ("required_next_evidence", []),
    ("unknowns", ["technical-support"]), ("required_next_evidence", ["price-breakout"]),
    ("rationale", "BUY now"), ("unknowns", ["source-recovery:fictional"] * 2),
])
def test_unknown_rejects_direction_ratio_prose_and_unowned_recovery(key, value):
    row, recovery, cap = unknown_fixture()
    row[key] = value
    with pytest.raises(ValueError):
        c.validate_unknown(row, mode="UNKNOWN_LIMIT", recovery=recovery, capability=cap)
    assert validate_json_schema(row, c.unknown_schema(recovery))


@pytest.mark.parametrize("bucket", c.DIRECTION_BUCKETS)
def test_unknown_rejects_any_observed_capability(bucket):
    row, recovery, cap = unknown_fixture()
    cap[bucket] = ["claim:observed"]
    with pytest.raises(ValueError, match="directional_capability"):
        c.validate_unknown(row, mode="UNKNOWN_LIMIT", recovery=recovery, capability=cap)


def base_gate():
    stock = dict(status="PASS", mandatory_missing=[], component_binding=[dict(
        requirement="MANDATORY", eligible=True, selected_value_in_packet=True)])
    authority = dict(status="PASS", authority_errors=[], authority_records=[dict(
        ref_id="context", allowed_uses=["CONTEXT"], prohibited_uses=["OVERALL_DIRECTION"],
        authority_state="RESOLVED", denial_reasons=["requires_review"])])
    return stock, authority


def test_unknown_eligibility_generic_context_only_not_missing_source():
    stock, authority = base_gate()
    assert c.decision_mode(stock, authority, {}) == "UNKNOWN_LIMIT"
    stock["mandatory_missing"] = ["price"]
    with pytest.raises(ValueError, match="source_assembly"):
        c.decision_mode(stock, authority, {})


@pytest.mark.parametrize("change", ["price", "authority", "denial", "observation"])
def test_unknown_never_masks_broken_inputs(change):
    stock, authority = base_gate()
    obs = {}
    if change == "price":
        stock["component_binding"][0]["eligible"] = False
    elif change == "authority":
        authority["status"] = "FAIL"
    elif change == "denial":
        authority["authority_records"][0]["denial_reasons"] = []
    else:
        obs["unowned"] = {}
    with pytest.raises(ValueError):
        c.decision_mode(stock, authority, obs)


def test_unknown_cannot_hide_separate_holder_entitlement():
    stock, authority = base_gate()
    authority["authority_records"][0]["allowed_uses"].append("HOLDER_STANCE")
    with pytest.raises(ValueError, match="has_holder_entitlement"):
        c.decision_mode(stock, authority, {})


@pytest.mark.parametrize("effects", [["positive"], ["negative"], ["positive", "negative"]])
def test_authorized_evidence_does_not_enter_unknown(effects):
    stock, authority = base_gate()
    authority["authority_records"][0].update(allowed_uses=["OVERALL_DIRECTION"], prohibited_uses=[])
    assert c.decision_mode(stock, authority, {effect: {} for effect in effects}) == "EVIDENCE_BASED"


def test_evidence_based_schema_delegation_unchanged():
    _, _, cap = unknown_fixture()
    cap.update(positive=["positive"], negative=[], holder_support=["positive"],
               confidence=[], quality=[], condition=[], risk_triggers={}, sell_eligible=[], current_stress=[])
    valuation = dict(fundamental_valid=False, compensating_discount=False)
    assert c.decision_schema("EVIDENCE_BASED", cap, valuation, {}, {}) == c.schemas.decision_schema(cap, valuation, {})
    stock, authority = base_gate()
    authority["authority_records"][0].update(allowed_uses=["OVERALL_DIRECTION"], prohibited_uses=[])
    assert c.decision_mode(stock, authority, {"observation": {}}) == "EVIDENCE_BASED"
    with pytest.raises(ValueError, match="authorized_direction_has_no_observation"):
        c.decision_mode(stock, authority, {})


def strategy_fixture():
    rules = dict(currency="USD", basis="close", support_zone_low=10, support_zone_high=12)
    record = dict(id=1, ticker="FICTIONAL", version=2, status="active",
                  created_at="2026-08-01T12:00:00", price_rules=json.dumps(rules))
    thesis = dict(table="investmentthesis", record_id="1", record=record, original_record_sha256=c.digest(record))
    security = dict(table="securitymaster", record_id="2", record=dict(ticker="FICTIONAL", canonical_security_id="SEC1"))
    security["original_record_sha256"] = c.digest(security["record"])
    roles = {"stored_thesis_and_business_metadata": dict(records=[thesis], eligible=True),
             "security_identity": dict(records=[security], eligible=True)}
    for role in roles.values():
        role["version"] = c.digest(role["records"])
    local = dict(contract="unified-local-seed-projection-v1", roles=roles, market="us")
    fact = dict(fact_id="chart:stored_price_rules", fact_type="chart_price_rules", source="investment_thesis",
                as_of_date="", fields=rules)
    stock = dict(ticker="FICTIONAL", market="us", input_hashes={"local": c.digest(local)}, packet=dict(stocks=[dict(
        ticker="FICTIONAL", thesis_version=2, chart_context={"stored_price_rules": rules}, fact_catalog=[fact])]))
    return stock, local


def test_exact_version_metadata_not_current_market_timestamp():
    stock, local = strategy_fixture()
    original = deepcopy(stock)
    receipt = c.versioned_rule_binding(stock, local, cutoff="2026-09-27T00:00:00+00:00")
    assert receipt["status"] == "PASS" and receipt["time_kind"] == "VERSIONED_STRATEGY_METADATA"
    assert receipt["original_as_of"] == "" and receipt["version_created_at"] == "2026-08-01T12:00:00"
    assert not receipt["current_market_as_of"] and stock == original
    later = c.versioned_rule_binding(stock, local, cutoff="2026-10-01T00:00:00+00:00")
    assert later == receipt


@pytest.mark.parametrize("mutation", ["version", "value", "currency", "source", "missing", "created", "future", "record_hash", "local_hash", "security"])
def test_stored_rule_binding_rejects_unowned_metadata(mutation):
    stock, local = strategy_fixture()
    raw = stock["packet"]["stocks"][0]
    if mutation == "version":
        raw["thesis_version"] = 3
    elif mutation in {"value", "currency"}:
        raw["fact_catalog"][0]["fields"] = {**raw["fact_catalog"][0]["fields"],
            ("support_zone_low" if mutation == "value" else "currency"): (11 if mutation == "value" else "KRW")}
    elif mutation == "source":
        raw["fact_catalog"][0]["source"] = "assessment_clock"
    elif mutation == "local_hash":
        stock["input_hashes"]["local"] = "wrong"
    else:
        role = local["roles"]["stored_thesis_and_business_metadata"]
        if mutation == "missing":
            role["records"] = []
        elif mutation == "security":
            local["roles"]["security_identity"]["records"] = []
        elif mutation == "record_hash":
            role["records"][0]["original_record_sha256"] = "wrong"
        else:
            record = role["records"][0]["record"]
            record["created_at"] = "" if mutation == "created" else "2027-01-01T00:00:00"
            role["records"][0]["original_record_sha256"] = c.digest(record)
        for role in local["roles"].values():
            role["version"] = c.digest(role["records"])
        stock["input_hashes"]["local"] = c.digest(local)
    receipt = c.versioned_rule_binding(stock, local, cutoff="2026-09-27T00:00:00+00:00")
    assert receipt["status"] == "DENIED" and receipt["denial_reason"] == c.RULE_DENIAL


def test_denied_rule_copied_thesis_removed_but_independent_price_retained():
    rows = [dict(ref_id=c.RULE_REF, category="chart", statement="10 to 12"),
            dict(ref_id="thesis:core", category="thesis", statement="old support 10 to 12"),
            dict(ref_id="canonical:chart:daily", category="chart", statement="current close 10")]
    stock = dict(evidence_packet=dict(evidence=rows), ownership=dict(
        source_packet=dict(evidence=rows), evidence=[dict(ref=r) for r in rows]))
    view, denied = c._filter_denied_rule_view(stock)
    assert denied == {c.RULE_REF, "thesis:core"}
    assert view["evidence_packet"]["evidence"] == [rows[-1]]
    assert len(stock["evidence_packet"]["evidence"]) == 3
