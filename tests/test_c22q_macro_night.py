from copy import deepcopy
from datetime import date,datetime
import hashlib,json
from pathlib import Path
import pytest
from app.services.dated_macro_display_claims import derive_observation,load_claims,render_macro_block,verify_macro_text
from app.services.unified_snapshot_contract import digest

R=Path(__file__).resolve().parents[3]
CAPTURE=dict(archive_path=str(R/'maintenance/20261110-c22p-v1/C22P_V1_APPROVED_SOURCE_ONLY_CANARY_RESULT_20261110.zip'),
    archive_sha256='1fc94bb4f80548d9ee49947acac5d8a57becc52111f6e364498ac51546f00b85')

def pair(series='DGS3',level='4.59',previous='4.53'):
    payload=dict(observations=[dict(date='2026-11-06',value=level),dict(date='2026-11-05',value=previous)])
    raw=json.dumps(payload).encode();h=hashlib.sha256(raw).hexdigest()
    receipt=dict(provider='fred',request=dict(params=dict(series_id=series)),artifact_sha256=h,outcome='HTTP_RESPONSE',http_status=200,received_at='2026-11-10T04:00:01+00:00')
    temporal=dict(response_sha256=h,series_code=series,query_as_of='2026-11-10T04:00:00+00:00',observation_date='2026-11-06',published_at=None)
    return raw,receipt,temporal

@pytest.mark.parametrize('level,previous,pp,bp',[('4.59','4.53',.06,6),('-.10','-.20',.10,10),('.10','0',.10,10)])
def test_yield_absolute_units_and_non_direction(level,previous,pp,bp):
    claim=derive_observation('DGS3',*pair(level=level,previous=previous))
    assert claim['delta_pp']==pytest.approx(pp) and claim['delta_bp']==pytest.approx(bp)
    assert claim['change_pct'] is None and claim['direction_eligible'] is False
    assert all(r['registered'] for r in claim['numeric_registry'] if r['field_path'] in ('fields.level_pct','fields.change_bp','fields.previous_level_pct'))

@pytest.mark.parametrize('series,level,previous,expected',[('DCOILWTICO','99.64','100.06',-.4197481511),('DTWEXBGS','121.88','121.50',.3127572),('VIXCLS','25.64','28.18',-9.0134847)])
def test_relative_changes_keep_two_dates(series,level,previous,expected):
    c=derive_observation(series,*pair(series,level,previous))
    assert c['change_pct']==pytest.approx(expected,abs=1e-5)
    assert c['previous_observation_date']=='2026-11-05' and c['delta_bp'] is None

@pytest.mark.parametrize('previous',['.','0','-1'])
def test_unavailable_or_nonpositive_relative_baseline(previous):
    c=derive_observation('VIXCLS',*pair('VIXCLS','25',previous))
    assert c['level']==25 and c['change_pct'] is None

@pytest.mark.parametrize('kind',['hash','duplicate','future','series','nonfinite'])
def test_source_tamper_rejected(kind):
    raw,r,t=pair();p=json.loads(raw)
    if kind=='hash':raw=raw.replace(b'4.59',b'4.60')
    elif kind=='series':r['request']['params']['series_id']='VIXCLS'
    else:
        if kind=='duplicate':p['observations'][1]['date']='2026-11-06'
        if kind=='future':p['observations'][0]['date']='2026-11-11'
        if kind=='nonfinite':p['observations'][0]['value']='NaN'
        raw=json.dumps(p).encode();r['artifact_sha256']=t['response_sha256']=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):derive_observation('DGS3',raw,r,t)

def test_real_sealed_raw_display_and_whole_text_audit():
    claims=load_claims(CAPTURE);text=render_macro_block(claims)
    assert '+0.06%p / +6bp' in text and 'DTWEXBGS' in text
    assert 'DXY' not in text and all(not c['same_day_directional_authority'] for c in claims)
    assert verify_macro_text(text,CAPTURE)['status']=='PASS'
    with pytest.raises(ValueError):verify_macro_text(text+'\nSOXX 99%',CAPTURE)

def test_legacy_and_explicit_canonical_format():
    from app.services.us_full_message_service import _treasury_curve_block
    from app.services.market_display_plan import build_display_plan,render_display_plan
    from app.services.numeric_semantic_registry import build_numeric_registry
    claims=load_claims(CAPTURE);facts=[c['fact'] for c in claims]
    text,refs=_treasury_curve_block({f['fields']['series_code']:f for f in facts})
    assert '+0.06%p / +6bp' in text and len(refs)==4
    source=dict(session=dict(market='us',assessment_date='2026-11-10',latest_completed_regular_session_date='2026-11-09'),fact_catalog=facts,numeric_registry=build_numeric_registry(facts))
    plan=build_display_plan(source,market='us',assessment_date='2026-11-10',eligible_refs=[f['fact_id'] for f in facts],macro_display_capture=CAPTURE)
    rendered=render_display_plan(plan,source,'자료를 확인합니다.')
    assert '+0.06%p / +6bp' in rendered
    assert 'macro_display_capture' not in build_display_plan(source,market='us',assessment_date='2026-11-10',eligible_refs=[]).model_dump(mode='json')

def night_row(tmp_path):
    from tests.test_krx_night_history_service import _bar
    from app.services.krx_night_history_service import store_normalized_bar,build_same_contract_timeframes
    from app.services.night_futures import NIGHT_COMPARISON_SEMANTIC
    from app.services.official_night_market_eligibility_service import ENDPOINT
    from app.services.night_futures_session_mapping_service import US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT
    store_normalized_bar(tmp_path,_bar(date(2026,11,9),contract='SAME',maturity='2026-12'))
    frames=build_same_contract_timeframes(tmp_path,instrument_root='KOSPI200',reference_date=date(2026,11,9),daily_baseline_date=date(2026,11,6),daily_baseline_close=100)
    return dict(source=ENDPOINT,exchange='XKRX',session_date='2026-11-09',reference_date='2026-11-06',reference_date_contract=US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT,
        session_type='NIGHT',reference_session='DAY',finality_valid=True,reference_date_match=True,expected_reference_date='2026-11-09',provider_raw_bas_dd='2026-11-09',
        comparison_semantic=NIGHT_COMPARISON_SEMANTIC,fact_id='market:night_futures:1',series_code='KRX_KOSPI200_NIGHT_FUT',state='CURRENT_DIRECTIONAL',contract_code='SAME',
        night_source_record_id='2026-11-09:NIGHT:SAME',reference_source_record_id='2026-11-06:REGULAR:SAME',night_source_payload_sha256='a'*64,reference_source_payload_sha256='b'*64,
        contract_maturity='2026-12',value=101,reference_price=100,change_value=1,change_pct=1,night_timeframes=frames.model_dump(mode='json'))

@pytest.mark.parametrize('kind',['daily_partial','maturity','baseline_contract','raw_date','missing'])
def test_realistic_daily_with_partial_periods_and_identity(tmp_path,kind):
    from app.services.official_night_market_eligibility_service import night_market_eligibility
    row=night_row(tmp_path)
    if kind=='maturity':row['night_timeframes']['monthly']['contract_maturity']='2027-03'
    if kind=='baseline_contract':row['reference_source_record_id']='2026-11-06:REGULAR:OTHER'
    if kind=='raw_date':row['provider_raw_bas_dd']='2026-11-10'
    if kind=='missing':row['night_timeframes']=None
    result=night_market_eligibility(row,market='us',assessment_date='2026-11-10',completed_session_date='2026-11-09')
    assert result['eligible'] is (kind=='daily_partial')
    if kind=='daily_partial':assert row['night_timeframes']['monthly']['return_pct'] is None

@pytest.mark.parametrize('hour',[5,6,14])
def test_november_date_mapping_conflict_explicit(hour):
    from zoneinfo import ZoneInfo
    from app.services.night_futures_session_mapping_service import map_latest_completed_krx_night_session,resolve_us_morning_night_reference_date
    at=datetime(2026,11,10,hour,tzinfo=ZoneInfo('Asia/Seoul'))
    end=map_latest_completed_krx_night_session(at,us_regular_session_date=date(2026,11,9))
    ref=resolve_us_morning_night_reference_date(at,us_regular_session_date=date(2026,11,9))
    assert ref.expected_reference_date==date(2026,11,9)
    assert (end.provider_night_bas_dd==date(2026,11,10)) is (hour>=6)
    assert (ref.session_clock_finality=='BEFORE_06_00_KST') is (hour<6)


def test_user_body_suppression_and_full_aux_audit():
    from app.services.dated_macro_display_claims import render_us_source_preview,verify_us_source_preview
    output=render_us_source_preview(CAPTURE)
    assert '시장 판단 유보' not in output['text'] and '확신도 산정 불가' not in output['text']
    assert '순위 제외' not in output['text'] and '반도체 관심 업종' in output['text']
    assert output['market_judgment'] is output['confidence'] is None
    assert verify_us_source_preview(output,CAPTURE)['status']=='PASS'
    output['text']=output['text'].replace('SOXX +6.26%','SOXX +99.00%')
    output['text_sha256']=hashlib.sha256(output['text'].encode()).hexdigest()
    with pytest.raises(ValueError):verify_us_source_preview(output,CAPTURE)


@pytest.mark.parametrize('kind',['before','after','null','forged_bas_dd'])
def test_raw_night_finality_and_raw_date(kind):
    from zoneinfo import ZoneInfo
    from tests.test_krx_night_history_service import _row
    from app.services.krx_night_history_service import normalize_krx_night_daily_bars
    payload={'OutBlock_1':[_row(day='20261109',name='코스피200 F 202612 (야간)')]}
    if kind=='null':payload=None
    if kind=='forged_bas_dd':payload['OutBlock_1'][0]['BAS_DD']='20261110'
    result=normalize_krx_night_daily_bars(payload=payload,query_date=date(2026,11,9),
        fetched_at=datetime(2026,11,9,5 if kind=='before' else 6,tzinfo=ZoneInfo('Asia/Seoul')),
        raw_payload_sha256='a'*64,raw_relative_path='fixture-only')
    if kind in ('null','forged_bas_dd'):assert not result.bars
    else:assert result.bars[0].bar_finality==('UNFINALIZED' if kind=='before' else 'FINAL')


@pytest.mark.parametrize('series,wrong_unit',[('DGS3','bp'),('DCOILWTICO','percent')])
def test_series_unit_cannot_be_reinterpreted(series,wrong_unit):
    from app.services.dated_macro_display_claims import validate_series_unit
    with pytest.raises(ValueError):validate_series_unit(series,wrong_unit)
