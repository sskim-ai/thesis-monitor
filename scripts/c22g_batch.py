"""Task-scoped C22G v2 sequential research runner. No wrapper retries or DB."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.dated_research_model import build_prompt, load_bound_view, validate_output, encoded, digest
from scripts.dated_economic_model import command, check_launcher_state, CLI_SHA

ROOT = Path('/Users/sskim/Documents/Codex/2026-07-04/the')
OUT = ROOT/'maintenance/20261109-c22g-v2'
ARCHIVE = ROOT/'maintenance/20261109-c22d-v2/C22D_V2_ALL_DELIVERABLES.zip'
SOURCE_SHA = '9d503cf07d0904ef98427c67ce1310873c23f930ff2d30318d987c89303c9338'
TICKERS = ('005930', 'MU', '000660', '047810', 'CORZ')
BINARY = Path('/Users/sskim/.codex/packages/standalone/releases/0.167.0-aarch64-apple-darwin/bin/codex')

def save(path, value):
    path.write_bytes(encoded(value))

def mark(path, value):
    with path.open('xb') as f:
        f.write(encoded(value)); f.flush(); os.fsync(f.fileno())

def classify(code):
    # Only source-local semantic refusals permit progression. All other errors stop.
    local = ('unverified_', 'issued_axis_requires_citations:', 'unknown_reference:',
             'numeric_value_unit_period_basis_mismatch', 'citation_axis_ref_membership',
             'numeric_and_falsification_evidence_required', 'registered_thesis_not_supplied')
    return 'LOCAL' if code.startswith(local) else 'GLOBAL'

def run_stage(ticker, stage, view, binding, prior, *, spawn=subprocess.Popen):
    prompt, schema, catalog = build_prompt(view, binding, stage=stage, prior=prior)
    if digest(BINARY.read_bytes()) != CLI_SHA: raise ValueError('CLI_SHA_drift')
    state = check_launcher_state()
    d = OUT/'live'/ticker/stage; d.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt = dict(task='C22G_V2', ticker=ticker, stage=stage, status='STARTED',
        model='gpt-6.1-sol', effort='high', CLI_binary_sha256=CLI_SHA, **binding,
        prompt_sha256=digest(prompt), prompt_bytes=len(prompt), schema_sha256=digest(encoded(schema)),
        at=datetime.now(timezone.utc).isoformat(), launcher_state=state, requested=1, actually_spawned=0,
        wrapper_retries=0, native_HTTP_attempts='UNKNOWN', native_stream_reconnects='UNKNOWN',
        credits='UNKNOWN', NO_SEND=True, Strict_READY='0/22', timeout_seconds=600, output_limit=128*1024)
    mark(d/'MODEL_STARTED.json', receipt)
    (d/'prompt.private.txt').write_bytes(prompt); save(d/'schema.private.json', schema)
    env=dict(HOME=str(Path.home()), CODEX_HOME=str(Path.home()/'.codex'), PATH='/usr/bin:/bin',
        TMPDIR='/private/tmp', RUST_LOG='off', CODEX_DISABLE_REMOTE_CONTROL='1')
    begin=time.monotonic(); accepted=None; proc=None
    try:
        with (d/'events.private.jsonl').open('xb') as stdout, (d/'stderr.private.txt').open('xb') as stderr:
            proc=spawn(command(BINARY,root=d,schema=d/'schema.private.json',output=d/'response.json'),
                cwd=d,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,start_new_session=True)
            receipt['actually_spawned']=1; save(d/'SPAWNED.json',dict(pid=proc.pid,at=datetime.now(timezone.utc).isoformat()))
            try: proc.communicate(input=prompt,timeout=600)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                raise ValueError('CLI_timeout_NO_RETRY')
        events=[json.loads(line) for line in (d/'events.private.jsonl').read_bytes().splitlines()]
        safe=[]; item_types=set()
        for i,e in enumerate(events):
            row=dict(ordinal=i,type=e.get('type'))
            if isinstance(e.get('usage'),dict):row['usage']=e['usage']
            if isinstance(e.get('item'),dict):
                row['item_type']=e['item'].get('type');item_types.add(row['item_type'])
            safe.append(row)
        receipt.update(events=safe,exit=proc.returncode,tool_activity_observation='SAFE_EVENTS_PRESENT' if safe else 'UNKNOWN')
        if item_types-{'reasoning','agent_message'}:raise ValueError('unexpected_tool_activity')
        if proc.returncode or not any(e.get('type')=='turn.completed' for e in events):
            raise ValueError('CLI_failure_NO_RETRY')
        raw=(d/'response.json').read_bytes()
        receipt.update(response_sha256=digest(raw),response_bytes=len(raw))
        accepted=validate_output(raw,view=view,binding=binding,stage=stage,catalog=catalog)
        save(d/'accepted.json',accepted)
        receipt.update(status='ACCEPTED',accepted_sha256=digest(encoded(accepted)),numeric_citations=len(accepted['citations']))
    except Exception as error:
        code=str(error)
        receipt.update(status='FAILED',failure_type=type(error).__name__,failure_code=code,
            failure_scope=classify(code) if isinstance(error,ValueError) else 'GLOBAL')
        save(d/'failure.private.json',dict(type=type(error).__name__,detail=code))
    finally:
        receipt['elapsed_seconds']=time.monotonic()-begin
        for n in ('response.json','events.private.jsonl','stderr.private.txt'):
            p=d/n
            if p.exists():receipt[n]=dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes()))
        save(d/'RECEIPT.json',receipt)
    return receipt,accepted

def orchestrate(views, prior, execute=run_stage):
    results=[];stop=None;requested=0;spawned=0;last_failure=None
    for ticker in TICKERS:
        view,binding=views[ticker];accepted=prior if ticker=='005930' else None
        for stage in (('ADJUDICATION',) if ticker=='005930' else ('BLIND','ADJUDICATION')):
            if stage=='ADJUDICATION' and accepted is None:
                results.append(dict(ticker=ticker,stage=stage,status='SKIPPED',reason='NO_ACCEPTED_SAME_TICKER_BLIND'));continue
            if requested>=9:raise ValueError('CLI_cap')
            requested+=1
            receipt,value=execute(ticker,stage,view,binding,accepted if stage=='ADJUDICATION' else None)
            results.append(receipt);spawned+=receipt['actually_spawned']
            if receipt['status']=='FAILED':
                code=receipt['failure_code']
                if receipt['failure_scope']=='GLOBAL' or code==last_failure:
                    stop=code;break
                last_failure=code
            else:last_failure=None
            if stage=='BLIND':accepted=value
            save(OUT/'BATCH_PROGRESS.json',dict(stages=results,requested=requested,actually_spawned=spawned))
        if stop:break
    attempted={(r['ticker'],r['stage']) for r in results}
    for ticker in TICKERS:
        for stage in (('ADJUDICATION',) if ticker=='005930' else ('BLIND','ADJUDICATION')):
            if (ticker,stage) not in attempted:results.append(dict(ticker=ticker,stage=stage,status='NOT_ATTEMPTED',reason='GLOBAL_STOP'))
    result=dict(task='C22G_V2',stages=results,requested=requested,actually_spawned=spawned,global_stop=stop,
        wrapper_retries=0,native_HTTP_attempts='UNKNOWN',credits='UNKNOWN',NO_SEND=True,Strict_READY='0/22',
        financial_HTTP=0,DB_reads=0,DB_writes=0,send=0,orders=0)
    save(OUT/'BATCH_STATUS.json',result)
    return result

def preflight():
    import zipfile
    archives=[(ARCHIVE,SOURCE_SHA),
      (ROOT/'maintenance/20261109-c22f-v2/C22F_V2_ALL_DELIVERABLES_20261109.zip','9ad0cdfdb6f83c499fc551c09956226b575c967dddd828cc0685c9e435e45789'),
      (ROOT/'maintenance/20261109-c22e/C22E_ALL_DELIVERABLES_20261109.zip','cb6cb55855826b03110a93940715e924eded0516c63c815d0bfe9ae685eb65ff')]
    custody=[]
    for p,expected in archives:
        assert digest(p.read_bytes())==expected,'global_source_SHA_mismatch'
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            files=json.loads(z.read('MANIFEST.json'))['files']
            for n,row in files.items():
                raw=z.read(n);assert digest(raw)==row['sha256'] and len(raw)==row['bytes']
        custody.append(dict(path=str(p),sha256=expected,member_count=len(files),CRC='PASS',memberSHA='PASS'))
    views={t:load_bound_view(ARCHIVE,expected_zip_sha256=SOURCE_SHA,ticker=t) for t in TICKERS}
    p=ROOT/'maintenance/20261109-c22f-v2/live-once/private-evidence'
    prior=None;prior_missing=False
    if (p/'response.json').exists() and (p/'accepted-BLIND.json').exists():
        raw=(p/'response.json').read_bytes();accepted=(p/'accepted-BLIND.json').read_bytes()
        assert digest(raw)=='5ec650cd61cba3b67c57412bcc53a1d2a156713d376ae75a86d87f4dc938d307'
        assert digest(accepted)=='d9c6c511bf963bc4149e9a37b579413e92a0696a55a70898e80546fccd779134'
        v,b=views['005930'];_,_,cat=build_prompt(v,b,stage='BLIND')
        prior=validate_output(raw,view=v,binding=b,stage='BLIND',catalog=cat)
        assert encoded(prior)==accepted and len(prior['citations'])==16
    else:prior_missing=True
    prompts={}
    for t,(v,b) in views.items():
        prompt,schema,catalog=build_prompt(v,b,stage='BLIND')
        assert json.loads(prompt.split(b'BOUND_RESEARCH_INPUT:\n')[1])['accepted_blind'] is None
        prompts[t]=dict(binding=b,prompt_bytes=len(prompt),prompt_sha256=digest(prompt),schema_sha256=digest(encoded(schema)),refs=len(catalog['refs']),numeric_facts=len(catalog['numeric_facts']))
        # Bound upper-size rehearsal without fabricating a model response.
        assert len(prompt)+128*1024<384*1024,'ADJ_size_reserve'
    if prior is not None:
        prompt,schema,_=build_prompt(*views['005930'],stage='ADJUDICATION',prior=prior)
        prompts['005930']['ADJ_prompt_bytes']=len(prompt)
    assert digest(BINARY.read_bytes())==CLI_SHA
    version=subprocess.run([str(BINARY),'--version'],capture_output=True,timeout=15,check=True)
    assert version.stdout.strip()==b'codex-cli 0.167.0'
    auth=subprocess.run([str(BINARY),'login','status'],capture_output=True,timeout=15)
    assert auth.returncode==0 and b'Logged in using ChatGPT' in auth.stdout+auth.stderr
    state=check_launcher_state()
    save(OUT/'PREFLIGHT.json',dict(at=datetime.now(timezone.utc).isoformat(),archives=custody,prompts=prompts,
        CLI_binary_sha256=CLI_SHA,CLI_version='codex-cli 0.167.0',signed_in=True,launcher_state=state,
        prior_raw_accepted_identical=not prior_missing,model='gpt-6.1-sol',effort='high'))
    return views,prior

if __name__=='__main__':
    views,prior=preflight()
    if '--execute-approved' in sys.argv:
        mark(OUT/'BATCH_STARTED.json',dict(task='C22G_V2',maximum=9,at=datetime.now(timezone.utc).isoformat()))
        result=orchestrate(views,prior)
        print(json.dumps(dict(batch_sealed_locally=True,requested=result['requested'],actually_spawned=result['actually_spawned'])))
    else:print('C22G_V2_OFFLINE_PREFLIGHT_COMPLETE')
