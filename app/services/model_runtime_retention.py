"""Retire one finished CLI's private state, preserving its execution evidence."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat

from app.services.codex_runtime_state_service import runtime_state_namespace_hash
from app.services.research_artifact_budget import plain_path


def tree_bytes(root):
    """Metadata only; do not follow auth references or other symlink targets."""
    seen, logical, allocated, files = set(), 0, 0, 0
    pending = [Path(root)]
    while pending:
        path = pending.pop()
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        key = info.st_dev, info.st_ino
        if key in seen:
            continue
        seen.add(key)
        if stat.S_ISDIR(info.st_mode):
            pending.extend(path.iterdir())
        else:
            logical += info.st_size
            allocated += getattr(info, 'st_blocks', 0) * 512
            files += 1
    return dict(logical_bytes=logical, allocated_bytes=allocated, files=files)


def retire_invocation_state(attempt, *, worker_pid, worker_reaped):
    """Remove only the expected namespace after its dedicated group is gone.

    The production worker starts the CLI in its own inherited process group.
    Prompt/schema, raw output, events/stderr, dispatch/exit receipts and the
    invocation journal live outside this disposable runtime-state subtree.
    """
    attempt = plain_path(attempt)
    state = plain_path(attempt / 'runtime-state' / runtime_state_namespace_hash(attempt.name))
    receipt = dict(contract='model-runtime-retention-v1', worker_pid=worker_pid,
        state_path=str(state), status='NOT_CREATED', removed_logical_bytes=0,
        removed_allocated_bytes=0, removed_files=0)
    if not state.exists():
        return receipt
    if not state.is_dir():
        raise ValueError('model_runtime_state_not_directory')
    if worker_reaped is not True or type(worker_pid) is not int or worker_pid <= 0:
        return dict(receipt, status='RETAINED_WORKER_NOT_REAPED')
    try:
        os.killpg(worker_pid, 0)
    except ProcessLookupError:
        pass
    except OSError:
        return dict(receipt, status='RETAINED_PROCESS_GROUP_UNCONFIRMED')
    else:
        return dict(receipt, status='RETAINED_PROCESS_GROUP_ACTIVE')
    before = tree_bytes(state)
    # shutil.rmtree unlinks internal symlinks; it never removes their targets.
    shutil.rmtree(state)
    try:
        state.parent.rmdir()
    except OSError:
        pass  # An unrelated namespace is not part of this invocation's cleanup.
    return dict(receipt, status='REMOVED', removed_logical_bytes=before['logical_bytes'],
        removed_allocated_bytes=before['allocated_bytes'], removed_files=before['files'])


def record_invocation_cleanup(attempt, *, worker_pid, worker_reaped):
    """Cleanup is secondary: never replace the model result or first exception."""
    from app.services.unified_run_artifacts import durable_json

    try:
        receipt = retire_invocation_state(attempt, worker_pid=worker_pid, worker_reaped=worker_reaped)
    except Exception as exc:
        receipt = dict(contract='model-runtime-retention-v1', worker_pid=worker_pid,
            status='RETAINED_CLEANUP_ERROR', error_type=type(exc).__name__)
    try:
        durable_json(Path(attempt) / 'runtime-cleanup.json', receipt)
    except Exception:
        # A capacity failure may prevent this optional receipt too. The original
        # parent/transport/error receipts keep their existing ownership and order.
        pass
    return receipt
