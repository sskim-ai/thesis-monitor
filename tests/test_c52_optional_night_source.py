"""C52 optional night: actual sealed attempts -> Source absence -> real renderer."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import socket
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.jobs.probe_krx_night_futures import fetch_live_probe
from app.services.canonical_source_acquisition import PublicationCapture
from app.services.canonical_source_replay import publication_inputs
from app.services.optional_night_source import collect_optional, FAILURE, replay_failure
from app.services.production_source_context import POLICY
from app.services.production_source_seal import slot_dispositions
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.selected_source_plan import SCOPE, SelectedConsumerPolicy, US_NIGHT_OPTIONAL, us_night_optional
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_sealed_context import replay_night
from app.services.unified_snapshot_contract import digest
from tests.test_c47_optional_night_market import parts, project, reseal, decision
from tests.test_c47_optional_night_source import captured_publications
from tests.test_c52_night_runtime import setup_case, execute, enter_model_budget


@pytest.fixture(autouse=True)
def no_live_io(monkeypatch):
    def denied(*args, **kwargs): raise AssertionError('C52_SOURCE_NO_REAL_NETWORK')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def frozen_for(run):
    day = run.plan.frozen_at.astimezone(ZoneInfo('Asia/Seoul')).date()
    repo = run.root.parent/'synthetic-native-owner'
    owner = repo/'app/providers/kiwoom.py'
    owner.parent.mkdir(parents=True, exist_ok=True)
    owner.write_bytes(b'# synthetic native owner; no implementation invoked\n')
    return dict(scope=SCOPE, selected_market='us', generation_id=run.plan.generation_id,
        frozen_at=run.plan.frozen_at.isoformat(), query_kst_date=day.isoformat(),
        plan=run.plan.model_dump(mode='json'), stock_plan={'reads':[]},
        native_owner_root=str(repo), native_owner={'owner_files':{
            'app/providers/kiwoom.py':sha256_bytes(owner.read_bytes())}},
        candidate=dict(selected_market='us',
            night_query_dates=[(day-timedelta(days=i)).isoformat() for i in range(7)],
            consumer_policy=SelectedConsumerPolicy(us_night=US_NIGHT_OPTIONAL).model_dump(mode='json')))


def capture_failure(tmp_path, kind):
    run, ledger, _, fred = setup_case(tmp_path)
    run.secrets = ('synthetic',)
    frozen = frozen_for(run)
    calls = []
    def respond(request):
        calls.append(request)
        if kind == 'transport': raise httpx.ReadTimeout('synthetic', request=request)
        if kind == 'http503': return httpx.Response(503, content=b'unavailable', request=request)
        if kind == 'empty200': return httpx.Response(200, content=b'', request=request)
        return httpx.Response(200, content=b'{broken', request=request)
    capture = PublicationCapture(SealedSourceTransport(run, httpx.MockTransport(respond),
        providers={'krx_night_futures'}), 'krx_night_futures', run.plan.generation_id, tmp_path/'night/probe')
    async def action():
        at = run.plan.frozen_at
        return await fetch_live_probe(run_date=at.astimezone(ZoneInfo('Asia/Seoul')).date(),
            observation_time=at, api_key='synthetic', transport=capture, hard_stop_on_error=True)
    value = asyncio.run(collect_optional(action, frozen=frozen, results=run.results, run_ledger=ledger))
    outcome = captured_publications(tmp_path, frozen)
    outcome.update(logical_results=deepcopy(run.results),
        completed_at=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat())
    phase = dict(status='CAPTURED_NOT_QUALIFIED', value=value)
    outcome['phases']['night'] = phase
    (tmp_path/'phase-night.json').write_text(json.dumps(phase))
    return run, ledger, fred, frozen, outcome, calls


@pytest.mark.parametrize('kind', ['http503','transport','bad_json','empty200'])
def test_real_optional_error_becomes_replayable_unavailable_and_other_stages_continue(tmp_path, kind):
    run, ledger, fred, frozen, outcome, calls = capture_failure(tmp_path, kind)
    assert len(calls) == 1 and us_night_optional(frozen)
    inputs = publication_inputs(tmp_path, frozen, outcome, POLICY)
    proof = replay_night(**inputs['night'])
    assert proof['value']['observations'] == [] and proof['network_calls'] == 0
    expected = 'UNAVAILABLE_COLLECTION_ERROR' if kind in {'http503','transport'} else 'UNAVAILABLE_INVALID_DATA'
    assert proof['value']['optional_night_failure']['state'] == expected
    assert len(proof['original_receipts']) == 1
    disposition = slot_dispositions(tmp_path, frozen, outcome)
    night_rows = [r for r in disposition['rows'] if r['role'].startswith('night:')]
    assert len(night_rows) == 7 and all(not r['mandatory'] for r in night_rows)
    assert all(r['disposition'] != 'MISSING_REQUIRED_ATTEMPT' for r in night_rows)
    # Unrelated mandatory inputs were intentionally not acquired in this fixture.
    # Their original coverage checks remain active.
    assert disposition['status'] == 'FAIL'
    assert any(r['mandatory'] and r['disposition'] == 'MISSING_REQUIRED_ATTEMPT'
        for r in disposition['rows'])
    assert execute(run, fred, lambda r:httpx.Response(200, json={}, request=r))['status'] == 'PASS'
    enter_model_budget(ledger)
    assert ledger.state()['model_total'] == 1


def failure_market(state):
    packet, seed, graph = parts()
    at = datetime.fromisoformat(graph['night']['observed_at'])
    day = at.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat()
    key = 'night:KOSPI200:'+day
    artifact = 'synthetic-night-error.body'
    body = b'unavailable'
    hashes = {artifact:sha256_bytes(body)}
    receipt_sha = digest('synthetic-original-final')
    value = dict(provider='krx_night_futures', observations=[], optional_night_failure=dict(
        contract=FAILURE, policy=US_NIGHT_OPTIONAL, state=state, code='NIGHT_COLLECTION_FAILED',
        observed_at=at.isoformat(), error_class='SyntheticError', application_frame=None,
        attempted_logical_ids=[key], final_receipt_sha256=[receipt_sha]))
    receipt = dict(run_id=seed['parent_run_id'], acquisition_id=seed['parent_run_id']+':night',
        provider='krx_night_futures', sealed_logical_id=key, sealed_final_receipt_sha256=receipt_sha,
        request=dict(method='GET', route='https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd',
            params={'basDd':day.replace('-','')}), outcome='HTTP_RESPONSE', http_status=503,
        artifact=artifact, artifact_sha256=hashes[artifact], requested_at=at.isoformat(),
        received_at=(at+timedelta(seconds=1)).isoformat())
    night = replay_failure(value=value, receipts=[receipt], bodies={artifact:body}, body_hashes=hashes,
        observed_at=at, run_id=seed['parent_run_id'], acquisition_id=seed['parent_run_id']+':night',
        expected_value_sha256=digest(value), run_started_at=at, acquisition_cutoff=at+timedelta(seconds=2))
    seed['us_night_policy'] = US_NIGHT_OPTIONAL
    seed['run_acquisitions']['night'] = digest(value)
    seed['night_publication_receipt_sha256'] = digest(dict(probe=[receipt],history=[]))
    graph['night'] = packet['night_and_publication_context'] = night
    reseal(packet, seed, graph)
    return packet, seed, graph


@pytest.mark.parametrize('state,notice', [
    ('UNAVAILABLE_COLLECTION_ERROR','수집 오류'), ('UNAVAILABLE_INVALID_DATA','자료 처리 오류')])
def test_optional_failure_reaches_actual_market_renderer_with_no_fabricated_night_direction(state, notice):
    from app.services import production_message_renderer as renderer
    from scripts import m12ds_r4_r4_market as consumer
    data = failure_market(state)
    projected = project(data)
    context = projected['context']
    source = projected['packet']['market_context']
    assert source['night_futures'] == []
    assert context['korean_night_futures']['state'] == state
    assert not any(f['fact_type'].startswith('night_futures') for f in source['fact_catalog'])
    output = decision(context)
    assert consumer.validate_market(output, context)['status'] == 'PASS'
    message = renderer.market_message(SimpleNamespace(market='us', gen='C52-synthetic',
        projected={'us':projected}, markets={'us':output}, fresh_stocks={}))
    assert message['message_id'] == 'MARKET_US' and notice in message['text'] and 'SPY' in message['text']
    output['rates_or_macro_context'] = '한국 야간선물 상승은 위험 선호를 뒷받침합니다.'
    assert consumer.validate_market(output, context)['status'] == 'FAIL'


@pytest.mark.parametrize('change', ['body','policy','missing_phase'])
def test_absence_keeps_original_source_binding_checks(tmp_path, change):
    run, ledger, fred, frozen, outcome, _ = capture_failure(tmp_path, 'http503')
    if change == 'body':
        path = run.root/next(iter(run.results.values()))['attempts'][0]['artifact']
        path.write_bytes(b'changed')
    elif change == 'policy':
        frozen['candidate']['consumer_policy']['us_night'] = 'ORIGINAL_CURRENT_PROBE_ONLY'
    else:
        outcome['phases'].pop('night')
    with pytest.raises((ValueError,OSError)):
        publication_inputs(tmp_path, frozen, outcome, POLICY)


def test_optional_policy_is_us_only_bounded_and_explicit():
    from tests.test_c22ab_selected_source import compile_market
    from app.services.selected_source_plan import compile_selected_plan
    _, args, kis = compile_market('kr','123456')
    args['selected_consumer_policy'] = SelectedConsumerPolicy(us_night=US_NIGHT_OPTIONAL)
    with pytest.raises(ValueError, match='us_only'):
        compile_selected_plan(compiler_args=args, kis_plan=kis)


def test_global_stop_and_external_cancel_are_never_optional_missing_data(tmp_path):
    from app.services.bounded_financial_acquisition import SystemicStop
    from app.services.research_artifact_budget import ArtifactCapacityError
    run, ledger, _, _ = setup_case(tmp_path)
    frozen = frozen_for(run)
    capacity = ArtifactCapacityError(code='SYNTHETIC_CAP', role='source', current=1, projected=2, cap=1)
    for exc in (SystemicStop('global_stop'), capacity, OSError('disk'), asyncio.CancelledError()):
        async def action(): raise exc
        with pytest.raises(type(exc)):
            asyncio.run(collect_optional(action, frozen=frozen, results=run.results, run_ledger=ledger))
    ledger.stop('SYNTHETIC_BUDGET_STOP')
    async def stopped(): raise ValueError('budget')
    with pytest.raises(ValueError, match='budget'):
        asyncio.run(collect_optional(stopped, frozen=frozen, results=run.results, run_ledger=ledger))


def test_publication_capacity_error_after_http_keeps_original_error(tmp_path, monkeypatch):
    from app.services import canonical_source_acquisition as module
    from app.services.research_artifact_budget import ArtifactCapacityError
    original = module.durable_json
    capacity = ArtifactCapacityError(code='SYNTHETIC_CAP', role='source', current=1, projected=2, cap=1)
    def fail_receipt(path, *args, **kwargs):
        if path.parent.name == 'probe' and path.name.startswith('receipt-'):
            raise capacity
        return original(path, *args, **kwargs)
    monkeypatch.setattr(module, 'durable_json', fail_receipt)
    with pytest.raises(ArtifactCapacityError) as caught:
        capture_failure(tmp_path, 'bad_json')
    assert caught.value is capacity
    finals = list((tmp_path/'dispatch/receipts').glob('*/final.json'))
    assert len(finals) == 1 and json.loads(finals[0].read_bytes())['status'] == 'PASS'
    assert not (tmp_path/'phase-night.json').exists()


def test_registered_cycle_freezes_optional_night_plan_and_ledger_before_http(tmp_path, monkeypatch):
    from app.jobs import unified_market_snapshot as job
    from app.services.campaign_runtime_cap import OPTIONAL_NIGHT
    from tests.test_local_launchd_entry import original_cycle_probe
    from tests.test_manual_source_budget import offline_only
    offline_only.__wrapped__(monkeypatch, tmp_path)
    monkeypatch.setattr('app.services.research_artifact_budget.os.statvfs',
        lambda path:SimpleNamespace(f_bavail=32*1024**3, f_frsize=1))
    runtime = tmp_path/'model-runtime'
    runtime.mkdir(mode=0o700)
    monkeypatch.setattr(job, '_local_model_runtime', lambda execution:runtime)
    result = original_cycle_probe(tmp_path, 'us', monkeypatch,
        config_overrides={'us_night_policy':US_NIGHT_OPTIONAL})
    frozen = json.loads((tmp_path/'source/production-frozen-source-plan.json').read_bytes())
    identity = json.loads((tmp_path/'campaign.jsonl').read_bytes().splitlines()[0])['identity']
    assert us_night_optional(frozen)
    assert identity['runtime_cap']['optional_night'] == OPTIONAL_NIGHT
    assert 'krx_night_futures' in frozen['config_identities']
    assert identity['max_http'] == 710 and identity['max_models'] == 42
    assert result['financial_HTTP'] == result['models'] == 0
    assert len(frozen['plan']['subjects']) == 14
