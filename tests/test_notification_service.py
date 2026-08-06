import json
from types import SimpleNamespace
from urllib.parse import parse_qs

import httpx
import pytest

from app.services.notification_service import KakaoSelfNotifier, _message_for_assessment


def test_assessment_notification_uses_investment_rationale_label() -> None:
    assessment = SimpleNamespace(
        ticker="000660",
        status="strengthened",
        summary="새 근거가 현재 투자 논리를 강화했습니다.",
        risk_level="watch",
    )

    message = _message_for_assessment(assessment)

    assert message.startswith("[000660] 투자 논리 강화")
    assert "Thesis" not in message


@pytest.mark.anyio
async def test_kakao_notifier_refreshes_token_and_sends(tmp_path) -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.host == "kauth.kakao.com":
            return httpx.Response(
                200,
                json={"access_token": "access", "refresh_token": "renewed-refresh"},
            )
        assert request.headers["Authorization"] == "Bearer access"
        form = parse_qs(request.content.decode())
        template = json.loads(form["template_object"][0])
        assert template["link"] == {}
        assert "button_title" not in template
        assert "buttons" not in template
        return httpx.Response(200, json={"result_code": 0})

    notifier = KakaoSelfNotifier(transport=httpx.MockTransport(handler))
    notifier.settings = notifier.settings.model_copy(
        update={
            "data_dir": str(tmp_path),
            "notification_dry_run": False,
            "kakao_rest_api_key": "rest-key",
            "kakao_client_secret": "client-secret",
            "kakao_refresh_token": "refresh",
        }
    )

    result = await notifier.send({"text": "Thesis strengthened"})

    assert result == "sent"
    assert len(requests) == 2
    token_payload = json.loads((tmp_path / "kakao_tokens.json").read_text(encoding="utf-8"))
    assert token_payload["refresh_token"] == "renewed-refresh"
