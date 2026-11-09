from copy import deepcopy
import json
import pytest

from app.services.dated_research_model import digest, encoded
from app.services.dated_research_review_v2 import (
    CONTRACT, temporal_record, operating_margin, comparison_semantics, replay_occurrence,
    validate_split, compact_evidence, render_numeric_citations, replay_context,
)

CUT = '2026-11-06T03:32:08.304067+00:00'


def fixture():
    view = dict(ticker='SYNTHETIC', as_of=CUT, financial_observations=[], financial_numeric_catalog=[],
        valuation=[dict(source_locator='valuation-ref', value=9, original_fact=dict(value=9, unit='multiple',
            retrieval_timestamp='2026-11-07T00:00:00Z', metric_semantic='PROVIDER_FORWARD_PE'))],
        technical=dict(evidence=[dict(ref_id='price-ref', value=100, numeric_prose_eligible=True, as_of=CUT,
            unit='USD', current_price_qualified=False)]), business_mechanism=dict(source_context=[]),
        structural_risk=dict(occurred_risk_assertion=False),
        dated_price_structure=dict(source_sha256='sr-ref', as_of=CUT, SR={}))
    axis = dict(state='ATTRACTIVE', confidence='HIGH', statement='Synthetic evidence-specific opinion.',
        refs=['price-ref'], pro=['price-ref'], con=[], unknown=['Causal mechanism unverified; no forced confidence cap.'],
        as_of=CUT, temporal_limitations=['DATED_PRICE_NOT_CURRENT'])
    output = dict(contract=CONTRACT, ticker=view['ticker'], input_digest=digest(encoded(view)),
        research_mode='RETROSPECTIVE_DATED_RESEARCH', newbuyer_fundamental_attractiveness=axis,
        newbuyer_entry_timing={**deepcopy(axis), 'state':'UNFAVORABLE'}, structural_risk='POTENTIAL_EXPOSURE',
        thesis_comparison='NOT_COMPARED_TO_REGISTERED_THESIS', NO_SEND=True, Strict_NATIVE_STAGE_READY=False)
    return view, dict(research_view_sha256=digest(encoded(view)), byte_binding_verified=True), output


@pytest.mark.parametrize('fundamental,timing', [('ATTRACTIVE','UNFAVORABLE'), ('UNATTRACTIVE','FAVORABLE'),
    ('UNKNOWN','WAIT_FOR_CONFIRMATION'), ('NEUTRAL','UNKNOWN')])
def test_independent_axes_no_label_or_confidence_coercion(fundamental, timing):
    view, binding, output = fixture()
    output['newbuyer_fundamental_attractiveness']['state'] = fundamental
    output['newbuyer_entry_timing']['state'] = timing
    result = validate_split(output, view=view, binding=binding, temporal={})
    assert result['newbuyer_entry_timing']['state'] == timing
    assert result['newbuyer_fundamental_attractiveness']['confidence'] == 'HIGH'
    assert view['technical']['evidence'][0]['current_price_qualified'] is False


@pytest.mark.parametrize('mutation', ['ticker','sha','ref','observed_risk'])
def test_split_corruption_rejected(mutation):
    view, binding, output = fixture()
    if mutation == 'ticker': output['ticker'] = 'OTHER'
    if mutation == 'sha': binding['research_view_sha256'] = '0'*64
    if mutation == 'ref': output['newbuyer_entry_timing']['refs'] = ['unknown-ref']
    if mutation == 'observed_risk': output['structural_risk'] = 'OBSERVED_RISK'
    with pytest.raises(ValueError): validate_split(output, view=view, binding=binding, temporal={})


def test_temporal_pit_retro_and_estimate_vintage():
    fact = dict(retrieval_timestamp='2026-11-07T00:00:00Z', metric_asof=None,
        estimate_vintage='2026-10-01', reference_price_as_of='2026-10-23', price_basis='UNADJUSTED')
    pit = temporal_record(fact, cutoff=CUT, prepared_at='2026-11-08T00:00:00Z', mode='POINT_IN_TIME')
    retro = temporal_record(fact, cutoff=CUT, prepared_at='2026-11-08T00:00:00Z', mode='RETROSPECTIVE_DATED_RESEARCH')
    assert not pit['direction_anchor_temporally_eligible']
    assert retro['direction_anchor_temporally_eligible']
    assert retro['issuer_estimate_vintage'] != retro['retrieved_at']
    view, binding, output = fixture()
    axis = output['newbuyer_entry_timing']; axis.update(refs=['valuation-ref'], pro=['valuation-ref'])
    output['research_mode'] = 'POINT_IN_TIME'
    with pytest.raises(ValueError): validate_split(output, view=view, binding=binding, temporal={'valuation-ref':pit})
    output['research_mode'] = 'RETROSPECTIVE_DATED_RESEARCH'
    axis['temporal_limitations'] = [retro['caveat']]
    assert validate_split(output, view=view, binding=binding, temporal={'valuation-ref':retro})
    with pytest.raises(ValueError):
        temporal_record(fact, cutoff=CUT, prepared_at=CUT, mode='POINT_IN_TIME')
    fact['retrieval_timestamp'] = '2026-11-05T00:00:00Z'
    assert not temporal_record(fact, cutoff=CUT, prepared_at=CUT, mode='POINT_IN_TIME')['direction_anchor_temporally_eligible']


def operands():
    row = dict(issuer_id='generic-issuer', statement_basis='consolidated', period_start='2026-04-01',
        period_end='2026-06-30', period_type='single_quarter', currency='USD', unit='USD', unit_scale=1,
        raw_verified=True, scale_verified=True, consolidation_explicitly_proven=True)
    return dict(row, ref='r', value=100, metric='revenue'), dict(row, ref='o', value=-10, metric='operating_income')


@pytest.mark.parametrize('field,value', [('unit','KRW'),('period_type','YTD'),('period_start','2026-01-01'),
    ('statement_basis','separate'),('unit_scale',1000),('issuer_id','other')])
def test_margin_scope_and_scale_corruption(field, value):
    r, o = operands(); o[field] = value
    assert operating_margin(r, o)['value'] is None


def test_margin_receipt_and_missing_scale_no_estimated_correction():
    r, o = operands(); result = operating_margin(r,o)
    assert result['value'] == '-10.0' and result['source_refs'] == ['r','o']
    assert result['direction_grant'] is False
    r['scale_verified'] = 'UNKNOWN'; assert operating_margin(r,o)['value'] is None
    r['scale_verified'] = True; r['value'] = 0; assert operating_margin(r,o)['value'] is None


def test_period_quarter_ytd_and_53_52_no_adjustment():
    f = dict(period_type='annual', period_start='2025-08-29', period_end='2026-09-03',
        prior_period_start='2024-08-30', prior_period_end='2025-08-28', fiscal_comparability=dict(
            contract='ISSUER_DECLARED_52_53_WEEK_ANNUAL_COMPARABLE', value_adjustment=None))
    assert comparison_semantics(f) is True
    f['fiscal_comparability']['value_adjustment'] = '53/52'
    assert comparison_semantics(f) == 'UNKNOWN'
    f['period_type'] = 'single_quarter'; assert comparison_semantics(f) == 'UNKNOWN'


def test_raw_sha_issuer_and_request_binding():
    payload = dict(cik=1, facts={'us-gaap':{'Revenue':{'units':{'USD':[
        dict(accn='filing', start='2026-01-01', end='2026-03-31', val=100)]}}}})
    raw = encoded(payload); receipt = dict(raw_sha256=digest(raw),HTTP_status=200,plan_sha256='plan')
    lineage = dict(concept='Revenue', taxonomy='us-gaap', currency='USD', issuer_cik=1,
        source_payload_sha256=digest(raw), receipt='filing', amount=100, amount_period_start='2026-01-01',
        amount_period_end='2026-03-31',statement_basis='sec_companyfacts_entity_wide')
    assert replay_occurrence(raw,receipt,dict(plan_sha256='plan'),lineage)['unit_scale'] == 1
    for changed in [dict(lineage,issuer_cik=2),dict(lineage,amount_period_start='2026-02-01')]:
        with pytest.raises(ValueError): replay_occurrence(raw,receipt,dict(plan_sha256='plan'),changed)
    with pytest.raises(ValueError): replay_occurrence(raw+b' ',receipt,dict(plan_sha256='plan'),lineage)


def test_compact_full_numeric_contract_and_negative_equity_positive_pbr_not_inverted():
    view, _, _ = fixture(); compact, full = compact_evidence(view)
    assert compact['evidence'] == view
    assert compact['reference_catalog']['numeric_facts'] == full['numeric_facts']
    fact = full['numeric_facts'][0]; output = dict(citations=[dict(fact,axis='valuation')])
    rendered = render_numeric_citations(output, full, view)
    assert rendered[0]['value'] == 9 and rendered[0]['FY1_caveat']
    assert rendered[0]['original_scale'] == 'UNKNOWN'
    for key in ('value','unit','period','basis','ref'):
        bad = deepcopy(output); bad['citations'][0][key] = 'corrupt'
        with pytest.raises(ValueError): render_numeric_citations(bad,full,view)
    # Negative equity and a positive provider PBR remain separate facts, never a synthetic denominator.
    assert operating_margin(dict(equity=-1),dict(PBR=9))['value'] is None


def test_dart_existing_period_parser_and_context_unknown_scale():
    from app.services.kr_financial_lineage_service import opendart_field_lineage
    row = dict(corp_code='generic-corp',rcept_no='filing',reprt_code='11012',bsns_year='2026',
        sj_div='IS',account_id='ifrs-full_Revenue',account_nm='Revenue',account_detail='-',ord='1',
        thstrm_amount='1000',frmtrm_q_amount='900',currency='KRW')
    request = dict(plan_sha256='plan',params=dict(corp_code='generic-corp',fs_div='CFS',reprt_code='11012',bsns_year=2026))
    raw=encoded(dict(list=[row])); receipt=dict(raw_sha256=digest(raw),HTTP_status=200,plan_sha256='plan')
    lineage=opendart_field_lineage(row,logical_field='revenue',report_code='11012',source_column='thstrm_amount',selected=True,requested_fs_div='CFS')
    result=replay_occurrence(raw,receipt,request,lineage)
    assert result['period_and_unit_scale_verified']=='UNKNOWN'
    fields=dict(original_raw_sha256=digest(raw),metric='revenue',currency='KRW',statement_basis='consolidated',
        period_start='2026-04-01',period_end='2026-06-30',current_value=1000,source_occurrences=[lineage['source_row_identity']])
    assert replay_context(raw,receipt,request,fields)['matches']==1
    for change in [dict(lineage,amount_period_start='2026-01-01'),dict(lineage,currency='USD'),dict(lineage,statement_basis='separate')]:
        with pytest.raises(ValueError): replay_occurrence(raw,receipt,request,change)


def test_derived_price_session_extracted_not_retrieval_backdated():
    fact=dict(retrieval_timestamp='2026-11-07T00:00:00Z',estimate_vintage='2026-10-14',
        basis=json.dumps(dict(price=dict(session='2026-10-23',basis='UNADJUSTED'))))
    time=temporal_record(fact,cutoff=CUT,prepared_at='2026-11-08T00:00:00Z',mode='RETROSPECTIVE_DATED_RESEARCH')
    assert time['reference_price_as_of']=='2026-10-23'
    assert time['reference_price_basis']=='UNADJUSTED'


def test_final_consolidation_boundary_and_original_mode_conflict():
    r,o=operands();o['consolidation_explicitly_proven']=False
    assert operating_margin(r,o)['state']=='DERIVATION_BLOCKED_CONSOLIDATION_UNPROVEN'
    view,binding,output=fixture();view['research_mode']='POINT_IN_TIME'
    binding['research_view_sha256']=digest(encoded(view));output['input_digest']=binding['research_view_sha256']
    with pytest.raises(ValueError,match='original_research_mode_conflict'):
        validate_split(output,view=view,binding=binding,temporal={})


def test_boolean_numeric_not_equal_to_zero_or_one():
    view,_,_=fixture();view['valuation'][0]['original_fact']['value']=1;view['valuation'][0]['value']=1
    _,full=compact_evidence(view);fact=full['numeric_facts'][0]
    output=dict(citations=[dict(fact,axis='valuation',value=True)])
    with pytest.raises(ValueError,match='exact_numeric_citation_mismatch'):
        render_numeric_citations(output,full,view)
