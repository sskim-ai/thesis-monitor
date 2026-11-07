"""Fresh C21H issuance over the pinned Sol capability; disabled without approval."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback
import uuid

from maintenance.guarded_sol_host import Binding, TASK, digest, plain, write_once
from maintenance.guarded_sol_canary import run_stage, same_journal_target


def validate_scope(scope, binding):
    expected = dict(task='C21H', model='gpt-6.1-sol', effort='high', maximum_contexts=2,
                    stage_seconds=600, input_bytes=393216, output_bytes=131072, retries=0, send=False)
    if any(scope.get(k) != v for k, v in expected.items()):
        raise ValueError('C21H_EXACT_LIMITS')
    if not scope.get('run_id', '').startswith('C21H_SOL_HIGH_20261107_'):
        raise ValueError('C21H_FRESH_RUN_ID')
    root, runtime, journal = (plain(scope[k]) for k in ('root', 'runtime', 'journal'))
    if root.name != '20261107-c21h' or runtime.name != 'c21h-20261107' or journal.name != 'c21h-sol-stage-journal-20261107':
        raise ValueError('C21H_FRESH_PATH_NAMES')
    if len({root, runtime, journal}) != 3 or any(a.is_relative_to(b) for a in (root, runtime, journal) for b in (root, runtime, journal) if a != b):
        raise ValueError('C21H_DISTINCT_ROOTS')
    if scope['guard_capability'] != TASK or binding.root != runtime or binding.scope.parent != root/'private':
        raise ValueError('C21H_CAPABILITY_SCOPE')
    bound = binding.verify()
    if bound['owner_sha256'] != scope['packet_sha256'] or binding.scope_sha256 != scope['scope_sha256']:
        raise ValueError('C21H_SOURCE_SCOPE_PIN')
    return root, runtime, journal


def require_fresh(root, runtime, journal):
    if journal.exists() or journal.is_symlink():
        raise ValueError('C21H_JOURNAL_ALREADY_EXISTS')
    if any((root/n).exists() for n in ('EXECUTION_STARTED.json', 'LIVE_RESULT.json', 'private/live')):
        raise ValueError('C21H_RUN_ALREADY_STARTED')
    # A prepared runtime has no ledgers, lock files, or Stage directories.
    if list(runtime.iterdir()):
        raise ValueError('C21H_RUNTIME_ALREADY_USED')


def validate_authorization(auth, scope, head):
    expected = dict(task='C21H', approved=True, confirmed_no_concurrent_use=True,
        run_id=scope['run_id'], scope_sha256=digest(scope), request_sha256=scope['request_sha256'],
        head=head, model='gpt-6.1-sol', effort='high', maximum_contexts=2,
        stage_seconds=600, input_bytes=393216, output_bytes=131072, retries=0,
        financial_HTTP=0, operating_DB=0, send=False)
    if any(auth.get(k) != v for k, v in expected.items()) or not auth.get('approval_basis'):
        raise ValueError('C21H_CURRENT_EXPLICIT_APPROVAL_REQUIRED')


def install_boundary(root, runtime, journal):
    def audit(event, args):
        if event in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname'):
            raise PermissionError('C21H_PARENT_NETWORK_DENIED')
        if event == 'sqlite3.connect' and not same_journal_target(args[0], journal/'research.sqlite3'):
            raise PermissionError('C21H_ONLY_FRESH_JOURNAL_DB_ALLOWED')
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0]))
            if path.name.startswith('.env') or path.name == 'auth.json':
                raise PermissionError('C21H_PARENT_SECRET_READ_DENIED')
            resolved = path.resolve()
            if ('.sqlite' in path.name or path.suffix == '.db') and not resolved.is_relative_to(journal):
                raise PermissionError('C21H_EXISTING_DB_ACCESS_DENIED')
            if len(args) > 2 and isinstance(args[2], int) and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
                if not any(resolved.is_relative_to(p) for p in (root, runtime, journal)):
                    raise PermissionError('C21H_WRITE_OUTSIDE_FRESH_TASK')
    sys.addaudithook(audit)


def execute_once(root):
    root = plain(root)
    scope = json.loads((root/'private/run-scope.json').read_bytes())
    values = json.loads((root/'private/binding.json').read_bytes())
    for key in ('binary', 'catalog', 'legacy', 'root', 'scope'):
        values[key] = Path(values[key])
    binding = Binding(**values)
    checked_root, runtime, journal = validate_scope(scope, binding)
    if root != checked_root:
        raise ValueError('C21H_ROOT_MISMATCH')
    worktree = plain(scope['worktree'])
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=worktree, text=True).strip()
    head = git('rev-parse', 'HEAD')
    if git('status', '--porcelain'):
        raise ValueError('C21H_WORKTREE_DRIFT')
    auth_path = plain(root/'USER_AUTHORIZATION.json')
    if auth_path.stat().st_mode & 0o222:
        raise ValueError('C21H_APPROVAL_NOT_FROZEN')
    authorization = json.loads(auth_path.read_bytes())
    validate_authorization(authorization, scope, head)
    freeze = json.loads((root/'OFFLINE_FREEZE.json').read_bytes())
    if freeze['head'] != head or freeze['scope_sha256'] != digest(scope):
        raise ValueError('C21H_FREEZE_DRIFT')
    for relative, expected in freeze['code_pins'].items():
        if digest(plain(worktree/relative).read_bytes()) != expected:
            raise ValueError('C21H_CODE_PIN_DRIFT')
    require_fresh(root, runtime, journal)
    install_boundary(root, runtime, journal)
    free = int(subprocess.check_output(['/bin/df', '-k', str(root)], text=True).splitlines()[-1].split()[3]) * 1024
    if free < 2*1024**3 + 256*1024**2:
        raise ValueError('C21H_DISK_GUARD')
    write_once(root/'PRE_GC_LIVE.json', dict(free_bytes=free, peak_bytes=256*1024**2,
        reserve_bytes=2*1024**3, decision='PRE_GC_NOOP_SUFFICIENT', actions=[]))
    write_once(root/'EXECUTION_STARTED.json', dict(task='C21H', run_id=scope['run_id'], head=head,
        approval_sha256=digest(authorization), scope_sha256=digest(scope), at=datetime.now(timezone.utc).isoformat()), 0o400)
    out = root/'private/live'
    out.mkdir(mode=0o700)
    result = dict(status='PREMODEL_INITIALIZATION', accepted_stages=[], financial_HTTP=0,
                  operating_DB=0, retries=0, send=False, strict_ready=0, original_two_stage_owner=False, NO_SEND=False)
    counts = None
    phase = 'HOST_SETUP'
    try:
        from maintenance.c21g_analysis_source import restore_view
        from app.services import vnext_balanced_stage_review as stages
        from app.services import vnext_unified_judgment as engine
        from app.services.vnext_daily_research import UseRegistry
        from app.services.vnext_execution_profile import SOL_HIGH_V1
        from app.services.vnext_optional_fy1_research import attach
        from app.services.vnext_codex_research import numeric_catalog
        from app.services.vnext_research_store import ResearchStore
        from app.services.vnext_runtime import RuntimeConfig
        from app.services.vnext_public_capture import target_session
        from app.services.vnext_unified_dispatch import consume

        packet_path = plain(scope['packet_path'])
        packet = json.loads(packet_path.read_bytes())
        if digest(packet) != scope['packet_sha256']:
            raise ValueError('C21H_PACKET_CHANGED')
        view, counts = restore_view(packet=packet, **scope['source'])
        registry = UseRegistry()
        ticker = packet['base']['public_security']['ticker']
        def economic_loader():
            base = view.packet(ticker)
            base['numeric_catalog'] = numeric_catalog(base)
            return attach(base)
        def source_loader():
            if json.loads(packet_path.read_bytes()) != packet:
                raise ValueError('C21H_FROZEN_PACKET_DRIFT')
            return engine.build_bundle(economic_loader(), registry=registry, contract=engine.AI_OWNED_V3,
                                       valuation_analysis_owner=view)
        if source_loader() != packet:
            raise ValueError('C21H_LIVE_SOURCE_OWNER_PACKET_MISMATCH')
        result['original_source_owner_rebound'] = True
        write_once(out/'SOURCE_BOUND.json', dict(packet_sha256=digest(packet), view_type=type(view).__name__,
            source_counts=counts, dated_only=True, new_financial_capture=0))
        rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm=,args='], text=True).splitlines()
        others = []
        for row in rows:
            parts = row.strip().split(None, 2)
            if len(parts) != 3 or not parts[0].isdigit() or int(parts[0]) in (os.getpid(), os.getppid()):
                continue
            if (Path(parts[1]).name == 'codex' and ' exec ' in ' '+parts[2]+' ') or str(binding.binary) in parts[2]:
                others.append(int(parts[0]))
        write_once(out/'CALLERS.json', dict(other_analysis_PIDs=others,
            user_no_concurrency=True, scope='Local observation plus current explicit user confirmation'))
        if others:
            raise ValueError('C21H_OTHER_ANALYSIS_PROCESS_PRESENT')
        journal.mkdir(mode=0o700)
        ResearchStore(journal/'research.sqlite3')
        config = RuntimeConfig(journal/'research.sqlite3', scope['run_id'], mode='write', environment='test')
        config.validate()
        @contextmanager
        def lease():
            fd = os.open(runtime/'signed-in-analysis.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError('C21H_LEASE_IDENTITY')
                fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
                yield
            finally:
                os.close(fd)
        latest, _ = target_session(packet['base']['public_security']['country'].lower(), datetime.now(timezone.utc))
        session = latest.isoformat() if hasattr(latest, 'isoformat') else str(latest)
        basis = json.loads(next(f['basis'] for f in packet['investment_valuation_context']['facts'] if f['metric'] == 'FPER'))
        prior_session = basis['price']['session']
        if prior_session >= session:
            raise ValueError('C21H_DATED_PRICE_SESSION')
        account = binding.verify()['account']
        accepted, requests = {}, {}
        frozen_request = json.loads((root/'private/BLIND-request.json').read_bytes())
        if digest(frozen_request) != scope['request_sha256']:
            raise ValueError('C21H_FRESH_REQUEST_PIN')
        for name in ('BLIND', 'ADJUDICATION'):
            prior = accepted.get('BLIND') if name == 'ADJUDICATION' else None
            invocation = frozen_request['invocation_id'] if name == 'BLIND' else 'C21H_SOL_ADJ_'+uuid.uuid4().hex
            request, _ = stages._stage_request(invocation_id=invocation, account=account, packet=packet,
                stage=name, version=stages.UNIFIED_AI_V3_SOL_HIGH, knowledge='', registry=registry, prior=prior)
            if name == 'BLIND' and request != frozen_request:
                raise ValueError('C21H_REQUEST_REBUILD_MISMATCH')
            requests[name] = deepcopy(request)
            def approval(candidate):
                return (candidate == requests.get(candidate.get('stage'))
                    and candidate['model'] == 'gpt-6.1-sol' and candidate['effort'] == 'high'
                    and candidate['source_sha'] == scope['packet_sha256']
                    and digest(json.loads(auth_path.read_bytes())) == digest(authorization)
                    and not (runtime/'STOP').exists() and not (journal/'STOP').exists()
                    and git('rev-parse', 'HEAD') == head)
            phase = 'HOST_SETUP'
            result['last_stage'] = name
            cap, host = run_stage(binding=binding, config=config, packet=packet, registry=registry,
                source_loader=source_loader, economic_loader=economic_loader, valuation_analysis_owner=view,
                request=request, knowledge='', approval=approval, account_lease=lease, session=session,
                prior_session=prior_session, out=out/name, prior=prior, enabled=True)
            if cap is None:
                result.update(status='PARTIAL_HOST_STAGE_NOT_ACCEPTED', host_state=host['state'])
                return
            accepted[name] = cap
            result['accepted_stages'].append(name)
        sessions = [json.loads((out/n/'HOST_TRANSPORT.json').read_bytes())['session'] for n in ('BLIND', 'ADJUDICATION')]
        if len(set(sessions)) != 2:
            raise ValueError('C21H_DISTINCT_MODEL_SESSIONS_REQUIRED')
        result['distinct_sessions'] = True
        with lease():
            phase = 'OWNER'
            owner = stages.StageReviewOwner(accepted['BLIND'], accepted['ADJUDICATION'], enabled=True)
            result['original_two_stage_owner'] = True
            controller = stages.StageController(config, enabled=True, execution_profile=SOL_HIGH_V1)
            phase = 'NO_SEND'
            output = consume(controller, packet=packet, owner=owner, mode='DATED_REPLAY', enabled=True,
                output_context=dict(observed_as_of=packet['base']['as_of'], completed_market_session=session,
                    freshness_by_source={f['source_generation']: dict(retrieved_at=f['retrieval_timestamp'], current=False)
                                         for f in packet['investment_valuation_context']['facts']},
                    required_market_fields=['FULL_KR_MARKET_NOT_SUPPLIED', 'FULL_US_MARKET_NOT_SUPPLIED'],
                    current_price_denials=['DATED_FPER_PRICE_IS_NOT_CURRENT_PRICE'],
                    source_revisions=['NOT_NEWLY_CHECKED_NO_FINANCIAL_HTTP']))
            if output['send'] is not False or output['strict_ready'] is not False:
                raise ValueError('C21H_NO_SEND_ONLY')
            write_once(out/'NO_SEND.json', output)
            write_once(out/'NO_SEND.md', output['message'].encode())
            result.update(status='C21H_FRESH_SOL_BLIND_ADJ_ACCEPTED_NO_SEND_PASS', NO_SEND=True,
                          decision_sha256=output['decision_sha256'])
    except Exception as exc:
        result.update(status='BLOCKED_NO_RETRY', error_type=type(exc).__name__, reason=str(exc)[:2000], phase=phase)
        write_once(out/'FAILURE_PRIVATE.json', dict(type=type(exc).__name__, trace=traceback.format_exc(), retry=False))
    finally:
        result.update(stage_host_attempts=len(list(out.glob('*/MODEL_STARTED.json'))),
            returned_model_outputs=len(list(out.glob('*/MODEL_RAW.txt'))), source_owner_consumptions=counts,
            private_DB_bytes=sum(p.stat().st_size for p in journal.glob('*') if p.is_file()) if journal.exists() else 0)
        write_once(root/'LIVE_RESULT.json', result)
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] != ['--execute-once']:
        raise SystemExit('C21H disabled: explicit --execute-once and current frozen approval required')
    sys.dont_write_bytecode = True
    execute_once(Path(os.environ['TM_C21H_TASK_ROOT']))
