import json
from types import SimpleNamespace
from urllib.parse import parse_qs

import httpx
import pytest

from app.services.notification_service import (
    KakaoSelfNotifier,
    TelegramNotifier,
    _macro_report,
    _message_for_assessment,
)


def test_assessment_notification_uses_investment_rationale_label() -> None:
    assessment = SimpleNamespace(
        ticker="000660",
        assessment_date="2026-08-07",
        thesis_version=1,
        status="strengthened",
        score=40,
        confidence=0.8,
        summary="새 근거가 현재 투자 논리를 강화했습니다.",
        new_buyer_view="가격을 확인합니다.",
        holder_view="근거를 확인하며 보유 논리를 유지합니다.",
        price_view="가격 범위 중간입니다.",
        risk_level="watch",
        evidence="[]",
        price_context="{}",
        valuation_context=json.dumps(
            {
                "impact": "compression",
                "summary": "새 근거가 멀티플 압축 조건과 연결됩니다.",
            },
            ensure_ascii=False,
        ),
        thesis_snapshot='{"base_thesis":"HBM 수요가 이익을 지지합니다."}',
    )

    message = _message_for_assessment(assessment)

    assert message.startswith("🏢 000660(000660)")
    assert "🎯 결론" in message
    assert "💰 가격 판단" in message
    assert "📐 시장 기대와 Valuation" in message
    assert "Thesis" not in message


def test_macro_report_explains_axes_confidence_and_friendly_series_names() -> None:
    briefing = SimpleNamespace(
        briefing_date="2030-01-02",
        as_of="2030-01-02T08:00:00+09:00",
        headline="mixed",
        market_summary=json.dumps(
            {
                "items": ["S&P +0.4%", "Nasdaq +0.8%", "VIX -4.2%"],
                "observations": [
                    {"series_code": "SPY", "change_pct": 0.4},
                    {"series_code": "QQQ", "change_pct": 0.8},
                    {"series_code": "SOXX", "change_pct": 0.7},
                    {"series_code": "VIXCLS", "change_pct": -4.2},
                    {"series_code": "DFII10", "change_value": 0.02},
                ],
            },
            ensure_ascii=False,
        ),
        regime_summary=json.dumps(
            {
                "label": "mixed",
                "summary": "성장 +0, 물가 +0, 유동성 +0, 금융여건 +0, 위험선호 +1, 이익 +0",
                "confidence": 0.9,
            },
            ensure_ascii=False,
        ),
        macro_theses=json.dumps(
            [
                {
                    "thesis_key": "us_soft_landing_disinflation",
                    "title": "미국 연착륙과 점진적 디스인플레이션",
                    "status": "strengthening",
                    "confidence": 0.85,
                }
            ],
            ensure_ascii=False,
        ),
        ticker_impacts="[]",
        today_calendar="[]",
        data_quality=json.dumps(
            [
                {
                    "series_code": "DTWEXBGS",
                    "quality_status": "stale",
                    "observed_at": "2029-12-20",
                }
            ],
            ensure_ascii=False,
        ),
    )

    report, _context = _macro_report(briefing)

    assert "6축 점수" not in report
    assert "위험선호 +1" not in report
    assert "🧭 현재 시장 상황" in report
    assert "• 위험선호:" in report
    assert "성장 급락과 물가 재가속" in report
    assert "미 달러지수(광의)(DTWEXBGS)" in report
    assert "당일 방향 판단에는 사용하지 않습니다" in report


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
        assert request.url.path == "/v2/api/talk/memo/send"
        form = parse_qs(request.content.decode())
        assert form["template_id"] == ["12345"]
        template_args = json.loads(form["template_args"][0])
        assert template_args == {
            "TITLE": "[000660] 투자 논리 강화",
            "BODY": "새 근거가 확인됐습니다.",
        }
        return httpx.Response(200, json={"result_code": 0})

    notifier = KakaoSelfNotifier(transport=httpx.MockTransport(handler))
    notifier.settings = notifier.settings.model_copy(
        update={
            "data_dir": str(tmp_path),
            "notification_dry_run": False,
            "kakao_rest_api_key": "rest-key",
            "kakao_client_secret": "client-secret",
            "kakao_refresh_token": "refresh",
            "kakao_template_id": "12345",
        }
    )

    result = await notifier.send({"text": "[000660] 투자 논리 강화\n새 근거가 확인됐습니다."})

    assert result == "sent"
    assert len(requests) == 2
    token_payload = json.loads((tmp_path / "kakao_tokens.json").read_text(encoding="utf-8"))
    assert token_payload["refresh_token"] == "renewed-refresh"


@pytest.mark.anyio
async def test_kakao_notifier_sends_long_report_as_text_chunks(tmp_path) -> None:
    sent_chunks: list[str] = []

    class StubNarrativeGenerator:
        async def generate(self, context: dict[str, object], fallback: str) -> str:
            assert context == {"analysis_type": "macro"}
            assert fallback == "기본 분석"
            return "🌍 시장환경 점검\n\n" + "• 분석 근거를 확인합니다. " * 30

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "kauth.kakao.com":
            return httpx.Response(200, json={"access_token": "access"})
        assert request.url.path == "/v2/api/talk/memo/default/send"
        form = parse_qs(request.content.decode())
        template = json.loads(form["template_object"][0])
        assert template["object_type"] == "text"
        assert template["button_title"] == "상태 확인"
        sent_chunks.append(template["text"])
        return httpx.Response(200, json={"result_code": 0})

    notifier = KakaoSelfNotifier(
        transport=httpx.MockTransport(handler),
        narrative_generator=StubNarrativeGenerator(),
    )
    notifier.settings = notifier.settings.model_copy(
        update={
            "data_dir": str(tmp_path),
            "notification_dry_run": False,
            "kakao_rest_api_key": "rest-key",
            "kakao_refresh_token": "refresh",
            "kakao_template_id": "12345",
        }
    )

    result = await notifier.send(
        {
            "text": "기본 분석",
            "presentation": "long_text",
            "use_llm": True,
            "analysis_context": {"analysis_type": "macro"},
        }
    )

    assert result == "sent"
    assert len(sent_chunks) >= 2
    assert all(len(chunk) <= 200 for chunk in sent_chunks)


@pytest.mark.anyio
async def test_telegram_notifier_sends_generated_report_as_section_chunks() -> None:
    sent_chunks: list[str] = []

    class StubNarrativeGenerator:
        async def generate(self, context: dict[str, object], fallback: str) -> str:
            assert context == {"analysis_type": "macro"}
            assert fallback == "기본 분석"
            return "🌍 시장환경 점검\n\n" + "• 시장 변화와 투자 의미를 연결합니다. " * 25

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.telegram.org"
        assert request.url.path.endswith("/sendMessage")
        payload = json.loads(request.content)
        assert payload["chat_id"] == "135988"
        assert payload["disable_web_page_preview"] is True
        sent_chunks.append(payload["text"])
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    notifier = TelegramNotifier(
        transport=httpx.MockTransport(handler),
        narrative_generator=StubNarrativeGenerator(),
    )
    notifier.settings = notifier.settings.model_copy(
        update={
            "notification_dry_run": False,
            "telegram_bot_token": "bot-token",
            "telegram_chat_id": "135988",
            "telegram_message_max_chars": 300,
            "telegram_retry_base_seconds": 0,
        }
    )

    result = await notifier.send(
        {
            "text": "기본 분석",
            "presentation": "long_text",
            "use_llm": True,
            "analysis_context": {"analysis_type": "macro"},
        }
    )

    assert result == "sent"
    assert len(sent_chunks) >= 2
    assert all(len(chunk) <= 310 for chunk in sent_chunks)
    assert sent_chunks[0].startswith("[1/")


@pytest.mark.anyio
async def test_telegram_notifier_retries_temporary_server_error() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"ok": False, "description": "temporary"})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 2}})

    notifier = TelegramNotifier(transport=httpx.MockTransport(handler))
    notifier.settings = notifier.settings.model_copy(
        update={
            "notification_dry_run": False,
            "telegram_bot_token": "bot-token",
            "telegram_chat_id": "135988",
            "telegram_retry_attempts": 2,
            "telegram_retry_base_seconds": 0,
        }
    )

    assert await notifier.send({"text": "전송 테스트"}) == "sent"
    assert calls == 2
