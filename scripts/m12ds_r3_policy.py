"""Shadow severity and axis policy, with canonical order owned by atomic claims."""
from copy import deepcopy
from datetime import date
from enum import StrEnum

from scripts import m12ds_r2_judgment_policy as r2
from scripts.m12dr_financial_source_authority import FAMILY, CONTRACT as COMPARISON_CONTRACT

CONTRACT = 'm12ds-r3-residual-judgment-policy-v1'
frozen_fact_fields = r2.frozen_fact_fields
number = r2.number
canonical_sha256 = r2.canonical_sha256


class Effect(StrEnum):
    POSITIVE = 'DIRECTIONAL_POSITIVE'
    CURRENT = 'DIRECTIONAL_NEGATIVE_CURRENT_STATE'
    DETERIORATION = 'DIRECTIONAL_NEGATIVE_DETERIORATION'
    IMPAIRMENT = 'THESIS_IMPAIRMENT'
    CONFIDENCE = 'CONFIDENCE_ONLY'
    CONDITION = 'REEVALUATION_CONDITION'
    QUALITY = 'DATA_QUALITY_ONLY'


ADVERSE = {Effect.CURRENT, Effect.DETERIORATION, Effect.IMPAIRMENT}


def comparable(fields):
    current, prior = fields.get('current_period'), fields.get('prior_period')
    if not isinstance(current, dict) or not isinstance(prior, dict):
        return False
    try:
        dates = [date.fromisoformat(p[k]) for p in (current, prior) for k in ('start', 'end')]
        return (dates[0] <= dates[1] and dates[2] <= dates[3] < dates[1]
                and fields.get('comparison_type') in ('YOY', 'QOQ', 'SAME_DURATION_BASELINE')
                and (dates[1] - dates[0]).days == (dates[3] - dates[2]).days
                and all(current.get(k) and current[k] == prior.get(k)
                        for k in ('period_type', 'currency', 'unit', 'entity_scope', 'statement_basis')))
    except (ValueError, TypeError, KeyError):
        return False


def observations(metadata, authority, fact_fields=None):
    result = {}
    records = {r['ref_id']: r for r in authority['authority_records']}
    for old_id, old in r2.observations(metadata, authority, fact_fields).items():
        obs = deepcopy(old)
        record = records[obs['source_ref']]
        # This existing owner recomputes exact comparative facts from frozen filing occurrences.
        owned_comparison = (record.get('source_family') == FAMILY
                            and record.get('authority_basis') == COMPARISON_CONTRACT
                            and record.get('source_scope') == 'exact_comparative_issuer_business_no_valuation'
                            and bool(obs['fact_binding']))
        if obs['prior_value'] is not None and not (owned_comparison or comparable(obs['financial_scope'])):
            continue
        if obs['effect'] == r2.Effect.NEGATIVE:
            obs['effect'] = Effect.DETERIORATION.value if obs['prior_value'] is not None else Effect.CURRENT.value
            if obs['effect'] == Effect.CURRENT:
                obs['text'] += ' Current state alone does not establish deterioration or thesis impairment.'
                obs['risk_trigger'] = 'OBSERVED_OPERATING_STRESS'
        obs['parent_observation_id'] = old_id
        obs['contract'] = CONTRACT
        obs.pop('observation_id')
        new_id = 'observed-proposition:' + canonical_sha256(obs)
        result[new_id] = {**obs, 'observation_id': new_id}
    return result


def canonical_core(core):
    """Dictionary order is incidental; the frozen atomic array owns ref order."""
    if core['binding_sha256'] != canonical_sha256({'atomic': core['atomic_claims'], 'effects': core['effects']}):
        raise ValueError('core_effect_binding_drift')
    order = [c['claim_ref'] for c in core['atomic_claims']]
    if len(set(order)) != len(order) or set(order) != set(core['effects']):
        raise ValueError('core_ref_order_manifest_mismatch')
    restored = deepcopy(core)
    restored['effects'] = {ref: restored['effects'][ref] for ref in order}
    return restored


def materialize_core(ticker, raw, metadata, authority, fact_fields=None):
    observed = observations(metadata, authority, fact_fields)
    coarse = deepcopy(raw)
    for original, claim in zip(raw['claims'], coarse['claims'], strict=True):
        effect = Effect(original['effect'])
        if effect == Effect.IMPAIRMENT:
            # The current packet adapter has no verified realized-event owner.
            raise ValueError('realized_impairment_source_unavailable')
        if effect in ADVERSE or effect == Effect.POSITIVE:
            ids = original['observation_ids']
            if not ids or any(i not in observed or observed[i]['effect'] != effect for i in ids):
                raise ValueError('severity_observation_mismatch')
            claim['observation_ids'] = [observed[i]['parent_observation_id'] for i in ids]
            claim['effect'] = r2.Effect.NEGATIVE.value if effect in ADVERSE else effect.value
    core = r2.materialize_core(ticker, coarse, metadata, authority, fact_fields)
    for claim, original in zip(core['atomic_claims'], raw['claims'], strict=True):
        effect = core['effects'][claim['claim_ref']]
        effect.update(effect=original['effect'], observation_ids=original['observation_ids'],
                      model_claim_sha256=canonical_sha256(original), severity_contract=CONTRACT)
        if original['effect'] == Effect.CURRENT:
            effect['risk_triggers'] = ['OBSERVED_OPERATING_STRESS']
    core['observations'] = observed
    core['binding_sha256'] = canonical_sha256({'atomic': core['atomic_claims'], 'effects': core['effects']})
    return canonical_core(core)


def axis_capability(core, chain, catalog, metadata):
    core = canonical_core(core)
    coarse = deepcopy(core)
    for effect in coarse['effects'].values():
        if effect['effect'] in ADVERSE:
            effect['effect'] = r2.Effect.NEGATIVE.value
    coarse['binding_sha256'] = canonical_sha256({'atomic': coarse['atomic_claims'], 'effects': coarse['effects']})
    cap = r2.axis_capability(coarse, chain, catalog, metadata)
    cap.update(contract=CONTRACT, core_binding_sha256=core['binding_sha256'],
               canonical_ref_order=[c['claim_ref'] for c in core['atomic_claims']],
               current_stress=[], deterioration=[], impairment=[], sell_eligible=[])
    for ref, effect in core['effects'].items():
        bucket = {Effect.CURRENT: 'current_stress', Effect.DETERIORATION: 'deterioration',
                  Effect.IMPAIRMENT: 'impairment'}.get(effect['effect'])
        if bucket:
            cap[bucket].append(ref)
        if effect['effect'] in (Effect.DETERIORATION, Effect.IMPAIRMENT) or ref in cap['holder_reduce']:
            cap['sell_eligible'].append(ref)
    return cap


def validate_decision(row, cap, ranges):
    checked = deepcopy(row)
    current_hold = row['overall_reason_class'] == 'CURRENT_STRESS_WITHOUT_PROVEN_DETERIORATION'
    if current_hold:
        checked['overall_reason_class'] = 'INSUFFICIENT_DIRECTIONAL_EVIDENCE'
    receipt = r2.validate_decision(checked, cap, ranges)
    errors = receipt['errors']
    if row['overall_direction'] == 'SELL' and not set(row['contradicting_refs']) & set(cap['sell_eligible']):
        errors.append('sell_requires_verified_deterioration_persistence_or_impairment')
    if current_hold and (row['overall_direction'] != 'HOLD' or not row['contradicting_refs']
                         or not set(row['contradicting_refs']) <= set(cap['current_stress'])):
        errors.append('current_state_hold_scope_mismatch')
    if cap['holder_risk'] and not ranges['compensating_discount'] and row['new_buyer'] != 'AVOID':
        errors.append('active_adverse_without_compensation_precedes_wait')
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors}


def policy_audit(row, cap, ranges):
    result = r2.policy_audit(row, cap, ranges)
    result['severity'] = {k: deepcopy(cap[k]) for k in ('current_stress', 'deterioration', 'impairment', 'sell_eligible')}
    result['ordering_owner'] = 'FROZEN_ATOMIC_CLAIM_ARRAY'
    result['archetype'] = ranges['option'].get('archetype')
    return result
