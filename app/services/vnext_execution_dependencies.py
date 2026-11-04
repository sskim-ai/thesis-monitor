"""Deterministic code custody for a frozen manual execution, not source authority."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import uuid

CONTRACT = 'FIXED_EXECUTION_DEPENDENCIES_V1'


def _plain(path):
    path = Path(path).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('dependency_symlink_or_noncanonical_path')
    return path


def _pin(path):
    path = _plain(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('dependency_not_regular_file')
        h = hashlib.sha256()
        while data := os.read(fd, 65536):
            h.update(data)
        after = os.fstat(fd)
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('dependency_changed_during_read')
        return dict(bytes=after.st_size, sha256=h.hexdigest())
    finally:
        os.close(fd)


def _paths(root):
    root = _plain(root)
    if not root.is_dir():
        raise ValueError('dependency_root_missing')
    paths = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            _plain(Path(directory)/name)
        paths.extend(str(Path(directory)/name) for name in files if name.endswith('.py'))
    return sorted(paths)


def freeze(files, *, inventory_roots, module_roots):
    """Caller must review the explicit path/category set before freezing it."""
    pinned = {str(_plain(p)):dict(category=category, **_pin(p)) for p, category in sorted(files.items())}
    roots = {str(_plain(r)):_paths(r) for r in inventory_roots}
    if any(p not in pinned for paths in roots.values() for p in paths):
        raise ValueError('dependency_inventory_not_fully_reviewed')
    return dict(contract=CONTRACT, files=pinned, inventory_roots=roots,
                module_roots=[str(_plain(r)) for r in module_roots])


class DependencyDrift(ValueError):
    def __init__(self, report, receipt):
        super().__init__('FROZEN_DEPENDENCY_DRIFT:'+str(receipt))
        self.report, self.receipt = report, receipt


def check(manifest, *, phase, failure_dir, modules=None):
    """Import membership may grow inside the fixed manifest, never beyond it."""
    if manifest['contract'] != CONTRACT:
        raise ValueError('dependency_contract')
    files = manifest['files']
    report = dict(contract=CONTRACT, phase=phase, pid=os.getpid(),
                  at=datetime.now(timezone.utc).isoformat(), missing=[], new=[], modified=[],
                  unexpected_modules=[], invalid=[], loaded=[])
    origins = {}
    for name, mod in tuple((sys.modules if modules is None else modules).items()):
        path = getattr(mod, '__file__', None)
        if not path:
            continue
        path = str(Path(path).absolute())
        if not any(Path(path).is_relative_to(r) for r in manifest['module_roots']):
            continue
        row = dict(module=name, path=path, import_origin=getattr(getattr(mod, '__spec__', None), 'origin', None))
        origins.setdefault(path, []).append(row)
        report['loaded'].append(row)
        if path not in files:
            try: row = dict(row, actual=_pin(path))
            except (OSError, ValueError) as exc: row = dict(row, error=str(exc))
            report['unexpected_modules'].append(row)
    for path, expected in files.items():
        row = dict(path=path, expected=expected, import_origin=origins.get(path, []))
        try: actual = _pin(path)
        except FileNotFoundError:
            report['missing'].append(dict(row, actual=None));continue
        except (OSError, ValueError) as exc:
            report['invalid'].append(dict(row, actual=None, error=str(exc)));continue
        if actual != {k:expected[k] for k in ('bytes', 'sha256')}:
            report['modified'].append(dict(row, actual=actual))
    for root, expected in manifest['inventory_roots'].items():
        try: actual = _paths(root)
        except (OSError, ValueError) as exc:
            report['invalid'].append(dict(path=root, error=str(exc)));continue
        for path in sorted(set(actual)-set(expected)):
            try: value = _pin(path)
            except (OSError, ValueError) as exc: value = dict(error=str(exc))
            report['new'].append(dict(path=path, expected=None, actual=value, import_origin=origins.get(path, [])))
    report['pass'] = not any(report[k] for k in ('missing','new','modified','unexpected_modules','invalid'))
    if not report['pass']:
        directory = _plain(failure_dir)
        directory.mkdir(parents=True, exist_ok=True)
        receipt = directory/('dependency-'+uuid.uuid4().hex+'.json')
        with receipt.open('x') as f:
            json.dump(report, f, sort_keys=True, ensure_ascii=False, indent=2)
            f.write('\n')
        raise DependencyDrift(report, receipt)
    return report
