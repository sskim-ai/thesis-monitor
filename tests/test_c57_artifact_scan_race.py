"""Deterministic CLI-state races using real temporary files; no live calls."""
import errno
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from app.services.codex_runtime_state_service import runtime_state_namespace_hash
from app.services import research_artifact_budget as storage


@pytest.fixture
def layout(tmp_path):
    runtime, source, result = (tmp_path / name for name in ('runtime', 'source', 'result'))
    for root in (runtime, source, result):
        root.mkdir()
    attempt = runtime / 'offline-attempt'
    state = attempt / 'runtime-state' / runtime_state_namespace_hash(attempt.name)
    transient = state / 'home' / 'tmp' / 'transient'
    transient.mkdir(parents=True)
    (transient / 'discarded.bin').write_bytes(b'discarded')
    retained = attempt / 'events.jsonl'
    retained.write_bytes(b'retained')
    budget = storage.ResearchArtifactBudget(roots={runtime: 'scratch', source: 'source', result: 'result'})
    budget.declare_cli_context(attempt)
    return SimpleNamespace(runtime=runtime, source=source, result=result, attempt=attempt, state=state,
        transient=transient, retained=retained, budget=budget)


def remove_before_listing(monkeypatch, target):
    original = Path.iterdir
    removed = []

    def iterdir(path):
        if path == target and not removed:
            shutil.rmtree(path)
            removed.append(path)
        return original(path)

    monkeypatch.setattr(Path, 'iterdir', iterdir)
    return removed


def assert_scan_failure(exc, *, operation, category, relative, error_type, error_number):
    assert isinstance(exc, OSError)
    assert exc.receipt == dict(code='RESEARCH_ARTIFACT_SCAN_FAILED', stage='A', operation=operation,
        path_category=category, relative_path=relative, error_type=error_type, errno=error_number)
    assert not Path(exc.receipt['relative_path']).is_absolute()
    assert len(exc.receipt['relative_path']) <= 512


def test_registered_state_directory_disappears_between_stat_and_listing(layout, monkeypatch):
    removed = remove_before_listing(monkeypatch, layout.transient)
    totals = layout.budget.measure()
    assert removed == [layout.transient]
    assert totals['scratch'] == totals['total'] == len(b'retained')
    assert totals['unique_files'] == 1 and totals['source'] == totals['result'] == 0
    assert layout.retained.read_bytes() == b'retained'


@pytest.mark.parametrize('protected', [
    'unregistered-scratch', 'source', 'result', 'declared-runtime-root', 'declared-state-root',
    'source-override', 'result-override', 'declared-result-child',
])
def test_disappearance_outside_disposable_state_remains_fatal(layout, monkeypatch, protected):
    budget, target, category, declared_root = layout.budget, layout.transient, 'scratch', layout.runtime
    if protected == 'unregistered-scratch':
        target = layout.runtime / 'unregistered-cache'
        target.mkdir()
    elif protected in {'source', 'result'}:
        declared_root = getattr(layout, protected)
        target = declared_root / 'protected'
        target.mkdir()
        category = protected
    elif protected == 'declared-runtime-root':
        target = layout.runtime
    elif protected == 'declared-state-root':
        target = declared_root = layout.state
        budget = storage.ResearchArtifactBudget(roots={**budget.roots, target: 'scratch'})
        budget.declare_cli_context(layout.attempt)
    elif protected.endswith('-override'):
        category = protected.removesuffix('-override')
        budget.declare(target, category)
    elif protected == 'declared-result-child':
        budget.declare(target / 'discarded.bin', 'result')
    removed = remove_before_listing(monkeypatch, target)
    with storage.artifact_stage('A'), pytest.raises(storage.ArtifactScanError) as failure:
        budget.measure()
    assert removed == [target]
    assert_scan_failure(failure.value, operation='iterdir', category=category,
        relative=str(target.relative_to(declared_root)), error_type='FileNotFoundError', error_number=errno.ENOENT)


@pytest.mark.parametrize('error_number,error_type', [
    (errno.ENOENT, 'FileNotFoundError'), (errno.EACCES, 'PermissionError'),
    (errno.ENOTDIR, 'NotADirectoryError'), (errno.EIO, 'OSError'),
])
def test_listing_errors_without_confirmed_disappearance_are_fatal(layout, monkeypatch, error_number, error_type):
    original = Path.iterdir

    def iterdir(path):
        if path == layout.transient:
            raise OSError(error_number, 'private diagnostic must not be exported', str(path))
        return original(path)

    monkeypatch.setattr(Path, 'iterdir', iterdir)
    with storage.artifact_stage('A'), pytest.raises(storage.ArtifactScanError) as failure:
        layout.budget.measure()
    assert layout.transient.is_dir()
    assert_scan_failure(failure.value, operation='iterdir', category='scratch',
        relative=str(layout.transient.relative_to(layout.runtime)), error_type=error_type, error_number=error_number)
    assert 'private diagnostic' not in str(failure.value.receipt)


@pytest.mark.parametrize('operation', ['lstat', 'readlink'])
def test_other_metadata_errors_remain_fatal(layout, tmp_path, monkeypatch, operation):
    if operation == 'lstat':
        target = layout.retained
        original = Path.lstat

        def lstat(path, *args, **kwargs):
            if path == target:
                raise OSError(errno.EIO, 'private detail', str(path))
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, 'lstat', lstat)
    else:
        target, _, _ = allowed_links(layout, tmp_path)
        original = os.readlink

        def readlink(path, *args, **kwargs):
            if Path(path) == target:
                raise OSError(errno.EIO, 'private detail', str(path))
            return original(path, *args, **kwargs)

        monkeypatch.setattr(os, 'readlink', readlink)
    with storage.artifact_stage('A'), pytest.raises(storage.ArtifactScanError) as failure:
        layout.budget.measure()
    assert_scan_failure(failure.value, operation=operation, category='scratch',
        relative=str(target.relative_to(layout.runtime)), error_type='OSError', error_number=errno.EIO)


def allowed_links(layout, tmp_path):
    auth = tmp_path / 'auth-reference'
    auth.write_bytes(b'offline fixture only')
    cli = tmp_path / 'qualified-cli'
    cli.write_bytes(b'not executable code')
    cli.chmod(0o700)
    home = layout.state / 'home'
    arg0 = home / 'tmp' / 'arg0-macos'
    arg0.mkdir(mode=0o700)
    helper = arg0 / 'codex-arg0Ab12Cd'
    helper.mkdir(mode=0o700)
    auth_link, helper_link = home / 'auth.json', helper / 'apply_patch'
    auth_link.symlink_to(auth)
    helper_link.symlink_to(cli)
    layout.budget.declare_cli_context(layout.attempt, auth, qualified_cli=cli)
    return auth_link, helper_link, helper


@pytest.mark.parametrize('kind', ['auth', 'arg0'])
def test_allowed_link_disappears_before_readlink(layout, tmp_path, monkeypatch, kind):
    auth_link, helper_link, _ = allowed_links(layout, tmp_path)
    target = auth_link if kind == 'auth' else helper_link
    removed_size = target.lstat().st_size
    before = layout.budget.measure()['total']
    original, removed = os.readlink, []

    def readlink(path, *args, **kwargs):
        if Path(path) == target and not removed:
            target.unlink()
            removed.append(target)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, 'readlink', readlink)
    assert layout.budget.measure()['total'] == before - removed_size
    assert removed == [target]
    assert layout.retained.read_bytes() == b'retained'


@pytest.mark.parametrize('which_parent', ['helper', 'arg0-root'])
def test_allowed_link_parent_disappears_during_validation(layout, tmp_path, monkeypatch, which_parent):
    _, link, helper = allowed_links(layout, tmp_path)
    parent = helper if which_parent == 'helper' else helper.parent
    removed_size = link.lstat().st_size
    before = layout.budget.measure()['total']
    original, armed, removed = Path.lstat, [], []

    def lstat(path, *args, **kwargs):
        if path == link:
            info = original(path, *args, **kwargs)
            armed.append(path)
            return info
        if path == parent and armed and not removed:
            shutil.rmtree(parent)
            removed.append(parent)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'lstat', lstat)
    assert layout.budget.measure()['total'] == before - removed_size
    assert removed == [parent] and not parent.exists()


@pytest.mark.parametrize('tamper', ['wrong-target', 'unknown-name', 'public-directory'])
def test_live_malformed_links_still_fail_validation(layout, tmp_path, tamper):
    auth_link, helper_link, helper = allowed_links(layout, tmp_path)
    if tamper == 'wrong-target':
        helper_link.unlink()
        helper_link.symlink_to(auth_link)
    elif tamper == 'unknown-name':
        helper_link.rename(helper / 'unregistered')
    else:
        helper.chmod(0o755)
    with pytest.raises(ValueError, match='research_artifact_unexpected_symlink'):
        layout.budget.measure()


@pytest.mark.parametrize('limited_role', ['source', 'result'])
def test_surviving_hardlinks_count_once_at_strongest_role_and_still_hit_caps(layout, monkeypatch, limited_role):
    layout.retained.write_bytes(b'x' * 101)
    os.link(layout.retained, getattr(layout, limited_role) / 'retained-link')
    limits = dict(work_cap=100, result_cap=100) if limited_role == 'source' else dict(work_cap=1000, result_cap=100)
    budget = storage.ResearchArtifactBudget(roots=layout.budget.roots, **limits)
    budget.declare_cli_context(layout.attempt)
    removed = remove_before_listing(monkeypatch, layout.transient)
    code = 'RESEARCH_WORK_CAP' if limited_role == 'source' else 'RESEARCH_RESULT_CAP'
    with pytest.raises(storage.ArtifactCapacityError, match=code):
        budget.check(path=layout.attempt)
    totals = budget.measure()
    assert removed == [layout.transient]
    assert totals['unique_files'] == 1 and totals['scratch'] == 0
    assert totals[limited_role] == totals['total'] == 101


def test_initially_missing_declared_roots_remain_valid(tmp_path):
    budget = storage.ResearchArtifactBudget(roots={tmp_path / 'runtime': 'scratch', tmp_path / 'results': 'result'})
    assert budget.measure()['total'] == 0


def test_scan_diagnostic_survives_first_failure_without_arbitrary_error_details(layout, monkeypatch):
    from app.services.research_no_send_run import _first_failure

    original = Path.iterdir

    def iterdir(path):
        if path == layout.transient:
            raise OSError(errno.EIO, 'must remain private', str(path))
        return original(path)

    monkeypatch.setattr(Path, 'iterdir', iterdir)
    with storage.artifact_stage('A'), pytest.raises(storage.ArtifactScanError) as failure:
        layout.budget.measure()
    first = _first_failure(failure.value, 'A')
    assert first['code'] == 'RESEARCH_ARTIFACT_SCAN_FAILED'
    assert first['artifact_scan'] == failure.value.receipt
    assert str(layout.runtime) not in str(first) and 'must remain private' not in str(first)
    forged = OSError(errno.EIO, 'must remain private')
    forged.receipt = failure.value.receipt
    assert 'artifact_scan' not in _first_failure(forged, 'A')


def test_scan_diagnostic_bounds_long_relative_paths(layout, monkeypatch):
    target = layout.transient
    for index in range(24):
        target = target / f'segment-{index:02d}-with-context'
    target.mkdir(parents=True)
    original = Path.iterdir

    def iterdir(path):
        if path == target:
            raise OSError(errno.EACCES, 'private message', str(path))
        return original(path)

    monkeypatch.setattr(Path, 'iterdir', iterdir)
    with storage.artifact_stage('A'), pytest.raises(storage.ArtifactScanError) as failure:
        layout.budget.measure()
    relative = failure.value.receipt['relative_path']
    assert 0 < len(relative) <= 512 and not Path(relative).is_absolute()
    assert str(layout.runtime) not in str(failure.value.receipt)
    assert 'private message' not in str(failure.value.receipt)


def test_unicode_scan_diagnostic_fits_and_persists_first_failure_limit(tmp_path):
    from app.services.research_no_send_run import _first_failure, _persist_first_failure

    with storage.artifact_stage('A'):
        failure = storage.ArtifactScanError(operation='iterdir', path_category='scratch',
            relative_path='\U0001f680' * 1024,
            error=FileNotFoundError(errno.ENOENT, 'private message', '/private/absolute/path'))
    state = dict(first_failure=_first_failure(failure, 'A'))
    _persist_first_failure(tmp_path, state)
    raw = (tmp_path / 'first-failure.json').read_bytes()
    assert state['first_failure_receipt']['status'] == 'PERSISTED'
    assert len(raw) <= 4096 and json.loads(raw) == state['first_failure']
    assert b'private message' not in raw and b'/private/absolute/path' not in raw
