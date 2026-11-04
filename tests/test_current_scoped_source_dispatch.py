"""SYNTHETIC_NOT_REAL_CURRENT: original Class-C owners and mock transport only.

No parent registry or validator is replaced. Only synthetic clocks are pinned.
Writing this file does not execute a provider, DB query, or test.
"""
import asyncio
from copy import deepcopy
from datetime import datetime
import gzip
import hashlib
import json

import httpx
import pytest

from app.services import current_scoped_source_owner as owner
from app.services import prospective_class_c_owner as registration
from app.services.current_scoped_source_dispatch import (
    CurrentScopedDispatcher, CurrentScopedRequestPlan, MAX_RESPONSE_BYTES,
)
from app.services.scoped_routing_identity import ScopedSubject
from app.services.scoped_source_plan import HistoryCounts, ScopedConfig, compile_scoped_wire_contract
from app.services.sealed_fresh_dispatch import SealedDispatcher, consume_bound_result, decode_request_plan
from app.services.sealed_source_transport import CapturedFragment, SealedSourceTransport
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest, encoded
from test_current_financial_parent_generality import POLICY, registered, synthetic_clock

PROVENANCE = "SYNTHETIC_NOT_REAL_CURRENT"
KEY, SECRET, TOKEN = "SYNTHETIC_AUTH_KEY", "SYNTHETIC_AUTH_SECRET", "SYNTHETIC_AUTH_TOKEN"


@pytest.fixture
def setup_parent(tmp_path, monkeypatch, record_property):
    record_property("provenance", PROVENANCE)
    clock = synthetic_clock(monkeypatch)
    monkeypatch.setattr(owner, "_now", clock.now)
    run_id = "TEST_ONLY_SYNTHETIC-ng44-dispatch"
    registered_owner, document, security = registered(tmp_path / "registration", "ZQTEST", "us",
        {"cik": "9141001"}, run_id=run_id)
    document = registration.apply_prospective_owner(document, original=document, owner=registered_owner)
    at = datetime.fromisoformat(document["cutoff"])
    counts = HistoryCounts(adjusted_daily=300, adjusted_weekly=300,
        adjusted_monthly=300, unadjusted_weekly_valuation=300)
    config = ScopedConfig(subjects=(ScopedSubject(ticker=security["ticker"], market="us",
        security_id=security["canonical_security_id"], issuer_id=security["cik"],
        venue=security["exchange"], currency="USD"),),
        kr_history=counts, us_history=counts, kr_max_pages=3)
    wire = compile_scoped_wire_contract(config=config, identities={security["ticker"]: security},
        generation_id=run_id, at=at, code_sha="b" * 40, provider_config_sha256="c" * 64, retries=0)
    plan = wire["request_plan"]
    spec = owner.ScopedSourceSpec(config=config, generation_id=run_id, cutoff=at,
        code_sha="b" * 40, provider_config_sha256="c" * 64,
        maximum_attempts=len(plan.descriptors), retries=0)
    parent = owner.issue_parent(registration_owners={"us": registered_owner},
        admitted_projections={"us": document}, spec=spec, plan=plan, policy=POLICY,
        code_pins=owner.current_code_pins(), enabled=True)
    args = dict(parent=parent, plan=plan, root=tmp_path / "dispatch",
        owners={d.normalizer: d.owner_sha256 for d in plan.descriptors},
        config_identities={"kiwoom": "c" * 64}, credential_presence={"kiwoom": True},
        secrets=(KEY, SECRET, TOKEN))
    return args, clock


def first_read(dispatcher):
    return next(d for d in dispatcher.plan.descriptors
                if d.consumer_role.startswith("stock:") and d.page_ordinal == 1)


def request_for(descriptor):
    wire = json.loads(descriptor.request_json)
    return httpx.Request(wire["method"], wire["url"], headers=wire["headers"],
                         content=wire["body"].encode())


def execute(dispatcher, descriptor, transport, request=None):
    return asyncio.run(dispatcher.execute(descriptor.logical_request_id,
        request or request_for(descriptor), transport=transport, normalize=CapturedFragment(descriptor)))


def test_versioned_receipt_replays_original_execution(setup_parent):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    def handle(request):
        assert run.physical_attempts == 1
        assert (run.root / "physical/attempt-0001.start.json").exists()
        return httpx.Response(200, json={"return_code": 0, "rows": []})
    final = execute(run, descriptor, httpx.MockTransport(handle))
    assert final["status"] == "PASS"
    decoded = decode_request_plan(run.plan.model_dump(mode="json"))
    assert type(decoded) is CurrentScopedRequestPlan
    assert decoded.original_plan() == args["plan"]
    assert decoded.plan_sha256 != args["plan"].plan_sha256
    proof = consume_bound_result(root=run.root, plan=decoded,
        logical_id=descriptor.logical_request_id, receipt_sha256=final["receipt_sha256"])
    assert proof["value"]["source_fact_qualified"] is False
    assert run.physical_accounting()["mutually_exclusive_categories"] == {"stock": 1}


@pytest.mark.parametrize("replacement", ["json", "unissued"])
def test_public_parent_cannot_issue_dispatch(setup_parent, replacement):
    args, _ = setup_parent
    args["parent"] = (owner.resolve_parent(args["parent"]) if replacement == "json"
                      else owner.CurrentScopedSourceParent())
    with pytest.raises(ValueError, match="live_capability_required"):
        CurrentScopedDispatcher(**args)
    assert not args["root"].exists()


def test_parent_lifetime_cannot_replenish_budget(setup_parent):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    with pytest.raises(ValueError, match="lifetime_already_claimed"):
        CurrentScopedDispatcher(**{**args, "root": args["root"].with_name("second-dispatch")})
    assert run.physical_attempts == 0


@pytest.mark.parametrize("mutation", ["parent_receipt", "generation", "retry", "body", "provider"])
def test_public_rehashed_plan_has_no_authority(setup_parent, mutation):
    args, _ = setup_parent
    receipt = owner.resolve_parent(args["parent"], plan=args["plan"])
    data = CurrentScopedRequestPlan(**args["plan"].model_dump(mode="json"),
        parent_receipt_sha256=digest(receipt)).model_dump(mode="json")
    if mutation == "parent_receipt":
        data["parent_receipt_sha256"] = "0" * 64
    elif mutation == "generation":
        data["generation_id"] = "caller-rehashed-generation"
    elif mutation == "retry":
        data["descriptors"][1]["transient_retry_max"] = 1
    elif mutation == "provider":
        data["descriptors"][1]["provider"] = "sec_edgar"
    else:
        row = data["descriptors"][1]
        wire = json.loads(row["request_json"])
        body = json.loads(wire["body"])
        body["stk_cd"] = "WRONG_SECURITY"
        wire["body"] = encoded(body).decode()
        row["request_json"] = encoded(wire).decode()
    with pytest.raises(ValueError):
        CurrentScopedDispatcher(**{**args, "plan": data})
    assert not args["root"].exists()


@pytest.mark.parametrize("mutation", ["owner", "config", "credential"])
def test_dispatch_rechecks_original_source_bindings(setup_parent, mutation):
    args, _ = setup_parent
    changed = {**args}
    if mutation == "owner":
        changed["owners"] = {}
    elif mutation == "config":
        changed["config_identities"] = {"kiwoom": "0" * 64}
    else:
        changed["credential_presence"] = {"kiwoom": False}
    with pytest.raises(ValueError, match="owner_config_or_credential_binding"):
        CurrentScopedDispatcher(**changed)
    assert not args["root"].exists()


@pytest.mark.parametrize("mutation", ["body", "query", "host", "http", "order", "oversize"])
def test_wrong_wire_rejects_before_physical_io(setup_parent, mutation):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    original = request_for(descriptor)
    body, url = original.content, original.url
    if mutation == "body":
        body = encoded({**json.loads(body), "stk_cd": "OTHER"})
    elif mutation == "query":
        url = url.copy_with(query=b"unexpected=1")
    elif mutation == "host":
        url = url.copy_with(host="not-api.kiwoom.com")
    elif mutation == "http":
        url = url.copy_with(scheme="http")
    elif mutation == "order":
        url = url.copy_with(path="/api/dostk/ordr")
    else:
        body = b" " * 20000 + body
    attempted = []
    transport = httpx.MockTransport(lambda request: attempted.append(request))
    with pytest.raises(SourceSafetyStop):
        execute(run, descriptor, transport,
                httpx.Request("POST", url, content=body, headers=original.headers))
    assert attempted == [] and run.physical_attempts == 0


@pytest.mark.parametrize("status", [401, 403, 429])
def test_auth_and_quota_stop_once_with_failure_receipts(setup_parent, status):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={"return_code": status})
    transport = httpx.MockTransport(handle)
    with pytest.raises(SourceSafetyStop):
        execute(run, descriptor, transport)
    final = run.results[descriptor.logical_request_id]
    assert final["status"] != "PASS" and len(final["attempts"]) == 1
    assert final["attempts"][0]["status"] == status
    assert len(calls) == run.physical_attempts == 1 and run.halted
    with pytest.raises(SourceSafetyStop):
        execute(run, descriptor, transport)
    assert len(calls) == 1


def test_transport_failure_never_automatically_retries(setup_parent):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    def fail(request):
        raise httpx.ConnectError("synthetic transport failure", request=request)
    final = execute(run, descriptor, httpx.MockTransport(fail))
    assert final["status"] == "FAILED" and len(final["attempts"]) == 1
    assert run.physical_attempts == 1


def test_http200_provider_denial_stops_with_original_failure_body(setup_parent):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    payload = {'return_code': 1, 'return_msg': 'SYNTHETIC_PROVIDER_DENIAL'}
    with pytest.raises(SourceSafetyStop, match='provider_rejection_stop'):
        execute(run, descriptor, httpx.MockTransport(lambda request: httpx.Response(200,json=payload)))
    final = run.results[descriptor.logical_request_id]
    assert final['status'] != 'PASS' and run.halted and run.physical_attempts == 1
    assert json.loads((run.root/final['attempts'][0]['artifact']).read_bytes()) == payload


@pytest.mark.parametrize("when", ["before", "during"])
def test_revocation_denies_before_source_pass(setup_parent, when):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    if when == "before":
        owner.revoke_parent(args["parent"])
    def handle(request):
        owner.revoke_parent(args["parent"])
        return httpx.Response(200, json={"return_code": 0})
    with pytest.raises((ValueError, SourceSafetyStop), match="capability|scoped"):
        execute(run, descriptor, httpx.MockTransport(handle))
    assert run.physical_attempts == (0 if when == "before" else 1)
    assert run.results.get(descriptor.logical_request_id, {}).get("status") != "PASS"


def test_auth_body_and_hash_not_exported_and_shared_reuse_not_counted(setup_parent):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    auth = next(d for d in run.plan.descriptors if d.endpoint_operation == "credential_exchange")
    response_body = encoded({"token": TOKEN, "return_code": 0})
    def handle(request):
        return httpx.Response(200, content=response_body)
    sealed = SealedSourceTransport(run, httpx.MockTransport(handle), providers={"kiwoom"})
    def request():
        return httpx.Request("POST", "https://api.kiwoom.com/oauth2/token",
            headers={"Content-Type": "application/json;charset=UTF-8"},
            json={"grant_type": "client_credentials", "appkey": KEY, "secretkey": SECRET})
    async def twice():
        first = await sealed.handle_async_request(request())
        second = await sealed.handle_async_request(request())
        assert first.json()["token"] == second.json()["token"] == TOKEN
    asyncio.run(twice())
    assert run.physical_attempts == 1 and sealed.auth_reuses == 1
    assert run.results[auth.logical_request_id]["status"] == "PASS"
    text = "\n".join(p.read_text() for p in run.root.rglob("*") if p.is_file())
    assert "credential_body_sha256" not in text
    assert hashlib.sha256(response_body).hexdigest() not in text
    assert all(value not in text for value in (KEY, SECRET, TOKEN))
    assert SealedDispatcher.credential_body_hash_evidence is True


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks, self.yielded, self.closed = chunks, 0, False

    async def __aiter__(self):
        for value in self.chunks:
            self.yielded += 1
            yield value

    async def aclose(self):
        self.closed = True


@pytest.mark.parametrize("encoding", ["identity", "gzip"])
def test_stream_response_bound_before_full_body_read(setup_parent, encoding):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    raw = b"x" * (MAX_RESPONSE_BYTES + 1)
    stream = Chunks([gzip.compress(raw)] if encoding == "gzip" else [raw, b"must-not-read"])
    transport = httpx.MockTransport(lambda request: httpx.Response(200,
        stream=stream, headers={"content-encoding": encoding}))
    with pytest.raises(SourceSafetyStop, match="response_.*limit"):
        execute(run, descriptor, transport)
    assert stream.closed and stream.yielded == 1
    assert run.physical_attempts == 1 and run.halted
    assert run.results[descriptor.logical_request_id]["status"] != "PASS"


def test_bounded_gzip_rebuild_preserves_status_cursor_and_original_receipt(setup_parent):
    args, _ = setup_parent
    run = CurrentScopedDispatcher(**args)
    descriptor = first_read(run)
    raw = encoded({"return_code": 0, "rows": []})
    compressed = gzip.compress(raw)
    stream = Chunks([compressed[:5], compressed[5:]])
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=stream,
        headers={"content-encoding": "gzip", "content-length": str(len(compressed)),
                 "cont-yn": "Y", "next-key": "synthetic-cursor"}))
    final = execute(run, descriptor, transport)
    assert stream.closed and final["status"] == "PASS"
    assert (run.root / descriptor.raw_path).read_bytes() == raw
    assert final["response_headers"] == {"cont-yn": "Y", "next-key": "synthetic-cursor"}
