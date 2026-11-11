import csv
import io
import json
from copy import deepcopy
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import shutil

import pytest
from app.services import broker_night_seed_history as h
from app.services.broker_night_us_consumer import us_broker_night_reference
from app.services.us_full_message_service import render_us_full_market_message
from app.services.market_cross_section_service import MarketFlowFact
from app.services.unified_aggregate_owners import validate_aggregate_flow_rows
from app.services.source_only_four_panel import render_four_panel

R=Path(__file__).resolve().parents[3]
TASK=R/'maintenance/20261111-c22w-v2'
HISTORY=TASK/'result/operational-history/broker-seed-v1/history.json'
CSV=Path(__file__).parent/'fixtures/c22w_broker_night_seed.csv'
AT=datetime(2026,11,11,5,tzinfo=timezone.utc)

def store(tmp_path):
    p=tmp_path/'history.json';p.write_bytes(HISTORY.read_bytes());return p

def update(path,timeframe,amount='800.00',kind='PROGRESS_SNAPSHOT'):
    row=next(r for r in csv.DictReader(io.StringIO(CSV.read_text(encoding='utf-8-sig'))) if r['timeframe']==timeframe and r['chart_status']=='IN_PROGRESS')
    row['close']=amount;row['volume']=str(int(row['volume'])+1)
    row['pct_vs_previous_same_timeframe_night_close']=str(((Decimal(amount)/Decimal(row['previous_same_timeframe_night_close'])-1)*100).quantize(Decimal('.0001')))
    row['screenshot_sha256']=h.sha((timeframe+amount).encode());row['source_zip_sha256']='e'*64
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=row);w.writeheader();w.writerow(row)
    previous=next((b,pin) for k,(b,pin) in h._versions(h.load_history(path)).items() if k[:4]==(row['instrument_root'],row['contract_maturity'],timeframe,row['broker_chart_date']))
    meta={row['screenshot_sha256']:dict(kind=kind,reason='new source snapshot',previous_revision_sha256=previous[1],
        observed_at='2026-11-11T04:50:00+00:00',received_at='2026-11-11T04:51:00+00:00')}
    return out.getvalue().encode(),meta


def test_legacy_57_noop_then_progress_versions_and_pit(tmp_path):
    p=store(tmp_path);before=p.read_bytes();original=h.load_history(p)
    assert h.commit_seed(history_path=p,raw=CSV.read_bytes(),available_at=AT)['unchanged']==57 and p.read_bytes()==before
    for tf in ('WEEKLY','MONTHLY'):
        raw,meta=update(p,tf)
        result=h.commit_seed(history_path=p,raw=raw,available_at=AT,revision_metadata=meta)
        assert result['new_revisions']==1 and result['inserted']==0
        assert h.commit_seed(history_path=p,raw=raw,available_at=AT,revision_metadata=meta)['status']=='NOOP'
    latest=h.load_history(p);assert latest['bars']==original['bars'] and len(latest['revisions'])==2
    assert h.commit_seed(history_path=p,raw=CSV.read_bytes(),available_at=AT)['unchanged']==57
    old=h.render_broker_history(latest,instrument_root='KOSPI200',contract_maturity='2026-12',cutoff=AT.replace(hour=4))
    new=h.render_broker_history(latest,instrument_root='KOSPI200',contract_maturity='2026-12',cutoff=AT)
    assert [b['close'] for b in old['selected']]==['798.00']*3
    assert [b['close'] for b in new['selected']]==['798.00','800.00','800.00']
    assert len(list((p.parent/'revisions').glob('*.json')))==2


def test_revision_conflicts_and_immutable_chain(tmp_path):
    p=store(tmp_path);raw,meta=update(p,'WEEKLY');before=p.read_bytes()
    bad=deepcopy(meta);next(iter(bad.values()))['kind']='UNDECLARED_FINAL_REWRITE'
    assert h.commit_seed(history_path=p,raw=raw,available_at=AT,revision_metadata=bad)['status']=='QUARANTINED_NO_HISTORY_CHANGE'
    assert p.read_bytes()==before
    h.commit_seed(history_path=p,raw=raw,available_at=AT,revision_metadata=meta)
    value=h.load_history(p);value['revisions'][0]['bar']['close']='801'
    p.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='revision_chain'):h.load_history(p)


def test_future_weekly_night_end_stale_daily_and_availability(tmp_path):
    p=store(tmp_path);value=h.load_history(p)
    future=deepcopy(value);future['bars']=[dict(next(b for b in value['bars'] if b['timeframe']=='WEEKLY'),broker_chart_date='2026-12-21')]
    rendered=h.render_broker_history(future,instrument_root='KOSPI200',contract_maturity='2026-12',cutoff=AT)
    assert not rendered['selected'] and rendered['exclusions'][0]['reason']=='FUTURE_CHART_DATE'
    stale=h.render_broker_history(value,instrument_root='KOSPI200',contract_maturity='2026-12',cutoff=AT.replace(day=13))
    assert not stale['selected'][0]['current_period_match'] and not stale['current_directional']
    morning=AT.replace(hour=23,day=10,minute=10)
    assert not h.render_broker_history(value,instrument_root='KOSPI200',contract_maturity='2026-12',cutoff=morning)['selected']
    before_end=deepcopy(value);before_end['bars']=[dict(next(b for b in value['bars'] if b['timeframe']=='DAILY' and b['broker_chart_date']=='2026-11-10'),first_system_available_at='2026-11-10T19:00:00+00:00')]
    assert h.render_broker_history(before_end,instrument_root='KOSPI200',contract_maturity='2026-12',cutoff=AT.replace(day=10,hour=20))['exclusions'][0]['reason']=='NIGHT_NOT_ENDED'


def test_us_consumer_chart_date_only_optional_no_market_stop(tmp_path):
    p=store(tmp_path);reference=us_broker_night_reference(history_path=p,cutoff=AT,contract_maturity='2026-12')
    assert all(x in reference['text'] for x in ('2026-11-10','2026-11-09','2026-11-02'))
    assert all(x not in reference['text'] for x in ('2026-11-11','BAS_DD','KRX 거래일','종료일'))
    base=render_us_full_market_message({})
    bound=render_us_full_market_message({},broker_seed_history_path=p,broker_seed_cutoff=AT,broker_contract_maturity='2026-12')
    assert 'BROKER_NIGHT_REFERENCE' in bound.section_order and bound.validation_errors==base.validation_errors
    assert '과거 차트 참고' in bound.text and reference['source_kind']=='USER_BROKER_SCREENSHOT'
    p.write_text('invalid-json')
    missing=render_us_full_market_message({},broker_seed_history_path=p,broker_seed_cutoff=AT,broker_contract_maturity='2026-12')
    assert missing.validation_errors==base.validation_errors and '자료 부족' in missing.text


def test_flow_numeric_scope_and_units_are_not_weakened():
    rows=[MarketFlowFact(actor=a,market=m,net_buy_amount=100_000_000,currency='KRW',exchange_basis='KRX_NXT_INTEGRATED',
        source_unit='100M_KRW',source_unit_scale_krw=100_000_000,source_ref=f'kiwoom:ka10051:{m}:{a}:2026-11-10')
        for m in ('KOSPI','KOSDAQ') for a in ('foreign','institution','retail')]
    validate_aggregate_flow_rows(rows,session='2026-11-10')
    for attribute,bad in (('source_unit','KRW'),('market','OTHER'),('net_buy_amount',float('nan'))):
        changed=deepcopy(rows);setattr(changed[0],attribute,bad)
        with pytest.raises(ValueError):validate_aggregate_flow_rows(changed,session='2026-11-10')
    with pytest.raises(ValueError):validate_aggregate_flow_rows(rows+rows[:1],session='2026-11-10')


def test_four_panel_sources_bound_and_night_only_in_us(tmp_path):
    p=store(tmp_path)
    us=json.loads((R/'maintenance/20261110-c22r-v1/result/REAL_US_MARKET_NO_SEND.json').read_bytes())
    kr=json.loads((R/'maintenance/20261111-c22v-v1/KR_MARKET_MESSAGE.json').read_bytes())
    doc=render_four_panel(us=us,kr=kr,mu='과거 MU',samsung='과거 삼성전자',history_path=p,cutoff=AT,contract_maturity='2026-12')
    assert doc['order']==['US Market','MU','KR Market','005930'] and doc['text'].count('KOSPI200 야간선물')==1
    assert doc['text'].index('KOSPI200 야간선물')<doc['text'].index('## MU')
    changed=deepcopy(kr);changed['text']=changed['text'].replace('5,239.13','5,240.13')
    with pytest.raises(ValueError,match='message_binding'):render_four_panel(us=us,kr=changed,mu='',samsung='',history_path=p,cutoff=AT,contract_maturity='2026-12')


def test_completed_flow_native_date_document_and_raw_hash_reject(tmp_path):
    from app.services.completed_date_aggregate_flows import project_completed_date_flows
    task=R/'maintenance/20261111-c22x-v1';doc=json.loads((task/'official-doc/RECEIPT.json').read_bytes())
    capture=json.loads((R/'maintenance/20261111-c22v-v1/MARKET_KR_RESULT.json').read_bytes())
    bundle=json.loads(Path(capture['bundle_path']).read_bytes())
    root=R/'maintenance/20261111-c22v-v1/private-source/kr/kr-market'
    arguments=dict(root=root,session='2026-11-10',cutoff=AT,original_observed_at=datetime.fromisoformat(bundle['cutoff']),
        official_source=task/'official-doc/get_domestic_sector_investor_net_buy.py',official_sha256=doc['source_sha256'],official_commit=doc['commit'])
    with pytest.raises(ValueError,match='market_session'):project_completed_date_flows(**dict(arguments,session='2026-11-11'))
    with pytest.raises(ValueError,match='document_pin'):project_completed_date_flows(**dict(arguments,official_sha256='0'*64))
    changed=tmp_path/'raw';shutil.copytree(root,changed)
    response=next(json.loads(p.read_bytes()) for p in changed.glob('*.response.json') if json.loads(p.read_bytes())['read_key']=='KOSPI:ka10051')
    body=changed/response['artifact'];body.write_bytes(body.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash|artifact'):project_completed_date_flows(**dict(arguments,root=changed))
