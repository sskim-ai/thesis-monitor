from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.services.adaptive_renderer_selector_shadow_service import (
    run_adaptive_renderer_shadow,
)
from app.services.free_analyst_natural_packet_adapter_shadow_service import (
    CONTRACT_VERSION,
    normalize_us_natural_packet,
    validate_natural_packet_adapter_result,
)


ROOT = Path(__file__).resolve().parents[1]

STOCK_MESSAGE = """🏢 Example Memory(MEM)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

구조적 위험: 보통

시장 기대: 매우 높음

🎯 핵심
메모리 수익성과 고객 실행이 핵심입니다.

📈 사업·실적
재고 증가율은 매출원가 증가율보다 15.7%p 밑돌았습니다. 사이클 방향은 확정하지 않습니다.

👁 핵심 감시
• ASP 둔화

💰 가격
현재 구조는 추가 확인 대기입니다.

📐 Valuation
사이클 정상화 이익을 확인합니다.

📌 다음 확인
• HBM 출하와 ASP를 확인합니다.
"""

MARKET_MESSAGE = """🌎 미국 종목 점검 · 2026-08-25
현재 환경: 스태그플레이션 위험

🎯 오늘 한 줄
기업별 실적과 현금흐름 근거를 우선 확인합니다.

📈 중요한 변화
• 반도체 상대 흐름이 약했습니다.

📅 오늘/근접 일정
향후 7일:
• NVDA quarterly earnings · D-1

⚠️ 데이터 주의
• 지연 자료를 현재 신호로 승격하지 않습니다.
"""


def _content_lines(value: str) -> list[str]:
    headings = {
        "🎯 핵심",
        "🎯 핵심 판단",
        "📅 오늘/근접 일정",
        "📌 다음 확인",
    }
    return [line for line in value.splitlines() if line.strip() not in headings]


def test_stock_natural_packet_normalizes_to_common_free_analyst_contract() -> None:
    result = normalize_us_natural_packet(STOCK_MESSAGE, benchmark_id="stock")

    assert result.contract == CONTRACT_VERSION
    assert result.status == "PASS"
    assert "🎯 핵심 판단" in result.normalized_text
    assert "🎯 핵심\n" not in result.normalized_text
    assert _content_lines(result.original_text) == _content_lines(result.normalized_text)
    assert validate_natural_packet_adapter_result(result) == ()
    assert any(row.common_ref == "evidence:core:01" for row in result.evidence_ref_map)


def test_market_schedule_is_preserved_as_next_check() -> None:
    result = normalize_us_natural_packet(MARKET_MESSAGE, benchmark_id="market")

    assert result.status == "PASS"
    assert "📌 다음 확인\n향후 7일:" in result.normalized_text
    assert any(
        row.common_ref == "evidence:next_check:01"
        for row in result.evidence_ref_map
    )
    assert "지연 자료를 현재 신호로 승격하지 않습니다." in result.normalized_text


@pytest.mark.parametrize("index", range(14))
def test_fourteen_message_fixture_shape_validates(index: int) -> None:
    message = MARKET_MESSAGE if index == 0 else STOCK_MESSAGE.replace(
        "(MEM)", f"(T{index:02d})"
    )

    adapter = normalize_us_natural_packet(
        message,
        benchmark_id=f"fixture-{index:02d}",
    )
    result = run_adaptive_renderer_shadow(
        adapter.normalized_text,
        benchmark_id=f"fixture-{index:02d}",
        deterministic_reference=adapter.original_text,
    )

    assert adapter.status == "PASS"
    assert result.status == "PASS"
    assert result.fallback_reason is None
    assert result.safety["material_information_loss"] == 0


def test_evidence_ref_normalization_rejects_dangling_map() -> None:
    result = normalize_us_natural_packet(STOCK_MESSAGE, benchmark_id="dangling")
    damaged = replace(result, evidence_ref_map=result.evidence_ref_map[:-1])

    assert "evidence_ref_map_incomplete_or_mismatched" in (
        validate_natural_packet_adapter_result(damaged)
    )


def test_adapter_does_not_add_arithmetic_or_external_knowledge() -> None:
    original = STOCK_MESSAGE.replace(
        "사이클 방향은 확정하지 않습니다.",
        "두 원시 수치의 차이는 10%라고 계산됩니다. NVIDIA는 외부 예시입니다.",
    )
    result = normalize_us_natural_packet(original, benchmark_id="preserve-only")

    assert _content_lines(result.original_text) == _content_lines(result.normalized_text)
    assert result.normalized_text.count("10%") == 1
    assert result.normalized_text.count("NVIDIA") == 1


def test_shadow_adapter_has_no_production_import_wiring() -> None:
    target = "free_analyst_natural_packet_adapter_shadow_service"
    importers = []
    for path in (ROOT / "app").rglob("*.py"):
        if path.name == f"{target}.py":
            continue
        if target in path.read_text(encoding="utf-8"):
            importers.append(path)

    assert importers == []
