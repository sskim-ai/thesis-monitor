"""Default-OFF B2 v2 builder. Export only provider_payload(), never backend audit."""
from copy import deepcopy

from scripts import newbuyer_b2_contract as v1
from scripts import newbuyer_b2_v2_contract as contract
from scripts import newbuyer_b2_v2_policy as policy
from scripts.kis_eps_wire_calibration import digest, sealed
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema, scan_provider_structured_output_schema,
)


def _strings(value):
    if isinstance(value,str):
        yield value
    elif isinstance(value,dict):
        for key,item in value.items():
            yield key
            yield from _strings(item)
    elif isinstance(value,list):
        for item in value:
            yield from _strings(item)


def build_request(*, enabled=False, v1_request=None, coverage=None, census=None,
                  coverage_sha=None, census_sha=None, legacy_records=None, confidence=None):
    if not enabled:
        return None
    before = digest([v1_request,coverage,census,legacy_records,confidence])
    if (v1_request['contract'] != v1.CONTRACT
            or v1_request['request_sha256'] != digest({k:v for k,v in v1_request.items() if k!='request_sha256'})
            or v1_request['output_schema'] != v1.output_schema(v1_request['subject'])):
        raise ValueError('v2_v1_frozen_request_drift')
    subject = v1_request['subject']
    if subject['absolute_discount'] is not None:
        raise ValueError('v2_separate_absolute_range_contract_review_required')
    coverage_rows = policy.coverage_gate(coverage,census,coverage_sha,census_sha)
    row = coverage_rows[subject['ticker']]
    evaluation, metrics, all_proof = policy.evaluability(subject,row,census,coverage_sha)
    if evaluation['evaluability_state'] == 'INVALID_INCOMPLETE_CONTRACT':
        raise ValueError('v2_invalid_contradictory_or_incomplete_ownership')
    roles, gate = policy.business_roles(subject,census,confidence)
    legacy = policy.legacy_entitlement(subject,legacy_records,coverage_sha,census_sha)
    current_business = set(gate['eligible_positive_core_refs_after_quality']+gate['eligible_negative_core_refs_after_quality'])
    risk = set(subject['capability']['holder_risk'])
    claims = {r['claim_ref']:r for r in subject['frozen_business_claims']}
    facts = {r:deepcopy(subject['facts'][r]) for r in evaluation['usable_valuation_metric_refs']}
    visible_roles = [deepcopy(r) for r in roles['rows'] if r['role']!='CONTEXT_ONLY']
    model_input = dict(contract_version=contract.CONTRACT,ticker=subject['ticker'],
        security_id=subject['security_id'],source_generation=subject['source_generation_id'],
        business_gate=gate,business_quality_blocker_refs=gate['business_quality_blocker_refs'],
        business_context=[deepcopy(claims[r]) for r in sorted(current_business)],
        active_risk_refs=sorted(risk),active_risk_context=[deepcopy(claims[r]) for r in sorted(risk)],
        valuation_evaluability=evaluation,valuation_metric_resolution_refs=evaluation['metric_resolution_refs'],
        qualified_usable_valuation_facts=facts,
        valuation_metric_blocker_refs=evaluation['metric_blocker_refs'],
        all_metrics_unusable_proof_ref=evaluation['all_metrics_unusable_proof_ref'],
        all_metrics_unusable_proof=all_proof,
        confidence_veto_refs=roles['confidence_veto_refs'],typed_current_blockers=visible_roles,
        timing_context=v1.timing(subject),timing_state=v1.timing(subject)['state'],
        timing_refs=v1.timing(subject)['evidence_refs'],
        authority_digests=deepcopy(subject['frozen_authority']),
        coverage_receipt_sha256=coverage_sha,blocker_census_receipt_sha256=census_sha,
        legacy_context_backend_audit_sha256=legacy['receipt_sha256'],
        prompt_version=contract.PROMPT_VERSION,schema_version=contract.SCHEMA_VERSION,
        policy_sha256=roles['receipt_sha256'])
    branches = contract.capabilities(model_input)
    model_input.update(allowed_stances=sorted({r['stance'] for r in branches}),
        allowed_wait_reasons=sorted({r['reason'] for r in branches if r['stance']=='WAIT'}),
        stance_capability=branches)
    schema = contract.output_schema(model_input)
    wire, projection = project_provider_wire_schema(v1.obj(dict(new_buyer_shadow=schema)))
    scan = scan_provider_structured_output_schema(wire)
    if scan['status'] != 'PASS':
        raise ValueError('v2_provider_wire_gap')
    provider = dict(prompt=contract.PROMPT,input=model_input,response_schema=wire)
    visible_strings = list(_strings(provider))
    legacy_refs = {r['claim_ref'] for r in legacy['rows']}
    for ref in legacy_refs:
        text = claims[ref]['claim'].get('text')
        if any(ref in value or (text and text in value) for value in visible_strings):
            raise ValueError('v2_legacy_model_visibility_leak')
    for axis in (current_business,risk,set(model_input['timing_refs']),legacy_refs):
        if set(facts) & axis:
            raise ValueError('v2_axis_evidence_overlap')
    request = dict(contract=contract.CONTRACT,provider_request=provider,output_schema=schema,
        provider_wire_receipt=projection,provider_dialect_validation=scan,
        request_sha256=digest(provider),backend_audit=dict(metric_resolution=metrics,
            blocker_role_policy=roles,legacy_entitlement=legacy,
            axis_separation=dict(ref_role_separation=True,legacy_model_visible_refs=0,
                legacy_prose_model_visible=False,blocked_values_model_visible=False),
            v1_request_sha256=v1_request['request_sha256'],
            frozen_subject_sha256=digest(subject),coverage_row_sha256=row['receipt_sha256']),
        shadow_only=True,dispatch_authorized=False,persistence_authorized=False,
        delivery_authorized=False,default_enabled=False)
    if digest([v1_request,coverage,census,legacy_records,confidence]) != before:
        raise ValueError('v2_authority_mutation')
    return sealed(request)


def provider_payload(request, *, expected_request_sha256):
    from scripts.kis_eps_wire_calibration import verified
    verified(request,contract.CONTRACT)
    provider = request['provider_request']
    if (request['request_sha256'] != expected_request_sha256 or digest(provider) != expected_request_sha256
            or set(provider) != {'prompt','input','response_schema'} or provider['prompt'] != contract.PROMPT
            or request['output_schema'] != contract.output_schema(provider['input'])):
        raise ValueError('v2_request_freeze_drift')
    wire, _ = project_provider_wire_schema(v1.obj(dict(new_buyer_shadow=request['output_schema'])))
    if provider['response_schema'] != wire or scan_provider_structured_output_schema(wire)['status']!='PASS':
        raise ValueError('v2_wire_freeze_drift')
    return deepcopy(provider)


def validate_result(output, request, *, expected_request_sha256):
    provider = provider_payload(request,expected_request_sha256=expected_request_sha256)
    errors = v1.validate_json_schema(output,provider['response_schema'])
    if errors:
        return dict(status='FAIL',errors=['V2_WIRE_OUTPUT_SHAPE']+errors)
    return contract.validate_output(output['new_buyer_shadow'],provider['input'])
