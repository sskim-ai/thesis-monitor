"""New C21S boundaries only. All quotes and provider responses are synthetic."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json,os
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import PriceContext, PriceDecisionContext, PricePeriodSummary
from app.services import ohlcv_client as client_module
from app.services import valuation_snapshot_service as valuation
from app.services.thesis_evaluation_service import _build_price_decision
from test_provider_native_technical import raw_payload,fixture_completion
from app.services.packet_owned_technical_context_service import load_packet_owned_technical_context
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,compact_ai_context
from app.services.kr_price_structure_selective_rollout_service import build_kr_price_structure_rollout_decision
from app.services.us_price_structure_selective_rollout_service import build_us_price_structure_rollout_decision

ASOF=datetime(2026,11,8,12,tzinfo=timezone.utc)

def fetch(monkeypatch,market='us',partial=1,asof=ASOF,complete_date='2026-11-05'):
    settings=Settings(_env_file=None,monitor_retry_attempts=1,
        kr_price_structure_v3_enabled=True,us_price_structure_v3_enabled=True)
    monkeypatch.setattr(client_module,'get_settings',lambda:settings)
    ticker='123456' if market=='kr' else 'SYNTH'
    requests=[];responses=[]
    def handle(request):
        p=dict(request.url.params);requests.append(p)
        tf=p['periods'];adjusted=p['adjusted']=='true'
        payload=raw_payload(ticker,market,tf,{'daily':85,'weekly':150,'monthly':28}[tf],adjusted)
        rows=payload['periods'][tf]
        if tf=='daily':
            rows=[r for r in rows if r['date']<=complete_date]
            rows[-1].update(open=95,high=96,low=94,close=95)
            for i in range(partial):
                rows.append(dict(date=f'2026-11-{int(complete_date[-2:])+1+i:02d}',open=135,high=136,low=134,close=135,
                                 volume=1500,bar_state='PARTIAL'))
        native=raw_payload(ticker,market,tf,1)['periods'][tf][-1]['indicators']
        limit=int(p['indicator_limit'])
        for r in rows:r.pop('indicators',None)
        if limit:
            for r in rows[-limit:]:r['indicators']=deepcopy(native)
        if tf=='daily' and market=='kr':
            for r in rows[-20:]:r['investor_flow']={'foreign_net_buy_qty':7,'foreign_net_buy_qty_20':140}
        payload['periods'][tf]=rows
        payload['meta']['indicator_limit']=limit
        responses.append(deepcopy(payload))
        return httpx.Response(200,json=payload)
    c=client_module.OhlcvClient(transport=httpx.MockTransport(handle),completion_verifier=fixture_completion)
    context=asyncio.run(c.fetch_price_context(ticker,as_of=asof))
    return context,requests,responses,ticker


@pytest.mark.parametrize('market',['kr','us'])
@pytest.mark.parametrize('asof',[ASOF,datetime(2026,11,6,2,tzinfo=timezone.utc)])
def test_raw_price_never_becomes_current_owner(monkeypatch,market,asof):
    context,requests,responses,ticker=fetch(monkeypatch,market,1,asof)
    native=context.technical_context_payload()['native_view']
    assert native['periods']['daily']['completed_as_of']=='2026-11-05'
    assert context.daily_history[-1].close==95
    assert context.decision.current_price is None
    assert context.decision.price_as_of is None and context.decision.price_basis=='unavailable'
    assert any('current-price Owner unavailable' in x for x in context.warnings)
    # The unadjusted PIT series keeps exact source labels, even if not eligible.
    assert [r.date.isoformat() for r in context.valuation_history]==[r['date'] for r in responses[3]['periods']['weekly']]
    result=_build_price_decision(InvestmentThesis(ticker=ticker,price_rules='{}'),context)
    assert result.current_price is None and result.price_as_of is None and result.price_basis=='unavailable'


@pytest.mark.parametrize('market',['kr','us'])
def test_emitted_queries_flow_owner_and_service_budget(monkeypatch,market):
    context,requests,_,_=fetch(monkeypatch,market)
    assert len(requests)==4  # Three technical plus one independent valuation history.
    assert [p['include_investor_flows'] for p in requests]==(['true','false','false','false'] if market=='kr' else ['false']*4)
    assert [p['indicator_limit'] for p in requests]==['5','5','5','0']
    assert context.supply.available is (market=='kr')
    if market=='kr':assert context.supply.foreign_net_buy_qty_20==140


@pytest.mark.parametrize('partial',[1,2,3])
def test_completed_native_values_survive_partial_tail(monkeypatch,partial):
    context,_,responses,_=fetch(monkeypatch,partial=partial)
    p=context.technical_context_payload()['native_view']['periods']['daily']
    expected=next(r['indicators'] for r in responses[0]['periods']['daily'] if r['date']=='2026-11-05')
    assert p['indicators']==expected
    assert p['indicators']['RSI14']==47.123456789
    assert p['indicators']['MACD']==.123456789
    assert p['indicators']['BB_36_1.541_UPPER']==111.123456789
    assert p['indicator_quality']['MA288']=='UNAVAILABLE_PROVIDER_NULL_OR_MISSING'
    assert p['quarantined_count']==partial
    assert len(json.dumps(responses[0]).encode())<128*1024


@pytest.mark.parametrize('count',[0,1,3,1000])
def test_indicator_window_bounded_for_short_or_empty(monkeypatch,count):
    monkeypatch.setattr(client_module,'get_settings',lambda:Settings(_env_file=None,monitor_retry_attempts=1))
    requests=[]
    def handle(request):
        requests.append(dict(request.url.params))
        return httpx.Response(200,json=raw_payload('SYNTH','us','daily',min(count,3)))
    async def run():
        c=client_module.OhlcvClient(transport=httpx.MockTransport(handle))
        async with httpx.AsyncClient(base_url='https://synthetic.invalid',transport=c.transport) as h:
            await c._request_period(h,'SYNTH','daily',count)
    asyncio.run(run())
    assert int(requests[0]['indicator_limit'])==min(count,5)
    assert requests[0]['include_investor_flows']=='false'


@pytest.mark.parametrize('owned',[False,True])
def test_independent_price_owner_preserved_and_no_valuation_fallback(monkeypatch,owned):
    context,_,_,ticker=fetch(monkeypatch)
    if owned:
        # This represents an already admitted independent Owner, not issuance.
        context.decision=PriceDecisionContext(current_price=96,currency='USD',price_as_of='2026-11-05',
            exchange_trade_date='2026-11-05',price_basis='close',market_session='closed')
    decision=_build_price_decision(InvestmentThesis(ticker=ticker,price_rules='{}'),context)
    assert decision.current_price==(96 if owned else None)
    assert decision.price_as_of==('2026-11-05' if owned else None)
    monkeypatch.setattr(valuation,'get_settings',lambda:Settings(_env_file=None))
    def forbidden(request):pytest.fail('No provider query permitted')
    service=valuation.ValuationSnapshotService(transport=httpx.MockTransport(forbidden))
    snapshot=asyncio.run(service.fetch(ticker,'NASDAQ',context,as_of=ASOF))
    assert snapshot.current_price==(96 if owned else None)
    assert snapshot.price_as_of==('2026-11-05' if owned else None)


def test_legacy_price_fallback_remains_separate():
    context=PriceContext(periods={'daily':PricePeriodSummary(requested_count=3,actual_count=3,
        latest_date='2026-11-05',latest_close=96)})
    d=_build_price_decision(InvestmentThesis(ticker='SYNTH',price_rules='{}'),context)
    assert d.current_price==96 and d.price_as_of=='2026-11-05' and d.price_basis=='close'


def test_scope_survives_public_serialization_without_private_packet():
    context=PriceContext(price_source_scope='dated_technical_only',periods={'daily':
        PricePeriodSummary(requested_count=85,actual_count=84,latest_date='2026-11-05',latest_close=95)})
    cold=PriceContext.model_validate_json(context.model_dump_json())
    assert not cold.technical_context_payload() and not cold.allows_legacy_price_fallback()
    d=_build_price_decision(InvestmentThesis(ticker='SYNTH',price_rules='{}'),cold)
    assert d.current_price is None and d.price_basis=='unavailable'
    cold.decision=PriceDecisionContext(current_price=96,price_as_of='2026-11-05',price_basis='close')
    d=_build_price_decision(InvestmentThesis(ticker='SYNTH',price_rules='{}'),cold)
    assert d.current_price==96 and d.price_as_of=='2026-11-05' and d.price_basis=='close'


@pytest.mark.parametrize('market',['kr','us'])
def test_changed_path_typed_prompt_and_original_sr_numeric_binding(monkeypatch,market):
    from app.services import price_structure_wave_fibonacci_v3_service as v3
    from app.services import packet_owned_technical_context_service as packet
    def forbidden(*a,**k):pytest.fail('Native indicator recomputation')
    monkeypatch.setattr(packet,'build_multi_timeframe_feature_packet',forbidden)
    monkeypatch.setattr(v3,'_bollinger_sources',forbidden)
    monkeypatch.setattr(v3,'_provisional_bollinger_sources',forbidden)
    context,requests,_,ticker=fetch(monkeypatch,market,3,
        complete_date='2026-11-06' if market=='us' else '2026-11-05')
    technical=load_packet_owned_technical_context(context.technical_context_payload(),ticker=ticker)
    evidence=build_decision_evidence_packet(packet={'packet_id':'C21S_SYNTHETIC','market':market,'assessment_date':'2026-11-06'},
        stock={'ticker':ticker,'company_name':'SYNTHETIC','fact_catalog':[]},technical_context=technical)
    prompt=compact_ai_context(evidence)
    assert prompt['technical_context_quality']['provider_native']['periods']['daily']['indicators']['RSI14']==47.123456789
    runtime=context.chart.structure['price_structure_v3']
    fn=build_kr_price_structure_rollout_decision if market=='kr' else build_us_price_structure_rollout_decision
    rendered=fn(runtime,ticker=ticker,monitored_subject=True,enabled=True)
    assert rendered.section and not rendered.render_validation_errors and rendered.numeric_bindings
    assert '📐 현재 가격 구조' in rendered.section and '조정봉·' in rendered.section
    assert '현재가' not in rendered.section and '정규장' not in rendered.section
    assert runtime['current_quote'] is None and context.decision.current_price is None
    output=Path(os.environ['C21S_OUTPUT']);output.mkdir(exist_ok=True)
    (output/(market+'-NO_SEND.md')).write_text('SYNTHETIC NO-SEND ONLY\n'+rendered.section)
    (output/(market+'-receipt.json')).write_text(json.dumps({'prompt':prompt,'renderer':rendered.to_dict(),
        'queries':requests,'current_price':None},ensure_ascii=False,indent=2))
