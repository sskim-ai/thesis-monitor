"""Synthetic Native env binding, never live Source, model, or operating DB work."""
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services.production_source_context import inspect_native
from app.services.unified_run_artifacts import sha256_bytes
from scripts.unified_stock_source_worker import encoded
from tests.test_manual_source_budget import offline_only

BASE='5e047adebbccbaecaf455f06e406d981f90d4a80'
REPO=Path(__file__).resolve().parents[1]
MARKER='SYNTHETIC_NATIVE_SECRET_NEVER_LOG'


@pytest.fixture
def native(tmp_path):
    root=tmp_path/'native'
    for name in ('app','app/providers','app/services'):
        folder=root/name
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'__init__.py').touch()
    (root/'app/config.py').write_text('''from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    kiwoom_app_key: str = ''
    kiwoom_secret_key: str = ''
    kiwoom_env: str = 'real'
    kiwoom_base_url_real: str = 'https://openapi.kiwoom.com'
    enable_live_provider: bool = False
    kiwoom_max_retries: int = 3
    kiwoom_timeout_seconds: float = 10
    sector_map_path: Path = Path('unused.csv')
    model_config = SettingsConfigDict(env_file='.env',extra='ignore')
    @property
    def kiwoom_base_url(self): return self.kiwoom_base_url_real
''')
    (root/'app/providers/kiwoom.py').write_text('''from datetime import datetime
class KiwoomAuth:
    def __init__(self,*a): pass
class KiwoomClient:
    def __init__(self,*a): pass
class KiwoomProvider:
    def __init__(self,*a): pass
''')
    for path,name in (('ohlcv_service.py','OhlcvService'),('symbol_resolver.py','SymbolResolver')):
        (root/'app/services'/path).write_text('class '+name+':\n    def __init__(self,*a): pass\n')
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1')
    for args in (['init','-q'],['add','app'],['-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',
            '-c','user.name=Offline Fixture','-c','user.email=fixture@example.invalid','commit','-qm','synthetic Native only']):
        subprocess.run(['/usr/bin/git',*args],cwd=root,env=env,check=True,capture_output=True)
    external=tmp_path/'operating/.env'
    external.parent.mkdir()
    external.write_text('KIWOOM_APP_KEY='+MARKER+'\nKIWOOM_SECRET_KEY='+MARKER+'_2\n'
        'ENABLE_LIVE_PROVIDER=true\nKIWOOM_BASE_URL_REAL=https://api.kiwoom.com\n')
    external.chmod(0o600)
    return SimpleNamespace(root=root,env=external,tmp=tmp_path,
        config=SimpleNamespace(native_python=sys.executable,native_owner_root=str(root)))


def inspected(n,label='inspect'):
    folder=n.tmp/label
    folder.mkdir()
    return inspect_native(n.config,folder,settings_env_file=str(n.env))


def packet(n,owner):
    return dict(native_owner=owner,us_market_symbols=[],stock_plan=dict(run_id='SYNTHETIC_ENV',
        acquisition_id='SYNTHETIC_ENV:stock',reads=[dict(subject='SYNTHETIC_ONLY')],
        **{k:owner[k] for k in ('owner_head','owner_files','settings_sha256','request_environment_sha256')}))


def start_worker(n,value,*,bad_sha=False,expected_sha=None):
    path=n.tmp/('input-'+str(len(list(n.tmp.glob('input-*'))))+'.json')
    path.write_bytes(encoded(value))
    output=n.tmp/(path.stem+'-output')
    # The actual production r9 worker/main and config guard run. Only acquisition
    # and replay payloads are synthetic; no transport or Owner grant is installed.
    script='''import sys,json
from pathlib import Path
from scripts import r9_rev11_native_worker as w
frozen=json.loads(Path(sys.argv[2]).read_bytes())
native_root=Path(sys.argv[1])
def acquire(plan,root,owner,settings,**kw):
    from app.config import Settings
    p=frozen['native_owner']['settings_env_file']
    config=w.stock_worker.owner_configuration(native_root,Settings(_env_file=p),settings_env_file=p)
    assert config==frozen['native_owner']
    root.mkdir(parents=True)
    return {'SYNTHETIC_DOMAIN':True}
def replay(plan,root,owner,**kw):
    (root.parent/'raw-owner-replay.json').write_text(json.dumps([{'status':'PASS'}]))
w.stock_worker.acquire=acquire
w.stock_worker.replay=replay
sys.argv=['native-worker','--owner-root',sys.argv[1],'--input',sys.argv[2],'--sha256',sys.argv[3],'--output',sys.argv[4]]
w.main()
'''
    digest=expected_sha or ('0'*64 if bad_sha else sha256_bytes(path.read_bytes()))
    return subprocess.Popen([sys.executable,'-B','-c',script,str(n.root),str(path),digest,str(output)],
        cwd=REPO,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0'),
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)


def finish(process,commands):
    out,err=process.communicate(''.join(json.dumps(c)+'\n' for c in commands),timeout=30)
    assert MARKER not in out+err
    return process.returncode,out,err


def test_external_env_inspection_is_pinned_without_dirtying_native(native):
    n=native
    result=inspected(n)
    assert result['credentials_present'] and result['live_provider'] and result['owner_clean']
    assert result['settings_env_file']==str(n.env)
    assert result['settings_env_file_sha256']==sha256_bytes(n.env.read_bytes())
    assert not (n.root/'.env').exists()
    assert not subprocess.check_output(['/usr/bin/git','status','--porcelain'],cwd=n.root).strip()
    assert MARKER not in json.dumps(result)


def test_actual_r9_acquire_replay_uses_inspected_file_and_digests(native):
    n=native
    value=packet(n,inspected(n))
    code,out,err=finish(start_worker(n,value),[{'stocks':True},{'replay-stocks':True},{'close':True}])
    assert code==0,err
    assert [json.loads(line)['result']['status'] for line in out.splitlines()]==[
        'STOCK_CAPTURE_COMPLETE_NOT_QUALIFIED','PASS']
    assert not (n.root/'.env').exists()


def test_missing_relative_symlink_or_forged_env_reference_denied(native,monkeypatch):
    n=native
    for name,path in (('relative','.env'),('missing',str(n.tmp/'missing.env'))):
        with pytest.raises(ValueError,match='native_settings_regular_absolute_file_required'):
            inspect_native(n.config,n.tmp,settings_env_file=path)
    link=n.tmp/'linked.env'
    link.symlink_to(n.env)
    with pytest.raises(ValueError,match='native_settings_regular_absolute_file_required'):
        inspect_native(n.config,n.tmp,settings_env_file=str(link))
    from app.services import production_source_context as context
    def forged(argv,**kw):
        output=Path(argv[argv.index('--output')+1])
        output.write_text(json.dumps(dict(settings_env_file=str(n.tmp/'other.env'),
            settings_env_file_sha256=sha256_bytes(n.env.read_bytes()))))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(context.subprocess,'run',forged)
    with pytest.raises(ValueError,match='production_native_settings_file_drift'):
        inspect_native(n.config,n.tmp,settings_env_file=str(n.env))


def test_frozen_input_generation_code_and_settings_tampering_denied(native):
    n=native
    owner=inspected(n)
    code,out,err=finish(start_worker(n,packet(n,owner),bad_sha=True),[])
    assert code!=0 and 'native_input_hash_mismatch' in err
    original=packet(n,owner)
    changed=deepcopy(original)
    changed['stock_plan']['run_id']='ALTERED_GENERATION'
    code,out,err=finish(start_worker(n,changed,expected_sha=sha256_bytes(encoded(original))),[])
    assert code!=0 and 'native_input_hash_mismatch' in err
    for field in ('owner_head','owner_files','settings_sha256','request_environment_sha256'):
        bad=deepcopy(owner)
        bad[field]={'app/config.py':'0'*64} if field=='owner_files' else '0'*64
        code,out,err=finish(start_worker(n,packet(n,bad)),[])
        assert code!=0 and 'native_owner_configuration_drift' in err
    bad=packet(n,owner)
    bad['stock_plan']['settings_sha256']='0'*64
    code,out,err=finish(start_worker(n,bad),[])
    assert code!=0 and 'native_stock_plan_configuration_drift' in err


def test_env_content_change_between_acquire_and_replay_stops(native):
    n=native
    process=start_worker(n,packet(n,inspected(n)))
    try:
        process.stdin.write(json.dumps({'stocks':True})+'\n')
        process.stdin.flush()
        line=process.stdout.readline()
        assert 'STOCK_CAPTURE_COMPLETE_NOT_QUALIFIED' in line
        # Even an ignored comment must change the bound file SHA.
        n.env.write_text(n.env.read_text()+'# changed after acquire\n')
        code,out,err=finish(process,[{'replay-stocks':True}])
        assert code!=0 and 'native_owner_configuration_drift' in err
    finally:
        if process.poll() is None:process.kill();process.wait()


def test_original_live_credential_gates_and_unrelated_policies_stay_closed(native):
    n=native
    original=n.env.read_text()
    for i,value in enumerate((original.replace('ENABLE_LIVE_PROVIDER=true','ENABLE_LIVE_PROVIDER=false'),
            original.replace('KIWOOM_APP_KEY='+MARKER,'KIWOOM_APP_KEY='))):
        n.env.write_text(value)
        with pytest.raises(ValueError,match='production_native_owner_not_qualified'):
            inspected(n,'negative-'+str(i))
    path=REPO/'app/jobs/unified_market_snapshot.py'
    before=ast.parse(subprocess.check_output(['/usr/bin/git','show',BASE+':app/jobs/unified_market_snapshot.py'],cwd=REPO))
    current=ast.parse(path.read_bytes())
    calls=[x for x in ast.walk(current) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='inspect_native']
    assert len(calls)==1 and calls[0].keywords[0].arg=='settings_env_file'
    calls[0].keywords=[]
    assert ast.dump(before)==ast.dump(current)
