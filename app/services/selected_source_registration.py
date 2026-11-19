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


def capture_markets(*, permission, approval, generations, policy, enabled=False, connect=None, on_captured=None,
                    market_subjects=None, audit_path=None, staged_markets=False,
                    subject_limits=None, priority_subjects=None, diagnostics=None,
                    execution=None, regular_assignments=None,reference_captures=None,retained_capture_pins=None,
                    monitoring_only=False, source_subjects=None):
    if enabled is not True:
        raise ValueError('selected_registration_default_off')
    if not generations or not set(generations) <= {'us','kr'} or len(set(generations.values())) != len(generations):
        raise ValueError('selected_distinct_market_generations_required')
    if source_subjects is not None and (
            not staged_markets or subject_limits is None or market_subjects is None
            or set(source_subjects) != set(generations)
            or any(not ts or len(set(ts)) != len(ts) or not set(ts) <= set(market_subjects.get(m, ()))
                   for m, ts in source_subjects.items())):
        raise ValueError('selected_retained_source_scope_invalid')
    decision = original._approval(approval)
    if permission.event_id != decision.event_id or set(permission.subjects) != set(decision.subjects):
        raise ValueError('selected_registration_approval_scope_mismatch')
    capture_args = {} if diagnostics is None else dict(diagnostics=diagnostics)
    if connect is not None:
        capture_args['connect'] = connect
    capture = capture_authorized_class_c(permission, **capture_args)
    _, receipt = captured_private_snapshot(capture)
    if callable(regular_assignments):
        regular_assignments = regular_assignments(capture)
    if on_captured is not None:
        on_captured(receipt)
    audit=None
    if market_subjects is not None:
        if ((not set(generations)<=set(market_subjects) if staged_markets else set(market_subjects)!=set(generations))
                or sorted(t for ts in market_subjects.values() for t in ts)
                !=sorted(permission.subjects)):
            raise ValueError('selected_exact_canonical_cohort_required')
        from app.services.minimal_class_c_export import registration_eligibility_audit
        from app.services.unified_run_artifacts import durable_json
        from datetime import datetime
        cutoff=datetime.fromisoformat(receipt['cutoff'])
        audit=registration_eligibility_audit(capture,approved_subjects=decision.subjects,
            market_subjects=market_subjects,policy=policy,
            sessions={m:original.completed_clock(m,cutoff)['target'] for m in market_subjects},
            execution=execution,regular_assignments=regular_assignments,monitoring_only=monitoring_only)
        if audit_path is not None:durable_json(Path(audit_path),audit,exclusive=True)
        if any(row['scope_denials'] for row in audit['subjects']):
            raise ValueError('MARKET_CLASSIFICATION_MISMATCH')
    owners = {}
    try:
        for market, generation in generations.items():
            selected=None
            if subject_limits is not None:
                limit=subject_limits.get(market)
                if (not staged_markets or audit is None or type(limit) is not int or limit<1
                        or set(priority_subjects or {})-set(generations)):
                    raise ValueError('selected_explicit_positive_subject_limit_required')
                eligible=sorted(r['ticker'] for r in audit['subjects']
                    if r['detected_market']==market and r['canonical_eligible'])
                if source_subjects is not None:
                    eligible=[t for t in eligible if t in source_subjects[market]]
                priority=tuple((priority_subjects or {}).get(market,()))
                if len(set(priority))!=len(priority) or not set(priority)<=set(market_subjects[market]):
                    raise ValueError('selected_priority_outside_approved_market')
                selected=tuple(([t for t in priority if t in eligible]+[t for t in eligible if t not in priority])[:limit])
                if not selected:raise ValueError('NO_ELIGIBLE_SUBJECT_FOR_MARKET')
            owners[market], _ = original.issue_prospective_owner(approval=approval, capture=capture,
                market=market, source_generation_id=generation, generation_id=generation, policy=policy,
                **(dict(purpose=original.ROUTINE_SCOPE) if getattr(decision,'routine_us_no_send_source_seconds',None) is not None else {}),
                **(dict(subjects=selected) if selected is not None else {}),
                execution=execution,regular_assignments=regular_assignments,
                reference_capture=(reference_captures or {}).get(market),
                retained_capture_sha256=(retained_capture_pins or {}).get(market),monitoring_only=monitoring_only)
    except Exception:
        for owner in owners.values():
            original.revoke_prospective_owner(owner)
        raise
    return capture, owners, receipt


def capture_approved_markets(*, settings, runtime_directory, approval, generations,
                             policy, ledger, enabled=False, connect=None, audit_path=None,
                             subject_limits=None,priority_subjects=None,diagnostics_path=None,
                             execution=None,regular_assignments=None,reference_captures=None,
                             revalidation_work_order_sha256=None,monitoring_only=False,source_subjects=None):
    """Derive the existing export permission from the ONE backend audit event."""
    if enabled is not True:
        raise ValueError('selected_registration_default_off')
    from app.services.minimal_class_c_export import ExportPermission
    decision = original._approval(approval)
    path, device, inode = database_target(settings, runtime_directory=runtime_directory)
    permission = ExportPermission(decision.event_id, True, path, device, inode, decision.subjects,
        max_private_export_bytes=ledger.identity.get('capture_max_private_export_bytes',8*1024*1024))
    retained_capture_pins={m:ledger.identity['children'][m].get('retained_capture_sha256') for m in generations}
    new_retained_use=bool(reference_captures) and all(retained_capture_pins.values())
    if new_retained_use:
        from app.services.unified_snapshot_contract import digest
        if (revalidation_work_order_sha256 is not None or set(reference_captures)!=set(generations)
                or any(digest(reference_captures[m])!=retained_capture_pins[m] for m in generations)):
            raise ValueError('selected_new_retained_capture_pin_required')
    ledger.before_registration(approval=approval, permission=permission, generations=generations,
        revalidation_work_order_sha256=revalidation_work_order_sha256)
    if reference_captures:
        if (set(reference_captures)!=set(generations) or revalidation_work_order_sha256 is None
                or any(reference_captures[m]!=ledger.state()['registration_revalidations'][m]['previous']['receipt']
                    for m in generations)) and not new_retained_use:
            raise ValueError('selected_revalidation_original_receipt_required')
    def original_connect(*args, **kwargs):
        import sqlite3
        import inspect
        if connect is not None:
            inspect.signature(connect).bind(*args,**kwargs)
        ledger.before_database_open()
        return (connect or sqlite3.connect)(*args, **kwargs)
    diagnostics={}
    try:
        capture, owners, receipt = capture_markets(permission=permission, approval=approval,
            generations=generations, policy=policy, enabled=True, connect=original_connect,
            on_captured=ledger.registration_captured,
            market_subjects={m:c['subjects'] for m,c in ledger.identity['children'].items()},audit_path=audit_path,
            staged_markets=ledger.identity.get('staged_markets',False),
            subject_limits=subject_limits,priority_subjects=priority_subjects,diagnostics=diagnostics,
            execution=execution,regular_assignments=regular_assignments,reference_captures=reference_captures,
            retained_capture_pins=retained_capture_pins if new_retained_use else None,
            monitoring_only=monitoring_only,source_subjects=source_subjects)
        if ledger.identity.get('staged_markets'):
            for market, owner in owners.items():
                ledger.select_registered_subjects(market,owner)
        return capture, owners, receipt
    except Exception:
        ledger.stop('REGISTRATION_CAPTURE_OR_OWNER_REJECTED')
        raise
    finally:
        if diagnostics_path is not None:
            from app.services.unified_run_artifacts import durable_json
            durable_json(Path(diagnostics_path),dict(diagnostics,
                approved_subjects=list(decision.subjects),requested_markets=list(generations),
                capture_scope='FULL_APPROVED_ROSTER',source_rows_exported=False),exclusive=True)


def local_seed(owner, *, stock, policy):
    """Use the original authenticated document, never a persisted public receipt."""
    from app.services.unified_local_seed_bridge import admit_pinned_local_seed
    from app.services.unified_snapshot_contract import digest, encoded
    original.require_generation(owner, stock.run_id,
        purpose=original.ROUTINE_SCOPE if stock.routine_us_no_send_source_seconds is not None else original.SCOPE)
    document, receipt = original._state(owner)
    sessions = {r.latest_completed_session for r in stock.reads}
    if (receipt.get('routine_us_no_send_source_seconds') != stock.routine_us_no_send_source_seconds
            or receipt['market'] != stock.market or len(sessions) != 1
            or receipt['calendar']['target'] not in sessions
            or receipt['cutoff'] != stock.frozen_at.isoformat()
            or set(receipt['bindings']) != set(stock.subjects)):
        raise ValueError('selected_registration_stock_generation_or_scope_mismatch')
    projected = original.apply_prospective_owner(document, original=document, owner=owner)
    return admit_pinned_local_seed(encoded(projected), expected_sha256=digest(projected),
        market=stock.market, session_key=next(iter(sessions)), cutoff=stock.frozen_at,
        subjects=stock.subjects, policy=policy, prospective_owner=owner)
