"""Focused Step 2 boundary checks; no provider/model/database calls."""
from types import SimpleNamespace
import pytest

from app.services.provider_native_technical import recent_completed_path
from app.services.monitoring_summary import summary_message, verify_summary_message
from app.services.analysis_report_service import telegram_render_parts
from app.services.detailed_stock_message_v2 import _buyer_action


def test_recent_path_is_observed_not_recomputed():
    rows = [{'date':f'2026-10-{i:02d}','close':100+i,'volume':i*10,
             'indicators':{'RSI14':i,'MACD':None if i==15 else i/100,
                           'MACD_HIST':i/10,'VOLUME_RATIO_20':i/20}}
            for i in range(1,26)]
    period = SimpleNamespace(status='AVAILABLE',rows=rows,completed_as_of='2026-10-25',
        indicators=rows[-1]['indicators'],
        indicator_quality={'RSI14':'PROVIDER_NATIVE','MACD':'PROVIDER_NATIVE',
                           'MACD_HIST':'PROVIDER_NATIVE','VOLUME_RATIO_20':'PROVIDER_NATIVE'})
    got=recent_completed_path(period)
    assert got['dates']==[r['date'] for r in rows[-20:]]
    assert got['close']==[r['close'] for r in rows[-20:]]
    assert got['indicators']['MACD'][9] is None
    assert got['indicators']['VOLUME_RATIO_20']==[r['indicators']['VOLUME_RATIO_20'] for r in rows[-20:]]
    period.indicator_quality['RSI14']='UNAVAILABLE'
    assert 'RSI14' not in recent_completed_path(period)['indicators']
    period.completed_as_of='2026-10-24'
    assert recent_completed_path(period) is None


@pytest.mark.parametrize('state,quality,expected',[
    ('MIXED','SUPPORTED','조건부 신규 매수 검토 가능'),
    ('INSUFFICIENT','SUPPORTED','조건부 신규 매수 검토 가능 · 기술적 확인 필요'),
    ('ADVERSE','SUPPORTED','기술지표 개선 또는 확인 신호 대기'),
    ('SUPPORTIVE','BLOCKED','지지 이탈 구조 재검토'),
])
def test_technical_state_does_not_override_entry_quality(state,quality,expected):
    assert _buyer_action('ATTRACTIVE','INSIDE',quality,
        technical={'state':state,'change':'IMPROVING'})==expected


def _detail(ticker,gen):
    row=dict(ticker=ticker,status='COMPLETE',price='$10.00',overall='HOLD',holder='HOLD',
        economic='ATTRACTIVE',technical='혼재·개선',entry_quality='CAUTION',rr='1.00배',
        support='$9–$10',rr2='교집합 없음',economic_preferred='미산출',
        action='가격 조정 대기',action_class='WAIT',plan_sha256=ticker+'-plan')
    return dict(message_id=ticker,generation_id=gen,plan_sha256=row['plan_sha256'],summary_row=row)


def test_summary_partial_includes_omitted_and_separate_action_count():
    gen='test'; subjects=('AAA','TSM'); cutoff='2026-11-27T08:10:00+09:00'
    omitted={'TSM':{'status':'B2_UNISSUED_TIMEOUT'}}
    details=[_detail('AAA',gen)]
    summary=summary_message(market='us',generation=gen,subjects=subjects,messages=details,
        omitted=omitted,completed='2026-11-25',cutoff=cutoff)
    assert '신규매수 검토 가능 0' in summary['text']
    assert '기업·가격 매력 1' in summary['text']
    assert 'TSM — B2 타임아웃' in summary['text']
    messages=[dict(message_id='MARKET_US'),summary,*details]
    verify_summary_message(messages=messages,market='us',subjects=subjects,omitted=omitted,
        expected_cutoff=cutoff,expected_generation=gen,expected_completed='2026-11-25')
    with pytest.raises(ValueError):
        verify_summary_message(messages=messages,market='us',subjects=subjects,omitted=omitted,
            expected_cutoff='2026-11-28T08:10:00+09:00')
    summary['text']+=' 변경'
    with pytest.raises(ValueError):
        verify_summary_message(messages=messages,market='us',subjects=subjects,omitted=omitted)


def test_telegram_long_preview_keeps_all_content_and_utf16_limit():
    lines=[f'종목{i} 📈 관찰 조건은 유지한다.' for i in range(900)]
    text='\n'.join(lines)
    parts=telegram_render_parts(text)
    assert len(parts)>1
    assert all(len(part.encode('utf-16-le'))//2<=4096 for part in parts)
    joined='\n'.join(part.split('\n',1)[1] for part in parts)
    assert all(line in joined for line in lines)
    assert telegram_render_parts('짧은 문안')==['짧은 문안']
