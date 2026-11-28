"""The regular Source budget at the real ledger, worker and fake HTTP ports."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest

from app.services import prospective_class_c_owner as registration
from app.services.campaign_runtime_cap import MeteredSyncTransport, RuntimeCap, apply_runtime_event
from app.services.model_timeout_retry import ALL_MODEL_STAGE_ONE_RETRY_V1, roster_model_ceiling
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_plan import request_budget
from app.services.selected_source_registration import capture_approved_markets
from app.services.unified_snapshot_contract import digest
from scripts.kr8_kis_integration import dispatch_accounted_kis_request
from tests.test_c22ab_selected_source import compile_market
from tests.test_minimal_class_c_export import database, POLICY


def regular_campaign(folder, market, *, dart_report=False):
    ticker = '123456' if market == 'kr' else 'NEWX'
    compiled, args, kis = compile_market(market, ticker)
    if dart_report:
        from app.services.selected_source_plan import compile_selected_plan
        compiled = compile_selected_plan(compiler_args=dict(args, dart_business_report=True), kis_plan=kis)
    plan = compiled['plan']
    budget = request_budget(compiled, kis)
    permission = database(folder, [(ticker, market)])
    now = datetime.now(timezone.utc)
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id='SYNTHETIC_HTTP_' + market, approved=True, user_message_sha256=digest('offline-only'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(hours=1), subjects=(ticker,)))
    endpoints = {provider: [dict(methods=['GET','POST'], host=provider.replace('_','-')+'.test',
        prefix='/source/', endpoint='SYNTHETIC')] for provider in budget['providers']}
    if dart_report:
        endpoints['opendart'] = [dict(methods=['GET'], host='opendart.fss.or.kr', prefix='/api/' + path,
            endpoint=path.split('.')[0]) for path in ('list.json','fnlttSinglAcntAll.json','document.xml')]
    ledger = SelectedRunLedger(path=folder/'campaign.jsonl', approval=approval, master_id='SYNTHETIC',
        children={market: dict(generation=plan.generation_id, subjects=[ticker])},
        provider_caps={}, max_http=0, plan_http_market=market, max_models=roster_model_ceiling((ticker,)),
        database_identity=dict(path=str(permission.database), device=permission.device, inode=permission.inode),
        timeout_retry_market=market, b2_retry_policy=ALL_MODEL_STAGE_ONE_RETRY_V1,
        wallclock_seconds_max=3600, staged_markets=True, runtime_cap=dict(endpoints=endpoints,
            stop_on_first_external_failure=True))
    capture_approved_markets(settings=SimpleNamespace(database_url='sqlite:///'+str(permission.database)),
        runtime_directory=folder, approval=approval, generations={market:plan.generation_id}, policy=POLICY,
        ledger=ledger, enabled=True, subject_limits={market:1}, priority_subjects={market:(ticker,)})
    return ledger, plan, kis, budget


@pytest.mark.parametrize('market', ['kr','us'])
def test_regular_bind_once_and_physical_fake_transport(tmp_path, market):
    ledger, plan, kis, budget = regular_campaign(tmp_path, market)
    binding = ledger.worker_binding()
    provider = 'naver_news' if market == 'kr' else 'google_news_rss'
    slot = next(d.logical_request_id for d in plan.descriptors if d.provider == provider)
    url = 'https://' + provider.replace('_','-') + '.test/source/article'
    sends = []
    def send(request):
        sends.append(request)
        return httpx.Response(200, content=b'{}')
    transport = MeteredSyncTransport(binding=binding, market=market, phase='SOURCE', inner=httpx.MockTransport(send))
    with pytest.raises(ValueError, match='FROZEN_OPEN_SOURCE_REQUIRED|PENDING_PLAN_SLOT'):
        transport.handle_request(httpx.Request('GET',url))
    if kis:
        with pytest.raises(ValueError, match='source_and_kis'):
            ledger.bind_source_plan(market,plan,kis_plan={**kis,'maximum_physical_HTTP':999})
    ledger.bind_source_plan(market, plan, kis_plan=kis)
    assert binding == ledger.worker_binding() and ledger.identity['max_http'] == 0
    assert RuntimeCap(binding).state()['http_budget'] == budget
    assert ledger.state()['runtime']['http_budget'] == budget
    with pytest.raises(ValueError, match='BOUND|freeze_once'):
        ledger.bind_source_plan(market, plan, kis_plan=kis)
    with pytest.raises(ValueError, match='OUTSIDE_FROZEN_SOURCE_SLOTS'):
        ledger.before_http(market=market, provider=provider, logical_id='unplanned', plan_sha256=plan.plan_sha256)
    worker = SelectedRunLedger.attach_worker(binding)
    key = worker.before_http(market=market, provider=provider, logical_id=slot, plan_sha256=plan.plan_sha256)
    with pytest.raises(ValueError):
        transport.handle_request(httpx.Request('GET',url.replace('/source/','/other/')))
    with pytest.raises(ValueError):
        transport.handle_request(httpx.Request('GET','https://unapproved.test/source/article'))
    # An approved route of another provider cannot spend this pending news slot.
    with pytest.raises(ValueError, match='PENDING_PLAN_SLOT'):
        transport.handle_request(httpx.Request('POST','https://kiwoom.test/source/auth'))
    transport.handle_request(httpx.Request('GET',url))
    with pytest.raises(ValueError, match='PENDING_PLAN_SLOT'):
        transport.handle_request(httpx.Request('GET',url+'?other=1'))
    worker.result(key, ok=True)
    with pytest.raises(ValueError):
        worker.before_http(market=market, provider=provider, logical_id=slot, plan_sha256=plan.plan_sha256)
    assert ledger.state()['http'] == {provider:1} and len(sends) == 1
    if kis:
        dispatch_accounted_kis_request(httpx.Request('POST','https://kis.test/source/auth'), send,
            accounting=worker, source_plan_sha256=plan.plan_sha256, logical_id='kis-wire:1')
        with pytest.raises(ValueError, match='OUTSIDE_FROZEN_SOURCE_SLOTS'):
            worker.before_http(market=market,provider='kis',logical_id='kis-wire:3',plan_sha256=plan.plan_sha256)
    # The cold worker and the original parent see the same actual physical usage.
    current = RuntimeCap(binding).state()
    assert current['providers'] == ledger.state()['http'] and current['total'] == len(sends)
    assert not current['pending'] and current['logical_provider'] is None
    # Exercise the physical limits independently of the earlier slot checks.
    physical = next(iter(current['attempts'].values()))
    for state in (dict(current, total=budget['total']), current):
        state['logical_provider'] = provider
        with pytest.raises(ValueError,match='CAP_EXHAUSTED'):
            apply_runtime_event(state, 'PHYSICAL_INTENT', dict(physical,attempt_id='next'), ledger.identity)


def test_regular_kis_worker_can_reach_action_61_within_its_frozen_plan(tmp_path, monkeypatch):
    import time
    from app.services.selected_kis_sources import build_plan
    from scripts.kr8_kis_integration import FreshActions, action_plan
    from scripts.kis_estimate_capability_probe import Credentials, ProbeStop
    from tests.test_kr8_kis_integration import plan as historical_plan, rows, docs
    original = historical_plan()
    securities = dict(original['securities'])
    securities['123456'] = dict(securities[next(iter(securities))], ticker='123456',
        canonical_security_id='KR:123456', corp_code='00111111')
    args = dict(generation='DYNAMIC_KIS', as_of=original['as_of'], securities=securities, static_hashes={})
    with pytest.raises(ValueError, match='bounded_subjects'):
        build_plan(**args)
    regular = build_plan(**args, plan_derived_http=True)
    assert regular['maximum_physical_HTTP'] == 100
    subjects = sorted(securities)
    test_rows = [*rows(set(original['securities'])),
        dict(security_code='123456',eps=dict(state='UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE'))]
    actions = action_plan(test_rows, docs(), selected_subjects=subjects,
                          continuation_max=regular['action_continuation_max'])
    assert actions['maximum_data_calls'] == regular['action_data_max'] == 72
    requests = []
    def send(request):
        requests.append(request)
        return httpx.Response(200, json=dict(rt_cd='0', output1=[]), headers={'tr_cont':'D'})
    with httpx.Client(transport=httpx.MockTransport(send)) as client:
        probe = FreshActions(tmp_path, Credentials('fixture-key', 'fixture-secret'), client,
                             plan=actions, documentation=docs())
        monkeypatch.setattr(probe, 'disk_guard', lambda:None)
        probe.token, probe.last_finished, probe.data_count = 'fixture-token', time.monotonic()-2, 60
        probe.fetch(actions['requests'][0], '', 1)
        assert probe.data_count == 61 and len(requests) == 1
        probe.data_count = actions['maximum_data_calls']
        with pytest.raises(ProbeStop,match='SELECTED_ACTION_BUDGET'):
            probe.fetch(actions['requests'][1], '', 1)
        assert len(requests) == 1
