from __future__ import annotations

import copy
import json
from pathlib import Path

from app.services.price_structure_v3_renderer_service import (
    classify_confluence_render_equivalence,
    detect_legacy_technical_tokens,
    relabel_stored_price_rules,
    render_current_price_structure,
    replace_current_price_structure,
    suppress_legacy_technical_prose,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/reports/20260826-v3-current-data-validation-evidence.json"


def _zone(
    zone_id: str,
    low: str,
    high: str,
    display: str,
) -> dict[str, object]:
    return {
        "zone_id": zone_id,
        "raw_low": low,
        "raw_high": high,
        "display": display,
        "currency": "USD",
        "source_refs": [f"source:{zone_id}"],
    }


def _selection(zone: dict[str, object] | None) -> dict[str, object]:
    return {"zone": zone, "classification": "AVAILABLE"}


def _summary(
    *,
    support: dict[str, object] | None = None,
    resistance: dict[str, object] | None = None,
    major_support: dict[str, object] | None = None,
    major_resistance: dict[str, object] | None = None,
    confluence: dict[str, object] | None = None,
    confluence_state: str = "UNAVAILABLE",
) -> dict[str, object]:
    return {
        "nearest_support": _selection(support),
        "nearest_resistance": _selection(resistance),
        "major_structural_support": _selection(major_support),
        "major_structural_resistance": _selection(major_resistance),
        "fib_sr_confluence": confluence,
        "fib_sr_confluence_state": confluence_state,
    }


def _render(summary: dict[str, object]) -> str:
    return render_current_price_structure(
        summary,
        ticker="TEST",
        as_of="2026-08-25",
        current_price="100",
        currency="USD",
        include_current_price=False,
    ).section


def _evidence_rows() -> dict[str, dict[str, object]]:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return {row["ticker"]: row for row in payload["rows"]}


def test_identical_confluence_suppresses_redundant_numeric_range() -> None:
    resistance = _zone("resistance", "105", "110", "약 $105~$110")
    confluence = copy.deepcopy(resistance)
    confluence["zone_id"] = "fib"

    rendered = _render(
        _summary(
            resistance=resistance,
            confluence=confluence,
            confluence_state="DIRECT_SR_CONFLUENCE",
        )
    )

    assert rendered.count("약 $105~$110") == 1
    assert "같은 구조 구간" in rendered


def test_partial_overlap_with_material_extension_preserves_fib_range() -> None:
    resistance = _zone("resistance", "105", "110", "약 $105~$110")
    confluence = _zone("fib", "105", "115", "약 $105~$115")

    decision = classify_confluence_render_equivalence(confluence, [resistance])
    rendered = _render(
        _summary(
            resistance=resistance,
            confluence=confluence,
            confluence_state="DIRECT_SR_CONFLUENCE",
        )
    )

    assert decision.classification == "MATERIAL_RANGE_EXTENSION"
    assert "Fib/SR 겹침: 약 $105~$115" in rendered


def test_distinct_confluence_is_rendered_separately() -> None:
    resistance = _zone("resistance", "105", "110", "약 $105~$110")
    confluence = _zone("fib", "120", "125", "약 $120~$125")

    decision = classify_confluence_render_equivalence(confluence, [resistance])
    rendered = _render(
        _summary(
            resistance=resistance,
            confluence=confluence,
            confluence_state="NEAR_SR_CONFLUENCE",
        )
    )

    assert decision.classification == "DISTINCT_RANGE"
    assert "약 $120~$125" in rendered


def test_reference_only_and_sr_only_do_not_render_empty_fib_line() -> None:
    support = _zone("support", "90", "95", "약 $90~$95")
    confluence = _zone("fib", "90", "95", "약 $90~$95")

    reference_only = _render(
        _summary(
            support=support,
            confluence=confluence,
            confluence_state="FIB_REFERENCE_ONLY",
        )
    )
    sr_only = _render(_summary(support=support))

    assert "Fib" not in reference_only
    assert "Fib" not in sr_only


def test_renderer_does_not_mutate_raw_sr_or_fib_values() -> None:
    summary = _summary(
        support=_zone("support", "90", "95", "약 $90~$95"),
        confluence=_zone("fib", "89", "96", "약 $89~$96"),
        confluence_state="DIRECT_SR_CONFLUENCE",
    )
    original = copy.deepcopy(summary)

    _render(summary)

    assert summary == original


def test_stored_price_rules_receive_explicit_owner_without_numeric_change() -> None:
    message = """💰 가격
현재가: $100.00

📐 현재 가격 구조
• 가까운 지지: 약 $90~$95

보유자:
• 차트 무효화 가격: $80.00
• 동적 지지 유지 여부: $85.00~$88.00
가격 규칙 이력:
• 등록 확인선 $105은 아직 도달하지 않았습니다.

📐 Valuation
PER: 10배
"""

    repaired = relabel_stored_price_rules(message, ticker="TEST")

    assert "🧭 기존 등록 가격 규칙" in repaired.message
    assert "• 기존 무효화 가격: $80.00" in repaired.message
    assert "• 기존 등록 지지 규칙: $85.00~$88.00" in repaired.message
    assert "• 기존 확인선 $105" in repaired.message
    assert "보유자:" not in repaired.message
    assert [binding["display"] for binding in repaired.numeric_bindings] == [
        "$80.00",
        "$85.00",
        "$88.00",
        "$105",
    ]
    assert all(
        binding["fact_ref"] == "chart:stored_price_rules"
        for binding in repaired.numeric_bindings
    )


def test_stale_legacy_sentence_is_removed_but_business_sentence_is_preserved() -> None:
    message = """🎯 핵심
HBM 수요가 수익성을 지지한다. 2026-08-12 OHLCV 기준 주봉 MACD가 플러스다.

📐 현재 가격 구조
• 가까운 지지: 약 $90~$95
"""

    repaired = suppress_legacy_technical_prose(
        message,
        current_session="2026-08-25",
        active_v3=True,
    )

    assert "HBM 수요가 수익성을 지지한다." in repaired.message
    assert "2026-08-12" not in repaired.message
    assert "MACD" not in repaired.message
    assert repaired.occurrences[0].classification == "STALE_OR_REDUNDANT_LEGACY"
    assert repaired.occurrences[0].action == "SUPPRESS"


def test_current_canonical_nonredundant_indicator_sentence_may_remain() -> None:
    message = """🎯 핵심
2026-08-25 OHLCV 기준 일봉 MACD가 개선됐습니다.

📐 현재 가격 구조
• 가까운 지지: 약 $90~$95
"""

    repaired = suppress_legacy_technical_prose(
        message,
        current_session="2026-08-25",
        active_v3=True,
        canonical_indicator_sessions=("2026-08-25",),
    )

    assert "MACD" in repaired.message
    assert repaired.occurrences[0].classification == "VALID_NONREDUNDANT_LEGACY"


def test_indicator_acronyms_do_not_match_inside_ordinary_words() -> None:
    ordinary_words = (
        "Recursion",
        "recursion",
        "conversion",
        "version",
        "diversion",
        "precision",
        "decision",
        "macdonald",
    )

    assert all(not detect_legacy_technical_tokens(word) for word in ordinary_words)


def test_indicator_tokens_support_korean_postpositions_and_numeric_suffixes() -> None:
    values = (
        "RSI 72",
        "RSI가 70을 상회",
        "RSI는 과열",
        "MACD histogram 둔화",
        "MACD가 0선 아래",
        "OHLCV를 확인",
        "Bollinger 상단",
        "ATR 확대",
        "EMA20",
    )

    assert all(detect_legacy_technical_tokens(value) for value in values)


def test_company_header_is_protected_from_legacy_technical_suppression() -> None:
    message = """🏢 Recursion Pharmaceuticals(RXRX)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

🎯 핵심
파트너 타깃 선택과 임상 진전이 핵심이다.
"""

    repaired = suppress_legacy_technical_prose(
        message,
        current_session="2026-08-25",
        active_v3=True,
    )

    assert repaired.message == message.strip()
    assert repaired.message.startswith("🏢 Recursion Pharmaceuticals(RXRX)")
    assert repaired.occurrences == ()


def test_structural_fields_are_never_suppressed_by_indicator_tokens() -> None:
    message = """🏢 RSI Holdings(TEST)

투자 논리: RSI 검증 상태 유지

🎯 핵심
사업 근거는 유지된다.

📌 다음 확인
• RSI 관련 제품명 확인
"""

    repaired = suppress_legacy_technical_prose(
        message,
        current_session="2026-08-25",
        active_v3=True,
    )

    assert repaired.message == message.strip()
    assert repaired.occurrences == ()


def test_stale_token_match_records_field_span_and_boundary() -> None:
    message = """🎯 핵심
사업 근거는 유지된다. 2026-08-12 OHLCV 기준 MACD가 둔화했다.
"""

    repaired = suppress_legacy_technical_prose(
        message,
        current_session="2026-08-25",
        active_v3=True,
    )

    occurrence = repaired.occurrences[0]
    assert occurrence.semantic_field == "TECHNICAL_PROSE_CANDIDATE"
    assert occurrence.matched_terms == ("OHLCV", "MACD")
    assert occurrence.match_spans
    assert occurrence.token_boundary_types == (
        "ASCII_TOKEN_OR_KOREAN_SUFFIX_BOUNDARY",
        "ASCII_TOKEN_OR_KOREAN_SUFFIX_BOUNDARY",
    )
    assert occurrence.suppression_reason == (
        "stale_or_redundant_legacy_technical_sentence"
    )


def test_exact_controls_repair_only_renderer_surfaces() -> None:
    rows = _evidence_rows()
    repaired: dict[str, str] = {}
    for ticker in ("000660", "SNDK", "MU", "TSM", "TSLA", "012450"):
        row = rows[ticker]
        render = render_current_price_structure(
            row["summary"],
            ticker=ticker,
            as_of=row["target_session"],
            current_price=row["current_price"],
            currency=row["currency"],
            include_current_price=row["market"] == "KR",
        )
        message = replace_current_price_structure(row["candidate_message"], render.section)
        message = relabel_stored_price_rules(message, ticker=ticker).message
        message = suppress_legacy_technical_prose(
            message,
            current_session=row["target_session"],
            active_v3=True,
        ).message
        repaired[ticker] = message

    assert "Fib/SR 겹침: 약 186.9만~191.6만원" in repaired["000660"]
    assert "📐 현재 가격 구조" in repaired["SNDK"]
    assert "🧭 기존 등록 가격 규칙" in repaired["SNDK"]
    assert "2026-08-12 OHLCV" not in repaired["MU"]
    assert "MACD" not in repaired["MU"]
    assert "가까운 저항: 약 $424.69~$426.83" in repaired["TSM"]
    assert "기존 확인선 $432" in repaired["TSM"]
    assert "Fib/SR" not in repaired["TSLA"]
    assert "Fib/SR 겹침: 약 104.7만~105.8만원" in repaired["012450"]
