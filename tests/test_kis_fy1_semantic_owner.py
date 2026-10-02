from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import pytest

from scripts import kis_fy1_semantic_owner as k


def evidence(value):
    raw = json.dumps(value, ensure_ascii=False).encode()
    return k.Evidence(raw, sha256(raw).hexdigest())


def source(code="123456"):
    return {"rt_cd": "0", "output1": {"sht_cd": "A" + code},
            "output3": [{f"data{i}": str(100 * row + i) for i in range(1, 6)} for row in range(8)],
            "output4": [{"dt": p} for p in ("2021.09", "2022.09", "2023.09", "2024.09E", "2025.09E")]}


def identity(code="123456"):
    return {"rt_cd": "0", "output": {"pdno": "00000A" + code, "shtn_pdno": code,
            "std_pdno": "KR7123456007", "prdt_type_cd": "300", "prdt_name": "가상보통주",
            "prdt_clsf_name": "주권", "ivst_prdt_type_cd_name": "주식"}}


def filing(year=2023, month=9):
    return {"stock_code": "123456", "corp_code": "01234567", "corp_cls": "Y",
            "rcept_no": f"{year}1215000100", "rcept_dt": f"{year}1215",
            "report_nm": f"사업보고서 ({year}.{month:02d})"}


def inventory(*rows):
    return {"status": "000", "page_no": 1, "total_page": 1,
            "total_count": len(rows), "list": list(rows)}


def documentation():
    return {"endpoint": k.ENDPOINT, "explicit_e_definition": False,
            "conflicting_marker_definition": False, "official_estimate_endpoint": True,
            "analyst_estimates_description": True, "output4_data1_to_5_link": True,
            "output3_layout": list(k.LAYOUT), "wire_scales": {}}


def scale(metric):
    return {"unit": "KRW_PER_SHARE" if metric == "EPS" else "MULTIPLE",
            "multiplier": "0.01" if metric == "EPS" else "0.1",
            "kind": "OFFICIAL_EXPLICIT_RAW_TO_DISPLAY", "source_sha256": "c" * 64,
            "definition": "Synthetic explicit wire conversion fixture, NOT a live KIS scale"}


def run(*, raw=None, ident=None, fiscal=None, doc=None, controls=None):
    return k.qualify("123456", "01234567", evidence(source() if raw is None else raw),
                     evidence(identity() if ident is None else ident),
                     evidence(inventory(filing()) if fiscal is None else fiscal), date(2024, 8, 1),
                     k.Documentation(evidence(documentation() if doc is None else doc)),
                     controls if controls is not None else [evidence(source()), evidence(source("987654"))])


def test_source_owned_identity_fiscal_and_endpoint_marker():
    out = run()
    assert out["security"]["state"] == out["fiscal"]["state"] == out["forecast"]["state"] == "QUALIFIED"
    assert out["forecast"]["fy1"] == "2024.09E"
    assert out["forecast"]["fy2"] == "2025.09E"
    assert out["forecast"]["is_inference_not_official_quote"]
    assert out["eps"]["state"] == "UNAVAILABLE_WIRE_SCALE"


@pytest.mark.parametrize("field,value", [("pdno", "00000A123457"), ("shtn_pdno", "123457"),
    ("std_pdno", ""), ("prdt_type_cd", "512"), ("prdt_clsf_name", ""), ("prdt_name", "")])
def test_wrong_sibling_product_or_name_only_identity_rejected(field, value):
    value_row = identity()
    value_row["output"][field] = value
    assert run(ident=value_row)["eps"]["state"] == "UNAVAILABLE_SECURITY_IDENTITY"


def test_wrong_estimate_security_rejected_even_same_name():
    assert run(raw=source("123457"))["eps"]["state"] == "UNAVAILABLE_SECURITY_IDENTITY"


@pytest.mark.parametrize("change", ["interim", "month", "stale", "future", "issuer", "partial"])
def test_fiscal_boundaries(change):
    item = filing()
    inv = inventory(item)
    if change == "interim":
        item["report_nm"] = "반기보고서 (2023.09)"
    elif change == "month":
        item["report_nm"] = "사업보고서 (2023.06)"
    elif change == "stale":
        inv = inventory(filing(2022))
    elif change == "future":
        item["rcept_dt"] = "20250101"
    elif change == "issuer":
        item["corp_code"] = "76543210"
    else:
        inv["total_page"] = 2
    assert run(fiscal=inv)["eps"]["state"].startswith("UNAVAILABLE_FISCAL")


def test_latest_annual_selected_not_first_or_interim():
    out = run(fiscal=inventory(filing(2022), filing()))
    assert out["fiscal"]["fiscal_year"] == 2023


def test_explicit_forecast_marker_without_control_inference():
    doc = documentation()
    doc["explicit_e_definition"] = True
    assert run(doc=doc, controls=[])["forecast"]["method"] == "OFFICIAL_DOCUMENTED_E"


@pytest.mark.parametrize("change", ["conflict", "no_link", "no_analyst", "one_control", "duplicate_control", "other_endpoint"])
def test_controlled_marker_requires_every_condition(change):
    doc = documentation()
    controls = [evidence(source()), evidence(source("987654"))]
    if change == "conflict":
        doc["conflicting_marker_definition"] = True
    elif change == "no_link":
        doc["output4_data1_to_5_link"] = False
    elif change == "no_analyst":
        doc["analyst_estimates_description"] = False
    elif change == "one_control":
        controls.pop()
    elif change == "duplicate_control":
        controls = [controls[0], controls[0]]
    else:
        doc["endpoint"] = "/unrelated"
    assert run(doc=doc, controls=controls)["eps"]["state"].startswith("UNAVAILABLE_")


@pytest.mark.parametrize("labels", [
    ["2021.09", "2022.09", "2023.09", "2024.09", "2025.09"],
    ["2021.09", "2022.09", "2023.09", "2024.09F", "2025.09E"],
    ["2021.09", "2022.09", "2023.09", "2025.09E", "2026.09E"],
])
def test_unlabelled_future_conflicting_marker_and_nonannual_stride(labels):
    raw = source()
    raw["output4"] = [{"dt": x} for x in labels]
    assert run(raw=raw)["eps"]["state"] == "UNAVAILABLE_FORECAST_MARKER"


@pytest.mark.parametrize("length", [0, 3, 7, 9])
def test_partial_layout_never_prefix_assumed(length):
    raw = source()
    raw["output3"] = (raw["output3"] + raw["output3"])[:length]
    assert run(raw=raw)["eps"]["state"] == "UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS"


def test_exact_full_layout_scale_independence_and_authority():
    doc = documentation()
    doc["wire_scales"]["EPS"] = scale("EPS")
    out = run(doc=doc)
    assert out["eps"]["value"] == "1.04"
    assert out["provider_per"]["state"] == "UNAVAILABLE_WIRE_SCALE"
    for role in k.ALLOWED_ROLES:
        assert k.admitted_to_role(out["eps"], role)
    for role in k.PROHIBITED_ROLES:
        assert not k.admitted_to_role(out["eps"], role)
    assert out["derived_fper"]["value"] is None
    doc["wire_scales"] = {"PER": scale("PER")}
    out = run(doc=doc)
    assert out["provider_per"]["value"] == "30.4"
    assert out["eps"]["state"] == "UNAVAILABLE_WIRE_SCALE"


@pytest.mark.parametrize("bad", [{"unit": "KRW"}, {"kind": "PRICE_DIVIDED_BY_EPS"},
    {"source_sha256": ""}, {"definition": ""}, {"multiplier": "NaN"}, {"multiplier": "0"}])
def test_ambiguous_or_reverse_engineered_scale_not_qualified(bad):
    doc = documentation()
    doc["wire_scales"]["EPS"] = {**scale("EPS"), **bad}
    assert not run(doc=doc)["eps"]["state"].startswith("QUALIFIED")


def test_reordered_documented_map_rejected():
    doc = documentation()
    doc["output3_layout"][1], doc["output3_layout"][3] = doc["output3_layout"][3], doc["output3_layout"][1]
    assert run(doc=doc)["eps"]["state"] == "UNAVAILABLE_OUTPUT3_LAYOUT"


def test_reordered_unlabelled_raw_breaks_sealed_hash_not_numeric_heuristic():
    original = evidence(source())
    modified = deepcopy(source())
    modified["output3"][1], modified["output3"][3] = modified["output3"][3], modified["output3"][1]
    with pytest.raises(k.SemanticGap, match="SOURCE_HASH"):
        k.Evidence(evidence(modified).raw, original.sha256).payload()


def test_missing_column_or_injected_row_identity_rejected():
    raw = source()
    raw["output3"][1].pop("data3")
    assert run(raw=raw)["eps"]["state"] == "UNAVAILABLE_OUTPUT3_LAYOUT"


def test_unqueried_estimate_not_stock_source_failure():
    out = k.qualify("123456", "01234567", None, None, None, date(2024, 8, 1), None)
    assert not out["source_failure"]
    assert out["eps"]["state"] == "UNAVAILABLE_NOT_QUERIED_STAGE_A_GATE"
