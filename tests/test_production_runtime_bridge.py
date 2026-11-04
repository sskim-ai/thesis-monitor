import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.jobs.unified_market_snapshot import build_engine, load_adapter
from app.services.production_b2_execution import ModelTransportError, SemanticReject
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.production_source_execution import ProductionSnapshotPolicy
from app.services.unified_runtime_v2 import CONTRACT
from tests.test_production_runtime_v2 import RuntimePorts, DAY
from tests.test_unified_market_snapshot import FakeClock


def policy(market="us"):
    return asyncio.run(RuntimePorts(FakeClock(market)).policy(market, DAY, "synthetic"))


@pytest.mark.parametrize(
    "mutation",
    [
        "av",
        "wrong_close",
        "omitted_subject",
        "missing_validator",
        "missing_family",
        "duplicate",
        "unknown_route",
        "undeclared_fallback",
    ],
)
def test_policy_fails_closed(mutation):
    value = policy().model_dump(mode="json")
    if mutation == "omitted_subject":
        value["subjects"].pop()
    elif mutation == "missing_validator":
        value["validator_contracts"].pop()
    elif mutation == "duplicate":
        value["source_roles"].append(deepcopy(value["source_roles"][0]))
        value["roles"].append(deepcopy(value["roles"][0]))
    elif mutation == "missing_family":
        keep = [i for i, r in enumerate(value["source_roles"]) if r["purpose"] != "FINANCIAL"]
        value["roles"] = [value["roles"][i] for i in keep]
        value["source_roles"] = [value["source_roles"][i] for i in keep]
    elif mutation == "undeclared_fallback":
        value["source_roles"][0]["declared_fallbacks"] = [["other", "route"]]
    else:
        field, entry = (
            ("provider", "alpha_vantage")
            if mutation == "av"
            else ("route", "usa06012" if mutation == "wrong_close" else "undeclared")
        )
        value["roles"][0][field] = value["source_roles"][0]["role"][field] = entry
    with pytest.raises(ValueError):
        ProductionSnapshotPolicy.model_validate(value)


def test_live_registry_cannot_be_enabled_by_settings_alone():
    with pytest.raises(RuntimeError, match="full_source_backend_not_qualified"):
        load_adapter(
            Settings(
                _env_file=None,
                unified_snapshot_enabled=True,
                unified_snapshot_adapter_version="production-v1",
                unified_snapshot_runtime_contract=CONTRACT,
            )
        )


def settings(tmp_path):
    debug = tmp_path / "debug"
    debug.mkdir()
    return Settings(
        _env_file=None,
        data_dir=str(tmp_path / "data"),
        notification_dry_run=True,
        unified_snapshot_debug_destination=str(debug),
        unified_snapshot_enabled=True,
        unified_snapshot_adapter_version="production-v1",
        unified_snapshot_runtime_contract=CONTRACT,
    )


def test_kis_preflight_before_any_collection(tmp_path):
    frozen = policy("kr")

    class Sources:
        calls = 0

        async def policy(self, *args):
            return frozen

        async def collect(self, *args):
            self.calls += 1
            raise AssertionError("no collection")

    sources = Sources()
    adapter = ProductionRuntimeBridgeV1(
        settings=settings(tmp_path),
        sources=sources,
        model=None,
        delivery=None,
        clock=FakeClock("kr"),
    )
    with pytest.raises(ValueError, match="kis_required_active_binding_missing"):
        asyncio.run(adapter.policy("kr", DAY, "synthetic"))
    assert sources.calls == 0


def test_actual_job_engine_factory_preserves_runtime_v2(tmp_path):
    adapter = object()
    engine = build_engine(
        settings(tmp_path),
        adapter,
        repo_commit="synthetic",
        adapter_fingerprint="unqualified-offline",
    )
    assert engine.ports is adapter and engine.v2
    assert engine.config.stage_timeout_seconds == engine.config.collection_timeout_seconds == 600
    assert engine.config.public()["model_attempts_per_role"] == 3


@pytest.mark.parametrize("first", ["timeout", "transport", "json", "wire"])
def test_bridge_raw_first_identical_transport_form_retry(tmp_path, first):
    events = []

    class Transport:
        async def request(self, payload, **kwargs):
            events.append(deepcopy(payload))
            if len(events) == 1:
                if first == "timeout":
                    raise TimeoutError()
                if first == "transport":
                    raise ModelTransportError()
                return b"not json" if first == "json" else b'{"value":"not numeric"}'
            return b'{"value":1}'

    def accept(stage, request, output):
        assert (tmp_path / "attempt-2/response.raw").read_bytes() == b'{"value":1}'
        assert output == {"value": 1}

    adapter = ProductionRuntimeBridgeV1(
        settings=None, sources=None, model=Transport(), delivery=None, clock=None
    )
    request = dict(
        batch=1,
        subjects=["synthetic"],
        payload=dict(
            prompt="fixed",
            input={},
            response_schema={
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        ),
    )
    row = asyncio.run(adapter._invoke(SimpleNamespace(accept=accept), "CORE", request, tmp_path))
    assert row["output"] == {"value": 1} and len(events) == 2 and events[0] == events[1]


def test_bridge_semantic_reject_is_final_with_raw_receipt(tmp_path):
    calls = []

    class Transport:
        async def request(self, *args, **kwargs):
            calls.append(1)
            return b"{}"

    def reject(*args):
        raise ValueError("semantic evidence mismatch")

    adapter = ProductionRuntimeBridgeV1(
        settings=None, sources=None, model=Transport(), delivery=None, clock=None
    )
    request = dict(
        batch=1,
        subjects=[],
        payload=dict(prompt="fixed", input={}, response_schema={"type": "object"}),
    )
    with pytest.raises(SemanticReject):
        asyncio.run(adapter._invoke(SimpleNamespace(accept=reject), "CORE", request, tmp_path))
    assert calls == [1] and (tmp_path / "attempt-1/response.raw").read_bytes() == b"{}"
    assert (
        json.loads((tmp_path / "attempt-1/receipt.json").read_bytes())["classification"]
        == "SEMANTIC_REJECT"
    )
