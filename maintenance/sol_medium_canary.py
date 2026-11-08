"""Explicitly approved single Medium BLIND; no ADJ or final judgment issuance."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback

from app.services import vnext_balanced_stage_review as stages
from app.services import vnext_unified_judgment as engine
from app.services.vnext_execution_profile import SOL_MEDIUM_V1
from app.services.vnext_daily_research import UseRegistry
from app.services.vnext_optional_fy1_research import attach
from app.services.vnext_codex_research import numeric_catalog
from app.services.vnext_research_store import ResearchStore
from app.services.vnext_runtime import RuntimeConfig
from app.services.vnext_public_capture import target_session
from maintenance.c21g_analysis_source import restore_view
from maintenance.c21h_sol_canary import require_fresh, install_boundary
from maintenance.guarded_sol_canary import run_stage
from maintenance.guarded_sol_host import Binding, MEDIUM_TASK, digest, plain, write_once


def validate_authorization(auth, scope, head):
    expected = dict(task=MEDIUM_TASK, approved=True, confirmed_no_concurrent_use=True,
        run_id=scope['run_id'], scope_sha256=digest(scope), request_sha256=scope['request_sha256'],
        head=head, model=SOL_MEDIUM_V1.model, effort=SOL_MEDIUM_V1.effort,
        execution_profile=SOL_MEDIUM_V1.contract, maximum_contexts=1, BLIND=1, ADJ=0,
        stage_seconds=600, input_bytes=393216, output_bytes=131072, retries=0,
        financial_HTTP=0, operating_DB=0, send=False)
    if any(auth.get(k) != v for k, v in expected.items()) or not auth.get('approval_basis'):
        raise ValueError('medium_fresh_explicit_approval_required')


def execute_once(root):
    root = plain(root)
    scope = json.loads((root/'private/run-scope.json').read_bytes())
    values = json.loads((root/'private/binding.json').read_bytes())
    for key in ('binary', 'catalog', 'legacy', 'root', 'scope'):
        values[key] = Path(values[key])
    binding = Binding(**values)
    runtime, journal = plain(scope['runtime']), plain(scope['journal'])
    worktree = plain(scope['worktree'])
    if (scope['task'] != MEDIUM_TASK or binding.execution_profile != SOL_MEDIUM_V1.contract
            or binding.root != runtime or binding.scope.parent != root/'private'
            or root != Path(scope['root']) or not scope['run_id'].startswith('SOL_MEDIUM_BLIND_')
            or len({root, runtime, journal}) != 3
            or any(a.is_relative_to(b) for a in (root, runtime, journal) for b in (root, runtime, journal) if a != b)):
        raise ValueError('medium_fresh_distinct_scope_required')
    bound = binding.verify()
    if bound['owner_sha256'] != scope['packet_sha256'] or binding.scope_sha256 != scope['scope_sha256']:
        raise ValueError('medium_source_scope_pin')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=worktree, text=True).strip()
    head = git('rev-parse', 'HEAD')
    if git('status', '--porcelain'):
        raise ValueError('medium_worktree_drift')
    auth_path = plain(root/'USER_AUTHORIZATION.json')
    if auth_path.stat().st_mode & 0o222:
        raise ValueError('medium_approval_not_frozen')
    auth = json.loads(auth_path.read_bytes())
    validate_authorization(auth, scope, head)
    freeze = json.loads((root/'OFFLINE_FREEZE.json').read_bytes())
    if freeze['head'] != head or freeze['scope_sha256'] != digest(scope):
        raise ValueError('medium_freeze_drift')
    for relative, expected in freeze['code_pins'].items():
        if digest(plain(worktree/relative).read_bytes()) != expected:
            raise ValueError('medium_code_pin_drift')
    if not freeze['offline_checks_passed']:
        raise ValueError('medium_offline_checks_required')
    require_fresh(root, runtime, journal)
    install_boundary(root, runtime, journal)
    free = int(subprocess.check_output(['/bin/df', '-k', str(root)], text=True).splitlines()[-1].split()[3])*1024
    if free < 2*1024**3+256*1024**2:
        raise ValueError('medium_disk_guard')
    write_once(root/'PRE_GC-live.json', dict(free_bytes=free, peak_bytes=256*1024**2,
        reserve_bytes=2*1024**3, decision='PRE_GC_NOOP_SUFFICIENT', actions=[]))
    write_once(root/'EXECUTION_STARTED.json', dict(task=MEDIUM_TASK, run_id=scope['run_id'], head=head,
        approval_sha256=digest(auth), scope_sha256=digest(scope), at=datetime.now(timezone.utc).isoformat()), 0o400)
    out = root/'private/live'
    out.mkdir(mode=0o700)
    result = dict(status='PREMODEL_INITIALIZATION', accepted_BLIND=False, maximum_contexts=1,
        ADJ=0, retries=0, financial_HTTP=0, operating_DB=0, send=False, strict_ready=0,
        two_stage_owner=False, final_NO_SEND_message=False)
    counts = None
    try:
        packet_path = plain(scope['packet_path'])
        packet = json.loads(packet_path.read_bytes())
        if digest(packet) != scope['packet_sha256']:
            raise ValueError('medium_packet_changed')
        view, counts = restore_view(packet=packet, **scope['source'])
        registry = UseRegistry()
        ticker = packet['base']['public_security']['ticker']
        def economic_loader():
            base = view.packet(ticker)
            base['numeric_catalog'] = numeric_catalog(base)
            return attach(base)
        def source_loader():
            if json.loads(packet_path.read_bytes()) != packet:
                raise ValueError('medium_packet_drift')
            return engine.build_bundle(economic_loader(), registry=registry,
                contract=engine.AI_OWNED_V3, valuation_analysis_owner=view)
        if source_loader() != packet:
            raise ValueError('medium_original_source_owner_mismatch')
        write_once(out/'SOURCE_BOUND.json', dict(packet_sha256=digest(packet), dated_only=True,
            view_type=type(view).__name__, new_financial_capture=0))
        rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm=,args='], text=True).splitlines()
        others = []
        for row in rows:
            parts = row.strip().split(None, 2)
            if len(parts) != 3 or not parts[0].isdigit() or int(parts[0]) in (os.getpid(), os.getppid()):
                continue
            if (Path(parts[1]).name == 'codex' and ' exec ' in ' '+parts[2]+' ') or str(binding.binary) in parts[2]:
                others.append(int(parts[0]))
        write_once(out/'CALLERS.json', dict(other_analysis_PIDs=others, user_no_concurrency=True))
        if others:
            raise ValueError('medium_other_analysis_process_present')
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
                    raise ValueError('medium_lease_identity')
                fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
                yield
            finally:
                os.close(fd)
        latest, _ = target_session(packet['base']['public_security']['country'].lower(), datetime.now(timezone.utc))
        session = latest.isoformat() if hasattr(latest, 'isoformat') else str(latest)
        basis = json.loads(next(f['basis'] for f in packet['investment_valuation_context']['facts'] if f['metric'] == 'FPER'))
        prior_session = basis['price']['session']
        if prior_session >= session:
            raise ValueError('medium_dated_price_session')
        request = json.loads((root/'private/BLIND-request.json').read_bytes())
        if digest(request) != scope['request_sha256'] or request['stage'] != 'BLIND':
            raise ValueError('medium_fresh_blind_request_required')
        def approval(candidate):
            return (candidate == request and candidate['model'] == SOL_MEDIUM_V1.model
                and candidate['effort'] == SOL_MEDIUM_V1.effort
                and candidate['execution_profile'] == SOL_MEDIUM_V1.contract
                and digest(json.loads(auth_path.read_bytes())) == digest(auth)
                and not (runtime/'STOP').exists() and not (journal/'STOP').exists()
                and git('rev-parse', 'HEAD') == head)
        cap, host = run_stage(binding=binding, config=config, packet=packet, registry=registry,
            source_loader=source_loader, economic_loader=economic_loader, valuation_analysis_owner=view,
            request=request, knowledge='', approval=approval, account_lease=lease, session=session,
            prior_session=prior_session, out=out/'BLIND', enabled=True)
        result.update(status='SOL_MEDIUM_BLIND_ACCEPTED' if cap is not None else 'PARTIAL_BLIND_NOT_ACCEPTED',
                      accepted_BLIND=cap is not None, host_state=host['state'])
    except Exception as exc:
        result.update(status='BLOCKED_NO_RETRY', error_type=type(exc).__name__, reason=str(exc)[:1000])
        write_once(out/'FAILURE_PRIVATE.json', dict(type=type(exc).__name__, trace=traceback.format_exc(), retry=False))
    finally:
        result.update(stage_host_attempts=len(list(out.glob('*/MODEL_STARTED.json'))),
            returned_outputs=len(list(out.glob('*/MODEL_RAW.txt'))), parent_source_consumptions=counts,
            source_count_scope='Parent only; child source validations are not aggregated',
            private_DB_bytes=sum(p.stat().st_size for p in journal.glob('*') if p.is_file()) if journal.exists() else 0)
        write_once(root/'LIVE_RESULT.json', result)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] != ['--execute-once']:
        raise SystemExit('Explicit --execute-once and fresh frozen approval required')
    sys.dont_write_bytecode = True
    execute_once(Path(os.environ['TM_SOL_MEDIUM_TASK_ROOT']))
