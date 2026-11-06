"""TEST_ONLY original Worker/GlobalLane/Parent with mock HTTP, never live."""
import asyncio
from datetime import datetime,timezone,timedelta
from pathlib import Path
import json
import httpx
import pytest
from app import vnext_worker as entry
from app.services import registered_valuation_source_intent as intents,pending_source_parent as pending
from app.services import retained_identity_routing as routing
from app.services.vnext_research_store import digest
from app.services.scoped_worker_launch import DUMMY
from test_registered_valuation_source import setup


@pytest.fixture(scope='module',autouse=True)
def parent_network_denial():
    import socket
    with pytest.MonkeyPatch.context() as mp:
        def denied(*a,**k):raise RuntimeError('C19_TEST_PARENT_NETWORK_FORBIDDEN')
        mp.setattr(socket.socket,'connect',denied)
        mp.setattr(socket,'create_connection',denied)
        yield


def configure(path,mp):
    h,args=setup(path,mp)
    identities=intents.require_intent(h,generation_id='VALUATION_INTENT',provider='kiwoom',subjects=('999999',))
    import app.services.valuation_research_preflight as pre
    mp.setattr(pre,'retained_listing_rows',lambda root:[dict(code='999999',marketCode='0')])
    return dict(routing_root=path,identities=identities,generation_id='C19_TEST_ONLY',
        cutoff=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64),h,args


@pytest.fixture(scope='module')
def captured(tmp_path_factory):
    root=tmp_path_factory.mktemp('c19-synthetic')
    with pytest.MonkeyPatch.context() as mp:
        pre,h,args=configure(root,mp);calls=[]
        name=pre['identities']['999999']['company_name']
        def respond(request):
            api=request.headers.get('api-id') or 'auth';calls.append(api)
            if api=='auth':body=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959')
            elif api=='ka10099':body=dict(return_code=0,list=[dict(code='999999',name=name,marketCode='0',marketName='KOSPI')])
            else:body=dict(return_code=0,stk_cd='999999',stk_nm=name,per='12',pbr='2')
            return httpx.Response(200,json=body,headers={'cont-yn':'N','next-key':''})
        result=asyncio.run(entry.run_registered_valuation_source(preflight=pre,base=root/'capture',
            external_root='/Users/sskim/Codex/ohlcv-analyst',
            acquire_current_context=lambda:dict(intent=h,intent_generation='VALUATION_INTENT',session=args['session']),
            load_credentials=lambda:dict(DUMMY),inner=httpx.MockTransport(respond),enabled=True))
        yield root/'capture',result,calls


def test_existing_entrypoint_worker_to_separate_cold(captured,record_property):
    root,result,calls=captured
    assert calls==['auth','ka10099','ka10001'] and result['physical_attempts']==3
    assert result['worker_returncode']==0 and not result['current_economic_owner'] and not result['send']
    assert all(m['display_eligible'] for m in result['cold']['rows'][0]['metrics'])
    assert len(result['cold']['rows'][0]['metrics'])==2
    record_property('scope','TEST_ONLY_ORIGINAL_CONSTRUCTORS_MOCK_HTTP_NOT_REAL_QUALIFIED_SOURCE')
    record_property('mock_transport_attempts',3)
    record_property('separate_process_cold','PASS')


def test_missing_selected_receipt_denied(captured):
    root,_,_=captured
    plan=routing.decode_request_plan(json.loads((root/'dispatch/plan.json').read_bytes()))
    descriptor=next(d for d in plan.descriptors if d.endpoint_operation=='ka10099' and d.page_ordinal==1)
    path=root/'dispatch/receipts'/descriptor.logical_request_id/'final.json';raw=path.read_bytes();path.unlink()
    try:
        with pytest.raises(ValueError,match='selected_receipt_missing'):routing.retained_listing_rows(root/'dispatch')
    finally:path.write_bytes(raw)


def test_unrequested_missing_continuation_requires_original_binding(captured):
    root,_,_=captured
    plan=routing.decode_request_plan(json.loads((root/'dispatch/plan.json').read_bytes()))
    descriptors=[d for d in plan.descriptors if d.endpoint_operation=='ka10099' and d.page_ordinal>1]
    saved=[]
    for d in descriptors:
        p=root/'dispatch/receipts'/d.logical_request_id/'final.json';saved.append((p,p.read_bytes()));p.unlink()
    try:assert routing.retained_listing_rows(root/'dispatch')[0]['code']=='999999'
    finally:
        for p,raw in saved:p.write_bytes(raw)


def test_corrupt_retained_raw_denied(captured):
    root,_,_=captured
    plan=routing.decode_request_plan(json.loads((root/'dispatch/plan.json').read_bytes()))
    d=next(d for d in plan.descriptors if d.endpoint_operation=='ka10099' and d.page_ordinal==1)
    p=root/'dispatch'/d.raw_path;raw=p.read_bytes();p.write_bytes(b'{}')
    try:
        with pytest.raises(ValueError):routing.retained_listing_rows(root/'dispatch')
    finally:p.write_bytes(raw)


def test_wrong_issuer_before_context_or_keys(tmp_path,monkeypatch):
    pre,_,_=configure(tmp_path,monkeypatch);pre['identities']['999999']['country']='US'
    with pytest.raises(ValueError):
        asyncio.run(entry.run_registered_valuation_source(preflight=pre,base=tmp_path/'unused',external_root='unused',
            acquire_current_context=lambda:pytest.fail('context before static'),load_credentials=lambda:pytest.fail('keys'),enabled=True))


@pytest.mark.parametrize('kind',['forged','expired'])
def test_original_parent_not_reusable(tmp_path,monkeypatch,kind):
    from app.services.valuation_research_preflight import prepare_registered_valuation
    pre,h,args=configure(tmp_path,monkeypatch)
    result=prepare_registered_valuation(**pre,enabled=True,
        acquire_current_context=lambda:dict(intent=h,intent_generation='VALUATION_INTENT',session=args['session']))
    parent=result['parent']
    if kind=='forged':parent=pending.PendingSourceParent()
    else:pending._LIVE[parent]['receipt']['expires_at']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError):pending.resolve_parent(parent)


def test_code_changed_after_preflight_before_credentials(tmp_path,monkeypatch):
    pre,h,args=configure(tmp_path,monkeypatch);changed=[False];original=Path.read_bytes
    def read(path):
        if changed[0] and path==Path(entry.__file__):return b'SYNTHETIC_CODE_DRIFT'
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',read)
    def backend():
        changed[0]=True
        return dict(intent=h,intent_generation='VALUATION_INTENT',session=args['session'])
    with pytest.raises(ValueError,match='code_changed'):
        asyncio.run(entry.run_registered_valuation_source(preflight=pre,base=tmp_path/'unused',external_root='unused',
            acquire_current_context=backend,load_credentials=lambda:pytest.fail('credentials'),inner=object(),enabled=True))


def test_plan_changed_after_seal_denied(tmp_path,monkeypatch):
    from app.services.valuation_research_preflight import prepare_registered_valuation
    pre,h,args=configure(tmp_path,monkeypatch)
    result=prepare_registered_valuation(**pre,enabled=True,
        acquire_current_context=lambda:dict(intent=h,intent_generation='VALUATION_INTENT',session=args['session']))
    plan=result['wire']['request_plan'].model_copy(update={'generation_id':'OTHER'})
    with pytest.raises(ValueError):pending.resolve_parent(result['parent'],plan=plan)


def test_default_off_no_scope_no_callbacks(tmp_path,monkeypatch):
    with pytest.raises(ValueError,match='enable'):
        asyncio.run(entry.run_registered_valuation_source(preflight={},base=tmp_path,external_root='unused'))
    pre,_,_=configure(tmp_path,monkeypatch)
    result=asyncio.run(entry.run_registered_valuation_source(preflight=pre,base=tmp_path/'unused',external_root='unused',enabled=True))
    assert result['status']=='NO_LIVE_NEW_OWNER' and result['physical_HTTP']==0
    assert not (tmp_path/'unused').exists()
