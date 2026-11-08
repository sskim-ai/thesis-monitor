"""Synthetic records exercise the original validators; no live acceptance claims."""
from copy import deepcopy
from dataclasses import replace
from contextlib import nullcontext
import os
import pytest

from app.services import vnext_balanced_stage_review as stage
from app.services.vnext_execution_profile import SOL_HIGH_V1, SOL_MEDIUM_V1, require_profile
from maintenance.guarded_sol_host import MEDIUM_TASK, require_request, terminal_diagnostic
from test_guarded_sol_host import subject
from test_c10r_sol_profile import arguments
from test_vnext_axis_evidence_roles import setup
from test_vnext_balanced_stage_review import MemoryController
from app.services.vnext_research_store import ResearchStore, digest
from app.services.vnext_runtime import RuntimeConfig
from maintenance.guarded_sol_canary import run_stage
from maintenance.sol_medium_canary import validate_authorization


def test_medium_blind_original_validation_and_profile_cannot_be_relabelled(monkeypatch):
    a = setup(monkeypatch)
    controller = MemoryController()
    controller.execution_profile = SOL_MEDIUM_V1
    kwargs = arguments(a, controller, version=stage.UNIFIED_AI_V3_SOL_MEDIUM)
    accepted = controller.run_stage(**kwargs)
    assert accepted.snapshot()['execution']['effort'] == 'medium'
    assert stage.output_schema(a[3], stage.UNIFIED_AI_V3_SOL_MEDIUM) == stage.output_schema(a[3], stage.UNIFIED_AI_V3_SOL_HIGH)
    with pytest.raises(ValueError, match='medium_blind_only'):
        controller.run_stage(**arguments(a, controller, name='ADJUDICATION', prior=accepted, version=stage.UNIFIED_AI_V3_SOL_MEDIUM))
    with pytest.raises(ValueError, match='VERSION_MISMATCH_PRECALL'):
        controller.run_stage(**arguments(a, controller, name='ADJUDICATION', prior=accepted))
    with pytest.raises(ValueError, match='two_stage_capabilities'):
        stage.StageReviewOwner(accepted, accepted, enabled=True)
    with pytest.raises(ValueError, match='exact_supported'):
        require_profile(replace(SOL_HIGH_V1, effort='medium'))


def test_medium_host_requires_new_scope_profile_and_blind_only():
    request, prompt, schema, packet, scope = subject()
    scope.update(task=MEDIUM_TASK, execution_profile=SOL_MEDIUM_V1.contract)
    request.update(effort='medium', execution_profile=SOL_MEDIUM_V1.contract,
        prompt_version=stage.UNIFIED_AI_V3_SOL_MEDIUM, contract=stage.execution_contract(stage.UNIFIED_AI_V3_SOL_MEDIUM))
    require_request(request, prompt, schema, packet, scope)
    for changed in (dict(effort='high'), dict(execution_profile=SOL_HIGH_V1.contract),
                    dict(stage='ADJUDICATION', prior_stage_sha='synthetic'), dict(retries=1)):
        with pytest.raises(ValueError):
            require_request(dict(request, **changed), prompt, schema, packet, scope)
    with pytest.raises(ValueError):
        require_request(request, prompt, schema, packet, dict(scope, task='C21H'))


def test_terminal_diagnostic_does_not_copy_free_text_or_secrets():
    completion = dict(status='failed', error=dict(message='Bearer SYNTHETIC_SECRET https://private.invalid',
        codexErrorInfo=dict(httpConnectionFailed=dict(httpStatusCode=400, authorization='SYNTHETIC_SECRET'))))
    value = terminal_diagnostic(completion)
    assert value['error_info'] == dict(httpConnectionFailed=dict(httpStatusCode=400))
    assert 'SYNTHETIC_SECRET' not in str(value) and 'private.invalid' not in str(value)
    assert terminal_diagnostic(None)['status'] == 'unknown'


def test_medium_real_fork_original_journal_and_parent_restore(monkeypatch, tmp_path):
    from test_vnext_ai_owned_judgment import setup as economic_setup, opinion
    from app.services import vnext_unified_judgment as engine
    economic, _, _, registry = economic_setup()
    packet = engine.build_bundle(economic, registry=registry, contract=engine.AI_OWNED_V3)
    value = opinion(packet, 'HOLD', 'WAIT', 'REVIEW')
    value.update(contract=engine.AI_OWNED_V3, policy_sha256=packet['policy_sha256'])
    database = (tmp_path/'research.sqlite3').resolve()
    ResearchStore(database)
    config = RuntimeConfig(database, 'SYNTHETIC_MEDIUM', 'write', 'test')
    request, _ = stage._stage_request(invocation_id='SYNTHETIC_MEDIUM_BLIND', account='SYNTHETIC_ACCOUNT',
        packet=packet, stage='BLIND', version=stage.UNIFIED_AI_V3_SOL_MEDIUM, knowledge={}, registry=registry, prior=None)
    class Binding:
        execution_profile = SOL_MEDIUM_V1.contract
        def verify(self):
            return dict(task=MEDIUM_TASK, execution_profile=self.execution_profile,
                account=request['account'], security=request['security']['canonical_security_id'],
                owner_sha256=digest(packet), source_generation=request['source_as_of'])
    parent = os.getpid()
    def synthetic(binding, **kwargs):
        assert os.getpid() != parent
        assert kwargs['request'] == request and kwargs['owner_check']()
        return deepcopy(value), dict(verified=True, session='SYNTHETIC_MEDIUM_BLIND')
    monkeypatch.setattr('maintenance.guarded_sol_canary.execute', synthetic)
    cap, result = run_stage(binding=Binding(), config=config, packet=packet, registry=registry,
        source_loader=lambda: deepcopy(packet), economic_loader=lambda: economic,
        valuation_analysis_owner=None, request=request, knowledge={}, approval=lambda r: r == request,
        account_lease=nullcontext, session='2026-10-28', prior_session='2026-10-27', out=tmp_path/'stage', enabled=True)
    assert result['state'] == 'COMPLETED_NO_SEND'
    assert result['child_pid'] != parent
    assert cap.snapshot()['execution']['execution_profile'] == SOL_MEDIUM_V1.contract
    assert (tmp_path/'stage/PARENT_RESTORED_STAGE.json').is_file()


def test_medium_authorization_rejects_old_high_or_expanded_scope():
    scope = dict(run_id='SOL_MEDIUM_BLIND_SYNTHETIC', request_sha256='a'*64)
    auth = dict(task=MEDIUM_TASK, approved=True, confirmed_no_concurrent_use=True,
        run_id=scope['run_id'], scope_sha256=digest(scope), request_sha256=scope['request_sha256'],
        head='b'*40, model=SOL_MEDIUM_V1.model, effort=SOL_MEDIUM_V1.effort,
        execution_profile=SOL_MEDIUM_V1.contract, maximum_contexts=1, BLIND=1, ADJ=0,
        stage_seconds=600, input_bytes=393216, output_bytes=131072, retries=0,
        financial_HTTP=0, operating_DB=0, send=False, approval_basis='SYNTHETIC')
    validate_authorization(auth, scope, 'b'*40)
    for change in (dict(effort='high'), dict(ADJ=1), dict(maximum_contexts=2), dict(head='c'*40)):
        with pytest.raises(ValueError):
            validate_authorization(dict(auth, **change), scope, 'b'*40)
