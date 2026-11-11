"""Synthetic cost/writer boundaries only. No operating DB, HTTP or model."""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlmodel import Session, create_engine, select
from sqlalchemy import MetaData, text

from app.services import prospective_class_c_owner as approval_module
from app.services.selected_run_lifecycle import SelectedRunLedger, OnboardingCampaignTransport
from app.services.unified_snapshot_contract import digest, encoded
from tests.test_c22ag_registration_recovery import isolated_boundary


def ledger(tmp_path, *, db=None):
    now = datetime.now(timezone.utc)
    approval = approval_module.record_backend_approval(approval_module.ApprovalDecision(
        event_id='C22AH_TEST_NOT_USER_APPROVAL', approved=True,
        user_message_sha256=digest('SYNTHETIC_ONLY'), effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(minutes=30), subjects=('TEST','123456')))
    return SelectedRunLedger(path=tmp_path/'budget.jsonl', approval=approval, master_id='TEST_ONLY',
        children={'us':dict(generation='TEST_US',subjects=['TEST']),
            'kr':dict(generation='TEST_KR',subjects=['123456'])},
        provider_caps={'sec_edgar':4,'opendart':4}, max_http=8, max_models=14,
        database_identity={'memory_only':True}, onboarding=True, database_budget=db)


def wire(journal, market, inner):
    routes = [dict(logical_id='document',method='GET',host='data.sec.gov',
        path_prefix='/submissions/',provider='sec_edgar',maximum_attempts=2)]
    pin = digest(routes)
    journal.bind_onboarding_http_plan(market=market,plan_sha256=pin,
        logical_ids=OnboardingCampaignTransport._ids(routes[0]))
    return OnboardingCampaignTransport(ledger=journal,market=market,plan_sha256=pin,
        routes=routes,inner=inner)


def test_dynamic_documents_charge_before_send_and_cold_duplicate_refusal(tmp_path):
    journal = ledger(tmp_path)
    sent=[]
    def send(request):
        assert journal.state()['pending'] and journal.state()['http_total'] == len(sent)+1
        sent.append(request.url.path)
        return httpx.Response(200,json={})
    transport = wire(journal,'us',httpx.MockTransport(send))
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            await client.get('https://data.sec.gov/submissions/CIK1.json')
            with pytest.raises(ValueError,match='already_attempted'):
                await client.get('https://data.sec.gov/submissions/CIK1.json')
            await client.get('https://data.sec.gov/submissions/CIK2.json')
            with pytest.raises(ValueError,match='exhausted'):
                await client.get('https://data.sec.gov/submissions/CIK3.json')
    asyncio.run(run())
    cold=SelectedRunLedger.attach_worker(journal.worker_binding())
    assert cold.state()['http_total']==2 and sent==['/submissions/CIK1.json','/submissions/CIK2.json']
    assert 'crtfc_key' not in journal.path.read_text()


@pytest.mark.parametrize('failure',['timeout','503'])
def test_failed_wire_no_refill_no_internal_retry(tmp_path,failure):
    journal=ledger(tmp_path)
    count=[]
    def send(request):
        count.append(1)
        if failure=='timeout':
            raise httpx.ReadTimeout('SYNTHETIC',request=request)
        return httpx.Response(503)
    transport=wire(journal,'us',httpx.MockTransport(send))
    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            try:
                await client.get('https://data.sec.gov/submissions/one.json')
            except httpx.ReadTimeout:
                pass
            with pytest.raises(ValueError,match='terminal'):
                await client.get('https://data.sec.gov/submissions/two.json')
    asyncio.run(run())
    assert journal.state()['http_total']==1 and count==[1]


def test_source_and_onboarding_same_expiration_no_spending(tmp_path):
    journal=ledger(tmp_path)
    wire(journal,'us',httpx.MockTransport(lambda r:httpx.Response(200)))
    # Mutate only the TEST clock; no real approval/STOP/lease is reset.
    journal._event('DB_INTENT')
    receipt=dict(permission_event=journal.identity['approval_event'],total_changes=0,
        sqlite_mode='ro',query_only=True,query_trace=[dict(operation='SELECT')],
        cutoff=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat())
    journal.registration_captured(receipt)
    for call in (journal.before_http,journal.before_onboarding_http):
        with pytest.raises(ValueError,match='window_expired'):
            call(market='us',provider='sec_edgar',logical_id='document:0',plan_sha256=digest('test'))
    assert journal.state()['http_total']==0


def test_unbound_lower_ohlcv_refused_before_any_initial_evidence_IO(tmp_path):
    from app.services.onboarding_evidence_service import build_initial_evidence
    from app.services.onboarding_campaign_io import InitialEvidenceIO
    journal=ledger(tmp_path)
    io=InitialEvidenceIO(ledger=journal,direct_transport=object(),ohlcv_transport=object(),
        require_ohlcv_physical_binding=None)
    with pytest.raises(ValueError,match='lower_physical_dispatch_unbound'):
        asyncio.run(build_initial_evidence(None,SimpleNamespace(ticker='TEST'),
            as_of=datetime.now(timezone.utc),acquire=True,campaign_io=io))
    assert journal.state()['http_total']==journal.state()['model_total']==0


def test_wallclock_stops_external_spending_without_refill(tmp_path):
    journal=ledger(tmp_path)
    # Reopen with a deliberately elapsed TEST-only finite wallclock identity.
    approval=journal.approval
    bounded=SelectedRunLedger(path=tmp_path/'elapsed.jsonl',approval=approval,master_id='ELAPSED_TEST',
        children=journal.identity['children'],provider_caps={'sec_edgar':1},max_http=1,max_models=14,
        database_identity={'memory_only':True},onboarding=True,wallclock_seconds_max=1)
    with pytest.raises(ValueError,match='wallclock_exhausted'):
        bounded.before_onboarding_model(market='us',ticker='TEST',stage='CORE',payload_sha256=digest('test'))
    assert bounded.state()['model_total']==0


def test_ohlcv_retry_zero_malformed_refetch_zero(monkeypatch):
    from app.services.ohlcv_client import OhlcvClient
    price=OhlcvClient(campaign_no_retry=True)
    calls=[]
    bad=[dict(date='2026-11-10',open=10,high=1,low=5,close=10,volume=1)]
    monkeypatch.setattr(price,'_decode_period_payload',lambda *a,**k:(bad,{},'kiwoom'))
    async def run():
        def send(request):
            calls.append(1)
            return httpx.Response(200,json={})
        async with httpx.AsyncClient(base_url='https://example.test',transport=httpx.MockTransport(send)) as client:
            with pytest.raises(ValueError,match='malformed_ohlcv_no_refetch'):
                await price._request_period(client,'TEST','daily',1000)
    asyncio.run(run())
    assert calls==[1]


def test_db_rows_other_subject_and_raw_writes_stopped_before_dispatch(tmp_path):
    from app.models.company import Company
    from app.services.onboarding_campaign_io import onboarding_database_budget
    journal=ledger(tmp_path,db={'SELECT':6,'INSERT:company':1,'UPDATE:company':1,'COMMIT':3})
    engine=create_engine('sqlite://')
    metadata=MetaData()
    Company.__table__.to_metadata(metadata)
    metadata.create_all(engine)
    with Session(engine) as session:
        with onboarding_database_budget(session,journal):
            session.add(Company(ticker='TEST',company_name='Test'))
            session.commit()
            item=session.exec(select(Company).where(Company.ticker=='TEST')).one()
            item.company_name='Changed'
            session.commit()
            with pytest.raises(ValueError,match='raw_bulk_or_schema'):
                session.exec(text('UPDATE company SET company_name="BAD"'))
            session.rollback()
            session.add(Company(ticker='OTHER',company_name='Untouched'))
            with pytest.raises(ValueError,match='other_subject'):
                session.commit()
            session.rollback()
    state=journal.state()
    assert state['database_used']['INSERT:company']==1 and state['database_used']['UPDATE:company']==1
    cold=SelectedRunLedger.attach_worker(journal.worker_binding())
    with pytest.raises(ValueError,match='exhausted'):
        cold.before_onboarding_database('INSERT:company')
    engine.dispose()


def test_original_sec_collector_and_valuation_use_same_physical_ledger(tmp_path,monkeypatch):
    from tests.test_onboarding_reconciler_service import _engine
    from app.config import Settings
    from app.models.company import Company
    from app.models.watchlist import WatchlistItem
    from app.providers.filings import SecEdgarProvider
    from app.services import collection_service as collection, valuation_snapshot_service as valuation
    from app.services.onboarding_campaign_io import onboarding_database_budget
    from app.schemas.thesis import PriceContext
    settings=Settings(_env_file=None,include_mock_provider=False,sec_user_agent='Synthetic contact test@example.test',
        monitor_retry_attempts=5)
    monkeypatch.setattr(collection,'provider_priority',lambda **k:[SecEdgarProvider()])
    # Existing SEC identities remain provider code, not a ticker exception in production.
    journal=ledger(tmp_path,db={'SELECT':128,'INSERT:company':1,'INSERT:watchlistitem':1,
        'INSERT:securitymaster':1,'UPDATE:securitymaster':4,'INSERT:providercalltelemetry':8,
        'UPDATE:providercalltelemetry':8,'INSERT:providerresponsecache':4,'COMMIT':4})
    routes=[dict(logical_id='ticker',method='GET',host='www.sec.gov',path='/files/company_tickers.json',provider='sec_edgar'),
        dict(logical_id='submission',method='GET',host='data.sec.gov',path_prefix='/submissions/',provider='sec_edgar'),
        dict(logical_id='facts',method='GET',host='data.sec.gov',path_prefix='/api/xbrl/companyfacts/',provider='sec_edgar')]
    pin=digest(routes)
    journal.bind_onboarding_http_plan(market='us',plan_sha256=pin,logical_ids=[r['logical_id'] for r in routes])
    calls=[]
    def send(request):
        assert journal.state()['pending'] and journal.state()['http_total']==len(calls)+1
        calls.append(request.url.path)
        if request.url.path.endswith('company_tickers.json'):
            return httpx.Response(200,json={'0':dict(ticker='TEST',cik_str=1234)})
        return httpx.Response(200,json=dict(cik='1234',name='Synthetic',facts={},filings=dict(recent={})))
    transport=OnboardingCampaignTransport(ledger=journal,market='us',plan_sha256=pin,
        routes=routes,inner=httpx.MockTransport(send))
    engine=_engine()
    with Session(engine) as session:
        with onboarding_database_budget(session,journal):
            session.add(Company(ticker='TEST',company_name='Synthetic',exchange='NASDAQ'))
            session.add(WatchlistItem(ticker='TEST',company_name='Synthetic',exchange='NASDAQ'))
            session.commit()
            monkeypatch.setattr(collection,'get_settings',lambda:settings)
            import app.providers.filings as filings
            monkeypatch.setattr(filings,'get_settings',lambda:settings)
            asyncio.run(collection.CollectionService(campaign_transport=transport).collect_events(session,'TEST',3))
            monkeypatch.setattr(valuation,'get_settings',lambda:settings)
            # The original valuation's SEC fallback shares the same frozen wire.
            view=asyncio.run(valuation.ValuationSnapshotService(transport=transport).fetch(
                'TEST','NASDAQ',PriceContext(),session=session))
            assert view.current_price is None  # No invented valuation or current price.
    engine.dispose()
    assert len(calls)==journal.state()['http_total']==3
    assert journal.state()['database_used']['COMMIT']==2


def test_original_reconciler_writer_to_cycle_owner_to_fresh_source(tmp_path):
    from tests.test_onboarding_reconciler_service import _engine,_seed_pending,_evidence_builder,_decision_builder
    from app.services.onboarding_reconciler_service import resume_onboarding_subject,OnboardingAttemptMode
    from app.services.unified_cycle_owner import issue_reconciler_cycle_owner
    from app.services.fresh_source_run_contract import validate_local_seed
    from app.services.minimal_class_c_export import COLUMNS
    from app.services.unified_source_policy import UnifiedSourcePolicy
    engine=_engine()
    policy=UnifiedSourcePolicy(frozenset({'canonical_local','local','sec_edgar'}))
    writer_at=datetime.fromisoformat('2026-11-12T07:59:00+09:00')
    events=[]
    with Session(engine) as session:
        for market,ticker,venue in (('us','TEST','NASDAQ'),('kr','123456','KRX')):
            item=_seed_pending(session,tmp_path,ticker=ticker,exchange=venue)
            result=asyncio.run(resume_onboarding_subject(session,item,origin='TEST_ONLY',
                mode=OnboardingAttemptMode.BACKGROUND,as_of=writer_at,data_dir=tmp_path,
                evidence_builder=_evidence_builder,decision_builder=_decision_builder,
                cycle_event_sink=events.append))
            assert result.active and result.error is None
        assert len(events)==2
        for market,ticker in (('us','TEST'),('kr','123456')):
            rows={table:[dict(row) for row in session.connection().exec_driver_sql(
                'SELECT '+','.join('"'+c+'"' for c in cols)+' FROM "'+table+'" WHERE ticker=?',
                (ticker,)).mappings()] for table,cols in COLUMNS.items()}
            slot=datetime.fromisoformat('2026-11-12T'+('08:10:00' if market=='us' else '16:10:00')+'+09:00')
            cutoff=slot+timedelta(seconds=60)
            target=(slot-timedelta(days=1)).date() if market=='us' else slot.date()
            args=dict(source_rows=encoded(rows),market=market,target_session=target,cutoff=cutoff,
                scheduled_at=slot,scheduled_run_event_sha256=digest('TEST_ONLY_ORIGINAL_RUN'),
                source_generation_id='TEST_SOURCE',execution_generation_id='TEST_EXECUTION',policy=policy)
            owner,accepted=issue_reconciler_cycle_owner(session,**args)
            validate_local_seed(accepted)
            assert accepted['cycle_owner_receipt']['approved']==[ticker]
            assert accepted['roles']['universe']['records'][0]['record']['first_eligible_session']=='2026-11-12'
            with pytest.raises(ValueError,match='scheduled_slot_not_owned'):
                issue_reconciler_cycle_owner(session,**dict(args,scheduled_at=slot+timedelta(minutes=1)))
            bad=__import__('copy').deepcopy(rows)
            bad['investmentthesis'][0]['version']+=1
            with pytest.raises(ValueError,match='mapping_ineligible'):
                issue_reconciler_cycle_owner(session,**dict(args,source_rows=encoded(bad)))
    engine.dispose()
