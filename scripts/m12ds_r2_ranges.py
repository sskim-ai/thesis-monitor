"""R2 shadow valuation conflict audit and disjoint fundamental/tactical fields."""
from copy import deepcopy

from scripts import m12cp_valuation_policy_contract as v
from scripts.m12cr_r1_typed_quality_contract import gate_policy_option_for_security_basis
from scripts.m12ds_r2_judgment_policy import number
from scripts.m12da_source_use_contract import SourceUse, validate_selected_refs


def eligible_range_inputs(subject, entry_catalog, chain):
    result, entries = deepcopy(subject), deepcopy(entry_catalog)
    exclusions = []
    current_currency = (subject.get('current_price') or {}).get('currency')
    for key, use in (('fundamental_candidates',SourceUse.VALUATION), ('tactical_candidates',SourceUse.ENTRY)):
        accepted = []
        for candidate in subject.get(key) or entry_catalog.get(key) or []:
            validation = validate_selected_refs(chain['projection'], refs=candidate.get('evidence_refs') or [],
                use=use, require_any=True, binding=chain['binding'])
            valid = validation['status']=='PASS' and candidate.get('ticker',subject['ticker'])==subject['ticker']
            valid &= bool(current_currency and current_currency==candidate.get('currency'))
            if valid:
                accepted.append(deepcopy(candidate))
            else:
                exclusions.append({'candidate':deepcopy(candidate), 'reason':'SOURCE_USE_OR_CURRENCY_INELIGIBLE',
                                   'source_use_validation':validation})
        result[key], entries[key] = accepted, deepcopy(accepted)
    return result, entries, exclusions


def valuation_policy(subject, classification, security_basis):
    ticker, archetype, tier = subject['ticker'], classification['archetype'], classification['valuation_regime_tier']
    option = v.select_policy_option(subject=subject, archetype=archetype, valuation_regime_tier=tier)
    current = subject.get('current_price') or {}
    price = number(current.get('value'))
    methods = []
    for candidate in sorted(subject.get('fundamental_candidates') or [], key=lambda r: r['candidate_id']):
        if candidate['ticker'] != ticker:
            raise ValueError('valuation_cross_subject')
        low, high = number(candidate.get('low')), number(candidate.get('high'))
        if low is None or high is None or low <= 0 or high < low or candidate.get('disqualifying_reasons'):
            raise ValueError('unsafe_canonical_valuation_candidate')
        projected = v._project_candidate(candidate=candidate, archetype=v.Archetype(archetype),
            tier=v.ValuationRegimeTier(tier), selection_basis='R2_ALL_ELIGIBLE_METHOD_AUDIT')
        projected, gate = gate_policy_option_for_security_basis(projected, security_basis)
        eligible = projected['status'] == 'RESOLVED' and candidate['quantile_band'] == v.TIER_TO_BAND[v.ValuationRegimeTier(tier)]
        relation = 'UNRESOLVED'
        if eligible and price is not None and price > 0 and current.get('currency') == candidate['currency']:
            relation = 'BELOW' if price < low else 'ABOVE' if price > high else 'INSIDE'
        methods.append({'candidate':deepcopy(candidate), 'eligible_for_selected_tier':eligible,
                        'relation_to_price':relation, 'security_gate':gate})
    usable = [r['candidate'] for r in methods if r['eligible_for_selected_tier'] and r['relation_to_price'] != 'UNRESOLVED']
    status = 'RESOLVED' if option['status'] == 'RESOLVED' else 'FUNDAMENTAL_RANGE_UNRESOLVED'
    confidence = 'LOW'
    if archetype == v.Archetype.STRUCTURAL_CYCLICAL_LEADER and tier != v.ValuationRegimeTier.UNRESOLVED:
        relations = {r['relation_to_price'] for r in methods if r['eligible_for_selected_tier'] and r['relation_to_price'] != 'UNRESOLVED'}
        reasons = []
        if len(relations) > 1:
            reasons = ['FUNDAMENTAL_RANGE_UNRESOLVED_METHOD_CONFLICT']
        elif len(usable) == 1:
            option = v._project_candidate(candidate=usable[0], archetype=v.Archetype(archetype), tier=v.ValuationRegimeTier(tier),
                                          selection_basis='SINGLE_METHOD_LOW_CONFIDENCE')
            status = 'SINGLE_METHOD_LOW_CONFIDENCE'
        elif len(usable) > 1:
            low, high = max(number(r['low']) for r in usable), min(number(r['high']) for r in usable)
            if len({r['currency'] for r in usable}) != 1 or low > high:
                reasons = ['FUNDAMENTAL_RANGE_UNRESOLVED_METHOD_CONFLICT']
            else:
                option = v._project_candidate(candidate=usable[0], archetype=v.Archetype(archetype), tier=v.ValuationRegimeTier(tier),
                                              selection_basis='SAME_DIRECTION_METHOD_INTERSECTION')
                option.update(low=float(low), high=float(high), method_family='METHOD_INTERSECTION',
                              source_candidate_ids=sorted(r['candidate_id'] for r in usable),
                              evidence_refs=sorted({ref for r in usable for ref in r['evidence_refs']}))
                option['option_id'] = 'policy-option:' + v.canonical_sha256(option)[:24]
                status, confidence = 'RESOLVED', 'MEDIUM'
        else:
            reasons = ['NO_ELIGIBLE_COMPARABLE_METHOD']
        if reasons:
            option = v._unresolved_option(ticker=ticker, archetype=v.Archetype(archetype), tier=v.ValuationRegimeTier(tier), reasons=reasons)
            status = reasons[0]
    elif option['status'] == 'RESOLVED':
        confidence = 'LOW' if len(usable) <= 1 else 'MEDIUM'
        status = 'SINGLE_METHOD_LOW_CONFIDENCE' if len(usable) <= 1 else 'RESOLVED'
    option, gate = gate_policy_option_for_security_basis(option, security_basis)
    if option['status'] != 'RESOLVED' and status in ('RESOLVED', 'SINGLE_METHOD_LOW_CONFIDENCE'):
        status = 'FUNDAMENTAL_RANGE_UNRESOLVED'
    valid = option['status'] == 'RESOLVED'
    # A discount is source-valued, not a technical band or a fitted percent cutoff.
    discount = bool(valid and price is not None and current.get('currency') == option['currency'] and price < number(option['low']))
    return {'option':option, 'method_audit':methods, 'security_gate':gate,
            'fundamental_entry_status':status, 'fundamental_entry_confidence':confidence if valid else 'UNRESOLVED',
            'fundamental_valid':valid, 'compensating_discount':discount,
            'method_conflict':status == 'FUNDAMENTAL_RANGE_UNRESOLVED_METHOD_CONFLICT'}


def materialize_ranges(valuation, entry_catalog, tactical_choice):
    option = valuation['option']
    candidates = {r['candidate_id']: r for r in entry_catalog.get('tactical_candidates') or []}
    tactical = candidates.get(tactical_choice)
    if candidates and tactical is None:
        raise ValueError('eligible_tactical_zone_must_be_surfaced')
    if not candidates and tactical_choice != 'UNRESOLVED':
        raise ValueError('unknown_tactical_choice')
    if tactical and (number(tactical['low']) is None or number(tactical['high']) is None
                     or number(tactical['low']) > number(tactical['high'])):
        raise ValueError('invalid_tactical_zone')
    valid = valuation['fundamental_valid']
    return {'fundamental_entry_status':valuation['fundamental_entry_status'],
        'fundamental_entry_low':option['low'] if valid else None,
        'fundamental_entry_high':option['high'] if valid else None,
        'fundamental_entry_method':option['method_family'] if valid else None,
        'fundamental_entry_confidence':valuation['fundamental_entry_confidence'],
        'fundamental_entry_basis':option['evidence_refs'] if valid else [],
        'fundamental_currency':option.get('currency') if valid else None,
        'tactical_watch_status':'RESOLVED' if tactical else 'UNRESOLVED',
        'tactical_watch_low':tactical['low'] if tactical else None,
        'tactical_watch_high':tactical['high'] if tactical else None,
        'tactical_watch_basis':tactical['evidence_refs'] if tactical else [],
        'tactical_currency':tactical.get('currency') if tactical else None,
        'render_warning':'TACTICAL_WATCH_ZONE != FAIR_VALUE'}
