"""Synthetic boundary controls, never evidence of a live cohort PASS."""

from datetime import datetime, timezone
import json

import httpx
import pytest

from app.services.unified_full_source_cohort import FullSourceRunSeed, compose_full_source
from app.services.unified_live_source_transport import BoundedTransport, SourceSafetyStop
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy


def recorder(tmp_path, monkeypatch, maximum=1):
    monkeypatch.setattr("app.services.unified_live_source_transport.time.sleep", lambda _: None)
    return BoundedTransport(root=tmp_path / "wire", maximum_logical=maximum, guard=lambda: None)


@pytest.mark.parametrize("maximum", [None, 0, -1, 1.5, True])
def test_unbounded_plan_denied_before_network(tmp_path, maximum):
    with pytest.raises(ValueError, match="finite_transport_budget"):
        BoundedTransport(root=tmp_path, maximum_logical=maximum, guard=lambda: None)


@pytest.mark.parametrize("statuses,expected", [([503, 502, 200], 3), ([429, 200], 2),
    ([400], 1), ([404], 1), ([422], 1), ([200], 1), ([503, 503, 503], 3)])
def test_only_transport_retry_byte_identical(tmp_path, monkeypatch, statuses, expected):
    wire = recorder(tmp_path, monkeypatch)
    calls = []
    def send(request):
        calls.append((request.url, request.content, request.headers))
        return httpx.Response(statuses[len(calls)-1], json={"result": []})
    with httpx.Client(transport=httpx.MockTransport(send)) as client:
        wire.post(client, "https://fixture.invalid/read", json={"source": "x"}, headers={}, request={"source": "x"})
    assert len(calls) == expected and all(c == calls[0] for c in calls)
    assert wire.attempts == expected and wire.retries == expected - 1
    assert len(list((tmp_path / "wire").glob("*.body"))) == expected


def test_timeout_three_attempts_not_four(tmp_path, monkeypatch):
    wire = recorder(tmp_path, monkeypatch)
    calls = []
    def send(request):
        calls.append(request)
        raise httpx.ReadTimeout("private exception omitted", request=request)
    with httpx.Client(transport=httpx.MockTransport(send)) as client:
        with pytest.raises(httpx.ReadTimeout):
            wire.post(client, "https://fixture.invalid/read", json={}, headers={}, request={})
    assert len(calls) == 3
    assert b"private exception" not in b"".join(p.read_bytes() for p in (tmp_path / "wire").iterdir())


def test_budget_exhaustion_is_systemic(tmp_path, monkeypatch):
    wire = recorder(tmp_path, monkeypatch)
    wire.begin({"role": "first"})
    with pytest.raises(SourceSafetyStop, match="budget_exhausted"):
        wire.begin({"role": "second"})
    assert not issubclass(SourceSafetyStop, Exception)


@pytest.mark.parametrize("status", [401, 403])
def test_auth_failure_no_retry(tmp_path, monkeypatch, status):
    wire = recorder(tmp_path, monkeypatch)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(status, json={}))) as client:
        with pytest.raises(SourceSafetyStop, match="authorization_failed"):
            wire.post(client, "https://fixture.invalid/read", json={}, headers={}, request={})
    assert wire.attempts == 1


def test_secret_exchange_receipt_contains_no_body_or_token(tmp_path, monkeypatch):
    wire = recorder(tmp_path, monkeypatch)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"token": "private"}))) as client:
        wire.post(client, "https://fixture.invalid/auth", json={"secret": "private"}, headers={},
                  request={"secret": "private"}, secret=True)
    exported = b"".join(p.read_bytes() for p in (tmp_path / "wire").iterdir())
    assert b"private" not in exported and not list((tmp_path / "wire").glob("*.body"))


def test_secret_in_data_systemic_stop(tmp_path, monkeypatch):
    wire = recorder(tmp_path, monkeypatch)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"token": "private"}))) as client:
        with pytest.raises(SourceSafetyStop, match="secret_integrity_failure"):
            wire.post(client, "https://fixture.invalid/data", json={}, headers={}, request={})
    assert not list((tmp_path / "wire").glob("*.body"))


def seed(**changes):
    h = digest("synthetic")
    params = dict(proof_mode="AD_HOC_LIVE_SOURCE_PROOF", packet_scope="LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION",
        parent_run_id="synthetic", started_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
        source_policy_sha256=h, inventory_sha256=h, code_config_sha256=h, universe_sha256=h,
        attempts={"us": "US-A1", "kr": "KR-A1"}, attempt_hashes={"us": h, "kr": h},
        run_acquisitions={"night": h}, class_c_version_set_sha256=digest({}),
        stock_cohort_hashes={"us": h, "kr": h}, night_publication_receipt_sha256=h,
        optional_denial_set_sha256=digest({}), skhy_issuer_bridge_sha256=digest({}), source_authority_contract_sha256=h)
    return FullSourceRunSeed(**{**params, **changes})


@pytest.mark.parametrize("changes", [{"attempts": {"us": "A", "kr": "A"}},
    {"attempts": {"us": "A"}}, {"run_acquisitions": {}}, {"night_publication_receipt_sha256": ""},
    {"started_at": datetime(2026, 9, 27)}, {"packet_scope": "PRODUCTION"}])
def test_seed_incomplete_identity_rejected(changes):
    with pytest.raises(ValueError):
        seed(**changes)


def test_seed_deterministic_json_roundtrip():
    first = seed()
    assert FullSourceRunSeed.model_validate(json.loads(first.model_dump_json())).sha256 == first.sha256


@pytest.mark.parametrize("changed", ["version_set", "optional_denials", "issuer_bridge"])
def test_full_composition_rejects_unbound_versions_or_denials(changed):
    args = dict(seed=seed(), market_inputs={}, stock_inputs={}, authority_inputs={},
                version_set={}, optional_denials={}, issuer_bridge={})
    args[changed] = {"unowned": "injected"}
    with pytest.raises(ValueError, match="run_component_hash_mismatch"):
        compose_full_source(**args)


def test_current_whole_stock_set_required():
    with pytest.raises(ValueError, match="whole_universe_required"):
        compose_full_source(seed=seed(), market_inputs={}, stock_inputs={}, authority_inputs={},
                            version_set={}, optional_denials={}, issuer_bridge={})


@pytest.mark.parametrize("provider", ["alpha_vantage", "massive", "mock", "undeclared"])
def test_provider_exclusion(provider):
    with pytest.raises(ValueError):
        UnifiedSourcePolicy(frozenset({"kiwoom"})).require(provider)


def test_legacy_market_plan_wire_shape_unchanged():
    from app.services.unified_source_observer import OhlcvRead
    from datetime import date
    read = OhlcvRead(role="market", symbol="SPY", market="us", provider="ohlcv_analyst",
        period="daily", adjusted=True, session_date=date(2026, 9, 25),
        params={"symbol": "SPY", "periods": "daily", "adjusted": "true"}, max_requests=1)
    assert "response_provider" not in read.model_dump(mode="json")
    assert "response_provider" not in json.loads(read.model_dump_json())
    native = read.model_copy(update={"response_provider": "kiwoom"})
    assert native.model_dump(mode="json")["response_provider"] == "kiwoom"


def test_native_response_provider_requires_explicit_policy(tmp_path):
    from app.services.unified_source_observer import OhlcvRead, OhlcvReceiptObserver
    from datetime import date
    read = OhlcvRead(role="market", symbol="SPY", market="us", provider="ohlcv_analyst",
        response_provider="kiwoom", period="daily", adjusted=True, session_date=date(2026, 9, 25),
        params={"symbol": "SPY", "periods": "daily", "adjusted": "true"}, max_requests=1)
    with pytest.raises(ValueError, match="source_provider_not_authorized"):
        OhlcvReceiptObserver(root=tmp_path / "a", run_id="a", attempt_id="b", reads=(read,),
                            policy=UnifiedSourcePolicy(frozenset({"ohlcv_analyst"})))


def test_only_real_native_transport_is_live(tmp_path, monkeypatch):
    import asyncio
    from app.services.unified_live_source_transport import LiveAsyncTransport, is_native_live_transport
    assert is_native_live_transport(None)
    mock = httpx.MockTransport(lambda r: httpx.Response(200, json={}))
    assert not is_native_live_transport(mock)
    wrapper = LiveAsyncTransport(recorder=recorder(tmp_path, monkeypatch), authorize=lambda r: None)
    assert is_native_live_transport(wrapper)
    asyncio.run(wrapper.shutdown())
    wrapper.native = mock
    assert not is_native_live_transport(wrapper)
