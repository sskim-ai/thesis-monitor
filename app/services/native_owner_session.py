"""Default-OFF single-parent ownership for explicitly attached offline sessions.

Legacy canonical batches are not converted to native outputs. The parent keeps
original invocation capabilities and raw per-invocation fixture responses; JSON
stage replay does not issue or reconstruct ownership.
"""

from __future__ import annotations

from threading import RLock
from typing import Literal

from app.services.native_input_admission import Closed, Identity, SHA
from app.services.unified_snapshot_contract import digest

from app.services.native_accepted_ownership import BackendOwnershipRegistry
from app.services.native_economic_core import (
    BackendInvocation,
    ClaimEconomicRequest,
    ReportedEconomicRequest,
)


_LEASE_LOCK = RLock()


class ParentInvocationBinding(Closed):
    invocation_id: Identity
    security_id: Identity
    request_sha256: SHA
    admission_bundle_sha256: SHA
    source_envelope_sha256: SHA


class ParentAdmissionManifest(Closed):
    contract: Literal["backend-parent-admission-manifest-v1"] = (
        "backend-parent-admission-manifest-v1"
    )
    run_id: Identity
    market: Literal["us", "kr"]
    generation_id: Identity
    source_generation_id: Identity
    snapshot_sha256: SHA
    invocations: tuple[ParentInvocationBinding, ...]


class BackendOwnerParent:
    def __init__(
        self,
        *,
        authority_native_v2=False,
        run_id,
        market,
        generation_id,
        source_generation_id,
        snapshot_sha256,
        admission_manifest,
        expected_manifest_sha256,
    ):
        if authority_native_v2 is not True:
            raise ValueError("NATIVE_PARENT_FEATURE_DISABLED")
        self._scope = (run_id, market, generation_id, source_generation_id, snapshot_sha256)
        manifest = ParentAdmissionManifest.model_validate(
            admission_manifest.model_dump(mode="json")
        )
        if (
            digest(manifest.model_dump(mode="json")) != expected_manifest_sha256
            or (
                manifest.run_id,
                manifest.market,
                manifest.generation_id,
                manifest.source_generation_id,
                manifest.snapshot_sha256,
            )
            != self._scope
        ):
            raise ValueError("PARENT_SOURCE_MANIFEST_BINDING_MISMATCH")
        if len({r.invocation_id for r in manifest.invocations}) != len(manifest.invocations):
            raise ValueError("DUPLICATE_PARENT_INVOCATION_BINDING")
        self._manifest = manifest
        self._token = object()
        self._registry = BackendOwnershipRegistry(offline_reproof=True)
        self._invocations = {}
        self._attempts = {}
        self._closed = False
        self._lock = RLock()

    def verify_scope(self, *, run_id, market, generation_id, source_generation_id, snapshot_sha256):
        if self._closed:
            raise ValueError("PARENT_LIFETIME_CLOSED")
        if (run_id, market, generation_id, source_generation_id, snapshot_sha256) != self._scope:
            raise ValueError("PARENT_SESSION_SCOPE_MISMATCH")

    def register(self, invocation):
        with self._lock, _LEASE_LOCK:
            if self._closed or not isinstance(invocation, BackendInvocation):
                raise ValueError("LIVE_PARENT_INVOCATION_REQUIRED")
            q = invocation.verify(invocation.request)
            if (
                q.reference_request.context.market,
                q.invocation.generation_id,
                q.invocation.source_generation_id,
            ) != self._scope[1:4]:
                raise ValueError("PARENT_INVOCATION_GENERATION_MISMATCH")
            if q.invocation.execution_purpose != "OFFLINE_CONTRACT_REPROOF":
                raise ValueError("PARENT_OFFLINE_SCOPE_ONLY")
            expected = ParentInvocationBinding(
                invocation_id=q.invocation.invocation_id,
                security_id=q.invocation.security_id,
                request_sha256=q.invocation.request_sha256,
                admission_bundle_sha256=digest(invocation._registry.bundle.model_dump(mode="json")),
                source_envelope_sha256=invocation._registry.bundle.source_envelope_sha256,
            )
            if expected not in self._manifest.invocations:
                raise ValueError("PARENT_SNAPSHOT_ADMISSION_MEMBERSHIP_MISMATCH")
            prior_parent = getattr(invocation, "_native_parent_token", None)
            if prior_parent is not None and prior_parent is not self._token:
                raise ValueError("INVOCATION_BOUND_TO_ANOTHER_PARENT")
            old = self._invocations.get(q.invocation.invocation_id)
            if old is not None and old is not invocation:
                raise ValueError("PARENT_INVOCATION_CAPABILITY_REPLACEMENT")
            self._invocations[q.invocation.invocation_id] = invocation
            invocation._native_parent_token = self._token

    def invocation(self, invocation_id):
        if self._closed or invocation_id not in self._invocations:
            raise ValueError("UNISSUED_PARENT_INVOCATION")
        invocation = self._invocations[invocation_id]
        if getattr(invocation, "_native_parent_token", None) is not self._token:
            raise ValueError("INVOCATION_BOUND_TO_ANOTHER_PARENT")
        return invocation

    def begin(self, invocation_id, *, model="OFFLINE_FIXTURE", effort="OFFLINE"):
        with self._lock:
            inv = self.invocation(invocation_id)
            from app.services.reported_economic_claim_consumer import is_reported_property_policy

            if isinstance(inv.request, ReportedEconomicRequest):
                handle = self._registry.begin_reported_context(inv)
            elif is_reported_property_policy(inv._policy):
                handle = self._registry.begin_reported_claim(inv)
            elif isinstance(inv.request, ClaimEconomicRequest):
                handle = self._registry.begin_claims(inv, model=model, effort=effort)
            else:
                handle = self._registry.begin(inv, model=model, effort=effort)
            self._attempts[handle] = inv
            return handle

    def complete(self, handle, raw_response=None):
        with self._lock:
            if self._closed or handle not in self._attempts:
                raise ValueError("UNISSUED_OR_CLOSED_PARENT_ATTEMPT")
            if isinstance(self._attempts[handle].request, ReportedEconomicRequest):
                if raw_response is not None:
                    raise ValueError("CONTEXT_DOES_NOT_ACCEPT_MODEL_OUTPUT")
                return self._registry.complete_reported_context(handle)
            from app.services.reported_economic_claim_consumer import is_reported_property_policy

            if is_reported_property_policy(self._attempts[handle]._policy):
                return self._registry.complete_reported_claim(handle, raw_response)
            return self._registry.complete(handle, raw_response)

    def reported_economic_claim(self, invocation_id, receipt, packet):
        from app.services.reported_economic_claim_consumer import consume_native_reported_economic_claim

        return consume_native_reported_economic_claim(self, invocation_id, receipt, packet)

    def context_prompt(self, invocation_id, receipt):
        from app.services.accepted_decision_v2_runtime_service import (
            accepted_v2_fundamental_core_prompt,
        )

        inv = self.invocation(invocation_id)
        return accepted_v2_fundamental_core_prompt(
            inv.request,
            backend_invocation=inv,
            context_ownership=receipt,
            ownership_registry=self._registry,
        )

    def economic_candidate(self, invocation_id, receipt, candidate):
        inv = self.invocation(invocation_id)
        return self._registry.resolve(
            receipt, invocation=inv, candidate=candidate, allow_offline_reproof=True
        )

    def bind_packet(self, invocation_id, receipt, candidate, packet):
        return self._registry.bind_downstream_packet(
            receipt,
            invocation=self.invocation(invocation_id),
            candidate=candidate,
            packet=packet,
            allow_offline_reproof=True,
        )

    def verify_packet(self, invocation_id, receipt, candidate, packet):
        return self._registry.verify_downstream_packet(
            receipt,
            invocation=self.invocation(invocation_id),
            candidate=candidate,
            packet=packet,
            allow_offline_reproof=True,
        )

    def revoke(self, receipt):
        if self._closed:
            raise ValueError("PARENT_LIFETIME_CLOSED")
        self._registry.revoke(receipt)

    def cancel(self, handle):
        with self._lock:
            if self._closed or handle not in self._attempts:
                raise ValueError("UNISSUED_OR_CLOSED_PARENT_ATTEMPT")
            self._registry.cancel_pending(handle)

    def close(self):
        with self._lock:
            for handle in self._attempts:
                try:
                    self._registry.cancel_pending(handle)
                except ValueError as error:
                    if str(error) != "ONLY_PENDING_ATTEMPT_CAN_BE_CANCELLED":
                        raise
            self._closed = True
            self._attempts.clear()
            self._invocations.clear()
