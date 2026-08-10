import json
import os
from datetime import datetime, timezone
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
    "strengthening": "강화",
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


def _json_value(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _json_list_value(value: str) -> list[object]:
    parsed = _json_value(value, [])
    return parsed if isinstance(parsed, list) else []


def _assessment_report(
    assessment: ThesisAssessment,
    company_name: str,
    thesis: InvestmentThesis | None,
) -> tuple[str, dict[str, object]]:
    labels = {
        "strengthened": "강화",
        "weakened": "약화",
        "mixed": "혼재",
        "invalidation_candidate": "무효화 후보",
        "invalidated": "무효화",
        "needs_review": "검토 필요",
    }
    label = labels.get(assessment.status, assessment.status)
    evidence = _json_list_value(assessment.evidence)
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
    evidence_items = evidence
    evidence_lines = [
        f"• {item.get('title', '제목 없음')} ({item.get('direction', '확인')})"
        for item in evidence_items[:3]
        if isinstance(item, dict)
    ]
    change_text = "\n".join(evidence_lines) or "• 투자 판단을 바꿀 새 근거가 확인되지 않았습니다."
    core_thesis = thesis.core_thesis if thesis else str(
        thesis_snapshot.get("base_thesis", "저장된 핵심 투자 논리가 없습니다.")
    )
    conditions = [
        *(str(item) for item in strengthen_signals[:1]),
        *(str(item) for item in weaken_signals[:1]),
        *(str(item) for item in invalidation_signals[:1]),
    ]
    condition_text = " / ".join(conditions) or "추가 확인 조건이 등록되지 않았습니다."
    validation_text = " / ".join(str(item) for item in validation_metrics[:3])
    expectation_level = str(market_expectations.get("level", "unknown"))
    expectation_summary = str(
        market_expectations.get("summary", "현재 시장 기대 정보가 등록되지 않았습니다.")
    )
    valuation_method = str(
        valuation_framework.get("primary_method", "평가 방식이 등록되지 않았습니다.")
    )
    valuation_impact = str(
        valuation_context.get("summary", "Valuation 영향 판단 자료가 없습니다.")
    )
    fallback = (
        f"🏢 {company_name}({assessment.ticker})\n"
        f"⚠️ 투자 논리 {label} · 신뢰도 {assessment.confidence:.0%}\n\n"
        f"🎯 결론\n"
        f"• 논리: {core_thesis}\n"
        f"• 행동: 신규 관찰자는 {assessment.new_buyer_view} "
        f"보유자는 {assessment.holder_view}\n"
        f"• 논리 조건: {condition_text}\n\n"
        f"🧭 현재 국면\n"
        f"• {assessment.summary} 위험 수준은 {assessment.risk_level}입니다.\n\n"
        f"🔄 이번 변화\n{change_text}\n\n"
        f"💰 가격 판단\n• {assessment.price_view}\n\n"
        f"📐 시장 기대와 Valuation\n"
        f"• 기대 수준: {expectation_level} · {expectation_summary}\n"
        f"• 평가 방식: {valuation_method}\n"
        f"• 멀티플 영향: {valuation_impact}\n\n"
        f"📌 확인할 것\n• 강화·약화·무효화 조건과 다음 공시·실적 근거를 계속 확인합니다."
    )
    if validation_text:
        fallback = fallback.replace(
            "📌 확인할 것\n• ",
            f"📌 확인할 것\n• 검증 지표: {validation_text}\n• ",
        )
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
            "score": assessment.score,
            "confidence": assessment.confidence,
            "summary": assessment.summary,
            "new_buyer_view": assessment.new_buyer_view,
            "holder_view": assessment.holder_view,
            "price_view": assessment.price_view,
            "risk_level": assessment.risk_level,
            "evidence": evidence_items,
            "price_context": price_context,
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
    text, analysis_context = _assessment_report(assessment, company_name, thesis)
    payload = json.dumps(
        {
            "text": text,
            "ticker": assessment.ticker,
            "assessment_date": str(assessment.assessment_date),
            "status": assessment.status,
            "presentation": "long_text",
            "analysis_context": analysis_context,
        },
        ensure_ascii=False,
    )
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == assessment.ticker,
            NotificationDelivery.assessment_date == assessment.assessment_date,
            NotificationDelivery.channel == "kakao_self",
        )
    ).first()
    if delivery is None:
        session.add(
            NotificationDelivery(
                ticker=assessment.ticker,
                assessment_date=assessment.assessment_date,
                channel="kakao_self",
                status="pending",
                payload=payload,
            )
        )
    elif delivery.status != "sent":
        delivery.payload = payload
        delivery.status = "pending"


def queue_macro_notification(session: Session, briefing: MacroBriefing) -> None:
    text, analysis_context = _macro_report(briefing)
    payload = json.dumps(
        {
            "text": text,
            "briefing_date": str(briefing.briefing_date),
            "type": "macro_morning",
            "presentation": "long_text",
            "analysis_context": analysis_context,
        },
        ensure_ascii=False,
    )
    delivery = session.exec(
        select(NotificationDelivery).where(
            NotificationDelivery.ticker == "__MACRO__",
            NotificationDelivery.assessment_date == briefing.briefing_date,
            NotificationDelivery.channel == "kakao_self",
        )
    ).first()
    if delivery is None:
        session.add(
            NotificationDelivery(
                ticker="__MACRO__",
                assessment_date=briefing.briefing_date,
                channel="kakao_self",
                status="pending",
                payload=payload,
            )
        )
    elif delivery.status != "sent":
        delivery.payload = payload
        delivery.status = "pending"


def _macro_report(briefing: MacroBriefing) -> tuple[str, dict[str, object]]:
    market = _json_value(briefing.market_summary, {})
    regime = _json_value(briefing.regime_summary, {})
    theses = _json_value(briefing.macro_theses, [])
    impacts = _json_value(briefing.ticker_impacts, [])
    calendar = _json_value(briefing.today_calendar, [])
    quality = _json_value(briefing.data_quality, [])

    market_items = market.get("items", []) if isinstance(market, dict) else []
    market_values = [str(item) for item in market_items[:8]]
    regime_label = str(regime.get("label", "mixed")) if isinstance(regime, dict) else "mixed"
    confidence = float(regime.get("confidence", 0)) if isinstance(regime, dict) else 0.0
    regime_summary = str(regime.get("summary", "판단 근거 부족")) if isinstance(regime, dict) else "판단 근거 부족"
    regime_display = REGIME_LABELS.get(regime_label, regime_label)
    interpretation = REGIME_INTERPRETATIONS.get(regime_label, "추가 확인이 필요합니다.")

    thesis_items = theses if isinstance(theses, list) else []
    ordered_theses = [item for item in thesis_items if isinstance(item, dict)]
    thesis_parts = []
    for item in ordered_theses[:5]:
        key = str(item.get("thesis_key", ""))
        status = str(item.get("status", "intact"))
        item_confidence = float(item.get("confidence", 0))
        thesis_parts.append(
            f"{MACRO_THESIS_LABELS.get(key, key)} {MACRO_STATUS_LABELS.get(status, status)}"
            f"({item_confidence:.0%})"
        )
    thesis_line = " · ".join(thesis_parts) or "주요 시장 가정 판단 보류"

    impact_items = [item for item in impacts if isinstance(item, dict)] if isinstance(impacts, list) else []
    impact_parts = [
        f"{item.get('ticker')} {IMPACT_LABELS.get(str(item.get('direction')), item.get('direction'))}"
        f" {item.get('magnitude', 0)}/5"
        for item in impact_items[:3]
    ]
    impact_text = ", ".join(impact_parts) or "변화 없음"
    calendar_items = calendar if isinstance(calendar, list) else []
    quality_items = quality if isinstance(quality, list) else []
    calendar_text = ", ".join(
        str(item.get("title", "일정")) for item in calendar_items[:3] if isinstance(item, dict)
    ) or "등록된 주요 일정 없음"
    quality_text = ", ".join(
        str(item.get("warning") or item.get("series_code") or "데이터 점검")
        for item in quality_items[:3]
        if isinstance(item, dict)
    ) or "특이사항 없음"
    fallback = (
        f"🌍 시장환경 점검 · {briefing.briefing_date}\n"
        f"⚠️ {regime_display} 국면 · 신뢰도 {confidence:.0%}\n\n"
        f"🎯 결론\n"
        f"• 시장: {interpretation}\n"
        f"• 행동: 방향을 단정하기보다 변화가 확인된 지표와 종목별 근거를 우선 점검합니다.\n\n"
        f"🧭 현재 국면\n"
        f"• {regime_summary}\n"
        f"• 주요 지표: {' · '.join(market_values) or '시장 데이터 없음'}\n\n"
        f"🔄 이번 변화\n"
        f"• 시장 가정: {thesis_line}\n\n"
        f"🏢 종목 영향\n"
        f"• {impact_text}\n\n"
        f"📌 오늘 확인\n"
        f"• {calendar_text}\n\n"
        f"⚠️ 데이터 주의\n"
        f"• {quality_text}"
    )
    context: dict[str, object] = {
        "analysis_type": "macro",
        "briefing_date": str(briefing.briefing_date),
        "as_of": str(briefing.as_of),
        "headline": briefing.headline,
        "market": market,
        "regime": regime,
        "macro_theses": thesis_items,
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
        self.narrative_generator = narrative_generator or InvestmentNarrativeGenerator()

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
            if payload.get("presentation") == "long_text":
                context = payload.get("analysis_context")
                if isinstance(context, dict):
                    text = await self.narrative_generator.generate(context, text)
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


async def dispatch_pending_notifications(
    session: Session,
    notifier: KakaoSelfNotifier | None = None,
) -> None:
    notifier = notifier or KakaoSelfNotifier()
    deliveries = session.exec(
        select(NotificationDelivery)
        .where(NotificationDelivery.status == "pending")
        .order_by(NotificationDelivery.created_at)
    ).all()
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
