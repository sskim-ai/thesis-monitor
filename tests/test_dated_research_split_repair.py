from copy import deepcopy
from pathlib import Path
import hashlib,json
import pytest
from test_dated_research_c22i import sample
from app.services.dated_research_model import encoded,digest,reference_catalog
from app.services.dated_research_review_v2 import validate_split,source_bound_temporal,split_quality_review


def validate(v,b,o,t):return validate_split(o,view=v,binding=b,temporal=t)


def supported():
    v,b,o,ref=sample();name='newbuyer_fundamental_attractiveness'
    time=source_bound_temporal(v,ref,mode=o['research_mode'],prepared_at='2026-11-09T14:10:00Z')
    a=o[name];a.update(refs=[ref],pro=['The dated observation supports a conditional hypothesis.'],
        con=['Profit durability remains unproven.'],statement='A conditional assessment, not a verified cause.',
        temporal_limitations=[ref+': '+time['caveat']+': later information'],
        independent_economic_support=[dict(ref='financial',path='fields.prior_comparable_value',
            statement_fragment='Independent dated financial context supports this conditional argument.',source_excerpt='')])
    c=deepcopy(reference_catalog(v)['numeric_facts'][0]);c['axis']=name;o['citations']=[c]
    return v,b,o,{ref:time}


def test_actual_unchanged_mu_raw_diagnostic_only():
    root=Path(__file__).resolve().parents[3];old=root/'maintenance/20261110-c22j-approved'
    raw=(old/'live/MU/private/response.json').read_bytes();before=hashlib.sha256(raw).hexdigest()
    assert before=='b53cea0f3c682312badddff1a7139b726dbaff25672343c514e104f3713804e4'
    p=json.loads((old/'instruction/source_previews/MU.json').read_bytes())
    result=validate(p['source_view'],p['source_binding'],raw,p['temporal'])
    assert result['citations']==json.loads(raw)['citations']
    assert result['newbuyer_fundamental_attractiveness']['refs']==json.loads(raw)['newbuyer_fundamental_attractiveness']['refs']
    assert hashlib.sha256((old/'live/MU/private/response.json').read_bytes()).hexdigest()==before
    assert json.loads((old/'live/MU/RESULT.json').read_bytes())['state']=='REJECTED_STOP_NO_RETRY'


def test_prose_embedded_caveat_and_nonliteral_independent_explanation():
    v,b,o,t=supported();before=deepcopy(o);a=validate(v,b,o,t)
    assert o==before and a['newbuyer_fundamental_attractiveness']['pro']==before['newbuyer_fundamental_attractiveness']['pro']
    assert a['newbuyer_fundamental_attractiveness']['refs']==before['newbuyer_fundamental_attractiveness']['refs']


@pytest.mark.parametrize('defect',['unknown_ref','ticker','digest','as_of','source_bytes','no_caveat','wrong_caveat_ref','forged_time'])
def test_original_source_time_gates_stay_hard(defect):
    v,b,o,t=supported();name='newbuyer_fundamental_attractiveness'
    if defect=='unknown_ref':o[name]['refs'].append('made-up')
    if defect=='ticker':o['ticker']='OTHER'
    if defect=='digest':o['input_digest']='0'*64
    if defect=='as_of':o[name]['as_of']='2026-01-01T00:00:00Z'
    if defect=='source_bytes':v['technical']['evidence'][0]['value']=999
    if defect=='no_caveat':o[name]['temporal_limitations']=[]
    if defect=='wrong_caveat_ref':o[name]['temporal_limitations']=['wrong-ref: '+next(iter(t.values()))['caveat']]
    if defect=='forged_time':
        o['research_mode']='POINT_IN_TIME'
        for x in t.values():x.update(research_mode='POINT_IN_TIME',direction_anchor_temporally_eligible=True,caveat='PIT_AVAILABLE')
        o[name]['temporal_limitations']=['PIT_AVAILABLE']
    with pytest.raises(ValueError):validate(v,b,o,t)


@pytest.mark.parametrize('defect',['duplicate_raw','wrong_path','empty_explanation','valuation_only','unproven_cause','occurred_risk'])
def test_support_and_economic_use_not_relaxed(defect):
    v,b,o,t=supported();name='newbuyer_fundamental_attractiveness'
    if defect=='duplicate_raw':
        v['financial_observations'][0]['original_fields']['original_raw_sha256']=v['valuation'][0]['original_fact']['raw_sha256']
        b['research_view_sha256']=digest(encoded(v));o['input_digest']=b['research_view_sha256']
    if defect=='wrong_path':o[name]['independent_economic_support'][0]['path']='fields.made_up'
    if defect=='empty_explanation':o[name]['independent_economic_support'][0]['statement_fragment']=' '
    if defect=='valuation_only':o[name]['independent_economic_support']=[];o['citations']=[]
    if defect=='unproven_cause':o[name]['claim_role']='VERIFIED_CAUSAL_FACT'
    if defect=='occurred_risk':o['structural_risk']='OBSERVED_RISK'
    with pytest.raises(ValueError):validate(v,b,o,t)


def test_citation_union_still_runs_valuation_time_checks():
    v,b,o,ref=sample();o['newbuyer_fundamental_attractiveness'].update(state='NEUTRAL',refs=[],pro=['Valuation context only.'])
    c=next(c for c in reference_catalog(v)['numeric_facts'] if c['ref']==ref)
    o['citations']=[dict(c,axis='newbuyer_fundamental_attractiveness')]
    time=source_bound_temporal(v,ref,mode=o['research_mode'],prepared_at='2026-11-09T14:10:00Z')
    o['newbuyer_fundamental_attractiveness']['temporal_limitations']=[ref+': '+time['caveat']]
    a=validate(v,b,o,{ref:time});assert a['newbuyer_fundamental_attractiveness']['refs']==[]
    with pytest.raises(ValueError):validate(v,b,o,{})
    o['citations'][0]['ref']='unknown'
    with pytest.raises(ValueError):validate(v,b,o,{ref:time})


def decimal_fixture(source_value):
    v,b,o,_=sample();v['financial_numeric_catalog'][0]['value']=source_value
    v['financial_observations'][0]['original_fields']['prior_comparable_value']=source_value
    b['research_view_sha256']=digest(encoded(v));o['input_digest']=b['research_view_sha256']
    o['citations']=[dict(reference_catalog(v)['numeric_facts'][0],axis='newbuyer_fundamental_attractiveness')]
    return v,b,o


def test_lossless_numeric_string_and_json_number_both_allowed_no_rewrite():
    v,b,o=decimal_fixture('1.25');assert validate(v,b,o,{})['citations'][0]['value']=='1.25'
    o['citations'][0]['value']=1.25
    assert validate(v,b,encoded(o),{})['citations'][0]['value']==1.25
    assert v['financial_numeric_catalog'][0]['value']=='1.25'
    # Raw JSON decimal lexemes are checked before float parsing can erase a wrong trailing amount.
    bad=encoded(o).replace(b'"value":1.25',b'"value":1.25000000000000000001')
    with pytest.raises(ValueError):validate(v,b,bad,{})


@pytest.mark.parametrize('field,value',[('value',1.26),('value','NaN'),('value',True),('unit','USD'),('period','wrong'),('basis','wrong')])
def test_numeric_precision_and_tuple_drift(field,value):
    v,b,o=decimal_fixture('1.25');o['citations'][0][field]=value
    with pytest.raises(ValueError):validate(v,b,o,{})


def test_no_citation_high_confidence_prose_numeric_blind_spots_report_only():
    v,b,o,_=sample();o['citations']=[];o['newbuyer_fundamental_attractiveness']['statement']='Unverified prose figure 9999 needs review.'
    a=validate(v,b,o,{});review=split_quality_review(a,view=v)
    assert a['newbuyer_fundamental_attractiveness']['confidence']=='HIGH'
    assert 'NO_STRUCTURED_NUMERIC_CITATIONS_REVIEW' in review['flags']
    assert any('FREE_PROSE_NUMERIC' in x for x in review['flags'])
    assert any('CONFIDENCE_CALIBRATION' in x for x in review['flags'])
    assert review['report_only'] and not review['prose_truth_proven']


def test_unfavorable_timing_requires_source_but_not_technical_only():
    v,b,o,_=sample();o['newbuyer_entry_timing'].update(refs=[],pro=['No automatic rejection based on label alone.'])
    with pytest.raises(ValueError):validate(v,b,o,{})
    o['newbuyer_entry_timing']['refs']=['financial'];assert validate(v,b,o,{})


@pytest.mark.parametrize('lexeme',['1e1000','1e-1000','1.25000000000000000001'])
def test_raw_decimal_must_not_overflow_underflow_or_round_on_decode(lexeme):
    v,b,o=decimal_fixture(lexeme)
    assert validate(v,b,encoded(o),{})['citations'][0]['value']==lexeme
    raw=encoded(o).replace(('"value":"'+lexeme+'"').encode(),('"value":'+lexeme).encode())
    with pytest.raises(ValueError):validate(v,b,raw,{})
