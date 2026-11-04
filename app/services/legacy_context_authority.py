"""Process-owned integrity for a built legacy context, not source admission."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict


class LegacyContextSeal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["legacy-context-projection-seal-v1"] = (
        "legacy-context-projection-seal-v1"
    )
    owner_lifetime: str
    scope: Literal["CORE_CONTEXT", "OWNED_EVIDENCE"]
    payload_sha256: str
    signature: str


_OWNER_LIFETIME = secrets.token_hex(16)
_SIGNING_KEY = secrets.token_bytes(32)
_OWNER_PID = os.getpid()
# Opaque capabilities held by the two validated builders, never wire values.
_CORE_BUILDER_PERMIT = object()
_OWNED_BUILDER_PERMIT = object()


def _require_owner_process() -> None:
    if os.getpid() != _OWNER_PID:
        raise ValueError("legacy_context_owner_process_mismatch")


def _payload_identity(context: BaseModel) -> str:
    payload = context.model_dump(mode="json", exclude={"backend_seal"})
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode()).hexdigest()


def _signature(identity: str, scope: str) -> str:
    message = f"legacy-context-projection-seal-v1:{_OWNER_LIFETIME}:{scope}:{identity}"
    return hmac.new(_SIGNING_KEY, message.encode(), hashlib.sha256).hexdigest()


def _seal_built_context(context, *, scope="CORE_CONTEXT", _permit=None):
    """Called only after the backend builder has derived exact ref ownership."""
    _require_owner_process()
    from app.services.fixture_context_authority import contains_fixture_provenance
    from app.services.owned_evidence_derivative import OwnedEvidenceDerivativeSeal

    if isinstance(getattr(context, "backend_seal", None), OwnedEvidenceDerivativeSeal):
        raise ValueError("owned_derivative_reseal_forbidden")
    if contains_fixture_provenance(context):
        raise ValueError("test_only_fixture_not_production_authority")
    expected = {"CORE_CONTEXT": _CORE_BUILDER_PERMIT,
                "OWNED_EVIDENCE": _OWNED_BUILDER_PERMIT}.get(scope)
    if expected is None or _permit is not expected:
        raise ValueError("legacy_context_backend_builder_permit_required")
    identity = _payload_identity(context)
    return context.model_copy(update={"backend_seal": LegacyContextSeal(
        owner_lifetime=_OWNER_LIFETIME,
        scope=scope,
        payload_sha256=identity,
        signature=_signature(identity, scope),
    )})


def verify_legacy_context(context: BaseModel, *, scope="CORE_CONTEXT", fixture_consumer=None) -> None:
    _require_owner_process()
    from app.services.fixture_context_authority import contains_fixture_provenance
    from app.services.owned_evidence_derivative import (
        OwnedEvidenceDerivativeSeal, verify_owned_derivative,
    )

    seal = getattr(context, "backend_seal", None)
    from app.services.reviewed_fixture_authority import (
        ReviewedFixtureSeal, verify_reviewed_owned_fixture,
    )
    if isinstance(seal, ReviewedFixtureSeal):
        if scope != seal.scope or fixture_consumer is None:
            raise ValueError("reviewed_fixture_consumer_forbidden")
        verify_reviewed_owned_fixture(context, consumer=fixture_consumer)
        return
    if contains_fixture_provenance(context):
        raise ValueError("test_only_fixture_not_production_authority")
    if isinstance(seal, OwnedEvidenceDerivativeSeal):
        verify_owned_derivative(context, scope=scope)
        return
    if not isinstance(seal, LegacyContextSeal):
        raise ValueError("legacy_context_backend_seal_required")
    identity = _payload_identity(context)
    if (seal.owner_lifetime != _OWNER_LIFETIME or seal.scope != scope
            or not hmac.compare_digest(seal.payload_sha256, identity)
            or not hmac.compare_digest(seal.signature, _signature(identity, scope))):
        raise ValueError("legacy_context_backend_seal_mismatch")
