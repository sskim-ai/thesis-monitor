"""Actual KR owner replay on synthetic receipts, not whole-source qualification."""

import asyncio
from datetime import datetime, timedelta
import json

import httpx
import pytest

from app.providers.kiwoom_rest_client import KiwoomRestClient
from app.services.kiwoom_consumed_page_contract import CONTRACT
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, kiwoom_market_reads
from app.services.unified_aggregate_receipt import AggregateReceipt
from app.services.unified_kiwoom_observer import KiwoomReceiptObserver
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import A, OwnerAdapter, SourceInput, SourceRole, _resolve
from app.services.unified_source_policy import UnifiedSourcePolicy
from scripts import r9_phase_a_gate as gate
from tests.test_kiwoom_rest_market_context import OBSERVED_AT, SESSION_DATE, _handler


STOP = 'test_stop_after_actual_kr_owner_replay'


def binding(root, name):
    return dict(path=name, sha256=sha256_bytes((root / name).read_bytes()))


@pytest.fixture
def captured_market(tmp_path, monkeypatch):
    def capture(*, consumer_complete=True, continuing=True, instantaneous=False):
        class Clock(datetime):
            ticks = 0

            @classmethod
            def now(cls, tz=None):
                cls.ticks += 1
                at = OBSERVED_AT if instantaneous else OBSERVED_AT + timedelta(seconds=cls.ticks)
                return at.astimezone(tz) if tz else at.replace(tzinfo=None)

        monkeypatch.setattr('app.services.unified_kiwoom_observer.datetime', Clock)
        monkeypatch.setattr('app.services.unified_source_observer.datetime', Clock)
        root = tmp_path / 'markets' / 'kr'
        policy = UnifiedSourcePolicy(frozenset({'kiwoom_rest'}))
        observer = KiwoomReceiptObserver(root=root, run_id='synthetic-ng08', attempt_id='synthetic-ng08:kr',
            session_date=SESSION_DATE, policy=policy, completed_session_only=consumer_complete,
            reads=kiwoom_market_reads(session_date=SESSION_DATE, max_pages=5, max_requests_per_page=1))
        base = _handler([])

        def reply(request):
            response = base.handle_request(request)
            if continuing and request.headers.get('api-id') in {'ka20001', 'ka20009'}:
                response.headers.update({'cont-yn': 'Y', 'next-key': 'synthetic-unused-tail'})
            return response

        client = KiwoomRestClient(app_key='fixture', secret_key='fixture', source_observer=observer,
            transport=httpx.MockTransport(reply), max_retries=0, request_interval_seconds=0)
        service = KiwoomKrMarketContextService(client, max_pages=5, completed_session_only=consumer_complete)
        collection = asyncio.run(service.collect(session_date=SESSION_DATE, observed_at=OBSERVED_AT))
        value = {k: collection.cross_section.model_dump(mode='json')[k]
                 for k in ('indices', 'sectors', 'breadth', 'breadth_by_scope')}
        children, rows = [], []
        for path in sorted(root.glob('*.response.json')):
            stem = path.name.removesuffix('.response.json')
            rows.append(json.loads(path.read_bytes()))
            children.append(dict(child_id=stem, receipt=binding(root, path.name),
                normalization=None, accepted_page=binding(root, stem + '.page.json')))
        durable_json(root / 'aggregate-value.json', value)
        role = SourceRole(key='kr_local_indices_sectors_breadth', owner='kiwoom_pages', market='kr',
            symbol='*', provider='kiwoom_rest', basis='query_time', session=str(SESSION_DATE),
            acquisition_class=A, mandatory=True)
        raw = dict(contract='unified-transitive-source-receipt-v1', owner=role.owner, role=role.key,
            market=role.market, symbol=role.symbol, provider=role.provider, basis=role.basis, session=role.session,
            run_id=observer.run_id, attempt_id=observer.attempt_id, acquisition_id=None, acquisition_class=A.value,
            requested_at=min(r['requested_at'] for r in rows), received_at=max(r['received_at'] for r in rows),
            artifact='aggregate-value.json', artifact_sha256=binding(root, 'aggregate-value.json')['sha256'],
            plan=binding(root, 'plan.json'), children=children, expected_child_ids=[c['child_id'] for c in children],
            normalized_sha256=digest(value), validator_contract=CONTRACT if consumer_complete else 'real-owner-synthetic-transport',
            coverage={'fixture_only': True})
        receipt = AggregateReceipt.model_validate({**raw, 'aggregate_sha256': digest(raw)})
        durable_json(root / 'aggregate.json', receipt.model_dump(mode='json'))
        if consumer_complete:
            durable_json(root.parent / 'kr-query.json', {'observed_at': OBSERVED_AT.isoformat()})
        item = SourceInput(role=role.key, run_id=receipt.run_id, attempt_id=receipt.attempt_id, acquisition_class=A,
            requested_at=receipt.requested_at, received_at=receipt.received_at,
            artifact=receipt.artifact, artifact_sha256=receipt.artifact_sha256,
            receipt_artifact='aggregate.json', receipt_sha256=binding(root, 'aggregate.json')['sha256'])

        def forbidden_callback(*args):
            pytest.fail('root_gate invoked a caller-supplied owner callback')

        native = dict(item=item, role=role, root=root, run_id=receipt.run_id, attempt_id=receipt.attempt_id,
            start=OBSERVED_AT - timedelta(seconds=1), cutoff=receipt.received_at + timedelta(seconds=1), policy=policy,
            owners={role.owner: OwnerAdapter('untrusted-caller', '0' * 64, forbidden_callback, forbidden_callback)})
        return native, value

    return capture


def run_market_boundary(monkeypatch, native):
    projected = []

    def compose(**args):
        projected.append(_resolve(**args['market_inputs']['kr']['native_aggregate']))
        # Deliberately stop before unrelated stock, Class-C and model stages.
        raise ValueError(STOP)

    monkeypatch.setattr(gate, 'code_fingerprints', lambda: {})
    monkeypatch.setattr(gate, 'compose_full_source', compose)
    proof = dict(code_fingerprints={}, whole_source_inputs=dict(
        seed=gate.FreshFullSourceRunSeed.model_construct(),
        market_inputs={'kr': {'native_aggregate': native}}),
        stock_outputs={t: None for subjects in gate.UNIVERSE.values() for t in subjects},
        market_outputs={'kr': None, 'us': None})
    receipt, _ = gate.root_gate(proof)
    assert receipt['dispatch_allowed'] is False
    assert receipt['provider_calls'] == receipt['model_calls'] == 0
    return receipt, projected


@pytest.mark.parametrize('continuing', [False, True])
def test_root_reconstructs_canonical_query_clock_and_completion(captured_market, monkeypatch, continuing):
    native, expected = captured_market(continuing=continuing)
    assert OBSERVED_AT < native['item'].requested_at < native['item'].received_at
    original_owner = native['owners'][native['role'].owner]
    receipt, rows = run_market_boundary(monkeypatch, native)
    assert receipt['errors'] == [{'stage': 'aggregate_whole_source_gate', 'reason': STOP}]
    assert len(rows) == 1 and rows[0]['value'] == expected
    assert rows[0]['original_source_time'] == OBSERVED_AT.isoformat()
    assert rows[0]['eligibility']['contract'] == CONTRACT
    assert native['owners'][native['role'].owner] is original_owner


def test_root_preserves_legacy_exhausted_receipt_mode(captured_market, monkeypatch):
    native, expected = captured_market(consumer_complete=False, continuing=False, instantaneous=True)
    receipt, rows = run_market_boundary(monkeypatch, native)
    assert receipt['errors'][0]['reason'] == STOP
    assert rows[0]['value'] == expected
    assert rows[0]['eligibility']['contract'] == 'kiwoom-child-owner-replay-v1'


def test_root_does_not_enable_consumer_completion_for_legacy_receipt(captured_market, monkeypatch):
    native, _ = captured_market(consumer_complete=False, instantaneous=True)
    receipt, rows = run_market_boundary(monkeypatch, native)
    assert not rows
    assert receipt['errors'][0]['reason'] == 'aggregate_page_set_incomplete'


def test_root_rejects_late_query_clock(captured_market, monkeypatch):
    native, _ = captured_market()
    durable_json(native['root'].parent / 'kr-query.json', {'observed_at': native['item'].received_at.isoformat()})
    receipt, rows = run_market_boundary(monkeypatch, native)
    assert not rows
    assert receipt['errors'][0]['reason'] == 'aggregate_completion_owner_mismatch'


def test_root_rejects_naive_query_clock(captured_market, monkeypatch):
    native, _ = captured_market()
    durable_json(native['root'].parent / 'kr-query.json', {'observed_at': OBSERVED_AT.replace(tzinfo=None).isoformat()})
    with pytest.raises(ValueError, match='source_timezone_required'):
        run_market_boundary(monkeypatch, native)


def test_root_requires_canonical_query_receipt(captured_market, monkeypatch):
    native, _ = captured_market()
    (native['root'].parent / 'kr-query.json').unlink()
    with pytest.raises(FileNotFoundError):
        run_market_boundary(monkeypatch, native)


@pytest.mark.parametrize('artifact', ['aggregate.json', 'plan.json'])
def test_root_rejects_unbound_receipt_or_plan(captured_market, monkeypatch, artifact):
    native, _ = captured_market()
    durable_json(native['root'] / artifact, {})
    with pytest.raises(ValueError, match='source_artifact_hash_mismatch'):
        run_market_boundary(monkeypatch, native)
