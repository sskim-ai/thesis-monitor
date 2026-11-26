"""C61 production B2 boundary probes, not model judgments or live source runs."""
from copy import deepcopy

import pytest

from app.services import new_buyer_base_contract as base
from app.services import new_buyer_request_owner as owner
from app.services import new_buyer_v2_contract as contract
from app.services.canonical_monitoring_input import economic_context
from app.services.cross_market_decision_engine_service import canonical_fact_statement
from app.services.unified_snapshot_contract import digest
from app.services.canonical_subject_preflight import synthetic_shape_probe
from app.services.detailed_stock_message_v2 import _entry_lines, _judgment_text
from tests.test_newbuyer_b2_v2 import inputs


def outputs(req):
    return [synthetic_shape_probe(branch) for branch in req['output_schema']['anyOf']]


def request(**kwargs):
    args = inputs(**kwargs)
    first = args['v1_request']
    first['subject']['economic_context'] = dict(observations=[
        dict(ref_id='source:comparison', kind='REPORTED_COMPARISON',
             as_of='2026-09-30', observation=dict(metric='revenue', current_value=120,
                 prior_comparable_value=100, currency='USD'))], relationships=[])
    first['output_schema'] = base.output_schema(first['subject'])
    first['request_sha256'] = digest({k:v for k,v in first.items() if k != 'request_sha256'})
    return owner.build_request(**args)


@pytest.mark.parametrize('overall,negative', [('BUY',False),('BUY',True),('HOLD',False),('HOLD',True)])
def test_supportive_allows_both_grounded_stances(overall, negative):
    req = request(overall=overall, negative=negative)
    data = owner.provider_payload(req, expected_request_sha256=req['request_sha256'])['input']
    assert data['business_gate']['v2_business_gate_pass']
    rows = [row for row in outputs(req) if row['valuation_context']['state']=='SUPPORTIVE']
    assert {row['new_buyer'] for row in rows} == {'ATTRACTIVE','WAIT'}
    for row in rows:
        row['economic_reason'] = ('공시 매출 개선은 현재 가격을 뒷받침하지만 수익화의 현금 전환 여부가 중요합니다.'
                                  if row['new_buyer']=='WAIT' else '공시 매출 개선과 현재 평가 부담을 함께 고려할 때 투자 가치가 있습니다.')
        row['valuation_context']['business_evidence_refs'] = ['business:p']
        if row['new_buyer']=='WAIT':
            row['reason_evidence_refs'] = ['source:comparison']
        assert owner.validate_result({'new_buyer_shadow':row},req,
            expected_request_sha256=req['request_sha256'])['status']=='PASS'
        lines, refs = _entry_lines(row, data, None, 'us', '2026-09-30')
        decision = dict(overall_direction=overall, directional_buy_score=5,
                        confidence='MEDIUM', holder='HOLDABLE', holder_reason='보유 축 유지')
        rendered = _judgment_text(decision, contract.presentation_plan(row, data), lines)
        assert row['economic_reason'] in rendered and '보유자: HOLD' in rendered
        assert 'business:p' in refs and len(rendered.encode('utf-16-le')) // 2 <= 4096
        if row['new_buyer']=='WAIT':
            bad=deepcopy(row)
            bad['reason_evidence_refs']=['unowned:ref']
            assert owner.validate_result({'new_buyer_shadow':bad},req,
                expected_request_sha256=req['request_sha256'])['status']=='FAIL'


@pytest.mark.parametrize('kwargs,expected', [
    ({'overall':'SELL'}, {'WAIT'}),
    ({'overall':'HOLD','positive':False}, {'WAIT'}),
    ({'overall':'HOLD','negative':True,'risk':True}, {'AVOID'}),
    ({'overall':'HOLD','denied':('PER','FORWARD_PE')}, {'WAIT'}),
    ({'overall':'HOLD','business_denial':True,'exact_link':True}, {'WAIT'}),
    ({'overall':'HOLD','confidence':True}, {'WAIT'}),
])
def test_existing_economic_denials_survive(kwargs, expected):
    req = request(**kwargs)
    assert {row['new_buyer'] for row in outputs(req)} == expected


def test_matched_margin_context_not_new_directional_ref():
    fields=dict(period_start='2026-07-01',period_end='2026-09-30',
        prior_period_start='2025-07-01',prior_period_end='2025-09-30',
        period_type='single_quarter',currency='USD',statement_basis='CFS',
        issuer_id='issuer:fixture',source_ticker='FIXTURE',source_receipt='filing:fixture')
    facts=[dict(fact_id='earnings_comparison:'+metric,fact_type='earnings_comparison',
        as_of_date=fields['period_end'],interpretation_eligible=True,
        fields=dict(fields,metric=metric,current_value=current,prior_comparable_value=prior))
        for metric,current,prior in [('revenue',150,100),('operating_income',12,10)]]
    rows=[dict(ref_id='canonical:'+fact['fact_id'],as_of=fact['as_of_date'],
        statement=canonical_fact_statement(fact),source_time={'canonical_fact_sha256':digest(fact)})
        for fact in facts]
    context=dict(decision_evidence=rows,source_use_projection={'source_permissions':[
        dict(ref_id=row['ref_id'],allowed_uses=['CONTEXT']) for row in rows]})
    view=dict(ticker='FIXTURE',packet={'stocks':[dict(ticker='FIXTURE',fact_catalog=facts)]})
    result=economic_context(view,context,{})
    assert len(result['observations'])==2
    relation,=result['relationships']
    assert (relation['prior_pct'],relation['current_pct'],relation['change_pp'])==(10,8,-2)
    assert set(relation['source_refs'])=={row['ref_id'] for row in rows}
    assert relation['scope']=='DERIVED_CONTEXT_NOT_INDEPENDENT_DIRECTION'
    compact = dict(context, decision_evidence=[{k:v for k,v in r.items() if k!='source_time'} for r in rows])
    assert economic_context(view, compact, {})['relationships']==[]
    assert economic_context(view, compact, {}, original_rows=rows)==result
    for key, changed in [('ref_id','unknown'),('as_of','2025-09-30'),('statement','other')]:
        changed_parent = [dict(rows[0], **{key:changed}), rows[1]]
        assert economic_context(view, compact, {}, original_rows=changed_parent)['relationships']==[]
    assert economic_context(view, compact, {}, original_rows=[dict(rows[0],source_time={}),rows[1]])['relationships']==[]
    context['source_use_projection']['source_permissions'][1]['allowed_uses']=[]
    assert economic_context(view,context,{})['relationships']==[]
    assert economic_context(view,compact,{},original_rows=rows)['relationships']==[]


def test_supplement_is_exact_security_context_only():
    projection = {'fields': []}
    field = dict(ticker='TEST', canonical_security_id='id:A', metric='cash_and_cash_equivalents',
                 value=10, context_eligible=True, source_use='ABSOLUTE_CONTEXT_ELIGIBLE',
                 period_role='point_in_time', period_end='2026-09-30', current_prior_role='current')
    def observed(row, *, bridge=False):
        stock = dict(ticker='TEST', fact_catalog=[], reported_absolute_context_fields=[row])
        owner = dict(monitored_security='TEST', selected_projection_sha256=digest(projection), bridge_receipt=bridge)
        return economic_context(dict(ticker='TEST', packet={'stocks':[stock]}, selected_financial_owner=owner,
                                     projection=projection, valuation_view={'security_id':'id:A'}),
                                dict(decision_evidence=[], source_use_projection={'source_permissions':[]}), {})
    valid = dict(field, normalized_hash=digest(field))
    result = observed(valid)
    assert [r['kind'] for r in result['observations']] == ['REPORTED_ABSOLUTE_CONTEXT_ONLY']
    assert result['relationships'] == []
    assert not observed(dict(valid, value=11))['observations']
    for change in ({'canonical_security_id':'id:B'}, {'quality_errors':['ambiguous']}, {'source_use':'DENIED'}):
        bad = dict(field, **change)
        assert not observed(dict(bad, normalized_hash=digest(bad)))['observations']
    assert not observed(valid, bridge=True)['observations']
