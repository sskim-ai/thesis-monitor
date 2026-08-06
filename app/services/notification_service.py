import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.macro import MacroBriefing
from app.models.thesis import NotificationDelivery, ThesisAssessment


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


def _message_for_assessment(assessment: ThesisAssessment) -> str:
    labels = {
        "strengthened": "강화",
        "weakened": "약화",
        "mixed": "혼재",
        "invalidation_candidate": "무효화 후보",
        "invalidated": "무효화",
        "needs_review": "검토 필요",
    }
    label = labels.get(assessment.status, assessment.status)
    message = (
        f"[{assessment.ticker}] 투자 논리 {label}\n"
        f"{assessment.summary}\n"
        f"위험 수준: {assessment.risk_level}"
    )
    return message[:200]


def queue_notification(session: Session, assessment: ThesisAssessment) -> None:
    if assessment.status not in MATERIAL_STATUSES:
        return
    payload = json.dumps(
        {
            "text": _message_for_assessment(assessment),
            "ticker": assessment.ticker,
            "assessment_date": str(assessment.assessment_date),
            "status": assessment.status,
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
    messages = _macro_notification_messages(briefing)
    payload = json.dumps(
        {
            "text": briefing.kakao_text,
            "messages": messages,
            "briefing_date": str(briefing.briefing_date),
            "type": "macro_morning",
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


def _json_value(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _macro_notification_messages(briefing: MacroBriefing) -> list[dict[str, str]]:
    market = _json_value(briefing.market_summary, {})
    regime = _json_value(briefing.regime_summary, {})
    theses = _json_value(briefing.macro_theses, [])
    impacts = _json_value(briefing.ticker_impacts, [])
    calendar = _json_value(briefing.today_calendar, [])
    quality = _json_value(briefing.data_quality, [])

    market_items = market.get("items", []) if isinstance(market, dict) else []
    market_values = [str(item) for item in market_items[:4]]
    market_lines = [
        " · ".join(market_values[:2]) or "시장 데이터 없음",
        " · ".join(market_values[2:4]) or "추가 시장 데이터 없음",
    ]
    regime_label = str(regime.get("label", "mixed")) if isinstance(regime, dict) else "mixed"
    confidence = float(regime.get("confidence", 0)) if isinstance(regime, dict) else 0.0
    regime_summary = str(regime.get("summary", "판단 근거 부족")) if isinstance(regime, dict) else "판단 근거 부족"
    compact_regime = (
        regime_summary.replace(", ", "·")
        .replace("금융여건", "금융")
        .replace("위험선호", "위험")
        .replace(" +", "+")
        .replace(" -", "-")
    )
    regime_display = REGIME_LABELS.get(regime_label, regime_label)
    interpretation = REGIME_INTERPRETATIONS.get(regime_label, "추가 확인이 필요합니다.")

    thesis_items = theses if isinstance(theses, list) else []
    ordered_theses = sorted(
        (item for item in thesis_items if isinstance(item, dict)),
        key=lambda item: item.get("status") == "intact",
    )
    thesis_parts = []
    for item in ordered_theses[:3]:
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
        for item in impact_items[:2]
    ]
    impact_text = ", ".join(impact_parts) or "변화 없음"
    calendar_count = len(calendar) if isinstance(calendar, list) else 0
    quality_count = len(quality) if isinstance(quality, list) else 0

    return [
        {
            "title": "[시장환경 점검] 주요 시장",
            "body": f"{market_lines[0]}\n{market_lines[1]}",
        },
        {
            "title": f"[시장환경 점검] 레짐 {regime_display} {confidence:.0%}",
            "body": f"{compact_regime}\n{interpretation}",
        },
        {
            "title": "[시장환경 점검] 투자 해석",
            "body": (
                f"시장 가정: {thesis_line}\n"
                f"종목: {impact_text} | 일정 {calendar_count}건 | 데이터 주의 {quality_count}건"
            ),
        },
    ]


class KakaoSelfNotifier:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

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
            headers = {"Authorization": f"Bearer {access_token}"}
            if self.settings.kakao_template_id:
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
                    "link": {},
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
