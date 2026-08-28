import asyncio
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone

import httpx
from sqlalchemy import case
from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import MacroBriefing
from app.models.thesis import InvestmentThesis, NotificationDelivery, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.analysis_report_service import (
    InvestmentNarrativeGenerator,
    split_telegram_text,
)
from app.services.cash_flow_baseline_consistency_service import (
    audit_shared_baseline_cash_flow_inputs,
    baseline_suppressed_claim_ids,
    financial_period_context,
    load_canonical_cash_flow_evidence,
    repair_baseline_cash_flow_items,
    repair_baseline_cash_flow_text,
)
from app.services.cash_flow_user_visible_service import (
    context_from_notification_payload,
    resolve_selected_unknowns,
    safe_select_user_visible_cash_flow,
    selection_to_dict as cash_flow_selection_to_dict,
)
from app.services.working_capital_user_visible_preintegration_service import (
    context_from_notification_payload as working_capital_context_from_notification_payload,
    context_to_dict as working_capital_context_to_dict,
    render_preview as render_working_capital_user_visible,
    resolve_selected_inventory_unknowns,
    safe_select_user_visible_inventory,
)
from app.services.canonical_fact_service import compact_krw_amount
from app.services.current_price_context_service import (
    fallback_price_context_errors,
    select_current_price_context,
)
from app.services.daily_digest import build_daily_digest, interpret_macro_briefing
from app.services.daily_digest_renderer import render_daily_digest
from app.services.financial_quality_service import (
    build_financial_quality_state,
    sanitize_financial_snapshot_for_prose,
)
from app.services.kr_close_fx import render_kr_close_fx, summarize_kr_close_fx
from app.services.kr_market_digest_context_service import (
    load_current_kr_digest_context,
)
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_rollout_decision,
    replace_legacy_price_surface,
)
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision,
)
from app.services.night_futures import (
    NIGHT_FUTURES_SERIES,
    is_night_futures_warning,
    render_night_futures,
    summarize_night_futures,
)
from app.services.numeric_semantic_registry import (
    NUMERIC_SEMANTICS,
    canonical_display_value,
)
from app.services.semantic_decision_service import (
    VALUATION_CONTEXT_CONTRACT,
    select_valuation_context,
)


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
    "KRX_KOSPI200_NIGHT_FUT": "KOSPI200 최근월물",
    "KRX_KOSDAQ150_NIGHT_FUT": "KOSDAQ150 최근월물",
}

REGIME_AXIS_KEYS = {
    "growth_momentum": "성장",
    "inflation_pressure": "물가",
    "liquidity_condition": "유동성",
    "financial_conditions": "금융여건",
    "risk_appetite": "위험선호",
    "earnings_momentum": "이익",
}

SUPPORTED_NOTIFICATION_CHANNELS = {"telegram"}
TELEGRAM_DELIVERY_METADATA_KEY = "_telegram_delivery"
STOCK_NOTIFICATION_METADATA_KEY = "_stock_notification"
MORNING_GATE_METADATA_KEY = "_morning_gate"
AI_ASSISTED_PILOT_METADATA_KEY = "_ai_assisted_pilot"
PACKET_BOUND_DELIVERY_INTENT_CONTRACT = "packet-bound-delivery-intent-v1"


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
    *,
    reset_attempts: bool = False,
) -> None:
    new_payload = json.loads(payload)
    if not isinstance(new_payload, dict):
        raise ValueError("Notification payload must be a JSON object")
    existing_payload = _delivery_payload(delivery.payload)
    existing_metadata = existing_payload.get(TELEGRAM_DELIVERY_METADATA_KEY)
    source_sha256 = _telegram_source_sha256(new_payload)
    if (
        not reset_attempts
        and isinstance(existing_metadata, dict)
        and existing_metadata.get("source_sha256") == source_sha256
    ):
        new_payload[TELEGRAM_DELIVERY_METADATA_KEY] = existing_metadata
    else:
        new_payload.pop(TELEGRAM_DELIVERY_METADATA_KEY, None)
    delivery.payload = json.dumps(new_payload, ensure_ascii=False)
    delivery.status = "pending"
    if reset_attempts:
        delivery.attempt_count = 0
    delivery.last_error = None
    delivery.sent_at = None


def _preserve_queued_delivery_payload(
    delivery: NotificationDelivery,
    payload: dict[str, object],
) -> None:
    delivery.payload = json.dumps(payload, ensure_ascii=False)
    if delivery.status != "pending":
        delivery.status = "pending"
    delivery.sent_at = None


def _assessment_mode(assessment: ThesisAssessment) -> str:
    snapshot = _json_value(getattr(assessment, "thesis_snapshot", "{}"), {})
    if not isinstance(snapshot, dict):
        return "daily_delta"
    mode = str(snapshot.get("assessment_mode") or "daily_delta")
    return mode if mode in {"initial_baseline", "daily_delta"} else "daily_delta"


def _notification_thesis_version(payload: dict[str, object]) -> int | None:
    candidates: list[object] = [payload.get("thesis_version")]
    metadata = payload.get(STOCK_NOTIFICATION_METADATA_KEY)
    if isinstance(metadata, dict):
        candidates.extend(
            [
                metadata.get("delivery_thesis_version"),
                metadata.get("thesis_version"),
            ]
        )
    analysis_context = payload.get("analysis_context")
    if isinstance(analysis_context, dict):
        thesis = analysis_context.get("thesis")
        if isinstance(thesis, dict):
            candidates.append(thesis.get("version"))
    for candidate in candidates:
        if isinstance(candidate, bool):
            continue
        if isinstance(candidate, int):
            return candidate
        if isinstance(candidate, str) and candidate.isdigit():
            return int(candidate)
    return None


def _notification_assessment_mode(payload: dict[str, object]) -> str:
    candidates: list[object] = [payload.get("assessment_mode")]
    metadata = payload.get(STOCK_NOTIFICATION_METADATA_KEY)
    if isinstance(metadata, dict):
        candidates.extend(
            [
                metadata.get("delivery_assessment_mode"),
                metadata.get("assessment_mode"),
            ]
        )
    for candidate in candidates:
        if candidate in {"initial_baseline", "daily_delta"}:
            return str(candidate)
    return "daily_delta"


def _stock_notification_metadata(
    *,
    delivery_thesis_version: int,
    delivery_assessment_mode: str,
    requeue_reason: str,
    current_thesis_version: int | None = None,
    current_assessment_mode: str | None = None,
    previous_thesis_version: int | None = None,
    previous_delivery_status: str | None = None,
    delivery_protection: str | None = None,
    active_logical_sha256: str | None = None,
    deferred_notifications: list[dict[str, object]] | None = None,
    promotion_reason: str | None = None,
    supersede_reason: str | None = None,
    superseded_notification_hashes: list[str] | None = None,
    relevant_event_fingerprints: list[str] | None = None,
) -> dict[str, object]:
    deferred = deferred_notifications or []
    metadata: dict[str, object] = {
        "delivery_thesis_version": delivery_thesis_version,
        "delivery_assessment_mode": delivery_assessment_mode,
        "current_thesis_version": current_thesis_version or delivery_thesis_version,
        "current_assessment_mode": (
            current_assessment_mode or delivery_assessment_mode
        ),
        "previous_thesis_version": previous_thesis_version,
        "previous_delivery_status": previous_delivery_status,
        "requeue_reason": requeue_reason,
        "status_transition": (
            f"{previous_delivery_status}->pending"
            if previous_delivery_status
            else "new->pending"
        ),
        "active_logical_sha256": active_logical_sha256,
        "deferred_count": len(deferred),
        "deferred_logical_sha256s": [
            item["logical_sha256"]
            for item in deferred
            if isinstance(item.get("logical_sha256"), str)
        ],
        "deferred_notifications": deferred,
        "relevant_event_fingerprints": relevant_event_fingerprints or [],
    }
    if delivery_protection:
        metadata["delivery_protection"] = delivery_protection
    if promotion_reason:
        metadata["promotion_reason"] = promotion_reason
    if supersede_reason:
        metadata["supersede_reason"] = supersede_reason
    if superseded_notification_hashes:
        metadata["superseded_notification_hashes"] = superseded_notification_hashes
    return metadata


def _material_daily_delta(assessment: ThesisAssessment) -> bool:
    if _assessment_mode(assessment) != "daily_delta":
        return False
    business_change = str(
        getattr(assessment, "business_thesis_change", None)
        or getattr(assessment, "status", "")
    ).strip()
    if business_change and business_change != "no_material_change":
        return True
    if str(getattr(assessment, "daily_change_severity", None) or "none") != "none":
        return True
    if str(
        getattr(assessment, "earnings_estimate_impact", None) or "unchanged"
    ) not in {
        "",
        "unchanged",
    }:
        return True
    if str(getattr(assessment, "valuation_change", "neutral") or "neutral") not in {
        "neutral",
        "unknown",
    }:
        return True
    return bool(_json_list_value(getattr(assessment, "new_warnings", "[]")))


def _logical_notification_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key
        not in {
            TELEGRAM_DELIVERY_METADATA_KEY,
            STOCK_NOTIFICATION_METADATA_KEY,
            MORNING_GATE_METADATA_KEY,
            AI_ASSISTED_PILOT_METADATA_KEY,
        }
    }


def _ai_assisted_pilot_holds(payload: dict[str, object]) -> bool:
    metadata = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
    return isinstance(metadata, dict) and metadata.get("state") == "held"


def _ai_assisted_pilot_owns_pending_payload(payload: dict[str, object]) -> bool:
    metadata = payload.get(AI_ASSISTED_PILOT_METADATA_KEY)
    return isinstance(metadata, dict) and metadata.get("state") in {
        "held",
        "ai_assisted_pending",
        "fallback_pending",
    }


def _notification_logical_sha256(payload: dict[str, object]) -> str:
    return _telegram_source_sha256(payload)


def _deferred_stock_notifications(
    payload: dict[str, object],
) -> list[dict[str, object]]:
    metadata = payload.get(STOCK_NOTIFICATION_METADATA_KEY)
    if not isinstance(metadata, dict):
        return []
    raw_items = metadata.get("deferred_notifications")
    if not isinstance(raw_items, list):
        return []
    deferred: list[dict[str, object]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        logical_payload = item.get("logical_payload")
        logical_sha256 = item.get("logical_sha256")
        if isinstance(logical_payload, dict) and isinstance(logical_sha256, str):
            deferred.append(dict(item))
    return deferred


def _assessment_event_fingerprints(assessment: ThesisAssessment) -> list[str]:
    fingerprints: list[str] = []
    for item in _json_list_value(getattr(assessment, "evidence", "[]")):
        if not isinstance(item, dict):
            continue
        fingerprint = item.get("fingerprint")
        if isinstance(fingerprint, str) and fingerprint:
            fingerprints.append(fingerprint)
    return list(dict.fromkeys(fingerprints))


def _deferred_stock_notification(
    payload: dict[str, object],
    assessment: ThesisAssessment,
) -> dict[str, object]:
    logical_payload = _logical_notification_payload(payload)
    return {
        "logical_payload": logical_payload,
        "logical_sha256": _notification_logical_sha256(logical_payload),
        "thesis_version": assessment.thesis_version,
        "assessment_mode": _assessment_mode(assessment),
        "queued_reason": "material_delta_while_delivery_pending",
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "relevant_event_fingerprints": _assessment_event_fingerprints(assessment),
    }


def _append_deferred_notification(
    deferred: list[dict[str, object]],
    item: dict[str, object],
    *,
    active_logical_sha256: str,
) -> list[dict[str, object]]:
    logical_sha256 = item["logical_sha256"]
    if logical_sha256 == active_logical_sha256:
        return deferred
    if any(existing.get("logical_sha256") == logical_sha256 for existing in deferred):
        return deferred
    return [*deferred, item]


def _previous_thesis_version(metadata: object) -> int | None:
    if not isinstance(metadata, dict):
        return None
    candidate = metadata.get("previous_thesis_version")
    if isinstance(candidate, int) and not isinstance(candidate, bool):
        return candidate
    return None


def _metadata_text_list(metadata: object, key: str) -> list[str]:
    if not isinstance(metadata, dict):
        return []
    value = metadata.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _promote_deferred_stock_notification(
    delivery: NotificationDelivery,
) -> bool:
    payload = _delivery_payload(delivery.payload)
    deferred = _deferred_stock_notifications(payload)
    if not deferred:
        return False
    item = deferred[0]
    logical_payload = item.get("logical_payload")
    if not isinstance(logical_payload, dict):
        return False
    remaining = deferred[1:]
    thesis_version = _notification_thesis_version(logical_payload)
    if thesis_version is None:
        candidate = item.get("thesis_version")
        if isinstance(candidate, int) and not isinstance(candidate, bool):
            thesis_version = candidate
    if thesis_version is None:
        return False
    assessment_mode = _notification_assessment_mode(logical_payload)
    existing_metadata = payload.get(STOCK_NOTIFICATION_METADATA_KEY)
    logical_sha256 = _notification_logical_sha256(logical_payload)
    logical_payload[STOCK_NOTIFICATION_METADATA_KEY] = _stock_notification_metadata(
        delivery_thesis_version=thesis_version,
        delivery_assessment_mode=assessment_mode,
        current_thesis_version=thesis_version,
        current_assessment_mode=assessment_mode,
        requeue_reason="deferred_material_delta_promoted",
        previous_thesis_version=_notification_thesis_version(payload),
        previous_delivery_status="sent",
        active_logical_sha256=logical_sha256,
        deferred_notifications=remaining,
        promotion_reason="previous_delivery_sent",
        relevant_event_fingerprints=_metadata_text_list(
            item,
            "relevant_event_fingerprints",
        ),
    )
    if isinstance(existing_metadata, dict):
        logical_payload[STOCK_NOTIFICATION_METADATA_KEY]["promoted_from_sha256"] = (
            existing_metadata.get("active_logical_sha256")
            or _notification_logical_sha256(payload)
        )
    _prepare_delivery_for_retry(
        delivery,
        json.dumps(logical_payload, ensure_ascii=False),
        reset_attempts=True,
    )
    return True


def _delivery_payload(payload: str) -> dict[str, object]:
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("Notification payload must be a JSON object")
    return parsed


def _previous_cash_flow_user_visible_context(
    session: Session,
    assessment: ThesisAssessment,
) -> dict[str, object]:
    delivery = session.exec(
        select(NotificationDelivery)
        .where(
            NotificationDelivery.ticker == assessment.ticker,
            NotificationDelivery.assessment_date < assessment.assessment_date,
            NotificationDelivery.channel == _notification_channel(),
            NotificationDelivery.status == "sent",
        )
        .order_by(
            NotificationDelivery.assessment_date.desc(),
            NotificationDelivery.id.desc(),
        )
    ).first()
    return context_from_notification_payload(delivery.payload if delivery else None)


def _previous_working_capital_user_visible_context(
    session: Session,
    assessment: ThesisAssessment,
) -> dict[str, object]:
    delivery = session.exec(
        select(NotificationDelivery)
        .where(
            NotificationDelivery.ticker == assessment.ticker,
            NotificationDelivery.assessment_date < assessment.assessment_date,
            NotificationDelivery.channel == _notification_channel(),
            NotificationDelivery.status == "sent",
        )
        .order_by(
            NotificationDelivery.assessment_date.desc(),
            NotificationDelivery.id.desc(),
        )
    ).first()
    return working_capital_context_from_notification_payload(
        delivery.payload if delivery else None
    )


def _telegram_source_sha256(payload: dict[str, object]) -> str:
    logical_payload = _logical_notification_payload(payload)
    encoded = json.dumps(
        logical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_price(value: object, currency: object) -> str:
    if not isinstance(value, (int, float)):
        return "자료 없음"
    rendered = f"{float(value):,.0f}" if float(value).is_integer() else f"{float(value):,.2f}"
    if currency == "KRW":
        return f"{rendered}원"
    if currency == "USD":
        return f"${rendered}"
    return rendered


def _report_chart_price(value: object, currency: object) -> str:
    if isinstance(value, (int, float)) and currency == "KRW":
        return f"{float(value):,.0f}원"
    return _report_price(value, currency)


def _compact_krw(value: object) -> str | None:
    return compact_krw_amount(value)


def _earnings_period_label(value: object, preliminary: bool) -> str | None:
    if not value:
        return None
    try:
        period = date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)
    quarter = (period.month - 1) // 3 + 1
    suffix = " 잠정" if preliminary else ""
    return f"{period.year}년 {quarter}분기{suffix}"


_INTERNAL_FACT_MARKERS = (
    "opendart",
    "dart text",
    " financial fact:",
    " treasury stock fact:",
)
_INTERNAL_FACT_FIELD = re.compile(
    r"\b(?:fs_div|sj_div|period_scope|amount_scope|report_code|provider|parser|"
    r"selected_for_valuation|thstrm_nm|unit)\s*(?:=|:)",
    flags=re.IGNORECASE,
)


def _is_internal_fact(value: object) -> bool:
    text = str(value)
    lowered = text.lower()
    return any(marker in lowered for marker in _INTERNAL_FACT_MARKERS) or bool(
        _INTERNAL_FACT_FIELD.search(text)
    )


def _user_fact_lines(
    valuation_snapshot: dict[str, object],
    evidence: list[object],
    confirmed_facts: list[object],
    *,
    initial_baseline: bool,
) -> list[str]:
    lines: list[str] = []
    has_internal_financial_fact = any(
        "financial fact:" in str(item).lower() for item in confirmed_facts
    )
    if initial_baseline or has_internal_financial_fact:
        period = _earnings_period_label(
            valuation_snapshot.get("latest_earnings_period"),
            bool(valuation_snapshot.get("earnings_context_is_preliminary")),
        )
        revenue = _compact_krw(valuation_snapshot.get("latest_revenue"))
        operating_income = _compact_krw(
            valuation_snapshot.get("latest_operating_income")
        )
        margin = valuation_snapshot.get("latest_operating_margin")
        if period and revenue:
            lines.append(f"{period} 매출 {revenue}")
        if operating_income:
            operating_line = f"영업이익 {operating_income}"
            if isinstance(margin, (int, float)) and math.isfinite(float(margin)):
                operating_line += f" · 영업이익률 {float(margin):.1f}%"
            lines.append(operating_line)
    for item in evidence:
        if not isinstance(item, dict):
            continue
        contract_name = str(item.get("contract_name") or "").strip()
        contract_amount = _compact_krw(item.get("contract_amount"))
        if contract_name and not _is_internal_fact(contract_name):
            lines.append(
                f"{contract_name} · 계약금액 {contract_amount}"
                if contract_amount
                else contract_name
            )
        title = str(item.get("title") or "").strip()
        if (
            title
            and not _is_internal_fact(title)
            and not (
                len(lines) >= 2 and item.get("event_type") == "financial_report"
            )
        ):
            lines.append(title)
    return _unique_text(lines)[:3]


def _supply_quantity(value: object, *, signed: bool = True) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "자료 없음"
    number = float(value)
    if not math.isfinite(number):
        return "자료 없음"
    sign = "+" if signed and number > 0 else ""
    absolute = abs(number)
    if absolute >= 100_000_000:
        rendered = f"{number / 100_000_000:.2f}억주"
    elif absolute >= 10_000:
        rendered = f"{number / 10_000:,.1f}만주"
    else:
        rendered = f"{number:,.0f}주"
    return sign + rendered


_SUPPLY_QUALITY_LABELS = {
    "accumulation": "매집 우위",
    "strong_joint": "외국인·기관 동반 매집",
    "foreign_led": "외국인 주도 매집",
    "institution_led": "기관 주도 매집",
    "mixed_absorption": "혼합 흡수",
    "retail_led": "개인 주도 매집",
    "distribution": "분산/매도 우위",
    "mixed": "혼재",
    "neutral": "중립",
    "unknown": "판단 보류",
    "unavailable": "판단 보류",
}

_SUPPLY_SIGNAL_LABELS = {
    "foreign_exit_retail_absorption": "외국인 이탈·개인 흡수",
    "foreign_exit_institution_retail_absorption": "외국인 이탈·기관/개인 흡수",
    "foreign_reentry": "외국인 재유입",
    "foreign_reentry_signal": "외국인 재유입",
    "foreign_institution_joint_accumulation": "외국인·기관 동반 매집",
    "strong_joint": "외국인·기관 동반 매집",
    "foreign_led": "외국인 주도 매집",
    "institution_led": "기관 주도 매집",
    "mixed_absorption": "혼합 흡수",
    "retail_led": "개인 주도 매집",
    "distribution": "분산/매도 우위",
    "retail_chasing_warning": "개인 추격매수 주의",
    "institutional_distribution_warning": "기관 매도/분산 주의",
    "foreign_exit_broad_absorption": "외국인 순매도·흡수 주체 분산",
    "participant_attribution_unavailable": "전체 주체 귀속 확인 필요",
    "mixed_window_flow": "5일·20일 흐름 혼재",
    "material_other_participant_flow": "기타 투자주체 영향 큼",
}


def _supply_report(price_context: dict[str, object]) -> str | None:
    supply = price_context.get("supply")
    if not isinstance(supply, dict) or not supply.get("available"):
        return None
    as_of = str(supply.get("as_of_date") or "")
    try:
        parsed_date = date.fromisoformat(as_of[:10])
        date_label = f"{parsed_date.month}/{parsed_date.day} 기준"
    except ValueError:
        date_label = "기준일 확인 불가"

    def flow_line(label: str, suffix: str) -> str:
        return (
            f"{label}: 외국인 {_supply_quantity(supply.get(f'foreign_net_buy_qty{suffix}'))} · "
            f"기관 {_supply_quantity(supply.get(f'institution_net_buy_qty{suffix}'))} · "
            f"개인 {_supply_quantity(supply.get(f'individual_net_buy_qty{suffix}'))}"
        )

    scope_label = "(주요 3주체)" if supply.get("omitted_participant_materiality") else ""
    lines = [
        f"📊 수급{scope_label} · {date_label}",
        flow_line("당일", ""),
        flow_line("5일", "_5"),
        flow_line("20일", "_20"),
    ]
    holding = supply.get("foreign_holding_qty")
    ratio = supply.get("foreign_holding_ratio")
    if isinstance(holding, (int, float)) or isinstance(ratio, (int, float)):
        holding_text = _supply_quantity(holding, signed=False)
        ratio_text = f"{float(ratio):.1f}%" if isinstance(ratio, (int, float)) else "자료 없음"
        lines.append(f"외국인 보유: {holding_text} · {ratio_text}")
    validated = supply.get("validation_status") == "validated" and supply.get("confidence") not in {
        "low",
        "unavailable",
    }
    if validated:
        summary = []
        score = supply.get("score")
        if isinstance(score, (int, float)):
            summary.append(f"수급 점수: {float(score):g}")
        quality = _SUPPLY_QUALITY_LABELS.get(str(supply.get("quality") or ""))
        if quality and (
            supply.get("attribution_safe")
            or str(supply.get("quality") or "")
            in {"distribution", "mixed", "neutral", "unknown", "unavailable"}
        ):
            summary.append(quality)
        signal = _SUPPLY_SIGNAL_LABELS.get(str(supply.get("primary_signal") or ""))
        if signal:
            basis = str(supply.get("signal_basis_window") or "")
            if basis in {"5d", "20d"}:
                signal = f"{basis.removesuffix('d')}일 기준 {signal}"
            summary.append(signal)
        if summary:
            lines.append(" · ".join(dict.fromkeys(summary)))
    else:
        lines.append("⚠️ 수급 데이터 검증이 충분하지 않아 종합 신호는 참고 수준입니다.")
    return "\n".join(lines)


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


def _valuation_formula_lines(
    snapshot: dict[str, object],
    *,
    label: str,
    multiple_field: str,
    denominator_field: str,
    denominator_label: str,
) -> list[str]:
    status = str(snapshot.get(f"{multiple_field}_status", "unavailable"))
    multiple = snapshot.get(multiple_field)
    if status == "not_meaningful":
        return [f"{label}: N/M"]
    if status == "conflict":
        return [f"{label}: 판단 보류"]
    if status != "value" or not isinstance(multiple, (int, float)):
        return []
    price = snapshot.get("current_price")
    denominator = snapshot.get(denominator_field)
    currency = snapshot.get("currency")
    if (
        isinstance(price, (int, float))
        and isinstance(denominator, (int, float))
        and denominator > 0
        and abs(float(price) / float(denominator) / float(multiple) - 1) <= 0.02
    ):
        return [
            f"{label} = 현재가 ÷ {denominator_label} = "
            f"{_report_price(price, currency)} ÷ {_report_price(denominator, currency)} "
            f"= {float(multiple):.1f}배",
        ]
    return [f"{label}: {float(multiple):.1f}배"]


def _forward_denominator_label(
    snapshot: dict[str, object],
    *,
    multiple_field: str,
) -> tuple[str, bool]:
    if multiple_field == "forward_price_to_book":
        source = str(snapshot.get("forward_price_to_book_source") or "unavailable")
        return (
            ("내부 FY1 추정 BVPS", True)
            if source == "modeled_forward"
            else ("시장 예상 BVPS", False)
            if source == "consensus_forward"
            else ("예상 BVPS", False)
        )
    source = str(snapshot.get("forward_pe_source") or "unavailable")
    method = str(
        snapshot.get("forecast_method") or snapshot.get("forward_pe_method") or ""
    ).lower()
    if source == "modeled_forward":
        if "normalized_roe" in method or "normalized roe" in method:
            return "내부 정상화 ROE 추정 EPS", True
        if "normalized_net_margin" in method or "normalized net margin" in method:
            return "내부 정상화 마진 추정 EPS", True
        if "cycle_adjusted" in method or "cycle adjusted" in method:
            return "내부 사이클 조정 EPS", True
        return "내부 FY1 추정 EPS", True
    if source == "consensus_forward":
        return "시장 예상 EPS", False
    return "예상 EPS", False


def _history_summary(snapshot: dict[str, object]) -> str | None:
    parts: list[str] = []
    for label, key in (
        ("PER", "historical_pe_statistics"),
        ("PBR", "historical_pb_statistics"),
    ):
        statistics = snapshot.get(key)
        if not isinstance(statistics, dict) or not statistics.get("observation_count"):
            continue
        median_value = statistics.get("historical_median")
        percentile = statistics.get("current_percentile")
        details: list[str] = []
        if isinstance(median_value, (int, float)):
            details.append(f"중앙값 {float(median_value):.1f}배")
        if isinstance(percentile, (int, float)):
            details.append(f"{float(percentile):.0f}백분위")
        if details:
            parts.append(f"{label} " + " · ".join(details))
    return " · ".join(parts) if parts else None


def _usable_multiple(snapshot: dict[str, object], field: str) -> bool:
    value = snapshot.get(field)
    return bool(
        snapshot.get(f"{field}_status") == "value"
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def _fallback_valuation_context(
    snapshot: dict[str, object],
    *,
    identity_state: str,
) -> dict[str, object]:
    current_pe = _usable_multiple(snapshot, "trailing_pe")
    current_pb = _usable_multiple(snapshot, "price_to_book")
    forward_pe = _usable_multiple(snapshot, "forward_pe")
    forward_pb = _usable_multiple(snapshot, "forward_price_to_book")
    history_used = _history_summary(snapshot) is not None
    current_used = current_pe or current_pb
    forward_used = forward_pe or forward_pb
    selection = select_valuation_context(
        current_status="available" if current_used else "unavailable",
        historical_status="available" if history_used else "unavailable",
        peer_status="unavailable",
        forward_status="available" if forward_used else "unavailable",
        current_used=current_used,
        history_used=history_used,
        peer_used=False,
        forward_used=forward_used,
    )
    if identity_state in {"conflict", "unknown"}:
        summary = (
            "증권 유형과 주당 기준의 일치 여부를 확인하지 못해 배수 해석을 "
            "보류합니다."
        )
    elif identity_state == "verified_depositary" and not current_used:
        summary = (
            "예탁증권 identity는 확인됐지만 current-security denominator·share·"
            "currency basis를 확인하지 못해 배수 해석을 보류합니다."
        )
    elif current_pe and current_pb:
        summary = (
            "검증된 현재 PER/PBR과 과거 배수 분포를 함께 확인합니다."
            if history_used
            else "검증된 현재 PER/PBR 범위에서 해석합니다."
        )
    elif current_pe:
        summary = (
            "검증된 현재 PER과 과거 이익 배수 분포를 함께 확인합니다."
            if history_used
            else "검증된 현재 PER 범위에서 해석합니다."
        )
    elif current_pb and forward_pe:
        summary = (
            "검증된 현재 PBR과 예상 이익 배수를 사용하며, 사용할 수 없는 "
            "trailing PER은 제외합니다."
        )
    elif current_pb:
        summary = (
            "검증된 현재 PBR과 과거 장부가 배수 분포를 함께 확인하며, "
            "이익 기반 배수는 사용하지 않습니다."
            if history_used
            else "검증된 현재 PBR만 사용하며, 이익 기반 배수는 사용하지 않습니다."
        )
    elif forward_pe:
        summary = "검증된 예상 이익 배수만 사용하며, 현재 PER/PBR은 제외합니다."
    else:
        summary = "검증 가능한 현재 배수가 없어 Valuation 해석을 보류합니다."
    return {
        **selection.as_dict(),
        "impact": "unknown",
        "summary": summary,
    }


def _price_check_lines(
    checks: object,
    currency: object,
) -> list[str]:
    if not isinstance(checks, list):
        return []
    lines: list[str] = []
    for item in checks:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "확인")
        low = item.get("price_low")
        high = item.get("price_high")
        price = item.get("price")
        if isinstance(low, (int, float)) and isinstance(high, (int, float)):
            rendered = f"{_report_price(low, currency)}~{_report_price(high, currency)}"
        elif isinstance(price, (int, float)):
            rendered = _report_price(price, currency)
        else:
            continue
        lines.append(f"• {label}: {rendered}")
    return lines


def _zone_price_text(zone: dict[str, object], currency: object) -> str | None:
    low = zone.get("zone_low")
    high = zone.get("zone_high")
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)):
        return None
    return f"{_report_chart_price(low, currency)}~{_report_chart_price(high, currency)}"


def _risk_reward_unavailable_text(reason: object) -> str:
    return {
        "resistance_unavailable": (
            "가까운 유효 저항이 없어 현재가 기준 차트 손익비는 계산하지 않습니다."
        ),
        "invalidation_unavailable": (
            "유효한 차트 무효화 가격이 없어 현재가 기준 차트 손익비는 계산하지 않습니다."
        ),
        "monthly_invalidation_contract_undefined": (
            "월봉 지지의 무효화 기준이 정의되지 않아 현재가 기준 차트 손익비는 계산하지 않습니다."
        ),
        "support_unavailable": (
            "유효한 동적 지지가 없어 현재가 기준 차트 손익비는 계산하지 않습니다."
        ),
        "nearest_support_resistance_overlap": (
            "가까운 지지·저항 구간이 겹쳐 현재가 기준 차트 손익비는 계산하지 않습니다."
        ),
    }.get(str(reason or ""), "현재 가격 구조로는 차트 손익비를 계산할 수 없습니다.")


def _registered_confirmation_text(
    confirmation: dict[str, object],
    currency: object,
) -> str | None:
    price = confirmation.get("price")
    if not isinstance(price, (int, float)):
        return None
    rendered = _report_chart_price(price, currency)
    state = str(confirmation.get("state") or "")
    return {
        "not_reached": f"등록 확인선 {rendered}은 아직 도달하지 않았습니다.",
        "crossed": f"기존 {rendered} 확인선은 이번에 돌파했습니다.",
        "holding_above": f"기존 {rendered} 확인선은 이미 돌파한 상태입니다.",
        "retest_in_progress": f"기존 {rendered} 확인선의 재시험이 진행 중입니다.",
        "retest_held": f"기존 {rendered} 확인선 재시험 뒤 상단을 유지하고 있습니다.",
        "failed_breakout": f"기존 {rendered} 확인선 돌파 뒤 다시 이탈했습니다.",
    }.get(state)


def _dynamic_price_block(
    selection: dict[str, object],
    *,
    currency: object,
) -> tuple[list[str], list[str], list[str], str | None]:
    support = selection.get("active_support")
    resistance = selection.get("active_resistance")
    rr = selection.get("current_price_risk_reward")
    invalidation = selection.get("chart_invalidation")
    chart_state = selection.get("chart_state")
    confirmation = selection.get("registered_confirmation")
    support = support if isinstance(support, dict) else {}
    resistance = resistance if isinstance(resistance, dict) else {}
    rr = rr if isinstance(rr, dict) else {}
    invalidation = invalidation if isinstance(invalidation, dict) else {}
    chart_state = chart_state if isinstance(chart_state, dict) else {}
    confirmation = confirmation if isinstance(confirmation, dict) else {}

    observer: list[str] = []
    holder: list[str] = []
    history: list[str] = []
    support_text = _zone_price_text(support, currency)
    resistance_text = _zone_price_text(resistance, currency)
    if support.get("available") is True and support_text:
        observer.append(f"• 동적 지지: {support_text}")
    if resistance.get("available") is True and resistance_text:
        observer.append(f"• 동적 저항: {resistance_text}")
    if rr.get("available") is True and isinstance(rr.get("ratio"), (int, float)):
        rr_display = canonical_display_value(
            NUMERIC_SEMANTICS["current_price_risk_reward_ratio"],
            float(rr["ratio"]),
            "x",
        )
        if rr_display:
            observer.append(f"• 현재가 기준 차트 손익비: {rr_display}")
    else:
        observer.append(f"• {_risk_reward_unavailable_text(rr.get('reason'))}")
    if invalidation.get("available") is True and isinstance(
        invalidation.get("price"), (int, float)
    ):
        holder.append(
            f"• 차트 무효화 가격: {_report_chart_price(invalidation['price'], currency)}"
        )
    if support.get("available") is True and support_text:
        holder.append(f"• 동적 지지 유지 여부: {support_text}")
    if not holder:
        holder.append(
            "• 유효한 동적 지지와 차트 무효화 가격이 없어 현재 가격 관리 기준은 제공하지 않습니다."
        )
    confirmation_text = _registered_confirmation_text(confirmation, currency)
    if confirmation_text:
        history.append(f"• {confirmation_text}")
    state_text = {
        "WAIT": "가격 구조상 추가 확인 대기",
        "HOLD": "가격 구조상 유지 여부 점검",
        "TRIM": "가격 구조상 위험 관리 필요",
        "INVALID": "가격 구조 재검토 필요",
    }.get(str(chart_state.get("state") or ""))
    return observer, holder, history, state_text


def _concise_text(value: str, *, sentence_limit: int = 2, character_limit: int = 320) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", value.strip())
    concise = " ".join(sentence for sentence in sentences[:sentence_limit] if sentence)
    if len(concise) <= character_limit:
        return concise
    shortened = concise[:character_limit].rsplit(" ", 1)[0].rstrip("., ")
    return shortened + "."


def _preliminary_ttm_eps_caution(
    snapshot: dict[str, object],
    reason_codes: set[str] | list[str],
) -> str | None:
    reasons = set(reason_codes)
    ttm_usable = bool(snapshot.get("ttm_eps_usable", snapshot.get("eps_per_usable")))
    if not (
        snapshot.get("earnings_context_is_preliminary")
        and snapshot.get("earnings_context_usable")
        and not ttm_usable
    ):
        return None
    if snapshot.get("latest_eps_usable"):
        if "per_share_basis_insufficient" in reasons:
            return (
                "최근 분기 주당 실적은 확인했지만 이전 분기들의 주당 기준을 확인하지 못해 "
                "TTM EPS/PER 자체 계산을 보류했습니다."
            )
        return (
            "최근 분기 주당 실적은 확인했지만 최근 4개 분기 자료가 충분하지 않아 "
            "TTM EPS/PER 자체 계산을 보류했습니다."
        )
    if "per_share_basis_insufficient" in reasons:
        return (
            "최근 공식 잠정실적의 매출·영업이익은 반영했지만 주당 기준을 확인하지 못해 "
            "자체 PER 계산은 보류했습니다."
        )
    if snapshot.get("trailing_pe_status") == "value":
        return "최근 잠정실적은 매출·영업이익에 반영했지만 EPS 기준이 없어 PER는 이전 기준입니다."
    return "최근 잠정실적은 매출·영업이익에 반영했지만 TTM EPS 자체 계산은 보류했습니다."


def _data_cautions(
    snapshot: dict[str, object],
    coverage: dict[str, object],
) -> list[str]:
    cautions: list[str] = []
    reason_codes = coverage.get("reason_codes", [])
    reasons = {str(item) for item in reason_codes} if isinstance(reason_codes, list) else set()
    preliminary_quality = str(
        coverage.get("preliminary_financial_quality")
        or coverage.get("preliminary_financial_freshness")
        or ""
    )
    if "preliminary_period_mapping_failed" in reasons:
        cautions.append("최근 잠정실적의 기간 매핑을 검증하지 못해 정식 재무 기준으로 판단합니다.")
    elif preliminary_quality == "validation_failed" or "preliminary_validation_failed" in reasons:
        cautions.append(
            "최근 잠정실적 숫자 검증이 완료되지 않아 현재 배수는 검증된 정식 재무를 기준으로 봅니다."
        )
    full_freshness = str(coverage.get("full_financial_freshness") or "")
    refresh_status = str(coverage.get("financial_freshness") or "")
    if full_freshness == "stale" or refresh_status in {
        "refresh_due",
        "refresh_pending",
        "refresh_required",
        "stale",
    }:
        cautions.append("최신 정식 재무 반영이 지연돼 현재 Valuation 신뢰도를 낮춰 봅니다.")
    if snapshot.get("consensus_disagreement") or snapshot.get("consensus_status") == "conflicting":
        cautions.append("예상 이익 전망이 데이터 공급 경로마다 크게 달라 fPER는 참고 수준입니다.")
    elif (
        snapshot.get("forward_pe_reference_caution")
        and snapshot.get("forward_pe_status") == "value"
    ):
        reason = str(snapshot.get("forward_pe_reference_caution_reason") or "")
        cautions.append(
            "fPER는 산출 기간이 명확하지 않아 참고 수준입니다."
            if reason == "horizon_unknown"
            else "예상 이익 기준이 서로 달라 fPER는 참고 수준입니다."
        )
    per_share_basis_insufficient = "per_share_basis_insufficient" in reasons
    preliminary_ttm_caution = _preliminary_ttm_eps_caution(snapshot, reasons)
    if preliminary_ttm_caution:
        cautions.append(preliminary_ttm_caution)
    if snapshot.get("trailing_pe_basis_conflict"):
        cautions.append("PER 계산의 이익 기준이 서로 충돌해 해당 배수는 판단에서 제외했습니다.")
    if snapshot.get("price_to_book_basis_conflict"):
        cautions.append("PBR 계산의 장부가치 기준이 서로 충돌해 해당 배수는 판단에서 제외했습니다.")
    if snapshot.get("forward_pe_basis_conflict"):
        cautions.append(
            "fPER 계산의 예상 이익 기준이 서로 충돌해 해당 배수는 판단에서 제외했습니다."
        )
    if snapshot.get("forward_price_to_book_basis_conflict"):
        cautions.append(
            "fPBR 계산의 예상 장부가치 기준이 서로 충돌해 해당 배수는 판단에서 제외했습니다."
        )
    if "preliminary_profitability_outlier" in reasons:
        cautions.append(
            "최신 잠정실적의 수익성 관계에 중대한 검증 경고가 있어 "
            "매출·이익과 이익 기반 배수의 정량 해석을 보류합니다."
        )
    if per_share_basis_insufficient and not preliminary_ttm_caution:
        basis_statuses = {
            str(snapshot.get("trailing_pe_basis_status") or ""),
            str(snapshot.get("price_to_book_basis_status") or ""),
        }
        cautions.append(
            "가격 통화와 주당 실적 기준 통화가 달라 자체 PER/PBR 계산을 보류했습니다."
            if "currency_mismatch" in basis_statuses
            else "현재 거래 증권의 주당 기준을 확인하지 못해 자체 PER/PBR 계산을 보류했습니다."
        )
    elif "missing_adr_ratio" in reasons and not preliminary_ttm_caution:
        cautions.append("주식 변환 비율이 확인되지 않아 일부 주당 Valuation 계산을 보류했습니다.")
    if "foreign_financial_parsing_failed" in reasons:
        cautions.append(
            "최근 해외 공시 재무표의 자동 검증이 끝나지 않아 Valuation을 보수적으로 봅니다."
        )
    if snapshot.get("historical_comparability") in {
        "price_share_basis_unverified",
        "price_share_basis_mismatch",
    }:
        cautions.append(
            "과거 배수 비교의 가격·주식수 기준을 확인하지 못해 역사적 백분위는 보류했습니다."
        )
    return list(dict.fromkeys(cautions))


def _assessment_report(
    assessment: ThesisAssessment,
    company_name: str,
    thesis: InvestmentThesis | None,
    *,
    previous_cash_flow_user_visible_context: dict[str, object] | None = None,
    previous_working_capital_user_visible_context: dict[str, object] | None = None,
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
    business_change = getattr(assessment, "business_thesis_change", None) or assessment.status
    label = labels.get(business_change, business_change)
    earnings_impact = getattr(assessment, "earnings_estimate_impact", None) or "unknown"
    evidence = _json_list_value(assessment.evidence)
    confirmed_facts = _json_list_value(getattr(assessment, "confirmed_facts", "[]"))
    background_confirmed_facts = _json_list_value(
        getattr(assessment, "background_confirmed_facts", "[]")
    )
    inferred_implications = _json_list_value(getattr(assessment, "inferred_implications", "[]"))
    unknowns = _json_list_value(getattr(assessment, "unknowns", "[]"))
    confirmed_warnings = _json_list_value(getattr(assessment, "confirmed_warnings", "[]"))
    watch_items = _json_list_value(getattr(assessment, "watch_items", "[]"))
    market_expectation_assessment = _json_value(
        getattr(assessment, "market_expectation_assessment", "{}"), {}
    )
    price_context = _json_value(assessment.price_context, {})
    thesis_snapshot = _json_value(assessment.thesis_snapshot, {})
    assessment_mode = str(thesis_snapshot.get("assessment_mode") or "daily_delta")
    is_initial_baseline = assessment_mode == "initial_baseline"
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
    raw_valuation_snapshot = _json_value(
        getattr(assessment, "valuation_snapshot", "{}"), {}
    )
    latest_formal_period, latest_preliminary_period = financial_period_context(
        raw_valuation_snapshot
    )
    cash_flow_evidence = load_canonical_cash_flow_evidence(
        assessment.ticker,
        cutoff=assessment.assessment_date,
        latest_formal_period=latest_formal_period,
        latest_preliminary_period=latest_preliminary_period,
    )
    stored_core_thesis = (
        thesis.core_thesis
        if thesis
        else str(thesis_snapshot.get("base_thesis", "저장된 핵심 투자 논리가 없습니다."))
    )
    core_thesis_repair = repair_baseline_cash_flow_text(
        assessment.ticker,
        stored_core_thesis,
        cash_flow_evidence,
        text_ref="thesis.core_thesis",
        section="core_thesis",
        origin_type="saved_thesis",
        origin_version=(f"thesis:{assessment.ticker}:v{assessment.thesis_version}"),
    )
    core_thesis = core_thesis_repair.text
    financial_quality = build_financial_quality_state(raw_valuation_snapshot)
    valuation_snapshot = sanitize_financial_snapshot_for_prose(
        raw_valuation_snapshot
    )
    non_prose_financial_fields = set(
        financial_quality.get("non_prose_fields", [])
    )
    if non_prose_financial_fields.intersection(
        {
            "latest_revenue",
            "latest_operating_income",
            "latest_operating_margin",
            "latest_revenue_qoq",
            "latest_revenue_yoy",
            "latest_operating_income_qoq",
            "latest_operating_income_yoy",
        }
    ):
        earnings_impact = "unknown"
    if non_prose_financial_fields.intersection(
        {
            "ttm_eps",
            "trailing_pe",
            "forward_eps",
            "forward_pe",
            "valuation_relative_position",
        }
    ):
        quality_source_value = raw_valuation_snapshot.get(
            "financial_quality_source_metadata"
        )
        quality_source = (
            quality_source_value
            if isinstance(quality_source_value, dict)
            else _json_value(str(quality_source_value or "{}"), {})
        )
        identity_value = quality_source.get("security_identity", {})
        identity = identity_value if isinstance(identity_value, dict) else {}
        identity_state = str(
            raw_valuation_snapshot.get("security_identity_state")
            or identity.get("identity_state")
            or ""
        )
        valuation_context = _fallback_valuation_context(
            valuation_snapshot,
            identity_state=identity_state,
        )
    raw_confirmed_warnings = [
        str(item).strip() for item in confirmed_warnings if str(item).strip()
    ]
    new_warnings = [
        str(item)
        for item in _json_list_value(getattr(assessment, "new_warnings", "[]"))
        if not _is_internal_fact(item)
    ]
    open_warnings = [
        str(item)
        for item in _json_list_value(getattr(assessment, "open_warnings", "[]"))
        if not _is_internal_fact(item)
    ]
    raw_new_warnings = list(new_warnings)
    raw_open_warnings = list(open_warnings)
    raw_open_confirmed_warnings = [
        str(item).strip()
        for item in _json_list_value(
            getattr(assessment, "open_confirmed_warnings", "[]")
        )
        if str(item).strip() and not _is_internal_fact(item)
    ]
    open_confirmed_warnings = (
        list(raw_open_confirmed_warnings)
        or open_warnings
    )
    warning_states_raw = _json_value(getattr(assessment, "warning_states", "[]"), [])
    warning_states = (
        [item for item in warning_states_raw if isinstance(item, dict)]
        if isinstance(warning_states_raw, list)
        else []
    )
    warning_state_by_text = {
        str(item.get("warning")): item for item in warning_states if item.get("warning")
    }
    shared_baseline_decisions = audit_shared_baseline_cash_flow_inputs(
        assessment.ticker,
        cash_flow_evidence,
        core_thesis=stored_core_thesis,
        assessment_summary=str(assessment.summary or ""),
        warning_groups={
            "confirmed_warnings": raw_confirmed_warnings,
            "new_warnings": raw_new_warnings,
            "open_confirmed_warnings": raw_open_confirmed_warnings,
            "open_warnings": raw_open_warnings,
        },
        origin_version=str(assessment.assessment_date),
        provenance_by_text=warning_state_by_text,
    )
    suppressed_baseline_claim_ids = baseline_suppressed_claim_ids(
        shared_baseline_decisions
    )
    new_warnings, _ = repair_baseline_cash_flow_items(
        assessment.ticker,
        new_warnings,
        cash_flow_evidence,
        section="new_warnings",
        origin_type="assessment_warning",
        origin_version=str(assessment.assessment_date),
        provenance_by_text=warning_state_by_text,
    )
    open_warnings, _ = repair_baseline_cash_flow_items(
        assessment.ticker,
        open_warnings,
        cash_flow_evidence,
        section="open_warnings",
        origin_type="assessment_warning",
        origin_version=str(assessment.assessment_date),
        provenance_by_text=warning_state_by_text,
    )
    open_confirmed_warnings, _ = repair_baseline_cash_flow_items(
        assessment.ticker,
        open_confirmed_warnings,
        cash_flow_evidence,
        section="open_confirmed_warnings",
        origin_type="assessment_warning",
        origin_version=str(assessment.assessment_date),
        provenance_by_text=warning_state_by_text,
    )
    confirmed_warnings, _ = repair_baseline_cash_flow_items(
        assessment.ticker,
        [str(item) for item in confirmed_warnings],
        cash_flow_evidence,
        section="confirmed_warnings",
        origin_type="assessment_warning",
        origin_version=str(assessment.assessment_date),
        provenance_by_text=warning_state_by_text,
    )
    cash_flow_source_text = " ".join(
        str(value)
        for value in (
            stored_core_thesis,
            json.dumps(thesis_drivers, ensure_ascii=False),
            json.dumps(validation_metrics, ensure_ascii=False),
        )
        if value
    )
    cash_flow_selection = safe_select_user_visible_cash_flow(
        ticker=assessment.ticker,
        cutoff=assessment.assessment_date,
        latest_formal_period=latest_formal_period,
        latest_preliminary_period=latest_preliminary_period,
        existing_unknowns=[str(item) for item in unknowns],
        materiality_signals=[
            *[str(item) for item in thesis_drivers],
            *[str(item) for item in validation_metrics],
            *[
                str(item)
                for item in _json_list_value(
                    getattr(assessment, "persistent_watch_risks", "[]")
                )
            ],
        ],
        source_text=cash_flow_source_text,
        suppressed_baseline_claim_ids=suppressed_baseline_claim_ids,
        previous_user_visible_context=previous_cash_flow_user_visible_context,
    )
    unknowns = list(
        resolve_selected_unknowns(
            [str(item) for item in unknowns],
            cash_flow_selection,
            industry=cash_flow_selection.industry,
            source_text=cash_flow_source_text,
        )
    )
    cash_flow_period_end = (
        cash_flow_selection.reasoning_context.primary_period.end
        if cash_flow_selection.reasoning_context
        and cash_flow_selection.reasoning_context.primary_period
        else None
    )
    working_capital_context = safe_select_user_visible_inventory(
        ticker=assessment.ticker,
        market="kr" if assessment.ticker.isdigit() else "us",
        packet_id=f"pending:{assessment.assessment_date}:{assessment.ticker}",
        assessment_date=assessment.assessment_date,
        industry="",
        monitoring_text=cash_flow_source_text,
        existing_unknowns=[str(item) for item in unknowns],
        latest_formal_balance_date=latest_formal_period,
        latest_provisional_period_end=latest_preliminary_period,
        cash_flow_context_id=cash_flow_selection.context_id,
        cash_flow_period_end=cash_flow_period_end,
        previous_user_visible_context=(
            previous_working_capital_user_visible_context
        ),
    )
    unknowns = list(
        resolve_selected_inventory_unknowns(unknowns, working_capital_context)
    )
    working_capital_text = (
        render_working_capital_user_visible(
            working_capital_context,
            channel="fallback",
        ).text
        if working_capital_context is not None
        else None
    )

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

    prior_open_warnings = [item for item in open_confirmed_warnings if item not in new_warnings]
    persistent_watch_risks = _json_list_value(getattr(assessment, "persistent_watch_risks", "[]"))
    structural_risk = str(getattr(assessment, "structural_risk_level", "normal") or "normal")
    assessment_state = str(getattr(assessment, "assessment_state", "final") or "final")
    market_session = str(getattr(assessment, "market_session", "unknown") or "unknown")
    evidence_items = evidence
    evidence_lines = [
        f"• {item.get('title', '제목 없음')} ({item.get('direction', '확인')})"
        for item in evidence_items[:3]
        if isinstance(item, dict) and not _is_internal_fact(item.get("title", ""))
    ]
    change_text = "\n".join(evidence_lines) or "• 투자 판단을 바꿀 새 근거가 확인되지 않았습니다."
    user_facts = _user_fact_lines(
        valuation_snapshot,
        evidence_items,
        confirmed_facts,
        initial_baseline=is_initial_baseline,
    )
    if user_facts:
        change_text = "\n".join(f"• {item}" for item in user_facts)
    elif business_change == "no_material_change":
        change_text = "• 오늘 투자 논리를 바꿀 신규 확정 사실은 확인되지 않았습니다."
    expectation_level = str(market_expectations.get("level", "unknown"))
    valuation_impact = str(valuation_context.get("summary", "Valuation 영향 판단 자료가 없습니다."))
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
    current_price_context = select_current_price_context(price_context)
    uses_current_structure = current_price_context.get("availability") != "legacy_only"
    current_price = (
        current_price_context.get("current_price")
        if uses_current_structure
        else valuation_snapshot.get("current_price", decision.get("current_price"))
    )
    currency = (
        current_price_context.get("currency")
        if uses_current_structure
        else valuation_snapshot.get("currency", decision.get("currency"))
    ) or valuation_snapshot.get("currency", decision.get("currency"))
    price_as_of = valuation_snapshot.get(
        "exchange_trade_date",
        valuation_snapshot.get(
            "price_as_of", decision.get("exchange_trade_date", decision.get("price_as_of"))
        ),
    )
    if uses_current_structure:
        price_as_of = current_price_context.get("as_of_date") or price_as_of
    price_basis = str(
        current_price_context.get("price_basis")
        if uses_current_structure
        else valuation_snapshot.get("price_basis", decision.get("price_basis", ""))
    )
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
    new_buyer_price_view = str(getattr(assessment, "new_buyer_price_view", "") or "")
    holder_price_view = str(getattr(assessment, "holder_price_view", "") or "")
    data_coverage = valuation_snapshot.get("data_coverage", {})
    if not isinstance(data_coverage, dict):
        data_coverage = {}
    relative_position = str(valuation_snapshot.get("valuation_relative_position", "unknown"))
    relative_label = {
        "discounted": "할인 구간",
        "somewhat_discounted": "다소 할인",
        "neutral": "중립 범위",
        "somewhat_premium": "다소 부담",
        "premium": "부담 구간",
        "unknown": "판단 자료 부족",
    }.get(relative_position, "판단 자료 부족")
    relative_reason = str(
        valuation_snapshot.get("valuation_relative_position_reason") or ""
    ).strip()
    if (
        relative_position == "unknown"
        and valuation_context.get("contract") == VALUATION_CONTEXT_CONTRACT
    ):
        relative_reason = ""
    matched_today = _unique_text(
        str(signal)
        for item in evidence_items
        if isinstance(item, dict) and item.get("event_type") != "price_rule"
        for signal in item.get("matched_signals", [])
        if str(signal).strip()
    )
    sections: list[str] = [f"🏢 {company_name}({assessment.ticker})"]
    if is_initial_baseline:
        sections.append("투자 논리: 초기 설정")
    elif business_change == "no_material_change":
        sections.append("투자 논리: 유지 · 오늘 중요한 신규 변화 없음")
    else:
        sections.append(f"투자 논리: {label}")
    sections.extend(
        [
            f"구조적 위험: {risk_label}",
            f"시장 기대: {expectation_label}",
            f"🎯 핵심\n{_concise_text(core_thesis)}",
        ]
    )
    if is_initial_baseline and change_text:
        sections.append(f"📌 초기 근거\n{change_text}")
    elif business_change != "no_material_change" and change_text:
        sections.append(f"🔄 중요한 변화\n{change_text}")
    business_earnings_lines = [
        item
        for item in (cash_flow_selection.rendered_text, working_capital_text)
        if item
    ]
    if business_earnings_lines:
        sections.append(f"📈 사업·실적\n{' '.join(business_earnings_lines)}")
    if new_warnings and not is_initial_baseline:
        sections.append("🚨 오늘 새 경고\n" + _bullet_text(new_warnings, ""))
    if prior_open_warnings:
        sections.append("⚠️ 기존 경고\n" + _bullet_text(prior_open_warnings, ""))
    if persistent_watch_risks:
        sections.append("👁 핵심 감시\n" + _bullet_text(persistent_watch_risks, "", limit=3))
    if matched_today and not is_initial_baseline:
        sections.append("📍 오늘 접근한 조건\n" + _bullet_text(matched_today, ""))

    price_lines = [
        "💰 가격",
        f"현재가: {_report_price(current_price, currency)} · {price_basis_label}",
    ]
    if uses_current_structure:
        observer_checks, holder_checks, history_checks, chart_state_text = (
            _dynamic_price_block(current_price_context, currency=currency)
        )
        if chart_state_text:
            price_lines.append(f"현재 구조: {chart_state_text}")
    else:
        price_lines.append(
            f"현재 위치: {decision.get('current_position', assessment.price_view)}"
        )
        observer_checks = _price_check_lines(
            decision.get("new_observer_checks"), currency
        )
        holder_checks = _price_check_lines(decision.get("holder_checks"), currency)
        history_checks = []
    if observer_checks:
        price_lines.extend(["신규 관찰자:", *observer_checks])
    elif new_buyer_price_view and not uses_current_structure:
        price_lines.extend(
            ["신규 관찰자:", *_audience_price_text(new_buyer_price_view, "").splitlines()]
        )
    if holder_checks:
        holder_checks = [line for line in holder_checks if line not in observer_checks]
    if holder_checks:
        price_lines.extend(["보유자:", *holder_checks])
    elif holder_price_view and not uses_current_structure:
        price_lines.extend(["보유자:", *_audience_price_text(holder_price_view, "").splitlines()])
    if history_checks:
        price_lines.extend(["가격 규칙 이력:", *history_checks])
    if assessment_state == "provisional":
        price_lines.append("⚠️ 현재 장중 데이터로 가격 판단은 잠정입니다.")
    sections.append("\n".join(price_lines))

    price_structure_v3_decision = None
    settings = get_settings()
    price_structure_enabled = (
        settings.kr_price_structure_v3_enabled
        if is_krx
        else settings.us_price_structure_v3_enabled
    )
    if price_structure_enabled:
        chart = price_context.get("chart")
        chart = chart if isinstance(chart, dict) else {}
        structure = chart.get("structure")
        structure = structure if isinstance(structure, dict) else {}
        price_structure_v3 = structure.get("price_structure_v3")
        price_structure_v3 = (
            price_structure_v3 if isinstance(price_structure_v3, dict) else {}
        )
        decision_builder = (
            build_kr_price_structure_rollout_decision
            if is_krx
            else build_us_price_structure_rollout_decision
        )
        price_structure_v3_decision = decision_builder(
            price_structure_v3, ticker=assessment.ticker, monitored_subject=True
        )

    if is_krx:
        supply_section = _supply_report(price_context)
        if supply_section:
            sections.append(supply_section)

    valuation_lines = ["📐 Valuation"]
    modeled_forward_formula = False
    for arguments in (
        ("PER", "trailing_pe", "ttm_eps", "TTM EPS"),
        ("PBR", "price_to_book", "bvps", "BVPS"),
        ("fPER", "forward_pe", "forward_eps", "예상 EPS"),
        ("fPBR", "forward_price_to_book", "forward_bvps", "예상 BVPS"),
    ):
        denominator_label = arguments[3]
        is_modeled = False
        if arguments[0] == "PER" and valuation_snapshot.get("ttm_contains_preliminary"):
            denominator_label = "최근 4개 분기 EPS"
        if arguments[0] in {"fPER", "fPBR"}:
            denominator_label, is_modeled = _forward_denominator_label(
                valuation_snapshot,
                multiple_field=arguments[1],
            )
        rendered_formula = _valuation_formula_lines(
            valuation_snapshot,
            label=arguments[0],
            multiple_field=arguments[1],
            denominator_field=arguments[2],
            denominator_label=denominator_label,
        )
        valuation_lines.extend(rendered_formula)
        modeled_forward_formula = modeled_forward_formula or (
            is_modeled
            and any(" = 현재가 ÷ " in line for line in rendered_formula)
        )
        if (
            arguments[0] == "PER"
            and rendered_formula
            and valuation_snapshot.get("ttm_contains_preliminary")
        ):
            valuation_lines.append("※ 최근 분기 잠정실적 반영")
    if modeled_forward_formula:
        valuation_lines.append("※ 내부 모델 추정치이며 시장 컨센서스가 아닙니다.")
    if (
        valuation_snapshot.get("earnings_context_is_preliminary")
        and valuation_snapshot.get("earnings_context_usable")
        and not valuation_snapshot.get("eps_per_usable")
        and valuation_snapshot.get("trailing_pe_status") != "value"
    ):
        valuation_lines.append("※ 최근 분기 잠정실적의 매출·영업이익을 반영했습니다.")
    history_summary = _history_summary(valuation_snapshot)
    if history_summary:
        valuation_lines.extend(["과거 대비:", history_summary])
    valuation_lines.append(f"현재 Valuation: {relative_label}")
    if relative_reason:
        valuation_lines.append(f"해석: {relative_reason}")
    if impact_label != "중립":
        valuation_lines.append(f"오늘 Valuation 변화: {impact_label}")
        if valuation_impact:
            valuation_lines.append(valuation_impact)
    if earnings_impact not in {"unchanged", "unknown", "none", "neutral"}:
        earnings_label = {"up": "상향", "down": "하향", "mixed": "혼재"}.get(
            earnings_impact, earnings_impact
        )
        valuation_lines.append(f"이익 추정: {earnings_label}")
    if len(valuation_lines) > 3:
        sections.append("\n".join(valuation_lines))

    cautions = _data_cautions(valuation_snapshot, data_coverage)
    if cautions:
        sections.append("⚠️ 데이터 주의\n" + _bullet_text(cautions, ""))
    next_checks = validation_metrics[:3] or persistent_watch_risks[:3]
    if next_checks:
        sections.append("📌 다음 확인\n" + _bullet_text(next_checks, ""))
    fallback = "\n\n".join(section for section in sections if section.strip())
    if (
        price_structure_v3_decision is not None
        and price_structure_v3_decision.section
    ):
        fallback = replace_legacy_price_surface(
            fallback,
            price_structure_v3_decision.section,
        )
    fallback_price_errors = fallback_price_context_errors(
        current_price_context,
        fallback,
    )
    if fallback_price_errors:
        raise ValueError(";".join(fallback_price_errors))
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
            "current_price_context": current_price_context,
            "fallback_price_context_validation": {
                "status": "passed",
                "errors": [],
            },
            "new_buyer_price_view": new_buyer_price_view,
            "holder_price_view": holder_price_view,
            "valuation_snapshot": valuation_snapshot,
            "valuation_context": valuation_context,
        },
        "cash_flow_user_visible": cash_flow_selection_to_dict(
            cash_flow_selection
        ),
        **(
            {
                "price_structure_v3_rollout": (
                    price_structure_v3_decision.to_dict()
                )
            }
            if price_structure_v3_decision is not None
            else {}
        ),
        **(
            {
                "working_capital_user_visible": working_capital_context_to_dict(
                    working_capital_context
                )
            }
            if working_capital_context is not None
            else {}
        ),
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
    text, _analysis_context = _assessment_report(
        assessment,
        company_name,
        thesis,
        previous_cash_flow_user_visible_context=(
            _previous_cash_flow_user_visible_context(session, assessment)
        ),
        previous_working_capital_user_visible_context=(
            _previous_working_capital_user_visible_context(session, assessment)
        ),
    )
    evidence = [item for item in _json_list_value(assessment.evidence) if isinstance(item, dict)]
    dedupe_keys = [
        str(item.get("url") or f"{item.get('date')}:{item.get('title')}") for item in evidence
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
        _prepare_delivery_for_retry(delivery, payload)


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
    text, analysis_context = _assessment_report(
        assessment,
        company_name,
        thesis,
        previous_cash_flow_user_visible_context=(
            _previous_cash_flow_user_visible_context(session, assessment)
        ),
        previous_working_capital_user_visible_context=(
            _previous_working_capital_user_visible_context(session, assessment)
        ),
    )
    assessment_mode = _assessment_mode(assessment)
    payload_data: dict[str, object] = {
        "text": text,
        "ticker": assessment.ticker,
        "assessment_date": str(assessment.assessment_date),
        "status": assessment.status,
        "type": "daily_stock_analysis",
        "presentation": "long_text",
        "use_llm": False,
        "thesis_version": assessment.thesis_version,
        "assessment_mode": assessment_mode,
        "analysis_context": analysis_context,
    }
    current_logical_sha256 = _notification_logical_sha256(payload_data)
    current_event_fingerprints = _assessment_event_fingerprints(assessment)
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == assessment.ticker,
            NotificationDelivery.assessment_date == assessment.assessment_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        payload_data[STOCK_NOTIFICATION_METADATA_KEY] = _stock_notification_metadata(
            delivery_thesis_version=assessment.thesis_version,
            delivery_assessment_mode=assessment_mode,
            requeue_reason="new_delivery",
            active_logical_sha256=current_logical_sha256,
            relevant_event_fingerprints=current_event_fingerprints,
        )
        delivery = NotificationDelivery(
            ticker=assessment.ticker,
            assessment_date=assessment.assessment_date,
            channel=channel,
            status="pending",
            payload=json.dumps(payload_data, ensure_ascii=False),
        )
        session.add(delivery)
        return delivery

    existing_payload = _delivery_payload(delivery.payload)
    existing_metadata = existing_payload.get(STOCK_NOTIFICATION_METADATA_KEY)
    previous_thesis_version = _notification_thesis_version(existing_payload)
    stored_delivery_mode = _notification_assessment_mode(existing_payload)
    active_logical_sha256 = _notification_logical_sha256(existing_payload)
    deferred = _deferred_stock_notifications(existing_payload)
    new_version_baseline = (
        assessment_mode == "initial_baseline"
        and previous_thesis_version is not None
        and previous_thesis_version != assessment.thesis_version
    )
    if new_version_baseline:
        superseded_hashes = [
            active_logical_sha256,
            *[
                str(item["logical_sha256"])
                for item in deferred
                if isinstance(item.get("logical_sha256"), str)
            ],
        ]
        payload_data[STOCK_NOTIFICATION_METADATA_KEY] = _stock_notification_metadata(
            delivery_thesis_version=assessment.thesis_version,
            delivery_assessment_mode=assessment_mode,
            requeue_reason="new_thesis_version_initial_baseline",
            previous_thesis_version=previous_thesis_version,
            previous_delivery_status=delivery.status,
            active_logical_sha256=current_logical_sha256,
            supersede_reason="superseded_by_new_thesis_version",
            superseded_notification_hashes=superseded_hashes,
            relevant_event_fingerprints=current_event_fingerprints,
        )
        _prepare_delivery_for_retry(
            delivery,
            json.dumps(payload_data, ensure_ascii=False),
            reset_attempts=True,
        )
    elif previous_thesis_version == assessment.thesis_version and delivery.status != "sent":
        if _material_daily_delta(assessment):
            deferred = _append_deferred_notification(
                deferred,
                _deferred_stock_notification(payload_data, assessment),
                active_logical_sha256=active_logical_sha256,
            )
        protected_baseline = stored_delivery_mode == "initial_baseline"
        existing_payload[STOCK_NOTIFICATION_METADATA_KEY] = (
            _stock_notification_metadata(
                delivery_thesis_version=assessment.thesis_version,
                delivery_assessment_mode=stored_delivery_mode,
                current_thesis_version=assessment.thesis_version,
                current_assessment_mode=assessment_mode,
                requeue_reason=(
                    "material_delta_deferred"
                    if _material_daily_delta(assessment)
                    else "undelivered_delivery_preserved"
                ),
                previous_thesis_version=_previous_thesis_version(existing_metadata),
                previous_delivery_status=delivery.status,
                delivery_protection=(
                    "undelivered_baseline"
                    if protected_baseline
                    else "undelivered_material_delta"
                ),
                active_logical_sha256=active_logical_sha256,
                deferred_notifications=deferred,
                relevant_event_fingerprints=_metadata_text_list(
                    existing_metadata,
                    "relevant_event_fingerprints",
                ),
            )
        )
        _preserve_queued_delivery_payload(delivery, existing_payload)
    elif delivery.status != "sent":
        payload_data[STOCK_NOTIFICATION_METADATA_KEY] = _stock_notification_metadata(
            delivery_thesis_version=assessment.thesis_version,
            delivery_assessment_mode=assessment_mode,
            requeue_reason="pending_payload_refresh",
            previous_thesis_version=previous_thesis_version,
            previous_delivery_status=delivery.status,
            active_logical_sha256=current_logical_sha256,
            relevant_event_fingerprints=current_event_fingerprints,
        )
        _prepare_delivery_for_retry(
            delivery,
            json.dumps(payload_data, ensure_ascii=False),
        )
    elif (
        previous_thesis_version == assessment.thesis_version
        and delivery.status == "sent"
        and _material_daily_delta(assessment)
        and current_logical_sha256 != active_logical_sha256
    ):
        payload_data[STOCK_NOTIFICATION_METADATA_KEY] = _stock_notification_metadata(
            delivery_thesis_version=assessment.thesis_version,
            delivery_assessment_mode=assessment_mode,
            requeue_reason="material_delta_after_previous_delivery",
            previous_thesis_version=previous_thesis_version,
            previous_delivery_status=delivery.status,
            active_logical_sha256=current_logical_sha256,
            relevant_event_fingerprints=current_event_fingerprints,
        )
        _prepare_delivery_for_retry(
            delivery,
            json.dumps(payload_data, ensure_ascii=False),
            reset_attempts=True,
        )
    elif _should_requeue_sent_delivery(delivery, requeue_sent_before):
        payload_data[STOCK_NOTIFICATION_METADATA_KEY] = _stock_notification_metadata(
            delivery_thesis_version=assessment.thesis_version,
            delivery_assessment_mode=assessment_mode,
            requeue_reason="sent_before_production_cutoff",
            previous_thesis_version=previous_thesis_version,
            previous_delivery_status=delivery.status,
            active_logical_sha256=current_logical_sha256,
            relevant_event_fingerprints=current_event_fingerprints,
        )
        _prepare_delivery_for_retry(
            delivery,
            json.dumps(payload_data, ensure_ascii=False),
            reset_attempts=True,
        )
    return delivery


def queue_macro_notification(
    session: Session,
    briefing: MacroBriefing,
    *,
    requeue_sent: bool = False,
) -> NotificationDelivery:
    text, analysis_context = _macro_report(briefing)
    is_kr_close = briefing.briefing_type == "kr_close"
    marker = "__MACRO_KR_CLOSE__" if is_kr_close else "__MACRO__"
    payload = json.dumps(
        {
            "text": text,
            "briefing_date": str(briefing.briefing_date),
            "type": "macro_kr_close" if is_kr_close else "macro_morning",
            "presentation": "long_text",
            "use_llm": False,
            "analysis_context": analysis_context,
        },
        ensure_ascii=False,
    )
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == marker,
            NotificationDelivery.assessment_date == briefing.briefing_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        delivery = NotificationDelivery(
            ticker=marker,
            assessment_date=briefing.briefing_date,
            channel=channel,
            status="pending",
            payload=payload,
        )
        session.add(delivery)
    elif delivery.status != "sent":
        _prepare_delivery_for_retry(delivery, payload)
    elif requeue_sent:
        _prepare_delivery_for_retry(delivery, payload, reset_attempts=True)
    return delivery


def queue_daily_digest_notification(
    session: Session,
    run_date: date,
    market_scope: str = "all",
    requeue_sent_before: datetime | None = None,
) -> NotificationDelivery | None:
    current = datetime.now(timezone.utc)
    market_context = (
        load_current_kr_digest_context(
            run_date,
            as_of=current,
            cutoff=current,
        )
        if market_scope == "kr"
        else None
    )
    digest = build_daily_digest(
        session,
        run_date,
        market_scope=market_scope,
        market_context=market_context,
    )
    us_market_digest_plan = (
        digest.us_market_digest_plan.to_dict()
        if getattr(digest, "us_market_digest_plan", None) is not None
        else None
    )
    us_market_digest_consumption = (
        {
            "contract": "us-market-digest-plan-consumption-v1",
            "selected_slots": [
                item.slot.value
                for item in digest.us_market_digest_plan.primary_claims()
            ],
            "evidence_refs": list(
                digest.us_market_digest_plan.required_evidence_refs()
            ),
        }
        if getattr(digest, "us_market_digest_plan", None) is not None
        else None
    )
    payload = json.dumps(
        {
            "text": render_daily_digest(digest, include_stock_details=False),
            "briefing_date": str(run_date),
            "type": "daily_monitoring_digest",
            "market_scope": market_scope,
            "presentation": "long_text",
            "use_llm": False,
            **(
                {
                    "us_market_digest_plan": us_market_digest_plan,
                    "us_market_digest_consumption": us_market_digest_consumption,
                }
                if us_market_digest_plan is not None
                else {}
            ),
        },
        ensure_ascii=False,
    )
    channel = _notification_channel()
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == (
                "__DAILY_DIGEST_KR__" if market_scope == "kr" else "__DAILY_DIGEST__"
            ),
            NotificationDelivery.assessment_date == run_date,
            NotificationDelivery.channel == channel,
        )
    ).first()
    if delivery is None:
        delivery = NotificationDelivery(
            ticker="__DAILY_DIGEST_KR__" if market_scope == "kr" else "__DAILY_DIGEST__",
            assessment_date=run_date,
            channel=channel,
            status="pending",
            payload=payload,
        )
        session.add(delivery)
    elif delivery.status != "sent" and _ai_assisted_pilot_owns_pending_payload(
        _delivery_payload(delivery.payload)
    ):
        return delivery
    elif delivery.status != "sent":
        _prepare_delivery_for_retry(delivery, payload)
    elif _should_requeue_sent_delivery(delivery, requeue_sent_before):
        _prepare_delivery_for_retry(delivery, payload, reset_attempts=True)
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
        if (axes["growth_momentum"] >= 1 and axes["inflation_pressure"] <= 0) or (
            axes["growth_momentum"] >= 0 and axes["inflation_pressure"] <= -1
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
        signal = int(axes["financial_conditions"] >= 1) - int(axes["financial_conditions"] <= -1)
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


def _kr_close_macro_report(briefing: MacroBriefing) -> tuple[str, dict[str, object]]:
    market = _json_value(briefing.market_summary, {})
    quality = _json_value(briefing.data_quality, [])
    quality_items = quality if isinstance(quality, list) else []
    body = render_kr_close_fx(summarize_kr_close_fx(briefing))
    text = f"🇰🇷 한국 시장환경 점검 · {briefing.briefing_date}\n{body}"
    return text, {
        "analysis_type": "macro_kr_close",
        "briefing_date": str(briefing.briefing_date),
        "as_of": str(briefing.as_of),
        "market": market,
        "data_quality": quality_items,
    }


def _night_futures_section(market: object) -> str:
    return render_night_futures(summarize_night_futures(market))


def _macro_report(briefing: MacroBriefing) -> tuple[str, dict[str, object]]:
    if getattr(briefing, "briefing_type", "morning") == "kr_close":
        return _kr_close_macro_report(briefing)
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
    impact_items = (
        [item for item in impacts if isinstance(item, dict)] if isinstance(impacts, list) else []
    )
    impact_detail_lines = [
        f"• {item.get('ticker')}: "
        f"{IMPACT_LABELS.get(str(item.get('direction')), item.get('direction'))} · "
        f"이익 {item.get('earnings_effect', 'neutral')} · "
        f"Valuation {item.get('valuation_effect', 'neutral')}"
        + (f" · {item.get('rationale')}" if item.get("rationale") else "")
        for item in impact_items[:5]
    ]
    impact_detail_text = (
        "\n".join(impact_detail_lines) or "• 강한 종목별 거시 전달 경로가 없습니다."
    )
    calendar_items = calendar if isinstance(calendar, list) else []
    quality_items = quality if isinstance(quality, list) else []
    night_futures = summarize_night_futures(market)
    calendar_text = (
        ", ".join(
            str(item.get("title", "일정")) for item in calendar_items[:5] if isinstance(item, dict)
        )
        or "등록된 주요 일정 없음"
    )
    quality_lines: list[str] = []
    for item in quality_items[:5]:
        if not isinstance(item, dict):
            continue
        if item.get("warning"):
            if is_night_futures_warning(item["warning"]):
                if not night_futures.cautions:
                    line = (
                        "• 한국 야간선물은 최신 완료 세션 데이터를 확인하지 못해 "
                        "오늘 개장 전 신호에서 제외했습니다."
                    )
                    if line not in quality_lines:
                        quality_lines.append(line)
                continue
            quality_lines.append(f"• {item['warning']}")
            continue
        series_code = str(item.get("series_code", "데이터"))
        if series_code in NIGHT_FUTURES_SERIES:
            continue
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
    quality_lines.extend(f"• {item}" for item in night_futures.cautions)
    quality_text = "\n".join(quality_lines) or "• 특이사항 없음"
    night_futures_text = _night_futures_section(market)
    night_futures_block = f"\n\n{night_futures_text}" if night_futures_text else ""
    change_heading = (
        "오늘 가장 중요한 변화"
        if macro.changes_heading == "중요한 변화"
        else macro.changes_heading
    )
    fallback = (
        f"🌍 시장환경 점검 · {briefing.briefing_date}\n"
        f"⚠️ {macro.regime_label} 국면 · 판단 신뢰도 {macro.confidence:.0%}\n\n"
        f"🎯 {macro.one_line_heading}\n{macro.one_line}\n\n"
        f"📈 {change_heading}\n"
        f"{change_text or '• 임계치를 넘은 핵심 시장 변화가 없습니다.'}"
        f"{night_futures_block}\n\n"
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


class TelegramDeliveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class TelegramChunkResult:
    message_id: int | None = None


class TelegramNotifier:
    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        narrative_generator: InvestmentNarrativeGenerator | None = None,
    ) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.narrative_generator = narrative_generator

    async def _send_chunk(
        self,
        client: httpx.AsyncClient,
        text: str,
    ) -> TelegramChunkResult:
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

            if (
                response.status_code >= 400
                or not isinstance(payload, dict)
                or not payload.get("ok")
            ):
                description = (
                    str(payload.get("description", "request rejected"))
                    if isinstance(payload, dict)
                    else "invalid response"
                )
                raise TelegramDeliveryError(
                    f"Telegram sendMessage failed with HTTP {response.status_code}: "
                    f"{description[:200]}"
                )
            result = payload.get("result")
            message_id = result.get("message_id") if isinstance(result, dict) else None
            return TelegramChunkResult(
                message_id=message_id if isinstance(message_id, int) else None
            )
        raise TelegramDeliveryError("Telegram sendMessage retry limit exceeded")

    async def prepare_text(self, payload: dict[str, object]) -> str:
        text = str(payload["text"])
        if payload.get("use_llm") is True:
            context = payload.get("analysis_context")
            if isinstance(context, dict):
                generator = self.narrative_generator or InvestmentNarrativeGenerator()
                text = await generator.generate(context, text)
        return text

    def build_chunks(self, text: str, max_chars: int) -> list[str]:
        return split_telegram_text(text, max_chars)

    async def send_chunk(self, text: str) -> TelegramChunkResult:
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            return await self._send_chunk(client, text)

    async def send(self, payload: dict[str, object]) -> str:
        if self.settings.notification_dry_run:
            return "dry_run"
        text = await self.prepare_text(payload)
        chunks = self.build_chunks(text, self.settings.telegram_message_max_chars)
        for index, chunk in enumerate(chunks, start=1):
            rendered = f"[{index}/{len(chunks)}]\n{chunk}" if len(chunks) > 1 else chunk
            await self.send_chunk(rendered)
        return "sent"


def _notifier_for_channel(
    channel: str,
) -> TelegramNotifier:
    if channel == "telegram":
        return TelegramNotifier()
    raise RuntimeError(f"Unsupported notification channel: {channel}")


async def _telegram_delivery_plan(
    session: Session,
    delivery: NotificationDelivery,
    notifier: TelegramNotifier,
) -> tuple[dict[str, object], list[str], int]:
    # next_chunk_index is a zero-based cursor pointing to the next unsent chunk.
    payload = _delivery_payload(delivery.payload)
    source_sha256 = _telegram_source_sha256(payload)
    metadata = payload.get(TELEGRAM_DELIVERY_METADATA_KEY)
    rendered_text: str | None = None
    chunk_max_chars: int | None = None
    next_chunk_index = 0
    if isinstance(metadata, dict) and metadata.get("source_sha256") == source_sha256:
        stored_text = metadata.get("rendered_text")
        stored_max = metadata.get("chunk_max_chars")
        stored_next = metadata.get("next_chunk_index")
        if isinstance(stored_text, str) and isinstance(stored_max, int) and stored_max >= 100:
            rendered_text = stored_text
            chunk_max_chars = stored_max
            if isinstance(stored_next, int):
                next_chunk_index = max(0, stored_next)

    if rendered_text is None or chunk_max_chars is None:
        rendered_text = await notifier.prepare_text(payload)
        chunk_max_chars = notifier.settings.telegram_message_max_chars
        next_chunk_index = 0

    chunks = notifier.build_chunks(rendered_text, chunk_max_chars)
    content_sha256 = hashlib.sha256(rendered_text.encode("utf-8")).hexdigest()
    if (
        not isinstance(metadata, dict)
        or metadata.get("content_sha256") != content_sha256
        or metadata.get("chunk_count") != len(chunks)
    ):
        next_chunk_index = 0
    next_chunk_index = min(next_chunk_index, len(chunks))
    payload[TELEGRAM_DELIVERY_METADATA_KEY] = {
        "source_sha256": source_sha256,
        "content_sha256": content_sha256,
        "rendered_text": rendered_text,
        "chunk_max_chars": chunk_max_chars,
        "chunk_count": len(chunks),
        "next_chunk_index": next_chunk_index,
    }
    delivery.payload = json.dumps(payload, ensure_ascii=False)
    session.add(delivery)
    session.commit()
    return payload, chunks, next_chunk_index


def _render_telegram_chunk(chunk: str, index: int, chunk_count: int) -> str:
    return f"[{index + 1}/{chunk_count}]\n{chunk}" if chunk_count > 1 else chunk


async def dispatch_pending_notifications(
    session: Session,
    notifier: TelegramNotifier | None = None,
    delivery_ids: set[int] | None = None,
) -> None:
    channel = _notification_channel()
    query = select(NotificationDelivery).where(
        NotificationDelivery.status == "pending",
        NotificationDelivery.channel == channel,
    )
    if delivery_ids is not None:
        if not delivery_ids:
            return
        query = query.where(NotificationDelivery.id.in_(delivery_ids))
    if notifier is None:
        notifier = _notifier_for_channel(channel)
    deliveries = session.exec(
        query.order_by(
            case(
                (
                    NotificationDelivery.ticker.in_(
                        ("__DAILY_DIGEST__", "__DAILY_DIGEST_KR__")
                    ),
                    0,
                ),
                else_=1,
            ),
            NotificationDelivery.created_at,
        )
    ).all()
    for delivery in deliveries:
        initial_payload = _delivery_payload(delivery.payload)
        if _ai_assisted_pilot_holds(initial_payload):
            continue
        dispatch_budget = 1 + len(_deferred_stock_notifications(initial_payload))
        for _ in range(dispatch_budget):
            delivery.attempt_count += 1
            try:
                payload = _delivery_payload(delivery.payload)
                if (
                    isinstance(notifier, TelegramNotifier)
                    and not notifier.settings.notification_dry_run
                ):
                    payload, chunks, next_chunk_index = await _telegram_delivery_plan(
                        session,
                        delivery,
                        notifier,
                    )
                    for index in range(next_chunk_index, len(chunks)):
                        await notifier.send_chunk(
                            _render_telegram_chunk(chunks[index], index, len(chunks))
                        )
                        metadata = payload[TELEGRAM_DELIVERY_METADATA_KEY]
                        if not isinstance(metadata, dict):
                            raise ValueError("Telegram delivery metadata is invalid")
                        metadata["next_chunk_index"] = index + 1
                        delivery.payload = json.dumps(payload, ensure_ascii=False)
                        session.add(delivery)
                        session.commit()
                    result = "sent"
                else:
                    result = await notifier.send(payload)
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                delivery.last_error = f"{type(exc).__name__}: {exc}"
                delivery.status = "pending"
                session.commit()
                break
            delivery.status = result
            delivery.last_error = None
            if result != "sent":
                session.commit()
                break
            delivery.sent_at = datetime.now(timezone.utc)
            if _promote_deferred_stock_notification(delivery):
                session.add(delivery)
                session.commit()
                continue
            session.commit()
            break
