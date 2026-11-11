"""Explicitly authorized four-table export, without the production DB freezer.

This backend-only operation requires a trusted caller and a separately admitted
boundary: effective OS write denial for v2, or the opt-in trusted SQLite v3
Source canary policy. The latter is not a kernel sandbox. Authorization is
supplied by the operator, never by model JSON.
Private original rows must not be included in public reports.
"""
from dataclasses import dataclass
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import time
import hashlib
import json
from weakref import WeakKeyDictionary

from sqlalchemy import MetaData
from sqlmodel import Session, create_engine, select

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.unified_persisted_projection import project_local_seed
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy

MODELS = {m.__tablename__: m for m in (WatchlistItem, SecurityMaster, Company, InvestmentThesis)}
COLUMNS = {
    'watchlistitem': tuple('id ticker company_name exchange issuer_type ordinary_share_identifier adr_ratio adr_currency underlying_currency notes active monitoring_requested onboarding_state production_eligible onboarding_readiness onboarding_failure_stage onboarding_initial_evidence onboarding_evidence_fingerprint onboarding_decision_readiness onboarding_retry_class onboarding_attempt_count onboarding_last_attempt_at onboarding_next_retry_at onboarding_last_error onboarding_last_attempt_origin onboarding_market_packet_cutoff registration_requested_at onboarding_ready_at activated_at first_eligible_session latest_status latest_assessment_date latest_valuation_context latest_earnings_estimate_impact created_at'.split()),
    'securitymaster': tuple('id canonical_company_id canonical_security_id ticker exchange country company_name legal_name cik corp_code figi security_type share_class issuer_type ordinary_share_identifier adr_identifier adr_ratio known_subsidiaries known_products known_brands aliases search_aliases identity_quality identity_provider identity_warnings adr_ratio_source adr_ratio_as_of updated_at'.split()),
    'company': tuple('id ticker company_name exchange industry sector business_units revenue_sources major_customers ir_url filings_url created_at'.split()),
    'investmentthesis': tuple('id ticker version core_thesis time_horizon thesis_drivers validation_metrics market_expectations valuation_framework multiple_expansion_signals multiple_compression_signals strengthen_signals weaken_signals invalidation_signals price_rules macro_exposures status source created_at'.split()),
}


@dataclass(frozen=True)
class ExportPermission:
    """Operator-issued in-process scope, not a deserializable permission token."""
    event_id: str
    approved: bool
    database: Path
    device: int
    inode: int
    subjects: tuple[str, ...]

    def require(self):
        if not self.approved or not self.event_id:
            raise PermissionError('class_c_explicit_read_authorization_required')
        if not self.subjects or len(self.subjects) != len(set(self.subjects)) or len(self.subjects) > 100:
            raise ValueError('class_c_bounded_cohort_required')
        if any(not isinstance(t, str) or not t or len(t) > 32 for t in self.subjects):
            raise ValueError('class_c_subject_invalid')
        if any(p.is_symlink() for p in (self.database, *self.database.parents)):
            raise ValueError('class_c_source_symlink_denied')
        s = self.database.stat()
        if not self.database.is_file() or (s.st_dev, s.st_ino) != (self.device, self.inode):
            raise ValueError('class_c_source_identity_changed')


class QueryBoundary:
    """SQLite authorizer: no schema/caches/views, writes, attach or extension."""
    def __init__(self):
        self.reads = set()
        self.denied = []
        self.boot = True

    def __call__(self, action, first, second, database, trigger):
        allowed = False
        if action == sqlite3.SQLITE_READ:
            allowed = database == 'main' and trigger is None and first in COLUMNS and second in COLUMNS[first]
            if allowed:
                self.reads.add((first, second))
        elif action == sqlite3.SQLITE_SELECT:
            allowed = trigger is None
        elif action == sqlite3.SQLITE_TRANSACTION:
            allowed = first in {'BEGIN', 'ROLLBACK'}
        elif action == sqlite3.SQLITE_FUNCTION:
            allowed = second in {'max', 'count'} and trigger is None
        elif action == sqlite3.SQLITE_PRAGMA:
            allowed = self.boot and first == 'query_only' and second in {'ON', '1', None}
        if not allowed:
            self.denied.append(dict(action=action, table=first, column=second))
        return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY


def read_authorized_rows(permission: ExportPermission, *, connect=None):
    permission.require()  # Must fail before even opening a connection.
    if any(set(COLUMNS[t]) != set(m.model_fields) for t, m in MODELS.items()):
        raise ValueError('class_c_model_column_scope_changed')
    boundary = QueryBoundary()
    statements = []
    trace = []
    rows, metadata = {}, {}
    start = datetime.now(timezone.utc)
    deadline = time.monotonic() + 15
    connection = (connect or sqlite3.connect)(permission.database.as_uri() + '?mode=ro', uri=True,
                         isolation_level=None, timeout=3)
    try:
        connection.set_authorizer(boundary)
        connection.set_trace_callback(lambda sql: trace.append(dict(
            operation=sql.split()[0], sha256=hashlib.sha256(sql.encode()).hexdigest())))
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone() == (1,)
        boundary.boot = False
        connection.execute('BEGIN')
        assert connection.in_transaction
        marks = ','.join('?' for _ in permission.subjects)
        for table, columns in COLUMNS.items():
            fields = ','.join(f't."{c}"' for c in columns)
            sql = f'SELECT {fields} FROM "{table}" t WHERE t.ticker IN ({marks})'
            if table == 'investmentthesis':
                sql += " AND t.status='active' AND t.version=(SELECT max(v.version) FROM investmentthesis v WHERE v.ticker=t.ticker AND v.status='active')"
            sql += ' ORDER BY t.ticker LIMIT ?'
            # Store templates, not expanded bound values or private row bodies.
            statements.append(sql)
            values = connection.execute(sql, (*permission.subjects, len(permission.subjects)+1)).fetchall()
            if table == 'watchlistitem':
                acquired = datetime.now(timezone.utc)
            if len(values) > len(permission.subjects):
                raise ValueError('class_c_duplicate_source_rows')
            records = [dict(zip(columns, v, strict=True)) for v in values]
            if len({r['ticker'] for r in records}) != len(records):
                raise ValueError('class_c_duplicate_subject_or_thesis_version')
            if not {r['ticker'] for r in records} <= set(permission.subjects):
                raise ValueError('class_c_query_scope_escape')
            rows[table] = records
            metadata[table] = dict(selected=len(records), missing=len(permission.subjects)-len(records))
        sql = f"SELECT ticker,count(version) FROM investmentthesis WHERE ticker IN ({marks}) AND status='active' GROUP BY ticker"
        statements.append(sql)
        active_counts = dict(connection.execute(sql, permission.subjects).fetchall())
        metadata['investmentthesis']['older_active_versions_not_exported'] = sum(max(0,n-1) for n in active_counts.values())
        if len(encoded(rows)) > 8*1024*1024:
            raise ValueError('class_c_private_export_size_limit')
        permission.require()
        assert connection.in_transaction and connection.total_changes == 0 and not boundary.denied
        end = datetime.now(timezone.utc)
        return rows, dict(contract='minimal-class-c-readonly-v1', permission_event=permission.event_id,
            source_identity=dict(device=permission.device,inode=permission.inode),
            snapshot_started_at=start.isoformat(), snapshot_finished_at=end.isoformat(),
            cutoff=acquired.isoformat(), snapshot_acquisition_window=[start.isoformat(),acquired.isoformat()],
            snapshot='ONE_BEGIN_READ_TRANSACTION_ROLLBACK',
            sqlite_mode='ro', query_only=True, total_changes=0, tables=metadata,
            observed_column_reads=sorted(boundary.reads), denied_queries=boundary.denied,
            statement_templates=statements, query_trace=trace, generation_retroactive=False,
            whole_database_copy=False, wal_copy=False, original_rows_sha256=digest(rows))
    finally:
        if connection.in_transaction:
            connection.execute('ROLLBACK')
        connection.close()


class CapturedClassC:
    """Process-local exporter capability; public JSON cannot rehydrate it."""
    __slots__ = ('__weakref__',)


_CAPTURES = WeakKeyDictionary()
_PROJECTIONS = WeakKeyDictionary()


def capture_authorized_class_c(permission: ExportPermission, *, connect=None):
    rows, receipt = read_authorized_rows(permission, connect=connect)
    handle = CapturedClassC()
    _CAPTURES[handle] = (encoded(rows), encoded(receipt), permission.subjects)
    return handle


def captured_private_snapshot(handle):
    """Return copies for private custody; edits never mutate issuing state."""
    if not isinstance(handle, CapturedClassC) or handle not in _CAPTURES:
        raise ValueError('class_c_unissued_capture')
    raw, receipt, _ = _CAPTURES[handle]
    return raw, json.loads(receipt)


def project_captured_export(handle, *, market: str, session_key: str, policy: UnifiedSourcePolicy,
                            cycle_owner=None):
    raw, receipt = captured_private_snapshot(handle)
    rows = json.loads(raw)
    subjects = _CAPTURES[handle][2]
    if digest(rows) != receipt['original_rows_sha256'] or any(
            not {r['ticker'] for r in values} <= set(subjects) for values in rows.values()):
        raise ValueError('class_c_capture_binding_changed')
    # Private, original in-process projection is judged once per frozen market.
    # Public JSON cannot insert cache entries or reconstruct the capture handle.
    files=(Path(__file__),Path(__file__).with_name('onboarding_readiness_service.py'),
        Path(__file__).with_name('unified_persisted_projection.py'))
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    key=(market,session_key,digest(sorted(policy.allowed_providers)),id(cycle_owner))
    cache=_PROJECTIONS.setdefault(handle,{})
    if key in cache:
        previous,value=cache[key]
        if previous!=pins:raise ValueError('class_c_projection_implementation_changed')
        return deepcopy(value)
    value=project_authorized_rows(rows,market=market,session_key=session_key,
        cutoff=datetime.fromisoformat(receipt['cutoff']),policy=policy,cycle_owner=cycle_owner)
    cache[key]=(pins,deepcopy(value))
    return value


def registration_eligibility_audit(capture, *, approved_subjects, market_subjects, policy, sessions):
    """Safe diagnostics from the SAME captured rows and canonical projections."""
    from app.services.onboarding_readiness_service import canonical_registration_eligibility
    raw,receipt=captured_private_snapshot(capture)
    rows=json.loads(raw)
    indices={t:{r['ticker']:MODELS[t].model_validate(r) for r in values} for t,values in rows.items()}
    projections={m:project_captured_export(capture,market=m,session_key=sessions[m],policy=policy)
        for m in market_subjects}
    by_ticker={r['ticker']:r for p in projections.values() for r in p['universe']['eligibility_audit']}
    audit=[]
    for ticker in sorted(approved_subjects):
        row=by_ticker.get(ticker)
        if row is None:
            row=canonical_registration_eligibility(ticker=ticker,item=indices['watchlistitem'].get(ticker),
                security=indices['securitymaster'].get(ticker),thesis=indices['investmentthesis'].get(ticker),
                company=indices['company'].get(ticker),cutoff=datetime.fromisoformat(receipt['cutoff']))
        expected=[m for m,ts in market_subjects.items() if ticker in ts]
        detected=row['detected_market']
        scope_denials=['MARKET_CLASSIFICATION_MISMATCH'] if detected is not None and expected!=[detected] else []
        audit.append(dict(row,requested=True,requested_markets=expected,scope_denials=scope_denials,
            market_classification_state='OBSERVED' if detected is not None else 'NOT_OBSERVED_MISSING_REGISTRATION'))
    markets={}
    for m,p in projections.items():
        eligible=p['universe']['eligible_subjects']
        issues=[]
        if not eligible:issues.append('NO_ELIGIBLE_SUBJECT_FOR_MARKET')
        if not set(eligible)<=set(approved_subjects):issues.append('ELIGIBLE_SUBJECT_OUTSIDE_APPROVAL')
        if set(market_subjects[m])!=set(eligible):issues.append('SELECTED_CANONICAL_MEMBERSHIP_MISMATCH')
        markets[m]=dict(requested=list(market_subjects[m]),eligible=eligible,
            excluded=p['universe']['excluded_subjects'],scope_denials=issues,
            original_source_role_denials=[{k:d[k] for k in ('role','ticker','reason') if k in d}
                for d in p['denials']])
    return dict(contract='canonical-registration-eligibility-audit-v1',approval_subjects=sorted(approved_subjects),
        captured_at=receipt['cutoff'],capture_receipt_sha256=digest(receipt),original_rows_sha256=receipt['original_rows_sha256'],
        subjects=audit,markets=markets,private_thesis_exported=False,source_or_economic_grant=False)


def project_authorized_rows(rows, *, market: str, session_key: str,
                            cutoff: datetime, policy: UnifiedSourcePolicy, cycle_owner=None):
    """Structural projection only, NOT source authentication; use the capture gate."""
    if set(rows) != set(MODELS):
        raise ValueError('class_c_exact_four_tables_required')
    engine = create_engine('sqlite://')
    try:
        # Legacy stored NULLs must survive: ORM reads do not run Pydantic
        # constructor validation or replace missing dates with today's defaults.
        local_schema = MetaData()
        for model in MODELS.values():
            table = model.__table__.to_metadata(local_schema)
            for column in table.columns:
                column.nullable = True
        local_schema.create_all(engine)
        with engine.begin() as connection:
            for table, values in rows.items():
                columns = COLUMNS[table]
                seen = set()
                for value in values:
                    if set(value) != set(columns):
                        raise ValueError('class_c_exact_column_projection_required')
                    if value['id'] is None or value['id'] in seen:
                        raise ValueError('class_c_original_identity_duplicate')
                    seen.add(value['id'])
                    if any(v is not None and not isinstance(v, (str, int, float)) for v in value.values()):
                        raise ValueError('class_c_sql_scalar_required')
                fields = ','.join(f'"{c}"' for c in columns)
                marks = ','.join('?' for _ in columns)
                if values:
                    connection.exec_driver_sql(f'INSERT INTO "{table}" ({fields}) VALUES ({marks})',
                        [tuple(value[c] for c in columns) for value in values])
        with Session(engine) as session:
            originals = {}
            for table, model_type in MODELS.items():
                for model in session.exec(select(model_type)).all():
                    original = model.model_dump(mode='json')
                    key = (table,str(model.id))
                    if model.id is None or key in originals:
                        raise ValueError('class_c_original_identity_duplicate')
                    originals[key] = digest(original)
            result = project_local_seed(session,market=market,session_key=session_key,cutoff=cutoff,
                policy=policy,cycle_owner=cycle_owner)
            for role in result['roles'].values():
                for record in role['records']:
                    if originals[(record['table'],record['record_id'])] != record['original_record_sha256']:
                        raise ValueError('class_c_original_row_projection_drift')
            return result
    finally:
        engine.dispose()
