"""Synthetic offline observations only; no provider client or credentials."""
from copy import deepcopy
from hashlib import sha256
import json

from pydantic import ValidationError
import pytest

from scripts import kis_no_estimate_owner as o
from scripts import newbuyer_fper_prerequisite_scope as s
from scripts.kis_current_fy1_owner import current_fper
from scripts.kis_eps_wire_calibration import sealed
from scripts.kis_fy1_semantic_owner import SemanticGap


def inputs(code="123456"):
    plan = sealed(dict(contract=o.PLAN, generation_id="synthetic-frozen-generation",
        as_of="2026-10-01T00:00:00+00:00", subjects=[code],
        securities={code: dict(ticker=code, canonical_security_id="synthetic-"+code)}))
    request = dict(method="GET", path=o.PATH, tr_id=o.TR_ID, security_code=code,
        params={"SHT_CD": code}, plan_sha256=plan["receipt_sha256"], redirects=False,
        started_at="2026-10-01T01:00:00+00:00")
    raw = json.dumps(dict(output1=o.EMPTY_OUTPUT1.copy(), output2=[], output3=[], output4=[],
        rt_cd="0", msg_cd="MCA00000", msg1="normal response"), sort_keys=True).encode()
    receipt = dict(request=deepcopy(request), raw_sha256=sha256(raw).hexdigest(), bytes=len(raw),
        state="COMPLETE", http_status=200, ended_at="2026-10-01T01:00:01+00:00",
        response_headers={"content-type": "application/json", "tr_id": o.TR_ID, "tr_cont": ""})
    return dict(code=code, generation=plan["generation_id"], plan=plan, raw=raw,
                receipt=receipt, request=request)


def payload(i, change):
    p = json.loads(i["raw"])
    change(p)
    i["raw"] = json.dumps(p, sort_keys=True).encode()
    i["receipt"].update(raw_sha256=sha256(i["raw"]).hexdigest(), bytes=len(i["raw"]))


def scope_inputs(i):
    eps = {"state": "UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE", "value": None}
    return dict(evidence_inputs=i, old_eps=eps, old_fper=current_fper(eps, None, None))


@pytest.mark.parametrize("code", ["123456", "654321", "999999"])
def test_normal_empty_request_bound_not_returned_identity(code):
    i = inputs(code)
    result = o.assess(**i)
    o.validate_assessment(result, **i)
    assert result["field_decision"] == "NO_RESEARCH_ESTIMATE_AT_RETRIEVAL"
    assert result["field_eligibility"] == "INELIGIBLE_NO_RESEARCH_ESTIMATE"
    assert result["normal_empty_confirmed"] and result["owner_complete"]
    assert result["request_binding_state"] == "REQUEST_BOUND_NEGATIVE_AVAILABILITY_OBSERVATION"
    assert result["provider_returned_security_identity_state"] == "UNAVAILABLE_NO_RETURNED_ESTIMATE_IDENTITY"
    assert result["source_generation"] == i["generation"]
    assert result["raw_sha256"] == sha256(i["raw"]).hexdigest()
    assert result["observation_time"] == i["receipt"]["ended_at"]
    assert result["field_effective_time_disposition"] == "NOT_AVAILABLE_BECAUSE_FIELD_ABSENT"
    assert all(result[k] is None for k in ("value", "estimate_effective_time", "estimate_period", "unit"))


@pytest.mark.parametrize("change", [
    lambda i: i["receipt"].update(http_status=403),
    lambda i: payload(i, lambda p: p.update(rt_cd="1")),
])
def test_provider_failure_never_normal_empty(change):
    i = inputs()
    change(i)
    result = o.assess(**i)
    assert result["field_decision"] == "SOURCE_FAILURE" and result["source_failure"]
    assert not result["normal_empty_confirmed"] and not result["owner_complete"]
    with pytest.raises(SemanticGap):
        s.prerequisite_scope(result, **scope_inputs(i))


def test_not_queried_is_not_empty_or_failure():
    i = inputs()
    i.update(raw=None, receipt=None, request=None)
    result = o.assess(**i)
    assert result["field_decision"] == "NOT_QUERIED"
    assert not result["source_failure"] and not result["owner_complete"]


@pytest.mark.parametrize("change", [
    lambda p: p.pop("output1"),
    lambda p: p.update(output1=[]),
    lambda p: p["output1"].pop("estdate"),
    lambda p: p["output1"].update(sht_cd="A123456"),
    lambda p: p["output1"].update(estdate="20260930"),
    lambda p: p["output1"].update(capital="0"),
    lambda p: p.update(output2={}),
    lambda p: p.update(output2=[{"value": "1"}]),
    lambda p: p.update(output3={}),
    lambda p: p.update(output3=None),
    lambda p: p.update(output4=[{"dt": "2026.12E"}]),
    lambda p: p.update(msg_cd="OTHER_SUCCESS"),
    lambda p: p.update(rt_cd=0),
    lambda p: p.update(extra={}),
])
def test_malformed_or_new_empty_shapes_fail_closed(change):
    i = inputs()
    payload(i, change)
    result = o.assess(**i)
    assert result["field_decision"] == "SEMANTIC_GAP"
    assert not result["owner_complete"] and not result["normal_empty_confirmed"]
    with pytest.raises(SemanticGap):
        s.prerequisite_scope(result, **scope_inputs(i))


def test_returned_identity_mismatch_is_not_empty():
    i = inputs()
    payload(i, lambda p: p["output1"].update(sht_cd="A654321"))
    result = o.assess(**i)
    assert result["field_decision"] == "IDENTITY_MISMATCH"
    assert result["provider_returned_security_identity_state"] == "MISMATCH"
    assert not result["normal_empty_confirmed"]


@pytest.mark.parametrize("field,value", [
    ("content-type", "text/html"), ("tr_id", "OTHER"), ("tr_cont", "M"), ("tr_cont", None),
])
def test_response_envelope_fail_closed(field, value):
    i = inputs()
    i["receipt"]["response_headers"][field] = value
    result = o.assess(**i)
    assert result["field_decision"] == "SEMANTIC_GAP" and not result["normal_empty_confirmed"]


@pytest.mark.parametrize("change", [
    lambda i: i.update(generation="other"),
    lambda i: i["receipt"].update(raw_sha256="0"*64),
    lambda i: i["receipt"].update(bytes=0),
    lambda i: i["receipt"].pop("ended_at"),
    lambda i: i["receipt"].update(ended_at="2026-10-01T01:00:01"),
    lambda i: i["receipt"].update(ended_at="2026-10-01T00:00:01+00:00"),
    lambda i: i["request"].update(started_at=None),
    lambda i: i["request"].update(tr_id="OTHER"),
    lambda i: i["request"].update(params={"SHT_CD": "654321"}),
    lambda i: i["plan"].update(generation_id="other"),
])
def test_missing_or_mutated_provenance_rejected(change):
    i = inputs()
    change(i)
    with pytest.raises(SemanticGap):
        o.assess(**i)


@pytest.mark.parametrize("field,value", [
    ("proof_type", "PRODUCER_SEMANTICS"), ("blocks_newbuyer_global_resolution", True),
    ("blocks_other_valuation_metrics", True), ("value", "10"), ("unit", "KRW_PER_SHARE"),
    ("owner_complete", False), ("observation_time", None), ("source_generation", "other"),
])
def test_resealed_forgery_cannot_manufacture_owner(field, value):
    i = inputs()
    result = o.assess(**i)
    result.pop("receipt_sha256")
    result[field] = value
    with pytest.raises((SemanticGap, ValidationError)):
        o.validate_assessment(sealed(result), **i)


def test_positive_estimate_requires_existing_positive_owner_not_inference():
    i = inputs()
    payload(i, lambda p: (p["output1"].update(sht_cd="A123456", estdate="20260930"),
                         p.update(output3=[{"data1": "1"}])))
    assert o.assess(**i)["field_decision"] == "SEMANTIC_GAP"
    from tests.test_kis_current_fy1_owner import eps
    positive = eps()
    positive.pop("receipt_sha256")
    positive.update(estimate_sha256=sha256(i["raw"]).hexdigest(), query_time=i["receipt"]["ended_at"])
    i["positive_eps"] = sealed(positive)
    before = deepcopy(i)
    result = o.assess(**i)
    assert result["field_decision"] == "USABLE_ESTIMATE_PRESENT"
    assert i == before and result["value"] is None
    assert not result["normal_empty_confirmed"]
    with pytest.raises(SemanticGap):
        s.prerequisite_scope(result, **scope_inputs(i))


def test_prerequisite_requirements_are_narrow_and_nonconsumption_owned():
    i = inputs()
    assessment = o.assess(**i)
    scope = s.prerequisite_scope(assessment, **scope_inputs(i))
    s.validate_scope(scope, assessment, **scope_inputs(i))
    assert len(scope["categories"]) == 11
    assert {r["category"] for r in scope["categories"] if r["required_on_this_path"]} == set(s.REQUIRED)
    for row in scope["categories"]:
        assert not row["positive_estimate_identity_granted"]
        if not row["required_on_this_path"]:
            assert row["proof_type"] == "PRODUCER_SEMANTICS"
            assert row["positive_non_consumption_proof"] == scope["dataflow_proof"]["receipt_sha256"]
    assert assessment["blocker_scope"] == "METRIC_SCOPED"
    assert assessment["blocks_metric_value_use"]
    assert not assessment["blocks_newbuyer_global_resolution"]
    assert not assessment["blocks_other_valuation_metrics"]


@pytest.mark.parametrize("change", [
    lambda scope: scope["categories"][1].update(positive_non_consumption_proof=None),
    lambda scope: scope.update(prerequisite_owner_ref=None),
    lambda scope: scope["categories"][0].update(category_semantics="POSITIVE_SECURITY_IDENTITY"),
    lambda scope: scope.update(producer_semantics_current_state_allowed=True),
])
def test_scope_rejects_unproved_na_or_identity_laundering(change):
    i = inputs()
    assessment = o.assess(**i)
    scope = s.prerequisite_scope(assessment, **scope_inputs(i))
    scope.pop("receipt_sha256")
    change(scope)
    with pytest.raises(SemanticGap):
        s.validate_scope(sealed(scope), assessment, **scope_inputs(i))


def test_short_circuit_does_not_touch_downstream_inputs():
    class Unreadable:
        def __bool__(self):
            raise AssertionError("downstream_access")

        def __getitem__(self, key):
            raise AssertionError("downstream_access")
    old = {"state": "UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE", "value": None}
    assert current_fper(old, Unreadable(), Unreadable()) == current_fper(old, None, None)
    assert s.nonconsumption_proof()["positive_non_consumption_proof"]


def test_ticker_literals_absent_from_owner_policy():
    from pathlib import Path
    for path in (Path(o.__file__), Path(s.__file__)):
        assert "003690" not in path.read_text()


def test_dataflow_mutation_invalidates_na(monkeypatch):
    monkeypatch.setattr(s, "PREFIX_SHA", "0"*64)
    with pytest.raises(SemanticGap, match="DATAFLOW_CHANGED"):
        s.nonconsumption_proof()


def prior_coverage(i):
    cells = []
    for category in s.CATEGORIES:
        cells.append(dict(category=category, metric="CURRENT_FY1_FPER", metric_ref="synthetic-fper",
            coverage_disposition="UNRESOLVED", owner_state="UNKNOWN", scope_level="METRIC_SCOPED"))
    return sealed(dict(contract="synthetic-prior-coverage", ticker=i["code"],
        source_generation=i["generation"], canonical_security_id="synthetic-"+i["code"],
        categories=cells, coverage_complete=False, owner_provenance_complete=False,
        temporal_provenance_complete=False, decision_provenance_complete=False,
        qualified_relevant_valuation_refs=["independently-qualified-native-per"],
        legacy_context_veto_status="UNRESOLVED_PENDING_BACKEND_COVERAGE"))


def test_coverage_then_metric_only_census_does_not_change_legacy_or_native_per():
    i = inputs()
    assessment = o.assess(**i)
    args = scope_inputs(i)
    scope = s.prerequisite_scope(assessment, **args)
    previous = prior_coverage(i)
    before = deepcopy(previous)
    row, changes = s.apply_to_coverage(previous, assessment, scope, **args)
    assert previous == before and len(changes) == 11
    assert row["qualified_relevant_valuation_refs"] == before["qualified_relevant_valuation_refs"]
    assert row["legacy_context_veto_status"] == before["legacy_context_veto_status"]
    assert row["coverage_complete"] and row["current_newbuyer_blocker_refs"] is None
    assert row["denied_relevant_valuation_refs"] == ["synthetic-fper"]
    assert row["receipt_ref"] == "availability-overlay:"+assessment["receipt_sha256"]
    census = s.blocker_census([row], expected_subjects=[i["code"]])
    assert census["current_blocker_count"] == 1
    assert census["global_blockers_emitted"] == 0
    assert census["rows"][0]["affected_metric_refs"] == ["synthetic-fper"]
    assert census["rows"][0]["scope_level"] == "METRIC_SCOPED"
    assert not census["rows"][0]["blocks_newbuyer_global_resolution"]


def test_incomplete_coverage_or_cohort_cannot_produce_census():
    i = inputs()
    with pytest.raises(SemanticGap, match="COVERAGE_INCOMPLETE"):
        s.blocker_census([prior_coverage(i)], expected_subjects=[i["code"]])
    with pytest.raises(SemanticGap, match="COHORT_GAP"):
        s.blocker_census([prior_coverage(i)], expected_subjects=[i["code"], "654321"])


def test_coverage_cannot_cross_generation():
    i = inputs()
    assessment = o.assess(**i)
    args = scope_inputs(i)
    scope = s.prerequisite_scope(assessment, **args)
    prior = prior_coverage(i)
    prior.pop("receipt_sha256")
    prior["source_generation"] = "other"
    prior = sealed(prior)
    with pytest.raises(SemanticGap, match="IDENTITY_GAP"):
        s.apply_to_coverage(prior, assessment, scope, **args)
