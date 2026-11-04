"""Pinned deny-network launch for the original private Source worker.

The project owner approved bounded private Source-child memory custody for P2K.
This policy does not approve a live registration read or provider request.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

import httpx

from app.services.scoped_external_code_manifest import validate_external_manifest

CONTRACT = 'scoped-private-worker-seatbelt-v1'
CUSTODY_POLICY = 'trusted-private-source-child-memory-v1'
DUMMY = {'app_key': 'TEST_ONLY_DUMMY_APP', 'secret_key': 'TEST_ONLY_DUMMY_SECRET'}
ROOT = Path(__file__).resolve().parents[2]


def _plain(path):
    path = Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('scoped_launch_plain_path_required')
    return path


def prepare(bridge):
    from app.services.sealed_source_transport import SealedSourceTransport
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    from app.services.kiwoom_participant_session import ParticipatingSession
    session = bridge.source_session
    if (bridge.custody_policy != CUSTODY_POLICY or type(session) is not ParticipatingSession
            or session.kind != 'CLI' or session._lane is not bridge.transport.dispatcher._account_pacer):
        raise ValueError('scoped_source_parent_delegation_required')
    session.attestation()
    required_modules = {'app.services.current_scoped_worker_bridge','app.services.current_scoped_source_dispatch',
        'app.services.scoped_worker_launch','app.services.sealed_source_transport'}
    if not required_modules <= {m.__name__ for m in session._modules}:
        raise ValueError('scoped_source_parent_loaded_closure_required')
    if (type(bridge.transport) is not SealedSourceTransport
            or type(bridge.transport.inner) not in (httpx.MockTransport,httpx.AsyncHTTPTransport)
            or set(bridge.credentials or {}) != set(DUMMY)
            or any(not isinstance(v,str) or not v or v not in bridge.transport.dispatcher.secrets
                for v in bridge.credentials.values())):
        raise ValueError('scoped_source_credential_transport_binding_required')
    test_only = type(bridge.transport.inner) is httpx.MockTransport
    if test_only and bridge.credentials != DUMMY:
        raise ValueError('scoped_mock_real_credentials_forbidden')
    if type(bridge.transport.dispatcher._account_pacer) is not GlobalKiwoomLane:
        raise ValueError('scoped_launch_original_parent_global_lane_required')
    if sys.platform != 'darwin':
        raise ValueError('scoped_supported_os_launcher_required')
    frozen = _plain(bridge.frozen)
    raw = frozen.read_bytes()
    if hashlib.sha256(raw).hexdigest() != bridge.sha:
        raise ValueError('scoped_launch_frozen_changed')
    env = json.loads(raw)
    output = _plain(bridge.output)
    if (not output.is_dir() or output.stat().st_uid != os.getuid()
            or output.stat().st_mode & 0o077 or frozen.is_relative_to(output)
            or Path(env['stage']) != ROOT or Path(env['output']) != output):
        raise ValueError('scoped_launch_private_scratch_required')
    pins = env['external_pins']
    validate_external_manifest(pins, env.get('external_code_contract'))
    external = _plain(env['external_root'])
    reads = {}
    directories = {ROOT}
    for name in env['read_paths']:
        p = _plain(name)
        local = p.is_relative_to(ROOT) and p.relative_to(ROOT).parts[0] in {'app', 'scripts'}
        rel = str(p.relative_to(external)) if p.is_relative_to(external) else None
        if p.suffix != '.py' or not p.is_file() or not (local or rel in pins):
            raise ValueError('scoped_launch_code_only_closure_required')
        data = p.read_bytes()
        record = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if rel is not None and record != pins[rel]:
            raise ValueError('scoped_launch_external_pin_changed')
        reads[str(p)] = record
        if local:
            directories.update(x for x in p.parents if x == ROOT or x.is_relative_to(ROOT))
    if not {str(external/n) for n in pins} <= set(reads):
        raise ValueError('scoped_launch_external_closure_missing')
    worker = ROOT/'scripts/current_scoped_source_worker.py'
    if Path(bridge.worker) != worker or str(worker) not in reads:
        raise ValueError('scoped_launch_original_worker_required')
    python = Path(sys.executable)
    actual = python.resolve(strict=True)
    framework = actual.parents[1]
    executable = framework/'Resources/Python.app/Contents/MacOS/Python'
    if not executable.is_file() or '/Frameworks/Python.framework/Versions/' not in str(framework):
        raise ValueError('scoped_python_framework_layout_unverified')
    runtime = framework.parents[2]
    site = Path(sys.prefix)/f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
    roots = [runtime, site, Path('/usr/lib'), Path('/System/Library'),
        Path('/usr/share/zoneinfo'), Path('/usr/share/zoneinfo').resolve(strict=True),
        Path('/usr/share/locale')]
    roots += [Path('/opt/homebrew/Cellar')/n for n in ('gettext','openssl@3','sqlite','xz','mpdecimal')]
    q = lambda p: json.dumps(str(p))
    lines = ['(version 1)', '(deny default)', '(allow process-info*)', '(allow sysctl-read)',
        '(allow file-read-metadata)', '(allow signal (target self))', '(deny network*)',
        '(allow file-read-data (literal "/"))']
    lines += ['(allow file-read* (subpath '+q(p)+'))' for p in roots]
    files = [*map(Path, reads), frozen, python, actual, Path(sys.prefix)/'pyvenv.cfg',
        Path('/private/etc/localtime'), Path('/etc/localtime'), Path('/dev/null'), Path('/dev/urandom')]
    lines += ['(allow file-read* (literal '+q(p)+'))' for p in files]
    lines += ['(allow file-read-data (literal '+q(p)+'))' for p in sorted(directories)]
    lines += ['(allow process-exec (literal '+q(p)+'))' for p in (actual, executable)]
    lines += ['(allow file-read* file-write* (subpath '+q(output)+'))',
        '(allow file-write* (literal "/dev/null"))']
    profile = '\n'.join(lines)+'\n'
    return dict(contract=CONTRACT, policy_sha256=hashlib.sha256(profile.encode()).hexdigest(),
        profile=profile, code_pins=reads, uid=os.getuid(), test_only=test_only,
        credential_policy=CUSTODY_POLICY, physical_lane='ORIGINAL_PARENT_ONLY',
        executable=str(actual), framework_executable=str(executable),
        argv=['/usr/bin/sandbox-exec','-p',profile,str(python),'-I','-S','-B',str(worker),str(frozen),bridge.sha],
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C'}, cwd=str(output), close_fds=True)
