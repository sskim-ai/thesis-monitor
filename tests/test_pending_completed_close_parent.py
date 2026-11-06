"""C12 synthetic isolated contracts, not live registration or price authority."""
import asyncio,hashlib,json,os
from datetime import datetime,timedelta,timezone
from pathlib import Path

import httpx
import pytest
from sqlmodel import Session,create_engine

from app.services import pending_source_intake as intake,pending_source_parent as parent
from app.services import prospective_class_c_owner as grants,kiwoom_global_lane as lane
from app.services import current_scoped_source_dispatch as dispatch,current_scoped_worker_bridge as bridge
from app.services import scoped_worker_launch as launch,sealed_source_transport as sealed
from app.services import pending_completed_close_contract as contract
from app.services.kiwoom_participant_session import ParticipatingSession
from app.services.minimal_class_c_export import MODELS,ExportPermission,capture_authorized_class_c,captured_private_snapshot
from app.services.scoped_source_plan import ScopedConfig,ScopedSubject,ScopedPriceCaptureSelection,ScopedCaptureSelectionV2,HistoryCounts
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.unified_snapshot_contract import digest

@pytest.fixture
def case(tmp_path,monkeypatch):
    now=datetime.now(timezone.utc);subjects=tuple(UNIVERSE['us'])
    approval=grants.record_backend_approval(grants.ApprovalDecision(event_id='SYNTHETIC_C12',
        user_message_sha256='a'*64,approved=True,effective_at=now-timedelta(seconds=1),expires_at=now+timedelta(minutes=10),subjects=subjects))
    scope=intake.record_backend_intake_scope(approval=approval,generation_id='SYNTHETIC_C12',source_generation_id='SYNTHETIC_C12',
        exclusive_use_confirmed=True,confirmation_sha256='b'*64,confirmed_at=now,enabled=True)
    db=tmp_path/'SYNTHETIC.sqlite3';engine=create_engine('sqlite:///'+str(db))
    for model in MODELS.values():model.__table__.create(engine,checkfirst=True)
    selections=[]
    with Session(engine) as s:
        for i,ticker in enumerate(subjects):
            venue=('NASDAQ','NYSE','AMEX')[i%3];sid='synthetic-security-'+str(i);issuer=str(i+1).zfill(10)
            s.add(MODELS['company'](ticker=ticker,company_name='SYNTHETIC',exchange=venue))
            s.add(MODELS['securitymaster'](ticker=ticker,company_name='SYNTHETIC',exchange=venue,country='US',
                canonical_company_id='synthetic-issuer-'+str(i),canonical_security_id=sid,cik=issuer))
            s.add(MODELS['watchlistitem'](ticker=ticker,company_name='SYNTHETIC',exchange=venue,
                active=False,production_eligible=False,monitoring_requested=True,onboarding_state='PENDING_ONBOARDING'))
            s.add(MODELS['investmentthesis'](ticker=ticker,version=1,status='active',core_thesis='TEST_ONLY'))
            selections.append(ScopedSubject(ticker=ticker,market='us',security_id=sid,issuer_id=issuer,venue=venue,currency='USD'))
        s.commit()
    st=db.stat();capture=capture_authorized_class_c(ExportPermission('SYNTHETIC_C12',True,db,st.st_dev,st.st_ino,subjects))
    raw,receipt=captured_private_snapshot(capture)
    owner,_=intake.issue_intake(scope=scope,capture=capture,market='us',expected_capture_sha256=digest(json.loads(raw)),enabled=True)
    directory=tmp_path/'SYNTHETIC_LANE';directory.mkdir(mode=0o700)
    boot='SYNTHETIC_BOOT';monkeypatch.setattr(lane,'boot_identity',lambda:boot)
    lane._atomic(directory/'activation.json',dict(protocol=lane.PROTOCOL,generation='SYNTHETIC_C12',boot_identity=boot,
        implementation_sha256=hashlib.sha256(Path(lane.__file__).read_bytes()).hexdigest()))
    lane._atomic(directory/'state.json',dict(protocol=lane.PROTOCOL,generation='SYNTHETIC_C12',boot_identity=boot,
        last_end=None,in_flight=False,halted=False,sequence=0,pid=os.getpid()))
    fd=os.open(directory/'lane.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    selected=lane.GlobalKiwoomLane(directory,boot=lambda:boot)
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1');monkeypatch.setattr(lane,'_loaded_lane',selected)
    session=ParticipatingSession(modules=(dispatch,bridge,launch,sealed),caller_kind='CLI')
    counts=HistoryCounts(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,unadjusted_weekly_valuation=300)
    config=ScopedConfig(subjects=tuple(selections),kr_history=counts,us_history=counts,kr_max_pages=7,
        capture_selection=ScopedPriceCaptureSelection(contract='scoped-price-capture-selection-v1',close_security_ids=tuple(s.security_id for s in selections)))
    args=dict(intake_owner=owner,config=config,session=session,generation_id='SYNTHETIC_C12',cutoff=datetime.fromisoformat(receipt['cutoff']),
        code_sha='a'*40,provider_config_sha256='b'*64,maximum_attempts=15,enabled=True)
    yield dict(args=args,owner=owner,scope=scope,approval=approval,root=tmp_path,lane=selected)
    if approval in grants._APPROVALS:grants.revoke_approval(approval)
    engine.dispose()

def test_full_typed_plan_and_no_current_rights(case):
    p,wire=parent.issue_completed_close_parent(**case['args'])
    value=parent.resolve_parent(p)
    assert value['scope']==contract.PURPOSE and value['contract']==contract.CONTRACT
    assert not wire['stock_reads'] and len(wire['request_plan'].descriptors)==15
    assert all(d.mandatory for d in wire['request_plan'].descriptors)
    assert len(contract.requirements(case['args']['config'],wire))==14
    assert not any(value[k] for k in ('chart_coverage','current_authority','valuation_use','economic_use','full22_native','D01_D02','model_use'))
    assert intake.require_live_worker_adapter(case['owner'],parent=p)['scope']==contract.PURPOSE
    from app.services import current_scoped_source_owner as active
    with pytest.raises(ValueError):active.resolve_parent(p)

def test_original_chart_parent_still_rejects_empty_reads(case):
    with pytest.raises(ValueError,match='original_chart_reads_required'):parent.issue_parent(**case['args'])

def test_legacy_chart_parent_unchanged(case):
    args=case['args'];subject=args['config'].subjects[0]
    selection=ScopedCaptureSelectionV2(contract='scoped-capture-selection-v2',stock_security_ids=(subject.security_id,),
        stock_roles=('adjusted_daily',),market_contexts=(),us_completed_closes=False)
    config=args['config'].model_copy(update={'subjects':(subject,),'capture_selection':selection})
    p,wire=parent.issue_parent(**dict(args,config=config))
    assert parent.resolve_parent(p)['scope']==parent.PURPOSE and len(wire['stock_reads'])==1

@pytest.mark.parametrize('mutation',['subset','missing_id','KR','identity','generation','budget','disabled','expired','revoked','PID','code','stopped_lane'])
def test_bad_authority_and_selection_denied(case,mutation,monkeypatch):
    args=dict(case['args']);config=args['config']
    if mutation=='subset':args['config']=config.model_copy(update={'subjects':config.subjects[:-1]})
    elif mutation=='missing_id':args['config']=config.model_copy(update={'capture_selection':config.capture_selection.model_copy(update={'close_security_ids':config.capture_selection.close_security_ids[:-1]})})
    elif mutation=='KR':args['config']=config.model_copy(update={'subjects':(config.subjects[0].model_copy(update={'market':'kr','venue':'KRX','currency':'KRW'}),)+config.subjects[1:]})
    elif mutation=='identity':args['config']=config.model_copy(update={'subjects':(config.subjects[0].model_copy(update={'issuer_id':'wrong'}),)+config.subjects[1:]})
    elif mutation=='generation':args['generation_id']='OLD'
    elif mutation=='budget':args['maximum_attempts']=14
    elif mutation=='disabled':args['enabled']=False
    elif mutation=='expired':intake._SCOPES[case['scope']]['expires']=datetime.now(timezone.utc)-timedelta(seconds=1)
    elif mutation=='revoked':grants.revoke_approval(case['approval'])
    elif mutation=='PID':monkeypatch.setattr(intake.os,'getpid',lambda:-1)
    elif mutation=='code':monkeypatch.setattr(parent,'pins',lambda:{'tampered':'x'})
    elif mutation=='stopped_lane':
        state=lane._read(case['lane'].root/'state.json');state['halted']=True;lane._atomic(case['lane'].root/'state.json',state)
    if mutation=='code':
        p,_=parent.issue_completed_close_parent(**args)
        if mutation=='code':monkeypatch.setattr(parent,'pins',lambda:{'changed':'y'})
        with pytest.raises((ValueError,RuntimeError)):parent.resolve_parent(p)
    else:
        with pytest.raises((ValueError,RuntimeError)):parent.issue_completed_close_parent(**args)

@pytest.mark.parametrize('mutation',['optional','retry','operation','extra','session'])
def test_original_compiled_descriptor_contract_is_rechecked(case,mutation):
    p,wire=parent.issue_completed_close_parent(**case['args'])
    state=parent._LIVE[p];plan=wire['request_plan'];descriptors=list(plan.descriptors)
    d=descriptors[1]
    updates={'optional':{'mandatory':False},'retry':{'transient_retry_max':1},'operation':{'endpoint_operation':'usa06012'},
        'session':{'target_period':'2000-01-01'}}
    if mutation=='extra':descriptors.append(descriptors[-1])
    else:descriptors[1]=d.model_copy(update=updates[mutation])
    state['wire']=dict(state['wire'],request_plan=plan.model_copy(update={'descriptors':tuple(descriptors)}))
    with pytest.raises(ValueError):parent.resolve_parent(p)

def test_no_reissue_restore_or_revoked_receipt(case):
    p,_=parent.issue_completed_close_parent(**case['args'])
    with pytest.raises(ValueError,match='one_dispatch'):parent.issue_completed_close_parent(**case['args'])
    with pytest.raises(ValueError):parent.resolve_parent(parent.public_handoff(p))
    parent.revoke_parent(p)
    with pytest.raises(ValueError):parent.resolve_parent(p)

@pytest.mark.parametrize('kind',['chart','market','wrong_scope','wire'])
def test_worker_cannot_expand_price_scope(case,kind):
    p,wire=parent.issue_completed_close_parent(**case['args']);plan=wire['request_plan'];d=plan.descriptors[1]
    handoff=parent.public_handoff(p);stock=dict(reads=[],run_id=plan.generation_id)
    templates={x.logical_request_id:x.model_dump(mode='json') for x in plan.descriptors}
    command={'market_wire':dict(logical_id=d.logical_request_id,request_json=d.request_json)}
    assert contract.validate_worker_command(handoff,stock,templates,command)
    if kind=='chart':stock['reads']=[{}]
    elif kind=='market':command={'market':'SPY'}
    elif kind=='wrong_scope':handoff['scope']=parent.PURPOSE
    else:command['market_wire']['request_json']=d.request_json.replace('/api/us/mrkcond','/api/us/chart')
    with pytest.raises(PermissionError):contract.validate_worker_command(handoff,stock,templates,command)

def test_original_isolated_worker_and_completed_owner_all_fourteen(case):
    from app.services import market_component_execution as execution,current_scoped_source_results as results
    from app.services.kiwoom_completed_close_owner import OFFICIAL_SPEC_SHA256
    import gzip
    p,wire=parent.issue_completed_close_parent(**case['args']);plan=wire['request_plan']
    target=next(s.target.isoformat() for s in wire['sessions'] if s.market=='us')
    calls=[]
    def respond(request):
        calls.append((request.url.path,request.headers.get('api-id')))
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959',token_type='Bearer'))
        assert request.headers['api-id']=='usa20590'
        return httpx.Response(200,json=dict(return_code=0,result_list=[dict(dt=target.replace('-',''),
            open_pric='100',high_pric='110',low_pric='90',cur_prc='105')]),headers={'cont-yn':'N','next-key':''})
    base=case['root']/'TEST_ONLY_CAPTURE'
    run,transport,worker,_=execution.prepare_capture(parent=p,wire=wire,session=case['args']['session'],base=base,
        credentials=dict(launch.DUMMY),inner=httpx.MockTransport(respond),external_root='/Users/sskim/Codex/ohlcv-analyst',completed_close_only=True)
    frozen=json.loads((base/'frozen.json').read_bytes());stock=frozen['stock_plan']
    results.bind_capture(p,wire,stock,run,run.root,worker.output,worker)
    doc=gzip.decompress(Path(__file__).with_name('fixtures').joinpath('kiwoom_completed_close_official.json.gz').read_bytes())
    assert hashlib.sha256(doc).hexdigest()==OFFICIAL_SPEC_SHA256
    (run.root/'documentation').write_bytes(doc)
    async def go():
        try:
            for d in plan.descriptors:
                if d.endpoint_operation!='usa20590':continue
                request,_,_=run.resolve(d.logical_request_id)
                reply=await worker.command({'market_wire':dict(logical_id=d.logical_request_id,request_json=request)})
                assert reply['status']==200,reply
            _,spec,scoped,capture_plan,capture_root,_=results._context(p,wire,stock,run,run.root,worker.output)
            price_plan,reads=results._completed_close_inputs(spec,capture_plan)
            values=[results._close(price_plan,r,spec,scoped,run,capture_root,dict(path='documentation',sha256=OFFICIAL_SPEC_SHA256)) for r in reads]
            assert len(values)==14 and all(v['state']['state']=='AVAILABLE' for v in values)
            assert all(v['native_use'] is False and v['economic_use'] is False for v in values)
            with pytest.raises(ValueError):
                results._close(price_plan,reads[0],spec,scoped,run,capture_root,dict(path='documentation',sha256='0'*64))
            assert worker._pending_ack and run.physical_attempts==15
        finally:await worker.shutdown();await transport.shutdown()
    asyncio.run(go())
    assert len(calls)==15 and calls[0][0]=='/oauth2/token' and worker.process.returncode==0
    assert not frozen['stock_plan']['reads']
    receipt=os.environ.get('C12_MOCK_WORKER_RECEIPT')
    if receipt:
        Path(receipt).write_text(json.dumps(dict(status='ORIGINAL_KERNEL_ISOLATED_CLOSE_ONLY_MOCK_PASS',
            mock_HTTP=15,financial_HTTP=0,original_numeric_Owners=14,chart_reads=0,authenticated_worker=True,
            real_Source=False,native_ready=False,worker_exit=worker.process.returncode)))
