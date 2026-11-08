"""Custody and finite scope for flexible public-tool output."""
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import zipfile
from datetime import datetime,timezone

sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
PRE=H.parent/'20261101-posco-p1-wire-schema'
spec=importlib.util.spec_from_file_location('wire_task',PRE/'task.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
pin,load,save,sha,wire,cmd,code,space=(getattr(prior,n) for n in ('pin','load','save','sha','wire','cmd','code','space'))
p0,ROOT,W,CLOUD,PY,BUILD,SOURCE,BIN=(getattr(prior,n) for n in ('p0','ROOT','W','CLOUD','PY','BUILD','SOURCE','BIN'))
BASE=H.parents[1]/'runs/c21p-20261108'
R=H/'result'
TASK_ID='C21P_0167_GUARDED_ADAPTER_CONTRACT_AND_ONE_CONDITIONAL_BLIND'
ATTACH=Path('/tmp/codex-remote-attachments/019f2bd6-93cc-7f32-b054-03ae39471eae/3A800849-9C1B-4798-BDC5-6F6C7C50A718/1-TM_POSCO_P1_FLEXIBLE_OUTPUT_INTEGRATED_CODEX_20261101.zip')
EXPECTED=dict(bytes=1633121,sha256='62f7be96bca47172b22cd60acaf8ce1787026daa21c7b1935f9f6a7d961761c4')

def baseline():
    assert not (H/'BASELINE.json').exists() and not BASE.exists()
    writers=[space(p) for p in (H,Path('/private/tmp'),CLOUD)]
    peak,reserve=12*1024**3,4*1024**3
    enough=all(x['free_bytes']>=peak+reserve for x in writers)
    save(H/'pre-gc-decision.json',dict(task=TASK_ID,at=datetime.now(timezone.utc).isoformat(),
        decision='PRE_GC_NOOP_SUFFICIENT' if enough else 'PRE_GC_CAPACITY_BLOCKED',writers=writers,
        peak_bytes=peak,reserve_bytes=reserve,required_existing_guard_bytes=0,required_bytes=peak+reserve,
        actions=[],deleted_files=0,observed_cleanup_gain_bytes=0,
        KEEP=['Code/WIP/Git','Active Source/Owner/CAS','Prior accepted and failed evidence','DB/secrets','Other projects'],
        plan='Reuse incremental build cache; narrow broker/guard proof and finite canary, no provider/full regression.',
        fd_limits=resource.getrlimit(resource.RLIMIT_NOFILE),open_fds=len(os.listdir('/dev/fd')),
        policy=pin(ROOT/'STANDING_PRE_GC_POLICY.md')))
    assert enough
    zpath=PRE/'TM_POSCO_P1_WIRE_SCHEMA_20261101_RESULT.zip'
    assert pin(zpath)==EXPECTED and zpath.with_suffix('.zip.sha256').read_text().split()[0]==EXPECTED['sha256']
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        m=json.loads(z.read('manifest.json'))['members']
        assert len(z.namelist())==len(set(z.namelist()))==126 and set(z.namelist())==set(m)|{'manifest.json'}
        assert all(dict(bytes=len(z.read(n)),sha256=sha(z.read(n)))==v for n,v in m.items())
        cb={n[9:]:z.read(n) for n in m if n.startswith('controls/')}
        ch=sha(''.join(f'{n}\t{len(b)}\t{sha(b)}\n' for n,b in sorted(cb.items()) if n!='result.sha256').encode())
        assert ch=='e7be6592bce0113029eb683127b3cbb7f561eb3cd4904ca7db12ca58641938c4'
        inherited={}
        for n in m:
            if n.startswith('implementation/codex-rs/'):
                rel=n.removeprefix('implementation/codex-rs/')
                assert pin(SOURCE/rel)==m[n]
                inherited[rel]=pin(SOURCE/rel);save(H/'baseline-source'/rel,z.read(n))
    with zipfile.ZipFile(ATTACH) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('MANIFEST.json'))
        save(H/'instruction-manifest-original.json',manifest)
        for n in z.namelist():
            assert Path(n).name==n
            save(H/'instruction'/n,z.read(n))
    app=code();assert sha(app)=='f52b0f7bd43c17b3f7c62fb04f3c4929dcd45a59c68b6eef6f04977052ee0a9c'
    assert pin(BIN)['sha256']=='166f8d4ebfe39647b96c867137f9ea01442f75a6ba8b242803a85d4c99dd4bb7'
    BASE.mkdir()
    with BIN.open('rb') as src,(BASE/'predecessor-codex-app-server').open('xb') as dst:shutil.copyfileobj(src,dst)
    records={str(p):pin(p) for p in (PRE/'result/live').rglob('*') if p.is_file()}
    for p in (prior.BASE/'inference-ledger.json',prior.BASE/'host-control-ledger.json',prior.BASE/'tool-budget.json',*prior.BASE.glob('response-*.json')):records[str(p)]=pin(p)
    save(H/'BASELINE.json',dict(task=TASK_ID,at=datetime.now(timezone.utc).isoformat(),predecessor=EXPECTED,controls9=ch,
        source_sha256=sha(app),source=app,source_host=inherited,host_binary=pin(BIN),installed_cli=pin(p0.CLI.resolve()),
        head=cmd('git','-C',str(W),'rev-parse','HEAD'),git_status=cmd('git','-C',str(W),'status','--porcelain=v2','--branch','--untracked-files=all'),
        attachment=pin(ATTACH),prior_live=records,
        approval=dict(basis='Latest user-delivered explicit finite instruction under standing attachment execution policy.',
            task=TASK_ID,stages=2,inference_requests=12,tools=24,stage_seconds=600,input_bytes=393216,output_bytes=131072,
            tool_capture_bytes=8388608,stage_capture_bytes=33554432,soft_delivery_target=262144,
            retry=0,finance=0,IBM=0,existing_DB=0,send=0,orders=0,scheduler=0,push=0,delete=0)))
    print(json.dumps(dict(status='BASELINE_PASS_PRE_GC_NOOP',free_gib=writers[0]['free_bytes']/1024**3)))

if __name__=='__main__':baseline()
