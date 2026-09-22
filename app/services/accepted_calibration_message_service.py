"""Faithful rendering of an accepted calibration result, without legacy synthesis."""
import hashlib
import json
import math

from pydantic import Field

from app.services.cross_market_decision_engine_service import FrozenModel
from app.services.directional_balance_service import render_directional_balance
from app.services.accepted_directional_balance_service import accepted_directional_balance


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


class AcceptedCalibrationPlan(FrozenModel):
    contract: str = "accepted-calibration-message-v1"
    ticker: str
    source_generation_id: str
    execution_generation_id: str
    evidence_packet_sha256: str
    decision: dict[str, object]
    entries: dict[str, object]
    claim_lineage: dict[str, tuple[str, ...]]
    acceptance: dict[str, object]
    acceptance_sha256: str
    quote_context: dict[str, object] | None = None
    render_schema: int = Field(default=1, ge=1, le=1)


class AcceptedMarketCalibration(FrozenModel):
    market: str
    assessment_date: str
    source_context: dict[str, object]
    decision: dict[str, object]
    acceptance: dict[str, object]
    acceptance_sha256: str
    numeric_catalog: dict[str, object] | None = None


def calibration_market_render(plan):
    from app.services.us_full_message_service import render_us_full_market_message

    expected = dict(status="PASS", errors=[], market=plan.market,
        assessment_date=plan.assessment_date, source_context_sha256=digest(plan.source_context),
        decision_sha256=digest(plan.decision))
    if plan.numeric_catalog is not None:
        expected["numeric_catalog_sha256"] = digest(plan.numeric_catalog)
    if plan.acceptance != expected or plan.acceptance_sha256 != digest(expected):
        raise ValueError("accepted_market_binding_mismatch")
    if plan.market not in ("us", "kr") or plan.decision["market"] != plan.market.upper():
        raise ValueError("accepted_market_identity_mismatch")
    labels = {"BROAD_RISK_ON": "시장 전반 위험 선호", "NARROW_LEADERSHIP": "일부 업종 주도",
        "MIXED": "방향 혼재", "BROAD_RISK_OFF": "시장 전반 위험 회피", "DATA_INSUFFICIENT": "판단 자료 부족"}
    confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    lines = ["시장 판단: " + labels[plan.decision["regime"]],
        "판단 확신도: " + confidence[plan.decision["confidence"]]]
    lines.extend(str(plan.decision[k]) for k in ("breadth_state", "leadership", "flows_or_participation", "rates_or_macro_context"))
    if plan.numeric_catalog is not None:
        from app.services.market_numeric_claim_service import (
            render_typed_market_facts, final_market_numeric_audit, narrative_errors,
        )
        if (narrative_errors(plan.decision) or plan.numeric_catalog.get("market") != plan.market
                or plan.numeric_catalog.get("assessment_date") != plan.assessment_date):
            raise ValueError("accepted_market_numeric_narrative_or_identity_invalid")
        narrative = "시장 해석\n" + "\n".join(lines)
        text = render_typed_market_facts(plan.numeric_catalog,plan.source_context)+"\n\n"+narrative
        if final_market_numeric_audit(text,plan.numeric_catalog,plan.source_context,narrative)["status"] != "PASS":
            raise ValueError("accepted_market_final_numeric_binding_invalid")
        return text
    if plan.market == "us":
        rendered = render_us_full_market_message(plan.source_context)
        if rendered.status != "PASS":
            raise ValueError("accepted_market_production_fact_render_failed")
        return rendered.text + "\n\n시장 해석\n" + "\n".join(lines)
    session = plan.source_context.get("session") or {}
    completed = session.get("latest_completed_regular_session_date")
    if not completed:
        raise ValueError("accepted_market_session_missing")
    return "\n".join([f"한국 시장 점검 · {plan.assessment_date}",
        f"완료된 정규장 기준: {completed}", "", *lines])


def calibration_render(packet, plan):
    # Import here to share the existing production result and language guards.
    from app.services.accepted_decision_v2_service import (
        AcceptedDecisionSource, AcceptedRenderValidationResult, RenderedProductionAcceptedDecision,
        _EXACT_NUMBER, _INTERNAL_LABEL_LANGUAGE, _ORDER_LANGUAGE,
    )
    errors = []
    expected = {"status": "PASS", "errors": [], "ticker": plan.ticker,
        "source_generation_id": plan.source_generation_id,
        "execution_generation_id": plan.execution_generation_id,
        "evidence_packet_sha256": digest(packet.model_dump(mode="json")),
        "decision_sha256": digest(plan.decision), "entries_sha256": digest(plan.entries),
        "claim_lineage_sha256": digest(plan.claim_lineage)}
    if plan.quote_context is not None:
        expected['quote_context_sha256'] = digest(plan.quote_context)
    if (not plan.source_generation_id or not plan.execution_generation_id
            or plan.ticker != packet.ticker or expected != plan.acceptance
            or digest(expected) != plan.acceptance_sha256
            or plan.evidence_packet_sha256 != expected["evidence_packet_sha256"]):
        raise ValueError("accepted_calibration_identity_or_validation_binding")
    row = plan.decision
    try:
        balance = accepted_directional_balance(row["directional_buy_score"], row["overall_direction"])
    except ValueError as exc:
        raise ValueError("accepted_calibration_render_invalid:" + str(exc)) from exc
    allowed = {r.ref_id for r in packet.evidence}
    consumed = set()
    for name in ("supporting_refs", "contradicting_refs", "confidence_caution_refs",
                 "data_quality_refs", "reevaluation_refs", "holder_reason_evidence_refs", "new_buyer_risk_refs"):
        consumed.update(row[name])
    if any(not plan.claim_lineage.get(r) or not set(plan.claim_lineage[r]) <= allowed for r in consumed):
        errors.append("accepted_calibration_claim_lineage_missing")
    reasons = [row[k] for k in ("overall_reason", "holder_reason", "new_buyer_reason")]
    for reason in reasons:
        if not isinstance(reason, str) or not reason.strip():
            errors.append("accepted_reason_missing")
            continue
        if _ORDER_LANGUAGE.search(reason) or _INTERNAL_LABEL_LANGUAGE.search(reason):
            errors.append("accepted_language_invalid")
        if _EXACT_NUMBER.search(reason):
            errors.append("accepted_unbound_numeric")
        if any(ref in reason for ref in allowed | set(plan.claim_lineage)):
            errors.append("accepted_internal_ref_leak")
    direction = {"BUY": "매수 관점", "HOLD": "중립·관찰", "SELL": "매도 관점"}
    buyer = {"ATTRACTIVE": "신규 진입 매력 있음", "WAIT": "확인 대기", "AVOID": "신규 진입 보류"}
    holder = {"HOLDABLE": "보유 유지 가능", "REVIEW": "보유 근거 재검토", "REDUCE": "노출 축소 검토"}
    confidence = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    lines = [f"{packet.company_name} ({packet.ticker})", f"판단 기준일: {packet.assessment_date}", "",
        f"종합 판단: {direction[row['overall_direction']]}",
        f"신규 관찰자: {buyer[row['new_buyer']]}", f"보유자: {holder[row['holder']]}",
        f"판단 균형: {render_directional_balance(balance)}",
        f"판단 확신도: {confidence[row['confidence']]}", "", "핵심 판단", str(row["overall_reason"]),
        "", "대상별 판단", "신규 관찰자: " + str(row["new_buyer_reason"]),
        "보유자: " + str(row["holder_reason"])]
    if plan.quote_context is not None:
        from datetime import date
        quote = plan.quote_context
        try:
            valid = (quote.get('contract') == 'current-price-context-v1'
                     and quote.get('availability') == 'ready'
                     and date.fromisoformat(quote['as_of_date']) <= date.fromisoformat(packet.assessment_date)
                     and quote.get('price_basis') in {'adjusted_close', 'close', 'intraday'})
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            errors.append('accepted_quote_asof_invalid')
        else:
            basis = {'adjusted_close':'조정 종가', 'close':'종가', 'intraday':'장중 관측'}[quote['price_basis']]
            lines.insert(2, f"가격 자료 기준: {quote['as_of_date']} · {basis}")
    for prefix, label in (("fundamental_entry", "기업가치 기준 진입 범위"),
                          ("tactical_watch", "가격 흐름 관찰 구간")):
        low, high = [plan.entries.get(prefix + suffix) for suffix in ("_low", "_high")]
        if low is None and high is None:
            continue
        currency = plan.entries.get(prefix.split("_")[0] + "_currency")
        if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in (low, high)) or low <= 0 or high < low or not currency
                or not plan.entries.get(prefix + "_basis")
                or plan.entries.get(prefix + "_status") not in ("RESOLVED", "SINGLE_METHOD_LOW_CONFIDENCE")):
            errors.append("accepted_range_invalid")
            continue
        precision = 0 if currency == "KRW" else 2
        lines.extend(["", f"{label}: {low:,.{precision}f} ~ {high:,.{precision}f} {currency}"])
        if prefix == "tactical_watch":
            lines.append("가격 흐름 관찰 구간은 적정가치 평가가 아닙니다.")
    if errors:
        raise ValueError("accepted_calibration_render_invalid:" + ",".join(errors))
    return RenderedProductionAcceptedDecision(ticker=packet.ticker,
        accepted_decision=row["overall_direction"], accepted_source=AcceptedDecisionSource.CANDIDATE,
        accepted_directional_balance=balance, text="\n".join(lines),
        validation=AcceptedRenderValidationResult(valid=True, errors=()))
