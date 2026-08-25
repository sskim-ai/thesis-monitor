from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path

from app.services.adaptive_renderer_selector_service import (
    CONTRACT_VERSION,
    AdaptiveRenderer,
    InformationElement,
    render_adaptive_candidate,
    renderer_information_audit,
    run_adaptive_renderer,
    select_adaptive_renderer,
)
from app.services.evidence_locked_free_analyst_service import (
    RenderedFreeAnalyst,
    build_free_analyst_analysis,
)


ROOT = Path(__file__).resolve().parents[1]


INVENTORY_MESSAGE = """🤖 AI stock review

🏢 Company Memory(AAA)
투자 논리: 유지
시장 기대: 매우 높음

🎯 핵심 판단
HBM execution and memory profitability remain the key tests.

📈 사업·실적
메모리 재고 점검에서 재고 증가율은 매출원가 증가율보다 2.1%p 밑돌았습니다. ASP와 제품 믹스를 함께 확인해야 합니다.

💰 가격·포지셔닝
Current price is 100 with support at 90 and resistance at 120.

📊 수급
기간별 주체 방향이 엇갈려 중기 사업 근거로 승격하지 않습니다.

📌 다음 확인
HBM 출하와 수율을 확인합니다.

⚠️ 미확인
HBM 출하와 수율을 확인합니다.
"""


FCF_MESSAGE = """🤖 AI stock review

🏢 Cloud Platform(CCC)
투자 논리: 유지
시장 기대: 높음

🎯 핵심 판단
AI investment recovery remains the key operating test.

📈 사업·실적
PPE 투자 후 잉여현금흐름은 전년보다 줄었습니다. AI·Cloud 성장과 마진을 함께 확인해야 합니다.

💰 가격·포지셔닝
Price action does not prove operating execution.

📊 수급
현재 가격·거래 흐름은 사업 변화의 증거가 아닙니다.

📌 다음 확인
Cloud 성장과 마진의 투자 회수 연결을 확인합니다.

⚠️ 미확인
Cloud 성장과 마진의 투자 회수 연결을 확인합니다.
"""


MARKET_MESSAGE = """🤖 AI 한국시장 마감

🎯 현재 시장 한 줄
새로운 당일 거시 관측이 없어 직전 세션과 지연 공표 자료를 현재 신호로 승격하지 않습니다.

🧭 시장 구조
직전 완료 세션은 오늘의 신규 관측은 아닙니다.

⚠️ 데이터 주의
다음 공식 관측 전까지 오늘의 거시 방향은 확정하지 않습니다.
"""


def _analysis(message: str, benchmark_id: str):
    return build_free_analyst_analysis(message, benchmark_id=benchmark_id)


def test_selector_enum_and_contract_are_typed() -> None:
    assert CONTRACT_VERSION == "adaptive-renderer-selector-v1"
    assert {item.value for item in AdaptiveRenderer} == {
        "DIRECT_ANALYST",
        "CONCISE_HYBRID",
        "MINIMAL_VNEXT",
    }


def test_ambiguous_inventory_requires_direct() -> None:
    analysis = _analysis(INVENTORY_MESSAGE, "inventory")
    decision = select_adaptive_renderer(analysis, INVENTORY_MESSAGE)

    assert decision.selected_renderer == AdaptiveRenderer.DIRECT_ANALYST
    assert "material_alternative_interpretation" in decision.direct_required_reasons
    assert AdaptiveRenderer.CONCISE_HYBRID in decision.disallowed_renderers


def test_clear_fcf_linkage_uses_hybrid() -> None:
    analysis = _analysis(FCF_MESSAGE, "fcf")
    decision = select_adaptive_renderer(analysis, FCF_MESSAGE)

    assert decision.selected_renderer == AdaptiveRenderer.CONCISE_HYBRID
    assert decision.direct_required_reasons == ()
    assert "expectation_verification_threshold" in decision.minimal_forbidden_reasons


def test_no_new_macro_observation_uses_minimal() -> None:
    analysis = _analysis(MARKET_MESSAGE, "macro")
    decision = select_adaptive_renderer(analysis, MARKET_MESSAGE)

    assert decision.selected_renderer == AdaptiveRenderer.MINIMAL_VNEXT
    assert decision.minimal_forbidden_reasons == ()


def test_hybrid_information_audit_detects_material_alternative_loss() -> None:
    analysis = _analysis(INVENTORY_MESSAGE, "inventory-loss")
    audit = renderer_information_audit(INVENTORY_MESSAGE, analysis, AdaptiveRenderer.CONCISE_HYBRID)

    assert InformationElement.ALTERNATIVE_INTERPRETATION in audit.dropped_elements
    assert InformationElement.ALTERNATIVE_INTERPRETATION in audit.material_dropped_elements


def test_minimal_is_forbidden_when_novel_thesis_linkage_exists() -> None:
    analysis = _analysis(FCF_MESSAGE, "minimal-overuse")
    decision = select_adaptive_renderer(analysis, FCF_MESSAGE)
    audit = decision.audit_for(AdaptiveRenderer.MINIMAL_VNEXT)

    assert AdaptiveRenderer.MINIMAL_VNEXT in decision.disallowed_renderers
    assert InformationElement.THESIS_LINKAGE in audit.material_dropped_elements


def test_selected_renderer_never_drops_material_information() -> None:
    for benchmark_id, message in (
        ("inventory", INVENTORY_MESSAGE),
        ("fcf", FCF_MESSAGE),
        ("macro", MARKET_MESSAGE),
    ):
        decision = select_adaptive_renderer(_analysis(message, benchmark_id), message)
        assert decision.audit_for(decision.selected_renderer).material_dropped_elements == ()


def test_selector_is_deterministic() -> None:
    analysis = _analysis(INVENTORY_MESSAGE, "deterministic")
    first = select_adaptive_renderer(analysis, INVENTORY_MESSAGE)
    second = select_adaptive_renderer(analysis, INVENTORY_MESSAGE)

    assert first == second


def test_selector_has_no_ticker_or_industry_hard_code() -> None:
    source = inspect.getsource(select_adaptive_renderer)

    assert "ticker" not in source.casefold()
    assert "industry" not in source.casefold()
    assert all(value not in source for value in ("000660", "GOOGL", "MU", "WULF"))


def test_end_to_end_production_contract_exercises_all_three_renderers() -> None:
    results = [
        run_adaptive_renderer(message, benchmark_id=benchmark_id)
        for benchmark_id, message in (
            ("inventory", INVENTORY_MESSAGE),
            ("fcf", FCF_MESSAGE),
            ("macro", MARKET_MESSAGE),
        )
    ]

    assert {result.decision.selected_renderer for result in results if result.decision} == set(
        AdaptiveRenderer
    )
    assert all(result.status == "PASS" for result in results)
    assert all(result.safety["status"] == "PASS" for result in results)
    assert all(result.final_delivery_mode == "ADAPTIVE_VALIDATED_CANDIDATE" for result in results)


def test_selected_renderer_validator_parity() -> None:
    for benchmark_id, message in (
        ("inventory", INVENTORY_MESSAGE),
        ("fcf", FCF_MESSAGE),
        ("macro", MARKET_MESSAGE),
    ):
        result = run_adaptive_renderer(message, benchmark_id=benchmark_id)
        assert result.safety["fact_mismatch"] == 0
        assert result.safety["unsupported_numeric_claims"] == []
        assert result.safety["unsupported_causality"] == 0
        assert result.safety["temporal_violations"] == 0
        assert result.safety["trade_ar_leak"] == 0
        assert result.safety["hidden_arithmetic"] == 0
        assert result.safety["external_knowledge"] == 0


def test_invalid_free_analyst_object_falls_back_without_free_message() -> None:
    analysis = _analysis(INVENTORY_MESSAGE, "invalid-analysis")
    invalid_item = replace(analysis.top_findings[0], evidence_refs=("missing",))
    invalid = replace(analysis, top_findings=(invalid_item,))
    result = run_adaptive_renderer(
        INVENTORY_MESSAGE,
        benchmark_id="invalid-analysis",
        analysis_override=invalid,
    )

    assert result.status == "FALLBACK"
    assert result.decision is None
    assert result.rendered is None
    assert result.fallback_reason == "free_analyst_validation_failed"
    assert result.final_delivery_mode == "DETERMINISTIC_FALLBACK"
    assert result.final_text == INVENTORY_MESSAGE


def test_selector_failure_uses_deterministic_fallback() -> None:
    def fail_selector(*_args):
        raise ValueError("negative control")

    result = run_adaptive_renderer(
        FCF_MESSAGE,
        benchmark_id="selector-failure",
        selector=fail_selector,
    )

    assert result.status == "FALLBACK"
    assert result.fallback_reason == "selector_failed"
    assert result.final_delivery_mode == "DETERMINISTIC_FALLBACK"
    assert result.final_text == FCF_MESSAGE


def test_selected_renderer_failure_uses_safe_fallback() -> None:
    def unsafe_renderer(_current, _analysis_value, _renderer):
        return RenderedFreeAnalyst(
            renderer="UNSAFE_TEST",
            text="Unsupported FCF 999999999999 USD",
            sentence_supports=(),
        )

    result = run_adaptive_renderer(
        FCF_MESSAGE,
        benchmark_id="renderer-failure",
        renderer=unsafe_renderer,
    )

    assert result.status == "FALLBACK"
    assert result.fallback_reason == "selected_renderer_validation_failed"
    assert result.final_delivery_mode == "DETERMINISTIC_FALLBACK"
    assert result.final_text == FCF_MESSAGE


def test_high_expectation_with_two_sided_interpretation_remains_direct() -> None:
    analysis = _analysis(INVENTORY_MESSAGE, "high-expectation-two-sided")
    decision = select_adaptive_renderer(analysis, INVENTORY_MESSAGE)

    assert analysis.expectation_valuation_interaction
    assert analysis.alternative_interpretations
    assert decision.selected_renderer == AdaptiveRenderer.DIRECT_ANALYST


def test_clear_single_implication_is_not_overlong_direct_default() -> None:
    analysis = _analysis(FCF_MESSAGE, "single-implication")
    decision = select_adaptive_renderer(analysis, FCF_MESSAGE)

    assert len(analysis.thesis_implications) == 1
    assert not analysis.alternative_interpretations
    assert decision.selected_renderer == AdaptiveRenderer.CONCISE_HYBRID


def test_minimal_renderer_reuses_existing_safe_vnext() -> None:
    analysis = _analysis(MARKET_MESSAGE, "minimal-equivalence")
    rendered = render_adaptive_candidate(MARKET_MESSAGE, analysis, AdaptiveRenderer.MINIMAL_VNEXT)
    result = run_adaptive_renderer(MARKET_MESSAGE, benchmark_id="minimal-equivalence")

    assert rendered.text == result.final_text


def test_production_selector_has_no_open_research_dependency() -> None:
    source = (ROOT / "app/services/adaptive_renderer_selector_service.py").read_text(
        encoding="utf-8"
    )

    assert "open_research" not in source
    assert "event_attribution" not in source
