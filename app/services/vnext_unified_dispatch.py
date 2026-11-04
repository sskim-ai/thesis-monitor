"""Shared immutable journal consumer, using existing stage/source capabilities."""
from copy import deepcopy

from app.services import vnext_unified_judgment as engine
from app.services.vnext_balanced_stage_review import StageReviewOwner, UNIFIED, UNIFIED_AI_VERSIONS, output_contract
from app.services.vnext_no_send_controller import NoSendController
from app.services.vnext_research_store import digest


def consume(controller, *, packet, owner, mode, output_context, enabled=False):
    if not enabled or not isinstance(controller, NoSendController) or not controller.enabled:
        raise ValueError('unified_dispatch_default_off')
    if controller.config.environment != 'test' or controller.config.mode != 'write':
        raise ValueError('unified_isolated_no_send_only')
    if (type(owner) is not StageReviewOwner or owner.blind.version not in (UNIFIED, *UNIFIED_AI_VERSIONS)
            or owner.adjudication.version != owner.blind.version or packet.get('contract') != output_contract(owner.blind.version)):
        raise ValueError('unified_original_two_stage_owner_required')
    if mode not in ('DATED_REPLAY','DAILY_NO_SEND'):
        raise ValueError('unified_no_send_modes_only')
    controller._check_host_recovery()
    receipt = owner.issue()
    checked = owner.consume(receipt, packet=packet)
    # The accepted snapshots revalidate exact code-version/prompt/source and both
    # stages on every read. A JSON receipt or cache hash cannot grant authority.
    model_record = owner.dependency_record()
    contract = output_contract(owner.blind.version)
    if contract in UNIFIED_AI_VERSIONS:
        # An unissued schema-valid candidate cannot self-declare ASTRA_ADJ.
        # Only the original live two-stage Owner reaches this issuance boundary.
        checked = deepcopy(checked)
        checked['decision'].update(decision_source='ASTRA_ADJ',model_receipt=dict(
            stage_owner=deepcopy(receipt), adjudication_execution=deepcopy(model_record['stages']['ADJUDICATION']['execution']),
            model_output_sha256=digest(model_record['stages']['ADJUDICATION']['output'])))
        checked['decision_sha256'] = digest(checked['decision'])
        checked['rendered'] = engine.render(checked['decision'])
    request = dict(contract=contract, packet_sha256=digest(packet),
        knowledge_sha256=digest(owner.blind.knowledge), stage_record_sha256=digest(model_record))
    name = 'unified-decision-'+digest(request)[:40]
    record = dict(validation=checked,stage_receipt=deepcopy(receipt),
        stage_record_sha256=digest(model_record),send=False)
    previous = controller._read(name, request)
    if previous is not None and previous != record:
        raise ValueError('unified_immutable_decision_conflict')
    if previous is None:
        controller._append(name,request,record)
    eligibility = engine.output_eligibility(checked['decision'],mode=mode,**output_context)
    return dict(state='UNIFIED_DECISION_NO_SEND',contract=contract,
        packet_sha256=request['packet_sha256'],
        decision_sha256=checked['decision_sha256'],decision=deepcopy(checked['decision']),
        output_eligibility=eligibility,message=checked['rendered'],
        reused=previous is not None,send=False,strict_ready=False)
