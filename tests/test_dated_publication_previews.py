from copy import deepcopy
import importlib.util,json
from pathlib import Path
import pytest
from app.services.dated_research_model import digest
from app.services.dated_split_research_consumer import validate_message
from app.services.dated_publication_previews import stock_short,market_preview,combined_preview,check_lane_receipts

@pytest.fixture(scope='module')
def cases():
    p=Path(__file__).resolve().parents[3]/'maintenance/20261110-c22l-v3/inputs.py'
    s=importlib.util.spec_from_file_location('c22l_inputs',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m.load_cases()[0]

def args(c):return {k:v for k,v in c.items() if k!='original_consumer'}
def view(c):return json.loads(c['preview_raw'])['source_view']

def test_five_original_consumers_strong_publication_and_short_replay(cases):
    for c in cases.values():
        original=deepcopy(c['original_consumer'])
        proof=validate_message(original,view=view(c),source_evidence=args(c))
        assert proof['publication_pass']
        a=stock_short(original,view=view(c),source_evidence=args(c));b=stock_short(original,view=view(c),source_evidence=args(c))
        assert a==b and a['content_sha256']==digest(a['text'].encode())
        assert a['original_citations']==original['split_panel']['citations']
        assert 'ref=' not in a['text'] and 'SHA=' not in a['text']

@pytest.mark.parametrize('kind',[
    'split_label','split_confidence','split_refs','split_pro','split_con','split_citations_empty',
    'split_citations_order','numeric_value','source_sha','prior_label','prior_confidence','prior_refs',
    'prior_citations_empty','company','financial_cutoff','valuation_metric','valuation_vintage',
    'valuation_period','valuation_available_at','NO_SEND','current_price','thesis'])
def test_canonical_tampering_rejected(cases,kind):
    c=cases['MU'];m=deepcopy(c['original_consumer']);a=m['split_panel']['axes']['newbuyer_fundamental_attractiveness']
    if kind=='split_label':a['state']='UNATTRACTIVE'
    elif kind=='split_confidence':a['confidence']='HIGH'
    elif kind=='split_refs':a['refs']=[]
    elif kind=='split_pro':a['pro']=[]
    elif kind=='split_con':a['con']=[]
    elif kind=='split_citations_empty':m['split_panel']['citations']=[]
    elif kind=='split_citations_order':m['split_panel']['citations'].reverse()
    elif kind=='numeric_value':m['split_panel']['citations'][0]['value']='0'
    elif kind=='source_sha':m['split_panel']['citations'][0]['source_sha256']='0'*64
    elif kind=='prior_label':m['prior_panel']['overall']['state']='SELL'
    elif kind=='prior_confidence':m['prior_panel']['holder_virtual']['confidence']='HIGH'
    elif kind=='prior_refs':m['prior_panel']['overall']['refs']=[]
    elif kind=='prior_citations_empty':m['prior_citations']=[]
    elif kind=='company':m['company_name']='ALTERED'
    elif kind=='financial_cutoff':m['financial'][0]['source_cutoff']='2099-01-01'
    elif kind=='valuation_metric':m['valuations'][0]['metric']='FY1_EPS'
    elif kind=='valuation_vintage':m['valuations'][0]['temporal']['issuer_estimate_vintage']='2099-01-01'
    elif kind=='valuation_period':m['valuations'][0]['fact']['period']='2099-01-01'
    elif kind=='valuation_available_at':m['valuations'][0]['temporal']['available_at_proven']='2099-01-01'
    elif kind=='NO_SEND':m['NO_SEND']=False
    elif kind=='current_price':m['current_price_grant']=True
    elif kind=='thesis':m['thesis_comparison']='THESIS_CONFIRMED'
    with pytest.raises(ValueError):validate_message(m,view=view(c),source_evidence=args(c))

def test_unbound_message_not_publication_and_receipt_drift_rejected(cases):
    c=cases['MU'];m=c['original_consumer']
    assert validate_message(m,view=view(c))['state']=='SOURCE_BOUND_PUBLICATION_NOT_PROVEN'
    e=args(deepcopy(c));e['split_receipt']['output_sha256']='0'*64
    with pytest.raises(ValueError,match='receipt'):validate_message(m,view=view(c),source_evidence=e)

def test_short_change_conditions_are_actual_source_condition_sentences(cases):
    c=cases['MU'];s=stock_short(c['original_consumer'],view=view(c),source_evidence=args(c))
    conditions=s['text'].split('## 판단 변경 조건',1)[1]
    assert '후속 비교 가능한 보고에서 이익 확대가 되돌려지거나' in conditions
    assert '이후 완료봉에서 일봉과 주봉의 MACD 히스토그램이' in conditions

def lane(market='us',session='2026-11-05'):
    p=dict(market=market,session=session,cutoff='2026-11-06T10:00:00+00:00',fingerprint='p',child_hashes=['h'])
    c=dict(market=market,session=session,parent_fingerprint='p',raw_sha256='h',available_at='2026-11-06T09:00:00+00:00')
    return p,c

@pytest.mark.parametrize('kind',['market','session','parent','child_sha','cutoff'])
def test_wrong_market_parent_child_session_cutoff(kind):
    p,c=lane()
    if kind=='market':c['market']='kr'
    elif kind=='session':c['session']='2026-11-06'
    elif kind=='parent':c['parent_fingerprint']='other'
    elif kind=='child_sha':c['raw_sha256']='other'
    elif kind=='cutoff':c['available_at']='2026-11-06T11:00:00+00:00'
    with pytest.raises(ValueError):check_lane_receipts(market='us',session='2026-11-05',cutoff=p['cutoff'],parent=p,children=[c])

def test_different_countries_dates_and_macro_vintages_are_not_forced_equal():
    for market,date in [('us','2026-11-05'),('kr','2026-11-06')]:
        p,c=lane(market,date)
        assert not check_lane_receipts(market=market,session=date,cutoff=p['cutoff'],parent=p,children=[c])['full_parent_issued']
    row=dict(status='PASS',value='4.2',ref='macro:yield',source_sha256='a'*64,unit='percent',period='2026-11-04',available_at='2026-11-05T12:00:00+00:00',original_owner_receipt_sha256='b'*64,is_session_price=False)
    ledger=dict(market='us',candidate_session='2026-11-05',candidate_cutoff='2026-11-06T10:00:00+00:00',fields={'US10Y':row})
    m=market_preview('us',ledger=ledger)
    assert m['fields'][4]['value']=='4.2' and m['state'].startswith('PARTIAL') and m['confidence'] is None
    assert m['fields'][0]['value'] is None and not m['full_market_parent']
    assert m==market_preview('us',ledger=ledger)
    assert combined_preview('mixed',[m])==combined_preview('mixed',[m])
