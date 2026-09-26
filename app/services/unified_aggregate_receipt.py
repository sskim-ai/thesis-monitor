"""Transitive artifact integrity for aggregates; owner normalization is mandatory.

An aggregate is never an HTTP response. The concrete owner must independently
check the planned read set and re-normalize child bytes before consumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path

from pydantic import Field, field_serializer, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_source_replay import read_bound_artifact


class ArtifactBinding(ContractModel):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AggregateChild(ContractModel):
    child_id: str = Field(min_length=1)
    receipt: ArtifactBinding
    normalization: ArtifactBinding | None = None
    accepted_page: ArtifactBinding | None = None


class AggregateReceipt(ContractModel):
    contract: str = "unified-transitive-source-receipt-v1"
    owner: str
    run_id: str
    acquisition_class: str
    attempt_id: str | None = None
    acquisition_id: str | None = None
    role: str
    market: str
    symbol: str
    provider: str
    basis: str
    session: str
    requested_at: datetime
    received_at: datetime
    artifact: str
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan: ArtifactBinding
    expected_child_ids: tuple[str, ...]
    children: tuple[AggregateChild, ...]
    normalized_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    validator_contract: str = Field(min_length=1)
    coverage: dict
    aggregate_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_serializer("requested_at", "received_at")
    def timestamp(self, value: datetime):
        return value.isoformat()

    @model_validator(mode="after")
    def identity(self):
        if self.contract != "unified-transitive-source-receipt-v1":
            raise ValueError("aggregate_contract_mismatch")
        if self.acquisition_class not in {"ATTEMPT_FRESH", "RUN_FRESH_ONCE"}:
            raise ValueError("aggregate_class_invalid")
        if ((self.acquisition_class == "ATTEMPT_FRESH" and (not self.attempt_id or self.acquisition_id))
                or (self.acquisition_class == "RUN_FRESH_ONCE" and (not self.acquisition_id or self.attempt_id))):
            raise ValueError("aggregate_acquisition_identity_invalid")
        ids = tuple(c.child_id for c in self.children)
        if (not ids or len(set(ids)) != len(ids) or ids != self.expected_child_ids
                or len({c.receipt.path for c in self.children}) != len(ids)):
            raise ValueError("aggregate_exact_child_set_required")
        if (self.requested_at.utcoffset() is None or self.received_at.utcoffset() is None
                or self.requested_at > self.received_at):
            raise ValueError("aggregate_time_invalid")
        if digest(self.model_dump(mode="json", exclude={"aggregate_sha256"})) != self.aggregate_sha256:
            raise ValueError("aggregate_hash_mismatch")
        return self


@dataclass(frozen=True)
class VerifiedAggregate:
    receipt: AggregateReceipt
    plan: bytes
    child_receipts: tuple[dict, ...]
    child_bodies: tuple[bytes | None, ...]
    child_normalizations: tuple[dict | None, ...]
    normalized: bytes


def verify_aggregate(root: Path, receipt: AggregateReceipt, *, policy: UnifiedSourcePolicy,
                     cutoff: datetime) -> VerifiedAggregate:
    policy.require(receipt.provider)
    if cutoff.utcoffset() is None or receipt.received_at > cutoff:
        raise ValueError("aggregate_after_cutoff")
    plan = read_bound_artifact(root, receipt.plan.path, receipt.plan.sha256)
    plan_identity = json.loads(plan)
    for key in ("run_id", "attempt_id", "acquisition_id", "acquisition_class"):
        if plan_identity.get(key) != getattr(receipt, key):
            raise ValueError("aggregate_plan_identity_mismatch")
    raw = read_bound_artifact(root, receipt.artifact, receipt.artifact_sha256)
    if digest(json.loads(raw)) != receipt.normalized_sha256:
        raise ValueError("aggregate_normalized_hash_mismatch")
    children, bodies, normalizations = [], [], []
    cursors, ordinals = {}, []
    for child in receipt.children:
        current = json.loads(read_bound_artifact(root, child.receipt.path, child.receipt.sha256))
        policy.require(current.get("provider"))
        for key in ("run_id", "attempt_id", "acquisition_id", "acquisition_class"):
            if current.get(key) != getattr(receipt, key):
                raise ValueError("aggregate_child_identity_mismatch")
        if current.get("request_sha256") != digest(current.get("request")):
            raise ValueError("aggregate_child_request_mismatch")
        times = [datetime.fromisoformat(current[k]) for k in ("requested_at", "received_at")]
        if any(t.utcoffset() is None for t in times) or not (
            receipt.requested_at <= times[0] <= times[1] <= receipt.received_at
        ):
            raise ValueError("aggregate_child_time_mismatch")
        ordinal = current.get("ordinal")
        if type(ordinal) is not int or ordinal < 1:
            raise ValueError("aggregate_child_ordinal_invalid")
        ordinals.append(ordinal)
        outcome = current.get("outcome")
        body = None
        if outcome in {"HTTP_RESPONSE", "CACHE_SOURCE_OPEN"}:
            parent = Path(child.receipt.path).parent
            if outcome == "CACHE_SOURCE_OPEN":
                original = json.loads(read_bound_artifact(root, str(parent / current["original_receipt"]),
                                                          current["original_receipt_sha256"]))
                policy.require(original.get("provider"))
                if (original.get("provider") != current["provider"]
                        or original.get("artifact_sha256") != current["artifact_sha256"]
                        or original.get("request_sha256") != current["request_sha256"]
                        or original.get("outcome") != "HTTP_RESPONSE"
                        or not 200 <= original.get("http_status", 0) < 300
                        or original.get("requested_at") != current.get("original_requested_at")
                        or original.get("received_at") != current.get("original_received_at")):
                    raise ValueError("aggregate_cache_original_mismatch")
                original_times = [datetime.fromisoformat(original[k]) for k in ("requested_at", "received_at")]
                if any(t.utcoffset() is None for t in original_times) or not original_times[0] <= original_times[1] <= cutoff:
                    raise ValueError("aggregate_cache_original_time_invalid")
            body = read_bound_artifact(root, str(parent / current["artifact"]), current["artifact_sha256"])
            try:
                policy.check_lineage(json.loads(body))
            except json.JSONDecodeError:
                pass
        elif outcome != "TRANSPORT_ERROR" or current.get("artifact") is not None:
            raise ValueError("aggregate_child_outcome_invalid")
        normalization = None
        if child.normalization:
            normalization = json.loads(read_bound_artifact(root, child.normalization.path, child.normalization.sha256))
            if (normalization.get("response_receipt_sha256") != digest(current)
                    or normalization.get("normalized_sha256") != digest(normalization.get("normalized"))):
                raise ValueError("aggregate_child_normalization_mismatch")
        if child.accepted_page:
            page = json.loads(read_bound_artifact(root, child.accepted_page.path, child.accepted_page.sha256))
            request = current["request"]
            key = current["read_key"]
            number, cursor = cursors.get(key, (0, hashlib.sha256(b"").hexdigest()))
            if (page.get("response_receipt_sha256") != digest(current)
                    or page.get("raw_sha256") != current.get("artifact_sha256")
                    or page.get("page") != number + 1 or request.get("page") != number + 1
                    or cursor is None or request.get("cursor_sha256") != cursor
                    or request.get("continuation") != bool(number)
                    or outcome != "HTTP_RESPONSE" or not 200 <= current.get("http_status", 0) < 300):
                raise ValueError("aggregate_page_cursor_mismatch")
            cursors[key] = (number + 1, page["next_cursor_sha256"] if page["continuation"] else None)
        children.append(current)
        bodies.append(body)
        normalizations.append(normalization)
    if ordinals != sorted(set(ordinals)):
        raise ValueError("aggregate_child_order_mismatch")
    if any(cursor is not None for _number, cursor in cursors.values()):
        raise ValueError("aggregate_page_set_incomplete")
    policy.check_lineage(json.loads(raw))
    return VerifiedAggregate(receipt, plan, tuple(children), tuple(bodies), tuple(normalizations), raw)
