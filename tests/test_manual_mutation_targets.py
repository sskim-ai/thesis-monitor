"""Filesystem ownership proof, without touching actual production paths."""
import os
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import qualified_official_launch_context as q


def test_verified_anonymous_pipe_write_open(targets):
    guard, _, _, _, _ = targets
    reader, writer = os.pipe()
    try:
        guard('open', (writer, 'w', os.O_WRONLY))
        receipt = guard.receipts[-1]
        assert receipt['reason'] == 'VERIFIED_ANONYMOUS_PIPE_OPEN'
        assert receipt['targets'][0]['path_kind'] == 'ANONYMOUS_PIPE_DESCRIPTOR'
        assert receipt['resolution_confidence'] == 'VERIFIED_ANONYMOUS_IPC_IDENTITY'
        assert 'canonical_target' not in receipt['targets'][0]
        for event, args in [('os.truncate', (writer, 0)), ('os.chmod', (writer, 0o600, -1)),
                ('os.chown', (writer, os.getuid(), os.getgid(), -1)),
                ('os.remove', ('item', writer))]:
            with pytest.raises(q.LaunchQualificationError):
                guard(event, args)
    finally:
        os.close(reader)
        os.close(writer)


@pytest.mark.parametrize('unlinked', [False, True])
def test_named_fifo_is_not_anonymous_ipc(targets, unlinked):
    guard, protected, _, _, _ = targets
    fifo = protected / 'fifo'
    os.mkfifo(fifo)
    fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
    try:
        if unlinked:
            fifo.unlink()
        with pytest.raises(q.LaunchQualificationError):
            guard('open', (fd, 'w', os.O_WRONLY))
    finally:
        os.close(fd)


def test_pipe_unknown_authority_denies(targets, monkeypatch):
    guard, _, _, _, _ = targets
    reader, writer = os.pipe()
    def unavailable(fd):
        raise OSError('kernel authority unavailable')
    monkeypatch.setattr(q, '_anonymous_pipe_authority', unavailable)
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('open', (writer, 'w', os.O_WRONLY))
        assert guard.receipts[-1]['decision'] == 'DENY'
    finally:
        os.close(reader)
        os.close(writer)


def test_pipe_descriptor_reuse_denies(targets, monkeypatch):
    guard, protected, _, _, _ = targets
    reader, writer = os.pipe()
    file_fd = os.open(protected / 'item', os.O_RDWR)
    authority = q._anonymous_pipe_authority
    def swap_original(fd):
        value = authority(fd)
        os.dup2(file_fd, writer)
        return value
    monkeypatch.setattr(q, '_anonymous_pipe_authority', swap_original)
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('open', (writer, 'w', os.O_WRONLY))
        assert guard.receipts[-1]['resolution_error'] == 'FD_REUSE_MISMATCH'
        assert (protected / 'item').read_text() == 'preserve'
    finally:
        for fd in (reader, writer, file_fd):
            os.close(fd)


def test_actual_subprocess_stdin_under_installed_guard(tmp_path):
    code = r'''
import json, subprocess, sys
from pathlib import Path
from scripts.qualified_official_launch_context import ManualMutationGuard
root = Path(sys.argv[1]); protected = root / 'protected'; protected.mkdir()
guard = ManualMutationGuard([protected, Path.cwd()])
sys.addaudithook(guard)
payload = b'exact synthetic stdin\x00bytes\n'
with (root/'events').open('xb') as events, (root/'errors').open('xb') as errors:
    result = subprocess.run([sys.executable, '-B', '-c',
        'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
        input=payload, stdout=events, stderr=errors, cwd=root, timeout=10, check=False)
assert result.returncode == 0
assert (root/'events').read_bytes() == payload
assert (root/'errors').read_bytes() == b''
assert guard.blocked_attempts == 0
assert any(r['reason'] == 'VERIFIED_ANONYMOUS_PIPE_OPEN' for r in guard.receipts)
print(json.dumps({'status': 'PASS', 'receipts': guard.receipts}))
'''
    result = subprocess.run([sys.executable, '-B', '-c', code, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'PASS'


@pytest.fixture
def targets(tmp_path, monkeypatch):
    protected = tmp_path / 'protected'
    operating = tmp_path / 'operating'
    local = tmp_path / 'local'
    for root in (protected, operating, local):
        (root / 'nested').mkdir(parents=True)
        (root / 'item').write_text('preserve')
    monkeypatch.chdir(protected)
    guard = q.ManualMutationGuard([protected, operating])
    fds = [os.open(root, os.O_RDONLY | os.O_DIRECTORY) for root in (protected, operating, local)]
    try:
        yield guard, protected, operating, local, fds
    finally:
        for fd in fds:
            os.close(fd)


@pytest.mark.parametrize('event,shape', [
    ('os.remove', lambda path, fd: (path, fd)),
    ('os.rmdir', lambda path, fd: (path, fd)),
    ('os.mkdir', lambda path, fd: (path, 0o700, fd)),
    ('os.chmod', lambda path, fd: (path, 0o600, fd)),
    ('os.chown', lambda path, fd: (path, os.getuid(), os.getgid(), fd)),
])
def test_single_dir_fd_matrix(targets, event, shape):
    guard, protected, operating, local, fds = targets
    guard(event, shape('item', fds[2]))
    assert guard.receipts[-1]['targets'][0]['canonical_target'] == str(local / 'item')
    assert guard.receipts[-1]['targets'][0]['fd_identity']['identity'][:2] == list(
        (os.fstat(fds[2]).st_dev, os.fstat(fds[2]).st_ino))
    for fd in fds[:2]:
        with pytest.raises(q.LaunchQualificationError):
            guard(event, shape('nested/../item', fd))
    assert (protected / 'item').read_text() == (operating / 'item').read_text() == 'preserve'


@pytest.mark.parametrize('event', ['os.rename', 'os.link'])
@pytest.mark.parametrize('src_index,dst_index,blocked', [(2,2,False),(0,2,True),(2,0,True),(1,2,True),(2,1,True)])
def test_both_endpoint_fd_ownership(targets, event, src_index, dst_index, blocked):
    guard, _, _, local, fds = targets
    args = ('item', 'copy', fds[src_index], fds[dst_index])
    if blocked:
        with pytest.raises(q.LaunchQualificationError):
            guard(event, args)
    else:
        guard(event, args)
        assert {row['canonical_target'] for row in guard.receipts[-1]['targets']} == {
            str(local/'item'), str(local/'copy')}


def test_nested_and_normalized_directory_fd(targets):
    guard, _, _, local, fds = targets
    fd = os.open(local/'nested', os.O_RDONLY | os.O_DIRECTORY)
    try:
        guard('os.remove', ('.././nested//future', fd))
        assert guard.receipts[-1]['targets'][0]['canonical_target'] == str(local/'nested/future')
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', ('../protected/item', fds[2]))
    finally:
        os.close(fd)


def test_absolute_path_keeps_absolute_semantics_with_invalid_dir_fd(targets):
    guard, protected, _, local, _ = targets
    guard('os.remove', (local/'item', 999999))
    assert guard.receipts[-1]['targets'][0]['absolute_path_ignores_dir_fd']
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', (protected/'item', 999999))


def test_relative_without_fd_uses_cwd(targets, monkeypatch):
    guard, _, _, local, _ = targets
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', ('item', -1))
    monkeypatch.chdir(local)
    guard('os.remove', ('item', -1))
    assert guard.receipts[-1]['targets'][0]['anchor'] == str(local)


def test_closed_non_directory_unknown_and_deleted_fds_fail_closed(targets):
    guard, _, _, local, _ = targets
    closed = os.open(local, os.O_RDONLY)
    os.close(closed)
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', ('item', closed))
    fd = os.open(local/'item', os.O_RDONLY)
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', ('child', fd))
    finally:
        os.close(fd)
    for value in (999999, 'fd-from-caller-hint', -200):
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', ('item', value))
    gone = local/'gone'
    gone.mkdir()
    fd = os.open(gone, os.O_RDONLY)
    gone.rmdir()
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', ('item', fd))
    finally:
        os.close(fd)


def test_reused_fd_does_not_retain_old_temp_authority(targets):
    guard, _, _, _, fds = targets
    fd = os.dup(fds[2])
    try:
        guard('os.remove', ('item', fd))
        os.dup2(fds[0], fd)
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', ('item', fd))
        assert guard.receipts[-1]['reason'] == 'PROTECTED_ROOT'
    finally:
        os.close(fd)


def test_fd_reuse_during_resolution_denies(targets, monkeypatch):
    guard, _, _, _, fds = targets
    old = q._descriptor_path
    fd = os.dup(fds[2])
    def race(pinned):
        path = old(pinned)
        os.dup2(fds[0], fd)
        return path
    monkeypatch.setattr(q, '_descriptor_path', race)
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', ('item', fd))
        assert guard.receipts[-1]['resolution_error'] == 'FD_REUSE_MISMATCH'
    finally:
        os.close(fd)


def test_wrong_fd_path_identity_denies(targets, monkeypatch):
    guard, protected, _, _, fds = targets
    monkeypatch.setattr(q, '_descriptor_path', lambda _: protected)
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', ('item', fds[2]))
    assert guard.receipts[-1]['resolution_error'] == 'FD_PATH_IDENTITY_MISMATCH'


def test_dangling_symlink_and_cycle_semantics(targets):
    guard, protected, _, local, fds = targets
    (local/'dangling').symlink_to('absent')
    guard('os.remove', ('dangling', fds[2]))
    assert guard.receipts[-1]['targets'][0]['canonical_target'] == str(local/'absent')
    (local/'protected-dangling').symlink_to(protected/'absent')
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', ('protected-dangling', fds[2]))
    (local/'loop-a').symlink_to('loop-b')
    (local/'loop-b').symlink_to('loop-a')
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', ('loop-a', fds[2]))


def test_non_filesystem_fd_rejected(targets):
    guard, *_ = targets
    read, write = os.pipe()
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('os.truncate', (write,0))
    finally:
        os.close(read)
        os.close(write)


def test_recursive_creation_projects_from_verified_ancestor(targets):
    guard, protected, _, local, fds = targets
    guard('os.mkdir', ('new/deep/tree',0o700,fds[2]))
    target = guard.receipts[-1]['targets'][0]
    assert target['canonical_target'] == str(local/'new/deep/tree')
    assert target['existing_ancestor']['path'] == str(local)
    assert target['resolution_confidence'] == 'VERIFIED_ANCESTOR_TARGET_PROJECTION'
    with pytest.raises(q.LaunchQualificationError):
        guard('os.mkdir', (protected/'new/deep/tree',0o700,-1))


def test_case_alias_of_protected_directory_is_not_new_authority(targets):
    guard, protected, _, _, _ = targets
    alias = protected.with_name(protected.name.upper())
    if not alias.exists():
        pytest.skip('Filesystem is case-sensitive')
    assert q._file_identity(alias.stat()) == q._file_identity(protected.stat())
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', (alias/'item',-1))
    fd = os.open(alias,os.O_RDONLY|os.O_DIRECTORY)
    try:
        with pytest.raises(q.LaunchQualificationError):
            guard('os.mkdir', ('new/deep',0o700,fd))
    finally:
        os.close(fd)


def test_protected_file_identity_alias_is_denied(tmp_path):
    source=tmp_path/'source'
    source.write_text('preserve')
    alias=tmp_path/'alias'
    os.link(source,alias)
    guard=q.ManualMutationGuard([source])
    with pytest.raises(q.LaunchQualificationError):
        guard('os.truncate',(alias,0))


def test_symlink_entry_referent_and_traversal_are_protected(targets):
    guard, protected, _, local, fds = targets
    (local/'escape').symlink_to(protected, target_is_directory=True)
    (protected/'out').symlink_to(local, target_is_directory=True)
    for path in ('escape/item','../protected/item'):
        with pytest.raises(q.LaunchQualificationError):
            guard('os.remove', (path, fds[2]))
    with pytest.raises(q.LaunchQualificationError):
        guard('os.remove', (protected/'out/item', -1))
    with pytest.raises(q.LaunchQualificationError):
        guard('os.symlink', ('../protected/item','link',fds[2]))
    guard('os.symlink', ('item','link',fds[2]))
    assert guard.receipts[-1]['targets'][1]['canonical_target'] == str(local/'item')


@pytest.mark.parametrize('event,shape', [
    ('os.truncate', lambda fd: (fd,0)),
    ('os.chmod', lambda fd: (fd,0o600,-1)),
    ('os.chown', lambda fd: (fd,os.getuid(),os.getgid(),-1)),
    ('open', lambda fd: (fd,'w',os.O_WRONLY)),
])
def test_direct_file_descriptor_ownership(targets, event, shape):
    guard, protected, _, local, _ = targets
    for path, blocked in ((protected/'item',True),(local/'item',False)):
        fd = os.open(path, os.O_RDONLY)
        try:
            if blocked:
                with pytest.raises(q.LaunchQualificationError):
                    guard(event, shape(fd))
            else:
                guard(event, shape(fd))
        finally:
            os.close(fd)


def test_unobservable_os_open_base_is_explicitly_denied(targets, monkeypatch):
    guard, _, _, local, _ = targets
    monkeypatch.chdir(local)
    with pytest.raises(q.LaunchQualificationError):
        guard('open', ('item',None,os.O_WRONLY))
    assert guard.receipts[-1]['resolution_error'] == 'OPEN_DIR_FD_NOT_OBSERVABLE'
    guard('open', ('item','w',os.O_WRONLY))
    guard('open', (local/'item',None,os.O_WRONLY))


@pytest.mark.parametrize('event,args', [('os.remove',(None,-1)),('os.remove',('',-1)),
    ('os.remove',('nul\0path',-1)),('os.remove',('item',)),
    ('sqlite3.connect',('file:protected?mode=rw',))])
def test_unknown_targets_deny_with_receipt(targets, event, args):
    guard, *_ = targets
    with pytest.raises(q.LaunchQualificationError):
        guard(event,args)
    assert guard.receipts[-1]['decision'] == 'DENY'
    assert guard.receipts[-1]['resolution_confidence'] == 'UNRESOLVED'
    assert guard.receipts[-1]['raw_arguments']


def test_actual_audit_hook_nested_cleanup_and_real_primitives(tmp_path):
    code = r'''
import json, os, sys
from pathlib import Path
from tempfile import TemporaryDirectory
from scripts.qualified_official_launch_context import ManualMutationGuard, LaunchQualificationError
base=Path(sys.argv[1]); protected=base/'protected'; protected.mkdir()
(protected/'item').write_text('preserve')
os.chdir(protected)
guard=ManualMutationGuard([protected]); sys.addaudithook(guard)
with TemporaryDirectory(dir=base) as name:
    root=Path(name); (root/'nested').mkdir(); (root/'nested/a').write_text('a')
    fd=os.open(root/'nested',os.O_RDONLY|os.O_DIRECTORY)
    pfd=os.open(protected,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.rename('a','b',src_dir_fd=fd,dst_dir_fd=fd)
        os.replace('b','c',src_dir_fd=fd,dst_dir_fd=fd)
        os.link('c','d',src_dir_fd=fd,dst_dir_fd=fd)
        os.symlink('c','e',dir_fd=fd)
        os.mkdir('new',dir_fd=fd); os.rmdir('new',dir_fd=fd)
        for fn in (lambda:os.unlink('item',dir_fd=pfd),
                   lambda:os.rename('c','bad',src_dir_fd=fd,dst_dir_fd=pfd)):
            try: fn()
            except LaunchQualificationError: pass
            else: raise AssertionError('protected write allowed')
    finally:
        os.close(fd); os.close(pfd)
assert not root.exists() and (protected/'item').read_text()=='preserve'
clean=[r for r in guard.receipts if r['operation'] in ('os.remove','os.rmdir') and r['decision']=='ALLOW']
assert clean and all(all(Path(t['canonical_entry']).is_relative_to(root) for t in r['targets']) for r in clean)
assert all(not t['protected_roots'] for r in guard.receipts if r['decision']=='ALLOW' for t in r['targets'])
print(json.dumps(dict(status='PASS',receipts=len(guard.receipts),cleanup_events=len(clean),blocked=guard.blocked_attempts)))
'''
    import json
    result = subprocess.run([sys.executable,'-B','-c',code,str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],text=True,capture_output=True,timeout=60)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['blocked'] == 2
