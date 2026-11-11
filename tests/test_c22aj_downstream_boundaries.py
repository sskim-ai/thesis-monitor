"""Changed C22AJ boundaries only. Mock CLI/transport are not live Source PASS."""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

from app.services import prospective_class_c_owner as approvals
from app.services.campaign_runtime_cap import RuntimeCap, MeteredAsyncTransport, CampaignOhlcvTransport
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest


def journal(tmp_path):
    now = datetime.now(timezone.utc)
    approval = approvals.record_backend_approval(approvals.ApprovalDecision(
        event_id='C22AJ_SYNTHETIC_NOT_LIVE', approved=True, user_message_sha256=digest('TEST_ONLY'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(hours=1), subjects=('TEST', '123456')))
    endpoint = dict(methods=['GET', 'POST'], host='wire.test', prefix='/', endpoint='MOCK')
    return SelectedRunLedger(path=tmp_path/'shared.jsonl', approval=approval, master_id='C22AJ_SYNTHETIC',
        children={'us': dict(generation='TEST_US', subjects=['TEST']),
            'kr': dict(generation='TEST_KR', subjects=['123456'])},
        provider_caps={'kiwoom': 10, 'kis': 10}, max_http=20, max_models=14,
        database_identity={'synthetic': True}, onboarding=True,
        runtime_cap={'endpoints': {'kiwoom': [endpoint], 'kis': [dict(endpoint, host='second.test')]},
            'stop_on_first_external_failure': True, 'market_subjects': {'us': ['ETF_TEST']}},
        wallclock_seconds_max=3600)


def test_first_external_failure_blocks_other_provider_and_model_cold(tmp_path):
    ledger = journal(tmp_path)
    calls = []
    async def run():
        transport = MeteredAsyncTransport(binding=ledger.worker_binding(), market='us', subject='TEST',
            inner=httpx.MockTransport(lambda r: calls.append(r.url.host) or httpx.Response(503)))
        await transport.handle_async_request(httpx.Request('GET', 'https://wire.test/one'))
        with pytest.raises(ValueError, match='CAP_EXHAUSTED'):
            await transport.handle_async_request(httpx.Request('GET', 'https://second.test/two'))
    asyncio.run(run())
    cold = SelectedRunLedger.attach_worker(ledger.worker_binding())
    with pytest.raises(ValueError, match='external_failure_blocks_model'):
        cold.before_onboarding_model(market='us', ticker='TEST', stage='CORE', payload_sha256=digest('mock'))
    assert calls == ['wire.test'] and cold.state()['http_total'] == 1 and cold.state()['model_total'] == 0
    assert RuntimeCap(ledger.worker_binding()).state()['first_external_failure']


def test_source_local_get_meters_lower_post_only_and_scope_stays_bound(tmp_path):
    ledger = journal(tmp_path)
    cap = RuntimeCap(ledger.worker_binding())
    def local(request):
        if request.method == 'OPTIONS':
            return httpx.Response(200, json={'campaign_budget_protocol': 'selected-run-physical-cap-v1'})
        assert 'X-Campaign-Budget' in request.headers
        key = cap.reserve(provider='kiwoom', method='POST', host='wire.test', path='/chart',
            market='us', subject='ETF_TEST', phase='SOURCE', owner='MockOriginalWorker', request_sha256=digest('one'))
        cap.dispatched(key); cap.finish(key, status=200)
        return httpx.Response(200, json={'SYNTHETIC_NOT_SOURCE': True})
    async def run():
        transport = CampaignOhlcvTransport(binding=ledger.worker_binding(), market='us', subject='ETF_TEST',
            phase='SOURCE', inner=httpx.MockTransport(local))
        await transport.handle_async_request(httpx.Request('GET', 'http://127.0.0.1:8765/ohlcv?symbol=ETF_TEST'))
        bad = CampaignOhlcvTransport(binding=ledger.worker_binding(), market='us', subject='OTHER',
            phase='SOURCE', inner=httpx.MockTransport(local))
        with pytest.raises(ValueError, match='SUBJECT_OUTSIDE'):
            await bad.handle_async_request(httpx.Request('GET', 'http://127.0.0.1:8765/ohlcv?symbol=OTHER'))
    asyncio.run(run())
    assert ledger.state()['http_total'] == 1


def test_onboarding_mock_core_stage2_original_validators_share_ledger(tmp_path, monkeypatch):
    from tests.test_c22ag_onboarding_campaign import cli_fixture, execute_mock_pair
    ledger = journal(tmp_path)
    observed = cli_fixture(monkeypatch, ledger)
    result = execute_mock_pair(tmp_path, ledger, observed)
    assert result['current_Source_qualified'] is False
    assert len(observed['commands']) == ledger.state()['model_total'] == 2
    assert not list(tmp_path.rglob('*.repair.*'))


def test_source_owner_and_four_panel_render_not_granted_by_chart_reference():
    from app.services.research_no_send_run import MarketResearchChild, MasterFourPanelManifest
    owner_calls = []
    class Cohort:
        market_subjects = {'us': ['TEST']}
        run_id = 'SYNTHETIC'
        def verify_source_owner(self, owner):
            owner_calls.append(owner)
            raise ValueError('ORIGINAL_SOURCE_OWNER_REQUIRED')
    plan = SimpleNamespace(validate=lambda: None, topology='CANONICAL_PRODUCTION', cohort=Cohort())
    child = MarketResearchChild(plan=plan, owner={'dated_reference_price': 123})
    with pytest.raises(ValueError, match='ORIGINAL_SOURCE_OWNER_REQUIRED'):
        child.verify()
    assert owner_calls
    with pytest.raises(ValueError, match='distinct_market_children'):
        MasterFourPanelManifest('SYNTHETIC', ()).combine({})


def test_nonstring_reference_proof_rejected_as_data_error():
    from app.services.dated_chart_reference import validate_reference
    with pytest.raises(ValueError, match='source_or_market_invalid'):
        validate_reference({}, {'response_body': {}, 'observed_at': '', 'analysis_cutoff': ''}, ticker='TEST', market='us')


def test_original_auth_reused_in_new_prepared_child_with_cold_count(tmp_path):
    ledger = journal(tmp_path)
    script = Path(__file__).resolve().parents[3]/'maintenance/20261112-c22aj-v1/external_mock_probe.py'
    result = subprocess.run([sys.executable, '-B', str(script)],
        input=json.dumps({'binding': ledger.worker_binding(), 'posts': 0, 'auth_reuse': True}),
        capture_output=True, text=True, timeout=30, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['status'] == 200 and report['lower_mock_POST'] == report['reserved'] == 1
    assert report['lane_stopped'] is False and report['real_HTTP'] == 0
    assert SelectedRunLedger.attach_worker(ledger.worker_binding()).state()['http_total'] == 1


def test_cycle_requires_original_committed_activation_not_dated_price():
    from app.services.unified_cycle_owner import capture_reconciler_activation
    session = SimpleNamespace(new=(), dirty=(), deleted=())
    item = SimpleNamespace(active=False, production_eligible=False, onboarding_state='PENDING')
    with pytest.raises(ValueError, match='committed_original_activation_required'):
        capture_reconciler_activation(session, item, market='us', writer_at=datetime.now(timezone.utc))
