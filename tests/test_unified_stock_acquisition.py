from copy import deepcopy
from datetime import datetime, timezone
import json

import httpx
import pytest

from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import (
    ROLES, UNIVERSE, StockPlan, StockRead, bound_artifact, coverage, make_reads, validate_role,
)
from scripts.unified_stock_source_worker import WireBoundary, sha


@pytest.fixture
def plan():
    universe = {m: {"eligible_subjects": list(ts)} for m, ts in UNIVERSE.items()}
    identities = {t: {"canonical_security_id": "security-" + t,
                     "exchange": "NASDAQ" if m == "us" else "KRX"}
                  for m, ts in UNIVERSE.items() for t in ts}
    counts = {m: {r: 300 for r in ROLES} for m in UNIVERSE}
    return StockPlan(run_id="run", acquisition_id="acquisition", frozen_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
        instruction_sha="1" * 40, implementation_sha="2" * 40, universe_sha256=digest(universe),
        owner_files={"app/providers/kiwoom.py": "3" * 64}, owner_head="4" * 40,
        settings_sha256="5" * 64, request_environment_sha256="6" * 64,
        reads=make_reads(universe, identities, at=datetime(2026, 9, 26, tzinfo=timezone.utc), counts=counts))


def fixture_receipt(plan, root):
    read = plan.reads[0]
    bars = [{"date": "2026-09-25", "open": 10, "high": 12, "low": 9, "close": 11,
             "volume": 500, "value": 5500}]
    raw = encoded({"return_code": 0, "result_list": bars})
    normalized = encoded(bars)
    (root / "page.body").write_bytes(raw)
    (root / "bars.json").write_bytes(normalized)
    request = {"method": "POST", "route": read.route, "api_id": read.api_id,
               "payload": {"stk_cd": read.subject, "upd_stkpc_tp": "1", "stex_tp": read.exchange}}
    page = {"provider": "kiwoom", "entry_id": read.entry_id, "page_ordinal": 1,
            "request": request, "request_sha256": digest(request), "requested_at": "2026-09-26T00:00:01+00:00",
            "received_at": "2026-09-26T00:00:02+00:00", "artifact": "page.body", "source_sha256": sha(raw),
            "http_status": 200}
    return {"run_id": plan.run_id, "acquisition_id": plan.acquisition_id,
            "plan_sha256": digest(plan.model_dump(mode="json")), "entry": read.model_dump(mode="json"),
            "started_at": "2026-09-26T00:00:00+00:00", "completed_at": "2026-09-26T00:00:03+00:00",
            "status": "CAPTURED", "pages": [page], "normalized_artifact": "bars.json",
            "normalized_sha256": sha(normalized)}


def test_exact_plan(plan):
    assert len(plan.reads) == 88
    assert len({r.entry_id for r in plan.reads}) == 88
    assert {r.latest_completed_session for r in plan.reads if r.market == "us"} == {"2026-09-25"}
    assert {r.latest_completed_session for r in plan.reads if r.market == "kr"} == {"2026-09-23"}


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra"])
def test_plan_coverage_fail_closed(plan, mutation):
    rows = list(plan.reads)
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = rows[0]
    else:
        rows.append(rows[0])
    with pytest.raises(ValueError):
        StockPlan.model_validate({**plan.model_dump(), "reads": rows})


@pytest.mark.parametrize("field,value", [("provider", "alpha_vantage"), ("provider", "massive"),
    ("provider", "mock"), ("provider", "unknown"), ("subject", "NVDA"), ("timeframe", "monthly"),
    ("adjusted", False), ("route", "/api/us/stkinfo"), ("exchange", "UNKNOWN"), ("max_pages", 12)])
def test_role_scope(plan, field, value):
    with pytest.raises(ValueError):
        StockRead.model_validate({**plan.reads[0].model_dump(), field: value})


def test_universe_mismatch_precedes_network():
    universe = {m: {"eligible_subjects": list(ts)} for m, ts in UNIVERSE.items()}
    universe["us"]["eligible_subjects"].remove("CORZ")
    with pytest.raises(ValueError, match="universe_mismatch"):
        make_reads(universe, {}, at=datetime.now(timezone.utc), counts={})


def test_valid_receipt(plan, tmp_path):
    receipt = fixture_receipt(plan, tmp_path)
    assert validate_role(plan, plan.reads[0], receipt, tmp_path)["status"] == "PASS"


@pytest.mark.parametrize("field,value", [("run_id", "prior"), ("acquisition_id", "prior"),
    ("plan_sha256", "0" * 64), ("normalized_sha256", "0" * 64), ("status", "FAILED"),
    ("started_at", "2026-09-25T00:00:00+00:00")])
def test_receipt_binding(plan, tmp_path, field, value):
    receipt = fixture_receipt(plan, tmp_path)
    receipt[field] = value
    with pytest.raises(ValueError):
        validate_role(plan, plan.reads[0], receipt, tmp_path)


@pytest.mark.parametrize("mutation", ["symbol", "basis", "role", "provider", "raw", "future", "empty"])
def test_negative_source_receipts(plan, tmp_path, mutation):
    receipt = fixture_receipt(plan, tmp_path)
    page = receipt["pages"][0]
    if mutation in {"symbol", "basis"}:
        page["request"]["payload"]["stk_cd" if mutation == "symbol" else "upd_stkpc_tp"] = "WRONG"
    elif mutation == "role":
        receipt["entry"]["role"] = "adjusted_monthly"
    elif mutation == "provider":
        page["provider"] = "alpha_vantage"
    elif mutation == "raw":
        (tmp_path / "page.body").write_bytes(b"tamper")
    else:
        bars = json.loads((tmp_path / "bars.json").read_bytes())
        if mutation == "empty":
            bars = []
        else:
            bars[0]["date"] = "2026-09-28"
        (tmp_path / "bars.json").write_bytes(encoded(bars))
        receipt["normalized_sha256"] = sha(encoded(bars))
    with pytest.raises(ValueError):
        validate_role(plan, plan.reads[0], receipt, tmp_path)


def test_coverage_not_partial_qualification(plan):
    rows = [{"entry_id": r.entry_id, "status": "PASS"} for r in plan.reads]
    assert coverage(plan, rows)["complete"]
    rows[0]["status"] = "FAIL"
    assert not coverage(plan, rows)["stock_materialization_allowed"]
    with pytest.raises(ValueError):
        coverage(plan, rows[:-1])


def test_path_escape(tmp_path):
    with pytest.raises(ValueError):
        bound_artifact(tmp_path, "../escape", "0" * 64)


class Client:
    def __init__(self, response=None):
        self.calls = []
        self.response = response or httpx.Response(200, json={"return_code": 0, "result_list": []})

    def post(self, url, **kwargs):
        self.calls.append(url)
        return self.response


def wire_request(plan):
    read = plan.reads[0]
    return "https://api.kiwoom.com" + read.route, {
        "json": {"stk_cd": read.subject, "upd_stkpc_tp": "1", "stex_tp": read.exchange,
                 "strt_dt": "", "exrt_appl_tp": "0"},
        "headers": {"api-id": read.api_id, "cont-yn": "N", "next-key": ""}, "timeout": 10}


@pytest.mark.parametrize("mutation", ["provider", "endpoint", "symbol", "basis", "api"])
def test_transport_denies_before_request(plan, tmp_path, mutation):
    client = Client()
    wire = WireBoundary(root=tmp_path, plan=plan.model_dump(mode="json"), client=client, secrets=())
    wire.begin(plan.reads[0].model_dump(mode="json"))
    url, kwargs = wire_request(plan)
    if mutation == "provider":
        url = "https://www.alphavantage.co/query"
    elif mutation == "endpoint":
        url = "https://api.kiwoom.com/api/us/stkinfo"
    elif mutation == "api":
        kwargs["headers"]["api-id"] = "usa10099"
    else:
        kwargs["json"]["stk_cd" if mutation == "symbol" else "upd_stkpc_tp"] = "WRONG"
    with pytest.raises(ValueError):
        wire.post(url, **kwargs)
    assert not client.calls


def test_no_automatic_retry_or_error_body_loss(plan, tmp_path):
    response = httpx.Response(429, json={"return_code": 429, "return_msg": "rate limit"})
    client = Client(response)
    wire = WireBoundary(root=tmp_path, plan=plan.model_dump(mode="json"), client=client, secrets=())
    wire.begin(plan.reads[0].model_dump(mode="json"))
    url, kwargs = wire_request(plan)
    wire.post(url, **kwargs)
    with pytest.raises(ValueError, match="retry"):
        wire.post(url, **kwargs)
    assert len(client.calls) == 1
    assert (tmp_path / "transport-0001.body").read_bytes() == response.content


def test_pagination_declared_counted_once(plan, tmp_path):
    client = Client(httpx.Response(200, json={"return_code": 0}, headers={"cont-yn": "Y", "next-key": "page2"}))
    wire = WireBoundary(root=tmp_path, plan=plan.model_dump(mode="json"), client=client, secrets=())
    wire.begin(plan.reads[0].model_dump(mode="json"))
    url, kwargs = wire_request(plan)
    wire.post(url, **kwargs)
    second = deepcopy(kwargs)
    second["headers"].update({"cont-yn": "Y", "next-key": "page2"})
    wire.post(url, **second)
    assert wire.data_calls == 2
    assert [r["page_ordinal"] for r in wire.pages] == [1, 2]


def test_secret_response_withheld(plan, tmp_path):
    client = Client(httpx.Response(200, json={"access_token": "private"}))
    wire = WireBoundary(root=tmp_path, plan=plan.model_dump(mode="json"), client=client, secrets=())
    wire.begin(plan.reads[0].model_dump(mode="json"))
    url, kwargs = wire_request(plan)
    with pytest.raises(ValueError, match="secret"):
        wire.post(url, **kwargs)
    assert not list(tmp_path.glob("*.body"))


def test_auth_once_no_credentials_exported(plan, tmp_path):
    client = Client(httpx.Response(200, json={"token": "private-auth"}))
    wire = WireBoundary(root=tmp_path, plan=plan.model_dump(mode="json"), client=client, secrets=("app-secret",))
    wire.begin(plan.reads[0].model_dump(mode="json"))
    kwargs = {"json": {"secretkey": "app-secret"}, "headers": {}, "timeout": 10}
    wire.post("https://api.kiwoom.com/oauth2/token", **kwargs)
    with pytest.raises(ValueError, match="auth_budget"):
        wire.post("https://api.kiwoom.com/oauth2/token", **kwargs)
    assert len(client.calls) == 1
    assert all(b"private-auth" not in p.read_bytes() and b"app-secret" not in p.read_bytes()
               for p in tmp_path.iterdir())
