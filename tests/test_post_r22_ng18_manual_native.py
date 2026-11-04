"""Original synthetic source and Market boundaries; no current/live grant."""
from copy import deepcopy
from datetime import timedelta

import pytest

from app.services.canonical_native_source_owner import (
    CanonicalPreparedSourceOwner, prepare_owned_monitoring_source,
)
from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.manual_native_owner import BackendManualNativeParent, issue_manual_native_parents
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.m12dr_financial_source_authority import build_source_authority
from scripts.r2b_r5_market_adapter import project_sealed_market_context
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_r2b_r5_market_adapter import fixture as market_fixture
from tests.test_reported_business_native_projection import window
from tests.test_unified_stock_acquisition import plan as plan_fixture


def original_source_args(root):
    plan = plan_fixture.__wrapped__()
    stocks, authorities, local = {}, {}, {}
    for market, tickers in UNIVERSE.items():
        stocks[market] = {}
        for ticker in tickers:
            with wire_clock(plan.frozen_at + timedelta(seconds=4)):
                inputs = fresh_inputs(root / ticker, ticker, verified_identity=True, plan=plan)
            inputs.update(reported_comparison_business=True, source_window=window(plan))
            stock = assemble_fresh_stock(**inputs)
            assert stock["status"] == "PASS", (ticker, stock.get("mandatory_missing"))
            authorities[ticker] = build_source_authority(**fresh_authority_inputs(stock, inputs))
            stocks[market][ticker] = stock
            local[ticker] = inputs["technical_inputs"]["local_seed"]
    parts = {m: market_fixture(m, run=plan.run_id) for m in UNIVERSE}
    seed = deepcopy(parts["kr"][1])
    for key in ("attempts", "attempt_hashes"):
        seed[key].update(parts["us"][1][key])
    graph = deepcopy(parts["kr"][2])
    graph["markets"].update(parts["us"][2]["markets"])
    graph["stocks"] = authorities
    graph["run_seed_sha256"] = digest(seed)
    packets = {}
    for market in UNIVERSE:
        packets[market] = {**parts[market][0], "stocks": stocks[market],
            "run_seed_sha256": digest(seed), "authority_graph_sha256": digest(graph)}
    whole = dict(packets=packets, seed=seed, authority_graph=graph,
                 authority_graph_sha256=digest(graph))
    return dict(whole=whole, local_seeds=local,
        valuation_contexts={t: {} for ts in UNIVERSE.values() for t in ts},
        generation="ng18-synthetic-original-source", coverage=None, census=None,
        market_projector=project_sealed_market_context)


@pytest.fixture(scope="module")
def original_source(tmp_path_factory):
    args = original_source_args(tmp_path_factory.mktemp("ng18-original-source"))
    source, owner = prepare_owned_monitoring_source(enabled=True, **args)
    yield source, owner, args
    owner.close()


@pytest.mark.parametrize("market", ["kr", "us"])
def test_original_source_market_accepts_but_not_native_without_economic_owner(
        original_source, tmp_path, market, record_property):
    source, owner, args = original_source
    scoped = owner.source(market)
    relationship = owner.relationship(market)
    assert relationship["outer_source_envelope_sha256"] == digest(args["whole"])
    assert relationship["inner_consumed_source_sha256"] == digest(scoped)
    assert relationship["outer_source_envelope_sha256"] != digest(scoped)
    session = ProductionMonitoringSession(tmp_path / market, market=market,
        generation_id=args["generation"], source_generation_id=source["source_generation_id"],
        source=scoped, manual_native_v1=True, manual_source_owner=owner)
    request = session.build("MARKET")[0]
    session.freeze_stage("market", [request])
    context = request["payload"]["input"]
    output = dict(market=market.upper(), regime="DATA_INSUFFICIENT", confidence="LOW",
        breadth_state="Synthetic scope probe.", leadership="No investment conclusion.",
        flows_or_participation="No investment conclusion.",
        rates_or_macro_context="No investment conclusion.",
        supporting_refs=list(context["facts"])[:1], contradicting_refs=[])
    session.accept("MARKET", request, output)
    assert ("MARKET", 1) in session._accepted_batches
    from app.services.manual_native_owner import original_market_acceptance
    acceptance = original_market_acceptance(session)
    assert acceptance["request_sha256"] == digest(request)
    session.captured["MARKET"][0]["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="original_market_acceptance_drift"):
        original_market_acceptance(session)
    session.captured["MARKET"] = [deepcopy(request)]
    session._accepted_batches.remove(("MARKET", 1))
    with pytest.raises(ValueError, match="original_market_acceptance_drift"):
        original_market_acceptance(session)
    session._accepted_batches.add(("MARKET", 1))
    assert original_market_acceptance(session) == acceptance
    with pytest.raises(ValueError, match="MANUAL_NATIVE_ADMISSION_REQUIRED_BEFORE_CORE"):
        session.build("CORE")
    with pytest.raises(ValueError, match="MANUAL_NATIVE_ECONOMIC_CONSUMER_CONTRACT_PENDING"):
        session.capture("core", {}, {}, {}, "")
    with pytest.raises(ValueError, match="MANUAL_NATIVE_ECONOMIC_CONSUMER_CONTRACT_PENDING"):
        session.freeze_stage("core", [])
    with pytest.raises(ValueError, match="MANUAL_NATIVE_ECONOMIC_CONSUMER_CONTRACT_PENDING"):
        session.accept("CORE", {}, {})
    with pytest.raises(ValueError, match="MANUAL_NATIVE_B2_COVERAGE_CENSUS_NOT_AUTHORIZED"):
        session.b2_request(UNIVERSE[market][0])
    from app.services.canonical_native_admission import CanonicalToNativeAdmissionProducer, CanonicalNativeGap
    producer = CanonicalToNativeAdmissionProducer(owner)
    gaps = {t: producer.produce(t, request_id="synthetic:" + t) for t in UNIVERSE[market]}
    assert all(isinstance(row, CanonicalNativeGap) for row in gaps.values())
    assert session._native_owner_parent is None and "CORE" not in session.captured
    record_property("ng18_source_market_boundary", dict(
        provenance="SYNTHETIC_ORIGINAL_SOURCE_AND_MARKET_CONSUMER",
        market=market, subjects=len(gaps), relationship=relationship,
        market_request_sha256=request["payload_sha256"], market_accepted=True,
        native_parent_issued=False, economic_qualification=False, live_models=0,
        gaps={t: r.model_dump(mode="json") for t, r in gaps.items()}))


@pytest.mark.parametrize("enabled", [False, None, 1, "true"])
def test_source_feature_default_off_before_source_reads(enabled):
    with pytest.raises(ValueError, match="source_feature_disabled"):
        prepare_owned_monitoring_source(enabled=enabled, whole=None)


@pytest.mark.parametrize("kind", [CanonicalPreparedSourceOwner, BackendManualNativeParent])
def test_public_construction_and_unissued_handle_are_not_authority(kind):
    with pytest.raises(ValueError, match="backend_issuance_required"):
        kind()
    forged = object.__new__(kind)
    with pytest.raises(ValueError, match="live_.*required"):
        forged._record()


def test_manual_parent_rejects_caller_manifest_without_source_session():
    with pytest.raises(ValueError, match="source_session_required"):
        issue_manual_native_parents({"status": "PASS", "execution_purpose": "MANUAL_SHADOW_UNSENT"}, {})


@pytest.mark.parametrize("change", ["stock", "prepared", "market", "source_generation"])
def test_original_consumer_rejects_rehashed_source_substitution(original_source, tmp_path, change):
    source, owner, args = original_source
    scoped = owner.source("us")
    if change == "stock":
        scoped["stocks"][UNIVERSE["us"][0]]["fresh_run_id"] = "other"
    elif change == "prepared":
        scoped["prepared"][UNIVERSE["us"][0]]["mode"] = "UNKNOWN_LIMIT"
    elif change == "market":
        scoped["markets"]["us"]["context"]["market"] = "KR"
    else:
        scoped["source_generation_id"] = "other"
    with pytest.raises(ValueError, match="MANUAL_SOURCE_EXTRACTION_MISMATCH"):
        ProductionMonitoringSession(tmp_path, market="us", generation_id=args["generation"],
            source_generation_id=source["source_generation_id"], source=scoped,
            manual_native_v1=True, manual_source_owner=owner)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("ticker", ["NVDA", "035420", "UNREGISTERED"])
def test_source_membership_does_not_enroll_new_tickers(original_source, ticker):
    with pytest.raises(ValueError, match="subject_not_owned"):
        original_source[1].resolve_subject(ticker)


def test_outer_or_inner_hash_json_is_not_live_source_authority(original_source):
    from app.services.canonical_native_admission import CanonicalToNativeAdmissionProducer
    with pytest.raises(ValueError):
        CanonicalToNativeAdmissionProducer(original_source[1].relationship("us"))


def test_prepared_owner_returns_copies_and_preserves_generation(original_source):
    source, owner, args = original_source
    one = owner.resolve_subject(UNIVERSE["kr"][0])
    one["stock"]["ticker"] = "changed"
    assert owner.resolve_subject(UNIVERSE["kr"][0])["stock"]["ticker"] == UNIVERSE["kr"][0]
    assert owner.source()["source_generation_id"] == source["source_generation_id"]
    assert owner.relationship("us")["generation_id"] == args["generation"]


@pytest.mark.parametrize("attribute", ["gen", "source_gen"])
def test_prepared_only_generation_mutation_denied_before_market(original_source, tmp_path, attribute):
    source, owner, args = original_source
    session = ProductionMonitoringSession(tmp_path / "changed", market="us",
        generation_id=args["generation"], source_generation_id=source["source_generation_id"],
        source=owner.source("us"), manual_native_v1=True, manual_source_owner=owner)
    setattr(session, attribute, "substituted-generation")
    with pytest.raises(ValueError, match="MANUAL_SOURCE_GENERATION_MISMATCH"):
        session.build("MARKET")
    assert not session.root.exists()
