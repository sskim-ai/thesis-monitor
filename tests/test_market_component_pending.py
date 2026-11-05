"""C3R new Market-only boundaries; no live Provider or registration query."""
import asyncio,hashlib,json,os
from datetime import datetime,timedelta,timezone
from pathlib import Path
import httpx
import pytest
from tests.test_p3g_pending_worker import local_read_closure
from app.services import pending_source_parent as adapter,prospective_class_c_owner as grants
from app.services import current_scoped_source_dispatch as dispatch,current_scoped_worker_bridge as bridge_module
from app.services import scoped_worker_launch as launch,sealed_source_transport as sealed
from app.services.scoped_source_plan import ScopedMarketComponentConfig,ScopedCaptureSelection,HistoryCounts,ScopedConfig
from app.services.same_session_market_windows import SameSessionWindows
from app.services.market_worker_rpc import MarketWorkerRPC
from app.services.scoped_external_code_manifest import REQUIRED_V2,CONTRACT_V2
from app.services.unified_snapshot_contract import encoded

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def prepared(tmp_path,monkeypatch):
    from app.services import kiwoom_global_lane as lane
    from app.services.kiwoom_participant_session import ParticipatingSession
    directory=tmp_path/'isolated-market-test-lane';directory.mkdir(mode=0o700)
    boot=lane.boot_identity()
    lane._atomic(directory/'activation.json',dict(protocol=lane.PROTOCOL,generation='SYNTHETIC_C3R',
        boot_identity=boot,implementation_sha256=hashlib.sha256(Path(lane.__file__).read_bytes()).hexdigest()))
    lane._atomic(directory/'state.json',dict(protocol=lane.PROTOCOL,generation='SYNTHETIC_C3R',
        boot_identity=boot,last_end=None,in_flight=False,halted=False,sequence=0,pid=os.getpid()))
    fd=os.open(directory/'lane.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    monkeypatch.setattr(lane,'_loaded_lane',lane.GlobalKiwoomLane(directory))
    session=ParticipatingSession(modules=(dispatch,bridge_module,launch,sealed),caller_kind='CLI')
    return dict(session=session),None,tmp_path

def market_args(prepared,market):
    old,_,tmp=prepared;now=datetime.now(timezone.utc)
    approval=grants.record_backend_approval(grants.ApprovalDecision(event_id='SYNTHETIC_C3R',
        user_message_sha256='a'*64,approved=True,effective_at=now,expires_at=now+timedelta(minutes=10),
        subjects=('market:kr','market:us')))
    counts=HistoryCounts(adjusted_daily=2,adjusted_weekly=2,adjusted_monthly=2,unadjusted_weekly_valuation=2)
    config=ScopedMarketComponentConfig(kr_history=counts,us_history=counts,kr_max_pages=20,
        capture_selection=ScopedCaptureSelection(stock_markets=(),stock_roles=(),market_contexts=(market,),us_completed_closes=False))
    return dict(approval=approval,config=config,session=old['session'],generation_id='SYNTHETIC_C3R_'+market,
        cutoff=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64,
        maximum_attempts=49 if market=='kr' else 56,enabled=True),tmp

@pytest.mark.parametrize('market,maximum',[('kr',49),('us',56)])
def test_market_only_exact_plan_no_class_c_or_native(prepared,market,maximum):
    args,_=market_args(prepared,market)
    assert type(ScopedConfig.model_validate(args['config'])) is ScopedMarketComponentConfig
    parent,wire=adapter.issue_market_component_parent(**args)
    assert not wire['stock_reads']
    assert sum(d.max_transport_attempts for d in wire['request_plan'].descriptors)==(49 if market=='kr' else 48)
    r=adapter.resolve_parent(parent)
    assert r['ClassC']=='NOT_ISSUED_NOT_REQUIRED_FOR_MARKET_COMPONENTS'
    assert not r['MarketParent'] and not r['model_use'] and not r['full22_native']
    with pytest.raises(ValueError,match='one_use'):adapter.issue_market_component_parent(**args)
    with pytest.raises(ValueError):adapter.resolve_parent(adapter.public_handoff(parent))

def test_market_does_not_widen_original_stock_parent(prepared):
    market,_=market_args(prepared,'kr')
    old={k:v for k,v in market.items() if k!='approval'}
    with pytest.raises(ValueError,match='chart_price_only'):
        adapter.issue_parent(**dict(old,intake_owner=None,maximum_attempts=20))
    with pytest.raises(ValueError):
        adapter.issue_market_component_parent(**dict(market,maximum_attempts=20))

def test_original_market_worker_rpc_two_replays(prepared):
    args,tmp=market_args(prepared,'kr');parent,wire=adapter.issue_market_component_parent(**args)
    plan=wire['request_plan']
    def respond(request):
        body=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959',token_type='Bearer') if request.url.path=='/oauth2/token' else dict(return_code=0,cur_prc='100',test_only=True)
        return httpx.Response(200,json=body,headers={'cont-yn':'N','next-key':''})
    run=dispatch.CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp/'market-capture',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},config_identities={'kiwoom':'b'*64},
        credential_presence={'kiwoom':True},secrets=(*launch.DUMMY.values(),'TEST_ONLY_TOKEN'),account_pacer=args['session']._lane)
    transport=sealed.SealedSourceTransport(run,httpx.MockTransport(respond),providers={'kiwoom'})
    windows=SameSessionWindows(transport)
    out=tmp/'market-worker';out.mkdir(mode=0o700);external=Path('/Users/sskim/Codex/ohlcv-analyst')
    pins={n:dict(bytes=(external/n).stat().st_size,sha256=hashlib.sha256((external/n).read_bytes()).hexdigest()) for n in REQUIRED_V2}
    stock=dict(contract='current-scoped-stock-capture-v1',run_id=plan.generation_id,acquisition_id=plan.generation_id,
        frozen_at=plan.frozen_at.isoformat(),reads=[],owner_files=json.loads(wire['owner_files_json']))
    envelope=dict(stage=str(ROOT),output=str(out),external_root=str(external),external_pins=pins,
        external_code_contract=CONTRACT_V2,stock_plan=stock,request_interval=1.5,
        latest_completed_us_session=grants.completed_clock('us',plan.frozen_at)['target'],us_market_symbols=[],
        read_paths=local_read_closure()+[str(external/n) for n in sorted(pins)],pending_handoff=adapter.public_handoff(parent),
        market_wire_templates={d.logical_request_id:d.model_dump(mode='json') for d in plan.descriptors})
    frozen=tmp/'market-frozen.json';frozen.write_bytes(encoded(envelope))
    bridge=bridge_module.ScopedBridge(parent=parent,original_plan=plan,transport=transport,physical_windows=windows,
        worker=ROOT/'scripts/current_scoped_source_worker.py',frozen=frozen,sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),
        output=out,credentials=dict(launch.DUMMY),market_reads=[],source_session=args['session'],custody_policy=launch.CUSTODY_POLICY)
    async def go():
        rpc=MarketWorkerRPC(bridge)
        from app.services.scoped_source_plan import kiwoom_request
        auth=httpx.Request('POST','https://api.kiwoom.com/oauth2/token',
            headers={'Content-Type':'application/json;charset=UTF-8'},
            json=dict(grant_type='client_credentials',appkey=launch.DUMMY['app_key'],secretkey=launch.DUMMY['secret_key']))
        try:
            assert (await rpc.handle_async_request(auth)).status_code==200
            d=next(d for d in plan.descriptors if d.endpoint_operation=='ka20001')
            w=json.loads(d.request_json)
            request=kiwoom_request('ka20001',httpx.URL(w['url']).path,json.loads(w['body']))
            request.headers['authorization']='Bearer TEST_ONLY_TOKEN'
            assert (await rpc.handle_async_request(request)).status_code==200
            for n in (1,2):
                r=await bridge.command({'market_replay':n})
                assert r['status']=='MARKET_COMPONENT_RAW_REPLAY_PASS'
            raw=next(out.glob('market-raw-*.body'));raw.write_bytes(b'{}')
            # Cold never treats a matching receipt with changed bytes as usable.
            record=json.loads((out/'market-replay-1.json').read_bytes())[0]
            assert hashlib.sha256(raw.read_bytes()).hexdigest()!=record['sha256']
        finally:await bridge.shutdown();await transport.shutdown()
    asyncio.run(go())
    assert run.physical_attempts==2 and bridge._pending_ack
