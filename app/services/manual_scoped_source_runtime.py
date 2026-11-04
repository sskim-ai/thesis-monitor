"""Opt-in composition of original live registration, scoped issuer and worker.

Trusted callers supply fresh grants and the original runtime; this module never
reads registration/settings or turns a historical plan into current authority.
The narrow chart canary is not the canonical financial/Market/Native pipeline.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
from weakref import WeakKeyDictionary, ref

from app.services import current_class_c_source_bridge as registration
from app.services import current_scoped_source_owner as owner
from app.services import current_scoped_source_results as results
from app.services.scoped_source_plan import (
    HistoryCounts, ScopedConfig, ScopedCaptureSelectionV2, ScopedSubject,
    compile_scoped_wire_contract,
)
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from app.services.scoped_external_code_manifest import validate_external_manifest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = 'manual-registration-scoped-chart-handoff-v1'


class ManualScopedCanary:
    __slots__ = ('__weakref__',)


_LIVE = WeakKeyDictionary()
_BY_PARENT = WeakKeyDictionary()


def _state(handle):
    if type(handle) is not ManualScopedCanary or handle not in _LIVE:
        raise ValueError('manual_scoped_live_handle_required')
    s = _LIVE[handle]
    if s['pid'] != os.getpid() or s['code'] != sha256_bytes(Path(__file__).read_bytes()):
        raise ValueError('manual_scoped_process_or_code_changed')
    for market in ('kr', 'us'):
        registration.memory_local_seed(s['registration'], frozen=s['frozen'],
            plan=s['original_stock'], market=market, policy=s['policy'])
    owner.resolve_parent(s['parent'], plan=s['wire']['request_plan'])
    return s


def prepare(*, class_c_bridge, frozen, stock_plan, policy, maximum_attempts,
            provider_config_sha256, enabled=False, capture_markets=('kr', 'us')):
    """Use full-cohort registration, selecting one chart per market, not 22 closes.

    Returning a parent is not a user HTTP approval. The trusted caller must
    independently possess the exact current registration/runtime/provider grant.
    """
    if enabled is not True:
        raise ValueError('manual_scoped_default_off')
    if capture_markets not in (('kr',), ('kr', 'us')):
        raise ValueError('manual_scoped_capture_markets')
    if type(maximum_attempts) is not int or not 1 <= maximum_attempts <= 32:
        raise ValueError('manual_scoped_pilot_bound')
    documents = {m: registration.memory_local_seed(class_c_bridge, frozen=frozen,
        plan=stock_plan, market=m, policy=policy) for m in ('kr', 'us')}
    original_configs = {d['config_identity_sha256'] for d in frozen['plan']['descriptors']
                        if d['provider'] == 'kiwoom'}
    if original_configs != {provider_config_sha256}:
        raise ValueError('manual_scoped_provider_config_changed')
    identities, subjects, histories, selected = {}, [], {}, []
    for market, doc in documents.items():
        cohort = []
        for row in doc['roles']['security_identity']['records']:
            record = row['record']
            ticker = record['ticker']
            identities[ticker] = record
            cohort.append(ScopedSubject(ticker=ticker, market=market,
                security_id=record['canonical_security_id'],
                issuer_id=record['corp_code' if market == 'kr' else 'cik'],
                venue=record['exchange'], currency='KRW' if market == 'kr' else 'USD'))
        subjects.extend(cohort)
        if market in capture_markets:
            selected.append(min(s.security_id for s in cohort))
        counts = {}
        for read in stock_plan.reads:
            if read.market == market:
                if read.role in counts and counts[read.role] != read.count:
                    raise ValueError('manual_scoped_nonuniform_original_history')
                counts[read.role] = read.count
        histories[market] = HistoryCounts(**counts)
    config = ScopedConfig(subjects=tuple(sorted(subjects, key=lambda s: s.security_id)),
        kr_history=histories['kr'], us_history=histories['us'], kr_max_pages=20,
        capture_selection=ScopedCaptureSelectionV2(contract='scoped-capture-selection-v2',
            stock_security_ids=tuple(selected), stock_roles=('adjusted_daily',),
            market_contexts=(), us_completed_closes=False))
    wire = compile_scoped_wire_contract(config=config, identities=identities,
        generation_id=stock_plan.run_id, at=stock_plan.frozen_at,
        code_sha=stock_plan.implementation_sha,
        provider_config_sha256=provider_config_sha256, retries=0)
    spec = owner.ScopedSourceSpec(config=config, generation_id=stock_plan.run_id,
        cutoff=stock_plan.frozen_at, code_sha=stock_plan.implementation_sha,
        provider_config_sha256=provider_config_sha256, maximum_attempts=maximum_attempts)
    parent = owner.issue_parent(registration_owners=registration.memory_owners(class_c_bridge),
        admitted_projections=documents, spec=spec, plan=wire['request_plan'], policy=policy,
        code_pins=owner.current_code_pins(), enabled=True)
    previous = _BY_PARENT.get(parent, lambda: None)()
    if parent in _BY_PARENT and previous is None:
        raise ValueError('manual_scoped_handle_lifetime_ended')
    if previous is not None:
        if _state(previous)['registration'] is not class_c_bridge:
            raise ValueError('manual_scoped_registration_alias')
        return previous
    scoped_stock = dict(contract='current-scoped-stock-capture-v1', run_id=stock_plan.run_id,
        acquisition_id=stock_plan.acquisition_id+'-scoped', frozen_at=stock_plan.frozen_at.isoformat(),
        reads=[r.model_dump(mode='json') for r in wire['stock_reads']],
        owner_files=json.loads(wire['owner_files_json']))
    handle = ManualScopedCanary()
    _LIVE[handle] = dict(pid=os.getpid(), code=sha256_bytes(Path(__file__).read_bytes()),
        registration=class_c_bridge, frozen=deepcopy(frozen),
        original_stock=type(stock_plan).model_validate_json(stock_plan.model_dump_json()),
        policy=policy, parent=parent, wire=wire, stock=scoped_stock, runtime=None)
    _BY_PARENT[parent] = ref(handle)
    return handle


def inputs(handle):
    """Trusted-process inputs for the ORIGINAL dispatcher/worker constructor."""
    s = _state(handle)
    return s['parent'], deepcopy(s['wire']), deepcopy(s['stock'])


def completed_sessions(handle):
    return deepcopy(_state(handle)['frozen']['sessions'])


def describe(handle):
    s = _state(handle)
    receipt = owner.resolve_parent(s['parent'], plan=s['wire']['request_plan'])
    return dict(contract=CONTRACT, purpose=owner.PURPOSE, registration_purpose='MANUAL_SHADOW_UNSENT',
        generation_id=s['original_stock'].run_id, parent=receipt,
        selected=[dict(security_id=r.canonical_security_id, role=r.role, count=r.count,
                       completed_session=r.latest_completed_session) for r in s['wire']['stock_reads']],
        scoped_stock_sha256=digest(s['stock']), runtime_bound=s['runtime'] is not None,
        actual_source_issued=False, full_market=False, full_native=False,
        financial_use=False, economic_use=False, model_use=False)


def _runtime_identity(s, dispatcher, worker_bridge):
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.sealed_source_transport import SealedSourceTransport
    if type(worker_bridge) is not ScopedBridge:
        raise ValueError('manual_scoped_original_worker_required')
    if (type(worker_bridge.transport) is not SealedSourceTransport
            or worker_bridge.transport.providers != frozenset({'kiwoom'})):
        raise ValueError('manual_scoped_original_sealed_transport_required')
    expected_worker = ROOT/'scripts/current_scoped_source_worker.py'
    if (Path(worker_bridge.worker) != expected_worker or expected_worker.is_symlink()
            or worker_bridge.parent is not s['parent']
            or worker_bridge.plan != s['wire']['request_plan']
            or worker_bridge.transport.dispatcher is not dispatcher):
        raise ValueError('manual_scoped_runtime_identity_changed')
    raw = Path(worker_bridge.frozen).read_bytes()
    if sha256_bytes(raw) != worker_bridge.sha:
        raise ValueError('manual_scoped_runtime_pin_changed')
    envelope = json.loads(raw)
    allowed = {'stage', 'output', 'external_root', 'external_pins', 'stock_plan',
               'request_interval', 'latest_completed_us_session', 'us_market_symbols', 'read_paths'}
    if (set(envelope) not in (allowed, allowed | {'external_code_contract'}) or Path(envelope['stage']) != ROOT
            or envelope['latest_completed_us_session'] != s['frozen']['sessions']['us']
            or envelope['us_market_symbols'] or worker_bridge.market_reads):
        raise ValueError('manual_scoped_original_runtime_envelope_required')
    pins = envelope['external_pins']
    validate_external_manifest(pins, envelope.get('external_code_contract'))
    if (any(not isinstance(v, dict) or set(v) != {'bytes','sha256'} for v in pins.values())
            or {n:v['sha256'] for n,v in pins.items()} != s['original_stock'].owner_files):
        raise ValueError('manual_scoped_external_pin_format_or_identity')
    external_root = Path(envelope['external_root'])
    external_paths = set()
    for name, pin in pins.items():
        relative = Path(name)
        path = external_root/relative
        if (relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'app'
                or path.suffix != '.py' or not path.is_absolute()
                or any(p.is_symlink() for p in (path,*path.parents))):
            raise ValueError('manual_scoped_external_code_path')
        # Trusted caller must obtain permission for these exact files first.
        content = path.read_bytes()
        if len(content) != pin['bytes'] or sha256_bytes(content) != pin['sha256']:
            raise ValueError('manual_scoped_external_code_changed')
        external_paths.add(str(path))
    if not external_paths <= set(envelope['read_paths']):
        raise ValueError('manual_scoped_external_code_not_in_read_closure')
    # No directories, credential files or database paths in the caller's closure.
    for value in envelope['read_paths']:
        path = Path(value)
        if (not path.is_absolute() or path.is_symlink() or not path.is_file()
                or path.suffix != '.py' or any(p.is_symlink() for p in path.parents)
                or not (str(path) in external_paths or (path.is_relative_to(ROOT)
                    and path.relative_to(ROOT).parts[0] in {'app', 'scripts'}))):
            raise ValueError('manual_scoped_code_only_read_closure')
    results._context(s['parent'],s['wire'],s['stock'],dispatcher,dispatcher.root,worker_bridge.output)
    return dict(frozen_sha256=worker_bridge.sha, worker_sha256=sha256_bytes(expected_worker.read_bytes()),
        frozen_path=str(worker_bridge.frozen),output=str(worker_bridge.output),
        dispatcher_root=str(dispatcher.root),transport=worker_bridge.transport,
        inner_transport=worker_bridge.transport.inner)


def bind_runtime(handle, *, dispatcher, worker_bridge):
    """Bind actual original live objects BEFORE I/O; never accept receipt JSON."""
    s = _state(handle)
    identity = _runtime_identity(s, dispatcher, worker_bridge)
    if s['runtime'] is not None:
        if (s['runtime'] != (dispatcher, worker_bridge) or identity != s['runtime_identity']):
            raise ValueError('manual_scoped_runtime_replacement')
        return describe(handle)
    results.bind_capture(parent=s['parent'], wire=s['wire'], stock_plan=s['stock'],
        dispatcher=dispatcher, capture_root=dispatcher.root, worker_root=worker_bridge.output,
        worker_bridge=worker_bridge)
    s['runtime'] = (dispatcher, worker_bridge)
    s['runtime_identity'] = identity
    return describe(handle)


async def command(handle, value):
    """Recheck custody immediately before each original worker command."""
    s = _state(handle)
    if s['runtime'] is None:
        raise ValueError('manual_scoped_runtime_not_bound')
    dispatcher, worker = s['runtime']
    if _runtime_identity(s,dispatcher,worker) != s['runtime_identity']:
        raise ValueError('manual_scoped_runtime_replacement')
    allowed = [{'stocks':True},{'replay':1},{'replay':2}]
    allowed += [{'projection':r.entry_id} for r in s['wire']['stock_reads']]
    if encoded(value) not in [encoded(v) for v in allowed]:
        raise ValueError('manual_scoped_command_outside_chart_scope')
    return await worker.command(value)


def revoke(handle):
    s = _LIVE.pop(handle, None)
    if s is not None:
        owner.revoke_parent(s['parent'])
