"""Only C22AO capacity boundaries; no live DB, financial HTTP or model calls."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import sqlite3
from types import SimpleNamespace
import zlib

import pytest

from app.services import minimal_class_c_export as export
from app.services import prospective_class_c_owner as prospective
from app.services import selected_source_registration as registration
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_plan import build_stock_plan, COUNTS
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_c22an_registration_and_cohorts import synthetic_campaign
from tests.test_minimal_class_c_export import POLICY

AT = datetime(2026, 11, 12, 23, 10, tzinfo=timezone.utc)


def record(name, value):
    root = Path(os.environ['C22AO_PROBE_ROOT'])
    root.mkdir(parents=True, exist_ok=True)
    with (root/(name+'.json')).open('x') as stream:
        json.dump(dict(provenance='SYNTHETIC_NOT_LIVE_AUTHORITY', operating_DB=0,
            financial_HTTP=0, model_calls=0, peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            **value), stream, indent=2)


def sized(tmp_path, monkeypatch, subjects, limit=16*1024**2):
    fixture = synthetic_campaign(tmp_path, monkeypatch)
    fixture.now[0] = AT
    event = 'C22AO_SYNTHETIC_' + str(len(subjects))
    permission = replace(fixture.permission, event_id=event, subjects=subjects,
        max_private_export_bytes=limit)
    decision = prospective.ApprovalDecision(event_id=event, approved=True,
        user_message_sha256=digest('SYNTHETIC_CAPACITY_TEST_NOT_USER_CONSENT'),
        effective_at=AT-timedelta(minutes=1), expires_at=AT+timedelta(minutes=30), subjects=subjects)
    approval = prospective.record_backend_approval(decision)
    return fixture, permission, approval


@pytest.mark.parametrize('count', [8, 14, 22])
def test_large_post_onboarding_shape_original_owner_seed_and_freeze(tmp_path, monkeypatch, count):
    from app.services.selected_source_context import freeze_registered_child
    from app.services.selected_source_plan import SelectedConsumerPolicy
    subjects = tuple(UNIVERSE['kr'] if count==8 else UNIVERSE['us'] if count==14
        else (*UNIVERSE['kr'], *UNIVERSE['us']))
    _, permission, approval = sized(tmp_path, monkeypatch, subjects)
    large = json.dumps(dict(evidence='S'* (9*1024**2), utf8='한글\\"\n'), ensure_ascii=False)
    with sqlite3.connect(permission.database) as db:
        db.execute('UPDATE watchlistitem SET onboarding_initial_evidence=?,latest_valuation_context=NULL WHERE ticker=?',
            (large, subjects[0]))
    markets = {m:tuple(t for t in ts if t in subjects) for m,ts in UNIVERSE.items() if set(ts)&set(subjects)}
    generations = {m:'C22AO_SYNTHETIC_'+m for m in markets}
    diagnostic = {}
    capture, owners, receipt = registration.capture_markets(permission=permission,approval=approval,
        generations=generations,policy=POLICY,enabled=True,market_subjects=markets,diagnostics=diagnostic)
    raw, saved = export.captured_private_snapshot(capture)
    rows = json.loads(raw)
    assert len(raw)>8*1024**2 and len(raw)<=permission.max_private_export_bytes
    assert saved['original_rows_sha256']==hashlib.sha256(raw).hexdigest()==diagnostic['original_rows_sha256']
    assert receipt['private_export']==diagnostic and diagnostic['SELECT']==5 and diagnostic['ROLLBACK']==1
    assert diagnostic['total_changes']==0 and not diagnostic['in_transaction_after_rollback']
    assert next(r for r in rows['watchlistitem'] if r['ticker']==subjects[0])['onboarding_initial_evidence']==large
    assert all(set(r)==set(export.COLUMNS[t]) for t,rs in rows.items() for r in rs)
    assert rows['watchlistitem'][0]['latest_valuation_context'] is None
    ledger = SimpleNamespace(identity=dict(children={m:dict(generation=generations[m],subjects=list(ts))
        for m,ts in markets.items()}),worker_binding=lambda:dict(synthetic=True))
    result = {}
    for market,owner in owners.items():
        frozen,_,_,seed = freeze_registered_child(registration_owner=owner,policy=POLICY,code_sha='a'*40,
            native=None,native_owner_root=tmp_path/'not-installed',config_identities={p:digest(p) for p in
                ('kiwoom','sec_edgar','opendart','fred','eia','ecos','krx_night_futures','finnhub','google_news_rss','naver_news')},
            configured_kr_pages=20,listing_rows=[],kis_static_hashes={},
            completed_close_documentation=dict(path='SYNTHETIC',sha256='a'*64),
            consumer_policy=SelectedConsumerPolicy(),master_id='C22AO_SYNTHETIC_MASTER',
            ohlcv_source_url='https://synthetic.invalid/ohlcv',enabled=True,run_ledger=ledger)
        assert not seed['denials'] and set(seed['universe']['eligible_subjects'])==set(markets[market])
        assert len(frozen['stock_plan']['reads'])==4*len(markets[market])
        assert frozen['financial_use_granted'] is False
        bad=deepcopy(seed)
        bad['roles']['universe']['records'][0]['original_record_sha256']='0'*64
        from app.services.unified_local_seed_bridge import admit_pinned_local_seed
        with pytest.raises(ValueError):
            admit_pinned_local_seed(encoded(bad),expected_sha256=digest(bad),market=market,
                session_key=frozen['sessions'][market],cutoff=AT,subjects=markets[market],policy=POLICY,
                prospective_owner=owner)
        result[market]=dict(subjects=len(markets[market]),Owner_and_local_seed=True,Source_freeze=True,
            Source_planning_only=True,Market_Parent=False,official_renderer=False)
    assert large not in json.dumps(diagnostic,ensure_ascii=False)
    record('large_'+str(count),dict(capture=diagnostic,markets=result,full_columns=True,NULL_preserved=True))


def test_exact_legacy_boundary_plus_one_utf8_escaping_and_compression(tmp_path, monkeypatch):
    _, permission, _ = sized(tmp_path,monkeypatch,('005930',),8*1024**2)
    with sqlite3.connect(permission.database) as db:
        db.execute('UPDATE watchlistitem SET onboarding_initial_evidence=?',
            (json.dumps(dict(utf8='한글',nested='\\"\n'),ensure_ascii=False),))
    rows,_=export.read_authorized_rows(permission)
    old=rows['watchlistitem'][0]['notes']
    padding=permission.max_private_export_bytes-len(encoded(rows))+len(encoded(old))-2
    with sqlite3.connect(permission.database) as db:
        db.execute('UPDATE watchlistitem SET notes=?',('S'*padding,))
    rows,receipt=export.read_authorized_rows(permission)
    assert len(encoded(rows))==8*1024**2
    assert receipt['private_export']['uncompressed_utf8_bytes']==8*1024**2
    with sqlite3.connect(permission.database) as db:
        db.execute('UPDATE watchlistitem SET notes=notes||?',('S',))
    diagnostics={}
    with pytest.raises(ValueError,match='private_export_size_limit'):
        export.read_authorized_rows(permission,diagnostics=diagnostics)
    assert diagnostics['uncompressed_utf8_bytes']==8*1024**2+1
    assert diagnostics['max_private_export_bytes']==8*1024**2
    assert diagnostics['SELECT']==5 and diagnostics['ROLLBACK']==1 and diagnostics['total_changes']==0
    rows['watchlistitem'][0]['notes']+='S'
    assert len(zlib.compress(encoded(rows)))<8*1024**2
    for table,detail in diagnostics['tables'].items():
        assert detail['serialized_bytes']==detail['structural_bytes']+sum(
            f['serialized_entry_bytes'] for f in detail['fields'].values())
    record('exact_boundary',dict(accepted_bytes=8*1024**2,rejected=diagnostics,
        compressed_length_not_used=True,legacy_default_unchanged=True))


def test_invalid_cap_and_network_payload_cannot_set_or_refill_limit(tmp_path,monkeypatch):
    _,permission,_=sized(tmp_path,monkeypatch,('005930',))
    for value in (-1,0,True,'16777216',float('inf'),64*1024**2+1,dict(max=64*1024**2)):
        with pytest.raises(ValueError,match='finite_private_export'):
            export.read_authorized_rows(replace(permission,max_private_export_bytes=value),
                connect=lambda *a,**k:pytest.fail('must reject before connect'))
    with pytest.raises(TypeError):
        registration.capture_approved_markets(settings=None,runtime_directory=None,approval=None,
            generations={},policy=POLICY,ledger=None,enabled=True,max_private_export_bytes=64*1024**2)
    record('cap_injection',dict(invalid_values_rejected=7,untrusted_call_keyword_rejected=True,
        before_connection=True,automatic_limit_growth=False,maximum_bytes=64*1024**2))


def test_one_frozen_limit_and_durable_rejection_diagnostic(tmp_path,monkeypatch):
    c=synthetic_campaign(tmp_path,monkeypatch);c.now[0]=AT
    old_identity=deepcopy(c.ledger.identity)
    new=SelectedRunLedger(path=tmp_path/'capacity.jsonl',approval=c.approval,master_id='C22AO_SYNTHETIC_CAP',
        children=c.ledger.identity['children'],provider_caps={'sec_edgar':3},max_http=3,max_models=48,
        database_identity=c.ledger.identity['database_identity'],staged_markets=True,
        runtime_cap=c.ledger.identity['runtime_cap'],capture_max_private_export_bytes=16*1024**2)
    with pytest.raises(ValueError,match='frozen_scope'):
        new.before_registration(approval=c.approval,permission=c.permission,generations={'kr':'SYNTHETIC_kr'})
    assert not new.state()['db_connection_attempts']
    with sqlite3.connect(c.permission.database) as db:
        db.execute('UPDATE watchlistitem SET notes=? WHERE ticker=?',('S'*(17*1024**2),'005930'))
    diagnostic=tmp_path/'size.json'
    with pytest.raises(ValueError,match='private_export_size_limit'):
        registration.capture_approved_markets(settings=SimpleNamespace(database_url='sqlite:///'+str(c.permission.database)),
            runtime_directory=tmp_path,approval=c.approval,generations={'kr':'SYNTHETIC_kr'},
            policy=POLICY,ledger=new,enabled=True,diagnostics_path=diagnostic)
    report=json.loads(diagnostic.read_bytes())
    assert report['uncompressed_utf8_bytes']>16*1024**2 and report['max_private_export_bytes']==16*1024**2
    assert report['capture_scope']=='FULL_APPROVED_ROSTER' and len(report['subjects'])==22
    assert new.state()['state']=='STOPPED_NO_SEND' and new.state()['http_total']==new.state()['model_total']==0
    assert c.ledger.identity==old_identity
    with pytest.raises(ValueError):new.worker_binding()
    assert new.identity['capture_max_private_export_bytes']==16*1024**2
    record('frozen_cap_rejection',dict(diagnostic=report,old_identity_preserved=True,stop_not_reset=True,
        extra_capture=False,cap_growth=False))


def test_64MiB_uncompressed_ceiling_stress(tmp_path,monkeypatch):
    _,permission,_=sized(tmp_path,monkeypatch,('005930',),64*1024**2)
    rows,_=export.read_authorized_rows(permission)
    padding=permission.max_private_export_bytes-len(encoded(rows))+len(encoded(rows['watchlistitem'][0]['notes']))-2
    with sqlite3.connect(permission.database) as db:
        db.execute('UPDATE watchlistitem SET notes=?',('S'*padding,))
    diagnostics={}
    rows,receipt=export.read_authorized_rows(permission,diagnostics=diagnostics)
    assert diagnostics['uncompressed_utf8_bytes']==64*1024**2
    assert receipt['original_rows_sha256']==digest(rows)
    assert diagnostics['SELECT']==5 and diagnostics['ROLLBACK']==1 and diagnostics['total_changes']==0
    record('64MiB_stress',dict(capture=diagnostics,actual_LIVE_size_sufficiency='UNVERIFIED',
        automatic_limit_increase=False,source_dispatch=False))


def test_legacy_small_capture_and_full_field_identity_remain_required(tmp_path,monkeypatch):
    _,permission,approval=sized(tmp_path,monkeypatch,('005930',),8*1024**2)
    capture,owners,receipt=registration.capture_markets(permission=permission,approval=approval,
        generations={'kr':'C22AO_SMALL_KR'},policy=POLICY,enabled=True)
    raw,_=export.captured_private_snapshot(capture)
    assert receipt['private_export']['max_private_export_bytes']==8*1024**2
    assert receipt['original_rows_sha256']==hashlib.sha256(raw).hexdigest()
    rows=json.loads(raw);rows['watchlistitem'][0].pop('notes')
    with pytest.raises(ValueError):
        export.project_authorized_rows(rows,market='kr',session_key='2026-11-12',cutoff=AT,policy=POLICY)
    with pytest.raises(ValueError):prospective.require_generation(owners['kr'],'FOREIGN')
    assert 'SYNTHETIC_UNRELATED' not in json.dumps(receipt)
    record('legacy_and_integrity',dict(default_bytes=8*1024**2,legacy_positive=True,
        missing_column_rejected=True,foreign_generation_rejected=True,current_economic_rights_added=False))


def test_actual_kr_failure_is_selected_read_set_not_capture_or_provider(tmp_path):
    import asyncio
    import traceback
    from datetime import date
    from app.services.kiwoom_kr_market_context_service import kiwoom_market_reads
    from app.services.selected_market_collection import SelectedKrMarketCollection
    from app.services.selected_source_plan import SelectedConsumerPolicy
    from app.services.unified_kiwoom_observer import KiwoomRead, KiwoomReceiptObserver
    from app.services.production_source_context import POLICY as production_policy

    root=Path(os.environ['C22AO_PROBE_ROOT']).parent/'private-live/source/kr'
    frozen=json.loads((root/'production-frozen-source-plan.json').read_bytes())
    query=json.loads((root/'markets/kr-query.json').read_bytes())
    reads=tuple(KiwoomRead.model_validate(r) for r in frozen['candidate']['kr_market_reads'])
    session=date.fromisoformat(frozen['sessions']['kr'])
    expected=kiwoom_market_reads(session_date=session,max_pages=frozen['kr_local_cap'],max_requests_per_page=1)
    missing=[r for r in expected if r not in reads]
    assert len(missing)==2 and all(r.api_id=='ka10066' and not r.mandatory for r in missing)
    assert tuple(r for r in expected if r.api_id!='ka10066')==reads
    observer=KiwoomReceiptObserver(root=tmp_path/'observer',run_id=frozen['generation_id'],
        attempt_id='C22AO_OFFLINE_ROOT_CAUSE',session_date=session,reads=reads,
        policy=production_policy,completed_session_only=True)
    calls=[]
    async def forbidden(**kwargs):
        calls.append(True)
        raise AssertionError('NO_REPLAY_HTTP_ALLOWED')
    client=SimpleNamespace(source_observer=observer,max_retries=0,request=forbidden)
    service=SelectedKrMarketCollection(client,max_pages=frozen['kr_local_cap'],
        completed_session_only=True,consumer_policy=SelectedConsumerPolicy())
    with pytest.raises(ValueError,match='kiwoom_whole_market_plan_required') as caught:
        asyncio.run(service.collect(session_date=session,observed_at=datetime.fromisoformat(query['observed_at'])))
    assert not calls and not observer._started
    frames=traceback.extract_tb(caught.value.__traceback__)
    source=next(f for f in reversed(frames) if f.name=='collect')
    record('actual_KR_market_root',dict(error='kiwoom_whole_market_plan_required',
        first_function='KiwoomKrMarketContextService.collect',first_line=source.lineno,
        planned_reads=len(reads),required_original_reads=len(expected),
        omitted_optional_apis=[r.api_id for r in missing],pre_wire_failure=True,
        cold_secondary_error='captured_phase_provenance_mismatch',
        original_Market_Parent_checks_unchanged=True,old_failed_phase_not_rewritten=True,
        original_full_owner_plan_also_requires_complete_read_set=True))


def test_us_market_wire_schema_matches_existing_consumer_without_pass_callbacks(tmp_path):
    import asyncio
    from datetime import date
    import httpx
    from app.macro.providers.market import MARKET_SYMBOLS, OhlcvMarketProvider
    from app.services.production_source_context import POLICY as production_policy
    from app.services.unified_source_observer import OhlcvRead,OhlcvReceiptObserver

    reads=tuple(OhlcvRead(role='us_market:'+s,symbol=s,market='us',provider='ohlcv_analyst',
        response_provider='kiwoom',period='daily',adjusted=True,session_date=date(2026,11,12),
        max_requests=1,params=dict(symbol=s,market='US',periods='daily',count=2,
            include_indicators='false',indicator_limit=0,adjusted='true')) for s in MARKET_SYMBOLS)
    observer=OhlcvReceiptObserver(root=tmp_path/'us-market',run_id='C22AO_US_SYNTHETIC',
        attempt_id='C22AO_US_SYNTHETIC:A1',reads=reads,policy=production_policy)
    calls=[]
    def wire(request):
        calls.append(request.url.params['symbol'])
        return httpx.Response(200,json=dict(meta=dict(provider='kiwoom',adjusted=True),
            resolved_symbol=dict(code=request.url.params['symbol']),periods=dict(daily=[
                dict(date='2026-11-11',close=100),dict(date='2026-11-12',close=101)])))
    service=OhlcvMarketProvider(transport=httpx.MockTransport(wire),source_observer=observer)
    service.settings=SimpleNamespace(ohlcv_api_key=None,action_api_key=None,
        ohlcv_base_url='https://synthetic.invalid',ohlcv_timeout_seconds=1)
    result=asyncio.run(service.collect(AT))
    assert set(calls)==set(MARKET_SYMBOLS) and len(calls)==len(MARKET_SYMBOLS)
    assert len(result.observations)==len(MARKET_SYMBOLS) and not result.warnings
    assert all(o.observed_at.date()==date(2026,11,12) and o.previous_value==100 and o.value==101
        for o in result.observations)
    assert len(list(observer.root.glob('*.normalization.json')))==len(MARKET_SYMBOLS)
    record('US_market_original_consumer',dict(symbols=len(MARKET_SYMBOLS),mock_GETs=len(calls),
        original_observer_and_normalizer=True,callbacks_forced_PASS=False,
        actual_live_Market_Parent=False,official_renderer=False))
