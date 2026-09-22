"""Provider/internal schemas for R3 severity and adverse-risk precedence."""
from copy import deepcopy

from scripts import m12ds_r2_schemas as r2
from scripts import m12ds_r3_policy as policy

obj, enum, string, refs = r2.obj, r2.enum, r2.string, r2.refs
normalize_decision = r2.normalize_decision


def core_schema(inputs):
    subjects = {}
    for ticker, context in inputs.items():
        obs = policy.observations(context['metadata'], context['authority'], context.get('frozen_fact_fields'))
        branches = []
        for oid, observation in obs.items():
            material = ['CONTEXT_ONLY']
            if observation['effect'] in policy.ADVERSE:
                material.append('ACTIVE_MATERIAL_RISK')
            branches.append(obj({'effect': enum([observation['effect']]), 'text': string(maximum=420),
                'evidence_refs': refs([observation['source_ref']], 1, 1), 'observation_ids': refs([oid], 1, 1),
                'materiality': enum(material)}))
        for effect in (policy.Effect.CONFIDENCE, policy.Effect.QUALITY, policy.Effect.CONDITION):
            eligible = [r['ref_id'] for r in context['metadata']
                        if bool(r.get('logical_condition')) == (effect == policy.Effect.CONDITION)]
            if eligible:
                branches.append(obj({'effect': enum([effect.value]), 'text': string(maximum=420),
                    'evidence_refs': refs(eligible, 1, 1), 'observation_ids': refs([]), 'materiality': enum(['CONTEXT_ONLY'])}))
        if not branches:
            raise ValueError('core_source_empty')
        subjects[ticker] = obj({'claims': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': {'anyOf': branches}}})
    return obj({'cores': obj(subjects)})


def decision_schema(cap, valuation, entry_catalog):
    schema = r2.decision_schema(cap, valuation, entry_catalog)
    props = schema['properties']
    overall = []
    for branch in props['overall']['anyOf']:
        fields = branch['properties']
        if fields['overall_direction']['enum'] == ['SELL']:
            if not cap['sell_eligible']:
                continue
            fields['contradicting_refs'] = refs(cap['sell_eligible'], 1)
        overall.append(branch)
    if cap['current_stress']:
        current = deepcopy(overall[0])
        current['properties'].update(overall_direction=enum(['HOLD']),
            overall_reason_class=enum(['CURRENT_STRESS_WITHOUT_PROVEN_DETERIORATION']),
            supporting_refs=refs(cap['positive']), contradicting_refs=refs(cap['current_stress'], 1))
        overall.append(current)
    props['overall']['anyOf'] = overall
    if cap['holder_risk'] and not valuation['compensating_discount']:
        props['new_buyer_axis']['anyOf'] = [branch for branch in props['new_buyer_axis']['anyOf']
                                          if branch['properties']['new_buyer']['enum'] == ['AVOID']]
    return schema


CORE_PROMPT = r2.CORE_PROMPT + '''
R3 severity: a current operating loss/negative margin is DIRECTIONAL_NEGATIVE_CURRENT_STATE,
not deterioration or impairment. Only the provided comparable dated observation may be
DIRECTIONAL_NEGATIVE_DETERIORATION. Never turn single-period stress into persistent stress.
Only source-owned realized impairment may support THESIS_IMPAIRMENT; if absent it is unavailable.
Do not infer deterioration from archetype, uncertainty, or future conditions.
Core is not an Overall vote. Report material current stress without assuming SELL.'''

B_PROMPT = r2.B_PROMPT + '''
R3 precedence supersedes the generic WAIT fallback: active material adverse business evidence
without an established compensating fundamental discount requires AVOID. Unresolved valuation
is NOT compensation. Confidence-only uncertainty without active adverse risk may remain WAIT.
Overall is long-horizon thesis direction, independent of entry timing and conviction confidence.
For DURABLE_FRANCHISE, STRUCTURAL_CYCLICAL_LEADER, PROFITABLE_PREMIUM_GROWTH and established
profitable-core businesses, observed positive business direction with intact thesis and no
realized material negative can remain BUY at LOW or MEDIUM confidence. Persistence caution
alone must not force HOLD. Do not invent positive direction from revenue presence alone.
For EXECUTION_DEPENDENT_GROWTH, weigh actual execution; a current pre-profit loss is not by
itself deterioration. It can support Holder REVIEW and New Buyer AVOID with Overall HOLD.
SELL needs eligible deterioration, verified persistence, financing/thesis impairment, or realized
failure. Mature-business unexpected loss also needs an observed comparable baseline; archetype
alone does not establish that it was unexpected. No label/distribution quotas or named examples.'''
