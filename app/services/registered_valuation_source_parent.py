"""Separate Source-only valuation Parent over the unchanged private Worker lane."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import os
from app.services import pending_source_parent as pending
from app.services.registered_valuation_source_intent import PURPOSE,require_intent,claim_provider
from app.services.provider_native_valuation_acquisition import routing_markets,add_slots
from app.services.canonical_source_plan import kiwoom_request
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor,RequestPlan,wire_identity
from app.services.sealed_chart_slots import chart_slots
from app.services.sealed_response_binding import binding_owner_hash
from app.services.scoped_source_plan import _sessions
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes


def compile_plan(*,identities,listing_rows,generation_id,cutoff,code_sha,provider_config_sha256):
    markets=routing_markets(identities,listing_rows=listing_rows)
    if not 1<=len(identities)<=8 or set(markets)!=set(identities):
        raise ValueError('valuation_parent_exact_kr_subjects')
    _,sessions=_sessions(cutoff);target=next(str(p.target) for p in sessions if p.market=='kr')
    normalizer='app/services/sealed_source_transport.py'
    owner=sha256_bytes((pending.ROOT/normalizer).read_bytes());descriptors=[]
    def add(key,provider,role,market,subject,operation,request,*,mandatory=True,pages=1,retries=0,**unused):
        d=FreshRequestDescriptor(generation_id=generation_id,logical_request_id=key,provider=provider,
            source_family=role.split(':')[0],role_id=role,market=market,subject=subject,
            endpoint_operation=operation,request_json=wire_identity(request,('PLAN_CREDENTIAL',)),
            target_period=target,mandatory=mandatory,group_id=key,page_ordinal=1,max_pages=pages,
            document_ordinal=1,max_documents=1,timeout_seconds=60,transient_retry_max=retries,
            raw_path='raw/'+key+'/source.body',normalizer=normalizer,consumer_role=role,
            owner_sha256=owner,config_identity_sha256=provider_config_sha256)
        descriptors.extend(chart_slots(d,maximum_pages=pages) if pages>1 else (d,))
    def kiwoom(key,role,market,subject,api,route,body,**kw):
        add(key,'kiwoom',role,market,subject,api,kiwoom_request(api,route,body),**kw)
    import httpx
    add('kiwoom:auth','kiwoom','kiwoom:credential_exchange','global','run','credential_exchange',
        httpx.Request('POST','https://api.kiwoom.com/oauth2/token',
            headers={'Content-Type':'application/json;charset=UTF-8'},
            json=dict(grant_type='client_credentials',appkey='PLAN_CREDENTIAL',secretkey='PLAN_CREDENTIAL')))
    inventory=add_slots(identities=identities,market_types=markets,add=add,kiwoom=kiwoom)
    if sum(d.max_transport_attempts for d in descriptors)>19:
        raise ValueError('valuation_parent_nineteen_physical_limit')
    plan=RequestPlan(generation_id=generation_id,code_sha=code_sha,frozen_at=cutoff,
        policy_schema_sha256=digest(dict(contract=PURPOSE,identities=identities,route_rows=listing_rows)),
        descriptors=tuple(descriptors),mandatory_roles=tuple(sorted({d.consumer_role for d in descriptors if d.mandatory})),
        binding_owner_sha256=binding_owner_hash())
    return dict(request_plan=plan,stock_reads=(),sessions=sessions,us_market_symbols=(),
        owner_files_json=json.dumps(pending.pins()),valuation_slots=inventory)


def issue_parent(*,intent,intent_generation,subjects,listing_rows,session,generation_id,
                 cutoff,code_sha,provider_config_sha256,enabled=False):
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.kiwoom_global_lane import GlobalKiwoomLane
    if (enabled is not True or type(session) is not ParticipatingSession
            or type(session._lane) is not GlobalKiwoomLane or session.kind!='CLI'
            or cutoff.utcoffset() is None or not cutoff<=datetime.now(timezone.utc)):
        raise ValueError('valuation_parent_explicit_original_session_required')
    session.attestation()
    identities=require_intent(intent,generation_id=intent_generation,provider='kiwoom',subjects=subjects)
    wire=compile_plan(identities=identities,listing_rows=listing_rows,generation_id=generation_id,
        cutoff=cutoff,code_sha=code_sha,provider_config_sha256=provider_config_sha256)
    plan=wire['request_plan']
    claim_provider(intent,generation_id=intent_generation,provider='kiwoom',subjects=subjects,plan_sha256=plan.plan_sha256)
    receipt=dict(contract='registered-valuation-source-parent-v1',scope=PURPOSE,generation_id=generation_id,
        plan_sha256=plan.plan_sha256,cutoff=cutoff.isoformat(),expires_at=(cutoff+timedelta(minutes=10)).isoformat(),
        maximum_attempts=19,planned_attempts=len(plan.descriptors),source_use=False,financial_use=False,
        valuation=False,model_use=False,ACTIVE=False,send=False)
    parent=pending.PendingSourceParent()
    pending._LIVE[parent]=dict(pid=os.getpid(),pins=pending.pins(),session=session,receipt=receipt,
        wire=wire,identities=identities,config=None,claimed=False,worker_pid=None,challenge=None,ack=False,
        valuation_intent=intent,intent_generation=intent_generation)
    return parent,deepcopy(wire)


def validate_worker_command(stock,templates,command):
    if stock['reads'] or set(command)!={'market_wire'}:
        raise PermissionError('VALUATION_SOURCE_ONLY_COMMAND_SCOPE')
    key=command['market_wire']['logical_id']
    if (key not in templates or templates[key]['endpoint_operation'] not in
            ('credential_exchange','ka10099','ka10001')):
        raise PermissionError('VALUATION_SOURCE_ONLY_OFFICIAL_READ_SCOPE')
