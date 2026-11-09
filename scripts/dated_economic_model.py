"""One-shot signed-in CLI research, sequential BLIND -> accepted ADJ, no retry."""
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
from app.services.dated_research_model import (build_prompt, digest, encoded, load_bound_view,
    render_no_send, validate_output)
from app.services.vnext_execution_profile import SOL_HIGH_V1, require_profile


def command(binary, *, root, schema, output):
    return [str(binary),'-a','never','exec','--strict-config','--ephemeral','--ignore-user-config',
        '--skip-git-repo-check','--sandbox','read-only','--json','-C',str(root),
        '-m',SOL_HIGH_V1.model,'-c','model_reasoning_effort="high"',
        '-c','features.shell_tool=false','-c','features.unified_exec=false',
        '-c','web_search="disabled"','-c','project_doc_max_bytes=0',
        '--output-schema',str(schema),'-o',str(output),'-']


def validate_native_retry_configuration():
    # The current native built-in provider rejects model_providers.openai overrides.
    # Removing them would leave internal retries unproven, not the approved zero.
    raise ValueError('NATIVE_OPENAI_ZERO_RETRY_NOT_VERIFIED_RESERVED_PROVIDER_OVERRIDE_REJECTED')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--archive-sha',required=True)
    p.add_argument('--tickers',nargs='+',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--binary',type=Path,required=True);p.add_argument('--binary-sha',required=True)
    p.add_argument('--execute-approved',action='store_true')
    args=p.parse_args();require_profile(SOL_HIGH_V1)
    if len(args.tickers)>2 or len(set(args.tickers))!=len(args.tickers):raise ValueError('maximum_two_unique_cases')
    if args.out.exists():raise ValueError('preserve_existing_attempt_directory')
    args.out.mkdir(parents=True,mode=0o700)
    if digest(args.binary.read_bytes())!=args.binary_sha:raise ValueError('existing_CLI_binary_drift')
    proofs={};completed=[];contexts=0
    def put(name,obj):
        with (args.out/name).open('xb') as f:f.write(encoded(obj))
    for ticker in args.tickers:
        view,binding=load_bound_view(args.archive,expected_zip_sha256=args.archive_sha,ticker=ticker)
        prompt,schema,catalog=build_prompt(view,binding,stage='BLIND')
        case=args.out/ticker;case.mkdir();(case/'BLIND.prompt.txt').write_bytes(prompt)
        (case/'schema.json').write_bytes(encoded(schema))
        proofs[ticker]=dict(binding=binding,profile=SOL_HIGH_V1.model_request(),
            prompt_sha256=digest(prompt),prompt_bytes=len(prompt),schema_sha256=digest(encoded(schema)),
            reference_catalog=catalog,prepared=True,model_started=False)
    put('C22E_MODEL_BINDING_PROOF.json',proofs)
    if not args.execute_approved:
        put('EXECUTION_RESULT.json',dict(state='OFFLINE_BINDING_READY',model_contexts=0,HTTP=0,DB=0,NO_SEND=True));return
    put('EXPLICIT_EXECUTION_SCOPE.json',dict(task='C22E',user_approved=True,no_concurrency_confirmed=True,
        tickers=args.tickers,maximum_contexts=4,profile=SOL_HIGH_V1.model_request(),financial_HTTP=0,DB=0,
        source_zip_sha256=args.archive_sha,CLI_sha256=args.binary_sha,retries=0))
    try:validate_native_retry_configuration()
    except ValueError as error:
        put('EXECUTION_RESULT.json',dict(state='MODEL_NOT_STARTED',CLI_invocations=0,model_contexts=0,
            first_blocking_function='scripts.dated_economic_model.validate_native_retry_configuration',
            required='built-in signed-in openai transport with native retries=0',actual=str(error),
            financial_HTTP=0,DB=0,NO_SEND=True))
        return
    env=dict(HOME=str(Path.home()),CODEX_HOME=str(Path.home()/'.codex'),PATH='/usr/bin:/bin',
        TMPDIR='/private/tmp',RUST_LOG='off',CODEX_DISABLE_REMOTE_CONTROL='1')
    for ticker in args.tickers:
        view,binding=load_bound_view(args.archive,expected_zip_sha256=args.archive_sha,ticker=ticker)
        case=args.out/ticker;prior=None
        for stage in ('BLIND','ADJUDICATION'):
            prompt,schema,catalog=build_prompt(view,binding,stage=stage,prior=prior)
            (case/(stage+'.prompt.txt')).write_bytes(prompt)
            schema_path=case/(stage+'.schema.json');schema_path.write_bytes(encoded(schema))
            stage_dir=case/stage;stage_dir.mkdir(mode=0o700)
            output=stage_dir/'response.json'
            argv=command(args.binary,root=stage_dir,schema=schema_path,output=output)
            if contexts>=4:raise ValueError('context_budget_exhausted')
            started=datetime.now(timezone.utc).isoformat();contexts+=1
            put(ticker+'-'+stage+'-STARTED.json',dict(context_ordinal=contexts,started=started,model=SOL_HIGH_V1.model,
                effort=SOL_HIGH_V1.effort,prompt_sha256=digest(prompt),prompt_bytes=len(prompt),
                schema_sha256=digest(encoded(schema)),argv=argv,maximum_seconds=600,attempt=1))
            begin=time.monotonic();timed_out=False
            with (stage_dir/'events.jsonl').open('xb') as stdout,(stage_dir/'stderr.private.txt').open('xb') as stderr:
                process=subprocess.Popen(argv,cwd=stage_dir,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,start_new_session=True)
                try:process.communicate(input=prompt,timeout=600)
                except subprocess.TimeoutExpired:
                    timed_out=True;os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            elapsed=time.monotonic()-begin
            events=[];parse_error=False
            for line in (stage_dir/'events.jsonl').read_bytes().splitlines():
                try:events.append(json.loads(line))
                except ValueError:parse_error=True
            receipt=dict(ticker=ticker,stage=stage,exit=process.returncode,timed_out=timed_out,elapsed_seconds=elapsed,
                CLI_invocation=1,retries=0,model=SOL_HIGH_V1.model,effort=SOL_HIGH_V1.effort,
                event_types=[e.get('type') for e in events],accepted=False,
                internal_HTTP_attempts='NOT_INDEPENDENTLY_OBSERVABLE; native request/stream retry settings=0')
            try:
                if timed_out or process.returncode or parse_error or not any(e.get('type')=='turn.completed' for e in events):
                    raise ValueError('native_CLI_turn_not_completed')
                # This route has no financial/DB/network tools configured. Preserve any unexpected tool evidence and stop.
                item_types={e.get('item',{}).get('type') for e in events if isinstance(e.get('item'),dict)}
                if item_types-{'agent_message','reasoning'}:
                    raise ValueError('unexpected_tool_activity_requires_review')
                if not output.exists():raise ValueError('native_CLI_output_missing')
                raw=output.read_bytes();accepted=validate_output(raw,view=view,binding=binding,stage=stage,catalog=catalog)
                receipt.update(accepted=True,response_sha256=digest(raw),response_bytes=len(raw))
                (stage_dir/'accepted-research-output.json').write_bytes(encoded(accepted))
                prior=accepted
                if stage=='ADJUDICATION':
                    (case/'NO_SEND.md').write_text(render_no_send(accepted))
                    completed.append(ticker)
            except Exception as error:
                receipt['failure']=dict(function='scripts.dated_economic_model.main/validate_output',type=type(error).__name__,code=str(error)[:300])
            put(ticker+'-'+stage+'-RESULT.json',receipt)
            print(json.dumps(dict(ticker=ticker,stage=stage,accepted=receipt['accepted'],elapsed_seconds=elapsed)),flush=True)
            if not receipt['accepted']:
                put('EXECUTION_RESULT.json',dict(state='MODEL_ATTEMPT_NOT_ACCEPTED',CLI_invocations=contexts,
                    completed=completed,first_failure=receipt,financial_HTTP=0,DB=0,send=0,NO_SEND=True));return
    put('EXECUTION_RESULT.json',dict(state='RESEARCH_BLIND_ADJ_NO_SEND_COMPLETE',CLI_invocations=contexts,
        completed=completed,financial_HTTP=0,DB=0,send=0,Strict_READY='0/22',NO_SEND=True))


if __name__=='__main__':main()
