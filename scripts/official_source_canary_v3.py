"""Default-off v3 entry to the ORIGINAL registered Source runtime. No daemon.

Release pins are built once. Runtime checks the core and checks all application
imports on use. A canary needs one fresh execution-plan-specific terminal grant.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'official-manual-scoped-source-parent-v3'
CORE = (
    'scripts/official_source_canary_v3.py', 'scripts/official_scoped_source_parent.py',
    'scripts/official_source_cold.py', 'scripts/current_scoped_source_worker.py',
    'app/services/source_parent_canary_v3.py', 'app/services/official_registered_source_runtime.py',
    'app/services/minimal_class_c_export.py', 'app/services/prospective_class_c_owner.py',
    'app/services/current_class_c_source_bridge.py', 'app/services/manual_scoped_source_runtime.py',
    'app/services/kiwoom_global_lane.py', 'app/services/kiwoom_participant_session.py',
    'app/services/runtime_maintenance.py', 'app/services/scoped_worker_launch.py',
    'app/services/current_scoped_worker_bridge.py', 'app/services/current_scoped_source_dispatch.py',
    'app/services/current_scoped_source_owner.py', 'app/services/current_scoped_source_results.py',
    'app/services/sealed_source_transport.py', 'app/services/scoped_source_plan.py',
    'app/services/production_source_context.py', 'scripts/r9_rev11_live.py',
)


def require(value, code):
    if not value:
        raise ValueError('official_v3_'+code)


def plain(value):
    p = Path(value)
    require(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)), 'plain_path')
    return p


def pin(path):
    raw = plain(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def validate_manifest(path, expected, *, candidate=False):
    path = plain(path)
    if candidate:
        require(path.parent == ROOT/'ops/source-parent-candidates', 'candidate_manifest_location')
    else:
        require(path == ROOT/'ops/manual-source-parent-v3.json', 'manifest_location')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected, 'manifest_sha256')
    m = json.loads(raw)
    if candidate:
        require(m['candidate_state']=='CODE_REVIEWED_NOT_INSTALLED'
            and m['base_manifest_sha256']==pin(ROOT/'ops/manual-source-parent-v3.json')['sha256'], 'candidate_base_binding')
    require(m['contract']==CONTRACT and m['worktree']==str(ROOT), 'manifest_contract')
    require(m['default_enabled'] is False and m['owner_approved'] is False
            and m['delivery']=='NO_SEND' and m['purpose']=='MANUAL_SHADOW_UNSENT', 'default_off_no_send')
    require(m['environment']=={'KIWOOM_GLOBAL_LANE_REQUIRED':'1'}, 'environment')
    require(tuple(m['core'])==CORE and m['import_policy']=='PINNED_SOURCE_ON_USE_V1', 'release_core')
    require(m['database_policy']=='TRUSTED_ORIGINAL_SQLITE_READONLY_V3', 'database_policy')
    require(m['runtime']['python_version']==sys.version and m['runtime']['platform']==sys.platform,
            'runtime_version')
    require(Path(sys.executable)==Path(m['interpreter'])
            and pin(Path(sys.executable).resolve())==m['interpreter_pin'], 'interpreter')
    for name in CORE:
        require(pin(ROOT/name)==m['source_pins'][name], 'core_changed')
    # No all-source disk loop here: the original loader checks lazy imports.
    loader_path = ROOT/'scripts/official_scoped_source_parent.py'
    raw = loader_path.read_bytes()
    require(dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())==m['source_pins']['scripts/official_scoped_source_parent.py'],
            'loader_race')
    scope = {'__file__':str(loader_path),'__name__':'official_v3_pinned_original_cli'}
    exec(compile(raw,str(loader_path),'exec',dont_inherit=True),scope)
    from types import SimpleNamespace
    cli = SimpleNamespace(**scope)
    require(tuple(m['modules'])==cli.MODULES, 'original_modules')
    return m,cli


def execution_plan(path, expected, invocation):
    path=plain(path)
    require(path.stat().st_size<=16384, 'plan_size')
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected, 'plan_sha256')
    c=json.loads(raw)
    keys={'invocation_id','markets','database','settings_file','output_root','external_root',
          'external_code_contract','external_head','instruction_sha1'}
    require(set(c)==keys and c['invocation_id']==invocation, 'execution_plan_scope')
    require(c['markets'] in (['kr'],['kr','us']), 'execution_markets')
    for key in ('database','settings_file','output_root','external_root'):
        plain(c[key])
    require(re.fullmatch('[0-9a-f]{40}',c['instruction_sha1']) is not None, 'instruction_identity')
    require(Path(c['output_root']).parent.is_dir() and not Path(c['output_root']).exists(), 'fresh_output')
    c['execution_plan_sha256']=expected
    return c


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=ROOT/'ops/manual-source-parent-v3.json')
    p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--invocation-id',required=True)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--preflight',action='store_true')
    g.add_argument('--canary',action='store_true')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--plan',type=Path)
    p.add_argument('--plan-sha256')
    p.add_argument('--receipt',type=Path)
    a=p.parse_args(argv)
    report=dict(contract=CONTRACT,status='BLOCKED_BEFORE_ADMISSION',financial_calls=0,
        database_sessions=0,models=0,slot_calls=0,worker_launched=False)
    cli=guard=None
    try:
        require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{7,79}',a.invocation_id) is not None, 'invocation')
        m,cli=validate_manifest(a.manifest,a.manifest_sha256)
        report.update(invocation_id=a.invocation_id,manifest_sha256=a.manifest_sha256,
            release_core_files=len(CORE),full_pins_checked_on_import=True,default_enabled=False)
        receipt=cli.receipt_destination(m,a.invocation_id,a.receipt)
        if receipt:report['receipt_path']=str(receipt)
        c=execution_plan(a.plan,a.plan_sha256,a.invocation_id) if a.canary else None
        if a.dry_run:
            report['status']='REVIEW_ONLY_NO_APP_IMPORT_OR_OPTIN'
            return report,0
        require(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize==0, 'isolated_python')
        if not a.canary:
            guard=cli.ReadOnlyPreflight(m['lane_root'],receipt)
            sys.addaudithook(guard)
        else:
            require(receipt is not None, 'fresh_receipt_required')
            require(sys.stdin.isatty() and sys.stdout.isatty(), 'owner_terminal_required')
        cli.bootstrap(m)
        from app.services import source_parent_canary_v3 as v3
        if a.canary:
            import asyncio
            scope=v3.CanaryScope(markets=tuple(c['markets']),us_http=12 if 'us' in c['markets'] else 0)
            report.update(asyncio.run(cli.run_canary(m,c,a.manifest_sha256,a.invocation_id,report,v3_scope=scope)))
        else:
            session,proof=v3.admit_parent(m,cli)
            session.close_admission()
            report.update(proof,status='NORMAL_HOST_PARENT_ADMITTED_NO_IO',parent_closed=True,
                owner_approved=False,preflight_is_not_grant=True)
        return report,0
    except BaseException as exc:
        message=str(exc)
        report.update(status='HOST_GATE_PENDING',error=(message if re.fullmatch(
            '(official_|global_lane_|participant_|maintenance_)[A-Za-z0-9_:-]{1,160}',message) else type(exc).__name__),
            exception_type=type(exc).__name__)
        if message=='global_lane_boot_identity_unavailable':
            import ctypes
            report['boot_errno']=ctypes.get_errno()
        if guard is not None:report['audit_denials']=guard.denials
        return report,2


if __name__=='__main__':
    report,rc=main()
    if report.get('receipt_path'):
        import os
        fd=os.open(report['receipt_path'],os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as f:
            json.dump(report,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(report,sort_keys=True))
    raise SystemExit(rc)
