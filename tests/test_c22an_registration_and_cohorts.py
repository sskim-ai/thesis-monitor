"""New C22AN boundaries only; all rows, clocks and approvals are synthetic."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.services.registration_definition_import import import_registration_definitions
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_c22ag_registration_recovery import database, donor, insert

SUBJECTS = tuple(t for market in ('kr', 'us') for t in UNIVERSE[market])


def test_oversized_original_capture_rolls_back_and_stops_both_windows(tmp_path, monkeypatch):
    from app.services import selected_source_registration as registration
    from tests.test_minimal_class_c_export import POLICY

    campaign = synthetic_campaign(tmp_path, monkeypatch)
    campaign.now[0] = datetime(2026, 11, 12, 16, 10,
        tzinfo=ZoneInfo('Asia/Seoul')).astimezone(timezone.utc)
    with sqlite3.connect(campaign.permission.database) as db:
        db.execute('UPDATE watchlistitem SET notes=? WHERE ticker=?',
            ('S' * (9 * 1024 * 1024), '005930'))
    operations, closed = [], []

    class ObservedConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            operations.append(sql.split()[0])
            return super().execute(sql, parameters)

        def close(self):
            closed.append(dict(total_changes=self.total_changes,
                in_transaction=self.in_transaction))
            return super().close()

    def connect(*args, **kwargs):
        return sqlite3.connect(*args, factory=ObservedConnection, **kwargs)

    kwargs = dict(settings=SimpleNamespace(database_url='sqlite:///' +
        str(campaign.permission.database)), runtime_directory=tmp_path,
        approval=campaign.approval, policy=POLICY, ledger=campaign.ledger,
        enabled=True, connect=connect)
    with pytest.raises(ValueError, match='class_c_private_export_size_limit'):
        registration.capture_approved_markets(generations={'kr': 'SYNTHETIC_kr'}, **kwargs)
    assert operations.count('SELECT') == 5
    assert operations[-1] == 'ROLLBACK'
    assert closed == [dict(total_changes=0, in_transaction=False)]
    state = campaign.ledger.state()
    assert state['state'] == 'STOPPED_NO_SEND'
    assert not state['registrations'] and state['http_total'] == state['model_total'] == 0
    previous_operations = list(operations)
    campaign.now[0] = datetime(2026, 11, 13, 8, 10,
        tzinfo=ZoneInfo('Asia/Seoul')).astimezone(timezone.utc)
    with pytest.raises(ValueError):
        registration.capture_approved_markets(generations={'us': 'SYNTHETIC_us'}, **kwargs)
    assert operations == previous_operations
    record('oversized_original_capture', dict(original_private_limit_bytes=8 * 1024 * 1024,
        synthetic_cell_bytes=9 * 1024 * 1024, SELECT=5, ROLLBACK=1,
        source_database_changes=0, future_window_denied_before_connection=True,
        owner_issued=False, limit_unchanged=True, stop_not_cleared=True))


def record(name, value):
    root = Path(os.environ['C22AN_PROBE_ROOT'])
    root.mkdir(parents=True, exist_ok=True)
    with (root / (name + '.json')).open('x') as stream:
        json.dump(dict(provenance='SYNTHETIC_NOT_LIVE_AUTHORITY', operating_DB=0,
                       financial_HTTP=0, model_calls=0, **value), stream, indent=2, default=str)


def apply(connection, rows, **kwargs):
    return import_registration_definitions(connection, rows, subjects=SUBJECTS,
        max_versions_per_subject=5, enabled=True, missing_subjects_only=True, **kwargs)


def snapshot(connection):
    return {table: connection.execute(f'SELECT * FROM "{table}" ORDER BY id').fetchall()
            for table in donor()}


def test_missing_twenty_preserves_active_two_and_outside_then_no_refill():
    assert len(SUBJECTS) == len(set(SUBJECTS)) == 22
    assert not set(SUBJECTS) & {'010140', '272210', '016360', 'META', 'JOBY', 'MRVL'}
    rows, connection = donor(SUBJECTS), database()
    outside = donor(('OTHER',))
    for table, values in outside.items():
        for value in values:
            insert(connection, table, value)
    outside_before = snapshot(connection)
    active = ('MU', '005930')
    original = {table: [row for row in values if row['ticker'] in active]
                for table, values in rows.items()}
    import_registration_definitions(connection, original, subjects=active,
        max_versions_per_subject=5, enabled=True)
    connection.execute("UPDATE watchlistitem SET active=1,production_eligible=1,onboarding_state='ACTIVE',first_eligible_session='2026-11-13',onboarding_decision_readiness='accepted-original' WHERE ticker IN ('MU','005930')")
    connection.execute("UPDATE securitymaster SET identity_quality='verified',identity_provider='sec_edgar',updated_at='2026-11-12T02:00:00+00:00' WHERE ticker IN ('MU','005930')")
    connection.execute("UPDATE company SET industry='Original accepted enrichment' WHERE ticker IN ('MU','005930')")
    before = {table: connection.execute(f'SELECT * FROM "{table}" WHERE ticker IN (?,?) ORDER BY id', active).fetchall()
              for table in rows}
    result = apply(connection, rows)
    assert result['inserted_rows'] == 20 * 8 and result['conflicts'] == []
    assert {r['ticker'] for r in result['reconciliation'] if r['status'] == 'PRESERVED_EXISTING_NOOP'} == set(active)
    for table in rows:
        assert connection.execute(f'SELECT * FROM "{table}" WHERE ticker IN (?,?) ORDER BY id', active).fetchall() == before[table]
        assert connection.execute(f'SELECT * FROM "{table}" WHERE ticker="OTHER" ORDER BY id').fetchall() == outside_before[table]
    assert connection.execute('SELECT count(*) FROM investmentthesis').fetchone() == (115,)
    changes = connection.total_changes
    repeated = apply(connection, rows)
    assert repeated['inserted_rows'] == 0 and connection.total_changes == changes
    assert not result['activation_granted'] and not result['source_or_economic_grant']
    assert 'Synthetic private' not in json.dumps(result)
    record('missing_twenty', dict(roster=UNIVERSE, inserted=160, active_two_unchanged=True,
        excluded_six_untouched=True, outside_unchanged=True, repeat_inserted=0, private_text_exported=False))


def test_conflicts_are_subject_local_and_never_filled_or_overwritten():
    rows, connection = donor(SUBJECTS), database()
    insert(connection, 'company', rows['company'][0])
    complete = {table: [r for r in values if r['ticker'] == 'MU'] for table, values in rows.items()}
    import_registration_definitions(connection, complete, subjects=('MU',), max_versions_per_subject=5, enabled=True)
    connection.execute("UPDATE investmentthesis SET core_thesis='Live private change' WHERE ticker='MU' AND version=1")
    preserved = {table: connection.execute(f'SELECT * FROM "{table}" WHERE ticker IN (?,?) ORDER BY id', ('000660', 'MU')).fetchall()
                 for table in rows}
    result = apply(connection, rows)
    assert set(result['conflicts']) == {'000660', 'MU'} and result['inserted_rows'] == 20 * 8
    for table in rows:
        assert connection.execute(f'SELECT * FROM "{table}" WHERE ticker IN (?,?) ORDER BY id', ('000660', 'MU')).fetchall() == preserved[table]
    assert 'Live private' not in json.dumps(result)
    record('conflicts', dict(subjects=result['conflicts'], partial_subject_not_filled=True,
        thesis_not_overwritten=True, other_missing_imported=20, private_text_exported=False))


def test_missing_import_failure_rolls_back_and_default_strict_path_survives():
    class Fault(sqlite3.Connection):
        def execute(self, statement, parameters=()):
            if statement.startswith('INSERT INTO "investmentthesis"') and parameters[0] == 'MU':
                raise sqlite3.IntegrityError('SYNTHETIC_INSERT_FAILURE')
            return super().execute(statement, parameters)
    connection = database(factory=Fault)
    with pytest.raises(sqlite3.IntegrityError, match='SYNTHETIC'):
        apply(connection, donor(SUBJECTS))
    assert not connection.in_transaction
    assert all(connection.execute(f'SELECT count(*) FROM "{table}"').fetchone() == (0,) for table in donor())
    connection = database()
    rows = donor(('MU',))
    import_registration_definitions(connection, rows, subjects=('MU',), max_versions_per_subject=5, enabled=True)
    connection.execute("UPDATE watchlistitem SET active=1,production_eligible=1")
    with pytest.raises(ValueError, match='existing_record_mismatch'):
        import_registration_definitions(connection, rows, subjects=('MU',), max_versions_per_subject=5, enabled=True)
    assert not connection.in_transaction
    record('atomic_and_strict', dict(failed_insert_fully_rolled_back=True, original_strict_mode_unchanged=True))


def test_activation_cutoffs_keep_kst_cycle_separate_from_exchange_close():
    from app.services.onboarding_reconciler_service import _next_cycle_date
    from app.services.prospective_class_c_owner import completed_clock
    zone = ZoneInfo('Asia/Seoul')
    results = []
    for market, hour, minute in (('kr',16,5), ('us',8,5)):
        at = datetime(2026,11,12,hour,minute,tzinfo=zone)
        before = _next_cycle_date(market,at-timedelta(microseconds=1))
        after = _next_cycle_date(market,at+timedelta(microseconds=1))
        assert before.isoformat()=='2026-11-12' and after.isoformat()=='2026-11-13'
        results.append(dict(market=market,before=str(before),after=str(after)))
    clocks = {}
    for label, at in (
            ('kr_today',datetime(2026,11,12,16,10,tzinfo=zone)),
            ('us_tomorrow',datetime(2026,11,13,8,10,tzinfo=zone)),
            ('us_weekend',datetime(2026,11,15,8,10,tzinfo=zone)),
            ('us_thanksgiving',datetime(2026,11,27,8,10,tzinfo=zone))):
        clocks[label] = {m:completed_clock(m,at) for m in ('kr','us')}
    assert clocks['kr_today']['kr']['target']=='2026-11-12'
    assert clocks['kr_today']['us']['target']=='2026-11-11'
    assert clocks['us_tomorrow']['us']['target']=='2026-11-12'
    assert clocks['us_tomorrow']['kr']['target']=='2026-11-12'
    assert clocks['us_weekend']['us']['target']=='2026-11-13'
    assert clocks['us_thanksgiving']['us']['target']=='2026-11-25'
    record('cycles',dict(cutoffs=results,calendars=clocks,actual_system_clock_changed=False))


def synthetic_campaign(tmp_path,monkeypatch):
    from app.services import prospective_class_c_owner as prospective
    from app.services import minimal_class_c_export as exporter
    from app.services import selected_run_lifecycle as lifecycle
    from app.services import campaign_runtime_cap as caps
    from app.services.unified_snapshot_contract import digest
    from tests.test_minimal_class_c_export import database as fixture_database
    now = [datetime(2026,11,12,13,0,tzinfo=ZoneInfo('Asia/Seoul')).astimezone(timezone.utc)]
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):
            return now[0].astimezone(tz) if tz else now[0].replace(tzinfo=None)
    monkeypatch.setattr(prospective,'_now',lambda:now[0])
    for module in (exporter,lifecycle,caps):
        monkeypatch.setattr(module,'datetime',Clock)
    permission = fixture_database(tmp_path,[(t,m) for m,ts in UNIVERSE.items() for t in ts])
    with sqlite3.connect(permission.database) as db:
        db.execute("UPDATE watchlistitem SET first_eligible_session=CASE WHEN exchange='NASDAQ' THEN '2026-11-13' ELSE '2026-11-12' END")
        for i,ticker in enumerate(SUBJECTS,1):
            db.execute('UPDATE securitymaster SET cik=?,corp_code=? WHERE ticker=?',
                (str(100000+i) if not ticker.isdigit() else None,
                 str(10000000+i) if ticker.isdigit() else None,ticker))
            for table in ('watchlistitem','securitymaster','company'):
                db.execute(f'UPDATE "{table}" SET company_name=? WHERE ticker=?',('Synthetic '+ticker,ticker))
    decision = prospective.ApprovalDecision(event_id=permission.event_id,approved=True,
        user_message_sha256=digest('SYNTHETIC_NOT_A_LIVE_USER_APPROVAL'), effective_at=now[0],
        expires_at=now[0]+timedelta(hours=24),subjects=SUBJECTS)
    approval = prospective.record_backend_approval(decision)
    ledger = lifecycle.SelectedRunLedger(path=tmp_path/'campaign.jsonl',approval=approval,
        master_id='C22AN_SYNTHETIC_MASTER',children={m:dict(generation='SYNTHETIC_'+m,subjects=list(ts)) for m,ts in UNIVERSE.items()},
        provider_caps={'sec_edgar':3},max_http=3,max_models=88,
        database_identity=dict(path=str(permission.database),device=permission.device,inode=permission.inode),
        onboarding=True,onboarding_subjects={m:[t for t in ts if t not in ('MU','005930')] for m,ts in UNIVERSE.items()},
        staged_markets=True,runtime_cap=dict(stop_on_first_external_failure=True,endpoints={
            'sec_edgar':[dict(host='synthetic.invalid',prefix='/data/',endpoint='TEST',methods=['GET'])]}))
    return SimpleNamespace(now=now,approval=approval,ledger=ledger,permission=permission)


@pytest.mark.parametrize('market,count',[('kr',1),('kr',4),('kr',8),('us',1),('us',7),('us',14)])
def test_partial_original_owner_seed_source_plan_and_dynamic_models(tmp_path,monkeypatch,market,count):
    from app.services import selected_source_registration as registration
    from app.services.prospective_class_c_owner import _state, require_generation
    from app.services.selected_source_context import freeze_registered_child
    from app.services.selected_source_plan import SelectedConsumerPolicy
    from app.services.model_execution_plan import CohortSubject,FrozenCohort,compile_model_plan
    from app.services.unified_snapshot_contract import digest
    from tests.test_minimal_class_c_export import POLICY
    campaign = synthetic_campaign(tmp_path,monkeypatch)
    zone=ZoneInfo('Asia/Seoul')
    at=datetime(2026,11,12,16,10,tzinfo=zone) if market=='kr' else datetime(2026,11,13,8,10,tzinfo=zone)
    campaign.now[0]=at.astimezone(timezone.utc)
    eligible=tuple(UNIVERSE[market][:count])
    with sqlite3.connect(campaign.permission.database) as db:
        excluded=set(UNIVERSE[market])-set(eligible)
        for ticker in excluded:
            db.execute("UPDATE watchlistitem SET active=0,production_eligible=0,onboarding_state='PENDING_ONBOARDING' WHERE ticker=?",(ticker,))
    capture,owners,receipt=registration.capture_approved_markets(
        settings=SimpleNamespace(database_url='sqlite:///'+str(campaign.permission.database)),runtime_directory=tmp_path,
        approval=campaign.approval,generations={market:'SYNTHETIC_'+market},policy=POLICY,
        ledger=campaign.ledger,enabled=True,audit_path=tmp_path/'eligibility.json')
    assert set(owners)=={market} and set(_state(owners[market])[1]['bindings'])==set(eligible)
    assert campaign.ledger.selected_child(market)['subjects']==sorted(eligible)
    configs={p:digest(p) for p in ('kiwoom','sec_edgar','opendart','fred','eia','ecos','krx_night_futures',
        'finnhub','google_news_rss','naver_news')}
    frozen,_,_,local=freeze_registered_child(registration_owner=owners[market],policy=POLICY,code_sha='a'*40,
        native=None,native_owner_root=tmp_path/'not-installed',config_identities=configs,
        configured_kr_pages=20,listing_rows=[],kis_static_hashes={},
        completed_close_documentation={'path':'SYNTHETIC','sha256':'a'*64},
        consumer_policy=SelectedConsumerPolicy(),master_id='C22AN_SYNTHETIC_MASTER',
        ohlcv_source_url='https://synthetic.invalid/ohlcv',enabled=True,run_ledger=campaign.ledger)
    assert len(frozen['stock_plan']['reads'])==4*count and not local['denials']
    assert set(r['subject'] for r in frozen['stock_plan']['reads'])==set(eligible)
    cohort=FrozenCohort('SYNTHETIC_'+market,'SYNTHETIC_'+market,frozen['sessions'][market],at.isoformat(),at.isoformat(),
        tuple(CohortSubject(market,t,'security:'+t,at.isoformat(),digest(t)) for t in eligible),
        ((market,digest(market)),),digest('PLANNING_ONLY'))
    plan=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    assert len(plan.slots)==1+3*((count+2)//3)+count
    with pytest.raises(ValueError):cohort.verify_source_owner(None)
    with pytest.raises(ValueError):require_generation(owners[market],'SYNTHETIC_FOREIGN')
    audit=json.loads((tmp_path/'eligibility.json').read_bytes())
    assert len(audit['subjects'])==22
    record('subset_'+market+'_'+str(count),dict(eligible=list(eligible),original_owner_seed=True,
        original_source_plan_reads=4*count,model_slots=len(plan.slots),source_dispatch=False,
        source_plan_planning_only=True,full_market_owner_and_renderer_proved=False,excluded=len(excluded)))


def test_one_approval_staged_freshness_shared_caps_and_persistent_calls(tmp_path,monkeypatch):
    from app.services import prospective_class_c_owner as prospective
    from app.services import selected_source_registration as registration
    from app.services.campaign_runtime_cap import RuntimeCap
    from app.services.selected_run_lifecycle import SelectedRunLedger
    from app.services.unified_snapshot_contract import digest
    from tests.test_minimal_class_c_export import POLICY
    campaign=synthetic_campaign(tmp_path,monkeypatch)
    ledger=campaign.ledger
    for market,ts in UNIVERSE.items():
        for ticker in ts:
            if ticker in ('MU','005930'):
                with pytest.raises(ValueError):ledger.before_onboarding_model(market=market,ticker=ticker,stage='CORE',payload_sha256=digest('x'))
                continue
            for stage in ('CORE','DECISION'):
                key=ledger.before_onboarding_model(market=market,ticker=ticker,stage=stage,payload_sha256=digest('x'))
                ledger.onboarding_model_result(key,ok=True,output_sha256=digest(key))
    assert ledger.state()['model_total']==40
    key=ledger.before_onboarding_model
    with pytest.raises(ValueError):key(market='kr',ticker='000660',stage='CORE',payload_sha256=digest('x'))
    zone=ZoneInfo('Asia/Seoul')
    owners={}
    for market,at in (('kr',datetime(2026,11,12,16,10,tzinfo=zone)),('us',datetime(2026,11,13,8,10,tzinfo=zone))):
        campaign.now[0]=at.astimezone(timezone.utc)
        capture,current,receipt=registration.capture_approved_markets(
            settings=SimpleNamespace(database_url='sqlite:///'+str(campaign.permission.database)),runtime_directory=tmp_path,
            approval=campaign.approval,generations={market:'SYNTHETIC_'+market},policy=POLICY,ledger=ledger,enabled=True)
        owners[market]=current[market]
        # These are ledger transition units, not Source/Cold/model/renderer acceptance.
        ledger._event('PLAN',market=market,sha256=digest(market))
        ledger._event('CAPTURE',market=market)
        ledger._event('SOURCE',market=market,sha256=digest('SYNTHETIC_SOURCE'))
        ledger._event('MODEL_PLAN',market=market,sha256=digest('SYNTHETIC_PLAN'+market),slots=1,slot_ids=[market])
        cap=RuntimeCap(ledger.worker_binding())
        request=dict(provider='sec_edgar',method='GET',host='synthetic.invalid',path='/data/'+market,
            market=market,subject=UNIVERSE[market][0],phase='SOURCE',owner='Synthetic',request_sha256=digest(market))
        reserved=cap.reserve(**request)
        cap.dispatched(reserved);cap.finish(reserved,status=200)
        model_key='MODEL:SYNTHETIC_'+market
        ledger._event('INTENT',key=model_key,kind='MODEL',market=market,slot=market,plan=digest('SYNTHETIC_PLAN'+market))
        ledger.result(model_key,ok=True)
        ledger._event('RENDER_MARKET',market=market,result_sha256=digest('SYNTHETIC_TERMINAL'))
        if market=='kr':
            campaign.now[0]+=timedelta(hours=2)
            with pytest.raises(ValueError,match='expired'):prospective._state(owners['kr'])
            with pytest.raises(ValueError,match='EXPIRED'):cap.reserve(**dict(request,request_sha256=digest('new')))
            with pytest.raises(ValueError,match='current_capture'):
                prospective.issue_prospective_owner(approval=campaign.approval,capture=capture,
                    market='us',source_generation_id='FOREIGN',generation_id='FOREIGN',policy=POLICY)
    state=ledger.state()
    assert state['db_connection_attempts']==2 and state['db_select_actual']==10
    assert state['model_total']==42 and state['http_total']==2 and state['state']=='RENDERED_NO_SEND'
    restored=SelectedRunLedger.attach_worker(dict(path=str(ledger.path),identity_sha256=digest(ledger.identity)))
    assert restored.state()['model_total']==42
    assert RuntimeCap(restored.worker_binding()).state()['terminal']
    with pytest.raises(ValueError):RuntimeCap(restored.worker_binding()).reserve(**dict(request,request_sha256=digest('third')))
    campaign.now[0]=datetime(2026,11,13,13,0,tzinfo=zone).astimezone(timezone.utc)
    with pytest.raises(ValueError,match='approval_expired'):prospective._approval(campaign.approval)
    record('staged_shared_ledger',dict(one_user_approval=True,fresh_captures=2,old_capture_rejected=True,
        old_owner_expired=True,actual_db_test_SELECT=10,synthetic_onboarding_intents=40,
        protected_two_intents=0,synthetic_monitoring_intents=2,persistent_no_refill=True,
        unit_transition_only=True,original_full_source_or_renderer_acceptance=False))


def test_staged_unknown_sender_blocks_cold_spending_and_finite_caps(tmp_path,monkeypatch):
    from app.services.campaign_runtime_cap import RuntimeCap
    from app.services.unified_snapshot_contract import digest
    campaign=synthetic_campaign(tmp_path,monkeypatch)
    cap=RuntimeCap(campaign.ledger.worker_binding())
    request=dict(provider='sec_edgar',method='GET',host='synthetic.invalid',path='/data/one',
        market='kr',subject='000660',phase='ONBOARDING',owner='Synthetic',request_sha256=digest('one'))
    first=cap.reserve(**request)
    cap.dispatched(first)
    cold=RuntimeCap(campaign.ledger.worker_binding())
    with pytest.raises(ValueError,match='CAP_EXHAUSTED'):
        cold.reserve(**dict(request,request_sha256=digest('two')))
    with pytest.raises(ValueError,match='external_failure'):
        campaign.ledger.before_onboarding_model(market='kr',ticker='000660',stage='CORE',payload_sha256=digest('test'))
    assert cold.state()['total']==1
    cold.finish(first,status=200)
    for i in (2,3):
        key=cold.reserve(**dict(request,request_sha256=digest(str(i))))
        cold.dispatched(key);cold.finish(key,status=200)
    with pytest.raises(ValueError):cold.reserve(**dict(request,request_sha256=digest('four')))
    assert cold.state()['total']==3
    record('unknown_and_caps',dict(unknown_sender_cold_block=True,prior_intent_preserved=True,
        max_physical=3,synthetic_intents=3,real_HTTP=0))


def test_original_writer_uses_completion_clock_not_model_start_for_first_cycle(tmp_path):
    import asyncio
    from sqlmodel import Session
    from app.services.onboarding_reconciler_service import resume_onboarding_subject,OnboardingAttemptMode
    from tests.test_onboarding_reconciler_service import _engine,_seed_pending,_evidence_builder,_decision_builder
    zone=ZoneInfo('Asia/Seoul')
    rows=[]
    for ticker,market,hour in (('SYNTHUS','us',8),('123456','kr',16)):
        for minute in (4,6):
            engine=_engine()
            started=datetime(2026,11,12,hour,0,tzinfo=zone)
            completed=started.replace(minute=minute)
            with Session(engine) as session:
                root=tmp_path/(ticker+str(minute))
                item=_seed_pending(session,root,ticker=ticker,exchange='NASDAQ' if market=='us' else 'KOSPI')
                result=asyncio.run(resume_onboarding_subject(session,item,origin='SYNTHETIC_C22AN',
                    mode=OnboardingAttemptMode.BACKGROUND,as_of=started,data_dir=root,
                    evidence_builder=_evidence_builder,decision_builder=_decision_builder,
                    activation_clock=lambda:completed))
                assert result.active
                expected='2026-11-12' if minute<5 else '2026-11-13'
                assert str(item.first_eligible_session)==expected
                rows.append(dict(market=market,started=started.isoformat(),completed=completed.isoformat(),
                    first_cycle=str(item.first_eligible_session)))
            engine.dispose()
    record('actual_writer_completion_clock',dict(cases=rows,source_or_economic_authority=False))


def test_local_market_failure_preserves_costs_and_does_not_clear_hard_stop(tmp_path,monkeypatch):
    from app.services.selected_source_registration import capture_approved_markets
    from app.services.campaign_runtime_cap import RuntimeCap
    from tests.test_minimal_class_c_export import POLICY
    campaign=synthetic_campaign(tmp_path,monkeypatch)
    ledger=campaign.ledger
    zone=ZoneInfo('Asia/Seoul')
    for market,at in (('kr',datetime(2026,11,12,16,10,tzinfo=zone)),('us',datetime(2026,11,13,8,10,tzinfo=zone))):
        campaign.now[0]=at.astimezone(timezone.utc)
        capture_approved_markets(settings=SimpleNamespace(database_url='sqlite:///'+str(campaign.permission.database)),
            runtime_directory=tmp_path,approval=campaign.approval,generations={market:'SYNTHETIC_'+market},
            policy=POLICY,ledger=ledger,enabled=True)
        if market=='kr':
            ledger.market_failed(market,'SYNTHETIC_DATA_QUALITY')
            assert ledger.state()['state']=='APPROVED_FROZEN_RUN'
        else:
            ledger.stop('SYNTHETIC_ACCOUNT_STOP')
            with pytest.raises(ValueError):ledger.market_failed(market,'MUST_NOT_CLEAR_STOP')
    assert ledger.state()['db_select_actual']==10 and ledger.state()['state']=='STOPPED_NO_SEND'
    assert list(ledger.state()['failed_markets'])==['kr']
    assert RuntimeCap(dict(path=str(ledger.path),identity_sha256=__import__('app.services.unified_snapshot_contract',fromlist=['digest']).digest(ledger.identity))).state()['terminal']
    record('local_market_failure',dict(fresh_captures=2,local_failure_not_PASS=True,hard_stop_preserved=True))


def test_native_explicit_settings_are_pinned_and_default_unchanged(tmp_path,monkeypatch):
    from scripts import unified_stock_source_worker as worker
    root=tmp_path/'code'
    root.mkdir()
    settings_file=tmp_path/'existing-settings.env'
    settings_file.write_text('DUMMY_ONLY=1\n')
    settings=SimpleNamespace(model_dump=lambda **kw:{'dummy':'MASKED'},kiwoom_base_url='https://api.kiwoom.com',
        enable_live_provider=True,kiwoom_env='real',kiwoom_max_retries=0,kiwoom_timeout_seconds=1,
        kiwoom_app_key='DUMMY_NOT_A_KEY',kiwoom_secret_key='DUMMY_NOT_A_SECRET')
    def git(args,**kw):
        return 'a'*40 if args[1]=='rev-parse' else ''
    monkeypatch.setattr(worker.subprocess,'check_output',git)
    before=worker.owner_configuration(root,settings)
    assert 'settings_env_file' not in before
    declared=worker.owner_configuration(root,settings,settings_env_file=settings_file)
    assert declared==dict(before,settings_env_file=str(settings_file))
    assert worker.settings_path(root)==root/'.env'
    assert worker.settings_path(root,settings_file)==settings_file
    alias=tmp_path/'alias'
    alias.symlink_to(settings_file)
    for bad in (alias,Path('relative.env'),tmp_path/'missing'):
        with pytest.raises(ValueError):worker.settings_path(root,bad)
    record('native_settings_binding',dict(original_default_unchanged=True,explicit_file_pinned=True,
        symlink_relative_missing_rejected=True,live_credentials_read=False))


def test_market_terminal_cannot_be_serialized_fake_child(tmp_path,monkeypatch):
    campaign=synthetic_campaign(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='original_market_child_required'):
        campaign.ledger.rendered_market(SimpleNamespace(market='kr',binding=lambda:{}),{})


def test_retained_submissions_profile_keeps_ticker_cik_and_sic_checks():
    from app.services.company_profile_service import SecCompanyProfileSource
    item=SimpleNamespace(ticker='SYNTH',company_name='Synthetic')
    raw=dict(cik='123',tickers=['SYNTH'],sic='3571',name='Synthetic legal',
        filings={'recent':{'filingDate':['2026-11-11']}})
    result=SecCompanyProfileSource.from_submissions(item,raw,cik='0000000123')
    assert result.cik=='0000000123' and result.source_as_of=='2026-11-11'
    for changed in (dict(cik='124'),dict(tickers=['OTHER']),dict(sic='')):
        assert SecCompanyProfileSource.from_submissions(item,{**raw,**changed},cik='123') is None


def test_collection_seal_accepts_selected_schema_but_not_missing_receipts(tmp_path,monkeypatch):
    from tests.test_c22ab_selected_source import compile_market
    from app.services import production_source_seal as seal
    compiled,_,_=compile_market('us','SYNTH')
    monkeypatch.setattr(seal,'row_count_proofs',lambda *args:{})
    (tmp_path/'dispatch/receipts').mkdir(parents=True)
    frozen=dict(scope='SELECTED_ORIGINAL_RESEARCH_V1',plan=compiled['plan'].model_dump(mode='json'))
    result=seal.slot_dispositions(tmp_path,frozen,{})
    assert result['status']=='FAIL' and result['counts']['MISSING_REQUIRED_ATTEMPT']>0
    frozen['plan']['subjects']=['OTHER']
    with pytest.raises(ValueError):seal.slot_dispositions(tmp_path,frozen,{})


def test_kis_worker_uses_current_subset_not_approved_roster(tmp_path,monkeypatch):
    from tests.test_c22ab_selected_source import compile_market
    from app.jobs import production_kis_worker as worker
    from app.services.selected_run_lifecycle import SelectedRunLedger
    from app.services.unified_snapshot_contract import digest
    import hashlib
    compiled,_,kis=compile_market('kr','123456')
    plan=compiled['plan']
    frozen=dict(scope='SELECTED_ORIGINAL_RESEARCH_V1',generation_id=plan.generation_id,
        plan=plan.model_dump(mode='json'),shared_run_ledger={'SYNTHETIC':'NOT_AUTHORITY'})
    raw=json.dumps(frozen).encode()
    (tmp_path/'production-frozen-source-plan.json').write_bytes(raw)
    (tmp_path/'kis-plan.json').write_text(json.dumps(kis))
    (tmp_path/'acquisition-outcome.json').write_text('{}')
    monkeypatch.setattr(worker,'current_inventories',lambda *args:{})
    subset={'generation':plan.generation_id,'subjects':['123456']}
    ledger=SimpleNamespace(identity={'staged_markets':True,'children':{'kr':{'subjects':list(UNIVERSE['kr'])}}},
        selected_child=lambda market:subset,state=lambda:{'plans':{'kr':plan.plan_sha256}})
    monkeypatch.setattr(SelectedRunLedger,'attach_worker',lambda binding:ledger)
    monkeypatch.setattr(worker.kis,'acquire',lambda *a,**kw:'SYNTHETIC_NOT_SOURCE_PASS')
    def frame():return dict(contract='production-kis-worker-authorization-v1',root=str(tmp_path),
        frozen_sha256=hashlib.sha256(raw).hexdigest(),plan_sha256=digest(kis),seconds_remaining=1,
        credentials={'app_key':'DUMMY_ONLY','app_secret':'DUMMY_ONLY'})
    assert worker.run(frame())=='SYNTHETIC_NOT_SOURCE_PASS'
    subset['subjects']=['654321']
    with pytest.raises(ValueError,match='shared_scope_changed'):worker.run(frame())


@pytest.mark.parametrize('ticker',['CPNG','IBM','TSM'])
def test_dated_reference_replays_existing_isolated_row_policy_not_new_price_rights(ticker):
    import hashlib
    from app.services.dated_chart_reference import _derive,validate_reference
    from app.services.dated_bar_admission import admit_rows
    from app.services.ohlcv_client import OhlcvClient
    root=Path(__file__).resolve().parents[3]/'maintenance/20261109-c22a/derived'/ticker/'daily'
    receipt=json.loads((root/'receipt.json').read_bytes())
    raw=(root/'response.body').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==receipt['body_sha256']
    cutoff=__import__('datetime').date.fromisoformat(receipt['actual_historical_as_of'])
    proof=dict(response_body=raw.decode(),observed_at=receipt['observed_at'],analysis_cutoff=cutoff.isoformat())
    reference,native=_derive(proof=proof,ticker=ticker,market='us')
    bars,_,_=OhlcvClient._decode_period_payload(json.loads(raw),ticker=ticker,period='daily',adjusted=True,
        response_body_sha256=receipt['body_sha256'])
    accepted,qa=admit_rows(bars,ticker=ticker,market='us',timeframe='daily',cutoff=cutoff)
    assert qa['excluded']==1 and all(r['date']!=qa['bad_date'] for r in native.periods['daily'].rows)
    assert native.periods['daily'].status=='AVAILABLE' and reference['reference_date']<=str(cutoff)
    assert reference['source_response_sha256']==receipt['body_sha256']
    assert reference['allowed_use']==['ONBOARDING_TECHNICAL','PRICE_LOCATION']
    assert validate_reference(reference,proof,ticker=ticker,market='us')==reference
    damaged=[dict(r) for r in accepted]
    damaged[-2]=dict(damaged[-2],high=0)
    with pytest.raises(ValueError):admit_rows(damaged,ticker=ticker,market='us',timeframe='daily',cutoff=cutoff)
    with pytest.raises(ValueError):validate_reference(reference,proof,ticker='OTHER',market='us')
    with pytest.raises(ValueError):_derive(proof={**proof,'analysis_cutoff':'2099-01-01'},ticker=ticker,market='us')


def test_dated_full_onboarding_context_reuses_native_values_without_current_price(monkeypatch):
    import asyncio,sys
    root=Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root/'maintenance/20261112-c22an-v1'))
    from retained_inputs import RetainedPrice
    from app.services.dated_chart_reference import technical_context_from_references
    client=RetainedPrice('CPNG')
    price=asyncio.run(client.fetch_price_context('CPNG',as_of=datetime(2026,11,12,6,tzinfo=timezone.utc)))
    assert price.decision.current_price is None
    assert price.dated_reference_price['reference_date']=='2026-11-05'
    evidence=dict(as_of='2026-11-12T06:00:00+00:00',dated_reference_price=price.dated_reference_price,
        dated_reference_evidence=price.dated_reference_evidence)
    context=technical_context_from_references(evidence,ticker='CPNG',market='us',period_sources=client.period_sources)
    assert context.ticker=='CPNG' and context.market=='us'


def test_original_capture_can_narrow_current_eligible_scope_without_refill_or_new_grants(tmp_path,monkeypatch):
    from app.services import prospective_class_c_owner as original
    from app.services import selected_source_registration as selected
    from app.services.minimal_class_c_export import captured_private_snapshot
    from app.services.unified_snapshot_contract import digest
    from tests.test_minimal_class_c_export import POLICY
    campaign=synthetic_campaign(tmp_path,monkeypatch)
    campaign.now[0]=datetime(2026,11,13,8,10,tzinfo=ZoneInfo('Asia/Seoul')).astimezone(timezone.utc)
    with sqlite3.connect(campaign.permission.database) as db:
        db.execute("UPDATE watchlistitem SET active=0,production_eligible=0,onboarding_state='PENDING_ONBOARDING' WHERE ticker='WULF'")
    capture,owners,receipt=selected.capture_approved_markets(
        settings=SimpleNamespace(database_url='sqlite:///'+str(campaign.permission.database)),runtime_directory=tmp_path,
        approval=campaign.approval,generations={'us':'SYNTHETIC_us'},policy=POLICY,ledger=campaign.ledger,enabled=True,
        audit_path=tmp_path/'full-audit.json',subject_limits={'us':3},priority_subjects={'us':('WULF','MU')})
    document,owned=original._state(owners['us'])
    assert set(owned['bindings'])=={'MU','CORZ','CPNG'} and owned['scope']=='MEMBERSHIP_ONLY_NOT_D01_D02'
    assert original.replay_captured_local_seed(owners['us'],policy=POLICY)==document
    raw,full_receipt=captured_private_snapshot(capture)
    assert len(json.loads(raw)['watchlistitem'])==22 and digest(full_receipt)==owned['capture_receipt_sha256']
    audit=json.loads((tmp_path/'full-audit.json').read_bytes())
    assert len(audit['subjects'])==22 and sum(r['canonical_eligible'] and r['detected_market']=='us' for r in audit['subjects'])==13
    from app.services.selected_source_context import freeze_registered_child
    from app.services.selected_source_plan import SelectedConsumerPolicy
    frozen,_,_,local=freeze_registered_child(registration_owner=owners['us'],policy=POLICY,
        code_sha='a'*40,native=None,native_owner_root=tmp_path/'SYNTHETIC',
        config_identities={p:digest(p) for p in ('kiwoom','sec_edgar','opendart','fred','eia','ecos',
            'krx_night_futures','finnhub','google_news_rss','naver_news')},configured_kr_pages=20,
        listing_rows=[],kis_static_hashes={},completed_close_documentation={'path':'SYNTHETIC','sha256':'a'*64},
        consumer_policy=SelectedConsumerPolicy(),master_id='SYNTHETIC_MASTER',
        ohlcv_source_url='https://synthetic.invalid/ohlcv',enabled=True,run_ledger=campaign.ledger)
    assert set(frozen['plan']['subjects'])=={'MU','CORZ','CPNG'} and not local['denials']
    for names in (('META',),('WULF',),('MU','MU')):
        with pytest.raises(ValueError):original.issue_prospective_owner(approval=campaign.approval,capture=capture,
            market='us',source_generation_id='NEGATIVE',generation_id='NEGATIVE',policy=POLICY,subjects=names)
    with pytest.raises(ValueError,match='duplicate_run_source_changed'):
        original.issue_prospective_owner(approval=campaign.approval,capture=capture,market='us',
            source_generation_id='SYNTHETIC_us',generation_id='SYNTHETIC_us',policy=POLICY,subjects=('MU',))
    campaign.now[0]+=timedelta(hours=2)
    with pytest.raises(ValueError,match='expired'):original._state(owners['us'])
    assert campaign.ledger.state()['db_select_actual']==5 and campaign.ledger.state()['http_total']==0
    record('narrow_original_capture',dict(full_capture=22,audit_US_eligible=13,selected=3,
        inactive_not_forced=True,original_row_hashes_and_owner_replay=True,original_TTL_unchanged=True,
        second_capture_or_quota_refill=False,source_or_economic_grants=0))
