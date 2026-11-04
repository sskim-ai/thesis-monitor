"""Synthetic model only; real fork, original durable journal and cold interpreter."""
from contextlib import nullcontext
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from app.services import vnext_balanced_stage_review as stage
from app.services import vnext_dated_research_timing as timing
from app.services import vnext_no_send_runner as host
from app.services.vnext_dated_timing_controller import DatedTimingController, outbox_key
from app.services.vnext_research_store import ResearchStore, digest
from app.services.vnext_runtime import RuntimeConfig
from test_vnext_dated_research_timing import setup


def configuration(path):
    return RuntimeConfig(Path(path).resolve(), 'SYNTHETIC_GATE_A', 'write', 'test')


class Harness:
    def __init__(self, monkeypatch, path, version=stage.DATED_TIMING_V2, create=True):
        self.now = [0]
        self.o, self.economic, self.registry, self.packet, self.value = setup(
            monkeypatch, clock=lambda: self.now[0])
        self.version = version
        if create:
            ResearchStore(path)
        self.config = configuration(path)
        self.ctrl = DatedTimingController(self.config, enabled=True)
        self.identity = dict(account_scope='SYNTHETIC_GATE_A',
            security=self.packet['base']['public_security']['canonical_security_id'],
            frozen_input_sha256=digest(self.packet))
        self.parent_memory = {}
        self.granted = True

    def source(self):
        return timing.attach(self.economic, timing_owner=self.o, registry=self.registry,
                             cutoff=self.packet['base']['as_of'])

    def args(self, name, prior=None):
        return dict(invocation_id='SYNTHETIC_'+name, account=self.identity['account_scope'],
            packet=self.packet, stage=name, version=self.version, knowledge={}, registry=self.registry,
            source_loader=self.source, approval=lambda req: self.granted, account_lease=nullcontext,
            prior=prior, timing_owner=self.o, economic_loader=lambda: self.economic)

    def scope(self, name):
        return dict(mode='MANUAL_RESEARCH_CANARY', market='us', session='2026-10-28',
            prior_session=None, kind='NEW_SUBJECT_BOOTSTRAP', identity=self.identity,
            plan_sha256=digest(['SYNTHETIC', name]),
            expires_at=(datetime.now(timezone.utc)+timedelta(seconds=120)).isoformat())

    def invoke(self, req, text, deadline, bad=False):
        assert os.getpid() != self.parent_pid
        if req['stage']=='ADJUDICATION':
            assert 'NEW_ACCEPTED_BLIND_ONLY' in text
            assert req['prior_stage_sha'] is not None
        output=deepcopy(self.value)
        if bad:
            output['security_id']='ticker-is-not-canonical'
        checked=timing.validate_and_render(output,self.packet,registry=self.registry,
            timing_owner=self.o,economic_loader=lambda:self.economic)
        now=time.time()
        execution=dict(stage=req['stage'],status='VALIDATED',exit=0,attempt=1,retry=0,
            runtime=dict(verified=True,session='SYNTHETIC_'+req['stage']),
            model='gpt-6-astra',effort='xhigh',packet_sha=digest(self.packet),
            prompt_sha=digest(text.encode()),schema_sha=digest(stage.output_schema(self.packet,self.version)),
            output_sha=digest(output),started=now,ended=now,deadline=deadline,
            stage_contract=stage.CONTRACT,prompt_version=self.version,invocation_id=req['invocation_id'],
            request_sha=digest(req),approved_request_sha=digest(req))
        return dict(output=output,validation=checked,execution=execution)

    def run(self, name='BLIND', prior=None, bad=False):
        scope=self.scope(name); self.parent_pid=os.getpid()
        def operation(child, gate):
            ctrl=DatedTimingController(child.config,enabled=True)
            cap=ctrl.run_stage(**self.args(name,prior),
                invoke=lambda req,text,deadline:self.invoke(req,text,deadline,bad))
            self.parent_memory[name]=cap
            return dict(send=False,input_identity=self.identity,state='ACCEPTED_RESEARCH_STAGE',
                        stage=name,record_sha=digest(cap.snapshot()))
        result=host.run_manual_research(self.config,scope=scope,identity=self.identity,
            approval=lambda:digest(scope),operation=operation,enabled=True,timeout_seconds=30)
        assert self.parent_memory=={}, 'Fork memory is not parent authority'
        assert result['child_pid'] != os.getpid()
        return scope,result

    def restore(self, scope, result, name='BLIND', prior=None, **overrides):
        args=self.args(name,prior)
        args.update(host_scope=scope,host_attempt=result['attempt'])
        args.update(overrides)
        return self.ctrl.restore_stage(**args)


def cold_readback(path, metadata):
    """Fresh interpreter creates fresh synthetic source owners, never JSON owners."""
    data=json.loads(Path(metadata).read_text())
    h=Harness(pytest.MonkeyPatch(),Path(path),data['version'],create=False)
    assert os.getpid()!=data['parent_pid']
    blind=h.restore(*data['BLIND'])
    adj=h.restore(*data['ADJUDICATION'],name='ADJUDICATION',prior=blind)
    reviewed=stage.StageReviewOwner(blind,adj,enabled=True)
    result=h.ctrl.finalize_timing(packet=h.packet,owner=reviewed,timing_owner=h.o)
    stored=h.ctrl._read(outbox_key(h.packet),dict(contract=timing.CONTRACT,packet_sha256=digest(h.packet)))
    assert digest(stored)==data['outbox_sha']==digest(result)
    assert result['send'] is False and result['strict_ready'] is False
    print(json.dumps(dict(pid=os.getpid(),outbox_sha=digest(result),send=False,live_model_calls=0)))


@pytest.mark.parametrize('version',[stage.DATED_TIMING,stage.DATED_TIMING_V2])
def test_actual_fork_parent_adjudication_and_cold_outbox(monkeypatch,tmp_path,version):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3',version)
    b=h.run(); assert b[1]['state']=='COMPLETED_NO_SEND'
    before=h.config.path.read_bytes()
    blind=h.restore(*b)
    assert h.config.path.read_bytes()==before
    assert h.restore(*b).snapshot()==blind.snapshot()
    a=h.run('ADJUDICATION',blind);assert a[1]['state']=='COMPLETED_NO_SEND'
    adj=h.restore(*a,name='ADJUDICATION',prior=blind)
    owner=stage.StageReviewOwner(blind,adj,enabled=True)
    result=h.ctrl.finalize_timing(packet=h.packet,owner=owner,timing_owner=h.o)
    assert not result['send'] and not result['formal_timing'] and not result['current_price']
    metadata=tmp_path/'cold.json'
    metadata.write_text(json.dumps(dict(BLIND=b,ADJUDICATION=a,version=version,
        parent_pid=os.getpid(),outbox_sha=digest(result))))
    before=h.config.path.read_bytes()
    guard='from gate_a_guard import install; install();' if os.getenv('GATE_A_TEST_ROOT') else ''
    command=guard+'from test_vnext_stage_fork_handoff import cold_readback; import sys; cold_readback(*sys.argv[1:])'
    proc=subprocess.run([sys.executable,'-B','-c',command,str(h.config.path),str(metadata)],
                        capture_output=True,text=True,timeout=30)
    assert proc.returncode==0,proc.stderr
    proof=json.loads(proc.stdout);assert proof['pid']!=os.getpid() and not proof['send']
    assert h.config.path.read_bytes()==before
    with h.ctrl.store.connect() as c:
        keys=[r[0] for r in c.execute('SELECT key FROM research_meta')]
    assert sum('dated-timing-outbox-' in k for k in keys)==1
    assert not any('daily-outbox-' in k for k in keys)


@pytest.mark.parametrize('mutation',[
    'missing_accepted','missing_started','missing_manual_start','missing_host_end','missing_manual_done',
    'failed_stage','failed_host','request','prompt','schema','security','host_record_sha',
    'host_pid','host_scope_expiry','wrong_attempt','wrong_invocation','wrong_store',
    'unissued_receipt','source_revoked','source_expired','approval_revoked','account_stop',
])
def test_actual_journal_restore_fails_closed(monkeypatch,tmp_path,mutation):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3');scope,result=h.run()
    args=h.args('BLIND');req,_=stage._stage_request(**{k:args[k] for k in
        ('invocation_id','account','packet','stage','version','knowledge','registry','prior')})
    name=stage._stage_name(req);prefix='vnext-runtime-v1:job:'
    one=digest({k:v for k,v in scope.items() if k!='expires_at'})[:48]
    key={'missing_accepted':name+'-accepted','missing_started':name+'-started',
        'missing_manual_start':'manual-start-'+one,'missing_host_end':result['attempt']+'-end',
        'missing_manual_done':'manual-done-'+one}.get(mutation)
    # Direct mutations are adversarial test fixtures, never a production repair.
    with sqlite3.connect(h.config.path) as c:
        if key:c.execute('DELETE FROM research_meta WHERE key=?',(prefix+key,))
        if mutation in ('request','prompt','schema','security'):
            key=prefix+name+'-accepted'
            row=json.loads(c.execute('SELECT value FROM research_meta WHERE key=?',(key,)).fetchone()[0])
            if mutation=='security':row['result']['output']['security_id']='forged'
            else:row['result']['execution'][mutation+'_sha']='0'*64
            c.execute('UPDATE research_meta SET value=? WHERE key=?',(json.dumps(row),key))
        if mutation in ('host_record_sha','host_pid'):
            suffix='-response' if mutation=='host_record_sha' else '-child'
            key=prefix+result['attempt']+suffix
            row=json.loads(c.execute('SELECT value FROM research_meta WHERE key=?',(key,)).fetchone()[0])
            row['result']['record_sha' if mutation=='host_record_sha' else 'pid']='forged'
            c.execute('UPDATE research_meta SET value=? WHERE key=?',(json.dumps(row),key))
    override={}
    if mutation=='failed_stage':h.ctrl._append(name+'-failed',req,dict(state='FAILED_NO_RETRY'))
    if mutation=='failed_host':
        hr=dict(contract=host.CONTRACT,identity=h.identity,market=scope['market'],session=scope['session'],
            manual_scope_sha256=digest({k:v for k,v in scope.items() if k!='expires_at'}))
        h.ctrl._append(result['attempt']+'-failure',hr,dict(state='CALLBACK_FAILED'))
    if mutation=='host_scope_expiry':scope['expires_at']='2099-01-01T00:00:00+00:00'
    if mutation=='wrong_attempt':result['attempt']='host-forged'
    if mutation=='wrong_invocation':override['invocation_id']='SYNTHETIC_OTHER'
    if mutation=='wrong_store':
        ResearchStore(tmp_path/'other.sqlite3')
        h.ctrl=DatedTimingController(configuration(tmp_path/'other.sqlite3'),enabled=True)
    if mutation=='unissued_receipt':override['source_loader']=deepcopy(h.packet)
    if mutation=='source_revoked':h.o.revoke()
    if mutation=='source_expired':h.now[0]=1801
    if mutation=='approval_revoked':h.granted=False
    if mutation=='account_stop':h.ctrl.stop_participating_account(h.identity['account_scope'])
    before=h.config.path.read_bytes()
    with pytest.raises(ValueError):h.restore(scope,result,**override)
    assert before==h.config.path.read_bytes()


def test_failed_child_and_unknown_stage_are_not_retried(monkeypatch,tmp_path):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3');scope,result=h.run(bad=True)
    assert result['state']=='CALLBACK_FAILED'
    with pytest.raises(ValueError):h.restore(scope,result)
    def forbidden(*args):raise AssertionError('No retry/invoke permitted')
    with pytest.raises(ValueError,match='already_attempted'):
        h.ctrl.run_stage(**h.args('BLIND'),invoke=forbidden)
    args=h.args('ADJUDICATION')
    assert host.run_manual_research(h.config,scope=scope,identity=h.identity,
        approval=lambda:digest(scope),operation=forbidden,enabled=True)['state']=='MANUAL_ALREADY_ATTEMPTED'
    req,_=stage._stage_request(**{k:v for k,v in h.args('BLIND').items() if k in
        ('invocation_id','account','packet','stage','version','knowledge','registry','prior')})
    req['invocation_id']='SYNTHETIC_UNKNOWN'
    h.ctrl._append(stage._stage_name(req)+'-started',req,dict(state='IN_FLIGHT'))
    with pytest.raises(ValueError,match='already_attempted'):
        h.ctrl.run_stage(**dict(h.args('BLIND'),invocation_id='SYNTHETIC_UNKNOWN'),invoke=forbidden)


@pytest.mark.parametrize('market,code',[('KR','UNSEEN_KR'),('US','UNSEEN_ORDINARY'),('US','UNSEEN_ADS')])
def test_v2_exact_identity_const_without_authority_upgrade(monkeypatch,market,code):
    o,p,r,packet,value=setup(monkeypatch,code,market)
    schema=stage.output_schema(packet,stage.DATED_TIMING_V2)
    canonical=packet['base']['public_security']['canonical_security_id']
    assert schema['properties']['security_id']['const']==canonical
    text=stage.prompt(packet,'BLIND',knowledge={},registry=r,version=stage.DATED_TIMING_V2)
    assert canonical in text and 'exact' in text and 'Do not' in text
    checked=timing.validate_and_render(value,packet,registry=r,timing_owner=o,economic_loader=lambda:p)
    assert not checked['formal_timing'] and not checked['current_price'] and not checked['send']
    value['security_id']=code
    with pytest.raises(ValueError,match='research_timing_security'):
        timing.validate_and_render(value,packet,registry=r,timing_owner=o,economic_loader=lambda:p)


def test_restore_default_off_and_live_revocation(monkeypatch,tmp_path):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3');s,r=h.run();cap=h.restore(s,r)
    cap.revoke()
    with pytest.raises(ValueError,match='stage_revoked'):cap.snapshot()
    h.ctrl=DatedTimingController(h.config)
    with pytest.raises(ValueError,match='default_off'):h.restore(s,r)


@pytest.mark.parametrize('field',['prompt_sha','schema_sha','output_sha','security_id'])
def test_rehashed_host_envelope_cannot_replace_original_validation(monkeypatch,tmp_path,field):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3');scope,result=h.run()
    prefix='vnext-runtime-v1:job:'
    with sqlite3.connect(h.config.path) as c:
        rows={k:json.loads(v) for k,v in c.execute('SELECT key,value FROM research_meta') if k.startswith(prefix)}
        key=next(k for k in rows if k.endswith('-accepted'))
        accepted=rows[key]['result']
        if field=='security_id':
            accepted['output']['security_id']='forged-security'
            accepted['execution']['output_sha']=digest(accepted['output'])
        else:accepted['execution'][field]='0'*64
        stamp=digest(accepted)
        for row in rows.values():
            v=row['result']
            if 'record_sha' in v:v['record_sha']=stamp
            if isinstance(v.get('response'),dict) and 'record_sha' in v['response']:
                v['response']['record_sha']=stamp
        for k,v in rows.items():
            c.execute('UPDATE research_meta SET value=? WHERE key=?',(json.dumps(v),k))
    with pytest.raises(ValueError,match='research_timing_security|stage_exact_execution_binding'):
        h.restore(scope,result)


def test_live_reconsumption_rechecks_approval_source_and_store(monkeypatch,tmp_path):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3');scope,result=h.run();cap=h.restore(scope,result)
    h.granted=False
    with pytest.raises(ValueError,match='grant_required'):cap.snapshot()
    h.granted=True;h.now[0]=1801
    with pytest.raises(ValueError,match='expired'):cap.snapshot()
    h.now[0]=0
    # Replacement of the pinned store is not an authorized restart.
    moved=tmp_path/'original.sqlite3';h.config.path.rename(moved)
    ResearchStore(h.config.path)
    with pytest.raises(ValueError,match='database_identity_changed'):cap.snapshot()


@pytest.mark.parametrize('version,other',[(stage.DATED_TIMING,stage.DATED_TIMING_V2),
                                       (stage.DATED_TIMING_V2,stage.DATED_TIMING)])
def test_timing_mixed_versions_rejected_before_intent_and_on_snapshot(monkeypatch,tmp_path,version,other):
    h=Harness(monkeypatch,tmp_path/'research.sqlite3',version)
    b=h.run();blind=h.restore(*b)
    before=h.config.path.read_bytes();calls=[]
    def forbidden(*args):calls.append(True);raise AssertionError('Mixed versions must not invoke')
    with pytest.raises(ValueError,match='stage_timing_prompt_version_mismatch'):
        h.ctrl.run_stage(**dict(h.args('ADJUDICATION',blind),version=other),invoke=forbidden)
    assert not calls and h.config.path.read_bytes()==before
    a=h.run('ADJUDICATION',blind)
    adj=h.restore(*a,name='ADJUDICATION',prior=blind)
    assert adj.snapshot()['execution']['prompt_version']==version
    adj.version=other
    with pytest.raises(ValueError,match='stage_timing_prompt_version_mismatch'):adj.snapshot()
