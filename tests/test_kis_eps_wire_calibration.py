from copy import deepcopy
from datetime import date
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts import kis_eps_wire_calibration as c
from scripts import kis_fy1_semantic_owner as prior


def ev(value):
    raw = json.dumps(value, ensure_ascii=False).encode()
    return c.Evidence(raw, sha256(raw).hexdigest())


def estimate(code="123456"):
    rows = [{f"data{i}": str(1000 * row + i) for i in range(1, 6)} for row in range(8)]
    rows[1] = dict(zip([f"data{i}" for i in range(1, 6)], ["-1200", "2400", "4800", "9600", "12000"]))
    return {"rt_cd": "0", "output1": {"sht_cd": "A" + code}, "output3": rows,
            "output4": [{"dt": p} for p in ("2021.09", "2022.09", "2023.09", "2024.09E", "2025.09E")]}


def identity(code="123456"):
    return ev({"rt_cd": "0", "output": {"pdno": "00000A" + code, "shtn_pdno": code,
        "std_pdno": "KR7123456007", "prdt_type_cd": "300", "prdt_name": "Synthetic Common",
        "prdt_clsf_name": "주권", "ivst_prdt_type_cd_name": "주식"}})


def inventory(code="123456"):
    return ev({"status": "000", "page_no": 1, "total_page": 1, "total_count": 1, "list": [{
        "stock_code": code, "corp_code": "01234567", "rcept_no": "20231215000100",
        "rcept_dt": "20231215", "report_nm": "사업보고서 (2023.09)"}]})


def docs():
    return prior.Documentation(ev({"endpoint": prior.ENDPOINT, "output3_layout": list(prior.LAYOUT),
        "explicit_e_definition": True, "conflicting_marker_definition": False}))


def fixture(*, unit=True, code="123456", values=None, raw=None, mutate=None):
    est = ev(raw or estimate(code))
    ratio = ev({"rt_cd": "0", "output": [{"stac_yymm": p, "eps": v}
        for p, v in zip(("202109", "202209", "202309"), values or ["-300", "600", "1200"])]
        + [{"stac_yymm": "202403", "eps": "999"}]})
    receipt = {"security_code": code, "raw_sha256": ratio.sha256, "http_status": 200,
        "ended_at": "2024-07-01T00:00:00+00:00", "response_headers": {}, "request": {
        "method": "GET", "path": c.RATIO_PATH, "tr_id": c.RATIO_TR,
        "params": {"FID_DIV_CLS_CODE": "0", "fid_cond_mrkt_div_code": "J", "fid_input_iscd": code}}}
    review = {"endpoint": c.RATIO_PATH, "eps_field": "eps", "annual_selector": "0"}
    if unit:
        review["wire_to_display"] = {"kind": "OFFICIAL_EXPLICIT_RAW_TO_DISPLAY", "unit": "KRW_PER_SHARE",
            "multiplier": "1", "source_sha256": "d" * 64, "definition": "Synthetic explicit field unit, not live KIS authority"}
    if mutate:
        mutate(receipt, review)
    fiscal = c.fiscal_owner(code, "01234567", inventory(code), date(2024, 8, 1))
    reference = c.annual_reference(code, est, identity(code), ratio, ev(receipt), fiscal, ev(review))
    return est, reference


def qualified(**kwargs):
    est, ref = fixture(**kwargs)
    return est, ref, c.calibrate(est, docs(), ref)


def snapshot(est, cal, code="123456", **kwargs):
    return c.qualify_eps(code, "01234567", est, identity(code), inventory(code), date(2024, 8, 1),
        docs(), (), cal, estimate_transport=ev({"SHT_CD": code, "http_status": 200,
        "raw_sha256": est.sha256, "ended_at": "2024-07-01T00:00:00+00:00"}), **kwargs)


def test_exact_three_period_conversion_negative_and_valuation_roles():
    est, ref, cal = qualified()
    assert cal["state"] == "QUALIFIED"
    assert cal["wire_to_krw_per_share"] == "0.25"
    assert cal["matched_period_count"] == 3
    assert ref["excluded_periods"][0]["stac_yymm"] == "202403"
    result = snapshot(est, cal)
    assert result["value"] == "2400"
    assert result["period"] == "2024.09E"
    assert result["provider_per"] == "UNAVAILABLE_WIRE_SCALE"
    assert result["derived_fper"] == "UNAVAILABLE_PRICE_SHARE_SPLIT_BASIS"
    for role in prior.PROHIBITED_ROLES:
        assert not prior.admitted_to_role(result, role)
    for role in prior.ALLOWED_ROLES:
        assert prior.admitted_to_role(result, role)


@pytest.mark.parametrize("unit", [True, False])
def test_one_conflicting_period_never_dropped_even_without_reference_unit(unit):
    est, ref = fixture(unit=unit, values=["-300", "600", "1199"])
    cal = c.calibrate(est, docs(), ref)
    assert cal["state"] == "UNAVAILABLE_CROSS_ENDPOINT_SCALE_CONFLICT"
    assert cal["matched_period_count"] == 3
    assert cal["wire_to_krw_per_share"] is None
    assert snapshot(est, cal)["value"] is None


def test_no_human_display_assumption_from_eps_label():
    est, ref, cal = qualified(unit=False)
    assert ref["unit"] is None
    assert cal["state"] == "UNAVAILABLE_REFERENCE_WIRE_SCALE"
    assert cal["raw_ratio_diagnostic_only"]
    assert snapshot(est, cal)["value"] is None


@pytest.mark.parametrize("values,state", [(["-300", None, "1200"], "QUALIFIED"),
    ([None, None, "1200"], "UNAVAILABLE_CROSS_ENDPOINT_SCALE_GAP")])
def test_minimum_two_non_null_periods(values, state):
    assert qualified(values=values)[2]["state"] == state


@pytest.mark.parametrize("values,state", [(["0", "0", "0"], "UNAVAILABLE_CROSS_ENDPOINT_SCALE_GAP"),
    (["0", "1", "0"], "UNAVAILABLE_CROSS_ENDPOINT_SCALE_CONFLICT")])
def test_zero_base_never_defines_or_hides_scale(values, state):
    raw = estimate()
    raw["output3"][1].update(data1="0", data2="0", data3="0")
    assert qualified(raw=raw, values=values)[2]["state"] == state


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "text", 12])
def test_invalid_numeric_fail_closed(bad):
    with pytest.raises(c.SemanticGap, match="WIRE_VALUE"):
        qualified(values=["-300", bad, "1200"])


@pytest.mark.parametrize("mutate", [
    lambda r, d: r["request"]["params"].update(FID_DIV_CLS_CODE="1"),
    lambda r, d: r["request"]["params"].update(fid_input_iscd="123457"),
    lambda r, d: r["request"].update(tr_id="other"),
    lambda r, d: r.update(raw_sha256="0" * 64),
    lambda r, d: r.update(ended_at="2024-01-01"),
    lambda r, d: r["response_headers"].update(tr_cont="M"),
    lambda r, d: d.update(eps_field="bps"),
])
def test_reference_ownership_boundaries(mutate):
    with pytest.raises(c.SemanticGap):
        fixture(mutate=mutate)


def test_unknown_review_is_not_numeric_plausibility_permission():
    def mutate(r, d):
        d["wire_to_display"]["kind"] = "PRICE_PER_PLAUSIBILITY"
    est, ref = fixture(mutate=mutate)
    assert c.calibrate(est, docs(), ref)["state"] == "UNAVAILABLE_REFERENCE_WIRE_SCALE"


def test_partial_unique_match_is_not_prefix_assumption():
    _, _, cal = qualified()
    raw = estimate("987654")
    raw["output3"] = [raw["output3"][7], raw["output3"][0], raw["output3"][1]]
    est, ref = fixture(code="987654", raw=raw)
    binding = c.partial_binding(est, ref, cal)
    assert binding["state"] == "QUALIFIED"
    assert binding["row_index"] == 2
    assert len(binding["candidate_rows"]) == 3
    result = snapshot(est, cal, code="987654", reference=ref)
    assert result["value"] == "2400"
    assert result["provider_per"] == "UNAVAILABLE_WIRE_SCALE"


@pytest.mark.parametrize("variant", ["none", "multiple", "one_conflict", "one_period"])
def test_partial_requires_unique_all_period_match(variant):
    _, _, cal = qualified()
    raw = estimate("987654")
    raw["output3"] = raw["output3"][:3]
    if variant == "none":
        raw["output3"][1] = deepcopy(raw["output3"][0])
    elif variant == "multiple":
        raw["output3"][2] = deepcopy(raw["output3"][1])
    elif variant == "one_conflict":
        raw["output3"][1]["data3"] = "4799"
    else:
        raw["output3"][1].update(data1=None, data2=None)
    est, ref = fixture(code="987654", raw=raw)
    assert c.partial_binding(est, ref, cal)["state"] == "UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS"


def test_receipt_tamper_and_control_source_change_rejected():
    est, ref, cal = qualified()
    changed = deepcopy(cal)
    changed["wire_to_krw_per_share"] = "1"
    assert snapshot(est, changed)["state"] == "UNAVAILABLE_RECEIPT_BINDING"
    raw = est.payload()
    raw["output3"][1]["data4"] = "12345"
    assert snapshot(ev(raw), cal)["state"] == "UNAVAILABLE_CALIBRATION_SOURCE_CHANGED"
    with pytest.raises(c.SemanticGap, match="SOURCE_HASH"):
        c.calibrate(c.Evidence(b"{}", est.sha256), docs(), ref)


def test_exact_decimal_no_precision_rounding_or_nonterminating_fit():
    assert c.decimal_string(Fraction(-1, 8)) == "-0.125"
    assert c.decimal_string(Fraction(10**40 + 1, 100)) == "100000000000000000000000000000000000000.01"
    with pytest.raises(c.SemanticGap, match="NON_DECIMAL"):
        c.decimal_string(Fraction(1, 3))


def test_stage_b_gate_denied_for_failed_calibration(tmp_path):
    est, _, cal = qualified(unit=False)
    out = snapshot(est, cal)
    path = tmp_path / "qualification.json"
    path.write_text(json.dumps(out))
    with pytest.raises(c.SemanticGap):
        c.verify_stage_b_gate({"owner_sha256": sha256(Path(c.__file__).read_bytes()).hexdigest(),
            "focused_tests": "PASS", "qualification_path": str(path),
            "qualification_sha256": sha256(path.read_bytes()).hexdigest()})


def test_period_mismatch_is_not_comparable():
    est, ref = fixture()
    body = {k: v for k, v in ref.items() if k != "receipt_sha256"}
    body["raw_eps_by_period"] = {k.replace(".09", ".06"): v for k, v in body["raw_eps_by_period"].items()}
    assert c.calibrate(est, docs(), c.sealed(body))["state"] == "UNAVAILABLE_CROSS_ENDPOINT_SCALE_GAP"


def test_stage_b_full_layout_uses_generic_control_and_fiscal_owner():
    _, _, cal = qualified()
    est = ev(estimate("987654"))
    assert snapshot(est, cal, code="987654")["state"] == "QUALIFIED_KIS_FY1_EPS"
    out = c.qualify_eps("987654", "01234567", est, identity("987654"), None, date(2024, 8, 1),
        docs(), (), cal, estimate_transport=ev({"SHT_CD": "987654", "http_status": 200,
        "raw_sha256": est.sha256, "ended_at": "2024-07-01T00:00:00+00:00"}))
    assert out["state"] == "UNAVAILABLE_FISCAL_PERIOD"


def test_absent_estimate_and_missing_transport_are_not_zero():
    est, _, cal = qualified()
    out = c.qualify_eps("123456", "01234567", None, None, None, date(2024, 8, 1), docs(), (), cal)
    assert out["state"] == "UNAVAILABLE_NO_ESTIMATE" and out["value"] is None
    out = c.qualify_eps("123456", "01234567", est, None, None, date(2024, 8, 1), docs(), (), cal)
    assert out["state"] == "UNAVAILABLE_ESTIMATE_TRANSPORT"


@pytest.mark.parametrize("variant", ["wrong_security", "wrong_layout", "changed_source"])
def test_calibration_requires_independently_bound_control(variant):
    est, ref = fixture()
    raw = est.payload()
    if variant == "wrong_security":
        raw["output1"]["sht_cd"] = "A987654"
    elif variant == "wrong_layout":
        raw["output3"][0].pop("data2")
    else:
        raw["output3"][1]["data4"] = "99"
    with pytest.raises(c.SemanticGap, match="CALIBRATION_CONTROL"):
        c.calibrate(ev(raw), docs(), ref)


def test_qualified_basis_cannot_be_invented_for_optional_fper():
    from app.services.security_valuation_basis import SecurityValuationBasisReceipt
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SecurityValuationBasisReceipt(status="QUALIFIED")
