"""One P3C focused run and one synthetic separate-process Cold; no live Owner."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from app.services import wm_period_currentness as wm
from app.services import registered_source_batch as b
from app.services.scoped_source_plan import ScopedStockRead
from app.services.current_scoped_source_dispatch import CurrentScopedRequestPlan
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor
from app.services.sealed_native_bridge import require_complete_stock_window
from app.services.unified_stock_acquisition import validate_role
from app.services.unified_snapshot_contract import digest,encoded

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT.parents[1]/'maintenance/20261104-p3c-wm-chain'
EXTERNAL=Path('/Users/sskim/Codex/ohlcv-analyst')

def write(path,value,raw=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if raw else encoded(value))

@pytest.fixture(scope='module')
def sample(tmp_path_factory):
    root=tmp_path_factory.mktemp('p3c-synthetic-chain');capture=root/'dispatch';stocks=root/'worker/stocks'
    manifest=json.loads((ROOT/'ops/source-parent-candidates/p3c-wm-chain-v1.json').read_bytes())
    pins=manifest['original_external_code'];parser=wm.pure_parser(EXTERNAL,pins)
    frozen='2026-11-04T00:57:00+00:00';observed='2026-11-04T00:58:00+00:00'
    reads=[];sources=[];rows=[];descriptors=[];raw_by_sha={};wire_by_entry={}
    for market,exchange,subject in (('kr','KRX','910001'),('us','NY','FICTIONAL')):
        for timeframe in ('weekly','monthly'):
            api=({'weekly':'ka10082','monthly':'ka10083'} if market=='kr' else {'weekly':'usa06013','monthly':'usa06014'})[timeframe]
            role='adjusted_'+timeframe;entry=f'{market}:{subject}:{role}'
            read=ScopedStockRead(entry_id=entry,market=market,subject=subject,
                canonical_security_id='fictional-'+market,provider='kiwoom',exchange=exchange,
                route='/api/dostk/chart' if market=='kr' else '/api/us/chart',api_id=api,
                role=role,timeframe=timeframe,adjusted=True,count=3,max_pages=2,
                query_date='20261104',latest_completed_session='2026-11-03',market_state='closed')
            labels=('20261019','20261026','20261102') if timeframe=='weekly' else ('20260901','20261001','20261102')
            records=[dict(dt=d,open_pric='10',high_pric='12',low_pric='9',cur_prc='11',trde_qty='10') for d in labels]
            key='result_list' if market=='us' else 'stk_stk_pole_chart_qry' if timeframe=='weekly' else 'stk_mth_pole_chart_qry'
            raw=encoded({key:records,'return_code':0});bars=parser._normalize_rows(records,3)
            payload=dict(stk_cd=subject,upd_stkpc_tp='1')
            if market=='us':payload.update(stex_tp=exchange,strt_dt='',exrt_appl_tp='0')
            else:payload.update(base_dt='20261104')
            request=dict(method='POST',route=read.route,api_id=api,payload=payload,
                continuation=dict(cont_yn='N',next_key=''))
            wire=dict(method='POST',url='https://api.kiwoom.com'+read.route,
                headers=[['api-id',api],['content-type','application/json;charset=UTF-8']],body=encoded(payload).decode())
            descriptor=FreshRequestDescriptor(generation_id='P3C_SYNTHETIC',logical_request_id=entry+':page1',
                provider='kiwoom',source_family='stock',role_id='stock:'+entry,market=market,subject=subject,
                endpoint_operation=api,request_json=encoded(wire).decode(),target_period='2026-11-03',
                mandatory=True,group_id=entry+':pages',page_ordinal=1,max_pages=2,document_ordinal=1,
                max_documents=1,timeout_seconds=60,transient_retry_max=0,raw_path='raw/'+entry+':page1/source.body',
                normalizer='SYNTHETIC_READBACK_NOT_LIVE',consumer_role='stock:'+entry,
                owner_sha256='a'*64,config_identity_sha256='b'*64)
            descriptors.append(descriptor);wire_by_entry[entry]=wire;raw_by_sha[hashlib.sha256(raw).hexdigest()]=raw
            ordinal=len(reads)+1
            page=dict(provider='kiwoom',entry_id=entry,page_ordinal=1,request=request,request_sha256=digest(request),
                requested_at=frozen,received_at=observed,http_status=200,artifact=f'raw-{ordinal:03d}.json',
                source_sha256=hashlib.sha256(raw).hexdigest(),response_continuation=dict(cont_yn='N',next_key=''))
            source=dict(run_id='P3C_SYNTHETIC',acquisition_id='SYNTHETIC_CAPTURE',entry=read.model_dump(mode='json'),
                started_at=frozen,completed_at=observed,status='CAPTURED',pages=[page],
                normalized_artifact=f'role-{ordinal:03d}.normalized.json',normalized_sha256=digest(bars))
            write(stocks/page['artifact'],raw,True);write(stocks/source['normalized_artifact'],bars)
            reads.append(read);sources.append(source);rows.append(bars)
    stock_value=dict(contract='SYNTHETIC_SCOPED_CAPTURE_NOT_LIVE',run_id='P3C_SYNTHETIC',
        acquisition_id='SYNTHETIC_CAPTURE',frozen_at=frozen,reads=[r.model_dump(mode='json') for r in reads])
    stock=SimpleNamespace(run_id='P3C_SYNTHETIC',acquisition_id='SYNTHETIC_CAPTURE',
        frozen_at=datetime.fromisoformat(frozen),model_dump=lambda **_:stock_value)
    plan=CurrentScopedRequestPlan(generation_id='P3C_SYNTHETIC',code_sha='a'*40,policy_schema_sha256='b'*64,
        frozen_at=datetime.fromisoformat(frozen),descriptors=tuple(descriptors),
        mandatory_roles=tuple(d.role_id for d in descriptors),parent_receipt_sha256='c'*64)
    replays=[dict(entry_id=r.entry_id,status='PASS',normalized_sha256=digest(bars),network_calls=0) for r,bars in zip(reads,rows)]
    receipts=[];artifacts=[];physical={}
    for n,(read,source,bars,descriptor) in enumerate(zip(reads,sources,rows,descriptors),1):
        source['plan_sha256']=digest(stock_value)
        validation=validate_role(stock,read,source,stocks)
        window=require_complete_stock_window(read,source,bars)
        proof=dict(status='ORIGINAL_SOURCE_ROLE_REPLAY_PASS',two_original_owner_replays='PASS',
            original_role_validation=validation,original_window_validation=window,requested_count_reached=True)
        period=wm.capture_period_proof(bars,read=read,receipt=source,original_proof=proof,
            cutoff=stock.frozen_at,parser_pins=pins)
        receipt=dict(contract='current-scoped-role-source-receipt-v2-wm',consumer='SCOPED_SOURCE_ONLY',
            allowed_use='BOUND_SOURCE_ROWS_ONLY',entry_id=read.entry_id,security_id=read.canonical_security_id,
            generation_id='P3C_SYNTHETIC',acquisition_id='SYNTHETIC_CAPTURE',
            target_session=read.latest_completed_session,parent_receipt_sha256='c'*64,
            plan_sha256=plan.plan_sha256,stock_plan_sha256=digest(stock_value),source_receipt_sha256=digest(source),
            raw_sha256=[p['source_sha256'] for p in source['pages']],normalized_sha256=digest(bars),
            proof_sha256=digest(proof),observed_at=observed,rows=3,requested_rows=3,
            period_proof=period,current_source_authority=False,source_evidence_state=period['state'],
            period_evidence=dict(source_receipt=source,stock_plan=stock_value,original_proof=proof,
                cutoff=frozen,parser_pins=pins,replays=[replays,replays]))
        for key in ('technical_signal','completed_price_authority','financial_use','valuation_use','economic_use',
                    'D01_D02','native_use','full22_native','model_use'):receipt[key]=False
        receipt['receipt_sha256']=digest(receipt);receipts.append(receipt)
        path='issued-source/'+f'{n:02d}.json';raw=encoded(bars);write(capture/path,raw,True)
        artifacts.append(dict(entry_id=read.entry_id,path=path,sha256=hashlib.sha256(raw).hexdigest()))
        key=descriptor.logical_request_id;base=capture/'receipts'/key;body=raw_by_sha[source['pages'][0]['source_sha256']]
        identity=dict(generation_id=plan.generation_id,logical_request_id=key,
            descriptor_sha256=descriptor.descriptor_sha256,plan_sha256=plan.plan_sha256,
            request_sha256=descriptor.request_semantic_sha256,role=descriptor.consumer_role)
        norm=dict(identity,source_sha256=hashlib.sha256(body).hexdigest())
        role=dict(identity,normalization_sha256=digest(norm));wire=wire_by_entry[read.entry_id]
        final=dict(identity,status='PASS',raw_sha256=hashlib.sha256(body).hexdigest(),
            normalization_sha256=digest(norm),role_binding_sha256=digest(role),
            resolved_request_sha256=hashlib.sha256(encoded(wire)).hexdigest(),
            attempts=[dict(artifact=str((base/'attempt-1.body').relative_to(capture)))])
        final['receipt_sha256']=digest(final);physical[key]=final['receipt_sha256']
        write(base/'final.json',final);write(base/'resolved-request.json',dict(request=wire,selected=None))
        write(base/'normalization.json',norm);write(base/'role-binding.json',role)
        write(capture/descriptor.raw_path,body,True);write(base/'attempt-1.body',body,True)
    value=b.Batch('P3C_SYNTHETIC',('fictional-kr','fictional-us'),('adjusted_weekly','adjusted_monthly'),
        (('kr','2026-11-03'),('us','2026-11-03')),(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),8)
    data=dict(contract='registered-source-batch-cold-v1',batch_id=value.batch_id,batch=value.public(),
        batch_sha256=digest(value.public()),capture=str(capture),plan=plan.model_dump(mode='json'),
        receipts=receipts,artifacts=artifacts,physical_receipts=physical,
        expected_reads=[r.model_dump(mode='json') for r in reads],source_pins=manifest['source_pins'],
        external_root=str(EXTERNAL),external_pins=pins,test_only=True)
    def reader(artifact):
        raw=(capture/artifact['path']).read_bytes();return raw,json.loads(raw)
    context=dict(stocks_root=stocks,external_root=EXTERNAL,sealed_raw=lambda sha:raw_by_sha[sha],expected_parser_pins=pins)
    return root,data,reader,context

def test_retained_four_api_examples_are_observed_not_official():
    result=json.loads((TASK/'EXISTING_DWM_COMPARISON.json').read_bytes())
    assert len(result['APIs'])==4 and result['financial_HTTP']==0
    for api in result['APIs']:
        assert api['status']=='OBSERVED_EXACT_HISTORICAL_EXAMPLES' and len(api['examples'])==3
        assert all(all(e['exact_fields'].values()) and e['first_session_label'] for e in api['examples'])
        assert api['official'] is False and api['current_source_authority'] is False

def test_positive_source_only_and_negative_mutations_in_one_validation(sample):
    root,data,reader,context=sample
    result=b.validate_cold_roles(data,reader,wm_context=context)
    assert len(result['roles'])==4 and result['new_live_authority'] is False
    assert all(r['period']['current_source_authority'] is False for r in result['roles'])
    mutations=('raw_hash','date','period_count','parser_pin','generation','exchange','api','version','replay','missing','model_use')
    for mutation in mutations:
        altered=deepcopy(data);r=altered['receipts'][0]
        if mutation=='raw_hash':r['raw_sha256']=['0'*64]
        elif mutation=='date':r['period_proof']['diagnostic']['last_source_label']='2026-11-03'
        elif mutation=='period_count':r['period_proof']['completed_rows']=3
        elif mutation=='parser_pin':r['period_evidence']['parser_pins']['app/providers/kiwoom.py']['sha256']='0'*64
        elif mutation=='generation':r['generation_id']='OTHER'
        elif mutation=='exchange':altered['expected_reads'][0]['exchange']='NY'
        elif mutation=='api':altered['expected_reads'][0]['api_id']='usa06013'
        elif mutation=='version':r['contract']='current-scoped-role-source-receipt-v1'
        elif mutation=='replay':r['period_evidence']['replays'][1][0]['status']='GAP'
        elif mutation=='missing':del r['period_evidence']['source_receipt']
        else:r['model_use']=True
        r.pop('receipt_sha256');r['receipt_sha256']=digest(r)
        with pytest.raises((ValueError,KeyError,TypeError)):
            b.validate_cold_roles(altered,reader,wm_context=context)

def test_one_separate_original_cold_process_no_live_parent(sample):
    root,data,reader,context=sample
    request=root/'cold-input.json';write(request,data)
    process=subprocess.run(['/Users/sskim/Codex/thesis-monitor/.venv/bin/python','-I','-B',
        str(ROOT/'scripts/official_source_batch_cold.py'),str(request),hashlib.sha256(request.read_bytes()).hexdigest()],
        capture_output=True,timeout=60,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},cwd=root)
    receipt=dict(exit=process.returncode,stdout=process.stdout.decode(),stderr=process.stderr.decode(),
        request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),test_only=True,
        live_Parent='NOT_RUN',current_Owner_issued=0)
    write(TASK/'COLD_PROCESS_RECEIPT.json',receipt)
    assert process.returncode==0 and not process.stderr,receipt
    value=json.loads(process.stdout)
    assert value['pid']!=os.getpid() and value['test_only'] is True
    assert len(value['roles'])==4 and value['HTTP']==value['DB']==value['models']==0
    assert value['new_live_authority'] is False

def test_candidate_cli_is_bound_but_installed_manifest_not_changed():
    path=ROOT/'scripts/official_source_canary_v3.py'
    scope={'__file__':str(path),'__name__':'p3c_candidate_review'}
    exec(compile(path.read_bytes(),str(path),'exec'),scope)
    candidate=ROOT/'ops/source-parent-candidates/p3c-wm-chain-v1.json'
    h=hashlib.sha256(candidate.read_bytes()).hexdigest()
    m,_=scope['validate_manifest'](candidate,h,candidate=True)
    assert m['default_enabled'] is False and m['owner_approved'] is False
    release=json.loads((ROOT/'ops/source-parent-candidates/p3c-batch-release-v2.json').read_bytes())
    old=ROOT/'ops/manual-source-parent-v3.json'
    assert hashlib.sha256(old.read_bytes()).hexdigest()==release['original_v3_manifest_sha256']
    assert release['manifest_candidate']['sha256']==h
    assert set(release['new_pins'])=={
        'app/services/registered_source_batch.py','app/services/wm_period_currentness.py',
        'app/services/current_scoped_source_results.py','scripts/official_source_batch.py',
        'scripts/official_source_batch_cold.py','scripts/official_source_canary_v3.py'}
    with pytest.raises(ValueError):scope['validate_manifest'](candidate,h)
