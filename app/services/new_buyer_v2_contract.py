"""Closed B2 v2 valuation judgments and independent backend timing, offline only."""
from copy import deepcopy
import re

from app.services import new_buyer_base_contract as v1
from app.services import new_buyer_v2_policy as policy
from scripts.kis_eps_wire_calibration import digest

CONTRACT = 'newbuyer-qualified-valuation-context-v2'
PROMPT_VERSION = 'newbuyer-b2-v2-qualified-multiple-context-v2'
SCHEMA_VERSION = 'newbuyer-b2-v2-closed-output-v1'
PROMPT = '''Judge only the NewBuyer fundamental/valuation attractiveness in this frozen shadow request.
Use only the provided qualified usable valuation facts. SUPPORTIVE, NEUTRAL and
BURDENSOME are economic MODEL_JUDGED interpretations, not source facts.
EVALUABLE requires exactly one of those states: UNRESOLVED is not permitted.
No universal fair-value threshold or target price is required for contextual
judgment; do not invent thresholds, target prices, fair-value ranges or numbers.
Only the backend ALL_RELEVANT_METRICS_UNUSABLE composite proof permits UNRESOLVED.
Qualified PER, PBR and forward PE are actual valuation inputs; none requires a
separate asset-relevance authorization. A low PBR alone does not establish
cheapness or attractiveness. Support from PBR needs supplied business, asset
quality, profitability/ROE or financial context that makes book value meaningful.
Do not invent those observations. A usable multiple with limited economic
inference remains usable: choose NEUTRAL when the supplied context supports
neither a favorable nor an unfavorable valuation judgment, not UNRESOLVED.
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

NATIVE_TECHNICAL_PROMPT = '''Also provide technical_assessment from native_technical_context as an independent
entry-context interpretation. SUPPORTIVE, MIXED, ADVERSE and INSUFFICIENT are model
interpretations, not source facts or changes to fundamental attractiveness.
Use the supplied provider fields, formula semantics, timeframes and bar dates.
Do not recalculate indicators, replace their formulas, invent universal thresholds
or treat unavailable values as zero. Short history alone does not invalidate the
other supplied values. Cite the exact supplied native evidence_refs you actually
used; explain agreement, conflict or limitations in a short Korean qualitative
reason. INSUFFICIENT must describe a material interpretive gap, not boilerplate
scarcity merely because a long-window field is missing. Do not repeat numeric
values or create new numeric facts in the reason; exact indicator names such as
RSI14 and MA144 are permitted. No tools or additional source requests.
Keep timing_context's selected zone, price relation and evidence unchanged.
Technical weakness may require entry confirmation, but cannot overturn fundamental
ATTRACTIVE, business direction, Holder or the valuation judgment. This assessment
is neither fair value nor a standalone buy instruction. Its short reason is the
only additional prose field; return the closed schema.'''


C60_TECHNICAL_PROMPT = """Use a concise Korean synthesis of the useful supplied families and time horizons.
The optional change field describes recent movement (IMPROVING, DETERIORATING, STABLE,
UNCLEAR), independently of the four technical states. Omit it or use UNCLEAR if the
observations do not resolve direction; ADVERSE can be improving and SUPPORTIVE deteriorating.
Recognize early recovery within a mixed or weak longer-term trend; do not require full
bullish alignment. A favorable price/RR alone does not prove recovery or a sound structure.
Explain material conflicting evidence, not a checklist or a majority count. Use qualitative
language and exact source refs; do not invent numeric observations. Technical analysis never
changes the frozen economics, selected candidate, or backend price relation."""


def c60_technical_input(model_input):
    return model_input.get('native_technical_context', {}).get('comparison_version') == 1


def prompt_for(model_input):
    prompt = PROMPT
    if 'economic_context' in model_input:
        prompt = prompt.replace(
            'SUPPORTIVE with an eligible business gate and no active risk or authorized veto\nrequires fundamental ATTRACTIVE.',
            'SUPPORTIVE permits, but does not require, ATTRACTIVE when the business is assessable.')
        prompt = prompt.replace('Return only the closed schema. No free prose or newly calculated source facts.',
            'Return only the closed schema, including the qualitative economic_reason. No new numeric facts.')
        from scripts.m12ds_r2_schemas import ECONOMIC_BUSINESS_GUIDANCE
        prompt += '\n' + ECONOMIC_BUSINESS_GUIDANCE + """
SUPPORTIVE includes a reasonable price for a good company, not only an obvious discount.
Evaluate the economic merits of the current price with the eligible positive and ordinary
negative business evidence. HOLD/MIXED is not itself a veto. If the allowed stance branches
permit either ATTRACTIVE or WAIT, decide based on the actual business and price. A WAIT
with SUPPORTIVE requires a specific, cited economic uncertainty material at this price,
not generic future uncertainty, routine monitoring, or technical timing. Use economic_reason
to explain both the valuation judgment and the stance, including the actual remaining risk
or why it is economically tolerable. Cite the positive business claim for ATTRACTIVE;
context observations may inform the explanation but cannot create business eligibility.
Absolute context field refs are the original normalized source hashes, not new directional
claims. Use their reported period/role exactly; do not infer a missing prior observation.
The derived margin relationship shares its two original source refs.
Do not independently penalize the same ordinary risk again: business analysis identifies
the risk, valuation evaluates whether it is reflected in the price. Keep active risk AVOID,
SELL restriction, exact quality limits, and frozen Overall/Holder. Low multiples alone
do not prove cheapness, high multiples alone do not prove burden. No implied EPS, target,
new ratio or price range. Use Korean qualitative prose, without unbound numbers.
"""
    if 'provider_reference_context' in model_input:
        prompt += '''
Use the provider_reference_context as independently owned descriptive valuation
context. Direct EPS/BPS are actual provider fields; unknown exact fiscal periods,
underlying split basis and provider formulas remain unknown. Never reconstruct
EPS from a ratio. Quarterly distributions are not own weekly PIT history.
Compare the current atomic ratio only with its same-provider field family and
only when current_value/current_metric_ref are present. Percentiles are empirical
ranks among observed positive ratios; inspect nonpositive, missing and conflict
counts. Missing dates are not proof of losses. Prefer the common recent five-year
window for current relevance; the whole series is context, not an alternative
chosen for a desired result. Quote quotients are diagnostics with an explicit
price basis, not replacement PER/PBR. If a current multiple and direct field
appear inconsistent, preserve their separate semantics; do not force a match
or assert cheapness. A provider-based price is a conditional arithmetic
scenario; exact numerator/denominator equivalence is not certified. A missing
quote-basis link precludes a precise quote relation/combined technical price,
not a descriptive reference. Never make business claims from these references.
Cite only actually used provider_reference_refs in the separate array and keep
the current valuation and business refs in their existing roles. These optional
references cannot grant current-multiple usability, override risk or change
Overall/Holder/technical timing.'''
    if 'historical_price_context' in model_input:
        prompt += '''
Historical price candidates are source-owned descriptive arithmetic, not target
prices or established fair value. A's valuation tier is a viewpoint, not proof.
Consider each eligible method independently; explain conflicting results and
whether current earnings/book are representative (cyclicality, unusual gains,
cash conversion, capital allocation). Never average conflicting methods.
In economic_price_review select one supplied candidate only if its assumptions
are economically defensible as a conditional value scenario; otherwise use
UNRESOLVED. An optional LOW/HIGH edge is a PREFERRED review price, not a maximum
permissible price and not an extra veto on current ATTRACTIVE. Use NONE for no
preferred edge. Explain the selection or limitation in economic_reason without
inventing prices, multiples, EPS, or required returns. The reference alone cannot
create business eligibility, waive missing qualified metrics, override a quality
or confidence veto, or offset active material risk or SELL. Neither historical
prices nor technical timing mechanically determine the economic stance.
'''
    if model_input.get('step2_quality_version') == 1:
        prompt += """
Use actual business observations, including cash generation, capital allocation,
competitive evidence and growth progress when present. A prior investment thesis
is a hypothesis to assess, not a newly verified success. Headlines are leads,
not confirmed results. Do not infer competitive facts from a financial ratio.
Distinguish ordinary business uncertainty from a concrete economic limitation.
If historical candidates are selectable but none is chosen, explain the
economic reason in economic_reason. If none is selectable, do not repeat
backend source-availability or selection-restriction notices.
Finish complete, concise Korean sentences well below the character limit.
"""
    if 'native_technical_context' not in model_input:
        return prompt
    prompt = ('Judge NewBuyer fundamental/valuation attractiveness and, separately, the supplied native technical evidence.'
            + prompt[prompt.index('\n'):] + '\n' + NATIVE_TECHNICAL_PROMPT)
    if c60_technical_input(model_input):
        from app.services.canonical_monitoring_input import C60_NATIVE_GUIDANCE
        prompt += '\n' + C60_NATIVE_GUIDANCE + '\n' + C60_TECHNICAL_PROMPT
    if 'technical_structure_context' in model_input:
        prompt += '''\nAlso interpret the existing technical_structure_context observations and
selected_entry_scenario, if provided. Their supplied ref_id/evidence_ref values are valid
technical citations. Use actual support/resistance roles, confirmation dates, ATR, Fibonacci
anchors, and observed price/volume as relevant; do not duplicate the native facts or transfer
risk from another candidate. General chart state is context, not the selected scenario.
Current and hypothetical target/RR are different; a role-unconfirmed barrier is uncertainty,
not a confirmed target. Use state to express the material *current* entry risk: ADVERSE for
decisive adverse evidence, MIXED for genuinely competing evidence without a decisive veto.
SUPPORTIVE can be deteriorating, and MIXED need not be fully recovered. Change is descriptive,
never another approval requirement. Missing native fields alone are not adverse. RR is not
expected return or probability. Consider actual upside and downside, including a near target.
Use qualitative prose; numeric values are rendered separately by the backend.'''
    if model_input.get('step2_quality_version') == 1:
        prompt = prompt.replace(
            'Use state to express the material *current* entry risk: ADVERSE for\n'
            'decisive adverse evidence, MIXED for genuinely competing evidence without a decisive veto.',
            'Use state to express observed trend, momentum and structural evidence: ADVERSE for '
            'decisive observed deterioration, MIXED for genuinely competing technical observations.')
        prompt += """
STEP 2: Separate observed technical state from deterministic entry quality.
Monthly bars describe long-term structure, weekly bars the medium-term trend and
daily bars actual entry momentum. Explain material disagreements and emerging recovery.
The recent_path arrays are chronological, at the exact supplied completed dates;
use the available close, volume, RSI14, MACD, MACD_HIST and VOLUME_RATIO_20
path to distinguish sustained recovery from intermittent rebounds. Null is unknown.
Do not penalize missing long windows. Low RR, price distance or nearby resistance
overlap alone do not establish ADVERSE technical state. Actual observed structural
breakdown, persistent weakness or decisive adverse evidence can establish ADVERSE.
Backend entry quality retains all current RR, overlap and invalidation restrictions.
If technical_flow_context is supplied, interpret the exact KR share quantities in
their own overlapping windows with matching dated price/volume; do not sum the windows
or infer intent, future direction, or business value. A path of twenty closes spans
nineteen close-to-close changes: use an existing native RETURN_20D for a twenty-bar
return if supplied, and never invent an earlier close. NOT_APPLICABLE is not missing evidence.
Cite its supplied ref_id only in technical_assessment. A single current observation
does not establish a trend. Finish concise Korean sentences well below the maximum.
Do not repeat numeric facts or generic source caveats. Explain the actual economic
counterargument and, where selection is allowed but no historical candidate is chosen,
explain the specific representative-earnings, method, or price-basis limitation in
economic_reason. No obligation to select a candidate. Prefer the actual supplied
business and cash-generation evidence over generic statements about uncertainty.
"""
    return prompt


def technical_refs(model_input):
    native = model_input.get('native_technical_context', {})
    refs = {ref for period in native.get('periods', {}).values()
            for field, ref in period.get('evidence_refs', {}).items()
            if period.get('indicators', {}).get(field) is not None
            and period.get('indicator_quality', {}).get(field) == 'PROVIDER_NATIVE'}
    if 'technical_structure_context' in model_input:
        refs.update(row['ref_id'] for row in model_input['technical_structure_context']
                    if row.get('observation'))
        scenario = model_input.get('selected_entry_scenario') or {}
        if scenario.get('evidence_ref') in model_input.get('timing_refs', ()):
            refs.add(scenario['evidence_ref'])
    flow = model_input.get('technical_flow_context') or {}
    if flow.get('status') == 'AVAILABLE' and flow.get('windows'):
        refs.add(flow['ref_id'])
    return sorted(refs)


def technical_assessment_schema(model_input):
    available = technical_refs(model_input)
    current = c60_technical_input(model_input)
    fields = dict(
        state=dict(type='string', enum=['SUPPORTIVE', 'MIXED', 'ADVERSE', 'INSUFFICIENT'])
              if available else dict(const='INSUFFICIENT'),
        evidence_refs=v1.refs(available, 1) if available else
                      dict(const=[], items=dict(type='string')),
        reason=dict(type='string', minLength=1, maxLength=600 if model_input.get('step2_quality_version') == 1
                    else 400 if current else 240) if available else
                dict(const='활용 가능한 원본 지표가 없어 기술 해석을 보류합니다.'))
    original = v1.obj(fields)
    if not current:
        return original
    change = (dict(type='string', enum=['IMPROVING', 'DETERIORATING', 'STABLE', 'UNCLEAR'])
              if available else dict(const='UNCLEAR'))
    # Provider strict objects require all their declared properties. Two closed
    # shapes keep absence genuinely valid without an optional-property wire error.
    return dict(anyOf=[v1.obj(dict(fields, change=change)), original])


def technical_reason(text, refs):
    """Use the existing prose boundary, allowing digits only in provider names."""
    from app.services.detailed_stock_message_service import _safe_prose
    from app.services.provider_native_technical import INDICATORS

    names = '|'.join(re.escape(name) for name in sorted(INDICATORS, key=len, reverse=True))
    prose = re.sub(r'(?<![A-Za-z0-9_])(?:' + names + r')(?![A-Za-z0-9_])', '', text,
                   flags=re.IGNORECASE)
    _safe_prose(prose, refs)
    if re.search(r'\d|[\r\n]', prose):
        raise ValueError('native_technical_unbound_number_or_multiline_reason')
    return text


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


def economic_refs(model_input):
    return sorted({r['claim_ref'] for r in model_input['business_context']}
                  | {r['ref_id'] for r in model_input.get('economic_context', {}).get('observations', ())})


def capabilities(model_input):
    rows = []
    for state in states(model_input):
        stance, reason, evidence = policy.choices(model_input, state)
        rows.append(dict(valuation_state=state, stance=stance, reason=reason,
                         reason_evidence_refs=evidence))
        if 'economic_context' in model_input and state == 'SUPPORTIVE' and stance == 'ATTRACTIVE':
            rows.append(dict(valuation_state=state, stance='WAIT', reason='ECONOMIC_UNCERTAINTY',
                             reason_evidence_refs=None))
    return rows


def provider_reference_refs(model_input):
    context = model_input.get('provider_reference_context', {})
    return {row['ref_id'] for key in ('direct','history') for row in context.get(key, ())}


def historical_price_refs(model_input):
    # These identifiers are not business capability refs or qualified multiples.
    return {ref for row in model_input.get('historical_price_context', {}).get('candidates', ())
            for ref in [row['candidate_id'], *row['evidence_refs']]} | provider_reference_refs(model_input)


def economic_reason(text, refs):
    from app.services.detailed_stock_message_service import _safe_prose
    return _safe_prose(text, refs)


def output_schema(model_input):
    facts = model_input['qualified_usable_valuation_facts']
    current = 'economic_context' in model_input
    business = economic_refs(model_input) if current else [r['claim_ref'] for r in model_input['business_context']]
    branches = []
    for row in capabilities(model_input):
        state, evidence = row['valuation_state'], row['reason_evidence_refs']
        unresolved = state == 'UNRESOLVED'
        valuation = v1.obj(dict(
            state=dict(const=state),
            authority=dict(const='BACKEND_COMPOSITE_UNUSABLE' if unresolved else 'MODEL_JUDGED'),
            valuation_evidence_refs=dict(const=[]) if unresolved else v1.refs(facts,1),
            business_evidence_refs=dict(const=[]) if unresolved else v1.refs(business,
                1 if current and row['stance'] == 'ATTRACTIVE' else 0),
            all_metrics_unusable_proof_ref=dict(const=model_input['all_metrics_unusable_proof_ref']),
        ))
        fields = dict(contract=dict(const=CONTRACT),input_sha256=dict(const=digest(model_input)),
            valuation_context=valuation, timing_context=dict(const=model_input['timing_context']),
            new_buyer=dict(const=row['stance']),reason_class=dict(const=row['reason']),
            reason_evidence_refs=(v1.refs(business,1) if row['reason']=='ECONOMIC_UNCERTAINTY'
                                  else v1.refs(facts,1) if evidence is None else dict(const=evidence)),
            active_risk_refs=dict(const=model_input['active_risk_refs']))
        if current:
            fields['economic_reason'] = dict(type='string', minLength=1,
                maxLength=600 if model_input.get('step2_quality_version') == 1 else 360)
        if 'provider_reference_context' in model_input:
            fields['provider_reference_refs'] = v1.refs(sorted(provider_reference_refs(model_input)),0)
        if 'historical_price_context' in model_input:
            eligible = (model_input['business_gate']['v2_business_gate_pass']
                        and not model_input['active_risk_refs']
                        and not model_input['confidence_veto_refs'] and not unresolved)
            ids = [r['candidate_id'] for r in model_input['historical_price_context']['candidates']] if eligible else []
            fields['economic_price_review'] = v1.obj(dict(
                candidate_id=dict(type='string', enum=['UNRESOLVED', *ids]),
                preferred_boundary=dict(type='string', enum=['NONE','LOW','HIGH'] if ids else ['NONE'])))
        if 'native_technical_context' in model_input:
            fields['technical_assessment'] = technical_assessment_schema(model_input)
        branches.append(v1.obj(fields))
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
    if 'economic_context' in model_input:
        if (output['new_buyer'] == 'ATTRACTIVE' and not
                set(val['business_evidence_refs'] + output['reason_evidence_refs'])
                    & set(model_input['business_gate']['eligible_positive_core_refs_after_quality'])):
            errors.append('ECONOMIC_ATTRACTIVE_POSITIVE_REF_REQUIRED')
        if (output['reason_class'] == 'ECONOMIC_UNCERTAINTY'
                and (not output['reason_evidence_refs']
                     or not set(output['reason_evidence_refs']) <= set(economic_refs(model_input)))):
            errors.append('ECONOMIC_WAIT_REF_SCOPE')
        try:
            economic_reason(output['economic_reason'], sorted(set(economic_refs(model_input))
                | set(model_input['qualified_usable_valuation_facts']) | set(model_input['active_risk_refs'])
                | historical_price_refs(model_input)))
        except ValueError:
            errors.append('ECONOMIC_REASON_UNBOUND')
    if 'provider_reference_context' in model_input:
        selected = output['provider_reference_refs']
        if len(selected)!=len(set(selected)) or not set(selected)<=provider_reference_refs(model_input):
            errors.append('PROVIDER_REFERENCE_REF_SCOPE')
    if 'historical_price_context' in model_input:
        price_review = output['economic_price_review']
        if price_review['candidate_id'] == 'UNRESOLVED' and price_review['preferred_boundary'] != 'NONE':
            errors.append('HISTORICAL_PREFERRED_PRICE_REQUIRES_SELECTED_CANDIDATE')
    if 'native_technical_context' in model_input:
        technical = output['technical_assessment']
        refs = technical['evidence_refs']
        if len(refs) != len(set(refs)):
            errors.append('DUPLICATE_EXACT_TECHNICAL_REF')
        try:
            technical_reason(technical['reason'], refs)
        except ValueError:
            errors.append('NATIVE_TECHNICAL_REASON_UNBOUND')
    return dict(status='FAIL' if errors else 'PASS',errors=errors,
        model_judgment_observed=False,economic_correctness_proven=False,
        new_source_facts=False,scope='NEWBUYER_V2_OFFLINE_SHADOW_ONLY')


def presentation_plan(output, model_input):
    if validate_output(output,model_input)['status'] != 'PASS':
        raise ValueError('v2_invalid_presentation_input')
    plan = dict(contract=CONTRACT,fundamental_attractiveness=output['new_buyer'],
        entry_timing=deepcopy(output['timing_context']),
        valuation_judgment=output['valuation_context']['state'],
        independent_axes=True,bare_buy_label_allowed=False,production_delivery_allowed=False,
        numeric_owner='EXISTING_BACKEND_VALUATION_RENDERER')
    if 'economic_reason' in output:
        plan['economic_reason'] = output['economic_reason']
    if 'technical_assessment' in output:
        plan['technical_assessment'] = deepcopy(output['technical_assessment'])
    if 'economic_price_review' in output:
        plan['economic_price_review'] = deepcopy(output['economic_price_review'])
    return plan
