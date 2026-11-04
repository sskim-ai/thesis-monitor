"""Private research persistence. This adapter issues no Native or source authority."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3

SCHEMA = 'vnext-private-research-v1'
TABLES = ('watchlistitem', 'securitymaster', 'company', 'investmentthesis')
STATES = {'CURRENT_VALID', 'SOURCE_REFERENCE', 'SHORT_HISTORY', 'STALE', 'PROVIDER_LIMIT',
          'MISSING_SOURCE', 'POLICY_DENIED', 'NOT_ATTEMPTED', 'MAPPING_CONFLICT', 'RESEARCH_UNREVIEWED'}

def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encoded(value)).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def plain(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('symlink_path_denied')
    return path

def operating_metadata(path):
    result = {}
    for suffix in ('', '-wal', '-shm', '-journal'):
        p = plain(str(path) + suffix)
        if p.exists():
            s = p.stat()
            if not p.is_file() or s.st_nlink != 1:
                raise ValueError('nonregular_or_aliased_database')
            result[suffix] = [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]
    return result

def read_user_snapshot(source, *, write_denial_check):
    """One consistent four-table snapshot, with values confined to private storage."""
    source = plain(source)
    before = operating_metadata(source)
    if not before:
        raise ValueError('source_missing')
    write_denial_check(source)
    con = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, isolation_level=None, timeout=3)
    trace = []
    def authorizer(action, first, second, db, trigger):
        allowed = trigger is None and (
            action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_TRANSACTION) or
            action == sqlite3.SQLITE_READ and db == 'main' and first in TABLES or
            action == sqlite3.SQLITE_PRAGMA and first == 'table_info' and second in TABLES)
        return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY
    try:
        con.execute('PRAGMA query_only=ON')
        con.enable_load_extension(False)
        con.set_authorizer(authorizer)
        con.set_trace_callback(lambda s: trace.append({'operation': s.split()[0], 'sha256': digest(s.encode())}))
        con.execute('BEGIN')
        start = now()
        columns = {t: [r[1] for r in con.execute('PRAGMA table_info("' + t + '")')] for t in TABLES}
        if any(not c or 'ticker' not in c for c in columns.values()):
            raise ValueError('four_table_identity_schema_missing')
        rows = {}
        def select(table, clause, args=()):
            cols = columns[table]
            sql = 'SELECT ' + ','.join('"' + c.replace('"','""') + '"' for c in cols)
            values = con.execute(sql + ' FROM "' + table + '" WHERE ' + clause, args).fetchall()
            return [dict(zip(cols, r, strict=True)) for r in values]
        rows['watchlistitem'] = select('watchlistitem', 'active=1')
        tickers = tuple(r['ticker'] for r in rows['watchlistitem'])
        if not 0 < len(tickers) <= 100 or len(set(tickers)) != len(tickers):
            raise ValueError('registered_cohort_ambiguous')
        clause = 'ticker IN (' + ','.join('?' for _ in tickers) + ')'
        for table in TABLES[1:]:
            rows[table] = select(table, clause, tickers)
        assert con.total_changes == 0
        receipt = dict(contract='private-vnext-user-snapshot-v1', cutoff=start, finished_at=now(),
            query_count=4, source_metadata_before=before, snapshot_sha256=digest(rows),
            counts={t: len(v) for t, v in rows.items()}, columns=columns,
            user_rows_exportable=False, source_mode='ro', total_changes=0, trace=trace,
            class_c_owner_issued=False)
        return rows, receipt
    finally:
        if con.in_transaction:
            con.rollback()
        con.close()

class ResearchStore:
    def __init__(self, path, *, operating=None):
        self.path = plain(path)
        if operating:
            source = plain(operating)
            if self.path == source or (self.path.exists() and os.path.samefile(self.path, source)):
                raise ValueError('operating_database_destination_denied')
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.path.exists():
            if self.path.stat().st_nlink != 1:
                raise ValueError('aliased_vnext_denied')
            with sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True) as c:
                if c.execute("SELECT value FROM research_meta WHERE key='schema'").fetchone() != (SCHEMA,):
                    raise ValueError('unrecognized_existing_database')
        else:
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            from sqlalchemy import MetaData
            from sqlmodel import create_engine
            from app.services.minimal_class_c_export import MODELS
            metadata = MetaData()
            for model in MODELS.values():
                table = model.__table__.to_metadata(metadata)
                # Preserve historical NULLs, never synthesize today's user registration.
                for column in table.columns:
                    if not column.primary_key:
                        column.nullable = True
                    column.default = None
            engine = create_engine('sqlite:///' + str(self.path))
            metadata.create_all(engine)
            engine.dispose()
            with self.connect() as c:
                c.executescript('''
                CREATE TABLE research_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE user_snapshot(snapshot_sha TEXT PRIMARY KEY,cutoff TEXT NOT NULL,rows_json TEXT NOT NULL,receipt_json TEXT NOT NULL);
                CREATE TABLE research_run(run_id TEXT PRIMARY KEY,started_at TEXT NOT NULL,as_of TEXT NOT NULL,status TEXT NOT NULL);
                CREATE TABLE source_capture(capture_id TEXT PRIMARY KEY,run_id TEXT NOT NULL,provider TEXT NOT NULL,request_key TEXT NOT NULL,raw_sha TEXT NOT NULL,raw_path TEXT NOT NULL,captured_at TEXT NOT NULL,receipt_json TEXT NOT NULL,UNIQUE(run_id,provider,request_key));
                CREATE TABLE research_observation(observation_id TEXT PRIMARY KEY,run_id TEXT NOT NULL,ticker TEXT NOT NULL,field TEXT NOT NULL,status TEXT NOT NULL,source_sha TEXT NOT NULL,payload_json TEXT NOT NULL,UNIQUE(run_id,ticker,field,source_sha));
                CREATE TABLE research_failure(run_id TEXT NOT NULL,provider TEXT NOT NULL,request_key TEXT NOT NULL,reason TEXT NOT NULL,at TEXT NOT NULL,PRIMARY KEY(run_id,provider,request_key));
                ''')
                c.execute('INSERT INTO research_meta VALUES (?,?)', ('schema', SCHEMA))

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path)
        c.execute('PRAGMA foreign_keys=ON')
        try:
            with c:
                yield c
        finally:
            c.close()

    def import_snapshot(self, rows, receipt):
        if set(rows) != set(TABLES) or digest(rows) != receipt['snapshot_sha256']:
            raise ValueError('snapshot_identity_mismatch')
        with self.connect() as c:
            c.execute('INSERT OR IGNORE INTO user_snapshot VALUES (?,?,?,?)',
                      (receipt['snapshot_sha256'], receipt['cutoff'], encoded(rows).decode(), encoded(receipt).decode()))
            for table in TABLES:
                cols = {r[1] for r in c.execute('PRAGMA table_info("'+table+'")')}
                for row in rows[table]:
                    names = sorted(set(row) & cols)
                    if not row.get('id') or not row.get('ticker'):
                        raise ValueError('source_row_key_missing')
                    values = [row[n] for n in names]
                    c.execute('INSERT INTO "'+table+'" ('+','.join('"'+n+'"' for n in names)+') VALUES ('+','.join('?' for _ in names)+') ON CONFLICT(id) DO UPDATE SET '+','.join('"'+n+'"=excluded."'+n+'"' for n in names if n!='id'), values)
                    actual = c.execute('SELECT '+','.join('"'+n+'"' for n in names)+' FROM "'+table+'" WHERE id=?',(row['id'],)).fetchone()
                    if list(actual) != values:
                        raise ValueError('user_state_roundtrip_mismatch')
            assert not c.execute('PRAGMA foreign_key_check').fetchall()
        return dict(counts={t:len(v) for t,v in rows.items()}, snapshot_sha256=receipt['snapshot_sha256'],
                    roundtrip_equal=True, extra_columns_preserved_in_private_snapshot=True, class_c_owner_issued=False)

    def identities(self):
        with self.connect() as c:
            c.row_factory=sqlite3.Row
            return [dict(r) for r in c.execute('SELECT s.* FROM securitymaster s JOIN watchlistitem w ON w.ticker=s.ticker WHERE w.active=1 ORDER BY s.ticker')]

    def start_run(self, run_id, as_of):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
            raise ValueError('unsafe_run_identifier')
        if datetime.fromisoformat(as_of).tzinfo is None:
            raise ValueError('aware_cutoff_required')
        with self.connect() as c:
            old=c.execute('SELECT as_of FROM research_run WHERE run_id=?',(run_id,)).fetchone()
            if old and old[0]!=as_of:
                raise ValueError('run_cutoff_mutation')
            c.execute('INSERT OR IGNORE INTO research_run VALUES (?,?,?,?)',(run_id,now(),as_of,'RUNNING'))

    def capture(self, run_id, provider, key, raw, receipt):
        sha=digest(raw);path=plain(self.path.parent/'raw'/sha)
        path.parent.mkdir(mode=0o700,exist_ok=True)
        if path.exists():
            if path.stat().st_nlink != 1: raise ValueError('aliased_raw_denied')
            if digest(path.read_bytes()) != sha: raise ValueError('CAS_corruption')
        else:
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
        ident=digest([run_id,provider,key])
        with self.connect() as c:
            old=c.execute('SELECT raw_sha FROM source_capture WHERE capture_id=?',(ident,)).fetchone()
            if old and old[0]!=sha:raise ValueError('capture_replacement_denied')
            c.execute('INSERT OR IGNORE INTO source_capture VALUES (?,?,?,?,?,?,?,?)',(ident,run_id,provider,key,sha,str(path),receipt['captured_at'],encoded(receipt).decode()))
        return sha

    def observation(self, run_id, ticker, field, status, source_sha, payload):
        if status not in STATES or any(k in payload for k in ('accepted_Core','accepted_receipt','field','status','source_sha')):
            raise ValueError('research_status_not_ownership')
        if not source_sha or payload.get('strict_native') is not False:
            raise ValueError('explicit_source_and_strict_denial_required')
        key=digest([run_id,ticker,field,source_sha])
        with self.connect() as c:
            if not c.execute('SELECT 1 FROM watchlistitem WHERE ticker=? AND active=1',(ticker,)).fetchone():
                raise ValueError('not_registered')
            if not c.execute('SELECT 1 FROM research_run WHERE run_id=?',(run_id,)).fetchone():
                raise ValueError('unknown_run')
            if not c.execute('SELECT 1 FROM source_capture WHERE run_id=? AND raw_sha=?',(run_id,source_sha)).fetchone():
                raise ValueError('unrecorded_source')
            c.execute('INSERT OR REPLACE INTO research_observation VALUES (?,?,?,?,?,?,?)',(key,run_id,ticker,field,status,source_sha,encoded(payload).decode()))

    def market_observation(self,run_id,market,field,source_sha,payload):
        if market not in ('KR','US') or payload.get('strict_native') is not False or any(k in payload for k in ('accepted_Core','accepted_receipt')):
            raise ValueError('market_research_scope')
        ticker='@MARKET:'+market;key=digest([run_id,ticker,field,source_sha])
        with self.connect() as c:
            if not c.execute('SELECT 1 FROM source_capture WHERE run_id=? AND raw_sha=?',(run_id,source_sha)).fetchone():raise ValueError('unrecorded_market_source')
            c.execute('INSERT OR REPLACE INTO research_observation VALUES (?,?,?,?,?,?,?)',(key,run_id,ticker,field,'SOURCE_REFERENCE',source_sha,encoded(payload).decode()))

    def market_packet(self,run_id,market):
        if market not in ('KR','US'):raise ValueError('market_research_scope')
        with self.connect() as c:
            rows=c.execute('SELECT field,source_sha,payload_json FROM research_observation WHERE run_id=? AND ticker=? ORDER BY field',(run_id,'@MARKET:'+market)).fetchall()
        return dict(market=market,run_id=run_id,full_market_owner=False,strict_native=False,
            facts=[dict(field=f,source_sha=h,payload=json.loads(p)) for f,h,p in rows],send_allowed=False)

    def packet(self, run_id, ticker):
        with self.connect() as c:
            if not c.execute('SELECT 1 FROM watchlistitem WHERE ticker=? AND active=1',(ticker,)).fetchone():
                raise ValueError('not_registered')
            rows=c.execute('SELECT field,status,source_sha,payload_json FROM research_observation WHERE run_id=? AND ticker=? ORDER BY field,source_sha',(run_id,ticker)).fetchall()
            run=c.execute('SELECT as_of FROM research_run WHERE run_id=?',(run_id,)).fetchone()
        if not run:raise ValueError('unknown_run')
        from app.services.unified_stock_acquisition import ROLES
        fields=['completed_close']+['ohlcv.'+r for r in ROLES]+[
            'financial.revenue','financial.operating_income','financial.net_income',
            'valuation.PER','valuation.PBR','valuation.FPER','valuation.FY1_EPS']
        selected={};variants={}
        for row in rows:
            f,s,h,p=row;data=json.loads(p)
            variants[f]=variants.get(f,0)+1
            current=bool(data.get('current_capture') or data.get('source_captured_this_run'))
            if f not in selected or current:selected[f]=(row,current)
        rows=[entry[0] for entry in selected.values()]
        present={r[0] for r in rows}
        return dict(contract='vnext-shadow-evidence-v1',run_id=run_id,ticker=ticker,as_of=run[0],
            provenance='REAL_CAPTURE_OR_EXPLICIT_REPLAY',strict_native_ready=False,send_allowed=False,
            facts=[dict(field=f,status=s,source_sha=h,**json.loads(p)) for f,s,h,p in rows],
            missing_fields=[dict(field=f,status='NOT_ATTEMPTED',reason='NO_OBSERVATION_IN_THIS_RUN') for f in fields if f not in present],
            model_execution='NOT_RUN',decision=None,live_authority=False,
            source_variant_counts=variants,
            user_thesis_excluded=True)
