from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest
from pydantic import ValidationError

from app.services.ohlcv_client import OhlcvClient
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_replay import (
    FrozenOhlcvRole, prohibited_provider, read_bound_artifact, replay_ohlcv_role,
)


@pytest.fixture
def frozen(tmp_path):
    at = datetime(2026, 9, 22, 8, tzinfo=timezone.utc)
    payload = {
        "resolved_symbol": {"code": "EXAMPLE"},
        "meta": {"provider": "ohlcv_analyst", "adjusted": True},
        "periods": {"daily": [{"date": "2026-09-21", "open": 10, "high": 12,
                               "low": 9, "close": 11, "volume": 100}]},
    }
    request = {"method": "GET", "route": "/ohlcv", "params": {
        "symbol": "EXAMPLE", "periods": "daily", "adjusted": "true", "count": 1,
    }}
    raw = json.dumps(payload).encode()
    (tmp_path / "raw.json").write_bytes(raw)
    bars, supply, _ = OhlcvClient._decode_period_payload(
        payload, ticker="EXAMPLE", period="daily", adjusted=True,
    )
    spec = FrozenOhlcvRole(
        run_id="fixture-run", attempt_id="attempt-A", market="us", role="price:EXAMPLE:daily",
        symbol="EXAMPLE", provider="ohlcv_analyst", period="daily", adjusted=True,
        latest_row_date=at.date() - timedelta(days=1), requested_at=at, received_at=at,
        request=request, request_sha256=digest(request), artifact="raw.json",
        artifact_sha256=hashlib.sha256(raw).hexdigest(),
        normalized_sha256=digest({"bars": bars, "supply_demand": supply}),
    )
    kwargs = dict(root=tmp_path, run_id=spec.run_id, attempt_id=spec.attempt_id,
                  market="us", started_at=at, completed_at=at + timedelta(seconds=1))
    return spec, kwargs, payload


def test_existing_owner_deterministic_replay(frozen):
    spec, kwargs, _ = frozen
    first = replay_ohlcv_role(spec, **kwargs)
    assert first == replay_ohlcv_role(spec, **kwargs)
    assert first.receipt.status == "PASS"
    assert first.validator_contract == "ohlcv-provider-integrity-v1"
    assert first.qualification == "ROLE_ONLY_NOT_PRODUCTION_ADAPTER"


@pytest.mark.parametrize("provider", ["alpha_vantage", "Alpha Vantage", "alpha-vantage",
                                     "Massive", "massive.com", "polygon.io"])
def test_prohibited_source_variants(provider):
    assert prohibited_provider(provider)


@pytest.mark.parametrize("change,error", [
    ({"attempt_id": "attempt-B"}, "source_attempt_identity_mismatch"),
    ({"run_id": "another-run"}, "source_attempt_identity_mismatch"),
    ({"market": "kr"}, "source_attempt_identity_mismatch"),
    ({"artifact": "../raw.json"}, "source_artifact_path_invalid"),
    ({"artifact": "/tmp/raw.json"}, "source_artifact_path_invalid"),
    ({"artifact": "missing.json"}, "source_artifact_missing"),
    ({"artifact_sha256": "0" * 64}, "source_artifact_hash_mismatch"),
    ({"request_sha256": "0" * 64}, "source_request_hash_mismatch"),
    ({"normalized_sha256": "0" * 64}, "source_normalization_binding_mismatch"),
    ({"provider": "alpha_vantage"}, "source_provider_not_authorized"),
])
def test_binding_failures(frozen, change, error):
    spec, kwargs, _ = frozen
    with pytest.raises(ValueError, match=error):
        replay_ohlcv_role(spec.model_copy(update=change), **kwargs)


def test_request_cannot_be_rebound_by_rehashing(frozen):
    spec, kwargs, _ = frozen
    request = {**spec.request, "params": {**spec.request["params"], "symbol": "OTHER"}}
    spec = spec.model_copy(update={"request": request, "request_sha256": digest(request)})
    with pytest.raises(ValueError, match="source_request_role_mismatch"):
        replay_ohlcv_role(spec, **kwargs)


@pytest.mark.parametrize("field", ["requested_at", "received_at"])
def test_earlier_attempt_timestamps_rejected(frozen, field):
    spec, kwargs, _ = frozen
    spec = spec.model_copy(update={field: spec.requested_at - timedelta(seconds=1)})
    with pytest.raises(ValueError, match="source_request_outside_attempt"):
        replay_ohlcv_role(spec, **kwargs)


def test_naive_timestamp_rejected(frozen):
    spec, kwargs, _ = frozen
    kwargs["started_at"] = kwargs["started_at"].replace(tzinfo=None)
    with pytest.raises(ValueError, match="source_timezone_required"):
        replay_ohlcv_role(spec, **kwargs)


@pytest.mark.parametrize("mutation,error", [
    (lambda p: p.pop("resolved_symbol"), "source_payload_identity_mismatch"),
    (lambda p: p["meta"].pop("adjusted"), "source_payload_basis_mismatch"),
    (lambda p: p["meta"].update(adjusted="true"), "source_payload_basis_mismatch"),
    (lambda p: p["meta"].update(upstream_provider="massive"), "source_upstream_not_authorized"),
    (lambda p: p["periods"]["daily"][0].update(high=1), "source_ohlcv_integrity_failed"),
    (lambda p: p["periods"].update(daily=[]), "source_ohlcv_integrity_failed"),
    (lambda p: p["periods"]["daily"][0].update(date="2026-09-22"), "source_ohlcv_integrity_failed"),
    (lambda p: p["periods"]["daily"][0].update(date="2026-09-18"), "source_latest_row_mismatch"),
])
def test_actual_owner_rejects_bad_source_even_with_valid_true(frozen, mutation, error):
    spec, kwargs, payload = frozen
    mutation(payload)
    payload["valid"] = True
    raw = json.dumps(payload).encode()
    (kwargs["root"] / "raw.json").write_bytes(raw)
    spec = spec.model_copy(update={"artifact_sha256": hashlib.sha256(raw).hexdigest()})
    with pytest.raises(ValueError, match=error):
        replay_ohlcv_role(spec, **kwargs)


def test_symlink_cannot_import_another_attempt(tmp_path):
    first = tmp_path / "A"
    second = tmp_path / "B"
    first.mkdir()
    second.mkdir()
    (first / "raw.json").write_bytes(b"{}")
    (second / "raw.json").symlink_to(first / "raw.json")
    with pytest.raises(ValueError, match="source_artifact_symlink"):
        read_bound_artifact(second, "raw.json", hashlib.sha256(b"{}").hexdigest())


def test_valid_true_is_not_an_accepted_receipt_field(frozen):
    spec, _, _ = frozen
    with pytest.raises(ValidationError):
        FrozenOhlcvRole.model_validate({**spec.model_dump(), "valid": True})
