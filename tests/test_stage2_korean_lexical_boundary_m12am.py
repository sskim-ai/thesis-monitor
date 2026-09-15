from __future__ import annotations

import pytest

from scripts.main_integration_two_stage_directional_m12ae_r2_runtime import (
    STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
    STAGE2_SCANNED_TEXT_PATHS,
    stage2_language_contamination_spans,
)


@pytest.mark.parametrize(
    "text",
    (
        "현재 주가가 상승했다",
        "주가는 아직 비싸다",
        "주가상승을 기다린다",
        "주가가 반등하면 진입한다",
        "차트가 개선됐다",
        "수급이 좋아져 신규 진입이 가능하다",
        "기술적 지지선을 확인한다",
        "거래량이 증가했다",
        "RSI가 과열이다",
        "MACD signal을 확인한다",
        "Bollinger band를 본다",
        "support level을 확인한다",
        "resistance level을 확인한다",
    ),
)
def test_genuine_price_technical_language_remains_contamination(text: str) -> None:
    assert stage2_language_contamination_spans(text)


@pytest.mark.parametrize(
    "text",
    (
        "해외수주가 확대되고 있다",
        "신규 수주가 증가했다",
        "신규수주가 늘었다",
        "발주가 회복됐다",
        "수주가 영업이익으로 전환된다",
        "기술적 경쟁력이 개선됐다",
        "기술적 진입장벽이 높다",
        "원자재 수급이 안정되고 생산 효율이 개선됐다",
    ),
)
def test_business_language_does_not_trigger_substring_false_positive(text: str) -> None:
    assert stage2_language_contamination_spans(text) == ()


def test_share_price_rule_keeps_left_boundary_and_open_right_side() -> None:
    spans = stage2_language_contamination_spans(
        "해외수주가 늘었지만 주가하락은 이어졌다",
        text_path="fundamental_new_buyer.summary",
    )

    assert len(spans) == 1
    assert spans[0] == {
        "text_path": "fundamental_new_buyer.summary",
        "matched_contamination_span": "주가",
        "matched_lexeme": "주가",
        "match_start": 11,
        "match_end": 13,
        "match_rule_id": "korean-share-price-left-boundary",
        "risk_class": "AMBIGUOUS_KOREAN_LEXEME_WITH_LEFT_BOUNDARY",
    }


def test_stage2_scanner_contract_is_stance_owned_only() -> None:
    assert STAGE2_LANGUAGE_CONTAMINATION_CONTRACT == (
        "stage2-language-contamination-v2"
    )
    assert STAGE2_SCANNED_TEXT_PATHS == (
        "fundamental_new_buyer.summary",
        "fundamental_new_buyer.confirmation_business_condition",
        "fundamental_holder.summary",
        "fundamental_holder.business_invalidation_condition",
    )
