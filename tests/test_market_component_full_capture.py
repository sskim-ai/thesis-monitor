"""C4 whole original isolated collector paths, synthetic responses only."""
import asyncio,json,os,subprocess,sys
from copy import deepcopy
from pathlib import Path
import httpx
import pytest
from tests.test_market_component_pending import prepared,market_args
from tests.test_kiwoom_rest_market_context import _current,_sector_rows,_aggregate,_stock_rows
from app.services import market_component_execution as execution,pending_source_parent as owners
from app.services.scoped_worker_launch import DUMMY
from app.services.unified_snapshot_contract import encoded

def response_handler(plan):
    from app.services.scoped_source_plan import _sessions
    from app.macro.providers.market import MARKET_SYMBOLS
    pair={p.market:p for p in _sessions(plan.frozen_at)[1]}
    def respond(request):
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959'))
        body=json.loads(request.content);api=request.headers['api-id']
        page=int(request.headers['next-key']) if request.headers.get('cont-yn')=='Y' else 1
        more=False
        if api=='usa10099':
            data=dict(result_list=[dict(stk_cd=s,stk_nm=s,stex_tp='ND') for s in MARKET_SYMBOLS] if body['stex_tp']=='ND' else [])
        elif api=='usa06012':
            day=pair['us'].target if page==1 else pair['us'].prior
            dates=(pair['us'].target,pair['us'].prior) if os.environ.get('C4_DRAIN_MOCK') else (day,)
            data=dict(result_list=[dict(dt=x.strftime('%Y%m%d'),open_pric='10',high_pric='12',low_pric='9',cur_prc='11',trde_qty='100') for x in dates]);more=page==1
        elif api=='ka20001':data=_current(body['inds_cd'])
        elif api=='ka20003':data=dict(all_inds_idex=_sector_rows(body['inds_cd']))
        elif api=='ka20009':
            current=_current(body['inds_cd'])
            data=dict(inds_cur_prc_daly_rept=[dict(dt_n=d.strftime('%Y%m%d'),cur_prc_n=current['cur_prc'],flu_rt_n=current['flu_rt']) for d in (pair['kr'].target,pair['kr'].prior)])
        elif api=='ka10051':data=_aggregate('001' if body['mrkt_tp']=='0' else '101')
        elif api=='ka10066':
            code=body['mrkt_tp'];more=page<20
            rows=_stock_rows(code,page) if page<3 else [dict(stk_cd=f'{code}{page:03d}_AL',stk_nm='SYNTHETIC',frgnr_invsr='0',orgn='0',ind_invsr='0')]
            data=dict(opaf_invsr_trde=rows)
        else:raise AssertionError(api)
        return httpx.Response(200,json=dict(data,return_code=0),headers={'cont-yn':'Y' if more else 'N','next-key':str(page+1) if more else ''})
    return respond

def create(prepared,market,inner):
    args,tmp=market_args(prepared,market);parent,wire=owners.issue_market_component_parent(**args)
    lane=args['session']._lane;clock=[0.0];lane.clock=lambda:clock[0]
    async def sleep(t):clock[0]+=t
    lane.async_sleep=sleep
    context=execution.prepare_capture(parent=parent,wire=wire,session=args['session'],base=tmp/(market+'-full'),
        credentials=dict(DUMMY),inner=inner(wire['request_plan']),external_root=Path('/Users/sskim/Codex/ohlcv-analyst'))
    return args,parent,wire,context

@pytest.mark.parametrize('market,physical',[('kr',49),('us',48)])
def test_full_original_isolated_market_owner_cold(prepared,market,physical):
    args,parent,wire,(run,transport,worker,windows)=create(prepared,market,lambda p:httpx.MockTransport(response_handler(p)))
    checkpoints=[]
    async def checkpoint():checkpoints.append(execution.sealed_checkpoint(run))
    result=asyncio.run(execution.execute_capture(market=market,config=args['config'],worker=worker,run=run,
        wire=wire,base=run.root.parent,credentials=dict(DUMMY),windows=windows,checkpoint=checkpoint))
    assert run.physical_attempts==physical and len(checkpoints)==1
    assert [r['physical_attempts'] for r in result['bundle']['windows']['windows']]==([20,20,9] if market=='kr' else [20,20,8])
    assert result['owner_receipt']['MarketParent']=='NOT_ISSUED'
    script='import json,sys;from app.services.market_component_execution import cold_component;print(json.dumps(cold_component(json.load(sys.stdin))))'
    child=subprocess.run([sys.executable,'-B','-c',script],input=json.dumps(result['bundle']),capture_output=True,
        text=True,timeout=60,env={**os.environ,'THESIS_MONITOR_ENV_FILE':''})
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)['MarketParent'] is False
    p=Path(os.environ['C4_FULL_MOCK_DIR']);p.mkdir(exist_ok=True)
    (p/(market+'-bundle.json')).write_bytes(encoded(result['bundle']))
    (p/(market+'-status.json')).write_bytes(encoded(dict(status='WHOLE_ORIGINAL_MOCK_E2E_PASS',physical=physical,
        windows=[r['physical_attempts'] for r in result['bundle']['windows']['windows']],two_replays=True,
        original_owner=True,new_process_Cold=True,real_HTTP=0,Worker_exit=worker.process.returncode)))

def test_current_plan_only_and_dataclass_only(prepared):
    args,_=market_args(prepared,'kr');parent,wire=owners.issue_market_component_parent(**args)
    with pytest.raises(ValueError):execution.preserve_plan(wire['request_plan'])
    with pytest.raises(ValueError):execution.normalize_observation(args['config'])
    owners._LIVE[parent]['pid']=-1
    with pytest.raises(ValueError):owners.resolve_parent(parent)
    owners._LIVE[parent]['pid']=os.getpid();owners.revoke_parent(parent)
    with pytest.raises(ValueError):owners.resolve_parent(parent)

@pytest.mark.parametrize('bad',['date','market','duplicate','missing','discovery','cursor','hash'])
def test_full_bundle_negative(bad):
    market='us' if bad=='discovery' else 'kr'
    p=Path(os.environ['C4_FULL_MOCK_DIR'])/(market+'-bundle.json')
    if not p.exists():pytest.skip('full original path must pass first')
    v=json.loads(p.read_bytes())
    if bad=='date':v['cutoff']='2000-01-01T00:00:00+00:00'
    elif bad=='market':v['market']='us'
    elif bad=='duplicate':v['commands'].append(deepcopy(next(r for r in v['commands'] if r['command']=={'market_replay':1})))
    elif bad=='missing':v['results'].pop(next(k for k in v['results'] if k!='kiwoom:auth'))
    elif bad=='discovery':
        d=next(r for r in v['plan']['descriptors'] if r.get('response_binding'))
        d['response_binding']['parents']=list(reversed(d['response_binding']['parents']))
    elif bad=='cursor':
        d=next(r for r in v['plan']['descriptors'] if r['endpoint_operation']=='ka10066' and r['page_ordinal']==20)
        d['request_json']=d['request_json'].replace('"next-key",""','"next-key","FORGED"')
        d['page_ordinal']=19
    else:v['owner_proof']['component_sha256']='0'*64
    with pytest.raises((ValueError,KeyError)):execution.cold_component(v)

@pytest.mark.parametrize('status',[401,403,429])
def test_auth_stop_before_market(prepared,status):
    args,parent,wire,(run,transport,worker,windows)=create(prepared,'kr',lambda p:httpx.MockTransport(lambda r:httpx.Response(status,json={'return_code':status})))
    async def checkpoint():raise AssertionError('must not reach Market')
    from app.services.unified_live_source_transport import SourceSafetyStop
    with pytest.raises(SourceSafetyStop):
        asyncio.run(execution.execute_capture(market='kr',config=args['config'],worker=worker,run=run,
            wire=wire,base=run.root.parent,credentials=dict(DUMMY),windows=windows,checkpoint=checkpoint))
    assert run.physical_attempts==1 and run.halted and worker.process.returncode is not None

def test_count_satisfied_but_original_tail_selected(prepared,monkeypatch):
    monkeypatch.setenv('C4_DRAIN_MOCK','1')
    test_full_original_isolated_market_owner_cold(prepared,'us',48)
