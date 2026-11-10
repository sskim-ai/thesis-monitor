from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest

from app.services.confirmed_sector_taxonomy import VERSION, render_confirmed_sectors, verify_retained_sector_output
from app.services.dated_market_legacy_adapter import render_retained_component_sectors, component_sector_source
from app.services.dated_market_message_slots import render_retained_market_message, verify_retained_market_message
from app.services.market_display_plan import build_display_plan, render_display_plan, final_display_audit
from app.services.unified_snapshot_contract import digest

R=Path(__file__).resolve().parents[3]
ARCHIVE=R/'maintenance/20261110-c22m-v1/C22M_V1_SOURCE_FIELD_RECOVERY_AND_E2E_PLAN.zip'
SHA='d0e1e948425d231ac450803ac960533083ef7ceb04fa50a0072ee545aa429ff5'

def custody(market):
    return dict(archive_path=ARCHIVE,archive_sha256=SHA,
        reference_path=R/f'maintenance/20261106-c15/C15_{market.upper()}_DATED_SOURCE_REFERENCE.json',market=market,enabled=True)

def result(market):
    return render_retained_component_sectors(**custody(market),taxonomy_version=VERSION)

@pytest.mark.parametrize('market,provider',[('us','ohlcv_analyst'),('kr','kiwoom_rest')])
def test_correct_provider_and_complete_custody_audit(market,provider):
    output=result(market)
    assert all(x['provider']==provider for x in output['classification_ledger'])
    audit=verify_retained_sector_output(output,**custody(market))
    assert audit['status']=='PASS' and audit['full_market_parent'] is False
    assert '상대 강세 TOP3' in output['text'] and '상대 약세 BOTTOM3' in output['text']

@pytest.mark.parametrize('change',['provider','row_sha','date','text','missing','order'])
def test_complete_auxiliary_mutation_even_with_rehash_rejected(change):
    output=result('kr')
    if change=='provider':output['auxiliary'][0]['binding']['provider']='ohlcv_analyst'
    elif change=='row_sha':output['auxiliary'][0]['binding']['source_row_sha256']='f'*64
    elif change=='date':output['auxiliary'][0]['binding']['session']='2026-11-10'
    elif change=='text':output['text']+='임의 숫자 12.00%'
    elif change=='missing':output['auxiliary'].pop()
    else:output['auxiliary'].reverse()
    output['text_sha256']=hashlib.sha256(output['text'].encode()).hexdigest()
    with pytest.raises(ValueError,match='complete_output_mismatch'):
        verify_retained_sector_output(output,**custody('kr'))

def test_us_provider_laundering_in_source_rejected():
    r=json.loads(custody('us')['reference_path'].read_bytes())
    next(x for x in r['value']['observations'] if x['series_code']=='SOXX')['provider']='kiwoom_rest'
    r['value_sha256']=digest(r['value'])
    with pytest.raises(ValueError,match='provider_mismatch'):render_confirmed_sectors(r)

def test_size_style_segment_labels_and_zero_count():
    output=result('kr')
    rows={x['binding']['raw_symbol']:x for x in output['auxiliary']}
    assert '규모별' in rows['138']['text']
    assert '기업유형' in rows['143']['text']
    assert '구성범위' in rows['151']['text']
    assert '604' not in rows and '605' not in rows
    assert any(x['raw_symbol']=='021' and x['reason']=='financial_parent_child_overlap_unresolved' for x in output['classification_ledger'])

@pytest.mark.parametrize('market',['us','kr'])
def test_single_slot_message_and_full_output_binding(market):
    kwargs=custody(market)
    if market=='kr':kwargs.update(flow_archive_path=R/'maintenance/20261110-c22m-continuation-v2/C22M_CONTINUATION_V2_LEGACY_MARKET_RESULT.zip',
        flow_archive_sha256='be8209af5a7d65cb729a1342c805d51cf72bf9ec93577f869d920ec4a9765b16')
    msg=render_retained_market_message(**kwargs)
    assert verify_retained_market_message(msg,**kwargs)['status']=='PASS'
    assert 'Original sector observations exist' not in msg['text']
    assert '외국인 수급: 자료 부족' not in msg['text']
    assert len({s['slot_id'] for s in msg['slots']})==len(msg['slots'])
    if market=='kr':assert len([s for s in msg['slots'] if s['slot_id'].startswith('FLOW_')])==6
    msg['text']+='섹터 TOP3: 자료 부족'
    msg['text_sha256']=hashlib.sha256(msg['text'].encode()).hexdigest()
    with pytest.raises(ValueError,match='complete_message_mismatch'):verify_retained_market_message(msg,**kwargs)

def test_current_canonical_opt_in_preserves_eligible_and_source():
    reference=json.loads(custody('us')['reference_path'].read_bytes())
    source=component_sector_source(reference)
    before=digest(source)
    refs=[f['fact_id'] for f in source['fact_catalog']]
    plan=build_display_plan(source,market='us',assessment_date='2026-11-05',eligible_refs=refs,sector_taxonomy_version=VERSION)
    ranked=[ref for i in plan.items if i.block_id=='sectors' for ref in i.fact_ids]
    assert all('SOXX' not in r for r in ranked)
    assert any(i.block_id=='sector_auxiliary' and i.proof['provider']=='ohlcv_analyst' for i in plan.items)
    text=render_display_plan(plan,source,'시장 판단은 유보합니다.')
    assert final_display_audit(text,plan,source,'시장 판단은 유보합니다.')['status']=='PASS'
    assert final_display_audit(text+' 임의 숫자',plan,source,'시장 판단은 유보합니다.')['status']=='FAIL'
    empty=build_display_plan(source,market='us',assessment_date='2026-11-05',eligible_refs=[],sector_taxonomy_version=VERSION)
    assert not any(i.block_id=='sector_auxiliary' for i in empty.items)
    assert digest(source)==before

def test_current_projection_stale_sector_unavailable():
    source=component_sector_source(json.loads(custody('us')['reference_path'].read_bytes()))
    source['session'].update(assessment_date='2026-11-09',latest_completed_regular_session_date='2026-11-09')
    plan=build_display_plan(source,market='us',assessment_date='2026-11-09',
        eligible_refs=[f['fact_id'] for f in source['fact_catalog']],sector_taxonomy_version=VERSION)
    assert all(i.status=='UNAVAILABLE' for i in plan.items if i.block_id=='sectors')
    assert not any(i.block_id=='sector_auxiliary' for i in plan.items)


def test_current_kr_projection_auxiliary_groups_and_future_refs():
    source=component_sector_source(json.loads(custody('kr')['reference_path'].read_bytes()))
    refs=[f['fact_id'] for f in source['fact_catalog']]
    plan=build_display_plan(source,market='kr',assessment_date='2026-11-06',eligible_refs=refs,sector_taxonomy_version=VERSION)
    ranked=[ref for i in plan.items if i.block_id=='sectors' for ref in i.fact_ids]
    assert not any(ref.endswith((':027',':106',':021')) for ref in ranked)
    assert len([i for i in plan.items if i.block_id=='sector_auxiliary'])==3
    future=deepcopy(source)
    for fact in future['fact_catalog']:fact['as_of_date']='2026-11-10'
    future_plan=build_display_plan(future,market='kr',assessment_date='2026-11-06',eligible_refs=refs,sector_taxonomy_version=VERSION)
    assert not any(i.block_id=='sector_auxiliary' for i in future_plan.items)
    assert all(i.status=='UNAVAILABLE' for i in future_plan.items if i.block_id=='sectors')
