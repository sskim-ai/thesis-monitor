"""No models: exact disclaimer boundaries and deterministic execution custody."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services import vnext_dated_research_timing as timing
from app.services import vnext_execution_dependencies as dep
from app.services import vnext_balanced_stage_review as stage
from test_vnext_dated_research_timing import setup, validate
from test_vnext_stage_fork_handoff import Harness, cold_readback
from app.services.vnext_research_store import digest


def test_exact_disclaimer_is_summary_only_and_never_authority(monkeypatch):
    args=setup(monkeypatch)
    value=args[-1];value['summary']+=' '+timing.DATED_AUTHORITY_DENIAL
    result=validate(args)
    assert not any(result[k] for k in ('current_price','formal_timing','investment_axes_changed','strict_ready','send'))
    with pytest.raises(ValueError):timing._prose(value['summary'])
    for field in ('conflicts','uncertainty','change_condition','economic_separation'):
        old=value[field];value[field]=value['summary']
        with pytest.raises(ValueError):validate(args)
        value[field]=old


@pytest.mark.parametrize('text',[
    '현재가를 사용해 매수한다', '현재가 판단 권한을 부여한다',
    '권한을 부여하지 않는다. 그러나 현재가로 매수한다',
    '현재가 판단의 권한을 부여하지 않는 것은 아니다.',
    '승인된 판단이다. '+timing.DATED_AUTHORITY_DENIAL,
    '고지는 거짓이다. '+timing.DATED_AUTHORITY_DENIAL,
    '권한을 부여한다. '+timing.DATED_AUTHORITY_DENIAL,
    'BUY now. '+timing.DATED_AUTHORITY_DENIAL, 'SELL now. '+timing.DATED_AUTHORITY_DENIAL,
    '추세 100이다. '+timing.DATED_AUTHORITY_DENIAL, 'USD 가격이다. '+timing.DATED_AUTHORITY_DENIAL,
    '목표가를 정한다. '+timing.DATED_AUTHORITY_DENIAL, '지지 가격이 유효하다. '+timing.DATED_AUTHORITY_DENIAL,
    '금액 $이다. '+timing.DATED_AUTHORITY_DENIAL,
    '기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL+' 그러나 현재가로 매수한다.',
    '기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL.replace('하지 않는다','한다'),
    '기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL.replace('하지 않는다','하지 않는 것은 아니다'),
    '기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL.replace('현재가 판단','현재가의 판단'),
    '기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL.replace('권한을 부여','권한을  부여'),
    '기술 관측이다, '+timing.DATED_AUTHORITY_DENIAL,
    '"기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL+'"',
    '기술 관측이다. '+timing.DATED_AUTHORITY_DENIAL+'\n',
    '현 재 가 를 사 용 해 매 수 한 다. '+timing.DATED_AUTHORITY_DENIAL,
    '권 한 을 부 여 한 다. '+timing.DATED_AUTHORITY_DENIAL,
])
def test_disclaimer_cannot_launder_forbidden_assertions(text):
    with pytest.raises(ValueError,match='forbidden_prose'):timing._summary_prose(text)


def _manifest(tmp_path):
    root=tmp_path/'code';root.mkdir()
    files={}
    for category in ('source','helper','parser_pin'):
        p=root/(category+'.py');p.write_text('VALUE = 1\n');files[str(p)]=category
    return root,dep.freeze(files,inventory_roots=[root],module_roots=[root])


@pytest.mark.parametrize('mutation',['source','helper','parser_pin','new_file','unknown_module','symlink','missing'])
def test_real_changes_fail_before_intent_with_first_snapshot(tmp_path,mutation):
    root,manifest=_manifest(tmp_path);modules={}
    p=root/'source.py'
    if mutation in ('source','helper','parser_pin'):
        p=root/(mutation+'.py');p.write_text('VALUE = 2\n')
    elif mutation=='new_file':(root/'unreviewed.py').write_text('VALUE = 3\n')
    elif mutation=='unknown_module':
        p=root/'unknown.txt';p.write_text('VALUE = 3\n');modules={'unknown':SimpleNamespace(__file__=str(p))}
    elif mutation=='symlink':
        p.unlink();p.symlink_to(root/'helper.py')
    else:p.unlink()
    with pytest.raises(dep.DependencyDrift) as err:
        dep.check(manifest,phase='BEFORE_MODEL_INTENT',failure_dir=tmp_path/'failures',modules=modules)
    evidence=err.value.receipt.read_bytes()
    report=json.loads(evidence);assert report['phase']=='BEFORE_MODEL_INTENT' and not report['pass']
    assert any(report[k] for k in ('missing','new','modified','unexpected_modules','invalid'))
    # A later fix cannot replace the first mismatch snapshot.
    assert err.value.receipt.read_bytes()==evidence


def test_import_order_old_false_drift_fixed_across_fork_and_cold(tmp_path):
    root,manifest=_manifest(tmp_path)
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    program='''
import importlib.util,json,os,sys
from pathlib import Path
from app.services import vnext_execution_dependencies as d
m=json.loads(Path(sys.argv[1]).read_text());root=Path(next(iter(m['inventory_roots'])))
before={k:getattr(v,'__file__',None) for k,v in sys.modules.items() if str(root) in str(getattr(v,'__file__',None))}
for name in sys.argv[2].split(','):
 p=root/(name+'.py');s=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v)
after={k:getattr(v,'__file__',None) for k,v in sys.modules.items() if str(root) in str(getattr(v,'__file__',None))}
assert before!=after
r=d.check(m,phase='COLD_IMPORT',failure_dir=root.parent/'failures');assert r['pass']
pid=os.fork()
if pid==0:
 d.check(m,phase='FORK',failure_dir=root.parent/'failures');os._exit(0)
assert os.waitpid(pid,0)[1]==0
print(json.dumps(dict(pid=os.getpid(),fork_pid=pid,old_false_drift=True,fixed_pass=True)))
'''
    for order in ('source,helper,parser_pin','parser_pin,helper,source'):
        p=subprocess.run([sys.executable,'-B','-c',program,str(path),order],capture_output=True,text=True,timeout=30)
        assert p.returncode==0,p.stderr
        proof=json.loads(p.stdout);assert proof['fixed_pass'] and proof['old_false_drift']
        assert proof['pid']!=os.getpid() and proof['fork_pid']!=proof['pid']


def test_disclaimer_actual_fork_original_journal_cold_no_send(monkeypatch,tmp_path):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3',stage.DATED_TIMING_V2)
    h.value['summary']+=' '+timing.DATED_AUTHORITY_DENIAL
    b=h.run();assert b[1]['state']=='COMPLETED_NO_SEND';blind=h.restore(*b)
    a=h.run('ADJUDICATION',blind);assert a[1]['state']=='COMPLETED_NO_SEND'
    adj=h.restore(*a,name='ADJUDICATION',prior=blind)
    result=h.ctrl.finalize_timing(packet=h.packet,owner=stage.StageReviewOwner(blind,adj,enabled=True),timing_owner=h.o)
    metadata=tmp_path/'cold.json'
    metadata.write_text(json.dumps(dict(BLIND=b,ADJUDICATION=a,version=h.version,parent_pid=os.getpid(),outbox_sha=digest(result))))
    before=h.config.path.read_bytes()
    guard='from gate_a_guard import install; install();' if os.getenv('GATE_A_TEST_ROOT') else ''
    program=guard+'from test_vnext_stage_fork_handoff import cold_readback;import sys;cold_readback(*sys.argv[1:])'
    p=subprocess.run([sys.executable,'-B','-c',program,str(h.config.path),str(metadata)],capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr
    assert h.config.path.read_bytes()==before
    assert not result['send'] and not result['strict_ready']
