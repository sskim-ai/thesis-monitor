"""Export-only market input; unavailable/lagging source rows never become current facts."""
from copy import deepcopy

from scripts.m12cr_shadow_contract import _strict_object as obj, _enum as enum, _string as string
from scripts.m12ds_r2_schemas import refs
from scripts.m12cq_two_pass_contract import canonical_sha256

REGIMES = ['BROAD_RISK_ON','NARROW_LEADERSHIP','MIXED','BROAD_RISK_OFF','DATA_INSUFFICIENT']


def market_context(packet):
    market = packet['market'].upper()
    source = packet['market_context']
    adapter = source.get('adapter_context') or {}
    session = adapter.get('session_context') or {}
    cutoff = session.get('latest_completed_regular_session_date')
    facts, suppressed = {}, []
    for fact in source.get('fact_catalog') or []:
        fields = fact.get('fields') or {}
        ref = fact['fact_id']
        if fields.get('today_signal_eligible') is True and fields.get('structured_state') == 'CURRENT_DIRECTIONAL':
            facts[ref] = deepcopy(fact)
        else:
            suppressed.append(ref)
    # Adapter data is gated against the same per-market completed-session owner.
    for name in ('indices','sectors','market_flows','size_context'):
        for row in adapter.get(name) or []:
            date, ref = row.get('as_of_date'), row.get('source_ref')
            if not ref:
                continue
            if not cutoff or date != cutoff or row.get('state') in ('SOURCE_UNAVAILABLE','UNAVAILABLE'):
                suppressed.append(ref)
                continue
            facts.setdefault(ref, {'kind':name, **deepcopy(row)})
    breadth = adapter.get('breadth') or {}
    if (breadth.get('availability') == 'AVAILABLE' and cutoff and adapter.get('session_date') == cutoff):
        for ref in breadth.get('source_refs') or []:
            facts[ref] = {'kind':'breadth', **deepcopy(breadth)}
    return {'market':market, 'assessment_date':packet['assessment_date'], 'source_market_sha256':canonical_sha256(source),
            'facts':facts, 'suppressed_refs':sorted(set(suppressed)), 'session_context':deepcopy(session),
            'export_only':True, 'stock_feedback':False}


def eligible_regimes(context):
    kinds = {f.get('kind', f.get('fact_type')) for f in context['facts'].values()}
    regimes = ['DATA_INSUFFICIENT']
    if 'indices' in kinds:
        regimes.append('MIXED')
        if 'sectors' in kinds:
            regimes.append('NARROW_LEADERSHIP')
        if 'breadth' in kinds:
            regimes.extend(['BROAD_RISK_ON', 'BROAD_RISK_OFF'])
    return regimes


def market_schema(context):
    known = list(context['facts'])
    return obj({'market':enum([context['market']]), 'regime':enum(eligible_regimes(context)), 'confidence':enum(['LOW','MEDIUM','HIGH']),
        'breadth_state':string(maximum=400), 'leadership':string(maximum=400),
        'flows_or_participation':string(maximum=400), 'rates_or_macro_context':string(maximum=400),
        'supporting_refs':refs(known,1 if known else 0,12), 'contradicting_refs':refs(known,0,12)})


def validate_market(row, context):
    errors = []
    support, contra = set(row['supporting_refs']), set(row['contradicting_refs'])
    if row['market'] != context['market'] or not support | contra <= set(context['facts']):
        errors.append('market_identity_or_ref_mismatch')
    if support & contra:
        errors.append('market_ref_overlap')
    if row['regime'] not in eligible_regimes(context):
        errors.append('market_regime_not_evidence_eligible')
    kinds = {f.get('kind', f.get('fact_type')) for f in context['facts'].values()}
    if row['regime'] in ('BROAD_RISK_ON','BROAD_RISK_OFF') and not {'indices','breadth'} <= kinds:
        errors.append('broad_market_verdict_without_breadth_and_indices')
    if not context['facts'] and row['regime'] != 'DATA_INSUFFICIENT':
        errors.append('market_data_absent')
    return {'status':'FAIL' if errors else 'PASS', 'errors':errors, 'stock_feedback':False}


PROMPT = '''Export-only market judgment, independent of stock decisions. Use only eligible frozen facts, exact refs.
No tools or external data. Do not infer current direction from suppressed/lagging observations.
Do not use absent breadth, unavailable flows or outdated returns. Unknown is not neutral or zero.
Broad risk-on/off needs both current index and breadth evidence. DATA_INSUFFICIENT is valid.
If only sparse macro facts exist, do not infer leadership or broad regime. Explain missing dimensions in Korean.
No numerical extrapolation. No stock labels. Return only the requested structured JSON.'''
