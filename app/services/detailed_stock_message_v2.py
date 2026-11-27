"""B2-owned New Buyer and backend timing, with unchanged accepted v1 body rows."""
from dataclasses import dataclass
from decimal import Decimal
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


@dataclass(frozen=True)
class EntryAssessment:
    """One source-bound presentation result for explanation and final action."""

    quality: str
    reason_code: str
    location: str
    note: str
    next_confirmation: str | None = None
    failure_condition: str | None = None
    warnings: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    confirmed_breakout: bool = False
    invalidation_ref: str | None = None
    invalidation_price: Decimal | None = None
    invalidation_timeframe: str | None = None
    scenario: dict | None = None


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
        rows.append(_row("price", zone["id"],
            f"참고 {tier}{labels[zone['side']]}: {number}",
            facts=(zone["id"], *refs), hashes=(digest(ref),),
            formatting="dated-us-reference-zone-v2"))
    if not rows:
        return ()
    excluded = f" · {ref['target_session']} 해당 일봉 불일치 제외" if ref.get('latest_daily_exclusion') else ''
    heading = _row("price", "dated-us-sr-context",
        f"참고 지지·저항: {ref['as_of']} 완료 조정봉 · USD{excluded}\n"
        "진입 관찰 지지 구간과 구분해 보는 가격 구조입니다.",
        facts=tuple(dict.fromkeys(value for row in rows for value in row.source_fact_ids)),
        hashes=(digest(ref),), formatting="dated-us-reference-context-v2")
    return (heading, *rows)



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
    from app.services.new_buyer_base_contract import number
    if (fact["fact_type"] != "chart_support_zone"
            or fact.get("source") not in {"deterministic_ohlcv_structure", "price_structure_wave_fibonacci_v3"}
            or (fact.get("source") == "price_structure_wave_fibonacci_v3"
                and (not fact["fields"].get("price_anchor_refs") or not fact["fields"].get("confirmation_bar")
                     or fact["fields"].get("entry_role") != "support"))
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
            or number(low) != number(entries.get("tactical_watch_low"))
            or number(high) != number(entries.get("tactical_watch_high"))
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


def _entry_gap_details(catalog, context, selected):
    """Separate no usable candidate, selection gaps, and incompatible data."""
    candidate = next((row for row in catalog if row['candidate_id'] == selected), None)
    if any(row['eligible'] for row in catalog):
        if candidate is None or not candidate['eligible']:
            return ('ELIGIBLE_NOT_SELECTED', '적격 지지 후보가 있으나 선택된 진입 구간 확인 필요',
                    '적격 완료봉 지지 후보 선택과 기준가격 위치 확인')
        return ('SELECTED_RELATION_UNCONFIRMED', '선택 지지와 기준가격의 위치 관계 확인 필요',
                '선택 지지와 같은 가격 기준의 위치 관계 확인')
    rows = ([candidate] if candidate is not None else
            context.get('entry_candidate_diagnostics') or catalog)
    reason_sets = [set(row.get('failure_reasons', [])) for row in rows]
    common = set.intersection(*reason_sets) if reason_sets else set()
    # A shared price/frame problem explains why every candidate failed. Avoid
    # replacing it with incidental gaps in an unrelated reference candidate.
    reasons = common or {code for codes in reason_sets for code in codes}
    if (context.get('reference_only_support_reason') == 'NO_QUALIFIED_STRUCTURE_V3_REFERENCE_ONLY'
            and not (reasons - {'STORED_PRICE_RULE_REFERENCE_ONLY',
                                'V3_COMPLETED_FRAME_BASIS_MISSING','SOURCE_USE_OR_CURRENCY_INELIGIBLE'})):
        return ('NO_ELIGIBLE_SUPPORT', '완료봉의 적격 지지 후보 없음 · 표시된 V3 지지는 참고 전용',
                '같은 가격 기준의 적격 지지 후보 형성 확인')
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
    unavailable_codes = {'STORED_PRICE_RULE_REFERENCE_ONLY', 'V3_COMPLETED_FRAME_BASIS_MISSING',
        'PRICE_ENTRY_DENIED', 'DAILY_ENTRY_DENIED', 'SUPPORT_ENTRY_DENIED',
        'SUPPORT_FRAME_ENTRY_DENIED', 'SOURCE_USE_OR_CURRENCY_INELIGIBLE',
        'SUPPORT_EVIDENCE_MISSING_OR_UNSUPPORTED', 'ZONE_EVIDENCE_MISSING_OR_DUPLICATE',
        'SUPPORT_FRAME_UNAVAILABLE'}
    if reasons - unavailable_codes:
        return ('DATA_INCOMPATIBLE', ' · '.join(notes[:2]) or '가격·완료봉 근거 연결 확인 필요',
                '가격·완료봉 자료의 연결을 확인한 뒤 진입 위치 재평가')
    note = '현재 적격 지지 구간 없음'
    specific = [value for value in notes if value != note]
    if specific:
        note += ' · ' + ' · '.join(specific[:2])
    return ('NO_ELIGIBLE_SUPPORT', note, '완료봉에 근거한 적격 지지 구간 확보 후 진입 위치 확인')


def _entry_gap_note(catalog, context, selected):
    return _entry_gap_details(catalog, context, selected)[1]


def _entry_assessment(model_input, timing, context, market, session):
    """Assess the frozen B context once, without promoting reference-only zones."""
    from app.services.new_buyer_base_contract import number
    from app.services.new_buyer_input_owner import _statement, tactical_catalog

    location, warnings, failure = None, [], None
    invalidation_ref, invalidation_price, invalidation_timeframe = None, None, None
    scenario = None

    def assessed(quality, code, note, refs=(), confirmation=None):
        refs = tuple(sorted(refs))
        return EntryAssessment(quality=quality, reason_code=code,
            location=location or '진입 판단: ' + note, note=note,
            next_confirmation=confirmation, failure_condition=failure,
            warnings=tuple(warnings), evidence_refs=refs,
            confirmed_breakout=_confirmed_breakout(context, refs),
            invalidation_ref=invalidation_ref, invalidation_price=invalidation_price,
            invalidation_timeframe=invalidation_timeframe, scenario=scenario)

    if context is None:
        return assessed('INSUFFICIENT_EVIDENCE', 'CONTEXT_MISSING', '진입 근거 상세 없음')
    if (digest(context) != model_input["authority_digests"]["context"]
            or context["ticker"] != model_input["ticker"]
            or context["source_evidence_binding"]["source_generation_id"] != model_input["source_generation"]):
        raise ValueError("detailed_v2_entry_context_mismatch")
    if session is None:
        return assessed('INSUFFICIENT_EVIDENCE', 'SESSION_MISSING', '완료 거래일 근거 확인 필요')
    if context["current_price"].get("as_of") not in (None, session):
        return assessed('INSUFFICIENT_EVIDENCE', 'PRICE_SESSION_MISMATCH',
            '완료 거래일과 가격·차트 세션 불일치',
            confirmation='완료 거래일과 가격·차트 자료의 기준일 일치 확인')
    catalog = tactical_catalog(context, model_input["ticker"], model_input["security_id"],
                               source_generation_id=model_input['source_generation'])
    candidate = next((r for r in catalog if r["candidate_id"] == timing["selected"]), None)
    if not candidate or timing["relation"] == "UNRESOLVED" or not candidate["relation_basis_proven"]:
        code, note, confirmation = _entry_gap_details(catalog, context, timing['selected'])
        return assessed('INSUFFICIENT_EVIDENCE', code, note, confirmation=confirmation)
    location = "가격 위치: 선택된 관찰 지지 구간 " + {
        "INSIDE": "안", "ABOVE": "위", "BELOW": "아래 — 구조 재확인"}[timing['relation']]
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
        return assessed('INSUFFICIENT_EVIDENCE', 'ENTRY_FRAME_UNLINKED',
            '같은 세션·가격 기준의 진입 품질 근거 없음',
            confirmation='선택 지지·완료봉·기준가격의 연결 확인')
    refs = set(timing["evidence_refs"]) | {daily_id} | {"canonical:chart:" + f for f in frames}
    low, high = number(candidate["low"]), number(candidate["high"])
    from app.services.entry_candidate_basis import selected_entry_scenario
    scenario = selected_entry_scenario(context, candidate)
    if scenario is not None or 'selected_entry_scenario' in model_input:
        if scenario != model_input.get('selected_entry_scenario'):
            raise ValueError('detailed_selected_scenario_mismatch')
    if scenario:
        proof = scenario['evidence_ref']
        refs.add(proof)
        stop = number(scenario.get('invalidation'))
        frame = scenario['timeframe']
        if stop is not None and frame in ('daily', 'weekly') and 0 < stop < low:
            invalidation_ref, invalidation_price, invalidation_timeframe = proof, stop, frame
            failure = ('완료 주봉 종가가 선택 무효화선 아래면 구조 재검토' if frame == 'weekly'
                       else '선택 무효화선 아래 완료 일봉 종가 2회 연속, 또는 해당 선 아래 종가와 거래량비율 1.2배 이상·분산 매도 동반 시 구조 재검토')
        else:
            stop = None
        status = scenario.get('status')
        if stop is not None and (price <= stop or status in ('hard_invalid', 'accelerated_invalid')):
            return assessed('BLOCKED', 'SELECTED_SUPPORT_INVALID', '현재 기준선 대비 선택 지지 위험', refs,
                            '선택 구조와 완료봉 종가 재평가')
        if status in ('recovered_review', 'lower_timeframe_review', 'higher_timeframe_review'):
            return assessed('CAUTION', 'SELECTED_WEEKLY_CONFIRMATION', '선택 주봉 구조 확인 필요', refs,
                            '다음 완료 주봉과 선택 기준선의 관계 확인')
        if scenario.get('active_obstacle') or scenario.get('current_overlap'):
            return assessed('CAUTION', 'SUPPORT_RESISTANCE_OVERLAP', '현재가 기준 적격 저항 중첩', refs,
                            '현재 저항 중첩의 해소 확인')
        if scenario.get('band_overlap'):
            warnings.append('가정 지지 접근 구간의 저항 중첩')
        if scenario.get('band_reason') == 'INTERMEDIATE_ROLE_UNCONFIRMED':
            warnings.append('하단 가정 진입 시 중간 구조의 역할 미확정')
        if scenario.get('possible_current_barrier') is not None:
            warnings.append('현재 목표보다 가까운 역할 미확정 구간도 관찰 필요')
        state_ref = 'canonical:chart:structure:state'
        state = _statement(evidence.get(state_ref, {}))
        reasons = set(state.get('reasons', ()))
        if 'distribution' in reasons:
            return assessed('CAUTION', 'COMMON_CHART_RISK', '분산 매도 수급', refs | {state_ref}, '실제 매도 압력 해소 확인')
        # Near resistance is a price observation, not another independent
        # veto on an already calculated favorable risk/reward.
        upside = number(scenario.get('current_upside_pct'))
        if upside is not None and upside <= 2:
            warnings.append('근접 저항: 상승 여력과 무효화 위험폭 함께 검토')
        if status == 'wick_only_review':
            warnings.append('저가는 기준선 아래였지만 완료 종가는 기준선 이상')
        if scenario.get('observed_support_reclaim'):
            warnings.append('지지 확인 이후 현재 고정 구간 하단 기준 종가 이탈·재회복 관측')
        # A global breakout may belong to a different candidate. Do not use
        # it as the selected scenario's own confirmation.
        target, ratio = number(scenario.get('current_target')), number(scenario.get('current_rr'))
        rating = scenario.get('classification')
        if (stop is None or target is None or not stop < price < target or ratio is None or ratio <= 0
                or rating not in ('attractive', 'conditional', 'poor_chase')):
            return assessed('INSUFFICIENT_EVIDENCE', 'CURRENT_PRICE_RISK_REWARD_MISSING',
                            '선택 지지의 현재가 손익비 미산출', refs, '유효한 무효화선과 가까운 저항 확인')
        if rating == 'attractive':
            return assessed('SUPPORTED', 'CURRENT_PRICE_RISK_REWARD_ATTRACTIVE', '선택 지지의 현재가 손익비가 지지함', refs)
        return assessed('CAUTION', 'CURRENT_PRICE_RISK_REWARD_' + rating.upper(),
                        '현재가 손익비가 조건부' if rating == 'conditional' else '현재가 추격 손익비가 불리함',
                        refs, '선택 지지와 손익비 2배 가격 조건 재확인')
    rr_ref = "canonical:chart:structure:risk_reward:current_price"
    inv_ref = "canonical:chart:structure:invalidation"
    inv = _statement(evidence.get(inv_ref, {}))
    linked_invalidation = (evidence.get(inv_ref, {}).get("label") == "chart_invalidation"
        and inv.get("chart_only") is True and inv.get("timeframe") in frames
        and inv.get("currency") == currency and number(inv.get("support_low")) == low
        and number(inv.get("price")) is not None and 0 < number(inv["price"]) < low)
    if linked_invalidation:
        refs.add(inv_ref)
        invalidation_ref, invalidation_price = inv_ref, number(inv['price'])
        invalidation_timeframe = inv['timeframe']
        frame_label = {"daily": "일봉", "weekly": "주봉", "monthly": "월봉"}[inv['timeframe']]
        # These are the existing producer's rule thresholds, not observed prices.
        failure = (
            '완료 일봉 종가가 선택 무효화선 아래에서 2회 연속 마감하거나, '
            '해당 선 아래 종가에 거래량비율 1.2배 이상·분산 매도가 함께 확인되면 구조 재검토'
            if inv['timeframe'] == 'daily' else
            '완료 주봉 종가가 선택 무효화선 아래면 구조 재검토'
            if inv['timeframe'] == 'weekly' else f'선택 {frame_label}의 무효화 조건 충족 시 구조 재검토')
        if inv.get("status") in {"hard_invalid", "accelerated_invalid"}:
            note = "해당 지지의 차트 무효화 조건 충족"
            frame = {"daily": "일봉", "weekly": "주봉"}.get(inv.get("trigger_timeframe"))
            dates = inv.get("trigger_dates")
            if frame and isinstance(dates, list) and dates:
                note += f" · 완료 {frame} 기준일 " + ", ".join(str(day) for day in dates)
            return assessed('BLOCKED', 'SELECTED_SUPPORT_INVALID', note, refs,
                            '무효화된 선택 지지의 구조 재평가')
        if inv.get("status") in {"higher_timeframe_review", "lower_timeframe_review", "recovered_review"}:
            weekly = f"완료 주봉(기준일 {inv['weekly_bar_date']})" if inv.get("weekly_bar_date") else "완료 주봉"
            if inv["status"] == "higher_timeframe_review":
                return assessed('CAUTION', 'LEGACY_CROSS_FRAME_COMPARISON',
                    f"{weekly}과 현재 선택 일봉 기준선의 위치 비교 · 과거 지지 이탈 여부 미확인",
                    refs)
            elif inv["status"] == "recovered_review":
                note = f"{weekly} 종가는 현재 선택 지지의 무효화선 아래 · 현재 일봉 종가는 해당 선 이상"
            else:
                note = "선택 주봉 지지에 대한 일봉 경고 · 주봉 무효화는 완료 주봉 확인 필요"
            return assessed('CAUTION', 'SELECTED_WEEKLY_CONFIRMATION', note, refs,
                            '다음 완료 주봉 종가가 선택 지지 무효화선 이상인지 확인')
        if inv.get("status") == "wick_only_review":
            return assessed('CAUTION', 'WICK_ONLY', '저가는 현재 무효화선 아래였지만 종가는 해당 선 이상',
                            refs, '다음 완료 일봉 종가의 무효화선 유지 확인')
        if (inv.get('status') == 'intact' and inv.get('timeframe') == 'daily'
                and inv.get('comparison_basis') == 'CURRENT_SELECTED_SUPPORT'
                and inv.get('historical_break_evidence') == 'NOT_ESTABLISHED'
                and inv.get('hard_weekly') is True):
            weekly = f"완료 주봉(기준일 {inv['weekly_bar_date']})" if inv.get('weekly_bar_date') else '완료 주봉'
            warnings.append(f"{weekly} 종가는 현재 선택 일봉의 무효화선 아래 · 과거 지지 이탈 여부 미확인")
    for ref, row in evidence.items():
        fields = _statement(row)
        if fields.get("currency") != currency:
            continue
        if (ref.startswith("canonical:chart:structure:nearest_resistance:") and
                row["label"] == "chart_resistance_zone" and matching_frame(fields.get("timeframe"))):
            floor, ceiling = number(fields.get("zone_low")), number(fields.get("zone_high"))
            if None not in (floor, ceiling) and 0 < floor <= ceiling and floor <= high and low <= ceiling:
                return assessed('CAUTION', 'SUPPORT_RESISTANCE_OVERLAP', '관찰 지지 구간과 저항이 겹침',
                    refs | {ref, "canonical:chart:" + fields["timeframe"]}, '선택 지지와 저항의 중첩 해소 확인')
    rr = _statement(evidence.get(rr_ref, {}))
    # These are the structure producer's price/volume conclusions on the bound
    # chart. Its HOLDER and hypothetical support-entry scenarios are not signals here.
    state_ref = "canonical:chart:structure:state"
    state = _statement(evidence.get(state_ref, {})) if evidence.get(state_ref, {}).get("label") == "chart_state" else {}
    reasons = state.get("reasons", ())
    if state.get("state") == "WAIT" and state.get("user_semantics") == "price_structure_wait_not_sell_command":
        conditions = {"support_resistance_overlap": ("지지·저항 중첩", "선택 지지와 저항의 중첩 해소 확인"),
            "strong_or_medium_resistance_within_2pct": ("근접 저항",
                "가까운 저항까지 간격 2% 초과 또는 저항 위 2회 연속 종가·거래량비율 1.2배 이상 확인"),
            "distribution": ("분산 매도 수급", "분산 매도 분류 해소 확인"),
            "rr_below_1_5": ("현재가 손익비 주의", "현재가 손익비 2배 이상 확인(기존 진입 검토 기준)")}
        notes = [text[0] for code, text in conditions.items() if code in reasons]
        if notes:
            confirmation = ' · '.join(text[1] for code, text in conditions.items() if code in reasons)
            return assessed('CAUTION', 'PRICE_STRUCTURE_WAIT', "가격 구조 확인 필요: " + ", ".join(notes),
                            refs | {state_ref}, confirmation)
    if (evidence.get(rr_ref, {}).get("label") == "chart_risk_reward_current_price"
            and rr.get("currency") == currency and rr.get("rr_basis") == rr.get("scenario") == "current_price"
            and number(rr.get("entry")) == price and number(rr.get("ratio")) is not None
            and number(rr.get("invalidation")) is not None and number(rr.get("target")) is not None
            and 0 < number(rr["invalidation"]) < price < number(rr["target"]) and number(rr["ratio"]) > 0):
        rating = rr.get("classification")
        if rating in ("attractive", "conditional", "poor_chase"):
            if rating == "attractive" and not (linked_invalidation and inv.get("status") == "intact"
                    and number(inv["price"]) == number(rr["invalidation"])):
                return assessed('INSUFFICIENT_EVIDENCE', 'RISK_REWARD_INVALIDATION_UNLINKED',
                    '현재가 손익비와 선택 지지의 무효화 근거 연결 부족', refs | {rr_ref},
                    '선택 지지 무효화선과 현재가 손익비 기준의 일치 확인')
            note = {"attractive":"현재가 기준 손익비 근거가 지지함", "conditional":"현재가 기준 손익비가 조건부임",
                    "poor_chase":"현재가 기준 추격 손익비가 불리함"}[rating]
            if (state.get("state") == "CONFIRM_ENTRY" and state.get("user_semantics") == "confirmed_breakout_not_buy_command"
                    and {"two_close_breakout", "volume_ratio_confirmed"}.issubset(reasons)):
                note += " · 종가 돌파와 거래량 확인"
                refs.add(state_ref)
            return assessed('SUPPORTED' if rating == 'attractive' else 'CAUTION',
                'CURRENT_PRICE_RISK_REWARD_' + rating.upper(), note, refs | {rr_ref},
                None if rating == 'attractive' else '현재가 손익비 2배 이상 확인(기존 진입 검토 기준)')
    return assessed('INSUFFICIENT_EVIDENCE', 'CURRENT_PRICE_RISK_REWARD_MISSING',
        '현재가 기준의 적격 손익비·확인 근거 부족', refs,
        '현재가·선택 지지 무효화선·가까운 저항을 연결한 손익비 확인')


def _entry_quality(model_input, timing, context, market, session):
    """Compatibility view of the single assessment used by production rendering."""
    result = _entry_assessment(model_input, timing, context, market, session)
    return result.quality, ' · '.join((result.note, *result.warnings)), result.evidence_refs


def _buyer_action(stance, relation, quality, *, reason_class=None, confirmed_breakout=False,
                  assessment=None, technical=None):
    if stance == "AVOID":
        return "신규 매수 회피"
    structural_review = relation == "BELOW" or quality == "BLOCKED"
    review = ("현재 기준선 대비 선택 지지 구조 재검토" if assessment and assessment.scenario
              else "지지 이탈 구조 재검토")
    if stance == "WAIT":
        reasons = {
            "BUSINESS_MIXED": "사업 근거 혼재 해소 대기",
            "ECONOMIC_UNCERTAINTY": "구체적 기업·가격 불확실성 확인 대기",
            "BUSINESS_GATE_NOT_MET": "사업 근거 확인 대기",
            "BUSINESS_EVIDENCE_UNCERTAINTY": "사업 근거의 불확실성 해소 대기",
            "VALUATION_UNRESOLVED": "가치평가 자료 확인 대기",
            "VALUATION_NEUTRAL": "가치평가 매력 개선 대기",
            "VALUATION_BURDENSOME": "가치평가 부담 완화 대기",
            "CONFIDENCE_UNCERTAINTY": "판단을 제한하는 근거 확인 대기",
        }
        action = reasons.get(reason_class, "신규매수 판단 근거 확인 대기")
        return action + " · " + review if structural_review else action
    if structural_review:
        return review
    if technical is not None and quality == 'SUPPORTED' and relation in {'INSIDE', 'ABOVE'}:
        state, change = technical.get('state'), technical.get('change')
        if state == 'ADVERSE':
            return '기술지표 개선 또는 확인 신호 대기'
        # State is the current entry-relevant judgment. Change is explanatory,
        # not a second veto. MIXED expresses meaningful conflict, not failure
        # to satisfy an independent approval flag.
        if state == 'MIXED':
            return '조건부 신규 매수 검토 가능'
        if state == 'INSUFFICIENT' and (relation == 'INSIDE' or confirmed_breakout):
            return '조건부 신규 매수 검토 가능 · 기술적 확인 필요'
        if state == 'SUPPORTIVE' and (relation == 'ABOVE' or change == 'DETERIORATING'
                                      or (assessment and getattr(assessment, 'warnings', ()))):
            return '조건부 신규 매수 검토 가능'
        if assessment and assessment.scenario and assessment.scenario.get('status') == 'wick_only_review':
            if state == 'SUPPORTIVE' or confirmed_breakout:
                return '조건부 신규 매수 검토 가능'
            return '완료 종가 회복 유지와 기술지표 개선 확인 대기'
        if relation == 'ABOVE' and confirmed_breakout:
            return '조건부 신규 매수 검토 가능'
    if relation == "ABOVE":
        if confirmed_breakout:
            return "돌파·거래량 확인 완료, 선택된 지지 구간 기준의 진입은 가격 조정 대기"
        return "가격 조정 또는 신규 확인 신호 대기"
    if relation != "INSIDE":
        if assessment is not None and assessment.next_confirmation:
            return assessment.next_confirmation + " 대기"
        return "진입 조건 미확인·대기"
    if quality != 'SUPPORTED' and assessment is not None:
        return (assessment.next_confirmation + ' 대기' if assessment.next_confirmation
                else '추가 확인 조건 미정·대기')
    return "신규 매수 검토 가능" if quality == "SUPPORTED" else "추가 가격 확인 대기"


def _entry_location(model_input, timing, context, market, session):
    return _entry_assessment(model_input, timing, context, market, session).location


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


def final_entry_action(output, model_input, assessment):
    """One action owner for both detailed and cohort presentation."""
    technical = output.get('technical_assessment')
    action = _buyer_action(output['new_buyer'], output['timing_context']['relation'], assessment.quality,
        reason_class=output['reason_class'], confirmed_breakout=assessment.confirmed_breakout,
        assessment=assessment, technical=technical if b2.c60_technical_input(model_input) else None)
    if technical and technical['state'] == 'ADVERSE':
        if action in {'신규 매수 검토 가능','조건부 신규 매수 검토 가능'}:
            action = '기술지표 개선 또는 확인 신호 대기'
        elif action != '기술지표 개선 또는 확인 신호 대기':
            action += ' · 기술지표 약화 추가 확인'
    return action


def _entry_lines(output, model_input, entry_context, market, session, *, assessment=None):
    timing = output["timing_context"]
    result = assessment or _entry_assessment(model_input, timing, entry_context, market, session)
    technical = output.get('technical_assessment')
    action = final_entry_action(output, model_input, result)
    reason = {"BUSINESS_MIXED":"사업 근거 혼재", "BUSINESS_GATE_NOT_MET":"사업 근거 요건 미충족",
              "ECONOMIC_UNCERTAINTY":"현재 가격에서 중요한 경제적 불확실성",
              "BUSINESS_EVIDENCE_UNCERTAINTY":"사업 근거 불확실", "VALUATION_UNRESOLVED":"가치평가 근거 부족",
              "CONFIDENCE_UNCERTAINTY":"확신을 제한하는 근거", "ACTIVE_ADVERSE_UNCOMPENSATED":"활성 중대 위험",
              "VALUATION_NEUTRAL":"중립적 가치평가", "VALUATION_BURDENSOME":"부담스러운 가치평가",
              "QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE":"사업과 가치평가 근거가 지지"}.get(
                  output["reason_class"], "신규매수 판단 근거 확인 필요")
    detail = result.location if result.note in result.location else f"{result.location} · {result.note}"
    if result.warnings:
        detail += '\n추가 관찰: ' + ' · '.join(result.warnings)
    if result.next_confirmation:
        detail += '\n가격 확인 조건: ' + result.next_confirmation
    elif result.quality in {'CAUTION', 'INSUFFICIENT_EVIDENCE'}:
        detail += '\n가격 확인 조건: 추가 확인 조건 미정'
    if result.failure_condition:
        detail += '\n구조 재검토 조건: ' + result.failure_condition
    lines = [f"신규매수 근거: {reason}"]
    refs = set(result.evidence_refs)
    if 'economic_reason' in output:
        valuation = output['valuation_context']
        economic_refs = set(valuation['business_evidence_refs'] + valuation['valuation_evidence_refs']
                            + output['reason_evidence_refs'])
        explanation = b2.economic_reason(output['economic_reason'], economic_refs | b2.historical_price_refs(model_input))
        label = {'SUPPORTIVE':'경제적 가격 지지','NEUTRAL':'중립','BURDENSOME':'가격 부담',
                 'UNRESOLVED':'적격 배수 자료 부족'}[valuation['state']]
        lines.append(f'기업·가격 판단: {label} — {explanation}')
        refs.update(economic_refs)
        refs.update(output.get('provider_reference_refs', ()))
    lines.append(detail)
    if technical is not None:
        explanation = b2.technical_reason(technical['reason'], technical['evidence_refs'])
        label = {'SUPPORTIVE': '지지', 'MIXED': '혼재', 'ADVERSE': '약화',
                 'INSUFFICIENT': '자료 부족'}[technical['state']]
        change = {'IMPROVING': '회복·개선', 'DETERIORATING': '악화 진행',
                  'STABLE': '변화 제한'}.get(technical.get('change'))
        if change:
            label += ' · ' + change
        lines.append(f'기술지표 판단: {label} — {explanation}')
        refs.update(technical['evidence_refs'])
    lines.append(f'최종 신규매수 행동: {action}')
    return tuple(lines), tuple(sorted(refs))


def _entry_invalidation_row(packet, base, assessment, session):
    """Show an existing selected-support level only through its numeric owner."""
    ref = assessment.invalidation_ref
    if not ref or not ref.startswith('canonical:') or not session:
        return None
    fact_id = ref.removeprefix('canonical:')
    scoped = assessment.scenario is not None
    path = 'fields.entry_scenario.invalidation' if scoped else 'fields.price'
    try:
        fact, node, registry, value = _source_number(fact_id, path, base.source_stock)
    except (KeyError, ValueError):
        return None
    currency = {'kr': 'KRW', 'us': 'USD'}[packet.market]
    fields = fact['fields']
    timeframe = assessment.invalidation_timeframe
    from app.services.new_buyer_base_contract import number
    owner = fields.get('entry_scenario', {}) if scoped else fields
    if (fact['fact_type'] != ('chart_support_zone' if scoped else 'chart_invalidation') or fact['as_of_date'] != session
            or owner.get('chart_only') is not True or fields.get('timeframe') != timeframe
            or fields.get('currency') != currency or registry['unit'] != currency
            or node.get('ticker') != packet.ticker or number(value) != number(assessment.invalidation_price)):
        return None
    from app.services.price_structure_v3_renderer_service import _price_display
    label = {'daily': '일봉', 'weekly': '주봉', 'monthly': '월봉'}[timeframe]
    return _row('price', 'selected-support-invalidation',
        f'선택 지지 무효화선({session} {label}): {_price_display(value, currency)} · 완료봉 조건으로 판정',
        facts=(ref,), hashes=(digest(fact), digest(node), digest(registry)),
        numeric=(fact_id + ':' + path,), formatting='selected-support-invalidation-registry-v1')


def _entry_scenario_row(packet, base, assessment, session):
    from app.services.new_buyer_base_contract import number
    from app.services.price_structure_v3_renderer_service import _price_display
    sc = assessment.scenario
    if not sc or sc['as_of'] != session:
        return None
    ref = sc['evidence_ref']
    fact_id = ref.removeprefix('canonical:')
    hashes, paths, lines = set(), [], []
    unit = {'us':'USD', 'kr':'KRW'}[packet.market]
    def display(key, *, ratio=False, pct=False):
        path = 'fields.entry_scenario.' + key
        if key not in sc:
            return None
        try:
            f, n, r, value = _source_number(fact_id, path, base.source_stock)
        except (KeyError, ValueError):
            return None
        if (f['fact_type'] != 'chart_support_zone' or f['as_of_date'] != session
                or n.get('ticker') != packet.ticker or f['fields'].get('currency') != unit
                or f['fields']['entry_scenario'].get('chart_only') is not True
                or r['unit'] != ('x' if ratio else 'pct' if pct else unit) or number(value) != number(sc[key])):
            return None
        hashes.update((digest(f), digest(n), digest(r)))
        paths.append(fact_id + ':' + path)
        return (('2배 미만(반올림 경계)' if number(value) < 2 and f'{value:.2f}' == '2.00'
                 else f'{value:.2f}배') if ratio else f'{value:.2f}%' if pct else _price_display(value, unit))
    target, rr = display('current_target'), display('current_rr', ratio=True)
    if rr and sc.get('classification') in ('conditional', 'poor_chase') and (number(rr.removesuffix('배')) or 0) >= 2:
        rr = '2배 미만(반올림 경계)'
    reason_labels = {'ACTIVE_RESISTANCE_OVERLAP': '현재가 저항 중첩',
        'SUPPORT_RESISTANCE_OVERLAP': '지지·저항 중첩',
        'INTERMEDIATE_ROLE_UNCONFIRMED': '중간 구조 역할 미확정',
        'RESISTANCE_UNAVAILABLE': '가까운 적격 저항 미확보',
        'INVALIDATION_UNAVAILABLE': '무효화선 미확보',
        'PRICE_AT_OR_BELOW_INVALIDATION': '현재가가 무효화선 이하',
        'invalidation_unavailable': '무효화선 미확보',
        'non_positive_upside_or_downside': '유효 상승·하락폭 없음'}
    if target:
        lines.append('현재가 기준 가까운 저항 하단 ' + target + (' · 손익비 ' + rr if rr else ' · 손익비 미산출'))
    elif sc.get('current_rr_reason'):
        lines.append('현재 손익비 미산출: ' + reason_labels.get(sc['current_rr_reason'], '가격 구조 재확인 필요'))
    if target and not rr and sc.get('current_rr_reason'):
        lines.append('미산출 사유: ' + reason_labels.get(sc['current_rr_reason'], '가격 구조 재확인 필요'))
    up, down = display('current_upside_pct', pct=True), display('current_downside_pct', pct=True)
    if up and down:
        lines.append(f'저항까지 상승 여력 {up} · 무효화선까지 하락 위험폭 {down}')
    barrier = display('possible_current_barrier')
    if barrier:
        lines.append('가까운 역할 미확정 구간 하단 ' + barrier + ' (저항 확정 아님)')
    current_ceiling = display('current_rr2_ceiling_inward')
    if current_ceiling:
        lines.append('현재 목표 고정 RR 2배 수학적 상한 ' + current_ceiling + ' (관찰 지지 아님)')
    band, ceiling = display('band_target'), display('rr2_ceiling_inward')
    if band and ceiling:
        overlap = sc.get('rr2_intersection')
        a, b = display('rr2_low'), display('rr2_high')
        note = (a + '–' + b if a and b else '표시 정밀도보다 좁음' if overlap == 'BELOW_DISPLAY_PRECISION'
                else '교집합 없음' if overlap == 'EMPTY' else '미확인')
        midpoint_rr = display('band_rr', ratio=True)
        assumed = ' (기존 저항 재접근 가정)' if sc.get('band_target_assumption') else ''
        label = '기존 구조 참고' if assessment.quality == 'BLOCKED' else '지지 접근 가정'
        lines.append(f'{label}: 가까운 저항 {band}{assumed}' +
                     (f' · 중간값 RR {midpoint_rr}' if midpoint_rr else '') +
                     f' · 손익비 2배 상한(내향 표시) {ceiling} · 지지 교집합 {note}')
    elif sc.get('band_reason') or sc.get('invalidation_reason'):
        lines.append('가정 진입 가격대 미산출: ' +
                     reason_labels.get(sc.get('band_reason'), '유효한 무효화·저항 조건 미확정'))
    if not lines:
        return None
    return _row('price', 'selected-support-rr', '\n'.join(lines), facts=(ref,),
        hashes=tuple(sorted(hashes)), numeric=tuple(paths), formatting='selected-support-scenario-v1')


def _provider_reference_row(context):
    reference = context.get('provider_reference_context')
    if not reference:
        return None
    from app.services.price_structure_v3_renderer_service import _price_display
    provider = 'Kiwoom' if reference['provider']=='kiwoom' else 'Finnhub'
    currency = reference['currency']
    lines, refs = [], set()
    for item in reference['direct']:
        label = {'eps':'EPS(기간 미명시)','bps':'BPS(기간 미명시)',
                 'epsTTM':'EPS(TTM 표기)','bookValuePerShareQuarterly':'BVPS(분기 표기)'}[item['field']]
        amount = _price_display(item['value'],currency)
        if item['zero_is_provider_observation_not_proven_zero_earnings']:
            amount += ' (공급자 0 관측, 실적 0 확정 아님)'
        note = ''
        if 'reference_quote_quotient' in item:
            note = (f" · 기준가 단순 몫 {item['reference_quote_quotient']:.2f}배"
                    " (공급자 현재 배수 재계산 아님)")
            refs.add(item['comparison_metric_ref'])
        lines.append(f'{provider} 직접 {label}: {amount}'+note)
        refs.add(item['ref_id'])
    for item in reference['history']:
        whole = item['all']
        recent = item.get('recent_five_years')
        label = item['metric']
        def display(window):
            text = (f"{window['positive_periods']}/{window['observed_periods']} 양수 관측"
                    f" · {window['first_period']}~{window['last_period']}")
            if window['positive_periods']:
                text += (f" · P25/50/75 {window['percentile_25']:.2f}/"
                         f"{window['percentile_50']:.2f}/{window['percentile_75']:.2f}배")
                if 'current_percentile' in window:
                    text += f" · 현재 배수 이하 관측 {window['current_percentile']:.1f}%"
            if window['nonpositive_periods'] or window['missing_value_periods'] or window['conflicting_periods']:
                text += (f" · 비양수 {window['nonpositive_periods']}, 누락 "
                         f"{window['missing_value_periods']}, 충돌 {window['conflicting_periods']}")
            if not window['price_sample_sufficient']:
                text += ' · 가격 산출용 표본 제한'
            return text
        lines.append(f'{provider} 분기 {label} 최근 5년: '+(display(recent) if recent else '관측 없음'))
        if not recent or recent['positive_periods'] == 0:
            lines.append(f'{provider} 분기 {label} 전체: '+display(whole))
        refs.add(item['ref_id'])
        if item.get('current_metric_ref'):
            refs.add(item['current_metric_ref'])
    if not lines:
        return None
    retrieved = reference['retrieval_timestamp'][:10]
    metric_day = reference.get('metric_asof')
    lines.append(f'공급자 조회 {retrieved} · 지표일 {metric_day or "미명시"}'
                 ' · 자체 산출 주간 배수와 별개 · 정확한 산식/주식 기준·재무일 미확정')
    return _row('valuation','provider-native-reference','\n'.join(lines),
        facts=tuple(sorted(refs)),hashes=(reference['raw_sha256'],reference['source_receipt_sha256']),
        formatting='provider-native-quarterly-reference-v1')


def _historical_price_row(context, output, assessment, *, scenario_row=None):
    """Render only the exact frozen deterministic candidates, never model numbers."""
    historical = context.get('historical_price_context')
    if not historical or not historical['candidates']:
        return None
    from decimal import ROUND_FLOOR
    from app.services.new_buyer_base_contract import number
    from app.services.price_structure_v3_renderer_service import _price_display
    currency = historical['currency']
    candidates = historical['candidates']
    review = output['economic_price_review']
    selected = next((r for r in candidates if r['candidate_id'] == review['candidate_id']), None)
    lines, used = [], []
    combined = False
    methods = {'HISTORICAL_TRAILING_PE_QUANTILE':'PER', 'HISTORICAL_PB_QUANTILE':'PBR'}
    for family, label in methods.items():
        for origin in (None,'PROVIDER_QUARTERLY_REFERENCE'):
            rows = [r for r in candidates if r['method_family']==family and r.get('origin')==origin]
            if not rows:
                continue
            row = next((r for r in rows if r['a_selected_tier']), None)
            if row is None:
                row = next((r for r in rows if r['quantile_band']=='P50_P75'), rows[0])
            low, high = (_price_display(row[k], currency) for k in ('low','high'))
            relation = {'BELOW':'현재가 하단 미만','INSIDE':'현재가 범위 안','ABOVE':'현재가 상단 초과',
                        'UNRESOLVED':'현재가와 동일 가격 기준 미확정'}[row['relation_to_price']]
            band = row['quantile_band'].replace('_','–')
            name = f'Finnhub 분기 {label}' if origin else f'역사적 {label}'
            lines.append(f'{name} 참고({band}): {low}–{high} · {relation}')
            used.append(row)
    if historical['method_conflict']:
        lines.append('평가 방법 상충 · 단일 가치 범위 미확정')
    if historical.get('provider_method_conflict'):
        lines.append('공급자 PER·PBR 참고 범위 상충 · 단일 가치 범위 미확정')
    if selected is not None:
        used.append(selected)
        label = methods[selected['method_family']]
        if selected.get('origin')=='PROVIDER_QUARTERLY_REFERENCE':
            label = 'Finnhub 분기 '+label
        low, high = (_price_display(selected[k], currency) for k in ('low','high'))
        lines.append(f'조건부 경제적 가치 시나리오({label}): {low}–{high} · 이익·자본 및 배수 가정 유지 전제')
        if review['preferred_boundary'] in ('LOW','HIGH'):
            ceiling = number(selected[review['preferred_boundary'].lower()])
            precision = number(1 if currency == 'KRW' else '0.01')
            ceiling = ceiling.quantize(precision, rounding=ROUND_FLOOR)
            if ceiling > 0:
                lines.append('경제적 선호 가격 상한: ' + _price_display(float(ceiling), currency)
                             + ' · 현재 투자 매력의 자동 제한 아님')
                sc = assessment.scenario or {}
                # Use the very same registered numeric bounds already approved
                # by the C60 scenario renderer. Do not expose denied numbers
                # through a second, derived intersection.
                registry_keys = {sc.get('evidence_ref', '').removeprefix('canonical:')
                                 + ':fields.entry_scenario.' + key for key in ('rr2_low','rr2_high')}
                if (output['new_buyer'] != 'AVOID' and assessment.quality != 'BLOCKED'
                        and (selected.get('origin')!='PROVIDER_QUARTERLY_REFERENCE'
                             or selected.get('quote_basis_comparable') is True)
                        and sc.get('rr2_intersection') == 'DISPLAYABLE'
                        and context.get('selected_entry_scenario') == sc
                        and sc.get('currency') == currency
                        and scenario_row is not None
                        and registry_keys <= set(scenario_row.numeric_registry_keys)):
                    lo, hi = number(sc.get('rr2_low')), number(sc.get('rr2_high'))
                    if lo is not None and hi is not None and lo > 0 and hi >= lo:
                        upper = min(hi, ceiling)
                        note = (_price_display(float(lo), currency) + '–' + _price_display(float(upper), currency)
                                if upper >= lo else '교집합 없음')
                        lines.append('경제적 선호·기술 RR 조건의 관찰 구간: ' + note
                                     + ' · 투자 논지 및 기술 구조 유지 전제')
                        combined = True
    else:
        selectable = (context['business_gate']['v2_business_gate_pass']
                      and not context['active_risk_refs'] and not context['confidence_veto_refs']
                      and context['valuation_evaluability']['evaluability_state'] == 'EVALUABLE')
        lines.append('경제적 가치 시나리오 미확정 · 역사적 참고 범위만 유지' if selectable
                     else '기존 기업·가치평가 조건에 따른 경제적 시나리오 선택 제한')
    refs = {ref for row in used for ref in row['evidence_refs']}
    hashes = {row['candidate_sha256'] for row in used}
    if combined:
        refs.add(assessment.scenario['evidence_ref'])
        hashes.add(scenario_row.acceptance_sha256)
    return _row('valuation', 'historical-price-context', '\n'.join(lines),
        facts=tuple(sorted(refs)), hashes=tuple(sorted(hashes)),
        numeric=tuple(sorted(registry_keys)) if combined else (),
        formatting='existing-deterministic-historical-reference-v1')


def _judgment_text(decision, axes, entry_lines, *, step2=False, price=None):
    score = decision["directional_buy_score"]
    if step2:
        from app.services.detailed_stock_message_service import reference_price_display
        quote = ('기준가격: '+reference_price_display(price.price,price.currency)
                 if price is not None and price.price is not None else '기준가격: 미확보')
        return "\n".join([quote, 'AI 분석 판단: '+decision['overall_direction'],
            f'판단 균형: BUY {score:.1f} : SELL {10-score:.1f}',
            '판단 확신도: '+{'HIGH':'높음','MEDIUM':'중간','LOW':'낮음'}[decision['confidence']],
            '신규 매수자: '+axes['fundamental_attractiveness'],
            '보유자: '+{'HOLDABLE':'HOLD','REVIEW':'REVIEW','REDUCE':'REDUCE'}[decision['holder']],
            entry_lines[-1], decision['holder_reason']])
    return "\n".join([
        "AI 분석 판단: " + decision["overall_direction"],
        f"판단 균형: BUY {score:.1f} : SELL {10-score:.1f}",
        "판단 확신도: " + {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}[decision["confidence"]],
        "신규 매수자: " + {"ATTRACTIVE": ("기업·가격 투자 매력 있음" if 'economic_reason' in axes else "기업 매력 있음"), "WAIT": "조건 확인 대기", "AVOID": "신규 매수 회피"}[
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
    assessment = _entry_assessment(context, output['timing_context'], entry_context, packet.market, price_session)
    entry_lines, entry_refs = _entry_lines(output, context, entry_context, packet.market, price_session,
                                         assessment=assessment)
    step2 = context.get('step2_quality_version') == 1
    text = _judgment_text(decision, axes, entry_lines, step2=step2, price=base.valuation)
    row = _row("judgment", "axes-v2", text,
        facts=tuple(sorted(set(output["reason_evidence_refs"] + output["active_risk_refs"]
            + output["valuation_context"]["valuation_evidence_refs"] + axes["entry_timing"]["evidence_refs"]) | set(entry_refs))),
        hashes=(base.acceptance_sha256, digest(b2_result), digest(authorization.model_dump(mode="json"))),
        formatting="accepted-independent-b2-axes-v2")
    rows = (row, *(r for r in presentation.rows if r.section != "judgment"))
    if step2:
        # These are the exact accepted entry/economic lines, not a second model.
        for i, line in enumerate(entry_lines[:-1]):
            section = 'valuation' if line.startswith(('신규매수 근거:', '기업·가격 판단:')) else 'price'
            rows += (_row(section, 'step2-entry-'+str(i), line, facts=tuple(entry_refs),
                hashes=(digest(b2_result),digest(authorization.model_dump(mode='json'))),
                formatting='accepted-independent-b2-axes-v2'),)
    if packet.market == "us":
        rows += (*_reported_quarter_rows(packet, base), *_us_sr_rows(packet, base, axes, authorization.security_id))
    support = _selected_support_row(packet, base, axes["entry_timing"], authorization.security_id,
        new_buyer=axes["fundamental_attractiveness"], price_session=price_session, entry_context=entry_context)
    scenario_row = None
    if support is not None:
        rows += (support,)
        invalidation = _entry_invalidation_row(packet, base, assessment, price_session)
        if invalidation is not None:
            rows += (invalidation,)
        scenario_row = _entry_scenario_row(packet, base, assessment, price_session)
        if scenario_row is not None:
            rows += (scenario_row,)
    provider_reference = _provider_reference_row(context)
    if provider_reference is not None:
        rows += (provider_reference,)
    historical = _historical_price_row(context, output, assessment, scenario_row=scenario_row)
    if historical is not None:
        rows += (historical,)
    elif step2:
        rows += (_row('valuation','historical-price-unavailable',
            '경제적 선호 가격 미산출 · 적격 주당지표·역사적 배수 조합 미확보',
            facts=(),hashes=(digest(b2_request),),formatting='existing-deterministic-historical-reference-v1'),)
    binding = dict(base=presentation.acceptance_sha256, request=digest(b2_request), result=digest(b2_result),
        authorization=digest(authorization.model_dump(mode="json")), rows=[r.model_dump(mode="json") for r in rows])
    return DetailedStockMessagePlanV2(base=presentation, b2_request=b2_request, b2_result=b2_result,
        authorization=authorization, rows=rows, acceptance_sha256=digest(binding))


def render_detailed_v2(packet, plan, *, entry_context=None):
    expected = build_detailed_plan_v2(packet=packet, base=plan.base, b2_request=plan.b2_request,
        b2_result=plan.b2_result, authorization=plan.authorization, entry_context=entry_context)
    if expected != plan:
        raise ValueError("detailed_v2_plan_changed")
    model_input = plan.b2_request['provider_request']['input']
    if model_input.get('step2_quality_version') == 1:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        base = plan.base.base if isinstance(plan.base, KrForwardMessagePlan) else plan.base
        session = _completed_price_session(packet, base, plan.authorization.security_id)
        generated = datetime.fromisoformat(base.source_stock['packet']['generated_at'])
        header = [f'{packet.company_name}({packet.ticker})',
            '기준 완료장: '+(session or '미확보'),
            '분석 기준 시각(KST): '+generated.astimezone(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M')]
        text = _render_rows(packet, plan.rows, header=header,
            section_order=('judgment','core','business','valuation','price','flow',
                           'thesis_state','warnings','monitoring','reevaluation'))
    else:
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
