"""Closed NewBuyer-only shadow outputs; no dispatch, persistence or delivery."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation

from app.services.unified_snapshot_contract import digest
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema

CONTRACT = 'newbuyer-qualified-valuation-context-v1'
MODEL_REASONS = {
    'SUPPORTIVE': 'MODEL_SUPPORTIVE_IN_BUSINESS_CONTEXT',
    'NEUTRAL': 'MODEL_NEUTRAL_IN_BUSINESS_CONTEXT',
    'BURDENSOME': 'MODEL_BURDENSOME_IN_BUSINESS_CONTEXT',
    'UNRESOLVED': 'JUDGMENT_NOT_RESOLVED',
}
PROMPT = '''Judge only the NewBuyer qualified valuation context in this shadow request.
SUPPORTIVE/NEUTRAL/BURDENSOME are economic MODEL_JUDGED interpretations, not facts.
Select exact qualified valuation and current business refs. Metric availability
does not establish attractiveness. No universal multiple thresholds, new numbers,
free rationale, target/fair-value inference, implied EPS or cross-security facts.
PBR without owned asset relevance is context-only. Forward/trailing coexistence
does not prove cheapness or earnings growth; no such relation is supplied here.
Active business risk requires AVOID and cannot be offset by valuation or timing.
UNRESOLVED means judgment unresolved even when qualified facts are available.
Use a WAIT reason only when its typed predicate is true. Timing is backend-owned:
inside a selected technical watch zone is neither fair value nor a buy instruction.
Overall, Core, A, directional score and Holder are frozen inputs, not outputs.
US FY1 may be USER_AUTHORIZED_PRODUCT_POLICY, not a Finnhub field definition.
KIS FY1 is dated house research, not consensus or NTM. Preserve all source caveats.
The separately owned absolute-range path, if supplied, has explicit precedence;
never claim VALID_FUNDAMENTAL_DISCOUNT for a model-judged multiple interpretation.
Return the closed output schema only. This request has no delivery authority.'''


def number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def business_state(subject):
    cap = subject['capability']
    if cap['holder_risk']:
        return 'ADVERSE'
    if cap['positive'] and not cap['negative']:
        return 'POSITIVE'
    if cap['positive'] and cap['negative']:
        return 'MIXED'
    return 'INSUFFICIENT'


def business_gate(subject):
    return subject['frozen_overall'] == 'BUY' and business_state(subject) == 'POSITIVE'


def timing(subject):
    selected = subject['selected_tactical_candidate']
    result = dict(state='UNRESOLVED', relation='UNRESOLVED', selected=selected,
                  evidence_refs=[], reason='NO_ELIGIBLE_SELECTED_CANDIDATE',
                  kind='TACTICAL_NOT_FAIR_VALUE')
    rows = [r for r in subject['tactical_catalog'] if r['candidate_id'] == selected]
    if len(rows) != 1:
        return result
    row, price = rows[0], subject['current_price']
    low, high, current = (number(v) for v in (row.get('low'), row.get('high'),
                                            price.get('value')))
    if (row.get('relation_basis_proven') is not True or row.get('eligible') is not True
            or row.get('ticker') != subject['ticker']
            or row.get('security_id') != subject['security_id']
            or not row.get('evidence_refs') or not price.get('ref_id')
            or not price.get('currency') or row.get('currency') != price['currency']
            or not price.get('basis') or row.get('price_basis') != price['basis']
            or not price.get('as_of') or row.get('as_of') != price['as_of']
            or None in (low, high, current) or low > high):
        result['reason'] = 'PRICE_ZONE_IDENTITY_BASIS_OR_VALUE_UNRESOLVED'
        return result
    inside = low <= current <= high
    result.update(state='FAVORABLE_NOW' if inside else 'WAIT_FOR_ZONE',
                  relation='INSIDE' if inside else 'BELOW' if current < low else 'ABOVE',
                  evidence_refs=sorted(set(row['evidence_refs'] + [price['ref_id']])),
                  reason='EXACT_SELECTED_ZONE_RELATION')
    return result


def usable_facts(subject):
    return {ref: row for ref, row in subject['facts'].items()
            if row['metric'] != 'PBR' or row['asset_relevance_proven'] is True}


def wait_reasons(subject, state):
    cap, entry = subject['capability'], timing(subject)
    reasons = {}
    if state == 'UNRESOLVED':
        reasons['VALUATION_UNRESOLVED'] = []
    caution = sorted(set(cap['confidence'] + cap['quality']))
    if caution or business_state(subject) == 'INSUFFICIENT':
        reasons['CONFIDENCE_UNCERTAINTY'] = caution
    if entry['state'] == 'WAIT_FOR_ZONE':
        reasons['NO_CLEAN_ENTRY'] = entry['evidence_refs']
    elif entry['state'] == 'UNRESOLVED':
        reasons['ENTRY_TIMING_UNRESOLVED'] = []
    if state in ('NEUTRAL', 'BURDENSOME'):
        reasons['VALUATION_' + state] = None  # Must equal the selected valuation refs.
    if not business_gate(subject):
        name = 'BUSINESS_MIXED' if business_state(subject) == 'MIXED' else 'BUSINESS_GATE_NOT_MET'
        reasons[name] = sorted(set(cap['positive'] + cap['negative']))
    return reasons


def obj(properties):
    return dict(type='object', properties=properties, required=list(properties),
                additionalProperties=False)


def refs(values, minimum=0):
    values = sorted(set(values))
    return dict(type='array', items=dict(type='string', enum=values) if values
                else dict(type='string'), minItems=minimum, maxItems=len(values), uniqueItems=True)


def output_schema(subject):
    cap = subject['capability']
    qualified = usable_facts(subject)
    business = sorted(set(cap['positive'] + cap['negative']))
    risk = sorted(set(cap['holder_risk']))
    relation = subject['absolute_discount']
    states = list(MODEL_REASONS) if qualified and business else ['UNRESOLVED']
    if relation and not risk:
        states = ['SUPPORTIVE']
    branches = []
    for state in states:
        owned = bool(relation and not risk)
        valuation = obj(dict(
            state=dict(const=state),
            authority=dict(const='SOURCE_DETERMINISTIC' if owned else
                           'NOT_RESOLVED' if state == 'UNRESOLVED' else 'MODEL_JUDGED'),
            reason_class=dict(const='OWNED_FUNDAMENTAL_DISCOUNT' if owned
                              else MODEL_REASONS[state]),
            valuation_evidence_refs=dict(const=[]) if owned or state == 'UNRESOLVED'
            else refs(qualified, 1),
            business_evidence_refs=dict(const=[]) if owned or state == 'UNRESOLVED'
            else refs(business, 1),
            relation_refs=dict(const=relation['evidence_refs'] if owned else []),
        ))
        if risk:
            choices = [('AVOID', 'ACTIVE_ADVERSE_UNCOMPENSATED', risk, 'ACTIVE_RISK')]
        elif owned:
            choices = [('ATTRACTIVE', 'VALID_FUNDAMENTAL_DISCOUNT',
                        relation['evidence_refs'], 'ABSOLUTE_FUNDAMENTAL_RANGE')]
        else:
            choices = [('WAIT', reason, evidence, 'QUALIFIED_VALUATION_CONTEXT')
                       for reason, evidence in wait_reasons(subject, state).items()]
            if state == 'SUPPORTIVE' and business_gate(subject):
                choices.append(('ATTRACTIVE', 'QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE',
                                sorted(set(cap['positive'])), 'QUALIFIED_VALUATION_CONTEXT'))
        for stance, reason, evidence, path in choices:
            branches.append(obj(dict(
                contract=dict(const=CONTRACT), input_sha256=dict(const=digest(subject)),
                decision_path=dict(const=path), valuation_context=deepcopy(valuation),
                timing_context=dict(const=timing(subject)), new_buyer=dict(const=stance),
                reason_class=dict(const=reason),
                reason_evidence_refs=refs(qualified, 1) if evidence is None
                else dict(const=evidence), active_risk_refs=dict(const=risk),
            )))
    return dict(anyOf=branches)


def validate_output(output, subject):
    errors = validate_json_schema(output, output_schema(subject))
    if errors:
        return dict(status='FAIL', errors=['CLOSED_SHAPE_OR_TYPED_PREDICATE'] + errors)
    valuation = output['valuation_context']
    for values in [output['reason_evidence_refs'], output['active_risk_refs'],
                   *[valuation[k] for k in ('valuation_evidence_refs',
                                           'business_evidence_refs', 'relation_refs')]]:
        if len(values) != len(set(values)):
            errors.append('DUPLICATE_EXACT_REF')
    if output['reason_class'] in ('VALUATION_NEUTRAL', 'VALUATION_BURDENSOME'):
        if set(output['reason_evidence_refs']) != set(valuation['valuation_evidence_refs']):
            errors.append('REASON_JUDGMENT_REF_MISMATCH')
    return dict(status='FAIL' if errors else 'PASS', errors=errors,
                economic_correctness_proven=False, source_facts_generated=False,
                scope='NEWBUYER_SHADOW_ONLY')


def presentation_plan(output, subject):
    """Symbolic slots for a future renderer, not a generated stock message."""
    if validate_output(output, subject)['status'] != 'PASS':
        raise ValueError('invalid_newbuyer_shadow_output')
    return dict(contract=CONTRACT, fundamental_attractiveness=output['new_buyer'],
                entry_timing=output['timing_context']['state'],
                timing_kind='TACTICAL_NOT_FAIR_VALUE',
                valuation_judgment=output['valuation_context']['state'],
                valuation_reason=output['reason_class'],
                numeric_owner='EXISTING_BACKEND_VALUATION_RENDERER',
                metric_refs=output['valuation_context']['valuation_evidence_refs'],
                bare_buy_label_allowed=False, production_delivery_allowed=False)
