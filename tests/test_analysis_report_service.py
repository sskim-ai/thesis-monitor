import json

import httpx
import pytest

from app.services.analysis_report_service import (
    InvestmentNarrativeGenerator,
    split_kakao_text,
    split_telegram_text,
)


def test_split_kakao_text_preserves_sections_within_limit() -> None:
    report = (
        "🌍 시장환경 점검\n⚠️ 혼합 국면\n\n"
        "🎯 결론\n• 시장: " + "변화 확인 " * 35 + "\n\n"
        "📌 오늘 확인\n• 주요 일정을 확인합니다."
    )

    chunks = split_kakao_text(report)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 200 for chunk in chunks)
    assert "🌍 시장환경 점검" in chunks[0]
    assert "📌 오늘 확인" in chunks[-1]


def test_split_telegram_text_preserves_long_sections() -> None:
    report = (
        "🌍 시장환경 점검\n⚠️ 혼합 국면\n\n"
        "📈 간밤 시장\n• " + "시장 변화와 투자 의미를 연결합니다. " * 30 + "\n\n"
        "📅 오늘 일정과 시나리오\n• 주요 일정을 확인합니다."
    )

    chunks = split_telegram_text(report, max_chars=350)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 350 for chunk in chunks)
    assert "🌍 시장환경 점검" in chunks[0]
    assert "📅 오늘 일정과 시나리오" in chunks[-1]


@pytest.mark.anyio
async def test_narrative_generator_uses_responses_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.com/v1/responses"
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "gpt-5.6-sol"
        assert payload["reasoning"] == {"effort": "low"}
        assert payload["max_output_tokens"] == 3000
        assert "macro" in payload["input"]
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "🌍 생성된 투자 분석"}
                        ],
                    }
                ]
            },
        )

    generator = InvestmentNarrativeGenerator(transport=httpx.MockTransport(handler))
    generator.settings = generator.settings.model_copy(
        update={
            "openai_api_key": "test-key",
            "openai_narrative_model": "gpt-5.6-sol",
        }
    )

    result = await generator.generate({"analysis_type": "macro"}, "기본 분석")

    assert result == "🌍 생성된 투자 분석"


@pytest.mark.anyio
async def test_narrative_generator_falls_back_on_api_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "temporary"})

    generator = InvestmentNarrativeGenerator(transport=httpx.MockTransport(handler))
    generator.settings = generator.settings.model_copy(
        update={"openai_api_key": "test-key"}
    )

    result = await generator.generate({"analysis_type": "stock"}, "기본 분석")

    assert result == "기본 분석"
