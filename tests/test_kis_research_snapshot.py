"""Synthetic contracts only. No fixture grants a live KIS transform/rounding rule."""

from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import pytest

from scripts import kis_research_snapshot as r
from scripts.kis_fy1_semantic_owner import Documentation, Evidence, ENDPOINT, LAYOUT, SemanticGap


def ev(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
    return Evidence(raw, sha256(raw).hexdigest())


def fixture(code="123456"):
    columns = [f"data{i}" for i in range(1, 6)]
    values = ["-1000", "2000", "4000", "6000", "9000"]
    rows = [dict(zip(columns, [str(i + j * 3) for i in range(1, 6)])) for j in range(8)]
    rows[1] = dict(zip(columns, values))
    rows[3] = dict(zip(columns, ["80", "90", "100", "110", "120"]))
    periods = ["2021.09", "2022.09", "2023.09", "2024.09E", "2025.09E"]
    estimate = ev({"rt_cd": "0", "output1": {"sht_cd": "A" + code, "name1": "Synthetic Analyst",
        "estdate": "20240701", "rcmd_name": "Synthetic Recommendation"}, "output3": rows,
        "output4": [{"dt": p} for p in periods]})
    identity = ev({"rt_cd": "0", "output": {"pdno": "00000A" + code, "shtn_pdno": code,
        "std_pdno": "KR7123456007", "prdt_type_cd": "300", "prdt_name": "Synthetic Common",
        "prdt_clsf_name": "주권", "ivst_prdt_type_cd_name": "주식"}})
    page, pdf = ev(b"Synthetic page; no actual official report"), ev(b"Synthetic PDF table")
    metadata = {"security_code": code, "analyst": "Synthetic Analyst", "date": "20240701",
                "recommendation": "Synthetic Recommendation", "title": "Synthetic", "report_type": "Note", "report_id": "fixture"}
    review = {"kind": "REVIEWED_OFFICIAL_RESEARCH_EXTRACTION", "page_sha256": page.sha256,
        "attachment_sha256": pdf.sha256, "page_url": "https://truefriend.com/synthetic-page",
        "attachment_url": "https://truefriend.com/synthetic.pdf", "attachment_linked_by_page": True,
        "all_metric_periods_preserved": True, "method": "PDF_TEXT",
        "page_metadata": metadata, "document_metadata": deepcopy(metadata), "tables": {
            "EPS": {"unit": "KRW_PER_SHARE", "page": 1, "section": "Financial table",
                "rows": [{"period": p, "value": v} for p, v in zip(periods, ["-100", "200", "400", "600", "900"])]},
            "PER": {"unit": "MULTIPLE", "page": 1, "section": "Financial table",
                "rows": [{"period": p, "value": v} for p, v in zip(periods, ["8", "9", "10", "11", "12"])]}}}
    docs = Documentation(ev({"endpoint": ENDPOINT, "output3_layout": list(LAYOUT)}))
    forecast = {"state": "QUALIFIED", "period_labels": periods, "fy1": periods[3], "fy1_column": 4}
    return {"code": code, "estimate": estimate, "identity": identity, "page": page, "attachment": pdf,
            "review": review, "docs": docs, "forecast": forecast}


def binding(f):
    return r.bind_research(f["code"], f["estimate"], f["identity"], f["page"], f["attachment"], ev(f["review"]))


def metric(f, kind="EPS", calibration=None):
    owner = binding(f)
    cal = calibration or r.calibrate(kind, f["estimate"], f["docs"], owner)
    return r.snapshot(kind, f["estimate"], owner["security"], f["forecast"], f["docs"], cal)


@pytest.mark.parametrize("kind,value", [("EPS", "600"), ("PER", "11")])
def test_independent_same_snapshot_calibration(kind, value):
    f = fixture()
    cal = r.calibrate(kind, f["estimate"], f["docs"], binding(f))
    assert cal["state"] == "QUALIFIED" and cal["factor"] == "0.1"
    assert len(cal["pairs"]) == 5 and not cal["reference_ratio_used"]
    result = metric(f, kind)
    assert result["value"] == value and result["estdate"] == "20240701"
    assert not result["overall_direction_use"] and not result["current_session_metric"]
    assert "NOT_CONSENSUS" in result["source_kind"]
    assert not set(result["allowed_roles"]) & set(result["prohibited_roles"])
    assert r.stage_b_admitted([result])


@pytest.mark.parametrize("key,value", [("security_code", "987654"), ("analyst", "other"),
    ("date", "20240702"), ("title", "Different"), ("report_type", "Other"), ("recommendation", "Other")])
def test_same_security_analyst_date_type_identity_required(key, value):
    f = fixture()
    f["review"]["document_metadata"][key] = value
    with pytest.raises(SemanticGap, match="SNAPSHOT_BINDING"):
        binding(f)


@pytest.mark.parametrize("change", [
    lambda f: f.update(attachment=None), lambda f: f.update(page=None),
    lambda f: f.update(attachment=Evidence(b"bad", "0" * 64)),
    lambda f: f["review"].update(page_url="https://third-party.example/report"),
    lambda f: f["review"].update(attachment_url="https://truefriend.com.evil.example/r.pdf"),
    lambda f: f["review"].update(attachment_url="https://secret@truefriend.com/r.pdf"),
    lambda f: f["review"].update(attachment_linked_by_page=False),
    lambda f: f["review"].update(all_metric_periods_preserved=False),
    lambda f: f["review"].update(attachment_sha256="0" * 64),
    lambda f: f["review"]["tables"]["EPS"].update(unit="KRW"),
    lambda f: f["review"]["tables"]["EPS"].update(page=0),
    lambda f: f["review"]["tables"]["EPS"]["rows"].append({"period": "2021.09", "value": "1"}),
])
def test_artifact_and_extraction_fail_closed(change):
    f = fixture()
    change(f)
    with pytest.raises(SemanticGap):
        binding(f)


@pytest.mark.parametrize("kind", ["EPS", "PER"])
def test_one_disagreement_retained_other_metric_independent(kind):
    f = fixture()
    f["review"]["tables"][kind]["rows"][2]["value"] = "401"
    cal = r.calibrate(kind, f["estimate"], f["docs"], binding(f))
    assert cal["state"] == "UNAVAILABLE_RESEARCH_SNAPSHOT_MISMATCH"
    assert len(cal["pairs"]) == 5 and cal["periods_dropped_for_disagreement"] == 0
    other = "PER" if kind == "EPS" else "EPS"
    assert metric(f, other)["state"].startswith("QUALIFIED_")
    with pytest.raises(SemanticGap):
        metric(f, kind, calibration=cal)


@pytest.mark.parametrize("n,state", [(1, "UNAVAILABLE_RESEARCH_WIRE_SCALE"), (2, "QUALIFIED")])
def test_two_forecast_columns_sufficient_but_one_is_not(n, state):
    f = fixture()
    f["review"]["tables"]["EPS"]["rows"] = f["review"]["tables"]["EPS"]["rows"][-n:]
    assert r.calibrate("EPS", f["estimate"], f["docs"], binding(f))["state"] == state


def partial_fixture():
    f = fixture()
    payload = f["estimate"].payload()
    payload["output3"] = [payload["output3"][0], payload["output3"][1],
        dict(zip([f"data{i}" for i in range(1, 6)], ["100", "-3000", "1000", "500", "500"]))]
    f["estimate"] = ev(payload)
    rule = {"rounding": "HALF_AWAY_FROM_ZERO", "wire_to_percentage_points": "0.1"}
    doc = {"endpoint": ENDPOINT, "output3_layout": list(LAYOUT), "growth_rounding": rule}
    f["docs"] = Documentation(ev(doc))
    policy = ev({"kind": "OFFICIAL_DOCUMENTED_GROWTH_ROUNDING",
                 "documentation_sha256": f["docs"].evidence.sha256, "rule": rule})
    return f, policy


def test_partial_equation_all_ordered_pairs_negative_denominator_unique():
    f, policy = partial_fixture()
    result = r.partial_eps_binding(f["estimate"], f["docs"], policy)
    assert result["state"] == "QUALIFIED" and result["matching_pairs"] == [[1, 2]]
    assert len(result["candidate_pairs"]) == 6
    cal = r.calibrate("EPS", f["estimate"], f["docs"], binding(f), result)
    assert cal["state"] == "QUALIFIED"
    with pytest.raises(SemanticGap, match="NO_PER_ROW"):
        r.calibrate("PER", f["estimate"], f["docs"], binding(f), result)


@pytest.mark.parametrize("variant", ["absolute_denominator", "duplicate_pair", "mismatch", "missing", "no_rule", "invented_rule"])
def test_partial_never_prefix_or_approximate_inference(variant):
    f, policy = partial_fixture()
    payload = f["estimate"].payload()
    if variant == "absolute_denominator":
        payload["output3"][2]["data2"] = "3000"
    elif variant == "duplicate_pair":
        payload["output3"][0] = deepcopy(payload["output3"][1])
    elif variant == "mismatch":
        payload["output3"][2]["data5"] = "501"
    elif variant == "missing":
        payload["output3"][1]["data5"] = None
    elif variant == "no_rule":
        policy = None
    else:
        bad = policy.payload()
        bad["rule"]["rounding"] = "TRUNCATE_TOWARD_ZERO"
        policy = ev(bad)
    result = r.partial_eps_binding(ev(payload), f["docs"], policy)
    assert result["state"].startswith("UNAVAILABLE_") and result["row_index"] is None


def test_stage_b_global_transform_and_changed_fiscal_or_raw_shape():
    control, subject = fixture(), fixture("987654")
    cal = r.calibrate("EPS", control["estimate"], control["docs"], binding(control))
    assert metric(subject, calibration=cal)["value"] == "600"
    subject["forecast"]["fy1"] = "2023.09"
    with pytest.raises(SemanticGap, match="FISCAL_PERIOD"):
        metric(subject, calibration=cal)
    partial, _ = partial_fixture()
    partial["docs"] = control["docs"]
    with pytest.raises(SemanticGap, match="PARTIAL_ROW"):
        metric(partial, calibration=cal)


@pytest.mark.parametrize("kind", ["EPS", "PER"])
def test_receipt_mutation_is_not_a_per_subject_conversion(kind):
    f = fixture()
    cal = r.calibrate(kind, f["estimate"], f["docs"], binding(f))
    cal["factor"] = "1"
    with pytest.raises(SemanticGap, match="RECEIPT_BINDING"):
        metric(f, kind, cal)


def test_freshness_preserves_estdate_without_latest_or_arbitrary_staleness():
    result = r.freshness(fixture()["estimate"], "2024-07-15T00:00:00+00:00", date(2024, 8, 1))
    assert result["age_days"] == 31 and result["estdate"] == "20240701"
    assert not result["latest_available_verified"] and not result["new_query_in_this_task"]
    assert result["arbitrary_stale_threshold"] is None


@pytest.mark.parametrize("timestamp", [None, "2024-07-01", "2024-06-30T00:00:00Z", "2024-09-01T00:00:00Z"])
def test_invalid_or_future_retrieval_not_current(timestamp):
    assert r.freshness(fixture()["estimate"], timestamp, date(2024, 8, 1))["state"].startswith("UNAVAILABLE_")


def test_current_fper_requires_real_action_window_not_intraday_or_report_price():
    f = fixture()
    assert r.current_fper_denial()["state"] == "UNAVAILABLE_EPS"
    assert r.current_fper_denial(metric(f, "PER"))["state"] == "UNAVAILABLE_EPS"
    assert r.current_fper_denial(metric(f))["state"] == "UNAVAILABLE_CORPORATE_ACTION_BASIS"
    # There is deliberately no price argument while the action-window owner is absent.
    with pytest.raises(TypeError):
        r.current_fper_denial(metric(f), price="1000")
    value = metric(f)
    value["value"] = "-1"
    value = r.sealed({k: v for k, v in value.items() if k != "receipt_sha256"})
    assert r.current_fper_denial(value)["state"] == "NOT_MEANINGFUL"


def test_stage_b_denied_without_any_independently_qualified_metric():
    assert not r.stage_b_admitted([])
    assert not r.stage_b_admitted([{"state": "QUALIFIED_KIS_RESEARCH_FY1_EPS"}])
    result = metric(fixture())
    result["value"] = "999"
    assert not r.stage_b_admitted([result])
