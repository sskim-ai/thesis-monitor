"""Shadow-only claim-effect ownership; source authority is an independent prerequisite."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import json

from app.services.cross_market_decision_engine_service import EvidenceClaim, _compact
from app.services.stage2_maturity_polarity_adapter_service import maturity_atomic_claim_ref
from app.services.logical_condition_service import SourceLogicalCondition, ClaimLogicalCondition, source_claim_expression
from scripts.m12cq_two_pass_contract import canonical_sha256
from scripts.m12da_source_use_contract import SourceUse, validate_selected_refs, validate_source_use_current_input

CONTRACT = 'm12ds-r2-judgment-policy-calibration-v1'


class Effect(StrEnum):
    POSITIVE = 'DIRECTIONAL_POSITIVE'
    NEGATIVE = 'DIRECTIONAL_NEGATIVE'
    CONFIDENCE = 'CONFIDENCE_ONLY'
    CONDITION = 'REEVALUATION_CONDITION'
    QUALITY = 'DATA_QUALITY_ONLY'


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


def statement(row):
    if isinstance(row.get('statement'), dict):
        return row['statement']
    try:
        value = json.loads(row.get('statement') or '{}')
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError):
        return {}


def frozen_fact_fields(packet, ticker, metadata):
    stock = next(r for r in packet['stocks'] if r['ticker']==ticker)
    facts = {'canonical:'+r['fact_id']:r for r in stock.get('fact_catalog') or []}
    result = {}
    for row in metadata:
        fact = facts.get(row['ref_id'])
        if fact and row.get('source_ref') == 'stock.fact_catalog.'+fact['fact_id']:
            if row.get('statement') != _compact(fact['fields']) or row.get('as_of') != fact['as_of_date']:
                raise ValueError('frozen_fact_projection_mismatch')
            result[row['ref_id']] = {'fields':deepcopy(fact['fields']), 'fact_sha256':canonical_sha256(fact)}
    return result


def observations(metadata, authority, fact_fields=None):
    """Mechanical observed propositions, never confidence prose or configured conditions."""
    permitted = {r['ref_id'] for r in authority['authority_records']
                 if r['authority_state'] == 'RESOLVED' and 'OVERALL_DIRECTION' in r['allowed_uses']}
    result = {}

    def add(row, metric, value, prior=None, fields=None):
        if value is None:
            return
        effect = None
        if prior is not None and value != prior:
            effect = Effect.POSITIVE if value > prior else Effect.NEGATIVE
        elif metric in ('operating_income', 'operating_margin_pct', 'operating_cash_flow') and value != 0:
            effect = Effect.POSITIVE if value > 0 else Effect.NEGATIVE
        elif metric == 'revenue' and value > 0:
            effect = Effect.POSITIVE
        if effect is None:
            return
        kind = ('OBSERVED_OPERATING_STRESS' if metric == 'operating_income' and value < 0
                else 'MATERIAL_MARGIN_OR_CASH_CONVERSION_DETERIORATION'
                if metric in ('operating_margin_pct', 'operating_cash_flow')
                else 'OBSERVED_BUSINESS_CONTRACTION') if effect == Effect.NEGATIVE else 'OBSERVED_BUSINESS_SUPPORT'
        payload = dict(source_ref=row['ref_id'], source_sha256=canonical_sha256(row), metric=metric,
                       value=str(value), prior_value=str(prior) if prior is not None else None,
                       effect=effect.value, risk_trigger=kind, as_of=row.get('as_of'),
                       persistence_verified=False, impairment_realized=False)
        payload['financial_scope'] = deepcopy(fields or {})
        payload['fact_binding'] = deepcopy((fact_fields or {}).get(row['ref_id']))
        # Canonical observation text cannot turn a durability caution into a bearish fact.
        relation = ('higher' if value > prior else 'lower') + ' versus the source-owned comparable period' if prior is not None and value != prior else 'positive' if value > 0 else 'negative'
        payload['text'] = (f"Reported {metric} is {relation}; source period {row.get('as_of')}. "
                           + ('Revenue presence alone does not establish growth, profitability or durability.' if metric=='revenue' and prior is None
                              else 'Recurrence is not established by this observation.'))
        oid = 'observed-proposition:' + canonical_sha256(payload)
        result[oid] = {'observation_id': oid, **payload}

    for row in metadata:
        if row['ref_id'] not in permitted or row.get('logical_condition') or row.get('category') != 'earnings':
            continue
        full = (fact_fields or {}).get(row['ref_id'])
        if full and _compact(full['fields']) != row['statement']:
            raise ValueError('observation_projection_mismatch')
        data = full['fields'] if full else statement(row)
        metric = data.get('metric')
        if metric in ('revenue', 'operating_income'):
            add(row, metric, number(data.get('current_value')), number(data.get('prior_comparable_value')),data)
        for metric in ('revenue', 'operating_income', 'operating_margin_pct'):
            raw = data.get(metric)
            add(row, metric, number(raw.get('value') if isinstance(raw, dict) else raw), fields=data)
    return result


def materialize_core(ticker, raw, metadata, authority, fact_fields=None):
    """Keep the model response untouched; emit an explicitly derived atomic catalog."""
    obs = observations(metadata, authority, fact_fields)
    known = {r['ref_id']: r for r in metadata}
    atomic, effects = [], {}
    for item in raw['claims']:
        effect = Effect(item['effect'])
        refs = item['evidence_refs']
        if not refs or len(set(refs)) != len(refs) or not set(refs) <= set(known):
            raise ValueError('core_unknown_duplicate_or_empty_source_refs')
        ids = item['observation_ids']
        if len(set(ids)) != len(ids) or not set(ids) <= set(obs):
            raise ValueError('core_unknown_or_duplicate_observation')
        directional = effect in (Effect.POSITIVE, Effect.NEGATIVE)
        if directional:
            if not ids or any(obs[x]['effect'] != effect for x in ids):
                raise ValueError('direction_effect_observation_mismatch')
            if set(refs) != {obs[x]['source_ref'] for x in ids}:
                raise ValueError('direction_exact_observation_parent_mismatch')
            text = ' '.join(obs[x]['text'] for x in ids)
            if len(text) > 420:
                raise ValueError('canonical_observation_claim_too_long')
        else:
            if ids or item['materiality'] != 'CONTEXT_ONLY':
                raise ValueError('non_directional_observation_or_risk_forbidden')
            text = item['text']
        conditions = [known[r]['logical_condition'] for r in refs if known[r].get('logical_condition')]
        if effect == Effect.CONDITION and not conditions:
            raise ValueError('condition_without_source_owned_condition')
        if effect != Effect.CONDITION and conditions:
            raise ValueError('configured_condition_not_observed')
        if effect != Effect.NEGATIVE and item['materiality'] != 'CONTEXT_ONLY':
            raise ValueError('non_adverse_material_risk')
        if item['materiality'] == 'PERSISTENT_OR_IMPAIRED' and not all(
            obs[x]['persistence_verified'] or obs[x]['impairment_realized'] for x in ids
        ):
            raise ValueError('unverified_persistent_or_impaired_claim')
        if len(conditions) > 1:
            raise ValueError('compound_condition_requires_single_source_owner')
        condition = None
        if conditions:
            source_condition = SourceLogicalCondition.model_validate(conditions[0])
            if source_condition.subject != ticker:
                raise ValueError('condition_cross_subject')
            condition = ClaimLogicalCondition(source_condition_ref=source_condition.source_condition_ref,
                coverage_mode='FULL', severity=source_condition.severity,
                expression=source_claim_expression(source_condition.expression))
            text = known[refs[0]]['statement']
        claim = EvidenceClaim(text=text, evidence_refs=tuple(refs), logical_condition=condition)
        ref = maturity_atomic_claim_ref(ticker=ticker, claim=claim)
        if ref in effects:
            raise ValueError('duplicate_atomic_claim')
        record = dict(effect=effect.value, materiality=item['materiality'], observation_ids=ids,
                      risk_triggers=sorted({obs[x]['risk_trigger'] for x in ids}) if effect == Effect.NEGATIVE else [],
                      source_refs=sorted(refs), model_claim_sha256=canonical_sha256(item))
        effects[ref] = record
        atomic.append(dict(contract='maturity-atomic-claim-identity-v1', claim_ref=ref, ticker=ticker,
            parent_source_refs=refs, claim={**claim.model_dump(mode='json'),
                'polarity': 'BULLISH' if effect == Effect.POSITIVE else 'BEARISH' if effect == Effect.NEGATIVE else 'NEUTRAL',
                'reason_role': 'FUNDAMENTAL'}))
    if not atomic:
        raise ValueError('core_empty')
    return {'atomic_claims': atomic, 'effects': effects, 'observations': obs,
            'binding_sha256': canonical_sha256({'atomic': atomic, 'effects': effects})}


def axis_capability(core, chain, catalog, metadata):
    valid = validate_source_use_current_input(chain['projection'], chain['binding'], chain['expectation'],
        ticker=catalog['ticker'], source_generation_id=chain['source_generation_id'],
        execution_generation_id=chain['execution_generation_id'], catalog=catalog, source_metadata=metadata)
    if valid['status'] != 'PASS' or catalog['atomic_claims'] != core['atomic_claims']:
        raise ValueError('axis_current_core_binding_invalid')
    if core['binding_sha256'] != canonical_sha256({'atomic': core['atomic_claims'], 'effects': core['effects']}):
        raise ValueError('core_effect_binding_drift')
    out = {'positive': [], 'negative': [], 'confidence': [], 'condition': [], 'quality': [],
           'holder_support': [], 'holder_risk': [], 'holder_reduce': [], 'risk_triggers': {}}
    for ref, effect in core['effects'].items():
        use = SourceUse.OVERALL_DIRECTION if effect['effect'] in (Effect.POSITIVE, Effect.NEGATIVE) else SourceUse.CONTEXT
        if validate_selected_refs(chain['projection'], refs=[ref], use=use, require_any=True, binding=chain['binding'])['status'] != 'PASS':
            if use == SourceUse.OVERALL_DIRECTION:
                raise ValueError('directional_claim_without_source_entitlement')
            continue
        bucket = {Effect.POSITIVE:'positive', Effect.NEGATIVE:'negative', Effect.CONFIDENCE:'confidence',
                  Effect.CONDITION:'condition', Effect.QUALITY:'quality'}[effect['effect']]
        out[bucket].append(ref)
        if effect['effect'] == Effect.POSITIVE:
            out['holder_support'].append(ref)
        if effect['effect'] == Effect.NEGATIVE:
            if effect['materiality'] in ('ACTIVE_MATERIAL_RISK', 'PERSISTENT_OR_IMPAIRED'):
                out['holder_risk'].append(ref)
                out['risk_triggers'][ref] = effect['risk_triggers']
            else:
                out['holder_support'].append(ref)
            if effect['materiality'] == 'PERSISTENT_OR_IMPAIRED':
                out['holder_reduce'].append(ref)
    out.update(contract=CONTRACT, ticker=catalog['ticker'], raw_authority_widened=False,
               holder_projection='ELIGIBLE_OBSERVED_BUSINESS_CLAIM_EFFECT_AND_MATERIALITY',
               core_binding_sha256=core['binding_sha256'], source_binding_sha256=chain['binding']['binding_sha256'])
    return out


def validate_decision(row, cap, ranges):
    errors = []
    score = number(row['directional_buy_score'])
    if score is None or not 0 <= score <= 10:
        errors.append('directional_score_invalid')
    fields = {'supporting_refs':'positive', 'contradicting_refs':'negative', 'confidence_caution_refs':'confidence',
              'data_quality_refs':'quality',
              'reevaluation_refs':'condition'}
    for name, bucket in fields.items():
        refs = row[name]
        if len(set(refs)) != len(refs) or not set(refs) <= set(cap[bucket]):
            errors.append('axis_ref_effect_mismatch:' + name)
    overall, reason = row['overall_direction'], row['overall_reason_class']
    pos, neg, caution = row['supporting_refs'], row['contradicting_refs'], row['confidence_caution_refs'] + row['data_quality_refs']
    if overall == 'BUY' and (not pos or reason != 'OBSERVED_POSITIVE_DOMINANT'):
        errors.append('buy_positive_required')
    if overall == 'SELL' and (not neg or reason != 'OBSERVED_NEGATIVE_DOMINANT'):
        errors.append('sell_observed_negative_required')
    if overall == 'HOLD':
        if reason == 'BALANCED_DIRECTIONAL_EVIDENCE' and not (pos and neg):
            errors.append('balanced_hold_two_observed_sides_required')
        elif reason == 'POSITIVE_BUT_CONFIDENCE_CAPPED' and (not pos or neg or not caution or row['confidence'] == 'HIGH'):
            errors.append('confidence_capped_hold_shape')
        elif reason not in ('BALANCED_DIRECTIONAL_EVIDENCE', 'POSITIVE_BUT_CONFIDENCE_CAPPED', 'INSUFFICIENT_DIRECTIONAL_EVIDENCE'):
            errors.append('hold_reason_invalid')
    if not pos and not neg:
        if overall != 'HOLD' or reason != 'INSUFFICIENT_DIRECTIONAL_EVIDENCE':
            errors.append('no_directional_evidence_requires_insufficient_hold')
    holder = row['holder']
    href = row['holder_reason_evidence_refs']
    allowed = cap['holder_risk'] if holder == 'REVIEW' else cap['holder_reduce'] if holder == 'REDUCE' else cap['holder_support']
    if not href or len(set(href)) != len(href) or not set(href) <= set(allowed):
        errors.append('holder_evidence_required_or_ineligible')
    if holder == 'HOLDABLE' and (cap['holder_risk'] or row['holder_reason_class'] != 'THESIS_INTACT_NO_ACTIVE_MATERIAL_TRIGGER'):
        errors.append('holdable_active_material_risk_or_reason')
    if holder in ('REVIEW', 'REDUCE'):
        triggers = {t for ref in href for t in cap['risk_triggers'].get(ref, [])}
        if row['holder_reason_class'] not in triggers:
            errors.append('holder_trigger_reason_mismatch')
    buyer = row['new_buyer']
    refs = row['new_buyer_risk_refs']
    if len(set(refs)) != len(refs) or not set(refs) <= set(cap['holder_risk']):
        errors.append('new_buyer_risk_not_observed_material')
    if buyer == 'ATTRACTIVE' and (not ranges['fundamental_valid'] or not ranges['compensating_discount']):
        errors.append('attractive_without_fundamental_discount')
    if buyer == 'AVOID' and (not refs or ranges['compensating_discount']):
        errors.append('avoid_requires_adverse_without_compensation')
    if buyer != 'AVOID' and row['new_buyer_reason_class'] == 'ACTIVE_ADVERSE_UNCOMPENSATED':
        errors.append('new_buyer_reason_stance_mismatch')
    if buyer == 'AVOID' and row['new_buyer_reason_class'] != 'ACTIVE_ADVERSE_UNCOMPENSATED':
        errors.append('avoid_reason_required')
    if buyer == 'WAIT' and row['new_buyer_reason_class'] not in ('VALUATION_UNRESOLVED', 'CONFIDENCE_UNCERTAINTY', 'NO_CLEAN_ENTRY', 'PRICE_NOT_FAVORABLE'):
        errors.append('wait_reason_required')
    if buyer == 'ATTRACTIVE' and row['new_buyer_reason_class'] != 'VALID_FUNDAMENTAL_DISCOUNT':
        errors.append('attractive_reason_required')
    return {'status':'FAIL' if errors else 'PASS', 'errors':errors}


def policy_audit(row, cap, ranges):
    return dict(overall={k: deepcopy(row[k]) for k in ('overall_direction','overall_reason_class','confidence','supporting_refs','contradicting_refs','confidence_caution_refs','data_quality_refs')},
        directional_balance={'buy':row['directional_buy_score'], 'sell':float(Decimal('10')-number(row['directional_buy_score']))},
        holder={'stance':row['holder'], 'reason_class':row['holder_reason_class'], 'refs':row['holder_reason_evidence_refs'],
                'active_triggers':cap['risk_triggers'], 'review_eligible':bool(cap['holder_risk']), 'reduce_eligible':bool(cap['holder_reduce'])},
        new_buyer={'stance':row['new_buyer'], 'active_adverse_refs':cap['holder_risk'], 'ranges':deepcopy(ranges)})
