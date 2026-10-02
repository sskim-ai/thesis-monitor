"""Synthetic mechanics only. These tests do not qualify a live source cohort."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import hashlib
import json

import httpx
import pytest
from sqlmodel import SQLModel, Session, create_engine

from app.providers.registry import provider_priority
from app.macro.kr_close import run_kr_close_market_briefing
from app.models.financial import FinancialSnapshot
from app.models.security import ConsensusEstimate, ShareCountObservation, ProviderResponseCache
from app.schemas.thesis import PriceContext
from app.services.ohlcv_client import OhlcvClient
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import (
    A, B, C, D, FrozenRun, OwnerAdapter, OwnerProjection, SourceInput, SourceRole,
    compose_attempt, freeze_run,
)
from app.services.unified_source_observer import OhlcvRead, OhlcvReceiptObserver
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.valuation_snapshot_service import ValuationSnapshotService


AT = datetime(2026, 9, 26, 0, tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({"ohlcv_analyst", "sec_edgar", "krx_night_futures"}))


@pytest.fixture
def anyio_backend():
    return "asyncio"


def payload(*, high=12, upstream=None):
    meta = {"provider": "ohlcv_analyst", "adjusted": True}
    if upstream:
        meta["upstream_provider"] = upstream
    return {"resolved_symbol": {"code": "EXAMPLE"}, "meta": meta,
            "periods": {"daily": [{"date": "2026-09-25", "open": 10, "high": high,
                                   "low": 9, "close": 11, "volume": 100}]}}


def observer(tmp_path, *, budget=2):
    params = {"symbol": "EXAMPLE", "periods": "daily", "count": 1,
              "include_indicators": "true", "indicator_limit": 1, "adjusted": "true"}
    read = OhlcvRead(role="price:EXAMPLE:daily", symbol="EXAMPLE", market="us",
                     provider="ohlcv_analyst", period="daily", adjusted=True,
                     session_date=date(2026, 9, 25), params=params, max_requests=budget)
    return OhlcvReceiptObserver(root=tmp_path / "attempt", run_id="synthetic-run",
                                attempt_id="A", reads=(read,), policy=POLICY)


@pytest.mark.anyio
@pytest.mark.parametrize("failure", ["malformed", "http", "transport"])
async def test_real_owner_records_every_retry_and_refetch(tmp_path, failure):
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            if failure == "transport":
                raise httpx.ReadTimeout("secret exception text must not be exported", request=request)
            if failure == "http":
                return httpx.Response(503, json={"error": "unavailable"})
            return httpx.Response(200, json=payload(high=1))
        return httpx.Response(200, json=payload())
    audit = observer(tmp_path)
    owner = OhlcvClient(source_observer=audit)
    async with httpx.AsyncClient(base_url="https://fixture.invalid", transport=httpx.MockTransport(handler),
                                headers={"X-API-Key": "do-not-record-this"}) as client:
        _, bars = await owner._request_period(client, "EXAMPLE", "daily", 1)
    assert bars[-1]["close"] == 11
    assert len(calls) == 2
    receipts = [json.loads(p.read_bytes()) for p in sorted(audit.root.glob("*.response.json"))]
    assert [r["ordinal"] for r in receipts] == [1, 2]
    assert all(r["attempt_id"] == "A" for r in receipts)
    assert receipts[-1]["request_sha256"] == digest(receipts[-1]["request"])
    for receipt in receipts:
        if receipt["artifact"]:
            raw = (audit.root / receipt["artifact"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == receipt["artifact_sha256"]
    normalized = [json.loads(p.read_bytes()) for p in sorted(audit.root.glob("*.normalization.json"))]
    assert len(normalized) == (2 if failure == "malformed" else 1)
    assert normalized[-1]["valid"] is True
    if failure == "malformed":
        assert normalized[0]["valid"] is False
    exported = b"".join(p.read_bytes() for p in audit.root.iterdir())
    assert b"do-not-record-this" not in exported
    assert b"secret exception text" not in exported


@pytest.mark.anyio
@pytest.mark.parametrize("upstream", ["alpha_vantage", "AlphaVantageKrCloseFx", "massive", "mock", "undeclared"])
async def test_nested_gateway_provider_rejected(tmp_path, upstream):
    audit = observer(tmp_path)
    async with httpx.AsyncClient(base_url="https://fixture.invalid", transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json=payload(upstream=upstream))
    )) as client:
        with pytest.raises(ValueError, match="source_provider_not_authorized"):
            await OhlcvClient(source_observer=audit)._request_period(client, "EXAMPLE", "daily", 1)
    assert len(list(audit.root.glob("*.body"))) == 1
    assert not list(audit.root.glob("*.normalization.json"))


@pytest.mark.anyio
async def test_budget_and_plan_reject_before_dispatch(tmp_path):
    audit = observer(tmp_path, budget=1)
    calls = []
    def handler(r):
        calls.append(r)
        return httpx.Response(200, json=payload(high=1))
    async with httpx.AsyncClient(base_url="https://fixture.invalid", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="source_request_budget_exhausted"):
            await OhlcvClient(source_observer=audit)._request_period(client, "EXAMPLE", "daily", 1)
        with pytest.raises(ValueError, match="source_request_outside_frozen_plan"):
            await OhlcvClient(source_observer=audit)._request_period(client, "OTHER", "daily", 1)
    assert len(calls) == 1


@pytest.mark.anyio
async def test_no_observer_preserves_original_owner_behavior():
    value = payload()
    value.pop("meta")
    value.pop("resolved_symbol")
    async with httpx.AsyncClient(base_url="https://fixture.invalid", transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json=value)
    )) as client:
        _, bars = await OhlcvClient()._request_period(client, "EXAMPLE", "daily", 1)
    assert bars[-1]["close"] == 11


@pytest.mark.anyio
async def test_secret_body_withheld(tmp_path):
    audit = observer(tmp_path)
    async with httpx.AsyncClient(base_url="https://fixture.invalid", transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={"token": "secret"})
    )) as client:
        with pytest.raises(ValueError, match="source_response_secret_risk"):
            await OhlcvClient(source_observer=audit)._request_period(client, "EXAMPLE", "daily", 1)
    assert not list(audit.root.glob("*.body"))


def test_default_registry_unchanged_optin_is_closed():
    assert any(p.name == "mock" for p in provider_priority())
    assert provider_priority(source_policy=POLICY) == []
    assert all(POLICY.permits(p.name) for p in provider_priority(True, source_policy=POLICY))


@pytest.mark.anyio
async def test_kr_fx_blocks_before_cache_or_delivery():
    class NoSession:
        def exec(self, *a, **k):
            pytest.fail("must not read or reuse existing Alpha briefing")
    result = await run_kr_close_market_briefing(NoSession(), date(2026, 9, 25), source_policy=POLICY)
    assert result.status == "unavailable"
    assert result.briefing is None
    assert result.observation_count == 0


def test_cached_financial_source_exclusion(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    # Isolate source policy from the independently tested financial quality gate.
    monkeypatch.setattr("app.services.valuation_snapshot_service.financial_snapshot_is_usable", lambda r: True)
    with Session(engine) as session:
        for provider in ("sec_edgar", "alpha_vantage", "massive", "mock"):
            session.add(FinancialSnapshot(ticker="EXAMPLE", period="2026", provider=provider))
        session.commit()
        assert len(ValuationSnapshotService()._financial_rows(session, "EXAMPLE")) == 4
        assert [r.provider for r in ValuationSnapshotService(source_policy=POLICY)._financial_rows(
            session, "EXAMPLE"
        )] == ["sec_edgar"]


@pytest.mark.anyio
async def test_actual_valuation_fetch_excludes_cached_alpha_with_credentials_present():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    service = ValuationSnapshotService(source_policy=POLICY, transport=httpx.MockTransport(
        lambda r: pytest.fail("no refresh or fallback is authorized during seed consumption")
    ))
    service.settings = service.settings.model_copy(update={"alpha_vantage_api_key": "fixture",
        "finnhub_api_key": "fixture", "sec_user_agent": "fixture"})
    with Session(engine) as session:
        session.add(ConsensusEstimate(ticker="EXAMPLE", provider="alpha_vantage", estimate_period="FY1",
                                      estimate_as_of=AT, estimate_mean=77))
        session.add(ShareCountObservation(ticker="EXAMPLE", provider="alpha_vantage", period="2026",
                                          diluted_shares=123))
        session.add(ProviderResponseCache(ticker="EXAMPLE", provider="alpha_vantage", data_type="OVERVIEW",
                                          payload='{"PERatio":"77"}', fetched_at=AT))
        session.commit()
        result = await service.fetch("EXAMPLE", "NASDAQ", PriceContext(), as_of=AT, session=session)
        assert result.estimate_provider != "alpha_vantage"
        assert result.forward_eps is None
        assert result.provider_trailing_pe is None


def fixture_receipt(root, role, fields, suffix=""):
    request = {"method": "GET", "route": "/synthetic-only"}
    receipt = {**fields, "symbol": role.symbol, "market": role.market,
               "provider": role.provider, "basis": role.basis, "session": role.session,
               "ordinal": 1, "outcome": "HTTP_RESPONSE", "http_status": 200,
               "request": request, "request_sha256": digest(request)}
    path = root / f"{role.key}{suffix}.receipt.json"
    raw = json.dumps(receipt, default=lambda v: v.isoformat()).encode()
    path.write_bytes(raw)
    return {"receipt_artifact": path.name, "receipt_sha256": hashlib.sha256(raw).hexdigest()}


@pytest.fixture
def composition(tmp_path):
    roles = tuple(SourceRole(key=key, owner="fixture_owner", market="us", symbol="EXAMPLE",
                             acquisition_class=cls, mandatory=key != "fx", provider=provider,
                             basis="fixture_basis", session="2026-09-25")
                  for key, cls, provider in (("price", A, "ohlcv_analyst"),
                      ("night", B, "krx_night_futures"), ("financial", C, "sec_edgar"),
                      ("fx", D, "alpha_vantage")))
    def project(raw, cutoff):
        value = json.loads(raw)
        return OwnerProjection(value=value["value"], provider=value["provider"], market=value["market"],
            symbol=value["symbol"], basis=value["basis"], session=value["session"],
            eligible=value["eligible"], denial=None, source_time=datetime.fromisoformat(value["source_time"]),
            record_id=value["record_id"], version=value["version"])
    owners = {"fixture_owner": OwnerAdapter("synthetic-mechanics-only", "1" * 64, project)}
    sources = {}
    for role in roles[:-1]:
        value = {"provider": role.provider, "market": "us", "symbol": "EXAMPLE", "basis": role.basis,
                 "session": role.session, "eligible": True, "source_time": (AT - timedelta(days=2)).isoformat(),
                 "record_id": "filing1", "version": "v1", "value": {"amount": 11, "provider": role.provider}}
        raw = json.dumps(value).encode()
        path = tmp_path / f"{role.key}.json"
        path.write_bytes(raw)
        extra = ({"attempt_id": "A", "requested_at": AT + timedelta(minutes=1),
                  "received_at": AT + timedelta(minutes=1)} if role.acquisition_class == A
                 else {"acquisition_id": "night-run-once", "requested_at": AT, "received_at": AT}
                 if role.acquisition_class == B else {"original_record_id": "filing1", "version": "v1"})
        fields = dict(role=role.key, run_id="run", acquisition_class=role.acquisition_class,
                      artifact=path.name, artifact_sha256=hashlib.sha256(raw).hexdigest(), **extra)
        if role.acquisition_class in (A, B):
            fields.update(fixture_receipt(tmp_path, role, fields))
        sources[role.key] = SourceInput(**fields)
    sources["fx"] = SourceInput(role="fx", run_id="run", acquisition_class=D, denial="provider_excluded")
    args = dict(root=tmp_path, run_id="run", run_started_at=AT, cutoff=AT, roles=roles,
                inputs=tuple(sources[k] for k in ("night", "financial", "fx")), policy=POLICY, owners=owners)
    return args, sources


def compose(args, sources, frozen=None, **overrides):
    seed = frozen or freeze_run(**args)
    kwargs = dict(frozen=seed, expected_run_sha256=seed.sha256, root=args["root"], attempt_id="A",
                  started_at=AT + timedelta(minutes=1), cutoff=AT + timedelta(minutes=2),
                  inputs=(sources["price"],), owners=args["owners"])
    kwargs.update(overrides)
    return compose_attempt(**kwargs)


def test_class_c_and_b_reuse_original_time_across_whole_attempts(composition):
    args, sources = composition
    seed = freeze_run(**args)
    first = compose(args, sources, seed)
    (args["root"] / "frozen-run.json").write_bytes(seed.content)
    (args["root"] / "attempt-A.json").write_text(json.dumps(first, indent=2))
    for attempt in ("B", "C"):
        fields = {**sources["price"].model_dump(), "attempt_id": attempt}
        fields.update(fixture_receipt(args["root"], args["roles"][0], fields, suffix=attempt))
        next_input = SourceInput.model_validate(fields)
        result = compose(args, sources, seed, attempt_id=attempt, inputs=(next_input,))
        assert result["seed_sha256"] == first["seed_sha256"]
        assert result["run_components"] == first["run_components"]
        assert result["snapshot_sha256"] != first["snapshot_sha256"]
        assert result["model_dispatch_qualified"] is False
        (args["root"] / f"attempt-{attempt}.json").write_text(json.dumps(result, indent=2))
    financial = next(c for c in first["run_components"] if c["source"]["role"] == "financial")
    assert financial["original_source_time"] == (AT - timedelta(days=2)).isoformat()
    assert financial["source"]["received_at"] is None
    denied = next(c for c in first["run_components"] if c["source"]["role"] == "fx")
    assert denied["value"] is None


@pytest.mark.parametrize("mutation,error", [
    ({"run_id": "other"}, "source_run_role_mismatch"),
    ({"attempt_id": "B"}, "source_attempt_mismatch"),
    ({"artifact_sha256": "0" * 64}, "source_artifact_hash_mismatch"),
    ({"artifact": "../outside.json"}, "source_artifact_path_invalid"),
    ({"received_at": AT + timedelta(minutes=3)}, "source_time_outside_cutoff"),
    ({"requested_at": AT}, "source_not_acquired_in_required_window"),
])
def test_attempt_binding_tamper(composition, mutation, error):
    args, sources = composition
    item = SourceInput.model_validate({**sources["price"].model_dump(), **mutation})
    with pytest.raises(ValueError, match=error):
        compose(args, sources, inputs=(item,))


@pytest.mark.parametrize("field,value,error", [
    ("symbol", "OTHER", "source_owner_identity_basis_session_mismatch"),
    ("market", "kr", "source_owner_identity_basis_session_mismatch"),
    ("basis", "adjusted_instead_of_raw", "source_owner_identity_basis_session_mismatch"),
    ("session", "2026-09-24", "source_owner_identity_basis_session_mismatch"),
    ("eligible", False, "source_owner_current_eligibility_failed"),
    ("source_time", "2026-09-27T00:00:00+00:00", "future_source_not_eligible"),
    ("value", {"nested": {"upstream_provider": "alpha_vantage"}}, "source_provider_not_authorized"),
])
def test_source_projection_cannot_be_repaired_by_rehashing(composition, field, value, error):
    args, sources = composition
    path = args["root"] / "price.json"
    payload = json.loads(path.read_bytes())
    payload[field] = value
    raw = json.dumps(payload).encode()
    path.write_bytes(raw)
    fields = {**sources["price"].model_dump(), "artifact_sha256": hashlib.sha256(raw).hexdigest()}
    fields.update(fixture_receipt(args["root"], args["roles"][0], fields))
    item = SourceInput.model_validate(fields)
    with pytest.raises(ValueError, match=error):
        compose(args, sources, inputs=(item,))


def test_missing_mandatory_price_and_price_patching_rejected(composition):
    args, sources = composition
    with pytest.raises(ValueError, match="whole_attempt_source_set_required"):
        compose(args, sources, inputs=())
    denied = SourceInput(role="price", run_id="run", acquisition_class=D, denial="missing")
    with pytest.raises(ValueError, match="mandatory_source_unavailable"):
        compose(args, sources, inputs=(denied,))
    with pytest.raises(ValueError):
        SourceInput.model_validate({**sources["price"].model_dump(), "value": 999})


def test_seed_content_owner_code_and_source_tamper_rejected(composition):
    args, sources = composition
    seed = freeze_run(**args)
    with pytest.raises(ValueError, match="run_seed_hash_mismatch"):
        compose(args, sources, frozen=FrozenRun(seed.content + b" "), expected_run_sha256=seed.sha256)
    changed = replace(args["owners"]["fixture_owner"], code_sha256="2" * 64)
    with pytest.raises(ValueError, match="frozen_run_projection_changed"):
        compose(args, sources, seed, owners={"fixture_owner": changed})
    (args["root"] / "financial.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="source_artifact_hash_mismatch"):
        compose(args, sources, seed)


def test_persisted_seed_not_relabelled_attempt_fresh(composition):
    args, sources = composition
    with pytest.raises(ValueError, match="persisted_record_version_required"):
        SourceInput.model_validate({**sources["financial"].model_dump(), "attempt_id": "A"})
    with pytest.raises(ValueError, match="denial_must_not_contain_source_or_value"):
        SourceInput.model_validate({**sources["fx"].model_dump(), "artifact": "cached.json"})
    changed = SourceInput.model_validate({**sources["financial"].model_dump(), "version": "v2"})
    with pytest.raises(ValueError, match="source_record_version_mismatch"):
        freeze_run(**{**args, "inputs": (sources["night"], changed, sources["fx"])})


def test_cannot_relabel_old_price_receipt_as_next_attempt(composition):
    args, sources = composition
    renamed = SourceInput.model_validate({**sources["price"].model_dump(), "attempt_id": "B"})
    with pytest.raises(ValueError, match="source_acquisition_receipt_binding_mismatch"):
        compose(args, sources, attempt_id="B", inputs=(renamed,))
