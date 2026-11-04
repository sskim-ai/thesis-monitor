"""V3 synthetic boundaries using original source/stage/host/store implementations."""
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from app.services import vnext_balanced_stage_review as stage
from app.services import vnext_dated_research_timing as legacy
from app.services import vnext_dated_research_timing_v3 as v3
from app.services import vnext_no_send_runner as host
from app.services.vnext_dated_timing_controller import outbox_key
from app.services.vnext_research_store import digest
from test_vnext_dated_research_timing import setup
from test_vnext_stage_fork_handoff import Harness


def candidate(value):
    out=deepcopy(value)
    out.update(contract=v3.CONTRACT,current_price=False,formal_timing=False,strict_ready=False,send=False)
    out['summary']='추세와 모멘텀의 차이를 반영한 혼재 상태다.'
    out['economic_separation']='사업 자료와 가치평가 관측은 각각의 기준일과 자료 한계를 따로 검토한다.'
    return out


def context(monkeypatch,code='UNSEEN',market='US'):
    owner,economic,registry,packet,value=setup(monkeypatch,code,market)
    packet=v3.attach(economic,timing_owner=owner,registry=registry,cutoff=packet['technical']['cutoff'])
    return owner,economic,registry,packet,candidate(value)


def validate(ctx):
    o,e,r,p,v=ctx
    return v3.validate_and_render(v,p,registry=r,timing_owner=o,economic_loader=lambda:e)


class V3Harness(Harness):
    def __init__(self,monkeypatch,path,create=True):
        super().__init__(monkeypatch,path,stage.DATED_TIMING_V3,create)
        self.packet=v3.attach(self.economic,timing_owner=self.o,registry=self.registry,
                              cutoff=self.packet['technical']['cutoff'])
        self.value=candidate(self.value)
        self.identity['frozen_input_sha256']=digest(self.packet)

    def source(self):
        return v3.attach(self.economic,timing_owner=self.o,registry=self.registry,
                         cutoff=self.packet['technical']['cutoff'])

    def invoke(self,req,text,deadline,bad=False):
        assert os.getpid()!=self.parent_pid
        assert req['contract']==stage.TIMING_V3_EXECUTION_CONTRACT
        if req['stage']=='ADJUDICATION':assert req['prior_stage_sha'] and 'NEW_ACCEPTED_BLIND_ONLY' in text
        output=deepcopy(self.value)
        if bad:output['security_id']='forged'
        checked=v3.validate_and_render(output,self.packet,registry=self.registry,
                                       timing_owner=self.o,economic_loader=lambda:self.economic)
        now=time.time()
        execution=dict(stage=req['stage'],status='VALIDATED',exit=0,attempt=1,retry=0,
            runtime=dict(verified=True,session='SYNTHETIC_V3_'+req['stage']),model='gpt-6-astra',effort='xhigh',
            packet_sha=digest(self.packet),prompt_sha=digest(text.encode()),
            schema_sha=digest(stage.output_schema(self.packet,self.version)),output_sha=digest(output),
            started=now,ended=now,deadline=deadline,stage_contract=req['contract'],prompt_version=self.version,
            invocation_id=req['invocation_id'],request_sha=digest(req),approved_request_sha=digest(req))
        return dict(output=output,validation=checked,execution=execution)


def cold(path,metadata):
    data=json.loads(Path(metadata).read_text())
    h=V3Harness(pytest.MonkeyPatch(),Path(path),create=False)
    blind=h.restore(*data['BLIND'])
    adj=h.restore(*data['ADJUDICATION'],name='ADJUDICATION',prior=blind)
    reviewed=stage.StageReviewOwner(blind,adj,enabled=True)
    stored=h.ctrl._read(outbox_key(h.packet),dict(contract=v3.CONTRACT,packet_sha256=digest(h.packet)))
    checked=reviewed.consume(reviewed.issue(),packet=h.packet)
    assert stored['validation']==checked and digest(stored)==data['outbox_sha']
    assert stored['authority_notice']==v3.authority_notice(h.packet,checked)
    assert stored['rendered'].count(v3.NOTICE_TEXT)==1
    assert os.getpid()!=data['parent_pid']
    print(json.dumps(dict(pid=os.getpid(),state='SYNTHETIC_V3_COLD_PASS',outbox_sha=digest(stored),models=0)))


def test_v3_actual_fork_parent_and_read_only_cold(monkeypatch,tmp_path):
    h=V3Harness(monkeypatch,tmp_path/'research.sqlite3')
    b=h.run();assert b[1]['state']=='COMPLETED_NO_SEND'
    blind=h.restore(*b)
    a=h.run('ADJUDICATION',blind);assert a[1]['state']=='COMPLETED_NO_SEND'
    adj=h.restore(*a,name='ADJUDICATION',prior=blind)
    reviewed=stage.StageReviewOwner(blind,adj,enabled=True)
    result=h.ctrl.finalize_timing(packet=h.packet,owner=reviewed,timing_owner=h.o)
    assert h.ctrl.finalize_timing(packet=h.packet,owner=reviewed,timing_owner=h.o)==result
    assert result['rendered'].count(v3.NOTICE_TEXT)==1
    assert v3.NOTICE_TEXT not in json.dumps(adj.snapshot()['output'],ensure_ascii=False)
    assert not any(result[k] for k in ('send','formal_timing','current_price','strict_ready'))
    metadata=tmp_path/'cold.json'
    metadata.write_text(json.dumps(dict(BLIND=b,ADJUDICATION=a,parent_pid=os.getpid(),outbox_sha=digest(result))))
    before=h.config.path.read_bytes()
    guard='from gate_a_guard import install; install();' if os.getenv('GATE_A_TEST_ROOT') else ''
    proc=subprocess.run([sys.executable,'-B','-c',guard+'from test_vnext_timing_v3 import cold; import sys; cold(*sys.argv[1:])',
                         str(h.config.path),str(metadata)],capture_output=True,text=True,timeout=60)
    assert proc.returncode==0,proc.stderr
    assert h.config.path.read_bytes()==before
    print(json.dumps(dict(kind='SYNTHETIC_ONLY',parent_pid=os.getpid(),blind_pid=b[1]['child_pid'],
        adj_pid=a[1]['child_pid'],cold=json.loads(proc.stdout),actual_models=0)))


@pytest.mark.parametrize('market,code',[('KR','NEW_KR'),('US','NEW_ORDINARY'),('US','NEW_ADS')])
def test_v3_identity_and_backend_notice(monkeypatch,market,code):
    ctx=context(monkeypatch,code,market);checked=validate(ctx)
    packet=ctx[3];s=stage.output_schema(packet,stage.DATED_TIMING_V3)
    assert s['properties']['security_id']['const']==packet['base']['public_security']['canonical_security_id']
    assert s['properties']['contract']['const']==v3.CONTRACT
    assert checked['authority_notice']['text_sha256']==digest(v3.NOTICE_TEXT.encode())
    assert checked['rendered'].count(v3.NOTICE_TEXT)==1
    assert v3.ENABLED_BY_DEFAULT is False
    assert outbox_key(packet)!=outbox_key(dict(packet,contract=legacy.CONTRACT))


@pytest.mark.parametrize('text',[
    '현재가의 근거를 대체하지 않는다.', '현재가를 사용해 매수한다.', '권한을 부여한다.',
    '권한을 부여하지 않는 것은 아니다.', '기술 상태다. '+legacy.DATED_AUTHORITY_DENIAL,
    '고지는 무효다.', '현재 가 사용을 승인한다.', 'BUY', 'SELL', '목표가 상승',
    '지지 가격과 가격구간', '허용하지 않는다. 그러나 매수한다.', 'authority is not granted',
    'no current price permission', '', '지표 42 상승', '지표 $ 상승',
])
def test_v3_prose_has_no_notice_exemption(monkeypatch,text):
    ctx=context(monkeypatch);ctx[4]['summary']=text
    with pytest.raises(ValueError):validate(ctx)


@pytest.mark.parametrize('field',['conflicts','uncertainty','change_condition','economic_separation','interpretation','reasoning'])
def test_all_prose_slots_reject_notice(monkeypatch,field):
    ctx=context(monkeypatch);v=ctx[4]
    target=v['citations'][0] if field=='interpretation' else v['periods'][0] if field=='reasoning' else v
    target[field]='현재가의 근거를 대체하지 않는다.'
    with pytest.raises(ValueError,match='MODEL_AUTHORITY_NOTICE_IN_PROSE'):validate(ctx)


@pytest.mark.parametrize('mutation',['date','value','hash','duplicate','missing_period','security','extra_notice','flag','packet','scope'])
def test_v3_source_and_notice_fail_closed(monkeypatch,mutation):
    ctx=context(monkeypatch);packet,value=ctx[3:]
    if mutation=='date':value['citations'][0]['period_end']='2099-01-01'
    if mutation=='value':value['citations'][0]['value']='100000'
    if mutation=='hash':value['citations'][0]['source_sha256']=['0'*64]
    if mutation=='duplicate':value['citations'].append(deepcopy(value['citations'][0]))
    if mutation=='missing_period':value['periods'].pop()
    if mutation=='security':value['security_id']='wrong-security'
    if mutation=='extra_notice':value['authority_notice']='changed'
    if mutation=='flag':value['send']=True
    if mutation=='packet':packet['contract']=legacy.CONTRACT
    if mutation=='scope':packet['technical']['current_price']=True
    with pytest.raises(ValueError):validate(ctx)


@pytest.mark.parametrize('old',[stage.DATED_TIMING,stage.DATED_TIMING_V2])
def test_old_blind_cannot_start_v3_adjudication(monkeypatch,tmp_path,old):
    h=Harness(monkeypatch,tmp_path/'old.sqlite3',old);b=h.run();prior=h.restore(*b)
    before=h.config.path.read_bytes();calls=[]
    with pytest.raises(ValueError,match='STAGE_VERSION_MISMATCH_PRECALL'):
        h.ctrl.run_stage(**dict(h.args('ADJUDICATION',prior),version=stage.DATED_TIMING_V3),invoke=lambda *a:calls.append(a))
    assert not calls and h.config.path.read_bytes()==before


def test_v3_duplicate_parallel_and_tampered_journal(monkeypatch,tmp_path):
    h=V3Harness(monkeypatch,tmp_path/'v3.sqlite3');scope=h.scope('BLIND');calls=[]
    with open(str(h.config.path)+'.no-send-runner.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        blocked=host.run_manual_research(h.config,scope=scope,identity=h.identity,
            approval=lambda:digest(scope),operation=lambda *a:calls.append(a),enabled=True,timeout_seconds=30)
        assert blocked['state']=='OVERLAP_SKIPPED' and not calls
    b=h.run();blind=h.restore(*b)
    for version in (stage.DATED_TIMING,stage.DATED_TIMING_V2):
        with pytest.raises(ValueError,match='STAGE_VERSION_MISMATCH_PRECALL'):
            h.ctrl.run_stage(**dict(h.args('ADJUDICATION',blind),version=version),invoke=lambda *a:calls.append(a))
    same=h.ctrl.run_stage(**h.args('BLIND'),invoke=lambda *a:calls.append(a))
    assert same.snapshot()==blind.snapshot()
    assert not calls
    req,_=stage._stage_request(**{k:v for k,v in h.args('BLIND').items() if k in
        ('invocation_id','account','packet','stage','version','knowledge','registry','prior')})
    key='vnext-runtime-v1:job:'+stage._stage_name(req)+'-accepted'
    with sqlite3.connect(h.config.path) as db:
        row=json.loads(db.execute('SELECT value FROM research_meta WHERE key=?',(key,)).fetchone()[0])
        row['result']['execution']['schema_sha']='0'*64
        db.execute('UPDATE research_meta SET value=? WHERE key=?',(json.dumps(row),key))
    with pytest.raises(ValueError):h.restore(*b)


def test_v3_failed_child_cannot_be_restored_or_retried(monkeypatch,tmp_path):
    h=V3Harness(monkeypatch,tmp_path/'v3.sqlite3');b=h.run(bad=True)
    assert b[1]['state']=='CALLBACK_FAILED'
    with pytest.raises(ValueError):h.restore(*b)
    def forbidden(*args):raise AssertionError('No retry')
    with pytest.raises(ValueError,match='already_attempted'):h.ctrl.run_stage(**h.args('BLIND'),invoke=forbidden)


@pytest.mark.parametrize('version',[stage.DATED_TIMING,stage.DATED_TIMING_V2,stage.DATED_TIMING_V3])
def test_wrong_packet_version_fails_before_intent(monkeypatch,tmp_path,version):
    h=V3Harness(monkeypatch,tmp_path/'version.sqlite3');calls=[]
    if version==stage.DATED_TIMING_V3:h.packet['contract']=legacy.CONTRACT
    before=h.config.path.read_bytes()
    with pytest.raises(ValueError,match='STAGE_VERSION_MISMATCH_PRECALL'):
        h.ctrl.run_stage(**dict(h.args('BLIND'),version=version),invoke=lambda *a:calls.append(a))
    assert not calls and h.config.path.read_bytes()==before
