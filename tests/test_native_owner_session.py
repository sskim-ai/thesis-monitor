"""Actual stage-session objects sharing one offline parent, no model dispatch."""

import inspect
import json
from types import SimpleNamespace

import pytest

from app.services.native_owner_session import (
    BackendOwnerParent,
    ParentAdmissionManifest,
    ParentInvocationBinding,
)
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_snapshot_contract import digest
from tests.test_economic_claim_qualification import claim_fixture, accept
from tests.test_reported_context_consumer import context_invocation
from tests.test_reported_fact_owner import owner_fixture


def source(generation, source_generation, market="us"):
    stocks = {t: {"fresh_run_id": source_generation} for t in UNIVERSE[market]}
    prepared = {
        t: dict(
            mode="EVIDENCE_BASED",
            initial_chain=dict(
                source_generation_id=source_generation, execution_generation_id=generation
            ),
            view_receipt=dict(raw_source_sha256=digest(stocks[t])),
        )
        for t in stocks
    }
    return dict(
        source_generation_id=source_generation,
        stocks=stocks,
        prepared=prepared,
        markets={market: {}},
        valuation_contexts={},
    )


def composition(inv, *, snapshot=None, register=True):
    q = inv.request
    body = source(q.invocation.generation_id, q.invocation.source_generation_id)
    scope = dict(
        run_id="isolated-parent-run",
        market="us",
        generation_id=q.invocation.generation_id,
        source_generation_id=q.invocation.source_generation_id,
        snapshot_sha256=digest(snapshot if snapshot is not None else body),
    )
    manifest = ParentAdmissionManifest(
        **scope,
        invocations=(
            ParentInvocationBinding(
                invocation_id=q.invocation.invocation_id,
                security_id=q.invocation.security_id,
                request_sha256=q.invocation.request_sha256,
                admission_bundle_sha256=digest(inv._registry.bundle.model_dump(mode="json")),
                source_envelope_sha256=inv._registry.bundle.source_envelope_sha256,
            ),
        ),
    )
    parent = BackendOwnerParent(
        authority_native_v2=True,
        **scope,
        admission_manifest=manifest,
        expected_manifest_sha256=digest(manifest.model_dump(mode="json")),
    )
    if register:
        parent.register(inv)
    return parent, scope, body


def session(root, parent, scope, body):
    return ProductionMonitoringSession(
        root,
        market=scope["market"],
        generation_id=scope["generation_id"],
        source_generation_id=scope["source_generation_id"],
        source=body,
        authority_native_v2=True,
        native_owner_parent=parent,
        native_parent_scope=scope,
    )


def test_context_consumer_across_recreated_actual_stage_sessions(tmp_path):
    fact_owner, _ = owner_fixture(UNIVERSE["us"][0])
    inv, _, _, _ = context_invocation(fact_owner)
    parent, scope, body = composition(inv)
    first = session(tmp_path / "core", parent, scope, body)
    receipt = parent.complete(parent.begin(inv.request.invocation.invocation_id))
    assert (
        first.native_context_prompt(inv.request.invocation.invocation_id, receipt)
        == inv.request.prompt
    )
    replay = session(tmp_path / "pass-a", parent, scope, body)
    assert (
        replay.native_context_prompt(inv.request.invocation.invocation_id, receipt)
        == inv.request.prompt
    )
    assert (
        replay.native_context_prompt(inv.request.invocation.invocation_id, receipt)
        == inv.request.prompt
    )
    with pytest.raises(ValueError):
        replay.native_economic_candidate(inv.request.invocation.invocation_id, receipt, None)
    with pytest.raises(ValueError, match="ANOTHER_PARENT"):
        composition(inv)
    parent.close()
    with pytest.raises(ValueError, match="CLOSED"):
        replay.native_context_prompt(inv.request.invocation.invocation_id, receipt)


def test_economic_retry_revoke_and_recreated_session(tmp_path):
    _, _, inv, model = claim_fixture(UNIVERSE["us"][0])
    core = accept(inv, model).candidate
    snapshot = {"collection": {"fixture": "SOURCE_VALIDATION_SEPARATE"}}
    parent, scope, body = composition(inv, snapshot=snapshot)
    first = session(tmp_path / "core", parent, scope, body)
    key = inv.request.invocation.invocation_id
    handle = parent.begin(key)
    raw = json.dumps(model).encode()
    receipt = parent.complete(handle, raw)
    assert parent.complete(handle, raw) == receipt
    assert first.native_economic_candidate(key, receipt, core) == core
    replay = session(tmp_path / "pass-a", parent, scope, body)
    assert replay.native_economic_candidate(key, receipt, core) == core
    from app.services.cross_market_decision_engine_service import DecisionEvidencePacket

    packet = DecisionEvidencePacket(
        packet_id="parent-offline-packet",
        ticker=core.ticker,
        company_name="SYNTHETIC",
        market="us",
        assessment_date="2026-10-09",
        horizon="fixture",
        evidence=(),
        prohibited_claims=(),
        evidence_sha256="a" * 64,
    )
    parent.bind_packet(key, receipt, core, packet)
    assert replay.native_economic_candidate(key, receipt, core, packet=packet) == core
    with pytest.raises(ValueError, match="PACKET_IDENTITY"):
        replay.native_economic_candidate(
            key, receipt, core, packet=packet.model_copy(update={"packet_id": "wrong"})
        )
    retry = parent.begin(key)
    with pytest.raises(ValueError, match="SUPERSEDED"):
        replay.native_economic_candidate(key, receipt, core)
    current = parent.complete(retry, raw)
    assert replay.native_economic_candidate(key, current, core) == core
    parent.revoke(current)
    with pytest.raises(ValueError, match="STALE"):
        replay.native_economic_candidate(key, current, core)
    late = parent.begin(key)
    parent.cancel(late)
    with pytest.raises(ValueError, match="CLOSED_REJECTED_ATTEMPT"):
        parent.complete(late, raw)
    late = parent.begin(key)
    parent.close()
    with pytest.raises(ValueError, match="CLOSED"):
        parent.complete(late, raw)


@pytest.mark.parametrize(
    "field", ["run_id", "market", "generation_id", "source_generation_id", "snapshot_sha256"]
)
def test_parent_scope_substitution(tmp_path, field):
    _, _, inv, _ = claim_fixture()
    parent, scope, body = composition(inv)
    wrong = dict(scope, **{field: "wrong"})
    with pytest.raises(ValueError):
        session(tmp_path, parent, wrong, body)


def test_default_off_and_no_json_capabilities(tmp_path):
    assert (
        inspect.signature(ProductionMonitoringSession).parameters["authority_native_v2"].default
        is False
    )
    assert (
        inspect.signature(ProductionRuntimeBridgeV1).parameters["authority_native_v2"].default
        is False
    )
    _, _, inv, _ = claim_fixture()
    parent, scope, body = composition(inv)
    with pytest.raises(ValueError, match="EXPLICIT_GATE"):
        ProductionMonitoringSession(
            tmp_path,
            market="us",
            generation_id=scope["generation_id"],
            source=body,
            native_owner_parent=parent,
        )
    with pytest.raises(ValueError, match="CAPABILITY_REQUIRED"):
        session(tmp_path, {}, scope, body)
    with pytest.raises(ValueError, match="explicit_bridge_gate"):
        ProductionRuntimeBridgeV1(
            settings=None,
            sources=None,
            model=None,
            delivery=None,
            clock=None,
            native_owner_parents={"run": parent},
        )


def test_actual_bridge_session_composition_passes_live_parent(tmp_path, monkeypatch):
    # Source acquisition is out of this unit's scope. The real bridge composition
    # and real session constructor/consumer execute against a typed fixture stub.
    from app.services import production_runtime_bridge as module

    fact_owner, _ = owner_fixture(UNIVERSE["us"][0])
    inv, _, _, _ = context_invocation(fact_owner)
    snapshot = {"collection": {"fixture": "SOURCE_VALIDATION_SEPARATE"}}
    parent, scope, body = composition(inv, snapshot=snapshot)
    collection = SimpleNamespace(
        market="us",
        packet={"monitoring_input": body},
        attempt_id="source-attempt",
        started_at="fixture",
        production_envelope=SimpleNamespace(generation_id=scope["generation_id"]),
    )
    monkeypatch.setattr(
        module, "ProductionCollection", SimpleNamespace(model_validate=lambda _: collection)
    )
    monkeypatch.setattr(module, "validate_production_collection", lambda *a, **kw: ())
    bridge = ProductionRuntimeBridgeV1(
        settings=None,
        sources=SimpleNamespace(verify=lambda _: None),
        model=None,
        delivery=None,
        clock=SimpleNamespace(now=lambda: None),
        authority_native_v2=True,
        native_owner_parents={scope["run_id"]: parent},
    )
    bridge.policies[scope["run_id"]] = "fixture-policy"
    request = dict(
        run_id=scope["run_id"],
        snapshot=snapshot,
        snapshot_sha256=scope["snapshot_sha256"],
        stage="MARKET",
        inputs={},
    )
    one, _ = bridge._session(request, tmp_path / "one")
    receipt = parent.complete(parent.begin(inv.request.invocation.invocation_id))
    two, _ = bridge._session(request, tmp_path / "two")
    assert one.native_context_prompt(
        inv.request.invocation.invocation_id, receipt
    ) == two.native_context_prompt(inv.request.invocation.invocation_id, receipt)


def test_concurrent_parent_lease_is_exclusive():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    _, _, inv, _ = claim_fixture()
    first, _, _ = composition(inv, register=False)
    second, _, _ = composition(inv, register=False)
    gate = Barrier(2)

    def register(parent):
        gate.wait(timeout=5)
        try:
            parent.register(inv)
            return "PASS"
        except ValueError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as executor:
        result = list(executor.map(register, [first, second]))
    assert sorted(result) == ["INVOCATION_BOUND_TO_ANOTHER_PARENT", "PASS"]
