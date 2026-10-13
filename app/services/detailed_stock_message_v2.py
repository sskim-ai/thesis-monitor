"""B2-owned New Buyer and backend timing, with unchanged accepted v1 body rows."""
from typing import Literal

from app.services.detailed_stock_message_service import (
    DetailedStockMessagePlan, DetailedRow, _render_rows, _row, detailed_render,
)
from app.services.production_b2_execution import ProductionB2ExecutionAuthorizationV1
from app.services.kr_forward_valuation_message import KrForwardMessagePlan, render as render_kr
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services import new_buyer_v2_contract as b2
from app.services import new_buyer_request_owner as canonical


class DetailedStockMessagePlanV2(ContractModel):
    contract: Literal["accepted-detailed-stock-message-v2"] = "accepted-detailed-stock-message-v2"
    base: DetailedStockMessagePlan | KrForwardMessagePlan
    b2_request: dict
    b2_result: dict
    authorization: ProductionB2ExecutionAuthorizationV1
    rows: tuple[DetailedRow, ...]
    acceptance_sha256: str


def build_detailed_plan_v2(*, packet, base, b2_request, b2_result, authorization):
    presentation = base
    if isinstance(base, KrForwardMessagePlan):
        render_kr(packet, base)
        base = base.base
    if not isinstance(base, DetailedStockMessagePlan):
        raise ValueError("detailed_v2_complete_business_owner_required")
    detailed_render(packet, base)
    payload = canonical.provider_payload(b2_request, expected_request_sha256=authorization.request_sha256)
    context = payload["input"]
    if (authorization.generation_id != base.execution_generation_id
            or authorization.source_generation_id != base.source_generation_id
            or context["source_generation"] != base.source_generation_id
            or context["ticker"] != base.ticker or authorization.ticker != base.ticker
            or context["security_id"] != authorization.security_id
            or authorization.core_sha256 != digest(base.core)
            or authorization.pass_a_sha256 != digest(base.pass_a)
            or authorization.pass_b_sha256 != digest(base.accepted_calibration.decision)
            or digest(context["authority_digests"]) != authorization.authority_sha256):
        raise ValueError("detailed_v2_current_authority_mismatch")
    if (b2_result.get("contract") != "production-b2-accepted-result-v1"
            or b2_result.get("generation_id") != base.execution_generation_id
            or b2_result.get("ticker") != base.ticker
            or b2_result.get("security_id") != authorization.security_id
            or b2_result.get("authorization_sha256") != digest(authorization.model_dump(mode="json"))
            or b2_result.get("request_sha256") != authorization.request_sha256
            or b2_result.get("output_sha256") != digest(b2_result.get("output"))
            or b2_result.get("status") != "PASS"):
        raise ValueError("detailed_v2_accepted_b2_required")
    verdict = canonical.validate_result(b2_result["output"], b2_request,
        expected_request_sha256=authorization.request_sha256)
    if verdict["status"] != "PASS":
        raise ValueError("detailed_v2_semantic_reject")
    output = b2_result["output"]["new_buyer_shadow"]
    axes = b2.presentation_plan(output, context)
    decision = base.accepted_calibration.decision
    score = decision["directional_buy_score"]
    text = "\n".join([
        "AI 분석 판단: " + decision["overall_direction"],
        f"판단 균형: BUY {score:.1f} : SELL {10-score:.1f}",
        "판단 확신도: " + {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}[decision["confidence"]],
        "신규 매수자: " + axes["fundamental_attractiveness"],
        "진입 시점: " + axes["entry_timing"]["state"],
        "보유자: " + {"HOLDABLE": "HOLD", "REVIEW": "REVIEW", "REDUCE": "REDUCE"}[decision["holder"]],
        decision["holder_reason"],
    ])
    row = _row("judgment", "axes-v2", text,
        facts=tuple(sorted(set(output["reason_evidence_refs"] + output["active_risk_refs"]))),
        hashes=(base.acceptance_sha256, digest(b2_result), digest(authorization.model_dump(mode="json"))),
        formatting="accepted-independent-b2-axes-v2")
    rows = (row, *(r for r in presentation.rows if r.section != "judgment"))
    binding = dict(base=presentation.acceptance_sha256, request=digest(b2_request), result=digest(b2_result),
        authorization=digest(authorization.model_dump(mode="json")), rows=[r.model_dump(mode="json") for r in rows])
    return DetailedStockMessagePlanV2(base=presentation, b2_request=b2_request, b2_result=b2_result,
        authorization=authorization, rows=rows, acceptance_sha256=digest(binding))


def render_detailed_v2(packet, plan):
    expected = build_detailed_plan_v2(packet=packet, base=plan.base, b2_request=plan.b2_request,
        b2_result=plan.b2_result, authorization=plan.authorization)
    if expected != plan:
        raise ValueError("detailed_v2_plan_changed")
    text = _render_rows(packet, plan.rows)
    forbidden = {"기존 등록 가격 규칙", "데이터 주의", "다음 확인", "미확인"}
    if any(line.strip() in forbidden for line in text.splitlines()):
        raise ValueError("detailed_v2_removed_heading")
    base = plan.base.base if isinstance(plan.base, KrForwardMessagePlan) else plan.base
    return {"text": text, "generation_id": base.execution_generation_id,
            "plan_sha256": plan.acceptance_sha256, "content_sha256": digest(text), "status": "PASS"}
