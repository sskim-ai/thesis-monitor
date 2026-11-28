"""Registered planning/physical transport boundary for an expanded synthetic roster."""
import asyncio
from collections import Counter
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import sqlite3
from types import SimpleNamespace

import httpx
import pytest

from app.jobs.unified_market_snapshot import LOCAL_CAPS, LOCAL_PROVIDERS
from app.macro.providers.market import MARKET_SYMBOLS
from app.services import prospective_class_c_owner as registration
from app.services.campaign_runtime_cap import RuntimeCap
from app.services.canonical_source_plan import kiwoom_request
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.model_timeout_retry import ALL_MODEL_STAGE_ONE_RETRY_V1, roster_model_ceiling
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_context import freeze_registered_child
from app.services.selected_source_plan import SelectedConsumerPolicy, SelectedRequestPlan, US_NIGHT_OPTIONAL, request_budget
from app.services.selected_source_registration import current_monitoring_subjects, capture_approved_markets
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from app.services.production_source_context import POLICY
from tests.test_minimal_class_c_export import database


@pytest.mark.parametrize('market,expand', [('kr',False),('kr',True),('us',False),('us',True)])
def test_expanded_regular_financial_plan(tmp_path, market, expand, record_property):
    record_property('roster_review',json.dumps(regular_financial_plan(tmp_path, market, expand),sort_keys=True))


def regular_financial_plan(tmp_path, market, expand, *, identities=None, auxiliary=None):
    extra = '175421' if market == 'kr' else 'NEWX'
    requested = tuple(sorted((*UNIVERSE[market], *((extra,) if expand else ()))))
    inactive = '123450' if market == 'kr' else 'INACTIVE'
    database_fixture = database(tmp_path, [(t,market) for t in (*requested,inactive)])
    with sqlite3.connect(database_fixture.database) as db:
        db.execute('UPDATE watchlistitem SET active=0 WHERE ticker=?', (inactive,))
        for index, ticker in enumerate(requested):
            for table in ('watchlistitem','company','securitymaster'):
                db.execute(f'UPDATE {table} SET company_name=? WHERE ticker=?', ('Synthetic '+ticker,ticker))
            if identities and ticker in identities:
                security = identities[ticker]
                db.execute('UPDATE securitymaster SET cik=?, exchange=?, identity_provider=?, issuer_type=?, '
                    'canonical_company_id=?, canonical_security_id=?, security_type=?, company_name=? WHERE ticker=?',
                    tuple(security[k] for k in ('cik','exchange','identity_provider','issuer_type','canonical_company_id',
                                               'canonical_security_id','security_type','company_name')) + (ticker,))
                db.execute('UPDATE watchlistitem SET company_name=?,exchange=? WHERE ticker=?',
                           (security['company_name'],security['exchange'],ticker))
                db.execute('UPDATE company SET company_name=? WHERE ticker=?',(security['company_name'],ticker))
            elif market == 'kr':
                db.execute("UPDATE securitymaster SET identity_provider='opendart',corp_code=? WHERE ticker=?",
                           (str(10000000+index),ticker))
            else:
                db.execute("UPDATE securitymaster SET cik=? WHERE ticker=?", (str(123400+index),ticker))
    subjects = current_monitoring_subjects(database_fixture.database, device=database_fixture.device,
        inode=database_fixture.inode, market=market)
    assert subjects == requested
    now = datetime.now(timezone.utc)
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id=f'SYNTHETIC_{market}_{len(subjects)}', approved=True, subjects=subjects,
        user_message_sha256=digest('offline-roster'), effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(hours=2), routine_us_no_send_source_seconds=1800 if market=='us' else None))
    generation = 'SYNTHETIC_'+market
    endpoints = {p: [dict(host=p.replace('_','-')+'.test', prefix='/source/', methods=['GET','POST'],
                          endpoint='SYNTHETIC')] for p in LOCAL_PROVIDERS[market]}
    endpoints['kiwoom'] = [dict(host='api.kiwoom.com',prefix='/api/',methods=['POST'],endpoint='KIWOOM_CHART')]
    ledger = SelectedRunLedger(path=tmp_path/'campaign.jsonl', approval=approval, master_id='SYNTHETIC_MASTER',
        children={market:dict(generation=generation, subjects=list(subjects))},
        database_identity=dict(path=str(database_fixture.database),device=database_fixture.device,inode=database_fixture.inode),
        max_models=roster_model_ceiling(subjects), provider_caps={}, max_http=0, plan_http_market=market,
        timeout_retry_market=market, b2_retry_policy=ALL_MODEL_STAGE_ONE_RETRY_V1,
        wallclock_seconds_max=16200, staged_markets=True, runtime_cap=dict(endpoints=endpoints,
            market_subjects={'us':[*MARKET_SYMBOLS,'000660'],'kr':[]}))
    settings = SimpleNamespace(database_url='sqlite:///'+str(database_fixture.database))
    _, owners, _ = capture_approved_markets(settings=settings, runtime_directory=tmp_path, approval=approval,
        generations={market:generation}, policy=POLICY, ledger=ledger, enabled=True, monitoring_only=True,
        subject_limits={market:len(subjects)}, priority_subjects={market:subjects})
    if market == 'us' and auxiliary is None:
        from tests.test_us14_source_scope import us_plan
        args, _, _ = us_plan()
        auxiliary = dict(security=args['auxiliary_security'],official_identity_sha256=args['auxiliary_identity_sha256'])
    frozen, compiler, kis, _ = freeze_registered_child(registration_owner=owners[market], policy=POLICY,
        code_sha='a'*40, native=dict(owner_head='a'*40,owner_files={'app/main.py':digest('fixture')},
            settings_sha256=digest('fixture-settings'),request_environment_sha256=digest('fixture-env')), native_owner_root=tmp_path, config_identities={p:digest(p) for p in endpoints},
        configured_kr_pages=20, listing_rows=[], kis_static_hashes={}, include_kr_stock_flow=market=='kr',
        kr_stock_chart_v3=market=='kr', completed_close_documentation=dict(path='static/offline',sha256='a'*64),
        consumer_policy=SelectedConsumerPolicy(us_night=US_NIGHT_OPTIONAL) if market=='us' else SelectedConsumerPolicy(),
        master_id='SYNTHETIC_MASTER', ohlcv_source_url='http://localhost/ohlcv', enabled=True, run_ledger=ledger,
        issuer_auxiliary=auxiliary)
    plan = SelectedRequestPlan.model_validate(frozen['plan'])
    assert plan.subjects == subjects and inactive not in plan.subjects
    ledger.bind_source_plan(market,plan,kis_plan=kis)
    binding = frozen['shared_run_ledger']
    worker = SelectedRunLedger.attach_worker(binding)
    cap = RuntimeCap(binding)
    budget = request_budget({'plan':plan},kis)
    assert ledger.state()['runtime']['http_budget'] == cap.state()['http_budget'] == budget
    providers = Counter(d.provider for d in plan.descriptors)
    assert 'ohlcv_analyst' not in providers and all(d.transient_retry_max==0 for d in plan.descriptors)
    assert budget['providers'] == {**providers, **({'kis':kis['maximum_physical_HTTP']} if kis else {})}
    stock_pages = [d for d in plan.descriptors if d.consumer_role.startswith('stock:')]
    assert stock_pages and all(d.provider=='kiwoom' for d in stock_pages)
    assert sum(d.logical_request_id=='kiwoom:auth' for d in plan.descriptors) == 1
    reports = [d for d in plan.descriptors if d.logical_request_id.endswith(':filing1:report')]
    assert len(reports) == (len(subjects) if market=='kr' else 0)
    if market=='us':
        assert any(d.subject=='000660' and d.provider=='opendart' for d in plan.descriptors)
    # Exercise a planned wire for the added subject, following its attached-worker path.
    ticker = extra if expand else subjects[-1]
    descriptor = next(d for d in stock_pages if d.subject == ticker and d.page_ordinal == 1)
    dispatcher = SelectedSourceDispatcher(plan=plan,compiler_args=compiler,kis_plan=kis,registration_owner=owners[market],
        policy=POLICY,config_identities=frozen['config_identities'],credential_presence={p:True for p in endpoints},
        repository_root=Path(__file__).resolve().parents[1],root=tmp_path/'dispatch',
        approved_plan_sha256=plan.plan_sha256,approved_provider_caps=budget['providers'],guard=lambda:None,
        enabled=True,run_ledger=worker,secrets=('PLAN_CREDENTIAL',))
    wires = []
    def send(req):
        wires.append(req)
        return httpx.Response(200,content=b'{}')
    wire = SealedSourceTransport(dispatcher,httpx.MockTransport(send),providers=endpoints)
    template = json.loads(descriptor.request_json)
    request = kiwoom_request(descriptor.endpoint_operation,httpx.URL(template['url']).path,json.loads(template['body']))
    outside = kiwoom_request(descriptor.endpoint_operation,httpx.URL(template['url']).path,
        dict(json.loads(template['body']),stk_cd=inactive))
    with pytest.raises(SourceSafetyStop,match='not_unique_sealed_slot'):
        asyncio.run(wire.handle_async_request(outside))
    assert not wires and RuntimeCap(binding).state()['total'] == 0
    response = asyncio.run(wire.handle_async_request(request))
    assert response.status_code == 200 and dispatcher.results[descriptor.logical_request_id]['status'] == 'PASS'
    actual = cap.state()['providers']
    assert actual == {'kiwoom':1} and len(wires)==1
    old = LOCAL_CAPS[market]
    if expand:
        assert budget['total'] > sum(old.values()) and any(n>old[p] for p,n in budget['providers'].items())
    return dict(market=market,subjects=subjects,removed_inactive=inactive,
        original_fixed_total=sum(old.values()),original_fixed_providers=old,frozen_plan_sha256=plan.plan_sha256,
        descriptor_slots=dict(providers), max_physical=budget, fake_physical=actual, fake_subject=ticker,
        original_dispatcher_receipt=dispatcher.results[descriptor.logical_request_id]['receipt_sha256'],
        inactive_subject_post_rejected_before_wire=True,
        over_old_total=budget['total']>sum(old.values()),
        over_old_providers={p:n-old[p] for p,n in budget['providers'].items() if n>old[p]},
        stock_kiwoom_pages=len(stock_pages), continuation_descriptor_slots=sum(d.page_ordinal>1 for d in plan.descriptors),
        internal_ohlcv_get_charged=0, kis_physical=kis['maximum_physical_HTTP'] if kis else 0,
        kis_auth=kis['auth_max'] if kis else 0, kis_conditioned_continuations=kis['action_continuation_max'] if kis else 0,
        conditional_dart_reports=len(reports), issuer_auxiliary_dart_slots=sum(d.subject=='000660' and d.provider=='opendart'
            and market=='us' for d in plan.descriptors), network_calls=0)
