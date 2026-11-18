"""SYNTHETIC wire/ledger fixtures; never live registration or provider authority."""
import asyncio
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import socket

import httpx
import pytest

from app.services.campaign_runtime_cap import OPTIONAL_NEWS_429, RuntimeCap
from app.services.canonical_source_replay import _stock_event_inputs
from app.services.fresh_event_carrier import replay_carrier
from app.services.model_execution_plan import CohortSubject, FrozenCohort, compile_model_plan, verify_mixed_render
from app.services.production_source_seal import corpus_index, seal_collection, verify_collection_seal
from app.services.selected_news_rate_limit import (KEY, STATUS, current_rows, disclose,
    optional_scope, require_prior, skipped_slots)
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.selected_source_plan import SelectedRequestPlan
from app.services.sealed_source_transport import CapturedFragment
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_live_source_transport import SourceSafetyStop


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('V5_TEST_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


@pytest.fixture
def original():
    base = Path(os.environ['TM_V5_V4_SOURCE'])
    return json.loads((base/'production-frozen-source-plan.json').read_bytes()), base


def ledger(tmp_path, original, plan, *, enabled=True):
    """Rehashed scratch accounting prefix, not a registration Owner issuance."""
    prefix = []
    for line in (original.parent/'campaign.jsonl').read_bytes().splitlines():
        row = json.loads(line)
        prefix.append(row)
        if row['event'] == 'PLAN':
            break
    identity = deepcopy(prefix[0]['identity'])
    now = datetime.now(timezone.utc)
    identity.update(master_id='SYNTHETIC_NEWS_TEST', authorized_at=(now-timedelta(seconds=10)).isoformat(),
        expires_at=(now+timedelta(minutes=50)).isoformat())
    identity['children']['us']['generation'] = plan.generation_id
    if enabled:
        identity['runtime_cap']['optional_news_429'] = OPTIONAL_NEWS_429
    path = tmp_path/'synthetic-campaign.jsonl'
    previous = None
    capture_sha = None
    with path.open('xb') as f:
        for i, row in enumerate(prefix):
            row.update(identity=identity, previous=previous, sequence=i)
            if row['event'] == 'REGISTRATION':
                row['value']['receipt']['cutoff'] = now.isoformat()
                capture_sha = row['value']['sha256'] = digest(row['value']['receipt'])
            if row['event'] == 'REGISTERED_SUBJECTS':
                row['value']['capture_sha256'] = capture_sha
            if row['event'] == 'PLAN':
                row['value']['sha256'] = plan.plan_sha256
            row['sha256'] = digest({k:v for k,v in row.items() if k != 'sha256'})
            previous = row['sha256']
            f.write(encoded(row)+b'\n')
    return SelectedRunLedger.attach_worker(dict(path=str(path), identity_sha256=digest(identity)))


def dispatcher(tmp_path, plan, budget):
    run = object.__new__(SelectedSourceDispatcher)
    run.plan, run.run_ledger = plan, budget
    run.admission = {'SYNTHETIC_TEST_NO_SOURCE_RIGHTS': True}
    run._require_current = lambda: None  # Only the registration port is synthetic.
    run._initialize(root=tmp_path/'dispatch', secrets=())
    return run


def request(d):
    row = json.loads(d.request_json)
    return httpx.Request(row['method'], row['url'], headers=row['headers'], content=row['body'].encode())


def execute(run, d, inner):
    return asyncio.run(run.execute(d.logical_request_id, request(d), transport=inner, normalize=CapturedFragment(d)))


@pytest.mark.parametrize('position', [0, 2, 13])
def test_mixed_actual_dispatch_ledger_cold_and_render(tmp_path, original, position):
    frozen, base = original
    frozen = deepcopy(frozen)
    frozen['optional_news_429'] = OPTIONAL_NEWS_429
    plan = SelectedRequestPlan.model_validate(frozen['plan'])
    news = [next(d for d in plan.descriptors if d.logical_request_id == 'events:'+r['subject']) for r in frozen['news_reads']]
    budget = ledger(tmp_path, base, plan)
    run = dispatcher(tmp_path, plan, budget)
    phases, wire = {}, []
    def respond(req):
        wire.append(str(req.url.host))
        return httpx.Response(429 if len(wire)-1 == position else 200,
            content=b'<rss><channel/></rss>', request=req)
    inner = httpx.MockTransport(respond)
    for i, d in enumerate(news):
        limited = current_rows(tmp_path, frozen, plan, run.results)
        if d.subject not in limited:
            execute(run, d, inner)
            limited = current_rows(tmp_path, frozen, plan, run.results)
        else:
            assert d.logical_request_id not in run.used
            run.used.add(d.logical_request_id)
        phases['event-'+d.subject] = dict(status='CAPTURED_NOT_QUALIFIED',
            value=limited.get(d.subject, {'normal':True}))
        if i > position:
            assert limited[d.subject]['wire_attempts'] == 0
    assert len(wire) == position+1 and not run.halted
    assert budget.state()['state'] == 'REGISTRATION_CAPTURED'
    cap = RuntimeCap(budget.worker_binding())
    assert cap.state()['first_external_failure'] is None
    assert cap.state()['stopped_providers'] == ['google_news_rss']
    # An independent required provider can still send, without relaxing STOP globally.
    d = next(d for d in plan.descriptors if d.provider == 'sec_edgar' and not d.response_binding)
    execute(run, d, httpx.MockTransport(lambda r:httpx.Response(200, json={}, request=r)))
    assert budget.state()['http_total'] == position+2
    outcome = dict(completed_at=datetime.now(timezone.utc).isoformat(), phases=phases, logical_results=run.results)
    stock = json.loads(json.dumps(frozen['stock_plan']))
    # Only the changed pure Cold event port consumes the actual sealed 429 proof.
    from app.services.selected_source_plan import SelectedStockPlan
    stock = SelectedStockPlan.model_validate(stock)
    window = dict(run_id=stock.run_id, collection_started_at=frozen['frozen_at'],
        source_query_cutoff=frozen['frozen_at'], business_availability_cutoff=outcome['completed_at'])
    events = []
    for i, d in enumerate(news):
        if i < position:
            events.append({'binding':{'provider':'google_news_rss', 'denial':None, 'evidence':[]}})
            continue
        carrier = _stock_event_inputs(tmp_path, frozen, outcome, market='us', ticker=d.subject, window=window)
        cold = replay_carrier(carrier, plan=stock, ticker=d.subject,
            security=next(s for s in frozen['security_records'] if s['ticker']==d.subject),
            policy=UnifiedSourcePolicy(frozenset({'google_news_rss'})))
        assert cold['facts'] == cold['evidence'] == [] and cold['receipt']['allowed_uses'] == []
        assert cold['binding']['denial'] == STATUS
        events.append(cold)
    instant = frozen['frozen_at']
    names = UNIVERSE['us']
    cohort = FrozenCohort('SYNTHETIC_RENDER', 'SYNTHETIC_SOURCE', frozen['sessions']['us'], instant, instant,
        tuple(CohortSubject('us', t, 'SEC:'+t, instant, digest(t)) for t in names),
        (('us', digest('SYNTHETIC_OWNER_NOT_ISSUED')),), digest('fixture'), limitation_subjects=('SKHY',))
    model = compile_model_plan(cohort, topology='CANONICAL_PRODUCTION')
    model.validate()
    assert all('SKHY' not in s.subjects for s in model.slots if s.stage in {'B','B2'})
    messages = [disclose(dict(message_id='MARKET_US', text='SYNTHETIC MARKET'), events, expected_count=14)]
    for d, event in zip(news, events, strict=True):
        messages.append(disclose(dict(message_id=d.subject, text='SYNTHETIC STOCK'), [event], expected_count=1))
    for m in messages:
        m.update(NO_SEND=True, generation_id=cohort.run_id)
        if m['message_id']=='SKHY':
            m.update(decision_mode='UNKNOWN_LIMIT', limitation_decision_sha256=digest('limit'), plan_sha256=digest('unknown-plan'))
    limited = next(m for m in messages if m['message_id']=='SKHY')
    verify_mixed_render(model, messages, {'SKHY':dict(plan_sha256=limited['plan_sha256'],
        content_sha256=digest(limited['text']),decision_sha256=limited['limitation_decision_sha256'])})
    assert len(messages) == len({m['message_id'] for m in messages}) == 15
    assert sum('HTTP 429' in m['text'] for m in messages) == 1+14-position
    assert digest(messages) == digest(deepcopy(messages))
    if os.environ.get('TM_V5_EVIDENCE_DIR'):
        target = Path(os.environ['TM_V5_EVIDENCE_DIR'])/f'mixed-{position}.json'
        target.write_bytes(encoded(dict(synthetic=True, real_http=0, real_models=0,
            mock_http=budget.state()['http_total'], news_wire=position+1,
            cold_affected=14-position, messages=15, messages_sha256=digest(messages),
            model_stages=dict(Counter(s.stage for s in model.slots)), journal_sha256=digest(budget.path.read_text()),
            stopped_providers=cap.state()['stopped_providers'], first_external_failure=None))+b'\n')


@pytest.mark.parametrize('kind', ['old_policy', 'mandatory', 'auth401', 'auth403', 'timeout',
    'sec429', 'finnhub429', 'kiwoom429', 'kiwoom_badjson', 'secret429', 'duplicate', 'forged_raw'])
def test_stop_and_integrity_are_not_optional(tmp_path, original, kind):
    frozen, base = original
    frozen = deepcopy(frozen)
    frozen['optional_news_429'] = OPTIONAL_NEWS_429
    plan = SelectedRequestPlan.model_validate(frozen['plan'])
    d = next(d for d in plan.descriptors if d.logical_request_id=='events:CRCL')
    if kind == 'mandatory':
        raw = plan.model_dump(mode='json')
        next(r for r in raw['descriptors'] if r['logical_request_id']==d.logical_request_id)['mandatory']=True
        plan = SelectedRequestPlan.model_validate(raw)
        d = next(r for r in plan.descriptors if r.logical_request_id==d.logical_request_id)
        assert optional_scope(plan,d) is None
    providers = {'sec429':'sec_edgar','finnhub429':'finnhub','kiwoom429':'kiwoom','kiwoom_badjson':'kiwoom'}
    if kind in providers:
        d = next(d for d in plan.descriptors if d.provider==providers[kind] and not d.response_binding)
    budget = ledger(tmp_path, base, plan, enabled=kind!='old_policy')
    run = dispatcher(tmp_path, plan, budget)
    def respond(req):
        if kind=='timeout':
            raise httpx.ReadTimeout('SYNTHETIC', request=req)
        status = 200 if kind=='kiwoom_badjson' else 401 if kind=='auth401' else 403 if kind=='auth403' else 429
        body = b'{"api_key":"SYNTHETIC_SECRET_ECHO"}' if kind=='secret429' else b'limited'
        return httpx.Response(status, content=body, request=req)
    if kind == 'forged_raw':
        execute(run,d,httpx.MockTransport(respond))
        a = run.results[d.logical_request_id]['attempts'][0]
        (run.root/a['artifact']).write_bytes(b'TAMPERED')
        with pytest.raises(ValueError,match='raw_hash_mismatch'):
            current_rows(tmp_path,frozen,plan,run.results)
    else:
        if kind == 'duplicate':
            execute(run,d,httpx.MockTransport(respond))
        with pytest.raises((SourceSafetyStop, ValueError)):
            execute(run,d,httpx.MockTransport(respond))
        assert budget.state()['state']=='STOPPED_NO_SEND'
        if kind not in {'secret429','duplicate','kiwoom_badjson'}:
            assert RuntimeCap(dict(path=str(budget.path),identity_sha256=digest(budget.identity))).state()['first_external_failure'] is not None


def test_prior_day_and_mixed_notice_scope(original):
    frozen, _ = original
    plan=SelectedRequestPlan.model_validate(frozen['plan'])
    proof=dict(prior_generation='SYNTHETIC_PRIOR',target_session=frozen['sessions']['us'],
        prior_logical_id='events:CRCL',observed_at=(plan.frozen_at-timedelta(seconds=1)).isoformat(),
        raw_sha256='a'*64,receipt_sha256='b'*64,dispatch_plan_sha256='c'*64,provider='google_news_rss',http_status=429)
    rows=skipped_slots({**frozen,KEY:proof},plan)
    assert len(rows)==14 and all(r['wire_attempts']==0 for r in rows.values())
    assert current_rows(Path('/not-read'),{**frozen,KEY:proof,'optional_news_429':OPTIONAL_NEWS_429},plan,{})=={}
    with pytest.raises(ValueError,match='prior_skip_has_current_wire'):
        current_rows(Path('/not-read'),{**frozen,KEY:proof,'optional_news_429':OPTIONAL_NEWS_429},plan,{'events:CORZ':{}})
    for change in ({'observed_at':(plan.frozen_at-timedelta(days=1)).isoformat()},
                   {'target_session':'1900-01-01'},{'raw_sha256':'forged'},{'prior_generation':plan.generation_id}):
        with pytest.raises(ValueError):
            require_prior({**proof,**change},generation=plan.generation_id,session=frozen['sessions']['us'],started_at=plan.frozen_at)
    with pytest.raises(ValueError,match='render_scope'):
        disclose({'text':'fixture'},[{'binding':{'provider':'google_news_rss','denial':STATUS,'evidence':[]}}],expected_count=14)


def test_forged_valid_sha_skip_and_result_reject(tmp_path, original):
    frozen, base = original
    frozen = {**frozen,'optional_news_429':OPTIONAL_NEWS_429}
    plan = SelectedRequestPlan.model_validate(frozen['plan'])
    budget = ledger(tmp_path,base,plan)
    run = dispatcher(tmp_path,plan,budget)
    d = next(d for d in plan.descriptors if d.logical_request_id=='events:CRCL')
    for mutation in ({'mandatory':True},{'endpoint_operation':'filing'},{'consumer_role':'financial:CRCL'},
                     {'provider':'finnhub'},{'market':'kr'}):
        assert optional_scope(plan,d.model_copy(update=mutation)) is None
    execute(run,d,httpx.MockTransport(lambda r:httpx.Response(429,content=b'limited',request=r)))
    rows = current_rows(tmp_path,frozen,plan,run.results)
    good = rows['GOOGL']
    fake = deepcopy(good)
    fake['current']['raw_sha256'] = 'f'*64
    phases={'event-GOOGL':{'status':'CAPTURED_NOT_QUALIFIED','value':fake}}
    outcome=dict(phases=phases,logical_results=run.results,completed_at=datetime.now(timezone.utc).isoformat())
    with pytest.raises(ValueError,match='current_skip_unsealed'):
        _stock_event_inputs(tmp_path,frozen,outcome,market='us',ticker='GOOGL',window={})
    key=budget.before_http(market='us',provider='sec_edgar',logical_id='SYNTHETIC',plan_sha256=plan.plan_sha256)
    with pytest.raises(ValueError,match='not_original_429'):
        budget.result(key,ok=False,optional_unavailable='UNISSUED')
    assert budget.state()['pending']==key
    budget.result(key,ok=False)


def test_retained_original_seal_with_scratch_mixed_news(tmp_path, original):
    old = Path(os.environ['TM_V5_V3_SOURCE'])
    before = corpus_index(old)
    frozen = json.loads((old/'production-frozen-source-plan.json').read_bytes())
    outcome = json.loads((old/'acquisition-outcome.json').read_bytes())
    plan = SelectedRequestPlan.model_validate(frozen['plan'])
    order = [r['subject'] for r in frozen['news_reads']]
    affected = order[order.index('CRCL'):]
    def ignore(path, names):
        relative = Path(path).relative_to(old)
        if str(relative) == '.':
            return [n for n in names if n in {'production-frozen-source-plan.json','acquisition-outcome.json'}
                or n in {'phase-event-'+t+'.json' for t in affected}]
        if str(relative) == 'events':
            return [t for t in affected if t in names]
        if str(relative) in {'dispatch/receipts','dispatch/raw'}:
            return ['events:'+t for t in affected if 'events:'+t in names]
        return []
    scratch = tmp_path/'historical-synthetic-mix'
    shutil.copytree(old, scratch, ignore=ignore)
    frozen['optional_news_429'] = OPTIONAL_NEWS_429
    outcome['logical_results'] = {k:v for k,v in outcome['logical_results'].items()
        if k not in {'events:'+t for t in affected}}
    for t in affected:
        outcome['phases'].pop('event-'+t,None)
    budget = ledger(tmp_path, original[1], plan)
    run = dispatcher(tmp_path/'new-mock-wire', plan, budget)
    d = next(d for d in plan.descriptors if d.logical_request_id=='events:CRCL')
    final = execute(run,d,httpx.MockTransport(lambda r:httpx.Response(429,content=b'SYNTHETIC_429',request=r)))
    shutil.copytree(run.root/'receipts/events:CRCL',scratch/'dispatch/receipts/events:CRCL')
    outcome['logical_results'][d.logical_request_id] = final
    limited = current_rows(scratch,frozen,plan,outcome['logical_results'])
    for t,row in limited.items():
        phase=dict(status='CAPTURED_NOT_QUALIFIED',value=row)
        outcome['phases']['event-'+t]=phase
        (scratch/('phase-event-'+t+'.json')).write_bytes(encoded(phase)+b'\n')
    outcome['completed_at']=datetime.now(timezone.utc).isoformat()
    (scratch/'production-frozen-source-plan.json').write_bytes(encoded(frozen)+b'\n')
    (scratch/'acquisition-outcome.json').write_bytes(encoded(outcome)+b'\n')
    seal=seal_collection(scratch,seal_path=tmp_path/'offline-source-seal.json',frozen=frozen,outcome=outcome)
    verify_collection_seal(scratch,seal,frozen)
    assert seal['slot_dispositions']['status']=='PASS'
    statuses={r['logical_request_id']:r['disposition'] for r in seal['slot_dispositions']['rows']}
    assert statuses['events:CORZ']=='ACQUIRED_BOUND_BODY_PENDING_OWNER_QUALIFICATION'
    assert statuses['events:CRCL']=='OPTIONAL_UNAVAILABLE_HTTP_429'
    assert statuses['events:GOOGL']=='NOT_ACTIVATED_OPTIONAL_NEWS_RATE_LIMIT'
    with pytest.raises(ValueError,match='request_coverage_gap'):
        seal_collection(scratch,seal_path=tmp_path/'must-not-exist.json',frozen=frozen,
            outcome={**outcome,'phases':{**outcome['phases'],'systemic_stop':{'SYNTHETIC_REQUIRED_FAILURE':True}}})
    assert corpus_index(old)==before
    if os.environ.get('TM_V5_EVIDENCE_DIR'):
        (Path(os.environ['TM_V5_EVIDENCE_DIR'])/'SOURCE_COLD_MODELPLAN_OFFLINE.json').write_bytes(encoded(dict(
            status='ORIGINAL_SOURCE_SEAL_MIXED_REPLAY_PASS', historical_originals_unchanged=True,
            original_corpus_sha256=digest(before), original_files=len(before),
            scratch_fixture='Historical original financial/Native receipts plus explicitly synthetic news429; NOT a new live Source Owner',
            real_http=0, real_models=0, original_source_seal_sha256=seal['receipt_sha256'],
            slot_counts=seal['slot_dispositions']['counts'], mandatory_failure='REJECTED',
            cold_event_port='Original replay_carrier in mixed-0/2/13 tests',
            model_plan_and_render='Original compile/validate/verify_mixed_render; synthetic messages only',
            full_current_prepare_child='NOT_RUN_NO_CURRENT_REGISTRATION_OWNER'))+b'\n')
