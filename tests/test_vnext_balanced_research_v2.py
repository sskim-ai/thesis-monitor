from copy import deepcopy
import pytest

from app.services import vnext_balanced_research as v1
from app.services import vnext_balanced_research_v2 as m
from test_vnext_balanced_research import fixture, negative


def case(*args):
    p,v,r=fixture(*args)
    v['contract']=m.CONTRACT
    v['balanced']['overall'].update(policy=m.OVERALL_CONTRACT,anchor_refs=[],corroborating_refs=[],
        independent_support_reason='No separate directional support has been admitted.',
        counterevidence_state='NOT_ISSUED',counterevidence_refs=[],missing_required=[])
    return p,v,r


def directional(side='BUY'):
    p,v,r=case()
    base=deepcopy(p['base'])
    first=base['evidence'][0];first['direction_allowed']=True
    second=deepcopy(first);second.update(ref='corroboration',source_sha=v1.digest('second'),field='financial.operating_income')
    second['data']['fields']['source_receipt']='distinct-economic-lineage'
    base['evidence'].append(second)
    from app.services.vnext_codex_research import numeric_catalog
    base['numeric_catalog']=numeric_catalog(base)
    p=v1.original.attach(base)
    driver=deepcopy(v['economic_drivers_positive'][0]);driver['refs']=['corroboration']
    driver['lineage_groups']=[v1.v3.evidence_contract(base)['corroboration']['lineage_group']]
    v['economic_drivers_positive'].append(driver)
    v['balanced']['business_positive_refs'].append('corroboration')
    if side=='SELL':
        v['economic_drivers_negative']=v.pop('economic_drivers_positive');v['economic_drivers_positive']=[]
        v['balanced'].update(business_positive_refs=[],business_negative_refs=['business','corroboration'])
        v['economic_evidence_signal']='LIMITED_NEGATIVE'
        v['newbuyer_stance']='WAIT_FOR_TRIGGER';v['holder_stance']='RISK_REVIEW'
        v['balanced']['holder_virtual']['stance']='REDUCE'
    v['balanced']['overall'].update(stance=side,balance=dict(buy=4.0 if side=='SELL' else 6.0,sell=6.0 if side=='SELL' else 4.0),
        refs=['business','corroboration'],anchor_refs=['business'],corroborating_refs=['corroboration'],
        independent_support_reason='Distinct operating evidence corroborates the material anchor within its admitted scope.',
        counterevidence_state='REVIEWED_WITHIN_ADMITTED_SET',
        counterevidence_refs=['business','corroboration'] if side=='SELL' else [])
    return p,v,r


def check(p,v,r):return m.validate_and_render(v,p,registry=r)


@pytest.mark.parametrize('side',['BUY','SELL'])
def test_opposite_polarity_not_universal_prerequisite(side):
    p,v,r=directional(side)
    assert check(p,v,r)['balanced']['overall']['stance']==side
    old=deepcopy(v);old['contract']=v1.CONTRACT
    old['balanced']['overall']={k:v for k,v in old['balanced']['overall'].items() if k in v1.Overall.model_fields}
    with pytest.raises(ValueError,match='independent_balance_missing'):
        v1.validate_and_render(old,p,registry=r)


def test_source_permission_not_created_by_new_policy():
    p,v,r=directional();p['base']['evidence'][0]['direction_allowed']=False
    with pytest.raises(ValueError,match='live_owner_binding'):check(p,v,r)
    p=v1.original.attach(p['base'])
    with pytest.raises(ValueError,match='source_direction_not_authorized'):check(p,v,r)


@pytest.mark.parametrize('change,error',[
    ('correlated','correlated_support'),('empty_anchor','material_anchor_missing'),
    ('empty_support','distinct_support_missing'),('missing_required','required_counterevidence_missing'),
    ('not_reviewed','required_counterevidence_missing'),('wrong_balance','ordinal_mismatch'),
    ('omitted_adverse','admitted_adverse_evidence_omitted'),('revoked','business_use_denied'),
    ('display','evidence_use_denied'),('price','evidence_use_denied'),
    ('private','private_investor_basis_not_admitted'),('wrong_policy','literal_error'),
    ('unbound_prose','unbound_or_invalid_prose')])
def test_overall_adversarial(change,error):
    p,v,r=directional('SELL' if change=='omitted_adverse' else 'BUY');o=v['balanced']['overall']
    if change=='correlated':p['base']['evidence'][-1]['data']['fields']['source_receipt']='synthetic'
    if change=='empty_anchor':o['anchor_refs']=[]
    if change=='empty_support':o['corroborating_refs']=[]
    if change=='missing_required':o['missing_required']=['Missing required operating confirmation.']
    if change=='not_reviewed':o['counterevidence_state']='NOT_ISSUED'
    if change=='wrong_balance':o['balance']={'buy':4,'sell':6}
    if change=='omitted_adverse':o['counterevidence_refs']=[]
    if change=='revoked':r.revoke(p['base']['public_security']['canonical_security_id'],p['base']['evidence'][0]['source_sha'])
    if change in ('display','price'):o['corroborating_refs']=['h_display' if change=='display' else 'price']
    if change=='private':v['holdings_included']=True
    if change=='wrong_policy':o['policy']='SELF_ISSUED'
    if change=='unbound_prose':o['independent_support_reason']='Target 100.'
    if change=='correlated':
        # Original v3 correctly coalesces same-lineage metrics into one driver.
        v['economic_drivers_positive']=v['economic_drivers_positive'][:1]
        v['economic_drivers_positive'][0]['refs']=['business','corroboration']
        p=v1.original.attach(p['base'])
    with pytest.raises(ValueError,match=error):check(p,v,r)


@pytest.mark.parametrize('judgment,expected',[('SUPPORTIVE','ATTRACTIVE'),('NEUTRAL','WAIT'),('BURDENSOME','WAIT'),('NOT_ISSUED','NOT_ISSUED')])
def test_newbuyer_not_overall_or_entry_timing(judgment,expected):
    p,v,r=case();v['balanced']['valuation']['judgment']=judgment
    result=check(p,v,r)['balanced']
    assert result['newbuyer_fundamental']==expected
    assert result['overall']['stance']=='NOT_ISSUED' and result['timing']['state']=='WAIT_FOR_ZONE'


def test_material_risk_still_avoid_and_not_automatic_holder_reduce():
    p,v,r=case();negative(v)
    v['balanced'].update(active_material_risk_refs=['business'],active_material_risk_reason='Current material structural impairment.')
    result=check(p,v,r)['balanced']
    assert result['newbuyer_fundamental']=='AVOID'
    assert result['holder_virtual']['stance']=='HOLDABLE'


def test_missing_economics_unissued_not_universal_wait():
    p,v,r=case();v['economic_drivers_positive']=[];v['economic_evidence_signal']='NO_ELIGIBLE_ECONOMIC_EVIDENCE'
    v['newbuyer_stance']='INSUFFICIENT';v['holder_stance']='INSUFFICIENT'
    v['balanced']['business_positive_refs']=[];v['balanced']['holder_virtual']['stance']='NOT_ISSUED'
    assert check(p,v,r)['balanced']['newbuyer_fundamental']=='NOT_ISSUED'


@pytest.mark.parametrize('country,kind,ticker',[('KR','common_stock','UNSEEN_KR'),('US','common_stock','UNSEEN_US'),
    ('US','ADS','UNSEEN_ADS'),('KR','financial','UNSEEN_FIN'),('US','cyclical','UNSEEN_CYCLE')])
def test_unseen_identity_equivalence(country,kind,ticker):
    p,v,r=case(ticker,country,kind)
    c=check(p,v,r)
    assert c['balanced']['newbuyer_fundamental']=='ATTRACTIVE'
    assert not c['balanced']['send'] and not c['balanced']['strict_B2']
    assert m.CONTRACT in m.render(c)


def test_prompt_and_schema_distinct_without_old_output_upgrade():
    p,v,r=case();text=m.prompt(p,'BLIND',knowledge={},registry=r)
    assert m.CONTRACT in text and 'False/unknown permission cannot be renewed' in text
    assert 'REVIEWED_WITHIN_ADMITTED_SET' in text
    assert v1.digest(m.schema())!=v1.digest(v1.schema()) and m.ENABLED_BY_DEFAULT is False
    _,old,_=fixture()
    with pytest.raises(ValueError):check(p,old,r)


@pytest.mark.parametrize('axis',['overall','timing'])
def test_unissued_confidence(axis):
    p,v,r=case();v['balanced'][axis]['confidence']='HIGH'
    if axis=='timing':v['balanced'][axis]['state']='UNRESOLVED'
    with pytest.raises(ValueError,match='unissued_axis_confidence'):check(p,v,r)


def test_v2_whole_native_no_send_consumer_and_revocation():
    import time
    from app.services import vnext_balanced_stage_review as stage
    from app.services.vnext_daily_research import compact_message
    p,v,r=case();caps=[]
    for name in ('BLIND','ADJUDICATION'):
        previous=caps[0] if caps else None
        text=stage.prompt(p,name,knowledge={},registry=r,version=stage.POLICY_V2,prior=v if previous else None)
        at=time.time()
        record=dict(output=deepcopy(v),validation=check(p,v,r),execution=dict(
            stage=name,status='VALIDATED',exit=0,attempt=1,retry=0,runtime=dict(verified=True,session='SYNTHETIC_'+name),
            model='gpt-6-astra',effort='xhigh',packet_sha=v1.digest(p),prompt_sha=v1.digest(text.encode()),
            schema_sha=v1.digest(m.schema()),output_sha=v1.digest(v),started=at,ended=at,deadline=at+600,
            stage_contract=stage.CONTRACT,prompt_version=stage.POLICY_V2,invocation_id='SYNTHETIC_ONLY',
            request_sha=v1.digest(name),approved_request_sha=v1.digest(name)))
        caps.append(stage.AcceptedStage(lambda rec=record:deepcopy(rec),packet=p,stage=name,
            version=stage.POLICY_V2,knowledge={},registry=r,source_loader=lambda:deepcopy(p),prior=previous))
    with pytest.raises(ValueError,match='default_off'):stage.StageReviewOwner(*caps)
    owner=stage.StageReviewOwner(*caps,enabled=True);receipt=owner.issue()
    assert receipt['contract']==m.CONTRACT and owner.issue() is receipt
    checked=owner.consume(receipt,packet=p)
    actions={k:dict(prior_verdict_reusable=True) for k in ('business','valuation','timing')}
    msg=compact_message('UNSEEN','2026-10-28',checked,actions,audit_ref='synthetic-only')
    assert m.CONTRACT in msg and 'ATTRACTIVE' in msg and 'WAIT_FOR_ZONE' in msg
    with pytest.raises(ValueError):owner.consume(dict(receipt),packet=p)
    caps[0].revoke()
    with pytest.raises(ValueError,match='revoked'):owner.issue()


def test_v1_blind_cannot_be_relabelled_v2_adjudication():
    from app.services import vnext_balanced_stage_review as stage
    from test_vnext_balanced_stage_review import cap, MemoryController
    p,v,r=fixture();old,_=cap(p,v,r)
    with pytest.raises(ValueError,match='policy_version_mismatch'):
        MemoryController().run_stage(invocation_id='synthetic-v2',account='test',packet=p,
            stage='ADJUDICATION',version=stage.POLICY_V2,knowledge={},registry=r,
            source_loader=lambda:p,approval=lambda _:True,account_lease=lambda:None,
            invoke=lambda *_:None,prior=old)
