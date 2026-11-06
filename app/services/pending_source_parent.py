"""Typed, one-dispatch pending Source adapter; never an ACTIVE Owner.

Only live Intake and original participating-session objects can create a Parent.
Public handoff JSON names the action but cannot reconstruct consent or a Parent.
"""
from copy import deepcopy
from datetime import datetime,timezone
import json,os,secrets
from pathlib import Path
from threading import RLock
from weakref import WeakKeyDictionary

from app.services import pending_source_intake as intake
from app.services.scoped_source_plan import ScopedConfig,compile_scoped_wire_contract
from app.services.unified_snapshot_contract import digest

CONTRACT='pending-scoped-source-parent-v1'
PURPOSE='SCOPED_SOURCE_ONLY_PENDING'
ROOT=Path(__file__).resolve().parents[2]
_LIVE=WeakKeyDictionary()
_CLAIMED=WeakKeyDictionary()
_LOCK=RLock()
FILES=('app/services/pending_source_parent.py','app/services/pending_source_intake.py',
 'app/services/source_dispatch_authority.py','app/services/current_scoped_worker_bridge.py',
 'app/services/current_scoped_source_dispatch.py','app/services/current_scoped_source_results.py',
 'scripts/current_scoped_source_worker.py','app/services/scoped_worker_launch.py',
 'app/services/scoped_source_plan.py','app/services/sealed_fresh_dispatch.py',
 'app/services/query_time_monitoring_price.py','app/services/source_value_quality.py',
 'app/services/price_session_projection.py',
 'app/services/sealed_response_binding.py','app/services/market_worker_rpc.py',
 'app/services/same_session_market_windows.py','app/services/market_component_execution.py',
 'app/services/market_component_handoff.py','app/services/registered_identity_source_parent.py',
 'app/services/pending_completed_close_contract.py')

class PendingSourceParent:
    __slots__=('__weakref__',)

def pins():return {n:digest((ROOT/n).read_bytes().hex()) for n in FILES}

def issue_parent(*,intake_owner,config,session,generation_id,cutoff,code_sha,
                 provider_config_sha256,maximum_attempts=20,enabled=False):
    return _issue_parent(intake_owner=intake_owner,config=config,session=session,
        generation_id=generation_id,cutoff=cutoff,code_sha=code_sha,
        provider_config_sha256=provider_config_sha256,maximum_attempts=maximum_attempts,
        enabled=enabled,close_only=False)

def issue_completed_close_parent(*,intake_owner,config,session,generation_id,cutoff,code_sha,
                                 provider_config_sha256,maximum_attempts=15,enabled=False):
    return _issue_parent(intake_owner=intake_owner,config=config,session=session,
        generation_id=generation_id,cutoff=cutoff,code_sha=code_sha,
        provider_config_sha256=provider_config_sha256,maximum_attempts=maximum_attempts,
        enabled=enabled,close_only=True)

def _issue_parent(*,intake_owner,config,session,generation_id,cutoff,code_sha,
                  provider_config_sha256,maximum_attempts,enabled,close_only):
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    if (enabled is not True or type(session) is not ParticipatingSession
            or type(session._lane) is not GlobalKiwoomLane or session.kind!='CLI'
            or type(maximum_attempts) is not int or not 1<=maximum_attempts<=20):
        raise ValueError('pending_parent_original_session_and_bound_required')
    session.attestation()
    if close_only:
        session._lane._state()
    config=ScopedConfig.model_validate(config)
    if config.capture_selection is None or config.capture_selection.market_contexts:
        raise ValueError('pending_parent_chart_price_only')
    state=intake._INTAKES.get(intake_owner)
    if not state:raise ValueError('pending_parent_live_intake_required')
    market=state['public']['market']
    if {s.market for s in config.subjects}!={market}:
        raise ValueError('pending_parent_exact_market')
    identities=deepcopy(state['identities'])
    selected={s.ticker for s in config.subjects}
    if not selected or not selected <= set(identities):
        raise ValueError('pending_parent_exact_subjects')
    identities={ticker:identities[ticker] for ticker in selected}
    for s in config.subjects:
        original=identities[s.ticker]
        if (s.security_id,s.venue,s.issuer_id)!=(original['canonical_security_id'],original['exchange'],
                original['corp_code' if market=='kr' else 'cik']):
            raise ValueError('pending_parent_identity_changed')
    wire=compile_scoped_wire_contract(config=config,identities=identities,generation_id=generation_id,
        at=cutoff,code_sha=code_sha,provider_config_sha256=provider_config_sha256,retries=0)
    close_requirements=()
    if close_only:
        from app.services.pending_completed_close_contract import requirements
        close_requirements=requirements(config,wire)
        for row in close_requirements:
            intake.consume_intake(intake_owner,generation_id=generation_id,role='completed_close',
                security_ids=(row['security_id'],),session=row['session'])
    elif not wire['stock_reads']:
        raise ValueError('pending_parent_original_chart_reads_required')
    for read in wire['stock_reads']:
        intake.consume_intake(intake_owner,generation_id=generation_id,role=read.role,
            security_ids=(read.canonical_security_id,),session=read.latest_completed_session)
    plan=wire['request_plan']
    attempts=sum(d.max_transport_attempts for d in plan.descriptors)
    if attempts>maximum_attempts:raise ValueError('pending_parent_physical_cap')
    now=datetime.now(timezone.utc)
    captured=intake._scope(state['scope'])[0]
    if ('maximum_physical_attempts' in captured
            and maximum_attempts>captured['maximum_physical_attempts']):
        raise ValueError('pending_parent_campaign_allocation_cap')
    if not captured['confirmed_at']<=cutoff<=now:
        raise ValueError('pending_parent_current_cutoff')
    with _LOCK:
        if intake_owner in _CLAIMED:raise ValueError('pending_parent_intake_one_dispatch_only')
        parent=PendingSourceParent()
        receipt=dict(contract=CONTRACT,scope=PURPOSE,generation_id=generation_id,
            plan_sha256=plan.plan_sha256,cutoff=cutoff.isoformat(),expires_at=captured['expires'].isoformat(),
            maximum_attempts=maximum_attempts,planned_attempts=attempts,
            code_pins_sha256=digest(pins()),registration_sha256=digest(state['public']),
            full22_native=False,D01_D02=False,financial_use=False,model_use=False,
            source_evidence_state='SOURCE_OBSERVED_PENDING_NOT_YET_CAPTURED')
        if close_only:
            from app.services.pending_completed_close_contract import CONTRACT as CLOSE_CONTRACT,PURPOSE as CLOSE_PURPOSE
            receipt.update(contract=CLOSE_CONTRACT,scope=CLOSE_PURPOSE,
                chart_coverage=False,current_authority=False,valuation_use=False,economic_use=False)
        _LIVE[parent]=dict(pid=os.getpid(),pins=pins(),intake=intake_owner,session=session,
            config=config,wire=wire,identities=identities,receipt=receipt,claimed=False,
            worker_pid=None,challenge=None,ack=False,close_only=close_only)
        _CLAIMED[intake_owner]=True
    return parent,deepcopy(wire)

def state(parent):
    if type(parent) is not PendingSourceParent or parent not in _LIVE:
        raise ValueError('pending_parent_live_handle_required')
    s=_LIVE[parent]
    if s['pid']!=os.getpid() or s['pins']!=pins():
        raise ValueError('pending_parent_process_or_code_changed')
    s['session'].attestation()
    if 'valuation_intent' in s:
        from app.services.registered_valuation_source_intent import PURPOSE,require_intent
        if (s['receipt']['scope']!=PURPOSE or datetime.now(timezone.utc)>=datetime.fromisoformat(s['receipt']['expires_at'])):
            raise ValueError('valuation_parent_scope_expired')
        if require_intent(s['valuation_intent'],generation_id=s['intent_generation'],provider='kiwoom',
                subjects=tuple(s['identities']))!=s['identities']:
            raise ValueError('valuation_parent_registration_changed')
        return s
    if 'identity_discovery' in s:
        from app.services.registered_identity_source_parent import PURPOSE
        from app.services.prospective_class_c_owner import require_identity_discovery
        if (s['receipt']['scope']!=PURPOSE or datetime.now(timezone.utc)>=datetime.fromisoformat(s['receipt']['expires_at'])):
            raise ValueError('identity_parent_scope_expired')
        for ticker,identity in s['identities'].items():
            if require_identity_discovery(s['identity_discovery'],generation_id=s['identity_generation'],ticker=ticker)!=identity:
                raise ValueError('identity_parent_registration_changed')
        return s
    if 'market_approval' in s:
        from app.services.prospective_class_c_owner import _approval
        decision=_approval(s['market_approval'])
        if ('market:'+s['market'] not in decision.subjects
                or datetime.now(timezone.utc)>=s['market_expires']
                or s['receipt']['scope']!='PENDING_MARKET_COMPONENT_SOURCE_ONLY'):
            raise ValueError('pending_market_component_approval_expired_or_changed')
        return s
    if s.get('close_only'):
        from app.services.pending_completed_close_contract import requirements
        from app.services.kiwoom_global_lane import _read
        lane_state=_read(s['session']._lane.root/'state.json')
        if (lane_state.get('halted') is not False
                or type(lane_state.get('in_flight')) is not bool
                or lane_state['in_flight'] and lane_state.get('pid')!=os.getpid()):
            raise ValueError('pending_close_original_lane_stopped_or_foreign_flight')
        for row in requirements(s['config'],s['wire']):
            intake.consume_intake(s['intake'],generation_id=s['receipt']['generation_id'],role='completed_close',
                security_ids=(row['security_id'],),session=row['session'])
    for read in s['wire']['stock_reads']:
        intake.consume_intake(s['intake'],generation_id=s['receipt']['generation_id'],role=read.role,
            security_ids=(read.canonical_security_id,),session=read.latest_completed_session)
    return s

def resolve_parent(parent,*,plan=None):
    s=state(parent)
    if plan is not None and plan!=s['wire']['request_plan']:
        raise ValueError('pending_parent_exact_plan_required')
    return deepcopy(s['receipt'])

def authorize_descriptor(parent,descriptor,*,plan):
    s=state(parent);resolve_parent(parent,plan=plan)
    if descriptor not in plan.descriptors:raise ValueError('pending_parent_exact_descriptor')
    return deepcopy(s['receipt'])

def revoke_parent(parent):
    if type(parent) is not PendingSourceParent or parent not in _LIVE:
        raise ValueError('pending_parent_live_handle_required')
    del _LIVE[parent]

def public_handoff(parent):
    r=resolve_parent(parent)
    return dict(contract=r['contract'],scope=r['scope'],generation_id=r['generation_id'],
        plan_sha256=r['plan_sha256'],parent_receipt_sha256=digest(r))

def begin_worker(parent,*,worker_pid,handoff,process):
    import asyncio
    with _LOCK:
        s=state(parent)
        if (s['claimed'] or handoff!=public_handoff(parent) or type(worker_pid)is not int or worker_pid<=0
                or type(process) is not asyncio.subprocess.Process or process.pid!=worker_pid or process.returncode is not None):
            raise ValueError('pending_parent_worker_handoff_one_use')
        s['claimed']=True;s['worker_pid']=worker_pid
        s['process']=process
        s['challenge']=secrets.token_hex(32)
        return dict(**handoff,nonce=s['challenge'])

def accept_worker(parent,ack,*,worker_pid):
    s=state(parent)
    expected=dict(**public_handoff(parent),nonce_sha256=digest(s['challenge']),worker_pid=worker_pid)
    if s['ack'] or s['worker_pid']!=worker_pid or s['challenge'] is None or ack!=expected:
        raise ValueError('pending_parent_worker_ack_mismatch')
    s['ack']=True

def require_worker(parent,worker_pid,*,physical=False):
    s=state(parent)
    if (not s['ack'] or s['worker_pid']!=worker_pid
            or (physical and s['process'].returncode is not None)):
        raise ValueError('pending_parent_worker_not_authenticated')

def replay_context(parent):
    from app.services.current_scoped_source_owner import ScopedSourceSpec
    s=state(parent);r=s['receipt'];plan=s['wire']['request_plan']
    if 'market_approval' in s:
        from types import SimpleNamespace
        return deepcopy(r),SimpleNamespace(config=s['config'],cutoff=plan.frozen_at),{}
    spec=ScopedSourceSpec(config=s['config'],generation_id=plan.generation_id,cutoff=plan.frozen_at,
        code_sha=plan.code_sha,provider_config_sha256=plan.descriptors[0].config_identity_sha256,
        maximum_attempts=r['maximum_attempts'])
    return deepcopy(r),spec,deepcopy(s['identities'])


_MARKET_ALLOCATIONS=WeakKeyDictionary()

def issue_market_component_parent(*,approval,config,session,generation_id,cutoff,code_sha,
        provider_config_sha256,maximum_attempts,enabled=False):
    """Distinct opt-in Market component authority, not Class-C/ACTIVE ownership."""
    from datetime import timedelta
    from app.services.prospective_class_c_owner import _approval
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    from app.services.scoped_source_plan import ScopedMarketComponentConfig
    decision=_approval(approval);now=datetime.now(timezone.utc)
    if (enabled is not True or type(config) is not ScopedMarketComponentConfig
            or type(session) is not ParticipatingSession or type(session._lane) is not GlobalKiwoomLane
            or session.kind!='CLI' or type(maximum_attempts) is not int or not 1<=maximum_attempts<=56
            or not decision.effective_at<=cutoff<=now or not generation_id):
        raise ValueError('pending_market_component_explicit_scope_required')
    market=config.capture_selection.market_contexts[0]
    if 'market:'+market not in decision.subjects:raise ValueError('pending_market_operator_scope_mismatch')
    session.attestation()
    wire=compile_scoped_wire_contract(config=config,identities={},generation_id=generation_id,
        at=cutoff,code_sha=code_sha,provider_config_sha256=provider_config_sha256,retries=0)
    plan=wire['request_plan'];attempts=sum(d.max_transport_attempts for d in plan.descriptors)
    if wire['stock_reads'] or not 0<attempts<=maximum_attempts:
        raise ValueError('pending_market_component_plan_or_budget_mismatch')
    if any(not d.logical_request_id.startswith((market+'_market:','kiwoom:auth')) for d in plan.descriptors):
        raise ValueError('pending_market_component_no_stock_or_other_provider')
    with _LOCK:
        allocated=_MARKET_ALLOCATIONS.setdefault(approval,{})
        if market in allocated or sum(allocated.values())+maximum_attempts>150:
            raise ValueError('pending_market_component_one_use_or_total_budget')
        expiry=min(decision.expires_at,now+timedelta(minutes=15))
        receipt=dict(contract='pending-market-component-parent-v1',scope='PENDING_MARKET_COMPONENT_SOURCE_ONLY',
            generation_id=generation_id,market=market,plan_sha256=plan.plan_sha256,cutoff=cutoff.isoformat(),
            expires_at=expiry.isoformat(),maximum_attempts=maximum_attempts,planned_attempts=attempts,
            code_pins_sha256=digest(pins()),operator_approval_sha256=digest(decision.model_dump(mode='json')),
            ClassC='NOT_ISSUED_NOT_REQUIRED_FOR_MARKET_COMPONENTS',MarketParent=False,
            full22_native=False,D01_D02=False,financial_use=False,model_use=False,
            source_evidence_state='MARKET_COMPONENT_PENDING_NOT_YET_CAPTURED')
        parent=PendingSourceParent()
        _LIVE[parent]=dict(pid=os.getpid(),pins=pins(),session=session,config=config,wire=wire,identities={},
            receipt=receipt,claimed=False,worker_pid=None,challenge=None,ack=False,
            market_approval=approval,market=market,market_expires=expiry)
        allocated[market]=maximum_attempts
        return parent,deepcopy(wire)
