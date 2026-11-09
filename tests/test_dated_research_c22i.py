from copy import deepcopy
import json
import pytest
from app.services.dated_research_model import encoded,digest,reference_catalog
from app.services.dated_research_review_v2 import (
    CONTRACT,source_bound_temporal,validate_split,render_numeric_citations,
    comparison_period_detail,comparison_semantics,split_preview,
)


def sample(*, early=False):
    cutoff='2026-11-06T03:32:08+00:00';retrieved='2026-11-05T00:00:00+00:00' if early else '2026-11-07T00:00:00+00:00'
    receipt=dict(ticker='GENERIC',raw_sha256='a'*64,retrieved_at=retrieved)
    fact=dict(metric='PER',value=10,unit='multiple',ticker='GENERIC',raw_sha256='a'*64,
        source_receipt_sha256=digest(encoded(receipt)),retrieval_timestamp=retrieved,overall_direction_use=False,
        basis='PROVIDER_REPORTED_PER')
    ref=encoded(dict(field='PER',receipt=fact['source_receipt_sha256'])).decode()
    fields=dict(current_value=100,prior_comparable_value=90,period_start='2026-04-01',period_end='2026-06-30',
        prior_period_start='2025-04-01',prior_period_end='2025-06-30',period_type='single_quarter',currency='KRW',unit_scale=1)
    view=dict(ticker='GENERIC',as_of=cutoff,valuation=[dict(metric='PER',value=10,source_locator=ref,original_fact=fact)],
        capture_receipts={fact['source_receipt_sha256']:receipt},verified_mechanism_count=0,
        financial_observations=[dict(original_ref='financial',role='QUANTITATIVE_COMPARISON',original_fields=fields,
            original_quality={},source_sha='b'*64,lineage_group='lineage',source_cutoff=cutoff)],
        financial_numeric_catalog=[dict(ref='financial',path='fields.prior_comparable_value',value=90,unit='KRW',
            as_of='2025-04-01/2025-06-30',basis='consolidated single_quarter')],
        technical=dict(evidence=[dict(ref_id='technical',value=55,as_of=cutoff,numeric_prose_eligible=True,unit='RSI')]),
        business_mechanism=dict(source_context=[]),structural_risk=dict(occurred_risk_assertion=False),
        dated_price_structure=dict(source_sha256='sr',as_of=cutoff,SR={}))
    binding=dict(byte_binding_verified=True,research_view_sha256=digest(encoded(view)))
    def axis(state,refs):return dict(state=state,refs=refs,pro=refs,con=[],unknown=['Causal mechanism unknown'],
        confidence='HIGH',statement='Synthetic opinion only',as_of=cutoff,temporal_limitations=[])
    output=dict(contract=CONTRACT,ticker='GENERIC',input_digest=binding['research_view_sha256'],
        research_mode='POINT_IN_TIME' if early else 'RETROSPECTIVE_DATED_RESEARCH',
        newbuyer_fundamental_attractiveness=axis('ATTRACTIVE',['financial']),
        newbuyer_entry_timing=axis('UNFAVORABLE',['technical']),structural_risk='POTENTIAL_EXPOSURE',
        thesis_comparison='NOT_COMPARED_TO_REGISTERED_THESIS',NO_SEND=True,Strict_NATIVE_STAGE_READY=False)
    return view,binding,output,ref


def test_positive_pit_proven_by_original_capture_and_retro_later_context():
    for early in (True,False):
        view,binding,out,ref=sample(early=early)
        time=source_bound_temporal(view,ref,mode=out['research_mode'],prepared_at='2026-11-08T00:00:00Z')
        axis=out['newbuyer_fundamental_attractiveness'];axis['refs'].append(ref);axis['pro'].append(ref)
        axis['temporal_limitations']=[time['caveat']]
        assert validate_split(out,view=view,binding=binding,temporal={ref:time})
        assert time['original_use_limits']['overall_direction_use'] is False


@pytest.mark.parametrize('change', ['eligible','available','raw_sha','cutoff','locator'])
def test_forged_temporal_map_rejected(change):
    view,binding,out,ref=sample();out['research_mode']='POINT_IN_TIME'
    time=source_bound_temporal(view,ref,mode='POINT_IN_TIME',prepared_at='2026-11-08T00:00:00Z')
    if change=='eligible':time.update(direction_anchor_temporally_eligible=True,caveat='PIT_AVAILABLE')
    if change=='available':time['available_at_proven']='2026-11-01T00:00:00Z'
    if change=='raw_sha':time['raw_sha256']='0'*64
    if change=='cutoff':time['historical_information_cutoff']='2026-11-09T00:00:00Z'
    if change=='locator':time['source_locator']='wrong'
    out['newbuyer_fundamental_attractiveness'].update(refs=[ref],pro=[ref],temporal_limitations=['PIT_AVAILABLE'])
    with pytest.raises(ValueError):validate_split(out,view=view,binding=binding,temporal={ref:time})


def test_arbitrary_availability_without_receipt_cannot_prove_early_pit():
    view,binding,out,ref=sample(early=True);view.pop('capture_receipts')
    binding['research_view_sha256']=digest(encoded(view));out['input_digest']=binding['research_view_sha256']
    time=source_bound_temporal(view,ref,mode='POINT_IN_TIME',prepared_at='2026-11-08T00:00:00Z')
    assert not time['direction_anchor_temporally_eligible']
    time.update(available_at_proven='2026-11-01T00:00:00Z',direction_anchor_temporally_eligible=True,caveat='PIT_AVAILABLE')
    out['newbuyer_fundamental_attractiveness'].update(refs=[ref],pro=[ref],temporal_limitations=['PIT_AVAILABLE'])
    with pytest.raises(ValueError):validate_split(out,view=view,binding=binding,temporal={ref:time})


@pytest.mark.parametrize('change',['timezone','future_price','price_conflict','receipt','ticker','ref'])
def test_source_temporal_drift(change):
    view,_,_,ref=sample();f=view['valuation'][0]['original_fact']
    if change=='timezone':f['retrieval_timestamp']='2026-11-07T00:00:00'
    if change=='future_price':f['reference_price_as_of']='2026-11-09'
    if change=='price_conflict':f.update(reference_price_as_of='2026-10-23',basis=json.dumps(dict(price=dict(session='2026-10-24'))))
    if change=='receipt':f['raw_sha256']='0'*64
    if change=='ticker':f['ticker']='OTHER'
    if change=='ref':view['valuation'][0]['source_locator']=ref.replace('PER','PBR');ref=view['valuation'][0]['source_locator']
    with pytest.raises(ValueError):source_bound_temporal(view,ref,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-08T00:00:00Z')


def test_period_projection_unknown_retrieval_and_exact_original_numbers():
    view,_,_,_=sample();catalog=reference_catalog(view);c=dict(catalog['numeric_facts'][0],axis='overall')
    rows=render_numeric_citations(dict(citations=[c]),catalog,view)
    assert [rows[0]['period_start'],rows[0]['period_end']]==['2025-04-01','2025-06-30']
    assert rows[0]['retrieved_at'] is None and rows[0]['source_cutoff']==view['as_of']
    assert rows[0]['provider']=='UNKNOWN' and rows[0]['value']==90
    bad=deepcopy(view);bad['financial_observations'][0]['original_fields']['prior_period_end']='2025-09-30'
    rows=render_numeric_citations(dict(citations=[c]),reference_catalog(bad),bad)
    assert rows[0]['period_metadata_state']=='UNKNOWN_OR_CONFLICT' and rows[0]['period_end'] is None


def test_evidence_roles_and_numeric_split_boundary():
    view,binding,out,_=sample()
    assert validate_split(out,view=view,binding=binding,temporal={})
    bad=deepcopy(out);bad['newbuyer_fundamental_attractiveness'].update(refs=['technical'],pro=['technical'])
    with pytest.raises(ValueError,match='economic_context'):validate_split(bad,view=view,binding=binding,temporal={})
    bad=deepcopy(out);bad['newbuyer_fundamental_attractiveness']['claim_role']='VERIFIED_CAUSAL_FACT'
    with pytest.raises(ValueError,match='unverified_cause'):validate_split(bad,view=view,binding=binding,temporal={})
    bad=deepcopy(out);bad['structural_risk']='OBSERVED_RISK'
    with pytest.raises(ValueError):validate_split(bad,view=view,binding=binding,temporal={})
    fact=reference_catalog(view)['numeric_facts'][0]
    out['citations']=[dict(fact,axis='newbuyer_fundamental_attractiveness')]
    assert validate_split(out,view=view,binding=binding,temporal={})
    out['citations'][0]['basis']='wrong'
    with pytest.raises(ValueError):validate_split(out,view=view,binding=binding,temporal={})


def test_typed_comparison_and_unissued_preview():
    view,binding,_,_=sample();f=view['financial_observations'][0]['original_fields']
    assert comparison_period_detail(f)['kind']=='EQUAL_DURATION'
    f=dict(period_type='annual',period_start='2025-08-29',period_end='2026-09-03',prior_period_start='2024-08-30',
        prior_period_end='2025-08-28',fiscal_comparability=dict(contract='ISSUER_DECLARED_52_53_WEEK_ANNUAL_COMPARABLE',value_adjustment=None))
    assert comparison_semantics(f) is True
    assert comparison_period_detail(f)['kind']=='ISSUER_DECLARED_53_52_WEEK_COMPARABLE_WITH_CAVEAT'
    preview=split_preview(view,binding,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-08T00:00:00Z')
    assert preview['new_judgment'] is None and preview['model_executed'] is False


def test_original_exact_decimal_string_not_replaced_by_float_rounding():
    view,_,_,ref=sample();row=view['valuation'][0];fact=row['original_fact']
    exact='50.906555090655509065550906555090655509065550906555'
    row['value']=exact;fact.update(value=50.90655509065551,exact_value=exact)
    assert source_bound_temporal(view,ref,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-08T00:00:00Z')
    row['value']='50.90655509065551'
    with pytest.raises(ValueError,match='value_or_metric_drift'):
        source_bound_temporal(view,ref,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-08T00:00:00Z')


def test_bound_view_sha_drift_and_prepared_time_conflict():
    view,binding,_,ref=sample();view['valuation'][0]['original_fact']['raw_sha256']='0'*64
    with pytest.raises(ValueError,match='source_digest'):
        split_preview(view,binding,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-08T00:00:00Z')
    view,_,_,ref=sample()
    with pytest.raises(ValueError,match='temporal_metadata_conflict'):
        source_bound_temporal(view,ref,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-01T00:00:00Z')


def test_original_finished_at_receipt_without_new_identity_protocol():
    view,_,_,ref=sample(early=True);row=view['valuation'][0];fact=row['original_fact']
    receipt=dict(raw_sha256=fact['raw_sha256'],finished_at=fact['retrieval_timestamp'],HTTP_status=200)
    fact['source_receipt_sha256']=digest(encoded(receipt))
    row['source_locator']=encoded(dict(field='PER',receipt=fact['source_receipt_sha256'])).decode()
    view['capture_receipts']={fact['source_receipt_sha256']:receipt}
    result=source_bound_temporal(view,row['source_locator'],mode='POINT_IN_TIME',prepared_at='2026-11-08T00:00:00Z')
    assert result['direction_anchor_temporally_eligible'] is True
