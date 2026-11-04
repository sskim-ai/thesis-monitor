"""V3 uses synthetic candidates; never reissues a failed real V2 output."""
from contextlib import nullcontext
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.services import vnext_unified_judgment as m
from app.services import vnext_balanced_stage_review as stage
from app.services.vnext_research_store import digest
from test_vnext_ai_owned_judgment import opinion, OpinionHarness, synthetic_stages, setup as v2_setup
from test_vnext_dated_research_timing import setup as timing_setup
from test_vnext_balanced_stage_review import MemoryController


def candidate(packet, review, labels=('BUY','ATTRACTIVE','HOLDABLE')):
    value=opinion(packet,*labels)
    value.update(contract=m.AI_OWNED_V3,policy_sha256=digest(m.opinion_policy(m.AI_OWNED_V3)))
    value['technical_review']=deepcopy(review)
    value['technical_review']['contract']=m.CONTRACT
    citations=review['citations']
    for name in ('overall','newbuyer','holder_virtual'):
        value[name]['refs']=[*value[name]['refs'],citations[0]['ref']]
        value[name]['counterevidence_refs']=[citations[1]['ref']]
    value['timing'].update(state='CAUTIOUS',refs=[c['ref'] for c in citations],
        counterevidence_refs=[citations[-1]['ref']])
    return value


def setup(monkeypatch,code='UNSEEN',market='US',clock=lambda:0):
    owner,economic,registry,_,review=timing_setup(monkeypatch,code,market,clock=clock)
    for e in economic['base']['evidence']:
        if e['field'].startswith('financial.'):
            e['data']['interpretation_eligible']=True
    packet=m.build_bundle(economic,registry=registry,timing_owner=owner,
        cutoff=economic['base']['as_of'],contract=m.AI_OWNED_V3)
    return owner,economic,registry,packet,candidate(packet,review)


def check(args):
    owner,economic,registry,packet,value=args
    return m.validate_and_render(value,packet,registry=registry,timing_owner=owner,economic_loader=lambda:economic)


@pytest.mark.parametrize('labels',[('BUY','ATTRACTIVE','HOLDABLE'),('HOLD','WAIT','REVIEW'),
    ('SELL','AVOID','REDUCE'),('BUY','AVOID','REDUCE'),('SELL','ATTRACTIVE','HOLDABLE')])
def test_v3_labels_unchanged_with_cross_axis_exact_roles(monkeypatch,labels):
    a=setup(monkeypatch)
    def forbidden(*args,**kwargs):pytest.fail('deterministic judgment invoked')
    monkeypatch.setattr(m.prior,'choices',forbidden)
    monkeypatch.setattr(m.prior_v2,'_overall',forbidden)
    a[-1]['overall']['stance'],a[-1]['newbuyer']['stance'],a[-1]['holder_virtual']['stance']=labels
    before=deepcopy(a[-1]);result=check(a)['decision']
    assert result['model_output']==before and result['decision_source']=='UNISSUED_MODEL_CANDIDATE'
    assert result['policy_sha256']==a[3]['policy_sha256'] and not result['strict_ready'] and not result['send']
    roles=result['axis_evidence']['axes']
    for name in ('overall','newbuyer','holder_virtual'):
        assert roles[name]['refs'][-1]['role']=='DATED_TECHNICAL_CONTEXT'
        assert roles[name]['counterevidence_refs'][0]['role']=='DATED_TECHNICAL_CONTEXT'
    assert all(r['role']=='DATED_TECHNICAL_TIMING' for r in roles['timing']['refs'])


@pytest.mark.parametrize('code,market',[('NEW_KR','KR'),('NEW_US','US'),('NEW_ADS','US'),
    ('NEW_FINANCIAL','KR'),('NEW_CYCLICAL','US')])
def test_unseen_identity_equivalent_roles(monkeypatch,code,market):
    a=setup(monkeypatch,code,market)
    assert check(a)['decision']['axis_evidence']['security_id']==a[-1]['security_id']


def test_policy_prompt_schema_resolver_single_source(monkeypatch):
    a=setup(monkeypatch);packet=a[3]
    text=stage.prompt(packet,'BLIND',knowledge={},registry=a[2],version=stage.UNIFIED_AI_V3)
    schema=stage.output_schema(packet,stage.UNIFIED_AI_V3)
    assert schema['properties']['contract']['const']==m.AI_OWNED_V3
    assert schema['properties']['policy_sha256']['const']==packet['policy_sha256']
    assert packet['opinion_policy']['axis_evidence_role_policy']==m.AXIS_EVIDENCE_ROLE_POLICY
    for name in m.AXIS_EVIDENCE_ROLE_POLICY['axes']:
        rule=m._axis_role_guidance(name)
        assert rule in text and rule in schema['properties'][name]['description']
    assert check(a)['decision']['axis_evidence']['policy_sha256']==digest(m.AXIS_EVIDENCE_ROLE_POLICY)
    assert 'ACCEPTED_BLIND' not in text and len(text.encode())<384*1024


@pytest.mark.parametrize('field',['refs','counterevidence_refs'])
@pytest.mark.parametrize('change',['unknown','prefix_only','fact_not_submitted','economic_claim_missing',
    'technical_in_valuation','economic_in_timing'])
def test_primary_and_counter_ref_rejections(monkeypatch,field,change):
    a=setup(monkeypatch);p=a[3];v=a[-1];ref=v['technical_review']['citations'][0]['ref'];name='overall'
    if change=='unknown':ref='foreign-owner-ref'
    elif change=='prefix_only':ref='dated-'+('0'*32)
    elif change=='fact_not_submitted':
        cited={c['ref'] for c in v['technical_review']['citations']}
        ref=next(f['ref'] for f in p['technical']['technical']['facts'] if f['ref'] not in cited)
    elif change=='economic_claim_missing':
        ref=v['claims'][0]['refs'][0];v['claims']=v['claims'][1:]
    elif change=='technical_in_valuation':name='valuation'
    elif change=='economic_in_timing':name='timing';ref=v['claims'][0]['refs'][0]
    v[name][field]=[ref]
    with pytest.raises(ValueError):check(a)


@pytest.mark.parametrize('axis',['overall','newbuyer','holder_virtual'])
def test_technical_only_economic_stance_denied_but_not_issued_allowed(monkeypatch,axis):
    a=setup(monkeypatch);a[-1][axis]['refs']=[a[-1]['technical_review']['citations'][0]['ref']]
    with pytest.raises(ValueError,match='economic_anchor_missing'):check(a)
    a[-1][axis]['stance']='NOT_ISSUED'
    assert check(a)['decision']['model_output'][axis]['stance']=='NOT_ISSUED'


def test_technical_does_not_issue_business_or_optional_valuation(monkeypatch):
    a=setup(monkeypatch);v=a[-1]
    v['claims']=[]
    for name in ('overall','newbuyer','holder_virtual'):
        v[name].update(stance='NOT_ISSUED',refs=[v['technical_review']['citations'][0]['ref']])
    v['valuation'].update(judgment='UNRESOLVED',refs=[])
    with pytest.raises(ValueError,match='business_economic_anchor'):check(a)
    v['business']='INSUFFICIENT'
    assert check(a)['decision']['model_output']['timing']['state']=='CAUTIOUS'


@pytest.mark.parametrize('mutation',['value','unit','formula','source_sha256','period_end','timeframe',
    'security','lookahead','revoked','parent_revoked','expired','owner_json','no_review',
    'technical_claim','technical_risk','external_denial','current_price','strict','send','order'])
def test_original_owner_and_use_boundaries(monkeypatch,mutation):
    now=[0];a=list(setup(monkeypatch,clock=lambda:now[0]));o,e,r,p,v=a
    c=v['technical_review']['citations'][0]
    if mutation in ('value','unit','formula','source_sha256','period_end'):
        c[mutation]=['wrong'] if mutation=='source_sha256' else 'wrong'
    elif mutation=='timeframe':c['timeframe']='monthly'
    elif mutation=='security':v['technical_review']['security_id']='another'
    elif mutation=='lookahead':p['technical']['technical']['cutoff']='1900-01-01'
    elif mutation=='revoked':o.revoke()
    elif mutation=='parent_revoked':o.parent.revoke()
    elif mutation=='expired':now[0]=1801
    elif mutation=='owner_json':a[0]=deepcopy(p['technical'])
    elif mutation=='no_review':v['technical_review']=None
    elif mutation in ('technical_claim','technical_risk'):
        v['claims'][0]['refs']=[c['ref']]
        if mutation=='technical_risk':v['claims'][0]['assertion']='STRUCTURAL_RISK_ESTABLISHED'
    elif mutation=='external_denial':e['base']['evidence'][0]['data']['external_use_prohibited']=True
    elif mutation=='current_price':v['overall']['reasoning']='Buy now.'
    elif mutation=='strict':v['strict_ready']=True
    elif mutation=='send':v['send']=True
    elif mutation=='order':v['action']='BUY'
    with pytest.raises(ValueError):check(a)


@pytest.mark.parametrize('mutation',['packet_version','policy_sha','policy_body','prior_version','prior_policy',
    'prior_security','prior_digest','prior_asof'])
def test_precall_version_policy_source_rejections(monkeypatch,mutation):
    a=setup(monkeypatch);p=deepcopy(a[3]);prior=deepcopy(a[-1]);name='ADJUDICATION'
    if mutation=='packet_version':p['contract']=m.AI_OWNED
    elif mutation=='policy_sha':p['policy_sha256']='wrong'
    elif mutation=='policy_body':p['opinion_policy']['axis_evidence_role_policy']['axes']['timing']['roles']=[]
    else:prior[{'prior_version':'contract','prior_policy':'policy_sha256','prior_security':'security_id',
        'prior_digest':'input_digest','prior_asof':'as_of'}[mutation]]='wrong'
    with pytest.raises(ValueError):stage.prompt(p,name,knowledge={},registry=a[2],version=stage.UNIFIED_AI_V3,prior=prior)


def test_v2_capability_cannot_enter_v3_before_approval(monkeypatch):
    p,b,v,r=v2_setup();_,old=synthetic_stages(p,b,v,r)
    a=setup(monkeypatch)
    with pytest.raises(ValueError,match='VERSION_MISMATCH_PRECALL'):
        MemoryController().run_stage(invocation_id='MIXED',account='TEST',packet=a[3],stage='ADJUDICATION',
            version=stage.UNIFIED_AI_V3,knowledge={},registry=a[2],source_loader=lambda:a[3],
            approval=lambda _:pytest.fail('approval reached'),account_lease=nullcontext,
            invoke=lambda *_:pytest.fail('model reached'),prior=old.blind)


class AxisHarness(OpinionHarness):
    def __init__(self,monkeypatch,path,create=True):
        super().__init__(monkeypatch,path,create=create)
        _,_,_,_,review=timing_setup(monkeypatch)
        self.version=stage.UNIFIED_AI_V3
        self.packet=self.source();self.value=candidate(self.packet,review)
        self.identity['frozen_input_sha256']=digest(self.packet)

    def source(self):
        return m.build_bundle(self.economic,registry=self.registry,timing_owner=self.o,
            cutoff=self.economic['base']['as_of'],contract=m.AI_OWNED_V3)


def cold_axis(path,metadata):
    data=json.loads(Path(metadata).read_text());h=AxisHarness(pytest.MonkeyPatch(),Path(path),create=False)
    value=h.consume(data['BLIND'],data['ADJUDICATION'],'DAILY_NO_SEND')
    assert os.getpid()!=data['pid'] and value['decision_sha256']==data['decision_sha256'] and value['reused']
    print(json.dumps(dict(pid=os.getpid(),decision_sha256=value['decision_sha256'],synthetic=True,models=0)))


def test_v3_real_fork_restore_cold_both_modes_and_owner_revocation(monkeypatch,tmp_path):
    h=AxisHarness(monkeypatch,tmp_path/'research.sqlite3')
    b=h.run();assert b[1]['state']=='COMPLETED_NO_SEND'
    blind=h.restore(*b);a=h.run('ADJUDICATION',blind);assert a[1]['state']=='COMPLETED_NO_SEND'
    v=h.consume(b,a,'DATED_REPLAY');z=h.consume(b,a,'DAILY_NO_SEND')
    assert v['decision_sha256']==z['decision_sha256'] and z['reused']
    assert v['decision']['model_output']==h.value and v['decision']['contract']==m.AI_OWNED_V3
    from app.services.vnext_unified_dispatch import consume
    restored_blind=h.restore(*b)
    owner=stage.StageReviewOwner(restored_blind,h.restore(*a,name='ADJUDICATION',prior=restored_blind),enabled=True)
    with pytest.raises(ValueError):consume(h.ctrl,packet=h.packet,owner=owner,mode='DATED_REPLAY',output_context={})
    metadata=tmp_path/'cold-axis.json'
    metadata.write_text(json.dumps(dict(BLIND=b,ADJUDICATION=a,pid=os.getpid(),decision_sha256=v['decision_sha256'])))
    before=h.config.path.read_bytes()
    guard='from gate_a_guard import install; install();' if os.getenv('GATE_A_TEST_ROOT') else ''
    proc=subprocess.run([sys.executable,'-B','-c',guard+
        'from test_vnext_axis_evidence_roles import cold_axis; import sys; cold_axis(*sys.argv[1:])',
        str(h.config.path),str(metadata)],capture_output=True,text=True,timeout=60)
    assert proc.returncode==0,proc.stderr
    assert h.config.path.read_bytes()==before
    (tmp_path/'v3-two-mode-proof.json').write_text(json.dumps(dict(synthetic=True,actual_models=0,
        parent_pid=os.getpid(),cold=json.loads(proc.stdout),dated_decision_sha256=v['decision_sha256'],
        daily_decision_sha256=z['decision_sha256'],accepted_output_unchanged=True,
        existing_journal_read_only_in_cold_process=True)))
    h.o.revoke()
    with pytest.raises(ValueError):h.consume(b,a,'DAILY_NO_SEND')


def test_v3_accepted_prior_mismatch_prevents_new_model(monkeypatch,tmp_path):
    h=AxisHarness(monkeypatch,tmp_path/'research.sqlite3')
    b=h.run();assert b[1]['state']=='COMPLETED_NO_SEND'
    for field in ('schema_sha','prompt_sha','packet_sha','request_sha','approved_request_sha'):
        prior=h.restore(*b);data=deepcopy(prior.reader());data['execution'][field]='forged'
        prior.reader=lambda data=data:deepcopy(data)
        kw=h.args('ADJUDICATION',prior)
        kw['approval']=lambda _:pytest.fail('approval reached')
        with pytest.raises(ValueError):h.ctrl.run_stage(**kw,invoke=lambda *_:pytest.fail('model reached'))
    h.now[0]=1801
    with pytest.raises(ValueError):h.restore(*b)


def test_v3_economic_only_and_optional_valuation_preserved():
    p,_,_,r=v2_setup()
    p['base']['evidence'][1]['data']['quality_valid']=False
    b=m.build_bundle(p,registry=r,contract=m.AI_OWNED_V3)
    v=opinion(b,'SELL','AVOID','REDUCE')
    v.update(contract=m.AI_OWNED_V3,policy_sha256=b['policy_sha256'])
    assert v['technical_review'] is None and v['valuation']['judgment']=='UNRESOLVED'
    checked=m.validate_and_render(v,b,registry=r,economic_loader=lambda:p)
    assert checked['decision']['model_output']==v
