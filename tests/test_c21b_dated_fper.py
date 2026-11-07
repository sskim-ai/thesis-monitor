"""New producer boundary only; fictional sources are not actual finance proof."""
from copy import deepcopy
import json
import pytest
from app.services import valuation_analysis as a
from app.services.vnext_research_store import digest
from scripts.kis_eps_wire_calibration import sealed
from test_kis_current_fy1_owner import price_inputs,eps as old_eps
from test_kis_exact_action_guard import docs,page


@pytest.fixture
def cap():
    i=price_inputs();raw=b'{"synthetic_analyst":true}'
    r=dict(http_status=200,raw_sha256=digest(raw),ended_at='2026-10-02T12:00:00+09:00')
    e=old_eps();e.pop('receipt_sha256');e['estimate_sha256']=digest(raw);e=sealed(e)
    f=a.ValuationAnalysisFact(metric='FY1_EPS',ticker=e['security_code'],canonical_security_id='synthetic-security',
        provider='KIS',value=30,exact_value='30',unit='KRW_PER_SHARE',metric_semantic='KIS_ANALYST_FY1_EPS',
        source_generation='SYNTHETIC',raw_sha256=digest(raw),source_receipt_sha256=digest(r),
        retrieval_timestamp=r['ended_at'],forecast_fiscal_period=e['period'],estimate_vintage=e['estdate'],
        estimated=True,scale_proof_sha256='a'*64,basis='SYNTHETIC',caution='SYNTHETIC')
    actions={}
    for v in docs()['actions']:
        ev,receipt=page(v);actions[v]=dict(raw=ev.raw,receipt=receipt)
    s=dict(i['security'],country='KR',security_type='common_stock',issuer_type='domestic',canonical_company_id='example',corp_code='example')
    return dict(security=s,eps=f,eps_raw=raw,eps_receipt=r,original_eps=e,
        price=dict(raw=i['evidence'].raw,receipt=i['receipt']),calendar=i['calendar'],price_docs=i['documentation'],actions=actions,action_docs=docs())


def test_dated_provenance_and_old_dump_unchanged(cap):
    before=cap['eps'].model_dump(mode='json');pin=digest(before)
    ids,facts,denials=a.dated_fper_source(lambda:deepcopy(cap)).read()
    assert not denials and len(facts)==1
    f=facts[0];p=json.loads(f.basis)
    assert p['price']['session']=='2026-09-30' and p['available_at']==cap['eps'].retrieval_timestamp
    assert p['price']['close']=='100' and p['exact_quotient']=={'numerator':'10','denominator':'3'}
    assert len(p['actions']['parents'])==6 and p['eps']==before
    assert not f.overall_direction_use and not f.formal_native and not f.send
    assert digest(cap['eps'].model_dump(mode='json'))==pin


@pytest.mark.parametrize('change',['code','canonical','raw','eps_receipt','share','price_receipt','session','action','missing_action'])
def test_source_tampering_denied(cap,change):
    if change=='code':cap['security']['ticker']='654321'
    if change=='canonical':cap['security']['canonical_security_id']='another'
    if change=='raw':cap['eps_raw']=b'changed'
    if change=='eps_receipt':cap['eps_receipt']['ended_at']='2026-10-03T12:00:00+09:00'
    if change=='share':
        e=cap['original_eps'];e.pop('receipt_sha256');e['unit']='USD_PER_SHARE';cap['original_eps']=sealed(e)
    if change=='price_receipt':cap['price']['receipt']['raw_sha256']='0'*64
    if change=='session':cap['calendar']['latest_completed_session']='2026-10-01'
    if change=='action':cap['actions']['rev_split']['receipt']['raw_sha256']='0'*64
    if change=='missing_action':cap['actions'].pop('rev_split')
    if change=='action':
        _,facts,denials=a.dated_fper_source(lambda:cap).read()
        assert not facts and denials[0]['reason']=='UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE'
    else:
        with pytest.raises(ValueError):a.dated_fper_source(lambda:cap).read()


def test_known_share_unit_action_denies_numeric_fact(cap):
    from test_kis_exact_action_guard import row
    ev,receipt=page('rev_split',rows=[row(day='2026-09-15')])
    cap['actions']['rev_split']=dict(raw=ev.raw,receipt=receipt)
    _,facts,denials=a.dated_fper_source(lambda:cap).read()
    assert not facts and denials[0]['reason']=='UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE'


@pytest.mark.parametrize('value',['0','-1'])
def test_nonmeaningful_does_not_damage_eps(cap,value):
    cap['eps']=a.ValuationAnalysisFact.model_validate(dict(cap['eps'].model_dump(),value=float(value),exact_value=value))
    e=cap['original_eps'];e.pop('receipt_sha256');e['value']=value;cap['original_eps']=sealed(e)
    before=cap['eps'].model_dump()
    _,facts,denials=a.dated_fper_source(lambda:cap).read()
    assert not facts and denials[0]['reason']=='NOT_MEANINGFUL' and cap['eps'].model_dump()==before


def test_ratio_only_cannot_issue_direction(cap):
    from app.services.vnext_daily_research import UseRegistry
    from app.services.vnext_unified_judgment import AI_OWNED_V3,_resolve_axis_evidence,prompt
    src=a.dated_fper_source(lambda:deepcopy(cap))
    view=a.AnalysisView(sources=[src],ticker=cap['eps'].ticker,as_of='2026-10-03T00:00:00+09:00',enabled=True)
    registry=UseRegistry();bundle=view.unified_premodel(registry=registry,contract=AI_OWNED_V3)
    ctx=bundle['investment_valuation_context'];f=ctx['facts'][0]
    assert all(ctx['axes'][axis][0]==f for axis in ('Overall','NewBuyer','Holders'))
    assert 'DATED ANALYSIS ONLY' in prompt(bundle,'BLIND',knowledge='',registry=registry,version=AI_OWNED_V3)
    ref=bundle['admissibility'][0]['ref']
    candidate=dict(business='INSUFFICIENT',technical_review=None,security_id=cap['eps'].canonical_security_id,as_of=bundle['base']['as_of'],
        **{k:dict(stance='NOT_ISSUED',refs=[],counterevidence_refs=[]) for k in ('overall','newbuyer','holder_virtual','valuation','timing')})
    candidate['overall']=dict(stance='BUY',refs=[ref],counterevidence_refs=[])
    with pytest.raises(ValueError,match='economic_anchor_missing'):_resolve_axis_evidence(candidate,bundle,{ref},None)
