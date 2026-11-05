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
 'app/services/sealed_response_binding.py')

class PendingSourceParent:
    __slots__=('__weakref__',)

def pins():return {n:digest((ROOT/n).read_bytes().hex()) for n in FILES}

def issue_parent(*,intake_owner,config,session,generation_id,cutoff,code_sha,
                 provider_config_sha256,maximum_attempts=20,enabled=False):
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    if (enabled is not True or type(session) is not ParticipatingSession
            or type(session._lane) is not GlobalKiwoomLane or session.kind!='CLI'
            or type(maximum_attempts) is not int or not 1<=maximum_attempts<=20):
        raise ValueError('pending_parent_original_session_and_bound_required')
    session.attestation()
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
    if not wire['stock_reads']:
        raise ValueError('pending_parent_original_chart_reads_required')
    for read in wire['stock_reads']:
        intake.consume_intake(intake_owner,generation_id=generation_id,role=read.role,
            security_ids=(read.canonical_security_id,),session=read.latest_completed_session)
    plan=wire['request_plan']
    attempts=sum(d.max_transport_attempts for d in plan.descriptors)
    if attempts>maximum_attempts:raise ValueError('pending_parent_physical_cap')
    now=datetime.now(timezone.utc)
    captured=intake._scope(state['scope'])[0]
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
        _LIVE[parent]=dict(pid=os.getpid(),pins=pins(),intake=intake_owner,session=session,
            config=config,wire=wire,identities=identities,receipt=receipt,claimed=False,
            worker_pid=None,challenge=None,ack=False)
        _CLAIMED[intake_owner]=True
    return parent,deepcopy(wire)

def state(parent):
    if type(parent) is not PendingSourceParent or parent not in _LIVE:
        raise ValueError('pending_parent_live_handle_required')
    s=_LIVE[parent]
    if s['pid']!=os.getpid() or s['pins']!=pins():
        raise ValueError('pending_parent_process_or_code_changed')
    s['session'].attestation()
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
    return dict(contract=CONTRACT,scope=PURPOSE,generation_id=r['generation_id'],
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
    spec=ScopedSourceSpec(config=s['config'],generation_id=plan.generation_id,cutoff=plan.frozen_at,
        code_sha=plan.code_sha,provider_config_sha256=plan.descriptors[0].config_identity_sha256,
        maximum_attempts=r['maximum_attempts'])
    return deepcopy(r),spec,deepcopy(s['identities'])
