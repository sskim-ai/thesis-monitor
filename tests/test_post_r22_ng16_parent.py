"""Existing consumers only. No manual-purpose entitlement or model output."""
from datetime import timedelta

import pytest

from app.services.canonical_monitoring_source import prepare_monitoring_subject
from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.native_owner_session import BackendOwnerParent, ParentAdmissionManifest
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.m12dr_financial_source_authority import build_source_authority
from tests.rev8_source_fixtures import fresh_inputs
from tests.rev10_source_fixtures import wire_clock
from tests.test_native_owner_session import source as mechanical_source
from tests.test_r2b_r5_market_adapter import fixture as market_fixture, project
from tests.test_reported_business_native_projection import window
from tests.test_unified_stock_acquisition import plan as plan_fixture


def parent_for(body, generation, market, *, outer=False):
    scope = dict(run_id='ng16-synthetic-offline-parent', market=market,
        generation_id=generation, source_generation_id=body['source_generation_id'],
        snapshot_sha256=digest({'collection': body} if outer else body))
    manifest = ParentAdmissionManifest(**scope, invocations=())
    parent = BackendOwnerParent(authority_native_v2=True, **scope,
        admission_manifest=manifest, expected_manifest_sha256=digest(manifest.model_dump(mode='json')))
    return parent, scope


def construct(root, body, parent, scope, *, enabled=True):
    args = dict(authority_native_v2=True, native_owner_parent=parent, native_parent_scope=scope) if enabled else {}
    return ProductionMonitoringSession(root, market=scope['market'], generation_id=scope['generation_id'],
        source_generation_id=body['source_generation_id'], source=body, **args)


@pytest.mark.parametrize('market', ['kr', 'us'])
def test_original_owned_source_to_original_market_constructor(tmp_path, market, record_property):
    plan = plan_fixture.__wrapped__()
    generation = 'ng16-synthetic-original-market-' + market
    stocks, prepared, receipts = {}, {}, {}
    for ticker in UNIVERSE[market]:
        with wire_clock(plan.frozen_at + timedelta(seconds=4)):
            inputs = fresh_inputs(tmp_path / ticker, ticker, verified_identity=True, plan=plan)
        inputs.update(reported_comparison_business=True, source_window=window(plan))
        stock = assemble_fresh_stock(**inputs)
        assert stock['status'] == 'PASS', (ticker, stock.get('mandatory_missing'))
        authority = build_source_authority(**fresh_authority_inputs(stock, inputs))
        readiness, data = prepare_monitoring_subject(stock=stock, authority=authority,
            local_seed=inputs['technical_inputs']['local_seed'], generation=generation)
        assert readiness['status'] == 'PASS' and data['mode'] == 'EVIDENCE_BASED'
        stocks[ticker], prepared[ticker] = stock, data
        receipts[ticker] = dict(readiness=readiness, authority_sha256=digest(authority),
            stock_sha256=digest(stock), view_receipt=data['view_receipt'])
    # Issue the entire synthetic source family with one identity, not relabel
    # an already issued night acquisition and its nested receipts.
    packet, seed, graph = market_fixture(market, run=plan.run_id)
    projected = project((packet, seed, graph))
    assert projected['context']['parity_status'] == 'PASS'
    body = dict(prepared=prepared, stocks=stocks, markets={market: projected},
        source_generation_id=plan.run_id, valuation_contexts={t: {} for t in stocks},
        coverage=None, census=None)
    parent, scope = parent_for(body, generation, market)
    active = construct(tmp_path / 'active', body, parent, scope)
    off = construct(tmp_path / 'off', body, parent, scope, enabled=False)
    request = active.build('MARKET')[0]
    off_request = off.build('MARKET')[0]
    assert request['payload'] == off_request['payload']
    assert request['payload_sha256'] == off_request['payload_sha256']
    active.freeze_stage('market', [request])
    assert active.native_owner() is parent is active.native_owner()
    with pytest.raises(ValueError, match='upstream_stage_incomplete'):
        active.build('CORE')
    parent.close()
    with pytest.raises(ValueError, match='PARENT_LIFETIME_CLOSED'):
        active.freeze_stage('later', [request])
    assert not (active.sealed / 'later-request-freeze.json').exists()
    record_property('ng16_original_market', dict(market=market,
        provenance='SYNTHETIC_ORIGINAL_SOURCE_OWNERS_AND_MARKET_CONSUMER',
        source_sha256=digest(body), source_receipts=receipts,
        market_owner_receipt=projected['receipt'], request_sha256=request['payload_sha256'],
        feature_off_payload_parity=True, manual_parent_qualified=False,
        native_economic_invocations_registered=0, models_called=0,
        actual_whole_source_two_pass=False, current_22_proof=False))


@pytest.mark.parametrize('market', ['kr', 'us'])
@pytest.mark.parametrize('boundary', ['native_owner', 'build', 'capture', 'freeze', 'accept', 'b2'])
@pytest.mark.parametrize('change', ['closed', 'source', 'consumed_copy'])
def test_parent_and_actual_consumed_content_rechecked_before_side_effects(tmp_path, market, boundary, change):
    body = mechanical_source('fixture-generation', 'fixture-source', market)
    parent, scope = parent_for(body, 'fixture-generation', market)
    session = construct(tmp_path / 'session', body, parent, scope)
    if change == 'closed':
        parent.close()
        expected = 'PARENT_LIFETIME_CLOSED'
    elif change == 'source':
        session.source['valuation_contexts']['unadmitted'] = 999
        expected = 'NATIVE_SESSION_SOURCE_CONTENT_DRIFT'
    else:
        session.prepared[UNIVERSE[market][0]]['unadmitted'] = 'unsupported'
        expected = 'NATIVE_SESSION_SOURCE_CONTENT_DRIFT'
    calls = {
        'native_owner': lambda: session.native_owner(),
        'build': lambda: session.build('MARKET'),
        'capture': lambda: session.capture('market', dict(market=market, subjects=[], batch=1), {}, {}, ''),
        'freeze': lambda: session.freeze_stage('market', []),
        'accept': lambda: session.accept('MARKET', {}, {}),
        'b2': lambda: session.b2_request(UNIVERSE[market][0]),
    }
    with pytest.raises(ValueError, match=expected):
        calls[boundary]()
    assert not session.captured and not session._accepted_batches
    assert not session.root.exists()


@pytest.mark.parametrize('attribute', ['fresh_stocks', 'projected', 'gen', 'source_gen', 'market'])
def test_each_consumed_source_copy_and_identity_is_pinned(tmp_path, attribute):
    body = mechanical_source('fixture-generation', 'fixture-source', 'us')
    parent, scope = parent_for(body, 'fixture-generation', 'us')
    session = construct(tmp_path / 'session', body, parent, scope)
    if attribute in {'fresh_stocks', 'projected'}:
        getattr(session, attribute)['unadmitted'] = {}
        reason = 'SOURCE_CONTENT_DRIFT'
    else:
        setattr(session, attribute, 'changed')
        reason = 'GENERATION_MISMATCH'
    with pytest.raises(ValueError, match=reason):
        session.native_owner()
    assert not session.root.exists()


def test_outer_envelope_hash_is_not_confused_with_local_content_integrity(tmp_path):
    body = mechanical_source('fixture-generation', 'fixture-source', 'us')
    parent, scope = parent_for(body, 'fixture-generation', 'us', outer=True)
    assert scope['snapshot_sha256'] != digest(body)
    session = construct(tmp_path / 'session', body, parent, scope)
    assert session.native_owner() is parent
    assert session._native_source_content_sha256 == digest(body)
    # This tests separate hash domains, not admission of the initial source to
    # the parent's outer envelope. That producer interface remains unimplemented.
    session.source['valuation_contexts']['unadmitted'] = 123
    with pytest.raises(ValueError, match='SOURCE_CONTENT_DRIFT'):
        session.native_owner()


def test_feature_off_does_not_gain_an_ownership_capability(tmp_path):
    body = mechanical_source('fixture-generation', 'fixture-source', 'us')
    parent, scope = parent_for(body, 'fixture-generation', 'us')
    session = construct(tmp_path / 'off', body, parent, scope, enabled=False)
    assert session._native_source_content_sha256 is None
    parent.close()
    session._verify_native_source()
    with pytest.raises(ValueError, match='NATIVE_SESSION_FEATURE_DISABLED'):
        session.native_owner()


@pytest.mark.parametrize('attribute,key', [('prepared', 'prepared'), ('fresh_stocks', 'stocks'), ('projected', 'markets')])
@pytest.mark.parametrize('original,changed', [(1, True), (100, 100.0)])
def test_equal_value_with_different_type_is_still_content_drift(tmp_path, attribute, key, original, changed):
    body = mechanical_source('fixture-generation', 'fixture-source', 'us')
    first = next(iter(body[key]))
    body[key][first]['synthetic_type_probe'] = original
    if key == 'stocks':
        body['prepared'][first]['view_receipt']['raw_source_sha256'] = digest(body[key][first])
    parent, scope = parent_for(body, 'fixture-generation', 'us')
    session = construct(tmp_path / 'session', body, parent, scope)
    getattr(session, attribute)[first]['synthetic_type_probe'] = changed
    assert getattr(session, attribute) == session.source[key]
    with pytest.raises(ValueError, match='NATIVE_SESSION_SOURCE_CONTENT_DRIFT'):
        session.native_owner()
    assert not session.root.exists()
