"""Single-attempt source evidence contract, independent of investment policy."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CONTRACT = "unified-query-time-snapshot-v1"
STAGES = ("MARKET", "CORE", "A", "B", "VALIDATE", "RENDER", "DELIVER")


def encoded(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def pointer(document: Any, path: str) -> Any:
    if not path.startswith("/"):
        raise ValueError("absolute_json_pointer_required")
    value = document
    for token in path[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Role(ContractModel):
    key: str
    symbol: str
    provider: str
    route: str
    packet_pointer: str
    session_date: date | None
    basis: str
    numeric_fields: tuple[str, ...] = ()
    ohlc: bool = False

    @model_validator(mode="after")
    def explicit_identity(self):
        if not all((self.key, self.symbol, self.provider, self.route, self.basis)):
            raise ValueError("explicit_source_identity_required")
        if self.provider.lower().replace("_", " ") in {"alpha vantage", "massive"}:
            raise ValueError("provider_not_authorized")
        if self.basis.lower() in {"unknown", "unavailable", "missing"}:
            raise ValueError("explicit_basis_required")
        return self


class SnapshotPolicy(ContractModel):
    market: Literal["us", "kr"]
    subjects: tuple[str, ...] = Field(min_length=1)
    roles: tuple[Role, ...] = Field(min_length=1)
    validator_contracts: tuple[str, ...] = Field(min_length=1)
    universe_owner_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    message_ids: tuple[str, ...] = Field(min_length=1)
    subject_pointer: str = "/stocks"
    subject_key: str = "ticker"

    @model_validator(mode="after")
    def unique(self):
        for values in (self.subjects, tuple(r.key for r in self.roles), self.validator_contracts,
                       self.message_ids):
            if len(values) != len(set(values)):
                raise ValueError("duplicate_policy_identity")
        return self


class SourceReceipt(ContractModel):
    role: str
    attempt_id: str
    provider: str
    route: str
    symbol: str
    session_date: date | None
    basis: str
    observed_at: datetime
    raw_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalized_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["PASS", "FAIL"]


class ValidatorReceipt(ContractModel):
    contract: str
    packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["PASS", "FAIL"]
    errors: tuple[str, ...] = ()


class Collection(ContractModel):
    run_id: str
    attempt_id: str
    market: Literal["us", "kr"]
    started_at: datetime
    completed_at: datetime
    packet: dict[str, Any]
    receipts: tuple[SourceReceipt, ...]
    validators: tuple[ValidatorReceipt, ...]
    policy_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_errors: tuple[str, ...] = ()
    semantics: Literal["QUERY_TIME_SNAPSHOT"] = "QUERY_TIME_SNAPSHOT"
    finality_claim: Literal["NOT_CLAIMED"] = "NOT_CLAIMED"


def validate_collection(collection: Collection, *, policy: SnapshotPolicy, run_id: str,
                        attempt_id: str, started_at: datetime, now: datetime) -> list[str]:
    errors: list[str] = []
    if (collection.run_id, collection.attempt_id, collection.market) != (
            run_id, attempt_id, policy.market):
        errors.append("collection_identity_mismatch")
    if collection.policy_sha256 != digest(policy.model_dump(mode="json")):
        errors.append("collection_policy_mismatch")
    times = (started_at, now, collection.started_at, collection.completed_at)
    if any(t.tzinfo is None for t in times):
        return errors + ["timezone_required"]
    if not started_at <= collection.started_at <= collection.completed_at <= now:
        errors.append("collection_time_outside_attempt")
    if collection.source_errors:
        errors.append("required_source_error")
    try:
        subjects = [r[policy.subject_key] for r in pointer(collection.packet, policy.subject_pointer)]
        if sorted(subjects) != sorted(policy.subjects):
            errors.append("production_universe_incomplete")
    except (KeyError, ValueError, TypeError, IndexError):
        errors.append("production_universe_invalid")
    receipts = {r.role: r for r in collection.receipts}
    if len(receipts) != len(collection.receipts) or set(receipts) != {r.key for r in policy.roles}:
        errors.append("required_source_roles_incomplete_or_duplicate")
    for role in policy.roles:
        receipt = receipts.get(role.key)
        if receipt is None:
            errors.append(f"missing_role:{role.key}")
            continue
        if (receipt.attempt_id, receipt.provider, receipt.route, receipt.symbol,
            receipt.session_date, receipt.basis, receipt.status) != (
                attempt_id, role.provider, role.route, role.symbol,
                role.session_date, role.basis, "PASS"):
            errors.append(f"source_identity_date_basis_invalid:{role.key}")
        if (receipt.observed_at.tzinfo is None or not
                collection.started_at <= receipt.observed_at <= collection.completed_at):
            errors.append(f"source_time_outside_attempt:{role.key}")
        try:
            value = pointer(collection.packet, role.packet_pointer)
            if digest(value) != receipt.normalized_sha256:
                errors.append(f"normalized_source_binding_mismatch:{role.key}")
            fields = set(role.numeric_fields) | ({"open", "high", "low", "close"} if role.ohlc else set())
            numbers = {}
            for key in fields:
                number = value[key]
                if isinstance(number, bool) or number is None or not math.isfinite(float(number)):
                    raise ValueError("invalid_numeric_source")
                numbers[key] = float(number)
            if role.ohlc and not (0 < numbers["low"] <= min(numbers["open"], numbers["close"])
                                 <= max(numbers["open"], numbers["close"]) <= numbers["high"]):
                raise ValueError("malformed_ohlc")
            if role.session_date and role.session_date > now.date():
                errors.append(f"future_source_row:{role.key}")
        except (KeyError, TypeError, ValueError, IndexError, OverflowError):
            errors.append(f"required_source_fields_invalid:{role.key}")
    validators = {v.contract: v for v in collection.validators}
    if (len(validators) != len(collection.validators)
            or set(validators) != set(policy.validator_contracts)):
        errors.append("source_validator_coverage_mismatch")
    packet_hash = digest(collection.packet)
    for receipt in collection.validators:
        if receipt.packet_sha256 != packet_hash or receipt.status != "PASS" or receipt.errors:
            errors.append(f"source_validation_failed:{receipt.contract}")
    return errors


def validate_render(output: dict, policy: SnapshotPolicy, snapshot_sha256: str) -> None:
    if output.get("finality_claim") != "NOT_CLAIMED":
        raise ValueError("unsupported_finality_claim")
    messages = output.get("messages", [])
    if sorted(m.get("message_id", "") for m in messages) != sorted(policy.message_ids):
        raise ValueError("render_message_coverage_mismatch")
    for message in messages:
        text = message.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("empty_rendered_message")
        if message.get("snapshot_sha256") != snapshot_sha256:
            raise ValueError("render_snapshot_mismatch")
        if any(phrase in text.lower() for phrase in (
                "official final close", "certified final close", "immutable final close",
                "\ud655\uc815 \uc885\uac00", "\uacf5\uc2dd \ucd5c\uc885 \uc885\uac00")):
            raise ValueError("unsupported_finality_wording")


def validate_delivery(output: dict, policy: SnapshotPolicy) -> None:
    rows = output.get("receipts", [])
    if (sorted(r.get("message_id", "") for r in rows) != sorted(policy.message_ids)
            or any(r.get("status") != "SENT" for r in rows)
            or output.get("normal_messages_sent") is not True):
        raise ValueError("delivery_receipt_incomplete_or_uncertain")


class StageResult(ContractModel):
    run_id: str
    snapshot_sha256: str
    request_sha256: str
    stage: Literal["MARKET", "CORE", "A", "B", "VALIDATE", "RENDER", "DELIVER"]
    status: Literal["PASS", "FAIL"]
    output: dict[str, Any]
    errors: tuple[str, ...] = ()


def validate_stage(result: StageResult, request: dict[str, Any]) -> None:
    if (result.run_id, result.snapshot_sha256, result.request_sha256, result.stage) != (
            request["run_id"], request["snapshot_sha256"], digest(request), request["stage"]):
        raise ValueError("stage_snapshot_or_request_binding_mismatch")
    if result.status != "PASS" or result.errors:
        raise ValueError("stage_validation_failed")
