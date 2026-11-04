from copy import deepcopy
import pytest

from app.services import vnext_balanced_research as m
from app.services import vnext_optional_fy1_research as original
from app.services.vnext_codex_research import numeric_catalog
from app.services.vnext_daily_research import UseRegistry, compact_message
from app.services.vnext_research_store import digest


def fixture(ticker='UNSEEN', country='US', security_type='common_stock'):
    at='2026-10-29T12:00:00+00:00'
    sec=dict(ticker=ticker,canonical_security_id=country+':'+ticker,
             canonical_company_id='ISSUER:'+ticker,country=country,security_type=security_type)
    def evidence(ref,field,data):
        return dict(ref=ref,field=field,data=data,status='CURRENT_VALID',allowed_use=m.USE,
            source_sha=digest(ref),original_run='synthetic-only',reviewed_at=at,
            freshness='CURRENT_VALIDATED_FOR_REQUEST',scope=[],direction_allowed=False,
            provenance=dict(original_receipt_sha256=digest('receipt:'+ref)))
    financial=dict(fields=dict(issuer_id=sec['canonical_company_id'],source_receipt='synthetic',
        statement_basis='CONSOLIDATED',period_type='QUARTER',period_start='2026-04-01',
        period_end='2026-06-30',currency='USD',current_value=100.0,delta=10.0,growth_pct=11.0,
        prior_comparable_value=90.0,prior_period_start='2025-04-01',prior_period_end='2025-06-30'))
    sec['exchange']='NASDAQ' if country=='US' else 'KRX'
    base=dict(case=ticker,ticker=ticker,run_id='synthetic-only',as_of=at,public_security=sec,send=False,strict_ready=False,
        holdings_included=False,user_thesis_included=False,missing=[],evidence=[
        evidence('business','financial.revenue',financial),
        evidence('valuation','valuation.PBR',dict(value=2.0,display_eligible=True,metric_semantic='PBR',retrieval_timestamp=at)),
        evidence('price','completed_close',dict(row=dict(close=12.0),currency='USD',calendar=dict(session='2026-10-28')))])
    base['numeric_catalog']=numeric_catalog(base)
    packet=original.attach(base)
    driver=dict(claim='Supported operating observation.',refs=['business'],
        lineage_groups=[m.v3.evidence_contract(base)['business']['lineage_group']],
        mechanism='Mechanism remains qualified and bounded.',importance='MATERIAL',limitations='Durability unresolved.')
    value=dict(contract=m.CONTRACT,disposition='INSUFFICIENT_EVIDENCE',decision=None,balance=None,
        **{k:'Bounded public research.' for k in ('summary','valuation_expectations','provisional_business_signal','entry_timing_view',
            'counterevidence','thesis_invalidation','uncertainty','missing_next_fact','review_changes')},
        economic_drivers_positive=[driver],economic_drivers_negative=[],timing_support=[],timing_risks=[],numeric_fact_refs=[],
        newbuyer={k:'Observe evidence before action.' for k in m.v3.NewBuyer.model_fields},
        holder={k:'Hypothetical holder perspective.' for k in m.v3.Holder.model_fields},
        decision_scope='PROVISIONAL_RESEARCH_NOT_CORE',economic_evidence_signal='LIMITED_POSITIVE',
        valuation_judgment='UNPROVEN',valuation_evidence_refs=['valuation'],market_or_price_timing='UNKNOWN',
        newbuyer_stance='CONDITIONAL_INTEREST',holder_stance='THESIS_HOLD_CONDITIONAL',holdings_included=False,
        user_thesis_included=False,counter_hypothesis_refs=[],counter_hypothesis_outcome='UNRESOLVED')
    def axis(refs):
        return dict(reasoning='Supported bounded interpretation.',refs=refs,
                    change_condition='Reassess when the supporting evidence changes.',confidence='NOT_SEPARATELY_ISSUED')
    value['balanced']=dict(business_positive_refs=['business'],business_negative_refs=[],business_quality_denials=[],
        active_material_risk_refs=[],active_material_risk_reason='',confidence_veto_refs=[],
        valuation=dict(axis(['valuation']),judgment='SUPPORTIVE'),
        overall=dict(axis([]),stance='NOT_ISSUED',balance=None),
        holder_virtual=dict(axis(['business']),stance='HOLDABLE'),
        timing=dict(axis(['price']),state='WAIT_FOR_ZONE'),newbuyer_confidence='NOT_SEPARATELY_ISSUED',
        newbuyer_change_condition='Reassess business quality and relative valuation.')
    return packet,value,UseRegistry()


def check(p,v,r):return m.validate_and_render(v,p,registry=r)


def record(p,v,r):
    stages={}
    for name in ('BLIND','ADJUDICATION'):
        text=m.prompt(p,name,knowledge={},registry=r,prior=None if name=='BLIND' else v)
        e=dict(status='VALIDATED',exit=0,runtime=dict(verified=True,session='SYNTHETIC_'+name),
            model='gpt-6-astra',effort='xhigh',packet_sha=digest(p),output_sha=digest(v),
            schema_sha=digest(m.schema()),prompt_sha=digest(text.encode()))
        stages[name]=dict(output=deepcopy(v),validation=check(p,v,r),execution=e)
    return dict(packet=deepcopy(p),stages=stages)


def test_positive_capability_timing_and_independent_axes():
    p,v,r=fixture();c=check(p,v,r);b=c['balanced']
    assert b['newbuyer_fundamental']=='ATTRACTIVE'
    assert b['timing']['state']=='WAIT_FOR_ZONE'
    assert b['overall']['stance']=='NOT_ISSUED' and b['holder_virtual']['stance']=='HOLDABLE'
    assert c['rendered']['decision'] is None and c['rendered']['valuation_judgment']=='UNPROVEN'
    assert not b['strict_B2'] and not b['send']


def negative(v):
    v['economic_drivers_negative']=deepcopy(v['economic_drivers_positive'])
    v['balanced']['business_negative_refs']=['business']
    v['economic_evidence_signal']='MIXED'


def test_current_material_risk_not_overridden_by_chart():
    p,v,r=fixture();negative(v)
    v['balanced']['active_material_risk_refs']=['business']
    v['balanced']['active_material_risk_reason']='Current structural business impairment supported.'
    v['balanced']['timing']['state']='FAVORABLE_NOW'
    c=check(p,v,r)['balanced']
    assert c['newbuyer_fundamental']=='AVOID' and c['holder_virtual']['stance']=='HOLDABLE'


def test_mixed_business_not_forced_positive():
    p,v,r=fixture();negative(v)
    c=check(p,v,r)['balanced']
    assert (c['newbuyer_fundamental'],c['newbuyer_reason'])==('WAIT','BUSINESS_MIXED')


@pytest.mark.parametrize('judgment,expected',[('SUPPORTIVE','ATTRACTIVE'),('NEUTRAL','WAIT'),('BURDENSOME','WAIT'),('NOT_ISSUED','NOT_ISSUED')])
def test_model_valuation_not_numeric_formula(judgment,expected):
    p,v,r=fixture();v['balanced']['valuation']['judgment']=judgment
    assert check(p,v,r)['balanced']['newbuyer_fundamental']==expected


def test_all_valuation_denied_and_optional_metric_independence():
    p,v,r=fixture()
    e=p['base']['evidence'][1];r.revoke(p['base']['public_security']['canonical_security_id'],e['source_sha'])
    v['balanced']['valuation'].update(judgment='NOT_ISSUED',refs=[])
    c=check(p,v,r)['balanced']
    assert (c['newbuyer_fundamental'],c['newbuyer_reason'])==('WAIT','VALUATION_UNRESOLVED')
    r=UseRegistry();r.revoke(p['base']['public_security']['canonical_security_id'],digest('missing_optional_PER'))
    v['balanced']['valuation'].update(judgment='SUPPORTIVE',refs=['valuation'])
    assert check(p,v,r)['balanced']['newbuyer_fundamental']=='ATTRACTIVE'


@pytest.mark.parametrize('required',[False,True])
def test_quality_denial_claim_scoped_not_issuer_global(required):
    p,v,r=fixture();base=deepcopy(p['base'])
    e=deepcopy(base['evidence'][0]);e.update(ref='denied',field='financial.operating_income',status='POLICY_DENIED')
    base['evidence'].append(e);p=original.attach(base)
    if required:v['balanced']['business_quality_denials']=['denied']
    c=check(p,v,r)['balanced']
    assert c['newbuyer_fundamental']==('WAIT' if required else 'ATTRACTIVE')


@pytest.mark.parametrize('country,kind,ticker',[('KR','common_stock','UNSEEN_KR'),('US','common_stock','UNSEEN_US'),('US','ADS','UNSEEN_ADS'),('KR','financial','UNSEEN_FIN'),('US','cyclical','UNSEEN_CYCLE')])
def test_unseen_identity_generality(country,kind,ticker):
    p,v,r=fixture(ticker,country,kind)
    assert check(p,v,r)['balanced']['newbuyer_fundamental']=='ATTRACTIVE'


@pytest.mark.parametrize('change', ['direction','private','display_ref','wrong_layer','invented_veto','invented_denial','unbound_number','overall_auto_buy','holder_auto_reduce','timing_without_ref'])
def test_semantic_use_rejections(change):
    p,v,r=fixture();b=v['balanced']
    if change=='direction':v['decision']='BUY'
    if change=='private':v['holdings_included']=True
    if change=='display_ref':b['valuation']['refs']=['h_supplemental_display']
    if change=='wrong_layer':b['valuation']['refs']=['price']
    if change=='invented_veto':b['confidence_veto_refs']=['business']
    if change=='invented_denial':b['business_quality_denials']=['business']
    if change=='unbound_number':b['valuation']['reasoning']='Price target is 300.'
    if change=='overall_auto_buy':b['overall'].update(stance='BUY',refs=['business'],balance=dict(buy=7.0,sell=3.0))
    if change=='holder_auto_reduce':b['holder_virtual']['stance']='REDUCE'
    if change=='timing_without_ref':b['timing']['refs']=[]
    with pytest.raises(ValueError):check(p,v,r)


@pytest.mark.parametrize('freshness,importance',[('LAST_QUALIFIED_HISTORICAL','MATERIAL'),('CURRENT_VALIDATED_FOR_REQUEST','LIMITED')])
def test_no_historical_or_immaterial_active_risk(freshness,importance):
    p,v,r=fixture();base=deepcopy(p['base']);base['evidence'][0]['freshness']=freshness;p=original.attach(base)
    negative(v);v['economic_drivers_negative'][0]['importance']=importance
    v['balanced'].update(active_material_risk_refs=['business'],active_material_risk_reason='Structural risk.')
    with pytest.raises(ValueError):check(p,v,r)


def test_backend_owner_default_off_registry_revocation_and_idempotence():
    p,v,r=fixture();rec=record(p,v,r)
    kwargs=dict(source_loader=lambda:deepcopy(p),registry=r,knowledge={})
    off=m.BalancedReviewOwner(lambda:deepcopy(rec),**kwargs)
    with pytest.raises(ValueError,match='default_off'):off.issue()
    owner=m.BalancedReviewOwner(lambda:deepcopy(rec),enabled=True,**kwargs)
    receipt=owner.issue();assert owner.issue() is receipt
    assert owner.consume(receipt,packet=p)['balanced']['newbuyer_fundamental']=='ATTRACTIVE'
    with pytest.raises(ValueError):owner.consume(dict(receipt),packet=p)
    other=m.BalancedReviewOwner(lambda:deepcopy(rec),enabled=True,**kwargs);other.issue()
    with pytest.raises(ValueError):other.consume(receipt,packet=p)
    r.revoke(p['base']['public_security']['canonical_security_id'],p['base']['evidence'][0]['source_sha'])
    with pytest.raises(ValueError):owner.consume(receipt,packet=p)


@pytest.mark.parametrize('field',['packet_sha','output_sha','prompt_sha','schema_sha','model','effort','exit','session','cold_security','cold_period','revoked'])
def test_execution_and_cold_binding(field):
    p,v,r=fixture();rec=record(p,v,r);cold=deepcopy(p)
    if field.startswith('cold_'):
        if field=='cold_security':cold['base']['public_security']['canonical_security_id']='wrong'
        else:cold['base']['evidence'][0]['data']['fields']['period_end']='2025-06-30'
    elif field!='revoked':
        e=rec['stages']['ADJUDICATION']['execution']
        if field=='session':e['runtime']['session']=rec['stages']['BLIND']['execution']['runtime']['session']
        else:e[field]=1 if field=='exit' else 'wrong'
    owner=m.BalancedReviewOwner(lambda:deepcopy(rec),source_loader=lambda:deepcopy(cold),registry=r,knowledge={},enabled=True)
    if field=='revoked':owner.revoke()
    with pytest.raises(ValueError):owner.issue()


def test_existing_native_daily_renderer_consumes_new_contract_only_whole():
    p,v,r=fixture();rec=record(p,v,r)
    owner=m.BalancedReviewOwner(lambda:deepcopy(rec),source_loader=lambda:deepcopy(p),registry=r,knowledge={},enabled=True)
    c=owner.consume(owner.issue(),packet=p)
    actions={k:dict(prior_verdict_reusable=True) for k in ('business','valuation','timing')}
    text=compact_message('UNSEEN','2026-10-28',c,actions,audit_ref='test-only')
    assert 'ATTRACTIVE' in text and 'WAIT_FOR_ZONE' in text and 'Strict B2 NOT_ISSUED' in text
    assert 'FPER: NOT_AVAILABLE_FOR_BALANCED_USE' in text
    assert 'newbuyer entry:' in text and 'holder resistance:' in text
    actions['valuation']['prior_verdict_reusable']=False
    with pytest.raises(ValueError):compact_message('UNSEEN','2026-10-28',c,actions,audit_ref='test-only')


def test_unissued_axis_cannot_claim_separate_confidence():
    p,v,r=fixture();v['balanced']['overall']['confidence']='HIGH'
    with pytest.raises(ValueError,match='unissued_axis_confidence'):check(p,v,r)


@pytest.mark.parametrize('case,error',[
    ('risk_explanation','risk_reason_without_evidence'),
    ('business_as_valuation','valuation_use_denied'),
    ('price_as_holder','independent_axis_use_denied'),
])
def test_cross_axis_prose_does_not_grant_authority(case,error):
    p,v,r=fixture();b=v['balanced']
    if case=='risk_explanation':b['active_material_risk_reason']='No current risk evidence.'
    if case=='business_as_valuation':b['valuation']['refs'].append('business')
    if case=='price_as_holder':b['holder_virtual']['refs'].append('price')
    with pytest.raises(ValueError,match=error):check(p,v,r)


def test_prompt_explicitly_preserves_empty_risk_and_axis_restrictions():
    p,_,r=fixture();text=m.prompt(p,'BLIND',knowledge={},registry=r)
    assert 'active_material_risk_reason MUST be the' in text
    assert 'only usable_valuation_refs' in text
    assert 'never chart/timing' in text


def test_original_controller_finalizes_complete_versioned_output(tmp_path):
    from app.services.vnext_research_store import ResearchStore
    from app.services.vnext_runtime import RuntimeConfig
    from app.services.vnext_no_send_controller import NoSendController,cycle_identity
    from app.services.vnext_model_dependencies import WholeVerdictDependencies
    p,v,r=fixture();rec=record(p,v,r)
    owner=m.BalancedReviewOwner(lambda:deepcopy(rec),source_loader=lambda:deepcopy(p),registry=r,knowledge={},enabled=True)
    reg=dict(security=p['base']['public_security'],registration_version='synthetic-registration')
    prompts={s:m.prompt(p,s,knowledge={},registry=r,prior=None if s=='BLIND' else v).encode() for s in rec['stages']}
    graph=WholeVerdictDependencies(owner,registration=reg,prompts=prompts)
    assert graph.review(p['base'],registry=r,registration=reg)['reusable']
    db=tmp_path/'research.sqlite3';ResearchStore(db)
    controller=NoSendController(RuntimeConfig(db,'test',mode='write',environment='test'),enabled=True)
    cycle=cycle_identity(registration=reg,session='2026-10-28',source_generation='synthetic-only',
        correction_epoch='',canonical_input_digest=digest(p))
    result=controller.finalize(cycle=cycle,packet=p,owner=owner,registry=r,registration=reg,prompts=prompts)
    assert result['state']=='NO_SEND_READY' and not result['send'] and not result['strict_ready']
    assert result['rendered']['balanced']['newbuyer_fundamental']=='ATTRACTIVE'
    assert result['validated_receipt']['contract']==m.CONTRACT
    assert controller.finalize(cycle=cycle,packet=p,owner=owner,registry=r,registration=reg,prompts=prompts)==result
