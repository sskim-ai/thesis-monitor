"""C38 receipt-only closeout. No collection, model execution, DB or new analysis runner."""
from collections import Counter
from datetime import datetime
import fcntl
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
C38=BASE/'maintenance/20261122-pr52-c38-next-session'
PYTHON='/Users/sskim/Codex/thesis-monitor/.venv/bin/python'
KST=ZoneInfo('Asia/Seoul');DUE=datetime(2026,11,24,12,45,tzinfo=KST)
SELF_LABEL='local.thesis-monitor.us.postrun.once.c38.20261124'
os.umask(0o077);os.environ['THESIS_MONITOR_ENV_FILE']=''
read=lambda p:json.loads(Path(p).read_bytes());pin=lambda p:sha256(Path(p).read_bytes()).hexdigest()
def audit(event,args):
    if event in {'sqlite3.connect','socket.connect','socket.getaddrinfo','socket.sendto'}:
        raise PermissionError('C38_POSTRUN_NO_DB_NETWORK')
    if event=='subprocess.Popen':
        executable,argv=args[:2];name=Path(os.fsdecode(executable)).name
        if name not in {'launchctl','git','swift','ps'} and not (
            name in {'python','python3','python3.12'} and len(argv)>3
            and str(argv[2])==str(Path(__file__).resolve()) and argv[3]=='--verify-zip'):
            raise PermissionError('C38_POSTRUN_NO_ANALYSIS_SUBPROCESS')
sys.addaudithook(audit)
def write(root,name,value):
    with (root/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def command(*args):return subprocess.check_output(list(args),text=True,timeout=30)
def query(label):
    p=subprocess.run(['launchctl','print',f'gui/{os.getuid()}/'+label],capture_output=True,text=True,timeout=15)
    return dict(label=label,loaded=p.returncode==0,returncode=p.returncode,
        has_PID=bool(re.search(r'^\s*pid = \d+',p.stdout,re.M)),stdout_sha256=sha256(p.stdout.encode()).hexdigest())
def scan(payload):
    from dotenv import dotenv_values
    values=[str(v).encode() for path in ('/Users/sskim/Codex/thesis-monitor/.env','/Users/sskim/Codex/ohlcv-analyst/.env')
        for k,v in dotenv_values(path).items() if v and len(str(v))>=8
        and any(w in k.lower() for w in ('key','secret','token','password','chat_id'))]
    for n,b in payload.items():
        assert not any(v in b for v in values),n
        assert b'-----BEGIN '+b'PRIVATE KEY-----' not in b
        assert re.search(rb'(?:sk-proj-|ghp_|github_pat_)[A-Za-z0-9_-]{20,}',b) is None
def package(out):
    archive=out/'TM_PR52_C38_POSTRUN_20261124_RESULT.zip'
    payload={p.name:p.read_bytes() for p in out.iterdir() if p.is_file() and p.suffix in {'.json','.md','.tsv'}}
    payload['postrun.py']=Path(__file__).read_bytes();scan(payload)
    payload['MANIFEST.json']=json.dumps(dict(self_excluded=True,files={n:dict(bytes=len(b),sha256=sha256(b).hexdigest())
        for n,b in sorted(payload.items())}),indent=2).encode()
    assert sum(map(len,payload.values()))<=20_000_000
    with ZipFile(archive,'x',compression=ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(payload.items()):z.writestr(n,b)
    with Path(str(archive)+'.sha256').open('x') as f:f.write(pin(archive)+'  '+archive.name+'\n')
    subprocess.run([PYTHON,'-B',str(Path(__file__).resolve()),'--verify-zip',str(archive)],check=True,timeout=90)
    dest=Path('/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Codex Results/TM-PR52-C38-FINAL-20261124')
    dest.mkdir(mode=0o700);files=[]
    for p in (archive,Path(str(archive)+'.sha256'),out/'INDEPENDENT_VERIFICATION.json'):
        b=p.read_bytes()
        with (dest/p.name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        assert pin(dest/p.name)==pin(p);files.append(str(dest/p.name))
    write(out,'DELIVERY.json',dict(paths=files,hashes='PASS',cloud_upload='NOT_YET_QUERIED'))
    for suffix in ('','_R1'):
        if suffix:time.sleep(12)
        p=subprocess.run(['swift','-module-cache-path','/private/tmp/tm-pr52-c35-swift-cache',
            str(BASE/'maintenance/20261120-pr52-model-runtime-fix/cloud_status.swift'),
            str(out/('CLOUD_STATUS'+suffix+'.json')),*files],capture_output=True,text=True,timeout=90)
        if p.returncode:write(out,'CLOUD_QUERY_ERROR'+suffix+'.json',dict(returncode=p.returncode,uploaded='UNCONFIRMED'));break
        if all(r.get('uploaded') is True for r in read(out/('CLOUD_STATUS'+suffix+'.json'))['files']):break

def observe(out,s):
    spec=importlib.util.spec_from_file_location('existing_c36_receipt_observer',BASE/'maintenance/20261121-pr52-c36-readback-live/observe.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.HERE=out;module.schedule=s;module.run=Path(s['run_root'])
    return module.snapshot()

def load_execution_schedule(installation,final_pin):
    """Keep C38 registration intact; optionally bind its approved C45 execution."""
    raw=(C38/'SCHEDULE.json').read_bytes();original_sha=sha256(raw).hexdigest()
    assert original_sha==installation['original_C38_schedule_sha256']
    schedule=json.loads(raw);binding_path=HERE/'CURRENT_EXECUTION_BINDING.json'
    if binding_path.exists():
        raw=binding_path.read_bytes()
        assert sha256(raw).hexdigest()==final_pin['current_execution_binding_sha256']
        binding=json.loads(raw)
        assert binding['prior_C38_schedule_sha256']==original_sha
        overrides=binding['schedule_overrides']
        assert set(overrides)=={'code_root','code_commit','configuration_sha256',
            'plist_sha256','C37_timer_sha256','after_terminal'}
        assert overrides['code_commit']=='374145c4337d50673db672c73a49e071b1801b5b'
        assert overrides['after_terminal']=='US_REGULAR_OFF'
        pins=binding['code_pins'];assert isinstance(pins.get('files'),dict) and pins['files']
        schedule={**schedule,**overrides,'_current_code_pins':pins}
    else:
        assert not final_pin.get('current_execution_binding_sha256')
    # observe() also imports project code: select the effective checkout first.
    sys.path.insert(0,str(Path(schedule['code_root'])))
    return schedule

def verify_receipts(out,s,observed):
    """Existing stage loaders, journal reader and B2 validators; no Owner reconstruction."""
    root=Path(s['code_root']);sys.path.insert(0,str(root))
    assert command('git','-C',str(root),'rev-parse','HEAD').strip()==s['code_commit']
    pins=s['_current_code_pins'] if '_current_code_pins' in s else read(C38/'CODE_PINS.json')
    assert all(pin(root/n)==r['sha256'] for n,r in pins['files'].items())
    assert pin(root/'app/services/research_no_send_run.py')==s['C37_timer_sha256']
    from app.services.research_request_storage import load_stage_request,load_stage_response
    from app.services.unified_snapshot_contract import digest
    from app.services.model_invocation_journal import read_invocation_journal
    from app.services import new_buyer_request_owner as b2,new_buyer_v2_contract
    from app.services.unified_stock_acquisition import UNIVERSE
    run=Path(s['run_root']);terminal=read(run/'terminal.json');intent=read(run/'intent.json')
    assert intent['session']==s['target_session'] and intent['code_commit']==s['code_commit']
    failure_path=run/'failure-diagnostic.json'
    failure=read(failure_path) if failure_path.is_file() else None
    if failure is not None:write(out,'FAILURE_DIAGNOSTIC.json',failure)
    rows=[json.loads(line) for line in (run/'campaign.jsonl').read_bytes().splitlines()]
    assert observed.get('journal_chain')=='PASS'
    intents={r['value']['attempt_id']:r for r in rows if r['event']=='PHYSICAL_INTENT'}
    results={r['value']['attempt_id']:r['value'] for r in rows if r['event']=='PHYSICAL_RESULT'}
    physical=[]
    for row in rows:
        if row['event']!='PHYSICAL_DISPATCH':continue
        key=row['value']['attempt_id'];request=intents[key];result=results.get(key,{})
        physical.append(dict(attempt_id=key,provider=request['value']['provider'],subject=request['value']['subject'],
            method=request['value']['method'],requested_at=request['recorded_at'],status=result.get('status'),outcome=result.get('outcome')))
    write(out,'PHYSICAL_CALL_LEDGER.json',dict(rows=physical,count=len(physical),
        original_campaign_sha256=pin(run/'campaign.jsonl'),chain='PASS',URLs_or_auth_bodies_exported=False))
    assert observed['financial_HTTP']<=710
    assert all(n<=s['provider_caps'][p] for p,n in observed['providers'].items())
    info=read(run/'model-runtime-preflight.json');inner=run/'results/unified-snapshot-runs'/info['execution']
    # Source can stop before an engine or invocation journal is created. Its
    # original diagnostic is the failure; absent model artifacts are expected.
    if (terminal.get('status')=='STOPPED_NO_SEND' and failure is not None
            and failure.get('stage') in {'SOURCE_PREPARATION_OR_COLLECTION','SOURCE_POST_COLLECTION'}
            and observed['source_accepted'] is False and observed['model_plan_accepted'] is False):
        assert not any(r['event'] in {'SOURCE','MODEL_PLAN'} for r in rows)
        assert all(observed[k]==0 for k in ('model_calls','model_acceptances','model_retries'))
        assert terminal.get('normal_messages_sent') is False and not terminal.get('messages')
        assert failure.get('NO_SEND') is True and failure.get('recorded_before_owner_cleanup') is True
        assert failure.get('market')=='us' and failure.get('target_session')==s['target_session']
        assert failure.get('code_commit')==s['code_commit']
        assert not any((inner/name).exists() for name in ('terminal.json','state.json'))
        assert not Path(info['journal_path']).exists()
        write(out,'ORIGINAL_TERMINAL_SUMMARY.json',dict(terminal,origin='ACTUAL_OUTER_TERMINAL'))
        write(out,'FIRST_FAILURE_LOCATION.json',dict(first_failure=failure,
            last_original_frame=failure.get('last_application_frame'),proof='RECORDED_ORIGINAL_ERROR_ONLY'))
        write(out,'STAGES.json',dict(Source=False,ModelPlan=False,
            stages=[dict(stage=stage,status='NOT_REACHED') for stage in ('MARKET','CORE','A','B','B2','VALIDATE','RENDER')],
            Cold=read(run/'source/phase-stock-native-replay.json') if (run/'source/phase-stock-native-replay.json').is_file() else None,
            Source_and_Owner_reissued=False))
        write(out,'MODEL_ATTEMPTS.json',dict(status='NOT_REACHED',attempts=[],physical_intents=0,
            actual_CLI_starts=0,accepted=0,retries=0,maximum=42,remote_billing='UNOBSERVED'))
        write(out,'FINAL_MESSAGES.json',dict(status=terminal['status'],messages=[],NO_SEND=True,
            origin='ACTUAL_C38_TERMINAL_ONLY',model_status='NOT_REACHED'))
        return False
    original=read(inner/'terminal.json') if (inner/'terminal.json').is_file() else read(inner/'state.json')
    write(out,'ORIGINAL_TERMINAL_SUMMARY.json',{k:original.get(k) for k in
        ('status','stage_receipts','first_failure','first_failure_receipt','error_chain','storage_failure','messages_sha256')})
    frames=[frame for error in original.get('error_chain',[]) for frame in error.get('frames',[])]
    write(out,'FIRST_FAILURE_LOCATION.json',dict(first_failure=original.get('first_failure'),
        original_error_chain=original.get('error_chain'),last_original_frame=frames[-1] if frames else None,
        proof='RECORDED_ORIGINAL_ERROR_ONLY' if frames else 'LOCATION_UNAVAILABLE_NOT_INVENTED'))
    if (inner/'first-failure.json').is_file():write(out,'FIRST_FAILURE.json',read(inner/'first-failure.json'))
    stage_outputs={};stages=[]
    for row in original.get('stage_receipts',[]):
        item={k:row[k] for k in ('stage','status','timing','deadline') if k in row}
        if row['status']=='PASS':
            folder=inner/row['stage'].lower()
            request=load_stage_request(folder/'request.json',expected_logical_sha256=row['logical_request_sha256'],
                expected_storage_sha256=row['storage_record_sha256'])
            response=load_stage_response(folder/'response.json',request)
            assert digest(response)==row['response_sha256'] and request['inputs']==stage_outputs
            stage_outputs[row['stage']]=response;item['stored_hash_and_generation']='PASS'
        stages.append(item)
    write(out,'STAGES.json',dict(stages=stages,Source=observed['source_accepted'],ModelPlan=observed['model_plan_accepted'],
        Cold=read(run/'source/phase-stock-native-replay.json') if (run/'source/phase-stock-native-replay.json').is_file() else None,
        Source_and_Owner_reissued=False))
    raw=Path(info['journal_path']).read_bytes();journal=read_invocation_journal(raw)
    model_rows=[json.loads(line) for line in raw.splitlines()];runtime=Path(info['runtime_root'])
    plans=[r['value'] for r in rows if r['event']=='MODEL_PLAN'];assert len(plans)==1
    assert plans[0]['sha256']==model_rows[0]['identity']['plan_sha256']
    attempts=[]
    for r in model_rows:
        if r['event'] not in {'CONSUME','RETRY_ATTEMPT'}:continue
        v=r['value'];a=v['attempt'];folder=runtime/a['attempt_id'];scope=journal['bound'][v['slot_id']]
        exit=read(folder/'market-cli-exit.json') if (folder/'market-cli-exit.json').is_file() else {}
        transport=read(folder/'transport-receipt.json') if (folder/'transport-receipt.json').is_file() else {}
        attempts.append(dict(stage=scope['stage'],subjects=scope['subjects'],attempt_id=a['attempt_id'],
            reserved=True,CLI_started=exit.get('process_started'),accepted=(v['slot_id'] in journal['accepted']
                and a==journal['attempts'][v['slot_id']][-1]),elapsed_seconds=exit.get('elapsed_seconds'),
            transport_status=transport.get('status'),transport_error=transport.get('error_code')))
    write(out,'MODEL_ATTEMPTS.json',dict(attempts=attempts,physical_intents=journal['physical_calls'],
        actual_CLI_starts=sum(a['CLI_started'] is True for a in attempts),accepted=len(journal['accepted']),
        retries=journal['retry_used'],maximum=42,remote_billing='UNOBSERVED'))
    assert journal['physical_calls']<=42
    messages=terminal.get('messages',[])
    write(out,'FINAL_MESSAGES.json',dict(status=terminal['status'],messages=messages,
        messages_sha256=terminal.get('messages_sha256'),NO_SEND=True,origin='ACTUAL_C38_TERMINAL_ONLY'))
    full=terminal.get('status')=='RENDER_VERIFIED_NO_SEND'
    if full:
        assert original['status']==terminal['status'] and original['messages']==messages
        assert original['normal_messages_sent'] is False and original['failure_notifications_sent'] is False
        assert [r['stage'] for r in stages]==['MARKET','CORE','A','B','B2','VALIDATE','RENDER']
        assert len(messages)==15 and {m['message_id'] for m in messages}=={'MARKET_US',*UNIVERSE['us']}
        assert digest(messages)==terminal['messages_sha256']==stage_outputs['VALIDATE']['output']['content_sha256']
        assert stage_outputs['RENDER']['output']['messages']==messages
        assert all(m.get('NO_SEND') is True and m.get('text') and m['generation_id']==info['execution'] for m in messages)
        assert all(not m.get('content_sha256') or m['content_sha256']==digest(m['text']) for m in messages)
        assert observed['source_accepted'] and observed['model_plan_accepted']
        cold=read(run/'source/phase-stock-native-replay.json');assert cold['value']['status']=='PASS'
        assert not journal['stopped'] and not journal['exhausted'] and not journal['inherited']
        assert set(plans[0]['slot_ids'])==set(journal['accepted'])==journal['used']
        assert all(a['CLI_started'] is True and a['elapsed_seconds'] is not None for a in attempts)
        assert not stage_outputs['B2']['output'].get('unissued')
        qa=[]
        for ticker in UNIVERSE['us']:
            message=next(m for m in messages if m['message_id']==ticker)
            if message.get('decision_mode')=='UNKNOWN_LIMIT':
                qa.append(dict(ticker=ticker,mode='UNKNOWN_LIMIT',buy_opinion='NOT_ELIGIBLE',entry_price='NOT_ELIGIBLE'))
                continue
            row=stage_outputs['B2']['output']['rows'][ticker];request=read(inner/'b2'/ticker/'request.json')
            result=row['result'];assert result['status']=='PASS'
            assert b2.validate_result(result['output'],request,expected_request_sha256=result['request_sha256'])['status']=='PASS'
            context=b2.provider_payload(request,expected_request_sha256=result['request_sha256'])['input']
            axes=new_buyer_v2_contract.presentation_plan(result['output']['new_buyer_shadow'],context)
            timing=axes['entry_timing'];eligible=(timing['state'] in {'FAVORABLE_NOW','WAIT_FOR_ZONE'}
                and timing['reason']=='EXACT_SELECTED_ZONE_RELATION' and bool(timing['evidence_refs']))
            qa.append(dict(ticker=ticker,mode='ACCEPTED_B2',buy_opinion=axes['fundamental_attractiveness'],
                entry_timing=timing,entry_price_relation_eligible=eligible,
                entry_numeric_values='Use accepted final message only; no new price or recommendation inferred',
                message_sha256=digest(message),text_sha256=digest(message['text'])))
        write(out,'BUY_ENTRY_ELIGIBILITY.json',dict(rows=qa,source='Original accepted B2 axes and timing authority; not a new investment judgment'))
    return full

def clean_one_shot(out,s):
    target=Path(s['plist_path']);row=query(s['label']);assert not row['has_PID']
    if target.exists():assert not target.is_symlink() and pin(target)==s['plist_sha256']
    domain=f'gui/{os.getuid()}'
    if row['loaded']:subprocess.run(['launchctl','bootout',domain+'/'+s['label']],check=True,capture_output=True,timeout=15)
    subprocess.run(['launchctl','disable',domain+'/'+s['label']],check=True,capture_output=True,timeout=15)
    if target.exists():target.unlink()
    checks=[query(s['label']),query(s['label'])];assert all(not r['loaded'] for r in checks)
    write(out,'ONESHOT_REMOVAL.json',dict(label=s['label'],plist_removed=not target.exists(),readbacks=checks))

def main():
    now=datetime.now(KST)
    if now.date()!=DUE.date() or now<DUE or now.hour>=14:
        print('C38_POSTRUN_OUTSIDE_EXACT_FUTURE_WINDOW_NO_ACTION');return
    with (HERE/'postrun.lock').open('a') as own:
        fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out=HERE/'actual-20261124'
        if out.exists():print('C38_POSTRUN_ALREADY_ATTEMPTED_NO_REPLAY');return
        out.mkdir(mode=0o700);installation=read(HERE/'INSTALL_INTENT.json')
        final_pin=read(HERE/'FINAL_COMMAND_PIN.json')
        assert pin(Path(__file__))==final_pin['script_sha256']
        s=load_execution_schedule(installation,final_pin);pre=read(C38/'PREFLIGHT.json')
        # Compare this postrun's start and end, not the older C38 registration.
        kr_before={k:pin(pre['protected'][k]['path']) for k in ('kr_config','kr_plist')}
        write(out,'POSTRUN_INTENT.json',dict(at_kst=now.isoformat(),code_commit=s['code_commit'],
            code_root=s['code_root'],current_execution_binding_sha256=final_pin.get('current_execution_binding_sha256'),
            new_financial_HTTP=0,new_model_CLI=0,new_DB=0))
        writers=[]
        for path in (HERE,Path('/private/tmp'),Path('/Users/sskim/Library/Mobile Documents/com~apple~CloudDocs/Codex Results')):
            fs=os.statvfs(path);writers.append(dict(path=str(path),device=path.stat().st_dev,free_bytes=fs.f_bavail*fs.f_frsize))
        write(out,'pre-gc-decision.json',dict(task='C38_POSTRUN_RECEIPTS_ONLY',at_kst=now.isoformat(),writers=writers,
            projected_peak_bytes=64*1024**2,reserve_bytes=2*1024**3,deletion_actions=[],
            decision='PRE_GC_NOOP_SUFFICIENT' if min(r['free_bytes'] for r in writers)>=64*1024**2+2*1024**3 else 'PRE_GC_NO_SAFE_CANDIDATE',
            no_large_artifacts=True,no_new_live_execution=True))
        observed=observe(out,s);write(out,'OBSERVATION.json',observed)
        full=False;error=None;status='C38_LIVE_PARTIAL_US_OFF';cleanup_status='NOT_ATTEMPTED'
        def record_error(exc):
            trace=exc.__traceback__;frames=[]
            while trace:
                frames.append(dict(file=Path(trace.tb_frame.f_code.co_filename).name,function=trace.tb_frame.f_code.co_name,line=trace.tb_lineno));trace=trace.tb_next
            reason=exc.args[0] if len(exc.args)==1 and isinstance(exc.args[0],str) and re.fullmatch(r'[A-Za-z0-9_:.]{1,128}',exc.args[0]) else None
            return dict(type=type(exc).__name__,code=reason,frames=frames[-4:],scope='POSTRUN_VERIFICATION_OR_ADMIN_NOT_A_NEW_ANALYSIS_FAILURE')
        try:
            if observed['active']:
                status='C38_STILL_RUNNING_OBSERVATION_ONLY'
            else:
                if observed['terminal_exists']:
                    try:full=verify_receipts(out,s,observed)
                    except BaseException as exc:
                        error=record_error(exc);write(out,'RECEIPT_VERIFICATION_ERROR.json',error)
                lease=Path(read(s['configuration_path'])['shared_lease_path'])
                lane=Path('/Users/sskim/Library/Application Support/ThesisMonitor/KiwoomGlobalLane/state.json')
                with lease.open('rb') as a,(lane.parent/'lane.lock').open('rb') as b:
                    try:
                        fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError:
                        cleanup_status='DEFERRED_OTHER_RUN_ACTIVE'
                        write(out,'RESOURCE_RELEASE.json',dict(status=cleanup_status,cleanup_performed=False,
                            Lane_writes=0,reason='SHARED_EXECUTION_OR_PROVIDER_LEASE_BUSY'))
                    else:
                        state=read(lane);assert not state['in_flight']
                        processes=command('ps','-axo','pid=,args=')
                        assert not any(marker in processes for marker in ('-m app.jobs.unified_market_snapshot',
                            '-m app.jobs.production_model_worker','-m app.jobs.production_kis_worker','scripts/r9_rev11_native_worker'))
                        cleanup_status='ATTEMPTED'
                        clean_one_shot(out,s);cleanup_status='COMPLETED'
                        write(out,'RESOURCE_RELEASE.json',dict(status=cleanup_status,cleanup_performed=True,
                            lease_free=True,Lane_sequence=state['sequence'],
                            Lane_halted=state['halted'],Lane_sha256=pin(lane),Lane_writes=0))
                if full:status='C38_US_LIVE_15_15_PASS_US_REGULAR_DEFERRED'
        except BaseException as exc:
            error=record_error(exc)
            write(out,'POSTRUN_ERROR.json',error)
            if full:status='C38_US_LIVE_15_15_PASS_US_REGULAR_DEFERRED'
        if not (out/'STAGES.json').exists():
            write(out,'STAGES.json',dict(Source=observed['source_accepted'],ModelPlan=observed['model_plan_accepted'],
                stages='NOT_AVAILABLE_OR_NOT_YET_REACHED; see preserved observation/first error',
                Source_and_Owner_reissued=False))
        if not (out/'FINAL_MESSAGES.json').exists():
            terminal=read(Path(s['run_root'])/'terminal.json') if observed['terminal_exists'] else {}
            write(out,'FINAL_MESSAGES.json',dict(status=terminal.get('status','NO_TERMINAL_YET'),
                messages=terminal.get('messages',[]),messages_sha256=terminal.get('messages_sha256'),
                origin='ACTUAL_TERMINAL_ONLY_NOT_ACCEPTED_BY_POSTRUN_UNLESS_SUMMARY_PASS'))
        kr_after={k:pin(pre['protected'][k]['path']) for k in kr_before}
        kr={k:kr_after[k]==kr_before[k] for k in kr_before}
        summary=dict(status=status,at_kst=datetime.now(KST).isoformat(),actual15of15=full,US_regular_activated=False,
            code_commit=s['code_commit'],current_execution_binding_sha256=final_pin.get('current_execution_binding_sha256'),
            financial_HTTP=observed['financial_HTTP'],model_intents=observed['model_calls'],model_acceptances=observed['model_acceptances'],
            final_messages=observed['messages'],first_failure=observed.get('first_failure',observed.get('failure-diagnostic.json')),
            postrun_error=error,one_shot_cleanup=cleanup_status,KR_unchanged=kr,KR_hashes_before=kr_before,KR_hashes_after=kr_after,
            new_financial_HTTP=0,new_model_CLI=0,new_DB=0,new_campaign=0,tests=0,sends=0,orders=0)
        write(out,'SUMMARY.json',summary)
        with (out/'RESULT.md').open('x') as f:f.write('# C38 실물 사후 확인\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n원래 문안/수락 기록만 검증. 매수·진입 적격성은 BUY_ENTRY_ELIGIBILITY.json에 기존 B2 축으로 구분하며 가격을 새로 만들지 않음.\n')
        package(out)
        # Disable future firing without booting out the process still writing its receipt.
        subprocess.run(['launchctl','disable',f'gui/{os.getuid()}/'+SELF_LABEL],capture_output=True,timeout=15)
        print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--verify-zip':
        archive=Path(sys.argv[2]);assert Path(str(archive)+'.sha256').read_text()==pin(archive)+'  '+archive.name+'\n'
        with ZipFile(archive) as z:
            assert z.testzip() is None;payload={n:z.read(n) for n in z.namelist()}
            assert len(payload)==len(z.namelist())
        scan(payload);m=json.loads(payload['MANIFEST.json']);assert set(payload)==set(m['files'])|{'MANIFEST.json'}
        for n,r in m['files'].items():assert len(payload[n])==r['bytes'] and sha256(payload[n]).hexdigest()==r['sha256']
        write(archive.parent,'INDEPENDENT_VERIFICATION.json',dict(status='PASS',independent_process=True,CRC='PASS',
            members=len(payload),SHA256='ALL_PASS',secret_scan='PASS',archive=archive.name,sha256=pin(archive),bytes=archive.stat().st_size))
    else:main()
