import asyncio
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import MacroBriefing
from app.models.thesis import InvestmentThesis, NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.analysis_report_service import (
    InvestmentNarrativeGenerator,
    split_kakao_text,
    split_telegram_text,
)
from app.services.daily_digest import build_daily_digest, interpret_macro_briefing
from app.services.daily_digest_renderer import render_daily_digest


MATERIAL_STATUSES = {
    "strengthened",
    "weakened",
    "mixed",
    "invalidation_candidate",
    "invalidated",
    "needs_review",
}

REGIME_LABELS = {
    "goldilocks": "골디락스",
    "stagflation_risk": "스태그플레이션 위험",
    "recession_risk": "경기침체 위험",
    "liquidity_risk_on": "유동성 주도 위험선호",
    "mixed": "혼합",
}

REGIME_INTERPRETATIONS = {
    "goldilocks": "성장·물가 조합 우호, 지속성 확인",
    "stagflation_risk": "비용 압력·성장 둔화 동시 경계",
    "recession_risk": "성장·신용 여건 악화 우선 확인",
    "liquidity_risk_on": "유동성 주도 위험선호, 지속성 확인",
    "mixed": "방향 혼재, 종목별 근거 확인 우선",
}

MACRO_THESIS_LABELS = {
    "us_soft_landing_disinflation": "연착륙",
    "fed_policy_path": "연준경로",
    "ai_capex_cycle": "AI CAPEX",
    "china_korea_export_cycle": "한·중 수출",
    "oil_supply_shock": "유가공급",
}

MACRO_STATUS_LABELS = {
    "strengthening": "근거 우세",
    "intact": "유지",
    "weakening": "약화",
    "structural_break": "재검토",
}

IMPACT_LABELS = {
    "strengthen": "강화",
    "weaken": "약화",
    "mixed": "혼재",
    "neutral": "중립",
}

SERIES_LABELS = {
    "SPY": "S&P",
    "QQQ": "Nasdaq",
    "IWM": "Russell 2000",
    "SOXX": "SOXX",
    "DGS10": "미10년 명목금리",
    "DFII10": "미10년 실질금리",
    "T10YIE": "미10년 기대인플레이션",
    "BAMLH0A0HYM2": "미 하이일드 스프레드",
    "DTWEXBGS": "미 달러지수(광의)",
    "USDKRW": "원/달러",
    "DCOILWTICO": "WTI",
    "VIXCLS": "VIX",
}

REGIME_AXIS_KEYS = {
    "growth_momentum": "성장",
    "inflation_pressure": "물가",
    "liquidity_condition": "유동성",
    "financial_conditions": "금융여건",
    "risk_appetite": "위험선호",
    "earnings_momentum": "이익",
}

SUPPORTED_NOTIFICATION_CHANNELS = {"kakao_self", "telegram"}


def _json_value(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _json_list_value(value: str) -> list[object]:
    parsed = _json_value(value, [])
    return parsed if isinstance(parsed, list) else []


def _unique_text(items) -> list[str]:
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))


def _notification_channel() -> str:
    channel = get_settings().notification_channel.strip().lower()
    if channel not in SUPPORTED_NOTIFICATION_CHANNELS:
        raise RuntimeError(f"Unsupported notification channel: {channel}")
    return channel


def _should_requeue_sent_delivery(
    delivery: NotificationDelivery,
    requeue_sent_before: datetime | None,
) -> bool:
    if delivery.status != "sent" or requeue_sent_before is None:
        return False
    if delivery.sent_at is None:
        return True
    sent_at = delivery.sent_at
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    cutoff = requeue_sent_before
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    return sent_at < cutoff


def _prepare_delivery_for_retry(
    delivery: NotificationDelivery,
    payload: str,
) -> None:
    delivery.payload = payload
    delivery.status = "pending"
    delivery.attempt_count = 0
    delivery.last_error = None
    delivery.sent_at = None


def _report_price(value: object, currency: object) -> str:
    if not isinstance(value, (int, float)):
        return "자료 없음"
    rendered = f"{float(value):,.0f}" if float(value).is_integer() else f"{float(value):,.2f}"
    if currency == "KRW":
        return f"{rendered}원"
    if currency == "USD":
        return f"${rendered}"
    return rendered


def _multiple_text(snapshot: dict[str, object], field: str) -> str:
    status = str(snapshot.get(f"{field}_status", "unavailable"))
    value = snapshot.get(field)
    if status == "not_meaningful":
        return "N/M"
    if status == "value" and isinstance(value, (int, float)):
        return f"{float(value):.1f}배"
    return "자료 없음"


def _multiple_source_text(snapshot: dict[str, object], field: str) -> str:
    source = str(snapshot.get(f"{field}_source", "unavailable"))
    method = str(snapshot.get(f"{field}_method") or "").strip()
    source_label = {
        "provider": "provider 값",
        "derived_trailing": "직접 계산",
        "consensus_forward": "시장 consensus",
        "modeled_forward": "내부 FY1 모델",
        "unavailable": "산출 불가",
    }.get(source, source)
    return f"{source_label} · {method}" if method else source_label


def _bullet_text(items: list[object], empty: str, limit: int = 4) -> str:
    lines = [f"• {item}" for item in items[:limit] if str(item).strip()]
    return "\n".join(lines) or f"• {empty}"


def _audience_price_text(value: str, empty: str) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return "\n".join(f"• {line}" for line in lines) or f"• {empty}"


def _multiple_roles(primary_method: str) -> dict[str, str]:
    method = primary_method.lower()
    if "p/b" in method or "pbr" in method or "roe" in method:
        return {"PER": "보조", "fPER": "보조", "PBR": "주요", "fPBR": "주요"}
    if "forward p/e" in method or "forward pe" in method:
        return {"PER": "참고", "fPER": "주요", "PBR": "참고", "fPBR": "참고"}
    if any(term in method for term in ("sotp", "sum-of-the-parts", "npv", "scenario")):
        return {name: "참고" for name in ("PER", "fPER", "PBR", "fPBR")}
    return {name: "참고" for name in ("PER", "fPER", "PBR", "fPBR")}


def _assessment_report(
    assessment: ThesisAssessment,
    company_name: str,
    thesis: InvestmentThesis | None,
) -> tuple[str, dict[str, object]]:
    labels = {
        "strengthened": "강화",
        "weakened": "약화",
        "mixed": "혼재",
        "no_material_change": "중요 변화 없음",
        "invalidation_candidate": "무효화 후보",
        "invalidated": "무효화",
        "needs_review": "검토 필요",
    }
    label = labels.get(assessment.status, assessment.status)
    business_change = (
        getattr(assessment, "business_thesis_change", None) or assessment.status
    )
    label = labels.get(business_change, business_change)
    earnings_impact = (
        getattr(assessment, "earnings_estimate_impact", None) or "unknown"
    )
    evidence = _json_list_value(assessment.evidence)
    confirmed_facts = _json_list_value(getattr(assessment, "confirmed_facts", "[]"))
    background_confirmed_facts = _json_list_value(
        getattr(assessment, "background_confirmed_facts", "[]")
    )
    inferred_implications = _json_list_value(
        getattr(assessment, "inferred_implications", "[]")
    )
    unknowns = _json_list_value(getattr(assessment, "unknowns", "[]"))
    confirmed_warnings = _json_list_value(
        getattr(assessment, "confirmed_warnings", "[]")
    )
    watch_items = _json_list_value(getattr(assessment, "watch_items", "[]"))
    market_expectation_assessment = _json_value(
        getattr(assessment, "market_expectation_assessment", "{}"), {}
    )
    price_context = _json_value(assessment.price_context, {})
    thesis_snapshot = _json_value(assessment.thesis_snapshot, {})
    thesis_drivers = _json_list_value(thesis.thesis_drivers) if thesis else []
    validation_metrics = _json_list_value(thesis.validation_metrics) if thesis else []
    strengthen_signals = _json_list_value(thesis.strengthen_signals) if thesis else []
    weaken_signals = _json_list_value(thesis.weaken_signals) if thesis else []
    invalidation_signals = _json_list_value(thesis.invalidation_signals) if thesis else []
    price_rules = _json_value(thesis.price_rules, {}) if thesis else {}
    market_expectations = _json_value(thesis.market_expectations, {}) if thesis else {}
    valuation_framework = _json_value(thesis.valuation_framework, {}) if thesis else {}
    expansion_signals = _json_list_value(thesis.multiple_expansion_signals) if thesis else []
    compression_signals = _json_list_value(thesis.multiple_compression_signals) if thesis else []
    macro_exposures = _json_list_value(thesis.macro_exposures) if thesis else []
    valuation_context = _json_value(assessment.valuation_context, {})
    valuation_snapshot = _json_value(
        getattr(assessment, "valuation_snapshot", "{}"), {}
    )
    new_warnings = _json_list_value(getattr(assessment, "new_warnings", "[]"))
    open_warnings = _json_list_value(getattr(assessment, "open_warnings", "[]"))
    open_confirmed_warnings = _json_list_value(
        getattr(assessment, "open_confirmed_warnings", "[]")
    ) or open_warnings
    warning_states_raw = _json_value(
        getattr(assessment, "warning_states", "[]"), []
    )
    warning_states = (
        [item for item in warning_states_raw if isinstance(item, dict)]
        if isinstance(warning_states_raw, list)
        else []
    )
    warning_state_by_text = {
        str(item.get("warning")): item
        for item in warning_states
        if item.get("warning")
    }

    def _warnings_with_provenance(items: list[str], empty: str) -> str:
        if not items:
            return empty
        lines: list[str] = []
        for warning in items:
            state = warning_state_by_text.get(warning, {})
            source_date = state.get("source_date") or state.get("opened_date")
            source_provider = state.get("source_provider") or state.get("source")
            suffix = (
                f"\n  근거: {source_date} {source_provider}"
                if source_date and source_provider
                else ""
            )
            lines.append(f"• {warning}{suffix}")
        return "\n".join(lines)
    prior_open_warnings = [
        item for item in open_confirmed_warnings if item not in new_warnings
    ]
    persistent_watch_risks = _json_list_value(
        getattr(assessment, "persistent_watch_risks", "[]")
    )
    structural_risk = str(
        getattr(assessment, "structural_risk_level", "normal") or "normal"
    )
    assessment_state = str(getattr(assessment, "assessment_state", "final") or "final")
    market_session = str(getattr(assessment, "market_session", "unknown") or "unknown")
    evidence_items = evidence
    evidence_lines = [
        f"• {item.get('title', '제목 없음')} ({item.get('direction', '확인')})"
        for item in evidence_items[:3]
        if isinstance(item, dict)
    ]
    change_text = "\n".join(evidence_lines) or "• 투자 판단을 바꿀 새 근거가 확인되지 않았습니다."
    fact_lines = [f"• {item}" for item in confirmed_facts[:3]]
    inference_lines = [f"• 투자적 해석: {item}" for item in inferred_implications[:2]]
    if fact_lines or inference_lines:
        change_text = "\n".join([*fact_lines, *inference_lines])
    elif business_change == "no_material_change":
        change_text = "• 오늘 투자 논리를 바꿀 신규 확정 사실은 확인되지 않았습니다."
    core_thesis = thesis.core_thesis if thesis else str(
        thesis_snapshot.get("base_thesis", "저장된 핵심 투자 논리가 없습니다.")
    )
    strengthen_text = str(strengthen_signals[0]) if strengthen_signals else "등록된 조건 없음"
    weaken_text = str(weaken_signals[0]) if weaken_signals else "등록된 조건 없음"
    invalidation_text = (
        str(invalidation_signals[0]) if invalidation_signals else "등록된 조건 없음"
    )
    expectation_level = str(market_expectations.get("level", "unknown"))
    expectation_summary = str(
        market_expectations.get("summary", "현재 시장 기대 정보가 등록되지 않았습니다.")
    )
    valuation_method = str(
        valuation_framework.get("primary_method", "평가 방식이 등록되지 않았습니다.")
    )
    multiple_roles = _multiple_roles(valuation_method)
    valuation_caveats = valuation_framework.get("valuation_caveats", [])
    if not isinstance(valuation_caveats, list):
        valuation_caveats = []
    valuation_impact = str(
        valuation_context.get("summary", "Valuation 영향 판단 자료가 없습니다.")
    )
    impact_label = {
        "neutral": "중립",
        "expansion": "확장",
        "compression": "압축",
        "mixed": "혼재",
        "unknown": "판단 자료 부족",
    }.get(str(valuation_context.get("impact", "unknown")), "판단 자료 부족")
    risk_label = {
        "low": "낮음",
        "normal": "보통",
        "elevated": "높아진 상태",
        "high": "높음",
        "critical": "매우 높음",
    }.get(structural_risk, structural_risk)
    expectation_label = {
        "depressed": "매우 낮음",
        "low": "낮음",
        "balanced": "균형",
        "elevated": "높음",
        "very_high": "매우 높음",
        "speculative": "투기적 기대",
        "unknown": "자료 부족",
    }.get(expectation_level, expectation_level)
    decision = price_context.get("decision", {}) if isinstance(price_context, dict) else {}
    if not isinstance(decision, dict):
        decision = {}
    current_price = valuation_snapshot.get("current_price", decision.get("current_price"))
    currency = valuation_snapshot.get("currency", decision.get("currency"))
    price_as_of = valuation_snapshot.get(
        "exchange_trade_date",
        valuation_snapshot.get("price_as_of", decision.get("exchange_trade_date", decision.get("price_as_of"))),
    )
    price_basis = str(valuation_snapshot.get("price_basis", decision.get("price_basis", "")))
    is_krx = assessment.ticker.isdigit()
    price_basis_label = (
        f"{price_as_of} 장중 · 잠정"
        if price_basis == "intraday"
        else f"{price_as_of} 미국장 종가"
        if price_as_of and not is_krx
        else f"{price_as_of} 종가"
        if price_as_of
        else "기준일 확인 불가"
    )
    observed_date = str(
        valuation_snapshot.get("price_observed_at")
        or decision.get("price_observed_at")
        or ""
    )[:10]
    session_status_text = (
        f"{observed_date} 미국장 개장 전"
        if market_session == "pre_market" and not is_krx and observed_date
        else "미국장 진행 중"
        if market_session == "open" and not is_krx
        else "한국장 진행 중"
        if market_session == "open" and is_krx
        else market_session
    )
    new_buyer_price_view = str(getattr(assessment, "new_buyer_price_view", "") or "")
    holder_price_view = str(getattr(assessment, "holder_price_view", "") or "")
    valuation_evidence = valuation_context.get("valuation_evidence", [])
    if not isinstance(valuation_evidence, list):
        valuation_evidence = []
    quality = str(valuation_snapshot.get("quality", "unavailable"))
    quality_label = {
        "fresh": "최신",
        "stale": "오래됨",
        "partial": "부분 확인",
        "unavailable": "자료 없음",
    }.get(quality, quality)
    snapshot_warnings = valuation_snapshot.get("warnings", [])
    if not isinstance(snapshot_warnings, list):
        snapshot_warnings = []
    data_coverage = valuation_snapshot.get("data_coverage", {})
    if not isinstance(data_coverage, dict):
        data_coverage = {}
    coverage_reason_labels = {
        "provider_not_supported": "현재 provider가 이 종목의 표준 재무 데이터를 충분히 지원하지 않습니다.",
        "latest_financial_event_without_snapshot": "최근 실적 이벤트는 확인됐지만 재무 snapshot이 아직 생성되지 않았습니다.",
        "financial_event_newer_than_snapshot": "최근 실적 발표가 Valuation 계산 재무자료보다 새롭습니다.",
        "insufficient_history": "현재 시스템에 확보된 point-in-time 재무 이력이 장기 비교에 충분하지 않습니다.",
        "missing_adr_ratio": "foreign issuer/ADR의 주식 변환 비율이 확인되지 않았습니다.",
        "stale_data": "핵심 재무 데이터의 최신성이 낮습니다.",
        "reporting_cadence_exceeded": "예상 재무 보고 주기가 지나 최신 정식 재무 반영 여부를 확인 중입니다.",
        "preliminary_validation_failed": "최근 잠정실적의 숫자·기간·단위 검증에 실패해 확정 재무 및 Valuation에 사용하지 않았습니다.",
        "foreign_financial_parsing_failed": "foreign filing의 재무표 후보를 확인했지만 자동 구조화·검증이 완료되지 않았습니다.",
        "foreign_latest_filing_not_financial": "최근 foreign filing은 재무 실적표가 아닌 문서로 확인됐습니다.",
    }
    coverage_reasons = [
        coverage_reason_labels.get(str(code), str(code))
        for code in data_coverage.get("reason_codes", [])
    ] if isinstance(data_coverage.get("reason_codes", []), list) else []
    relative_position = str(
        valuation_snapshot.get("valuation_relative_position", "unknown")
    )
    relative_label = {
        "discounted": "할인 구간",
        "somewhat_discounted": "다소 할인",
        "neutral": "중립 범위",
        "somewhat_premium": "다소 부담",
        "premium": "부담 구간",
        "unknown": "판단 자료 부족",
    }.get(relative_position, "판단 자료 부족")
    relative_basis = valuation_snapshot.get("valuation_relative_basis")
    relative_basis_text = (
        f"현재 Valuation 위치: {relative_label} · {relative_basis}"
        if relative_basis
        else f"현재 Valuation 위치: {relative_label}"
    )
    relative_confidence = {
        "high": "높음",
        "medium": "보통",
        "low": "낮음",
    }.get(str(valuation_snapshot.get("valuation_relative_position_confidence", "low")), "낮음")
    relative_reason = str(
        valuation_snapshot.get("valuation_relative_position_reason") or ""
    ).strip()

    def _history_line(label: str, key: str) -> str:
        raw = valuation_snapshot.get(key)
        if not isinstance(raw, dict) or not raw.get("observation_count"):
            return f"• {label}: 역사적 관측치 부족"
        median_value = raw.get("historical_median")
        percentile = raw.get("current_percentile")
        years = raw.get("lookback_years")
        count = raw.get("deduplicated_observation_count", raw.get("observation_count"))
        history_quality = str(raw.get("history_quality", "insufficient"))
        median_text = f"중앙값 {float(median_value):.1f}배" if isinstance(median_value, (int, float)) else "중앙값 확인 불가"
        percentile_text = f"현재 {float(percentile):.0f} percentile" if isinstance(percentile, (int, float)) else "현재 위치 확인 불가"
        coverage = raw.get("history_coverage_ratio")
        coverage_text = (
            f" · 목표기간 충족률 {float(coverage):.0%}"
            if isinstance(coverage, (int, float)) else ""
        )
        return (
            f"• {label}: 최근 {years}년 {median_text} · {percentile_text} · "
            f"주간 말일 {count}개 · 품질 {history_quality}{coverage_text}"
        )

    historical_text = (
        f"{_history_line('trailing PER', 'historical_pe_statistics')}\n"
        f"{_history_line('PBR', 'historical_pb_statistics')}"
    )
    forward_basis = str(valuation_snapshot.get("forward_basis") or "").strip()
    forward_basis_label = (
        " · provider forward consensus 기준"
        if forward_basis == "provider-defined forward consensus"
        else f" · {forward_basis} 기준" if forward_basis else ""
    )
    forward_freshness_label = (
        " · 기준일 일부 미확인"
        if valuation_snapshot.get("forward_pe_status") == "value"
        and valuation_snapshot.get("forward_pe_source") == "consensus_forward"
        and not valuation_snapshot.get("denominator_as_of")
        else ""
    )
    forward_pe_label = (
        "내부 추정 fPER"
        if valuation_snapshot.get("forward_pe_source") == "modeled_forward"
        else "fPER"
    )
    forward_pb_label = (
        "내부 추정 fPBR"
        if valuation_snapshot.get("forward_price_to_book_source") == "modeled_forward"
        else "fPBR"
    )
    caveat_text = (
        f"• 해석 주의: {valuation_caveats[0]}"
        if valuation_caveats
        else "• 해석 주의: 등록된 종목별 Valuation 주의사항 없음"
    )
    data_status_parts = [
        f"가격 {data_coverage.get('price_quality', data_coverage.get('price', 'unavailable'))}",
        f"이벤트 {data_coverage.get('event_quality', 'unavailable')}",
        "정식 재무 "
        f"{data_coverage.get('full_financial_availability', 'unavailable')}/"
        f"{data_coverage.get('full_financial_freshness', data_coverage.get('full_financial_quality', 'unavailable'))}",
        "잠정실적 "
        f"{data_coverage.get('preliminary_financial_freshness', data_coverage.get('preliminary_financial_quality', 'unavailable'))}",
        f"Consensus {data_coverage.get('consensus_quality', 'unavailable')}",
        f"역사 Valuation {data_coverage.get('historical_valuation_quality', 'unavailable')}",
        f"Forward {data_coverage.get('forward_valuation_quality', 'unavailable')}",
    ]
    if data_coverage.get("filing_discovery_coverage") not in {None, "not_applicable"}:
        data_status_parts.append(
            "Foreign 최신 filing "
            + str(
                data_coverage.get("latest_foreign_filing_parse_result")
                or data_coverage.get("foreign_latest_filing_result")
                or "unavailable"
            )
        )
    detailed_data_status = any(
        str(data_coverage.get(key, "")) in {"stale", "partial", "unavailable", "validation_failed", "refresh_due", "refresh_pending"}
        for key in (
            "financial_quality",
            "event_quality",
            "consensus_quality",
            "historical_valuation_quality",
            "forward_valuation_quality",
            "full_financial_freshness",
            "preliminary_financial_freshness",
            "latest_foreign_filing_parse_result",
        )
    )
    data_status_text = (
        "📊 데이터 상태\n"
        + " · ".join(data_status_parts)
        + "\n전체 판단 데이터: "
        + str(data_coverage.get("overall_data_quality", "unavailable"))
        + "\n주의: "
        + str(data_coverage.get("overall_quality_reason") or "별도 데이터 경고 없음")
        + "\n"
        if detailed_data_status
        else ""
    )
    consensus_status = str(valuation_snapshot.get("consensus_status") or "unavailable")
    consensus_status_label = {
        "full": "충분",
        "partial": "부분 확인",
        "unavailable": "자료 없음",
        "stale": "오래됨",
        "conflicting": "provider 간 충돌",
    }.get(consensus_status, consensus_status)
    consensus_detail = ""
    if consensus_status == "partial" and valuation_snapshot.get("forward_pe_status") == "value":
        consensus_detail = "\nForward PE 값은 확인됐지만 기준일 또는 분석가 수 metadata가 일부 부족합니다."
    elif consensus_status == "conflicting":
        consensus_detail = "\nForward 추정치가 provider 간 엇갈려 단일 배수를 강하게 해석하지 않습니다."
    analyst_count = valuation_snapshot.get("estimate_analyst_count")
    analyst_text = (
        f"분석가 {analyst_count}명"
        if isinstance(analyst_count, int) and analyst_count > 0
        else "분석가 수 확인 불가"
    )
    if assessment_state == "provisional" and is_krx:
        session_label = "잠정 · 한국장 진행 중"
        provisional_text = (
            "\n⚠️ 한국장이 진행 중이므로 현재가와 기술적 가격 판단은 잠정입니다. "
            "간밤 미국 시장 데이터는 확정 기준입니다.\n"
        )
    elif assessment_state == "provisional":
        session_label = "잠정 · 미국장 진행 중"
        provisional_text = (
            "\n⚠️ 미국장이 진행 중이므로 현재가와 시장 가격 신호는 잠정입니다.\n"
        )
    else:
        session_label = f"확정 · 시장 세션 {market_session}"
        provisional_text = ""
    matched_today = _unique_text(
        str(signal)
        for item in evidence_items
        if isinstance(item, dict) and item.get("event_type") != "price_rule"
        for signal in item.get("matched_signals", [])
        if str(signal).strip()
    )
    fallback = (
        f"🏢 {company_name}({assessment.ticker})\n"
        f"⚠️ 오늘 투자 논리 {label}\n"
        f"구조적 위험: {risk_label} · 판단 신뢰도 {assessment.confidence:.0%}\n"
        f"평가 상태: {session_label}{provisional_text}\n"
        f"🎯 핵심 투자 논리\n{core_thesis}\n\n"
        f"🔄 오늘 새로 확인된 변화\n{change_text}\n\n"
        f"🚨 오늘 새 경고\n{_warnings_with_provenance(new_warnings, '없음')}\n\n"
        f"⚠️ 아직 해결되지 않은 기존 경고\n"
        f"{_warnings_with_provenance(prior_open_warnings, '없음')}\n\n"
        f"👁 계속 감시하는 구조적 리스크\n"
        f"{_bullet_text(persistent_watch_risks, '등록된 상시 감시 리스크 없음')}\n\n"
        f"📍 투자 논리 조건\n"
        f"↑ 강화: {strengthen_text}\n"
        f"↓ 약화: {weaken_text}\n"
        f"✕ 무효화: {invalidation_text}\n\n"
        f"오늘 충족된 조건: "
        f"{', '.join(matched_today) if matched_today else '없음'}\n\n"
        f"💰 가격 판단\n"
        f"현재가: {_report_price(current_price, currency)} · {price_basis_label}\n"
        f"현재 상태: {session_status_text}\n"
        f"가격 위치: {decision.get('current_position', assessment.price_view)}\n"
        f"가격 위치는 타이밍 보조 정보이며 적정가치와는 별도로 봅니다.\n\n"
        f"👀 신규 관찰자 가격 체크\n"
        f"{_audience_price_text(new_buyer_price_view, '등록된 구조적 확인 가격 없음')}\n\n"
        f"🛡 보유자 가격 체크\n"
        f"{_audience_price_text(holder_price_view, '투자 논리 조건과 실적 데이터를 우선 확인')}\n\n"
        f"📐 시장 기대와 Valuation\n"
        f"시장 기대: {expectation_label} · {expectation_summary}\n"
        f"현재가: {_report_price(current_price, currency)}\n"
        f"정식 재무 기준: {valuation_snapshot.get('latest_full_financial_period') or valuation_snapshot.get('financial_period_end') or '확인 불가'}\n"
        f"정식 재무 공시일: {valuation_snapshot.get('latest_full_filing_date') or valuation_snapshot.get('filing_date') or '확인 불가'}\n"
        f"최근 잠정실적: {valuation_snapshot.get('latest_preliminary_financial_period') or '없음'}\n"
        f"잠정실적 공시일: {valuation_snapshot.get('latest_preliminary_filing_date') or '없음'}\n"
        f"가격 기준: {price_basis_label}\n"
        f"TTM 기준: {valuation_snapshot.get('ttm_period_start') or '확인 불가'}~"
        f"{valuation_snapshot.get('ttm_period_end') or '확인 불가'}\n"
        f"PER 분모: {valuation_snapshot.get('trailing_pe_denominator_period_end') or '확인 불가'} 재무 · "
        f"공시 {valuation_snapshot.get('trailing_pe_denominator_filing_date') or '확인 불가'}\n"
        f"PBR 분모: {valuation_snapshot.get('pbr_denominator_period_end') or '확인 불가'} 재무 · "
        f"공시 {valuation_snapshot.get('pbr_denominator_filing_date') or '확인 불가'}\n"
        f"• PER: {_multiple_text(valuation_snapshot, 'trailing_pe')} "
        f"({multiple_roles['PER']}) · {_multiple_source_text(valuation_snapshot, 'trailing_pe')}\n"
        f"• {forward_pe_label}: {_multiple_text(valuation_snapshot, 'forward_pe')} "
        f"({multiple_roles['fPER']}) · {_multiple_source_text(valuation_snapshot, 'forward_pe')}"
        f"{forward_basis_label}{forward_freshness_label}\n"
        f"• PBR: {_multiple_text(valuation_snapshot, 'price_to_book')} "
        f"({multiple_roles['PBR']}) · {_multiple_source_text(valuation_snapshot, 'price_to_book')}\n"
        f"• {forward_pb_label}: {_multiple_text(valuation_snapshot, 'forward_price_to_book')} "
        f"({multiple_roles['fPBR']}) · {_multiple_source_text(valuation_snapshot, 'forward_price_to_book')}\n"
        f"주 평가 방식: {valuation_method}\n"
        f"역사적 위치:\n{historical_text}\n"
        f"{relative_basis_text}\n"
        f"현재 Valuation 위치 신뢰도: {relative_confidence}\n"
        f"해석: {relative_reason or '역사적·peer 비교 근거가 부족해 현재 위치를 확정하지 않습니다.'}\n"
        f"배수 신호: {valuation_snapshot.get('valuation_signal_summary') or '중요한 배수 충돌 없음'}\n"
        f"Consensus: {consensus_status_label} · {valuation_snapshot.get('estimate_provider') or 'provider 없음'}"
        f" · {valuation_snapshot.get('estimate_period') or '기간 확인 불가'}"
        f" · {analyst_text}"
        f"{consensus_detail}\n"
        f"{caveat_text}\n"
        f"{data_status_text}"
        f"Valuation 데이터 품질: {quality_label} · {valuation_snapshot.get('provider', '자료 없음')}\n"
        f"재무 커버리지: {data_coverage.get('financials', 'unavailable')} · "
        f"최신성 {data_coverage.get('financial_freshness', 'unavailable')}\n"
        f"커버리지 설명: {data_coverage.get('overall_quality_reason') or (coverage_reasons[0] if coverage_reasons else '핵심 데이터의 별도 커버리지 경고 없음')}\n"
        f"오늘 Valuation 영향: {impact_label} · {valuation_impact}\n"
        f"{_bullet_text(valuation_evidence, '오늘 배수를 바꿀 신규 근거 없음')}\n"
        f"이익 추정치 영향: {earnings_impact}\n\n"
        f"📌 오늘 확인\n"
        f"{_bullet_text(validation_metrics, '등록된 핵심 검증 지표를 계속 확인합니다.')}"
    )
    if snapshot_warnings:
        fallback += f"\n• Valuation 주의: {snapshot_warnings[0]}"
    if unknowns:
        fallback += f"\n• 미확인: {unknowns[0]}"
    context: dict[str, object] = {
        "analysis_type": "stock",
        "assessment_date": str(assessment.assessment_date),
        "company_name": company_name,
        "ticker": assessment.ticker,
        "thesis": {
            "version": assessment.thesis_version,
            "core_thesis": core_thesis,
            "time_horizon": thesis.time_horizon if thesis else None,
            "thesis_drivers": thesis_drivers,
            "validation_metrics": validation_metrics,
            "strengthen_signals": strengthen_signals,
            "weaken_signals": weaken_signals,
            "invalidation_signals": invalidation_signals,
            "price_rules": price_rules,
            "market_expectations": market_expectations,
            "valuation_framework": valuation_framework,
            "multiple_expansion_signals": expansion_signals,
            "multiple_compression_signals": compression_signals,
            "macro_exposures": macro_exposures,
            "snapshot": thesis_snapshot,
        },
        "assessment": {
            "status": assessment.status,
            "business_thesis_change": business_change,
            "earnings_estimate_impact": earnings_impact,
            "market_expectation_assessment": market_expectation_assessment,
            "confirmed_facts": confirmed_facts,
            "background_confirmed_facts": background_confirmed_facts,
            "inferred_implications": inferred_implications,
            "unknowns": unknowns,
            "confirmed_warnings": confirmed_warnings,
            "new_warnings": new_warnings,
            "open_warnings": open_warnings,
            "open_confirmed_warnings": open_confirmed_warnings,
            "persistent_watch_risks": persistent_watch_risks,
            "watch_items": watch_items,
            "score": assessment.score,
            "confidence": assessment.confidence,
            "summary": assessment.summary,
            "new_buyer_view": assessment.new_buyer_view,
            "holder_view": assessment.holder_view,
            "price_view": assessment.price_view,
            "risk_level": assessment.risk_level,
            "structural_risk_level": structural_risk,
            "assessment_state": assessment_state,
            "market_session": market_session,
            "evidence": evidence_items,
            "price_context": price_context,
            "new_buyer_price_view": new_buyer_price_view,
            "holder_price_view": holder_price_view,
            "valuation_snapshot": valuation_snapshot,
            "valuation_context": valuation_context,
        },
    }
    return fallback, context


def _message_for_assessment(assessment: ThesisAssessment) -> str:
    return _assessment_report(assessment, assessment.ticker, None)[0]


def queue_notification(session: Session, assessment: ThesisAssessment) -> None:
    if assessment.status not in MATERIAL_STATUSES:
        return
    watchlist_item = session.exec(
        select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
    ).first()
    thesis = session.exec(
        select(InvestmentThesis).where(
            InvestmentThesis.ticker == assessment.ticker,
            InvestmentThesis.version == assessment.thesis_version,
        )
    ).first()
    company_name = watchlist_item.company_name if watchlist_item else assessment.ticker
    text, _analysis_context = _assessment_report(assessment, company_name, thesis)
    evidence = [item for item in _json_list_value(assessment.evidence) if isinstance(item, dict)]
    dedupe_keys = [
        str(item.get("url") or f"{item.get('date')}:{item.get('title')}")
        for item in evidence
    ]
    payload = json.dumps(
        {
            "text": text,
            "ticker": assessment.ticker,
            "assessment_date": str(assessment.assessment_date),
            "status": assessment.status,
            "type": "material_event_alert",
            "presentation": "long_text",
            "use_llm": False,
            "event_dedupe_keys": dedupe_keys,
        },
        ensure_ascii=False,
    )
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == assessment.ticker,
            NotificationDelivery.assessment_date == assessment.assessment_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        session.add(
            NotificationDelivery(
                ticker=assessment.ticker,
                assessment_date=assessment.assessment_date,
                channel=channel,
                status="pending",
                payload=payload,
            )
        )
    elif delivery.status != "sent":
        delivery.payload = payload
        delivery.status = "pending"


def queue_daily_stock_notification(
    session: Session,
    assessment: ThesisAssessment,
    requeue_sent_before: datetime | None = None,
) -> NotificationDelivery:
    """Queue the full morning analysis even when today's thesis delta is neutral."""
    watchlist_item = session.exec(
        select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
    ).first()
    thesis = session.exec(
        select(InvestmentThesis).where(
            InvestmentThesis.ticker == assessment.ticker,
            InvestmentThesis.version == assessment.thesis_version,
        )
    ).first()
    company_name = watchlist_item.company_name if watchlist_item else assessment.ticker
    text, analysis_context = _assessment_report(assessment, company_name, thesis)
    payload = json.dumps(
        {
            "text": text,
            "ticker": assessment.ticker,
            "assessment_date": str(assessment.assessment_date),
            "status": assessment.status,
            "type": "daily_stock_analysis",
            "presentation": "long_text",
            "use_llm": False,
            "analysis_context": analysis_context,
        },
        ensure_ascii=False,
    )
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == assessment.ticker,
            NotificationDelivery.assessment_date == assessment.assessment_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        delivery = NotificationDelivery(
            ticker=assessment.ticker,
            assessment_date=assessment.assessment_date,
            channel=channel,
            status="pending",
            payload=payload,
        )
        session.add(delivery)
    elif delivery.status != "sent" or _should_requeue_sent_delivery(
        delivery, requeue_sent_before
    ):
        _prepare_delivery_for_retry(delivery, payload)
    return delivery


def queue_macro_notification(session: Session, briefing: MacroBriefing) -> None:
    text, analysis_context = _macro_report(briefing)
    payload = json.dumps(
        {
            "text": text,
            "briefing_date": str(briefing.briefing_date),
            "type": "macro_morning",
            "presentation": "long_text",
            "use_llm": False,
            "analysis_context": analysis_context,
        },
        ensure_ascii=False,
    )
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == "__MACRO__",
            NotificationDelivery.assessment_date == briefing.briefing_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        session.add(
            NotificationDelivery(
                ticker="__MACRO__",
                assessment_date=briefing.briefing_date,
                channel=channel,
                status="pending",
                payload=payload,
            )
        )
    elif delivery.status != "sent":
        delivery.payload = payload
        delivery.status = "pending"


def queue_daily_digest_notification(
    session: Session,
    run_date: date,
    requeue_sent_before: datetime | None = None,
) -> NotificationDelivery | None:
    digest = build_daily_digest(session, run_date)
    payload = json.dumps(
        {
            "text": render_daily_digest(digest, include_stock_details=False),
            "briefing_date": str(run_date),
            "type": "daily_monitoring_digest",
            "presentation": "long_text",
            "use_llm": False,
        },
        ensure_ascii=False,
    )
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == "__DAILY_DIGEST__",
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        delivery = NotificationDelivery(
            ticker="__DAILY_DIGEST__",
            assessment_date=run_date,
            channel=channel,
            status="pending",
            payload=payload,
        )
        session.add(delivery)
    elif delivery.status != "sent" or _should_requeue_sent_delivery(
        delivery, requeue_sent_before
    ):
        _prepare_delivery_for_retry(delivery, payload)
    session.commit()
    session.refresh(delivery)
    return delivery


def _observation_map(market: object) -> dict[str, dict[str, object]]:
    if not isinstance(market, dict):
        return {}
    observations = market.get("observations", [])
    if not isinstance(observations, list):
        return {}
    return {
        str(item.get("series_code")): item
        for item in observations
        if isinstance(item, dict) and item.get("series_code")
    }


def _change_pct(observation: dict[str, object] | None) -> float | None:
    if observation is None:
        return None
    value = observation.get("change_pct")
    return float(value) if isinstance(value, (int, float)) else None


def _change_value(observation: dict[str, object] | None) -> float | None:
    if observation is None:
        return None
    value = observation.get("change_value")
    return float(value) if isinstance(value, (int, float)) else None


def _equity_interpretation(observations: dict[str, dict[str, object]]) -> str:
    spy = _change_pct(observations.get("SPY"))
    qqq = _change_pct(observations.get("QQQ"))
    soxx = _change_pct(observations.get("SOXX"))
    vix = _change_pct(observations.get("VIXCLS"))
    parts: list[str] = []
    if spy is not None and qqq is not None:
        if qqq - spy >= 0.3:
            parts.append("Nasdaq이 S&P를 웃돌아 성장주 상대강도가 확인됐습니다.")
        elif spy - qqq >= 0.3:
            parts.append("S&P가 Nasdaq을 웃돌아 대형 성장주 주도력은 제한적이었습니다.")
        else:
            parts.append("S&P와 Nasdaq이 비슷하게 움직여 지수 간 주도력 차이는 작았습니다.")
    if soxx is not None:
        if soxx >= 1.0:
            parts.append("반도체 강세는 AI·이익 모멘텀 기대에 우호적입니다.")
        elif soxx <= -1.0:
            parts.append("반도체 약세는 AI CAPEX·이익 기대의 추가 확인을 요구합니다.")
    if vix is not None:
        if vix <= -3.0:
            parts.append("VIX 하락은 단기 위험선호를 지지합니다.")
        elif vix >= 5.0:
            parts.append("VIX 상승은 위험 프리미엄 확대 신호입니다.")
    return " ".join(parts) or "지수 상대강도를 해석할 충분한 변화 데이터가 없습니다."


def _rates_fx_commodity_interpretation(
    observations: dict[str, dict[str, object]],
) -> str:
    nominal = observations.get("DGS10")
    real = observations.get("DFII10")
    nominal_change = _change_value(nominal)
    real_change = _change_value(real)
    parts: list[str] = []
    if nominal_change is not None and real_change is not None:
        nominal_bp = nominal_change * 100
        real_bp = real_change * 100
        if nominal_bp >= 5 or real_bp >= 5:
            parts.append(
                f"미10년 금리 {nominal_bp:+.0f}bp, 실질10년 {real_bp:+.0f}bp 상승은 "
                "장기 성장주의 할인율 부담을 높입니다."
            )
        elif nominal_bp <= -5 or real_bp <= -5:
            parts.append(
                f"미10년 금리 {nominal_bp:+.0f}bp, 실질10년 {real_bp:+.0f}bp 하락은 "
                "장기 성장주의 멀티플에 우호적입니다."
            )
        else:
            parts.append("명목·실질금리 변화는 멀티플을 바꿀 정도로 크지 않았습니다.")
    usdkrw = observations.get("USDKRW")
    usdkrw_change = _change_pct(usdkrw)
    if usdkrw_change is not None:
        if usdkrw_change >= 0.5:
            parts.append("원화 약세는 수입비용에는 부담이고 달러 매출 기업에는 완충 요인입니다.")
        elif usdkrw_change <= -0.5:
            parts.append("원화 강세는 수입비용에는 우호적이나 달러 매출 환산에는 부담입니다.")
        else:
            parts.append("원화 변동은 종목 이익 추정치를 바꿀 정도로 크지 않았습니다.")
    oil = observations.get("DCOILWTICO")
    oil_change = _change_pct(oil)
    if oil_change is None:
        parts.append("유가는 최신 수준만 확인돼 공급 충격과 수요 회복 중 원인을 단정하지 않습니다.")
    elif oil_change >= 2.0:
        parts.append("유가 상승은 비용·물가 압력 경로를 강화하므로 원인을 추가 확인해야 합니다.")
    elif oil_change <= -2.0:
        parts.append("유가 하락은 비용 부담을 낮추지만 수요 둔화 신호인지 구분해야 합니다.")
    return " ".join(parts) or "금리·환율·원자재 변화 자료가 부족합니다."


def _regime_axis_values(regime: object) -> dict[str, int]:
    if not isinstance(regime, dict):
        return {key: 0 for key in REGIME_AXIS_KEYS}
    explicit = {
        key: int(regime[key])
        for key in REGIME_AXIS_KEYS
        if isinstance(regime.get(key), (int, float))
    }
    if len(explicit) == len(REGIME_AXIS_KEYS):
        return explicit
    summary = str(regime.get("summary", ""))
    values = dict(explicit)
    for key, label in REGIME_AXIS_KEYS.items():
        if key in values:
            continue
        match = re.search(rf"{label}\s*([+-]?\d+)", summary)
        values[key] = int(match.group(1)) if match else 0
    return values


def _move_text(
    observations: dict[str, dict[str, object]],
    series_code: str,
    *,
    basis_points: bool = False,
) -> str:
    observation = observations.get(series_code)
    if observation is None:
        return "자료 없음"
    change = _change_value(observation) if basis_points else _change_pct(observation)
    if change is None:
        return "변화율 없음"
    return f"{change * 100:+.0f}bp" if basis_points else f"{change:+.1f}%"


def _axis_explanations(
    axes: dict[str, int],
    observations: dict[str, dict[str, object]],
) -> list[str]:
    return [
        (
            f"• 성장 {axes['growth_momentum']:+d}: Russell 2000 "
            f"{_move_text(observations, 'IWM')}, SOXX {_move_text(observations, 'SOXX')}. "
            "소형주와 반도체가 함께 강하거나 약한 임계치를 넘는지 봅니다."
        ),
        (
            f"• 물가 {axes['inflation_pressure']:+d}: 기대인플레이션 "
            f"{_move_text(observations, 'T10YIE', basis_points=True)}, WTI "
            f"{_move_text(observations, 'DCOILWTICO')}. 유가와 기대물가가 함께 움직이는지 봅니다."
        ),
        (
            f"• 유동성 {axes['liquidity_condition']:+d}: 미 달러지수(광의) "
            f"{_move_text(observations, 'DTWEXBGS')}. 달러 강세는 글로벌 유동성에 부담으로 봅니다."
        ),
        (
            f"• 금융여건 {axes['financial_conditions']:+d}: 실질금리 "
            f"{_move_text(observations, 'DFII10', basis_points=True)}, 하이일드 스프레드 "
            f"{_move_text(observations, 'BAMLH0A0HYM2', basis_points=True)}. "
            "둘의 상승은 할인율·신용비용 부담입니다."
        ),
        (
            f"• 위험선호 {axes['risk_appetite']:+d}: S&P {_move_text(observations, 'SPY')}, "
            f"Nasdaq {_move_text(observations, 'QQQ')}, VIX "
            f"{_move_text(observations, 'VIXCLS')}. 주가 상승과 변동성 하락의 조합을 봅니다."
        ),
        (
            f"• 이익 {axes['earnings_momentum']:+d}: SOXX {_move_text(observations, 'SOXX')}. "
            "현재는 반도체 가격 반응을 단기 이익 기대의 대용치로 사용하므로 실제 실적 추정치와는 구분합니다."
        ),
    ]


def _daily_signal_label(value: int) -> str:
    if value >= 1:
        return "지지"
    if value <= -1:
        return "약화"
    return "중립"


def _fallback_thesis_signal(
    thesis_key: str,
    axes: dict[str, int],
) -> tuple[int, str]:
    if thesis_key == "us_soft_landing_disinflation":
        if (
            axes["growth_momentum"] >= 1
            and axes["inflation_pressure"] <= 0
        ) or (
            axes["growth_momentum"] >= 0
            and axes["inflation_pressure"] <= -1
        ):
            signal = 1
        elif axes["growth_momentum"] <= -1 or axes["inflation_pressure"] >= 1:
            signal = -1
        else:
            signal = 0
        rationale = (
            f"성장 {axes['growth_momentum']:+d}, 물가 {axes['inflation_pressure']:+d}: "
            "성장 급락과 물가 재가속의 동시 발생 여부를 점검했습니다."
        )
    elif thesis_key == "fed_policy_path":
        signal = int(axes["financial_conditions"] >= 1) - int(
            axes["financial_conditions"] <= -1
        )
        rationale = (
            f"금융여건 {axes['financial_conditions']:+d}: 실질금리와 신용스프레드의 "
            "구조적 재긴축 여부를 점검했습니다."
        )
    elif thesis_key == "ai_capex_cycle":
        signal = axes["earnings_momentum"]
        rationale = f"이익 모멘텀 {axes['earnings_momentum']:+d}: 반도체 가격 반응을 단기 대용치로 사용했습니다."
    elif thesis_key == "china_korea_export_cycle":
        signal = axes["growth_momentum"]
        rationale = f"성장 모멘텀 {axes['growth_momentum']:+d}: 소형주와 반도체 반응을 단기 대용치로 사용했습니다."
    else:
        signal = -1 if axes["inflation_pressure"] >= 2 else 0
        rationale = f"물가 압력 {axes['inflation_pressure']:+d}: 공급 충격 수준인지 점검했습니다."
    return signal, rationale


def _macro_report(briefing: MacroBriefing) -> tuple[str, dict[str, object]]:
    market = _json_value(briefing.market_summary, {})
    regime = _json_value(briefing.regime_summary, {})
    theses = _json_value(briefing.macro_theses, [])
    impacts = _json_value(briefing.ticker_impacts, [])
    calendar = _json_value(briefing.today_calendar, [])
    quality = _json_value(briefing.data_quality, [])
    macro = interpret_macro_briefing(briefing)
    axis_text = "\n".join(
        f"• {label}: {explanation}" for label, explanation in macro.axis_explanations
    )
    change_text = "\n".join(f"• {item}" for item in macro.key_changes)
    assumption_text = "\n".join(f"• {item}" for item in macro.market_assumptions)
    impact_items = [item for item in impacts if isinstance(item, dict)] if isinstance(impacts, list) else []
    impact_detail_lines = [
        f"• {item.get('ticker')}: "
        f"{IMPACT_LABELS.get(str(item.get('direction')), item.get('direction'))} · "
        f"이익 {item.get('earnings_effect', 'neutral')} · "
        f"Valuation {item.get('valuation_effect', 'neutral')}"
        + (f" · {item.get('rationale')}" if item.get("rationale") else "")
        for item in impact_items[:5]
    ]
    impact_detail_text = "\n".join(impact_detail_lines) or "• 강한 종목별 거시 전달 경로가 없습니다."
    calendar_items = calendar if isinstance(calendar, list) else []
    quality_items = quality if isinstance(quality, list) else []
    calendar_text = ", ".join(
        str(item.get("title", "일정")) for item in calendar_items[:5] if isinstance(item, dict)
    ) or "등록된 주요 일정 없음"
    quality_lines: list[str] = []
    for item in quality_items[:5]:
        if not isinstance(item, dict):
            continue
        if item.get("warning"):
            quality_lines.append(f"• {item['warning']}")
            continue
        series_code = str(item.get("series_code", "데이터"))
        label = SERIES_LABELS.get(series_code, series_code)
        status = str(item.get("quality_status", "점검 필요"))
        observed_at = item.get("observed_at")
        explanation = (
            "미국의 주요 교역 상대국 통화 대비 달러 강도를 나타내는 지수입니다. "
            if series_code == "DTWEXBGS"
            else ""
        )
        quality_lines.append(
            f"• {label}({series_code}): {status} · 최신 관측 {observed_at or '확인 불가'}. "
            f"{explanation}최신 관측일이 오래되어 당일 방향 판단에는 사용하지 않습니다."
        )
    quality_text = "\n".join(quality_lines) or "• 특이사항 없음"
    fallback = (
        f"🌍 시장환경 점검 · {briefing.briefing_date}\n"
        f"⚠️ {macro.regime_label} 국면 · 판단 신뢰도 {macro.confidence:.0%}\n\n"
        f"🎯 오늘 한 줄\n{macro.one_line}\n\n"
        f"📈 오늘 가장 중요한 변화\n"
        f"{change_text or '• 임계치를 넘은 핵심 시장 변화가 없습니다.'}\n\n"
        f"🧭 현재 시장 상황\n{axis_text}\n\n"
        f"💡 종합 해석\n{' '.join(macro.integrated_view)}\n\n"
        f"🔄 시장 가정\n"
        f"{assumption_text or '• 방향을 바꿀 신규 확정 근거가 없습니다.'}\n\n"
        f"🏢 주요 종목 전달 경로\n"
        f"{impact_detail_text}\n\n"
        f"📅 오늘/근접 일정\n"
        f"• {calendar_text}\n\n"
        f"⚠️ 데이터 주의\n"
        f"{quality_text}"
    )
    context: dict[str, object] = {
        "analysis_type": "macro",
        "briefing_date": str(briefing.briefing_date),
        "as_of": str(briefing.as_of),
        "headline": briefing.headline,
        "market": market,
        "regime": regime,
        "macro_theses": theses if isinstance(theses, list) else [],
        "ticker_impacts": impact_items,
        "today_calendar": calendar_items,
        "data_quality": quality_items,
    }
    return fallback, context


class KakaoSelfNotifier:
    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        narrative_generator: InvestmentNarrativeGenerator | None = None,
    ) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.narrative_generator = narrative_generator

    def _token_path(self) -> Path:
        path = Path(self.settings.data_dir) / "kakao_tokens.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _load_refresh_token(self) -> str | None:
        path = self._token_path()
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                token = payload.get("refresh_token")
                if isinstance(token, str) and token:
                    return token
            except (OSError, json.JSONDecodeError):
                pass
        return self.settings.kakao_refresh_token

    def _store_refresh_token(self, refresh_token: str) -> None:
        path = self._token_path()
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump({"refresh_token": refresh_token}, handle)
            handle.write("\n")
            temporary_path = Path(handle.name)
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        refresh_token = self._load_refresh_token()
        if not self.settings.kakao_rest_api_key or not refresh_token:
            raise RuntimeError("Kakao credentials are not configured")
        form = {
            "grant_type": "refresh_token",
            "client_id": self.settings.kakao_rest_api_key,
            "refresh_token": refresh_token,
        }
        if self.settings.kakao_client_secret:
            form["client_secret"] = self.settings.kakao_client_secret
        response = await client.post("https://kauth.kakao.com/oauth/token", data=form)
        response.raise_for_status()
        payload = response.json()
        renewed_refresh_token = payload.get("refresh_token")
        if isinstance(renewed_refresh_token, str) and renewed_refresh_token:
            self._store_refresh_token(renewed_refresh_token)
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeError("Kakao token response did not contain an access token")
        return access_token

    async def send(self, payload: dict[str, object]) -> str:
        if self.settings.notification_dry_run:
            return "dry_run"
        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            access_token = await self._access_token(client)
            text = str(payload["text"])
            if payload.get("use_llm") is True:
                context = payload.get("analysis_context")
                if isinstance(context, dict):
                    generator = self.narrative_generator or InvestmentNarrativeGenerator()
                    text = await generator.generate(context, text)
            headers = {"Authorization": f"Bearer {access_token}"}
            if payload.get("presentation") == "long_text":
                for chunk in split_kakao_text(text):
                    template = {
                        "object_type": "text",
                        "text": chunk,
                        "link": {
                            "web_url": self.settings.kakao_web_url,
                            "mobile_web_url": self.settings.kakao_web_url,
                        },
                        "button_title": "상태 확인",
                    }
                    response = await client.post(
                        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
                        headers=headers,
                        data={"template_object": json.dumps(template, ensure_ascii=False)},
                    )
                    response.raise_for_status()
            elif self.settings.kakao_template_id:
                raw_messages = payload.get("messages")
                messages = (
                    [item for item in raw_messages if isinstance(item, dict)]
                    if isinstance(raw_messages, list)
                    else []
                )
                if not messages:
                    lines = text.splitlines()
                    messages = [
                        {
                            "title": lines[0] if lines else "투자 분석",
                            "body": "\n".join(lines[1:]) or "유의미한 변화가 없습니다.",
                        }
                    ]
                for message in messages:
                    response = await client.post(
                        "https://kapi.kakao.com/v2/api/talk/memo/send",
                        headers=headers,
                        data={
                            "template_id": self.settings.kakao_template_id,
                            "template_args": json.dumps(
                                {
                                    "TITLE": str(message.get("title", "투자 분석")),
                                    "BODY": str(message.get("body", "")),
                                },
                                ensure_ascii=False,
                            ),
                        },
                    )
                    response.raise_for_status()
            else:
                template = {
                    "object_type": "text",
                    "text": text,
                    "link": {
                        "web_url": self.settings.kakao_web_url,
                        "mobile_web_url": self.settings.kakao_web_url,
                    },
                }
                response = await client.post(
                    "https://kapi.kakao.com/v2/api/talk/memo/default/send",
                    headers=headers,
                    data={"template_object": json.dumps(template, ensure_ascii=False)},
                )
                response.raise_for_status()
        return "sent"


class TelegramDeliveryError(RuntimeError):
    pass


class TelegramNotifier:
    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        narrative_generator: InvestmentNarrativeGenerator | None = None,
    ) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.narrative_generator = narrative_generator

    async def _send_chunk(self, client: httpx.AsyncClient, text: str) -> None:
        token = self.settings.telegram_bot_token
        chat_id = self.settings.telegram_chat_id
        if not token or not chat_id:
            raise TelegramDeliveryError("Telegram credentials are not configured")
        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
        attempts = max(1, self.settings.telegram_retry_attempts)
        for attempt in range(attempts):
            retry_after = self.settings.telegram_retry_base_seconds * (2**attempt)
            try:
                response = await client.post(
                    endpoint,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                )
                payload = response.json()
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                if attempt + 1 >= attempts:
                    raise TelegramDeliveryError(
                        f"Telegram network failure: {type(exc).__name__}"
                    ) from None
                await asyncio.sleep(retry_after)
                continue

            if response.status_code == 429 or response.status_code >= 500:
                parameters = payload.get("parameters", {}) if isinstance(payload, dict) else {}
                if isinstance(parameters, dict) and parameters.get("retry_after") is not None:
                    retry_after = min(60.0, float(parameters["retry_after"]))
                if attempt + 1 < attempts:
                    await asyncio.sleep(retry_after)
                    continue

            if response.status_code >= 400 or not isinstance(payload, dict) or not payload.get("ok"):
                description = (
                    str(payload.get("description", "request rejected"))
                    if isinstance(payload, dict)
                    else "invalid response"
                )
                raise TelegramDeliveryError(
                    f"Telegram sendMessage failed with HTTP {response.status_code}: "
                    f"{description[:200]}"
                )
            return
        raise TelegramDeliveryError("Telegram sendMessage retry limit exceeded")

    async def send(self, payload: dict[str, object]) -> str:
        if self.settings.notification_dry_run:
            return "dry_run"
        text = str(payload["text"])
        if payload.get("use_llm") is True:
            context = payload.get("analysis_context")
            if isinstance(context, dict):
                generator = self.narrative_generator or InvestmentNarrativeGenerator()
                text = await generator.generate(context, text)
        chunks = split_telegram_text(text, self.settings.telegram_message_max_chars)
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            for index, chunk in enumerate(chunks, start=1):
                rendered = f"[{index}/{len(chunks)}]\n{chunk}" if len(chunks) > 1 else chunk
                await self._send_chunk(client, rendered)
        return "sent"


def _notifier_for_channel(
    channel: str,
) -> KakaoSelfNotifier | TelegramNotifier:
    if channel == "telegram":
        return TelegramNotifier()
    if channel == "kakao_self":
        return KakaoSelfNotifier()
    raise RuntimeError(f"Unsupported notification channel: {channel}")


async def dispatch_pending_notifications(
    session: Session,
    notifier: KakaoSelfNotifier | TelegramNotifier | None = None,
) -> None:
    channel = _notification_channel()
    query = select(NotificationDelivery).where(
        NotificationDelivery.status == "pending",
        NotificationDelivery.channel == channel,
    )
    if notifier is None:
        notifier = _notifier_for_channel(channel)
    deliveries = session.exec(query.order_by(NotificationDelivery.created_at)).all()
    for delivery in deliveries:
        delivery.attempt_count += 1
        try:
            result = await notifier.send(json.loads(delivery.payload))
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            delivery.last_error = f"{type(exc).__name__}: {exc}"
            delivery.status = "pending"
        else:
            delivery.status = result
            delivery.last_error = None
            if result == "sent":
                delivery.sent_at = datetime.now(timezone.utc)
        session.commit()
