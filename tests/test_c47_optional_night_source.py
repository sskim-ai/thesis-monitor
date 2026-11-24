"""Precollection exclusion boundaries; synthetic plans/inputs, no live acquisition."""
from datetime import datetime, timedelta
import json
import socket
from types import SimpleNamespace

import pytest

from app.services.canonical_source_replay import publication_inputs
from app.services.production_source_context import credential_binding
from app.services.selected_source_composition import (
    SelectedSourceRunBinding, code_fingerprints, raw_owner_binding, validate_composition,
)
from app.services.selected_source_plan import (
    SelectedConsumerPolicy, SelectedStockPlan, SCOPE, US_NIGHT_EXCLUDED,
    compile_selected_plan, request_budget, us_night_excluded,
)
from app.services.unified_snapshot_contract import digest
from tests.test_c22ab_selected_source import compile_market
from tests.test_c22ac_selected_whole import binding


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C47_NO_LIVE_IO')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def compiled(excluded=True):
    _, args, _ = compile_market('us', 'NEWX')
    args['identities']['NEWX']['updated_at'] = args['stock'].frozen_at.isoformat()
    args['selected_consumer_policy'] = SelectedConsumerPolicy(
        us_night=US_NIGHT_EXCLUDED if excluded else 'ORIGINAL_CURRENT_PROBE_ONLY')
    if excluded:
        args['config_identities'].pop('krx_night_futures')
    result = compile_selected_plan(compiler_args=args)
    frozen = dict(**{k:v for k,v in result.items() if k != 'plan'},
        scope=SCOPE, selected_market='us', generation_id=args['stock'].run_id,
        frozen_at=args['stock'].frozen_at.isoformat(), plan=result['plan'].model_dump(mode='json'))
    return result, args, frozen


def test_exclusion_removes_only_night_requests_and_unused_credential_requirement():
    included, _, _ = compiled(False)
    excluded, _, frozen = compiled()
    before, after = included['plan'], excluded['plan']
    assert len(included['candidate']['night_query_dates']) == 7
    assert excluded['candidate']['night_query_dates'] == [] and us_night_excluded(frozen)
    assert not any(d.provider == 'krx_night_futures' for d in after.descriptors)
    assert [d for d in before.descriptors if d.provider != 'krx_night_futures'] == list(after.descriptors)
    assert request_budget(included)['total'] - request_budget(excluded)['total'] == 7
    _, kr_args, kis = compile_market('kr', '123456')
    kr_args['selected_consumer_policy'] = SelectedConsumerPolicy()
    assert compile_selected_plan(compiler_args=kr_args, kis_plan=kis)['candidate']['night_query_dates'] == []
    kr_args['selected_consumer_policy'] = SelectedConsumerPolicy(us_night=US_NIGHT_EXCLUDED)
    with pytest.raises(ValueError, match='exclusion_us_only'):
        compile_selected_plan(compiler_args=kr_args, kis_plan=kis)


def test_optional_krx_key_does_not_make_other_credentials_optional():
    settings = SimpleNamespace(**{key:'synthetic' for key in (
        'kiwoom_app_key', 'kiwoom_secret_key', 'sec_user_agent', 'opendart_api_key',
        'fred_api_key', 'eia_api_key', 'ecos_api_key', 'krx_open_api_key',
        'naver_client_id', 'naver_client_secret', 'finnhub_api_key')})
    settings.krx_open_api_key = ''
    policy = SelectedConsumerPolicy(us_night=US_NIGHT_EXCLUDED)
    assert 'krx_night_futures' not in credential_binding(settings, 'us', consumer_policy=policy)
    with pytest.raises(ValueError, match='credential_missing'):
        credential_binding(settings, 'us', consumer_policy=SelectedConsumerPolicy())
    settings.sec_user_agent = ''
    with pytest.raises(ValueError, match='credential_missing'):
        credential_binding(settings, 'us', consumer_policy=policy)


def captured_publications(root, frozen):
    phases = {}
    for provider in ('fred', 'eia', 'ecos'):
        phases[provider] = dict(status='CAPTURED_NOT_QUALIFIED', value={'observations':[]})
        (root / ('phase-' + provider + '.json')).write_text(json.dumps(phases[provider]))
    # This test covers capture composition only; empty provider fixtures are not
    # qualified macro data and do not issue an accepted Source owner.
    return dict(phases=phases, completed_at=(
        datetime.fromisoformat(frozen['frozen_at']) + timedelta(seconds=1)).isoformat())


def test_publication_composition_omits_only_explicitly_excluded_night(tmp_path):
    _, _, frozen = compiled()
    outcome = captured_publications(tmp_path, frozen)
    result = publication_inputs(tmp_path, frozen, outcome, None)
    assert result['night'] is None
    assert set(result['publications']['providers']) == {'fred','eia','ecos'}
    assert result['publications']['market_scope'] == 'SELECTED_US'
    _, _, included = compiled(False)
    with pytest.raises(ValueError, match='SOURCE_PREREQUISITE_NOT_CAPTURED:night'):
        publication_inputs(tmp_path, included, outcome, None)
    outcome['phases'].pop('fred')
    with pytest.raises(ValueError, match='SOURCE_PREREQUISITE_NOT_CAPTURED:fred'):
        publication_inputs(tmp_path, frozen, outcome, None)


@pytest.mark.parametrize('change', ['dates', 'slot', 'scope', 'captured'])
def test_exclusion_rejects_existing_night_requests_or_collected_value(tmp_path, change):
    _, _, frozen = compiled()
    outcome = captured_publications(tmp_path, frozen)
    if change == 'dates':
        frozen['candidate']['night_query_dates'] = ['2026-11-11']
    elif change == 'slot':
        included, _, _ = compiled(False)
        frozen['plan']['descriptors'].append(next(d.model_dump(mode='json')
            for d in included['plan'].descriptors if d.provider == 'krx_night_futures'))
    elif change == 'scope':
        frozen['selected_market'] = 'kr'
    else:
        outcome['phases']['night'] = dict(status='FAILED', error_class='ValueError')
    with pytest.raises(ValueError, match='selected_us_.*night'):
        publication_inputs(tmp_path, frozen, outcome, None)


def test_selected_binding_requires_explicit_policy_for_none_and_keeps_default_wire():
    _, args, _ = compiled()
    raw = args['stock'].model_dump(mode='json')
    raw.update(planning_only=False, owner_files={'fixture.py':'0'*64}, owner_head='0'*40,
        settings_sha256='0'*64, request_environment_sha256='0'*64)
    stock = SelectedStockPlan.model_validate(raw)
    item = dict(technical_inputs=dict(plan=stock, receipts={'fixture':'synthetic'}),
        financial_inputs=dict(plan=dict(run_id=stock.run_id, cutoff=stock.frozen_at.isoformat(),
            security=args['identities']['NEWX']), receipts=[]))
    seed = binding(parent_run_id=stock.run_id, child_id=stock.run_id,
        raw_owner_bindings={'NEWX':raw_owner_binding(item)}, us_night_policy=US_NIGHT_EXCLUDED,
        run_acquisitions={'stock':digest('stock'), 'night':digest(None)},
        night_publication_receipt_sha256=digest(None))
    wire = seed.model_dump(mode='json')
    assert SelectedSourceRunBinding.model_validate(wire).sha256 == seed.sha256
    assert wire['us_night_policy'] == US_NIGHT_EXCLUDED
    assert 'us_night_policy' not in binding().model_dump(mode='json')
    meta = dict(selected_code_fingerprints=code_fingerprints(),
        selected_request_plan_sha256=seed.request_plan_sha256,
        selected_registration_receipt_sha256=seed.registration_receipt_sha256)
    kwargs = dict(stock_inputs={'NEWX':{'fresh_financial_binding':item}},
        market_inputs={'us':{'native_aggregate':dict(run_id=stock.run_id,
            role=SimpleNamespace(market='us', session=seed.target_session))}},
        composition_metadata=meta, fresh_context_inputs=dict(
            publications={'market_scope':'SELECTED_US'}, night=None))
    assert validate_composition(seed, **kwargs) == seed
    absent_policy = {k:v for k,v in wire.items() if k != 'us_night_policy'}
    with pytest.raises(ValueError, match='context_or_code_scope'):
        validate_composition(absent_policy, **kwargs)
    kwargs['fresh_context_inputs']['night'] = {'old':'observation'}
    with pytest.raises(ValueError, match='context_or_code_scope'):
        validate_composition(seed, **kwargs)
    with pytest.raises(ValueError, match='exclusion_binding'):
        SelectedSourceRunBinding.model_validate(dict(wire, night_publication_receipt_sha256=digest('old')))


def test_actual_registered_cycle_freezes_exclusion_before_any_financial_dispatch(tmp_path, monkeypatch):
    from app.jobs import unified_market_snapshot as job
    from tests.test_local_launchd_entry import original_cycle_probe
    from tests.test_manual_source_budget import offline_only
    offline_only.__wrapped__(monkeypatch, tmp_path)
    # This connection test uses a bounded synthetic DB and a healthy synthetic
    # volume; the unchanged production capacity policy is not under test.
    monkeypatch.setattr('app.services.research_artifact_budget.os.statvfs',
        lambda path:SimpleNamespace(f_bavail=32*1024**3, f_frsize=1))
    runtime = tmp_path/'model-runtime'
    runtime.mkdir(mode=0o700)
    monkeypatch.setattr(job, '_local_model_runtime', lambda execution:runtime)
    result = original_cycle_probe(tmp_path, 'us', monkeypatch,
        config_overrides={'us_night_policy':US_NIGHT_EXCLUDED})
    frozen = json.loads((tmp_path/'source/production-frozen-source-plan.json').read_bytes())
    assert us_night_excluded(frozen)
    assert 'krx_night_futures' not in frozen['config_identities']
    assert result['financial_HTTP'] == result['models'] == 0
    assert len(frozen['plan']['subjects']) == 14
