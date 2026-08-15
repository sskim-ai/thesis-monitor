from __future__ import annotations

import pytest

from app.services.numeric_provenance_service import (
    bind_numeric_fact_references,
    canonical_numeric_label_mismatch,
)
from app.services.numeric_semantic_registry import build_numeric_registry


def _fact(fact_id: str, fact_type: str, fields: dict[str, object]) -> dict[str, object]:
    return {"fact_id": fact_id, "fact_type": fact_type, "fields": fields}


def _bind_stock(
    facts: list[dict[str, object]],
    text: str,
    refs: list[dict[str, str]],
    *,
    ticker: str = "GENERIC",
):
    packet = {
        "stocks": [
            {
                "ticker": ticker,
                "numeric_registry": build_numeric_registry(facts),
            }
        ]
    }
    output = {
        "stock_reviews": [
            {
                "ticker": ticker,
                "facts_used": [str(item["fact_id"]) for item in facts],
                "core_judgment": {"text": text},
                "numeric_claims": [],
                "numeric_fact_refs": refs,
            }
        ]
    }
    return bind_numeric_fact_references(packet, output)


def _bind_market(
    facts: list[dict[str, object]],
    text: str,
    refs: list[dict[str, str]],
):
    packet = {
        "market_context": {"numeric_registry": build_numeric_registry(facts)}
    }
    output = {
        "market_review": {
            "facts_used": [str(item["fact_id"]) for item in facts],
            "core_judgment": {"text": text},
            "numeric_claims": [],
            "numeric_fact_refs": refs,
        }
    }
    return bind_numeric_fact_references(packet, output)


def _ref(
    ref_id: str,
    fact_id: str,
    field_path: str,
    *,
    role: str | None = None,
) -> dict[str, str]:
    value = {
        "ref_id": ref_id,
        "fact_id": fact_id,
        "field_path": field_path,
        "text_ref": "core_judgment.text",
    }
    if role is not None:
        value["role"] = role
    return value


def test_placeholder_contract_binds_complete_stock_numeric_phrases() -> None:
    facts = [
        _fact(
            "earnings:usd",
            "earnings",
            {
                "revenue": {"value": 164_200_000, "currency": "USD"},
                "revenue_qoq_pct": 18.5,
                "revenue_yoy_pct": 108.8,
                "operating_margin_pct": 60.3,
            },
        ),
        _fact(
            "earnings:twd",
            "earnings",
            {"revenue": {"value": 1_270_380_000_000, "currency": "TWD"}},
        ),
        _fact(
            "valuation:consensus",
            "valuation",
            {
                "currency": "USD",
                "trailing_pe": 42.4069,
                "forward_pe": 68.9372,
                "forward_pe_source": "consensus_forward",
                "price_to_book": 58.88,
                "historical_pb_statistics": {"current_percentile": 100.0},
            },
        ),
        _fact(
            "valuation:modeled",
            "valuation",
            {
                "currency": "USD",
                "forward_pe": 5.87,
                "forward_pe_source": "modeled_forward",
            },
        ),
        _fact(
            "price:current",
            "price",
            {"current_price": 5.85, "currency": "USD"},
        ),
        _fact(
            "chart:daily",
            "chart_timeframe",
            {"volume_ratio_20": 0.52, "currency": "USD"},
        ),
        _fact(
            "chart:support",
            "chart_support_zone",
            {"zone_low": 19.44, "zone_high": 20.34, "currency": "USD"},
        ),
        _fact(
            "chart:resistance",
            "chart_resistance_zone",
            {"zone_low": 23.05, "zone_high": 24.21, "currency": "USD"},
        ),
        _fact(
            "chart:rr",
            "chart_risk_reward",
            {"ratio": 1.77, "currency": "USD"},
        ),
    ]
    refs = [
        _ref("usd_revenue", "earnings:usd", "fields.revenue.value"),
        _ref("twd_revenue", "earnings:twd", "fields.revenue.value"),
        _ref("margin", "earnings:usd", "fields.operating_margin_pct"),
        _ref("qoq", "earnings:usd", "fields.revenue_qoq_pct"),
        _ref("yoy", "earnings:usd", "fields.revenue_yoy_pct"),
        _ref("price", "price:current", "fields.current_price"),
        _ref("pe", "valuation:consensus", "fields.trailing_pe"),
        _ref("consensus_fpe", "valuation:consensus", "fields.forward_pe"),
        _ref("modeled_fpe", "valuation:modeled", "fields.forward_pe"),
        _ref("pbr", "valuation:consensus", "fields.price_to_book"),
        _ref(
            "pb_percentile",
            "valuation:consensus",
            "fields.historical_pb_statistics.current_percentile",
        ),
        _ref("volume", "chart:daily", "fields.volume_ratio_20"),
        _ref("support_low", "chart:support", "fields.zone_low", role="lower"),
        _ref(
            "resistance_high",
            "chart:resistance",
            "fields.zone_high",
            role="upper",
        ),
        _ref("rr", "chart:rr", "fields.ratio"),
    ]
    draft = " · ".join(f"{{{{numeric:{item['ref_id']}}}}}" for item in refs)

    result = _bind_stock(facts, draft, refs)

    assert result.errors == ()
    text = result.output["stock_reviews"][0]["core_judgment"]["text"]
    expected = (
        "매출 $164.2M",
        "매출 NT$1.27T",
        "영업이익률 60.3%",
        "매출 QoQ 18.5%",
        "매출 성장률 108.8%",
        "현재가 $5.85",
        "현재 PER 42.41배",
        "시장 예상 fPER 68.94배",
        "내부 추정 fPER 5.87배",
        "현재 PBR 58.88배",
        "PBR 역사적 백분위 100%",
        "20일 거래량비 0.52배",
        "동적 지지구간 하단 $19.44",
        "동적 저항구간 상단 $24.21",
        "차트 손익비 1.77배",
    )
    assert all(item in text for item in expected)
    assert len(result.report["bindings"]) == len(refs)


@pytest.mark.parametrize(
    ("fact", "field_path", "authored_label"),
    [
        (
            _fact(
                "earnings",
                "earnings",
                {"revenue": {"value": 164_200_000, "currency": "USD"}},
            ),
            "fields.revenue.value",
            "매출",
        ),
        (
            _fact(
                "valuation",
                "valuation",
                {"trailing_pe": 42.41, "currency": "USD"},
            ),
            "fields.trailing_pe",
            "현재 PER",
        ),
        (
            _fact(
                "valuation",
                "valuation",
                {"trailing_pe": 42.41, "currency": "USD"},
            ),
            "fields.trailing_pe",
            "PER",
        ),
        (
            _fact(
                "valuation",
                "valuation",
                {
                    "forward_pe": 68.94,
                    "forward_pe_source": "consensus_forward",
                    "currency": "USD",
                },
            ),
            "fields.forward_pe",
            "선행 PER",
        ),
        (
            _fact(
                "valuation",
                "valuation",
                {
                    "forward_pe": 68.94,
                    "forward_pe_source": "consensus_forward",
                    "currency": "USD",
                },
            ),
            "fields.forward_pe",
            "fPER",
        ),
        (
            _fact(
                "valuation",
                "valuation",
                {"price_to_book": 2.45, "currency": "USD"},
            ),
            "fields.price_to_book",
            "현재 PBR",
        ),
        (
            _fact(
                "valuation",
                "valuation",
                {"price_to_book": 2.45, "currency": "USD"},
            ),
            "fields.price_to_book",
            "PBR",
        ),
        (
            _fact(
                "price",
                "price",
                {"current_price": 5.85, "currency": "USD"},
            ),
            "fields.current_price",
            "현재가",
        ),
        (
            _fact(
                "earnings",
                "earnings",
                {"revenue_yoy_pct": 108.8},
            ),
            "fields.revenue_yoy_pct",
            "매출 성장률",
        ),
        (
            _fact(
                "earnings",
                "earnings",
                {"operating_margin_pct": 60.3},
            ),
            "fields.operating_margin_pct",
            "영업이익률",
        ),
    ],
)
def test_redundant_authored_stock_labels_fail_closed(
    fact: dict[str, object],
    field_path: str,
    authored_label: str,
) -> None:
    result = _bind_stock(
        [fact],
        f"{authored_label} {{{{numeric:value}}}}",
        [_ref("value", str(fact["fact_id"]), field_path)],
    )

    assert any(
        "GENERIC:numeric_fact_ref_redundant_authored_label:"
        "value:core_judgment.text" in item
        for item in result.errors
    )
    assert result.report["label_quality"]["redundant_authored_label_count"] == 1


def test_redundant_authored_futures_label_fails_closed() -> None:
    fact = _fact(
        "night",
        "night_futures",
        {
            "series_code": "KRX_KOSPI200_NIGHT_FUT",
            "change_pct": -0.32,
        },
    )
    result = _bind_market(
        [fact],
        "야간선물 등락률 {{numeric:return}}",
        [_ref("return", "night", "fields.change_pct")],
    )

    assert any("numeric_fact_ref_redundant_authored_label" in item for item in result.errors)


def test_numeric_context_does_not_trigger_redundant_label_false_positive() -> None:
    facts = [
        _fact(
            "earnings",
            "earnings",
            {
                "revenue": {"value": 1_270_380_000_000, "currency": "TWD"},
                "operating_margin_pct": 60.3,
            },
        ),
        _fact(
            "valuation",
            "valuation",
            {
                "currency": "USD",
                "trailing_pe": 27.87,
                "forward_pe": 21.36,
                "forward_pe_source": "consensus_forward",
            },
        ),
    ]
    text = (
        "TWD 기준인 {{numeric:revenue}}를 ADR 가격과 직접 환산하지 않습니다. "
        "현재 평가에서는 {{numeric:pe}}와 {{numeric:fpe}}의 방향을 비교합니다. "
        "다음 실적에서 {{numeric:margin}}의 지속성을 확인합니다."
    )
    refs = [
        _ref("revenue", "earnings", "fields.revenue.value"),
        _ref("pe", "valuation", "fields.trailing_pe"),
        _ref("fpe", "valuation", "fields.forward_pe"),
        _ref("margin", "earnings", "fields.operating_margin_pct"),
    ]

    result = _bind_stock(facts, text, refs)

    assert result.errors == ()
    bound = result.output["stock_reviews"][0]["core_judgment"]["text"]
    assert "TWD 기준인 매출 NT$1.27T" in bound
    assert "현재 평가에서는 현재 PER 27.87배와 시장 예상 fPER 21.36배" in bound


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("modeled_forward", "내부 추정 fPER 5.87배"),
        ("consensus_forward", "시장 예상 fPER 5.87배"),
    ],
)
def test_forward_source_enum_selects_canonical_label(
    source: str,
    expected: str,
) -> None:
    fact = _fact(
        "valuation",
        "valuation",
        {
            "currency": "USD",
            "forward_pe": 5.87,
            "forward_pe_source": source,
        },
    )

    result = _bind_stock(
        [fact],
        "{{numeric:fpe}}",
        [_ref("fpe", "valuation", "fields.forward_pe")],
        ticker="RENAMED",
    )

    assert result.errors == ()
    assert result.output["stock_reviews"][0]["core_judgment"]["text"] == expected


@pytest.mark.parametrize(
    ("source", "expected_pbr", "expected_bvps"),
    [
        ("modeled_forward", "내부 추정 fPBR 2.45배", "내부 추정 BVPS $5.85"),
        ("consensus_forward", "시장 예상 fPBR 2.45배", "시장 예상 BVPS $5.85"),
    ],
)
def test_forward_book_source_enum_selects_canonical_labels(
    source: str,
    expected_pbr: str,
    expected_bvps: str,
) -> None:
    fact = _fact(
        "valuation",
        "valuation",
        {
            "currency": "USD",
            "forward_price_to_book": 2.45,
            "forward_bvps": 5.85,
            "forward_price_to_book_source": source,
        },
    )

    result = _bind_stock(
        [fact],
        "{{numeric:fpbr}} · {{numeric:bvps}}",
        [
            _ref("fpbr", "valuation", "fields.forward_price_to_book"),
            _ref("bvps", "valuation", "fields.forward_bvps"),
        ],
        ticker="RENAMED",
    )

    assert result.errors == ()
    text = result.output["stock_reviews"][0]["core_judgment"]["text"]
    assert expected_pbr in text
    assert expected_bvps in text


def test_crcl_consensus_forward_regression_uses_market_expected_label() -> None:
    fact = _fact(
        "valuation:CRCL",
        "valuation",
        {
            "currency": "USD",
            "trailing_pe": 42.4069,
            "forward_pe": 68.9372,
            "forward_pe_source": "consensus_forward",
        },
    )
    result = _bind_stock(
        [fact],
        "{{numeric:pe}}보다 {{numeric:fpe}}가 높습니다.",
        [
            _ref("pe", "valuation:CRCL", "fields.trailing_pe"),
            _ref("fpe", "valuation:CRCL", "fields.forward_pe"),
        ],
        ticker="CRCL",
    )

    assert result.errors == ()
    text = result.output["stock_reviews"][0]["core_judgment"]["text"]
    assert text == "현재 PER 42.41배보다 시장 예상 fPER 68.94배가 높습니다."


def test_unknown_forward_source_is_not_given_a_generic_label() -> None:
    fact = _fact(
        "valuation",
        "valuation",
        {
            "currency": "USD",
            "forward_pe": 5.87,
            "forward_pe_source": "unavailable",
        },
    )
    registry = build_numeric_registry([fact])
    row = next(item for item in registry if item["field_path"] == "fields.forward_pe")

    assert row["canonical_label"] is None
    assert row["prose_allowed"] is False
    result = _bind_stock(
        [fact],
        "{{numeric:fpe}}",
        [_ref("fpe", "valuation", "fields.forward_pe")],
    )
    assert any("numeric_fact_ref_semantic_not_supported" in item for item in result.errors)


@pytest.mark.parametrize(
    ("series_code", "expected"),
    [
        ("SPY", "S&P500 등락률 -0.2%"),
        ("QQQ", "Nasdaq 등락률 -0.2%"),
        ("IWM", "Russell 2000 등락률 -0.2%"),
    ],
)
def test_market_index_identity_selects_canonical_label(
    series_code: str,
    expected: str,
) -> None:
    fact = _fact(
        "index",
        "market_index",
        {"series_code": series_code, "return_pct": -0.2},
    )

    result = _bind_market(
        [fact],
        "{{numeric:index_return}}",
        [_ref("index_return", "index", "fields.return_pct")],
    )

    assert result.errors == ()
    assert result.output["market_review"]["core_judgment"]["text"] == expected


def test_unknown_index_does_not_fall_back_to_sp500() -> None:
    fact = _fact(
        "index",
        "market_index",
        {"series_code": "UNKNOWN_INDEX", "return_pct": 1.2},
    )
    registry = build_numeric_registry([fact])
    row = next(item for item in registry if item["field_path"] == "fields.return_pct")

    assert row["canonical_label"] is None
    assert row["prose_allowed"] is False
    result = _bind_market(
        [fact],
        "{{numeric:index_return}}",
        [_ref("index_return", "index", "fields.return_pct")],
    )
    assert any("numeric_fact_ref_semantic_not_supported" in item for item in result.errors)


def test_relative_market_metric_uses_subject_and_benchmark_identity() -> None:
    facts = [
        _fact(
            "growth",
            "market_growth_relative",
            {"subject": "QQQ", "benchmark": "SPY", "relative_return_pct": 0.3},
        ),
        _fact(
            "sector",
            "market_sector_relative",
            {"subject": "SOXX", "benchmark": "SPY", "relative_return_pct": -0.1},
        ),
    ]
    refs = [
        _ref("growth", "growth", "fields.relative_return_pct"),
        _ref("sector", "sector", "fields.relative_return_pct"),
    ]

    result = _bind_market(
        facts,
        "{{numeric:growth}} · {{numeric:sector}}",
        refs,
    )

    assert result.errors == ()
    text = result.output["market_review"]["core_judgment"]["text"]
    assert "S&P500 대비 Nasdaq 상대수익률 +0.3%" in text
    assert "S&P500 대비 반도체 상대수익률 -0.1%" in text


def test_unknown_relative_identity_does_not_use_first_approved_label() -> None:
    fact = _fact(
        "relative",
        "market_growth_relative",
        {
            "subject": "UNKNOWN_SUBJECT",
            "benchmark": "SPY",
            "relative_return_pct": 0.3,
        },
    )
    row = next(
        item
        for item in build_numeric_registry([fact])
        if item["field_path"] == "fields.relative_return_pct"
    )

    assert row["canonical_label"] is None
    assert row["prose_allowed"] is False


@pytest.mark.parametrize(
    ("series_code", "product"),
    [
        ("KRX_KOSPI200_NIGHT_FUT", "KOSPI200 야간선물"),
        ("KRX_KOSDAQ150_NIGHT_FUT", "KOSDAQ150 야간선물"),
    ],
)
def test_night_futures_identity_selects_all_canonical_labels(
    series_code: str,
    product: str,
) -> None:
    fact = _fact(
        "night",
        "night_futures",
        {
            "series_code": series_code,
            "value": 1095.4,
            "change_value": -3.5,
            "change_pct": -0.32,
        },
    )
    refs = [
        _ref("close", "night", "fields.value"),
        _ref("change", "night", "fields.change_value"),
        _ref("return", "night", "fields.change_pct"),
    ]

    result = _bind_market(
        [fact],
        "{{numeric:close}} · {{numeric:change}} · {{numeric:return}}",
        refs,
    )

    assert result.errors == ()
    text = result.output["market_review"]["core_judgment"]["text"]
    assert f"{product} 종가 1,095.4포인트" in text
    assert f"{product} 등락폭 -3.5포인트" in text
    assert f"{product} 등락률 -0.32%" in text


def test_unknown_night_futures_and_wrong_instrument_usage_fail_closed() -> None:
    unknown = _fact(
        "unknown",
        "night_futures",
        {"series_code": "UNKNOWN_NIGHT_FUT", "change_pct": 1.2},
    )
    row = next(
        item
        for item in build_numeric_registry([unknown])
        if item["field_path"] == "fields.change_pct"
    )
    assert row["prose_allowed"] is False

    qqq = _fact(
        "qqq",
        "market_index",
        {"series_code": "QQQ", "return_pct": 1.2},
    )
    source = next(
        item
        for item in build_numeric_registry([qqq])
        if item["field_path"] == "fields.return_pct"
    )
    assert canonical_numeric_label_mismatch(source, "S&P500 등락률 +1.2%") == "instrument"
    assert canonical_numeric_label_mismatch(source, "Nasdaq 등락률 +1.2%") is None

    kospi = _fact(
        "kospi",
        "night_futures",
        {
            "series_code": "KRX_KOSPI200_NIGHT_FUT",
            "change_pct": -0.32,
        },
    )
    kosdaq = _fact(
        "kosdaq",
        "night_futures",
        {
            "series_code": "KRX_KOSDAQ150_NIGHT_FUT",
            "change_pct": 1.67,
        },
    )
    kospi_source = next(
        item
        for item in build_numeric_registry([kospi])
        if item["field_path"] == "fields.change_pct"
    )
    kosdaq_source = next(
        item
        for item in build_numeric_registry([kosdaq])
        if item["field_path"] == "fields.change_pct"
    )
    assert (
        canonical_numeric_label_mismatch(
            kospi_source,
            "KOSDAQ150 야간선물 등락률 -0.32%",
        )
        == "instrument"
    )
    assert (
        canonical_numeric_label_mismatch(
            kosdaq_source,
            "KOSPI200 야간선물 등락률 +1.67%",
        )
        == "instrument"
    )
