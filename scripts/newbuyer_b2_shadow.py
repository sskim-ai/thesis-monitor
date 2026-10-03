"""Explicit default-OFF adapter from accepted B inputs to B2-only shadow requests.

Inputs must be accepted, frozen Core/A/B artifacts from the caller's run. This
module cannot acquire sources, invoke a model, persist an assessment or deliver.
"""
from copy import deepcopy
import json

from app.services.provider_valuation_calibration_context import parse_context
from app.services.provider_native_valuation_snapshot import (
    ProviderNativeForwardValuationSnapshot, ProviderNativeValuationSnapshot,
)
from app.services.unified_snapshot_contract import digest
from scripts import newbuyer_b2_contract as contract
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
                          asset_relevance_proven=False, metadata=deepcopy(row),
                          source_fact=deepcopy(fact), registry=deepcopy(registry),
                          current_scope='FROZEN_INPUT_ONLY',
                          source_kind='ATOMIC_PROVIDER_SNAPSHOT' if native
                          else 'KIS_HOUSE_RESEARCH_NOT_CONSENSUS')
    # No asset-relevance owner is supplied by the current production adapter.
    # PBR remains visible as context, never an independent economic-state anchor.
    return facts


def _statement(row):
    value = row.get('statement', {})
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def tactical_catalog(context, ticker, security):
    permissions = _unique(context['source_use_projection']['source_permissions'], 'ref_id')
    evidence = _unique(context['decision_evidence'], 'ref_id')
    price = context['current_price']
    price_row = evidence.get(price.get('ref_id'), {})
    price_value = _statement(price_row)
    result = []
    for candidate in context['r2_eligible_range_catalog']['tactical_candidates']:
        row = deepcopy(candidate)
        proofs = []
        for ref in row['evidence_refs']:
            ev = evidence.get(ref, {})
            zone = _statement(ev)
            chart_ref = 'canonical:chart:' + str(zone.get('timeframe'))
            chart = evidence.get(chart_ref, {})
            chart_value = _statement(chart)
            basis_match = (price.get('basis'), chart_value.get('price_basis')) in {
                ('adjusted_close', 'adjusted'), ('unadjusted_close', 'unadjusted'),
                ('regular_close', 'unadjusted')}
            passed = (
                row.get('ticker', ticker) == ticker
                and row.get('security_id', security) == security
                and ev.get('label') == 'chart_support_zone'
                and contract.number(zone.get('zone_low')) == contract.number(row['low'])
                and contract.number(zone.get('zone_high')) == contract.number(row['high'])
                and zone.get('currency') == row['currency'] == price.get('currency')
                and chart_value.get('currency') == price.get('currency')
                and price_value.get('currency') == price.get('currency')
                and ev.get('as_of') == chart.get('as_of') == price.get('as_of')
                and price_row.get('as_of') == price.get('as_of')
                and contract.number(chart_value.get('candle', {}).get('close'))
                == contract.number(price.get('value'))
                and contract.number(price_value.get('current_price'))
                == contract.number(price.get('value'))
                and price_value.get('price_basis') == price.get('basis')
                and price_value.get('price_as_of') == price.get('as_of')
                and chart_value.get('quality') == 'available' and basis_match
                and 'ENTRY' in permissions.get(ref, {}).get('allowed_uses', [])
            )
            proofs.append(dict(ref=ref, chart_ref=chart_ref, zone_sha256=digest(ev),
                               chart_sha256=digest(chart), price_sha256=digest(price_row),
                               passed=passed))
        row.update(ticker=row.get('ticker', ticker), security_id=row.get('security_id', security),
                   as_of=price.get('as_of'), price_basis=price.get('basis'), eligible=True,
                   relation_basis_proven=bool(proofs) and all(p['passed'] for p in proofs),
                   basis_proofs=proofs)
        result.append(row)
    return result


def absolute_discount(context):
    """Consume the frozen deterministic owner; never derive a range from multiples."""
    value = context['r2_valuation']
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


def build_request(*, settings, context, accepted, core, pass_a, source_generation_id):
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
                                                     context['valuation_context']['security_id']),
                   selected_tactical_candidate=accepted['tactical_choice'],
                   frozen_business_claims=deepcopy(core['atomic_claims']),
                   frozen_classification=deepcopy(pass_a),
                   frozen_holder={k: deepcopy(v) for k, v in accepted.items()
                                  if k.startswith('holder')},
                   frozen_authority=dict(core=digest(core), capability=digest(capability),
                       pass_a=digest(pass_a), accepted_b=digest(accepted),
                       context=digest(context)))
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
