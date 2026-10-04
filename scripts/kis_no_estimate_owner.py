"""Offline request-bound KIS availability sidecar; never a valuation or stance owner.

The empty-shape contract describes one observed wire shape, not all possible
KIS empty responses. New shapes require review. Existing valuation bytes stay
with their original producers; this module has no production caller.
"""
from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict

from scripts.kis_eps_wire_calibration import digest, sealed, verified
from scripts.kis_fy1_semantic_owner import SemanticGap

CONTRACT = "KISResearchEstimateAvailabilityAssessmentV1"
DECISION = "kis-request-bound-estimate-availability-v1"
SHAPE = "KISResearchEstimateObservedNormalEmptyShapeV1"
PLAN = "kr8-fresh-kis-source-integration-v1"
PATH = "/uapi/domestic-stock/v1/quotations/estimate-perform"
TR_ID = "HHKST668300C0"
EMPTY_OUTPUT1 = {
    "sht_cd": "", "item_kor_nm": "", "name1": "", "name2": "", "estdate": "",
    "rcmd_name": "", "capital": "0.0", "forn_item_lmtrt": "0.00",
}
REQUIRED_KEYS = {"output1", "output2", "output3", "output4", "rt_cd", "msg_cd", "msg1"}


class AvailabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    contract: Literal["KISResearchEstimateAvailabilityAssessmentV1"] = CONTRACT
    decision_version: Literal["kis-request-bound-estimate-availability-v1"] = DECISION
    proof_type: Literal["CURRENT_SOURCE_OBSERVATION"] = "CURRENT_SOURCE_OBSERVATION"
    security_code: str
    canonical_security_id: str
    source_generation: str
    source_plan_sha256: str
    security_input_sha256: str
    request_path: str | None = None
    request_tr_id: str | None = None
    request_params: dict[str, str] | None = None
    request_started_at: str | None = None
    request_ended_at: str | None = None
    raw_sha256: str | None = None
    source_receipt_sha256: str | None = None
    http_status: int | None = None
    response_content_type: str | None = None
    response_tr_id: str | None = None
    provider_rt_cd: str | None = None
    provider_msg_cd: str | None = None
    observed_payload_shape_contract: Literal["KISResearchEstimateObservedNormalEmptyShapeV1"] = SHAPE
    output1_shape_disposition: Literal["UNOBSERVED", "OBSERVED_EMPTY", "OTHER"] = "UNOBSERVED"
    output2_shape_disposition: Literal["UNOBSERVED", "OBSERVED_EMPTY", "OTHER"] = "UNOBSERVED"
    output3_shape_disposition: Literal["UNOBSERVED", "OBSERVED_EMPTY", "OTHER"] = "UNOBSERVED"
    output4_shape_disposition: Literal["UNOBSERVED", "OBSERVED_EMPTY", "OTHER"] = "UNOBSERVED"
    normal_empty_confirmed: bool = False
    field: Literal["KIS_RESEARCH_ESTIMATE"] = "KIS_RESEARCH_ESTIMATE"
    field_decision: Literal[
        "USABLE_ESTIMATE_PRESENT", "NO_RESEARCH_ESTIMATE_AT_RETRIEVAL",
        "SOURCE_FAILURE", "NOT_QUERIED", "IDENTITY_MISMATCH", "SEMANTIC_GAP",
    ]
    field_eligibility: Literal[
        "ELIGIBLE_BY_EXISTING_POSITIVE_OWNER", "INELIGIBLE_NO_RESEARCH_ESTIMATE", "UNRESOLVED",
    ] = "UNRESOLVED"
    decision_reason_code: str
    observation_time: str | None = None
    temporal_scope: Literal["OBSERVED_AT_RETRIEVAL", "UNOBSERVED"] = "UNOBSERVED"
    field_effective_time_disposition: Literal[
        "NOT_AVAILABLE_BECAUSE_FIELD_ABSENT", "OWNED_BY_EXISTING_POSITIVE_OWNER", "UNRESOLVED",
    ] = "UNRESOLVED"
    request_binding_state: Literal[
        "REQUEST_BOUND_NEGATIVE_AVAILABILITY_OBSERVATION", "EXACT_REQUEST_RESPONSE_BOUND", "NOT_QUERIED",
    ] = "NOT_QUERIED"
    provider_returned_security_identity_state: Literal[
        "UNAVAILABLE_NO_RETURNED_ESTIMATE_IDENTITY", "OWNED_BY_EXISTING_POSITIVE_OWNER",
        "MISMATCH", "NOT_ASSESSED",
    ] = "NOT_ASSESSED"
    source_failure: bool = False
    provider_success: bool = False
    owner_complete: bool = False
    positive_owner_ref: str | None = None
    legacy_prose_used: Literal[False] = False
    blind_label_used: Literal[False] = False
    value: None = None
    estimate_effective_time: None = None
    estimate_period: None = None
    unit: None = None
    blocker_scope: Literal["METRIC_SCOPED"] = "METRIC_SCOPED"
    affected_metric: Literal["CURRENT_FY1_FPER"] = "CURRENT_FY1_FPER"
    blocks_metric_value_use: bool = False
    blocks_other_valuation_metrics: Literal[False] = False
    blocks_newbuyer_global_resolution: Literal[False] = False
    receipt_sha256: str


def aware(value):
    try:
        stamp = datetime.fromisoformat(value)
        if stamp.utcoffset() is None:
            raise ValueError
        return stamp
    except (ValueError, TypeError):
        raise SemanticGap("AVAILABILITY_TEMPORAL_PROVENANCE_GAP") from None


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def _result(base, decision, reason, **changes):
    data = dict(base, field_decision=decision, decision_reason_code=reason, **changes)
    # Populate declared defaults before hashing, so schema and wire receipts agree.
    model = AvailabilityAssessment(**data, receipt_sha256="")
    result = sealed(model.model_dump(exclude={"receipt_sha256"}))
    return AvailabilityAssessment.model_validate(result).model_dump()


def assess(*, code, generation, plan, raw, receipt, request, positive_eps=None):
    """Replay exact frozen inputs. Missing binding raises; malformed payload stays a gap."""
    verified(plan, PLAN)
    security = plan.get("securities", {}).get(code, {})
    if (not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code)
            or not generation or generation != plan.get("generation_id")
            or code not in plan.get("subjects", []) or security.get("ticker") != code
            or not security.get("canonical_security_id")):
        raise SemanticGap("AVAILABILITY_GENERATION_SECURITY_GAP")
    base = dict(security_code=code, canonical_security_id=security["canonical_security_id"],
                source_generation=generation, source_plan_sha256=plan["receipt_sha256"],
                security_input_sha256=digest(security))
    if raw is None and receipt is None and request is None and positive_eps is None:
        return _result(base, "NOT_QUERIED", "NO_REQUEST_OBSERVATION")
    if not isinstance(raw, bytes) or not isinstance(receipt, dict) or not isinstance(request, dict):
        raise SemanticGap("AVAILABILITY_SOURCE_BINDING_GAP")
    raw_hash = sha256(raw).hexdigest()
    if (receipt.get("request") != request or request.get("plan_sha256") != plan["receipt_sha256"]
            or request.get("path") != PATH or request.get("tr_id") != TR_ID
            or request.get("method") != "GET" or request.get("security_code") != code
            or request.get("params") != {"SHT_CD": code} or request.get("redirects") is not False
            or receipt.get("raw_sha256") != raw_hash
            or receipt.get("bytes") != len(raw) or receipt.get("state") != "COMPLETE"):
        raise SemanticGap("AVAILABILITY_SOURCE_BINDING_GAP")
    start, end = request.get("started_at"), receipt.get("ended_at")
    if not aware(plan.get("as_of")) <= aware(start) <= aware(end):
        raise SemanticGap("AVAILABILITY_TEMPORAL_ORDER_GAP")
    headers = receipt.get("response_headers", {})
    if not isinstance(headers, dict):
        raise SemanticGap("AVAILABILITY_RESPONSE_HEADERS_GAP")
    content_type, response_tr = headers.get("content-type"), headers.get("tr_id")
    base.update(request_path=PATH, request_tr_id=TR_ID, request_params={"SHT_CD": code},
        request_started_at=start, request_ended_at=end, raw_sha256=raw_hash,
        source_receipt_sha256=digest(receipt), http_status=receipt.get("http_status"),
        response_content_type=content_type, response_tr_id=response_tr,
        observation_time=end, temporal_scope="OBSERVED_AT_RETRIEVAL",
        request_binding_state="EXACT_REQUEST_RESPONSE_BOUND")
    if type(receipt.get("http_status")) is not int:
        raise SemanticGap("AVAILABILITY_HTTP_STATUS_GAP")
    if receipt["http_status"] != 200:
        return _result(base, "SOURCE_FAILURE", "HTTP_FAILURE", source_failure=True)
    try:
        payload = _json(raw)
    except (ValueError, UnicodeError):
        return _result(base, "SEMANTIC_GAP", "INVALID_JSON")
    if not isinstance(payload, dict):
        return _result(base, "SEMANTIC_GAP", "INVALID_ENDPOINT_CONTAINER")
    for field in ("rt_cd", "msg_cd"):
        if not isinstance(payload.get(field), str):
            return _result(base, "SEMANTIC_GAP", "INVALID_PROVIDER_STATUS")
    base.update(provider_rt_cd=payload["rt_cd"], provider_msg_cd=payload["msg_cd"])
    if payload["rt_cd"] != "0":
        return _result(base, "SOURCE_FAILURE", "PROVIDER_FAILURE", source_failure=True)
    if (not isinstance(content_type, str) or content_type.split(";", 1)[0].strip().lower() != "application/json"
            or response_tr != TR_ID or payload["msg_cd"] != "MCA00000"
            or headers.get("tr_cont") != ""):
        return _result(base, "SEMANTIC_GAP", "UNQUALIFIED_ENDPOINT_SUCCESS_ENVELOPE")
    base["provider_success"] = True
    for name in ("output1", "output2", "output3", "output4"):
        expected = EMPTY_OUTPUT1 if name == "output1" else []
        base[name + "_shape_disposition"] = "OBSERVED_EMPTY" if payload.get(name) == expected else "OTHER"
    if (set(payload) != REQUIRED_KEYS or not isinstance(payload["msg1"], str)
            or not isinstance(payload.get("output1"), dict)
            or any(not isinstance(payload.get(name), list) for name in ("output2", "output3", "output4"))):
        return _result(base, "SEMANTIC_GAP", "UNQUALIFIED_ENDPOINT_SHAPE")
    returned = payload["output1"].get("sht_cd")
    if returned not in (None, "", "A" + code):
        return _result(base, "IDENTITY_MISMATCH", "RETURNED_ESTIMATE_SECURITY_MISMATCH",
                       provider_returned_security_identity_state="MISMATCH")
    if payload["output1"] == EMPTY_OUTPUT1 and all(payload[name] == [] for name in ("output2", "output3", "output4")):
        if positive_eps is not None:
            raise SemanticGap("AVAILABILITY_CONTRADICTORY_POSITIVE_OWNER")
        return _result(base, "NO_RESEARCH_ESTIMATE_AT_RETRIEVAL", "OBSERVED_SUCCESS_EMPTY_SHAPE",
            field_eligibility="INELIGIBLE_NO_RESEARCH_ESTIMATE", normal_empty_confirmed=True,
            field_effective_time_disposition="NOT_AVAILABLE_BECAUSE_FIELD_ABSENT",
            request_binding_state="REQUEST_BOUND_NEGATIVE_AVAILABILITY_OBSERVATION",
            provider_returned_security_identity_state="UNAVAILABLE_NO_RETURNED_ESTIMATE_IDENTITY",
            owner_complete=True, blocks_metric_value_use=True)
    if payload["output3"] and returned == "A" + code and positive_eps is not None:
        from scripts.kis_current_fy1_owner import eps_receipt
        eps_receipt(positive_eps)
        if (positive_eps.get("security_code") != code or positive_eps.get("estimate_sha256") != raw_hash
                or positive_eps.get("query_time") != end):
            raise SemanticGap("AVAILABILITY_POSITIVE_OWNER_BINDING_GAP")
        return _result(base, "USABLE_ESTIMATE_PRESENT", "EXISTING_POSITIVE_OWNER_BOUND",
            field_eligibility="ELIGIBLE_BY_EXISTING_POSITIVE_OWNER",
            field_effective_time_disposition="OWNED_BY_EXISTING_POSITIVE_OWNER",
            provider_returned_security_identity_state="OWNED_BY_EXISTING_POSITIVE_OWNER",
            positive_owner_ref=positive_eps["receipt_sha256"], owner_complete=True)
    return _result(base, "SEMANTIC_GAP", "UNQUALIFIED_EMPTY_OR_POSITIVE_OWNER_SHAPE")


def validate_assessment(value, **inputs):
    AvailabilityAssessment.model_validate(value)
    verified(value, CONTRACT)
    if value != assess(**inputs):
        raise SemanticGap("AVAILABILITY_REPRODUCTION_GAP")


def shape_contract():
    return dict(contract=SHAPE, http_status=200, content_type="application/json", response_tr_id=TR_ID,
        rt_cd="0", msg_cd="MCA00000", tr_cont="", exact_keys=sorted(REQUIRED_KEYS),
        output1=EMPTY_OUTPUT1.copy(), output2=[], output3=[], output4=[],
        msg1="STRING_ONLY_NOT_A_SEMANTIC_SIGNAL", future_shapes="REQUALIFICATION_REQUIRED",
        establishes="REQUEST_BOUND_NEGATIVE_AVAILABILITY_ONLY")
