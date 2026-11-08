"""C21R synthetic /ohlcv source-to-prompt and NO-SEND renderer proof."""
import asyncio
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import hashlib,json,math,os
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.services import ohlcv_client as client_module
from app.services.provider_native_technical import MAX_COUNTS, PIVOT_LOOKBACKS, INDICATORS, build_provider_native_view
from app.services.packet_owned_technical_context_service import build_native_packet_context
from app.services.market_session import exchange_calendar
from app.services import price_structure_wave_fibonacci_v3_service as v3
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,compact_ai_context
from app.services.kr_price_structure_selective_rollout_service import build_kr_price_structure_rollout_decision,apply_current_price_structure_section
from app.services.us_price_structure_selective_rollout_service import build_us_price_structure_rollout_decision

CUTOFF=date(2026,11,6)


@lru_cache
def labels(market,tf,count):
    if count==0:return []
    calendar=exchange_calendar.get_calendar('XKRX' if market=='kr' else 'XNYS',start='1995-01-01',end='2026-12-31')
    sessions=[s.date() for s in calendar.sessions_in_range(calendar.first_session,CUTOFF)]
    if tf=='daily':return sessions[-count:]
    grouped={}
    for d in sessions:
        key=d.isocalendar()[:2] if tf=='weekly' else (d.year,d.month)
        grouped[key]=d
    if tf=='monthly':grouped.pop((2026,11),None)
    return list(grouped.values())[-count:]


def raw_payload(ticker,market,tf,count,adjusted=True):
    rows=[]
    for i,d in enumerate(labels(market,tf,count)):
        close=100+4*math.sin((i-count+1)*math.pi/8)
        rows.append(dict(date=d.isoformat(),open=close,high=close+1,low=close-1,close=close,volume=1000+i,
                         bar_state='FINAL'))
    if rows:
        indicators={key:None for key in INDICATORS}
        indicators.update(RSI14=47.123456789,MACD=.123456789,MACD_SIGNAL=.08,MACD_HIST=.043456789,
            VOLUME_RATIO_20=1.23456789,MA33=99.3456789,MA111=98.7654321,
            BB_36_1_541_placeholder=None)
        indicators.pop('BB_36_1_541_placeholder')
        indicators['BB_36_1.541_UPPER']=111.123456789
        indicators['RETURN_20D']=2.3456789
        rows[-1]['indicators']=indicators
    return dict(symbol=ticker,resolved_symbol=dict(code=ticker,market=market.upper(),exchange='KRX' if market=='kr' else 'NASDAQ'),
        periods={tf:rows},meta=dict(provider='kiwoom',adjusted=adjusted,count=count,include_indicators=True,indicator_limit=1,generated_at='2026-11-08T12:00:00Z'))


def decoded(ticker,market,tf,count):
    payload=raw_payload(ticker,market,tf,count)
    body=json.dumps(payload).encode()
    return client_module.OhlcvClient._decode_period_payload(payload,ticker=ticker,period=tf,adjusted=True,
        response_body_sha256=hashlib.sha256(body).hexdigest())[0]


def fixture_completion(row,tf,cutoff):
    # Trusted synthetic fixture Owner only; it is never installed into Settings
    # or the unproven production W/M provider label registry.
    return row.get('bar_state')=='FINAL' and date.fromisoformat(row['date'])<=cutoff


def view_for(counts):
    return build_provider_native_view(ticker='SYNTH',market='us',cutoff=CUTOFF,
        periods={tf:decoded('SYNTH','us',tf,n) for tf,n in counts.items()},completion_verifier=fixture_completion)


def test_short_counts_and_native_values_are_not_recomputed():
    counts=dict(daily=85,weekly=150,monthly=28);view=view_for(counts)
    for tf,n in counts.items():
        p=view.periods[tf];assert p.status=='AVAILABLE' and p.completed_count==n
        assert p.indicators==raw_payload('SYNTH','us',tf,n)['periods'][tf][-1]['indicators']
        assert p.indicators['RSI14']==47.123456789
    assert len(INDICATORS)==38 and not view.current_price_qualified


def test_ceiling_zero_and_null_are_independent():
    view=view_for(dict(daily=1005,weekly=0,monthly=28))
    assert view.periods['daily'].returned_count==1005 and view.periods['daily'].completed_count==1000
    assert view.periods['weekly'].status=='UNAVAILABLE'
    assert view.periods['monthly'].status=='AVAILABLE'
    assert view.periods['monthly'].indicators['MA288'] is None


@pytest.mark.parametrize('bad',['hash','ohlc','duplicate','basis','identity'])
def test_invalid_source_does_not_poison_other_timeframes(bad):
    periods={tf:decoded('SYNTH','us',tf,n) for tf,n in dict(daily=85,weekly=52,monthly=28).items()}
    row=periods['daily'][0]
    if bad=='hash':row['close']+=.01
    if bad=='ohlc':row['high']=row['low']-1
    if bad=='duplicate':periods['daily'].append(deepcopy(row))
    if bad=='basis':row['_native_capture']['adjusted']=False
    if bad=='identity':row['_native_capture']['code']='FOREIGN'
    if bad=='ohlc':
        from app.services.unified_snapshot_contract import digest
        row['_native_capture']['normalized_bar_sha256']=digest({k:v for k,v in row.items() if k!='_native_capture'})
    view=build_provider_native_view(ticker='SYNTH',market='us',periods=periods,cutoff=CUTOFF,completion_verifier=fixture_completion)
    assert view.periods['daily'].status=='INVALID' and view.periods['weekly'].status=='AVAILABLE'
    if bad=='ohlc':assert 'INVALID_OHLCV' in view.periods['daily'].reasons


def test_unconfirmed_and_unknown_labels_do_not_become_completed_prices():
    rows=decoded('SYNTH','us','weekly',28)
    view=build_provider_native_view(ticker='SYNTH',market='us',periods={'weekly':rows},cutoff=CUTOFF)
    assert view.periods['weekly'].status=='UNAVAILABLE'
    assert 'FINALITY_OR_PERIOD_LABEL_UNPROVEN' in view.periods['weekly'].reasons


def test_latest_provisional_quarantined_without_date_relabel():
    rows=decoded('SYNTH','us','daily',85);rows[-1]['bar_state']='PARTIAL'
    from app.services.unified_snapshot_contract import digest
    rows[-1]['_native_capture']['normalized_bar_sha256']=digest({k:v for k,v in rows[-1].items() if k!='_native_capture'})
    view=build_provider_native_view(ticker='SYNTH',market='us',periods={'daily':rows},cutoff=CUTOFF,completion_verifier=fixture_completion)
    assert view.periods['daily'].completed_count==84
    assert view.periods['daily'].completed_as_of==rows[-2]['date']
    assert view.periods['daily'].indicators['RSI14'] is None


def test_v3_pivots_only_from_recent_completed_window():
    periods={tf:decoded('SYNTH','us',tf,n) for tf,n in MAX_COUNTS.items()}
    result=v3.build_price_structure_wave_fib_v3(ticker='SYNTH',security_id='US_LISTED:SYNTH',market='US',currency='USD',
        adjustment_basis='provider_adjusted_price_v1',cutoff=CUTOFF.isoformat(),raw_by_timeframe=periods,
        observed_at='2026-11-08T12:00:00+00:00',provider_native=True)
    for tf,lookback in PIVOT_LOOKBACKS.items():
        assert result.coverage[tf].actual_count==MAX_COUNTS[tf]
        assert result.pivots[tf]
        oldest=periods[tf][-lookback]['date']
        assert all(p.pivot_bar_date>=oldest for p in result.pivots[tf])
        assert all(p.confirmation_date is None or p.confirmation_date<=CUTOFF.isoformat() for p in result.pivots[tf])


@pytest.mark.parametrize('market,ticker',[('us','SYNTH'),('kr','123456')])
def test_client_to_typed_prompt_and_original_sr_no_send(market,ticker,monkeypatch):
    settings=Settings(_env_file=None,kr_price_structure_v3_enabled=True,us_price_structure_v3_enabled=True,monitor_retry_attempts=1)
    monkeypatch.setattr(client_module,'get_settings',lambda:settings)
    from app.services import packet_owned_technical_context_service as legacy
    def forbidden(*args,**kwargs):pytest.fail('Native path recalculated a basic technical indicator')
    monkeypatch.setattr(legacy,'build_multi_timeframe_feature_packet',forbidden)
    monkeypatch.setattr(v3,'_bollinger_sources',forbidden)
    monkeypatch.setattr(v3,'_provisional_bollinger_sources',forbidden)
    requests=[];counts=dict(daily=85,weekly=150,monthly=28)
    def handle(request):
        params=dict(request.url.params);requests.append(params)
        tf=params['periods'];adjusted=params['adjusted']=='true'
        response=raw_payload(ticker,market,tf,counts[tf],adjusted)
        if market=='us':response['periods'][tf][-1]['investor_flow']={'foreign_net_buy_qty':999}
        return httpx.Response(200,json=response)
    client=client_module.OhlcvClient(transport=httpx.MockTransport(handle),completion_verifier=fixture_completion)
    context=asyncio.run(client.fetch_price_context(ticker,as_of=datetime(2026,11,8,12,tzinfo=timezone.utc)))
    payload=context.technical_context_payload()
    technical=legacy.load_packet_owned_technical_context(payload,ticker=ticker)
    assert technical.features is None and technical.native_view is not None
    if market=='us':assert context.supply.available is False
    assert all(technical.native_view.periods[tf].completed_count==n for tf,n in counts.items())
    assert [int(p['count']) for p in requests[:3]]==[1000,700,300]
    assert all(p['indicator_limit']=='5' for p in requests[:3])
    assert requests[3]['adjusted']=='false' and requests[3]['count']=='300'
    evidence=build_decision_evidence_packet(packet=dict(packet_id='C21R_SYNTHETIC',market=market,assessment_date='2026-11-06'),
        stock=dict(ticker=ticker,company_name='SYNTHETIC NO-SEND',fact_catalog=[]),technical_context=technical)
    prompt=compact_ai_context(evidence)
    assert prompt['technical_context_quality']['provider_native']['periods']['daily']['indicators']['RSI14']==47.123456789
    assert any('provider-native:RSI14' in ref.label for ref in evidence.evidence)
    runtime=context.chart.structure['price_structure_v3']
    decision=(build_us_price_structure_rollout_decision if market=='us' else build_kr_price_structure_rollout_decision)(runtime,
        ticker=ticker,monitored_subject=True,enabled=True)
    assert decision.section and not decision.render_validation_errors,decision
    assert decision.numeric_bindings and decision.displayed_zone_ids
    assert '📐 현재 가격 구조' in decision.section
    assert '조정봉·' in decision.section and '정규장' not in decision.section and '현재가' not in decision.section
    assert runtime['current_quote'] is None
    message=apply_current_price_structure_section('SYNTHETIC NO_SEND\nNo investment judgment issued.',decision.section)
    assert decision.section in message
    target=Path(os.environ['C21R_FIXTURE_OUTPUT']);target.mkdir(parents=True,exist_ok=True)
    (target/(market+'-native-prompt.json')).write_text(json.dumps(prompt,ensure_ascii=False,indent=2))
    (target/(market+'-native-source.json')).write_text(json.dumps(technical.native_view.prompt_payload(),ensure_ascii=False,indent=2))
    (target/(market+'-sr-runtime.json')).write_text(json.dumps(runtime,ensure_ascii=False,indent=2))
    (target/(market+'-NO_SEND.md')).write_text(message)
    (target/(market+'-renderer-receipt.json')).write_text(json.dumps(decision.to_dict(),ensure_ascii=False,indent=2))


def test_future_bar_quarantined_and_projection_tamper_denied():
    from app.services.unified_snapshot_contract import digest
    rows=decoded('SYNTH','us','daily',85)
    rows[-1]['date']='2026-11-09'
    rows[-1]['_native_capture']['normalized_bar_sha256']=digest({k:v for k,v in rows[-1].items() if k!='_native_capture'})
    view=build_provider_native_view(ticker='SYNTH',market='us',periods={'daily':rows},cutoff=CUTOFF,completion_verifier=fixture_completion)
    assert view.periods['daily'].completed_count==84 and view.periods['daily'].raw_bar_date=='2026-11-09'
    view.periods['daily'].indicators['RSI14']=99
    with pytest.raises(ValueError,match='native_technical_view_changed'):view.verify()


def test_wrong_exchange_and_market_do_not_become_native_input():
    payload=raw_payload('SYNTH','us','daily',85)
    payload['resolved_symbol']['exchange']='KRX'
    with pytest.raises(ValueError,match='exchange_identity'):client_module.OhlcvClient._decode_period_payload(payload,ticker='SYNTH',period='daily',adjusted=True)
    payload['resolved_symbol']['market']='KR'
    with pytest.raises(ValueError,match='market_identity'):client_module.OhlcvClient._decode_period_payload(payload,ticker='SYNTH',period='daily',adjusted=True)


def test_mixed_source_captures_rejected_without_poisoning_other_periods():
    periods={tf:decoded('SYNTH','us',tf,n) for tf,n in dict(daily=85,weekly=52).items()}
    periods['daily'][0]['_native_capture']['response_body_sha256']='0'*64
    view=build_provider_native_view(ticker='SYNTH',market='us',periods=periods,cutoff=CUTOFF,completion_verifier=fixture_completion)
    assert view.periods['daily'].status=='INVALID'
    assert 'CONFLICTING_SOURCE_CAPTURES' in view.periods['daily'].reasons
    assert view.periods['weekly'].status=='AVAILABLE'
