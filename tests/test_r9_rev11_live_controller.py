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
