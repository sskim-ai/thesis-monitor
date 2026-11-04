"""Offline original-wire compilation and SYNTHETIC byte-only Cold replay."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

from app.services.market_component_chunks import partition_market_plan, cold_reassemble, CONTRACT
from app.services.scoped_source_plan import (ScopedConfig,ScopedSubject,HistoryCounts,
    ScopedCaptureSelection,ScopedPriceCaptureSelection,ScopedPriceCaptureSelectionV2,compile_scoped_wire_contract)
from app.services.unified_snapshot_contract import digest,encoded
from app.services.unified_run_artifacts import sha256_bytes


def wire(market,price=False,max_pages=7):
    subject=ScopedSubject(ticker='654321' if market=='kr' else 'FUTURE',market=market,
        security_id='synthetic-security',issuer_id='00000123',venue='KRX' if market=='kr' else 'NASDAQ',
        currency='KRW' if market=='kr' else 'USD')
    security=dict(ticker=subject.ticker,canonical_security_id=subject.security_id,
        exchange=subject.venue,country=market.upper(),cik='00000123',corp_code='00000123')
    history=HistoryCounts(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,unadjusted_weekly_valuation=300)
    selection=(ScopedPriceCaptureSelectionV2(contract='scoped-price-capture-selection-v2',close_security_ids=(subject.security_id,))
        if price else ScopedCaptureSelection(stock_markets=(),stock_roles=(),market_contexts=(market,),us_completed_closes=False))
    config=ScopedConfig(subjects=(subject,),kr_history=history,us_history=history,kr_max_pages=max_pages,capture_selection=selection)
    return compile_scoped_wire_contract(config=config,identities={subject.ticker:security},
        generation_id='P3F_SYNTHETIC',at=datetime.now(timezone.utc)-timedelta(seconds=2),
        code_sha='a'*40,provider_config_sha256='b'*64,retries=0),config,security


@pytest.mark.parametrize('market',['kr','us'])
def test_price_selector_keeps_original_market_wire_and_no_market_coverage(market):
    data,config,security=wire(market,True)
    rows=[d for d in data['request_plan'].descriptors if d.endpoint_operation!='credential_exchange']
    assert not data['kr_market_reads_json']!='[]' and not data['us_market_symbols']
    if market=='kr':
        assert {d.endpoint_operation for d in rows}=={'ka10081'}
        assert json.loads(json.loads(rows[0].request_json)['body'])['upd_stkpc_tp']=='1'
        assert len(data['stock_reads'])==1 and data['stock_reads'][0].count==2
        assert data['price_pairs'][0].basis=='ADJUSTED_STOCK_CHART'
        old=dict(config.model_dump(mode='json'),capture_selection=ScopedPriceCaptureSelection(
            contract='scoped-price-capture-selection-v1',close_security_ids=(security['canonical_security_id'],)).model_dump(mode='json'))
        with pytest.raises(ValueError,match='outside_us'):ScopedConfig.model_validate(old)
    else:
        assert {d.endpoint_operation for d in rows}=={'usa20590'}
        assert data['price_pairs'][0].basis=='REGULAR_STOCK_CLOSE'


def test_kr_original_price_owner_replay_not_regular_native_authority():
    from tests.test_completed_session_current_price import price_inputs
    from app.services.kr_source_close import project_source_close
    inputs=price_inputs('000660')
    before=deepcopy(inputs['receipt'])
    result=project_source_close(**inputs)
    assert result['projection']['availability']=='AVAILABLE'
    assert result['completed_regular_session_close']=='UNAVAILABLE_ADJUSTMENT_COMPATIBILITY_UNPROVEN'
    assert not result['native'] and not result['current_price_authority']
    assert inputs['receipt']==before
    inputs['receipt']['run_id']='OLD'
    with pytest.raises(ValueError):project_source_close(**inputs)


def captured_chunks(plan,chunks):
    records=[];artifacts={};ordinal=0
    now=datetime.now(timezone.utc).isoformat()
    for chunk in chunks:
        entries=[]
        for d in chunk['plan']['descriptors']:
            if d['logical_request_id']=='kiwoom:auth':continue
            ordinal+=1
            key=d['logical_request_id']
            raw=encoded(dict(SYNTHETIC=True,descriptor_id=key))
            path=chunk['chunk_id']+'/'+key.replace(':','_')+'.body'
            artifacts[path]=raw
            entries.append(dict(descriptor_id=key,descriptor_sha256=digest(d),generation_id=plan.generation_id,
                provider=d['provider'],session=d['target_period'],page_ordinal=d['page_ordinal'],
                request_sha256=sha256_bytes(d['request_json'].encode()),status='CAPTURED',http_status=200,
                physical_ordinal=ordinal,artifact=path,raw_sha256=sha256_bytes(raw),raw_bytes=len(raw),
                requested_at=now,received_at=now,response_headers={'cont-yn':'Y' if d['page_ordinal']<d['max_pages'] else 'N','next-key':'synthetic-next'}))
        records.append(dict(contract=CONTRACT,chunk_id=chunk['chunk_id'],plan_sha256=chunk['plan_sha256'],
            actual_http=len(entries)+1,entries=entries))
    return records,lambda name,sha:artifacts[name]


@pytest.mark.parametrize('market',['kr','us'])
def test_market_full_plan_partition_cold_complete_bytes_no_parent(market):
    plan=wire(market)[0]['request_plan'];before=plan.model_dump(mode='json')
    chunks=partition_market_plan(plan)
    assert sum(d.max_transport_attempts for d in plan.descriptors)>20
    assert len(chunks)>1 and all(c['maximum_physical_http']<=20 for c in chunks)
    records,reader=captured_chunks(plan,chunks)
    result=cold_reassemble(plan,chunks,records,reader)
    assert result['MarketParent']=='NOT_ISSUED'
    assert not result['native'] and not result['model_use']
    assert len(result['components'])==len(plan.descriptors)-1
    assert plan.model_dump(mode='json')==before


@pytest.mark.parametrize('mutation',['missing','duplicate','hash','session','continuation','cap'])
def test_market_chunk_mutations_rejected(mutation):
    plan=wire('kr')[0]['request_plan'];chunks=partition_market_plan(plan)
    records,reader=captured_chunks(plan,chunks)
    if mutation=='missing':records.pop()
    elif mutation=='duplicate':records[-1]=deepcopy(records[0])
    elif mutation=='hash':records[0]['entries'][0]['raw_sha256']='0'*64
    elif mutation=='session':records[0]['entries'][0]['session']='2000-01-01'
    elif mutation=='cap':chunks[0]['maximum_physical_http']=21
    else:
        row=next(r for record in records for r in record['entries']
            if r['response_headers']['cont-yn']=='N' and r['page_ordinal']>1)
        row['response_headers']={'cont-yn':'Y','next-key':'more'}
    with pytest.raises(ValueError):cold_reassemble(plan,chunks,records,reader)


def test_chunk_rejects_changed_plan_retry_and_fake_parent_promotion():
    plan=wire('us')[0]['request_plan']
    bad=plan.model_dump(mode='json');bad['descriptors'][0]['transient_retry_max']=1
    with pytest.raises(ValueError,match='retry_zero'):partition_market_plan(bad)
    chunks=partition_market_plan(plan)
    chunks[0]['MarketParent']=True
    records,reader=captured_chunks(plan,chunks)
    with pytest.raises(ValueError):cold_reassemble(plan,chunks,records,reader)


def test_original_kr49_plan_cannot_truncate_twenty_page_chain():
    plan=wire('kr',max_pages=20)[0]['request_plan']
    assert sum(d.max_transport_attempts for d in plan.descriptors)==49
    before=plan.model_dump(mode='json')
    with pytest.raises(ValueError,match='indivisible_component_exceeds_cap'):
        partition_market_plan(plan)
    assert plan.model_dump(mode='json')==before
