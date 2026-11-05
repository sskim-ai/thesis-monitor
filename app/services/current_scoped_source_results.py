"""Generic bounded post-capture source ownership; never issues financial or Native authority.

Call bind_capture before acquisition when a live ScopedBridge is available.
Call examine synchronously after worker shutdown and before parent revocation.
JSON replay files alone are diagnostic, not proof of an executed owner replay.
No provider, credential, registration query or external-repository read occurs.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from weakref import WeakKeyDictionary


_CAPTURES = WeakKeyDictionary()
_ROLE_RESULTS = WeakKeyDictionary()
_MAX_FILE = 32 * 1024 * 1024
_ERROR_CODE = re.compile(r'^[A-Za-z_][A-Za-z_0-9:.-]{0,150}$')
_ERROR_MODULES = (
    'app.services.current_scoped_source_owner', 'app.services.current_scoped_source_dispatch',
    'app.services.unified_stock_acquisition', 'app.services.sealed_native_bridge',
    'app.services.sealed_fresh_dispatch', 'app.services.sealed_response_binding',
    'app.services.completed_price_state', 'app.services.kiwoom_completed_close_owner',
    'app.services.canonical_source_replay', 'app.services.unified_aggregate_owners',
    'app.services.unified_aggregate_receipt', 'app.services.unified_source_composition',
    'app.services.unified_source_policy', 'app.services.unified_source_replay',
    'app.services.kiwoom_consumed_page_contract', 'app.services.native_completed_market',
    'app.macro.providers.market',
    'app.services.wm_period_currentness',
)


class ScopedRoleSourceReceipt:
    """Process-local capability, not its exportable JSON audit receipt."""
    __slots__ = ('__weakref__',)


def _plain(value):
    if hasattr(value, 'model_dump'):
        return value.model_dump(mode='json')
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _encoded(value):
    return json.dumps(_plain(value), sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _digest(value):
    return _sha(_encoded(value))


def _root(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_dir():
        raise ValueError('scoped_replay_root_not_plain_directory')
    return path


def _read(root, relative, expected=None):
    name = Path(relative)
    if (name.is_absolute() or '..' in name.parts or not name.parts
            or any(p.startswith('.env') or p.endswith(('.db', '.sqlite', '.sqlite3', '-wal', '-shm', '.sb'))
                   for p in name.parts)):
        raise ValueError('scoped_replay_artifact_path_denied')
    path = root / name
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('scoped_replay_artifact_symlink_denied')
    if not path.is_file() or path.stat().st_size > _MAX_FILE:
        raise ValueError('scoped_replay_artifact_missing_or_oversize')
    raw = path.read_bytes()
    if expected is not None and _sha(raw) != expected:
        raise ValueError('scoped_replay_artifact_hash_mismatch')
    return raw


def _json(root, relative):
    return json.loads(_read(root, relative))


def _failure(exc, gate):
    # A regex alone also accepts tokens or private identifiers. Export only an
    # exact static error literal from a known already-loaded validator frame.
    message = str(exc)
    code = 'UNCLASSIFIED_EXCEPTION'
    if _ERROR_CODE.fullmatch(message):
        files = {__file__}
        files.update(getattr(sys.modules.get(name), '__file__', None) for name in _ERROR_MODULES)
        trace = exc.__traceback__
        while trace is not None:
            frame = trace.tb_frame.f_code
            if frame.co_filename in files and message in frame.co_consts:
                code = message
                break
            trace = trace.tb_next
    return dict(status='GAP', gate=gate, error_class=type(exc).__name__,
                error_code=code, error_sha256=_sha(message.encode()))


@dataclass(frozen=True)
class _ScopedCapturePlan:
    """Duck-typed per-role input, explicitly NOT the Full22 StockPlan contract."""
    raw_json: str
    reads: tuple
    run_id: str
    acquisition_id: str
    frozen_at: datetime

    def model_dump(self, *, mode='json'):
        if mode != 'json':
            raise ValueError('scoped_capture_json_only')
        return json.loads(self.raw_json)


def _context(parent, wire, stock_plan, dispatcher, capture_root, worker_root):
    from app.services import current_scoped_source_owner as owners
    from app.services.scoped_source_plan import compile_scoped_wire_contract
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher

    plan = wire['request_plan']
    from app.services import pending_source_parent as pending
    from app.services.source_dispatch_authority import resolve_parent
    receipt = resolve_parent(parent, plan=plan)
    # Only the public configuration in the live capability is used here, never
    # the private registration documents retained by the original parent.
    if type(parent) is pending.PendingSourceParent:
        _,spec,identities=pending.replay_context(parent)
    else:
        with owners._LOCK:
            spec = owners.ScopedSourceSpec.model_validate_json(owners._PARENTS[parent].spec_json)
        identities = {s.ticker: dict(canonical_security_id=s.security_id, exchange=s.venue)
                      for s in spec.config.subjects}
    rebuilt = compile_scoped_wire_contract(config=spec.config, identities=identities,
        generation_id=spec.generation_id, at=spec.cutoff, code_sha=spec.code_sha,
        provider_config_sha256=spec.provider_config_sha256, retries=spec.retries)
    if _plain(wire) != _plain(rebuilt):
        raise ValueError('scoped_replay_wire_not_parent_derived')
    if (type(dispatcher) is not CurrentScopedDispatcher
            or dispatcher._parent is not parent or dispatcher.plan.original_plan() != plan
            or _root(dispatcher.root) != _root(capture_root)):
        raise ValueError('scoped_replay_dispatcher_identity_mismatch')
    dispatcher._require_parent()
    capture, worker = _root(capture_root), _root(worker_root)
    raw = _plain(stock_plan)
    if (not isinstance(raw, dict) or raw.get('run_id') != plan.generation_id
            or datetime.fromisoformat(raw['frozen_at']) != plan.frozen_at
            or raw.get('reads') != _plain(rebuilt['stock_reads'])
            or not isinstance(raw.get('acquisition_id'), str) or not raw['acquisition_id']
            or raw.get('contract') in {'one-shot-stock-source-acquisition-v1',
                'one-shot-kr8-source-acquisition-v1', 'one-shot-us14-source-acquisition-v1'}
            or raw.get('automatic_retries', 0) != 0):
        raise ValueError('scoped_replay_stock_plan_scope_mismatch')
    adapter = _ScopedCapturePlan(_encoded(raw).decode(), tuple(rebuilt['stock_reads']),
        raw['run_id'], raw['acquisition_id'], plan.frozen_at)
    return receipt, spec, dispatcher.plan, adapter, capture, worker


def bind_capture(parent, wire, stock_plan, dispatcher, capture_root, worker_root, worker_bridge):
    """Trusted main-process binding BEFORE I/O; no new dispatch authorization.

    Stores object identities, not an accepted receipt reconstructed from JSON.
    The live bridge owns the private child command history used for two replays.
    """
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.scoped_external_code_manifest import validate_external_manifest
    _, _, plan, stock, capture, worker = _context(
        parent, wire, stock_plan, dispatcher, capture_root, worker_root)
    if (type(worker_bridge) is not ScopedBridge or worker_bridge.parent is not parent
            or worker_bridge.transport.dispatcher is not dispatcher
            or worker_bridge.plan != plan.original_plan() or _root(worker_bridge.output) != worker
            or dispatcher.used or dispatcher.results or worker_bridge.process is not None
            or worker_bridge.commands):
        raise ValueError('scoped_replay_preacquisition_live_bridge_required')
    if dispatcher in _CAPTURES:
        raise ValueError('scoped_replay_capture_already_bound')
    frozen_raw = Path(worker_bridge.frozen).read_bytes()
    if _sha(frozen_raw) != worker_bridge.sha:
        raise ValueError('scoped_worker_frozen_input_mismatch')
    frozen = json.loads(frozen_raw)
    validate_external_manifest(frozen['external_pins'], frozen.get('external_code_contract'))
    if ('historical_source_root' in frozen or frozen['stock_plan'] != _plain(stock_plan)
            or frozen['output'] != str(worker)):
        raise ValueError('scoped_current_original_worker_config_required')
    _CAPTURES[dispatcher] = dict(parent=parent, bridge=worker_bridge,
        plan_sha256=plan.plan_sha256, stock_sha256=_digest(stock_plan),
        worker_sha256=_sha(Path(worker_bridge.worker).read_bytes()),
        helper_sha256=_sha(Path(__file__).read_bytes()),
        frozen_sha256=worker_bridge.sha, capture=capture, worker=worker,
        wire=deepcopy(wire), stock_plan=deepcopy(_plain(stock_plan)), pid=os.getpid(), roles={})
    return dict(status='LIVE_CAPTURE_OBJECTS_BOUND_NOT_SOURCE_QUALIFIED',
                plan_sha256=plan.plan_sha256, stock_plan_sha256=_digest(stock.model_dump()))


def _sealed(dispatcher, capture, plan, key):
    from app.services.sealed_fresh_dispatch import consume_bound_result
    d = next(d for d in plan.descriptors if d.logical_request_id == key)
    final = dispatcher.results.get(key)
    if not final or _json(capture, f'receipts/{key}/final.json') != final:
        raise ValueError('scoped_replay_live_final_mismatch')
    consume_bound_result(root=capture, plan=plan, logical_id=key,
                         receipt_sha256=final['receipt_sha256'])
    raw = _read(capture, d.raw_path, final['raw_sha256'])
    wire = _json(capture, f'receipts/{key}/resolved-request.json')['request']
    return d, final, raw, wire


def _worker_custody(parent, dispatcher, plan, stock, capture, worker):
    binding = _CAPTURES.get(dispatcher)
    if (not binding or binding['parent'] is not parent or binding['capture'] != capture
            or binding['worker'] != worker or binding['plan_sha256'] != plan.plan_sha256
            or binding['stock_sha256'] != _digest(stock.model_dump())
            or binding['pid'] != os.getpid()
            or binding['helper_sha256'] != _sha(Path(__file__).read_bytes())):
        raise ValueError('scoped_replay_live_capture_binding_missing')
    bridge = binding['bridge']
    if (bridge.parent is not parent or bridge.transport.dispatcher is not dispatcher
            or bridge.plan != plan.original_plan() or bridge.sha != binding['frozen_sha256']
            or _sha(Path(bridge.frozen).read_bytes()) != binding['frozen_sha256']
            or _sha(Path(bridge.worker).read_bytes()) != binding['worker_sha256']
            or bridge.process is None or bridge.process.returncode != 0 or bridge.busy):
        raise ValueError('scoped_replay_worker_lifetime_mismatch')
    start, end = (_json(worker, f'process-{p}.json') for p in ('start', 'end'))
    from app.services.scoped_worker_launch import CONTRACT as LAUNCH_CONTRACT
    settings = _json(worker, 'effective-settings.json')
    if (bridge.launch is None or start.get('launch_contract') != LAUNCH_CONTRACT
            or start.get('policy_sha256') != bridge.launch['policy_sha256']
            or settings.get('worker_pid') != bridge.process.pid
            or settings.get('worker_uid') != start.get('uid')
            or settings.get('child_global_lane') is not False
            or settings.get('os_policy_denials') != dict.fromkeys(
                ('network-outbound','network-inbound','other_home','other_database','arbitrary_exec'),True)):
        raise ValueError('scoped_replay_production_launch_boundary_unproven')
    if (start['pid'] != bridge.process.pid or end['pid'] != start['pid']
            or start['worker_sha256'] != binding['worker_sha256']
            or end['state'] != 'NORMAL_END' or end['exit'] != 0 or end['end'] < start['start']):
        raise ValueError('scoped_replay_worker_end_missing')
    for i, command in enumerate(bridge.commands, 1):
        if _json(worker, f'command-{i:03d}.json') != command:
            raise ValueError('scoped_replay_command_disk_live_mismatch')
        for key, sha in command['sealed_receipts'].items():
            if dispatcher.results.get(key, {}).get('receipt_sha256') != sha:
                raise ValueError('scoped_replay_command_dispatch_mismatch')
    commands = deepcopy(bridge.commands)
    captures = [c for c in commands if c['command'] == {'stocks': True}]
    if (len(captures) != 1 or captures[0]['result_sha256'] !=
            _digest(dict(status='CAPTURE_COMPLETE_NOT_QUALIFIED'))
            or not captures[0]['sealed_receipts']):
        raise ValueError('scoped_replay_original_capture_command_missing')
    expected = [r.entry_id for r in stock.reads]
    replays = []
    for number in (1, 2):
        raw = _read(worker, f'raw-owner-replay-{number}.json')
        rows = json.loads(raw)
        matches = [c for c in commands if c['command'] == {'replay': number}]
        response = dict(status='REPLAY_RESULT', rows=rows, sha256=_sha(raw))
        if (len(matches) != 1 or matches[0]['result_sha256'] != _digest(response)
                or matches[0]['sealed_receipts'] or not isinstance(rows, list)
                or [r.get('entry_id') for r in rows] != expected
                or commands.index(matches[0]) <= commands.index(captures[0])):
            raise ValueError('scoped_replay_original_command_or_coverage_mismatch')
        replays.append(rows)
    if replays[0] != replays[1]:
        raise ValueError('scoped_replay_two_original_runs_disagree')
    return commands, {r['entry_id']: r for r in replays[0]}


def _stock_role(stock, read, receipt, stocks, dispatcher, capture, plan, replay):
    from app.services.unified_stock_acquisition import decode_owned_role, validate_role
    from app.services.sealed_native_bridge import require_complete_stock_window

    bars = decode_owned_role(stock, read, receipt,
        lambda name, sha: _read(stocks, name, sha))
    bound = []
    for page in receipt['pages']:
        matches = [d for d in plan.descriptors
                   if d.consumer_role == 'stock:' + read.entry_id
                   and d.page_ordinal == page['page_ordinal']]
        if len(matches) != 1:
            raise ValueError('scoped_replay_original_page_slot_missing')
        d, final, raw, resolved = _sealed(dispatcher, capture, plan, matches[0].logical_request_id)
        headers = dict(resolved['headers'])
        expected = dict(method=resolved['method'], route=read.route,
            api_id=headers['api-id'], payload=json.loads(resolved['body']),
            continuation=dict(cont_yn=headers.get('cont-yn'), next_key=headers.get('next-key')))
        body = json.loads(raw)
        continuation = {name: str(final['response_headers'].get(header) or body.get(header)
                         or body.get(name) or default)
                        for name, header, default in (('cont_yn', 'cont-yn', 'N'), ('next_key', 'next-key', ''))}
        if (raw != _read(stocks, page['artifact'], page['source_sha256'])
                or page['request'] != expected or page['response_continuation'] != continuation):
            raise ValueError('scoped_replay_worker_sealed_page_mismatch')
        bound.append(final['receipt_sha256'])
    row = dict(entry_id=read.entry_id, capture_custody='PASS', source_pages=len(bound),
        sealed_receipts=bound, normalized_sha256=receipt['normalized_sha256'],
        technical_eligibility='NOT_GRANTED', financial_use=False, native_use=False)
    if (replay is not None and replay.get('status') == 'PASS'
            and replay.get('normalized_sha256') == receipt['normalized_sha256']
            and replay.get('network_calls') == 0):
        row['two_original_owner_replays'] = 'PASS'
    else:
        row['two_original_owner_replays'] = 'UNVERIFIED_OR_REJECTED'
    for key, action in (
        ('original_role_validation', lambda: validate_role(stock, read, receipt, stocks)),
        ('original_window_validation', lambda: require_complete_stock_window(read, receipt, bars)),
    ):
        try:
            row[key] = action()
        except (ValueError, KeyError, TypeError, OSError) as exc:
            row[key] = _failure(exc, key)
    row['requested_rows'] = read.count
    row['returned_rows'] = len(bars)
    row['requested_count_reached'] = len(bars) >= read.count
    row['status'] = ('ORIGINAL_SOURCE_ROLE_REPLAY_PASS' if
        row['two_original_owner_replays'] == 'PASS'
        and row['original_role_validation']['status'] == 'PASS'
        and row['original_window_validation']['status'] == 'PASS'
        else 'PARTIAL')
    return row


def _close(stock, read, spec, plan, dispatcher, capture, document):
    from app.services.completed_price_state import project_state, required_slot
    from app.services.kiwoom_completed_close_owner import OFFICIAL_SPEC_SHA256
    d = required_slot(plan, read)
    if d is None:
        raise ValueError('scoped_replay_close_slot_missing')
    final = dispatcher.results.get(d.logical_request_id)
    final_path = f'receipts/{d.logical_request_id}/final.json'
    final_raw = _read(capture, final_path)
    if json.loads(final_raw) != final:
        raise ValueError('scoped_replay_close_live_final_mismatch')
    if final['status'] == 'PASS':
        _sealed(dispatcher, capture, plan, d.logical_request_id)
    if not document or document.get('sha256') != OFFICIAL_SPEC_SHA256:
        raise ValueError('scoped_replay_original_close_documentation_required')
    # Documentation is an explicitly copied public artifact inside capture_root.
    _read(capture, document['path'], OFFICIAL_SPEC_SHA256)
    source = dict(provider_plan=plan.model_dump(mode='json'),
        final=dict(path=final_path, sha256=_sha(final_raw)), documentation=document)
    subject = next(s for s in spec.config.subjects if s.ticker == read.subject)
    security = dict(ticker=subject.ticker, canonical_security_id=subject.security_id,
                    exchange=subject.venue, currency=subject.currency)
    state = project_state(source=source, plan=stock, read=read, security=security,
        artifact_reader=lambda name, sha: _read(capture, name, sha))
    return dict(status='ORIGINAL_COMPLETED_CLOSE_REPLAYED',
        state=state.model_dump(mode='json'), technical_injection=False,
        financial_use=False, economic_use=False, native_use=False)


def _completed_close_inputs(spec, stock):
    """Legacy price read shape from the authenticated spec, not captured charts.

    This separately named plan grants no OHLCV coverage. The original price
    owner still requires exact membership, slot, raw, calendar and quality.
    """
    from app.services.scoped_source_plan import (
        ScopedCaptureSelectionV2, ScopedPriceCaptureSelection, ScopedStockRead,
        _sessions, selected_independent_closes,
    )
    from app.services.unified_stock_acquisition import stock_read_fields
    selection = spec.config.capture_selection
    if not isinstance(selection, (ScopedCaptureSelectionV2, ScopedPriceCaptureSelection)):
        return stock, tuple(r for r in stock.reads if r.market == 'us' and r.role == 'adjusted_daily')
    reads = []
    if selection.us_completed_closes:
        states, _ = _sessions(spec.cutoff)
        for subject in selected_independent_closes(spec.config):
            reads.append(ScopedStockRead(**stock_read_fields(subject=subject.ticker,
                identity=dict(canonical_security_id=subject.security_id, exchange=subject.venue),
                market='us', role='adjusted_daily', count=spec.config.us_history.adjusted_daily,
                at=spec.cutoff, state=states['us'])))
    raw = dict(contract='current-scoped-completed-price-plan-v1', purpose='PRICE_ONLY_NO_CHART_CAPTURE_CLAIM',
        run_id=stock.run_id, acquisition_id=stock.run_id+'-completed-price', frozen_at=stock.frozen_at.isoformat(),
        reads=[r.model_dump(mode='json') for r in reads], chart_coverage_granted=False)
    return _ScopedCapturePlan(_encoded(raw).decode(), tuple(reads), stock.run_id,
        raw['acquisition_id'], stock.frozen_at), tuple(reads)


def _market(market, spec, plan, dispatcher, capture, commands):
    """Original transitive component owner, not the Full22 source graph builder."""
    from app.services.canonical_source_replay import aggregate
    from app.services.unified_aggregate_owners import us_market_aggregate_owner, kiwoom_aggregate_owner
    from app.services.unified_snapshot_contract import digest
    from app.services.unified_source_composition import A, SourceInput, SourceRole, _resolve
    from app.services.unified_source_policy import UnifiedSourcePolicy
    from app.services.scoped_source_plan import _sessions

    root = _root(capture.parent / (market + '-market'))
    original = _json(root, 'plan.json')
    if original['run_id'] != plan.generation_id:
        raise ValueError('scoped_replay_market_generation_mismatch')
    sessions = {s.market: s for s in _sessions(spec.cutoff)[1]}
    role = SourceRole(key='us_market_prices' if market == 'us' else 'kr_local_indices_sectors_breadth',
        owner='us_market' if market == 'us' else 'kiwoom_pages', market=market, symbol='*',
        provider='ohlcv_analyst' if market == 'us' else 'kiwoom_rest',
        basis='adjusted_close' if market == 'us' else 'query_time',
        session=sessions[market].target.isoformat(), acquisition_class=A, mandatory=True)
    # Fixed original provider identities; no caller-defined widening or fallback.
    policy = UnifiedSourcePolicy(frozenset({'kiwoom', 'kiwoom_rest', 'ohlcv_analyst'}))
    responses = sorted(root.glob('*.response.json'))
    if not responses:
        raise ValueError('scoped_replay_market_children_missing')
    normalized = []
    source_urls = set()
    for path in responses:
        child = _json(root, path.name)
        raw = _read(root, child['artifact'], child['artifact_sha256'])
        if market == 'us':
            if commands is None:
                raise ValueError('scoped_replay_market_live_worker_required')
            response = dict(status=child['http_status'], body=json.loads(raw))
            matches = [c for c in commands if c['command'] == {'market': child['symbol']}
                       and c['result_sha256'] == digest(response)]
            if len(matches) != 1 or not matches[0]['sealed_receipts']:
                raise ValueError('scoped_replay_market_original_command_missing')
            for key, sha in matches[0]['sealed_receipts'].items():
                d, final, _, _ = _sealed(dispatcher, capture, plan, key)
                if (final['receipt_sha256'] != sha or d.consumer_role != 'us_market:' + child['symbol']
                        or d.subject != child['symbol']):
                    raise ValueError('scoped_replay_market_command_role_mismatch')
            name = path.name.removesuffix('.response.json') + '.normalization.json'
            n = _json(root, name)
            if n['response_receipt_sha256'] != digest(child):
                raise ValueError('scoped_replay_market_normalization_mismatch')
            source_urls.add(n['normalized']['source_url'])
            normalized.append((child['symbol'], json.loads(raw)))
        else:
            matches = [d for d in plan.descriptors
                       if d.consumer_role == 'kr_market:' + child['read_key']
                       and d.page_ordinal == child['request']['page']]
            if len(matches) != 1:
                raise ValueError('scoped_replay_market_page_slot_missing')
            _, _, sealed_raw, resolved = _sealed(dispatcher, capture, plan, matches[0].logical_request_id)
            headers = dict(resolved['headers'])
            request = child['request']
            if (sealed_raw != raw or request['method'] != resolved['method']
                    or request['body'] != json.loads(resolved['body'])
                    or request['api_id'] != headers['api-id']
                    or request['cursor_sha256'] != _sha(headers.get('next-key', '').encode())
                    or request['continuation'] != (headers.get('cont-yn') == 'Y')):
                raise ValueError('scoped_replay_market_page_wire_mismatch')
    if market == 'us':
        from app.macro.providers.market import normalize_market_observation
        from app.macro.providers.base import MacroProviderResult
        from pydantic import TypeAdapter
        if len(source_urls) != 1:
            raise ValueError('scoped_replay_market_source_url_ambiguous')
        source_url = source_urls.pop()
        from urllib.parse import urlsplit
        parsed = urlsplit(source_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('scoped_replay_market_source_url_private')
        observations = [normalize_market_observation(body, symbol=symbol, source_url=source_url)
                        for symbol, body in normalized]
        if any(o is None for o in observations):
            raise ValueError('scoped_replay_market_observation_missing')
        value = TypeAdapter(MacroProviderResult).dump_python(
            MacroProviderResult(provider=role.provider, observations=observations), mode='json')
        owner = us_market_aggregate_owner(role=role, source_url=source_url, policy=policy)
    else:
        n = _json(root, 'normalization.json')
        value = n['roles'][role.key]['value']
        # This flag is never accepted as authority: the original owner replays
        # every page and independently runs the consumed-page completion gate.
        owner = kiwoom_aggregate_owner(role=role, observed_at=spec.cutoff,
            max_pages=spec.config.kr_max_pages, max_requests_per_page=1,
            policy=policy, consumer_complete=True)
    # Existing builder writes only its two deterministic public derived files.
    receipt = aggregate(root, role, value)
    item = SourceInput(role=role.key, run_id=receipt.run_id, attempt_id=receipt.attempt_id,
        acquisition_class=A, requested_at=receipt.requested_at, received_at=receipt.received_at,
        artifact=receipt.artifact, artifact_sha256=receipt.artifact_sha256,
        receipt_artifact='aggregate.json', receipt_sha256=_sha(_read(root, 'aggregate.json')))
    component = _resolve(item=item, role=role, root=root, run_id=plan.generation_id,
        start=plan.frozen_at, cutoff=datetime.now(timezone.utc), attempt_id=receipt.attempt_id,
        policy=policy, owners={role.owner: owner})
    return dict(status='ORIGINAL_TRANSITIVE_MARKET_COMPONENT_REPLAY_PASS',
        role=role.key, aggregate_sha256=receipt.aggregate_sha256,
        component_sha256=digest(component), value_sha256=component['value_sha256'],
        original_owner_contract=component['eligibility']['contract'],
        children=len(responses), full_source_graph='NOT_RUN_SCOPED_COHORT_NOT_FULL22',
        D01_D02=False, native_use=False, economic_use=False)


def _eligible_role(parent, dispatcher, entry_id):
    binding = _CAPTURES.get(dispatcher)
    if not binding or binding['parent'] is not parent:
        raise ValueError('scoped_role_live_capture_required')
    receipt, _, plan, stock, capture, worker = _context(parent, binding['wire'],
        binding['stock_plan'], dispatcher, binding['capture'], binding['worker'])
    _, rows = _worker_custody(parent, dispatcher, plan, stock, capture, worker)
    reads = [(i, r) for i, r in enumerate(stock.reads, 1) if r.entry_id == entry_id]
    if len(reads) != 1:
        raise ValueError('scoped_role_exact_read_required')
    ordinal, read = reads[0]
    original = _json(worker / 'stocks', f'role-{ordinal:03d}.receipt.json')
    proof = _stock_role(stock, read, original, worker / 'stocks', dispatcher, capture,
                        plan, rows.get(entry_id))
    projection = None
    normalized_sha = original['normalized_sha256']
    if read.timeframe == 'daily':
        from app.services.completed_session_projection import project_completed_rows
        path = f'projection-{ordinal:03d}.json'
        raw = _read(worker, path)
        value = json.loads(raw)
        commands = binding['bridge'].commands
        result = dict(status='COMPLETED_PROJECTION_REPLAY_PASS',entry_id=entry_id,
                      artifact=path,sha256=_sha(raw))
        matches = [c for c in commands if c['command']=={'projection':entry_id}
                   and c['result_sha256']==_digest(result) and not c['sealed_receipts']]
        frozen = json.loads(Path(binding['bridge'].frozen).read_bytes())
        if (len(matches)!=1 or value['parser_pins']!=frozen['external_pins']
                or [p['sha256'] for p in value['receipt']['source_pages']] != [p['source_sha256'] for p in original['pages']]
                or proof['two_original_owner_replays']!='PASS'):
            raise ValueError('scoped_projection_original_worker_replay_required')
        selected, projection = project_completed_rows(value['all_rows'],read=read,
            cutoff=stock.frozen_at,source_pages=value['receipt']['source_pages'])
        if selected!=value['rows'] or projection!=value['receipt']:
            raise ValueError('scoped_projection_consumer_replay_mismatch')
        normalized_sha = projection['selected_sha256']
    elif proof['status'] != 'ORIGINAL_SOURCE_ROLE_REPLAY_PASS':
        raise ValueError('scoped_role_original_replay_or_quality_gap')
    if projection is None and not proof['requested_count_reached']:
        raise ValueError('scoped_role_requested_history_incomplete')
    period_proof = None
    if read.timeframe in {'weekly', 'monthly'}:
        from app.services.wm_period_currentness import capture_period_proof
        frozen = json.loads(Path(binding['bridge'].frozen).read_bytes())
        bars = json.loads(_read(worker / 'stocks', original['normalized_artifact'], original['normalized_sha256']))
        period_proof = capture_period_proof(bars, read=read, receipt=original,
            original_proof=proof, cutoff=stock.frozen_at, parser_pins=frozen['external_pins'])
    elif projection is None and proof['original_role_validation']['current_session_aligned'] is not True:
        raise ValueError('scoped_role_current_session_alignment_unproven')
    value = dict(contract='current-scoped-role-source-receipt-v1',
        consumer='SCOPED_SOURCE_ONLY', generation_id=plan.generation_id,
        entry_id=entry_id, security_id=read.canonical_security_id,
        acquisition_id=stock.acquisition_id, parent_receipt_sha256=_digest(receipt),
        plan_sha256=plan.plan_sha256, original_plan_sha256=plan.original_plan().plan_sha256,
        stock_plan_sha256=_digest(stock.model_dump()),
        source_receipt_sha256=_digest(original), raw_sha256=[p['source_sha256'] for p in original['pages']],
        normalized_sha256=normalized_sha, proof_sha256=_digest(proof),projection=projection,
        observed_at=original['completed_at'], target_session=read.latest_completed_session,
        requested_rows=read.count, rows=projection['selected_rows'] if projection else proof['returned_rows'], expires_at=receipt['expires_at'],
        allowed_use='BOUND_SOURCE_ROWS_ONLY', technical_signal=False, completed_price_authority=False,
        financial_use=False, valuation_use=False, economic_use=False, D01_D02=False,
        native_use=False, full22_native=False, model_use=False)
    if period_proof is not None:
        # New W/M semantics cannot be silently consumed as an old v1 receipt.
        value.update(contract='current-scoped-role-source-receipt-v2-wm', period_proof=period_proof,
            current_source_authority=False,source_evidence_state=period_proof['state'],
            period_evidence=dict(source_receipt=original,stock_plan=stock.model_dump(),
                original_proof=proof,cutoff=stock.frozen_at.isoformat(),parser_pins=frozen['external_pins'],
                replays=[_json(worker,f'raw-owner-replay-{n}.json') for n in (1,2)]))
    if receipt.get('scope')=='SCOPED_SOURCE_ONLY_PENDING':
        from app.services import pending_source_parent as pending
        pending.require_worker(parent,binding['bridge'].process.pid)
        value.update(contract='pending-scoped-role-source-receipt-v1-wm' if period_proof is not None else 'pending-scoped-role-source-receipt-v1',
            source_evidence_state=period_proof['state'] if period_proof is not None else 'SOURCE_OBSERVED_PENDING',current_source_authority=False,
            production_eligible=False,registration_scope='PENDING_ONBOARDING')
    return value


def issue_source_result(parent, *, dispatcher, entry_id):
    """Replay from bound original custody; accepts no caller evidence/PASS flags.

    This application capability grants only one exact source role, never Native.
    """
    value = _eligible_role(parent, dispatcher, entry_id)
    binding = _CAPTURES[dispatcher]
    existing = binding['roles'].get(entry_id)
    if existing is not None:
        state = _ROLE_RESULTS.get(existing)
        if state is None or state['value'] != value:
            raise ValueError('scoped_role_reissued_changed_or_revoked')
        return existing
    capability = ScopedRoleSourceReceipt()
    _ROLE_RESULTS[capability] = dict(parent=parent, dispatcher=dispatcher,
        entry_id=entry_id, value=deepcopy(value), pid=os.getpid())
    binding['roles'][entry_id] = capability
    return capability


def consume_source_result(parent, capability, *, dispatcher, entry_id, consumer='SCOPED_SOURCE_ONLY'):
    """Same-invocation idempotent lookup; rechecks parent and original bytes."""
    if (type(capability) is not ScopedRoleSourceReceipt or capability not in _ROLE_RESULTS
            or consumer != 'SCOPED_SOURCE_ONLY'):
        raise ValueError('scoped_role_issued_capability_and_consumer_required')
    state = _ROLE_RESULTS[capability]
    if (state['parent'] is not parent or state['dispatcher'] is not dispatcher
            or state['entry_id'] != entry_id or state['pid'] != os.getpid()):
        raise ValueError('scoped_role_parent_dispatch_or_role_mismatch')
    value = _eligible_role(parent, dispatcher, entry_id)
    if value != state['value']:
        raise ValueError('scoped_role_consumed_artifact_drift')
    return dict(deepcopy(value), receipt_sha256=_digest(value))


def revoke_source_result(capability):
    if type(capability) is not ScopedRoleSourceReceipt or capability not in _ROLE_RESULTS:
        raise ValueError('scoped_role_unissued_or_revoked')
    if _ROLE_RESULTS[capability]['pid'] != os.getpid():
        raise ValueError('scoped_role_wrong_process')
    del _ROLE_RESULTS[capability]


def read_source_rows(parent, capability, *, dispatcher, entry_id, consumer='SCOPED_SOURCE_ONLY'):
    """Actual bounded row consumer; receipt metadata alone is not row transport."""
    receipt = consume_source_result(parent, capability, dispatcher=dispatcher,
        entry_id=entry_id, consumer=consumer)
    binding = _CAPTURES[dispatcher]
    ordinal = next(i for i,r in enumerate(binding['stock_plan']['reads'],1) if r['entry_id']==entry_id)
    if receipt['projection']:
        rows = _json(binding['worker'], f'projection-{ordinal:03d}.json')['rows']
    else:
        original = _json(binding['worker']/'stocks', f'role-{ordinal:03d}.receipt.json')
        rows = json.loads(_read(binding['worker']/'stocks', original['normalized_artifact'], original['normalized_sha256']))
    if len(rows)!=receipt['rows'] or _digest(rows)!=receipt['normalized_sha256']:
        raise ValueError('scoped_consumed_rows_identity_mismatch')
    return dict(receipt=receipt, rows=rows, consumer=consumer)


def examine(parent, wire, stock_plan, dispatcher, capture_root, worker_root, market_results):
    """Return sanitized artifact statuses; never accepts supplied PASS flags.

    capture_root is dispatcher.root; worker_root contains stocks/ and the two
    raw-owner-replay files. market_results may include the public descriptor
    completed_close_documentation={path,sha256}, relative to capture_root.
    """
    receipt, spec, plan, stock, capture, worker = _context(
        parent, wire, stock_plan, dispatcher, capture_root, worker_root)
    result = dict(contract='current-scoped-source-replay-audit-v1',
        generation_id=plan.generation_id, plan_sha256=plan.plan_sha256,
        stock_plan_sha256=_digest(stock.model_dump()), parent_receipt_sha256=_digest(receipt),
        stock_roles=[], completed_closes={}, markets={}, current_source_evidence='NOT_ISSUED',
        scoped_role_receipts={}, source_result_integration='PER_ROLE_SOURCE_ONLY_CAPABILITY',
        full22_native=False, D01_D02=False, financial_use=False, economic_use=False, model_use=False)
    commands, replay_rows = None, {}
    try:
        commands, replay_rows = _worker_custody(parent, dispatcher, plan, stock, capture, worker)
        result['worker_custody'] = dict(status='PASS', commands=len(commands),
            two_replay_files=True, original_capture_plan_sha256=_digest(stock.model_dump()))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        result['worker_custody'] = _failure(exc, 'live_worker_capture_and_replay')
    stocks = worker / 'stocks'
    for ordinal, read in enumerate(stock.reads, 1):
        try:
            original = _json(stocks, f'role-{ordinal:03d}.receipt.json')
            row = _stock_role(stock, read, original, stocks, dispatcher, capture, plan,
                              replay_rows.get(read.entry_id))
        except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
            row = dict(entry_id=read.entry_id, **_failure(exc, 'original_stock_capture_replay'))
        result['stock_roles'].append(row)
        try:
            capability = issue_source_result(parent, dispatcher=dispatcher, entry_id=read.entry_id)
            result['scoped_role_receipts'][read.entry_id] = dict(status='ISSUED_AND_CONSUMED_SOURCE_ONLY',
                receipt=consume_source_result(parent, capability, dispatcher=dispatcher,
                                              entry_id=read.entry_id))
        except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
            result['scoped_role_receipts'][read.entry_id] = _failure(exc, 'scoped_role_current_source_use')
    price_plan, price_reads = _completed_close_inputs(spec, stock)
    for read in price_reads:
        try:
            result['completed_closes'][read.subject] = _close(price_plan, read, spec, plan,
                dispatcher, capture, (market_results or {}).get('completed_close_documentation'))
        except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
            result['completed_closes'][read.subject] = _failure(exc, 'original_completed_close_owner')
    for market in ('us', 'kr'):
        try:
            result['markets'][market] = _market(market, spec, plan, dispatcher, capture, commands)
        except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
            result['markets'][market] = _failure(exc, 'original_transitive_market_owner')
    from app.services.source_dispatch_authority import resolve_parent
    if resolve_parent(parent, plan=plan.original_plan()) != receipt:
        raise ValueError('scoped_replay_parent_changed_during_validation')
    result['source_only_roles_issued'] = sum(r['status'] == 'ISSUED_AND_CONSUMED_SOURCE_ONLY'
                                            for r in result['scoped_role_receipts'].values())
    if result['source_only_roles_issued']:
        admitted=[r['receipt'] for r in result['scoped_role_receipts'].values()
                  if r['status']=='ISSUED_AND_CONSUMED_SOURCE_ONLY']
        result['current_source_evidence'] = ('PER_ROLE_CAPTURE_ONLY_CURRENTNESS_NOT_GRANTED'
            if all(r.get('current_source_authority') is False for r in admitted)
            else 'PER_ROLE_ONLY_NOT_WHOLE_SOURCE_OWNER')
    result['status'] = 'PARTIAL_PER_ROLE'
    result['full_source_owner_status'] = 'NOT_ISSUED_SCOPED_ROLE_CAPABILITIES_ONLY'
    result['artifact_sha256'] = _digest(result)
    return result
