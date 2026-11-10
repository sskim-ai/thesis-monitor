import asyncio
from copy import deepcopy
from datetime import date,datetime,timezone
import hashlib,importlib.util,json,sys
from pathlib import Path
import httpx
import pytest

from app.services.krx_source_only import (
    issue_source_only_parent,collect_source_only,replay_source_only,source_only_adapter,POLICY,
)
from app.services.unified_aggregate_receipt import AggregateReceipt,verify_aggregate

ROOT=Path(__file__).resolve().parents[3]
DATES=(date(2026,11,9),date(2026,11,10))
CUTOFF=datetime.fromisoformat('2026-11-10T08:10:00+09:00')

def rows(day,session='야간',close='101.00',contract='A016C000',maturity='202612'):
    return dict(BAS_DD=day,PROD_NM='코스피200 선물',MKT_NM=session,ISU_CD=contract,
        ISU_NM=f'코스피200 F {maturity} ({"주간" if session=="정규" else "야간"})',
        TDD_OPNPRC='100.00',TDD_HGPRC='103.00',TDD_LWPRC='99.00',TDD_CLSPRC=close,
        CMPPREVDD_PRC='1.00',ACC_TRDVOL='100')

def transport(kind='ok',calls=None):
    calls=calls if calls is not None else []
    def send(request):
        calls.append(dict(method=request.method,route=str(request.url.copy_with(query=None)),params=dict(request.url.params)))
        if len(calls)==1:
            if kind=='timeout':raise httpx.ReadTimeout('fixture',request=request)
            if kind in ('401','403','429','302','500','201'):return httpx.Response(int(kind),content=b'fixture',headers={'Location':'https://unapproved.invalid/'})
            if kind=='bad_json':return httpx.Response(200,content=b'{invalid')
            if kind=='empty':return httpx.Response(200,json={'OutBlock_1':[]})
            if kind=='secret':return httpx.Response(200,json={'echo':'fixture-credential-not-for-export'})
            if kind=='wrong_date':return httpx.Response(200,json={'OutBlock_1':[rows('20261108','정규','100.00')]})
        day=request.url.params['basDd']
        r=rows(day,'정규' if day=='20261109' else '야간','100.00' if day=='20261109' else '101.00')
        if day=='20261110':
            if kind=='provider_conflict':r['CMPPREVDD_PRC']='9.00'
            if kind=='rollover':r['ISU_CD']='OTHER';r['ISU_NM']='코스피200 F 202703 (야간)'
        return httpx.Response(200,json={'OutBlock_1':[r]})
    return httpx.MockTransport(send)

def capture(tmp_path,kind='ok',calls=None):
    parent=issue_source_only_parent(root=tmp_path/'wire',run_id='C22S_SYNTHETIC',exact_dates=DATES,cutoff=CUTOFF)
    value=asyncio.run(collect_source_only(parent,transport=transport(kind,calls),api_key='fixture-credential-not-for-export'))
    return parent,value

def test_v4_real_dataclass_lineage_old_failure_and_new_pass(tmp_path):
    parent,value=capture(tmp_path)
    assert value['status']=='SOURCE_ONLY_DAILY_PASS',value
    obs=value['provider_value']['observations']
    flat=[{**o,**o['raw_payload'],'retrieved_at':value['available_at']} for o in obs]
    spec=importlib.util.spec_from_file_location('c22r_original_night',ROOT/'work/thesis-monitor-c22r-v1-20261110/app/services/night_futures.py')
    old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
    before=old.night_futures_context_row(old.summarize_night_futures({'observations':flat}).items[0])
    required={'night_trade_date','regular_reference_date','observation_time_kst'}
    assert required.isdisjoint(before)
    from app.services.official_night_market_eligibility_service import night_market_eligibility
    assert not night_market_eligibility(before,market='us',assessment_date='2026-11-10',completed_session_date='2026-11-09')['eligible']
    after=value['source']['night_futures'][0]
    assert required <= after.keys() and all(value['gates'][0]['eligible'] for _ in [0])
    assert after['night_timeframes']['weekly']['return_pct'] is None
    assert after['night_timeframes']['monthly']['return_pct'] is None
    assert value['numeric_audit']['status']=='PASS' and '일봉' in value['text']
    receipt=AggregateReceipt.model_validate_json((parent.root/'aggregate.json').read_bytes())
    graph=verify_aggregate(parent.root,receipt,policy=POLICY,cutoff=receipt.received_at)
    projected=source_only_adapter(root=parent.root,plan_sha256=parent.plan_sha256).project_aggregate_and_validate(graph,receipt.received_at)
    assert projected.eligible and projected.value==value
    assert value['full_market_parent'] is value['model_use'] is value['production'] is False

@pytest.mark.parametrize('kind',['401','403','429','302','500','201','timeout','bad_json','empty','wrong_date'])
def test_exact_first_error_stops_without_redirect_or_retry(tmp_path,kind):
    calls=[];parent,value=capture(tmp_path,kind,calls)
    assert len(calls)==1 and value['physical_HTTP']==1
    assert len(list(parent.root.glob('read-*.response.json')))==1
    assert value['status']=='SOURCE_ONLY_PARTIAL'
    assert not value['source']['night_futures']

def test_exact_two_requests_and_parent_reuse_default_off(tmp_path):
    parent=issue_source_only_parent(root=tmp_path/'off',run_id='off',exact_dates=DATES,cutoff=CUTOFF)
    with pytest.raises(ValueError,match='default_OFF'):asyncio.run(collect_source_only(parent))
    calls=[];p,v=capture(tmp_path/'good','ok',calls)
    assert [r['params'] for r in calls]==[{'basDd':'20261109'},{'basDd':'20261110'}]
    assert all(r['method']=='GET' and r['route']=='https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd' for r in calls)
    assert v['physical_HTTP']==2 and len(list(p.root.glob('read-*.response.json')))==2
    with pytest.raises(ValueError,match='reused'):asyncio.run(collect_source_only(p,transport=transport()))

def test_late_received_clock_not_backdated_to_cutoff(tmp_path):
    p,v=capture(tmp_path)
    receipts=[json.loads(f.read_bytes()) for f in sorted(p.root.glob('read-*.response.json'))]
    assert v['available_at']==receipts[-1]['received_at']
    assert datetime.fromisoformat(v['available_at'])>CUTOFF
    assert v['late_capture'] and not v['eligible_at_requested_cutoff']
    assert v['provider_published_at'] is None and '실제 수신:' in v['text']
    with pytest.raises(ValueError,match='after_cutoff'):
        replay_source_only(root=p.root,receipt=json.loads((p.root/'aggregate.json').read_bytes()),plan_sha256=p.plan_sha256,cutoff=CUTOFF)

@pytest.mark.parametrize('kind',['provider_conflict','rollover'])
def test_pair_conflict_is_daily_gap_not_fake_price(tmp_path,kind):
    p,v=capture(tmp_path,kind)
    assert v['status']=='SOURCE_ONLY_PARTIAL' and v['physical_HTTP']==2
    assert not v['source']['night_futures']

@pytest.mark.parametrize('field',['night_trade_date','regular_reference_date','observation_time_kst'])
def test_context_drop_fails_actual_numeric_consumer(tmp_path,field):
    from app.services.market_numeric_claim_service import numeric_catalog
    p,v=capture(tmp_path);source=deepcopy(v['source']);row=source['night_futures'][0];row.pop(field)
    source['fact_catalog'][0]['fields']=row
    cat=numeric_catalog(source,market='us',assessment_date='2026-11-10',eligible_refs=[row['fact_id']])
    assert not any(c['claim_type']=='OFFICIAL_NIGHT' for c in cat['claims'])

@pytest.mark.parametrize('kind',['body','projection','plan','child_receipt'])
def test_transitive_chain_tamper_cannot_be_rehashed_into_acceptance(tmp_path,kind):
    p,v=capture(tmp_path)
    receipt=json.loads((p.root/'aggregate.json').read_bytes())
    name={'body':'read-0002.body','projection':'projection.json','plan':'source-only-plan.json','child_receipt':'read-0001.response.json'}[kind]
    path=p.root/name;path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):replay_source_only(root=p.root,receipt=receipt,plan_sha256=p.plan_sha256,cutoff=datetime.now(timezone.utc))

def test_secret_echo_withheld_and_no_second_GET(tmp_path):
    calls=[];p,v=capture(tmp_path,'secret',calls)
    assert v['status']=='SOURCE_ONLY_BODY_WITHHELD' and len(calls)==1
    assert not list(p.root.glob('*.body'))
    assert all(b'fixture-credential-not-for-export' not in f.read_bytes() for f in p.root.iterdir() if f.is_file())

def test_symlink_parent_and_duplicate_dates_reject_before_dispatch(tmp_path):
    (tmp_path/'link').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):issue_source_only_parent(root=tmp_path/'link'/'unsafe',run_id='a',exact_dates=DATES,cutoff=CUTOFF)
    with pytest.raises(ValueError):issue_source_only_parent(root=tmp_path/'dup',run_id='a',exact_dates=(DATES[0],DATES[0]),cutoff=CUTOFF)
