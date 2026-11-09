"""Trusted bootstrap binding for Native V2; no HTTP enrollment endpoint.

Only the control plane supplies a private service enrollment resolver. Public
receipts and V1 Parents are never accepted here. Installation remains separate.
"""
from datetime import datetime, timezone
import os
from weakref import WeakKeyDictionary
from app.services import prospective_class_c_owner as original
from app.services.unified_snapshot_contract import digest, encoded


class NativeServiceParticipant:
    __slots__ = ('__weakref__',)


class NativeGetConsent:
    __slots__ = ('__weakref__',)


_PARTICIPANTS = WeakKeyDictionary()
_CONSENTS = WeakKeyDictionary()
SERVICE_BRIDGE_SHA256 = 'ce90b845255c1adacd4d4044466f8868d7f0938c008d5e9f20f5f6ba9c268dc2'


def record_native_get_consent(*, approval, reads, generation_id, physical_max, consent_event_sha256):
    """Trusted backend records a NEW explicit native-GET operator decision.

Not a web endpoint. Original membership approval alone cannot call the service.
The backend audit trail must bind consent_event_sha256 to the exact frozen plan.
"""
    import re
    original._approval(approval)
    if (not re.fullmatch('[0-9a-f]{64}',consent_event_sha256)
            or type(physical_max) is not int or not 1 <= physical_max <= 44):
        raise ValueError('native_explicit_bounded_GET_consent_required')
    handle=NativeGetConsent()
    _CONSENTS[handle]=(approval,generation_id,digest([r.model_dump(mode='json') for r in reads]),physical_max)
    return handle


def enroll_participant(*, approval, consent, owners, reads, service_enrollment,
                       resolve_service_enrollment, generation_id):
    """Host-only adapter; the original backend must supply the opaque handles.

The resolver is supplied by the pinned service bootstrap, NOT a user request,
model, boolean or a deserialized receipt. It returns the actual private bridge.
It is intentionally not installed into any currently running host by this task.
"""
    from app.services.native_source_v2 import NativeReadV2
    reads = tuple(NativeReadV2.model_validate_json(r.model_dump_json()) for r in reads)
    if not reads or len(reads)>2 or set(owners) != {r.market for r in reads}:
        raise ValueError('native_exact_market_owners_required')
    if (type(consent) is not NativeGetConsent or consent not in _CONSENTS
            or _CONSENTS[consent][:3] != (approval,generation_id,digest([r.model_dump(mode='json') for r in reads]))):
        raise ValueError('native_explicit_GET_consent_capability_required')
    if not callable(resolve_service_enrollment) or not hasattr(resolve_service_enrollment,'__module__'):
        raise ValueError('native_trusted_service_resolver_required')
    # The installed resolver must be the pinned implementation, not a callback
    # supplied by a request or a self-signed substitute. Pin set after code audit.
    import hashlib, inspect, sys
    resolver_module = sys.modules.get(resolve_service_enrollment.__module__)
    if (resolver_module is None
            or getattr(resolver_module, 'resolve_enrollment', None) is not resolve_service_enrollment
            or hashlib.sha256(inspect.getsource(resolver_module).encode()).hexdigest() != SERVICE_BRIDGE_SHA256):
        raise ValueError('native_pinned_service_resolver_required')
    bridge = resolve_service_enrollment(service_enrollment)
    if type(bridge) is not resolver_module.ServiceBridge:
        raise ValueError('native_actual_service_bridge_required')
    frozen = digest([r.model_dump(mode='json') for r in reads])

    def check():
        decision = original._approval(approval)
        if consent not in _CONSENTS or bridge.maximum != _CONSENTS[consent][3]:
            raise ValueError('native_consent_revoked_or_budget_changed')
        if bridge.generation != generation_id or bridge.mode != 'LIVE':
            raise ValueError('native_live_service_not_authorized')
        if tuple(bridge.queries) != tuple(encoded(r.params()) for r in reads):
            raise ValueError('native_service_frozen_queries_mismatch')
        if bridge.pid != os.getpid():
            raise ValueError('native_private_bootstrap_process_required')
        if bridge.expires > decision.expires_at:
            raise ValueError('native_service_exceeds_operator_consent')
        for read in reads:
            if read.symbol not in decision.subjects:
                raise ValueError('native_subject_not_approved')
            owner = owners[read.market]
            original.require_generation(owner, generation_id)
            document, receipt = original._state(owner)
            if (receipt['approval_sha256'] != digest(decision.model_dump(mode='json'))
                    or receipt['calendar']['target'] != read.session.isoformat()
                    or datetime.now(timezone.utc) >= datetime.fromisoformat(receipt['expires_at'])):
                raise ValueError('native_original_scope_or_session_mismatch')
            rows = [row['record'] for component in document['roles'].values()
                    for row in component['records'] if row['table']=='securitymaster'
                    and row['record']['ticker']==read.symbol]
            if len(rows)!=1:
                raise ValueError('native_registered_security_missing')
            row = rows[0]
            if (row['canonical_security_id'] != read.security_id
                    or row['canonical_company_id'] != read.issuer_id
                    or row['exchange'] != read.exchange
                    or read.currency != ('KRW' if read.market=='kr' else 'USD')):
                raise ValueError('native_registered_security_issuer_venue_mismatch')
        bridge.check()
        if frozen != digest([r.model_dump(mode='json') for r in reads]):
            raise ValueError('native_enrollment_plan_changed')

    check()
    participant = NativeServiceParticipant()
    _PARTICIPANTS[participant] = (bridge, reads, check, os.getpid())
    return participant


def resolve_participant(participant):
    if type(participant) is not NativeServiceParticipant or participant not in _PARTICIPANTS:
        raise ValueError('native_signed_service_runtime_and_physical_adapter_required')
    bridge, reads, check, pid = _PARTICIPANTS[participant]
    if pid != os.getpid():
        raise ValueError('native_bootstrap_process_changed')
    check()
    return bridge, reads, check
