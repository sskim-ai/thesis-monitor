"""Live, narrowing-only derivatives of an already verified owned projection.

This capability cannot admit a source, change time, or grant an economic use.
"""
from __future__ import annotations

import os
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OwnedEvidenceDerivativeSeal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract: Literal["owned-evidence-subset-derivative-v1"] = (
        "owned-evidence-subset-derivative-v1"
    )
    owner_lifetime: str
    receipt_id: str
    scope: Literal["OWNED_EVIDENCE"] = "OWNED_EVIDENCE"
    purpose: Literal["DENIED_USE_FILTER", "REQUEST_REF_RESTRICTION"]
    parent_payload_sha256: str
    payload_sha256: str
    retained_refs: tuple[str, ...]
    depth: int = Field(ge=1, le=16)


_PID = os.getpid()
_LIFETIME = secrets.token_hex(24)
_ISSUED: dict[str, tuple[OwnedEvidenceDerivativeSeal, BaseModel]] = {}
_ACTIVE: dict[tuple, str] = {}
_KEY_BY_ID: dict[str, tuple] = {}
_MAX_ISSUED = 4096


def _process() -> None:
    if os.getpid() != _PID:
        raise ValueError("owned_derivative_owner_process_mismatch")


def restrict_owned_evidence(parent, *, retained_refs, purpose):
    """Derive exact rows from a verified parent; no caller payload is signed."""
    from app.services.legacy_context_authority import (
        _payload_identity, verify_legacy_context,
    )

    _process()
    verify_legacy_context(parent, scope="OWNED_EVIDENCE")
    if len(_ISSUED) >= _MAX_ISSUED:
        raise ValueError("owned_derivative_registry_capacity")
    ancestor = parent.backend_seal
    depth = ancestor.depth + 1 if isinstance(ancestor, OwnedEvidenceDerivativeSeal) else 1
    if depth > 16:
        raise ValueError("owned_derivative_depth_limit")
    refs = tuple(retained_refs)
    if len(refs) != len(set(refs)):
        raise ValueError("owned_derivative_duplicate_ref")
    raw = parent.source_packet.evidence
    raw_ids = {row.ref_id for row in raw}
    owned_ids = {row.ref.ref_id for row in parent.evidence}
    if not set(refs).issubset(raw_ids & owned_ids):
        raise ValueError("owned_derivative_membership_expansion")
    # Construction preserves the producer's original ordering and every field.
    child = parent.model_copy(update={
        "source_packet": parent.source_packet.model_copy(update={
            "evidence": tuple(row for row in raw if row.ref_id in refs),
        }),
        "evidence": tuple(row for row in parent.evidence if row.ref.ref_id in refs),
        "backend_seal": None,
    })
    parent_sha = _payload_identity(parent)
    child_sha = _payload_identity(child)
    canonical_refs = tuple(row.ref.ref_id for row in child.evidence)
    key = (ancestor.model_dump_json(), parent_sha, purpose, canonical_refs, depth, child_sha)
    existing = _ISSUED.get(_ACTIVE.get(key))
    if existing is not None:
        restored = child.model_copy(update={"backend_seal": existing[0]})
        verify_owned_derivative(restored, scope="OWNED_EVIDENCE")
        return restored
    seal = OwnedEvidenceDerivativeSeal(
        owner_lifetime=_LIFETIME,
        receipt_id=secrets.token_hex(32),
        purpose=purpose,
        parent_payload_sha256=parent_sha,
        payload_sha256=child_sha,
        retained_refs=canonical_refs,
        depth=depth,
    )
    _ISSUED[seal.receipt_id] = (seal, parent.model_copy(deep=True))
    _ACTIVE[key] = seal.receipt_id
    _KEY_BY_ID[seal.receipt_id] = key
    return child.model_copy(update={"backend_seal": seal})


def verify_owned_derivative(context, *, scope) -> None:
    from app.services.legacy_context_authority import (
        _payload_identity, verify_legacy_context,
    )

    _process()
    seal = context.backend_seal
    issued = _ISSUED.get(seal.receipt_id)
    if (scope != "OWNED_EVIDENCE" or seal.owner_lifetime != _LIFETIME
            or issued is None or issued[0] != seal):
        raise ValueError("owned_derivative_unissued_or_wrong_scope")
    parent = issued[1]
    verify_legacy_context(parent, scope="OWNED_EVIDENCE")
    if (_payload_identity(parent) != seal.parent_payload_sha256
            or _payload_identity(context) != seal.payload_sha256):
        raise ValueError("owned_derivative_payload_mismatch")


def revoke_owned_derivative(context) -> None:
    """Revocation invalidates this receipt and recursively dependent children."""
    _process()
    seal = context.backend_seal
    if not isinstance(seal, OwnedEvidenceDerivativeSeal):
        raise ValueError("owned_derivative_receipt_required")
    _ISSUED.pop(seal.receipt_id, None)
    key = _KEY_BY_ID.pop(seal.receipt_id, None)
    if key is not None and _ACTIVE.get(key) == seal.receipt_id:
        _ACTIVE.pop(key)
