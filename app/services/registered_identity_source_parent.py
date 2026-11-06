"""Default-off official KR identity reads under the original private Worker.

This permits no chart, economic use, valuation decision, ACTIVE or delivery.
It reuses original descriptors, continuation binding, dispatcher and Worker.
"""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import json
import os
from weakref import WeakKeyDictionary

from app.services import pending_source_parent as pending
from app.services import prospective_class_c_owner as registration
from app.services.canonical_source_plan import kiwoom_request
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor,RequestPlan,wire_identity
from app.services.sealed_chart_slots import chart_slots
from app.services.sealed_response_binding import binding_owner_hash
from app.services.scoped_source_plan import _sessions
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes

PURPOSE='REGISTERED_IDENTITY_DISCOVERY_ONLY_V1'
_ISSUED=WeakKeyDictionary()


def issue_parent(*,discovery_owner,discovery_generation,subjects,session,generation_id,
                 cutoff,code_sha,provider_config_sha256,enabled=False):
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    if (enabled is not True or type(session) is not ParticipatingSession
            or type(session._lane) is not GlobalKiwoomLane or session.kind!='CLI'
            or not subjects or len(set(subjects))!=len(subjects)
            or cutoff.utcoffset() is None or not cutoff<=datetime.now(timezone.utc)):
        raise ValueError('identity_parent_explicit_original_session_required')
    session.attestation()
    if discovery_owner in _ISSUED:
        raise ValueError('identity_parent_one_dispatch_only')
    identities={t:registration.require_identity_discovery(discovery_owner,
        generation_id=discovery_generation,ticker=t) for t in subjects}
    if any(r['country']!='KR' for r in identities.values()):
        raise ValueError('identity_parent_kr_listing_contract_only')
    descriptors=[]
    owner='app/services/sealed_source_transport.py'
    owner_hash=sha256_bytes((pending.ROOT/owner).read_bytes())
    _,pairs=_sessions(cutoff)
    target=next(str(p.target) for p in pairs if p.market=='kr')
    def add(key,api,body,*,subject,pages=1):
        route='/oauth2/token' if api=='credential_exchange' else '/api/dostk/stkinfo'
        if api=='credential_exchange':
            import httpx
            request=httpx.Request('POST','https://api.kiwoom.com'+route,
                headers={'Content-Type':'application/json;charset=UTF-8'},json=body)
        else:request=kiwoom_request(api,route,body)
        role='kiwoom:credential_exchange' if api=='credential_exchange' else key
        descriptor=FreshRequestDescriptor(generation_id=generation_id,logical_request_id=key,
            provider='kiwoom',source_family=role.split(':')[0],role_id=role,market='kr',subject=subject,
            endpoint_operation=api,request_json=wire_identity(request,('PLAN_CREDENTIAL',)),
            target_period=target,mandatory=True,group_id=key,page_ordinal=1,max_pages=pages,
            document_ordinal=1,max_documents=1,timeout_seconds=600,transient_retry_max=0,
            raw_path='raw/'+key+'/source.body',normalizer=owner,consumer_role=role,
            owner_sha256=owner_hash,config_identity_sha256=provider_config_sha256)
        descriptors.extend(chart_slots(descriptor,maximum_pages=pages) if pages>1 else (descriptor,))
    add('kiwoom:auth','credential_exchange',dict(grant_type='client_credentials',appkey='PLAN_CREDENTIAL',secretkey='PLAN_CREDENTIAL'),subject='run')
    for market in ('0','10'):
        add('identity:list:'+market,'ka10099',{'mrkt_tp':market},subject='*',pages=5)
    for ticker in sorted(subjects):add('identity:basic:'+ticker,'ka10001',{'stk_cd':ticker},subject=ticker)
    if len(descriptors)>20:raise ValueError('identity_parent_twenty_attempt_limit')
    plan=RequestPlan(generation_id=generation_id,code_sha=code_sha,
        policy_schema_sha256=digest(dict(contract=PURPOSE,subjects=sorted(subjects))),
        frozen_at=cutoff,descriptors=tuple(descriptors),mandatory_roles=tuple(sorted({d.consumer_role for d in descriptors})),
        binding_owner_sha256=binding_owner_hash())
    wire=dict(request_plan=plan,stock_reads=(),sessions=pairs,us_market_symbols=(),
        owner_files_json=json.dumps(pending.pins()))
    receipt=dict(contract='registered-identity-parent-v1',scope=PURPOSE,generation_id=generation_id,
        plan_sha256=plan.plan_sha256,cutoff=cutoff.isoformat(),
        expires_at=(cutoff+timedelta(minutes=10)).isoformat(),maximum_attempts=20,
        planned_attempts=len(descriptors),source_use=False,financial_use=False,
        valuation=False,model_use=False,ACTIVE=False,send=False)
    parent=pending.PendingSourceParent()
    pending._LIVE[parent]=dict(pid=os.getpid(),pins=pending.pins(),session=session,receipt=receipt,
        wire=wire,identities=identities,config=None,claimed=False,worker_pid=None,challenge=None,ack=False,
        identity_discovery=discovery_owner,identity_generation=discovery_generation)
    _ISSUED[discovery_owner]=True
    return parent,deepcopy(wire)
