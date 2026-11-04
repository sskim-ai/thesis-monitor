"""Manual, default-off Source parent. No daemon, activation or lane repair.

Review the pinned manifest first. A local terminal confirmation is an operator
intent, not an OS permission or an account-wide exclusivity attestation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.machinery import PathFinder
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'official-manual-scoped-source-parent-v2'
MODULES = (
    'app.services.kiwoom_global_lane',
    'app.services.runtime_maintenance',
    'app.services.kiwoom_participant_session',
    'app.services.current_scoped_worker_bridge',
    'app.services.current_scoped_source_dispatch',
    'app.services.scoped_worker_launch',
    'app.services.sealed_source_transport',
    'app.services.manual_scoped_source_runtime',
    'app.services.official_registered_source_runtime',
)


class AdmissionDenied(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise AdmissionDenied(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    raw = Path(path).read_bytes()
    return dict(bytes=len(raw), sha256=digest(raw))


def plain(path):
    path = Path(path)
    require(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)),
            'official_plain_path_required')
    return path


def validate_manifest(path, expected):
    path = plain(path)
    require(path == ROOT/'ops/manual-source-parent.json', 'official_manifest_location')
    raw = path.read_bytes()
    require(digest(raw) == expected, 'official_manifest_digest')
    m = json.loads(raw)
    require(m['contract'] == CONTRACT and m['worktree'] == str(ROOT), 'official_manifest_contract')
    require(m['purpose'] == 'MANUAL_SHADOW_UNSENT' and m['delivery'] == 'NO_SEND', 'official_purpose')
    require(m['default_enabled'] is False and m['owner_approved'] is False, 'official_no_persisted_approval')
    require(m['environment'] == {'KIWOOM_GLOBAL_LANE_REQUIRED': '1'}, 'official_environment_scope')
    require(tuple(m['modules']) == MODULES, 'official_module_scope')
    require(m['operations'] == ['preflight', 'canary'], 'official_operation_scope')
    require(m['limits'] == dict(HTTP=20, retries=0, DB_sessions=1, SELECT=5,
        models=0, KR_bytes=10*1024**3, US_bytes=12*1024**3,
        scratch_bytes=384*1024**2, reserve_bytes=4*1024**3), 'official_limits')
    require(Path(sys.executable) == Path(m['interpreter']), 'official_interpreter_path')
    require(pin(Path(sys.executable).resolve()) == m['interpreter_pin'], 'official_interpreter_changed')
    for name, expected_pin in m['source_pins'].items():
        p = plain(ROOT/name)
        require(p.is_relative_to(ROOT) and p.suffix == '.py'
                and p.relative_to(ROOT).parts[0] in {'app', 'scripts'}, 'official_source_scope')
        require(pin(p) == expected_pin, 'official_source_changed')
    require(m['source_pins'].get(str(Path(__file__).relative_to(ROOT))) == pin(__file__),
            'official_launcher_pin_required')
    return m


def review(m, manifest_sha, operation, invocation):
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{7,79}', invocation) is not None,
            'official_invocation_id')
    require(operation in m['operations'], 'official_operation_denied')
    return dict(contract=CONTRACT, operation=operation, invocation_id=invocation,
        manifest_sha256=manifest_sha, code_installed=True, review_status=m['review_status'],
        reviewed_source_pins_sha256=digest(encoded(m['source_pins'])),
        reviewed_interpreter_pin=m['interpreter_pin'],
        owner_approved=False, operationally_installed=False,
        purpose=m['purpose'], delivery=m['delivery'], limits=m['limits'],
        automatic_canary=False, financial_calls=0, database_sessions=0,
        source_owner_issued=False, worker_launched=False, strict_ready=0)


def confirm_owner(manifest_sha, invocation, operation):
    require(sys.stdin.isatty() and sys.stdout.isatty(), 'official_owner_terminal_required')
    phrase = f'APPROVE {operation} {invocation} {manifest_sha}'
    print('No service activation or host security change. Type exactly:')
    print(phrase, flush=True)
    require(input().strip() == phrase, 'official_owner_confirmation_denied')
    return dict(scope='CURRENT_PROCESS_AND_MANIFEST_ONLY', uid=os.getuid(), pid=os.getpid(),
        at=datetime.now(timezone.utc).isoformat(), invocation_id=invocation,
        manifest_sha256=manifest_sha, operation=operation, statement_sha256=digest(phrase.encode()),
        os_permission_granted=False, account_exclusivity_proven=False)


def bootstrap(m):
    require(sys.flags.isolated and sys.dont_write_bytecode, 'official_isolated_python_required')
    require(not any(n == 'app' or n.startswith('app.') for n in sys.modules), 'official_app_preloaded')
    require(os.environ.get('KIWOOM_MAINTENANCE_STARTUP', '0') == '0', 'official_maintenance_hold')
    require(os.environ.get('KIWOOM_GLOBAL_LANE_REQUIRED') in (None, '1'), 'official_ambient_optin_conflict')
    # This assignment belongs to the reviewed launcher, never to a shell profile.
    os.environ['KIWOOM_GLOBAL_LANE_REQUIRED'] = m['environment']['KIWOOM_GLOBAL_LANE_REQUIRED']
    sys.path.insert(0, str(ROOT))
    sys.meta_path.insert(0, PinnedApplicationImports(m))


class PinnedApplicationImports:
    def __init__(self, manifest):
        self.pins = dict(manifest['source_pins'])

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in {'app', 'scripts'} and not fullname.startswith(('app.', 'scripts.')):
            return None
        spec = PathFinder.find_spec(fullname, path)
        require(spec is not None and spec.origin is not None, 'official_import_not_pinned')
        source = plain(spec.origin)
        require(source.is_relative_to(ROOT), 'official_import_outside_worktree')
        relative = str(source.relative_to(ROOT))
        require(relative in self.pins and pin(source) == self.pins[relative], 'official_import_pin_mismatch')
        # Compile the pinned source instead of allowing an unrelated cached pyc.
        from importlib.machinery import SourceFileLoader
        class PinnedLoader(SourceFileLoader):
            def get_code(self, name):
                raw = source.read_bytes()
                require(dict(bytes=len(raw), sha256=digest(raw)) == self_expected, 'official_import_race')
                return compile(raw, str(source), 'exec', dont_inherit=True)
        self_expected = self.pins[relative]
        spec.loader = PinnedLoader(fullname, str(source))
        return spec


class ReadOnlyPreflight:
    """Defense in depth for audited Python imports, not a claimed OS sandbox."""
    def __init__(self, lane_root, receipt_path=None):
        self.lock = plain(lane_root)/'lane.lock'
        self.receipt_path = receipt_path
        self.denials = []

    def __call__(self, event, args):
        reason = None
        if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'socket.sendto',
                     'sqlite3.connect', 'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.fork'):
            reason = 'official_preflight_no_io_or_child'
        if event.startswith(('os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.chmod', 'os.truncate')):
            reason = 'official_preflight_no_mutation'
        if event == 'open' and isinstance(args[0], (str, bytes)):
            p = Path(os.fsdecode(args[0])).absolute()
            if (p.name.startswith('.env') or p.name in {'auth.json', 'auth.toml'}
                    or p.suffix in {'.key', '.pem', '.db', '.sqlite', '.sqlite3'}
                    or p.name.endswith(('-wal', '-shm'))):
                reason = 'official_preflight_no_private_file'
            flags = args[2]
            # Original participant checks open the existing lock read/write,
            # without acquiring a slot or writing it. Creation/truncation is denied.
            lock_check = (p == self.lock and flags & os.O_ACCMODE == os.O_RDWR
                and flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND) == 0)
            receipt_create = (p == self.receipt_path and flags & os.O_EXCL
                and flags & os.O_CREAT and not flags & (os.O_RDWR | os.O_TRUNC | os.O_APPEND))
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND) and not (lock_check or receipt_create):
                reason = 'official_preflight_no_file_write'
        if reason:
            self.denials.append(dict(event=event, reason=reason))
            raise AdmissionDenied(reason)


def lane_snapshot(root):
    result = {}
    for name in ('activation.json', 'state.json', 'lane.lock'):
        p = plain(root)/name
        s = p.stat()
        require(s.st_uid == os.getuid() and not s.st_mode & 0o077 and s.st_nlink == 1,
                'official_lane_metadata_denied')
        result[name] = dict(device=s.st_dev, inode=s.st_ino, bytes=s.st_size)
        if name != 'lane.lock':
            result[name].update(pin(p))
    return result


def admit_parent(m):
    modules = tuple(importlib.import_module(n) for n in MODULES)
    lane, maintenance, participant = modules[:3]
    require(str(lane.DEFAULT_ROOT) == m['lane_root'], 'official_original_lane_root_changed')
    maintenance.assert_operation_allowed()
    before = lane_snapshot(lane.DEFAULT_ROOT)
    session = participant.ParticipatingSession(modules=modules, caller_kind='CLI')
    try:
        return _check_admitted_parent(m, modules, session, before)
    except BaseException:
        session.close_admission()
        raise


def _check_admitted_parent(m, modules, session, before):
    lane = modules[0]
    attestation = session.attestation()
    from app.services.unified_snapshot_contract import digest as original_digest
    require(original_digest(attestation['activation']) == m['activation_digest'], 'official_activation_changed')
    require(list(session._lane.lock_identity) == m['lock_identity'], 'official_original_lock_changed')
    # _state() may latch a STOP. Read only; never call it in this phase.
    state = lane._read(lane.DEFAULT_ROOT/'state.json')
    require(state['generation'] == attestation['activation']['generation']
            and state['boot_identity'] == attestation['boot_identity'], 'official_state_epoch_changed')
    require(not state['halted'] and not state['in_flight'], 'official_lane_stop_or_inflight')
    require(before == lane_snapshot(lane.DEFAULT_ROOT), 'official_lane_changed_during_preflight')
    return session, dict(parent=attestation, lane_before=before, lane_after=before,
        sequence_observed=state['sequence'], account_exclusivity='NOT_PROVEN_BY_PID_OR_STATE',
        child_policy=dict(contract=modules[5].CONTRACT, custody=modules[5].CUSTODY_POLICY,
            original_policy_source=pin(modules[5].__file__), source_parity=True,
            effective_child_isolation='NOT_RUN_REQUIRES_ORIGINAL_BRIDGE_LAUNCH'),
        physical_slots=0, credentials_read=False, database_sessions=0)


def require_canary_installation(m, invocation):
    # The previous unused P2L grant is evidence only, not a current capability.
    c = m['canary_installation']
    require(c['state'] == 'CURRENT_OWNER_REVIEW_REQUIRED', 'official_canary_installation_state')
    require(c.get('current_invocation_id') == invocation and c.get('settings_file')
            and c.get('database') and c.get('os_readonly_launcher')
            and c.get('output_root') and c.get('external_root') and c.get('external_code_contract')
            and c.get('external_head') and c.get('instruction_sha1') and c.get('owner_preflight'),
            'official_current_canary_configuration_and_grant_required')
    for key in ('database','settings_file','output_root','external_root','os_readonly_launcher'):
        plain(c[key])
    require(re.fullmatch('[0-9a-f]{40}',c['instruction_sha1']) is not None,
            'official_instruction_legacy_identity')
    require(Path(c['output_root']).parent.is_dir() and not Path(c['output_root']).exists(),
            'official_fresh_canary_output_required')
    # Configuration is a proposal. Actual kernel policy and live approvals are
    # separately required by run_canary before any settings/registration read.
    return c


def require_owner_preflight(m, configuration, manifest_sha):
    spec = configuration['owner_preflight']
    path = plain(spec['path'])
    require(path.parent == Path(m['owner_receipts_root']) and pin(path) == spec['pin'],
            'official_owner_preflight_custody')
    r = json.loads(path.read_bytes())
    require(r.get('status') == 'READONLY_PARENT_ADMITTED_WORKER_AND_CANARY_PENDING'
            and r.get('owner_approved') is True and r.get('parent_closed') is True
            and r.get('financial_calls') == 0 and r.get('database_sessions') == 0,
            'official_owner_preflight_not_passed')
    # Pin the preflight's source/manifest identity in the reviewed current
    # manifest, rather than creating a circular hash by embedding the receipt.
    require(r.get('manifest_sha256') == spec['manifest_sha256']
            and r.get('reviewed_source_pins_sha256') == digest(encoded(m['source_pins']))
            and r.get('reviewed_interpreter_pin') == m['interpreter_pin'],
            'official_owner_preflight_code_changed')
    intent = r['owner_intent']
    now = datetime.now(timezone.utc)
    at = datetime.fromisoformat(intent['at'])
    require(intent['uid'] == os.getuid() and at.utcoffset() is not None
            and 0 <= (now-at).total_seconds() <= 3600, 'official_owner_preflight_stale')
    require(intent['operation'] == 'preflight' and intent['manifest_sha256'] == r['manifest_sha256']
            and intent['invocation_id'] == r['invocation_id'], 'official_owner_preflight_intent_mismatch')
    return r


def confirm_canary_grant(manifest_sha, invocation, database, subjects):
    from datetime import timedelta
    from app.services.prospective_class_c_owner import ApprovalDecision, record_backend_approval
    require(sys.stdin.isatty() and sys.stdout.isatty(), 'official_owner_terminal_required')
    phrase = f'APPROVE canary {invocation} {manifest_sha} DB1_SELECT5_KIWOOM20_NO_RETRY_NO_CONCURRENT_USE'
    print('Current 22 registered subjects; one readonly four-table snapshot; KR1+US1 daily Source only.')
    print('Database:', database)
    print('No models, orders, sends, services or scheduler changes. Prior grants are not reused.')
    print(phrase,flush=True)
    require(input().strip() == phrase, 'official_current_scope_and_exclusivity_required')
    now = datetime.now(timezone.utc)
    return record_backend_approval(ApprovalDecision(event_id=invocation,user_message_sha256=digest(phrase.encode()),
        approved=True,effective_at=now,expires_at=now+timedelta(minutes=55),subjects=subjects))


async def run_canary(m, configuration, manifest_sha, invocation, report, *, v3_scope=None):
    from app.services import official_registered_source_runtime as registered
    from app.services import prospective_class_c_owner as prospective
    from app.services.unified_run_artifacts import durable_json
    from app.services.unified_snapshot_contract import digest as original_digest
    session = approval = boundary = worker = dispatcher = None
    output = None
    counters = dict(registration_session_attempts=0,registration_sessions_completed=0,SELECT=0,
                    settings_read_attempts=0,physical_HTTP=0,worker_launches=0,cold_processes=0)
    report['canary_counters'] = counters
    try:
        markets, boundary_policy = ('kr','us'), 'OS_WRITE_DENIAL_V2'
        if v3_scope is None:
            require_owner_preflight(m,configuration,manifest_sha)
            resources = registered.check_space([Path(configuration['output_root']).parent])
            session, parent_proof = admit_parent(m)
            boundary = registered.admit_os_boundary(configuration['database'])
            approval = confirm_canary_grant(manifest_sha,invocation,configuration['database'],registered.registered_subjects())
        else:
            from app.services import source_parent_canary_v3 as v3
            require(m['contract']==v3.CONTRACT and type(v3_scope) is v3.CanaryScope, 'official_v3_explicit_contract')
            resources = v3.check_space([Path(configuration['output_root']).parent],v3_scope)
            # Use this exact loader instance, not a second unverified import.
            from types import SimpleNamespace
            session, parent_proof = v3.admit_parent(m,SimpleNamespace(**globals()))
            approval = v3.confirm_grant(manifest_sha,invocation,configuration,v3_scope)
            boundary = v3.admit_readonly(configuration['database'],approval,enabled=True)
            markets, boundary_policy = v3_scope.markets, v3.DB_POLICY
        output = claim_current_invocation(configuration,manifest_sha,invocation)
        from app.config import Settings
        counters['settings_read_attempts'] += 1
        settings = Settings(_env_file=configuration['settings_file'])
        public_config = dict(provider='kiwoom',base_url=settings.kiwoom_rest_base_url,
            interval=max(1.5,settings.kiwoom_rest_request_interval_seconds),retries=0)
        config_sha = original_digest(public_config)
        config_ids = {n:original_digest(dict(provider=n,state='UNREQUESTED_NOT_CONFIGURED'))
            for n in ('sec_edgar','opendart','fred','eia','ecos','krx_night_futures','google_news_rss','naver_news')}
        config_ids['kiwoom'] = config_sha
        metadata = dict(run_id=invocation,acquisition_id=invocation+'-D',
            instruction_sha=configuration['instruction_sha1'],
            implementation_sha=hashlib.sha1(encoded(m['source_pins'])).hexdigest(),
            owner_files={n:p['sha256'] for n,p in registered.original_external_pins(
                m,configuration['external_code_contract']).items()},
            owner_head=configuration['external_head'],settings_sha256=config_sha,
            request_environment_sha256=original_digest(public_config))
        counts = {market:dict(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,
            unadjusted_weekly_valuation=300) for market in ('kr','us')}
        with session.operation(), registered.capture_registered_runtime(approval=approval,boundary=boundary,
                database=configuration['database'],metadata=metadata,counts=counts,
                config_identities=config_ids,counters=counters,boundary_policy=boundary_policy,
                capture_markets=markets) as (handle,registration):
            if v3_scope is not None:
                report['v3_frozen_plan'] = v3.validate_plan(handle,v3_scope)
            dispatcher,worker = await registered.bind_original_worker(handle=handle,manifest=m,
                configuration=configuration,settings=settings,session=session,output=output/'source-runtime')
            durable_json(output/'registered-plan.json',registration,exclusive=True)
            result = await consume_original_runtime(handle=handle,dispatcher=dispatcher,worker_bridge=worker,markets=markets)
            counters['cold_processes'] += 1
            cold = await cold_readback(m,dispatcher,result,output,markets=markets)
            return dict(status='ORIGINAL_SOURCE_ONLY_AND_COLD_PASS',registration=registration,
                source=result,cold=cold,parent=parent_proof,resources=resources,
                financial_calls=dispatcher.physical_attempts,database_sessions=1,models=0,
                native=False,market=False,strict_ready=0)
    finally:
        if dispatcher is not None:counters['physical_HTTP'] = dispatcher.physical_attempts
        if worker is not None:counters['worker_launches'] = int(worker.process is not None)
        report['financial_calls'] = counters['physical_HTTP']
        report['database_sessions'] = counters['registration_session_attempts']
        report['worker_launched'] = bool(counters['worker_launches'])
        try:
            if worker is not None:
                try: await worker.shutdown()
                finally: await worker.transport.inner.aclose()
        finally:
            try:
                if approval is not None:
                    try: prospective.revoke_approval(approval)
                    except ValueError: pass
                if boundary is not None: registered._BOUNDARIES.pop(boundary,None)
                if v3_scope is not None:
                    from app.services.source_parent_canary_v3 import retire_readonly
                    retire_readonly(boundary)
            finally:
                try:
                    if session is not None: session.close_admission()
                finally:
                    if output is not None:
                        durable_json(output/'attempt-counters.json',counters,exclusive=True)


def claim_current_invocation(configuration, manifest_sha, invocation):
    from app.services.unified_run_artifacts import durable_json
    output = plain(configuration['output_root'])
    output.mkdir(mode=0o700)
    durable_json(output/'invocation-claimed.json',dict(invocation_id=invocation,
        manifest_sha256=manifest_sha,claimed_at=datetime.now(timezone.utc).isoformat(),
        scope='ONE_CURRENT_EXPLICIT_GRANT_NOT_A_SERIALIZED_CAPABILITY',
        automatic_retry=False),exclusive=True)
    return output


async def cold_readback(m, dispatcher, source_result, output, *, markets=('kr','us')):
    import asyncio
    from app.services.unified_run_artifacts import durable_json
    from app.services.unified_snapshot_contract import digest as original_digest
    require(markets in (('kr',),('kr','us')), 'official_cold_market_scope')
    require(source_result['status']=='SOURCE_CONSUMED_COLD_READBACK_STILL_REQUIRED'
            and len(source_result['receipts'])==len(markets) and len(source_result.get('row_artifacts',[]))==len(markets),
            'official_cold_original_source_required')
    request = dict(contract=('official-issued-source-cold-v1' if markets==('kr','us')
                            else 'official-issued-source-cold-kr-v3'),capture=str(dispatcher.root),
        plan=dispatcher.plan.model_dump(mode='json'),
        receipts={k:v['receipt_sha256'] for k,v in dispatcher.results.items() if v['status']=='PASS'},
        already_issued_source_receipts=source_result['receipts'],
        row_artifacts=source_result['row_artifacts'],source_pins=m['source_pins'])
    path = output/'cold-input.json'; durable_json(path,request,exclusive=True)
    proc = await asyncio.create_subprocess_exec(m['interpreter'],'-I','-B',
        str(ROOT/'scripts/official_source_cold.py'),str(path),digest(path.read_bytes()),
        stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},cwd=str(output))
    async def bounded(stream, limit):
        body = bytearray()
        while True:
            chunk = await stream.read(4096)
            if not chunk: return bytes(body)
            body.extend(chunk)
            require(len(body)<=limit,'official_cold_output_limit')
    try:
        stdout,stderr,_ = await asyncio.wait_for(asyncio.gather(
            bounded(proc.stdout,128*1024),bounded(proc.stderr,4096),proc.wait()),timeout=60)
    except BaseException:
        if proc.returncode is None:proc.kill()
        await proc.communicate()
        raise
    require(proc.returncode==0 and len(stdout)<=128*1024 and not stderr, 'official_cold_process_failed')
    value = json.loads(stdout)
    require(value['pid'] != os.getpid() and value['input_sha256']==digest(path.read_bytes())
            and value['receipt_set_sha256']==original_digest(request['receipts'])
            and value['new_live_authority'] is False, 'official_cold_process_identity')
    durable_json(output/'cold-receipt.json',value,exclusive=True)
    return value


async def consume_original_runtime(*, handle, dispatcher, worker_bridge, markets=('kr','us')):
    """The real in-process composition; serialized receipts cannot enter here.

    Only a separately qualified host with a current registered-memory grant may
    create these original objects. This function never issues registration or
    financial authorization, loads keys, or substitutes an alternate transport.
    """
    from app.services import manual_scoped_source_runtime as manual
    from app.services import current_scoped_source_results as results
    from app.services.official_registered_source_runtime import retire_manual
    try:
        parent, wire, _ = manual.inputs(handle)
        require(dispatcher.maximum_attempts <= 20, 'official_http_cap')
        require(markets in (('kr',),('kr','us')), 'official_consumer_market_scope')
        require(len(wire['stock_reads']) == len(markets)
                and {r.market for r in wire['stock_reads']} == set(markets)
                and {r.role for r in wire['stock_reads']} == {'adjusted_daily'}, 'official_d_only_scope')
        require(all(d.provider == 'kiwoom' for d in wire['request_plan'].descriptors), 'official_provider_scope')
        manual.bind_runtime(handle, dispatcher=dispatcher, worker_bridge=worker_bridge)
        capture = await manual.command(handle, {'stocks': True})
        require(capture['status'] == 'CAPTURE_COMPLETE_NOT_QUALIFIED', 'official_capture_incomplete')
        for replay_id in (1, 2):
            replay = await manual.command(handle, {'replay': replay_id})
            require(all(r['status'] == 'PASS' for r in replay['rows']), 'official_replay_denied')
        for r in wire['stock_reads']:
            value = await manual.command(handle, {'projection': r.entry_id})
            require(value['status'] == 'COMPLETED_PROJECTION_REPLAY_PASS', 'official_projection_denied')
        await worker_bridge.shutdown()
        require(worker_bridge.process is not None and worker_bridge.process.returncode == 0,
                'official_worker_exit_not_normal')
        from app.services.unified_run_artifacts import durable_json
        receipts, row_artifacts = [], []
        for r in wire['stock_reads']:
            cap = results.issue_source_result(parent, dispatcher=dispatcher, entry_id=r.entry_id)
            try:
                value = results.read_source_rows(parent, cap, dispatcher=dispatcher, entry_id=r.entry_id)
                receipts.append(value['receipt'])
                path = dispatcher.root/'issued-source'/f'{len(receipts):02d}.json'
                durable_json(path,value['rows'],exclusive=True)
                row_artifacts.append(dict(entry_id=r.entry_id,path=str(path.relative_to(dispatcher.root)),
                    sha256=digest(path.read_bytes())))
            finally:
                results.revoke_source_result(cap)
        return dict(status='SOURCE_CONSUMED_COLD_READBACK_STILL_REQUIRED', receipts=receipts,
            row_artifacts=row_artifacts,
            physical_HTTP=dispatcher.physical_attempts, cold_readback='NOT_RUN', native=False, models=0)
    finally:
        try:
            await worker_bridge.shutdown()
        finally:
            retire_manual(handle)


def safe_error(exc):
    value = str(exc)
    if re.fullmatch(r'(official_|global_lane_|participant_|maintenance_)[A-Za-z0-9_:-]{1,160}', value):
        return value
    return type(exc).__name__


def receipt_destination(m, invocation, supplied):
    if supplied is None:
        return None
    path = plain(supplied)
    root = plain(m['owner_receipts_root'])
    require(path == root/(invocation+'.json') and root.is_dir() and not path.exists(),
            'official_receipt_fresh_exact_path_required')
    require(root.stat().st_uid == os.getuid() and not root.stat().st_mode & 0o077,
            'official_receipt_private_directory_required')
    return path


def write_public_receipt(report):
    if report.get('receipt_path'):
        fd = os.open(report['receipt_path'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(encoded(report))
            f.flush()
            os.fsync(f.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT/'ops/manual-source-parent.json')
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--invocation-id', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight', action='store_true')
    group.add_argument('--canary', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='Review only; no application imports or opt-in')
    parser.add_argument('--receipt', type=Path, help='New receipt under the pinned private task directory only')
    args = parser.parse_args(argv)
    report = dict(status='BLOCKED_BEFORE_ADMISSION', financial_calls=0, database_sessions=0,
                  models=0, slot_calls=0, worker_launched=False)
    guard = None
    try:
        m = validate_manifest(args.manifest, args.manifest_sha256)
        operation = 'canary' if args.canary else 'preflight'
        report.update(review(m, args.manifest_sha256, operation, args.invocation_id))
        receipt = receipt_destination(m, args.invocation_id, args.receipt)
        if receipt is not None:
            report['receipt_path'] = str(receipt)
        if args.dry_run:
            report['status'] = 'REVIEW_ONLY_NO_APP_IMPORT_OR_OPTIN'
            return report, 0
        if args.canary:
            require(receipt is not None,'official_current_canary_receipt_required')
            configuration = require_canary_installation(m, args.invocation_id)
            require_owner_preflight(m,configuration,args.manifest_sha256)
            require(sys.stdin.isatty() and sys.stdout.isatty(), 'official_owner_terminal_required')
            bootstrap(m)
            import asyncio
            report.update(asyncio.run(run_canary(m,configuration,args.manifest_sha256,args.invocation_id,report)))
            return report,0
        report['owner_intent'] = confirm_owner(args.manifest_sha256, args.invocation_id, operation)
        report['owner_approved'] = True
        guard = ReadOnlyPreflight(m['lane_root'], receipt)
        sys.addaudithook(guard)
        bootstrap(m)
        session, proof = admit_parent(m)
        report.update(proof)
        session.close_admission()
        report.update(status='READONLY_PARENT_ADMITTED_WORKER_AND_CANARY_PENDING',
            owner_approved=True, parent_closed=True, audit_denials=guard.denials,
            preflight_scope='ACTUAL_PARENT_ONLY_CHILD_POLICY_SOURCE_PARITY_NOT_EFFECTIVE_WORKER_PROOF')
        return report, 0
    except BaseException as exc:
        report.update(error=safe_error(exc), exception_type=type(exc).__name__,
            status=('HOST_OWNER_EXECUTION_REQUIRED' if str(exc) == 'official_owner_terminal_required'
                    else 'BLOCKED_OFFICIAL_PARENT'))
        if str(exc) == 'global_lane_boot_identity_unavailable':
            import ctypes
            report['boot_errno'] = ctypes.get_errno()
            report['status'] = 'HOST_BOOT_PERMISSION_DENIED' if report['boot_errno'] == 1 else 'HOST_BOOT_IDENTITY_UNAVAILABLE'
        if guard is not None:
            report['audit_denials'] = guard.denials
        # No arbitrary exception repr/traceback: imports may eventually handle keys.
        return report, 2


if __name__ == '__main__':
    report, code = main()
    write_public_receipt(report)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(code)
