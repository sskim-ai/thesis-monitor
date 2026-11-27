"""Explicit default-OFF adapter from accepted B inputs to B2-only shadow requests.

Inputs must be accepted, frozen Core/A/B artifacts from the caller's run. This
module cannot acquire sources, invoke a model, persist an assessment or deliver.
"""
from copy import deepcopy
from app.services.entry_candidate_basis import assess_entry_candidates, selected_entry_scenario
from app.services.entry_candidate_basis import statement as _statement  # noqa: F401 - renderer re-export
from app.services.provider_valuation_calibration_context import parse_context
from app.services.provider_native_valuation_snapshot import (
    ProviderNativeForwardValuationSnapshot, ProviderNativeValuationSnapshot,
)
from app.services.unified_snapshot_contract import digest
from app.services import new_buyer_base_contract as contract
from scripts.m12da_source_use_contract import canonical_source_metadata_sha256
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema, scan_provider_structured_output_schema,
)


def _unique(rows, field):
    values = {row[field]: row for row in rows}
    if len(values) != len(rows):
        raise ValueError('shadow_duplicate_evidence_identity')
    return values


def qualified_facts(context, ticker, generation):
    vc = context['valuation_context']
    parse_context(vc)
    if (vc['ticker'] != ticker or vc['run_id'] != generation
            or vc['overall_direction_use'] is not False or 'NEW_BUYER' not in vc['allowed_axes']):
        raise ValueError('shadow_valuation_current_identity_or_permission')
    facts = {}
    for row in vc['metric_states']:
        ref = row['fact_ref']
        if ref is None or row['metric'] not in ('PER', 'PBR', 'FORWARD_PE', 'CURRENT_FY1_FPER'):
            continue
        fact, registry = (vc['facts'][ref][name] for name in ('fact', 'registry'))
        if (fact['ticker'] != ticker or fact['fact_id'] != ref
                or fact['overall_direction_use'] is not False
                or registry['registered'] is not True or registry['unit'] != 'x'
                or contract.number(row['value']) is None):
            raise ValueError('shadow_valuation_fact_binding')
        native = fact.get('provider_snapshot')
        if native:
            cls = (ProviderNativeForwardValuationSnapshot if row['metric'] == 'FORWARD_PE'
                   else ProviderNativeValuationSnapshot)
            parsed = cls.model_validate(native)
            if (not parsed.display_eligible or not parsed.new_buyer_valuation_context_eligible
                    or parsed.canonical_security_id != vc['security_id']
                    or parsed.run_id != generation
                    or parsed.requested_security_id != ticker or parsed.returned_security_id != ticker
                    or parsed.snapshot_sha256 != row['snapshot_sha256']
                    or parsed.state != row['state'] or parsed.value != row['value']
                    or native['security_identity_receipt']['status'] != 'QUALIFIED_EXACT_SECURITY'):
                raise ValueError('shadow_native_valuation_binding')
        elif (row['metric'] != 'CURRENT_FY1_FPER' or row['state'] != 'QUALIFIED'
              or ref != 'kr-forward-valuation:' + vc['security_id'] + ':CURRENT_FY1_FPER'
              or fact['fields']['currency'] != 'KRW' or fact['decimal_value'] != row['value']
              or fact['input_receipt_sha256'] != row['input_receipt_sha256']):
            raise ValueError('shadow_kr_fper_owner_binding')
        facts[ref] = dict(metric=row['metric'], ticker=ticker, security_id=vc['security_id'],
                          metadata=deepcopy(row),
                          source_fact=deepcopy(fact), registry=deepcopy(registry),
                          current_scope='FROZEN_INPUT_ONLY',
                          source_kind='ATOMIC_PROVIDER_SNAPSHOT' if native
                          else 'KIS_HOUSE_RESEARCH_NOT_CONSENSUS')
    # All qualified multiples reach the economic assessment. Their availability
    # proves the input, not cheapness; the model judges their business relevance.
    return facts


def tactical_catalog(context, ticker, security, *, source_generation_id=None):
    return assess_entry_candidates(context, ticker=ticker, security_id=security,
                                   source_generation_id=source_generation_id)


def absolute_discount(context):
    """Consume the frozen deterministic owner; never derive a range from multiples."""
    value = context['r2_valuation']
    if value.get('historical_context_only') is True:
        if value['compensating_discount']:
            raise ValueError('historical_reference_must_not_compensate_risk')
        return None
    if not (value['fundamental_valid'] and value['compensating_discount']):
        return None
    option, price = value['option'], context['current_price']
    refs = option['evidence_refs']
    permissions = _unique(context['source_use_projection']['source_permissions'], 'ref_id')
    candidates = context['r2_eligible_range_catalog']['fundamental_candidates']
    catalog = _unique(candidates, 'candidate_id')
    selected = option.get('source_candidate_ids') or []
    security_gate = value.get('security_gate', {})
    low, high, current = (contract.number(v) for v in
                          (option.get('low'), option.get('high'), price.get('value')))
    owned_refs = {ref for row in candidates for ref in row['evidence_refs']}
    if (option['status'] != 'RESOLVED' or option['ticker'] != context['ticker']
            or context.get('deterministic_fundamental_option') != option
            or security_gate.get('status') != 'PASS'
            or security_gate.get('basis_state') != 'RESOLVED'
            or security_gate.get('ticker') != context['ticker']
            or not selected or not set(selected) <= set(catalog)
            or any(catalog[cid].get('ticker') != context['ticker']
                   or catalog[cid].get('currency') != price.get('currency') for cid in selected)
            or not refs or not set(refs) <= owned_refs
            or not all('VALUATION' in permissions.get(ref, {}).get('allowed_uses', [])
                       for ref in refs)
            or not option.get('currency') or option['currency'] != price.get('currency')
            or None in (low, high, current) or not 0 < low <= high or current >= low):
        raise ValueError('shadow_absolute_range_owner_binding')
    return dict(kind='EXACT_OWNED_FUNDAMENTAL_DISCOUNT', evidence_refs=sorted(set(refs)),
                valuation_sha256=digest(value), option_id=option['option_id'])


def historical_price_context(context):
    """Project existing source-use qualified candidates, not a new price owner.

    A's tier is context. Keep distinct method/band IDs even when the old
    deterministic intersection is unresolved. Do not grant new source uses.
    """
    value = context['r2_valuation']
    if value.get('historical_context_only') is not True:
        return None
    if value['compensating_discount']:
        raise ValueError('historical_reference_must_not_compensate_risk')
    price = context.get('current_price') or {}
    current = contract.number(price.get('value'))
    if current is None or current <= 0:
        return None
    permissions = _unique(context['source_use_projection']['source_permissions'], 'ref_id')
    catalog = _unique(context['r2_eligible_range_catalog']['fundamental_candidates'], 'candidate_id')
    candidates = []
    for audit in value['method_audit']:
        candidate = audit['candidate']
        gate = audit['security_gate']
        if (gate.get('status') != 'PASS' or gate.get('basis_state') != 'RESOLVED'
                or gate.get('output_status') != 'RESOLVED' or gate.get('ticker') != context['ticker']
                or catalog.get(candidate['candidate_id']) != candidate
                or candidate.get('ticker') != context['ticker']
                or candidate.get('currency') not in ('USD','KRW')
                or candidate.get('currency') != price.get('currency')
                or candidate.get('contract') != 'm12co-fundamental-entry-candidate-builder-v1'
                or candidate.get('method_version') != 'v1'
                or candidate.get('quantile_band') not in ('P25_P50','P50_P75','P75_P90')
                or candidate.get('method_family') not in ('HISTORICAL_TRAILING_PE_QUANTILE',
                                                          'HISTORICAL_PB_QUANTILE')
                or candidate.get('entry_candidate_not_price_target') is not True
                or candidate.get('quality_state') != 'ARITHMETICALLY_SAFE_POLICY_SELECTION_REQUIRED'
                or candidate.get('disqualifying_reasons')):
            continue
        refs = candidate.get('evidence_refs') or []
        if not refs or not all('VALUATION' in (set(permissions.get(ref, {}).get('allowed_uses', ()))
                - set(permissions.get(ref, {}).get('prohibited_uses', ()))) for ref in refs):
            continue
        low, high = (contract.number(candidate.get(k)) for k in ('low','high'))
        if low is None or high is None or not 0 < low <= high:
            continue
        inputs = candidate.get('formula_inputs') or {}
        if inputs.get('denominator_ref') not in refs or inputs.get('history_ref') not in refs:
            continue
        # The existing candidate builder owns arithmetic; this is a projection
        # of its values and source IDs, not a newly generated range.
        row = {k: deepcopy(candidate[k]) for k in ('candidate_id','method_family','quantile_band',
                    'low','high','currency','formula_inputs','evidence_refs','assumptions')}
        row['relation_to_price'] = 'BELOW' if current < low else 'ABOVE' if current > high else 'INSIDE'
        row['a_selected_tier'] = audit['eligible_for_selected_tier']
        row['candidate_sha256'] = digest(candidate)
        candidates.append(row)
    if not candidates:
        return None
    option = value['option']
    return dict(scope='HISTORICAL_REFERENCE_NOT_FAIR_VALUE',
        ticker=context['ticker'], currency=price['currency'], current_price=deepcopy(price),
        candidates=candidates, method_conflict=value['method_conflict'],
        a_archetype=option['archetype'], a_regime_tier=option['valuation_regime_tier'])


def native_reference_for_b2(context, valuation_view, forward_view=None):
    """Use the same verified view as B, without copying its history into B."""
    if valuation_view is None:
        return None
    from app.services.unavailable_price_valuation import parse_view
    from app.services.provider_valuation_calibration_context import calibration_context
    view = parse_view(valuation_view)
    ref = deepcopy(view.provider_reference_context)
    if ref is None:
        return None
    if forward_view is not None:
        from app.services.kr_forward_valuation_context import KrForwardValuationView, calibration_context as kr_context
        forward = KrForwardValuationView.model_validate(forward_view)
        if forward.native != view:
            raise ValueError('native_reference_kr_view_mismatch')
        expected = kr_context(forward)
    else:
        expected = calibration_context(view)
    if expected != context['valuation_context'] or ref['ticker'] != context['ticker']:
        raise ValueError('native_reference_calibration_view_mismatch')
    quote = context.get('current_price') or {}
    price = contract.number(quote.get('value'))
    # A diagnostic quotient is not a recalculated or replacement native ratio.
    # Do not infer same-session comparability from close or identity alone.
    quote_matches = (price is not None and price>0 and price==contract.number(view.price)
        and quote.get('currency')==view.currency and quote.get('as_of')==view.price_session.isoformat()
        and quote.get('basis')==view.price_basis)
    ref['quote_basis_comparable'] = bool(quote_matches and (
        view.price_basis in ('close','regular_close') or view.unadjusted_price_binding is not None))
    if quote_matches:
        ref['reference_quote'] = dict(value=float(price),currency=view.currency,
            as_of=view.price_session.isoformat(),basis=view.price_basis,
            scope='DIAGNOSTIC_NOT_PROVIDER_SAME_SESSION_RECOMPUTATION')
        current_metrics = {m.metric: m for m in view.metrics if m.status=='QUALIFIED'}
        for row in ref['direct']:
            value = contract.number(row['value'])
            # Compare two independently available observations. Never
            # reconstruct a missing/denied atomic multiple as a diagnostic.
            if value is not None and value>0 and row['metric'] in current_metrics:
                quotient = float(price/value)
                if quotient != float('inf'):
                    row['reference_quote_quotient'] = round(quotient,4)
                    row['comparison_metric_ref'] = 'current-valuation:'+view.security_id+':'+row['metric']
    return ref


def append_native_reference_candidates(historical, reference, context):
    """Reuse C63's descriptive candidate catalog/selection, not its own-basis gate."""
    from scripts.m12co_entry_range_contract import provider_reference_candidates
    from scripts.m12cp_valuation_policy_contract import TIER_TO_BAND
    rows = provider_reference_candidates(reference)
    if not rows:
        return historical
    value = context['r2_valuation']
    if value.get('historical_context_only') is not True or value['compensating_discount']:
        raise ValueError('native_reference_requires_noncompensating_context')
    option = value['option']
    price = context.get('current_price')
    current = contract.number((price or {}).get('value'))
    tier = TIER_TO_BAND.get(option['valuation_regime_tier'])
    quote_comparable = reference.get('quote_basis_comparable') is True and current is not None and current>0
    denominator_basis = {d['ref_id']: d.get('own_denominator_basis_resolved') is True
                         for d in reference['direct']}
    candidates = []
    for candidate in rows:
        low,high = contract.number(candidate['low']),contract.number(candidate['high'])
        if low is None or high is None or not 0<low<=high:
            continue
        row = {k:deepcopy(candidate[k]) for k in ('candidate_id','method_family','quantile_band',
            'low','high','currency','formula_inputs','evidence_refs','assumptions',
            'origin','history_window','history_first','history_last','positive_periods','provider_formula_exact')}
        # An unadjusted local close does not establish the provider's per-share adjustment basis.
        comparable = quote_comparable and denominator_basis.get(candidate['formula_inputs']['denominator_ref'], False)
        row['relation_to_price'] = ('BELOW' if current<low else 'ABOVE' if current>high else 'INSIDE') if comparable else 'UNRESOLVED'
        row['quote_basis_comparable'] = bool(comparable)
        row['a_selected_tier'] = row['quantile_band']==tier
        row['candidate_sha256'] = digest(candidate)
        candidates.append(row)
    if not candidates:
        return historical
    if historical is None:
        historical = dict(scope='HISTORICAL_REFERENCE_NOT_FAIR_VALUE',ticker=context['ticker'],
            currency=reference['currency'],current_price=deepcopy(price),candidates=[],method_conflict=False,
            a_archetype=option['archetype'],a_regime_tier=option['valuation_regime_tier'])
    # Independent provider and own-weekly methods are never intersected or averaged.
    comparison_band = tier or 'P50_P75'
    selected = [r for r in candidates if r['quantile_band']==comparison_band]
    historical['provider_method_conflict'] = (len(selected)>1 and (
        max(contract.number(r['low']) for r in selected)>min(contract.number(r['high']) for r in selected)
        or len({r['relation_to_price'] for r in selected if r['relation_to_price']!='UNRESOLVED'})>1))
    historical['candidates'].extend(candidates)
    return historical


def technical_structure_context(context, selected, scenario):
    """Existing B evidence, with compact observations rather than ref IDs alone.

    Preserve the selected scenario separately. Do not grant new uses or import
    display-only price levels into the model's ENTRY catalog.
    """
    eligible = {r['ref_id'] for r in context['source_use_projection']['source_permissions']
                if 'ENTRY' in r.get('allowed_uses', ())}
    support_refs = set(selected.get('evidence_refs', ())) if selected else {
        ref for row in context.get('r2_eligible_range_catalog', {}).get('tactical_candidates', ())
        for ref in row.get('evidence_refs', ())}
    fields = {
        'chart_timeframe': ('timeframe','candle','volume_ratio_20','price_basis','quality','range_position_pct'),
        'chart_support_zone': ('zone_low','zone_high','currency','timeframe','entry_role','entry_role_basis','confirmation_bar'),
        'chart_resistance_zone': ('zone_low','zone_high','currency','timeframe','entry_role','entry_role_basis'),
        'chart_structure_atr': ('value','currency','timeframe','period'),
        'chart_fibonacci': ('anchor_type','low_price','high_price','low_date','high_date','retracements','timeframe','confidence','currency'),
        'chart_major_swing': ('kind','price','currency','timeframe','confirmed_at'),
        'chart_box': ('box_low','box_high','currency','timeframe','width_pct'),
        'chart_state': ('state','reasons','user_semantics','blocking_unknowns'),
    }
    result = []
    for row in context['decision_evidence']:
        ref, label = row['ref_id'], row.get('label')
        if ref not in eligible or label not in fields:
            continue
        if scenario and ref == scenario['evidence_ref']:
            continue
        if label == 'chart_support_zone' and ref not in support_refs:
            continue
        observation = _statement(row)
        if not observation:
            continue
        value = {k: deepcopy(observation[k]) for k in fields[label] if k in observation}
        if value:
            result.append(dict(ref_id=ref, label=label, as_of=row.get('as_of'), observation=value,
                scope='GENERAL_CHART_CONTEXT_NOT_SELECTED_SCENARIO' if label == 'chart_state' else 'EXISTING_ENTRY_CONTEXT'))
    return result


def build_request(*, settings, context, accepted, core, pass_a, source_generation_id,
                  valuation_view=None, forward_view=None, technical_flow_context=None):
    if not settings.newbuyer_qualified_valuation_shadow:
        return None
    before = digest([context, accepted, core, pass_a])
    ticker = context['ticker']
    if (context['source_evidence_binding']['ticker'] != ticker
            or context['source_evidence_binding']['source_generation_id'] != source_generation_id
            or context['frozen_pass_a_classification'] != pass_a):
        raise ValueError('shadow_frozen_subject_identity')
    facts = qualified_facts(context, ticker, source_generation_id)
    capability = deepcopy(context['r2_policy_capability'])
    if (core['effects'] != context['r2_core_effects']
            or core['binding_sha256'] != digest(dict(atomic=core['atomic_claims'],
                                                     effects=core['effects']))
            or capability['core_binding_sha256'] != core['binding_sha256']
            or capability['ticker'] != ticker
            or capability['source_binding_sha256']
            != context['source_evidence_binding']['source_use_binding_sha256']
            or capability['source_binding_sha256'] != context['source_use_projection']['binding_sha256']
            or context['source_evidence_binding']['emitted_evidence_sha256']
            != canonical_source_metadata_sha256(context['decision_evidence'])):
        raise ValueError('shadow_frozen_core_binding')
    for key in ('positive', 'negative', 'confidence', 'quality', 'holder_risk'):
        values = capability[key]
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
            raise ValueError('shadow_business_capability_shape')
        if (len(values) != len(set(values)) or set(values) & set(facts)
                or not set(values) <= set(core['effects'])):
            raise ValueError('shadow_business_capability_scope')
    subject = dict(ticker=ticker, security_id=context['valuation_context']['security_id'],
                   source_generation_id=source_generation_id,
                   capability=capability, frozen_overall=accepted['overall_direction'],
                   facts=facts, absolute_discount=absolute_discount(context),
                   current_price=deepcopy(context['current_price']),
                   tactical_catalog=tactical_catalog(context, ticker,
                        context['valuation_context']['security_id'],
                        source_generation_id=source_generation_id),
                   selected_tactical_candidate=accepted['tactical_choice'],
                   frozen_business_claims=deepcopy(core['atomic_claims']),
                   frozen_classification=deepcopy(pass_a),
                   frozen_holder={k: deepcopy(v) for k, v in accepted.items()
                                  if k.startswith('holder')},
                   frozen_authority=dict(core=digest(core), capability=digest(capability),
                       pass_a=digest(pass_a), accepted_b=digest(accepted),
                       context=digest(context)))
    if 'native_technical_context' in context:
        subject['native_technical_context'] = deepcopy(context['native_technical_context'])
    if technical_flow_context is not None:
        if (technical_flow_context['ticker'] != ticker
                or technical_flow_context['security_id'] != subject['security_id']
                or technical_flow_context['source_generation'] != source_generation_id):
            raise ValueError('b2_stock_flow_subject_scope')
        subject['technical_flow_context'] = deepcopy(technical_flow_context)
    selected = next((c for c in subject['tactical_catalog']
                     if c['candidate_id'] == subject['selected_tactical_candidate']), None)
    scenario = selected_entry_scenario(context, selected)
    if scenario is not None:
        subject['selected_entry_scenario'] = scenario
    if subject.get('native_technical_context', {}).get('comparison_version') == 1:
        subject['technical_structure_context'] = technical_structure_context(context, selected, scenario)
    if 'economic_context' in context:
        subject['economic_context'] = deepcopy(context['economic_context'])
        subject['economic_context']['overall_reason_class'] = accepted.get('overall_reason_class')
        historical = historical_price_context(context)
        reference = native_reference_for_b2(context, valuation_view, forward_view)
        if reference is not None:
            subject['provider_reference_context'] = reference
            historical = append_native_reference_candidates(historical,reference,context)
        if historical is not None:
            subject['historical_price_context'] = historical
    request = dict(contract=contract.CONTRACT, prompt=contract.PROMPT, subject=subject,
                   output_schema=contract.output_schema(subject), shadow_only=True,
                   dispatch_authorized=False, persistence_authorized=False,
                   delivery_authorized=False)
    wire, receipt = project_provider_wire_schema(
        contract.obj(dict(new_buyer_shadow=request['output_schema'])))
    scan = scan_provider_structured_output_schema(wire)
    if scan['status'] != 'PASS':
        raise ValueError('shadow_provider_wire_schema_gap')
    request.update(provider_wire_schema=wire, provider_wire_receipt=receipt,
                   provider_dialect_validation=scan)
    request['request_sha256'] = digest(request)
    if digest([context, accepted, core, pass_a]) != before:
        raise ValueError('shadow_authority_mutation')
    return request


def validate_result(output, request):
    if request['request_sha256'] != digest({k: v for k, v in request.items()
                                            if k != 'request_sha256'}):
        raise ValueError('shadow_request_drift')
    if request['output_schema'] != contract.output_schema(request['subject']):
        raise ValueError('shadow_schema_drift')
    return contract.validate_output(output, request['subject'])


def validate_wire_result(output, request):
    """Wire removes uniqueItems only; exact-ref uniqueness remains a local gate."""
    errors = contract.validate_json_schema(output, request['provider_wire_schema'])
    if errors:
        return dict(status='FAIL', errors=['SHADOW_WIRE_SHAPE'] + errors)
    return validate_result(output['new_buyer_shadow'], request)
