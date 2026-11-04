"""Synthetic output fixtures prove mechanics, never actual Astra acceptance."""
from contextlib import nullcontext
from copy import deepcopy
from types import SimpleNamespace
import time

import pytest

from app.services import vnext_unified_judgment as m
from app.services import vnext_balanced_stage_review as stage
from app.services.vnext_research_store import digest
from test_vnext_unified_judgment import fixture
from test_vnext_balanced_stage_review import MemoryController


def opinion(packet, overall='BUY', buyer='ATTRACTIVE', holder='HOLDABLE'):
    rows=[r for r in packet['admissibility'] if r['analytic_opinion_use']['eligible']]
    economic=[r['ref'] for r in rows if r['layer']=='ECONOMIC_OBSERVATION']
    valuation=[r['ref'] for r in rows if r['layer']=='VALUATION_CONTEXT']
    def axis(refs):
        return dict(refs=refs, counterevidence_refs=[], confidence='LOW',
            reasoning='An uncertain interpretation of the cited dated observations.',
            uncertainty='Durability and current conditions remain unresolved.',
            change_condition='Reassess when contrary evidence becomes available.')
    return dict(contract=m.AI_OWNED, policy_sha256=digest(m.OPINION_POLICY), input_digest=digest(packet),
        security_id=packet['base']['public_security']['canonical_security_id'],as_of=packet['base']['as_of'],
        action='NONE',authority='MODEL_INTERPRETATION',holder_basis='VIRTUAL',business='MIXED',
        claims=[dict(claim='The dated observation permits an uncertain interpretation.',
            assertion='ECONOMIC_INTERPRETATION',refs=[r['ref']],citations=deepcopy(r['opinion_observations']),
            counterevidence_refs=[],counterevidence_review='Other explanations remain possible within the limited source set.',
            limitations='No cause or recurrence is established.',confidence='LOW',independent_corroboration=False) for r in rows],
        overall=dict(axis(economic),stance=overall),newbuyer=dict(axis(economic),stance=buyer),
        holder_virtual=dict(axis(economic),stance=holder),
        valuation=dict(axis(valuation),judgment='NEUTRAL' if valuation else 'UNRESOLVED'),
        timing=dict(axis([]),state='UNRESOLVED'),technical_review=None,
        counterevidence_review='The available observations do not establish an absence of risk.',
        missing_evidence=['Current price and complete market review are unavailable.'],
        axis_differences='The business view and hypothetical entry or holding views have different purposes.',
        adjudication_changes='This synthetic fixture is not an actual model judgment.')


def setup(*identity):
    p,_,r=fixture(*identity);b=m.build_bundle(p,registry=r,contract=m.AI_OWNED)
    return p,b,opinion(b),r


def check(p,b,v,r):
    return m.validate_and_render(v,b,registry=r,economic_loader=lambda:deepcopy(p))


@pytest.mark.parametrize('labels',[('BUY','ATTRACTIVE','HOLDABLE'),('HOLD','WAIT','REVIEW'),
    ('SELL','AVOID','REDUCE'),('BUY','AVOID','REDUCE'),('SELL','ATTRACTIVE','HOLDABLE')])
def test_ai_labels_preserved_without_economic_recalculation(labels,monkeypatch):
    import app.services.new_buyer_v2_policy as b2
    def forbidden(*a,**kw):pytest.fail('deterministic stance path invoked')
    monkeypatch.setattr(m.prior,'choices',forbidden);monkeypatch.setattr(b2,'choices',forbidden)
    monkeypatch.setattr(m.prior_v2,'_overall',forbidden)
    monkeypatch.setattr(m,'directional_balance_ordinal_calibration_prompt',forbidden)
    p,b,v,r=setup();v=opinion(b,*labels);before=deepcopy(v)
    checked=check(p,b,v,r)
    assert checked['decision']['model_output']==v==before
    assert checked['decision']['newbuyer_fundamental']==labels[1]
    assert checked['decision']['decision_source']=='UNISSUED_MODEL_CANDIDATE'
    assert checked['decision']['model_receipt'] is None
    text=stage.prompt(b,'BLIND',knowledge={},registry=r,version=stage.UNIFIED_AI)
    assert 'ordinal calibration' not in text and 'ACCEPTED_BLIND' not in text


def test_missing_optional_valuation_does_not_veto_other_axes():
    p,b,v,r=setup();p['base']['evidence'][1]['data']['quality_valid']=False
    b=m.build_bundle(p,registry=r,contract=m.AI_OWNED);v=opinion(b,'SELL','AVOID','REDUCE')
    assert check(p,b,v,r)['decision']['model_output']['overall']['stance']=='SELL'
    assert v['valuation']['judgment']=='UNRESOLVED'


@pytest.mark.parametrize('change',['security','asof','digest','policy','wrong_ref','value','sha','period','basis',
    'independence','mechanism','recurrence','risk','current_price','numeric_prose','risk_absence','missing_citation',
    'owner_revoked','packet_tamper','forged_receipt'])
def test_narrow_objective_contract_rejections(change):
    p,b,v,r=setup();c=v['claims'][0]['citations'][0]
    if change=='security':v['security_id']='FOREIGN'
    if change=='asof':v['as_of']='2026-11-01'
    if change=='digest':v['input_digest']='forged'
    if change=='policy':v['policy_sha256']='forged'
    if change=='wrong_ref':v['overall']['refs']=['foreign']
    if change=='value':c['value']='123000000'
    if change=='sha':c['source_sha256']='forged'
    if change=='period':c['period_start']='2026-07-01'
    if change=='basis':c['statement_basis']='PARENT_ONLY'
    if change=='independence':v['claims'][0]['independent_corroboration']=True
    if change in ('mechanism','recurrence','risk'):
        v['claims'][0]['assertion']={'mechanism':'MECHANISM_ESTABLISHED','recurrence':'RECURRENCE_ESTABLISHED','risk':'STRUCTURAL_RISK_ESTABLISHED'}[change]
    if change=='current_price':v['newbuyer']['reasoning']='Buy now.'
    if change=='numeric_prose':v['claims'][0]['claim']='Cash flow was -100.'
    if change=='risk_absence':v['claims'][0]['claim']='No risks exist.'
    if change=='missing_citation':v['claims'][0]['citations']=[]
    if change=='owner_revoked':r.revoke(v['security_id'],p['base']['evidence'][0]['source_sha'])
    if change=='packet_tamper':b['admissibility'][0]['data']['fields']['current_value']=999
    if change=='forged_receipt':v['model_receipt']={'accepted':True}
    with pytest.raises(ValueError):check(p,b,v,r)


@pytest.mark.parametrize('key',['external_use_prohibited','provider_use_prohibited','legal_use_prohibited',
    'external_use_restrictions','provider_use_restrictions','legal_use_restrictions'])
def test_explicit_external_restrictions_never_revised(key):
    p,b,v,r=setup();p['base']['evidence'][0]['data'][key]=True
    b=m.build_bundle(p,registry=r,contract=m.AI_OWNED)
    assert b['admissibility'][0]['analytic_opinion_use']['eligible'] is False
    v['input_digest']=digest(b)
    with pytest.raises(ValueError):check(p,b,v,r)


def test_unknown_direction_denial_not_blanket_overridden():
    p,b,v,r=setup();p['base']['evidence'][0]['data']['direction_allowed']=False
    b=m.build_bundle(p,registry=r,contract=m.AI_OWNED)
    assert not b['admissibility'][0]['analytic_opinion_use']['eligible']


def test_original_amount_policy_requires_original_replay_provenance():
    p,b,v,r=setup();e=p['base']['evidence'][0]
    e['data'].update(direction_allowed=False,interpretation_eligible=False,
        quality_contract=m.OPINION_POLICY['internal_amount_quality_contract'])
    e['data']['fields']['observation_only']=True
    e['provenance']={'provider':'FinancialAmountReplay'}
    b=m.build_bundle(p,registry=r,contract=m.AI_OWNED)
    assert b['admissibility'][0]['analytic_opinion_use']['eligible']
    e['provenance']={'provider':'CallerJSON'}
    b=m.build_bundle(p,registry=r,contract=m.AI_OWNED)
    assert not b['admissibility'][0]['analytic_opinion_use']['eligible']


@pytest.mark.parametrize('identity',[('NEW_KR','KR','common_stock'),('NEW_US','US','common_stock'),
    ('NEW_ADS','US','ADS'),('NEW_BANK','KR','financial'),('NEW_CYCLE','US','cyclical')])
def test_unseen_identities_use_equivalent_fact_contract(identity):
    p,b,v,r=setup(*identity)
    assert check(p,b,v,r)['decision']['model_output']==v
    assert stage.output_schema(b,stage.UNIFIED_AI)['properties']['security_id']['const']==v['security_id']


def test_blind_cannot_receive_old_labels_or_version_mixture():
    p,b,v,r=setup()
    with pytest.raises(ValueError,match='source_only_blind'):
        stage.prompt(b,'BLIND',knowledge={'previous':'BUY'},registry=r,version=stage.UNIFIED_AI)
    with pytest.raises(ValueError,match='VERSION_MISMATCH_PRECALL'):
        stage.prompt(b,'BLIND',knowledge={},registry=r,version=stage.UNIFIED)
    with pytest.raises(ValueError,match='VERSION_MISMATCH_PRECALL'):
        m.prompt(b,'ADJUDICATION',knowledge={},registry=r,version=m.AI_OWNED,prior={'contract':m.CONTRACT})


def synthetic_stages(p,b,v,r,controller=None):
    c=controller or MemoryController();caps=[]
    for name in ('BLIND','ADJUDICATION'):
        previous=caps[0] if caps else None
        def invoke(request,text,deadline):
            now=time.time()
            execution=dict(stage=name,status='VALIDATED',exit=0,attempt=1,retry=0,
                runtime=dict(verified=True,session='SYNTHETIC_NOT_ASTRA_'+name),model='gpt-6-astra',effort='xhigh',
                packet_sha=digest(b),prompt_sha=digest(text.encode()),schema_sha=digest(stage.output_schema(b,stage.UNIFIED_AI)),
                output_sha=digest(v),started=now,ended=now,deadline=deadline,
                stage_contract=stage.execution_contract(stage.UNIFIED_AI),prompt_version=stage.UNIFIED_AI,
                invocation_id=request['invocation_id'],request_sha=digest(request),approved_request_sha=digest(request))
            return dict(execution=execution,output=deepcopy(v),validation=check(p,b,v,r))
        caps.append(c.run_stage(invocation_id='SYNTHETIC_AI_OWNED',account='TEST',packet=b,stage=name,
            version=stage.UNIFIED_AI,knowledge={},registry=r,source_loader=lambda:deepcopy(b),
            approval=lambda _:True,account_lease=nullcontext,invoke=invoke,prior=previous,economic_loader=lambda:deepcopy(p)))
    return c,stage.StageReviewOwner(*caps,enabled=True)


def test_original_stages_dispatch_modes_and_revocation(monkeypatch):
    from app.services.vnext_unified_dispatch import consume
    p,b,v,r=setup();c,owner=synthetic_stages(p,b,v,r)
    c.config=SimpleNamespace(environment='test',mode='write')
    context=dict(observed_as_of=b['base']['as_of'],completed_market_session=None,
        freshness_by_source={},required_market_fields={'state':'NOT_CHECKED'},current_price_denials=['DATED_ONLY'],source_revisions={})
    a=consume(c,packet=b,owner=owner,mode='DATED_REPLAY',output_context=context,enabled=True)
    z=consume(c,packet=b,owner=owner,mode='DAILY_NO_SEND',output_context=context,enabled=True)
    assert a['decision_sha256']==z['decision_sha256'] and z['reused']
    assert a['decision']['decision_source']=='ASTRA_ADJ' and a['decision']['model_output']==v
    assert 'SYNTHETIC_NOT_ASTRA' in a['decision']['model_receipt']['adjudication_execution']['runtime']['session']
    owner.revoke()
    with pytest.raises(ValueError):consume(c,packet=b,owner=owner,mode='DATED_REPLAY',output_context=context,enabled=True)


def test_v1_blind_cannot_feed_v2_adj_before_approval():
    from test_vnext_balanced_stage_review import cap
    from test_vnext_balanced_research import fixture as legacy
    p,v,r=legacy();old,_=cap(p,v,r)
    p,b,v,r=setup()
    with pytest.raises(ValueError,match='VERSION_MISMATCH_PRECALL'):
        MemoryController().run_stage(invocation_id='CROSS',account='TEST',packet=b,stage='ADJUDICATION',
            version=stage.UNIFIED_AI,knowledge={},registry=r,source_loader=lambda:b,
            approval=lambda _:pytest.fail('approval reached'),account_lease=nullcontext,
            invoke=lambda *_:pytest.fail('invoked'),prior=old)


from test_vnext_stage_fork_handoff import Harness as OriginalHarness


class OpinionHarness(OriginalHarness):
    def __init__(self,monkeypatch,path,create=True):
        super().__init__(monkeypatch,path,create=create)
        for e in self.economic['base']['evidence']:
            if e['field'].startswith('financial.'):
                e['data']['interpretation_eligible']=True
        self.version=stage.UNIFIED_AI
        self.packet=self.source();self.value=opinion(self.packet)
        self.identity['frozen_input_sha256']=digest(self.packet)

    def source(self):
        return m.build_bundle(self.economic,registry=self.registry,timing_owner=self.o,
            cutoff=self.economic['base']['as_of'],contract=m.AI_OWNED)

    def invoke(self,req,text,deadline,bad=False):
        import os
        assert os.getpid()!=self.parent_pid
        checked=m.validate_and_render(self.value,self.packet,registry=self.registry,timing_owner=self.o,
            economic_loader=lambda:self.economic)
        now=time.time()
        execution=dict(stage=req['stage'],status='VALIDATED',exit=0,attempt=1,retry=0,
            runtime=dict(verified=True,session='SYNTHETIC_NOT_ASTRA_'+req['stage']),
            model='gpt-6-astra',effort='xhigh',packet_sha=digest(self.packet),prompt_sha=digest(text.encode()),
            schema_sha=digest(stage.output_schema(self.packet,self.version)),output_sha=digest(self.value),
            started=now,ended=now,deadline=deadline,stage_contract=stage.execution_contract(self.version),
            prompt_version=self.version,invocation_id=req['invocation_id'],request_sha=digest(req),approved_request_sha=digest(req))
        return dict(output=deepcopy(self.value),validation=checked,execution=execution)

    def consume(self,b,a,mode):
        from app.services.vnext_unified_dispatch import consume
        blind=self.restore(*b);adj=self.restore(*a,name='ADJUDICATION',prior=blind)
        owner=stage.StageReviewOwner(blind,adj,enabled=True)
        context=dict(observed_as_of=self.packet['base']['as_of'],completed_market_session=None,
            freshness_by_source={},required_market_fields={'state':'NOT_CHECKED'},current_price_denials=['DATED_ONLY'],source_revisions={})
        return consume(self.ctrl,packet=self.packet,owner=owner,mode=mode,output_context=context,enabled=True)


def cold_opinion(path,metadata):
    import json,os
    from pathlib import Path
    data=json.loads(Path(metadata).read_text())
    h=OpinionHarness(pytest.MonkeyPatch(),Path(path),create=False)
    value=h.consume(data['BLIND'],data['ADJUDICATION'],'DAILY_NO_SEND')
    assert os.getpid()!=data['pid'] and value['decision_sha256']==data['decision_sha256'] and value['reused']
    print(json.dumps(dict(pid=os.getpid(),decision_sha256=value['decision_sha256'],synthetic=True,models=0)))


def test_v2_real_fork_parent_restore_and_fresh_process_no_send(monkeypatch,tmp_path):
    import json,os,subprocess,sys
    h=OpinionHarness(monkeypatch,tmp_path/'research.sqlite3')
    b=h.run();assert b[1]['state']=='COMPLETED_NO_SEND'
    blind=h.restore(*b)
    a=h.run('ADJUDICATION',blind);assert a[1]['state']=='COMPLETED_NO_SEND'
    v=h.consume(b,a,'DATED_REPLAY');z=h.consume(b,a,'DAILY_NO_SEND')
    assert v['decision_sha256']==z['decision_sha256'] and z['reused']
    metadata=tmp_path/'cold-opinion.json'
    metadata.write_text(json.dumps(dict(BLIND=b,ADJUDICATION=a,pid=os.getpid(),decision_sha256=v['decision_sha256'])))
    before=h.config.path.read_bytes()
    guard='from gate_a_guard import install; install();' if os.getenv('GATE_A_TEST_ROOT') else ''
    command=guard+'from test_vnext_ai_owned_judgment import cold_opinion; import sys; cold_opinion(*sys.argv[1:])'
    proc=subprocess.run([sys.executable,'-B','-c',command,str(h.config.path),str(metadata)],capture_output=True,text=True,timeout=60)
    assert proc.returncode==0,proc.stderr
    assert json.loads(proc.stdout)['decision_sha256']==v['decision_sha256']
    assert h.config.path.read_bytes()==before
    (tmp_path/'two-mode-proof.json').write_text(json.dumps(dict(
        synthetic=True,actual_models=0,parent_pid=os.getpid(),cold=json.loads(proc.stdout),
        dated_decision_sha256=v['decision_sha256'],daily_decision_sha256=z['decision_sha256'],
        accepted_output_unchanged=v['decision']['model_output']==h.value,
        existing_journal_read_only_in_cold_process=True)))
