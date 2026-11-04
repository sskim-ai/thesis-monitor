"""Opt-in local worker over the existing research DB, with no legacy startup.

This is a no-send research runtime, not a production provider admission service.
SQLite transactions exclude all concurrent writers; the advisory lease additionally
excludes cooperating runtime instances. Existing collectors are not claimed enrolled.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import re
import sqlite3
import stat

from app.services.vnext_research_store import ResearchStore, SCHEMA, TABLES, digest, encoded, now, plain

CONTRACT = 'vnext-runtime-v1'
CANONICAL_ROOT = Path(__file__).resolve().parents[2] / 'data/vnext'
DATA_TABLES = (*TABLES, 'research_meta', 'user_snapshot', 'research_run',
               'source_capture', 'research_observation', 'research_failure')
WRITABLE_TABLES = {'research_meta', 'research_observation'}
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')


@dataclass(frozen=True)
class RuntimeConfig:
    path: Path
    instance: str
    mode: str = 'read_only'
    environment: str = 'research'

    @classmethod
    def from_environment(cls, env=None):
        env = os.environ if env is None else env
        if env.get('VNEXT_RUNTIME_ENABLED') != '1':
            raise ValueError('vnext_runtime_default_off')
        if any(env.get(k, '0') != '0' for k in
               ('VNEXT_PROVIDER_ENABLED', 'VNEXT_MODEL_ENABLED', 'VNEXT_SEND_ENABLED')):
            raise ValueError('external_capabilities_not_admitted')
        path = env.get('VNEXT_DB_PATH', '')
        if not path or not Path(path).is_absolute():
            raise ValueError('explicit_absolute_vnext_path_required')
        if env.get('DATABASE_URL') not in (None, '', 'sqlite:///' + path):
            raise ValueError('legacy_session_url_denied')
        result = cls(Path(path), env.get('VNEXT_INSTANCE_ID', ''),
                     env.get('VNEXT_RUNTIME_MODE', 'read_only'),
                     env.get('VNEXT_ENVIRONMENT', 'research'))
        result.validate()
        return result

    def validate(self):
        if not ID.fullmatch(self.instance) or self.mode not in ('read_only', 'dry_run', 'write'):
            raise ValueError('runtime_identity_or_mode')
        if self.environment not in ('research', 'test'):
            raise ValueError('runtime_environment')
        # Production invocation cannot select arbitrary existing SQLite databases.
        # Tests may only select isolated scratch; a test flag cannot open an old DB.
        root = CANONICAL_ROOT if self.environment == 'research' else Path('/private/tmp')
        # Reject traversal and foreign paths before even stat-ing an excluded DB.
        if not self.path.is_absolute() or '..' in self.path.parts or not self.path.is_relative_to(root):
            raise ValueError('existing_vnext_database_required')
        path = plain(self.path)
        if not path.is_file():
            raise ValueError('existing_vnext_database_required')
        s = path.stat()
        if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
            raise ValueError('aliased_database_denied')
        for suffix in ('-wal', '-shm', '-journal'):
            side = plain(str(path) + suffix)
            if side.exists() and (not side.is_file() or side.stat().st_nlink != 1):
                raise ValueError('aliased_database_sidecar_denied')
        return path, (s.st_dev, s.st_ino)


class RuntimeStore(ResearchStore):
    """Reuse original reads/parsers without bootstrap, registration writes or raw copies."""
    def __init__(self, config):
        self.config = config
        self.path, self.identity = config.validate()
        self._transaction = None
        with self.connect() as c:
            if c.execute("SELECT value FROM research_meta WHERE key='schema'").fetchone() != (SCHEMA,):
                raise ValueError('unrecognized_existing_database')
            actual = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not set(DATA_TABLES) <= actual:
                raise ValueError('research_schema_missing')

    def _assert_identity(self):
        path, identity = self.config.validate()
        if path != self.path or identity != self.identity:
            raise ValueError('database_identity_changed')

    @staticmethod
    def _authorizer(write):
        def check(action, first, second, db, trigger):
            if trigger is not None:
                return sqlite3.SQLITE_DENY
            allowed = action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_TRANSACTION,
                                 sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE)
            # SQLite's count(*) optimization emits an empty-column read with no
            # database name; allow only known-table counts, never other schemas.
            allowed |= (action == sqlite3.SQLITE_READ and first in (*DATA_TABLES, 'sqlite_master')
                        and (db == 'main' or db is None and second == ''))
            allowed |= (action == sqlite3.SQLITE_PRAGMA and
                        (first == 'table_info' and second in DATA_TABLES or
                         first in ('journal_mode', 'query_only') and second is None))
            allowed |= (write and action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE,
                                             sqlite3.SQLITE_DELETE) and db == 'main' and first in WRITABLE_TABLES)
            return sqlite3.SQLITE_OK if allowed else sqlite3.SQLITE_DENY
        return check

    def _open(self, write=False):
        self._assert_identity()
        c = sqlite3.connect(self.path.as_uri() + ('?mode=rw' if write else '?mode=ro'),
                            uri=True, isolation_level=None, timeout=2)
        try:
            c.enable_load_extension(False)
            c.execute('PRAGMA foreign_keys=ON')
            if not write:
                c.execute('PRAGMA query_only=ON')
            c.set_authorizer(self._authorizer(write))
            self._assert_identity()
            return c
        except BaseException:
            c.close()
            raise

    @contextmanager
    def connect(self):
        if self._transaction is not None:
            yield self._transaction
            return
        c = self._open()
        try:
            c.execute('BEGIN')
            yield c
        finally:
            if c.in_transaction:
                c.rollback()
            c.close()

    @contextmanager
    def snapshot(self):
        if self._transaction is not None:
            yield
            return
        with self.connect() as c:
            self._transaction = c
            try:
                yield
            finally:
                self._transaction = None

    @contextmanager
    def atomic_job(self, job_id, request):
        if self.config.mode != 'write':
            raise ValueError('read_only_runtime')
        if not ID.fullmatch(job_id) or self._transaction is not None:
            raise ValueError('invalid_or_nested_job')
        lock = plain(str(self.path) + '.vnext-runtime.lock')
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        c = None
        try:
            if os.fstat(fd).st_nlink != 1 or not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('writer_lock_alias')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            c = self._open(write=True)
            c.execute('BEGIN IMMEDIATE')
            self._transaction = c
            key = CONTRACT + ':job:' + job_id
            old = c.execute('SELECT value FROM research_meta WHERE key=?', (key,)).fetchone()
            stamp = digest(request() if callable(request) else request)
            if old:
                old = json.loads(old[0])
                if old['request_sha256'] != stamp:
                    raise ValueError('job_idempotency_conflict')
            cell = {'previous': old, 'result': None}
            yield cell
            if not old:
                if cell['result'] is None:
                    raise ValueError('job_result_required')
                receipt = dict(contract=CONTRACT, instance=self.config.instance,
                               request_sha256=stamp, status='COMMITTED', at=now(), result=cell['result'])
                c.execute('INSERT INTO research_meta VALUES (?,?)', (key, encoded(receipt).decode()))
            c.commit()
        finally:
            self._transaction = None
            if c is not None:
                if c.in_transaction:
                    c.rollback()
                c.close()
            os.close(fd)

    def capture(self, *args, **kwargs):
        raise ValueError('provider_capture_not_admitted_use_existing_receipts')

    def start_run(self, *args, **kwargs):
        raise ValueError('runtime_reuses_original_run')

    def import_snapshot(self, *args, **kwargs):
        raise ValueError('registration_import_not_exposed')


class VNextRuntime:
    def __init__(self, config):
        self.store = RuntimeStore(config)

    def state(self):
        with self.store.connect() as c:
            counts = {t: c.execute('SELECT count(*) FROM "' + t + '"').fetchone()[0] for t in DATA_TABLES}
            columns = {t: [r[1] for r in c.execute('PRAGMA table_info("' + t + '")')] for t in DATA_TABLES}
            statuses = dict(c.execute('SELECT status,count(*) FROM investmentthesis GROUP BY status'))
            active = c.execute('SELECT count(*) FROM watchlistitem WHERE active=1').fetchone()[0]
            runs = [dict(zip(('run_id', 'started_at', 'as_of', 'status'), r)) for r in
                    c.execute('SELECT run_id,started_at,as_of,status FROM research_run ORDER BY started_at')]
            journal = c.execute('PRAGMA journal_mode').fetchone()[0]
        return dict(contract=CONTRACT, schema=SCHEMA, mode=self.store.config.mode,
                    environment=self.store.config.environment, instance=self.store.config.instance,
                    counts=counts, columns=columns, thesis_status_counts=statuses, active_registered=active,
                    runs=runs, journal_mode=journal, provider='NOT_ADMITTED', model='OFF', send='OFF',
                    strict_native_ready=0, no_migration=True)

    def registration(self):
        # Only public identity, never notes, theses, positions, or the private snapshot.
        keys = ('ticker', 'canonical_security_id', 'canonical_company_id', 'country', 'exchange', 'currency', 'security_type')
        return [{k: row.get(k) for k in keys} for row in self.store.identities()]

    def coverage(self):
        with self.store.connect() as c:
            return [dict(zip(('run_id', 'field', 'status', 'count'), row)) for row in c.execute(
                'SELECT run_id,field,status,count(*) FROM research_observation GROUP BY run_id,field,status ORDER BY run_id,field,status')]

    def valuation_identity(self, ticker):
        from app.services.vnext_research_ingestion import current_identity
        return current_identity(self.store, ticker)

    def ingest_reviewed_valuation(self, **kwargs):
        from app.services.vnext_research_ingestion import ingest_reviewed_valuation
        return ingest_reviewed_valuation(self.store.config, **kwargs)

    def ingest_reviewed_kis(self, **kwargs):
        from app.services.vnext_research_ingestion import ingest_reviewed_kis
        return ingest_reviewed_kis(self.store.config, **kwargs)

    def ingest_reviewed_kis_sources(self, **kwargs):
        from app.services.vnext_kis_source_ingestion import ingest_sources
        return ingest_sources(self.store.config, **kwargs)

    def ingest_reviewed_kis_multisource(self, **kwargs):
        from app.services.vnext_kis_multisource_ingestion import ingest
        return ingest(self.store.config, **kwargs)

    def research_product(self, ticker, *, as_of, run_ids=None, ingestion=None, historical_valuation_owner=None,
                         source_runtime=None, source_run_ids=None, kis_ingestion=None,
                         kis_source_owner=None, kis_multisource_owner=None, **references):
        """Trusted manual worker flow; no Settings, network, models or sending.

        A reviewed callback is a backend capability, never public receipt JSON.
        Caller authorization is still required for a write-mode runtime.
        """
        from app.services.vnext_composite_research import draft, render_draft
        stages = []
        identity = self.valuation_identity(ticker)
        stages.append(dict(stage='REGISTRATION', status='QUALIFIED',
                           registration_version=identity['registration_version']))
        if kis_ingestion is not None:
            if ingestion is not None:raise ValueError('one_ingestion_per_atomic_product')
            reviewed=kis_ingestion.get('reviewed_capture')
            if (not callable(reviewed) or reviewed()['security']['ticker'] != ticker or
                kis_ingestion.get('expected_registration_version') != identity['registration_version']):
                raise ValueError('research_product_source_security_mismatch')
            imported=self.ingest_reviewed_kis(**kis_ingestion)
            stages.append(dict(stage='PERSIST_KIS',status='COMMITTED',receipt=imported))
        if ingestion is not None:
            reviewed = ingestion.get('reviewed_capture')
            if (not callable(reviewed) or reviewed()['security']['ticker'] != ticker or
                    ingestion.get('expected_registration_version') != identity['registration_version']):
                raise ValueError('research_product_source_security_mismatch')
            imported = self.ingest_reviewed_valuation(**ingestion)
            stages.append(dict(stage='PERSIST', status='COMMITTED', receipt=imported))
        else:
            stages.append(dict(stage='PERSIST', status='READ_ONLY_EXISTING'))
        packet = self.composite_batch([ticker], as_of=as_of, run_ids=run_ids,
                                      kis_multisource_owner=kis_multisource_owner)[0]
        if source_runtime is not None:
            if not isinstance(source_runtime, VNextRuntime) or source_runtime.store.config.mode != 'read_only':
                raise ValueError('read_only_source_runtime_required')
            source_identity = source_runtime.valuation_identity(ticker)
            if identity['security'] != source_identity['security']:
                raise ValueError('research_source_registration_mismatch')
            other = source_runtime.composite_batch([ticker],as_of=as_of,run_ids=source_run_ids)[0]
            from app.services.vnext_composite_research import merge_public_reference
            packet = merge_public_reference(packet,other)
            stages.append(dict(stage='SOURCE',status='QUALIFIED_PUBLIC_NOT_DURABLE',source_snapshot=other['snapshot_sha256']))
        from app.services.vnext_reference_bundle import assemble
        if kis_source_owner is not None:
            from app.services.vnext_kis_source_state import attach
            packet = attach(packet, kis_source_owner)
            stages.append(dict(stage='KIS_SOURCE_STATUS', status='READ_ONLY_SOURCE_OBSERVATION'))
        packet = assemble(packet, **references)
        result = draft(packet, historical_valuation_owner=historical_valuation_owner,
                       kis_source_owner=kis_source_owner, kis_multisource_owner=kis_multisource_owner, **references)
        stages.extend([dict(stage='COMPOSITE', status='QUALIFIED', packet_sha256=digest(packet)),
                       dict(stage='MODEL', status='NOT_RUN'),
                       dict(stage='MESSAGE', status='NO_SEND_RENDERED')])
        return dict(contract='vnext-research-product-v1', stages=stages, packet=packet,
                    draft=result, preview=render_draft(result), send=False, strict_ready=False)

    def research_product_views(self, ticker, *, as_of, review_owner=None,
                               kis_multisource_owner=None, post_model_as_of=None, **data_options):
        """Two explicit no-send products; a data preview is never a model result."""
        from app.services.vnext_ai_research_review import ResearchReviewOwner, render_data_view
        if any(data_options.get(k) is not None for k in ('ingestion','kis_ingestion')):
            raise ValueError('research_views_readonly_only')
        product = self.research_product(ticker, as_of=as_of,
            kis_multisource_owner=kis_multisource_owner, **data_options)
        result = dict(data=product, data_view=render_data_view(product), ai_review=None,
                      new_model_calls=0, send=False, strict_ready=False)
        if review_owner is not None:
            if not isinstance(review_owner, ResearchReviewOwner):
                raise ValueError('live_research_review_owner_required')
            # The AI input excludes optional display attachments, exactly as at issuance.
            parent = self.composite_batch([ticker], as_of=as_of,
                kis_multisource_owner=kis_multisource_owner)[0]
            receipt = review_owner.issue(parent)
            result['ai_review'] = review_owner.consume(receipt, parent)
            later = (lambda: self.composite_batch([ticker], as_of=post_model_as_of,
                kis_multisource_owner=kis_multisource_owner)[0]) if post_model_as_of is not None else None
            with self.store.connect() as c:
                persisted = {row[0] for row in c.execute(
                    'SELECT observation_id FROM research_observation WHERE ticker=?', (ticker,)).fetchall()}
            views = review_owner.readable_views(receipt, parent, post_model_loader=later,
                persisted_record_ids=persisted)
            result['ai_readable'] = views['readable']
            result['ai_audit'] = views['audit']
            result['default_view'] = 'ai_readable'
        else:
            if post_model_as_of is not None:
                raise ValueError('post_model_requires_actual_model_owner')
            result['default_view'] = 'data_view'
        return result

    def verify_sources(self, run_id, provider=None):
        with self.store.connect() as c:
            rows = c.execute('SELECT capture_id,provider,raw_sha,raw_path,captured_at,receipt_json FROM source_capture WHERE run_id=?', (run_id,)).fetchall()
        if not rows:
            raise ValueError('unknown_or_empty_source_run')
        checked = []
        for ident, source, sha, path, at, text in rows:
            if provider and source != provider:
                continue
            expected = plain(self.store.path.parent / 'raw' / sha)
            if not re.fullmatch(r'[0-9a-f]{64}', sha) or plain(path) != expected:
                raise ValueError('source_path_not_canonical_cas')
            if expected.stat().st_nlink != 1 or digest(expected.read_bytes()) != sha:
                raise ValueError('source_integrity_gap')
            receipt = json.loads(text)
            if receipt.get('captured_at') != at:
                raise ValueError('capture_time_binding')
            checked.append(dict(capture_id=ident, provider=source, raw_sha=sha, captured_at=at,
                                receipt_sha256=digest(receipt), current_recollection=False))
        if not checked:
            raise ValueError('provider_receipt_missing')
        return checked

    def shadow(self, run_id, ticker):
        with self.store.snapshot():
            self.verify_sources(run_id)
            return self.store.packet(run_id, ticker)

    def draft(self, run_id, ticker, *, job_id=None):
        if job_id is not None:
            prepared = {}
            def request():
                prepared['result'] = self.draft(run_id, ticker)
                return dict(action='draft', content_sha256=digest(prepared['result']))
            with self.store.atomic_job(job_id, request) as cell:
                if cell['previous']:
                    return cell['previous']['result']
                cell['result'] = prepared['result']
                return cell['result']
        packet = self.shadow(run_id, ticker)
        result = dict(contract='vnext-unsent-source-draft-v1', run_id=run_id, ticker=ticker,
                      evidence_as_of=packet['as_of'], input_sha256=digest(packet),
                      facts=packet['facts'], missing_fields=packet['missing_fields'],
                      source_variant_counts=packet['source_variant_counts'],
                      decision=None, model_execution='NOT_RUN', send_allowed=False,
                      strict_native_ready=False, user_thesis_excluded=True,
                      message_status='DRAFT_SOURCE_CONTEXT_NOT_MODEL_JUDGMENT')
        return result

    def composite(self, ticker, *, as_of, run_ids=None, price_reference=None, component_reference=None, financial_reference=None):
        packet = self.composite_batch([ticker], as_of=as_of, run_ids=run_ids)[0]
        from app.services.vnext_reference_bundle import assemble
        return assemble(packet, price_reference=price_reference, component_reference=component_reference, financial_reference=financial_reference)

    def composite_batch(self, tickers=None, *, as_of, run_ids=None, kis_multisource_owner=None):
        from app.services.vnext_composite_research import CompositeView
        with self.store.snapshot():
            view = CompositeView(self.store, as_of=as_of, run_ids=run_ids, tickers=tickers,
                                 kis_multisource_owner=kis_multisource_owner)
            subjects = sorted(view.identities) if tickers is None else tickers
            if not subjects or len(subjects) != len(set(subjects)) or not set(subjects) <= set(view.identities):
                raise ValueError('composite_subject_scope')
            return [view.packet(t) for t in subjects]

    def composite_draft(self, ticker, *, as_of, run_ids=None, price_reference=None, component_reference=None, financial_reference=None):
        from app.services.vnext_composite_research import draft
        return draft(self.composite(ticker, as_of=as_of, run_ids=run_ids, price_reference=price_reference,
                                     component_reference=component_reference, financial_reference=financial_reference), price_reference=price_reference,
                     component_reference=component_reference, financial_reference=financial_reference)

    def valuation(self, run_id, ticker, market_type, *, job_id=None):
        from app.services import vnext_valuation_replay as replay
        def request():
            inputs = self.verify_sources(run_id, 'Kiwoom')
            security = next((s for s in self.store.identities() if s['ticker'] == ticker), None)
            with self.store.connect() as c:
                run = c.execute('SELECT * FROM research_run WHERE run_id=?', (run_id,)).fetchone()
            return dict(action='valuation', run_id=run_id, ticker=ticker, market_type=market_type,
                        receipts=inputs, security=security, run=list(run) if run else None, policy=replay.POLICY,
                        implementation=replay.implementation_identity())
        if job_id is None:
            with self.store.snapshot():
                request()
                return replay.replay_valuation(self.store, run_id, ticker, market_type, persist=False)
        with self.store.atomic_job(job_id, request) as cell:
            if cell['previous']:
                return cell['previous']['result']
            cell['result'] = replay.replay_valuation(self.store, run_id, ticker, market_type, persist=True)
            return cell['result']
