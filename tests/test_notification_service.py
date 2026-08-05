import json

import httpx
import pytest

from app.services.notification_service import KakaoSelfNotifier


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
