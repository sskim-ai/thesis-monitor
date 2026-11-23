"""C31 auth-file metadata no longer grants or denies execution; temporary files only."""
from dataclasses import replace
import json
import os
from pathlib import Path
import socket
import sqlite3
from types import SimpleNamespace

import pytest

from app.services import codex_runtime_binding as binding
from app.services import codex_runtime_state_service as runtime
from app.services.official_codex_shadow_transport_service import OfficialShadowError, file_sha256
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.test_c22aq_runtime_parity import installed


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C31_NO_NETWORK_DB_OR_MODEL')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(sqlite3, 'connect', denied)
    monkeypatch.setattr('subprocess.Popen', denied)
    monkeypatch.setattr(runtime, '_sqlite_wal_write_probe', lambda path: None)


def test_inode_replacement_legacy_qualification_and_freeze_all_pass(installed, tmp_path):
    value, inspection, path = installed
    auth = Path(value.auth_source)
    inspection['auth_reference'].update(device=-1, inode=-1, uid=-1, mode='0o000')
    path.write_text(json.dumps(inspection))
    value = binding.freeze_current_binding(inspection_path=path, qualification_path=tmp_path/'new-review.json', profile=SOL_HIGH_V1)
    qualified = json.loads(value.qualification_path.read_bytes())
    qualified['auth_reference'].update(device=-1, inode=-1, uid=-1, mode='0o000')
    value.qualification_path.write_text(json.dumps(qualified))
    value = replace(value, qualification_sha256=file_sha256(value.qualification_path))
    old_inode = auth.stat().st_ino
    replacement = auth.with_suffix('.replacement'); replacement.write_bytes(b'{}'); replacement.chmod(0o600)
    replacement.replace(auth)
    assert auth.stat().st_ino != old_inode
    binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    assert binding.parent_environment(value)['HOME'] == value.home
    assert binding.auth_identity(auth) == dict(path=str(auth), exists=True, readable=True, content_read=False)
    with pytest.raises(OfficialShadowError, match='EXECUTABLE_DRIFT'):
        binding.validate_binding(replace(value, executable_sha256='0'*64), str(value.executable), profile=SOL_HIGH_V1)


def test_readable_foreign_owner_and_public_mode_do_not_deny(installed, tmp_path, monkeypatch):
    value, _, _ = installed
    auth = Path(value.auth_source); auth.chmod(0o644)
    original = Path.stat
    def metadata(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if path == auth:
            fields = list(result); fields[4] = os.getuid()+10000
            return os.stat_result(fields)
        return result
    monkeypatch.setattr(Path, 'stat', metadata)
    binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    state = runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='readable', auth_source=auth)
    assert (state.codex_home/'auth.json').resolve() == auth and state.mode == '0700'


def test_missing_auth_denies_binding_and_runtime(installed, tmp_path):
    value, _, _ = installed
    auth = Path(value.auth_source); auth.unlink()
    with pytest.raises(OfficialShadowError, match='AUTH_REFERENCE_MISSING'):
        binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    with pytest.raises(runtime.CodexRuntimeStateError, match='auth_reference_missing'):
        runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='missing', auth_source=auth)


def test_actual_open_failure_denies_even_if_access_says_yes(installed, tmp_path, monkeypatch):
    value, _, _ = installed
    auth = Path(value.auth_source); original = Path.open
    def denied_auth(path, *args, **kwargs):
        if path == auth:
            raise PermissionError('synthetic-unreadable')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', denied_auth)
    with pytest.raises(OfficialShadowError, match='AUTH_REFERENCE_UNREADABLE'):
        binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
    with pytest.raises(runtime.CodexRuntimeStateError, match='auth_reference_unreadable'):
        runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='unreadable', auth_source=auth)


def test_isolated_symlink_keeps_source_route_and_no_plaintext_copy(installed, tmp_path, monkeypatch):
    value, _, _ = installed
    environment = binding.invocation_environment(value, root=tmp_path/'runtime', namespace='isolated')
    home = Path(environment['CODEX_HOME']); reference = home/'auth.json'
    assert reference.is_symlink() and reference.resolve() == Path(value.auth_source)
    assert binding.auth_identity(reference) == binding.auth_identity(value.auth_source)
    reference.unlink(); reference.write_bytes(b'{}')
    with pytest.raises(runtime.CodexRuntimeStateError, match='plaintext_copy_forbidden'):
        runtime.prepare_codex_runtime_state(tmp_path/'runtime', namespace='isolated', auth_source=Path(value.auth_source))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path/'different-home'))
    with pytest.raises(OfficialShadowError):
        binding.validate_binding(value, str(value.executable), profile=SOL_HIGH_V1)
