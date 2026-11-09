from copy import deepcopy
import pytest
from test_dated_research_c22i import sample
from app.services.dated_research_model import encoded,digest,reference_catalog
from app.services.dated_research_review_v2 import source_bound_temporal,validate_split


def case():
    view,binding,out,ref=sample()
    t=source_bound_temporal(view,ref,mode='RETROSPECTIVE_DATED_RESEARCH',prepared_at='2026-11-09T14:10:00Z')
    axis=out['newbuyer_fundamental_attractiveness']
    axis.update(refs=[ref],pro=[ref],temporal_limitations=[t['caveat']],claim_role='ECONOMIC_HYPOTHESIS')
    return view,binding,out,ref,{ref:t}


@pytest.mark.parametrize('state',['ATTRACTIVE','UNATTRACTIVE'])
def test_restricted_valuation_only_direction_rejected(state):
    view,binding,out,_,times=case();out['newbuyer_fundamental_attractiveness']['state']=state
    with pytest.raises(ValueError,match='standalone_direction'):
        validate_split(out,view=view,binding=binding,temporal=times)


@pytest.mark.parametrize('state',['NEUTRAL','UNKNOWN'])
def test_non_directional_valuation_context_allowed(state):
    view,binding,out,_,times=case();out['newbuyer_fundamental_attractiveness']['state']=state
    assert validate_split(out,view=view,binding=binding,temporal=times)


def add_financial_link(view,out):
    name='newbuyer_fundamental_attractiveness';a=out[name]
    a['refs'].append('financial');a['pro'].append('financial')
    a['statement']='Dated revenue supports a conditional economic hypothesis, not a causal FACT.'
    c=deepcopy(reference_catalog(view)['numeric_facts'][0]);c['axis']=name
    out['citations']=[c]
    a['independent_economic_support']=[dict(ref='financial',path=c['path'],
        statement_fragment='Dated revenue supports a conditional economic hypothesis',source_excerpt='')]


def test_linked_financial_positive_and_unfavorable_timing_stay_independent():
    view,binding,out,_,times=case();add_financial_link(view,out)
    result=validate_split(out,view=view,binding=binding,temporal=times)
    assert result['newbuyer_fundamental_attractiveness']['state']=='ATTRACTIVE'
    assert result['newbuyer_entry_timing']['state']=='UNFAVORABLE'
    assert result['newbuyer_fundamental_attractiveness']['confidence']=='HIGH'


@pytest.mark.parametrize('defect',['dummy_ref','missing_citation','unlinked_prose','same_raw'])
def test_dummy_or_correlated_support_not_independent(defect):
    view,binding,out,ref,times=case();add_financial_link(view,out)
    if defect=='dummy_ref':out['newbuyer_fundamental_attractiveness']['independent_economic_support']=[]
    if defect=='missing_citation':out['citations']=[]
    if defect=='unlinked_prose':out['newbuyer_fundamental_attractiveness']['independent_economic_support'][0]['statement_fragment']='not in the argument'
    if defect=='same_raw':
        view['financial_observations'][0]['original_fields']['original_raw_sha256']=view['valuation'][0]['original_fact']['raw_sha256']
        binding['research_view_sha256']=digest(encoded(view));out['input_digest']=binding['research_view_sha256']
    with pytest.raises(ValueError,match='standalone_direction'):
        validate_split(out,view=view,binding=binding,temporal=times)


def test_explicit_original_standalone_grant_not_overblocked():
    view,binding,out,ref,_=case();view['valuation'][0]['original_fact']['overall_direction_use']=True
    binding['research_view_sha256']=digest(encoded(view));out['input_digest']=binding['research_view_sha256']
    t=source_bound_temporal(view,ref,mode=out['research_mode'],prepared_at='2026-11-09T14:10:00Z')
    assert validate_split(out,view=view,binding=binding,temporal={ref:t})


def test_count_is_not_causal_proof_and_hypothesis_remains_usable():
    view,binding,out,_=sample();view['verified_mechanism_count']=1
    binding['research_view_sha256']=digest(encoded(view));out['input_digest']=binding['research_view_sha256']
    out['newbuyer_fundamental_attractiveness']['claim_role']='VERIFIED_CAUSAL_FACT'
    with pytest.raises(ValueError,match='no_proven_cause_ref_available'):
        validate_split(out,view=view,binding=binding,temporal={})
    for role in ('ECONOMIC_HYPOTHESIS','DATED_OBSERVATION'):
        out['newbuyer_fundamental_attractiveness']['claim_role']=role
        assert validate_split(out,view=view,binding=binding,temporal={})


def test_forged_pit_still_rejected_before_standalone_gate():
    view,binding,out,_,times=case();add_financial_link(view,out);out['research_mode']='POINT_IN_TIME'
    for t in times.values():t.update(research_mode='POINT_IN_TIME',direction_anchor_temporally_eligible=True,caveat='PIT_AVAILABLE')
    out['newbuyer_fundamental_attractiveness']['temporal_limitations']=['PIT_AVAILABLE']
    with pytest.raises(ValueError,match='temporally_eligible'):
        validate_split(out,view=view,binding=binding,temporal=times)


def test_source_excerpt_profile_support_is_hypothesis_not_cause():
    view,binding,out,_,times=case()
    view['business_mechanism']['source_context']=[dict(source_ref='business',source_sha256='c'*64,
        content=dict(description='Public business context supports a demand hypothesis.'))]
    binding['research_view_sha256']=digest(encoded(view));out['input_digest']=binding['research_view_sha256']
    a=out['newbuyer_fundamental_attractiveness'];a['refs'].append('business');a['pro'].append('business')
    a['statement']='Demand is a conditional hypothesis, not verified causality.'
    a['independent_economic_support']=[dict(ref='business',path='content.description',
        statement_fragment='Demand is a conditional hypothesis',source_excerpt='Public business context')]
    assert validate_split(out,view=view,binding=binding,temporal=times)
    a['claim_role']='VERIFIED_CAUSAL_FACT'
    with pytest.raises(ValueError,match='no_proven_cause_ref_available'):
        validate_split(out,view=view,binding=binding,temporal=times)
