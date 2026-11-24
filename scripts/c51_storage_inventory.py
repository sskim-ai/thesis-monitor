"""Inspect only one saved generation and its declared runtime; never delete files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat

from app.services.codex_runtime_state_service import runtime_state_namespace_hash
from app.services.research_artifact_budget import CLI_RESULT_FILENAMES, plain_path
from app.services.unified_run_artifacts import durable_json


def inventory(generation):
    generation = plain_path(generation)
    preflight = json.loads(plain_path(generation / 'model-runtime-preflight.json').read_bytes())
    runtime = plain_path(preflight['runtime_root'])
    roots = {plain_path(path): role for path, role in preflight['artifact_roots'].items()}
    if roots != {generation: 'source', generation / 'results': 'result', runtime: 'scratch'}:
        raise ValueError('storage_inventory_generation_roots_mismatch')
    if runtime == generation or runtime.is_relative_to(generation) or generation.is_relative_to(runtime):
        raise ValueError('storage_inventory_runtime_roots_overlap')
    rank = {'scratch': 0, 'source': 1, 'result': 2}
    seen_dirs, files = set(), {}

    def visit(path):
        try:
            info = path.lstat()
        except FileNotFoundError:
            return
        key = info.st_dev, info.st_ino
        if stat.S_ISDIR(info.st_mode):
            if key not in seen_dirs:
                seen_dirs.add(key)
                for child in path.iterdir():
                    visit(child)
            return
        # lstat only: neither auth references nor arbitrary symlinks are followed.
        root = max((root for root in roots if path == root or path.is_relative_to(root)),
            key=lambda root: len(root.parts))
        role = roots[root]
        relative = path.relative_to(root)
        if root == runtime and len(relative.parts) == 2 and path.name in CLI_RESULT_FILENAMES:
            role = 'result'  # Same per-invocation result declarations as the live budget.
        if key not in files or rank[role] > rank[files[key]['role']]:
            files[key] = dict(role=role, root=str(root), top=relative.parts[0],
                logical_bytes=info.st_size, allocated_bytes=getattr(info, 'st_blocks', 0) * 512)

    for root in roots:
        visit(root)
    totals = {role: dict(logical_bytes=0, allocated_bytes=0, files=0) for role in rank}
    root_totals = {str(root): dict(declared_root_role=role, logical_bytes=0,
        allocated_bytes=0, files=0) for root, role in roots.items()}
    directories = {}
    for row in files.values():
        key = row['root'], row['top'], row['role']
        bucket = directories.setdefault(key, dict(path=str(Path(row['root']) / row['top']), role=row['role'],
            logical_bytes=0, allocated_bytes=0, files=0))
        for target in (totals[row['role']], root_totals[row['root']], bucket):
            for name in ('logical_bytes', 'allocated_bytes'):
                target[name] += row[name]
            target['files'] += 1
    attempts, invalid_candidates = [], []
    for attempt in sorted(runtime.iterdir()) if runtime.is_dir() else []:
        if attempt.is_symlink() or not attempt.is_dir():
            continue
        state = attempt / 'runtime-state' / runtime_state_namespace_hash(attempt.name)
        try:
            state = plain_path(state)
        except ValueError:
            invalid_candidates.append(dict(attempt=str(attempt), reason='SYMLINK_IN_STATE_PATH'))
            continue
        if not state.is_dir():
            continue
        attempts.append(dict(attempt=str(attempt), disposable_state=str(state),
            parent_exit_present=(attempt / 'parent-exit.json').is_file(),
            cleanup_receipt_present=(attempt / 'runtime-cleanup.json').is_file(),
            deletion_performed=False))
    return dict(contract='generation-storage-inventory-v1', generation=str(generation),
        runtime_root=str(runtime), roots={str(path): role for path, role in roots.items()},
        accounting_kind='FILESYSTEM_ROOTS_WITH_KNOWN_RECEIPT_OVERRIDES_NOT_FULL_HISTORICAL_BUDGET',
        accounting_limitation='Historical per-file Budget.declared overrides are not reconstructed; '
            'role totals must not be treated as the original cap accounting. Physical root totals '
            'use nonoverlapping declared roots and deduplicate shared inodes.',
        physical_root_totals=root_totals,
        totals=totals, total_logical_bytes=sum(row['logical_bytes'] for row in totals.values()),
        total_allocated_file_bytes=sum(row['allocated_bytes'] for row in totals.values()),
        allocation_note='st_blocks metadata; APFS shared extents and free-space recovery are not measured',
        directories=sorted(directories.values(), key=lambda row: row['logical_bytes'], reverse=True)[:30],
        runtime_state_candidates=attempts, invalid_runtime_state_candidates=invalid_candidates,
        deleted_files=0, credentials_opened=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.generation)
    durable_json(plain_path(args.output), result)
    print(json.dumps({key: result[key] for key in ('total_logical_bytes',
        'total_allocated_file_bytes', 'deleted_files')}, sort_keys=True))


if __name__ == '__main__':
    main()
