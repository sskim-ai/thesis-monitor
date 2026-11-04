"""Pure release-aware research planning. No scheduler/provider/model capability."""
from copy import deepcopy
from datetime import datetime,timedelta
import re
from zoneinfo import ZoneInfo
from app.services.market_session import _exchange_calendar,is_exchange_session_date
from app.services.unified_runtime_v2 import scheduled_slots
from app.services.vnext_research_store import digest

CONTRACT='research-daily-delta-selection-v1'
DEPENDENCIES={'business':('financial','business'), 'valuation':('valuation','forecast'),
              'timing':('ohlcv','close','market')}
STATES={'VALID','EMPTY','DENIED','NOT_RELEASED','NOT_CHECKED','MISSING',
        'EMPTY_CURRENT','REVOKED','OWNER_ACCEPTED','VALID_LAST_QUALIFIED_RESEARCH',
        'INELIGIBLE_MISMATCH','VALID_CURRENT','SHORT_HISTORY','QUALITY_DENIED'}
AVAILABLE={'VALID','OWNER_ACCEPTED','VALID_CURRENT','VALID_LAST_QUALIFIED_RESEARCH'}
HEX=re.compile(r'[0-9a-f]{64}\Z')

def completed_session(market,at):
    if at.tzinfo is None or market not in ('kr','us'):raise ValueError('explicit_market_time_required')
    local=at.astimezone(ZoneInfo('Asia/Seoul'))
    day=local.date() if market=='kr' else at.astimezone(ZoneInfo('America/New_York')).date()
    name='XKRX' if market=='kr' else 'XNYS'
    # No weekday substitute when the original exchange calendar is unavailable.
    if not is_exchange_session_date(name,day):return None
    cal=_exchange_calendar(name)
    try:close=cal.session_close(cal.date_to_session(day)).to_pydatetime()
    except (ValueError,IndexError,TypeError):return None
    if at<close:return None
    return day.isoformat()

def slots(market,day):return [s.isoformat() for s in scheduled_slots(market,day)]

def _validated(snapshot):
    keys=set();copy=deepcopy(snapshot)
    for s in copy:
        key=s['security_id']
        if not key or key in keys or s['market'] not in ('kr','us'):raise ValueError('delta_identity_scope')
        keys.add(key)
        for role,item in s['sources'].items():
            if role not in {r for roles in DEPENDENCIES.values() for r in roles}:raise ValueError('delta_unknown_role')
            if (item['security_id']!=key or item['status'] not in STATES or
                not HEX.fullmatch(item['receipt_sha256']) or not HEX.fullmatch(item['raw_sha256']) or
                not item['source_generation'] or not item['as_of']):raise ValueError('delta_source_binding')
            if item['status'] not in AVAILABLE and item.get('numeric_value') is not None:raise ValueError('unavailable_is_not_numeric')
    return copy

def stage_digests(subject):
    return {stage:digest([subject['security_id'],subject['market'],subject.get('registration_version'),
        subject.get('model_contract','vnext-economic-timing-research-v4'),stage,
        {r:subject['sources'].get(r) for r in roles}])
        for stage,roles in DEPENDENCIES.items()}

def plan(previous,current,*,at,requests=(),provider_limits=None,account_state=None):
    """Inputs are reviewed projections. The plan itself issues no source-use grant."""
    old={s['security_id']:s for s in _validated(previous)};new=_validated(current)
    if set(old)!={s['security_id'] for s in new}:raise ValueError('registration_set_changed')
    rows=[];refresh=set();acquisition=set()
    for s in new:
        prior=old[s['security_id']]
        if s['market']!=prior['market']:raise ValueError('market_identity_changed')
        session=completed_session(s['market'],at)
        oldhash,newhash=stage_digests(prior),stage_digests(s)
        changed=[k for k in DEPENDENCIES if oldhash[k]!=newhash[k]]
        invalid=[r for r,i in s['sources'].items() if i['status'] not in AVAILABLE]
        invalid += [r for r in prior['sources'] if r not in s['sources']]
        needed=[]
        # No old/fabricated bar is silently presented as today's completed close.
        for role in ('ohlcv','close'):
            item=s['sources'].get(role)
            if item and item['status'] in AVAILABLE and item['as_of']!=session:
                invalid.append(role)
            if session is not None and (item is None or item['as_of']!=session):
                needed.append(role)
        status='NO_COMPLETED_SESSION' if session is None else 'CHANGED' if changed else 'UNCHANGED'
        available={r for r,i in s['sources'].items() if i['status'] in AVAILABLE and r not in invalid}
        # One admissible economic/valuation field permits a bounded analysis;
        # timing structure needs both prices and chart history. Market is optional.
        enough={'business':bool(available&{'financial','business'}),
                'valuation':bool(available&{'valuation','forecast'}),
                'timing':{'ohlcv','close'}<=available}
        eligible=[] if session is None else [st for st in changed if enough[st]]
        for st in eligible:refresh.add((s['security_id'],st))
        if needed:acquisition.add((s['security_id'],'timing'))
        rows.append(dict(security_id=s['security_id'],market=s['market'],session=session,status=status,
            prior_stage_digests=oldhash,stage_digests=newhash,model_decision_plan=eligible,
            unavailable_roles=sorted(set(invalid)),acquisition_needed=needed,reuse_business=oldhash['business']==newhash['business'],
            source_as_of={r:i['as_of'] for r,i in s['sources'].items()},send=False))
        rows[-1]['stage_inference_admission']={st:dict(proposed=st in eligible,live_admitted=False,
            reason='ORIGINAL_OWNER_REQUIRED' if enough[st] else 'STAGE_WAIT_SOURCE') for st in DEPENDENCIES}
        rows[-1]['source_change_detection']=changed
        rows[-1]['capture_or_replay_requirement']=needed
    budget={};chosen=[];seen=set()
    for q in requests:
        key=(q['security_id'],q['stage'])
        if key not in refresh|acquisition:continue
        if q['request_id'] in seen:raise ValueError('duplicate_delta_request')
        seen.add(q['request_id'])
        if type(q['physical_max']) is not int or q['physical_max']<1 or q['retries']!=0:raise ValueError('finite_request_budget_required')
        if q['stage'] not in DEPENDENCIES or q['role'] not in DEPENDENCIES[q['stage']]:raise ValueError('request_role_stage_mismatch')
        # Financial/forecast/ratio requests need a concrete published release.
        if q['stage'] in ('business','valuation') and not HEX.fullmatch(q.get('release_receipt_sha256','')):raise ValueError('release_receipt_required')
        provider=q['provider'];budget[provider]=budget.get(provider,0)+q['physical_max'];chosen.append(deepcopy(q))
    limits=provider_limits or {}
    for provider,count in budget.items():
        limit=min(limits.get(provider,0),25) if provider=='AlphaVantage' else limits.get(provider,0)
        if count>limit:raise ValueError('daily_provider_budget_exceeded')
        if provider in ('Kiwoom','KIS'):
            a=(account_state or {}).get(provider,{})
            if (a.get('shared_lane') is not True or a.get('pacer_verified') is not True or
                a.get('latch_clear') is not True or a.get('concurrent_callers_excluded') is not True):raise ValueError('shared_account_boundary_unverified')
    return dict(contract=CONTRACT,rows=rows,planned_requests=chosen,physical_budget=budget,
        stage_proposals=sorted([list(x) for x in refresh]),plan_only=True,owner_grant=False,
        scheduler_active=False,actual_HTTP=0,actual_model_calls=0,send=False)
