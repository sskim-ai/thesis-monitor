"""Fictional ownership and branch probes. No provider/model requests."""
from copy import deepcopy
from itertools import product
import json
from pathlib import Path

import pytest

from scripts import newbuyer_b2_contract as v1
from scripts import newbuyer_b2_v2_contract as v2
from scripts import newbuyer_b2_v2_policy as policy
from scripts import newbuyer_b2_v2_shadow as shadow
from scripts.kis_eps_wire_calibration import digest, sealed
from scripts.newbuyer_fper_prerequisite_scope import CATEGORIES, blocker_census
from tests.test_newbuyer_b2_contract import subject as base_subject, instantiate


def claim(ref, evidence):
    return dict(claim_ref=ref,claim=dict(text='Current observed '+ref,evidence_refs=[evidence]),
                parent_source_refs=['same-parent'])


def inputs(*, denied=(), risk=False, timing='FAVORABLE_NOW', business_denial=False,
           exact_link=False, independent=False, overall='BUY', negative=False,
           positive=True, legacy=True, confidence=False):
    sub = base_subject()
    sub.update(source_generation_id='fictional-generation',frozen_authority={'core':'fixture-core',
        'pass_a':'fixture-a','accepted_b':'fixture-b','context':'fixture-source'})
    sub['facts'] = {f'valuation:{m}':dict(metric=m,asset_relevance_proven=False,
        ticker=sub['ticker'],security_id=sub['security_id'],metadata={'value':10})
        for m in ('PER','FORWARD_PE') if m not in denied}
    sub['frozen_overall'] = overall
    cap = sub['capability']
    cap.update(positive=['business:p'] if positive else [],negative=['business:n'] if negative else [],
        holder_risk=['business:r'] if risk else [],confidence=['legacy:c'] if legacy else [],quality=[])
    if independent:
        cap['positive'].append('business:independent')
    if timing == 'WAIT_FOR_ZONE':
        sub['current_price']['value'] = 120
    elif timing == 'UNRESOLVED':
        sub['selected_tactical_candidate'] = 'absent'
    sub['frozen_business_claims'] = [claim(r,'business-quality:exact' if exact_link and r=='business:p'
        else 'source:'+r) for r in sorted(set(cap['positive']+cap['negative']+cap['holder_risk']+cap['confidence']))]
    records = []
    for c in sub['frozen_business_claims']:
        if c['claim_ref'] == 'legacy:c':
            c['claim']['text'] = 'LEGACY CONFIDENCE PROSE MUST NOT ENTER MODEL INPUT'
            records.append(dict(ticker=sub['ticker'],claim_ref=c['claim_ref'],effect='CONFIDENCE_ONLY',
                existing_materiality='CONTEXT_ONLY',legacy_claim_sha256=digest(c)))
    cells = []
    for metric in ('PER','FORWARD_PE','SELECTED_REPORTED_BUSINESS'):
        ref = 'business-quality:exact' if metric=='SELECTED_REPORTED_BUSINESS' else 'valuation:'+metric
        for category in (('BUSINESS_SOURCE_QUALITY',) if metric=='SELECTED_REPORTED_BUSINESS' else CATEGORIES):
            bad = (business_denial if metric=='SELECTED_REPORTED_BUSINESS' else
                   metric in denied and category=='VALUATION_SOURCE_QUALITY')
            cells.append(dict(category=category,metric=metric,metric_ref=ref,required=True,
                coverage_disposition='PROVEN_APPLICABLE',coverage_proof_kind='COMPOSED_TYPED_OWNER',
                owner_state='DENIED' if bad else 'QUALIFIED',owner_contract='fictional-current-owner',
                owner_ref='owner:'+ref,owner_decision_version='fictional-v1',owner_field_eligibility={'owned':True},
                owner_as_of='2026-01-02T00:00:00+00:00',owner_temporal_scope='OBSERVED_AT_RETRIEVAL',
                applies_to_metric_refs=[ref],not_applicable_to_metric_refs=[],not_applicable_reason_codes=[],
                denial_reason_codes=['EXPLICIT_TYPED_DENIAL'] if bad else [],input_refs=['input:'+ref],
                input_sha256=digest(ref),scope_level='BUSINESS_GLOBAL' if metric=='SELECTED_REPORTED_BUSINESS'
                else 'METRIC_SCOPED',missing_fields=[]))
    row = sealed(dict(contract='fictional-category-coverage',ticker=sub['ticker'],
        canonical_security_id=sub['security_id'],source_generation=sub['source_generation_id'],
        relevant_valuation_metric_refs=['valuation:PER','valuation:FORWARD_PE'],
        qualified_relevant_valuation_refs=sorted(sub['facts']),categories=cells,
        coverage_complete=True,owner_provenance_complete=True,temporal_provenance_complete=True,
        decision_provenance_complete=True))
    coverage = sealed(dict(contract='REV56COfflineCoverageReproofV1',rows=[row],subjects=1,
        complete_subjects=1,unresolved_required_cells=0,coverage_complete=True,
        owner_provenance_complete=True,temporal_provenance_complete=True,decision_provenance_complete=True))
    census = blocker_census([row],expected_subjects=[sub['ticker']])
    request = dict(contract=v1.CONTRACT,subject=sub,output_schema=v1.output_schema(sub))
    request['request_sha256'] = digest(request)
    owner = sealed(dict(contract=policy.CONFIDENCE,ticker=sub['ticker'],security_id=sub['security_id'],
        source_generation=sub['source_generation_id'],scope='NEWBUYER_GLOBAL',
        category='NEWBUYER_CONFIDENCE_ADMISSIBILITY',state='DENIED',cross_cutting_admissibility=True,
        input_refs=['current-confidence-source'],input_sha256=digest('current-confidence-source'),
        reason_codes=['EXPLICIT_CROSS_CUTTING_ADMISSIBILITY'],proof_type='CURRENT_TYPED_OWNER',
        as_of='2026-01-02T00:00:00+00:00')) if confidence else None
    return dict(enabled=True,v1_request=request,coverage=coverage,census=census,
        coverage_sha=coverage['receipt_sha256'],census_sha=census['receipt_sha256'],
        legacy_records=records,confidence=owner)


def outputs(request):
    return [instantiate(r) for r in request['output_schema']['anyOf']]


def validate(output,request):
    return shadow.validate_result({'new_buyer_shadow':output},request,
                                  expected_request_sha256=request['request_sha256'])


@pytest.mark.parametrize('timing', ['FAVORABLE_NOW','WAIT_FOR_ZONE','UNRESOLVED'])
def test_supportive_is_fundamentally_attractive_independent_of_timing(timing):
    req = shadow.build_request(**inputs(timing=timing))
    rows = outputs(req)
    assert {r['valuation_context']['state'] for r in rows} == {'SUPPORTIVE','NEUTRAL','BURDENSOME'}
    for row in rows:
        assert validate(row,req)['status']=='PASS'
        expected = 'ATTRACTIVE' if row['valuation_context']['state']=='SUPPORTIVE' else 'WAIT'
        assert row['new_buyer']==expected
        assert row['timing_context']['state']==timing
        assert v2.presentation_plan(row,req['provider_request']['input'])['entry_timing']['state']==timing


@pytest.mark.parametrize('overall,pos,neg,risk,timing', product(('BUY','HOLD','SELL'),(False,True),
    (False,True),(False,True),('FAVORABLE_NOW','WAIT_FOR_ZONE','UNRESOLVED')))
def test_complete_business_risk_timing_truth_table(overall,pos,neg,risk,timing):
    req = shadow.build_request(**inputs(overall=overall,positive=pos,negative=neg,risk=risk,timing=timing))
    rows = outputs(req)
    assert all(validate(r,req)['status']=='PASS' for r in rows)
    stances = {r['new_buyer'] for r in rows}
    assert ('ATTRACTIVE' in stances)==(overall=='BUY' and pos and not neg and not risk)
    if risk:
        assert stances=={'AVOID'}


def test_all_metrics_unusable_requires_exact_composite():
    req = shadow.build_request(**inputs(denied=('PER','FORWARD_PE')))
    inp = req['provider_request']['input']
    assert inp['valuation_evaluability']['evaluability_state']=='ALL_RELEVANT_METRICS_UNUSABLE'
    assert inp['all_metrics_unusable_proof']['no_usable_metric_survives']
    assert len(inp['all_metrics_unusable_proof']['exact_blocker_refs'])==2
    assert [(r['new_buyer'],r['reason_class']) for r in outputs(req)]==[('WAIT','VALUATION_UNRESOLVED')]


@pytest.mark.parametrize('denied', [('FORWARD_PE',),('PER',)])
def test_one_unavailable_metric_does_not_block_independent_usable_metric(denied):
    req = shadow.build_request(**inputs(denied=denied))
    inp = req['provider_request']['input']
    assert inp['valuation_evaluability']['evaluability_state']=='EVALUABLE'
    assert len(inp['qualified_usable_valuation_facts'])==1
    assert not inp['all_metrics_unusable_proof_ref']
    assert not inp['business_quality_blocker_refs']
    assert not inp['confidence_veto_refs']


def test_legacy_claims_preserved_but_absent_from_actual_provider_payload():
    args = inputs()
    before = deepcopy(args)
    req = shadow.build_request(**args)
    payload = shadow.provider_payload(req,expected_request_sha256=req['request_sha256'])
    text = json.dumps(payload)
    assert 'legacy:c' not in text and 'LEGACY CONFIDENCE PROSE' not in text
    assert 'CONFIDENCE_UNCERTAINTY' not in payload['input']['allowed_wait_reasons']
    assert req['backend_audit']['legacy_entitlement']['rows'][0]['model_visible_in_b2_v2'] is False
    assert args==before


def test_typed_current_confidence_veto_not_legacy_prose():
    req = shadow.build_request(**inputs(confidence=True))
    assert all(r['reason_class']=='CONFIDENCE_UNCERTAINTY' for r in outputs(req))
    assert all(r['reason_evidence_refs']==req['provider_request']['input']['confidence_veto_refs'] for r in outputs(req))


@pytest.mark.parametrize('exact,independent,blocks', [(False,False,False),(True,False,True),(True,True,False)])
def test_business_quality_requires_exact_gate_linkage_and_surviving_support(exact,independent,blocks):
    req = shadow.build_request(**inputs(business_denial=True,exact_link=exact,independent=independent))
    inp = req['provider_request']['input']
    assert inp['business_gate']['v2_business_gate_pass'] is not blocks
    assert inp['valuation_evaluability']['evaluability_state']=='EVALUABLE'
    rows = outputs(req)
    if blocks:
        assert {r['reason_class'] for r in rows}=={'BUSINESS_EVIDENCE_UNCERTAINTY'}
    else:
        assert any(r['new_buyer']=='ATTRACTIVE' for r in rows)
    if not exact:
        assert req['backend_audit']['blocker_role_policy']['rows'][0]['role']=='CONTEXT_ONLY'


@pytest.mark.parametrize('mutation', ['free_unresolved','timing','unknown_ref','business_as_value',
    'legacy_as_value','blocked_value','free_confidence','free_business','free_prose','duplicate'])
def test_output_rejects_unauthorized_semantics_and_exact_refs(mutation):
    req = shadow.build_request(**inputs(denied=('FORWARD_PE',)))
    row = outputs(req)[0]
    if mutation=='free_unresolved':
        row['valuation_context']['state']='UNRESOLVED'
    elif mutation=='timing':
        row['timing_context']['state']='WAIT_FOR_ZONE'
    elif mutation in ('unknown_ref','business_as_value','legacy_as_value','blocked_value'):
        row['valuation_context']['valuation_evidence_refs']=[{
            'unknown_ref':'missing','business_as_value':'business:p',
            'legacy_as_value':'legacy:c','blocked_value':'valuation:FORWARD_PE'}[mutation]]
    elif mutation in ('free_confidence','free_business'):
        row.update(new_buyer='WAIT',reason_class='CONFIDENCE_UNCERTAINTY' if mutation=='free_confidence'
            else 'BUSINESS_EVIDENCE_UNCERTAINTY',reason_evidence_refs=['legacy:c'])
    elif mutation=='free_prose':
        row['free_rationale']='target price 200'
    else:
        row['valuation_context']['valuation_evidence_refs']*=2
    assert validate(row,req)['status']=='FAIL'


def test_same_metric_qualified_and_denied_without_supersession_is_invalid():
    args = inputs()
    row = deepcopy(args['coverage']['rows'][0])
    cell = next(c for c in row['categories'] if c['metric']=='PER' and c['category']=='VALUATION_SOURCE_QUALITY')
    cell.update(owner_state='DENIED',denial_reason_codes=['EXPLICIT_TYPED_DENIAL'])
    row = sealed({k:v for k,v in row.items() if k!='receipt_sha256'})
    c = sealed({**{k:v for k,v in args['coverage'].items() if k!='receipt_sha256'},'rows':[row]})
    b = blocker_census([row],expected_subjects=[row['ticker']])
    result,metrics,_ = policy.evaluability(args['v1_request']['subject'],row,b,c['receipt_sha256'])
    assert result['evaluability_state']=='INVALID_INCOMPLETE_CONTRACT'
    assert any(r['state']=='INVALID_CONTRADICTORY_OWNERSHIP' for r in metrics)
    args.update(coverage=c,census=b,coverage_sha=c['receipt_sha256'],census_sha=b['receipt_sha256'])
    with pytest.raises(ValueError,match='contradictory'):
        shadow.build_request(**args)


@pytest.mark.parametrize('mutation', ['coverage_sha','census_sha','cross_metric','missing_cell','no_fact',
    'role','confidence_owner','request_identity','legacy_overlap'])
def test_request_fail_closed(mutation):
    args = inputs(denied=('FORWARD_PE',))
    if mutation in ('coverage_sha','census_sha'):
        args[mutation]='0'*64
    elif mutation=='cross_metric':
        args['census']['rows'][0]['affected_metric_refs']=['valuation:PER']
    elif mutation=='missing_cell':
        args['coverage']['rows'][0]['categories'].pop(0)
    elif mutation=='no_fact':
        args['v1_request']['subject']['facts'].clear()
    elif mutation=='role':
        args['census']['rows'][0]['scope_level']='VALUATION_GLOBAL'
    elif mutation=='confidence_owner':
        args['confidence']=inputs(confidence=True)['confidence']
        args['confidence']['category']='BUSINESS_SOURCE_QUALITY'
    elif mutation=='request_identity':
        args['v1_request']['subject']['ticker']='OTHER'
    else:
        args['v1_request']['subject']['capability']['positive'].append('legacy:c')
    with pytest.raises(ValueError):
        shadow.build_request(**args)


def test_zero_facts_without_typed_denial_rejected_even_when_request_resealed():
    args=inputs()
    sub=args['v1_request']['subject']
    sub['facts'].clear()
    args['v1_request']['output_schema']=v1.output_schema(sub)
    args['v1_request']['request_sha256']=digest({k:v for k,v in args['v1_request'].items() if k!='request_sha256'})
    with pytest.raises(ValueError):
        shadow.build_request(**args)


def test_frozen_request_reseal_cannot_replace_expected_identity():
    req=shadow.build_request(**inputs())
    expected=req['request_sha256']
    req['provider_request']['input']['ticker']='OTHER'
    req['request_sha256']=digest(req['provider_request'])
    req=sealed({k:v for k,v in req.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='freeze_drift'):
        shadow.provider_payload(req,expected_request_sha256=expected)


def test_escaped_legacy_prose_cannot_leak_through_valuation_metadata():
    args=inputs()
    sub=args['v1_request']['subject']
    legacy=next(r for r in sub['frozen_business_claims'] if r['claim_ref']=='legacy:c')
    legacy['claim']['text']='Legacy "confidence"\nnot valuation evidence'
    args['legacy_records'][0]['legacy_claim_sha256']=digest(legacy)
    sub['facts']['valuation:PER']['metadata']['unowned_note']=legacy['claim']['text']
    args['v1_request']['output_schema']=v1.output_schema(sub)
    args['v1_request']['request_sha256']=digest({k:v for k,v in args['v1_request'].items() if k!='request_sha256'})
    with pytest.raises(ValueError,match='legacy_model_visibility_leak'):
        shadow.build_request(**args)


def test_default_off_and_no_production_imports_or_ticker_literals():
    assert shadow.build_request() is None
    root=Path(__file__).parents[1]
    for name in ('newbuyer_b2_v2_contract.py','newbuyer_b2_v2_policy.py','newbuyer_b2_v2_shadow.py'):
        text=(root/'scripts'/name).read_text()
        for ticker in ('003690','012450','010120','GOOGL','CORZ','047810'):
            assert ticker not in text
    assert not any('newbuyer_b2_v2' in p.read_text() for p in (root/'app').rglob('*.py'))
