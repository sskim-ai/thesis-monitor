"""One authorized registration capture, kept in the trusted process only.

No consent is minted here. Callers supply the existing backend permission and
approval objects after separate user authorization. No file snapshot is made.
"""
from pathlib import Path

from sqlalchemy.engine import make_url

from app.services import prospective_class_c_owner as original
from app.services.minimal_class_c_export import capture_authorized_class_c, captured_private_snapshot


def database_target(settings, *, runtime_directory):
    """Resolve already-loaded runtime settings without opening the database."""
    url = make_url(settings.database_url)
    if url.get_backend_name() != 'sqlite' or not url.database or url.database == ':memory:' or url.query:
        raise ValueError('selected_exact_local_sqlite_target_required')
    path = Path(url.database)
    if not path.is_absolute():
        path = Path(runtime_directory) / path
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('selected_registration_symlink_denied')
    stat = path.stat()
    if not path.is_file():
        raise ValueError('selected_registration_file_required')
    return path.absolute(), stat.st_dev, stat.st_ino


def capture_markets(*, permission, approval, generations, policy, enabled=False, connect=None, on_captured=None):
    if enabled is not True:
        raise ValueError('selected_registration_default_off')
    if not generations or not set(generations) <= {'us','kr'} or len(set(generations.values())) != len(generations):
        raise ValueError('selected_distinct_market_generations_required')
    decision = original._approval(approval)
    if permission.event_id != decision.event_id or set(permission.subjects) != set(decision.subjects):
        raise ValueError('selected_registration_approval_scope_mismatch')
    capture = (capture_authorized_class_c(permission) if connect is None
        else capture_authorized_class_c(permission, connect=connect))
    _, receipt = captured_private_snapshot(capture)
    if on_captured is not None:
        on_captured(receipt)
    owners = {}
    try:
        for market, generation in generations.items():
            owners[market], _ = original.issue_prospective_owner(approval=approval, capture=capture,
                market=market, source_generation_id=generation, generation_id=generation, policy=policy)
    except Exception:
        for owner in owners.values():
            original.revoke_prospective_owner(owner)
        raise
    return capture, owners, receipt


def capture_approved_markets(*, settings, runtime_directory, approval, generations,
                             policy, ledger, enabled=False, connect=None):
    """Derive the existing export permission from the ONE backend audit event."""
    if enabled is not True:
        raise ValueError('selected_registration_default_off')
    from app.services.minimal_class_c_export import ExportPermission
    decision = original._approval(approval)
    path, device, inode = database_target(settings, runtime_directory=runtime_directory)
    permission = ExportPermission(decision.event_id, True, path, device, inode, decision.subjects)
    ledger.before_registration(approval=approval, permission=permission, generations=generations)
    def original_connect(*args, **kwargs):
        import sqlite3
        ledger.before_database_open()
        return (connect or sqlite3.connect)(*args, **kwargs)
    try:
        capture, owners, receipt = capture_markets(permission=permission, approval=approval,
            generations=generations, policy=policy, enabled=True, connect=original_connect,
            on_captured=ledger.registration_captured)
        return capture, owners, receipt
    except Exception:
        ledger.stop('REGISTRATION_CAPTURE_OR_OWNER_REJECTED')
        raise


def local_seed(owner, *, stock, policy):
    """Use the original authenticated document, never a persisted public receipt."""
    from app.services.unified_local_seed_bridge import admit_pinned_local_seed
    from app.services.unified_snapshot_contract import digest, encoded
    original.require_generation(owner, stock.run_id)
    document, receipt = original._state(owner)
    sessions = {r.latest_completed_session for r in stock.reads}
    if (receipt['market'] != stock.market or len(sessions) != 1
            or receipt['calendar']['target'] not in sessions
            or receipt['cutoff'] != stock.frozen_at.isoformat()
            or set(receipt['bindings']) != set(stock.subjects)):
        raise ValueError('selected_registration_stock_generation_or_scope_mismatch')
    projected = original.apply_prospective_owner(document, original=document, owner=owner)
    return admit_pinned_local_seed(encoded(projected), expected_sha256=digest(projected),
        market=stock.market, session_key=next(iter(sessions)), cutoff=stock.frozen_at,
        subjects=stock.subjects, policy=policy, prospective_owner=owner)
