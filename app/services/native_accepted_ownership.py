"""Backend-held issuance for the opt-in native economic boundary.

The registry and response recorder are backend capabilities, not request payloads.
No public receipt fields authorize an output without the matching live registry.
Offline transport proofs remain distinguishable from executed model judgments.
"""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import secrets
from threading import RLock
from typing import Literal

from pydantic import Field

from app.services.native_input_admission import Closed, Identity, SHA
from app.services.native_economic_core import (
    BackendInvocation,
    decode_model_candidate,
    decode_bound_candidate,
    accept_economic_candidate,
    materialize_economic_candidate,
)
from app.services.unified_snapshot_contract import digest


class AcceptedOwnership(Closed):
    contract: Literal["backend-accepted-economic-ownership-v1"] = (
        "backend-accepted-economic-ownership-v1"
    )
    accepted_output_id: Identity
    request_sha: SHA
    prompt_sha: SHA
    schema_sha: SHA
    invocation_sha: SHA
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    model: Identity
    effort: Identity
    attempt_id: Identity
    attempt_number: int = Field(ge=1)
    raw_response_sha: SHA
    validated_candidate_sha: SHA
    semantic_validation_sha: SHA
    authority_validation_sha: SHA
    policy_sha: SHA
    validator_sha: SHA
    accepted_at: datetime
    accepted_owner: Literal["BACKEND_MODEL_RUNTIME", "OFFLINE_VALIDATION_REPROOF"]
    provenance: Literal["MODEL_TRANSPORT", "OFFLINE_TRANSPORT_FIXTURE"]


class _AttemptHandle:
    """Object identity, not its printable ID, is the recording capability."""

    __slots__ = ()


class ReportedSourceBinding(Closed):
    owner_contract: Identity
    owner_sha256: SHA
    fact_admission_sha256: tuple[SHA, ...] = Field(min_length=1)
    raw_source_sha256: tuple[SHA, ...] = Field(min_length=1)
    economic_policy_version: Identity
    interpretation_result_sha256: SHA
    consumer: Identity
    use_axis: Identity


class FactBoundAcceptedOwnership(AcceptedOwnership):
    contract: Literal["backend-accepted-economic-ownership-fact-v2"] = (
        "backend-accepted-economic-ownership-fact-v2"
    )
    reported_source_binding: ReportedSourceBinding


class ClaimBoundAcceptedOwnership(AcceptedOwnership):
    contract: Literal["backend-accepted-qualified-claim-ownership-v2"] = "backend-accepted-qualified-claim-ownership-v2"
    claim_policy_sha256: SHA
    claim_eligibility_sha256: tuple[SHA, ...] = Field(min_length=4)


class ReportedContextOwnership(Closed):
    """Backend-issued input ownership, deliberately not AcceptedOwnership."""
    contract: Literal["backend-reported-context-ownership-fact-v2"] = "backend-reported-context-ownership-fact-v2"
    context_output_id: Identity
    request_sha: SHA
    prompt_sha: SHA
    schema_sha: SHA
    invocation_sha: SHA
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    policy_sha: tuple[SHA, ...]
    grant_sha: tuple[SHA, ...]
    source_owner_sha: tuple[SHA, ...]
    supporting_fact_sha: tuple[SHA, ...]
    packet_sha: SHA
    attempt_id: Identity
    attempt_number: int = Field(ge=1)
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_REPORTED_CONTEXT"] = "CORE_REPORTED_CONTEXT"
    provenance: Literal["REAL_OR_SYNTHETIC_SEALED_FACT_CONTEXT_OFFLINE"] = "REAL_OR_SYNTHETIC_SEALED_FACT_CONTEXT_OFFLINE"
    accepted_model_judgment: Literal[False] = False


def _decode_receipt(raw):
    value = json.loads(raw)
    kind = {"backend-accepted-economic-ownership-fact-v2": FactBoundAcceptedOwnership,
            "backend-accepted-qualified-claim-ownership-v2": ClaimBoundAcceptedOwnership}.get(value.get("contract"), AcceptedOwnership)
    return kind.model_validate(value)


class BackendOwnershipRegistry:
    """Per-run in-memory backend ledger; never hydrated from caller JSON.

    A single active accepted attempt exists per invocation. Starting a retry
    revokes the previous accepted attempt. Identical completion of the current
    accepted attempt is idempotent; rejected or superseded attempts stay closed.
    Production wiring/dispatch is deliberately absent. Losing this registry
    invalidates all of its receipts (no caller reconstruction or DB fallback).
    """

    def __init__(self, *, offline_reproof: bool = True):
        if type(offline_reproof) is not bool:
            raise ValueError("EXPLICIT_BACKEND_EXECUTION_MODE_REQUIRED")
        self._offline = offline_reproof
        self._attempts = {}
        self._current = {}
        self._accepted = {}
        self._downstream_packets = {}
        self._context_attempts = {}
        self._context_current = {}
        self._context_issued = {}
        self._reported_claim_issued = {}
        self._reported_role_requests = {}
        self._invocation_routes = {}
        self._lock = RLock()

    def _pin_invocation_route(self, request, route):
        key = request.invocation.invocation_id
        binding = (route, request.invocation.request_sha256)
        previous = self._invocation_routes.get(key)
        if previous is not None and previous != binding:
            raise ValueError("INVOCATION_ROUTE_OR_REQUEST_REUSE_FORBIDDEN")
        self._invocation_routes[key] = binding

    def begin(self, invocation: BackendInvocation, *, model: str, effort: str):
        from app.services.native_economic_core import ClaimEconomicRequest

        if isinstance(invocation, BackendInvocation) and isinstance(invocation.request, ClaimEconomicRequest):
            raise ValueError("QUALIFIED_CLAIM_V2_ROUTE_REQUIRED_NOT_V1")
        return self._begin(invocation, model=model, effort=effort, route="ECONOMIC_RESULT")

    def begin_claims(self, invocation, *, model, effort):
        from app.services.native_economic_core import ClaimEconomicRequest
        from app.services.economic_claim_qualification import BackendQualifiedEconomicPolicy

        if not self._offline:
            raise ValueError("QUALIFIED_CLAIM_OFFLINE_ONLY")
        if (not isinstance(invocation, BackendInvocation) or not isinstance(invocation.request, ClaimEconomicRequest)
                or not isinstance(invocation._policy, BackendQualifiedEconomicPolicy)):
            raise ValueError("QUALIFIED_CLAIM_INVOCATION_REQUIRED")
        return self._begin(invocation, model=model, effort=effort, route="QUALIFIED_CLAIM_V2")

    def _begin(self, invocation, *, model, effort, route):
        if not isinstance(invocation, BackendInvocation):
            raise ValueError("BACKEND_INVOCATION_REQUIRED")
        request = invocation.verify(invocation.request)
        if any(m.owner_contract in {
            "real-economic-property-owner-v1", "real-narrative-risk-property-owner-v1",
            "real-balanced-synthesis-property-owner-v1",
        } for m in invocation._registry.bundle.metrics):
            if route != "REPORTED_ECONOMIC_CLAIM_FACT_V2":
                raise ValueError("REPORTED_FACT_ECONOMIC_V2_ROUTE_REQUIRED")
        from app.services.native_economic_core import ReportedEconomicRequest

        if isinstance(request, ReportedEconomicRequest):
            raise ValueError("FACT_V2_CONTEXT_ROUTE_REQUIRED_NOT_ECONOMIC_V1")
        expected = "OFFLINE_CONTRACT_REPROOF" if self._offline else "ACCEPTED_CORE_MODEL_REPROOF"
        if request.invocation.execution_purpose != expected:
            raise ValueError("EXECUTION_PURPOSE_PROVENANCE_MISMATCH")
        # Reuse the closed identity type for backend-selected transport settings.
        from pydantic import TypeAdapter

        TypeAdapter(Identity).validate_python(model)
        TypeAdapter(Identity).validate_python(effort)
        key = request.invocation.invocation_id
        with self._lock:
            self._pin_invocation_route(request, route)
            previous = self._current.get(key)
            number = 1
            if previous is not None:
                old = self._attempts[previous]
                if old["request"] != request.model_dump_json():
                    raise ValueError("INVOCATION_REUSE_WITH_CHANGED_REQUEST")
                number = old["number"] + 1
                old["status"] = "SUPERSEDED"
            handle = _AttemptHandle()
            self._attempts[handle] = dict(
                invocation=invocation, request=request.model_dump_json(), key=key,
                model=model, effort=effort, number=number, status="PENDING",
                raw_sha=None, accepted=None, attempt_id=secrets.token_hex(24), fact_owner=None,
                interpretation=None, source_binding=None,
                route=route,
            )
            self._current[key] = handle
            return handle

    def begin_reported_claim(self, invocation):
        from app.services.reported_economic_claim_consumer import reported_role_request, is_reported_property_policy

        if not self._offline or not is_reported_property_policy(invocation._policy):
            raise ValueError("OFFLINE_REPORTED_PROPERTY_CLAIM_REQUIRED")
        invocation._policy.verify_backend(invocation._registry)
        with self._lock:
            role_request=reported_role_request(invocation)
            key=invocation.request.invocation.invocation_id
            previous=self._reported_role_requests.get(key)
            if previous is not None and previous != role_request.model_dump_json():
                raise ValueError("REPORTED_ROLE_REQUEST_RETRY_IDENTITY_CHANGED")
            handle=self._begin(invocation,model="OFFLINE_ROLE_FIXTURE",effort="OFFLINE",
                               route="REPORTED_ECONOMIC_CLAIM_FACT_V2")
            self._reported_role_requests[key]=role_request.model_dump_json()
            self._attempts[handle]["role_request"]=role_request.model_dump_json()
            return handle

    def complete_reported_claim(self, handle, raw_response):
        from app.services.reported_economic_claim_consumer import (
            ReportedRoleCandidate, validate_reported_role, reported_role_request, role_types,
        )
        if type(raw_response) is not bytes:
            raise ValueError("EXACT_TRANSPORT_BYTES_REQUIRED")
        with self._lock:
            row=self._attempts.get(handle)
            if row is None or row["route"] != "REPORTED_ECONOMIC_CLAIM_FACT_V2":
                raise ValueError("UNISSUED_REPORTED_CLAIM_ATTEMPT")
            if self._current.get(row["key"]) is not handle or row["status"] == "SUPERSEDED":
                raise ValueError("SUPERSEDED_REPORTED_CLAIM_ATTEMPT")
            inv=row["invocation"]
            _, _, receipt_type = role_types(inv._policy)
            inv.verify(inv.request)
            if reported_role_request(inv).model_dump_json() != row["role_request"]:
                raise ValueError("REPORTED_ROLE_REQUEST_CHANGED")
            raw_sha=hashlib.sha256(raw_response).hexdigest()
            if row["status"] == "ISSUED_ROLE":
                if row["raw_sha"] != raw_sha:
                    raise ValueError("REPORTED_CLAIM_RESPONSE_CONFLICT")
                return receipt_type.model_validate_json(row["role_receipt"])
            if row["status"] != "PENDING":
                raise ValueError("CLOSED_REPORTED_CLAIM_ATTEMPT")
            try:
                packet=validate_reported_role(ReportedRoleCandidate.model_validate_json(raw_response),invocation=inv)
                receipt=receipt_type(output_id=secrets.token_hex(24),
                    request_sha256=packet.request_sha256,invocation_sha256=packet.invocation_sha256,
                    property_admission_sha256=packet.property_admission_sha256,
                    claim_eligibility_sha256=packet.claim_eligibility_sha256,
                    packet_sha256=digest(packet.model_dump(mode="json")),role_schema_sha256=packet.role_schema_sha256,
                    role_request_sha256=packet.role_request_sha256,
                    raw_response_sha256=raw_sha,attempt_id=row["attempt_id"],attempt_number=row["number"],
                    security_id=packet.security_id,generation_id=packet.generation_id,source_generation_id=packet.source_generation_id)
            except Exception:
                row["status"]="REJECTED"
                raise
            row.update(status="ISSUED_ROLE",raw_sha=raw_sha,role_receipt=receipt.model_dump_json(),role_packet=packet.model_dump_json())
            self._reported_claim_issued[receipt.output_id]=handle
            return receipt

    def reported_claim_packet(self, receipt, *, invocation):
        from app.services.reported_economic_claim_consumer import reported_role_request, role_types

        _, packet_type, receipt_type = role_types(invocation._policy)
        if type(receipt) is not receipt_type:
            raise ValueError("REPORTED_ECONOMIC_FACT_V2_RECEIPT_REQUIRED")
        with self._lock:
            handle=self._reported_claim_issued.get(receipt.output_id)
            if handle is None:
                raise ValueError("UNISSUED_REPORTED_ECONOMIC_CLAIM")
            row=self._attempts[handle]
            if row["status"] != "ISSUED_ROLE" or self._current.get(row["key"]) is not handle:
                raise ValueError("REVOKED_OR_SUPERSEDED_REPORTED_CLAIM")
            if row["invocation"] is not invocation or row["role_receipt"] != receipt.model_dump_json():
                raise ValueError("REPORTED_CLAIM_RECEIPT_INVOCATION_MISMATCH")
            if reported_role_request(invocation).model_dump_json() != row["role_request"]:
                raise ValueError("REPORTED_ROLE_REQUEST_CHANGED")
            return packet_type.model_validate_json(row["role_packet"])

    def consume_reported_claim(self, receipt, *, invocation, packet):
        from app.services.reported_economic_claim_consumer import ReportedEconomicClaimPacket, validate_reported_role

        with self._lock:
            expected=self.reported_claim_packet(receipt,invocation=invocation)
            if not isinstance(packet, ReportedEconomicClaimPacket) or packet != expected:
                raise ValueError("REPORTED_CLAIM_PACKET_BINDING_MISMATCH")
            checked=validate_reported_role(packet.candidate,invocation=invocation)
            if checked != expected or digest(checked.model_dump(mode="json")) != receipt.packet_sha256:
                raise ValueError("REPORTED_CLAIM_PROPERTY_OR_PACKET_CHANGED")
            return checked

    def begin_reported_context(self, invocation):
        from app.services.native_economic_core import ReportedEconomicRequest

        if not isinstance(invocation, BackendInvocation) or not self._offline:
            raise ValueError("OFFLINE_BACKEND_CONTEXT_INVOCATION_REQUIRED")
        request = invocation.verify(invocation.request)
        if not isinstance(request, ReportedEconomicRequest) or request.invocation.execution_purpose != "OFFLINE_CONTRACT_REPROOF":
            raise ValueError("FACT_V2_CONTEXT_REQUEST_REQUIRED")
        key = request.invocation.invocation_id
        with self._lock:
            self._pin_invocation_route(request, "REPORTED_CONTEXT_FACT_V2")
            prior = self._context_current.get(key)
            number = 1
            if prior is not None:
                previous = self._context_attempts[prior]
                if previous["request"] != request.model_dump_json():
                    raise ValueError("INVOCATION_REUSE_WITH_CHANGED_REQUEST")
                previous["status"] = "SUPERSEDED"
                number = previous["number"] + 1
            handle = _AttemptHandle()
            self._context_attempts[handle] = dict(invocation=invocation, request=request.model_dump_json(),
                key=key, number=number, attempt_id=secrets.token_hex(24), status="PENDING", receipt=None)
            self._context_current[key] = handle
            return handle

    def complete_reported_context(self, handle):
        """No caller payload or claimed validation result participates in issuance."""
        with self._lock:
            row = self._context_attempts.get(handle)
            if row is None:
                raise ValueError("UNISSUED_CONTEXT_ATTEMPT")
            if self._context_current.get(row["key"]) is not handle or row["status"] == "SUPERSEDED":
                raise ValueError("SUPERSEDED_CONTEXT_ATTEMPT")
            if row["status"] == "ISSUED":
                return ReportedContextOwnership.model_validate_json(row["receipt"])
            if row["status"] != "PENDING":
                raise ValueError("CLOSED_CONTEXT_ATTEMPT")
            try:
                request = row["invocation"].verify(row["invocation"].request)
                if request.model_dump_json() != row["request"]:
                    raise ValueError("CONTEXT_REQUEST_CHANGED")
                s = request.invocation
                grants = request.reported_contexts
                receipt = ReportedContextOwnership(context_output_id=secrets.token_hex(32),
                    request_sha=s.request_sha256, prompt_sha=s.prompt_sha256, schema_sha=s.schema_sha256,
                    invocation_sha=s.invocation_scope_sha256, security_id=s.security_id,
                    generation_id=s.generation_id, source_generation_id=s.source_generation_id,
                    policy_sha=tuple(g.policy_sha256 for g in grants), grant_sha=tuple(g.grant_sha256 for g in grants),
                    source_owner_sha=tuple(g.comparison.source_owner_sha256 for g in grants),
                    supporting_fact_sha=tuple(sha for g in grants for sha in g.comparison.supporting_admission_sha256),
                    packet_sha=digest(request.model_dump(mode="json")),
                    attempt_id=row["attempt_id"], attempt_number=row["number"])
            except Exception:
                row["status"] = "REJECTED"
                raise
            row.update(status="ISSUED", receipt=receipt.model_dump_json())
            self._context_issued[receipt.context_output_id] = handle
            return receipt

    def consume_reported_context(self, receipt, *, invocation, request):
        """Native prompt boundary: exact live ledger AND current owner/use binding."""
        if not isinstance(receipt, ReportedContextOwnership):
            raise ValueError("FACT_V2_CONTEXT_OWNERSHIP_REQUIRED")
        with self._lock:
            handle = self._context_issued.get(receipt.context_output_id)
            if handle is None:
                raise ValueError("UNISSUED_CONTEXT_OWNERSHIP")
            row = self._context_attempts[handle]
            if self._context_current.get(row["key"]) is not handle or row["status"] != "ISSUED":
                raise ValueError("STALE_REVOKED_OR_SUPERSEDED_CONTEXT")
            if row["receipt"] != receipt.model_dump_json() or invocation is not row["invocation"]:
                raise ValueError("CONTEXT_OWNERSHIP_INVOCATION_MISMATCH")
            checked = invocation.verify(request)
            if checked.model_dump_json() != row["request"] or digest(checked.model_dump(mode="json")) != receipt.packet_sha:
                raise ValueError("CONTEXT_PACKET_BINDING_MISMATCH")
            return checked.prompt

    def begin_with_reported_interpretation(self, invocation, *, model, effort, fact_owner,
                                          interpretation, use_axis):
        """Explicit v2 entry, with owner/use qualification before attempt issuance.

        Current comparison-only policy cannot authorize a Core directional use.
        It must remain a gap rather than silently using the old unbound path.
        """
        from app.services.reported_fact_owner import BackendReportedFactOwner, CONTRACT

        if not isinstance(fact_owner, BackendReportedFactOwner):
            raise ValueError("BACKEND_REPORTED_FACT_OWNER_REQUIRED")
        scope = invocation.verify(invocation.request).invocation
        if use_axis not in {a.value for a in scope.allowed_use_axes}:
            raise ValueError("FACT_INVOCATION_USE_SCOPE_MISMATCH")
        facts = fact_owner.authorize_interpretation(interpretation, axis=use_axis,
            security_id=scope.security_id, execution_generation_id=scope.generation_id,
            source_generation_id=scope.source_generation_id)
        binding = ReportedSourceBinding(owner_contract=CONTRACT,
            owner_sha256=interpretation.source_owner_sha256,
            fact_admission_sha256=interpretation.supporting_admission_sha256,
            raw_source_sha256=tuple(sorted({f.raw_source_sha256 for f in facts})),
            economic_policy_version=interpretation.policy_version,
            interpretation_result_sha256=interpretation.interpretation_sha256,
            consumer=scope.intended_consumer.value, use_axis=use_axis)
        with self._lock:
            handle = self.begin(invocation, model=model, effort=effort)
            self._attempts[handle].update(fact_owner=fact_owner, interpretation=interpretation,
                                          source_binding=binding.model_dump_json())
            return handle

    def _verify_reported_source(self, row, scope):
        if row["source_binding"] is None:
            return None
        binding = ReportedSourceBinding.model_validate_json(row["source_binding"])
        result = row["interpretation"]
        row["fact_owner"].authorize_interpretation(result, axis=binding.use_axis,
            security_id=scope.security_id, execution_generation_id=scope.generation_id,
            source_generation_id=scope.source_generation_id)
        if (result.interpretation_sha256 != binding.interpretation_result_sha256
                or result.policy_version != binding.economic_policy_version
                or scope.intended_consumer.value != binding.consumer
                or binding.use_axis not in {a.value for a in scope.allowed_use_axes}):
            raise ValueError("REPORTED_SOURCE_POLICY_BINDING_MISMATCH")
        return binding

    def complete(self, handle, raw_response: bytes) -> AcceptedOwnership:
        """Called by trusted transport composition, never by model JSON.

        Validation hashes are computed here after the native AND path executes.
        There is no caller-supplied 'validated', owner, provenance or hash input.
        """
        if type(raw_response) is not bytes:
            raise ValueError("EXACT_TRANSPORT_BYTES_REQUIRED")
        if not isinstance(handle, _AttemptHandle):
            raise ValueError("UNISSUED_ATTEMPT_CAPABILITY")
        with self._lock:
            row = self._attempts.get(handle)
            if row is None:
                raise ValueError("UNISSUED_ATTEMPT_CAPABILITY")
            if row["route"] == "REPORTED_ECONOMIC_CLAIM_FACT_V2":
                raise ValueError("ROLE_ELIGIBILITY_IS_NOT_COMPLETE_ECONOMIC_OUTPUT")
            if self._current.get(row["key"]) is not handle or row["status"] == "SUPERSEDED":
                raise ValueError("SUPERSEDED_ATTEMPT")
            raw_sha = hashlib.sha256(raw_response).hexdigest()
            if row["status"] == "ACCEPTED":
                if row["raw_sha"] != raw_sha:
                    raise ValueError("ACCEPTED_ATTEMPT_RESPONSE_CONFLICT")
                return _decode_receipt(row["accepted"])
            if row["status"] != "PENDING":
                raise ValueError("CLOSED_REJECTED_ATTEMPT")
            row["raw_sha"] = raw_sha
            try:
                invocation = row["invocation"]
                request = invocation.verify(invocation.request)
                if request.model_dump_json() != row["request"]:
                    raise ValueError("PINNED_REQUEST_CHANGED")
                value = decode_model_candidate(json.loads(raw_response))
                bound = materialize_economic_candidate(
                    value.model_dump(mode="json"), request, invocation=invocation
                )
                validated = accept_economic_candidate(bound, request, invocation=invocation)
                scope = request.invocation
                source_binding = self._verify_reported_source(row, scope)
                claim_receipts = ()
                if row["route"] == "QUALIFIED_CLAIM_V2":
                    claim_receipts = invocation._policy.validate_model(value, request=request, invocation=invocation)
                candidate = validated.candidate.model_dump(mode="json")
                candidate_sha = digest(candidate)
                semantic = digest(dict(candidate_sha=candidate_sha, policy_sha=scope.policy_sha256,
                                       validator_sha=scope.validator_sha256, result="PASS"))
                authority = digest(dict(references=validated.reference_output.model_dump(mode="json"),
                    invocation_sha=scope.invocation_scope_sha256, authority_sha=scope.authority_sha256,
                    validator_sha=scope.validator_sha256, result="PASS"))
                receipt_type = ClaimBoundAcceptedOwnership if claim_receipts else FactBoundAcceptedOwnership if source_binding else AcceptedOwnership
                receipt = receipt_type(
                    accepted_output_id=secrets.token_hex(32), request_sha=scope.request_sha256,
                    prompt_sha=scope.prompt_sha256, schema_sha=scope.schema_sha256,
                    invocation_sha=scope.invocation_scope_sha256, security_id=scope.security_id,
                    generation_id=scope.generation_id, source_generation_id=scope.source_generation_id,
                    model=row["model"], effort=row["effort"], attempt_id=row["attempt_id"],
                    attempt_number=row["number"], raw_response_sha=raw_sha,
                    validated_candidate_sha=candidate_sha, semantic_validation_sha=semantic,
                    authority_validation_sha=authority, policy_sha=scope.policy_sha256,
                    validator_sha=scope.validator_sha256, accepted_at=datetime.now(UTC),
                    accepted_owner="OFFLINE_VALIDATION_REPROOF" if self._offline else "BACKEND_MODEL_RUNTIME",
                    provenance="OFFLINE_TRANSPORT_FIXTURE" if self._offline else "MODEL_TRANSPORT",
                    **({"reported_source_binding":source_binding} if source_binding else {}),
                    **({"claim_policy_sha256":invocation._policy.bundle.rule_sha256,
                        "claim_eligibility_sha256":tuple(digest(r.model_dump(mode="json")) for r in claim_receipts)} if claim_receipts else {}),
                )
            except Exception:
                row["status"] = "REJECTED"
                raise
            row.update(status="ACCEPTED", accepted=receipt.model_dump_json(), candidate=candidate,
                       bound=bound.model_dump_json())
            self._accepted[receipt.accepted_output_id] = handle
            return receipt

    def resolve(self, receipt, *, invocation, candidate, allow_offline_reproof=False):
        """The versioned downstream gate checks issuance AND current native validation."""
        if type(allow_offline_reproof) is not bool:
            raise ValueError("EXPLICIT_REPROOF_MODE_REQUIRED")
        if not isinstance(receipt, AcceptedOwnership):
            raise ValueError("BACKEND_ISSUED_OWNERSHIP_REQUIRED")
        receipt = _decode_receipt(receipt.model_dump_json())
        with self._lock:
            handle = self._accepted.get(receipt.accepted_output_id)
            if handle is None:
                raise ValueError("UNISSUED_ACCEPTED_OUTPUT")
            row = self._attempts[handle]
            if row["status"] != "ACCEPTED" or self._current.get(row["key"]) is not handle:
                raise ValueError("STALE_OR_SUPERSEDED_ACCEPTED_OUTPUT")
            if receipt.model_dump_json() != row["accepted"]:
                raise ValueError("ISSUED_OWNERSHIP_BINDING_MISMATCH")
            if receipt.provenance != "MODEL_TRANSPORT" and not allow_offline_reproof:
                raise ValueError("TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT")
            if invocation is not row["invocation"]:
                raise ValueError("BACKEND_INVOCATION_CAPABILITY_MISMATCH")
            request = invocation.verify(invocation.request)
            self._verify_reported_source(row, request.invocation)
            if request.model_dump_json() != row["request"]:
                raise ValueError("ISSUED_REQUEST_BINDING_MISMATCH")
            if not hasattr(candidate, "model_dump") or candidate.model_dump(mode="json") != row["candidate"]:
                raise ValueError("ISSUED_CANDIDATE_BINDING_MISMATCH")
            # Revalidate through current semantics, membership, axis, identity and time.
            result = accept_economic_candidate(
                decode_bound_candidate(json.loads(row["bound"])), request, invocation=invocation
            )
            if digest(result.candidate.model_dump(mode="json")) != receipt.validated_candidate_sha:
                raise ValueError("VALIDATED_CANDIDATE_HASH_MISMATCH")
            return result.candidate

    def attempt_states(self):
        with self._lock:
            return tuple(dict(attempt_id=r["attempt_id"], attempt_number=r["number"], status=r["status"])
                         for r in self._attempts.values())

    def cancel_pending(self, handle):
        with self._lock:
            row = self._attempts.get(handle) or self._context_attempts.get(handle)
            if row is None:
                raise ValueError("UNISSUED_ATTEMPT_CAPABILITY")
            if row["status"] != "PENDING":
                raise ValueError("ONLY_PENDING_ATTEMPT_CAN_BE_CANCELLED")
            row["status"] = "CANCELLED"

    def revoke(self, receipt):
        """Trusted backend revocation is permanent for this accepted attempt."""
        from app.services.reported_economic_claim_consumer import ReportedEconomicClaimOwnership

        if isinstance(receipt, ReportedEconomicClaimOwnership):
            with self._lock:
                handle = self._reported_claim_issued.get(receipt.output_id)
                if handle is None or self._attempts[handle]["role_receipt"] != receipt.model_dump_json():
                    raise ValueError("UNISSUED_REPORTED_ECONOMIC_CLAIM")
                self._attempts[handle]["status"] = "REVOKED"
            return
        if isinstance(receipt, ReportedContextOwnership):
            with self._lock:
                handle = self._context_issued.get(receipt.context_output_id)
                if handle is None or self._context_attempts[handle]["receipt"] != receipt.model_dump_json():
                    raise ValueError("UNISSUED_CONTEXT_OWNERSHIP")
                self._context_attempts[handle]["status"] = "REVOKED"
            return
        if not isinstance(receipt, AcceptedOwnership):
            raise ValueError("BACKEND_ISSUED_OWNERSHIP_REQUIRED")
        with self._lock:
            handle = self._accepted.get(receipt.accepted_output_id)
            if handle is None or self._attempts[handle]["accepted"] != receipt.model_dump_json():
                raise ValueError("UNISSUED_ACCEPTED_OUTPUT")
            self._attempts[handle]["status"] = "REVOKED"

    def bind_downstream_packet(self, receipt, *, invocation, candidate, packet,
                               allow_offline_reproof=False):
        """Backend composition pins a packet once; consumers can only verify it."""
        from app.services.cross_market_decision_engine_service import DecisionEvidencePacket

        with self._lock:
            self.resolve(receipt, invocation=invocation, candidate=candidate,
                         allow_offline_reproof=allow_offline_reproof)
            if not isinstance(packet, DecisionEvidencePacket):
                raise ValueError("TYPED_DOWNSTREAM_PACKET_REQUIRED")
            scope = invocation.request.invocation
            if packet.ticker != candidate.ticker:
                raise ValueError("DOWNSTREAM_PACKET_SECURITY_MISMATCH")
            binding = dict(accepted_output_id=receipt.accepted_output_id,
                invocation_sha=scope.invocation_scope_sha256, security_id=scope.security_id,
                generation_id=scope.generation_id, source_generation_id=scope.source_generation_id,
                packet_id=packet.packet_id, packet_sha=digest(packet.model_dump(mode="json")),
                provenance=receipt.provenance)
            if isinstance(receipt, FactBoundAcceptedOwnership):
                binding["reported_source_binding_sha256"] = digest(receipt.reported_source_binding.model_dump(mode="json"))
            prior = self._downstream_packets.get(receipt.accepted_output_id)
            if prior is not None and prior != binding:
                raise ValueError("DOWNSTREAM_PACKET_REBIND_FORBIDDEN")
            self._downstream_packets[receipt.accepted_output_id] = binding
            return dict(binding)

    def verify_downstream_packet(self, receipt, *, invocation, candidate, packet,
                                 allow_offline_reproof=False):
        with self._lock:
            self.resolve(receipt, invocation=invocation, candidate=candidate,
                         allow_offline_reproof=allow_offline_reproof)
            binding = self._downstream_packets.get(receipt.accepted_output_id)
            if binding is None:
                raise ValueError("UNISSUED_DOWNSTREAM_PACKET_BINDING")
            if (packet.packet_id != binding["packet_id"]
                    or digest(packet.model_dump(mode="json")) != binding["packet_sha"]):
                raise ValueError("DOWNSTREAM_PACKET_IDENTITY_GENERATION_MISMATCH")
            return dict(binding)
