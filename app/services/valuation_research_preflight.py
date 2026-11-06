"""Opt-in valuation entrypoint: static routing before ephemeral authority.

The backend callback supplies existing genuine capabilities, not JSON approval.
This entrypoint neither loads credentials nor changes the original Parent cap.
"""
from app.services.retained_identity_routing import retained_listing_rows
from app.services.registered_valuation_source_parent import compile_plan, issue_parent
from app.services.registered_valuation_source_intent import require_intent
from app.services.vnext_research_store import digest


def prepare_registered_valuation(*, routing_root, identities, generation_id,
        cutoff, code_sha, provider_config_sha256, acquire_current_context=None, enabled=False):
    if enabled is not True:
        raise ValueError('valuation_preflight_explicit_enable_required')
    rows=retained_listing_rows(routing_root)
    wire=compile_plan(identities=identities,listing_rows=rows,generation_id=generation_id,
        cutoff=cutoff,code_sha=code_sha,provider_config_sha256=provider_config_sha256)
    plan=wire['request_plan']
    receipt=dict(contract='valuation-prewire-static-v1',plan_sha256=plan.plan_sha256,
        identity_sha256=digest(identities),routing_rows_sha256=digest(rows),
        planned_attempts=sum(d.max_transport_attempts for d in plan.descriptors),
        maximum_attempts=19,source_use=False,economic_use=False,model=False,send=False)
    if acquire_current_context is None:
        return dict(status='PREFLIGHT_PASS_LIVE_SCOPE_NOT_ISSUED',receipt=receipt,wire=wire,parent=None)
    if not callable(acquire_current_context):
        raise ValueError('valuation_backend_context_callback_required')
    context=acquire_current_context()
    current=require_intent(context['intent'],generation_id=context['intent_generation'],
        provider='kiwoom',subjects=tuple(identities))
    if current!=identities:
        raise ValueError('valuation_preflight_current_identity_changed')
    parent,actual=issue_parent(intent=context['intent'],intent_generation=context['intent_generation'],
        subjects=tuple(identities),listing_rows=rows,session=context['session'],generation_id=generation_id,
        cutoff=cutoff,code_sha=code_sha,provider_config_sha256=provider_config_sha256,enabled=True)
    if actual['request_plan'].plan_sha256!=plan.plan_sha256:
        raise ValueError('valuation_preflight_plan_changed')
    return dict(status='ORIGINAL_PARENT_ISSUED_SOURCE_ONLY',receipt=receipt,wire=actual,parent=parent)
