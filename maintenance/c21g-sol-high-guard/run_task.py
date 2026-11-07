"""Approved C21G only. Fresh original Stage/manual host; no finance or old DB."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl,hashlib,json,os,stat,subprocess,sys,time,traceback,uuid
from pathlib import Path
H=Path(os.environ['TM_C21G_TASK_ROOT']).resolve();R=H.parents[1];W=R/'work/thesis-monitor-vnext-balanced-20261029';sys.path.insert(0,str(W));sys.dont_write_bytecode=True
JOURNAL=Path('/private/tmp/c21g-sol-stage-journal-20261107')
def boundary(event,args):
    if event.startswith('socket.') and event in ('socket.connect','socket.getaddrinfo','socket.gethostbyname'):
        raise PermissionError('C21G_PARENT_PYTHON_NETWORK_DENIED')
    if event=='sqlite3.connect' and Path(args[0])!=JOURNAL/'research.sqlite3':
        raise PermissionError('C21G_ONLY_NEW_TASK_JOURNAL_DB_ALLOWED')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0]))
        if p.name.startswith('.env') or p.name=='auth.json':
            raise PermissionError('C21G_PARENT_SECRET_READ_DENIED')
        if len(args)>2 and isinstance(args[2],int) and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
            allowed=(H,JOURNAL,R/'private-runtime/c21f-guarded-host-20261107/runs/c21g-20261107')
            if not any(p.is_relative_to(root) for root in allowed):
                raise PermissionError('C21G_PARENT_WRITE_OUTSIDE_TASK')
sys.addaudithook(boundary)
from maintenance.guarded_sol_host import Binding,digest,write_once,TASK
from maintenance.guarded_sol_canary import run_stage
from maintenance.c21g_analysis_source import restore_view
from app.services import vnext_balanced_stage_review as stages
from app.services import vnext_unified_judgment as engine
from app.services.vnext_daily_research import UseRegistry
from app.services.vnext_execution_profile import SOL_HIGH_V1
from app.services.vnext_optional_fy1_research import attach
from app.services.vnext_codex_research import numeric_catalog
from app.services.vnext_research_store import ResearchStore
from app.services.vnext_runtime import RuntimeConfig
from app.services.vnext_public_capture import target_session
from app.services.vnext_unified_dispatch import consume

PACKET_SHA='3cc32a9e6abe78e404496172bcb9f16e21d5de09fe566dccb8673773f45cb4b9'
OUT=H/'private/live'

def git(*args):return subprocess.check_output(['git',*args],cwd=W,text=True).strip()
def current_disk():
    data=subprocess.check_output(['/bin/df','-k',str(H)],text=True);return int(data.splitlines()[-1].split()[3])*1024

def run():
    assert not (H/'LIVE_RESULT.json').exists() and not OUT.exists() and not JOURNAL.exists(),'FRESH_ONCE_ONLY'
    assert not git('status','--porcelain'),'WORKTREE_DRIFT'
    free=current_disk();assert free>=2*1024**3+256*1024**2
    write_once(H/'PRE_GC_LIVE.json',dict(task='C21G',timestamp=datetime.now(timezone.utc).isoformat(),free_bytes=free,peak_bytes=256*1024**2,reserve_bytes=2*1024**3,decision='PRE_GC_NOOP_SUFFICIENT',actions=[]))
    authorization=dict(task=TASK,basis='Current user: 실행 승인·현재 동시 사용 없음',profile=SOL_HIGH_V1.contract,model=SOL_HIGH_V1.model,effort=SOL_HIGH_V1.effort,packet_sha256=PACKET_SHA,maximum_contexts=2,stage_seconds=600,input_bytes=393216,output_bytes=131072,retries=0,new_private_journal=True,financial_HTTP=0,operating_DB=0,send=False,other_execution_confirmed_absent=True,at=datetime.now(timezone.utc).isoformat(),head=git('rev-parse','HEAD'))
    write_once(H/'USER_AUTHORIZATION.json',authorization,0o400)
    OUT.mkdir(mode=0o700)
    result=dict(status='PREMODEL_INITIALIZATION',model_attempts=0,accepted_stages=[],model_profile=SOL_HIGH_V1.contract,financial_HTTP=0,operating_DB=0,private_journal_created=False,retries=0,send=False)
    source_counts=None
    try:
        values=json.loads((H/'private/binding-final.json').read_bytes())
        for name in ('binary','catalog','legacy','root','scope'):values[name]=Path(values[name])
        binding=Binding(**values);runtime_scope=binding.verify()
        frozen_request=json.loads((H/'private/BLIND-request.json').read_bytes())
        rawpacket=(R/'maintenance/20261107-c21e/private/packet.json').read_bytes();packet=json.loads(rawpacket)
        assert digest(packet)==PACKET_SHA
        # Original factory/Owner consumption, not previous suites or financial IO.
        view,source_counts=restore_view(packet=packet,native_root=W/'data/vnext/c20r1-20261107',
            native_replay_sha256='ff7694dbb5dcada3e6e3382ab06966cc99edf1cd6e07fe6e5dfa6fac2267c297',
            kis_root=W/'data/vnext/c16-20261106/kis',kis_generation='C16_KIS_20261106',
            calibration_archive=Path.home()/'Documents/Codex/Reports/20261001-r2b-r9-rev40-r1-kr8-live-fper/thesis-monitor-20261001-r2b-r9-rev40-r1-kr8-live-fper-report.zip',
            calibration_sha256='34c3ade5f8b1f640f3d4f88b6aa6a35b82c2da3151ca1236a193addb7e571d35',
            dated_archive=Path.home()/'Library/Mobile Documents/com~apple~CloudDocs/Thesis Monitor/NG83/NG83_RESULT.zip',
            dated_archive_sha256='9dad6a7af153516941c3bbbe89b03f5c0561d233fe0b26de06cf93291bcbe1d5')
        registry=UseRegistry();ticker=packet['base']['public_security']['ticker']
        def economic_loader():
            base=view.packet(ticker);base['numeric_catalog']=numeric_catalog(base)
            return attach(base)
        def source_loader():
            if json.loads((R/'maintenance/20261107-c21e/private/packet.json').read_bytes())!=packet:
                raise ValueError('frozen_source_packet_changed')
            return engine.build_bundle(economic_loader(),registry=registry,contract=engine.AI_OWNED_V3,valuation_analysis_owner=view)
        assert source_loader()==packet,'ORIGINAL_LIVE_SOURCE_OWNER_PACKET_MISMATCH'
        result['original_source_owner_rebound']=True
        write_once(OUT/'SOURCE_BOUND.json',dict(packet_sha256=digest(packet),original_View_type=type(view).__name__,source_counts=source_counts,dated_only=True,new_financial_capture=0))
        # Read process arguments transiently, retain PIDs only. This plus the user's
        # current confirmation is not claimed to be a universal remote census.
        rows=subprocess.check_output(['/bin/ps','-axo','pid=,comm=,args='],text=True).splitlines()
        others=[]
        for row in rows:
            fields=row.strip().split(None,2)
            if len(fields)!=3 or not fields[0].isdigit() or int(fields[0]) in (os.getpid(),os.getppid()):continue
            if (Path(fields[1]).name=='codex' and ' exec ' in ' '+fields[2]+' ') or str(binding.binary) in fields[2]:others.append(int(fields[0]))
        write_once(OUT/'CALLERS.json',dict(other_analysis_PIDs=others,user_no_concurrency=True,scope='Local process observation plus current user confirmation'))
        assert not others,'OTHER_ANALYSIS_PROCESS_PRESENT'
        JOURNAL.mkdir(mode=0o700)
        ResearchStore(JOURNAL/'research.sqlite3')
        config=RuntimeConfig(JOURNAL/'research.sqlite3','C21G_SOL_HIGH_20261107',mode='write',environment='test');config.validate()
        result['private_journal_created']=True
        account=runtime_scope['account'];accepted={};requests={}
        @contextmanager
        def lease():
            fd=os.open(binding.root/'signed-in-analysis.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
            try:
                info=os.fstat(fd);assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                yield
            finally:os.close(fd)
        latest,_=target_session(packet['base']['public_security']['country'].lower(),datetime.now(timezone.utc))
        # Host calendar accounting only; it does not update any fact's as-of date.
        session=latest.isoformat() if hasattr(latest,'isoformat') else str(latest)
        price_basis=json.loads(next(f['basis'] for f in packet['investment_valuation_context']['facts'] if f['metric']=='FPER'))
        prior_session=price_basis['price']['session']
        assert prior_session<session
        for name in ('BLIND','ADJUDICATION'):
            prior=accepted.get('BLIND') if name=='ADJUDICATION' else None
            invocation=frozen_request['invocation_id'] if name=='BLIND' else 'C21G_SOL_ADJ_'+uuid.uuid4().hex
            request,text=stages._stage_request(invocation_id=invocation,account=account,packet=packet,stage=name,
                version=stages.UNIFIED_AI_V3_SOL_HIGH,knowledge='',registry=registry,prior=prior)
            if name=='BLIND':assert request==frozen_request
            requests[name]=deepcopy(request)
            def approval(candidate):
                return (candidate==requests.get(candidate.get('stage'))
                    and candidate['model']=='gpt-6.1-sol' and candidate['effort']=='high'
                    and candidate['source_sha']==PACKET_SHA and candidate['execution_profile']==SOL_HIGH_V1.contract
                    and digest(json.loads((H/'USER_AUTHORIZATION.json').read_bytes()))==digest(authorization)
                    and not (binding.root/'STOP').exists() and not (JOURNAL/'STOP').exists()
                    and git('rev-parse','HEAD')==authorization['head'])
            cap,host=run_stage(binding=binding,config=config,packet=packet,registry=registry,source_loader=source_loader,
                economic_loader=economic_loader,valuation_analysis_owner=view,request=request,knowledge='',approval=approval,
                account_lease=lease,session=session,prior_session=prior_session,out=OUT/name,prior=prior,enabled=True)
            if cap is None:
                result.update(status='HOST_STAGE_NOT_ACCEPTED',last_stage=name,host_state=host['state']);return
            accepted[name]=cap;result['accepted_stages'].append(name)
        with lease():
            owner=stages.StageReviewOwner(accepted['BLIND'],accepted['ADJUDICATION'],enabled=True)
            controller=stages.StageController(config,enabled=True,execution_profile=SOL_HIGH_V1)
            # DATED_REPLAY remains a dated manual research output, never a current slot.
            output=consume(controller,packet=packet,owner=owner,mode='DATED_REPLAY',
                output_context=dict(observed_as_of=packet['base']['as_of'],completed_market_session=session,
                    freshness_by_source={f['source_generation']:dict(retrieved_at=f['retrieval_timestamp'],current=False) for f in packet['investment_valuation_context']['facts']},
                    required_market_fields=['FULL_KR_MARKET_NOT_SUPPLIED','FULL_US_MARKET_NOT_SUPPLIED'],
                    current_price_denials=['DATED_FPER_PRICE_IS_NOT_CURRENT_PRICE'],
                    source_revisions=['NOT_NEWLY_CHECKED_NO_FINANCIAL_HTTP']),enabled=True)
            assert output['send'] is False and output['strict_ready'] is False
            write_once(OUT/'NO_SEND.json',output)
            write_once(OUT/'NO_SEND.md',output['message'].encode())
            result.update(status='BLIND_ADJ_ACCEPTED_NO_SEND_PASS',original_two_stage_owner=True,
                NO_SEND=True,decision_sha256=output['decision_sha256'])
    except Exception as exc:
        result.update(status='BLOCKED_NO_RETRY',error_type=type(exc).__name__,reason=str(exc)[:2000])
        write_once(OUT/'FAILURE_PRIVATE.json',dict(type=type(exc).__name__,trace=traceback.format_exc(),retry=False))
    finally:
        result['stage_host_attempts']=len(list(OUT.glob('*/MODEL_STARTED.json')))
        result['model_attempts']=len(list(OUT.glob('*/MODEL_RAW.txt')))
        result['model_attempt_count_note']='MODEL_STARTED counts backend transport entries; MODEL_RAW counts returned outputs, neither alone proves HTTP inference.'
        result['source_owner_consumptions']=source_counts
        result['private_DB_bytes']=sum(p.stat().st_size for p in JOURNAL.glob('*') if p.is_file()) if JOURNAL.exists() else 0
        write_once(H/'LIVE_RESULT.json',result)
        print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':run()
