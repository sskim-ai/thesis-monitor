from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import app.services.free_analyst_production_integration_service as integration
from app.services.free_analyst_production_integration_service import (
    CommonAIAnalysisMode,
    build_production_candidate,
    candidate_provenance,
    fail_closed_canary_selection,
    free_analyst_adaptive_canary_armed,
    free_analyst_adaptive_kill_switch_open,
    restrict_canary_selection,
    select_limited_canary,
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

⚠️ 데이터 주의
• 지연 자료를 현재 신호로 승격하지 않습니다.
"""


def _settings(*, enabled: bool, mode: str, pilot: bool) -> SimpleNamespace:
    return SimpleNamespace(
        free_analyst_adaptive_enabled=enabled,
        free_analyst_adaptive_mode=mode,
        ai_review_pilot_enabled=pilot,
    )


def _candidate(key: str, *, market: bool = False):
    return build_production_candidate(
        MARKET_MESSAGE if market else STOCK_MESSAGE,
        deterministic_text=f"deterministic:{key}",
        message_key=key,
        market="us",
        is_market_digest=market,
    )


def test_control_plane_requires_kill_switch_mode_and_authoritative_pilot(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        integration,
        "get_settings",
        lambda: _settings(enabled=False, mode="current", pilot=False),
    )
    assert integration.configured_analysis_mode() == CommonAIAnalysisMode.CURRENT
    assert free_analyst_adaptive_kill_switch_open() is False
    assert free_analyst_adaptive_canary_armed() is False

    monkeypatch.setattr(
        integration,
        "get_settings",
        lambda: _settings(
            enabled=True,
            mode="free_analyst_adaptive_canary",
            pilot=False,
        ),
    )
    assert free_analyst_adaptive_kill_switch_open() is True
    assert free_analyst_adaptive_canary_armed() is False

    monkeypatch.setattr(
        integration,
        "get_settings",
        lambda: _settings(
            enabled=True,
            mode="free_analyst_adaptive_canary",
            pilot=True,
        ),
    )
    assert free_analyst_adaptive_canary_armed() is True


def test_full_mode_is_never_mistaken_for_limited_canary(monkeypatch) -> None:
    monkeypatch.setattr(
        integration,
        "get_settings",
        lambda: _settings(
            enabled=True,
            mode="free_analyst_adaptive",
            pilot=True,
        ),
    )

    assert free_analyst_adaptive_kill_switch_open() is True
    assert free_analyst_adaptive_canary_armed() is False


def test_kr_and_us_use_the_same_production_candidate_contract() -> None:
    us = build_production_candidate(
        STOCK_MESSAGE,
        deterministic_text="US fallback",
        message_key="stock:US",
        market="us",
    )
    kr = build_production_candidate(
        STOCK_MESSAGE,
        deterministic_text="KR fallback",
        message_key="stock:KR",
        market="kr",
    )

    assert us.contract == kr.contract == "common-ai-core-v1"
    assert us.eligible is True
    assert kr.eligible is True
    assert us.hard_validation == kr.hard_validation == "PASS"


def test_production_candidate_preserves_explicit_packet_owner() -> None:
    candidate = build_production_candidate(
        STOCK_MESSAGE,
        deterministic_text="fallback",
        message_key="stock:MEM",
        market="us",
        packet_owner="2026-08-25-us-run-37",
    )

    assert candidate.result is not None
    assert candidate.result.analysis.semantic_owner.packet_owner == "2026-08-25-us-run-37"


def test_invalid_candidate_fails_closed_to_its_deterministic_message() -> None:
    candidate = build_production_candidate(
        STOCK_MESSAGE,
        deterministic_text="safe deterministic fallback",
        message_key="stock:invalid",
        market="unsupported",
    )

    assert candidate.eligible is False
    assert candidate.hard_validation == "FAIL"
    assert candidate.candidate_text == "safe deterministic fallback"


def test_limited_canary_selects_at_most_one_market_and_two_stocks() -> None:
    candidates = [_candidate("market:packet", market=True)] + [
        _candidate(f"stock:{index}") for index in range(6)
    ]
    selection = select_limited_canary(candidates)

    assert selection.market_selected <= 1
    assert selection.stock_selected <= 2
    assert selection.total_selected <= 3
    assert len(selection.selected_keys) == len(set(selection.selected_keys))


def test_runtime_restriction_falls_back_only_rejected_canary_message() -> None:
    candidates = [_candidate("market:packet", market=True)] + [
        _candidate(f"stock:{index}") for index in range(3)
    ]
    selection = select_limited_canary(candidates)
    permitted = selection.selected_keys[:-1]
    restricted = restrict_canary_selection(selection, permitted)

    assert restricted.total_selected == selection.total_selected - 1
    rejected_key = selection.selected_keys[-1]
    rejected = restricted.row_for(rejected_key)
    assert rejected.canary_selected is False
    assert rejected.final_simulated_delivery_mode == "deterministic_fallback"
    assert set(permitted) == set(restricted.selected_keys)


def test_set_level_canary_failure_preserves_current_validated_ai() -> None:
    candidates = [_candidate("market:packet", market=True), _candidate("stock:AAA")]
    selection = fail_closed_canary_selection(select_limited_canary(candidates))

    assert selection.total_selected == 0
    assert all(
        row.final_simulated_delivery_mode
        == (
            "current_ai_existing"
            if row.canary_candidate
            else "deterministic_fallback"
        )
        for row in selection.rows
    )


def test_candidate_provenance_contains_required_audit_fields() -> None:
    candidate = _candidate("stock:provenance")
    selection = select_limited_canary([candidate])
    provenance = candidate_provenance(candidate, selection)

    assert provenance["analysis_mode"] == "free_analyst_adaptive_canary"
    assert provenance["free_analyst_generated"] is True
    assert provenance["free_analyst_validation"] == "PASS"
    assert provenance["hard_validation"] == "PASS"
    assert provenance["semantic_ownership_validation"] == "PASS"
    assert not any(provenance["semantic_ownership_mismatches"].values())
    assert provenance["canary_selected"] is True


def test_selector_source_has_no_ticker_hard_code() -> None:
    source = inspect.getsource(select_limited_canary)

    assert "ticker" not in source.casefold()
    assert all(value not in source for value in ("000660", "GOOGL", "MU", "WULF"))


def test_production_dependency_graph_excludes_research_and_web_paths() -> None:
    paths = (
        "free_analyst_message_service.py",
        "evidence_locked_free_analyst_service.py",
        "free_analyst_natural_packet_adapter_service.py",
        "adaptive_renderer_selector_service.py",
        "free_analyst_production_integration_service.py",
    )
    source = "\n".join((ROOT / "app/services" / path).read_text(encoding="utf-8") for path in paths)

    assert "open_research" not in source
    assert "event_attribution" not in source
    assert "web__run" not in source
    assert "requests." not in source
