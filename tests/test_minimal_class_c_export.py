"""Synthetic source-scope proof, never production authority."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import sqlite3
import json

import pytest
from sqlmodel import Session, SQLModel, create_engine
from app.models.watchlist import WatchlistItem
from app.models.security import SecurityMaster
from app.models.company import Company
from app.models.thesis import InvestmentThesis
from app.services.minimal_class_c_export import (
    COLUMNS, MODELS, ExportPermission, QueryBoundary, project_authorized_rows, read_authorized_rows,
    CapturedClassC, capture_authorized_class_c, captured_private_snapshot, project_captured_export,
)
from app.services.unified_local_seed_bridge import admit_pinned_local_seed
from app.services.unified_snapshot_contract import encoded
from app.services.unified_source_policy import UnifiedSourcePolicy

AT = datetime(2026,9,26,tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({'canonical_local','sec_edgar','dart'}))


def database(tmp_path, subjects):
    path=tmp_path/'synthetic.sqlite3'
    engine=create_engine('sqlite:///'+str(path))
    SQLModel.metadata.create_all(engine,tables=[m.__table__ for m in MODELS.values()])
    with Session(engine) as session:
        for ticker,market in subjects:
            venue='NASDAQ' if market=='us' else 'KOSPI'
            session.add(WatchlistItem(ticker=ticker,company_name='Synthetic',exchange=venue,
                created_at=AT,activated_at=AT,registration_requested_at=AT,notes='private-not-in-projection'))
            session.add(SecurityMaster(ticker=ticker,company_name='Synthetic',exchange=venue,
                canonical_company_id='issuer:'+ticker,canonical_security_id='security:'+ticker,
                country='US' if market=='us' else 'KR',cik='1234' if market=='us' else None,
                corp_code='00123456' if market=='kr' else None,issuer_type='domestic_us' if market=='us' else 'krx',
                identity_provider='sec_edgar' if market=='us' else 'dart',updated_at=AT))
            session.add(Company(ticker=ticker,company_name='Synthetic',exchange=venue,created_at=AT))
            session.add_all([InvestmentThesis(ticker=ticker,version=1,core_thesis='old active',created_at=AT),
                InvestmentThesis(ticker=ticker,version=2,core_thesis='selected private',created_at=AT),
                InvestmentThesis(ticker=ticker,version=3,core_thesis='inactive excluded',status='inactive',created_at=AT)])
        session.commit()
    engine.dispose()
    s=path.stat()
    return ExportPermission('synthetic-explicit-grant',True,path,s.st_dev,s.st_ino,tuple(t for t,_ in subjects))


@pytest.fixture
def source(tmp_path):
    return database(tmp_path,[('UNSEEN','us')])


def project(rows,market='us'):
    return project_authorized_rows(rows,market=market,session_key='2026-09-25' if market=='us' else '2026-09-23',cutoff=AT,policy=POLICY)


def admit(doc,subjects,pin=None):
    raw=encoded(doc)
    return admit_pinned_local_seed(raw,expected_sha256=pin or sha256(raw).hexdigest(),market=doc['market'],
        session_key='2026-09-25',cutoff=AT,subjects=subjects,policy=POLICY)


def test_permission_denied_before_connection_or_stat(source):
    with pytest.raises(PermissionError,match='explicit_read'):
        read_authorized_rows(replace(source,approved=False,database=source.database/'absent'),
            connect=lambda *a,**k:pytest.fail('must not connect'))


def test_one_readonly_snapshot_exact_tables_columns_latest_version_and_owner(source):
    before=sha256(source.database.read_bytes()).hexdigest()
    rows,receipt=read_authorized_rows(source)
    assert set(rows)==set(COLUMNS)
    assert rows['investmentthesis'][0]['version']==2
    assert receipt['tables']['investmentthesis']['older_active_versions_not_exported']==1
    assert receipt['total_changes']==0 and not receipt['denied_queries']
    assert [x['operation'] for x in receipt['query_trace']]==['PRAGMA','PRAGMA','BEGIN',*['SELECT']*5,'ROLLBACK']
    assert set(t for t,_ in receipt['observed_column_reads'])==set(COLUMNS)
    assert all('SELECT *' not in s and 'providerresponsecache' not in s for s in receipt['statement_templates'])
    assert before==sha256(source.database.read_bytes()).hexdigest()
    doc=project(rows)
    assert not doc['denials']
    assert 'notes' not in doc['roles']['universe']['records'][0]['record']
    assert admit(doc,source.subjects)==doc


@pytest.mark.parametrize('sql',[
    'SELECT name FROM sqlite_master','PRAGMA table_info(watchlistitem)','PRAGMA wal_checkpoint',
    'UPDATE watchlistitem SET active=0','DELETE FROM watchlistitem',
    "ATTACH DATABASE ':memory:' AS other",'CREATE TABLE intrusion (id INTEGER)',
    'SELECT load_extension(NULL)','PRAGMA query_only=OFF','COMMIT',
])
def test_sql_authorizer_blocks_metadata_writes_attach_extensions(source,sql):
    connection=sqlite3.connect(source.database.as_uri()+'?mode=ro',uri=True)
    guard=QueryBoundary()
    guard.boot=False
    connection.set_authorizer(guard)
    try:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(sql)
        assert guard.denied
    finally:
        connection.close()


def test_other_table_and_view_reads_denied(source):
    with sqlite3.connect(source.database) as db:
        db.execute('CREATE TABLE providerresponsecache (payload TEXT)')
        db.execute('CREATE VIEW innocent AS SELECT ticker FROM watchlistitem')
    with sqlite3.connect(source.database.as_uri()+'?mode=ro',uri=True) as db:
        guard=QueryBoundary()
        guard.boot=False
        db.set_authorizer(guard)
        for sql in ['SELECT payload FROM providerresponsecache','SELECT ticker FROM innocent']:
            with pytest.raises(sqlite3.DatabaseError):
                db.execute(sql)
        assert guard.denied


@pytest.mark.parametrize('mutation',['inode','symlink','duplicate_cohort'])
def test_source_identity_rejected_before_connect(source,mutation,tmp_path):
    if mutation=='inode':
        source=replace(source,inode=source.inode+1)
    elif mutation=='symlink':
        link=tmp_path/'alias'
        link.symlink_to(source.database)
        source=replace(source,database=link)
    else:
        source=replace(source,subjects=source.subjects*2)
    with pytest.raises(ValueError):
        read_authorized_rows(source,connect=lambda *a,**k:pytest.fail('must not connect'))


@pytest.mark.parametrize('mutation',['cycle','future_activation','future_identity','future_thesis','missing_thesis','wrong_venue','conflicting_adr'])
def test_genuine_export_does_not_override_owner_denial(source,mutation):
    rows,_=read_authorized_rows(source)
    if mutation=='cycle':
        rows['watchlistitem'][0]['first_eligible_session']='2026-09-25'
    elif mutation=='future_activation':
        rows['watchlistitem'][0]['activated_at']=(AT+timedelta(days=1)).isoformat()
    elif mutation=='future_identity':
        rows['securitymaster'][0]['updated_at']=(AT+timedelta(days=1)).isoformat()
    elif mutation=='future_thesis':
        rows['investmentthesis'][0]['created_at']=(AT+timedelta(days=1)).isoformat()
    elif mutation=='missing_thesis':
        rows['investmentthesis']=[]
    elif mutation=='wrong_venue':
        rows['securitymaster'][0]['exchange']='KOSPI'
    else:
        rows['securitymaster'][0]['security_type']='adr'
    with pytest.raises(ValueError):
        admit(project(rows),source.subjects)


def test_replaced_after_export_pin_and_omitted_original_fields_rejected(source):
    rows,_=read_authorized_rows(source)
    doc=project(rows)
    pin=sha256(encoded(doc)).hexdigest()
    doc['roles']['stored_thesis_and_business_metadata']['records'][0]['record']['version']=99
    with pytest.raises(ValueError,match='independent_source_pin'):
        admit(doc,source.subjects,pin)
    rows['watchlistitem'][0].pop('notes')
    with pytest.raises(ValueError,match='exact_column'):
        project(rows)


def test_legacy_stored_null_preserved_without_registration_date_fabrication(source):
    from app.services.unified_snapshot_contract import digest
    rows,_=read_authorized_rows(source)
    rows['watchlistitem'][0]['registration_requested_at']=None
    doc=project(rows)
    original_engine=create_engine('sqlite:///'+str(source.database))
    with Session(original_engine) as session:
        original=session.get(WatchlistItem,rows['watchlistitem'][0]['id']).model_dump(mode='json')
    original_engine.dispose()
    original['registration_requested_at']=None
    expected=digest(original)
    assert doc['roles']['universe']['records'][0]['original_record_sha256']==expected
    assert admit(doc,source.subjects)==doc
    rows['watchlistitem'][0]['first_eligible_session']='2026-09-25'
    assert any(d['reason']=='first_eligible_cycle_to_session_authority_required' for d in project(rows)['denials'])


def test_configured_kr8_us14_structure(tmp_path):
    subjects=[(f'{100000+i}','kr') for i in range(8)]+[(f'UNSEEN{i}','us') for i in range(14)]
    permission=database(tmp_path,subjects)
    rows,receipt=read_authorized_rows(permission)
    assert all(r['selected']==22 for r in receipt['tables'].values())
    for market,n in [('kr',8),('us',14)]:
        doc=project(rows,market)
        assert len(doc['universe']['eligible_subjects'])==n and not doc['denials']
    assert not {'035420','NVDA'} & set(permission.subjects)


@pytest.mark.parametrize('ticker,market',[('035420','kr'),('NVDA','us')])
def test_pending_config_never_activates_registration(tmp_path,ticker,market):
    permission=database(tmp_path,[(ticker,market)])
    rows,_=read_authorized_rows(permission)
    rows['watchlistitem'][0].update(active=False,production_eligible=False,onboarding_state='PENDING')
    doc=project(rows,market)
    assert doc['universe']['eligible_subjects']==[]
    assert all(not r['eligible'] for r in doc['roles'].values())


def test_snapshot_remains_consistent_across_concurrent_task_wal_write(source):
    writer=sqlite3.connect(source.database)
    writer.execute('PRAGMA journal_mode=WAL')
    class Observed(sqlite3.Connection):
        def execute(self,sql,*args,**kwargs):
            if 'FROM "securitymaster"' in sql:
                writer.execute("UPDATE investmentthesis SET core_thesis='concurrent newer' WHERE version=2")
                writer.commit()
            return super().execute(sql,*args,**kwargs)
    try:
        rows,receipt=read_authorized_rows(source,connect=lambda *a,**kw:sqlite3.connect(*a,**kw,factory=Observed))
        assert rows['investmentthesis'][0]['core_thesis']=='selected private'
        assert receipt['total_changes']==0
        assert writer.execute('SELECT core_thesis FROM investmentthesis WHERE version=2').fetchone()==('concurrent newer',)
    finally:
        writer.close()


def test_duplicate_thesis_rows_and_partial_table_contract_rejected(source):
    rows,_=read_authorized_rows(source)
    rows['investmentthesis']*=2
    with pytest.raises(ValueError,match='original_identity_duplicate'):
        project(rows)
    rows.pop('company')
    with pytest.raises(ValueError,match='exact_four_tables'):
        project(rows)


def test_capture_capability_rejects_unissued_and_modified_decoded_copies(source):
    capture=capture_authorized_class_c(source)
    raw,receipt=captured_private_snapshot(capture)
    rows=json.loads(raw)
    rows['investmentthesis'][0]['core_thesis']='caller replacement'
    receipt['cutoff']='1900-01-01T00:00:00+00:00'
    for invalid in (CapturedClassC(),rows,receipt):
        with pytest.raises(ValueError,match='unissued_capture'):
            project_captured_export(invalid,market='us',session_key='2026-09-25',policy=POLICY)
    doc=project_captured_export(capture,market='us',session_key='2026-09-25',policy=POLICY)
    assert doc['cutoff']!='1900-01-01T00:00:00+00:00'
    thesis=next(r for r in doc['roles']['stored_thesis_and_business_metadata']['records'] if r['table']=='investmentthesis')
    assert thesis['record']['core_thesis']=='selected private'


def test_existing_wal_commits_visible_and_unapproved_cohort_extra_columns_excluded(tmp_path):
    permission=database(tmp_path,[('PERMITTED','us'),('OTHER','us')])
    writer=sqlite3.connect(permission.database)
    try:
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('ALTER TABLE company ADD COLUMN private_extra TEXT')
        writer.execute("UPDATE company SET private_extra='never export'")
        writer.execute("UPDATE investmentthesis SET core_thesis='wal committed' WHERE ticker='PERMITTED' AND version=2")
        writer.commit()
        rows,receipt=read_authorized_rows(replace(permission,subjects=('PERMITTED',)))
        assert rows['investmentthesis'][0]['core_thesis']=='wal committed'
        assert all({r['ticker'] for r in v}=={'PERMITTED'} for v in rows.values())
        assert 'private_extra' not in rows['company'][0]
        assert all(c!='private_extra' for _,c in receipt['observed_column_reads'])
    finally:
        writer.close()


def test_runtime_connection_guard_not_captured_as_default(source,monkeypatch):
    def denied(*args,**kwargs):
        raise PermissionError('runtime_guard')
    monkeypatch.setattr(sqlite3,'connect',denied)
    with pytest.raises(PermissionError,match='runtime_guard'):
        read_authorized_rows(source)
