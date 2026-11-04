"""Official CLI composition of the existing Class-C and scoped Source owners.

This module does not install a host sandbox, approve a request, or reconstruct a
capability from JSON. The default path requires effective OS write denial; the
explicit v3 policy uses the audited SQLite read-only boundary, not that guarantee.
"""
from contextlib import contextmanager
import ast
import ctypes
import hashlib
import os
from pathlib import Path
import sys
from weakref import WeakKeyDictionary

from app.services import current_class_c_source_bridge as registration
from app.services import manual_scoped_source_runtime as manual
from app.services import prospective_class_c_owner as prospective
from app.services.minimal_class_c_export import (
    ExportPermission, capture_authorized_class_c, captured_private_snapshot,
)
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import UNIVERSE

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = 'official-registered-memory-source-composition-v1'
WRITE_OPERATIONS = ('file-write-data', 'file-write-create', 'file-write-unlink',
                    'file-write-mode', 'file-write-owner', 'file-write-setugid',
                    'file-write-xattr', 'file-write-flags')
_BOUNDARIES = WeakKeyDictionary()


def require(value, code):
    if not value:
        raise ValueError(code)


def plain(value):
    p = Path(value)
    require(p.is_absolute() and not any(x.is_symlink() for x in (p, *p.parents)),
            'official_registration_plain_path')
    return p


class EffectiveRegistrationBoundary:
    __slots__ = ('__weakref__',)


def _os_decisions(database):
    """Query the actual current kernel policy; no write/open probe on the DB."""
    require(sys.platform == 'darwin', 'official_host_os_boundary_unavailable')
    library = ctypes.CDLL('/usr/lib/libsandbox.dylib', use_errno=True)
    library.sandbox_check.restype = ctypes.c_int
    paths = (database, Path(str(database)+'-wal'), Path(str(database)+'-shm'),
             Path(str(database)+'-journal'))
    result = {}
    for p in paths:
        for op in WRITE_OPERATIONS:
            rc = library.sandbox_check(os.getpid(), op.encode(), 1, os.fsencode(p))
            require(rc in (0, 1), 'official_host_os_query_failed')
            result[(str(p), op)] = rc == 1
    return result


def admit_os_boundary(database):
    """Only a host-installed effective policy can issue this process-local handle."""
    db = plain(database)
    decisions = _os_decisions(db)
    require(len(decisions) == 4*len(WRITE_OPERATIONS) and all(decisions.values()),
            'official_effective_os_db_write_denial_required')
    s = db.stat()
    require(db.is_file() and s.st_nlink == 1, 'official_registration_file_identity')
    h = EffectiveRegistrationBoundary()
    _BOUNDARIES[h] = dict(pid=os.getpid(), database=db, identity=(s.st_dev,s.st_ino),
        source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return h


def require_os_boundary(handle, database):
    require(type(handle) is EffectiveRegistrationBoundary and handle in _BOUNDARIES,
            'official_live_os_boundary_required')
    s = _BOUNDARIES[handle]
    db = plain(database)
    require(s['pid'] == os.getpid() and s['database'] == db
            and s['source'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'official_os_boundary_process_or_code_changed')
    stat = db.stat()
    require((stat.st_dev,stat.st_ino) == s['identity'], 'official_registration_identity_changed')
    decisions = _os_decisions(db)
    require(len(decisions) == 4*len(WRITE_OPERATIONS) and all(decisions.values()),
            'official_effective_os_boundary_lost')
    return s['identity']


def original_identity_policy():
    values = []
    for name in ('app/services/production_source_context.py','scripts/r9_rev11_live.py'):
        node = next(n for n in ast.parse((ROOT/name).read_text()).body
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROVIDERS' for t in n.targets))
        require(isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name)
                and node.value.func.id=='frozenset', 'official_original_identity_policy_shape')
        values.append(frozenset(ast.literal_eval(node.value.args[0])))
    require(values[0] == values[1] and 'kiwoom' in values[0], 'official_original_identity_policy_drift')
    return UnifiedSourcePolicy(values[0])


def registered_subjects():
    return tuple(sorted(t for members in UNIVERSE.values() for t in members))


def original_external_pins(manifest, contract):
    from app.services.scoped_external_code_manifest import CONTRACT_V2, REQUIRED_V2, validate_external_manifest
    require(contract == CONTRACT_V2, 'official_policy_a_external_contract_required')
    approved = manifest['original_external_code']
    require(REQUIRED_V2 <= set(approved), 'official_original_external_closure_missing')
    pins = {name:approved[name] for name in sorted(REQUIRED_V2)}
    validate_external_manifest(pins,contract)
    return pins


def check_space(paths):
    rows = []
    for path in paths:
        p = plain(path)
        require(p.is_dir(), 'official_writer_directory_required')
        stat = os.statvfs(p)
        free = stat.f_bavail*stat.f_frsize
        require(free >= max(12*1024**3, 384*1024**2+4*1024**3), 'official_live_writer_headroom')
        rows.append(dict(path=str(p),device=p.stat().st_dev,free_bytes=free))
    return rows


@contextmanager
def capture_registered_runtime(*, approval, boundary, database, metadata, counts,
                               config_identities, maximum_attempts=20, counters=None,
                               boundary_policy='OS_WRITE_DENIAL_V2', capture_markets=('kr', 'us')):
    """One original DB snapshot, both original Owners, and SAME-process Source."""
    owners, bridge, handle, capture = {}, None, None, None
    try:
        require(type(approval) is prospective.OperatorApproval, 'official_original_approval_required')
        decision = prospective._approval(approval)
        require(tuple(sorted(decision.subjects)) == registered_subjects(), 'official_exact_registered22_scope')
        require(maximum_attempts == 20, 'official_exact_http_limit')
        from app.services import source_parent_canary_v3 as v3
        require(boundary_policy in ('OS_WRITE_DENIAL_V2',v3.DB_POLICY), 'official_boundary_policy')
        require(boundary_policy == v3.DB_POLICY or capture_markets == ('kr','us'), 'official_v2_full_scope')
        device,inode = (v3.require_readonly(boundary,database,approval,consume=True)
            if boundary_policy == v3.DB_POLICY else require_os_boundary(boundary,database))
        if counters is not None:counters['registration_session_attempts'] += 1
        capture = capture_authorized_class_c(ExportPermission(decision.event_id,True,
            Path(database),device,inode,registered_subjects()))
        if boundary_policy == v3.DB_POLICY:
            v3.require_readonly(boundary,database,approval)
        else:
            require_os_boundary(boundary,database)
        raw, receipt = captured_private_snapshot(capture)
        require(len(receipt['statement_templates']) == 5 and receipt['total_changes'] == 0,
                'official_original_query_contract')
        require(receipt['sqlite_mode']=='ro' and receipt['query_only'] is True
                and not receipt['denied_queries'] and receipt['snapshot']=='ONE_BEGIN_READ_TRANSACTION_ROLLBACK',
                'official_original_readonly_receipt')
        if counters is not None:
            counters.update(registration_sessions_completed=1,SELECT=5)
        del raw
        policy = original_identity_policy()
        for market in ('kr','us'):
            owners[market], _ = prospective.issue_prospective_owner(approval=approval,capture=capture,
                market=market,source_generation_id=metadata['run_id']+'-registration',
                generation_id=metadata['run_id'],policy=policy)
        bridge,stock,frozen = registration.prepare_current_bridge(capture=capture,owners=owners,
            policy=policy,stock_metadata=metadata,counts=counts,config_identities=config_identities,
            configured_kr_pages=20,kr_post_acquisition_completeness_approved=True,enabled=True)
        handle = manual.prepare(class_c_bridge=bridge,frozen=frozen,stock_plan=stock,policy=policy,
            maximum_attempts=maximum_attempts,provider_config_sha256=config_identities['kiwoom'],enabled=True,
            capture_markets=capture_markets)
        # Never expose rows or thesis text, even as an exception or diagnostic object.
        public = dict(contract=CONTRACT,boundary_policy=boundary_policy,registration=dict(tables=receipt['tables'],
            snapshot_sha256=receipt['original_rows_sha256'],cutoff=receipt['cutoff'],
            SELECT=len(receipt['statement_templates']),sessions=1,total_changes=0),
            source_plan=manual.describe(handle),sessions=frozen['sessions'],
            private_rows_exported=False,financial_or_economic_authority=False)
        yield handle, public
    finally:
        try:
            if handle is not None: retire_manual(handle)
        finally:
            try:
                if bridge is not None: registration.revoke_bridge(bridge)
            finally:
                for h in owners.values():
                    # The root approval also invalidates already expired children.
                    try: prospective.revoke_prospective_owner(h)
                    except ValueError: pass
                if type(approval) is prospective.OperatorApproval:
                    try: prospective.revoke_approval(approval)
                    except ValueError: pass
                if type(boundary) is EffectiveRegistrationBoundary:_BOUNDARIES.pop(boundary,None)
                from app.services.source_parent_canary_v3 import retire_readonly
                retire_readonly(boundary)
                capture = None


def retire_manual(handle):
    try:
        manual.revoke(handle)
    except ValueError as exc:
        # A failed original dispatch revokes its parent first. The manual
        # handle has already been removed; never replace the original failure.
        if str(exc) != 'scoped_parent_live_capability_required':raise


async def bind_original_worker(*, handle, manifest, configuration, settings, session, output):
    """Original constructors only. No HTTP is made by this composition."""
    import httpx
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.sealed_source_transport import SealedSourceTransport
    from app.services.scoped_worker_launch import CUSTODY_POLICY
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.unified_run_artifacts import durable_json
    require(type(session) is ParticipatingSession, 'official_original_participant_required')
    session.attestation()
    parent,wire,stock = manual.inputs(handle)
    credentials = dict(app_key=settings.kiwoom_app_key,secret_key=settings.kiwoom_secret_key)
    require(all(isinstance(v,str) and v for v in credentials.values()), 'official_original_credentials_missing')
    require(settings.kiwoom_rest_base_url.rstrip('/') == 'https://api.kiwoom.com', 'official_provider_origin')
    output = plain(output)
    output.mkdir(mode=0o700)
    worker_output = output/'worker'; worker_output.mkdir(mode=0o700)
    plan = wire['request_plan']
    config_sha = next(d.config_identity_sha256 for d in plan.descriptors)
    dispatcher = CurrentScopedDispatcher(parent=parent,plan=plan,root=output/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
        config_identities={'kiwoom':config_sha},credential_presence={'kiwoom':True},
        secrets=tuple(credentials.values()),account_pacer=session._lane)
    require(dispatcher._account_pacer is session._lane, 'official_single_parent_lane')
    external = plain(configuration['external_root'])
    pins = original_external_pins(manifest,configuration['external_code_contract'])
    envelope = dict(stage=str(ROOT),output=str(worker_output),external_root=str(external),
        external_pins=pins,external_code_contract=configuration['external_code_contract'],
        stock_plan=stock,request_interval=max(1.5,settings.kiwoom_rest_request_interval_seconds),
        latest_completed_us_session=manual.completed_sessions(handle)['us'],
        us_market_symbols=[],read_paths=[str(ROOT/n) for n in manifest['source_pins']]+
            [str(external/n) for n in pins])
    frozen = output/'worker-plan.json'; durable_json(frozen,envelope,exclusive=True)
    worker = ScopedBridge(parent=parent,original_plan=plan,
        transport=SealedSourceTransport(dispatcher,httpx.AsyncHTTPTransport(retries=0),providers={'kiwoom'}),
        worker=ROOT/'scripts/current_scoped_source_worker.py',frozen=frozen,
        sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=worker_output,
        credentials=credentials,market_reads=(),source_session=session,custody_policy=CUSTODY_POLICY)
    try:
        manual.bind_runtime(handle,dispatcher=dispatcher,worker_bridge=worker)
    except BaseException:
        await worker.transport.inner.aclose()
        raise
    return dispatcher,worker
