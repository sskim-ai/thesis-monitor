"""C22AG synthetic boundaries only; never use a real registry or provider."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
import socket
import sqlite3
import sqlite3.dbapi2
import subprocess

import pytest
from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateTable
from sqlmodel import Session

from app.services.minimal_class_c_export import COLUMNS, MODELS
from app.services.registration_definition_import import (
    import_registration_definitions, prepare_registration_definitions,
)

AT = datetime(2026, 1, 5, tzinfo=timezone.utc)
SUBJECTS = ('NEWUS', '123456')


@pytest.fixture(autouse=True)
def isolated_boundary(monkeypatch):
    original = sqlite3.connect

    def memory_only(database, *args, **kwargs):
        if database != ':memory:':
            raise PermissionError('C22AG_TEST_REAL_DATABASE_FORBIDDEN')
        return original(database, *args, **kwargs)

    def denied(*args, **kwargs):
        raise PermissionError('C22AG_TEST_NETWORK_OR_SUBPROCESS_FORBIDDEN')

    monkeypatch.setattr(sqlite3, 'connect', memory_only)
    monkeypatch.setattr(sqlite3.dbapi2, 'connect', memory_only)
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
    monkeypatch.setattr(subprocess, 'Popen', denied)


def donor(subjects=SUBJECTS):
    rows = {table: [] for table in MODELS}
    for i, ticker in enumerate(subjects, 1):
        market = 'KRX' if ticker.isdigit() else 'NASDAQ'
        objects = {
            'watchlistitem': MODELS['watchlistitem'](id=i, ticker=ticker,
                company_name=ticker+' Company', exchange=market, created_at=AT,
                registration_requested_at=AT, active=False, production_eligible=False,
                onboarding_state='PENDING_ONBOARDING', onboarding_failure_stage='COMPANY_PROFILE'),
            'securitymaster': MODELS['securitymaster'](id=i, ticker=ticker,
                canonical_company_id='company:'+ticker, canonical_security_id='security:'+ticker,
                company_name=ticker+' Company', exchange=market,
                country='KR' if ticker.isdigit() else 'US', identity_quality='inferred',
                identity_provider='local', updated_at=AT),
            'company': MODELS['company'](id=i, ticker=ticker,
                company_name=ticker+' Company', exchange=market, created_at=AT),
        }
        for table, model in objects.items():
            rows[table].append(model.model_dump(mode='json'))
        for version in range(1, 6):
            model = MODELS['investmentthesis'](id=(i-1)*5+version,
                ticker=ticker, version=version, core_thesis='Synthetic private definition '+str(version),
                created_at=AT, status='active' if version == 5 else 'superseded',
                thesis_drivers='["original driver"]', valuation_framework='{"original":"unchanged"}',
                price_rules='{"synthetic":1}')
            rows['investmentthesis'].append(model.model_dump(mode='json'))
    return rows


def database(factory=sqlite3.Connection):
    connection = sqlite3.connect(':memory:', isolation_level=None, factory=factory)
    for model in MODELS.values():
        connection.execute(str(CreateTable(model.__table__).compile(dialect=sqlite.dialect())))
    return connection


def apply(connection, rows, enabled=True):
    return import_registration_definitions(connection, rows, subjects=SUBJECTS,
        max_versions_per_subject=5, enabled=enabled)


def insert(connection, table, record):
    columns = tuple(record)
    fields = ','.join('"'+field+'"' for field in columns)
    marks = ','.join('?' for _ in columns)
    connection.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({marks})', tuple(record.values()))


def test_atomic_two_subject_history_and_private_safe_receipt():
    rows, connection = donor(), database()
    result = apply(connection, rows)
    assert result['inserted_rows'] == 16 and result['commits'] == 1 and result['SELECT'] == 9
    assert connection.execute('SELECT count(*) FROM investmentthesis').fetchone() == (10,)
    assert connection.execute('SELECT version,core_thesis,price_rules,status FROM investmentthesis WHERE ticker=? ORDER BY version',
        (SUBJECTS[0],)).fetchall() == [(r['version'], r['core_thesis'], r['price_rules'], r['status'])
        for r in rows['investmentthesis'] if r['ticker'] == SUBJECTS[0]]
    assert connection.execute('SELECT identity_quality FROM securitymaster').fetchall() == [('inferred',), ('inferred',)]
    assert connection.execute('SELECT active,production_eligible,activated_at FROM watchlistitem').fetchall() == [(0,0,None),(0,0,None)]
    assert 'Synthetic private' not in json.dumps(result)
    assert not result['activation_granted'] and not result['source_or_economic_grant']


def test_exact_second_import_is_noop_and_unrelated_primary_ids_survive():
    connection = database()
    outside = donor(('OTHER',))
    for table, records in outside.items():
        for record in records:
            insert(connection, table, record)
    before = connection.execute('SELECT core_thesis FROM investmentthesis WHERE ticker="OTHER" ORDER BY version').fetchall()
    first = apply(connection, donor())
    assert all(m['source_id'] != m['destination_id'] for m in first['mappings'])
    changes = connection.total_changes
    second = apply(connection, donor())
    assert second['inserted_rows'] == 0 and connection.total_changes == changes
    assert all(m['status'] == 'EXACT_NOOP' for m in second['mappings'])
    assert connection.execute('SELECT core_thesis FROM investmentthesis WHERE ticker="OTHER" ORDER BY version').fetchall() == before


def test_existing_definition_mismatch_stops_before_insert():
    connection = database()
    record = donor()['company'][0]
    insert(connection, 'company', dict(record, company_name='Different original'))
    changes = connection.total_changes
    with pytest.raises(ValueError, match='existing_record_mismatch'):
        apply(connection, donor())
    assert connection.total_changes == changes
    assert connection.execute('SELECT count(*) FROM watchlistitem').fetchone() == (0,)


def test_failure_after_first_subject_rolls_back_whole_transaction():
    class FaultConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if sql.startswith('INSERT INTO "investmentthesis"') and parameters[0] == '123456':
                raise sqlite3.IntegrityError('SYNTHETIC')
            return super().execute(sql, parameters)
    connection = database(factory=FaultConnection)
    with pytest.raises(sqlite3.IntegrityError, match='SYNTHETIC'):
        apply(connection, donor())
    assert not connection.in_transaction
    assert all(connection.execute(f'SELECT count(*) FROM "{table}"').fetchone() == (0,) for table in MODELS)


def test_existing_trigger_cannot_modify_other_rows_or_tables():
    connection = database()
    connection.execute('CREATE TRIGGER unknown_target_trigger AFTER INSERT ON watchlistitem BEGIN UPDATE company SET company_name="SIDE_EFFECT"; END')
    with pytest.raises(ValueError, match='target_triggers_require_review'):
        apply(connection, donor())
    assert all(connection.execute(f'SELECT count(*) FROM "{table}"').fetchone() == (0,) for table in MODELS)


def test_canonical_security_unique_conflict_with_other_subject_stops():
    connection = database()
    original = donor(('OTHER',))['securitymaster'][0]
    insert(connection, 'securitymaster', dict(original, canonical_security_id='security:NEWUS'))
    with pytest.raises(ValueError, match='unique_conflict'):
        apply(connection, donor())
    assert connection.execute('SELECT count(*) FROM watchlistitem').fetchone() == (0,)


def test_extra_version_and_changed_private_thesis_never_overwrite():
    connection = database()
    apply(connection, donor())
    record = donor()['investmentthesis'][0]
    insert(connection, 'investmentthesis', dict(record, id=100, version=6))
    with pytest.raises(ValueError, match='unexpected_existing_version'):
        apply(connection, donor())
    connection.execute('DELETE FROM investmentthesis WHERE id=100')
    changed = donor()
    changed['investmentthesis'][0]['core_thesis'] = 'Changed synthetic definition'
    with pytest.raises(ValueError, match='existing_record_mismatch'):
        apply(connection, changed)
    assert connection.execute('SELECT count(*) FROM investmentthesis').fetchone() == (10,)


def test_default_off_and_caller_transaction_untouched():
    connection = database()
    statements = []
    connection.set_trace_callback(statements.append)
    with pytest.raises(ValueError, match='default_off'):
        apply(connection, donor(), enabled=False)
    assert statements == []
    connection.execute('BEGIN')
    with pytest.raises(ValueError, match='owns_whole_transaction'):
        apply(connection, donor())
    assert connection.in_transaction
    connection.execute('ROLLBACK')


def test_duplicate_or_missing_history_scope_rejected_without_io():
    rows = donor()
    rows['investmentthesis'].append(deepcopy(rows['investmentthesis'][0]))
    with pytest.raises(ValueError, match='source_scope_exceeded'):
        prepare_registration_definitions(rows, subjects=SUBJECTS, max_versions_per_subject=5)
    rows = donor()
    rows['investmentthesis'][4]['status'] = 'superseded'
    with pytest.raises(ValueError, match='active_thesis_history_invalid'):
        prepare_registration_definitions(rows, subjects=SUBJECTS, max_versions_per_subject=5)


def test_import_drops_old_activation_without_changing_user_definition():
    rows = donor()
    rows['watchlistitem'][0].update(active=True, production_eligible=True,
        onboarding_state='ACTIVE', activated_at=AT.isoformat(), first_eligible_session='2026-01-05',
        onboarding_decision_readiness='{"old":"not current authority"}')
    plan = prepare_registration_definitions(rows, subjects=SUBJECTS, max_versions_per_subject=5)
    watch = plan['watchlistitem'][0]
    assert watch['active'] is False and watch['production_eligible'] is False
    assert watch['activated_at'] is None and watch['first_eligible_session'] is None
    assert watch['onboarding_decision_readiness'] == '{}'
    assert [MODELS['investmentthesis'].model_validate(row).model_dump() for row in plan['investmentthesis']] == [
        MODELS['investmentthesis'].model_validate(row).model_dump() for row in donor()['investmentthesis']]


def test_original_onboarding_background_only_and_source_cycle_gate(tmp_path):
    from tests.test_onboarding_reconciler_service import (
        _engine, _seed_pending, _evidence_builder, _decision_builder,
    )
    from app.services.onboarding_reconciler_service import resume_onboarding_subject, OnboardingAttemptMode
    from app.services.unified_persisted_projection import project_local_seed
    from app.services.unified_source_policy import UnifiedSourcePolicy
    engine = _engine()
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    calls = []

    def decision(*args, **kwargs):
        calls.append('SYNTHETIC_MODEL_SUBSTITUTE')
        return _decision_builder(*args, **kwargs)

    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker='NEWPATH', exchange='NASDAQ')
        common = dict(origin='C22AG_SYNTHETIC', as_of=now, data_dir=tmp_path,
            evidence_builder=_evidence_builder, decision_builder=decision)
        immediate = asyncio.run(resume_onboarding_subject(session, item,
            mode=OnboardingAttemptMode.IMMEDIATE, **common))
        assert not immediate.active and 'DECISION_READINESS' in immediate.remaining_blockers and calls == []
        background = asyncio.run(resume_onboarding_subject(session, item,
            mode=OnboardingAttemptMode.BACKGROUND, **common))
        assert background.active and background.production_eligible and len(calls) == 1
        assert item.first_eligible_session is not None
        # A real writer-produced activation date is not erased to admit Source.
        from app.services.prospective_class_c_owner import completed_clock
        cutoff = now + timedelta(days=7)
        source = project_local_seed(session, market='us', cutoff=cutoff,
            session_key=completed_clock('us', cutoff)['target'],
            policy=UnifiedSourcePolicy(frozenset({'canonical_local'})))
        assert any(row['reason'] == 'first_eligible_cycle_to_session_authority_required' for row in source['denials'])
        assert item.first_eligible_session is not None
