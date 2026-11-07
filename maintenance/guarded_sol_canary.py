"""Original manual host/Stage journals around one guarded Sol stage, default off."""
from contextlib import nullcontext
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import time

from app.services import vnext_balanced_stage_review as stages
from app.services.vnext_execution_profile import SOL_HIGH_V1
from app.services.vnext_no_send_runner import run_manual_research
from app.services.vnext_research_store import digest
from maintenance.guarded_sol_host import execute, require_request, write_once


def run_stage(*, binding, config, packet, registry, source_loader, economic_loader,
              valuation_analysis_owner, request, knowledge, approval, account_lease,
              session, prior_session, out, prior=None, enabled=False):
    if not enabled:
        raise ValueError('canary_default_off')
    if not all(callable(v) for v in (approval, account_lease, source_loader, economic_loader)):
        raise ValueError('trusted_backend_callbacks_required')
    if approval(deepcopy(request)) is not True or source_loader() != packet:
        raise ValueError('fresh_request_grant_and_original_source_required')
    name = request['stage']; invocation = request['invocation_id']; account = request['account']
    current, text = stages._stage_request(invocation_id=invocation, account=account, packet=packet,
        stage=name, version=stages.UNIFIED_AI_V3_SOL_HIGH, knowledge=knowledge,
        registry=registry, prior=prior)
    if current != request:
        raise ValueError('frozen_stage_request_changed')
    schema = stages.output_schema(packet, stages.UNIFIED_AI_V3_SOL_HIGH)
    require_request(request, text, schema, packet, binding.verify())
    identity = dict(account_scope=account, security=request['security']['canonical_security_id'], frozen_input_sha256=digest(packet))
    scope = dict(mode='MANUAL_RESEARCH_CANARY', market=request['security']['country'].lower(),
        session=session, prior_session=prior_session, kind='EXISTING_SUBJECT_SUCCESSOR', identity=identity,
        plan_sha256=digest(request), expires_at=(datetime.now(timezone.utc) + timedelta(seconds=600)).isoformat())
    out.mkdir(mode=0o700)
    write_once(out / 'MODEL_REQUEST.json', request)
    write_once(out / 'MANUAL_HOST_SCOPE.json', scope)
    def approve_host():
        return digest(scope) if approval(deepcopy(request)) is True and source_loader() == packet else None
    def operation(original, gate):
        controller = stages.StageController(config, enabled=True, execution_profile=SOL_HIGH_V1)
        controller._host_slot_guard = original._host_slot_guard
        controller._host_recovery_guard = original._host_recovery_guard
        def invoke(req, prompt, deadline):
            execution = dict(stage=name, status='STARTED', started=time.time(), deadline=deadline,
                attempt=1, retry=0, model=SOL_HIGH_V1.model, effort=SOL_HIGH_V1.effort,
                execution_profile=SOL_HIGH_V1.contract, stage_contract=stages.execution_contract(stages.UNIFIED_AI_V3_SOL_HIGH),
                prompt_version=stages.UNIFIED_AI_V3_SOL_HIGH, invocation_id=invocation,
                request_sha=digest(req), approved_request_sha=digest(request), packet_sha=digest(packet),
                prompt_sha=digest(prompt.encode()), schema_sha=digest(schema))
            write_once(out / 'MODEL_STARTED.json', execution)
            try:
                output, runtime = execute(binding, request=req, prompt=prompt, schema=schema, packet=packet,
                    owner_check=lambda: approval(deepcopy(req)) is True and source_loader() == packet,
                    deadline=deadline, out=out)
                execution.update(runtime=runtime, exit=0, ended=time.time())
                validation = stages._engine(stages.UNIFIED_AI_V3_SOL_HIGH).validate_and_render(output, packet,
                    registry=registry, economic_loader=economic_loader, valuation_analysis_owner=valuation_analysis_owner)
                stages._engine(stages.UNIFIED_AI_V3_SOL_HIGH).validate_transition(output, prior.snapshot()['output'] if prior else None)
                execution.update(status='VALIDATED', output_sha=digest(output))
                return dict(output=output, validation=validation, execution=execution)
            except Exception as exc:
                execution.update(status='FAILED_NO_RETRY', error_type=type(exc).__name__)
                raise
            finally:
                execution['ended'] = time.time()
                write_once(out / 'MODEL_FINISHED.json', execution)
        accepted = controller.run_stage(invocation_id=invocation, account=account, packet=packet,
            stage=name, version=stages.UNIFIED_AI_V3_SOL_HIGH, knowledge=knowledge, registry=registry,
            source_loader=source_loader, approval=approval, account_lease=nullcontext,
            invoke=invoke, prior=prior, economic_loader=economic_loader,
            valuation_analysis_owner=valuation_analysis_owner)
        row = accepted.snapshot()
        write_once(out / 'CHILD_ACCEPTED_STAGE.json', row)
        return dict(send=False, input_identity=identity, state='ACCEPTED_RESEARCH_STAGE', stage=name, record_sha=digest(row))
    with account_lease():
        result = run_manual_research(config, scope=scope, identity=identity, approval=approve_host,
            operation=operation, enabled=True, timeout_seconds=600, execution_profile=SOL_HIGH_V1)
        write_once(out / 'HOST_RESULT.json', result)
        if result['state'] != 'COMPLETED_NO_SEND':
            return None, result
        # The parent never trusts the child's in-memory object or a success JSON.
        controller = stages.StageController(config, enabled=True, execution_profile=SOL_HIGH_V1)
        def approve_restore(grant):
            return (grant.get('contract') == 'ACCEPTED_STAGE_PARENT_RECONSUMPTION_V1'
                and grant.get('stage_request') == request and grant.get('host_attempt') == result['attempt']
                and grant.get('original_scope_sha256') == digest(scope)
                and grant.get('new_model_calls') == 0 and approval(deepcopy(request)) is True)
        accepted = controller.restore_stage(invocation_id=invocation, account=account, packet=packet,
            stage=name, version=stages.UNIFIED_AI_V3_SOL_HIGH, knowledge=knowledge, registry=registry,
            source_loader=source_loader, approval=approve_restore, account_lease=nullcontext,
            host_scope=scope, host_attempt=result['attempt'], prior=prior,
            economic_loader=economic_loader, valuation_analysis_owner=valuation_analysis_owner)
        write_once(out / 'PARENT_RESTORED_STAGE.json', accepted.snapshot())
        return accepted, result
