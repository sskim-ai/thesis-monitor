"""SYNTHETIC helper mechanics only; no provider, external owner, or real READY.

Main runs this in its pinned isolated stage. This file itself does not execute.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.services import current_scoped_source_results as replay
from app.services.current_scoped_worker_bridge import ScopedBridge
from app.services import current_scoped_source_owner as owner
from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services.scoped_source_plan import compile_scoped_wire_contract
from app.services.unified_snapshot_contract import digest, encoded
import test_current_scoped_source_dispatch as original_tests


setup_parent = original_tests.setup_parent


@pytest.fixture
def capture(setup_parent, tmp_path):
    args, clock = setup_parent
    parent = args['parent']
    spec = owner.ScopedSourceSpec.model_validate_json(owner._PARENTS[parent].spec_json)
    identities = {s.ticker: dict(canonical_security_id=s.security_id, exchange=s.venue)
                  for s in spec.config.subjects}
    wire = compile_scoped_wire_contract(config=spec.config, identities=identities,
        generation_id=spec.generation_id, at=spec.cutoff, code_sha=spec.code_sha,
        provider_config_sha256=spec.provider_config_sha256, retries=spec.retries)
    stock = dict(contract='current-scoped-stock-capture-v1', run_id=spec.generation_id,
        acquisition_id=spec.generation_id + '-stock', frozen_at=spec.cutoff.isoformat(),
        reads=[r.model_dump(mode='json') for r in wire['stock_reads']],
        owner_files=json.loads(wire['owner_files_json']))
    dispatcher = CurrentScopedDispatcher(**args)
    worker = tmp_path / 'worker'
    worker.mkdir()
    (worker / 'stocks').mkdir()
    frozen=tmp_path/'worker-plan.json'
    frozen.write_bytes(encoded(dict(stock_plan=stock,output=str(worker),external_pins={str(i):{'sha256':'a'*64} for i in range(25)})))
    bridge = ScopedBridge(parent=parent, original_plan=args['plan'],
        transport=SimpleNamespace(dispatcher=dispatcher),
        worker=Path(replay.__file__).resolve().parents[2]/'scripts/current_scoped_source_worker.py',
        frozen=frozen, sha=replay._sha(frozen.read_bytes()), output=worker,
        credentials={}, market_reads=())
    return dict(parent=parent, wire=wire, stock_plan=stock, dispatcher=dispatcher,
                capture_root=dispatcher.root, worker_root=worker), bridge, clock


def test_versioned_plan_and_generic_identity(capture):
    args, bridge, _ = capture
    context = replay._context(**args)
    assert context[2] is args['dispatcher'].plan
    assert context[2].original_plan() == args['wire']['request_plan']
    assert context[2].plan_sha256 != args['wire']['request_plan'].plan_sha256
    result = replay.bind_capture(**args, worker_bridge=bridge)
    assert result['status'] == 'LIVE_CAPTURE_OBJECTS_BOUND_NOT_SOURCE_QUALIFIED'


@pytest.mark.parametrize('mutation', ['read_count', 'security', 'generation', 'full22', 'wrong_root'])
def test_context_rejects_substitution(capture, tmp_path, mutation):
    args, _, _ = capture
    args = {**args, 'stock_plan': deepcopy(args['stock_plan'])}
    if mutation == 'read_count':
        args['stock_plan']['reads'][0]['count'] -= 1
    elif mutation == 'security':
        args['stock_plan']['reads'][0]['canonical_security_id'] = 'WRONG'
    elif mutation == 'generation':
        args['stock_plan']['run_id'] = 'WRONG'
    elif mutation == 'full22':
        args['stock_plan']['contract'] = 'one-shot-stock-source-acquisition-v1'
    else:
        args['capture_root'] = tmp_path
    with pytest.raises(ValueError):
        replay._context(**args)


def _execute_page(args):
    dispatcher = args['dispatcher']
    descriptor = original_tests.first_read(dispatcher)
    body = dict(return_code=0, result_list=[])
    final = original_tests.execute(dispatcher, descriptor,
        httpx.MockTransport(lambda request: httpx.Response(200, json=body)))
    return descriptor, final


def test_sealed_consumer_uses_versioned_plan(capture):
    args, _, _ = capture
    descriptor, final = _execute_page(args)
    value = replay._sealed(args['dispatcher'], args['capture_root'], args['dispatcher'].plan,
                           descriptor.logical_request_id)
    assert value[1] == final
    # The ordinary fragment explicitly does not issue source-fact authority.
    assert json.loads(value[2]) == dict(return_code=0, result_list=[])


def test_bind_after_capture_is_denied(capture):
    args, bridge, _ = capture
    _execute_page(args)
    with pytest.raises(ValueError, match='preacquisition_live_bridge'):
        replay.bind_capture(**args, worker_bridge=bridge)


def test_json_pass_cannot_issue_worker_custody(capture):
    args, _, _ = capture
    for i in (1, 2):
        (args['worker_root'] / f'raw-owner-replay-{i}.json').write_text('[{"status":"PASS"}]')
    result = replay.examine(**args, market_results={'us': {'status': 'PASS'}, 'kr': {'status': 'PASS'}})
    assert result['worker_custody']['status'] == 'GAP'
    assert result['current_source_evidence'] == 'NOT_ISSUED'
    assert result['status'] == 'PARTIAL_PER_ROLE'
    assert result['source_only_roles_issued'] == 0
    assert all(row['status'] != 'ORIGINAL_SOURCE_ROLE_REPLAY_PASS' for row in result['stock_roles'])
    assert all(row['status'] == 'GAP' for row in result['markets'].values())
    assert result['full22_native'] is False and result['financial_use'] is False


def test_revocation_invalidates_examination(capture):
    args, _, _ = capture
    owner.revoke_parent(args['parent'])
    with pytest.raises(ValueError, match='live_capability_required'):
        replay.examine(**args, market_results={})


def test_unbound_role_cannot_issue_or_reconstruct_receipt(capture):
    args, _, _ = capture
    read = args['wire']['stock_reads'][0]
    with pytest.raises(ValueError, match='live_capture_required'):
        replay.issue_source_result(args['parent'], dispatcher=args['dispatcher'], entry_id=read.entry_id)
    for forged in ({'status': 'PASS'}, replay.ScopedRoleSourceReceipt()):
        with pytest.raises(ValueError, match='issued_capability'):
            replay.consume_source_result(args['parent'], forged, dispatcher=args['dispatcher'], entry_id=read.entry_id)


def test_public_application_boundary_rejects_unbound_or_reconstructed_source(capture):
    args,bridge,_=capture
    entry=args['wire']['stock_reads'][0].entry_id
    with pytest.raises(ValueError,match='live_capture_required'):
        owner.issue_source_result(args['parent'],plan=args['wire']['request_plan'],dispatcher=args['dispatcher'],entry_id=entry)
    with pytest.raises(ValueError):
        owner.consume_source_result(args['parent'],{'status':'PASS'},plan=args['wire']['request_plan'],dispatcher=args['dispatcher'],entry_id=entry)
    Path(bridge.frozen).write_text('{}')
    with pytest.raises(ValueError,match='frozen_input_mismatch'):
        replay.bind_capture(**args,worker_bridge=bridge)


def _stock_receipt(args, *, count=1, future=False, continuation=False):
    dispatcher = args['dispatcher']
    read = args['wire']['stock_reads'][0]
    descriptor = next(d for d in dispatcher.plan.descriptors
                      if d.consumer_role == 'stock:' + read.entry_id and d.page_ordinal == 1)
    start = max(datetime.now().astimezone(), dispatcher.plan.frozen_at).isoformat()
    original_tests.execute(dispatcher, descriptor, httpx.MockTransport(lambda request:
        httpx.Response(200, json={'return_code': 0, 'result_list': []},
            headers={'cont-yn': 'Y' if continuation else 'N', 'next-key': 'next' if continuation else ''})))
    _, final, raw, resolved = replay._sealed(dispatcher, args['capture_root'], dispatcher.plan,
                                            descriptor.logical_request_id)
    root = args['worker_root'] / 'stocks'
    (root / 'transport-0001.body').write_bytes(raw)
    target = datetime.fromisoformat(read.latest_completed_session)
    if future:
        target += timedelta(days=1)
    bars = [dict(date=(target - timedelta(days=i)).date().isoformat(),
                 open=10, high=12, low=9, close=11, volume=100) for i in range(count)]
    normalized = encoded(bars)
    (root / 'role-001.normalized.json').write_bytes(normalized)
    headers = dict(resolved['headers'])
    request = dict(method='POST', route=read.route, api_id=read.api_id,
        payload=json.loads(resolved['body']),
        continuation=dict(cont_yn=headers.get('cont-yn'), next_key=headers.get('next-key')))
    end = max(datetime.now().astimezone(), dispatcher.plan.frozen_at).isoformat()
    receipt = dict(run_id=args['stock_plan']['run_id'], acquisition_id=args['stock_plan']['acquisition_id'],
        plan_sha256=digest(args['stock_plan']), entry=read.model_dump(mode='json'),
        started_at=start, completed_at=end, status='CAPTURED',
        normalized_artifact='role-001.normalized.json', normalized_sha256=replay._sha(normalized),
        pages=[dict(provider='kiwoom', entry_id=read.entry_id, page_ordinal=1, request=request,
            request_sha256=digest(request), requested_at=start, received_at=end,
            artifact='transport-0001.body', source_sha256=replay._sha(raw), http_status=200,
            response_continuation=dict(cont_yn='Y' if continuation else 'N', next_key='next' if continuation else ''))])
    return read, receipt


@pytest.mark.parametrize('future,continuation', [(False, False), (True, False), (False, True)])
def test_actual_role_validator_never_promotes_technical(capture, future, continuation):
    args, _, _ = capture
    read, receipt = _stock_receipt(args, future=future, continuation=continuation)
    _, _, plan, stock, capture_root, worker = replay._context(**args)
    # No fake executed replay is supplied: this proves custody/validator mechanics only.
    row = replay._stock_role(stock, read, receipt, worker / 'stocks',
        args['dispatcher'], capture_root, plan, None)
    assert row['capture_custody'] == 'PASS'
    assert row['status'] == 'PARTIAL'
    assert row['technical_eligibility'] == 'NOT_GRANTED'
    assert row['requested_count_reached'] is False
    if future:
        assert row['original_role_validation']['status'] == 'GAP'
    if continuation:
        assert row['original_window_validation']['status'] == 'GAP'


def test_altered_worker_raw_rejected(capture):
    args, _, _ = capture
    read, receipt = _stock_receipt(args)
    path = args['worker_root'] / 'stocks/transport-0001.body'
    changed = encoded({'return_code': 0, 'result_list': [{'changed': True}]})
    path.write_bytes(changed)
    receipt['pages'][0]['source_sha256'] = replay._sha(changed)
    _, _, plan, stock, capture_root, worker = replay._context(**args)
    with pytest.raises(ValueError, match='worker_sealed_page_mismatch'):
        replay._stock_role(stock, read, receipt, worker / 'stocks',
            args['dispatcher'], capture_root, plan, None)


@pytest.mark.parametrize('name', ['../outside.json', '/tmp/outside.json', '.env', 'data.sqlite3', 'private-policy.sb'])
def test_artifact_escape_and_protected_names_denied(tmp_path, name):
    with pytest.raises(ValueError, match='path_denied'):
        replay._read(tmp_path, name)


def test_static_error_code_is_exported_without_private_path(tmp_path):
    try:
        replay._read(tmp_path, '../private-value.json')
    except ValueError as exc:
        failure = replay._failure(exc, 'artifact')
    assert failure['error_code'] == 'scoped_replay_artifact_path_denied'
    assert 'private-value' not in json.dumps(failure)
    assert len(failure['error_sha256']) == 64


@pytest.mark.parametrize('message', [
    'PRIVATE_TOKEN_abc123', 'scoped_role_private_identifier',
    '/private/value', 'multiline\nprivate', 'x' * 152,
])
def test_regex_alone_does_not_export_arbitrary_exception_text(message):
    try:
        raise ValueError(message)
    except ValueError as exc:
        failure = replay._failure(exc, 'synthetic_reporting_only')
    assert failure['error_code'] == 'UNCLASSIFIED_EXCEPTION'
    assert message not in json.dumps(failure)
    assert failure['error_sha256'] == replay._sha(message.encode())
