"""Offline spies only: fixture provenance cannot enter production dispatch."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from app.services import fixture_context_authority as authority
from app.services import production_model_transport as transport_module
from app.services import production_runtime_bridge as bridge_module
from app.services.market_expectation_evidence_service import (
    build_market_expectation_evidence_view, constrain_market_expectation_batch_schema,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema, build_evidence_alias_catalog, compact_alias_ai_context,
)
from app.services.two_stage_directional_service import DirectionalCoreJudgment
from tests.test_fixture_context_authority_r22r2 import _inputs
from tests.test_production_model_transport import (
    invocation as offline_invocation, payload as normal_payload, transport,
)


def _schema(view):
    schema = build_alias_constrained_batch_schema(
        candidate_schema=DirectionalCoreJudgment.model_json_schema(),
        contract="fixture-semantic-schema", packet_id="fixture:market-expectation",
        aliases_by_ticker={view.ticker: [item.alias for item in view.items]},
    )
    return constrain_market_expectation_batch_schema(schema, views={view.ticker: view})


def _projections():
    owned, catalog, bases = _inputs()
    view = build_market_expectation_evidence_view(owned, catalog, structured_bases=bases)
    alias = compact_alias_ai_context(owned.source_packet, catalog, fixture_view=view)
    return owned, catalog, view, alias, _schema(view)


def _payload(stage, carrier):
    _, _, view, alias, schema = _projections()
    context = view.model_context() if carrier == "semantic" else alias
    value = normal_payload(stage)
    if carrier == "schema":
        value["response_schema"] = schema
    elif carrier == "prompt":
        value["prompt"] = "Offline fixture.\nFROZEN_CONTEXT:\n" + json.dumps(context)
    else:
        value["input"] = context
        if stage != "B2":
            value["prompt"] = "Offline fixture.\nFROZEN_CONTEXT:\n" + json.dumps(context)
    return json.loads(json.dumps(value))


@pytest.fixture
def bound_transport(tmp_path, monkeypatch):
    installation = offline_invocation.__wrapped__(tmp_path, monkeypatch)
    return transport(installation, tmp_path)


def test_generic_alias_rejects_reserved_fixture_without_verified_parent():
    owned, catalog, _ = _inputs()
    with pytest.raises(ValueError, match="fixture_context_verified_alias_path_required"):
        compact_alias_ai_context(owned.source_packet, catalog)


def test_alias_and_schema_retain_issued_parent_after_json_roundtrip():
    owned, _, view, alias, schema = _projections()
    assert alias["test_only_provenance"] == owned.backend_seal.model_dump(mode="json")
    assert alias["contract"] == authority.ALIAS_CONTRACT
    assert alias["production_eligible"] is False
    proof = schema["x-test-only-provenance"]
    assert proof["parents"] == [view.test_only_provenance.model_dump(mode="json")]
    assert proof["production_eligible"] is False
    for projection in (alias, schema):
        assert authority.contains_fixture_provenance(json.loads(json.dumps(projection)))


@pytest.mark.parametrize("change", ("packet", "catalog", "view"))
def test_explicit_alias_path_cannot_sign_arbitrary_projection(change):
    owned, catalog, view, _, _ = _projections()
    packet = owned.source_packet
    if change == "packet":
        packet = packet.model_copy(update={"company_name": "caller replacement"})
    elif change == "catalog":
        catalog = catalog.model_copy(update={"alias_map_sha256": "0" * 64})
    else:
        view = view.model_copy(update={"test_only_provenance": None})
    with pytest.raises(ValueError, match="fixture_context_"):
        compact_alias_ai_context(packet, catalog, fixture_view=view)


def test_revocation_blocks_new_alias_and_schema_projections():
    owned, catalog, view, alias, schema = _projections()
    authority.revoke_market_expectation_fixture(owned)
    for build in (lambda: compact_alias_ai_context(owned.source_packet, catalog, fixture_view=view),
                  lambda: _schema(view)):
        with pytest.raises(ValueError, match="fixture_context_unissued_revoked_or_changed"):
            build()
    for existing in (alias, schema):
        with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
            authority.reject_test_only_production(existing)


def test_parent_receipt_removal_does_not_erase_remaining_projection_markers():
    _, _, _, alias, schema = _projections()
    alias.pop("test_only_provenance")
    schema["x-test-only-provenance"].pop("parents")
    for projection in (alias, schema):
        with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
            authority.reject_test_only_production(projection)


@pytest.mark.parametrize("stage", ("CORE", "B2"))
@pytest.mark.parametrize("carrier", ("semantic", "alias", "schema", "prompt"))
def test_transport_rejects_fixture_before_counter_write_or_worker(bound_transport, stage, carrier):
    item, calls = bound_transport
    value = _payload(stage, carrier)
    before = (deepcopy(item.counts), item.total)
    with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
        transport_module.render_prompt(value, stage)
    with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
        asyncio.run(item.request(value, model="gpt-5.6-sol", effort="xhigh", timeout=600, stage=stage))
    assert not calls
    assert (item.counts, item.total) == before
    assert not item.runtime_root.exists()


@pytest.mark.parametrize("stage", ("CORE", "B2"))
@pytest.mark.parametrize("carrier", ("semantic", "alias", "schema", "prompt"))
def test_bridge_rejects_fixture_before_intent_or_model(tmp_path, stage, carrier):
    calls = []

    async def request(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("fixture reached model")

    bridge = bridge_module.ProductionRuntimeBridgeV1(settings=None, sources=None,
        model=SimpleNamespace(request=request), delivery=None, clock=None)
    request_value = dict(batch=1, subjects=["EXP-FIXTURE"], payload=_payload(stage, carrier))
    with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
        asyncio.run(bridge._invoke(None, stage, request_value, tmp_path / "dispatch"))
    assert not calls and not (tmp_path / "dispatch").exists()


@pytest.mark.parametrize("entry", ("stage", "collect"))
def test_bridge_rejects_marked_request_before_session_or_collection(tmp_path, entry):
    bridge = bridge_module.ProductionRuntimeBridgeV1(settings=None, sources=None,
        model=None, delivery=None, clock=None)
    request = {"payload": _payload("B2", "alias")}
    with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
        asyncio.run(getattr(bridge, entry)(request, tmp_path / "dispatch"))
    assert not (tmp_path / "dispatch").exists()


def test_b2_generated_fixture_rejected_before_authorization(tmp_path, monkeypatch):
    calls = []
    bridge = bridge_module.ProductionRuntimeBridgeV1(settings=None, sources=None,
        model=None, delivery=None, clock=None)
    session = SimpleNamespace(b2_request=lambda ticker: _payload("B2", "schema"))
    collection = SimpleNamespace(production_envelope=SimpleNamespace(subjects=("EXP-FIXTURE",)))
    monkeypatch.setattr(bridge, "_session", lambda *args: (session, collection))
    monkeypatch.setattr(bridge_module, "validate_stage_v2", lambda *args: None)
    monkeypatch.setattr(bridge_module, "authorize_b2", lambda *args, **kwargs: calls.append("authorize"))
    request = dict(contract=bridge_module.CONTRACT, run_id="offline-dispatch", stage="B2",
        snapshot_sha256="0" * 64, snapshot={"collection": {"production_envelope": {"generation_id": "offline"}}})
    with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
        asyncio.run(bridge.stage(request, tmp_path / "dispatch"))
    assert not calls and not (tmp_path / "dispatch").exists()


@pytest.mark.parametrize("stage", ("CORE", "B2"))
def test_unmarked_legacy_transport_still_reaches_only_offline_worker(bound_transport, stage):
    item, calls = bound_transport
    result = asyncio.run(item.request(normal_payload(stage), model="gpt-5.6-sol",
        effort="xhigh", timeout=600, stage=stage))
    assert result == b"{}" and len(calls) == item.total == 1


def test_unmarked_legacy_bridge_still_accepts_offline_response(tmp_path):
    calls = []

    async def request(*args, **kwargs):
        calls.append("model")
        return b"{}"

    bridge = bridge_module.ProductionRuntimeBridgeV1(settings=None, sources=None,
        model=SimpleNamespace(request=request), delivery=None, clock=None)
    session = SimpleNamespace(accept=lambda *args: calls.append("accept"))
    request_value = dict(batch=1, subjects=["NORMAL"], payload=normal_payload("CORE"))
    result = asyncio.run(bridge._invoke(session, "CORE", request_value, tmp_path / "dispatch"))
    assert calls == ["model", "accept"] and result["output"] == {}


def test_unmarked_compact_alias_keeps_legacy_contract_and_shape():
    owned, _, _ = _inputs(issued=False)
    ref = owned.source_packet.evidence[0].model_copy(update={
        "ref_id": "canonical:ordinary", "source_ref": "stock.fact_catalog.ordinary"})
    packet = owned.source_packet.model_copy(update={"packet_id": "ordinary", "ticker": "NORMAL",
                                                   "evidence": (ref,)})
    context = compact_alias_ai_context(packet, build_evidence_alias_catalog(packet))
    assert context["contract"] == packet.contract
    assert "test_only_provenance" not in context
    assert not authority.contains_fixture_provenance(context)


@pytest.mark.parametrize("boundary", ("transport", "bridge"))
@pytest.mark.parametrize("stage", ("CORE", "B2"))
@pytest.mark.parametrize("mutation,error", (
    ("duplicate_block", "production_frozen_context_duplicate"),
    ("malformed_json", "production_frozen_context_json_invalid"),
    ("json_tail", "production_frozen_context_json_invalid"),
    ("duplicate_key", "production_frozen_context_duplicate_key"),
))
def test_prompt_framing_rejected_before_boundary_effects(
    bound_transport, tmp_path, boundary, stage, mutation, error,
):
    item, worker_calls = bound_transport
    value = normal_payload(stage)
    _, _, _, alias, _ = _projections()
    delimiter = "\nFROZEN_CONTEXT:\n"
    fixture_json = json.dumps(alias)
    if mutation == "duplicate_block":
        body = fixture_json + delimiter + json.dumps(value["input"])
    elif mutation == "malformed_json":
        body = fixture_json[:-1]
    elif mutation == "json_tail":
        body = fixture_json + "\nnon-JSON tail"
    else:
        body = '{"provenance":"TEST_ONLY","provenance":"ORDINARY"}'
    value["prompt"] = "Offline framing probe." + delimiter + body
    before = (deepcopy(item.counts), item.total)
    model_calls = []

    async def request(*args, **kwargs):
        model_calls.append((args, kwargs))
        return await item.request(*args, **kwargs)

    bridge = bridge_module.ProductionRuntimeBridgeV1(settings=None, sources=None,
        model=SimpleNamespace(request=request), delivery=None, clock=None)
    with pytest.raises(ValueError, match="^" + error + "$"):
        transport_module.render_prompt(value, stage)
    with pytest.raises(ValueError, match="^" + error + "$"):
        if boundary == "transport":
            asyncio.run(item.request(value, model="gpt-5.6-sol", effort="xhigh", timeout=600, stage=stage))
        else:
            request_value = dict(batch=1, subjects=["NORMAL"], payload=value)
            asyncio.run(bridge._invoke(None, stage, request_value, tmp_path / "dispatch"))
    assert not worker_calls and not model_calls
    assert (item.counts, item.total) == before
    assert not item.runtime_root.exists()
    assert not (tmp_path / "dispatch").exists()


@pytest.mark.parametrize("stage", ("CORE", "B2"))
@pytest.mark.parametrize("variant", ("whitespace", "escaped_delimiter", "ordinary_prose"))
def test_valid_prompt_framing_preserves_offline_boundary_bytes(
    bound_transport, tmp_path, stage, variant,
):
    item, worker_calls = bound_transport
    value = normal_payload(stage)
    prefix = "Offline normal prompt."
    if variant == "escaped_delimiter":
        value["input"]["note"] = "Quoted marker:\nFROZEN_CONTEXT:\nordinary text"
    elif variant == "ordinary_prose":
        prefix += " TEST_ONLY and FROZEN_CONTEXT: are ordinary prose here."
        value["input"]["note"] = "The word TEST_ONLY is not a provenance field."
    else:
        prefix += " \t\r\n"
    context_json = json.dumps(value["input"], ensure_ascii=False, sort_keys=True)
    value["prompt"] = (prefix + "\nFROZEN_CONTEXT:\n" + context_json + " \t\r\n"
                       if stage == "CORE" else prefix)
    expected = (value["prompt"] if stage == "CORE" else
                prefix + "\nFROZEN_CONTEXT:\n" + context_json + "\n").encode()
    before = deepcopy(value)
    assert transport_module.render_prompt(value, stage) == expected
    assert asyncio.run(item.request(value, model="gpt-5.6-sol", effort="xhigh", timeout=600,
                                   stage=stage)) == b"{}"
    accepted = []
    bridge = bridge_module.ProductionRuntimeBridgeV1(settings=None, sources=None,
        model=item, delivery=None, clock=None)
    session = SimpleNamespace(accept=lambda *args: accepted.append(args))
    request_value = dict(batch=1, subjects=["NORMAL"], payload=value)
    result = asyncio.run(bridge._invoke(session, stage, request_value, tmp_path / "dispatch"))
    assert result["output"] == {} and len(accepted) == 1
    assert len(worker_calls) == item.total == 2
    prompts = list(item.runtime_root.glob("*/approved-input/prompt.txt"))
    assert len(prompts) == 2 and all(path.read_bytes() == expected for path in prompts)
    assert value == before
