"""Original consumer qualification on synthetic data, not a live cohort proof."""
from copy import deepcopy
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.services.canonical_monitoring_source import prepare_monitoring_subject
from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.native_economic_core import InvocationSpec
from app.services.native_owner_session import BackendOwnerParent, ParentAdmissionManifest
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.prospective_class_c_owner import SCOPE
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.m12dr_financial_source_authority import build_source_authority
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_r2b_r5_market_adapter import fixture as market_fixture, project
from tests.test_reported_business_native_projection import window
from tests.test_unified_stock_acquisition import plan as plan_fixture


@pytest.fixture(scope="module")
def qualified_source(tmp_path_factory):
    root = tmp_path_factory.mktemp("ng15-canonical-source")
    plan = plan_fixture.__wrapped__()
    generation = "ng15-synthetic-original-native-market"
    stocks, prepared, receipts = {}, {}, {}
    for ticker in UNIVERSE["kr"]:
        with wire_clock(plan.frozen_at + timedelta(seconds=4)):
            inputs = fresh_inputs(root / ticker, ticker, verified_identity=True, plan=plan)
        inputs.update(reported_comparison_business=True, source_window=window(plan))
        stock = assemble_fresh_stock(**inputs)
        assert stock["status"] == "PASS", (ticker, stock.get("mandatory_missing"))
        authority = build_source_authority(**fresh_authority_inputs(stock, inputs))
        readiness, data = prepare_monitoring_subject(stock=stock, authority=authority,
            local_seed=inputs["technical_inputs"]["local_seed"], generation=generation)
        assert readiness["status"] == "PASS" and data["mode"] == "EVIDENCE_BASED"
        stocks[ticker], prepared[ticker] = stock, data
        receipts[ticker] = dict(readiness=readiness, authority_sha256=digest(authority),
            source_sha256=digest(stock), view_receipt=data["view_receipt"])
    # Construct one synthetic generation before invoking the original owners;
    # these are newly generated fixture records, never relabelled real receipts.
    packet, seed, graph = market_fixture("kr")
    source = graph["markets"]["kr"]
    source["run_id"] = seed["parent_run_id"] = plan.run_id
    source["attempt_id"] = seed["attempts"]["kr"] = plan.run_id + ":kr"
    seed["attempt_hashes"]["kr"] = digest(source)
    graph["run_seed_sha256"] = digest(seed)
    packet.update(market_sources=deepcopy(source), run_seed_sha256=digest(seed),
                  authority_graph_sha256=digest(graph))
    market = project((packet, seed, graph))
    assert market["context"]["parity_status"] == "PASS"
    body = dict(prepared=prepared, stocks=stocks, markets={"kr": market},
        source_generation_id=plan.run_id, valuation_contexts={t: {} for t in stocks},
        coverage=None, census=None)
    return body, generation, receipts


def parent_for(body, generation):
    scope = dict(run_id="ng15-synthetic-parent", market="kr", generation_id=generation,
        source_generation_id=body["source_generation_id"], snapshot_sha256=digest(body))
    manifest = ParentAdmissionManifest(**scope, invocations=())
    parent = BackendOwnerParent(authority_native_v2=True, **scope,
        admission_manifest=manifest, expected_manifest_sha256=digest(manifest.model_dump(mode="json")))
    return parent, scope


def construct(root, body, parent, scope):
    return ProductionMonitoringSession(root, market="kr", generation_id=scope["generation_id"],
        source_generation_id=body["source_generation_id"], source=body, authority_native_v2=True,
        native_owner_parent=parent, native_parent_scope=scope)


def test_original_prepared_native_parent_and_market_request(qualified_source, tmp_path, record_property):
    body, generation, receipts = qualified_source
    parent, scope = parent_for(body, generation)
    session = construct(tmp_path / "session", body, parent, scope)
    assert session.native_owner() is parent
    requests = session.build("MARKET")
    assert len(requests) == 1 and requests[0]["stage"] == "market"
    request = requests[0]
    assert request["payload"]["input"] == body["markets"]["kr"]["context"]
    assert request["payload_sha256"] == digest(request["payload"])
    assert request["execution_generation_id"] == generation
    session.freeze_stage("market", requests)
    assert session.stage_manifests["market"]
    with pytest.raises(ValueError, match="upstream_stage_incomplete"):
        session.build("CORE")
    parent.close()
    with pytest.raises(ValueError, match="PARENT_LIFETIME_CLOSED"):
        session.native_owner()
    record_property("ng15_native_parent_proof", dict(
        provenance="SYNTHETIC_ORIGINAL_OWNER_AND_CONSUMER_ONLY", market="kr",
        native_preflight=receipts, source_sha256=digest(body), scope=scope,
        market_projection_receipt=body["markets"]["kr"]["receipt"],
        market_request_sha256=request["payload_sha256"],
        full22_current_proof=False, market_model_called=False, manual_shadow_supported=False,
        production_session_valuation_not_exercised=True, b2_not_exercised=True,
        native_invocations_registered=0, source_and_market_generation=body["source_generation_id"],
        full_source_composition_not_exercised=True))


@pytest.mark.parametrize("case,reason", [
    ("missing", "BACKEND_PARENT_CAPABILITY_REQUIRED"),
    ("source_generation", "NATIVE_SESSION_GENERATION_MISMATCH"),
    ("snapshot", "PARENT_SESSION_SCOPE_MISMATCH"),
    ("run", "PARENT_SESSION_SCOPE_MISMATCH"),
    ("closed", "PARENT_LIFETIME_CLOSED"),
    ("cohort", "production_monitoring_current_cohort_gap"),
    ("unqualified", "production_monitoring_subject_authority_gap"),
])
def test_original_parent_boundary_rejections(qualified_source, tmp_path, case, reason):
    original, generation, _ = qualified_source
    body = deepcopy(original)
    parent, scope = parent_for(body, generation)
    if case == "missing":
        parent = None
    elif case == "source_generation":
        scope["source_generation_id"] = "another-source"
    elif case == "snapshot":
        scope["snapshot_sha256"] = "0" * 64
    elif case == "run":
        scope["run_id"] = "another-run"
    elif case == "closed":
        parent.close()
    elif case == "cohort":
        body["prepared"].pop(next(iter(body["prepared"])))
    elif case == "unqualified":
        body["prepared"][next(iter(body["prepared"]))]["mode"] = "UNKNOWN_LIMIT"
    with pytest.raises(ValueError, match=reason):
        construct(tmp_path / "denied", body, parent, scope)
    assert not (tmp_path / "denied").exists()


def test_absent_market_context_cannot_construct_request(qualified_source, tmp_path):
    original, generation, _ = qualified_source
    body = deepcopy(original)
    body["markets"]["kr"] = {}
    parent, scope = parent_for(body, generation)
    session = construct(tmp_path / "missing-market", body, parent, scope)
    with pytest.raises(KeyError, match="context"):
        session.build("MARKET")
    assert not session.captured and not (tmp_path / "missing-market").exists()


def test_manual_shadow_is_not_an_existing_native_invocation_mode():
    with pytest.raises(ValidationError) as error:
        InvocationSpec(execution_purpose=SCOPE)
    issue = next(e for e in error.value.errors() if e["loc"] == ("execution_purpose",))
    assert issue["type"] == "literal_error"
    assert "OFFLINE_CONTRACT_REPROOF" in issue["ctx"]["expected"]


def test_market_owner_rejects_changed_authority_before_session_construction():
    packet, seed, graph = market_fixture("kr")
    packet["authority_graph_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="market_identity_mismatch"):
        project((packet, seed, graph))
