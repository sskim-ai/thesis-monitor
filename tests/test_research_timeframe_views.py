from copy import deepcopy
from datetime import date
import json

import pytest

from app.services.market_session import _exchange_calendar
from app.services.vnext_timeframe_views import analytic_view, bounds, replay_view, APIS
from app.services.vnext_research_store import digest


def bars(tf='daily', market='US'):
    sessions = _exchange_calendar('XNYS' if market == 'US' else 'XKRX').sessions_in_range('2023-01-03', '2026-10-26')
    grouped = {}
    for d in sessions:
        grouped[bounds(d.date(), tf)[0]] = str(d.date())
    return [dict(date=d, open=10., high=12., low=9., close=11., volume=100) for d in grouped.values()]


def view(rows, tf='daily', **kw):
    return analytic_view(rows,timeframe=tf,market=kw.pop('market','US'),session='2026-10-26',**kw)


@pytest.mark.parametrize('tf', ['daily','weekly','monthly'])
@pytest.mark.parametrize('market', ['KR','US'])
def test_clean_independent_completed_timeframes(tf, market):
    rows=bars(tf,market); before=digest(rows); v=view(rows,tf,market=market)
    assert v['status']==tf.upper()+'_USABLE' and v['count']>0
    assert digest(rows)==before
    if tf!='daily': assert v['excluded_incomplete'] and v['end']<'2026-10-26'


@pytest.mark.parametrize('tf', ['daily','weekly','monthly'])
def test_bad_old_row_cuts_only_own_contiguous_suffix(tf):
    rows=bars(tf); rows[-9]['low']=13
    v=view(rows,tf)
    assert v['first_invalid']['date']==rows[-9]['date']
    assert v['start']==rows[-8]['date']
    assert len(v['rows'])==(8 if tf=='daily' else 7)
    for other in {'daily','weekly','monthly'}-{tf}:
        assert view(bars(other),other)['first_invalid'] is None


@pytest.mark.parametrize('change', ['duplicate','ordering','nan_volume','missing_volume','basis','gap'])
def test_invalid_inputs_are_not_stitched(change):
    rows=bars()
    if change=='duplicate': rows[-2]=deepcopy(rows[-1])
    elif change=='ordering': rows[-2],rows[-1]=rows[-1],rows[-2]
    elif change=='nan_volume': rows[-4]['volume']=float('nan')
    elif change=='missing_volume': rows[-4].pop('volume')
    elif change=='basis': rows[-4]['price_basis']='unadjusted'
    elif change=='gap': rows.pop(-4)
    if change in ('duplicate','ordering'):
        with pytest.raises(ValueError): view(rows)
    else:
        v=view(rows); assert v['count']==3 and v['first_invalid']


def test_recent_bad_row_cannot_supply_warmup():
    rows=bars();rows[-2]['close']=30
    assert view(rows)['count']==1


def test_zero_volume_original_nonnegative_contract():
    rows=bars();rows[-1]['volume']=0
    assert view(rows)['count']==len(rows)


def test_derived_week_must_not_hide_bad_daily_parent():
    daily=bars(); daily[-10]['low']=99
    weekly=bars('weekly')
    derived=view(weekly,'weekly',source_kind='DERIVED_FROM_DAILY',daily_parent=daily)
    assert derived['first_invalid']['reasons']==['DERIVED_PERIOD_CONTAINS_INVALID_DAILY']
    assert view(weekly,'weekly')['first_invalid'] is None
    with pytest.raises(ValueError): view(weekly,'weekly',source_kind='DERIVED_FROM_DAILY')


def test_new_append_does_not_reintroduce_rejected_history():
    rows=bars();rows[-50]['low']=13
    old=analytic_view(rows[:-1],timeframe='daily',market='US',session=rows[-2]['date'])
    new=view(rows)
    assert old['start']==new['start'] and new['count']==old['count']+1


def bound_input(tf='daily'):
    rows=bars(tf);physical=json.dumps({'rows':rows}).encode();sha=digest(physical)
    body=dict(stk_cd='UNSEEN',stex_tp='NY',upd_stkpc_tp='1')
    receipt=dict(raw_birth='CURRENT_HTTP',raw_sha256=sha,status=200,auth=False,run_id='original',
        captured_at='2026-10-27T01:00:00+00:00',request=dict(api=APIS['US'][tf],body=json.dumps(body)))
    root=dict(kind='CURRENT_CHART_REPLAY',calendar=dict(session='2026-10-26',calendar='XNYS'),
        request_body=body,pages=[dict(raw_sha256=sha,captured_at=receipt['captured_at'])],
        selected=rows,quality=dict(valid=True),parser_sha256='pinned-original')
    raw=json.dumps(root).encode();h=digest(raw)
    entry=dict(source_sha=h,original_run='original',status='SOURCE_REFERENCE',
        provenance=dict(dependencies=[dict(raw_sha256=sha,receipt_sha256=digest(receipt))]))
    binding=dict(source_sha=h,source_generation='original',receipts=[receipt])
    identity=dict(ticker='UNSEEN',country='US',exchange='NYSE')
    return entry,{h:raw,sha:physical},binding,identity


@pytest.mark.parametrize('tf',['daily','weekly','monthly'])
def test_existing_feature_consumer_and_repeat_digest(tf):
    e,raw,b,identity=bound_input(tf)
    one=replay_view(e,raw,identity=identity,timeframe=tf,session='2026-10-26',binding=b)
    two=replay_view(e,raw,identity=identity,timeframe=tf,session='2026-10-26',binding=b)
    assert one==two and 'sma_20' in one['permitted_indicators']
    assert one['strict_native'] is False


@pytest.mark.parametrize('tamper',['api','body','generation','raw','receipt','security'])
def test_actual_consumer_rejects_wrong_bindings(tamper):
    e,raw,b,identity=bound_input()
    if tamper=='api':b['receipts'][0]['request']['api']='usa06013'
    elif tamper=='body':b['receipts'][0]['request']['body']='{}'
    elif tamper=='generation':b['source_generation']='new'
    elif tamper=='raw':raw[e['source_sha']]=b'{}'
    elif tamper=='receipt':b['receipts'][0]['status']=201
    elif tamper=='security':identity['ticker']='OTHER'
    with pytest.raises(ValueError):replay_view(e,raw,identity=identity,timeframe='daily',session='2026-10-26',binding=b)


def test_financial_one_attempt_plan_and_no_retry(monkeypatch,tmp_path):
    import asyncio
    from datetime import datetime,timezone
    from types import SimpleNamespace
    from app.services import vnext_public_capture as capture
    identity=dict(ticker='UNSEEN',country='US',cik='123456',issuer_type='domestic_us',
        identity_provider='official',canonical_company_id='company',canonical_security_id='security')
    store=SimpleNamespace(path=tmp_path/'research.sqlite3',identities=lambda:[identity])
    observed=[]
    class Reader:
        def __init__(self,plan,*args,**kw): observed.append(plan);self.receipts=[]
    async def collect(reader):raise ValueError('offline_probe')
    monkeypatch.setattr(capture,'ResearchReader',Reader);monkeypatch.setattr(capture,'collect',collect)
    asyncio.run(capture.financial(store,'test',identity,datetime.now(timezone.utc),
        SimpleNamespace(opendart_api_key=None,sec_user_agent='test'),SimpleNamespace(stopped={}),maximum_attempts=1))
    assert len(observed)==1
    assert observed[0]['maximum_attempts_per_request']==1
    assert observed[0]['maximum_retries_per_request']==0
    assert observed[0]['maximum_HTTP_attempts']==observed[0]['maximum_logical_requests']


def test_original_cold_message_is_not_new_source_claim():
    from app.services.vnext_daily_research import compact_message
    actions={s:dict(dirty=False,action='REUSE_VALID_PRIOR',model_dependency_status='VERIFIED') for s in ('business','valuation','timing')}
    checked=dict(rendered=dict(provisional_business_signal='x',counterevidence='x',valuation_expectations='x',
        newbuyer=dict(assessment='x'),holder=dict(assessment='x'),missing_next_fact='x'))
    cold=compact_message('UNSEEN','2026-10-26',checked,actions,audit_ref='local')
    original=compact_message('UNSEEN','2026-10-26',checked,actions,audit_ref='local',event_kind='ORIGINAL_NEW_SOURCE_AND_PRIMARY_GENERATION')
    assert '재시작 검증' in cold and '원래 실행' in original
    assert '새 적격 입력 없음' not in cold+original


def test_weekly_survives_missing_daily_without_fabricating_sr():
    from app.services.vnext_timeframe_views import CONTRACT
    from app.services.vnext_price_zones import build_price_attachment,numeric_price_catalog
    from app.services.vnext_research_v3 import evidence_contract,friendly_number
    e,raw,b,identity=bound_input('weekly')
    identity['canonical_security_id']='unseen-id'
    e.update(field='ohlcv.adjusted_weekly',ref='w',data=dict(source_captured_at='2026-10-27T01:00:00+00:00'),scope=[])
    packet=dict(case='UNSEEN',run_id='original',public_security=identity,
        evidence=[e,dict(field='completed_close',ref='close',scope=[],status='SOURCE_REFERENCE',source_sha='close',data=dict(calendar=dict(session='2026-10-26'),currency='USD'))],
        timeframe_view_policy=CONTRACT,timeframe_view_inputs=dict(weekly=b))
    attached=build_price_attachment(packet,raw);packet['price_attachment']=attached
    assert attached['status']=='DATED_TIMEFRAME_REFERENCE' and not attached['facts']
    contracts=evidence_contract(packet)
    owned=[x for key,x in contracts.items() if key.startswith('analytic:')]
    assert len(owned)==1 and owned[0]['eligible'] and owned[0]['layer']=='PRICE_TIMING'
    nums=numeric_price_catalog(packet)
    assert nums and all(n.get('analytic_timeframe')=='weekly' for n in nums)
    assert all('주봉' in friendly_number(n,packet) for n in nums)


def test_prompt_tables_are_lossless_with_nested_ragged_rows():
    from app.services.vnext_research_v3 import prompt_table_encode,prompt_table_decode
    value=dict(facts=[dict(semantic='adjusted_price',value=i,unit='USD',limits=[None,False]) for i in range(20)],
        different=[dict(a=1),dict(b=2)],strings=['1',None,False])
    packed=prompt_table_encode(value)
    assert prompt_table_decode(packed)==value
    assert len(json.dumps(packed))<len(json.dumps(value))
    with pytest.raises(ValueError):prompt_table_encode({'$rows':[]})
    with pytest.raises(ValueError):prompt_table_decode({'$columns':['a'],'$rows':[[1,2]]})


def test_prompt_repeated_text_keeps_all_original_bytes():
    from app.services.vnext_research_v3 import prompt_text_encode,prompt_text_decode
    value=[dict(raw='abc'*100,other='unchanged',zero=0) for _ in range(10)]
    packed=prompt_text_encode(value)
    assert prompt_text_decode(packed)==value
    assert len(json.dumps(packed))<len(json.dumps(value))
    with pytest.raises(ValueError):prompt_text_encode({'$text':0})
    with pytest.raises(ValueError):prompt_text_decode({'$data':{'$text':-1},'$text_dictionary':['a']})


def test_numeric_catalog_order_is_not_timeframe_authority():
    from app.services.vnext_timeframe_views import CONTRACT
    from app.services.vnext_research_v3 import verify_numeric_catalog
    rows=[dict(catalog_id='daily',value=1.0),dict(catalog_id='weekly',value=2.0)]
    packet=dict(timeframe_view_policy=CONTRACT,numeric_catalog=rows[::-1])
    verify_numeric_catalog(packet,rows)
    with pytest.raises(ValueError):verify_numeric_catalog(dict(numeric_catalog=rows[::-1]),rows)
    for invalid in (rows+[rows[0]], [dict(rows[0],value=4.),rows[1]],rows[:1]):
        with pytest.raises(ValueError):verify_numeric_catalog(dict(packet,numeric_catalog=invalid),rows)


def test_whole_verdict_decodes_lossless_prompt_and_keeps_legacy():
    from app.services.vnext_research_v3 import prompt_text_encode,prompt_table_encode
    from app.services.vnext_model_dependencies import _prompt_input
    packet=dict(stage='BLIND',packet=dict(facts=[dict(value=i,label='long label'*12) for i in range(8)]),
        source_contracts={'ref':'allowed'},blind=None,original_knowledge='unchanged policy')
    for envelope in (packet,prompt_text_encode(prompt_table_encode(packet))):
        assert _prompt_input(('Instructions\n'+json.dumps(envelope)).encode())==packet
    invalid={'$text_dictionary':[],'$data':{'$text':10}}
    with pytest.raises(ValueError):_prompt_input(json.dumps(invalid).encode())


def test_analytic_indicator_display_is_not_financial_evidence():
    from app.services.vnext_readable_research import readable_number
    row=dict(value=12.345,unit='USD',analytic_timeframe='weekly',semantic='SMA20',
             as_of='2026-10-19',field_path='/price_attachment/timeframe_views/weekly/features/facts/0/value')
    text=readable_number(row,{'evidence':[]})
    assert '주봉' in text and '12.35달러' in text and '완료 구간 참고' in text
