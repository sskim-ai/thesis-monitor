import asyncio
import json

import httpx
import pytest

from app.services.sealed_source_transport import CapturedFragment, SealedSourceTransport
from app.services.unified_snapshot_contract import digest, encoded
from scripts.r9_rev11_collect import PublicationCapture
from scripts.r9_rev11_replay import require_sealed_body
from tests.test_r9_rev11_response_slots import run_slots, wire
from tests.test_r9_rev11_sealed_dispatch import descriptor


def source_run(tmp_path):
    d = descriptor('fred:fixture')
    run = run_slots(tmp_path, (d,))
    return d, run


def test_publication_native_receipt_is_sealed_and_consumer_bound(tmp_path):
    d, run = source_run(tmp_path)
    inner = httpx.MockTransport(lambda _: httpx.Response(200, json={'observations': []}))
    transport = SealedSourceTransport(run, inner, providers={'fred'})
    capture = PublicationCapture(transport, 'fred', run.plan.generation_id, tmp_path/'pub')
    asyncio.run(capture.handle_async_request(wire(d.request_json)))
    row = capture.receipts[0]
    final = run.results[d.logical_request_id]
    assert row['sealed_final_receipt_sha256'] == final['receipt_sha256']
    assert row['artifact_sha256'] == final['raw_sha256']
    assert row['requested_at'] <= row['received_at']
    frozen = {'plan': run.plan.model_dump(mode='json')}
    # The helper's fixed dispatch root is intentional: no alternate corpus.
    run.root.rename(tmp_path/'dispatch')
    require_sealed_body(tmp_path, frozen, {'logical_results':run.results}, role=d.role_id, raw_sha256=final['raw_sha256'])
    with pytest.raises(ValueError, match='not_bound'):
        require_sealed_body(tmp_path, frozen, {'logical_results':run.results}, role='wrong', raw_sha256=final['raw_sha256'])
    (tmp_path/'dispatch'/d.raw_path).write_bytes(b'changed')
    with pytest.raises(ValueError):
        require_sealed_body(tmp_path, frozen, {'logical_results':run.results}, role=d.role_id, raw_sha256=final['raw_sha256'])


def test_fragment_receipt_never_claims_canonical_source_qualification():
    d = descriptor('fred:fixture')
    result = CapturedFragment(d)(b'{}')
    assert result['value']['source_fact_qualified'] is False
    assert result['source_period'] == 'SOURCE_FRAGMENT_PENDING_NATIVE_OWNER'


def test_new_model_controller_loads_only_new_generation_inputs(tmp_path):
    from scripts.r9_rev11_models import FreshExecution
    sources=tmp_path/'sources'
    sources.mkdir()
    (sources/'r9-rev11-final-provider-plan.json').write_bytes(encoded({'generation_id':'new-only'}))
    proof=FreshExecution(tmp_path/'models',sources)
    assert proof.gen == proof.source_gen == 'new-only'
    assert proof.prepared == proof.markets == proof.cores == proof.arows == proof.brows == {}
    assert proof.frozen is None and proof.ledger == []
    assert proof.DETAILED_PRESENTATION is True and proof.TYPED_PRESENTATION is False


def test_private_command_receipt_binds_result_and_only_used_sealed_receipts(tmp_path, monkeypatch):
    from app.services.sealed_native_bridge import SealedNativeBridge
    from types import SimpleNamespace
    value={'status':200,'body':{'value':12}}
    class Reader:
        async def readline(self):
            return encoded({'result':value})+b'\n'
    class Writer:
        def write(self, raw):
            assert json.loads(raw)=={'market':'SPY'}
        async def drain(self):
            pass
    dispatcher=SimpleNamespace(results={'prior':{'receipt_sha256':'a'*64}},plan=SimpleNamespace(generation_id='new'))
    bridge=SealedNativeBridge(owner_root=tmp_path,input_path=tmp_path/'input',input_sha256='b'*64,
        output=tmp_path/'native',transport=SimpleNamespace(dispatcher=dispatcher),market_reads=[])
    bridge.process=SimpleNamespace(stdin=Writer(),stdout=Reader())
    assert asyncio.run(bridge.command({'market':'SPY'}))==value
    receipt=json.loads((tmp_path/'native/command-001.json').read_bytes())
    assert receipt['result_sha256']==digest(value)
    assert receipt['sealed_receipts']=={}
    assert receipt['generation_id']=='new'
    assert 'wire' not in receipt


def test_mandatory_market_source_not_inferred_from_renderable_unavailable():
    from scripts.r9_rev11_market_qualification import check_projection
    from tests.test_r9_rev6_display_and_source_time import source, temporal, NOW
    from app.services.market_intelligence_service import _observation_fact
    from app.services.numeric_semantic_registry import build_numeric_registry
    s=source()
    projected=dict(packet=dict(assessment_date='2026-09-28',market_context=s),
        context=dict(request_eligible_refs=[f['fact_id'] for f in s['fact_catalog']]))
    assert check_projection(projected,'us')['status']=='SOURCE_PARTIAL'
    for series in ('DGS3','DGS5','DGS30','DTWEXBGS'):
        s['fact_catalog'].append(_observation_fact(series,dict(value=4.,quality_status='fresh',observed_at='2026-09-25',
            raw_payload={'publication_context':temporal(series)}),NOW.date()))
    s['numeric_registry']=build_numeric_registry(s['fact_catalog'])
    projected['context']['request_eligible_refs']=[f['fact_id'] for f in s['fact_catalog']]
    assert check_projection(projected,'us')['status']=='PASS'
    dollar=next(f for f in s['fact_catalog'] if f['fields'].get('series_code')=='DTWEXBGS')
    dollar['fields']['publication_context']['latest_available_at_query_time']=False
    assert check_projection(projected,'us')['mandatory_missing']==['DTWEXBGS']


def test_kr_source_requires_both_current_indices_and_qualified_fx():
    from scripts.r9_rev11_market_qualification import check_projection
    from tests.test_r9_rev6_display_and_source_time import source
    s=source('kr')
    for t in ('KOSPI','KOSDAQ'):
        s['fact_catalog'].append(dict(fact_id=t,fact_type='market_cross_section_index',as_of_date='2026-09-25',fields=dict(symbol=t)))
    projected=dict(packet=dict(assessment_date='2026-09-28',market_context=s),
        context=dict(request_eligible_refs=[f['fact_id'] for f in s['fact_catalog']]))
    assert check_projection(projected,'kr')['status']=='PASS'
    s['fact_catalog'][-1]['as_of_date']='2026-09-24'
    assert check_projection(projected,'kr')['mandatory_missing']==['KOSDAQ']
