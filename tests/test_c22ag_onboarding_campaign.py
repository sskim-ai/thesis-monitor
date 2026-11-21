"""Scoped onboarding uses original validators and a mocked CLI, never live auth."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import json
import subprocess

import pytest

from app.services import onboarding_decision_service as service
from app.services import prospective_class_c_owner as approval_module
from app.services.accepted_decision_v2_runtime_service import AcceptedV2FundamentalCoreBatch, AcceptedV2ProductionBatchOutput
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.test_c22ag_registration_recovery import isolated_boundary


def ledger(tmp_path, *, maximum=14, onboarding=True):
    now = datetime.now(timezone.utc)
    approval = approval_module.record_backend_approval(approval_module.ApprovalDecision(
        event_id='C22AG_SYNTHETIC_ONLY', approved=True,
        user_message_sha256=digest('SYNTHETIC_NOT_REAL_APPROVAL'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(minutes=30),
        subjects=('TEST', '123456')))
    return SelectedRunLedger(path=tmp_path/'shared.jsonl', approval=approval,
        master_id='C22AG_SYNTHETIC', children={
            'us': dict(generation='SYNTHETIC_US', subjects=['TEST']),
            'kr': dict(generation='SYNTHETIC_KR', subjects=['123456'])},
        provider_caps={'sec_edgar': 2, 'kis': 2}, max_http=4, max_models=maximum,
        database_identity={'synthetic': True}, onboarding=onboarding)


def cli_fixture(monkeypatch, journal, *, mode='valid'):
    from tests.test_preconfirmation_decision_v2_service import (
        _packet, _candidate, _core, _runtime_owned_source_ref_payload, _reviewed_stage2_materialization_fixture,
    )
    packet, candidate = _packet(), _candidate()
    core = _core(candidate)
    fixture_context, _, _ = _reviewed_stage2_materialization_fixture()
    observed = dict(commands=[], context=fixture_context, packet=packet)
    original_builder = service.build_accepted_v2_production_context

    def context(**kwargs):
        value = original_builder(**kwargs)
        observed['context'] = value
        return value

    def fake_run(command, **kwargs):
        state = journal.state()
        assert state['pending'] and state['model_total'] >= 1
        assert command[command.index('-m')+1] == 'gpt-6.1-sol'
        assert 'model_reasoning_effort="high"' in command
        assert kwargs['timeout'] == 600
        assert 'features.shell_tool=false' in command
        observed['commands'].append(command)
        if mode == 'timeout':
            raise subprocess.TimeoutExpired(command, 600)
        output = Path(command[command.index('-o')+1])
        ctx = observed['context']
        if '.core.' in output.name:
            payload = AcceptedV2FundamentalCoreBatch(packet_id=ctx.packet_id,
                claim_id=ctx.claim_id, market=ctx.market, assessment_date=ctx.assessment_date,
                cores=(core,)).model_dump(mode='json')
            if mode == 'invalid_core':
                payload['cores'][0]['ticker'] = 'OTHER'
        else:
            typed = AcceptedV2ProductionBatchOutput(packet_id=ctx.packet_id, claim_id=ctx.claim_id,
                market=ctx.market, assessment_date=ctx.assessment_date,
                fundamental_cores=(core,), candidates=(candidate,))
            payload = _runtime_owned_source_ref_payload(typed)
            if mode == 'invalid_stage2':
                payload['candidates'][0]['new_buyer_axis']['reason']['evidence_refs'] = ['not:owned']
        output.write_text(json.dumps(payload), encoding='utf-8')
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(service, 'build_onboarding_decision_evidence_packet', lambda *a, **k: packet)
    monkeypatch.setattr(service, 'build_accepted_v2_production_context', context)
    monkeypatch.setattr(service, '_signed_in_codex_bin', lambda: '/synthetic/codex')
    monkeypatch.setattr(service, 'prepare_codex_runtime_state',
        lambda *a, **k: SimpleNamespace(environment=lambda: {'SYNTHETIC_ONLY': '1'}))
    monkeypatch.setattr(service.subprocess, 'run', fake_run)
    return observed


def execute_mock_pair(tmp_path, journal, observed):
    """Exercise the scoped CLI with named TEST_ONLY evidence, not current Source."""
    from app.services.accepted_decision_v2_runtime_service import (
        validate_accepted_v2_fundamental_core, validate_accepted_v2_candidate_ownership,
    )
    from app.services.onboarding_decision_service import validate_preconfirmation_candidate
    from app.services.reviewed_stage2_maturity_fixture import materialize_reviewed_stage2_fixture
    execution = service._CampaignOnboardingExecution(ledger=journal, profile=SOL_HIGH_V1,
        item=SimpleNamespace(ticker='TEST'), timeout=600, data_dir=tmp_path)
    root = tmp_path/'mock-cli'
    root.mkdir()
    prompt, schema = root/'prompt.txt', root/'schema.json'
    prompt.write_text('SYNTHETIC CLI CONTRACT INPUT', encoding='utf-8')
    schema.write_text(json.dumps(AcceptedV2FundamentalCoreBatch.model_json_schema()), encoding='utf-8')
    core_path = root/'response.core.json'
    try:
        execution.invoke(stage='CORE', prompt=prompt, schema=schema, output=core_path,
            log=root/'core.log', timeout=600, state_namespace='SYNTHETIC')
        batch = AcceptedV2FundamentalCoreBatch.model_validate_json(core_path.read_bytes())
        core = batch.cores[0]
        ownership = observed['context'].evidence_ownership[0]
        if validate_accepted_v2_fundamental_core(core, ownership):
            raise ValueError('SYNTHETIC_CORE_REJECTED_BY_ORIGINAL_VALIDATOR')
        execution.accept(core_path)
        output = root/'response.json'
        execution.invoke(stage='DECISION', prompt=prompt, schema=schema, output=output,
            log=root/'decision.log', timeout=600, state_namespace='SYNTHETIC')
        materialized = materialize_reviewed_stage2_fixture(observed['context'], json.loads(output.read_bytes()),
            fundamental_cores=(core,), subjects=('TEST',))
        candidate = materialized.candidates[0]
        if (not validate_preconfirmation_candidate(observed['packet'], candidate).valid
                or validate_accepted_v2_candidate_ownership(candidate, core, ownership)):
            raise ValueError('SYNTHETIC_STAGE2_REJECTED_BY_ORIGINAL_VALIDATOR')
        execution.accept(output)
        return dict(status='MOCK_CLI_AND_ORIGINAL_TYPED_VALIDATORS_PASS', current_Source_qualified=False)
    except BaseException as error:
        execution.fail(error)
        raise


def generate(tmp_path, journal):
    return service.generate_onboarding_accepted_decision(None, SimpleNamespace(ticker='TEST'),
        {'fingerprint': 'SYNTHETIC_INITIAL_EVIDENCE'}, timeout=600, data_dir=tmp_path,
        execution_profile=SOL_HIGH_V1, campaign_ledger=journal)


def test_sol_high_core_then_stage2_original_validators_and_cold_journal(tmp_path, monkeypatch):
    journal = ledger(tmp_path)
    observed = cli_fixture(monkeypatch, journal)
    result = execute_mock_pair(tmp_path, journal, observed)
    assert result['status'] == 'MOCK_CLI_AND_ORIGINAL_TYPED_VALIDATORS_PASS'
    assert result['current_Source_qualified'] is False
    assert len(observed['commands']) == 2
    cold = SelectedRunLedger.attach_worker(journal.worker_binding())
    assert cold.state()['onboarding_model_total'] == cold.state()['model_total'] == 2
    with pytest.raises(ValueError, match='already_attempted'):
        generate(tmp_path, cold)
    assert len(observed['commands']) == 2
    assert not list(tmp_path.rglob('*.repair.*'))


@pytest.mark.parametrize('mode,maximum_calls', [('invalid_core', 1), ('invalid_stage2', 2), ('timeout', 1)])
def test_rejected_or_timed_out_stage_never_repairs_or_promotes(tmp_path, monkeypatch, mode, maximum_calls):
    journal = ledger(tmp_path)
    observed = cli_fixture(monkeypatch, journal, mode=mode)
    with pytest.raises((ValueError, subprocess.TimeoutExpired)):
        execute_mock_pair(tmp_path, journal, observed)
    state = journal.state()
    assert state['pending'] is None and state['state'] == 'APPROVED_FROZEN_RUN'
    assert 'us:TEST' in state['onboarding_failed']
    assert len(observed['commands']) == state['model_total'] == maximum_calls
    assert not list(tmp_path.rglob('*.accepted.json')) and not list(tmp_path.rglob('*.repair.*'))
    failures = list(tmp_path.rglob('c22ag-failure-*.json'))
    assert len(failures) == 1 and json.loads(failures[0].read_bytes())['ready'] is False
    cold = SelectedRunLedger.attach_worker(journal.worker_binding())
    with pytest.raises(ValueError, match='already_attempted'):
        generate(tmp_path, cold)
    # An unrelated approved subject can still use its own first slot.
    key = cold.before_onboarding_model(market='kr', ticker='123456', stage='CORE', payload_sha256=digest('other'))
    cold.onboarding_model_result(key, ok=True, output_sha256=digest('other accepted'))
    assert len(observed['commands']) == maximum_calls


def test_shared_four_onboarding_plus_ten_monitoring_cap_and_http_counting(tmp_path):
    journal = ledger(tmp_path)
    for market, ticker in (('us','TEST'), ('kr','123456')):
        journal.bind_onboarding_http_plan(market=market, plan_sha256=digest(market),
            logical_ids=['profile', 'kis' if market == 'kr' else 'profile2'])
    for market, ticker in (('us','TEST'), ('kr','123456')):
        key = journal.before_onboarding_http(market=market,
            provider='kis' if market == 'kr' else 'sec_edgar', logical_id='profile', plan_sha256=digest(market))
        journal.result(key, ok=True)
        for stage in ('CORE','DECISION'):
            key = journal.before_onboarding_model(market=market, ticker=ticker,
                stage=stage, payload_sha256=digest((market,stage)))
            journal.onboarding_model_result(key, ok=True, output_sha256=digest((ticker,stage)))
    assert journal.state()['model_total'] == journal.state()['onboarding_model_total'] == 4
    assert journal.state()['http_total'] == 2
    with pytest.raises(ValueError, match='duplicate'):
        journal.before_onboarding_model(market='us', ticker='TEST', stage='CORE', payload_sha256=digest('retry'))
    # Drive existing ledger events with synthetic owned-plan receipts, no Owner grant.
    journal._event('DB_INTENT')
    journal._event('REGISTRATION', selects=5, receipt={'SYNTHETIC': True}, sha256=digest({'SYNTHETIC': True}))
    for market in ('us','kr'):
        journal._event('PLAN', market=market, sha256=digest(market))
    for market in ('us','kr'):
        journal._event('CAPTURE', market=market)
        journal._event('SOURCE', market=market, sha256=digest('synthetic owner shape'))
    for market in ('us','kr'):
        journal._event('MODEL_PLAN', market=market, sha256=digest('models:'+market), slots=5,
            slot_ids=[market+str(i) for i in range(5)])
    for market in ('us','kr'):
        for i in range(5):
            key = 'MODEL:'+market+str(i)
            journal._event('INTENT', key=key, kind='MODEL', market=market,
                slot=market+str(i), plan=digest('models:'+market))
            journal.result(key, ok=True)
    state = journal.state()
    assert state['model_total'] == 14 and state['monitoring_model_total'] == 10
    with pytest.raises(ValueError, match='scope_or_budget'):
        journal._event('INTENT', key='MODEL:UNPLANNED_15', kind='MODEL', market='us',
            slot='us0', plan=digest('models:us'))
    journal._event('RENDER', messages_sha256=digest('SYNTHETIC_FOUR_NOT_REAL_MESSAGES'))
    assert journal.state()['state'] == 'RENDERED_NO_SEND'


def test_inflight_intent_survives_restart_and_old_model_defaults_unchanged(tmp_path):
    journal = ledger(tmp_path)
    journal.before_onboarding_model(market='us', ticker='TEST', stage='CORE', payload_sha256=digest('pending'))
    cold = SelectedRunLedger.attach_worker(journal.worker_binding())
    with pytest.raises(ValueError, match='duplicate'):
        cold.before_onboarding_model(market='us', ticker='TEST', stage='CORE', payload_sha256=digest('pending'))
    assert cold.state()['model_total'] == 1 and cold.state()['pending'] is not None
    assert (service.REASONING_MODEL, service.REASONING_EFFORT) == ('gpt-5.6-sol', 'xhigh')
    legacy = ledger(tmp_path/'legacy', onboarding=False, maximum=10)
    assert 'onboarding' not in legacy.identity
    with pytest.raises(ValueError, match='duplicate_dependency_or_budget'):
        legacy.before_onboarding_model(market='us', ticker='TEST', stage='CORE', payload_sha256=digest('not approved'))


def test_unowned_onboarding_input_is_still_rejected_before_cli(tmp_path, monkeypatch):
    journal = ledger(tmp_path)
    observed = cli_fixture(monkeypatch, journal)
    with pytest.raises(ValueError, match='rejected_no_retry'):
        generate(tmp_path, journal)
    assert observed['commands'] == [] and journal.state()['model_total'] == 0
    assert not list(tmp_path.rglob('*.accepted.json'))


def test_c22ag_reconciler_passes_explicit_600_without_changing_other_defaults(tmp_path):
    import asyncio
    from sqlmodel import Session
    from tests.test_onboarding_reconciler_service import _engine, _seed_pending, _evidence_builder, _decision_builder
    from app.services.onboarding_reconciler_service import resume_onboarding_subject, OnboardingAttemptMode
    observed = []

    def synthetic_decision(*args, **kwargs):
        observed.append(kwargs['timeout'])
        return _decision_builder(*args, **kwargs)

    engine = _engine()
    with Session(engine) as session:
        item = _seed_pending(session, tmp_path, ticker='DEADLINE', exchange='NASDAQ')
        result = asyncio.run(resume_onboarding_subject(session, item, origin='C22AG_SYNTHETIC',
            mode=OnboardingAttemptMode.BACKGROUND, data_dir=tmp_path,
            evidence_builder=_evidence_builder, decision_builder=synthetic_decision,
            decision_timeout_seconds=600))
    assert observed == [600] and result.active


def test_real_profile_client_and_kis_wire_share_count_before_mock_send(tmp_path):
    import asyncio
    import httpx
    from app.services.selected_run_lifecycle import OnboardingCampaignTransport
    from app.services.company_profile_service import SecCompanyProfileSource
    journal = ledger(tmp_path)
    routes = [dict(logical_id='profile-list', provider='sec_edgar', method='GET', host='www.sec.gov', path='/files/company_tickers.json'),
        dict(logical_id='profile-detail', provider='sec_edgar', method='GET', host='data.sec.gov', path='/submissions/CIK0000000001.json')]
    kis_routes = [dict(logical_id='kis-extra', provider='kis', method='GET', host='openapi.koreainvestment.com', path='/synthetic-estimate')]
    for market, selected in (('us',routes), ('kr',kis_routes)):
        journal.bind_onboarding_http_plan(market=market, plan_sha256=digest(selected),
            logical_ids=[r['logical_id'] for r in selected])
    sent = []

    def mock_send(request):
        assert journal.state()['pending'] and journal.state()['http_total'] == len(sent)+1
        sent.append(request.url.path)
        if request.url.path.endswith('company_tickers.json'):
            return httpx.Response(200, json={'0': {'ticker':'TEST', 'cik_str':1}})
        if request.url.path.endswith('.json'):
            return httpx.Response(200, json=dict(tickers=['TEST'], sic='3674', name='Test Company', filings={}))
        return httpx.Response(200, json={'SYNTHETIC_ONLY': True})

    inner = httpx.MockTransport(mock_send)
    us = OnboardingCampaignTransport(ledger=journal, market='us', plan_sha256=digest(routes), routes=routes, inner=inner)
    kr = OnboardingCampaignTransport(ledger=journal, market='kr', plan_sha256=digest(kis_routes), routes=kis_routes, inner=inner)

    async def run():
        profile = await SecCompanyProfileSource('SYNTHETIC UA', transport=us).fetch(SimpleNamespace(ticker='TEST',company_name='Test'), None)
        assert profile is not None and profile.source == 'sec_submissions'
        async with httpx.AsyncClient(transport=kr) as client:
            await client.get('https://openapi.koreainvestment.com/synthetic-estimate')
            with pytest.raises(ValueError, match='duplicate_or_parallel'):
                await client.get('https://openapi.koreainvestment.com/synthetic-estimate')
    asyncio.run(run())
    assert len(sent) == journal.state()['http_total'] == 3
    assert journal.state()['http'] == {'sec_edgar':2, 'kis':1}
    assert journal.state()['model_total'] == 0
