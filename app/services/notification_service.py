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
    payload = json.dumps(
        {
            "text": briefing.kakao_text,
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
            template = {
                "object_type": "text",
                "text": str(payload["text"]),
                "link": {
                    "web_url": self.settings.kakao_web_url,
                    "mobile_web_url": self.settings.kakao_web_url,
                },
            }
            response = await client.post(
                "https://kapi.kakao.com/v2/api/talk/memo/default/send",
                headers={"Authorization": f"Bearer {access_token}"},
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
