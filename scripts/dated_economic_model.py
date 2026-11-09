"""C22F v2: one approved native-default-retry BLIND, no wrapper retry or ADJ."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.dated_research_model import build_prompt, digest, encoded, load_bound_view, validate_output
from app.services.vnext_execution_profile import SOL_HIGH_V1, require_profile

CLI_SHA='030316ecfbb41f4e7946e584b0063ef333b7a36cd312ba349f2f6869e39b62cc'
POLICY='C22F_V2_ONE_BLIND_NATIVE_DEFAULT'


def command(binary, *, root, schema, output):
    return [str(binary),'-a','never','exec','--strict-config','--ephemeral','--ignore-user-config',
        '--skip-git-repo-check','--sandbox','read-only','--json','-C',str(root),
        '-m',SOL_HIGH_V1.model,'-c','model_reasoning_effort="high"',
        '-c','features.shell_tool=false','-c','features.unified_exec=false',
        '-c','web_search="disabled"','-c','project_doc_max_bytes=0',
        '--output-schema',str(schema),'-o',str(output),'-']


def validate_native_retry_configuration(scope, *, binary_sha, version, signed_in):
    required=dict(task='C22F_V2',user_approved=True,allowed_tickers=['005930'],allowed_stages=['BLIND'],
        maximum_CLI_invocations=1,wrapper_retries=0,native_retry_policy='CLI_DEFAULT_USER_APPROVED',
        model='gpt-6.1-sol',effort='high',timeout_seconds=600,input_limit=384*1024,output_limit=128*1024,
        CLI_binary_sha256=CLI_SHA,CLI_version='codex-cli 0.167.0',signed_in_chatgpt=True)
    if any(scope.get(k)!=v for k,v in required.items()):raise ValueError('C22F_V2_exact_user_scope_required')
    if binary_sha!=CLI_SHA or version!='codex-cli 0.167.0' or signed_in is not True:
        raise ValueError('C22F_V2_current_native_runtime_mismatch')
    if scope.get('competing_model_processes')!=[] or not scope.get('concurrency_checked_at'):
        raise ValueError('current_launcher_state_required')
    return dict(policy=POLICY,wrapper_retries=0,native_retry_policy='CLI_DEFAULT_USER_APPROVED',
        native_HTTP_attempts='UNKNOWN',native_stream_reconnects='UNKNOWN',CLI_cap=1,stage='BLIND')


def validate_execution_request(tickers, scope):
    if tickers!=scope.get('allowed_tickers') or tickers!=['005930']:
        raise ValueError('C22F_V2_only_approved_single_BLIND_subject')


def check_launcher_state():
    # Same native CLI process-state check used by the earlier C21K route.
    rows=subprocess.check_output(['/bin/ps','-axo','pid=,comm=,args='],text=True)
    competing=[]
    for line in rows.splitlines():
        parts=line.strip().split(None,2)
        if len(parts)!=3:continue
        pid=int(parts[0]);comm=Path(parts[1]).name;args=parts[2]
        if pid in (os.getpid(),os.getppid()):continue
        if ((comm=='codex' and ' exec ' in ' '+args+' ')
            or (comm in ('codex-app-server','python','python3','Python') and
                any(s in args for s in ('guarded_sol_host.py','/private-runtime/','dated_economic_model.py --')))):
            competing.append(dict(pid=pid,executable=comm,args_sha256=digest(args.encode())))
    if competing:raise ValueError('competing_native_model_launcher')
    return dict(at=datetime.now(timezone.utc).isoformat(),competing_model_processes=competing,
        basis='Current native CLI process state; this route does not consume the old DB-backed Stage lease')


def run_one_blind(*,scope,scope_path,binary,view,binding,prompt,schema,catalog,out,spawn=None):
    policy=validate_native_retry_configuration(scope,binary_sha=digest(binary.read_bytes()),
        version=scope['CLI_version'],signed_in=scope['signed_in_chatgpt'])
    validate_execution_request([view['ticker']],scope)
    if len(prompt)>384*1024:raise ValueError('input_limit')
    # One task-local file is an attempt ledger, not a new security capability.
    marker=scope_path.parent/'MODEL_STARTED.json'
    if marker.exists():raise ValueError('one_BLIND_attempt_already_consumed')
    state=check_launcher_state()
    private=out/'private-evidence';private.mkdir(mode=0o700)
    (private/'prompt.txt').write_bytes(prompt)
    schema_path=private/'schema.json';schema_path.write_bytes(encoded(schema))
    output=private/'response.json'
    argv=command(binary,root=private,schema=schema_path,output=output)
    receipt=dict(task='C22F_V2',ticker=view['ticker'],**policy,
        model=SOL_HIGH_V1.model,effort=SOL_HIGH_V1.effort,CLI_binary_sha256=CLI_SHA,
        CLI_version=scope['CLI_version'],input_zip_sha256=binding['source_zip_sha256'],
        original_sha256=binding['original_sha256'],research_view_sha256=binding['research_view_sha256'],
        prompt_sha256=digest(prompt),prompt_bytes=len(prompt),schema_sha256=digest(encoded(schema)),
        maximum_seconds=600,maximum_output_bytes=128*1024,at=datetime.now(timezone.utc).isoformat(),
        launcher_state=state,accepted=False,ADJ_started=0,MU_started=0,NO_SEND=True,
        native_usage_caveat='Native retries may cause more remote requests/usage; wrapper invocation count is not HTTP count.',
        financial_HTTP=0,DB=0,send=0,orders=0,Strict_READY='0/22')
    with marker.open('xb') as f:f.write(encoded(receipt))
    (out/'STARTED.json').write_bytes(encoded(receipt))
    env=dict(HOME=str(Path.home()),CODEX_HOME=str(Path.home()/'.codex'),PATH='/usr/bin:/bin',
        TMPDIR='/private/tmp',RUST_LOG='off',CODEX_DISABLE_REMOTE_CONTROL='1')
    begin=time.monotonic();timed_out=False;process=None;events=[]
    try:
        with (private/'events.jsonl').open('xb') as stdout,(private/'stderr.txt').open('xb') as stderr:
            process=(spawn or subprocess.Popen)(argv,cwd=private,env=env,stdin=subprocess.PIPE,
                stdout=stdout,stderr=stderr,start_new_session=True)
            try:process.communicate(input=prompt,timeout=600)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        receipt.update(exit=process.returncode,timed_out=timed_out,CLI_invocations=1)
        for line in (private/'events.jsonl').read_bytes().splitlines():events.append(json.loads(line))
        receipt['event_types']=[e.get('type') for e in events]
        receipt['actual_turn_started_events']=sum(e.get('type')=='turn.started' for e in events)
        receipt['usage_events']=[e['usage'] for e in events if isinstance(e.get('usage'),dict)]
        item_types={e.get('item',{}).get('type') for e in events if isinstance(e.get('item'),dict)}
        receipt['item_types']=sorted(str(x) for x in item_types)
        if timed_out or process.returncode or not any(e.get('type')=='turn.completed' for e in events):
            raise ValueError('native_CLI_turn_not_completed')
        if item_types-{'agent_message','reasoning'}:raise ValueError('unexpected_tool_activity')
        if not output.exists():raise ValueError('native_CLI_output_missing')
        raw=output.read_bytes()
        receipt.update(response_sha256=digest(raw),response_bytes=len(raw))
        accepted=validate_output(raw,view=view,binding=binding,stage='BLIND',catalog=catalog)
        (private/'accepted-BLIND.json').write_bytes(encoded(accepted))
        receipt.update(accepted=True,state='C22F_005930_BLIND_ACCEPTED_ADJ_NOT_STARTED',
            axes={k:dict(state=accepted[k]['state'],confidence=accepted[k]['confidence']) for k in ('overall','newbuyer','holder_virtual')},
            numeric_citation_count=len(accepted['citations']))
    except Exception as error:
        (private/'failure.private.json').write_bytes(encoded(dict(type=type(error).__name__,detail=str(error))))
        receipt.update(state='C22F_005930_BLIND_ATTEMPT_FAILED_NO_RETRY',CLI_invocations=int(process is not None),
            failure_type=type(error).__name__,failure_code=str(error) if type(error) is ValueError else 'PRIVATE_ERROR_DETAILS_RETAINED')
    finally:
        receipt['elapsed_seconds']=time.monotonic()-begin
        receipt['credits']='UNKNOWN'
        for name in ('events.jsonl','stderr.txt','response.json'):
            path=private/name
            if path.exists():receipt[name.replace('.','_')]=dict(bytes=path.stat().st_size,sha256=digest(path.read_bytes()))
        (out/'RESULT.json').write_bytes(encoded(receipt))
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--archive-sha',required=True)
    parser.add_argument('--tickers',nargs='+',required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--binary',type=Path,required=True);parser.add_argument('--binary-sha',required=True)
    parser.add_argument('--scope',type=Path,required=True);parser.add_argument('--execute-approved',action='store_true')
    args=parser.parse_args();require_profile(SOL_HIGH_V1)
    scope=json.loads(args.scope.read_bytes());validate_execution_request(args.tickers,scope)
    if args.out.exists():raise ValueError('preserve_existing_attempt_directory')
    if digest(args.binary.read_bytes())!=args.binary_sha:raise ValueError('existing_CLI_binary_drift')
    if args.archive_sha!=scope['input_zip_sha256']:raise ValueError('approved_source_archive_required')
    args.out.mkdir(parents=True,mode=0o700)
    view,binding=load_bound_view(args.archive,expected_zip_sha256=args.archive_sha,ticker=args.tickers[0])
    prompt,schema,catalog=build_prompt(view,binding,stage='BLIND')
    (args.out/'BINDING_PROOF.json').write_bytes(encoded(dict(binding=binding,prompt_sha256=digest(prompt),
        prompt_bytes=len(prompt),schema_sha256=digest(encoded(schema)),references=len(catalog['refs']),
        numeric_facts=len(catalog['numeric_facts']),native_retry_policy=scope['native_retry_policy'])))
    if not args.execute_approved:
        print(json.dumps(dict(state='OFFLINE_BINDING_READY',CLI_invocations=0)));return
    (args.out/'EXPLICIT_EXECUTION_SCOPE.json').write_bytes(encoded(scope))
    result=run_one_blind(scope=scope,scope_path=args.scope,binary=args.binary,view=view,binding=binding,
        prompt=prompt,schema=schema,catalog=catalog,out=args.out)
    print(json.dumps(dict(state=result['state'],CLI_invocations=result['CLI_invocations'],accepted=result['accepted'])))


if __name__=='__main__':main()
