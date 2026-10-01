"""Synthetic source-family tests; no fixture asserts live source authority."""

from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import httpx
import pytest

from scripts import kis_output3_protocol_owner as p
from scripts import kis_protocol_stage_b_probe as transport
from scripts.kis_estimate_capability_probe import Credentials, ProbeStop, STAGE_B
from scripts.kis_fy1_semantic_owner import Documentation, ENDPOINT, Evidence, LAYOUT, SemanticGap, fiscal_owner


def ev(value):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return Evidence(raw, sha256(raw).hexdigest())


def fixture():
    codes = ("123456", "654321")
    columns = [f"data{i}" for i in range(1, 6)]
    rows = [dict(zip(columns, [str(i + j * 3) for i in range(1, 6)])) for j in range(8)]
    rows[1] = dict(zip(columns, ["-1000", "2000", "4000", "6000", "9000"]))
    rows[3] = dict(zip(columns, ["80", "90", "100", "110", "120"]))
    growth = dict(zip(columns, ["999999", "-3000", "1000", "500", "500"]))
    sources, identities, inventories = {}, {}, {}
    for code in codes:
        sources[code] = ev({"rt_cd": "0", "output1": {"sht_cd": "A" + code, "estdate": "20240701"},
            "output3": rows if code == codes[0] else [rows[0], rows[1], growth],
            "output4": [{"dt": v} for v in ["2021.09", "2022.09", "2023.09", "2024.09E", "2025.09E"]]})
        identities[code] = ev({"rt_cd": "0", "output": {"pdno": "00000A" + code, "shtn_pdno": code,
            "std_pdno": "KR7" + code + "007", "prdt_type_cd": "300", "prdt_name": "Synthetic",
            "prdt_clsf_name": "주권", "ivst_prdt_type_cd_name": "주식"}})
        inventories[code] = ev({"status": "000", "page_no": 1, "total_page": 1, "total_count": 1,
            "list": [{"stock_code": code, "corp_code": "11111111", "rcept_dt": "2023-12-01",
                      "rcept_no": "20231201000001", "report_nm": "사업보고서 (2023.09)"}]})
    docs = Documentation(ev({"endpoint": ENDPOINT, "output3_layout": list(LAYOUT),
        "conflicting_marker_definition": False, "official_estimate_endpoint": True,
        "analyst_estimates_description": True, "output4_data1_to_5_link": True}))
    pdf = ev(b"%PDF-synthetic fixture, not an official PDF")
    controls = [{"security_code": code, "metric": metric, "period": period,
        "period_kind": "ACTUAL", "value": value, "raw_token": value, "bbox": [1, 2, 3, 4]}
        for code, metric, values in [(codes[0], "EPS", ["-100", "200"]),
            (codes[0], "PER", ["8", "9"]), (codes[1], "EPS", ["-100", "200"])]
        for period, value in zip(["2021.09", "2022.09"], values)]
    review = {"kind": "VISUAL_VERIFIED_OFFICIAL_HISTORICAL_TABLE", "artifact_sha256": pdf.sha256,
        "url": "https://file.truefriend.com/Storage/research/synthetic.pdf", "document_date": "2023-12-02",
        "title": "Synthetic Historical Table", "analyst": "Synthetic", "page": 5,
        "section": "Coverage", "units": p.UNITS, "all_selected_historical_controls_preserved": True,
        "controls": controls}
    fiscals = {c: fiscal_owner(c, "11111111", inventories[c], date(2024, 7, 2)) for c in codes}
    return {"codes": codes, "sources": sources, "identities": identities, "inventories": inventories,
            "docs": docs, "pdf": pdf, "review": review, "fiscals": fiscals}


def protocol(f):
    return p.calibrate(f["pdf"], ev(f["review"]), f["docs"], f["sources"], f["identities"], f["fiscals"])


def qualify(f, code, cal=None, stage_a=True):
    return p.qualify(code, f["sources"][code], f["identities"][code], f["inventories"][code], "11111111",
        date(2024, 7, 2), f["docs"], list(f["sources"].values()), cal or protocol(f),
        "2024-07-01T16:00:00+00:00", date(2024, 8, 1), stage_a=stage_a)


def test_protocol_historical_controls_not_current_report_and_both_stage_a():
    f = fixture()
    cal = protocol(f)
    assert cal["factors"] == {"EPS": "0.1", "PER": "0.1"} and len(cal["pairs"]) == 6
    assert not cal["price_used"] and not cal["financial_ratio_used"]
    rows = [qualify(f, c) for c in f["codes"]]
    assert [r["eps"]["value"] for r in rows] == ["600", "600"]
    assert rows[0]["provider_per"]["value"] == "11"
    assert rows[1]["provider_per"]["state"] == "UNAVAILABLE_NO_PER_ROW"
    assert rows[1]["eps"]["partial_binding"]["matching_pairs"] == [[1, 2]]
    assert rows[1]["eps"]["age_days"] == 31
    assert not rows[0]["eps"]["overall_direction_use"]
    assert set(rows[0]["eps"]["allowed_roles"]).isdisjoint(rows[0]["eps"]["prohibited_roles"])
    assert all(r["current_price_derived_fper"]["value"] is None for r in rows)
    p.verify_gate(p.stage_b_gate(rows, cal))


@pytest.mark.parametrize("change", [
    lambda f: f["review"].update(url="https://mirror.example/report.pdf"),
    lambda f: f["review"].update(url="https://file.truefriend.com.evil/Storage/research/a.pdf"),
    lambda f: f["review"].update(url="https://secret@file.truefriend.com/Storage/research/a.pdf"),
    lambda f: f["review"].update(artifact_sha256="0" * 64),
    lambda f: f["review"].update(document_date="invalid"),
    lambda f: f["review"].update(all_selected_historical_controls_preserved=False),
    lambda f: f["review"]["controls"][0].update(value="100"),
    lambda f: f["review"]["controls"][0].update(period_kind="FORECAST"),
    lambda f: f["review"]["controls"].append(deepcopy(f["review"]["controls"][0])),
    lambda f: f["review"].update(controls=f["review"]["controls"][:4]),
    lambda f: f.update(pdf=Evidence(b"bad", "0" * 64)),
])
def test_artifact_and_control_fail_closed(change):
    f = fixture()
    change(f)
    with pytest.raises(SemanticGap):
        protocol(f)


@pytest.mark.parametrize("mutation", ["duplicate", "wrong_sign", "wrong_growth", "missing_growth", "nonconsecutive"])
def test_partial_competing_mismatch_missing_and_signed_denominator(mutation):
    f = fixture()
    cal = protocol(f)
    c = f["codes"][1]
    raw = f["sources"][c].payload()
    if mutation == "duplicate":
        raw["output3"][0] = deepcopy(raw["output3"][1])
    elif mutation == "wrong_sign":
        raw["output3"][2]["data2"] = "3000"
    elif mutation == "wrong_growth":
        raw["output3"][2]["data5"] = "501"
    elif mutation == "missing_growth":
        raw["output3"][2]["data3"] = None
    else:
        raw["output3"][1]["data3"] = None
        raw["output3"][2]["data5"] = "500"
    bound = p.partial_binding(ev(raw), f["docs"], cal)
    assert bound["state"] == "UNAVAILABLE_PARTIAL_ROW_SEMANTICS"
    assert bound["row_index"] is None


def test_stage_a_never_uses_only_growth_after_absolute_source_changed():
    f = fixture()
    cal = protocol(f)
    raw = f["sources"][f["codes"][1]].payload()
    raw["output1"]["estdate"] = "20240702"
    with pytest.raises(SemanticGap, match="ABSOLUTE_EPS_BINDING"):
        p.partial_binding(ev(raw), f["docs"], cal, stage_a=True)


def test_stage_b_row_permutation_uses_unique_pair_not_prefix():
    f = fixture()
    cal = protocol(f)
    c = f["codes"][1]
    raw = f["sources"][c].payload()
    raw["output3"] = list(reversed(raw["output3"]))
    f["sources"][c] = ev(raw)
    result = qualify(f, c, cal, stage_a=False)
    assert result["eps"]["value"] == "600"
    assert result["eps"]["partial_binding"]["matching_pairs"] == [[1, 0]]
    assert result["provider_per"]["value"] is None


@pytest.mark.parametrize("change,expected", [
    (lambda raw: raw["output1"].update(sht_cd="A999999"), "SECURITY_IDENTITY"),
    (lambda raw: raw["output1"].update(estdate="20250101"), "ESTDATE"),
    (lambda raw: raw["output4"][3].update(dt="2024.12E"), "FORECAST_MARKER"),
    (lambda raw: raw.update(output3=[]), "NO_KIS_RESEARCH_ESTIMATE"),
    (lambda raw: raw.update(rt_cd="1"), "PROVIDER_ESTIMATE"),
])
def test_subject_failures_typed_without_stock_source_failure(change, expected):
    f = fixture()
    cal = protocol(f)
    c = f["codes"][0]
    raw = f["sources"][c].payload()
    change(raw)
    f["sources"][c] = ev(raw)
    result = qualify(f, c, cal)
    assert expected in result["eps"]["state"] and not result["source_failure"]


def test_negative_and_zero_eps_keep_snapshot_but_forbid_current_per():
    for value in ("-100", "0"):
        f = fixture()
        cal = protocol(f)
        c = f["codes"][0]
        raw = f["sources"][c].payload()
        raw["output3"][1]["data4"] = value
        f["sources"][c] = ev(raw)
        result = qualify(f, c, cal)
        assert result["eps"]["state"] == p.STATES["EPS"]
        assert result["current_price_derived_fper"]["state"] == "UNAVAILABLE_NONPOSITIVE_EPS"


@pytest.mark.parametrize("variant", ["none", "MERGER", "SPLIT", "REVERSE_SPLIT", "BONUS", "PAID_IN", "missing", "short", "other"])
def test_action_window_interface_does_not_grant_metric_permission(variant):
    receipt = {"security_code": "123456", "from": "2024-07-01", "through": "2024-08-01",
        "source_kind": "KIS_OFFICIAL", "families": ["MERGER", "SPLIT", "REVERSE_SPLIT", "BONUS", "PAID_IN"],
        "complete": True, "events": []}
    if variant in receipt["families"]:
        receipt["events"] = [{"type": variant}]
    elif variant == "missing":
        receipt["families"].pop()
    elif variant == "short":
        receipt["from"] = "2024-07-02"
    elif variant == "other":
        receipt["security_code"] = "654321"
    result = p.action_window_guard(receipt, security_code="123456", estdate="2024-07-01", price_date="2024-08-01")
    assert (result["state"] == "ACTION_WINDOW_CLEAR") == (variant == "none")
    assert result["metric_permission"] is False


def make_probe(tmp_path, monkeypatch, handler):
    f = fixture()
    gate = p.stage_b_gate([qualify(f, c) for c in f["codes"]], protocol(f))
    probe = transport.StageBProbe(tmp_path, Credentials("synthetic-key", "synthetic-secret"),
        httpx.Client(transport=httpx.MockTransport(handler)), gate=gate)
    monkeypatch.setattr(probe, "disk_guard", lambda: None)
    monkeypatch.setattr(transport.time, "sleep", lambda _: None)
    probe.token = "synthetic-token"
    return probe


def test_probe_exact_scope_once_and_pacing(tmp_path, monkeypatch):
    requests, sleeps = [], []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"rt_cd": "0", "output3": []})
    probe = make_probe(tmp_path, monkeypatch, handler)
    monkeypatch.setattr(transport.time, "sleep", sleeps.append)
    for c in STAGE_B:
        probe.fetch(c, "estimate")
        probe.fetch(c, "identity")
    assert len(requests) == 12 and all(1 <= s <= 1.1 for s in sleeps)
    assert probe.counters()["estimate_perform"] == 6 and probe.counters()["search_info"] == 6
    for code, kind in [(STAGE_B[0], "estimate"), ("005930", "estimate"), (STAGE_B[0], "actions")]:
        with pytest.raises(ProbeStop, match="SCOPE_GAP"):
            probe.fetch(code, kind)


@pytest.mark.parametrize("response,state", [(httpx.Response(200, json={"rt_cd": "1", "msg_cd": "EGW00201"}), "RATE_LIMIT"),
    (httpx.Response(302), "TRANSPORT_FAILURE"),
    (httpx.Response(200, json={"rt_cd": "0"}, headers={"tr_cont": "M"}), "CONTINUATION")])
def test_probe_no_retry_on_stop(tmp_path, monkeypatch, response, state):
    probe = make_probe(tmp_path, monkeypatch, lambda _: response)
    with pytest.raises(ProbeStop, match=state):
        probe.fetch(STAGE_B[0], "estimate")
    assert probe.data_count == 1 and probe.counters()["retries"] == 0


def test_probe_secrets_never_persisted(tmp_path, monkeypatch):
    probe = make_probe(tmp_path, monkeypatch, lambda _: httpx.Response(200, json={"access_token": "unexpected"}))
    with pytest.raises(ProbeStop, match="SECRET_EXPOSURE"):
        probe.fetch(STAGE_B[0], "estimate")
    assert not list(tmp_path.rglob("*.body"))


def test_mutated_scale_and_stage_b_gate_rejected():
    f = fixture()
    cal = protocol(f)
    cal["factors"]["EPS"] = "1"
    with pytest.raises(SemanticGap, match="RECEIPT_BINDING"):
        p.stage_b_gate([qualify(f, f["codes"][0])], cal)
    gate = p.stage_b_gate([], protocol(f))
    with pytest.raises(SemanticGap, match="STAGE_A_GATE"):
        p.verify_gate(gate)
