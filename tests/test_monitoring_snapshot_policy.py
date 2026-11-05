import asyncio,json
from copy import deepcopy
from datetime import datetime,timezone
from types import SimpleNamespace

import httpx
import pytest

from tests.test_p3g_pending_worker import prepared,pending
from tests.test_current_financial_parent_generality import registered,synthetic_clock,POLICY
from app.services import current_scoped_source_owner as owner
from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services.scoped_source_plan import (ScopedConfig,ScopedSubject,ScopedCaptureSelectionV2,
    ScopedMonitoringCaptureSelection,compile_scoped_wire_contract)
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.query_time_monitoring_price import project_monitoring_rows,consume_monitoring_price,validate_monitoring_readback
from app.services.semantic_stop_recovery import review_recovery
from app.services import kiwoom_global_lane as lane_module
from app.services.unified_snapshot_contract import digest
from app.services.unified_live_source_transport import SourceSafetyStop


@pytest.fixture
def run(prepared,tmp_path,monkeypatch):
    args,_,_=prepared;clock=synthetic_clock(monkeypatch,at=datetime.now(timezone.utc))
    monkeypatch.setattr(owner,'_now',clock.now)
    registration,doc,security=registered(tmp_path/'registration','UNSEEN','us',{'cik':'00000123'},run_id='C1R_TEST')
    subject=ScopedSubject(ticker='UNSEEN',market='us',security_id=security['canonical_security_id'],
        issuer_id=security['cik'],venue=security['exchange'],currency='USD')
    selection=ScopedMonitoringCaptureSelection(contract='scoped-monitoring-capture-selection-v1',
        stock_security_ids=(subject.security_id,),market_contexts=('us',),strict_close_security_ids=(subject.security_id,))
    config=ScopedConfig(subjects=(subject,),kr_history=args['config'].kr_history,
        us_history=args['config'].us_history,kr_max_pages=2,capture_selection=selection)
    at=datetime.fromisoformat(doc['cutoff'])
    wire=compile_scoped_wire_contract(config=config,identities={'UNSEEN':security},generation_id='C1R_TEST',
        at=at,code_sha='a'*40,provider_config_sha256='b'*64,retries=0)
    parent=owner.issue_parent(registration_owners={'us':registration},admitted_projections={'us':doc},
        spec=owner.ScopedSourceSpec(config=config,generation_id='C1R_TEST',cutoff=at,code_sha='a'*40,
            provider_config_sha256='b'*64,maximum_attempts=64),plan=wire['request_plan'],policy=POLICY,
        code_pins=owner.current_code_pins(),enabled=True)
    dispatch=CurrentScopedDispatcher(parent=parent,plan=wire['request_plan'],root=tmp_path/'capture',
        owners={d.normalizer:d.owner_sha256 for d in wire['request_plan'].descriptors},
        config_identities={'kiwoom':'b'*64},credential_presence={'kiwoom':True},
        secrets=('TEST_ONLY_TOKEN',),account_pacer=args['session']._lane)
    return dispatch,wire,config,args['session']._lane


def request_for(run,key):
    wire,_,_=run.resolve(key);v=json.loads(wire)
    return httpx.Request(v['method'],v['url'],headers=v['headers'],content=v['body'].encode())


@pytest.mark.parametrize('kind',['semantic','duplicate','wrong_date','envelope',401,403,429,'unknown',
    'wrong_security','bad_hash','lost_envelope','transport','oversize','valid_strict'])
def test_real_account_slot_quality_vs_hard_stop(run,kind):
    dispatch,wire,_,lane=run
    close=next(d for d in dispatch.plan.descriptors if d.endpoint_operation=='usa20590')
    target=close.target_period.replace('-','')
    row=dict(dt=target,open_pric='10',high_pric='12',low_pric='9',cur_prc='8' if kind=='semantic' else '11')
    if kind=='wrong_date':row['dt']='20000101'
    payload=dict(return_code=1 if kind=='envelope' else 0,result_list=[row,row] if kind=='duplicate' else [row])
    def respond(request):
        if kind=='transport':raise httpx.ConnectError('SYNTHETIC_TRANSPORT_FAILURE')
        if kind=='oversize':return httpx.Response(200,content=b'x'*(4*1024**2+1))
        if kind=='lost_envelope':return httpx.Response(200,content=b'not-json')
        if request.headers.get('api-id')!='usa20590':
            return httpx.Response(200,json=dict(return_code=0,result_list=[dict(row,cur_prc='11')]),headers={'cont-yn':'N','next-key':''})
        return httpx.Response(kind if isinstance(kind,int) else 200,json=payload,headers={'cont-yn':'N','next-key':''})
    transport=SealedSourceTransport(dispatch,httpx.MockTransport(respond),providers={'kiwoom'})
    async def go():
        if kind in ('wrong_security','bad_hash'):
            request=request_for(dispatch,close.logical_request_id)
            if kind=='bad_hash':
                (dispatch.root/'plan.json').write_text('{}')
            else:
                body=json.loads(request.content);body['stk_cd']='OTHER'
                request=httpx.Request(request.method,request.url,headers=request.headers,json=body)
            with pytest.raises((ValueError,SourceSafetyStop)):await transport.handle_async_request(request)
        elif kind=='valid_strict':
            await transport.handle_async_request(request_for(dispatch,close.logical_request_id))
            assert not dispatch.role_quality_denials and not lane._state()['halted']
        elif kind=='unknown':
            from app.services.sealed_source_transport import CapturedFragment
            class Broken(CapturedFragment):
                def __call__(self,raw):raise ValueError('UNKNOWN_NOT_A_SOURCE_QUALITY_CODE')
            with pytest.raises((ValueError,SourceSafetyStop)):
                await dispatch.execute(close.logical_request_id,request_for(dispatch,close.logical_request_id),
                    transport=httpx.MockTransport(respond),normalize=Broken(close))
        elif kind=='semantic':
            response=await transport.handle_async_request(request_for(dispatch,close.logical_request_id))
            assert response.status_code==200
            assert dispatch.role_quality_denials[close.logical_request_id].strict_close_eligible is False
            assert lane._state()['halted'] is False and not dispatch.halted
            # An independent chart and Market source request really traverse the
            # original dispatcher/account slots after the optional close denial.
            for d in (next(d for d in dispatch.plan.descriptors if d.endpoint_operation=='usa06012'),
                      next(d for d in dispatch.plan.descriptors if d.endpoint_operation=='usa10099')):
                await transport.handle_async_request(request_for(dispatch,d.logical_request_id))
            assert dispatch.physical_attempts==3 and lane._state()['halted'] is False
        else:
            with pytest.raises((ValueError,SourceSafetyStop)):await transport.handle_async_request(request_for(dispatch,close.logical_request_id))
        await transport.shutdown()
    asyncio.run(go())
    persisted=lane_module._read(lane.root/'state.json')
    assert persisted['halted'] is (kind not in ('semantic','valid_strict'))
    assert persisted['in_flight'] is False


def test_snapshot_selection_never_inherits_legacy_close_default(run):
    _,wire,config,_=run
    selection=config.capture_selection.model_copy(update={'strict_close_security_ids':()})
    snap=config.model_copy(update={'capture_selection':selection})
    identities={'UNSEEN':dict(canonical_security_id=snap.subjects[0].security_id,exchange=snap.subjects[0].venue)}
    out=compile_scoped_wire_contract(config=snap,identities=identities,generation_id='NEW',
        at=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64,retries=0)
    assert not any(d.endpoint_operation=='usa20590' for d in out['request_plan'].descriptors)
    strict=next(d for d in wire['request_plan'].descriptors if d.endpoint_operation=='usa20590')
    assert strict.mandatory is False
    assert ScopedCaptureSelectionV2(contract='scoped-capture-selection-v2',stock_security_ids=('x',)).us_completed_closes is True


def snapshot():
    at=datetime.now(timezone.utc);session=at.astimezone(__import__('zoneinfo').ZoneInfo('America/New_York')).date().isoformat()
    read=SimpleNamespace(timeframe='daily',market='us',count=2,latest_completed_session=session,
        canonical_security_id='security-unseen',subject='UNSEEN',exchange='ND',provider='kiwoom',
        owner='ohlcv_analyst.KiwoomProvider.get_bars',api_id='usa06012',route='/api/us/chart',adjusted=True)
    rows=[dict(date=session,open=10,high=12,low=9,close=11)]
    read.count=1
    options=dict(read=read,frozen_at=at,observed_at=at,source_pages=[dict(page=1,sha256='a'*64)])
    return rows,options


@pytest.mark.parametrize('mutation',['valid','FINAL','strict','basis','security','bad_latest','bad_older','valuation','duplicate_latest'])
def test_snapshot_value_and_consumer_bounds(mutation):
    rows,options=snapshot()
    if mutation=='bad_latest':rows[0]['close']=8
    if mutation=='bad_older':
        rows.insert(0,dict(rows[0],date='2000-01-03',close=8));options['read'].count=2
    if mutation=='duplicate_latest':rows.append(dict(rows[0],close=10));options['read'].count=2
    value=project_monitoring_rows(rows,**options)
    if mutation in ('bad_latest','duplicate_latest'):
        assert value['observation'] is None and not value['window_eligible'];return
    if mutation=='bad_older':
        assert value['observation'] and not value['window_eligible']
        with pytest.raises(ValueError):consume_monitoring_price(value,security_id='security-unseen',adjusted=True,use='SOURCE_ONLY_TECHNICAL_REFERENCE')
        return
    if mutation=='FINAL':value['observation']['finality_claim']='FINAL'
    if mutation=='strict':value['strict_close_eligible']=True
    kwargs=dict(security_id='wrong' if mutation=='security' else 'security-unseen',adjusted=mutation!='basis',
        use='VALUATION_DENOMINATOR' if mutation=='valuation' else 'SOURCE_ONLY_DISPLAY')
    if mutation=='valid':
        assert consume_monitoring_price(value,**kwargs)['finality_claim']=='NOT_CLAIMED'
        assert validate_monitoring_readback(value,rows=rows,**options)['strict_close_eligible'] is False
    else:
        with pytest.raises(ValueError):consume_monitoring_price(value,**kwargs)


def test_recovery_review_refuses_boolean_only_stop(run):
    _,_,_,lane=run
    asyncio.run(lane.halt())
    before=lane_module._read(lane.root/'state.json')
    value=review_recovery(lane,expected_state_sha256=digest(before),expected_lock_identity=lane.lock_identity)
    assert value['recovery_executable'] is False and value['STOP_reset'] is False
    assert lane_module._read(lane.root/'state.json')==before
    with pytest.raises(ValueError):review_recovery(lane,expected_state_sha256='0'*64,expected_lock_identity=lane.lock_identity)


def test_legacy_production_profile_still_requires_all_us_closes():
    from app.services.production_source_plan import ProductionRequestPlan,VALIDATORS
    from app.services.unified_stock_acquisition import UNIVERSE
    with pytest.raises(ValueError,match='PLAN_GAP_usa20590_14_of_14'):
        ProductionRequestPlan.production_binding(SimpleNamespace(subjects=UNIVERSE['us'],market='us',
            generation_id='run-attempt-1',attempt_id='run-attempt-1',run_id='run',
            validator_contracts=VALIDATORS,kis_plan_sha256=None,descriptors=[]))
