"""Scoped accounting for prepared research; external CLI writes are not a quota."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import stat

RESULT_CAP = 96_000_000
WORK_CAP = 2 * 1024**3
FREE_GUARD = 12 * 1024**3
CLI_WORK_ALLOWANCE = 48 * 1024**2
MODEL_RESULT_ALLOWANCE = 2 * 128 * 1024 + 256 * 1024
CLI_RESULT_FILENAMES = ('raw-output.json', 'raw-output.json.invocation', 'transport-receipt.json',
    'production-authorization.json', 'parent-exit.json', 'runtime-cleanup.json')
_active = ContextVar('research_artifact_budget', default=None)
_role = ContextVar('research_artifact_role', default=None)
_stage = ContextVar('research_artifact_stage', default='PREPARE')


class ArtifactCapacityError(ValueError):
    def __init__(self, *, code, role, current, projected, cap):
        super().__init__(code)
        self.receipt = dict(code=code, stage=_stage.get(), path_category=role,
            measured_at=datetime.now(timezone.utc).isoformat(), current_bytes=current,
            projected_bytes=projected, cap_bytes=cap)


class ArtifactScanError(OSError):
    """A failed observation, with bounded metadata and no absolute paths or payloads."""

    def __init__(self, *, operation, path_category, relative_path, error):
        code = 'RESEARCH_ARTIFACT_SCAN_FAILED'
        super().__init__(error.errno, code)
        # Even astral Unicode escapes must fit the 4096-byte first-failure receipt.
        self.receipt = dict(code=code, stage=_stage.get(), operation=operation,
            path_category=path_category, relative_path=relative_path[:256],
            error_type=type(error).__name__, errno=error.errno)


def active_budget():
    return _active.get()


@contextmanager
def artifact_scope(budget):
    token = _active.set(budget)
    try:
        yield
    finally:
        _active.reset(token)


@contextmanager
def artifact_role(role):
    token = _role.set(role)
    try:
        yield
    finally:
        _role.reset(token)


@contextmanager
def artifact_stage(stage):
    token = _stage.set(stage)
    try:
        yield
    finally:
        _stage.reset(token)


def plain_path(path):
    path = Path(path).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('research_artifact_unsafe_path')
    return path


class ResearchArtifactBudget:
    """One sequential writer, measuring all declared roots including CLI scratch."""

    def __init__(self, *, roots, result_cap=RESULT_CAP, work_cap=WORK_CAP, free_guard=FREE_GUARD):
        self.roots = {plain_path(p): role for p, role in roots.items()}
        if (not self.roots or any(role not in {'result', 'source', 'scratch'} for role in self.roots.values())
                or not 0 < result_cap <= RESULT_CAP or not 0 < work_cap <= WORK_CAP or free_guard < FREE_GUARD):
            raise ValueError('research_artifact_invalid_limits_or_roots')
        self.result_cap, self.work_cap, self.free_guard = result_cap, work_cap, free_guard
        self.declared = {}
        self.auth_refs = {}
        self.cli_arg0_roots = {}
        self.cli_state_roots = set()
        self.peak_work = 0
        self.peak_result = 0

    def category(self, path):
        if path in self.declared:
            return self.declared[path]
        root = max((p for p in self.roots if path == p or path.is_relative_to(p)),
                   key=lambda p: len(p.parts), default=None)
        if root is None:
            raise ValueError('research_artifact_root_not_declared')
        return self.roots[root]

    def declare(self, path, role):
        path = plain_path(path)
        self.category(path)
        if role not in {'result', 'source', 'scratch'} or self.declared.setdefault(path, role) != role:
            raise ValueError('research_artifact_role_drift')

    def declare_cli_context(self, path, auth_source=None, *, qualified_cli=None):
        from app.services.codex_runtime_state_service import runtime_state_namespace_hash

        path = plain_path(path)
        home = path / 'runtime-state' / runtime_state_namespace_hash(path.name) / 'home'
        for name in CLI_RESULT_FILENAMES:
            self.declare(path / name, 'result')
        if auth_source is not None:
            # Account for the existing worker's exact auth reference without following it.
            self.auth_refs[home/'auth.json'] = str(Path(auth_source).resolve())
        if qualified_cli is not None:
            target = plain_path(qualified_cli)
            root = home/'tmp/arg0-macos'
            if (auth_source is None or not stat.S_ISREG(target.lstat().st_mode)
                    or not os.access(target,os.X_OK) or self.category(root)!='scratch'
                    or self.cli_arg0_roots.setdefault(root,str(target))!=str(target)):
                raise ValueError('research_artifact_cli_scratch_binding_invalid')
        self.cli_state_roots.add(home.parent)

    def measure(self):
        seen_dirs, inodes, arg0_dirs = set(), {}, {}
        rank = {'scratch': 0, 'source': 1, 'result': 2}

        def scan_error(path, operation, error):
            root = max((p for p in self.roots if path == p or path.is_relative_to(p)),
                key=lambda p: len(p.parts))
            return ArtifactScanError(operation=operation, path_category=self.category(path),
                relative_path=path.relative_to(root).as_posix(), error=error)

        def read_metadata(path, operation, read):
            try:
                return read()
            except OSError as exc:
                # Only this invocation's disposable CLI state may vanish during a scan.
                # Never hide a failure on a retained artifact or an observed declared root.
                if (isinstance(exc, FileNotFoundError) and path not in self.roots
                        and self.category(path) == 'scratch'
                        and any(path.is_relative_to(root) for root in self.cli_state_roots)
                        and not any(role != 'scratch' and (item == path or item.is_relative_to(path))
                            for item, role in (*self.roots.items(), *self.declared.items()))):
                    try:
                        path.lstat()
                    except FileNotFoundError:
                        return None
                    except OSError as probe_error:
                        exc, operation = probe_error, 'lstat'
                raise scan_error(path, operation, exc) from exc

        def visit(path):
            try:
                info = path.lstat()
            except FileNotFoundError:
                return
            except OSError as exc:
                raise scan_error(path, 'lstat', exc) from exc
            key = (info.st_dev, info.st_ino)
            if stat.S_ISDIR(info.st_mode):
                if key not in seen_dirs:
                    entries = read_metadata(path, 'iterdir', lambda: tuple(path.iterdir()))
                    if entries is None:
                        return
                    seen_dirs.add(key)
                    for entry in entries:
                        visit(entry)
                return
            role = self.category(path)
            if stat.S_ISLNK(info.st_mode):
                expected = self.auth_refs.get(path)
                root = path.parent.parent
                if expected is None and root in self.cli_arg0_roots:
                    # The qualified macOS CLI creates one private random arg0
                    # directory per invocation. Never traverse a link target.
                    if (role=='scratch' and path.name in {'applypatch','apply_patch'}
                            and re.fullmatch(r'codex-arg0[A-Za-z0-9]{6}',path.parent.name)):
                        directories = [read_metadata(p, 'lstat', p.lstat) for p in (root, path.parent)]
                        if any(info is None for info in directories):
                            return
                        if (all(stat.S_ISDIR(d.st_mode) and d.st_uid==os.geteuid() and not d.st_mode&0o077
                                for d in directories) and arg0_dirs.setdefault(root,path.parent)==path.parent):
                            expected = self.cli_arg0_roots[root]
                if expected is None:
                    raise ValueError('research_artifact_unexpected_symlink')
                target = read_metadata(path, 'readlink', lambda: os.readlink(path))
                if target is None:
                    return
                if target != expected:
                    raise ValueError('research_artifact_unexpected_symlink')
            elif not stat.S_ISREG(info.st_mode):
                raise ValueError('research_artifact_unexpected_file_type')
            if key not in inodes or rank[role] > rank[inodes[key][0]]:
                inodes[key] = (role, info.st_size)

        for root in self.roots:
            visit(plain_path(root))
        totals = dict(result=0, source=0, scratch=0)
        for role, size in inodes.values():
            totals[role] += size
        total = sum(totals.values())
        self.peak_work = max(self.peak_work, total)
        self.peak_result = max(self.peak_result, totals['result'])
        return dict(**totals, total=total, unique_files=len(inodes),
                    peak_observed_work=self.peak_work, peak_observed_result=self.peak_result)

    def check(self, *, path, added_work=0, added_result=0, role='scratch'):
        path = plain_path(path)
        self.category(path)
        totals = self.measure()
        for code, current, added, cap, category in (
            ('RESEARCH_RESULT_CAP', totals['result'], added_result, self.result_cap, 'result'),
            ('RESEARCH_WORK_CAP', totals['total'], added_work, self.work_cap, role),
        ):
            if current + added > cap:
                raise ArtifactCapacityError(code=code, role=category, current=current, projected=current+added, cap=cap)
        volumes = {}
        for root in (*self.roots, path):
            volume = next(p for p in (root, *root.parents) if p.exists())
            fs = os.statvfs(volume)
            volumes[volume.stat().st_dev] = fs.f_bavail * fs.f_frsize
        free = min(volumes.values())
        if free - added_work < self.free_guard:
            raise ArtifactCapacityError(code='RESEARCH_FREE_SPACE_GUARD', role=role, current=free,
                projected=free-added_work, cap=self.free_guard)
        return totals

    def before_write(self, path, size, *, role=None):
        path = plain_path(path)
        role = role or _role.get() or self.category(path)
        self.declare(path, role)
        # Atomic replacement briefly coexists with the previous file.
        return self.check(path=path, added_work=size, added_result=size if role == 'result' else 0, role=role)
