from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.services.free_analyst_message_service import build_minimal_vnext_message
from app.services.evidence_locked_free_analyst_service import (
    CONTRACT_VERSION,
    Direction,
    SupportType,
    build_free_analyst_analysis,
    novel_synthesis_report,
    render_free_analyst_direct,
    render_free_analyst_vnext_hybrid,
    rendered_safety_report,
    validate_free_analyst_analysis,
)


ROOT = Path(__file__).resolve().parents[1]


INVENTORY_MESSAGE = """🤖 AI 보조 종목 점검 · KR Pilot 1/1

🏢 Example Memory(AAA)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 보통
시장 기대: 매우 높음

🎯 핵심 판단
HBM 실행과 메모리 수익성의 지속 여부가 핵심입니다.

📈 사업·실적
메모리 재고 점검에서 재고 증가율은 매출원가 증가율보다 2.1%p 밑돌았습니다. ASP와 제품 믹스를 함께 확인해야 합니다.

💰 가격·포지셔닝
가격 구조는 현재가 100원, 동적 지지구간 하단 90원, 동적 저항구간 하단 120원 기준입니다.
• 신규 관찰자: 실적 확인 뒤 진입을 검토합니다.
• 보유자: 사업과 가격 훼손을 분리합니다.

📊 수급
외국인 당일 순매도 10주. 기관 5일 순매수 20주. 외국인 20일 순매수 30주. 기간별 주체 방향이 엇갈려 중기 사업 근거로 승격하지 않습니다.

📐 Valuation
사이클 고점의 이익만으로 판단하지 않습니다.

📌 다음 확인
• HBM 출하와 수율을 확인합니다.

⚠️ 미확인
• HBM 출하와 수율을 확인합니다.
"""


MARKET_MESSAGE = """🤖 AI 보조 한국시장 마감 · KR Pilot 1/1

🎯 현재 시장 한 줄
새로운 당일 거시 관측이 없어 직전 세션과 지연 공표 자료를 현재 신호로 승격하지 않습니다.

🧭 시장 구조
직전 완료된 미국 정규장에서는 S&P500 등락률 +0.4%였지만 오늘의 신규 관측은 아닙니다.

⚠️ 데이터 주의
• 다음 공식 관측 전까지 오늘의 거시 방향은 확정하지 않습니다.
"""


def _analysis():
    return build_free_analyst_analysis(INVENTORY_MESSAGE, benchmark_id="inventory")


def _replace_first_item(analysis, **changes):
    item = replace(analysis.top_findings[0], **changes)
    return replace(analysis, top_findings=(item, *analysis.top_findings[1:]))


def test_structured_analysis_contract_and_support_types() -> None:
    analysis = _analysis()

    assert analysis.analysis_version == CONTRACT_VERSION
    assert analysis.top_findings
    assert analysis.thesis_implications
    assert analysis.alternative_interpretations
    assert analysis.expectation_valuation_interaction
    assert analysis.positioning_synthesis
    assert analysis.unknowns
    assert analysis.next_checks
    assert analysis.message_plan.primary_conclusion == analysis.top_findings[0].item_id
    assert {item.support_type for item in analysis.analysis_items()} >= {
        SupportType.BOUNDED_INFERENCE,
        SupportType.THESIS_LINKAGE,
        SupportType.ALTERNATIVE_INTERPRETATION,
        SupportType.EXPECTATION_VALUATION_LINK,
        SupportType.POSITIONING_SYNTHESIS,
    }
    assert validate_free_analyst_analysis(analysis).status == "PASS"


def test_evidence_ref_integrity_is_fail_closed() -> None:
    analysis = _replace_first_item(_analysis(), evidence_refs=("missing:fact",))
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "evidence_ref_integrity" in {issue.code for issue in result.issues}


def test_unclassified_bounded_inference_is_rejected() -> None:
    analysis = _replace_first_item(_analysis(), rule_id=None)
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "unclassified_synthesis_rule" in {issue.code for issue in result.issues}


def test_hidden_arithmetic_is_rejected_even_when_raw_numbers_exist() -> None:
    analysis = _replace_first_item(
        _analysis(),
        text="두 원시 수치의 차이는 10%라고 계산됩니다.",
        boundary="새 산술은 허용하지 않습니다.",
    )
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "hidden_arithmetic_or_numeric_synthesis" in {issue.code for issue in result.issues}


def test_external_company_knowledge_is_rejected() -> None:
    analysis = _replace_first_item(
        _analysis(),
        text="현재 자료에서는 NVIDIA 고객 채택이 빨라졌을 가능성이 있습니다.",
    )
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "external_knowledge_claim" in {issue.code for issue in result.issues}


def test_unsupported_causality_and_stronger_language_are_rejected() -> None:
    analysis = _replace_first_item(
        _analysis(),
        text="재고 증가 때문에 수요가 붕괴했다고 확정한다.",
    )
    result = validate_free_analyst_analysis(analysis)
    codes = {issue.code for issue in result.issues}

    assert result.status == "FAIL"
    assert "unsupported_causal_conclusion" in codes


def test_temporal_reference_cannot_be_rendered_as_today_move() -> None:
    analysis = build_free_analyst_analysis(MARKET_MESSAGE, benchmark_id="market")
    analysis = _replace_first_item(
        analysis,
        text="현재 자료에서는 미국 시장이 오늘 상승했다고 봅니다.",
    )
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "temporal_leakage" in {issue.code for issue in result.issues}


def test_trade_ar_and_unsupported_metrics_do_not_leak() -> None:
    analysis = _replace_first_item(
        _analysis(),
        text="현재 자료에서는 Trade AR 증가율과 ROIC를 확인할 필요가 있습니다.",
    )
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "forbidden_field_leak" in {issue.code for issue in result.issues}


def test_supply_cannot_change_fundamental_state() -> None:
    analysis = _analysis()
    positioning = replace(
        analysis.positioning_synthesis[0],
        text="외국인 매도로 투자 논리가 약화됐다고 단정합니다.",
        direction=Direction.CHALLENGES,
    )
    analysis = replace(analysis, positioning_synthesis=(positioning,))
    result = validate_free_analyst_analysis(analysis)

    assert result.status == "FAIL"
    assert "supply_fundamental_promotion" in {issue.code for issue in result.issues}


def test_direct_and_hybrid_renderers_use_only_validated_analysis() -> None:
    analysis = _analysis()
    direct = render_free_analyst_direct(analysis)
    hybrid = render_free_analyst_vnext_hybrid(analysis)

    assert validate_free_analyst_analysis(analysis).status == "PASS"
    assert rendered_safety_report(INVENTORY_MESSAGE, analysis, direct)["status"] == "PASS"
    assert rendered_safety_report(INVENTORY_MESSAGE, analysis, hybrid)["status"] == "PASS"
    assert "2.1%p" not in direct.text
    assert "Trade AR" not in direct.text
    assert direct.text.count(analysis.top_findings[0].text) == 1
    assert len(hybrid.text) < len(direct.text)


def test_novel_synthesis_is_distinct_from_current_and_vnext() -> None:
    analysis = _analysis()
    direct = render_free_analyst_direct(analysis)
    vnext = build_minimal_vnext_message(INVENTORY_MESSAGE)
    safety = rendered_safety_report(INVENTORY_MESSAGE, analysis, direct)
    report = novel_synthesis_report(INVENTORY_MESSAGE, vnext.text, direct, safety)

    assert report["novel_supported_synthesis_sentences"] >= 1
    assert report["unsupported_synthesis_sentences"] == 0


def test_production_module_has_no_open_research_dependency() -> None:
    source = (ROOT / "app/services/evidence_locked_free_analyst_service.py").read_text(
        encoding="utf-8"
    )

    assert "open_research" not in source
    assert "event_attribution" not in source


def test_existing_vnext_behavior_remains_available_independently() -> None:
    before = build_minimal_vnext_message(INVENTORY_MESSAGE)
    analysis = _analysis()
    render_free_analyst_direct(analysis)
    after = build_minimal_vnext_message(INVENTORY_MESSAGE)

    assert before == after
