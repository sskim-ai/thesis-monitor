"""B2-owned New Buyer and backend timing, with unchanged accepted v1 body rows."""
from typing import Literal

from app.services.detailed_stock_message_service import (
    DetailedStockMessagePlan, DetailedRow, _render_rows, _row, _source_number, detailed_render,
)
from app.services.production_b2_execution import ProductionB2ExecutionAuthorizationV1, ProductionB2ExecutionAuthorizationV2
from app.services.kr_forward_valuation_message import KrForwardMessagePlan, render as render_kr
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services import new_buyer_v2_contract as b2
from app.services import new_buyer_request_owner as canonical


class DetailedStockMessagePlanV2(ContractModel):
    contract: Literal["accepted-detailed-stock-message-v2"] = "accepted-detailed-stock-message-v2"
    base: DetailedStockMessagePlan | KrForwardMessagePlan
    b2_request: dict
    b2_result: dict
    authorization: ProductionB2ExecutionAuthorizationV2 | ProductionB2ExecutionAuthorizationV1
    rows: tuple[DetailedRow, ...]
    acceptance_sha256: str


def _reported_quarter_rows(packet, base):
    if packet.market != "us":
        return ()
    from app.services.issuer_fiscal_week_policy import QUARTER
    source=base.source_stock
    stock=source["packet"]["stocks"][0]
    groups = {}
    for fact in stock.get("fact_catalog", ()):
        basis = fact["fields"].get("reported_quarter_basis")
        if not basis:
            continue
        entry = source.get("source_graph", {}).get(fact["fact_id"],{})
        current, prior = basis["current_duration"], basis["prior_duration"]
        if (fact["fact_type"] != "earnings_comparison" or basis["contract"] != QUARTER
                or basis["normalization"] != "NONE" or {current, prior} != {"P13W", "P14W"}
                or source.get("fresh_run_id") != base.source_generation_id
                or "canonical:"+fact["fact_id"] not in source.get("comparative_fact_refs", ())
                or entry.get("fact_sha256") != digest(fact)
                or entry.get("occurrences") != fact["fields"]["source_occurrences"]
                or entry.get("quality_receipt_sha256") != fact["quality_receipt_sha256"]
                or basis != fact["field_dependency_receipts"].get("reported_quarter_basis")):
            raise ValueError("detailed_v2_reported_quarter_owner_binding")
        key = current, prior, basis["policy_receipt_sha256"]
        groups.setdefault(key, []).append(fact["fact_id"])
    return tuple(_row("business", "reported-quarter-weeks-" + policy[:12],
        f"공시 기준 전년 동기 비교: 이번 분기 {current[1:-1]}주 vs 전년 분기 {prior[1:-1]}주. "
        "분기 길이를 보정하지 않은 공시 금액 기준이며, 전년 기저에 따라 증가율이 크게 보일 수 있습니다.",
        facts=tuple(sorted(refs)), hashes=(policy,), formatting="as-reported-fiscal-quarter-not-normalized-v1")
        for (current, prior, policy), refs in sorted(groups.items()))


def _us_sr_rows(packet, base, axes, security_id):
    if packet.market != "us":
        return ()
    from decimal import Decimal, InvalidOperation
    from datetime import date, datetime
    import re
    from app.services.dated_multiframe_research import period_end
    from app.services.market_session import us_market_session
    from app.services.us_dated_source_sr import CONTRACT, REFERENCE, valid_reference_lineage
    source = base.source_stock
    chart = source["packet"]["stocks"][0]["chart_context"]
    ref = chart.get("structure", {}).get("price_structure_v3", {})
    if (ref.get("contract") != CONTRACT or ref.get("scope") != "DATED_REFERENCE_ONLY"
            or ref.get("ticker") != packet.ticker or ref.get("security_id") != security_id
            or ref.get("currency") != "USD" or ref.get("adjustment_basis") != "provider_adjusted_price_v1"
            or ref.get("source_generation") != base.source_generation_id
            or ref.get("source_generation") != source.get("fresh_run_id")
            or not isinstance(ref.get("source_plan_sha256"), str)
            or not re.fullmatch(r"[a-f0-9]{64}", ref["source_plan_sha256"])
            or ref.get("eligible_for_current_price") is not False or ref.get("eligible_for_b2_timing") is not False
            or not valid_reference_lineage(ref)
            or ref.get("as_of") != ref.get("completed_sources", {}).get("daily", {}).get("completed")):
        return ()
    # Dated adjusted S/R has its own receipt/session proof, not the isolated
    # technical-view date and not the separate regular_close amount/basis.
    clock = source["packet"].get("source_time_domains", {})
    try:
        observed = datetime.fromisoformat(ref["observed_at"])
        original = datetime.fromisoformat(clock.get("price_source_frozen_at") or clock["started_at"])
        target = date.fromisoformat(ref["as_of"])
        if (observed.utcoffset() is None or original != observed
                or clock.get("run_id") != ref["source_generation"]
                or us_market_session(observed).latest_completed_regular_session_date != date.fromisoformat(ref['target_session'])):
            return ()
        completed = ref["completed_sources"]
        if set(completed) != {"daily", "weekly", "monthly"}:
            return ()
        for tf, proof in completed.items():
            if (proof.get("bar_state") != "COMPLETE" or proof.get("calendar") != "XNYS"
                    or proof.get("completion_owner") != "normalize_completed_bars"
                    or proof.get("source_role") != "adjusted_" + tf
                    or proof.get("completed_count", 0) < 1
                    or date.fromisoformat(proof["completed"]) > target
                    or period_end(date.fromisoformat(proof["label"]), tf, "us").isoformat() != proof["completed"]
                    or not all(isinstance(proof.get(key), str) and re.fullmatch(r"[a-f0-9]{64}", proof[key])
                        for key in ("receipt_sha256", "normalized_sha256", "original_rows_sha256", "completed_rows_sha256"))):
                return ()
        facts = {f["fact_id"]: f for f in source["packet"]["stocks"][0].get("fact_catalog", ())}
        bound = any(node.get("source") == "sealed_stock_roles" and node.get("ticker") == packet.ticker
            and node.get("fact_sha256") == digest(facts.get(fact_id))
            and all(node.get("roles", {}).get("adjusted_" + tf, {}).get(key) == proof[key]
                for tf, proof in completed.items() for key in ("receipt_sha256", "normalized_sha256"))
            for fact_id, node in source.get("source_graph", {}).items())
        if not bound:
            return ()
    except (KeyError, TypeError, ValueError):
        return ()
    rows = []
    for zone in ref.get("zones", ())[:4]:
        labels = {"support": "지지", "resistance": "저항"}
        refs = zone.get("source_refs", [])
        if (zone.get("side") not in labels or not refs
                or not all(isinstance(x, str) and REFERENCE.fullmatch(x) for x in (zone.get("id"), *refs))):
            continue
        try:
            low, high = Decimal(zone["low"]), Decimal(zone["high"])
        except (InvalidOperation, KeyError, TypeError):
            continue
        if not low.is_finite() or not high.is_finite() or not 0 < low <= high:
            continue
        number = f"${low:,.2f}–${high:,.2f}"
        if low < Decimal("0.01") or low != high and format(low, ".2f") == format(high, ".2f"):
            number = f"${low:f}–${high:f}"
        tier = {"near": "가까운 ", "major": "주요 구조 "}.get(zone.get("tier"), "")
        excluded = f" ({ref['target_session']} 해당 일봉 불일치 제외)" if ref.get('latest_daily_exclusion') else ''
        rows.append(_row("price", zone["id"],
            f"{ref['as_of']} 미국 완료 거래일 기준 조정봉 V3 참고{excluded} {tier}{labels[zone['side']]} USD: {number} "
            "(현재가·평가배수·B2 진입 권한 아님)",
            facts=(zone["id"], *refs), hashes=(digest(ref),),
            formatting="dated-us-v3-no-b2-or-quote-authority-v1"))
    support = _us_accepted_support_row(packet, base, axes, security_id, ref["as_of"])
    return (*rows, support) if support is not None else tuple(rows)


def _us_accepted_support_row(packet, base, axes, security_id, session):
    """Reuse the accepted KR9 registry invariants, without taking a V3 quote."""
    timing = axes["entry_timing"]
    accepted = base.accepted_calibration
    entries = accepted.entries
    refs = entries.get("tactical_watch_basis") or []
    if (timing["state"] not in {"WAIT_FOR_ZONE", "FAVORABLE_NOW"}
            or timing["reason"] != "EXACT_SELECTED_ZONE_RELATION"
            or timing["selected"] != accepted.decision.get("tactical_choice")
            or entries.get("tactical_watch_status") != "RESOLVED"
            or base.valuation.security_id != security_id or len(refs) != 1
            or refs[0] not in timing["evidence_refs"]):
        return None
    matches = [e for e in packet.evidence if e.ref_id == refs[0] and e.label == "chart_support_zone"]
    if len(matches) != 1 or not matches[0].source_ref.startswith("stock.fact_catalog."):
        return None
    evidence = matches[0]
    fact_id = evidence.source_ref.removeprefix("stock.fact_catalog.")
    source = base.source_stock
    stock = source["packet"]["stocks"][0]
    quote = stock["current_price_context"]
    try:
        fact, node, low_reg, low = _source_number(fact_id, "fields.zone_low", source)
        _, _, high_reg, high = _source_number(fact_id, "fields.zone_high", source)
    except (KeyError, ValueError):
        return None
    frame = stock["chart_context"].get("timeframes", {}).get(fact["fields"].get("timeframe"), {})
    if (fact["fact_type"] != "chart_support_zone" or fact.get("source") != "deterministic_ohlcv_structure"
            or node.get("ticker") != packet.ticker or not evidence.source_time
            or evidence.source_time.subject_ticker != packet.ticker
            or evidence.source_time.canonical_fact_sha256 != digest(fact)
            or fact["as_of_date"] != evidence.as_of or evidence.as_of != session
            or quote.get("as_of_date") != session or frame.get("as_of_date") != session
            or frame.get("candle", {}).get("close") != quote.get("current_price")
            or source.get("fresh_run_id") != source["packet"].get("source_time_domains", {}).get("run_id")
            or frame.get("quality") != "available"
            or (quote.get("price_basis"), frame.get("price_basis")) not in {
                ("adjusted_close", "adjusted"), ("unadjusted_close", "unadjusted"), ("regular_close", "unadjusted")}
            or any(value != "USD" for value in (fact["fields"].get("currency"), quote.get("currency"),
                entries.get("tactical_currency"), low_reg["unit"], high_reg["unit"]))
            or low != entries.get("tactical_watch_low") or high != entries.get("tactical_watch_high") or not 0 < low <= high):
        return None
    warning = " (가격 관찰 참고, 신규 매수 권고 아님)" if axes["fundamental_attractiveness"] == "AVOID" else ""
    return _row("price", "accepted-tactical-support",
        f"B2 수락 관찰 지지({session} USD): ${low:,.2f}–${high:,.2f}{warning}",
        facts=tuple(refs), hashes=(digest(fact), digest(node), digest(low_reg), digest(high_reg)),
        numeric=(fact_id + ":fields.zone_low", fact_id + ":fields.zone_high"),
        formatting="accepted-tactical-support-registry-v1")


def _selected_support_row(packet, base, timing, security_id, *, new_buyer=None):
    """Keep the accepted tactical selection separate from a V3 structural zone."""
    accepted = base.accepted_calibration
    entries = accepted.entries
    refs = entries.get("tactical_watch_basis") or []
    if (timing["state"] not in {"WAIT_FOR_ZONE", "FAVORABLE_NOW"}
            or timing["reason"] != "EXACT_SELECTED_ZONE_RELATION"
            or timing["selected"] != accepted.decision.get("tactical_choice")
            or entries.get("tactical_watch_status") != "RESOLVED"
            or base.valuation.security_id != security_id
            or len(refs) != 1 or refs[0] not in timing["evidence_refs"]):
        return None
    ref = refs[0]
    matches = [row for row in packet.evidence if row.ref_id == ref and row.label == "chart_support_zone"]
    if len(matches) != 1 or not matches[0].source_ref.startswith("stock.fact_catalog."):
        return None
    evidence = matches[0]
    fact_id = evidence.source_ref.removeprefix("stock.fact_catalog.")
    source = base.source_stock
    stock = source["packet"]["stocks"][0]
    quote = stock["current_price_context"]
    try:
        fact, node, low_reg, low = _source_number(fact_id, "fields.zone_low", source)
        _, _, high_reg, high = _source_number(fact_id, "fields.zone_high", source)
    except (KeyError, ValueError):
        return None
    currency = {"kr": "KRW", "us": "USD"}[packet.market]
    timeframe = fact["fields"].get("timeframe")
    labels = {"daily": "일봉", "weekly": "주봉", "monthly": "월봉"}
    frame = stock["chart_context"].get("timeframes", {}).get(timeframe, {})
    basis = quote.get("price_basis")
    session = packet.assessment_date
    if (fact["fact_type"] != "chart_support_zone" or fact.get("source") != "deterministic_ohlcv_structure"
            or node.get("ticker") != packet.ticker or not evidence.source_time
            or evidence.source_time.subject_ticker != packet.ticker
            or evidence.source_time.canonical_fact_sha256 != digest(fact)
            or fact["as_of_date"] != evidence.as_of or evidence.as_of != session
            or quote.get("as_of_date") != session or frame.get("as_of_date") != session
            or frame.get("candle", {}).get("close") != quote.get("current_price")
            or source["fresh_run_id"] != source["packet"]["source_time_domains"]["run_id"]
            or timeframe not in labels or frame.get("quality") != "available"
            or (basis, frame.get("price_basis")) not in {
                ("adjusted_close", "adjusted"), ("unadjusted_close", "unadjusted"), ("regular_close", "unadjusted")}
            or any(value != currency for value in (fact["fields"].get("currency"), quote.get("currency"),
                entries.get("tactical_currency"), low_reg["unit"], high_reg["unit"]))
            or low != entries.get("tactical_watch_low") or high != entries.get("tactical_watch_high")
            or not 0 < low <= high):
        return None
    from app.services.price_structure_v3_renderer_service import _price_display

    basis_label = "조정봉" if basis == "adjusted_close" else "비조정봉"
    text = f"진입 관찰 지지 구간({session} {labels[timeframe]}·{basis_label}): " \
           f"{_price_display(low, currency)}–{_price_display(high, currency)}"
    if new_buyer == "AVOID":
        text += " (가격 관찰 참고, 신규 매수 권고 아님)"
    return _row("price", "accepted-tactical-support", text, facts=(ref,),
        hashes=(digest(fact), digest(node), digest(low_reg), digest(high_reg)),
        numeric=(fact_id + ":fields.zone_low", fact_id + ":fields.zone_high"),
        formatting="accepted-tactical-support-registry-v1")


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
    if packet.market == "us":
        rows += (*_reported_quarter_rows(packet, base), *_us_sr_rows(packet, base, axes, authorization.security_id))
    if packet.market == "kr":
        support = _selected_support_row(packet, base, axes["entry_timing"], authorization.security_id,
                                        new_buyer=axes["fundamental_attractiveness"])
        if support is not None:
            rows += (support,)
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
    result = {"text": text, "generation_id": base.execution_generation_id,
              "plan_sha256": plan.acceptance_sha256, "content_sha256": digest(text), "status": "PASS"}
    if type(plan.authorization) is ProductionB2ExecutionAuthorizationV2:
        result['NO_SEND'] = True
    return result
