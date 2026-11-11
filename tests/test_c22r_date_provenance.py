from copy import deepcopy
from datetime import date, datetime
import hashlib,json
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

from app.services.night_futures_session_mapping_service import (
    resolve_us_morning_night_reference_date as resolve, US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT as CONTRACT,
)
from app.services.official_night_market_eligibility_service import night_market_eligibility, ENDPOINT

KST=ZoneInfo('Asia/Seoul')
ROOT=Path(__file__).resolve().parents[3]
CAPTURE=dict(archive_path=str(ROOT/'maintenance/20261110-c22p-v1/C22P_V1_APPROVED_SOURCE_ONLY_CANARY_RESULT_20261110.zip'),
    archive_sha256='1fc94bb4f80548d9ee49947acac5d8a57becc52111f6e364498ac51546f00b85')

@pytest.mark.parametrize('at,night,day,final',[
    ('2026-11-10T05:59:00+09:00','2026-11-07','2026-11-06',False),
    ('2026-11-10T06:00:00+09:00','2026-11-10','2026-11-09',True),
    ('2026-11-10T08:10:00+09:00','2026-11-10','2026-11-09',True),
    ('2026-11-07T06:00:00+09:00','2026-11-07','2026-11-06',True),
    ('2026-11-08T08:10:00+09:00','2026-11-07','2026-11-06',True),
    ('2026-08-18T08:10:00+09:00','2026-08-15','2026-08-14',True),
])
def test_official_end_date_and_start_day_holiday(at,night,day,final):
    m=resolve(datetime.fromisoformat(at),us_regular_session_date=date(2026,11,9))
    assert str(m.night_trade_date)==night and str(m.regular_reference_date)==day
    assert m.expected_reference_date==m.night_trade_date
    assert (m.session_clock_finality=='FINAL_BY_06_00_KST') is final

def row(tmp_path):
    from tests.test_krx_night_history_service import _bar
    from app.services.krx_night_history_service import store_normalized_bar,build_same_contract_timeframes
    from app.services.night_futures import NIGHT_COMPARISON_SEMANTIC
    store_normalized_bar(tmp_path,_bar(date(2026,11,10),contract='SAME',maturity='2026-12'))
    frames=build_same_contract_timeframes(tmp_path,instrument_root='KOSPI200',reference_date=date(2026,11,10),
        daily_baseline_date=date(2026,11,9),daily_baseline_close=100)
    return dict(source=ENDPOINT,exchange='XKRX',session_date='2026-11-10',reference_date='2026-11-09',
        reference_date_contract=CONTRACT,session_type='NIGHT',reference_session='DAY',finality_valid=True,reference_date_match=True,
        expected_reference_date='2026-11-10',provider_raw_bas_dd='2026-11-10',night_trade_date='2026-11-10',regular_reference_date='2026-11-09',
        observation_time_kst='2026-11-10T08:10:00+09:00',comparison_semantic=NIGHT_COMPARISON_SEMANTIC,fact_id='market:night_futures:1',
        series_code='KRX_KOSPI200_NIGHT_FUT',state='CURRENT_DIRECTIONAL',contract_code='SAME',
        night_source_record_id='2026-11-10:NIGHT:SAME',reference_source_record_id='2026-11-09:REGULAR:SAME',
        night_source_payload_sha256='a'*64,reference_source_payload_sha256='b'*64,contract_maturity='2026-12',
        value=101,reference_price=100,change_value=1,change_pct=1,night_timeframes=frames.model_dump(mode='json'))

@pytest.mark.parametrize('kind',['valid_partial','raw_date','raw_hash','wrong_day_contract','rollover','before06','old_v3','wrong_US_session'])
def test_night_date_identity_gate(tmp_path,kind):
    r=row(tmp_path);completed='2026-11-09'
    if kind=='raw_date':r['provider_raw_bas_dd']='2026-11-09'
    if kind=='raw_hash':r['night_source_payload_sha256']='c'*64
    if kind=='wrong_day_contract':r['reference_source_record_id']='2026-11-09:REGULAR:OTHER'
    if kind=='rollover':r['night_timeframes']['daily']['contract_maturity']='2027-03'
    if kind=='before06':r['observation_time_kst']='2026-11-10T05:59:00+09:00'
    if kind=='old_v3':r['reference_date_contract']='us-morning-night-reference-date-v3'
    if kind=='wrong_US_session':completed='2026-11-06'
    result=night_market_eligibility(r,market='us',assessment_date='2026-11-10',completed_session_date=completed)
    assert result['eligible'] is (kind=='valid_partial')
    if kind=='valid_partial':assert r['night_timeframes']['weekly']['return_pct'] is None

def test_old_actual_cache_replay_no_current_qualification():
    from app.jobs.probe_krx_night_futures import parse_krx_futures_payloads
    diagnostic=json.loads((ROOT/'maintenance/20261110-c22q-v2/NIGHT_DIAGNOSTIC.json').read_bytes())
    cache=next(r for r in diagnostic['roots'] if r.get('receipt_count')==3)
    payloads={};hashes={}
    for item in cache['raw_checks']:
        receipt=item['receipt'];raw=(Path(cache['path'])/receipt['raw_relative_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==receipt['raw_payload_sha256']
        d=date.fromisoformat(receipt['query_date']);payloads[d]=json.loads(raw);hashes[d]=receipt['raw_payload_sha256']
    probe=parse_krx_futures_payloads(payloads,fetched_at=datetime(2026,11,5,18,tzinfo=KST),payload_sha256_by_date=hashes)
    assert probe.night_session_usable and probe.observations
    assert all(o.session_date==date(2026,11,4) and o.reference_date==date(2026,11,3) for o in probe.observations)
    assert all(o.session_date!=date(2026,11,10) for o in probe.observations)

def test_user_KR_hides_only_labels_and_full_body_audit():
    from app.services.dated_macro_display_claims import render_kr_source_preview,verify_kr_source_preview
    out=render_kr_source_preview(CAPTURE)
    assert '판단 유보' not in out['text'] and '확신도 산정 불가' not in out['text']
    assert out['market_judgment'] is out['confidence'] is None and out['status']=='PARTIAL'
    assert verify_kr_source_preview(out,CAPTURE)['status']=='PASS'
    out['text']=out['text'].replace('5,018.85','5,999.00')+'\n임의 본문'
    out['text_sha256']=hashlib.sha256(out['text'].encode()).hexdigest()
    with pytest.raises(ValueError):verify_kr_source_preview(out,CAPTURE)

@pytest.mark.parametrize('kind',['same_values_new_run','earlier_cutoff','new_parent','new_generation'])
def test_old_capture_never_injected_into_current_market(kind):
    from app.services.market_display_plan import build_display_plan
    from app.services.production_message_renderer import market_message
    with pytest.raises(ValueError,match='offline_source_only'):
        build_display_plan({'session':{'run':kind}},market='us',assessment_date='2026-11-10',eligible_refs=[],macro_display_capture=CAPTURE)
    with pytest.raises(ValueError,match='offline_source_only'):
        market_message(None,macro_display_capture=CAPTURE)
