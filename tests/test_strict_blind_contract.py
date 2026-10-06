from copy import deepcopy
import json

import pytest

from app.services.unified_snapshot_contract import digest
from scripts import strict_blind_contract as b
from scripts import strict_blind_comparison as compare
from tests.strict_blind_fixtures import source_inputs, response, from_context


@pytest.mark.parametrize("risk,timing,denied,technical", [
    (False, "FAVORABLE_NOW", (), True),
    (False, "WAIT_FOR_ZONE", (), True),
    (False, "UNRESOLVED", (), False),
    (False, "UNRESOLVED", ("PER", "FORWARD_PE"), False),
    (False, "WAIT_FOR_ZONE", ("FORWARD_PE",), True),
    (True, "WAIT_FOR_ZONE", (), True),
])
def test_real_contract_offline_positive_cases(tmp_path, risk, timing, denied, technical):
    inp = source_inputs(tmp_path, risk=risk, denied=denied, technical=technical, timing=timing)
    before = digest(inp)
    subject, audit = b.project_subject(inp, generation="new-offline-generation")
    raw = response(subject, audit, risk=risk, timing=timing)
    payload, wire_receipt = b.payload(subject)
    assert not b.validate_json_schema(raw, payload["response_schema"])
    assert b.validate_output(raw, subject, audit)["status"] == "PASS"
    assert wire_receipt and digest(inp) == before
    assert "observations" not in subject and "business_gate" not in json.dumps(payload)
    assert not subject["evidence"]["source:price"]["value"].get("unavailable")


def test_kr_native_per_survives_fy1_no_estimate(tmp_path):
    from app.services.provider_valuation_calibration_context import calibration_context
    from tests.test_newbuyer_b2_v2_coverage import source, compose
    owner = source(tmp_path, ticker="003690", empty=True)
    coverage = compose(owner)
    inp = from_context(calibration_context(owner.stock["valuation_view"]), technical=False)
    inp.update(coverage=coverage["coverage"], census=coverage["census"])
    subject, audit = b.project_subject(inp, generation="new-offline-generation")
    states = {r["metric"]: r["state"] for r in audit["resolution"]}
    assert states["PER"] == "USABLE"
    assert states["CURRENT_FY1_FPER"] == "UNUSABLE_TYPED_DENIAL"
    raw = response(subject, audit, timing="UNRESOLVED")
    assert raw["axes"]["valuation_evaluability"]["judgment"] == "EVALUABLE"
    assert b.validate_output(raw, subject, audit)["status"] == "PASS"
    assert all(row["value"] is None for row in subject["evidence"].values()
        if row.get("metric") == "CURRENT_FY1_FPER")


@pytest.mark.parametrize("bad", ["marker", "missing_axis", "enum", "ticker", "security_id", "generation",
    "source_generation_id", "subject_sha256", "outside_ref", "blocked_metric", "cross_metric",
    "timing_overwrite", "risk_suppression", "numeric", "fair_value", "duplicate", "holder_scope"])
def test_invalid_blind_responses_reject(tmp_path, bad):
    inp = source_inputs(tmp_path, denied=("FORWARD_PE",))
    subject, audit = b.project_subject(inp, generation="new-offline-generation")
    raw = response(subject, audit)
    if bad == "marker":
        raw = {"synthetic": "BLIND"}
    elif bad == "missing_axis":
        del raw["axes"]["holder"]
    elif bad == "enum":
        raw["axes"]["new_buyer"]["judgment"] = "BUY"
    elif bad in ("ticker", "security_id", "generation", "source_generation_id", "subject_sha256"):
        raw[bad] = "wrong"
    elif bad == "outside_ref":
        raw["axes"]["holder"]["evidence_refs"] = ["other:security"]
    elif bad == "blocked_metric":
        raw["axes"]["valuation_state"]["evidence_refs"] = audit["evaluability"]["blocked_metric_refs"]
    elif bad == "cross_metric":
        raw["axes"]["valuation_evaluability"]["judgment"] = "ALL_RELEVANT_METRICS_UNUSABLE"
    elif bad == "timing_overwrite":
        raw["axes"]["new_buyer"]["judgment"] = "WAIT"
    elif bad == "risk_suppression":
        raw["axes"]["active_material_risk"]["judgment"] = True
    elif bad == "numeric":
        raw["axes"]["new_buyer"]["rationale"] = "Fair value 200"
    elif bad == "fair_value":
        raw["fair_value"] = 200
    elif bad == "duplicate":
        raw["axes"]["new_buyer"]["evidence_refs"] *= 2
    else:
        raw["axes"]["holder"]["judgment"] = "REDUCE"
    receipt = b.validate_output(raw, subject, audit)
    assert receipt["status"] == "FAIL" and not receipt["retryable"]


@pytest.mark.parametrize("key", ["business_gate", "active_risk_state", "timing_state", "valuation_state",
    "valuation_evaluability", "core_output", "independent_assessment", "human_comparison", "ai_new_buyer"])
def test_dynamic_contamination_in_json_string_rejected(tmp_path, key):
    inp = source_inputs(tmp_path)
    inp["metadata"][0]["statement"] = json.dumps({key: "OLD_DECISION"})
    with pytest.raises(ValueError):
        b.project_subject(inp, generation="new")


def test_source_package_reprojection_rejects_tamper_and_empty(tmp_path):
    inp = source_inputs(tmp_path)
    source = dict(generation="new", blind_inputs={inp["ticker"]: inp})
    package = b.package(source)
    assert b.validate_package(package, source)
    package["subjects"][inp["ticker"]]["source_sha256"] = "0" * 64
    assert not b.validate_package(package, source)
    with pytest.raises(ValueError, match="EMPTY"):
        b.package(dict(generation="new", blind_inputs={}))
    inp["metadata"][0]["statement"] = "changed fact"
    with pytest.raises(ValueError, match="AUTHORITY_BINDING"):
        b.project_subject(inp, generation="new")


def test_economic_disagreement_never_becomes_accuracy_threshold(tmp_path):
    inp = source_inputs(tmp_path)
    subject, audit = b.project_subject(inp, generation="new")
    left = response(subject, audit)
    right = response(subject, audit, valuation="BURDENSOME")
    ticker = inp["ticker"]
    receipt = dict(status="PASS", blind_sha256=digest(left), monitoring_sha256=digest(right))
    result = compare.compare({ticker: left}, {ticker: right},
        binding_receipts={ticker: receipt}, semantic_receipts={ticker: receipt},
        authority=compare.AUTHORITY, acceptance=compare.ACCEPTANCE)
    assert result["status"] == "PASS" and result["ECONOMIC_JUDGMENT"]["disagreements"] == 2
    assert compare.validate_comparison(result, compare.AUTHORITY, compare.ACCEPTANCE)
    changed = deepcopy(compare.AUTHORITY)
    changed["historical_aliases"] = {"BUY": "ATTRACTIVE"}
    assert not compare.validate_comparison(result, changed, compare.ACCEPTANCE)
    assert not compare.valid_value(0, [False, True])
    unbound = compare.compare({ticker: left}, {ticker: right},
        binding_receipts={ticker: dict(status="PASS")}, semantic_receipts={ticker: receipt},
        authority=compare.AUTHORITY, acceptance=compare.ACCEPTANCE)
    assert unbound["status"] == "FAIL"
