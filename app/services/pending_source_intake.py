"""Default-off pending-registration intake, NOT an ACTIVE/production Owner.

Only the trusted operator adapter may record scope. This control-plane API does
not discover consent or attest remote account use. No live Worker adapter exists
until the original Parent explicitly supports this separate capability type.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from weakref import WeakKeyDictionary

from app.services import prospective_class_c_owner as approval_owner
from app.services.minimal_class_c_export import captured_private_snapshot
from app.services.unified_snapshot_contract import digest

CONTRACT = 'pending-registration-source-intake-v1'
ROLES = frozenset(('adjusted_daily', 'adjusted_weekly', 'adjusted_monthly',
                   'unadjusted_weekly_valuation', 'completed_close'))


class IntakeScope:
    __slots__ = ('__weakref__',)


class PendingSourceIntake:
    __slots__ = ('__weakref__',)


_SCOPES = WeakKeyDictionary()
_INTAKES = WeakKeyDictionary()
_RUNS = WeakKeyDictionary()
_ISSUED_MARKETS = WeakKeyDictionary()


def _now():
    return datetime.now(timezone.utc)


def _code():
    return digest({str(p): digest(p.read_bytes().hex()) for p in
        (Path(__file__), Path(approval_owner.__file__))})


def record_backend_intake_scope(*, approval, generation_id, source_generation_id,
                                exclusive_use_confirmed, confirmation_sha256,
                                confirmed_at, enabled=False):
    """Trusted backend only: bind a real current operator/account confirmation.

    Do not feed model/request JSON into this function. Old statements are not a
    current confirmation; the actual Parent/Global Lane must still admit live IO.
    """
    decision = approval_owner._approval(approval)
    now = _now()
    if (enabled is not True or exclusive_use_confirmed is not True
            or not isinstance(confirmed_at, datetime) or confirmed_at.utcoffset() is None
            or not decision.effective_at <= confirmed_at <= now
            or now-confirmed_at > timedelta(minutes=5)
            or not isinstance(confirmation_sha256, str) or len(confirmation_sha256) != 64
            or any(c not in '0123456789abcdef' for c in confirmation_sha256)
            or not generation_id or source_generation_id != generation_id):
        raise ValueError('pending_intake_current_scope_and_exclusivity_required')
    if approval in _RUNS:
        raise ValueError('pending_intake_approval_already_bound')
    scope = IntakeScope()
    _SCOPES[scope] = dict(approval=approval, generation=generation_id,
        confirmed_at=confirmed_at, confirmation_sha256=confirmation_sha256,
        expires=min(decision.expires_at, now+timedelta(minutes=15)),pid=os.getpid(),code=_code())
    _RUNS[approval] = generation_id
    return scope


def _scope(scope):
    if type(scope) is not IntakeScope or scope not in _SCOPES:
        raise ValueError('pending_intake_live_scope_required')
    s = _SCOPES[scope]
    decision = approval_owner._approval(s['approval'])
    if s['pid'] != os.getpid() or s['code'] != _code() or _now() >= s['expires']:
        raise ValueError('pending_intake_scope_expired_or_changed')
    if 'local_session' in s:
        s['local_session'].attestation()
    return s, decision


def record_backend_campaign_scope(*,approval,session,generation_id,source_generation_id,
                                  campaign_plan_sha256,maximum_physical_attempts,
                                  expires_at,enabled=False):
    """Explicit finite multi-batch IO scope; legacy 15-minute scopes unchanged.

    This is a trusted manual composition-root API, not a JSON renewal method.
    Every original Parent keeps its 20-request cap and every Worker keeps its
    deadline. The captured registration, original session clock, code identity,
    account lane, and approval are still checked on every consumption.
    """
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    decision=approval_owner._approval(approval);now=_now()
    if (enabled is not True or type(session) is not ParticipatingSession
            or type(session._lane) is not GlobalKiwoomLane or session.kind!='CLI'
            or not generation_id or generation_id!=source_generation_id or approval in _RUNS
            or not isinstance(campaign_plan_sha256,str) or len(campaign_plan_sha256)!=64
            or any(c not in '0123456789abcdef' for c in campaign_plan_sha256)
            or type(maximum_physical_attempts) is not int or not 1<=maximum_physical_attempts<=20
            or not isinstance(expires_at,datetime) or expires_at.utcoffset() is None
            or not now<expires_at<=min(decision.expires_at,now+timedelta(minutes=45))):
        raise ValueError('campaign_scope_finite_explicit_manual_authority_required')
    session.attestation()
    fd=session._lane._open()
    try:
        if not session._lane._try_lock(fd):raise ValueError('campaign_scope_lane_busy')
        session._lane._state()
    finally:os.close(fd)
    scope=IntakeScope()
    _SCOPES[scope]=dict(approval=approval,generation=generation_id,confirmed_at=now,
        confirmation_sha256=decision.user_message_sha256,expires=expires_at,pid=os.getpid(),
        code=_code(),local_session=session,policy='FINITE_MANUAL_SOURCE_CAMPAIGN_V2',
        campaign_plan_sha256=campaign_plan_sha256,maximum_physical_attempts=maximum_physical_attempts,
        remote_account_exclusivity='USER_CONFIRMATION_NOT_LOCALLY_OBSERVABLE')
    _RUNS[approval]=generation_id
    return scope


def record_backend_local_scope(*, approval, session, generation_id,
                               source_generation_id, enabled=False):
    """Trusted backend: explicit read-only approval plus original local lane.

    This distinct policy does NOT attest remote account exclusivity. Original
    per-request lane serialization, STOP, Worker custody and consumers remain.
    The caller must bind the actual user instruction through ApprovalDecision.
    """
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    decision = approval_owner._approval(approval)
    now = _now()
    if (enabled is not True or type(session) is not ParticipatingSession
            or type(session._lane) is not GlobalKiwoomLane or session.kind != 'CLI'
            or not generation_id or generation_id != source_generation_id
            or approval in _RUNS):
        raise ValueError('pending_intake_original_local_session_required')
    session.attestation()
    fd = session._lane._open()
    try:
        if not session._lane._try_lock(fd):
            raise ValueError('pending_intake_local_lane_busy')
        session._lane._state()
    finally:
        os.close(fd)
    scope = IntakeScope()
    _SCOPES[scope] = dict(approval=approval, generation=generation_id,
        confirmed_at=now, confirmation_sha256=decision.user_message_sha256,
        expires=min(decision.expires_at, now+timedelta(minutes=15)),
        pid=os.getpid(), code=_code(), local_session=session,
        policy='PENDING_READ_ONLY_LOCAL_SERIALIZATION_V1',
        remote_account_exclusivity='NOT_OBSERVABLE')
    _RUNS[approval] = generation_id
    return scope


def issue_intake(*, scope, capture, market, expected_capture_sha256, enabled=False):
    if enabled is not True:
        raise ValueError('pending_intake_default_off')
    s, decision = _scope(scope)
    if market in _ISSUED_MARKETS.get(scope,set()):
        raise ValueError('pending_intake_market_already_issued')
    raw, receipt = captured_private_snapshot(capture)
    rows = json.loads(raw)
    cutoff = datetime.fromisoformat(receipt['cutoff'])
    if (digest(rows) != expected_capture_sha256 or receipt['original_rows_sha256'] != expected_capture_sha256
            or not s['confirmed_at'] <= cutoff <= _now()
            or _now()-cutoff > timedelta(minutes=5)
            or receipt['permission_event'] != decision.event_id
            or receipt['sqlite_mode'] != 'ro' or receipt['query_only'] is not True
            or receipt['total_changes'] != 0 or receipt['denied_queries']
            or len(receipt['statement_templates']) != 5
            or sum(q['operation'] == 'SELECT' for q in receipt['query_trace']) != 5):
        raise ValueError('pending_intake_fresh_five_select_capture_required')
    expected_tables = {'watchlistitem', 'securitymaster', 'company', 'investmentthesis'}
    if set(rows) != expected_tables or market not in ('kr', 'us'):
        raise ValueError('pending_intake_exact_registration_required')
    indices = {}
    for table, values in rows.items():
        if len({r['ticker'] for r in values}) != len(values) or len({r['id'] for r in values}) != len(values):
            raise ValueError('pending_intake_duplicate_registration')
        indices[table] = {r['ticker']:r for r in values}
    subjects = set(indices['watchlistitem'])
    if subjects != set(decision.subjects) or any(set(v) != subjects for v in indices.values()):
        raise ValueError('pending_intake_registration_coverage')
    bindings, identities, ids = {}, {}, set()
    for ticker in sorted(subjects):
        watch, security, company, thesis = [indices[t][ticker] for t in
            ('watchlistitem', 'securitymaster', 'company', 'investmentthesis')]
        venue = security['exchange']
        row_market = 'kr' if security['country'] == 'KR' else 'us' if security['country'] == 'US' else None
        valid_venue = venue in ({'KRX', 'KOSPI', 'KOSDAQ'} if row_market == 'kr' else {'NASDAQ', 'NYSE', 'AMEX'})
        sid = security['canonical_security_id']
        if (watch['onboarding_state'] != 'PENDING_ONBOARDING' or watch['active'] not in (False, 0)
                or watch['production_eligible'] not in (False, 0) or watch['monitoring_requested'] not in (True, 1)
                or watch['activated_at'] or watch['first_eligible_session']
                or not row_market or not valid_venue or not sid or sid in ids
                or not security['canonical_company_id'] or watch['exchange'] != venue or company['exchange'] != venue
                or thesis['status'] != 'active' or not thesis['core_thesis'].strip() or thesis['version'] < 1):
            raise ValueError('pending_intake_pending_identity_thesis_required')
        ids.add(sid)
        if row_market == market:
            identities[ticker] = {k:security[k] for k in ('ticker','canonical_security_id',
                'canonical_company_id','country','exchange','cik','corp_code')}
            bindings[ticker] = dict(security_id=sid,registration_hash=digest(watch),
                identity_hash=digest(security),thesis_hash=digest(thesis),thesis_version=thesis['version'])
    if not bindings:
        raise ValueError('pending_intake_empty_market')
    clock = approval_owner.completed_clock(market, cutoff)
    public = dict(contract=CONTRACT, generation_id=s['generation'],market=market,calendar=clock,
        capture_sha256=expected_capture_sha256,capture_receipt_sha256=digest(receipt),
        bindings=bindings,scope='SOURCE_ONLY_NO_NATIVE',
        ACTIVE=False,production_eligible=False,first_eligible_session=None,
        current_production_Source=False,MarketParent=False,valuation=False,native=False,judgment=False,send=False)
    handle = PendingSourceIntake()
    _INTAKES[handle] = dict(scope=scope,capture=capture,capture_hash=digest(rows),
        receipt_hash=digest(receipt),public=public,identities=identities)
    _ISSUED_MARKETS.setdefault(scope,set()).add(market)
    return handle, json.loads(json.dumps(public))


def consume_intake(handle, *, generation_id, role, security_ids, session):
    if type(handle) is not PendingSourceIntake or handle not in _INTAKES:
        raise ValueError('pending_intake_live_owner_required')
    s = _INTAKES[handle]
    _scope(s['scope'])
    raw, receipt = captured_private_snapshot(s['capture'])
    public = s['public']
    if 'source_intake_owner' in s:
        approval_owner.source_intake_snapshot(s['source_intake_owner'],generation_id=generation_id,
            subjects=tuple(s['identities']),policy=s['identity_policy'])
    clock = approval_owner.completed_clock(public['market'], _now())
    if (digest(json.loads(raw)) != s['capture_hash'] or digest(receipt) != s['receipt_hash']
            or generation_id != public['generation_id'] or role not in ROLES
            or not security_ids or len(set(security_ids)) != len(security_ids)
            or not set(security_ids) <= {r['security_id'] for r in public['bindings'].values()}
            or session != public['calendar']['target'] or clock['target'] != session):
        raise ValueError('pending_intake_generation_role_or_session_mismatch')
    return json.loads(json.dumps(public))


def adapt_registered_intake(*,scope,source_intake_owner,subjects,policy,enabled=False):
    """C9: authenticated subset into the ORIGINAL pending Parent/Worker contract.

    No ACTIVE projection, new provider, source fact or current use is issued.
    Exact provider/account authorization remains at the original Parent boundary.
    """
    if enabled is not True:
        raise ValueError('pending_intake_default_off')
    s,decision=_scope(scope)
    identities,receipt,capture,approval=approval_owner.source_intake_snapshot(source_intake_owner,
        generation_id=s['generation'],subjects=subjects,policy=policy)
    if approval is not s['approval'] or not set(subjects)<=set(decision.subjects):
        raise ValueError('pending_intake_adapter_approval_mismatch')
    market=receipt['market']
    if market in _ISSUED_MARKETS.get(scope,set()):
        raise ValueError('pending_intake_market_already_issued')
    raw,captured=captured_private_snapshot(capture)
    cutoff=datetime.fromisoformat(captured['cutoff'])
    if not s['confirmed_at']<=cutoff<=_now():
        raise ValueError('pending_intake_adapter_capture_time')
    bindings={t:dict(security_id=r['canonical_security_id'],identity_hash=digest(r),
        registration_hash=receipt['subjects'][t]['registration_sha256']) for t,r in identities.items()}
    public=dict(contract='registered-source-intake-pending-adapter-v1',generation_id=s['generation'],
        market=market,calendar=approval_owner.completed_clock(market,cutoff),
        capture_sha256=captured['original_rows_sha256'],capture_receipt_sha256=digest(captured),
        bindings=bindings,scope='SOURCE_ONLY_NO_NATIVE',ACTIVE=False,production_eligible=False,
        first_eligible_session=None,current_production_Source=False,MarketParent=False,
        valuation=False,native=False,judgment=False,send=False)
    handle=PendingSourceIntake()
    _INTAKES[handle]=dict(scope=scope,capture=capture,capture_hash=digest(json.loads(raw)),
        receipt_hash=digest(captured),public=public,identities=identities,
        source_intake_owner=source_intake_owner,identity_policy=policy)
    _ISSUED_MARKETS.setdefault(scope,set()).add(market)
    return handle,json.loads(json.dumps(public))


def require_live_worker_adapter(handle, *, parent=None):
    """Never impersonate the ACTIVE-only original Parent or issue live HTTP."""
    if type(handle) is not PendingSourceIntake or handle not in _INTAKES:
        raise ValueError('pending_intake_live_owner_required')
    _scope(_INTAKES[handle]['scope'])
    from app.services import pending_source_parent as adapter
    if type(parent) is not adapter.PendingSourceParent or adapter.state(parent)['intake'] is not handle:
        raise ValueError('SOURCE_INTAKE_ADAPTER_NOT_PROVEN')
    return adapter.resolve_parent(parent)


def revoke_intake(handle):
    if handle not in _INTAKES:
        raise ValueError('pending_intake_live_owner_required')
    del _INTAKES[handle]
