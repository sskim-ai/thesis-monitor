from copy import deepcopy
from datetime import date
import json

import pytest

from app.services import kiwoom_completed_close_owner as owner
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from tests.rev10_cohort_fixtures import plan_and_securities


def source_fixture(monkeypatch):
    plan, securities = plan_and_securities()
    read = next(r for r in plan.reads if r.subject == "CORZ" and r.role == "adjusted_daily")
    security = next(s for s in securities["us"] if s["ticker"] == "CORZ")
    request = dict(ticker="CORZ", canonical_security_id=read.canonical_security_id, currency="USD",
        api_id="usa20590", method="POST", path="/api/us/mrkcond", generation_id="synthetic-supplement",
        started_at=plan.frozen_at.isoformat(),
        body=dict(stk_cd="CORZ", stex_tp=read.exchange, base_dt=read.latest_completed_session.replace("-", "")))
    row = dict(dt=request["body"]["base_dt"], cur_prc="105.0000", open_pric="100", high_pric="110", low_pric="90")
    artifacts = {"request": encoded(request), "response": encoded(dict(return_code=0, result_list=[row])),
        "documentation": b"FICTIONAL official field-contract fixture"}
    monkeypatch.setattr(owner, "OFFICIAL_SPEC_SHA256", sha256_bytes(artifacts["documentation"]))
    source = {}
    def reseal():
        artifacts["capture"] = encoded(dict(http_status=200, response_received=True,
            raw_sha256=sha256_bytes(artifacts["response"]), raw_bytes=len(artifacts["response"]),
            request_sha256=sha256_bytes(artifacts["request"])))
        source.update({k: dict(path=k, sha256=sha256_bytes(v)) for k,v in artifacts.items()})
    reseal()
    return dict(source=source, plan=plan, read=read, security=security,
        artifact_reader=lambda path, sha: artifacts[path]), artifacts, reseal


def test_valid_raw_completed_close_has_separate_lineage_and_no_technical_permission(monkeypatch):
    inputs, artifacts, _ = source_fixture(monkeypatch)
    before = deepcopy(artifacts)
    price = owner.project(**inputs)
    assert price.current_price == 105
    assert price.price_role == "COMPLETED_REGULAR_SESSION_CLOSE"
    assert price.adjustment_basis == "regular_close"
    assert price.generation_id == inputs["plan"].run_id
    assert price.supplement_generation_id == "synthetic-supplement"
    assert not price.technical_compatibility["technical_target_injection_allowed"]
    assert price.technical_compatibility["raw_price_display_allowed"]
    assert artifacts == before


@pytest.mark.parametrize("kind", ["wrong_date", "missing", "duplicate", "conflict", "close_range",
    "open_range", "zero", "numeric_negative", "nan", "infinity", "overflow", "exchange", "security",
    "stale_base", "future_base", "currency", "api", "calendar", "documentation", "http", "api_failure"])
def test_rejects_invalid_price_source(monkeypatch, kind):
    inputs, artifacts, reseal = source_fixture(monkeypatch)
    request, response = json.loads(artifacts["request"]), json.loads(artifacts["response"])
    row = response["result_list"][0]
    if kind == "wrong_date":
        row["dt"] = "20260921"
    elif kind == "missing":
        response["result_list"] = []
    elif kind in {"duplicate", "conflict"}:
        response["result_list"].append(dict(row, cur_prc="101" if kind == "conflict" else row["cur_prc"]))
    elif kind in {"close_range", "zero", "numeric_negative", "nan", "infinity", "overflow"}:
        row["cur_prc"] = dict(close_range="999", zero="0", numeric_negative=-5, nan="NaN", infinity="Infinity", overflow="1e999")[kind]
    elif kind == "open_range":
        row["open_pric"] = "80"
    elif kind == "exchange":
        request["body"]["stex_tp"] = "NY"
    elif kind == "security":
        request["body"]["stk_cd"] = "OTHER"
    elif kind in {"stale_base", "future_base"}:
        request["body"]["base_dt"] = "20260921" if kind == "stale_base" else "20260924"
    elif kind == "currency":
        request["currency"] = "KRW"
    elif kind == "api":
        request["api_id"] = "usa06012"
    elif kind == "calendar":
        request["started_at"] = "2026-09-24T08:10:00+00:00"
    elif kind == "documentation":
        artifacts["documentation"] = b"unqualified definition"
    elif kind == "api_failure":
        response["return_code"] = 1
    artifacts.update(request=encoded(request), response=encoded(response))
    reseal()
    if kind == "http":
        capture = json.loads(artifacts["capture"])
        artifacts["capture"] = encoded(dict(capture, http_status=302))
        inputs["source"]["capture"]["sha256"] = sha256_bytes(artifacts["capture"])
    with pytest.raises(ValueError):
        owner.project(**inputs)


def test_direction_sign_is_not_negative_economic_price(monkeypatch):
    inputs, artifacts, reseal = source_fixture(monkeypatch)
    response = json.loads(artifacts["response"])
    response["result_list"][0]["cur_prc"] = "-105.0000"
    artifacts["response"] = encoded(response)
    reseal()
    assert owner.project(**inputs).current_price == 105


@pytest.mark.parametrize("binding", [None, "0" * 64])
def test_capture_requires_exact_request_hash(monkeypatch, binding):
    inputs, artifacts, _ = source_fixture(monkeypatch)
    capture = json.loads(artifacts["capture"])
    if binding is None:
        capture.pop("request_sha256")
    else:
        capture["request_sha256"] = binding
    artifacts["capture"] = encoded(capture)
    inputs["source"]["capture"]["sha256"] = sha256_bytes(artifacts["capture"])
    with pytest.raises(ValueError, match="capture_binding_mismatch"):
        owner.project(**inputs)


@pytest.mark.parametrize("key", ["request", "capture", "response", "documentation"])
def test_post_seal_bytes_change_rejected(monkeypatch, key):
    inputs, artifacts, _ = source_fixture(monkeypatch)
    artifacts[key] += b" "
    with pytest.raises(ValueError, match="hash_mismatch"):
        owner.project(**inputs)


@pytest.mark.parametrize("close", [105, 200])
def test_latest_chart_close_disqualified_even_inside_ohlc(monkeypatch, close):
    inputs, _, _ = source_fixture(monkeypatch)
    p = owner.project(**inputs)
    prior = dict(date="2026-09-21", open=100, high=110, low=90, close=101, volume=10)
    roles = {r: [prior, dict(prior, date=p.target_session, close=close)]
        for r in ("adjusted_daily", "adjusted_weekly", "adjusted_monthly", "unadjusted_weekly_valuation")}
    before = digest(roles)
    components = owner.materialize(projection=p, roles=roles, ticker="CORZ", market="us",
        cutoff=date.fromisoformat(p.target_session), observed_at=inputs["plan"].frozen_at.isoformat())
    assert components["current_price"] == 105
    assert components["latest_chart_close_disqualification"] == owner.CHART_DENIAL
    assert all(not f["facts"] for f in components["features"].values())
    assert all(not c["eligible"] for cs in components["role_consumer_matrix"].values() for c in cs)
    assert digest(roles) == before


def test_fresh_owner_price_valuation_binding_and_source_removal_fail_closed(tmp_path, monkeypatch):
    from tests.rev8_source_fixtures import fresh_inputs
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    inputs, artifacts, _ = source_fixture(monkeypatch)
    item = fresh_inputs(tmp_path, "CORZ", plan=inputs["plan"])
    item["technical_inputs"] = owner.bind_technical_input(item["technical_inputs"],
        source=inputs["source"], artifacts=artifacts, security=inputs["security"])
    result = assemble_fresh_stock(**item)
    stock = result["packet"]["stocks"][0]
    assert stock["current_price_context"]["current_price"] == 105
    assert stock["current_price_context"]["price_basis"] == "regular_close"
    assert stock["current_valuation_view"]["price_basis"] == "regular_close"
    assert not stock["chart_context"]["available"]
    assert all(not stock["technical_context"]["features"][tf]["facts"] for tf in ("daily", "weekly", "monthly"))
    item["technical_inputs"].pop("completed_close_source")
    with pytest.raises(ValueError, match="completed_close_source_required"):
        assemble_fresh_stock(**item)


@pytest.mark.parametrize("mutation", [None, "parent", "hash", "raw", "escape", "symlink"])
def test_lineage_loader_rejects_drift_and_path_escape(tmp_path, monkeypatch, mutation):
    inputs, artifacts, _ = source_fixture(monkeypatch)
    for name, raw in artifacts.items():
        (tmp_path/name).write_bytes(raw)
    sources = {"CORZ": inputs["source"]}
    lineage = dict(contract=owner.CONTRACT, parent_generation_id=inputs["plan"].run_id,
        sources=sources, sources_sha256=digest(sources))
    if mutation == "parent":
        lineage["parent_generation_id"] = "other"
    elif mutation == "hash":
        lineage["sources_sha256"] = "0"*64
    elif mutation == "raw":
        (tmp_path/"response").write_bytes(b"modified")
    elif mutation == "escape":
        sources["CORZ"]["response"]["path"] = "../response"
        lineage["sources_sha256"] = digest(sources)
    elif mutation == "symlink":
        (tmp_path/"response").unlink()
        (tmp_path/"response").symlink_to(tmp_path/"request")
    (tmp_path/"completed-close-lineage.json").write_bytes(encoded(lineage))
    if mutation:
        with pytest.raises(ValueError):
            owner.load_supplement_lineage(tmp_path, parent_generation_id=inputs["plan"].run_id)
    else:
        loaded = owner.load_supplement_lineage(tmp_path, parent_generation_id=inputs["plan"].run_id)
        assert owner.project(**dict(inputs, source=loaded["CORZ"]["source"],
            artifact_reader=lambda path, sha: loaded["CORZ"]["artifacts"][path])).current_price == 105
