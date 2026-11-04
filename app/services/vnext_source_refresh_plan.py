"""Read-only, family-aware research planning. This module issues no use grants."""
from copy import deepcopy
from datetime import datetime
from app.services.bounded_financial_acquisition import make_plan
from app.services.vnext_research_store import digest

CONTRACT = 'source-family-refresh-plan-v1'
VALUATION = {'kiwoom_ratios', 'kis_estimates', 'finnhub_ratios'}


def freshness(family, *, original, target, identity_verified, raw_verified,
              latest_inventory_verified=False, cadence_verified=False):
    """No same-day equivalence for forecasts; no freshness from a digest alone."""
    if not original:
        return 'MISSING_FETCH_REQUIRED'
    if not identity_verified or not raw_verified:
        return 'SOURCE_DENIED'
    if family in VALUATION:
        return ('REUSED_SAME_TARGET_VERIFIED' if cadence_verified and
                original.get('verified_through') == target else 'STALE_REFRESH_REQUIRED')
    if family == 'financial':
        return ('REUSED_SAME_TARGET_VERIFIED' if latest_inventory_verified and
                original.get('inventory_cutoff') == target else 'STALE_REFRESH_REQUIRED')
    if family in ('completed_close', 'adjusted_daily', 'market_daily'):
        if original.get('session') == target and original.get('quality_valid') is True:
            return 'REUSED_SAME_TARGET_VERIFIED'
        return 'STALE_REFRESH_REQUIRED'
    if family in ('adjusted_monthly', 'unadjusted_weekly_valuation'):
        return 'RESEARCH_HISTORICAL_ONLY'
    return 'STALE_REFRESH_REQUIRED'


def plan(securities, *, cutoff, calendars, baseline, market_types):
    if cutoff.utcoffset() is None or not securities:
        raise ValueError('aware_cutoff_and_roster_required')
    required = ('ticker', 'canonical_security_id', 'canonical_company_id', 'country',
                'exchange', 'issuer_type', 'security_type', 'identity_provider')
    if any(any(not s.get(k) for k in required) for s in securities):
        raise ValueError('canonical_security_required')
    if len({s['canonical_security_id'] for s in securities}) != len(securities) or len({s['ticker'] for s in securities}) != len(securities):
        raise ValueError('duplicate_security')
    if any(s['country'] not in ('KR', 'US') for s in securities):
        raise ValueError('market_not_supported')
    kr = [s for s in securities if s['country'] == 'KR']
    us = [s for s in securities if s['country'] == 'US']
    if set(market_types) != {s['ticker'] for s in kr} or not set(market_types.values()) <= {'0', '10'}:
        raise ValueError('original_listing_route_required')
    rows, financial = [], []
    for s in sorted(securities, key=lambda r: r['ticker']):
        market, code = s['country'].lower(), s['ticker']
        target = calendars[market]['session']
        families = ('completed_close', 'adjusted_daily', 'adjusted_weekly',
                    'adjusted_monthly', 'unadjusted_weekly_valuation', 'financial',
                    *(('kiwoom_ratios', 'kis_estimates') if market == 'kr' else ('finnhub_ratios',)))
        # The original source owner retains all period and candidate bounds.
        fp = make_plan(s, market=market, cutoff=cutoff, run_id='NG86_V2',
                       all_subjects_fresh=True, exact_financial_owner=market == 'us')
        financial.append(fp)
        for family in families:
            previous = baseline.get(code, {}).get(family)
            target_value = cutoff.isoformat() if family in VALUATION or family == 'financial' else target
            state = freshness(family, original=previous, target=target_value,
                identity_verified=bool(previous and previous.get('identity_verified')),
                raw_verified=bool(previous and previous.get('raw_verified')))
            rows.append(dict(ticker=code, canonical_security_id=s['canonical_security_id'],
                market=market, family=family, target=target_value, state=state,
                previous=deepcopy(previous), strict_native_grant=False))
    # A bounded research weekly page is not the unchanged 700-week Native role.
    # Monthly/valuation-weekly history stays dated; no fictitious complete history.
    kw_parts = dict(authentication=int(bool(securities)), listing=5*len(set(market_types.values())),
        ratios=len(kr), us_completed_close=len(us), kr_daily=3*len(kr), us_daily=12*len(us),
        weekly_reference=len(securities), kr_market=2*int(bool(kr)), us_market=5*int(bool(us)))
    budgets = dict(
        Kiwoom=dict(maximum=sum(kw_parts.values()), endpoints=kw_parts, minimum_if_all_gates_pass=
                    int(bool(securities))+len(set(market_types.values()))+len(kr)+len(us)+2*len(securities)+2*int(bool(kr))+5*int(bool(us))),
        KIS=dict(maximum=int(bool(kr))+9*len(kr), minimum_if_all_gates_pass=int(bool(kr))+len(kr),
                 endpoints=dict(auth=int(bool(kr)), estimate=len(kr), conditional_identity=len(kr),
                                conditional_close=len(kr), conditional_actions=6*len(kr))),
        Finnhub=dict(maximum=2*len(us), minimum_if_all_gates_pass=2*len(us),
                     endpoints=dict(profile2=len(us), stock_metric=len(us))),
        SEC=dict(maximum=sum(p['maximum_logical_requests'] for p in financial if p['market']=='us'),
                 minimum_if_all_gates_pass=len(us), endpoints=dict(inventory=len(us), rest='Conditional original make_plan document/statement bounds')),
        OpenDART=dict(maximum=sum(p['maximum_logical_requests'] for p in financial if p['market']=='kr'),
                 minimum_if_all_gates_pass=len(kr), endpoints=dict(inventory_min=len(kr), rest='Conditional original discovery/statement bounds')),
        FRED=dict(maximum=5, minimum_if_all_gates_pass=5, endpoints={'series/observations':5}),
        ECOS=dict(maximum=1, minimum_if_all_gates_pass=1, endpoints={'KeyStatisticList':1}),
        Alpha_Vantage=dict(maximum=0, minimum_if_all_gates_pass=0, endpoints={}))
    if budgets['Kiwoom']['maximum'] > 250:
        raise ValueError('existing_public_transport_cap_requires_narrower_plan')
    for b in budgets.values():
        b.update(retries=0, minimum_on_safety_stop=0, approved=False, actual=0)
    n = len(securities)
    raw_max = sum(b['maximum'] for b in budgets.values()) - int(bool(kr)) - int(bool(securities))
    captures_max = raw_max + 2*n + n + n + len(kr) + 2*len(kr)
    observations_max = 6*n + n + 2*n + 7*3*n + 4*len(kr) + 3*len(us) + 12
    value = dict(contract=CONTRACT, cutoff=cutoff.isoformat(), calendars=calendars,
        securities=deepcopy(securities), roster_sha256=digest(securities), rows=rows,
        financial_plans=financial, provider_budgets=budgets,
        append=dict(approved=False,tables=['research_run','source_capture','research_observation','research_meta'],
            runs_max=8,captures_max=captures_max,observations_max=observations_max,journals_max=7*n+2,
            CAS_bytes_max=1024**3, DB_incremental_bytes_max=128*1024**2,
            updates=0,deletes=0,migrations=0,private_thesis_content=0),
        models=dict(approved=False,model='gpt-6-astra',effort='xhigh',primary_by_market=True,
            contexts_max=2*n,physical_attempts_max=2*n,retries=0,timeout_seconds=600,
            canary='One eligible KR and US before remaining eligible subjects',backup=False,paid_API=False),
        technical_scope=dict(daily_rows=1000,weekly_page_max=1,weekly_native_required_rows=700,
            monthly='Historical completed-month references only; incomplete history remains incomplete',
            unadjusted_weekly='Historical only; no current per-share valuation use',
            no_native_contract_reduction=True),
        approval_state='PENDING_CONSOLIDATED_USER_APPROVAL',
        revalidate_before_dispatch='Current target sessions, registry versions, final helper/source pins, lane and disk; never silently retarget',
        fetch_policy='Inventory first; identical immutable document URL/digest may be reused with ORIGINAL receipt and a separate reuse event; never fresh-relabel',
        send=False,scheduler=False,strict_ready=False)
    value['plan_sha256'] = digest(value)
    return value
