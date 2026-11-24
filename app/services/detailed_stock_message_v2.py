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
from app.services.entry_price_basis import frame_matches_price


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
    return tuple(rows)



def _selected_support_row(packet, base, timing, security_id, *, new_buyer=None, price_session=None,
                          entry_context=None):
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
    if entry_context is not None:
        from app.services.entry_candidate_basis import assess_entry_candidates
        catalog = assess_entry_candidates(entry_context, ticker=packet.ticker,
            security_id=security_id, source_generation_id=base.source_generation_id)
        if not any(row['candidate_id'] == timing['selected'] and row['eligible'] for row in catalog):
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
    session = price_session
    price = dict(value=quote.get("current_price"), currency=quote.get("currency"),
                 basis=basis, as_of=quote.get("as_of_date"))
    if (fact["fact_type"] != "chart_support_zone" or fact.get("source") != "deterministic_ohlcv_structure"
            or node.get("ticker") != packet.ticker or not evidence.source_time
            or evidence.source_time.subject_ticker != packet.ticker
            or evidence.source_time.canonical_fact_sha256 != digest(fact)
            or fact["as_of_date"] != evidence.as_of or evidence.as_of != session
            or not frame_matches_price(dict(frame, currency=fact["fields"].get("currency")),
                                       timeframe=timeframe, frame_as_of=frame.get("as_of_date"),
                                       price=price, session=session)
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
    period = f"{session} {labels[timeframe]}·{basis_label}"
    if timeframe != "daily" and frame.get("as_of_date") != session:
        period = f"{session} 평가·{frame['as_of_date']} {labels[timeframe]} 완료봉·{basis_label}"
    text = f"진입 관찰 지지 구간({period}): " \
           f"{_price_display(low, currency)}–{_price_display(high, currency)}"
    if new_buyer == "AVOID":
        text += " (가격 관찰 참고, 신규 매수 권고 아님)"
    return _row("price", "accepted-tactical-support", text, facts=(ref,),
        hashes=(digest(fact), digest(node), digest(low_reg), digest(high_reg)),
        numeric=(fact_id + ":fields.zone_low", fact_id + ":fields.zone_high"),
        formatting="accepted-tactical-support-registry-v1")


def _completed_price_session(packet, base, security_id):
    """Read the calendar-owned target from the already accepted source stock."""
    from datetime import date

    projection = base.source_stock.get("completed_session_current_price")
    if projection is None:
        return None
    if (projection.get("generation_id") != base.source_generation_id
            or projection.get("market") != packet.market
            or projection.get("ticker") != packet.ticker
            or projection.get("canonical_security_id") != security_id):
        raise ValueError("detailed_v2_price_session_identity_mismatch")
    session = projection.get("target_session")
    if not isinstance(session, str) or date.fromisoformat(session).isoformat() != session:
        raise ValueError("detailed_v2_price_session_required")
    return session


def _entry_gap_note(catalog, context, selected):
    """Explain the same candidate exclusions used before B's selection."""
    candidate = next((row for row in catalog if row['candidate_id'] == selected), None)
    if candidate is None and any(row['eligible'] for row in catalog):
        return '선택된 진입 구간 확인 필요'
    rows = [candidate] if candidate is not None else context.get('entry_candidate_diagnostics', [])
    reason_sets = [set(row.get('failure_reasons', [])) for row in rows]
    common = set.intersection(*reason_sets) if reason_sets else set()
    # A shared price/frame problem explains why every candidate failed. Avoid
    # replacing it with incidental gaps in an unrelated reference candidate.
    reasons = common or {code for codes in reason_sets for code in codes}
    labels = (
        ({'PRICE_STATEMENT_INVALID_JSON', 'DAILY_STATEMENT_INVALID_JSON',
          'ZONE_STATEMENT_INVALID_JSON', 'SUPPORT_STATEMENT_INVALID_JSON'},
         '가격·차트 근거 JSON 형식 손상'),
        ({'PRICE_STATEMENT_NOT_OBJECT', 'DAILY_STATEMENT_NOT_OBJECT',
          'ZONE_STATEMENT_NOT_OBJECT', 'SUPPORT_STATEMENT_NOT_OBJECT'},
         '가격·차트 근거의 구조화 형식 확인 필요'),
        ({'SOURCE_GENERATION_MISMATCH'}, '가격 기준 확인 필요 — 수집 실행 연결 불일치'),
        ({'TICKER_MISMATCH', 'SECURITY_MISMATCH', 'SECURITY_IDENTITY_MISSING'},
         '가격 기준 확인 필요 — 종목·증권 연결 불일치'),
        ({'DAILY_FRAME_UNAVAILABLE', 'PRICE_EVIDENCE_MISSING'}, '일봉 데이터 부족'),
        ({'DAILY_FRAME_PRICE_INVALID', 'SUPPORT_FRAME_PRICE_INVALID'}, '완료봉 종가 자료 확인 필요'),
        ({'DAILY_FRAME_CURRENCY_MISMATCH', 'SUPPORT_FRAME_CURRENCY_MISMATCH',
          'PRICE_CURRENCY_MISMATCH', 'ZONE_CURRENCY_MISMATCH'}, '가격 기준 확인 필요 — 통화 불일치'),
        ({'DAILY_FRAME_PRICE_BASIS_MISMATCH', 'SUPPORT_FRAME_PRICE_BASIS_MISMATCH',
          'PRICE_BASIS_MISMATCH', 'ZONE_PRICE_BASIS_MISMATCH'}, '가격 기준 확인 필요 — 조정 기준 불일치'),
        ({'DAILY_FRAME_SESSION_MISMATCH', 'PRICE_SESSION_MISMATCH'},
         '가격 기준 확인 필요 — 완료 거래일과 가격·차트 세션 불일치'),
        ({'ZONE_SESSION_MISMATCH'}, '가격 기준 확인 필요 — 완료 거래일과 지지·차트 세션 불일치'),
        ({'DAILY_FRAME_CLOSE_MISMATCH', 'PRICE_VALUE_MISMATCH'},
         '가격 기준 확인 필요 — 기준가격과 일봉 종가 연결 확인 필요'),
        ({'SUPPORT_TIMEFRAME_MISSING_OR_MISMATCH'}, '지지 봉 기간 미확정'),
        ({'DAILY_FRAME_INCOMPLETE', 'SUPPORT_FRAME_INCOMPLETE'}, '완료되지 않은 봉은 진입 근거에서 제외'),
        ({'DAILY_FRAME_EVALUATION_MISMATCH', 'SUPPORT_FRAME_EVALUATION_MISMATCH',
          'SUPPORT_FRAME_SESSION_MISMATCH', 'SUPPORT_FRAME_CLOSE_MISMATCH'},
         '가격 기준 확인 필요 — 완료봉과 현재 평가일 연결 확인 필요'),
        ({'STORED_PRICE_RULE_REFERENCE_ONLY'}, '등록 가격 규칙은 완료봉 지지 근거가 아님'),
        ({'V3_COMPLETED_FRAME_BASIS_MISSING'}, '참고 지지의 완료봉·가격 기준 연결 없음'),
        ({'PRICE_ENTRY_DENIED', 'DAILY_ENTRY_DENIED', 'SUPPORT_ENTRY_DENIED',
          'SUPPORT_FRAME_ENTRY_DENIED'}, '현재 적격 지지 구간 없음'),
        ({'ZONE_BOUNDS_MISMATCH', 'ZONE_VALUE_INVALID'}, '선택 구간과 원본 지지 가격 연결 확인 필요'),
        ({'SUPPORT_EVIDENCE_MISSING_OR_UNSUPPORTED', 'ZONE_EVIDENCE_MISSING_OR_DUPLICATE',
          'SUPPORT_FRAME_UNAVAILABLE'}, '선택된 지지 근거 또는 완료봉 자료 부족'),
    )
    notes = [text for codes, text in labels if reasons & codes]
    if notes:
        return ' · '.join(notes[:2])
    return '선택된 진입 구간 확인 필요' if catalog else '현재 적격 지지 구간 없음'


def _entry_quality(model_input, timing, context, market, session):
    """Explain the frozen B decision context, never the display-only V3 zones."""
    from app.services.new_buyer_base_contract import number
    from app.services.new_buyer_input_owner import _statement, tactical_catalog

    if context is None:
        return "INSUFFICIENT_EVIDENCE", "진입 근거 상세 없음", ()
    if (digest(context) != model_input["authority_digests"]["context"]
            or context["ticker"] != model_input["ticker"]
            or context["source_evidence_binding"]["source_generation_id"] != model_input["source_generation"]):
        raise ValueError("detailed_v2_entry_context_mismatch")
    if session is None:
        return "INSUFFICIENT_EVIDENCE", "완료 거래일 근거 확인 필요", ()
    if context["current_price"].get("as_of") not in (None, session):
        return "INSUFFICIENT_EVIDENCE", "완료 거래일과 가격·차트 세션 불일치", ()
    catalog = tactical_catalog(context, model_input["ticker"], model_input["security_id"],
                               source_generation_id=model_input['source_generation'])
    candidate = next((r for r in catalog if r["candidate_id"] == timing["selected"]), None)
    if not candidate or timing["relation"] == "UNRESOLVED" or not candidate["relation_basis_proven"]:
        return "INSUFFICIENT_EVIDENCE", _entry_gap_note(catalog, context, timing['selected']), ()
    permissions = {r["ref_id"] for r in context["source_use_projection"]["source_permissions"]
                   if "ENTRY" in r["allowed_uses"]}
    quote = context["current_price"]
    currency = {"kr": "KRW", "us": "USD"}[market]
    price = number(quote.get("value"))
    daily_id = "canonical:chart:daily"
    evidence = {r["ref_id"]: r for r in context["decision_evidence"]
                if r["ref_id"] in permissions and (r["as_of"] == session or
                    r["ref_id"] in {"canonical:chart:weekly", "canonical:chart:monthly"}
                    and frame_matches_price(_statement(r), timeframe=r["ref_id"].rsplit(":", 1)[1],
                                            frame_as_of=r["as_of"], price=quote, session=session))}
    def matching_frame(frame):
        row = evidence.get("canonical:chart:" + str(frame), {})
        return frame_matches_price(_statement(row), timeframe=frame, frame_as_of=row.get("as_of"),
                                   price=quote, session=session)

    frames = {_statement(evidence.get(ref, {})).get("timeframe") for ref in candidate["evidence_refs"]}
    if (not set(timing["evidence_refs"]) <= evidence.keys() or quote.get("as_of") != session
            or quote.get("currency") != currency or not matching_frame("daily")
            or not frames or not all(matching_frame(frame) for frame in frames)):
        return "INSUFFICIENT_EVIDENCE", "같은 세션·가격 기준의 진입 품질 근거 없음", ()
    refs = set(timing["evidence_refs"]) | {daily_id} | {"canonical:chart:" + f for f in frames}
    low, high = number(candidate["low"]), number(candidate["high"])
    rr_ref = "canonical:chart:structure:risk_reward:current_price"
    inv_ref = "canonical:chart:structure:invalidation"
    inv = _statement(evidence.get(inv_ref, {}))
    linked_invalidation = (evidence.get(inv_ref, {}).get("label") == "chart_invalidation"
        and inv.get("chart_only") is True and inv.get("timeframe") in frames
        and inv.get("currency") == currency and number(inv.get("support_low")) == low
        and number(inv.get("price")) is not None and 0 < number(inv["price"]) < low)
    if linked_invalidation:
        refs.add(inv_ref)
        if inv.get("status") in {"hard_invalid", "accelerated_invalid"}:
            return "BLOCKED", "해당 지지의 차트 무효화 조건 충족", tuple(sorted(refs))
        if inv.get("status") == "wick_only_review":
            return "CAUTION", "무효화 가격 일시 이탈로 종가 재확인 필요", tuple(sorted(refs))
    for ref, row in evidence.items():
        fields = _statement(row)
        if fields.get("currency") != currency:
            continue
        if (ref.startswith("canonical:chart:structure:nearest_resistance:") and
                row["label"] == "chart_resistance_zone" and matching_frame(fields.get("timeframe"))):
            floor, ceiling = number(fields.get("zone_low")), number(fields.get("zone_high"))
            if None not in (floor, ceiling) and 0 < floor <= ceiling and floor <= high and low <= ceiling:
                return "CAUTION", "관찰 지지 구간과 저항이 겹침", tuple(sorted(refs | {ref, "canonical:chart:" + fields["timeframe"]}))
    rr = _statement(evidence.get(rr_ref, {}))
    # These are the structure producer's price/volume conclusions on the bound
    # chart. Its HOLDER and hypothetical support-entry scenarios are not signals here.
    state_ref = "canonical:chart:structure:state"
    state = _statement(evidence.get(state_ref, {})) if evidence.get(state_ref, {}).get("label") == "chart_state" else {}
    reasons = state.get("reasons", ())
    if state.get("state") == "WAIT" and state.get("user_semantics") == "price_structure_wait_not_sell_command":
        warnings = {"support_resistance_overlap":"지지·저항 중첩", "strong_or_medium_resistance_within_2pct":"근접 저항",
                    "distribution":"분산 매도 수급", "rr_below_1_5":"현재가 손익비 주의"}
        notes = [text for code, text in warnings.items() if code in reasons]
        if notes:
            return "CAUTION", "가격 구조 확인 필요: " + ", ".join(notes), tuple(sorted(refs | {state_ref}))
    if (evidence.get(rr_ref, {}).get("label") == "chart_risk_reward_current_price"
            and rr.get("currency") == currency and rr.get("rr_basis") == rr.get("scenario") == "current_price"
            and number(rr.get("entry")) == price and number(rr.get("ratio")) is not None
            and number(rr.get("invalidation")) is not None and number(rr.get("target")) is not None
            and 0 < number(rr["invalidation"]) < price < number(rr["target"]) and number(rr["ratio"]) > 0):
        rating = rr.get("classification")
        if rating in ("attractive", "conditional", "poor_chase"):
            if rating == "attractive" and not (linked_invalidation and inv.get("status") == "intact"
                    and number(inv["price"]) == number(rr["invalidation"])):
                return "INSUFFICIENT_EVIDENCE", "현재가 손익비와 선택 지지의 무효화 근거 연결 부족", tuple(sorted(refs | {rr_ref}))
            note = {"attractive":"현재가 기준 손익비 근거가 지지함", "conditional":"현재가 기준 손익비가 조건부임",
                    "poor_chase":"현재가 기준 추격 손익비가 불리함"}[rating]
            if (state.get("state") == "CONFIRM_ENTRY" and state.get("user_semantics") == "confirmed_breakout_not_buy_command"
                    and {"two_close_breakout", "volume_ratio_confirmed"}.issubset(reasons)):
                note += " · 종가 돌파와 거래량 확인"
                refs.add(state_ref)
            return "SUPPORTED" if rating == "attractive" else "CAUTION", note, tuple(sorted(refs | {rr_ref}))
    return "INSUFFICIENT_EVIDENCE", "현재가 기준의 적격 손익비·확인 근거 부족", ()


def _buyer_action(stance, relation, quality, *, reason_class=None, confirmed_breakout=False):
    if stance == "AVOID":
        return "신규 매수 회피"
    if relation == "BELOW" or quality == "BLOCKED":
        return "지지 이탈 구조 재검토"
    if stance == "WAIT":
        reasons = {
            "BUSINESS_MIXED": "사업 근거 혼재 해소 대기",
            "BUSINESS_GATE_NOT_MET": "사업 근거 확인 대기",
            "BUSINESS_EVIDENCE_UNCERTAINTY": "사업 근거의 불확실성 해소 대기",
            "VALUATION_UNRESOLVED": "가치평가 자료 확인 대기",
            "VALUATION_NEUTRAL": "가치평가 매력 개선 대기",
            "VALUATION_BURDENSOME": "가치평가 부담 완화 대기",
            "CONFIDENCE_UNCERTAINTY": "판단을 제한하는 근거 확인 대기",
        }
        return reasons.get(reason_class, "신규매수 판단 근거 확인 대기")
    if relation == "ABOVE":
        if confirmed_breakout:
            return "돌파·거래량 확인 완료, 선택된 지지 구간 기준의 진입은 가격 조정 대기"
        return "가격 조정 또는 신규 확인 신호 대기"
    if relation != "INSIDE":
        return "진입 조건 미확인·대기"
    return "신규 매수 검토 가능" if quality == "SUPPORTED" else "추가 가격 확인 대기"


def _entry_location(model_input, timing, context, market, session):
    """Explain a frozen timing gap without upgrading display-only S/R to ENTRY."""
    from app.services.new_buyer_input_owner import tactical_catalog

    if context is None:
        return "진입 판단: 진입 근거 확인 필요"
    if session is None:
        return "진입 판단: 완료 거래일 근거 확인 필요"
    quote = context["current_price"]
    currency = {"kr": "KRW", "us": "USD"}[market]
    if quote.get("as_of") != session:
        return "진입 판단: 가격 기준 확인 필요 — 완료 거래일과 가격·차트 세션 불일치"
    if quote.get("currency") != currency:
        return "진입 판단: 가격 기준 확인 필요 — 통화 불일치"
    catalog = tactical_catalog(context, model_input["ticker"], model_input["security_id"],
                               source_generation_id=model_input['source_generation'])
    candidate = next((row for row in catalog if row["candidate_id"] == timing["selected"]), None)
    if candidate and candidate['eligible'] and timing["relation"] in {"INSIDE", "ABOVE", "BELOW"}:
        return "가격 위치: 선택된 관찰 지지 구간 " + {
            "INSIDE": "안", "ABOVE": "위", "BELOW": "아래 — 구조 재확인"}[timing["relation"]]
    return "진입 판단: " + _entry_gap_note(catalog, context, timing['selected'])


def _confirmed_breakout(context, refs):
    """Only a typed confirmation already accepted by _entry_quality can qualify."""
    from app.services.new_buyer_input_owner import _statement

    state_ref = "canonical:chart:structure:state"
    if context is None or state_ref not in refs:
        return False
    row = next((row for row in context["decision_evidence"] if row["ref_id"] == state_ref), {})
    state = _statement(row)
    return (row.get("label") == "chart_state" and state.get("state") == "CONFIRM_ENTRY"
            and state.get("user_semantics") == "confirmed_breakout_not_buy_command"
            and {"two_close_breakout", "volume_ratio_confirmed"}.issubset(state.get("reasons", ())))


def _entry_lines(output, model_input, entry_context, market, session):
    timing = output["timing_context"]
    quality, note, refs = _entry_quality(model_input, timing, entry_context, market, session)
    action = _buyer_action(output["new_buyer"], timing["relation"], quality,
                           reason_class=output["reason_class"],
                           confirmed_breakout=_confirmed_breakout(entry_context, refs))
    reason = {"BUSINESS_MIXED":"사업 근거 혼재", "BUSINESS_GATE_NOT_MET":"사업 근거 요건 미충족",
              "BUSINESS_EVIDENCE_UNCERTAINTY":"사업 근거 불확실", "VALUATION_UNRESOLVED":"가치평가 근거 부족",
              "CONFIDENCE_UNCERTAINTY":"확신을 제한하는 근거", "ACTIVE_ADVERSE_UNCOMPENSATED":"활성 중대 위험",
              "VALUATION_NEUTRAL":"중립적 가치평가", "VALUATION_BURDENSOME":"부담스러운 가치평가",
              "QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE":"사업과 가치평가 근거가 지지"}.get(
                  output["reason_class"], "신규매수 판단 근거 확인 필요")
    location = _entry_location(model_input, timing, entry_context, market, session)
    detail = location if note in location else f"{location} · {note}"
    return (f"신규매수 근거: {reason}",
            detail,
            f"최종 신규매수 행동: {action}"), refs


def _judgment_text(decision, axes, entry_lines):
    score = decision["directional_buy_score"]
    return "\n".join([
        "AI 분석 판단: " + decision["overall_direction"],
        f"판단 균형: BUY {score:.1f} : SELL {10-score:.1f}",
        "판단 확신도: " + {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}[decision["confidence"]],
        "신규 매수자: " + {"ATTRACTIVE": "기업 매력 있음", "WAIT": "조건 확인 대기", "AVOID": "신규 매수 회피"}[
            axes["fundamental_attractiveness"]],
        *entry_lines,
        "보유자: " + {"HOLDABLE": "HOLD", "REVIEW": "REVIEW", "REDUCE": "REDUCE"}[decision["holder"]],
        decision["holder_reason"],
    ])


def build_detailed_plan_v2(*, packet, base, b2_request, b2_result, authorization, entry_context=None):
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
    price_session = _completed_price_session(packet, base, authorization.security_id)
    entry_lines, entry_refs = _entry_lines(output, context, entry_context, packet.market, price_session)
    text = _judgment_text(decision, axes, entry_lines)
    row = _row("judgment", "axes-v2", text,
        facts=tuple(sorted(set(output["reason_evidence_refs"] + output["active_risk_refs"]
            + output["valuation_context"]["valuation_evidence_refs"] + axes["entry_timing"]["evidence_refs"]) | set(entry_refs))),
        hashes=(base.acceptance_sha256, digest(b2_result), digest(authorization.model_dump(mode="json"))),
        formatting="accepted-independent-b2-axes-v2")
    rows = (row, *(r for r in presentation.rows if r.section != "judgment"))
    if packet.market == "us":
        rows += (*_reported_quarter_rows(packet, base), *_us_sr_rows(packet, base, axes, authorization.security_id))
    support = _selected_support_row(packet, base, axes["entry_timing"], authorization.security_id,
        new_buyer=axes["fundamental_attractiveness"], price_session=price_session, entry_context=entry_context)
    if support is not None:
        rows += (support,)
    binding = dict(base=presentation.acceptance_sha256, request=digest(b2_request), result=digest(b2_result),
        authorization=digest(authorization.model_dump(mode="json")), rows=[r.model_dump(mode="json") for r in rows])
    return DetailedStockMessagePlanV2(base=presentation, b2_request=b2_request, b2_result=b2_result,
        authorization=authorization, rows=rows, acceptance_sha256=digest(binding))


def render_detailed_v2(packet, plan, *, entry_context=None):
    expected = build_detailed_plan_v2(packet=packet, base=plan.base, b2_request=plan.b2_request,
        b2_result=plan.b2_result, authorization=plan.authorization, entry_context=entry_context)
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
