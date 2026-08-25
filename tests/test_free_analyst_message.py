from app.services.free_analyst_message_service import (
    ValueAddType,
    advisory_value_add_gate,
    build_minimal_vnext_message,
    duplicate_next_check_unknown_count,
    factual_parity_report,
)


STOCK_MESSAGE = """🤖 AI 보조 종목 점검

🏢 Example Corp.(AAA)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 보통
시장 기대: 매우 높음

🎯 핵심 판단
수익 확대가 현금 전환으로 이어지는지가 핵심이며 하루 가격만으로 판단을 바꾸지 않습니다.

📈 사업·실적
2026 회계연도 상반기 누계 PPE 투자 후 잉여현금흐름은 $40M입니다. 전년 비교기간보다 줄었으며 CAPEX 회수는 매출 성장과 함께 봐야 합니다.

💰 가격·포지셔닝
가격 구조는 현재가 $100, 동적 지지 $90, 동적 저항 $120, 차트 손익비 2.0배입니다.
• 신규 관찰자: 실적 확인과 지지 유지가 함께 나타날 때 진입을 검토합니다.
• 보유자: 사업 훼손과 가격 훼손을 분리합니다.

📊 수급
외국인 당일 순매도 10주. 기관 5일 순매수 20주. 외국인 20일 순매수 30주. 단기 매도와 중기 매수가 엇갈려 사업 변화의 근거로 쓰지 않습니다.

📐 Valuation
현재 PER 30배로 기대가 높습니다. 실행 확인 전에는 추가 배수 확장을 전제하지 않습니다.

⚠️ 기존 경고
• 설비 전환 지연

📌 다음 확인
• 다음 공식 실적에서 매출과 현금 전환을 확인합니다.

⚠️ 미확인
• 다음 공식 실적에서 매출과 현금 전환을 확인합니다.
"""


def test_dynamic_sections_compress_numeric_recitation_and_deduplicate_unknown() -> None:
    result = build_minimal_vnext_message(STOCK_MESSAGE)

    assert "🎯 오늘 판단" in result.text
    assert "🔎 왜 중요한가" in result.text
    assert "가격 구조는 현재가" not in result.text
    assert "사업 훼손과 가격 훼손을 분리합니다" in result.text
    assert "단기 매도와 중기 매수가 엇갈려" in result.text
    assert result.text.count("다음 공식 실적에서 매출과 현금 전환") == 1
    assert result.duplicate_next_check_unknown_before == 1
    assert result.duplicate_next_check_unknown_after == 0
    assert ValueAddType.PRIORITY_SELECTION in result.value_add_types
    assert ValueAddType.THESIS_LINKAGE in result.value_add_types
    assert ValueAddType.CROSS_HORIZON_SYNTHESIS in result.value_add_types
    assert ValueAddType.EXPECTATION_VALUATION_CONNECTION in result.value_add_types
    assert ValueAddType.UNKNOWN_RESOLUTION_FRAMING in result.value_add_types


def test_selected_source_spans_create_no_new_arithmetic_or_causality() -> None:
    result = build_minimal_vnext_message(STOCK_MESSAGE)
    parity = factual_parity_report(STOCK_MESSAGE, result.text)

    assert parity["status"] == "PASS"
    assert parity["fact_mismatch"] == 0
    assert parity["unsupported_numeric_claims"] == []
    assert parity["unsupported_causality"] == 0


def test_advisory_value_add_gate_requires_real_selection() -> None:
    result = build_minimal_vnext_message(STOCK_MESSAGE)
    gate = advisory_value_add_gate("deterministic fallback", STOCK_MESSAGE, result)

    assert gate["AI_ANALYST_VALUE_ADD"] == "PASS"
    assert gate["compression_percent"] > 0
    assert gate["vnext_numeric_density"] < gate["current_numeric_density"]
    assert set(gate["advisory_checks"].values()) == {"PASS"}


def test_market_digest_omits_reference_only_context() -> None:
    message = """🤖 AI 보조 한국시장 마감

🎯 현재 시장 한 줄
새로운 당일 거시 관측이 없어 이전 자료를 현재 신호로 승격하지 않습니다.

🧭 시장 구조
직전 완료된 미국 정규장에서는 S&P500 등락률 +0.4%였지만 오늘의 신규 관측은 아닙니다.

⚠️ 데이터 주의
• 다음 공식 관측 전까지 오늘의 거시 방향은 확정하지 않습니다.
"""

    result = build_minimal_vnext_message(message)

    assert "직전 완료된 미국 정규장" not in result.text
    assert "다음 공식 관측" in result.text
    assert result.value_add_types == (ValueAddType.PRIORITY_SELECTION,)


def test_distinct_unknown_is_retained_once() -> None:
    message = STOCK_MESSAGE.replace(
        "• 다음 공식 실적에서 매출과 현금 전환을 확인합니다.\n\n⚠️ 미확인\n"
        "• 다음 공식 실적에서 매출과 현금 전환을 확인합니다.",
        "• 다음 공식 실적에서 매출과 현금 전환을 확인합니다.\n\n⚠️ 미확인\n"
        "• 고객별 투자 회수 기간은 미확인입니다.",
    )

    result = build_minimal_vnext_message(message)

    assert result.text.count("다음 공식 실적에서 매출과 현금 전환") == 1
    assert result.text.count("고객별 투자 회수 기간") == 1
    assert duplicate_next_check_unknown_count(result.text) == 0


def test_unsupported_number_fails_factual_parity() -> None:
    result = build_minimal_vnext_message(STOCK_MESSAGE)
    tampered = result.text + "\n새 목표가는 $999입니다."
    parity = factual_parity_report(STOCK_MESSAGE, tampered)

    assert parity["status"] == "FAIL"
    assert "999" in parity["unsupported_numeric_claims"]


def test_exact_trade_ar_is_not_introduced() -> None:
    result = build_minimal_vnext_message(STOCK_MESSAGE)
    tampered = result.text + "\nTrade AR 증가율 18.0%p입니다."
    parity = factual_parity_report(STOCK_MESSAGE, tampered)

    assert parity["status"] == "FAIL"
    assert parity["trade_ar_user_visible_leaks"]
