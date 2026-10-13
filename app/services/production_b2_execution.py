"""Detached operational authorization around the unchanged canonical B2 v2 owner."""
from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field

from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_runtime_v2 import CONTRACT as RUNTIME
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services import new_buyer_base_contract as wire_contract
from app.services import new_buyer_v2_contract as economic_contract
from app.services import new_buyer_v2_policy as economic_policy
from app.services import new_buyer_request_owner as canonical

SHA = r"^[a-f0-9]{64}$"


def file_sha(module):
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


class ProductionB2ExecutionAuthorizationV1(ContractModel):
    contract: Literal["production-b2-execution-authorization-v1"] = "production-b2-execution-authorization-v1"
    runtime_contract: Literal["unified-query-time-snapshot-v2"] = RUNTIME
    execution_purpose: Literal["PRODUCTION_MONITORING"] = "PRODUCTION_MONITORING"
    generation_id: str = Field(min_length=1)
    source_generation_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    security_id: str = Field(min_length=1)
    request_sha256: str = Field(pattern=SHA)
    prompt_sha256: str = Field(pattern=SHA)
    schema_sha256: str = Field(pattern=SHA)
    policy_sha256: str = Field(pattern=SHA)
    validator_sha256: str = Field(pattern=SHA)
    authority_sha256: str = Field(pattern=SHA)
    source_envelope_sha256: str = Field(pattern=SHA)
    owner_sha256: str = Field(pattern=SHA)
    core_sha256: str = Field(pattern=SHA)
    pass_a_sha256: str = Field(pattern=SHA)
    pass_b_sha256: str = Field(pattern=SHA)
    model: Literal["gpt-5.6-sol"] = "gpt-5.6-sol"
    effort: Literal["xhigh"] = "xhigh"
    timeout_seconds: Literal[600] = 600
    transport_form_retries: int = Field(default=2, ge=0, le=2)
    semantic_retries: Literal[0] = 0
    persistence_policy: Literal["IMMUTABLE_RUN_ARTIFACTS_ONLY"] = "IMMUTABLE_RUN_ARTIFACTS_ONLY"
    renderer_handoff: Literal["ACCEPTED_DETAILED_STOCK_V2"] = "ACCEPTED_DETAILED_STOCK_V2"
    delivery_handoff: Literal["SEPARATE_EXPLICIT_DELIVERY_AUTHORIZATION"] = "SEPARATE_EXPLICIT_DELIVERY_AUTHORIZATION"


def authorize_b2(request, *, generation_id, source_envelope_sha256, owner_sha256,
                 core_sha256, pass_a_sha256, pass_b_sha256, retries=2, source_generation_id=None):
    payload = canonical.provider_payload(request, expected_request_sha256=request["request_sha256"])
    current = payload["input"]
    authority = current["authority_digests"]
    source_generation_id = source_generation_id or generation_id
    if (current["source_generation"] != source_generation_id
            or authority.get("core") != core_sha256
            or authority.get("pass_a") != pass_a_sha256
            or authority.get("accepted_b") != pass_b_sha256):
        raise ValueError("production_b2_current_authority_mismatch")
    return ProductionB2ExecutionAuthorizationV1(
        generation_id=generation_id, source_generation_id=source_generation_id,
        ticker=current["ticker"], security_id=current["security_id"],
        request_sha256=digest(payload), prompt_sha256=digest(payload["prompt"]),
        schema_sha256=digest(payload["response_schema"]), policy_sha256=file_sha(economic_policy),
        validator_sha256=digest([file_sha(canonical), file_sha(economic_contract), file_sha(wire_contract)]),
        authority_sha256=digest(authority), source_envelope_sha256=source_envelope_sha256,
        owner_sha256=owner_sha256, core_sha256=core_sha256, pass_a_sha256=pass_a_sha256,
        pass_b_sha256=pass_b_sha256, transport_form_retries=retries)


def verify_authorization(request, authorization, *, generation_id, source_envelope_sha256,
                         owner_sha256, core_sha256, pass_a_sha256, pass_b_sha256, source_generation_id=None):
    expected = authorize_b2(request, generation_id=generation_id,
        source_envelope_sha256=source_envelope_sha256, owner_sha256=owner_sha256,
        core_sha256=core_sha256, pass_a_sha256=pass_a_sha256, pass_b_sha256=pass_b_sha256,
        retries=authorization.transport_form_retries, source_generation_id=source_generation_id)
    if expected != authorization:
        raise ValueError("production_b2_detached_authorization_drift")


class ModelTransportError(Exception):
    """Only transport implementations may classify their API/connection failure."""


class SemanticReject(ValueError):
    """A schema-valid semantic object is final and must never be retried."""


class ModelTransport(Protocol):
    async def request(self, payload: dict, *, model: str, effort: str, timeout: int) -> bytes: ...


async def execute_b2(request, authorization, *, current_binding, transport: ModelTransport, directory: Path):
    verify_authorization(request, authorization, **current_binding)
    frozen = deepcopy(request)
    payload = canonical.provider_payload(frozen, expected_request_sha256=authorization.request_sha256)
    durable_json(directory / "authorization.json", authorization.model_dump(mode="json"), exclusive=True)
    durable_json(directory / "request.json", frozen, exclusive=True)
    attempts = []
    for ordinal in range(1, authorization.transport_form_retries + 2):
        verify_authorization(frozen, authorization, **current_binding)
        if request != frozen:
            raise ValueError("production_b2_request_mutation")
        row = {"ordinal": ordinal, "request_sha256": authorization.request_sha256,
               "authorization_sha256": digest(authorization.model_dump(mode="json")),
               "generation_id": authorization.generation_id, "classification": "INTENT"}
        attempt = directory / f"attempt-{ordinal}"
        durable_json(attempt / "intent.json", row, exclusive=True)
        parsed = None
        try:
            raw = await asyncio.wait_for(transport.request(deepcopy(payload), model=authorization.model,
                effort=authorization.effort, timeout=authorization.timeout_seconds), authorization.timeout_seconds)
        except (ModelTransportError, TimeoutError) as exc:
            row.update(classification="TRANSPORT_FAILURE", error_type=type(exc).__name__)
        else:
            if not isinstance(raw, bytes):
                raise TypeError("production_transport_raw_bytes_required")
            # Raw bytes are durable before decoding or semantic validation.
            durable_bytes(attempt / "response.raw", raw, exclusive=True)
            row["raw_sha256"] = hashlib.sha256(raw).hexdigest()
            try:
                parsed = json.loads(raw)
            except (UnicodeError, ValueError):
                row["classification"] = "RESPONSE_FORM_FAILURE"
            else:
                errors = wire_contract.validate_json_schema(parsed, payload["response_schema"])
                if errors:
                    row["classification"] = "PROVIDER_SCHEMA_FAILURE"
                else:
                    verdict = canonical.validate_result(parsed, frozen,
                        expected_request_sha256=authorization.request_sha256)
                    row.update(classification="SEMANTIC_REJECT" if verdict["status"] != "PASS" else "ACCEPTED",
                               semantic_verdict=verdict)
        if request != frozen or digest(payload) != authorization.request_sha256:
            raise ValueError("production_b2_request_mutation")
        attempts.append(row)
        durable_json(attempt / "receipt.json", row, exclusive=True)
        if row["classification"] == "SEMANTIC_REJECT":
            raise SemanticReject("production_b2_semantic_reject_no_retry")
        if row["classification"] == "ACCEPTED":
            result = {"contract": "production-b2-accepted-result-v1", "generation_id": authorization.generation_id,
                "ticker": authorization.ticker, "security_id": authorization.security_id,
                "request_sha256": authorization.request_sha256,
                "authorization_sha256": digest(authorization.model_dump(mode="json")),
                "output": parsed, "output_sha256": digest(parsed), "attempts": attempts,
                "semantic_retries": 0, "status": "PASS"}
            durable_json(directory / "accepted.json", result, exclusive=True)
            return result
    raise ModelTransportError("production_b2_transport_form_budget_exhausted")
