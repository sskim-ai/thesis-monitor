from contextlib import contextmanager, nullcontext
from copy import deepcopy
import time

import pytest

from app.services import vnext_balanced_stage_review as m
from app.services.vnext_research_store import digest
from test_vnext_balanced_research import fixture


def stage_record(p,v,r,stage='BLIND',prior=None,version=m.ORIGINAL,request=None,deadline=None):
    now=time.time()
    text=m.prompt(p,stage,knowledge={},registry=r,prior=prior,version=version)
    e=dict(stage=stage,status='VALIDATED',exit=0,attempt=1,retry=0,
        runtime=dict(verified=True,session='SYNTHETIC_'+stage),model='gpt-6-astra',effort='xhigh',
        packet_sha=digest(p),prompt_sha=digest(text.encode()),schema_sha=digest(m.balanced.schema()),
        output_sha=digest(v),started=now,ended=now,deadline=deadline or now+600,
        stage_contract=m.CONTRACT,prompt_version=version,invocation_id='UNIT',
        request_sha=digest(request or {}),approved_request_sha=digest(request or {}))
    return dict(output=deepcopy(v),validation=m.balanced.validate_and_render(v,p,registry=r),execution=e)


def cap(p,v,r,stage='BLIND',prior=None,version=m.ORIGINAL,legacy=False):
    row=stage_record(p,v,r,stage,prior.snapshot()['output'] if prior else None,version)
    return m.AcceptedStage(lambda:deepcopy(row),packet=p,stage=stage,version=version,
        knowledge={},registry=r,source_loader=lambda:deepcopy(p),prior=prior,legacy_blind=legacy),row


class MemoryController(m.StageController):
    """Only the journal is in memory; no file DB or model in these unit tests."""
    def __init__(self,enabled=True):
        self.enabled=enabled;self.rows={};self._host_slot_guard=None;self._host_recovery_guard=None
    def _read(self,name,request):
        if name not in self.rows:return None
        pin,value=self.rows[name]
        if pin!=digest(request):raise ValueError('controller_journal_binding')
        return deepcopy(value)
    def _append(self,name,request,result):
        old=self._read(name,request)
        if old is not None:
            if old!=result:raise ValueError('controller_journal_conflict')
            return False
        self.rows[name]=(digest(request),deepcopy(result));return True


def args(p,v,r,stage='BLIND',prior=None):
    def invoke(request,text,deadline):
        return stage_record(p,v,r,stage,prior.snapshot()['output'] if prior else None,
            request=request,deadline=deadline)
    return dict(invocation_id='UNIT',account='TEST_ACCOUNT',packet=p,stage=stage,
        version=m.ORIGINAL,knowledge={},registry=r,source_loader=lambda:deepcopy(p),
        approval=lambda _:True,account_lease=nullcontext,invoke=invoke,prior=prior)


def test_accepted_legacy_blind_reused_without_reexecution():
    p,v,r=fixture();b,_=cap(p,v,r,legacy=True);c=MemoryController();calls=[]
    a=args(p,v,r,'ADJUDICATION',b);original=a['invoke']
    a['invoke']=lambda *x:(calls.append(x[0]['stage']) or original(*x))
    adj=c.run_stage(**a);owner=m.StageReviewOwner(b,adj,enabled=True)
    receipt=owner.issue();assert owner.consume(receipt,packet=p)['balanced']['newbuyer_fundamental']=='ATTRACTIVE'
    assert calls==['ADJUDICATION'] and not receipt['original_shared_deadline_claimed']
    assert not receipt['strict_B2'] and not receipt['send']


@pytest.mark.parametrize('first,second',[(m.ORIGINAL,m.EXPLICIT),(m.EXPLICIT,m.ORIGINAL)])
def test_balanced_original_explicit_cross_compatibility_preserved(first,second):
    p,v,r=fixture();b,_=cap(p,v,r,version=first)
    request,_=m._stage_request(invocation_id='CROSS_COMPAT',account='TEST_ACCOUNT',packet=p,
        stage='ADJUDICATION',version=second,knowledge={},registry=r,prior=b)
    assert request['prompt_version']==second
    a,_=cap(p,v,r,'ADJUDICATION',b,version=second)
    assert a.snapshot()['execution']['prompt_version']==second


def test_default_off_and_explicit_new_grant():
    p,v,r=fixture();b,_=cap(p,v,r);a,_=cap(p,v,r,'ADJUDICATION',b)
    with pytest.raises(ValueError,match='default_off'):m.StageReviewOwner(b,a)
    with pytest.raises(ValueError,match='default_off'):MemoryController(False).run_stage(**args(p,v,r))
    kw=args(p,v,r);kw['approval']=lambda _:False
    with pytest.raises(ValueError,match='explicit_new_stage_grant'):MemoryController().run_stage(**kw)


def test_failed_old_adjudication_and_bad_deadline_cannot_import():
    p,v,r=fixture();b,_=cap(p,v,r,legacy=True);a,row=cap(p,v,r,'ADJUDICATION',b)
    row['execution']['status']='FAILED_NO_RETRY'
    with pytest.raises(ValueError):a.snapshot()
    row['execution']['status']='VALIDATED';row['execution']['deadline']=row['execution']['started']+601
    with pytest.raises(ValueError):m.AcceptedStage(lambda:row,packet=p,stage='ADJUDICATION',
        version=m.ORIGINAL,knowledge={},registry=r,source_loader=lambda:p,prior=b)
    with pytest.raises(ValueError,match='only_original_accepted_blind'):cap(p,v,r,'ADJUDICATION',b,legacy=True)


def test_idempotent_lookup_and_no_failed_stage_retry():
    p,v,r=fixture();c=MemoryController();kw=args(p,v,r);calls=[];original=kw['invoke']
    kw['invoke']=lambda *x:(calls.append(1) or original(*x))
    a=c.run_stage(**kw);assert c.run_stage(**kw).snapshot()==a.snapshot() and calls==[1]
    c=MemoryController()
    def fail(*_):raise TimeoutError('synthetic')
    kw['invoke']=fail
    with pytest.raises(TimeoutError):c.run_stage(**kw)
    with pytest.raises(ValueError,match='already_attempted_no_retry'):c.run_stage(**kw)
    assert any(x[1].get('state')=='FAILED_NO_RETRY' for x in c.rows.values())


def test_sticky_stop_busy_lease_and_host_guard_prevent_call():
    p,v,r=fixture();c=MemoryController();kw=args(p,v,r);c.stop_participating_account('TEST_ACCOUNT')
    with pytest.raises(ValueError,match='account_stopped'):c.run_stage(**kw)
    @contextmanager
    def busy():
        raise ValueError('busy_account');yield
    kw['account_lease']=busy
    with pytest.raises(ValueError,match='busy_account'):MemoryController().run_stage(**kw)
    c=MemoryController();kw['account_lease']=nullcontext
    def halted():raise ValueError('host_stop')
    c._host_slot_guard=halted
    with pytest.raises(ValueError,match='host_stop'):c.run_stage(**kw)


def test_wrong_source_security_date_and_prior_binding():
    p,v,r=fixture();b,_=cap(p,v,r,legacy=True)
    for field,value in [('as_of','2026-10-30T12:00:00+00:00'),('ticker','OTHER')]:
        wrong=deepcopy(p);wrong['base'][field]=value
        with pytest.raises(ValueError,match='prior_packet_binding'):MemoryController().run_stage(**args(wrong,v,r,'ADJUDICATION',b))
    kw=args(p,v,r);kw['source_loader']=lambda:{}
    with pytest.raises(ValueError,match='source_changed_before_call'):MemoryController().run_stage(**kw)


def test_prompt_versions_keep_original_and_only_clarify_semantics():
    p,v,r=fixture();old=m.balanced.prompt(p,'BLIND',knowledge={},registry=r)
    assert m.prompt(p,'BLIND',knowledge={},registry=r)==old
    new=m.prompt(p,'BLIND',knowledge={},registry=r,version=m.EXPLICIT)
    assert new.startswith(old) and 'timing.state=UNRESOLVED cannot have LOW' in new
    assert m.balanced.schema()==m.balanced.schema()


def test_unresolved_low_denied_and_unissued_confidence_admitted():
    p,v,r=fixture();v['balanced']['timing'].update(state='UNRESOLVED',confidence='LOW')
    before=deepcopy(v)
    with pytest.raises(ValueError,match='balanced_unissued_axis_confidence'):m.balanced.validate_and_render(v,p,registry=r)
    assert v==before
    synthetic=deepcopy(v);synthetic['balanced']['timing']['confidence']='NOT_SEPARATELY_ISSUED'
    assert m.balanced.validate_and_render(synthetic,p,registry=r)['balanced']['timing']['state']=='UNRESOLVED'


def test_private_context_and_wrong_axis_refs_denied():
    p,v,r=fixture()
    for field,value in [('holdings_included',True),('user_thesis_included',True)]:
        wrong=deepcopy(v);wrong[field]=value
        with pytest.raises(ValueError):cap(p,wrong,r)
    v['balanced']['valuation']['refs']=['price']
    with pytest.raises(ValueError):cap(p,v,r)


def test_mutation_revocation_forged_receipt_and_same_context_fail():
    p,v,r=fixture();b,row=cap(p,v,r);a,arow=cap(p,v,r,'ADJUDICATION',b)
    owner=m.StageReviewOwner(b,a,enabled=True);receipt=owner.issue()
    with pytest.raises(ValueError):owner.consume(dict(receipt),packet=p)
    b.revoke()
    with pytest.raises(ValueError,match='stage_revoked'):owner.issue()
    b,row=cap(p,v,r);row['output']['summary']='tampered'
    with pytest.raises(ValueError,match='record_changed'):b.snapshot()


def test_request_tamper_and_late_result_fail_before_acceptance():
    p,v,r=fixture()
    for name,value in [('request_sha','forged'),('deadline',0),('attempt',2)]:
        c=MemoryController();kw=args(p,v,r);original=kw['invoke']
        def invoke(*x):
            row=original(*x);row['execution'][name]=value;return row
        kw['invoke']=invoke
        with pytest.raises(ValueError):c.run_stage(**kw)
        assert not any(k.endswith('-accepted') for k in c.rows)


def test_shared_runtime_context_rejected():
    p,v,r=fixture();b,_=cap(p,v,r);row=stage_record(p,v,r,'ADJUDICATION',v)
    row['execution']['runtime']['session']='SYNTHETIC_BLIND'
    a=m.AcceptedStage(lambda:row,packet=p,stage='ADJUDICATION',version=m.ORIGINAL,
        knowledge={},registry=r,source_loader=lambda:p,prior=b)
    with pytest.raises(ValueError,match='distinct_model_contexts'):m.StageReviewOwner(b,a,enabled=True).issue()


def test_unseen_typed_identity_same_contract():
    for ticker,country,kind in [('UNSEEN_KR','KR','common_stock'),('UNSEEN_US','US','common_stock'),('UNSEEN_ADS','US','ADS')]:
        p,v,r=fixture(ticker,country,kind);b,_=cap(p,v,r);a,_=cap(p,v,r,'ADJUDICATION',b)
        c=m.StageReviewOwner(b,a,enabled=True).issue()
        assert c['source_label']=='DATE_LABELED_EXISTING_CAPTURE' and not c['strict_Core']


def test_live_source_permission_revocation_invalidates_whole_result():
    p,v,r=fixture();b,_=cap(p,v,r);a,_=cap(p,v,r,'ADJUDICATION',b)
    owner=m.StageReviewOwner(b,a,enabled=True);owner.issue()
    r.revoke(p['base']['public_security']['canonical_security_id'],p['base']['evidence'][1]['source_sha'])
    with pytest.raises(ValueError):owner.issue()
