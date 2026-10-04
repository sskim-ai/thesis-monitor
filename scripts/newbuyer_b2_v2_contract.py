"""Closed B2 v2 valuation judgments and independent backend timing, offline only."""
from copy import deepcopy

from scripts import newbuyer_b2_contract as v1
from scripts import newbuyer_b2_v2_policy as policy
from scripts.kis_eps_wire_calibration import digest

CONTRACT = 'newbuyer-qualified-valuation-context-v2'
PROMPT_VERSION = 'newbuyer-b2-v2-owned-evaluability-timing-independent-v1'
SCHEMA_VERSION = 'newbuyer-b2-v2-closed-output-v1'
PROMPT = '''Judge only the NewBuyer fundamental/valuation attractiveness in this frozen shadow request.
Use only the provided qualified usable valuation facts. SUPPORTIVE, NEUTRAL and
BURDENSOME are economic MODEL_JUDGED interpretations, not source facts.
EVALUABLE requires exactly one of those states: UNRESOLVED is not permitted.
No universal fair-value threshold or target price is required for contextual
judgment; do not invent thresholds, target prices, fair-value ranges or numbers.
Only the backend ALL_RELEVANT_METRICS_UNUSABLE composite proof permits UNRESOLVED.
Unavailable/blocked metrics must not be reconstructed, even if another metric
is usable. No implied-EPS reverse calculation, ADR/home-security transfer,
invented currency/share conversion or multiple-to-earnings-growth inference.
Legacy confidence/quality prose is intentionally absent. Do not recreate it or
launder generic uncertainty into valuation evidence. Business context is not a
valuation fact. Select exact valuation refs and business-context refs separately.
Current typed blocker states have only their explicit capability role: metric
denials affect those exact metrics; business quality affects only linked business
gate support; only explicit current confidence-veto refs permit that veto.
Active material risk requires AVOID regardless of valuation or timing.
SUPPORTIVE with an eligible business gate and no active risk or authorized veto
requires fundamental ATTRACTIVE. Timing WAIT_FOR_ZONE or UNRESOLVED does not
erase that stance. Carry the exact backend timing unchanged as a separate axis.
An ATTRACTIVE stance is not a buy-now instruction. Never substitute chart zones
for fair value. Core, Pass A, Overall, directional score and Holder are frozen.
US FY1 may be USER_AUTHORIZED_PRODUCT_POLICY, not a Finnhub field definition.
KIS FY1 is dated house research, not consensus or NTM. Preserve source caveats.
Return only the closed schema. No free prose or newly calculated source facts.
This request is default-OFF shadow with no persistence or delivery authority.'''


def states(model_input):
    state = model_input['valuation_evaluability']['evaluability_state']
    if state == 'EVALUABLE':
        if not model_input['qualified_usable_valuation_facts']:
            raise ValueError('v2_evaluable_without_facts')
        return ['SUPPORTIVE','NEUTRAL','BURDENSOME']
    if (state == 'ALL_RELEVANT_METRICS_UNUSABLE'
            and model_input['valuation_evaluability']['all_metrics_unusable_proof']
            and model_input['all_metrics_unusable_proof_ref']
            and not model_input['qualified_usable_valuation_facts']):
        return ['UNRESOLVED']
    raise ValueError('v2_invalid_evaluability_not_model_resolvable')


def capabilities(model_input):
    return [dict(valuation_state=state, stance=stance, reason=reason,
                 reason_evidence_refs=evidence)
            for state in states(model_input)
            for stance,reason,evidence in [policy.choices(model_input,state)]]


def output_schema(model_input):
    facts = model_input['qualified_usable_valuation_facts']
    business = [r['claim_ref'] for r in model_input['business_context']]
    branches = []
    for row in capabilities(model_input):
        state, evidence = row['valuation_state'], row['reason_evidence_refs']
        unresolved = state == 'UNRESOLVED'
        valuation = v1.obj(dict(
            state=dict(const=state),
            authority=dict(const='BACKEND_COMPOSITE_UNUSABLE' if unresolved else 'MODEL_JUDGED'),
            valuation_evidence_refs=dict(const=[]) if unresolved else v1.refs(facts,1),
            business_evidence_refs=dict(const=[]) if unresolved else v1.refs(business),
            all_metrics_unusable_proof_ref=dict(const=model_input['all_metrics_unusable_proof_ref']),
        ))
        branches.append(v1.obj(dict(contract=dict(const=CONTRACT),input_sha256=dict(const=digest(model_input)),
            valuation_context=valuation, timing_context=dict(const=model_input['timing_context']),
            new_buyer=dict(const=row['stance']),reason_class=dict(const=row['reason']),
            reason_evidence_refs=v1.refs(facts,1) if evidence is None else dict(const=evidence),
            active_risk_refs=dict(const=model_input['active_risk_refs']))))
    return dict(anyOf=branches)


def validate_output(output, model_input):
    errors = v1.validate_json_schema(output, output_schema(model_input))
    if errors:
        return dict(status='FAIL',errors=['V2_CLOSED_SHAPE_OR_BRANCH_PREDICATE']+errors)
    val = output['valuation_context']
    for values in (output['reason_evidence_refs'],output['active_risk_refs'],
                   val['valuation_evidence_refs'],val['business_evidence_refs']):
        if len(values) != len(set(values)):
            errors.append('DUPLICATE_EXACT_REF')
    if output['reason_class'] in ('VALUATION_NEUTRAL','VALUATION_BURDENSOME'):
        if set(output['reason_evidence_refs']) != set(val['valuation_evidence_refs']):
            errors.append('V2_REASON_VALUATION_REF_MISMATCH')
    return dict(status='FAIL' if errors else 'PASS',errors=errors,
        model_judgment_observed=False,economic_correctness_proven=False,
        new_source_facts=False,scope='NEWBUYER_V2_OFFLINE_SHADOW_ONLY')


def presentation_plan(output, model_input):
    if validate_output(output,model_input)['status'] != 'PASS':
        raise ValueError('v2_invalid_presentation_input')
    return dict(contract=CONTRACT,fundamental_attractiveness=output['new_buyer'],
        entry_timing=deepcopy(output['timing_context']),
        valuation_judgment=output['valuation_context']['state'],
        independent_axes=True,bare_buy_label_allowed=False,production_delivery_allowed=False,
        numeric_owner='EXISTING_BACKEND_VALUATION_RENDERER')
