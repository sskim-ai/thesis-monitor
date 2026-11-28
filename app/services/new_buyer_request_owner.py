"""Default-OFF B2 v2 builder. Export only provider_payload(), never backend audit."""
from copy import deepcopy

from app.services import new_buyer_base_contract as v1
from app.services import new_buyer_v2_contract as contract
from app.services import new_buyer_v2_policy as policy
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


def _link_reported_eps(reference, observations):
    """Allow comparison with period-labelled reported EPS, never equate it to provider TTM."""
    reported = []
    for item in observations:
        row = item.get('observation')
        if (item.get('kind') == 'REPORTED_ABSOLUTE_CONTEXT_ONLY' and isinstance(row, dict)
                and row.get('metric') == 'diluted_eps' and row.get('semantic') == 'us-gaap:EarningsPerShareDiluted'
                and row.get('unit') == 'USD/shares' and row.get('currency') == reference['currency']
                and row.get('source_document_id') and row.get('period_start') and row.get('period_end')):
            reported.append(item['ref_id'])
    if reported:
        for field in reference['direct']:
            if field['field'] == 'epsTTM':
                field['reported_diluted_eps_context_refs'] = reported
                field['period_equivalence'] = 'NOT_ESTABLISHED_PROVIDER_TTM_VS_REPORTED_DURATION'


def build_request(*, enabled=False, v1_request=None, coverage=None, census=None,
                  coverage_sha=None, census_sha=None, legacy_records=None, confidence=None,
                  step2_quality=False):
    if not enabled:
        return None
    before = digest([v1_request,coverage,census,legacy_records,confidence])
    if (v1_request['contract'] != v1.CONTRACT
            or v1_request['request_sha256'] != digest({k:v for k,v in v1_request.items() if k!='request_sha256'})
            or v1_request['output_schema'] != v1.output_schema(v1_request['subject'])):
        raise ValueError('v2_v1_frozen_request_drift')
    subject = v1_request['subject']
    if subject['absolute_discount'] is not None:
        # Do not accept a legacy request carrying an automatic discount grant.
        # Current C63 historical references arrive through the separate,
        # descriptive historical_price_context, with absolute_discount=None.
        raise ValueError('v2_separate_absolute_range_contract_review_required')
    coverage_rows = policy.coverage_gate(coverage,census,coverage_sha,census_sha)
    coverage_row = coverage_rows[subject['ticker']]
    evaluation, metrics, all_proof = policy.evaluability(subject,coverage_row,census,coverage_sha)
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
    if step2_quality:
        model_input['step2_quality_version'] = 1
        model_input['prompt_version'] += '-step2'
        model_input['schema_version'] += '-step2'
    if 'technical_flow_context' in subject:
        model_input['technical_flow_context'] = deepcopy(subject['technical_flow_context'])
    if 'native_technical_context' in subject:
        model_input['native_technical_context'] = deepcopy(subject['native_technical_context'])
        model_input['prompt_version'] += '-native-technical'
        model_input['schema_version'] += '-native-technical'
        if contract.c60_technical_input(model_input):
            model_input['prompt_version'] += '-comparison-v1'
            model_input['schema_version'] += '-optional-change-v1'
    if 'selected_entry_scenario' in subject:
        scenario = subject['selected_entry_scenario']
        if (scenario['candidate_id'] != model_input['timing_context']['selected']
                or scenario['evidence_ref'] not in model_input['timing_refs']):
            raise ValueError('v2_selected_entry_scenario_mismatch')
        model_input['selected_entry_scenario'] = deepcopy(scenario)
    if 'technical_structure_context' in subject:
        model_input['technical_structure_context'] = deepcopy(subject['technical_structure_context'])
        model_input['prompt_version'] += '-entry-structure'
        model_input['schema_version'] += '-entry-structure-refs'
    if 'economic_context' in subject:
        # A context-only observation may inform interpretation, never create
        # an eligible positive business claim or bypass an exact quality block.
        economic = deepcopy(subject['economic_context'])
        blocked = {ref for item in visible_roles for ref in item.get('affected_metric_refs', ())}
        legacy_claims = [claims[r['claim_ref']] for r in legacy['rows']]
        legacy_tokens = {token for c in legacy_claims
                         for token in (c['claim_ref'], c['claim'].get('text')) if token}
        economic['observations'] = [r for r in economic.get('observations', ())
            if r['ref_id'] not in blocked and not any(token in value
                for value in _strings(r) for token in legacy_tokens)]
        retained = {r['ref_id'] for r in economic['observations']}
        economic['relationships'] = [r for r in economic.get('relationships', ())
                                     if set(r['source_refs']) <= retained]
        model_input['economic_context'] = economic
        model_input['prompt_version'] += '-economic-context'
        model_input['schema_version'] += '-economic-reason'
        reference = deepcopy(subject.get('provider_reference_context'))
        reference_refs = set()
        if reference is not None:
            if (reference['scope']!='PROVIDER_NATIVE_REFERENCE_NOT_OWN_DENOMINATOR'
                    or (reference['ticker'],reference['security_id'],reference['run_id'])
                    != (subject['ticker'],subject['security_id'],subject['source_generation_id'])
                    or reference.get('overall_direction_use') is not False):
                raise ValueError('native_reference_subject_identity')
            for key in ('direct','history'):
                reference[key] = [r for r in reference[key] if r['ref_id'] not in blocked
                    and not any(token in value for value in _strings(r) for token in legacy_tokens)]
            for row in reference['direct']:
                if row.get('comparison_metric_ref') not in facts:
                    row.pop('reference_quote_quotient',None)
                    row.pop('comparison_metric_ref',None)
            for row in reference['history']:
                metric_ref = row.get('current_metric_ref')
                if metric_ref is not None and metric_ref not in facts:
                    # The independent historical distribution survives. The
                    # denied current ratio and its relative rank do not.
                    row['current_value'] = row['current_metric_ref'] = None
                    for window in ('all','recent_five_years'):
                        if row.get(window):
                            row[window].pop('current_percentile',None)
            _link_reported_eps(reference, economic['observations'])
            if reference['direct'] or reference['history']:
                model_input['provider_reference_context'] = reference
                reference_refs = {r['ref_id'] for r in reference['direct']+reference['history']}
                model_input['prompt_version'] += '-native-valuation-reference'
                model_input['schema_version'] += '-native-reference-refs'
        historical = deepcopy(subject.get('historical_price_context'))
        if historical is not None:
            if (historical['scope'] != 'HISTORICAL_REFERENCE_NOT_FAIR_VALUE'
                    or historical['ticker'] != subject['ticker']
                    or historical['current_price'] != subject['current_price']):
                raise ValueError('historical_price_context_identity')
            historical['candidates'] = [row for row in historical['candidates']
                if not (set(row['evidence_refs']) & blocked)
                and (row.get('origin')!='PROVIDER_QUARTERLY_REFERENCE'
                     or set(row['evidence_refs'])<=reference_refs)
                and not any(token in value for value in _strings(row) for token in legacy_tokens)]
            if 'provider_method_conflict' in historical:
                # The surviving provider references, not a removed method,
                # own any displayed conflict after existing source denials.
                rows = [r for r in historical['candidates']
                    if r.get('origin')=='PROVIDER_QUARTERLY_REFERENCE']
                comparable = [r for r in rows if r['a_selected_tier']] or [
                    r for r in rows if r['quantile_band']=='P50_P75']
                historical['provider_method_conflict'] = (len(comparable)>1 and (
                    max(v1.number(r['low']) for r in comparable)>min(v1.number(r['high']) for r in comparable)
                    or len({r['relation_to_price'] for r in comparable
                            if r['relation_to_price']!='UNRESOLVED'})>1))
            if historical['candidates']:
                model_input['historical_price_context'] = historical
                model_input['prompt_version'] += '-historical-price-context'
                model_input['schema_version'] += '-historical-price-review'
    branches = contract.capabilities(model_input)
    model_input.update(allowed_stances=sorted({r['stance'] for r in branches}),
        allowed_wait_reasons=sorted({r['reason'] for r in branches if r['stance']=='WAIT'}),
        stance_capability=branches)
    schema = contract.output_schema(model_input)
    wire, projection = project_provider_wire_schema(v1.obj(dict(new_buyer_shadow=schema)))
    scan = scan_provider_structured_output_schema(wire)
    if scan['status'] != 'PASS':
        raise ValueError('v2_provider_wire_gap')
    provider = dict(prompt=contract.prompt_for(model_input),input=model_input,response_schema=wire)
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
            frozen_subject_sha256=digest(subject),coverage_row_sha256=coverage_row['receipt_sha256']),
        shadow_only=True,dispatch_authorized=False,persistence_authorized=False,
        delivery_authorized=False,default_enabled=False)
    if digest([v1_request,coverage,census,legacy_records,confidence]) != before:
        raise ValueError('v2_authority_mutation')
    return sealed(request)


def _required_order_only(schema):
    """JSON Schema required is a set; preserve every other array and value."""
    if not isinstance(schema,dict):
        return deepcopy(schema)
    result=deepcopy(schema)
    for key in ('properties','patternProperties','$defs','definitions','dependentSchemas'):
        if key in schema:
            result[key]={k:_required_order_only(v) for k,v in schema[key].items()}
    for key in ('anyOf','oneOf','allOf','prefixItems'):
        if key in schema:
            result[key]=[_required_order_only(v) for v in schema[key]]
    for key in ('items','additionalProperties','not','if','then','else','contains','propertyNames'):
        if key in schema:
            result[key]=_required_order_only(schema[key])
    if 'required' in schema:
        values=schema['required']
        if (not isinstance(values,list) or any(not isinstance(v,str) for v in values)
                or len(values)!=len(set(values))):
            raise ValueError('v2_required_schema_invariant')
        result['required']=sorted(values)
    return result


def provider_payload(request, *, expected_request_sha256):
    from scripts.kis_eps_wire_calibration import verified
    verified(request,contract.CONTRACT)
    provider = request['provider_request']
    if (request['request_sha256'] != expected_request_sha256 or digest(provider) != expected_request_sha256
            or set(provider) != {'prompt','input','response_schema'}
            or provider['prompt'] != contract.prompt_for(provider['input'])
            or request['output_schema'] != contract.output_schema(provider['input'])):
        raise ValueError('v2_request_freeze_drift')
    wire, _ = project_provider_wire_schema(v1.obj(dict(new_buyer_shadow=request['output_schema'])))
    if (_required_order_only(provider['response_schema']) != _required_order_only(wire)
            or scan_provider_structured_output_schema(wire)['status']!='PASS'):
        raise ValueError('v2_wire_freeze_drift')
    return deepcopy(provider)


def validate_result(output, request, *, expected_request_sha256):
    provider = provider_payload(request,expected_request_sha256=expected_request_sha256)
    errors = v1.validate_json_schema(output,provider['response_schema'])
    if errors:
        return dict(status='FAIL',errors=['V2_WIRE_OUTPUT_SHAPE']+errors)
    return contract.validate_output(output['new_buyer_shadow'],provider['input'])
