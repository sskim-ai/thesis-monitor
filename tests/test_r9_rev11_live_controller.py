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
    from tests.test_market_display_view import fresh
    projected=fresh(missing_publications=('DGS3','DGS5','DGS30','DTWEXBGS'))
    assert set(check_projection(projected,'us')['mandatory_missing'])=={'DGS3','DGS5','DGS30','DTWEXBGS'}
    projected=fresh()
    assert check_projection(projected,'us')['status']=='PASS'
    projected=fresh(missing_publications=('DTWEXBGS',))
    assert check_projection(projected,'us')['mandatory_missing']==['DTWEXBGS']


def test_kr_source_requires_both_current_indices_and_qualified_fx():
    from scripts.r9_rev11_market_qualification import check_projection
    from tests.test_market_display_view import fresh
    projected=fresh('kr')
    assert check_projection(projected,'kr')['status']=='PASS'
    projected=fresh('kr',missing_indices=('KOSDAQ',))
    assert check_projection(projected,'kr')['mandatory_missing']==['KOSDAQ']
    projected.pop('views')
    with pytest.raises(ValueError,match='market_display_view_required'):
        check_projection(projected,'kr')


def test_root_receipt_file_and_content_identities_are_not_interchangeable(tmp_path, monkeypatch):
    from scripts import r9_rev11_live as live
    from app.services.unified_run_artifacts import sha256_bytes
    receipt = dict(status='PASS', dispatch_allowed=True)
    receipt['receipt_sha256'] = digest(receipt)
    raw = encoded(receipt) + b'\n'
    path = tmp_path/'root.json'
    path.write_bytes(raw)
    monkeypatch.setattr(live, 'REV10_ROOT_FILE_SHA256', sha256_bytes(raw))
    monkeypatch.setattr(live, 'REV10_ROOT_RECEIPT_SHA256', receipt['receipt_sha256'])
    assert live.exact_rev10_receipt(path) == receipt
    path.write_bytes(raw + b'\n')
    with pytest.raises(ValueError, match='rev10_exact_receipt_required'):
        live.exact_rev10_receipt(path)
    receipt['dispatch_allowed'] = False
    raw = encoded(receipt) + b'\n'
    path.write_bytes(raw)
    monkeypatch.setattr(live, 'REV10_ROOT_FILE_SHA256', sha256_bytes(raw))
    with pytest.raises(ValueError, match='rev10_exact_receipt_required'):
        live.exact_rev10_receipt(path)


def test_existing_local_identity_lineage_does_not_add_a_provider_call():
    from scripts.r9_rev11_live import POLICY
    from scripts.unified_stock_owner_proof import POLICY as existing_policy
    from app.services.sealed_fresh_dispatch import HOSTS
    assert existing_policy.permits('local+openfigi')
    assert POLICY.permits('local+openfigi')
    assert not POLICY.permits('openfigi')
    assert 'openfigi' not in HOSTS and 'local+openfigi' not in HOSTS
    assert not POLICY.permits('alphavantage')


def test_static_identity_matches_preserved_repository_evidence(tmp_path, monkeypatch):
    from scripts import r9_rev11_live as live
    name = 'docs/reports/20260815-phase7-2-6-skhy-official-identity-evidence.json'
    original = (live.ROOT/name).read_bytes()
    official = live.static_official_identity()
    assert official['evidence']['ticker'] == 'SKHY'
    assert official['evidence']['ordinary_share_identifier'] == '000660'
    assert official['provider'] == 'sec_official_identity'
    target = tmp_path/name
    target.parent.mkdir(parents=True)
    target.write_bytes(original + b'\n')
    monkeypatch.setattr(live, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='official_static_identity_changed'):
        live.static_official_identity()


def test_systemic_stop_never_continues_independent_phases(tmp_path, monkeypatch):
    from scripts import r9_rev11_collect as collect
    from app.services.unified_live_source_transport import SourceSafetyStop
    from types import SimpleNamespace
    calls = []
    class Bridge:
        exit_receipt = {'closed':True}
        def __init__(self, **kwargs):
            pass
        async def command(self, command):
            calls.append(command)
            raise SourceSafetyStop('test_safety_stop')
        async def shutdown(self):
            pass
    class Transport:
        def __init__(self, *args, **kwargs):
            pass
        async def shutdown(self):
            pass
    monkeypatch.setattr(collect, 'SealedNativeBridge', Bridge)
    monkeypatch.setattr(collect, 'SealedSourceTransport', Transport)
    from tests.test_r9_rev11_full_plan import compiled
    from tests.completed_price_fixtures import official_spec
    from app.services.unified_run_artifacts import sha256_bytes
    stock, _, out = compiled()
    raw = official_spec()
    (tmp_path/'close-documentation.json').write_bytes(raw)
    dispatcher = SimpleNamespace(plan=out['plan'], results={})
    frozen = dict(native_owner={}, stock_plan=stock.model_dump(mode='json'), us_market_symbols=[],
        native_owner_root=str(tmp_path), us_market_reads=[], sessions={'us':'2026-09-22'},
        completed_close_documentation=dict(path='close-documentation.json', sha256=sha256_bytes(raw)))
    result = asyncio.run(collect.acquire_all(root=tmp_path,frozen=frozen,settings=None,dispatcher=dispatcher,
        inner=None,policy=None,guard=lambda:None))
    assert calls == [{'stocks':True}]
    assert result['systemic_stop']['reason'] == 'test_safety_stop'
    assert json.loads((tmp_path/'acquisition-outcome.json').read_bytes())['provider_attempts'] == 0
