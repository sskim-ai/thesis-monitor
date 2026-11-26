"""C63R1 native response/reference/price boundary probes; no live I/O."""
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest

from app.services import new_buyer_base_contract as base
from app.services import new_buyer_request_owner as owner
from app.services import new_buyer_v2_contract as contract
from app.services.current_fresh_valuation import CurrentMultiple, CurrentValuationView
from app.services.detailed_stock_message_v2 import _historical_price_row, _provider_reference_row
from app.services.new_buyer_input_owner import native_reference_for_b2, append_native_reference_candidates
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots, provider_reference_context
from app.services.provider_valuation_calibration_context import calibration_context, require_direction_isolation
from app.services.unified_snapshot_contract import digest
from scripts.m12co_entry_range_contract import provider_reference_candidates
from scripts.m12ds_r2_ranges import valuation_policy
from tests.rev28_native_fixtures import native_input, security
from tests.test_r9_rev28_native_snapshot import alter
from tests.test_newbuyer_b2_v2 import inputs
from tests.test_c61_economic_judgment import outputs

SESSION = '2026-09-30'


def quarterly():
    return [dict(period=f'{year}-{month}',v=float(10+i))
            for i,(year,month) in enumerate((y,m) for y in range(2023,2027)
                for m in ('03-31','06-30','09-30','12-31')
                if f'{y}-{m}'<=SESSION)]


def raw_reference(ticker='IBM', *, missing_per=False, missing_history=False, wrong_symbol=False,
                  stale=False, run='fictional-snapshot', security_id=None):
    sec = security(ticker)
    if security_id is not None:
        sec['canonical_security_id']=security_id
    wire = native_input(sec,run=run)
    if not ticker.isdigit():
        def change(body):
            body['metric'].update(epsTTM=10,bookValuePerShareQuarterly=20,
                                 peTTM=None if missing_per else 12.3)
            if not missing_history:
                rows = quarterly()
                body['series']={'quarterly':{'peTTM':rows,
                    'pb':[dict(period=r['period'],v=r['v']/10) for r in rows]}}
            if wrong_symbol:
                body['symbol']='OTHER'
            if stale:
                body['isStale']=True
        alter(wire,change)
    else:
        alter(wire,lambda body:body.update(eps='-10',bps='100'))
    snapshots = derive_provider_snapshots(wire,security=sec,run_id=run)
    currency = 'KRW' if ticker.isdigit() else 'USD'
    return wire,sec,snapshots,provider_reference_context(wire,snapshots,currency=currency,as_of=SESSION)


def test_native_direct_and_history_independent_of_own_basis():
    _,_,snapshots,ref = raw_reference(missing_per=True)
    assert ref['scope']=='PROVIDER_NATIVE_REFERENCE_NOT_OWN_DENOMINATOR'
    assert ref['direct'][0]['value']==10
    assert ref['direct'][0]['own_denominator_basis_resolved'] is False
    pe,pb=ref['history']
    assert pe['all']['positive_periods']==len(quarterly())
    assert pe['current_value'] is None and 'current_percentile' not in pe['all']
    assert pb['current_value']==1.5
    assert pb['all']['current_percentile']==round(100*6/len(quarterly()),1)
    candidates=provider_reference_candidates(ref)
    assert len(candidates)==6
    assert {r['origin'] for r in candidates}=={'PROVIDER_QUARTERLY_REFERENCE'}
    assert all(r['provider_formula_exact'] is False for r in candidates)
    assert all(r['current_price_context'] is None for r in candidates)
    assert not any(s.overall_direction_use for s in snapshots)
    assert len(provider_reference_candidates(raw_reference(missing_history=True)[3]))==0


def test_kiwoom_preserves_signed_eps_and_unspecified_period():
    _,_,_,ref=raw_reference('005930')
    assert [(r['field'],r['value']) for r in ref['direct']]==[('eps',-10),('bps',100)]
    assert all(r['period']=='PROVIDER_PERIOD_UNSPECIFIED' for r in ref['direct'])
    assert ref['history']==[] and provider_reference_candidates(ref)==[]
    text=_provider_reference_row({'provider_reference_context':ref}).text
    assert 'EPS(기간 미명시)' in text and 'BPS(기간 미명시)' in text


@pytest.mark.parametrize('kwargs',[{'wrong_symbol':True},{'stale':True}])
def test_native_reference_inherits_identity_and_currentness_denial(kwargs):
    assert raw_reference(**kwargs)[3] is None


def test_quarterly_duplicates_future_conflicts_and_nonpositive_are_visible():
    from app.services.provider_native_valuation_snapshot import _quarterly_reference_summary
    rows=[dict(period='2025-03-31',v=4),dict(period='2025-03-31',v=4),
          dict(period='2025-06-30',v=1),dict(period='2025-06-30',v=2),
          dict(period='2025-09-30',v=-5),dict(period='2025-12-31',v=None),
          dict(period='2027-03-31',v=200),dict(period='bad',v=100)]
    result=_quarterly_reference_summary(rows,as_of=date.fromisoformat(SESSION),current=4)
    assert result['duplicate_rows']==2 and result['future_rows']==1 and result['invalid_date_rows']==1
    all_=result['all']
    assert (all_['observed_periods'],all_['positive_periods'],all_['nonpositive_periods'],
            all_['missing_value_periods'],all_['conflicting_periods'])==(4,1,1,1,1)
    assert all_['current_percentile']==100 and not all_['price_sample_sufficient']


def make_view():
    _,sec,snapshots,reference=raw_reference()
    metrics=tuple(CurrentMultiple(metric=s.metric,status='QUALIFIED',value=s.value,
        numerator=100,numerator_role='CURRENT_PRICE_CONTEXT_ONLY',
        source_method='provider_native_latest_snapshot',
        input_hashes=(s.snapshot_sha256,s.raw_sha256,s.source_receipt_sha256),
        denial_reason=None,display_eligible=True,native_snapshot=s) for s in snapshots)
    metrics+=(CurrentMultiple(metric='fPER',status='UNAVAILABLE',numerator=100,
        source_method='fixture-unavailable',input_hashes=('a'*64,),denial_reason='UNAVAILABLE'),)
    return CurrentValuationView(ticker=sec['ticker'],security_id=sec['canonical_security_id'],
        run_id='fictional-snapshot',currency='USD',price=100,price_session=SESSION,
        price_basis='adjusted_close',price_context_sha256='a'*64,
        security_sha256=digest(sec),financial_projection_sha256='b'*64,
        owner_output_sha256='c'*64,metrics=metrics,provider_reference_context=reference)


def test_view_serialization_and_existing_b2_input_binding():
    view=make_view()
    raw=view.model_dump(mode='json')
    assert CurrentValuationView.model_validate(raw)==view
    old=dict(raw)
    old.pop('provider_reference_context')
    assert CurrentValuationView.model_validate(old).model_dump(mode='json')==old
    cal=calibration_context(view)
    assert 'provider_reference_context' not in cal and not view.metrics[0].entry_use_eligible
    ctx=dict(ticker=view.ticker,valuation_context=cal,
        current_price=dict(value=100,currency='USD',as_of=SESSION,basis='adjusted_close'))
    ref=native_reference_for_b2(ctx,raw)
    assert not ref['quote_basis_comparable'] and ref['direct'][0]['reference_quote_quotient']==10
    ctx['valuation_context']=dict(cal,valuation_view_sha256='a'*64)
    with pytest.raises(ValueError,match='calibration_view_mismatch'):
        native_reference_for_b2(ctx,raw)
    with pytest.raises(ValueError,match='valuation_directional'):
        require_direction_isolation({'provider_reference_context':ref})


@pytest.mark.parametrize('kwargs,stances,selection',[
    ({'overall':'HOLD','negative':True},{'ATTRACTIVE','WAIT'},True),
    ({'risk':True},{'AVOID'},False),
    ({'overall':'SELL'},{'WAIT'},False),
    ({'denied':('PER','FORWARD_PE')},{'WAIT'},False)])
def test_existing_b2_selection_and_no_current_metric_promotion(kwargs,stances,selection):
    args=inputs(**kwargs)
    first=args['v1_request']; sub=first['subject']
    _,_,_,reference=raw_reference(sub['ticker'],run=sub['source_generation_id'],security_id=sub['security_id'])
    reference['quote_basis_comparable']=False
    # Synthetic coverage fixture has different atomic ref names. The new
    # native history rank must not recreate an absent current ratio.
    sub['provider_reference_context']=reference
    sub['economic_context']=dict(observations=[dict(ref_id='source:comparison',
        kind='REPORTED_COMPARISON',as_of=SESSION,observation={'metric':'revenue'})],relationships=[])
    ranges=valuation_policy(dict(ticker=sub['ticker'],current_price=sub['current_price'],
        fundamental_candidates=[]),dict(archetype='DURABLE_FRANCHISE',valuation_regime_tier='BASE'),
        {'state':'UNRESOLVED'},historical_context_only=True)
    context=dict(ticker=sub['ticker'],current_price=sub['current_price'],r2_valuation=ranges)
    sub['historical_price_context']=append_native_reference_candidates(None,reference,context)
    assert sub['absolute_discount'] is None and len(sub['historical_price_context']['candidates'])==6
    first['output_schema']=base.output_schema(sub)
    first['request_sha256']=digest({k:v for k,v in first.items() if k!='request_sha256'})
    req=owner.build_request(**args)
    inp=owner.provider_payload(req,expected_request_sha256=req['request_sha256'])['input']
    assert all(h['current_value'] is None and 'current_percentile' not in h['all']
               for h in inp['provider_reference_context']['history'])
    assert {r['new_buyer'] for r in outputs(req)}==stances
    row=next((r for r in outputs(req) if r['new_buyer']=='ATTRACTIVE'),outputs(req)[0])
    if row['new_buyer']=='ATTRACTIVE':
        row['valuation_context']['business_evidence_refs']=['business:p']
    ref=inp['provider_reference_context']['history'][0]['ref_id']
    row['provider_reference_refs']=[ref]
    def validate(raw):
        return owner.validate_result({'new_buyer_shadow':raw},req,
            expected_request_sha256=req['request_sha256'])['status']
    assert validate(row)=='PASS'
    bad=deepcopy(row); bad['provider_reference_refs']=['unowned']
    assert validate(bad)=='FAIL'
    chosen=deepcopy(row)
    chosen['economic_price_review']={'candidate_id':inp['historical_price_context']['candidates'][0]['candidate_id'],
                                    'preferred_boundary':'LOW'}
    assert validate(chosen)==('PASS' if selection else 'FAIL')
    display=_provider_reference_row(inp)
    assert 'Finnhub 분기 PER 최근 5년' in display.text and ref in display.source_fact_ids
    if selection:
        rendered=_historical_price_row(inp,chosen,SimpleNamespace(scenario=None,quality='INSUFFICIENT_EVIDENCE'))
        assert 'Finnhub 분기 PER 참고' in rendered.text and 'Finnhub 분기 PBR 참고' in rendered.text
        assert '현재가와 동일 가격 기준 미확정' in rendered.text
        assert '경제적 선호 가격 상한' in rendered.text
        assert '관찰 구간' not in rendered.text
