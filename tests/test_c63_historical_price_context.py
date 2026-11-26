"""C63 existing-candidate and stance boundary probes; no Source or model calls."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import new_buyer_base_contract as base
from app.services import new_buyer_request_owner as owner
from app.services import new_buyer_v2_contract as contract
from app.services.new_buyer_input_owner import absolute_discount, historical_price_context
from app.services.detailed_stock_message_v2 import _historical_price_row
from app.services.unified_snapshot_contract import digest
from scripts.m12co_entry_range_contract import MethodFamily, _candidate
from scripts.m12ds_r2_ranges import valuation_policy
from scripts import m12ds_r3_schemas as r3
from tests.test_c61_economic_judgment import outputs
from tests.test_m12ds_r2_judgment_policy import capability
from tests.test_newbuyer_b2_v2 import inputs


def context(price, ticker='SYN_A', *, both=True, basis='RESOLVED'):
    items = []
    for method, lo, hi in (
            (MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE, 12, 16),
            (MethodFamily.HISTORICAL_PB_QUANTILE, 7, 9)):
        if not both and method == MethodFamily.HISTORICAL_PB_QUANTILE:
            continue
        suffix = 'pe' if method == MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE else 'pb'
        items.append(_candidate(ticker=ticker, method_family=method, band_name='P50_P75',
            denominator_name='reported-per-share', denominator=Decimal(10),
            denominator_ref='source:denominator:'+suffix, low_multiple=Decimal(lo),
            high_multiple=Decimal(hi), history_ref='source:history:'+suffix,
            basis_refs=('source:basis:'+suffix,), currency=price['currency'],
            assumptions=('historical descriptive reference',), generally_meaningful_archetypes=(),
            conditionally_meaningful_archetypes=(), current_price=price))
    subject = dict(ticker=ticker, current_price=price, fundamental_candidates=items)
    classification = dict(archetype='STRUCTURAL_CYCLICAL_LEADER', valuation_regime_tier='BASE')
    ranges = valuation_policy(subject,classification,{'state':basis},historical_context_only=True)
    refs = sorted({ref for row in items for ref in row['evidence_refs']})
    return dict(ticker=ticker, current_price=price, r2_valuation=ranges,
                r2_eligible_range_catalog={'fundamental_candidates':items},
                source_use_projection={'source_permissions':[
                    dict(ref_id=ref, allowed_uses=['VALUATION']) for ref in refs]})


def test_b_discount_is_descriptive_and_conflict_preserves_methods():
    quote = dict(value=100, currency='USD', as_of='2026-10-01', basis='regular_close')
    ctx = context(quote)
    assert ctx['r2_valuation']['method_conflict']
    assert not ctx['r2_valuation']['fundamental_valid']
    history = historical_price_context(ctx)
    assert {r['relation_to_price'] for r in history['candidates']} == {'BELOW','ABOVE'}
    single = context(quote,both=False)
    assert single['r2_valuation']['below_reference_range']
    assert single['r2_valuation']['fundamental_valid']
    assert not single['r2_valuation']['compensating_discount']
    assert absolute_discount(single) is None
    cap,*_ = capability(-2,risk=True)
    cap.update(sell_eligible=[],current_stress=[])
    assert cap['holder_risk']
    schema = r3.decision_schema(cap,single['r2_valuation'],{})
    assert {b['properties']['new_buyer']['enum'][0]
            for b in schema['properties']['new_buyer_axis']['anyOf']} == {'AVOID'}
    assert historical_price_context(context(quote,basis='UNRESOLVED')) is None
    bad = deepcopy(single)
    bad['source_use_projection']['source_permissions'][0]['prohibited_uses']=['VALUATION']
    assert historical_price_context(bad) is None


def request(**kwargs):
    args = inputs(**kwargs)
    first = args['v1_request']
    sub = first['subject']
    sub['economic_context'] = dict(observations=[
        dict(ref_id='source:comparison',kind='REPORTED_COMPARISON',as_of='2026-09-30',
             observation=dict(metric='revenue',current_value=120,prior_comparable_value=100,currency='USD'))],
        relationships=[])
    sub['historical_price_context'] = historical_price_context(context(sub['current_price'],sub['ticker']))
    assert sub['absolute_discount'] is None
    first['output_schema'] = base.output_schema(sub)
    first['request_sha256'] = digest({k:v for k,v in first.items() if k!='request_sha256'})
    return owner.build_request(**args)


@pytest.mark.parametrize('kwargs,stances,selectable', [
    ({'overall':'HOLD','negative':True},{'ATTRACTIVE','WAIT'},True),
    ({'overall':'BUY','risk':True},{'AVOID'},False),
    ({'overall':'SELL'},{'WAIT'},False),
    ({'denied':('PER','FORWARD_PE')},{'WAIT'},False),
])
def test_b2_history_does_not_change_stance_or_grant_new_authority(kwargs,stances,selectable):
    req = request(**kwargs)
    inp = owner.provider_payload(req,expected_request_sha256=req['request_sha256'])['input']
    rows = outputs(req)
    assert {r['new_buyer'] for r in rows} == stances
    assert all(r['economic_price_review']=={'candidate_id':'UNRESOLVED','preferred_boundary':'NONE'} for r in rows)
    target = next(r for r in inp['historical_price_context']['candidates'] if r['relation_to_price']=='BELOW')
    row = next((r for r in rows if r['new_buyer']=='ATTRACTIVE'), rows[0])
    def validate(raw):
        return owner.validate_result({'new_buyer_shadow':raw},req,
            expected_request_sha256=req['request_sha256'])['status']
    # Use the exact existing source refs and keep the C61 decision independent.
    if row['new_buyer']=='ATTRACTIVE':
        row['valuation_context']['business_evidence_refs']=['business:p']
    assert validate(row)=='PASS'
    bad = deepcopy(row)
    bad['economic_price_review']['preferred_boundary']='HIGH'
    assert validate(bad)=='FAIL'
    chosen = deepcopy(row)
    chosen['economic_price_review']={'candidate_id':target['candidate_id'],'preferred_boundary':'LOW'}
    assert validate(chosen)==('PASS' if selectable else 'FAIL')
    unknown = deepcopy(chosen)
    unknown['economic_price_review']['candidate_id']='not-a-source-candidate'
    assert validate(unknown)=='FAIL'
    if selectable:
        assessment = SimpleNamespace(scenario=None,quality='INSUFFICIENT_EVIDENCE')
        rendered = _historical_price_row(inp,chosen,assessment)
        assert '역사적 PER 참고' in rendered.text and '역사적 PBR 참고' in rendered.text
        assert '조건부 경제적 가치 시나리오' in rendered.text
        assert '경제적 선호 가격 상한: $120.00' in rendered.text
        assert '자동 제한 아님' in rendered.text
        assert '관찰 구간' not in rendered.text


def test_preferred_edge_intersects_technical_interval_not_value_lower_bound():
    req = request()
    inp = req['provider_request']['input']
    chosen = next(r for r in outputs(req) if r['new_buyer']=='ATTRACTIVE')
    pe = next(r for r in inp['historical_price_context']['candidates']
              if r['method_family']=='HISTORICAL_TRAILING_PE_QUANTILE')
    chosen['economic_price_review']={'candidate_id':pe['candidate_id'],'preferred_boundary':'LOW'}
    scenario = dict(currency='USD',evidence_ref='entry:zone',rr2_intersection='DISPLAYABLE',
                    rr2_low=105,rr2_high=135)
    inp['selected_entry_scenario']=scenario
    row = _historical_price_row(inp,chosen,SimpleNamespace(scenario=scenario,quality='SUPPORTED'))
    assert '$105.00–$120.00' in row.text
    assert 'entry:zone' in row.source_fact_ids
    blocked = _historical_price_row(inp,chosen,SimpleNamespace(scenario=scenario,quality='BLOCKED'))
    assert '관찰 구간' not in blocked.text
