"""Original engine with synthetic session-aligned inputs; no real issuer admission."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import short_history_reference as short
from app.services.market_session import korea_market_session,us_market_session,_exchange_calendar
from app.services.unified_snapshot_contract import digest


def sample(n,market='us',ticker='UNSEENUS'):
    cutoff=datetime(2026,10,23,5,tzinfo=timezone.utc)
    state=(korea_market_session if market=='kr' else us_market_session)(cutoff)
    target=state.latest_completed_regular_session_date.isoformat()
    dates=_exchange_calendar('XKRX' if market=='kr' else 'XNYS').sessions_in_range('2021-01-01',target)
    dates=list(dates[-n:]) if n else []
    rows=[dict(date=d.date().isoformat(),open=100+i*.1,high=102+i*.1,low=99+i*.1,
        close=101+i*.1,volume=1000+i) for i,d in enumerate(dates)]
    read=SimpleNamespace(market=market,subject=ticker,canonical_security_id='SYNTHETIC:'+ticker,
        timeframe='daily',role='adjusted_daily',adjusted=True,count=1000,max_pages=2,
        latest_completed_session=target,query_date='20261023',entry_id=ticker+':adjusted_daily')
    page=dict(sha256=digest(rows))
    receipt=dict(status='CAPTURED',pages=[dict(source_sha256=page['sha256'],response_continuation={'cont_yn':'N','next_key':''})])
    return dict(read=read,cutoff=cutoff,all_rows=rows,source_receipt=receipt,source_pages=[page])


@pytest.mark.parametrize('market,ticker',[('us','UNSEENUS'),('us','UNSEENADS'),('kr','777777')])
@pytest.mark.parametrize('n',[0,1,19,20,73,74,199,200,999,1000])
def test_history_boundaries_and_original_engine(market,ticker,n):
    args=sample(n,market,ticker)
    if n in (0,1000):
        with pytest.raises(ValueError): short.review_rows(**args)
        return
    rows,value=short.review_rows(**args)
    assert len(rows)==value['actual_bars']==n
    assert len(value['availability'])==78
    assert len({v['semantic'] for v in value['availability']})==78
    for entry in value['availability']:
        if entry['status']=='AVAILABLE': assert entry['semantic'] in value['facts']
        elif n<entry['activation_minimum']: assert entry['status']=='HISTORY_INSUFFICIENT'
        else: assert entry['status']=='UNAVAILABLE_ENGINE_PREDICATE'
    assert not any(value[k] for k in ('technical_signal','projected_1000','valuation_use','native_use','D01_D02','economic_use'))
    assert value['legal_listing_inception']=='UNPROVEN'
    if n in (73,74):
        assert len(value['facts'])==60
        assert sum(r['status']=='HISTORY_INSUFFICIENT' for r in value['availability'])==18
        assert 'sma_200' not in value['facts']


@pytest.mark.parametrize('case',['truncated','unknown_cursor','wrong_market','wrong_session','weekend',
    'missing_session','duplicate','future','wrong_source','weekly','unadjusted','lowered_required_count','invalid_price'])
def test_reference_rejects_invalid_source_window(case):
    a=sample(74)
    if case=='truncated': a['source_receipt']['pages'][0]['response_continuation']={'cont_yn':'Y','next_key':'more'}
    elif case=='unknown_cursor': a['source_receipt']['pages'][0]['response_continuation']={'cont_yn':'','next_key':''}
    elif case=='wrong_market': a['read'].market='other'
    elif case=='wrong_session': a['read'].latest_completed_session='2026-10-18'
    elif case=='weekend': a['all_rows'][-2]['date']='2026-10-18'
    elif case=='missing_session': a['all_rows'].pop(20)
    elif case=='duplicate': a['all_rows'][5]=dict(a['all_rows'][4])
    elif case=='future': a['all_rows'][-1]['date']='2026-11-01'
    elif case=='wrong_source': a['source_pages'][0]['sha256']='f'*64
    elif case=='weekly': a['read'].timeframe='weekly'
    elif case=='unadjusted': a['read'].adjusted=False
    elif case=='lowered_required_count': a['read'].count=74
    else: a['all_rows'][-1]['close']=-1
    with pytest.raises((ValueError,KeyError)): short.review_rows(**a)


def test_equivalent_evidence_does_not_depend_on_ticker():
    a=short.review_rows(**sample(74,ticker='NEWPLAIN'))[1]
    b=short.review_rows(**sample(74,ticker='NEWDEPOSITARY'))[1]
    assert a['availability']==b['availability']
    assert {k:(v['value'],v['minimum_history']) for k,v in a['facts'].items()}=={
        k:(v['value'],v['minimum_history']) for k,v in b['facts'].items()}


@pytest.mark.parametrize('market,ticker',[('us','NEWCOMMON'),('us','NEWADS'),('kr','888888')])
def test_full_thousand_uses_original_completed_projection(market,ticker):
    from app.services.completed_session_projection import project_completed_rows
    args=sample(1000,market,ticker)
    with pytest.raises(ValueError):short.review_rows(**args)
    rows,proof=project_completed_rows(args['all_rows'],read=args['read'],cutoff=args['cutoff'],source_pages=args['source_pages'])
    assert len(rows)==proof['selected_rows']==1000
    assert not proof['economic_use'] and not proof['native_use']


def test_worker_namespace_switch_keeps_local_review_dependencies(monkeypatch):
    import sys
    import importlib.abc
    args=sample(74)
    class ExternalNamespace(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,*unused):
            if fullname=='app' or fullname.startswith('app.'):
                raise PermissionError('EXTERNAL_OWNER_NAMESPACE_ONLY')
    with monkeypatch.context() as m:
        for name in list(sys.modules):
            if name=='app' or name.startswith('app.'):m.delitem(sys.modules,name)
        m.setattr(sys,'meta_path',[ExternalNamespace(),*sys.meta_path])
        assert len(short.review_rows(**args)[1]['facts'])==60


def test_unissued_context_or_json_never_becomes_capability():
    for cap in ({'status':'PASS'}, short.ShortHistoryReference()):
        with pytest.raises(ValueError): short.consume(object(),cap,dispatcher=object(),entry_id='x',security_id='x',generation_id='x')
    with pytest.raises(ValueError): short.issue(object(),dispatcher=object(),entry_id='x')
    with pytest.raises(ValueError): short.issue(object(),dispatcher=object(),entry_id='x',enabled=True)


def synthetic_capture(tmp_path,index=0):
    """Live backend fixtures, simulated worker journal, NOT external parser proof."""
    import json
    import os
    import httpx
    from pathlib import Path
    from app.services import current_scoped_source_results as replay, current_scoped_source_owner as owner
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.scoped_source_plan import ScopedConfig,compile_scoped_wire_contract
    from app.services.unified_snapshot_contract import encoded
    from test_current_scoped_source_owner import setup_parent,wire
    from test_current_scoped_source_dispatch import execute
    args,_,identities=setup_parent(tmp_path,three_types=True)
    spec=args['spec'];subject=spec.config.subjects[index];config=spec.config.model_dump(mode='json')
    config['capture_selection']=dict(contract='scoped-capture-selection-v2',stock_security_ids=[subject.security_id],
        stock_markets=[subject.market],stock_roles=['adjusted_daily'],market_contexts=[],us_completed_closes=False)
    spec=spec.model_copy(update={'config':ScopedConfig.model_validate(config)})
    plan=wire(spec,identities);parent=owner.issue_parent(**dict(args,spec=spec,plan=plan))
    dispatcher=CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp_path/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
        config_identities={'kiwoom':spec.provider_config_sha256},credential_presence={'kiwoom':True})
    wire_value=compile_scoped_wire_contract(config=spec.config,identities=identities,generation_id=spec.generation_id,
        at=spec.cutoff,code_sha=spec.code_sha,provider_config_sha256=spec.provider_config_sha256,retries=0)
    read,=wire_value['stock_reads']
    stock=dict(contract='current-scoped-stock-capture-v1',run_id=spec.generation_id,acquisition_id=spec.generation_id+'-stock',
        frozen_at=spec.cutoff.isoformat(),reads=[read.model_dump(mode='json')],owner_files=json.loads(wire_value['owner_files_json']))
    worker=tmp_path/'worker';(worker/'stocks').mkdir(parents=True)
    frozen=tmp_path/'worker-plan.json';pins={str(i):{'sha256':'a'*64} for i in range(25)}
    frozen.write_bytes(encoded(dict(stock_plan=stock,output=str(worker),external_pins=pins)))
    bridge=ScopedBridge(parent=parent,original_plan=plan,transport=SimpleNamespace(dispatcher=dispatcher),
        worker=Path(replay.__file__).resolve().parents[2]/'scripts/current_scoped_source_worker.py',
        frozen=frozen,sha=replay._sha(frozen.read_bytes()),output=worker,credentials={},market_reads=())
    context=dict(parent=parent,wire=wire_value,stock_plan=stock,dispatcher=dispatcher,capture_root=dispatcher.root,worker_root=worker)
    replay.bind_capture(**context,worker_bridge=bridge)
    calendar=_exchange_calendar('XKRX' if read.market=='kr' else 'XNYS')
    dates=calendar.sessions_in_range('2025-01-01',read.latest_completed_session)[-74:]
    rows=[dict(date=d.date().isoformat(),open=100+i*.1,high=102+i*.1,low=99+i*.1,close=101+i*.1,volume=1000+i)
        for i,d in enumerate(dates)]
    d=next(d for d in plan.descriptors if d.consumer_role=='stock:'+read.entry_id and d.page_ordinal==1)
    start=datetime.now(timezone.utc).isoformat()
    execute(dispatcher,d,httpx.MockTransport(lambda r:httpx.Response(200,json=dict(return_code=0,synthetic_rows=rows),
        headers={'cont-yn':'N','next-key':''})))
    _,final,raw,resolved=replay._sealed(dispatcher,dispatcher.root,dispatcher.plan,d.logical_request_id)
    rawname='transport-0001.body';(worker/'stocks'/rawname).write_bytes(raw)
    normalized=encoded(rows);(worker/'stocks/role-001.normalized.json').write_bytes(normalized)
    headers=dict(resolved['headers'])
    request=dict(method='POST',route=read.route,api_id=read.api_id,payload=json.loads(resolved['body']),
        continuation=dict(cont_yn=headers.get('cont-yn'),next_key=headers.get('next-key')))
    end=datetime.now(timezone.utc).isoformat()
    receipt=dict(run_id=stock['run_id'],acquisition_id=stock['acquisition_id'],plan_sha256=digest(stock),
        entry=read.model_dump(mode='json'),started_at=start,completed_at=end,status='CAPTURED',
        normalized_artifact='role-001.normalized.json',normalized_sha256=replay._sha(normalized),
        pages=[dict(provider='kiwoom',entry_id=read.entry_id,page_ordinal=1,request=request,request_sha256=digest(request),
            requested_at=start,received_at=end,artifact=rawname,source_sha256=replay._sha(raw),
            http_status=200,response_continuation=dict(cont_yn='N',next_key=''))])
    (worker/'stocks/role-001.receipt.json').write_bytes(encoded(receipt))
    page=dict(artifact=rawname,sha256=replay._sha(raw))
    selected,value=short.review_rows(read=read,cutoff=spec.cutoff,all_rows=rows,source_receipt=receipt,source_pages=[page])
    name='short-reference-001.json'
    (worker/name).write_bytes(encoded(dict(all_rows=rows,rows=selected,receipt=value,parser_pins=pins)))
    commands=[dict(command={'stocks':True},result_sha256=digest(dict(status='CAPTURE_COMPLETE_NOT_QUALIFIED')),
        sealed_receipts={d.logical_request_id:final['receipt_sha256']})]
    replays=[dict(entry_id=read.entry_id,status='PASS',normalized_sha256=receipt['normalized_sha256'],network_calls=0)]
    for number in (1,2):
        rb=encoded(replays);(worker/f'raw-owner-replay-{number}.json').write_bytes(rb)
        commands.append(dict(command={'replay':number},result_sha256=digest(dict(status='REPLAY_RESULT',rows=replays,sha256=replay._sha(rb))),sealed_receipts={}))
    commands.append(dict(command={'short_reference':read.entry_id},result_sha256=digest(dict(status='SHORT_REFERENCE_REPLAY_PASS',
        entry_id=read.entry_id,artifact=name,sha256=replay._sha((worker/name).read_bytes()))),sealed_receipts={}))
    bridge.commands=commands;bridge.process=SimpleNamespace(pid=os.getpid(),returncode=0)
    for i,c in enumerate(commands,1):(worker/f'command-{i:03d}.json').write_bytes(encoded(c))
    (worker/'process-start.json').write_bytes(encoded(dict(pid=os.getpid(),worker_sha256=replay._sha(Path(bridge.worker).read_bytes()),start=1)))
    (worker/'process-end.json').write_bytes(encoded(dict(pid=os.getpid(),end=2,state='NORMAL_END',exit=0)))
    return parent,dispatcher,read,spec,worker


@pytest.mark.parametrize('index',[0,1,2])
def test_synthetic_backend_issue_consume_idempotent_revoke(tmp_path,index,record_property):
    from app.services import current_scoped_source_owner as owner
    parent,dispatcher,read,spec,_=synthetic_capture(tmp_path,index)
    record_property('proof_boundary','SYNTHETIC_BACKEND_ONLY_SIMULATED_WORKER_JOURNAL_NOT_EXTERNAL_PARSER_RUN')
    cap=short.issue(parent,dispatcher=dispatcher,entry_id=read.entry_id,enabled=True)
    args=dict(dispatcher=dispatcher,entry_id=read.entry_id,security_id=read.canonical_security_id,generation_id=spec.generation_id)
    value=short.consume(parent,cap,**args)
    assert value==short.consume(parent,cap,**args)
    assert value['actual_bars']==74 and not value['native_use'] and not value['projected_1000']
    for consumer in ('technical-reference-1000','FULL22_NATIVE','CORE_DIRECTION'):
        with pytest.raises(ValueError):short.consume(parent,cap,**args,consumer=consumer)
    short.revoke(cap)
    with pytest.raises(ValueError):short.consume(parent,cap,**args)
    cap=short.issue(parent,dispatcher=dispatcher,entry_id=read.entry_id,enabled=True)
    owner.revoke_parent(parent)
    with pytest.raises(ValueError):short.consume(parent,cap,**args)


@pytest.mark.parametrize('mutation',['security','generation','parent','dispatcher','raw','receipt','replay','parser','packet'])
def test_synthetic_owner_consumption_rejects_substitution(tmp_path,mutation):
    from app.services.unified_snapshot_contract import encoded
    import json
    parent,dispatcher,read,spec,worker=synthetic_capture(tmp_path)
    cap=short.issue(parent,dispatcher=dispatcher,entry_id=read.entry_id,enabled=True)
    args=dict(dispatcher=dispatcher,entry_id=read.entry_id,security_id=read.canonical_security_id,generation_id=spec.generation_id)
    if mutation=='security':args['security_id']='OTHER'
    elif mutation=='generation':args['generation_id']='OLD'
    elif mutation=='parent':parent=object()
    elif mutation=='dispatcher':args['dispatcher']=object()
    else:
        path=worker/({'raw':'stocks/transport-0001.body','receipt':'stocks/role-001.receipt.json',
            'replay':'raw-owner-replay-1.json','parser':'short-reference-001.json','packet':'short-reference-001.json'}[mutation])
        value=json.loads(path.read_bytes())
        if mutation=='raw':value['synthetic_rows'][0]['close']=999
        elif mutation=='receipt':value['run_id']='HISTORICAL_REHASHED'
        elif mutation=='replay':value[0]['status']='GAP'
        elif mutation=='parser':value['parser_pins']={}
        else:value['receipt']['native_use']=True
        path.write_bytes(encoded(value))
    with pytest.raises((ValueError,KeyError)):short.consume(parent,cap,**args)
