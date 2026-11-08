"""Synthetic real-binary predispatch matrix; no auth or network permitted."""
from pathlib import Path
import copy
import hashlib
import json
import os
import subprocess
import sys
import time

H=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
B=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else H.parents[1]/'private-runtime/c21l-guarded-host-0167-20261108'
binary=B/'target/dev-small/codex-app-server'
ROOT=Path('/private/tmp/c21l-offline-20261108')
TASK='C21L_OFFICIAL_0167_GUARDED_SOL_HIGH_PORT_AND_OFFLINE_PREDISPATCH'
sha=lambda b:hashlib.sha256(b).hexdigest()
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def put(p,v,immutable=False):
    with p.open('xb') as f:f.write(v if isinstance(v,bytes) else enc(v))
    if immutable:p.chmod(0o444)

assert binary.is_file()
ROOT.mkdir(mode=0o700)
catalog=json.loads((B/'source/codex-rs/http-client/src/task_guard_catalog.json').read_text())
schema=dict(type='object',properties=dict(result=dict(type='string')),required=['result'],additionalProperties=False)
prompt='Synthetic offline policy validation. This is not an investment request.'
body=dict(model='gpt-6.1-sol',reasoning=dict(effort='high'),stream=True,tools=catalog,
    input=[dict(role='user',content=[dict(type='input_text',text=prompt)])],
    text=dict(format=dict(type='json_schema',strict=True,schema=schema)))
base=dict(url='https://chatgpt.com/backend-api/codex/responses',
    headers={'authorization':'C21L_SYNTHETIC_NO_CREDENTIAL','thread-id':'C21L_SYNTHETIC_THREAD',
        'chatgpt-account-id':'C21L_SYNTHETIC_ACCOUNT'},body=body)
cases=['positive','model','effort','account','source','stage','schema','tool','endpoint','lite','continuation','expired','bytes','ledger-replay','opaque-raw-client']
results=[]
for case in cases:
    root=ROOT/case;root.mkdir(mode=0o700)
    for name in ('home','codex-home','tmp'):(root/name).mkdir()
    now=int(time.time())
    policy=dict(task=TASK,execution_profile='SOL_61_HIGH_EXECUTION_V1',account='C21L_SYNTHETIC_ACCOUNT',
        stage='BLIND',security='SYNTHETIC_NON_FINANCIAL',owner_sha256='a'*64,prompt_sha256=sha(prompt.encode()),
        request_sha256='b'*64,thread_id='C21L_SYNTHETIC_THREAD',source_generation='SYNTHETIC_DATED_ONLY',
        schema=schema,schema_binding=dict(adapter_version='LOCAL_REF_DESCRIPTION_INLINE_V1',
            canonical_schema_sha256=sha(enc(schema)),wire_schema_sha256=sha(enc(schema)),changed_paths=['/synthetic_fixture']),
        started_unix=now,deadline_unix=now+600,ledger=str(root/'inference-ledger.json'))
    scope=dict(task=TASK,execution_profile=policy['execution_profile'],account=policy['account'],
        security=policy['security'],owner_sha256=policy['owner_sha256'],source_generation=policy['source_generation'],
        root=str(root),ledger=policy['ledger'],stage_seconds=600,input_bytes=393216,output_bytes=131072,retries=0)
    fixture=copy.deepcopy(base)
    if case=='model':fixture['body']['model']='UNAUTHORIZED'
    if case=='effort':fixture['body']['reasoning']['effort']='medium'
    if case=='account':fixture['headers']['chatgpt-account-id']='OTHER_SYNTHETIC_ACCOUNT'
    if case=='source':policy['source_generation']='MISMATCH'
    if case=='stage':policy['stage']='UNKNOWN'
    if case=='schema':fixture['body']['text']['format']['schema']={}
    if case=='tool':fixture['body']['tools']=[dict(type='function',name='shell')]
    if case=='endpoint':fixture['url']='https://api.openai.com/v1/responses'
    if case=='lite':fixture['url']='https://chatgpt.com/backend-api/codex/responses/compact'
    if case=='continuation':fixture['body']['previous_response_id']='UNBOUND'
    if case=='expired':policy['started_unix']=now-601;policy['deadline_unix']=now-1
    if case=='bytes':fixture['body']['padding']='x'*393216
    if case=='ledger-replay':
        row=dict(execution_profile=policy['execution_profile'],account=policy['account'],owner_sha256=policy['owner_sha256'],
            source_generation=policy['source_generation'],model='gpt-6.1-sol',effort='high',
            input_sha256=sha(enc(fixture['body']['input'])))
        put(root/'inference-ledger.json',[row])
    if case=='opaque-raw-client':fixture['opaque_raw_client']=True
    put(root/'policy.json',policy,True);put(root/'scope.json',scope,True);put(root/'fixture.json',fixture,True)
    sb=f'''(version 1)
(allow default)
(deny network*)
(deny file-read-data (require-all (subpath "/Users/sskim") (require-not (literal {json.dumps(str(binary))}))))
(deny file-write* (subpath "/Users/sskim"))
'''
    put(root/'host.sb',sb.encode(),True)
    env=dict(PATH='/usr/bin:/bin',HOME=str(root/'home'),CODEX_HOME=str(root/'codex-home'),TMPDIR=str(root/'tmp'),
        TM_P1_DISPATCH_POLICY=str(root/'policy.json'),TM_P1_DISPATCH_POLICY_SHA256=sha(enc(policy)),
        TM_SOL_TASK_SCOPE=str(root/'scope.json'),TM_SOL_TASK_SCOPE_SHA256=sha(enc(scope)),
        TM_P1_PREDISPATCH_PROBE='1',TM_C21L_OFFLINE_FIXTURE=str(root/'fixture.json'),
        CODEX_DISABLE_REMOTE_CONTROL='1',RUST_LOG='off')
    p=subprocess.run(['/usr/bin/sandbox-exec','-f',str(root/'host.sb'),str(binary)],env=env,cwd=root,capture_output=True,timeout=30)
    raw=p.stdout+p.stderr
    put(root/'process.stdout',p.stdout);put(root/'process.stderr',p.stderr)
    expected=77 if case=='positive' else 78
    passed=p.returncode==expected and (b'transport_called=false' in raw if case=='positive' else b'PREDISPATCH_DENIED' in raw)
    results.append(dict(case=case,exit=p.returncode,expected_exit=expected,pass_=passed,
        output_sha256=sha(raw),OS_network='DENIED_INCLUDING_LOOPBACK',credentials='SYNTHETIC_ONLY',
        predispatch_short_circuit=passed,transport_called=False if passed else 'UNVERIFIED'))
with (H/'OFFLINE_MATRIX.json').open('x') as f:json.dump(dict(binary_sha256=sha(binary.read_bytes()),
    cases=results,all_pass=all(x['pass_'] for x in results),scope='ACTUAL_BINARY_TRANSPORT_SEAM_NOT_MODEL_OR_STAGE_ACCEPT'),f,indent=2)
print(json.dumps(results))
