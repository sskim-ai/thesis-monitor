import json
import logging
from collections.abc import Iterable

import httpx

from app.config import get_settings


KAKAO_TEXT_MAX_CHARS = 190
TELEGRAM_TEXT_MAX_CHARS = 3500

logger = logging.getLogger(__name__)


REPORT_INSTRUCTIONS = """당신은 한국어 투자 모니터링 분석가다.
입력 JSON에 포함된 사실만 사용해 Telegram에서 바로 읽을 수 있는 분석문을 작성한다.

성공 기준:
- 첫 문장에서 현재 판단과 불확실성을 분명히 밝힌다.
- 숫자 나열보다 투자 논리, 변화, 행동 기준의 연결을 설명한다.
- 확인된 사실과 해석을 구분하고, 자료가 없으면 없다고 쓴다.
- 매수나 매도를 단정하지 않고 신규 관찰자와 보유자의 확인 행동을 제시한다.
- 입력에 없는 기업 사실, 날짜, 수치, 사건, 전망은 만들지 않는다.
- 한국어로 작성하고 아래 형식을 지킨다.
- 최종 분석문만 출력하며 코드 블록, 링크, 면책 문구는 넣지 않는다.

거시 분석 형식:
🌍 시장환경 점검 · 날짜
⚠️ 한 줄 판단

🎯 결론
• 시장: ...
• 행동: ...

📈 간밤 시장
• 주가지수·반도체·위험선호의 방향과 의미: ...

💵 금리·환율·원자재
• 명목금리·실질금리·달러·원화·유가·변동성의 변화와 전달 경로: ...

🧭 현재 국면
• 성장·물가·유동성·금융여건·위험선호·이익 모멘텀: ...

🔄 시장 가정 변화
• 연착륙·연준 경로·AI CAPEX·한중 수출·유가 공급충격: ...

🏢 종목 영향
• 영향이 있는 모니터링 종목과 이익·valuation 전달 경로: ...

📅 오늘 일정과 시나리오
• 주요 일정, 예상과 다른 결과가 나올 때 확인할 시장 반응: ...

⚠️ 데이터 주의
• ...

종목 분석 형식:
🏢 회사명(종목코드)
⚠️ 상태 · 신뢰도 또는 자료 확인 상태

🎯 결론
• 논리: ...
• 행동: ...
• 논리 조건: ...

🧭 현재 국면
• ...

🔄 이번 변화
• ...

💰 가격 판단
• ...

📐 시장 기대와 Valuation
• 현재 기대: ...
• 평가 방식: ...
• 멀티플 영향: ...

📌 확인할 것
• ...

종목 분석은 확인된 사실 → 현재 시장 기대 → 투자적 해석 → 투자 논리 변화 →
이익 추정치 영향과 valuation multiple 영향 순서로 연결한다. 기업의 질과 현재
가격의 매력도를 분리하고, 컨센서스나 추정 입력값이 없으면 적정가를 만들지 않는다.

거시 분석은 근거가 충분하면 1,500~2,500자, 부족하면 800~1,400자로 작성한다.
종목 분석은 근거가 충분하면 900~1,600자, 부족하면 500~900자로 작성한다.
단순 수치 나열 뒤에는 반드시 기대 대비 의미, 투자 논리 영향, valuation 영향을 설명한다.
"""


def _response_text(payload: dict[str, object]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    output = payload.get("output", [])
    if not isinstance(output, list):
        return ""
    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for content_item in content:
            if not isinstance(content_item, dict) or content_item.get("type") != "output_text":
                continue
            value = content_item.get("text")
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts).strip()


class InvestmentNarrativeGenerator:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def generate(self, context: dict[str, object], fallback: str) -> str:
        if not self.settings.openai_api_key:
            return fallback
        request = {
            "model": self.settings.openai_narrative_model,
            "reasoning": {"effort": "low"},
            "instructions": REPORT_INSTRUCTIONS,
            "input": json.dumps(context, ensure_ascii=False, default=str),
            "max_output_tokens": 3000,
            "text": {"verbosity": "medium"},
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.openai_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json=request,
                )
                response.raise_for_status()
                generated = _response_text(response.json())
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("OpenAI narrative generation failed; using local report: %s", exc)
            return fallback
        return generated or fallback


def _split_long_line(line: str, max_chars: int) -> list[str]:
    if len(line) <= max_chars:
        return [line]
    prefix = ""
    body = line
    if line.startswith("• "):
        prefix = "• "
        body = line[2:]
    chunks: list[str] = []
    while body:
        available = max_chars - len(prefix)
        if len(body) <= available:
            chunks.append(prefix + body)
            break
        split_at = body.rfind(" ", 0, available + 1)
        if split_at <= 0:
            split_at = available
        chunks.append(prefix + body[:split_at].rstrip())
        body = body[split_at:].lstrip()
    return chunks


def _report_blocks(text: str, max_chars: int) -> Iterable[str]:
    for section in (item.strip() for item in text.strip().split("\n\n")):
        if not section:
            continue
        if len(section) <= max_chars:
            yield section
            continue
        current = ""
        for raw_line in section.splitlines():
            for line in _split_long_line(raw_line.strip(), max_chars):
                candidate = f"{current}\n{line}" if current else line
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        yield current
                    current = line
        if current:
            yield current


def split_kakao_text(text: str, max_chars: int = KAKAO_TEXT_MAX_CHARS) -> list[str]:
    if max_chars < 20:
        raise ValueError("max_chars must be at least 20")
    chunks: list[str] = []
    current = ""
    for block in _report_blocks(text, max_chars):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = block
    if current:
        chunks.append(current)
    return chunks or ["분석할 수 있는 데이터가 없습니다."]


def split_telegram_text(
    text: str,
    max_chars: int = TELEGRAM_TEXT_MAX_CHARS,
) -> list[str]:
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    chunks: list[str] = []
    current = ""
    for block in _report_blocks(text, max_chars):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = block
    if current:
        chunks.append(current)
    return chunks or ["분석할 수 있는 데이터가 없습니다."]
