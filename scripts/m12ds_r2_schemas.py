"""R2 shadow schemas project exact effect/axis eligibility, with no target labels."""
from copy import deepcopy
from scripts.m12cr_shadow_contract import _strict_object as obj, _enum as enum, _string as string
from scripts.m12ds_r2_judgment_policy import Effect, observations


def refs(values, minimum=0, maximum=6):
    values = sorted(set(values))
    if minimum and not values:
        raise ValueError('required_axis_has_no_eligible_refs')
    return {'type':'array', 'items':enum(values) if values else {'type':'string'},
            'minItems':minimum, 'maxItems':min(maximum,len(values)), 'uniqueItems':True}


def core_schema(inputs):
    subjects = {}
    for ticker, context in inputs.items():
        obs = observations(context['metadata'], context['authority'], context.get('frozen_fact_fields'))
        branches = []
        for oid, observation in obs.items():
            material = ['CONTEXT_ONLY']
            if observation['effect'] == Effect.NEGATIVE:
                material += ['ACTIVE_MATERIAL_RISK']
                if observation['persistence_verified'] or observation['impairment_realized']:
                    material += ['PERSISTENT_OR_IMPAIRED']
            branches.append(obj({'effect':enum([observation['effect']]), 'text':string(maximum=420),
                'evidence_refs':refs([observation['source_ref']],1,1), 'observation_ids':refs([oid],1,1),
                'materiality':enum(material)}))
        for effect in (Effect.CONFIDENCE, Effect.QUALITY, Effect.CONDITION):
            eligible = [r['ref_id'] for r in context['metadata'] if bool(r.get('logical_condition')) == (effect == Effect.CONDITION)]
            if eligible:
                branches.append(obj({'effect':enum([effect.value]), 'text':string(maximum=420),
                    'evidence_refs':refs(eligible,1,1), 'observation_ids':refs([]), 'materiality':enum(['CONTEXT_ONLY'])}))
        if not branches:
            raise ValueError('core_source_empty')
        subjects[ticker] = obj({'claims':{'type':'array', 'minItems':1, 'maxItems':8, 'items':{'anyOf':branches}}})
    return obj({'cores':obj(subjects)})


def decision_schema(cap, valuation, entry_catalog):
    common = {'overall_direction':enum(['BUY','HOLD','SELL']), 'confidence':enum(['LOW','MEDIUM','HIGH']),
        'directional_buy_score':{'type':'number','minimum':0,'maximum':10},
        'overall_reason_class':enum(['OBSERVED_POSITIVE_DOMINANT','OBSERVED_NEGATIVE_DOMINANT','BALANCED_DIRECTIONAL_EVIDENCE',
                                    'POSITIVE_BUT_CONFIDENCE_CAPPED','INSUFFICIENT_DIRECTIONAL_EVIDENCE']),
        'supporting_refs':refs(cap['positive']), 'contradicting_refs':refs(cap['negative']),
        'confidence_caution_refs':refs(cap['confidence']), 'data_quality_refs':refs(cap['quality']), 'reevaluation_refs':refs(cap['condition']),
        'overall_reason':string(maximum=500)}
    overall = []
    specs = [('HOLD','INSUFFICIENT_DIRECTIONAL_EVIDENCE',False,False,False)]
    if cap['positive']:
        specs += [('BUY','OBSERVED_POSITIVE_DOMINANT',True,False,False)]
        if cap['confidence']:
            specs += [('HOLD','POSITIVE_BUT_CONFIDENCE_CAPPED',True,False,True)]
    if cap['negative']:
        specs += [('SELL','OBSERVED_NEGATIVE_DOMINANT',False,True,False)]
    if cap['positive'] and cap['negative']:
        specs += [('HOLD','BALANCED_DIRECTIONAL_EVIDENCE',True,True,False)]
    for label, reason, need_pos, need_neg, need_caution in specs:
        props = deepcopy(common)
        props.update(overall_direction=enum([label]), overall_reason_class=enum([reason]),
            supporting_refs=refs(cap['positive'],int(need_pos)), contradicting_refs=refs(cap['negative'],int(need_neg)),
            confidence_caution_refs=refs(cap['confidence'],int(need_caution)))
        if need_caution:
            props['contradicting_refs'] = refs([])
            props['confidence'] = enum(['LOW','MEDIUM'])
        overall.append(obj(props))
    if cap['positive'] and cap['quality']:
        props = deepcopy(common)
        props.update(overall_direction=enum(['HOLD']), overall_reason_class=enum(['POSITIVE_BUT_CONFIDENCE_CAPPED']),
                     confidence=enum(['LOW','MEDIUM']), supporting_refs=refs(cap['positive'],1),
                     contradicting_refs=refs([]), data_quality_refs=refs(cap['quality'],1))
        overall.append(obj(props))
    holder = []
    if not cap['holder_risk'] and cap['holder_support']:
        holder.append(obj({'holder':enum(['HOLDABLE']), 'holder_reason_class':enum(['THESIS_INTACT_NO_ACTIVE_MATERIAL_TRIGGER']),
            'holder_reason_evidence_refs':refs(cap['holder_support'],1), 'holder_reason':string(maximum=500)}))
    for stance, key in (('REVIEW','holder_risk'),('REDUCE','holder_reduce')):
        triggers = sorted({t for ref in cap[key] for t in cap['risk_triggers'][ref]})
        for trigger in triggers:
            eligible = [ref for ref in cap[key] if trigger in cap['risk_triggers'][ref]]
            holder.append(obj({'holder':enum([stance]), 'holder_reason_class':enum([trigger]),
                'holder_reason_evidence_refs':refs(eligible,1), 'holder_reason':string(maximum=500)}))
    if not holder:
        raise ValueError('M12DS_R2_HOLDER_AXIS_CONTRACT_DEPENDENCY')
    buyer = [obj({'new_buyer':enum(['WAIT']), 'new_buyer_reason_class':enum([
        'VALUATION_UNRESOLVED','CONFIDENCE_UNCERTAINTY','NO_CLEAN_ENTRY','PRICE_NOT_FAVORABLE']),
        'new_buyer_risk_refs':refs(cap['holder_risk']), 'new_buyer_reason':string(maximum=500)})]
    if valuation['fundamental_valid'] and valuation['compensating_discount']:
        buyer.append(obj({'new_buyer':enum(['ATTRACTIVE']), 'new_buyer_reason_class':enum(['VALID_FUNDAMENTAL_DISCOUNT']),
                          'new_buyer_risk_refs':refs(cap['holder_risk']), 'new_buyer_reason':string(maximum=500)}))
    elif cap['holder_risk']:
        buyer.append(obj({'new_buyer':enum(['AVOID']), 'new_buyer_reason_class':enum(['ACTIVE_ADVERSE_UNCOMPENSATED']),
                          'new_buyer_risk_refs':refs(cap['holder_risk'],1), 'new_buyer_reason':string(maximum=500)}))
    choices = [r['candidate_id'] for r in entry_catalog.get('tactical_candidates') or []] or ['UNRESOLVED']
    return obj({'overall':{'anyOf':overall}, 'holder_axis':{'anyOf':holder},
                'new_buyer_axis':{'anyOf':buyer}, 'tactical_choice':enum(choices)})


def normalize_decision(raw):
    return {**deepcopy(raw['overall']), **deepcopy(raw['holder_axis']), **deepcopy(raw['new_buyer_axis']),
            'tactical_choice':raw['tactical_choice']}


CORE_PROMPT = '''Use only this exact frozen packet. No tools, external knowledge, old outputs or target labels.
Select the meaningful current business propositions and separate them from epistemic cautions.
There is no quota for positive or negative claims. Never manufacture a sell driver.
Each directional claim must choose one exact observation_id and its matching source ref/effect.
The backend will materialize its canonical observation text; your text is a short interpretation, not a replacement fact.
Single-period recurrence not proven, insufficient trend evidence and valuation-basis uncertainty are CONFIDENCE_ONLY.
Configured future weakening/invalidation conditions are REEVALUATION_CONDITION, not realized events.
DATA_QUALITY_ONLY may reduce confidence, not independently create a bearish claim.
An observed operating loss or material deterioration may be ACTIVE_MATERIAL_RISK; do not infer persistence from one period.
Only classify materially holding-relevant adverse facts as active risks, not every minor fluctuation.
Positive facts use CONTEXT_ONLY materiality. Core does not choose prices or overall/holder/new-buyer labels.
Use exact opaque IDs. Keep conditional logical meaning. Return only the requested JSON.'''

B_PROMPT = '''Use only the frozen Core, A, source-use-bound evidence and deterministic policy capability supplied.
No tools, external knowledge, new facts, ticker targets or desired distribution.
Overall: meaningful positive observed evidence can support BUY; uncertainty lowers conviction without being a bearish counterweight.
Return one directional_buy_score from 0 through 10; the backend owns the exact sell complement to 10.
HOLD can be positive-but-confidence-capped with no negative refs, balanced observed facts, or insufficient directional evidence.
SELL requires observed adverse evidence, never uncertainty alone. Keep positive/negative/caution ref sets separate.
Holder is independent: evidence is mandatory. HOLDABLE requires no active material trigger; REVIEW uses actual material business risk.
REDUCE requires verified persistent deterioration or realized impairment, never one weak quarter alone.
New Buyer is independently evaluated: ATTRACTIVE needs valid non-conflicted fundamental discount, not technical support.
WAIT covers valuation incompleteness, conviction uncertainty or no clean entry. AVOID needs active material adverse risk without fundamental compensation.
Do not simply copy Overall or Holder. A Holder REVIEW does not mechanically force AVOID.
Choose an available tactical watch zone when supplied, including WAIT/AVOID. TACTICAL_WATCH_ZONE != FAIR_VALUE.
Never invent a fundamental range. Backend owns all prices, range status and method conflict.
Respect period, financial scope and industry cautions. No FCF yield, per-share FCF, CCC, ROIC or runway inference.
Return compact structured Korean rationale with exact refs, no unbound numerical additions.'''
