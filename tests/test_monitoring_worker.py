"""Original isolated Worker -> Source-only snapshot -> independent Cold."""
import asyncio,base64,hashlib,json,os,subprocess,sys
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
import httpx

from tests.test_p3g_pending_worker import prepared,pending,local_read_closure,ROOT
from app.services import pending_source_parent as parent_module,current_scoped_source_results as results
from app.services import current_scoped_source_dispatch as dispatch,current_scoped_worker_bridge as bridge_module
from app.services import scoped_worker_launch as launch,sealed_source_transport as sealed
from app.services.scoped_source_plan import ScopedMonitoringCaptureSelection
from app.services.scoped_external_code_manifest import REQUIRED_V2,CONTRACT_V2
from app.services.registered_source_batch import Batch
from app.services.prospective_class_c_owner import completed_clock
from app.services.unified_snapshot_contract import digest,encoded


def test_original_worker_chart_survives_optional_strict_quality_and_cold(prepared):
    args,_,tmp=prepared
    config=args['config'];sid=config.subjects[0].security_id
    selection=ScopedMonitoringCaptureSelection(contract='scoped-monitoring-capture-selection-v1',
        stock_security_ids=(sid,),stock_roles=('adjusted_daily',),market_contexts=(),strict_close_security_ids=(sid,))
    config=config.model_copy(update={'capture_selection':selection})
    parent,wire=parent_module.issue_parent(**dict(args,config=config,maximum_attempts=4))
    plan=wire['request_plan'];read=wire['stock_reads'][0]
    prior=str(next(s.prior for s in wire['sessions'] if s.market=='us'))
    rows=[dict(dt=d.replace('-',''),open_pric='10',high_pric='12',low_pric='9',cur_prc='11',trde_qty='100')
        for d in (read.latest_completed_session,prior)]
    def respond(request):
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959',token_type='Bearer'))
        body=[dict(rows[0],cur_prc='8')] if request.headers.get('api-id')=='usa20590' else rows
        return httpx.Response(200,json=dict(return_code=0,result_list=body),headers={'cont-yn':'N','next-key':''})
    run=dispatch.CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp/'capture',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},config_identities={'kiwoom':'b'*64},
        credential_presence={'kiwoom':True},secrets=(*launch.DUMMY.values(),'TEST_ONLY_TOKEN'),account_pacer=args['session']._lane)
    transport=sealed.SealedSourceTransport(run,httpx.MockTransport(respond),providers={'kiwoom'})
    external=Path('/Users/sskim/Codex/ohlcv-analyst')
    pins={n:dict(bytes=(external/n).stat().st_size,sha256=hashlib.sha256((external/n).read_bytes()).hexdigest()) for n in REQUIRED_V2}
    output=tmp/'worker';output.mkdir(mode=0o700)
    stock=dict(contract='current-scoped-stock-capture-v1',run_id='SYNTHETIC',acquisition_id='C1R_SYNTHETIC',
        frozen_at=plan.frozen_at.isoformat(),reads=[r.model_dump(mode='json') for r in wire['stock_reads']],owner_files=json.loads(wire['owner_files_json']))
    envelope=dict(stage=str(ROOT),output=str(output),external_root=str(external),external_pins=pins,
        external_code_contract=CONTRACT_V2,stock_plan=stock,request_interval=1.5,
        latest_completed_us_session=read.latest_completed_session,us_market_symbols=[],
        read_paths=local_read_closure()+[str(external/n) for n in sorted(pins)],pending_handoff=parent_module.public_handoff(parent))
    frozen=tmp/'frozen.json';frozen.write_bytes(encoded(envelope))
    bridge=bridge_module.ScopedBridge(parent=parent,original_plan=plan,transport=transport,
        worker=ROOT/'scripts/current_scoped_source_worker.py',frozen=frozen,
        sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=output,credentials=dict(launch.DUMMY),
        market_reads=[],source_session=args['session'],custody_policy=launch.CUSTODY_POLICY)
    results.bind_capture(parent,wire,stock,run,run.root,output,bridge)
    async def go():
        try:
            assert (await bridge.command({'stocks':True}))['status']=='CAPTURE_COMPLETE_NOT_QUALIFIED'
            for number in (1,2):assert (await bridge.command({'replay':number}))['status']=='REPLAY_RESULT'
            assert (await bridge.command({'monitoring':read.entry_id}))['status']=='QUERY_TIME_SNAPSHOT_REPLAY_PASS'
            from app.services.canonical_source_plan import kiwoom_request
            request=kiwoom_request('usa20590','/api/us/mrkcond',dict(stex_tp=read.exchange,stk_cd=read.subject,
                base_dt=read.latest_completed_session.replace('-','')))
            request.headers['authorization']='Bearer TEST_ONLY_TOKEN'
            await transport.handle_async_request(request)
            assert run.role_quality_denials and args['session']._lane._state()['halted'] is False
        finally:await bridge.shutdown();await transport.shutdown()
    asyncio.run(go())
    capability=results.issue_source_result(parent,dispatcher=run,entry_id=read.entry_id)
    value=results.read_source_rows(parent,capability,dispatcher=run,entry_id=read.entry_id)
    assert value['receipt']['monitoring_snapshot']['observation']['finality_claim']=='NOT_CLAIMED'
    assert value['receipt']['native_use'] is False and len(value['rows'])==2
    dates={m:completed_clock(m,datetime.now(timezone.utc))['target'] for m in ('kr','us')}
    batch=Batch('C1R_SYNTHETIC_COLD',(sid,),('adjusted_daily',),tuple(sorted(dates.items())),
        (datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),4)
    raw=encoded(value['rows'])
    data=dict(contract='registered-source-batch-cold-v1',batch=batch.public(),batch_id=batch.batch_id,
        batch_sha256=digest(batch.public()),plan=run.plan.model_dump(mode='json'),receipts=[value['receipt']],
        expected_reads=[read.model_dump(mode='json')],artifacts=[dict(entry_id=read.entry_id,sha256=hashlib.sha256(raw).hexdigest())])
    code="""import json,base64,sys
from app.services.registered_source_batch import validate_cold_roles
x=json.load(sys.stdin);r=base64.b64decode(x['raw']);print(json.dumps(validate_cold_roles(x['data'],lambda a:(r,json.loads(r)))))
"""
    for mutation in ('none','FINAL','strict'):
        payload=dict(data=deepcopy(data),raw=base64.b64encode(raw).decode())
        if mutation!='none':
            receipt=payload['data']['receipts'][0]
            receipt['monitoring_snapshot']['finality_claim' if mutation=='FINAL' else 'strict_close_eligible']='FINAL' if mutation=='FINAL' else True
            receipt['receipt_sha256']=digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
        r=subprocess.run([sys.executable,'-B','-c',code],input=json.dumps(payload),capture_output=True,text=True,cwd=ROOT,
            env={**os.environ,'THESIS_MONITOR_ENV_FILE':''},timeout=30)
        assert (r.returncode==0)==(mutation=='none'),r.stderr
