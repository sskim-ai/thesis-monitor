"""Real seven-axis adapter under the existing controller, entirely offline."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.services.unified_snapshot_contract import digest, encoded
from scripts import strict_blind_adapter as adapter
from scripts import strict_blind_contract as contract
from scripts import strict_blind_comparison as comparison
from scripts import scoped_attempt_failure as failure
from scripts.strict_blind_controller import StrictBlindController, ControllerError
from scripts.strict_blind_offline_proof import fixture, host_for
from tests.strict_blind_fixtures import source_inputs, response


def prepared(root):
    inp = source_inputs(root/'sources')
    generation = "INVENTED-OFFLINE-GENERATION"
    source = dict(generation=generation, blind_inputs={inp['ticker']: inp})
    old, _, code = fixture(root/'host-only', subjects=[inp['ticker']])
    c = StrictBlindController.create(root/'real-controller', generation=generation,
        plan=old.contract['plan'], host_preparation=old.contract['host_preparation'],
        declared_host_transitions=['CODEX_SANDBOX'],
        code_files=[code, __file__, adapter.__file__, contract.__file__, comparison.__file__])
    adapter.register(c)
    c.seal_pre_source(adapter.authorities(c.contract['plan'], dict(slots=c.contract['plan']['source_slots'])))
    c.admit_source('source-one', simulated=True)
    c.seal_source(source, dict(status='PASS', generation=generation, source_sha256=digest(source)))
    c.seal_blind_package(contract.package(source), validate_source_only=contract.validate_package)
    request = adapter.build_requests(c)[0]
    c.seal_requests('BLIND', [request])
    validation = adapter.BlindValidation(request, inp)
    return c, request, validation


def attempt(c, request, validation, raw):
    host, context, _ = host_for(c, request)
    def transport(payload):
        assert payload == encoded(request['payload'])
        return encoded(raw)
    return c.attempt('BLIND', request, host=host, context=context, transport=transport,
        provider_validate=validation.provider, semantic_validate=validation.semantic, simulated=True)


def test_real_blind_schema_raw_first_and_declared_view_isolation(tmp_path, monkeypatch):
    import socket
    import subprocess
    def deny(*args, **kwargs):
        pytest.fail('External I/O in offline adapter test')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket.socket, 'connect_ex', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(subprocess, 'Popen', deny)
    c, request, validation = prepared(tmp_path)
    raw = response(validation.subject, validation.audit)
    assert attempt(c, request, validation, raw)['status'] == 'PASS'
    events = [json.loads(p.read_bytes())['event'] for p in sorted((c.root/'journal').glob('*.json'))]
    assert events.index('RAW_DURABLE_BEFORE_VALIDATION') < events.index('ATTEMPT_VALIDATED')
    c.seal_stage('BLIND')
    with pytest.raises(ControllerError, match='FORBIDDEN_CONTEXT_READ'):
        c.view('AI', ['outputs_BLIND'])
    with pytest.raises(ControllerError, match='BLIND_REQUIRES_ALLOWLIST_PACKAGE'):
        c.view('BLIND', ['source'])
    c.materialize_view('AI', ['source'], tmp_path/'ai-input')
    assert 'outputs_BLIND' not in (tmp_path/'ai-input/context.json').read_text()
    with pytest.raises(ControllerError, match='STAGE_ALREADY_SEALED'):
        attempt(c, request, validation, raw)
    with pytest.raises(ControllerError, match='EARLY_REVEAL'):
        c.reveal()
    assert not c.data['strict_run_started']


def test_semantic_reject_cannot_be_retried_with_real_contract(tmp_path):
    c, request, validation = prepared(tmp_path)
    raw = response(validation.subject, validation.audit)
    raw['axes']['new_buyer']['judgment'] = 'WAIT'
    receipt = attempt(c, request, validation, raw)
    assert receipt['provider_schema_status'] == 'PASS'
    assert receipt['failure_class'] == failure.SEMANTIC and not receipt['retry_eligible']
    with pytest.raises(ControllerError, match='TERMINAL_FAIL_STOP'):
        attempt(c, request, validation, raw)


def test_frozen_request_mutation_and_extra_view_rejected(tmp_path):
    c, request, _ = prepared(tmp_path)
    host, context, _ = host_for(c, request)
    changed = deepcopy(request)
    changed['payload']['prompt'] += ' mutation'
    with pytest.raises(ControllerError):
        c.authorize('BLIND', changed, host=host, context=context)
    view = c.view('BLIND', ['blind_package','blind_rubric','blind_prompt','blind_schema'])
    view['historical'] = {'judgment':'BUY'}
    with pytest.raises(ValueError, match='UNDECLARED_VIEW'):
        adapter.BlindSubjectAdapter(request['subjects'][0]).build(view)


def test_static_source_adapter_has_no_ticker_rules_or_historical_dependencies():
    import ast
    forbidden = {'CORZ','CPNG','CRCL','GOOGL','HUT','IBM','MU','RXRX','SKHY','SNDK',
        'TSLA','TSM','WRD','WULF','000660','003690','005490','005930','010120','012450','047810','086280'}
    for module in (adapter, contract, comparison):
        tree = ast.parse(Path(module.__file__).read_text())
        strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not forbidden.intersection(strings)
        assert not any('/Reports/' in s or 'rev58e-result' in s for s in strings)
        assert not any(isinstance(n, ast.ImportFrom) and n.module and n.module.startswith('tests') for n in ast.walk(tree))
    assert comparison.AUTHORITY['agreement_threshold'] is None
    assert comparison.AUTHORITY['compatible_pairs'] == []


def test_native_plan_preserves_22_subjects_and_market_scope():
    from scripts.strict_blind_run_plan import execution_plan
    plan = execution_plan(['sealed-slot'])
    assert {k: len(v) for k,v in plan['stages'].items()} == dict(BLIND=22, MARKET=2, CORE=8, A=8, B=8, B2=22)
    for stage in ('BLIND','B2'):
        assert len({s['subjects'][0] for s in plan['stages'][stage]}) == 22
        assert all(s['scope']=='SUBJECT_SCOPED' and len(s['subjects'])==1 for s in plan['stages'][stage])
    assert all(s['scope']=='MARKET_SCOPED' and not s['subjects'] for s in plan['stages']['MARKET'])


def test_native_replay_tuple_json_parity_without_reordering():
    from scripts.strict_blind_monitoring import NativeSession
    session = NativeSession.__new__(NativeSession)
    session.market = 'US'
    seen = []
    requests = {'MARKET': [dict(subjects=[])], 'CORE': [dict(subjects=('SYN_A', 'SYN_B'))]}
    session.capture = lambda stage: requests[stage]
    session.accept = lambda stage, request, output: seen.append(stage)
    view = dict(outputs_MARKET=[dict(market='US',subjects=[],output={})],
        outputs_CORE=[dict(market='US',subjects=['SYN_A','SYN_B'],output={})])
    session.replay('A',view)
    assert seen == ['MARKET','CORE']
    view['outputs_CORE'][0]['subjects'].reverse()
    with pytest.raises(ValueError, match='SUBJECT_DRIFT'):
        session.replay('A',view)
