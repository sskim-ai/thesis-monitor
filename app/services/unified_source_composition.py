"""Unregistered source-only composition mechanics; existing owner adapters required.

Owners project and revalidate named source artifacts, not caller-supplied values or
boolean eligibility flags. The run seed is immutable bytes. Each price attempt is
rebuilt in full. This module does not qualify or activate a production adapter.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import hashlib
import json
from pathlib import Path

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_source_replay import read_bound_artifact
from app.services.unified_aggregate_receipt import AggregateReceipt, VerifiedAggregate, verify_aggregate


class AcquisitionClass(StrEnum):
    ATTEMPT_FRESH = "ATTEMPT_FRESH"
    RUN_FRESH_ONCE = "RUN_FRESH_ONCE"
    VERSIONED_PERSISTED_ALLOWED = "VERSIONED_PERSISTED_ALLOWED"
    OPTIONAL_UNAVAILABLE = "OPTIONAL_UNAVAILABLE"


A, B, C, D = tuple(AcquisitionClass)


class SourceRole(ContractModel):
    key: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    market: str = Field(pattern=r"^(us|kr|both)$")
    symbol: str = Field(min_length=1)
    acquisition_class: AcquisitionClass
    mandatory: bool
    provider: str = Field(min_length=1)
    basis: str = Field(min_length=1)
    session: str = Field(min_length=1)


class SourceInput(ContractModel):
    role: str
    run_id: str
    acquisition_class: AcquisitionClass
    attempt_id: str | None = None
    acquisition_id: str | None = None
    requested_at: datetime | None = None
    received_at: datetime | None = None
    original_record_id: str | None = None
    version: str | None = None
    artifact: str | None = None
    artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    receipt_artifact: str | None = None
    receipt_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    denial: str | None = None

    @model_validator(mode="after")
    def class_ownership(self):
        if self.acquisition_class == D:
            if not self.denial or any(v is not None for v in (
                self.attempt_id, self.acquisition_id, self.requested_at, self.received_at,
                self.original_record_id, self.version, self.artifact, self.artifact_sha256,
                self.receipt_artifact, self.receipt_sha256,
            )):
                raise ValueError("denial_must_not_contain_source_or_value")
            return self
        if (self.denial and self.acquisition_class != C) or not self.artifact or not self.artifact_sha256:
            raise ValueError("bound_source_artifact_required")
        if self.acquisition_class == A:
            if not self.attempt_id or self.acquisition_id or self.version or self.original_record_id:
                raise ValueError("attempt_identity_required")
        elif self.acquisition_class == B:
            if not self.acquisition_id or self.attempt_id or self.version or self.original_record_id:
                raise ValueError("run_acquisition_identity_required")
        elif not self.original_record_id or not self.version or self.attempt_id or self.acquisition_id:
            raise ValueError("persisted_record_version_required")
        if self.acquisition_class in (A, B) and (
            self.requested_at is None or self.received_at is None
            or not self.receipt_artifact or not self.receipt_sha256
        ):
            raise ValueError("source_acquisition_time_required")
        if (self.requested_at is None) != (self.received_at is None):
            raise ValueError("incomplete_original_acquisition_time")
        if (self.receipt_artifact is None) != (self.receipt_sha256 is None):
            raise ValueError("incomplete_original_receipt")
        return self


@dataclass(frozen=True)
class OwnerProjection:
    value: object
    provider: str
    market: str
    symbol: str
    basis: str
    session: str
    eligible: bool
    denial: str | None
    # Real owners must return these from the artifact, not from request labels.
    source_time: datetime | None
    record_id: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class OwnerAdapter:
    contract: str
    code_sha256: str
    project_and_validate: Callable[[bytes, datetime], OwnerProjection]
    project_aggregate_and_validate: Callable[[VerifiedAggregate, datetime], OwnerProjection] | None = None
    page_completion_observed_at: datetime | None = None


@dataclass(frozen=True)
class FrozenRun:
    content: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


def _aware(*times: datetime | None) -> None:
    if any(t is not None and t.utcoffset() is None for t in times):
        raise ValueError("source_timezone_required")


def _roles(roles: tuple[SourceRole, ...]) -> dict[str, SourceRole]:
    result = {role.key: role for role in roles}
    if not roles or len(result) != len(roles):
        raise ValueError("source_role_inventory_invalid")
    if any(role.mandatory and role.acquisition_class == D for role in roles):
        raise ValueError("mandatory_role_cannot_be_optional")
    return result


def _resolve(item: SourceInput, role: SourceRole, *, root: Path, run_id: str,
             start: datetime, cutoff: datetime, attempt_id: str | None,
             policy: UnifiedSourcePolicy, owners: dict[str, OwnerAdapter]) -> dict:
    if item.role != role.key or item.run_id != run_id:
        raise ValueError("source_run_role_mismatch")
    if item.acquisition_class == D:
        if role.mandatory:
            raise ValueError("mandatory_source_unavailable")
        return {"source": item.model_dump(mode="json"), "value": None}
    if item.acquisition_class != role.acquisition_class:
        raise ValueError("source_acquisition_class_mismatch")
    if item.acquisition_class == A and item.attempt_id != attempt_id:
        raise ValueError("source_attempt_mismatch")
    _aware(start, cutoff, item.requested_at, item.received_at)
    if start > cutoff:
        raise ValueError("source_time_window_invalid")
    if item.requested_at is not None:
        if not item.requested_at <= item.received_at <= cutoff:
            raise ValueError("source_time_outside_cutoff")
        if item.acquisition_class in (A, B) and item.requested_at < start:
            raise ValueError("source_not_acquired_in_required_window")
    policy.require(role.provider)
    owner = owners.get(role.owner)
    if owner is None or not owner.contract or len(owner.code_sha256) != 64:
        raise ValueError("source_owner_not_qualified")
    raw = read_bound_artifact(root, item.artifact, item.artifact_sha256)
    if item.acquisition_class == C and item.receipt_artifact:
        read_bound_artifact(root, item.receipt_artifact, item.receipt_sha256)
    aggregate = None
    if item.acquisition_class in (A, B):
        receipt = json.loads(read_bound_artifact(root, item.receipt_artifact, item.receipt_sha256))
        expected = {"run_id": run_id, "attempt_id": item.attempt_id,
                    "acquisition_id": item.acquisition_id,
                    "acquisition_class": item.acquisition_class.value,
                    "requested_at": item.requested_at.isoformat(),
                    "received_at": item.received_at.isoformat(),
                    "role": role.key, "symbol": role.symbol, "market": role.market,
                    "provider": role.provider, "basis": role.basis, "session": role.session,
                    "artifact": item.artifact, "artifact_sha256": item.artifact_sha256}
        if any(receipt.get(k) != v for k, v in expected.items()):
            raise ValueError("source_acquisition_receipt_binding_mismatch")
        if receipt.get("contract") == "unified-transitive-source-receipt-v1":
            aggregate = verify_aggregate(root, AggregateReceipt.model_validate(receipt), policy=policy, cutoff=cutoff,
                                         completion_observed_at=owner.page_completion_observed_at)
            if aggregate.receipt.owner != role.owner or owner.project_aggregate_and_validate is None:
                raise ValueError("aggregate_owner_replay_not_qualified")
        elif (receipt.get("request_sha256") != digest(receipt.get("request"))
            or type(receipt.get("ordinal")) is not int or receipt["ordinal"] < 1
            or receipt.get("outcome") != "HTTP_RESPONSE"
            or not 200 <= receipt.get("http_status", 0) < 300):
            raise ValueError("source_successful_request_receipt_required")
    projected = (owner.project_aggregate_and_validate(aggregate, cutoff) if aggregate
                 else owner.project_and_validate(raw, cutoff))
    if aggregate and digest(projected.value) != aggregate.receipt.normalized_sha256:
        raise ValueError("aggregate_output_not_child_derived")
    if (projected.provider, projected.market, projected.symbol, projected.basis,
        projected.session) != (role.provider, role.market, role.symbol, role.basis, role.session):
        raise ValueError("source_owner_identity_basis_session_mismatch")
    _aware(projected.source_time)
    if projected.source_time and projected.source_time > cutoff:
        raise ValueError("future_source_not_eligible")
    if item.acquisition_class == C and (projected.record_id, projected.version) != (
        item.original_record_id, item.version
    ):
        raise ValueError("source_record_version_mismatch")
    if item.denial is not None:
        if (item.acquisition_class != C or role.mandatory or projected.eligible
                or projected.denial != item.denial or projected.value is not None):
            raise ValueError("optional_persisted_denial_not_owner_bound")
        return {"source": item.model_dump(mode="json"), "value": None,
                "availability": "UNAVAILABLE", "provider": projected.provider,
                "eligibility": {"owner": role.owner, "contract": owner.contract,
                    "code_sha256": owner.code_sha256, "cutoff": cutoff.isoformat()},
                "basis": projected.basis, "session": projected.session}
    if not projected.eligible or projected.denial:
        raise ValueError("source_owner_current_eligibility_failed")
    policy.check_lineage(projected.value)
    return {"source": item.model_dump(mode="json"), "value": projected.value,
            "value_sha256": digest(projected.value), "provider": projected.provider,
            "original_source_time": projected.source_time.isoformat() if projected.source_time else None,
            "eligibility": {"owner": role.owner, "contract": owner.contract,
                            "code_sha256": owner.code_sha256, "cutoff": cutoff.isoformat()},
            "basis": projected.basis, "session": projected.session}


def freeze_run(*, root: Path, run_id: str, run_started_at: datetime, cutoff: datetime,
               roles: tuple[SourceRole, ...], inputs: tuple[SourceInput, ...],
               policy: UnifiedSourcePolicy, owners: dict[str, OwnerAdapter]) -> FrozenRun:
    role_map = _roles(roles)
    expected = {r.key for r in roles if r.acquisition_class != A}
    if {i.role for i in inputs} != expected or len(inputs) != len(expected):
        raise ValueError("run_seed_role_set_mismatch")
    _aware(run_started_at, cutoff)
    values = [_resolve(i, role_map[i.role], root=root, run_id=run_id, start=run_started_at,
                       cutoff=cutoff, attempt_id=None, policy=policy, owners=owners)
              for i in sorted(inputs, key=lambda x: x.role)]
    return FrozenRun(encoded({"contract": "unified-source-composition-v1", "run_id": run_id,
        "run_started_at": run_started_at.isoformat(), "cutoff": cutoff.isoformat(),
        "roles": [r.model_dump(mode="json") for r in roles],
        "allowed_providers": sorted(policy.allowed_providers), "components": values}))


def compose_attempt(*, frozen: FrozenRun, expected_run_sha256: str, root: Path,
                    attempt_id: str, started_at: datetime, cutoff: datetime,
                    inputs: tuple[SourceInput, ...], owners: dict[str, OwnerAdapter]) -> dict:
    if frozen.sha256 != expected_run_sha256:
        raise ValueError("run_seed_hash_mismatch")
    seed = json.loads(frozen.content)
    roles = tuple(SourceRole.model_validate(r) for r in seed["roles"])
    role_map = _roles(roles)
    expected = {r.key for r in roles if r.acquisition_class == A}
    if not attempt_id or {i.role for i in inputs} != expected or len(inputs) != len(expected):
        raise ValueError("whole_attempt_source_set_required")
    _aware(started_at, cutoff)
    if not datetime.fromisoformat(seed["cutoff"]) <= started_at <= cutoff:
        raise ValueError("attempt_precedes_frozen_run")
    policy = UnifiedSourcePolicy(frozenset(seed["allowed_providers"]))
    # Replay frozen B/C against the current cutoff without changing their bytes
    # or timestamps. Changed eligibility fails the attempt, not a price patch.
    for component in seed["components"]:
        item = SourceInput.model_validate(component["source"])
        replayed = _resolve(item, role_map[item.role], root=root, run_id=seed["run_id"],
                            start=datetime.fromisoformat(seed["run_started_at"]), cutoff=cutoff,
                            attempt_id=None, policy=policy, owners=owners)
        if any(replayed.get(k) != component.get(k) for k in (
            "value_sha256", "original_source_time", "basis", "session", "provider"
        )) or replayed.get("eligibility", {}).get("code_sha256") != component.get(
            "eligibility", {}
        ).get("code_sha256"):
            raise ValueError("frozen_run_projection_changed")
    current = [_resolve(i, role_map[i.role], root=root, run_id=seed["run_id"], start=started_at,
                        cutoff=cutoff, attempt_id=attempt_id, policy=policy, owners=owners)
               for i in sorted(inputs, key=lambda x: x.role)]
    packet = {"contract": seed["contract"], "run_id": seed["run_id"], "attempt_id": attempt_id,
              "run_manifest_sha256": frozen.sha256,
              "seed_sha256": digest([c for c in seed["components"]
                                     if c["source"]["acquisition_class"] == C.value]),
              "attempt_started_at": started_at.isoformat(),
              "component_sha256": {
                  cls.value: digest([c for c in seed["components"]
                                     if c["source"]["acquisition_class"] == cls.value])
                  for cls in (B, C, D)
              },
              "cutoff": cutoff.isoformat(), "attempt_components": current,
              "run_components": seed["components"],
              "model_dispatch_qualified": False}
    return {**packet, "snapshot_sha256": digest(packet)}
