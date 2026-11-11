"""Bounded selected KIS plan over the unchanged fiscal/price/action owners."""
from scripts import kis_current_fy1_owner as price
from scripts import kis_exact_action_guard as action
from scripts.kis_eps_wire_calibration import sealed

CONTRACT='selected-original-kis-source-v1'


def build_plan(*,generation,as_of,securities,static_hashes):
    subjects=tuple(sorted(securities))
    if not subjects or len(subjects)>8:
        raise ValueError('selected_kis_bounded_subjects_required')
    for t,s in securities.items():
        if (s['ticker']!=t or s['exchange'] not in ('KRX','KOSPI','KOSDAQ') or s['currency']!='KRW'
                or not s['canonical_security_id'] or not s.get('corp_code')):
            raise ValueError('selected_kis_security_identity_gap')
    initial=len(action.VARIANTS)*len(subjects)
    continuation=min(18,60-initial)
    return sealed(dict(contract=CONTRACT,generation_id=generation,scope='SELECTED_ORIGINAL_RESEARCH_V1',
        securities=securities,subjects=list(subjects),as_of=as_of,calendar=price.calendar_receipt(as_of),
        static_hashes=static_hashes,auth_max=1,estimate_max=len(subjects),identity_max=len(subjects),price_max=len(subjects),
        action_initial_max=initial,action_data_max=initial+continuation,action_continuation_max=continuation,
        data_max=3*len(subjects)+initial+continuation,maximum_physical_HTTP=1+3*len(subjects)+initial+continuation,
        minimum_spacing_seconds=1.101,timeout_seconds=45,retries=0,estimate_identity_continuation='DENY',
        action_policy=action.POLICY,action_variants=list(action.VARIANTS),
        conditional_price_action='FRESH_QUALIFIED_POSITIVE_FY1_EPS_ONLY',overall_direction_use=False,delivery_disabled=True,us_calls=0))


def validate_plan(plan):
    rebuilt=build_plan(generation=plan['generation_id'],as_of=plan['as_of'],securities=plan['securities'],static_hashes=plan['static_hashes'])
    if plan!=rebuilt:
        raise ValueError('selected_kis_plan_reproduction_gap')
    return tuple(plan['subjects'])
