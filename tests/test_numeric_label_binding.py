from __future__ import annotations

import pytest

from app.services.numeric_provenance_service import (
    bind_numeric_fact_references,
    canonical_numeric_label_mismatch,
    resolve_numeric_postposition,
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
    postposition: str | None = None,
) -> dict[str, str]:
    value = {
        "ref_id": ref_id,
        "fact_id": fact_id,
        "field_path": field_path,
        "text_ref": "core_judgment.text",
    }
    if role is not None:
        value["role"] = role
    if postposition is not None:
        value["postposition"] = postposition
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


def test_historical_valuation_distribution_roles_bind_distinct_labels() -> None:
    fact = _fact(
        "valuation:current",
        "valuation",
        {
            "historical_pb_statistics": {
                "current_value": 1.8154,
                "historical_median": 3.279,
                "current_percentile": 9.5,
            }
        },
    )
    refs = [
        _ref(
            "current",
            "valuation:current",
            "fields.historical_pb_statistics.current_value",
        ),
        _ref(
            "median",
            "valuation:current",
            "fields.historical_pb_statistics.historical_median",
        ),
        _ref(
            "percentile",
            "valuation:current",
            "fields.historical_pb_statistics.current_percentile",
        ),
    ]

    result = _bind_stock(
        [fact],
        "{{numeric:current}}; {{numeric:median}}; {{numeric:percentile}}",
        refs,
    )

    assert result.errors == ()
    text = result.output["stock_reviews"][0]["core_judgment"]["text"]
    assert text == (
        "현재 PBR 1.82배; 역사적 PBR 중앙값 3.28배; "
        "PBR 역사적 백분위 9.5%"
    )
    bindings = result.report["bindings"]
    assert [item["comparison_role"] for item in bindings] == [
        "current_value",
        "historical_median",
        "current_percentile",
    ]


@pytest.mark.parametrize(
    ("base_field", "history_field", "expected_semantic"),
    [
        ("price_to_book", "historical_pb_statistics", "price_to_book"),
        ("trailing_pe", "historical_pe_statistics", "trailing_pe"),
    ],
)
def test_visible_current_historical_multiple_binds_to_canonical_base_field(
    base_field: str,
    history_field: str,
    expected_semantic: str,
) -> None:
    fact = _fact(
        "valuation:current",
        "valuation",
        {
            base_field: 1.8154,
            history_field: {
                "current_value": 1.8154,
                "historical_median": 3.279,
            },
        },
    )
    result = _bind_stock(
        [fact],
        "{{numeric:current}}",
        [
            _ref(
                "current",
                "valuation:current",
                f"fields.{history_field}.current_value",
            )
        ],
    )

    assert result.errors == ()
    binding = result.report["bindings"][0]
    assert binding["field_path"] == f"fields.{base_field}"
    assert binding["semantic_type"] == expected_semantic


def test_legacy_historical_registry_recovers_comparison_labels_from_path() -> None:
    fact = _fact(
        "valuation:current",
        "valuation",
        {
            "historical_pb_statistics": {
                "current_value": 1.8154,
                "historical_median": 3.279,
            }
        },
    )
    registry = build_numeric_registry([fact])
    for item in registry:
        item["canonical_label"] = None
        item["canonical_label_kind"] = None
        item["canonical_label_required"] = False
        item["comparison_role"] = None
    packet = {"stocks": [{"ticker": "GENERIC", "numeric_registry": registry}]}
    output = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": ["valuation:current"],
                "core_judgment": {
                    "text": "{{numeric:current}}; {{numeric:median}}"
                },
                "numeric_claims": [],
                "numeric_fact_refs": [
                    _ref(
                        "current",
                        "valuation:current",
                        "fields.historical_pb_statistics.current_value",
                    ),
                    _ref(
                        "median",
                        "valuation:current",
                        "fields.historical_pb_statistics.historical_median",
                    ),
                ],
            }
        ]
    }

    result = bind_numeric_fact_references(packet, output)

    assert result.errors == ()
    assert (
        result.output["stock_reviews"][0]["core_judgment"]["text"]
        == "현재 PBR 1.82배; 역사적 PBR 중앙값 3.28배"
    )
    assert [item["comparison_role"] for item in result.report["bindings"]] == [
        "current_value",
        "historical_median",
    ]


def test_same_label_with_different_valuation_roles_fails_closed() -> None:
    fact = _fact(
        "valuation:current",
        "valuation",
        {"price_to_book": 1.8154, "trailing_pe": 3.279},
    )
    packet = {
        "stocks": [
            {
                "ticker": "GENERIC",
                "numeric_registry": build_numeric_registry([fact]),
            }
        ]
    }
    for item in packet["stocks"][0]["numeric_registry"]:
        item["canonical_label"] = "가치평가 배수"
    output = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": ["valuation:current"],
                "core_judgment": {
                    "text": "{{numeric:current}}; {{numeric:median}}"
                },
                "numeric_claims": [],
                "numeric_fact_refs": [
                    _ref(
                        "current",
                        "valuation:current",
                        "fields.price_to_book",
                    ),
                    _ref(
                        "median",
                        "valuation:current",
                        "fields.trailing_pe",
                    ),
                ],
            }
        ]
    }

    result = bind_numeric_fact_references(packet, output)

    assert any(
        "numeric_bound_label_semantic_collision:가치평가 배수:current,median"
        in error
        for error in result.errors
    )
    assert result.report["label_quality"]["semantic_label_collision_count"] == 1


@pytest.mark.parametrize(
    ("field_path", "role", "expected_role"),
    [
        ("fields.zone_low", None, "lower"),
        ("fields.zone_low", "upper", "lower"),
        ("fields.zone_high", None, "upper"),
        ("fields.zone_high", "lower", "upper"),
    ],
)
def test_zone_endpoint_role_is_mandatory_and_directional(
    field_path: str,
    role: str | None,
    expected_role: str,
) -> None:
    fact = _fact(
        "chart:zone",
        "chart_support_zone",
        {"zone_low": 19.44, "zone_high": 20.34, "currency": "USD"},
    )

    result = _bind_stock(
        [fact],
        "{{numeric:zone}}",
        [_ref("zone", "chart:zone", field_path, role=role)],
    )

    assert any(
        f"numeric_fact_ref_zone_role_mismatch:zone:core_judgment.text:"
        f"support_zone_price:{role or 'value'}:{expected_role}" in error
        for error in result.errors
    )
    assert result.report["label_quality"]["zone_role_mismatch_count"] == 1


def test_single_pivot_rejects_zone_role_and_binds_without_one() -> None:
    fact = _fact(
        "chart:invalidation",
        "chart_invalidation",
        {"price": 18.5, "currency": "USD"},
    )
    invalid = _bind_stock(
        [fact],
        "{{numeric:pivot}}",
        [_ref("pivot", "chart:invalidation", "fields.price", role="lower")],
    )
    valid = _bind_stock(
        [fact],
        "{{numeric:pivot}}",
        [_ref("pivot", "chart:invalidation", "fields.price")],
    )

    assert any("numeric_fact_ref_unexpected_role" in error for error in invalid.errors)
    assert valid.errors == ()
    assert "차트 무효화 가격 $18.5" in valid.output["stock_reviews"][0]["core_judgment"]["text"]


def test_bound_korean_numeric_postposition_fails_closed() -> None:
    fact = _fact(
        "earnings",
        "earnings",
        {"revenue": {"value": 60_542_600_000_000, "currency": "KRW"}},
    )

    invalid = _bind_stock(
        [fact],
        "{{numeric:revenue}}와 다른 값을 비교합니다.",
        [_ref("revenue", "earnings", "fields.revenue.value")],
    )
    raw_also_invalid = _bind_stock(
        [fact],
        "{{numeric:revenue}}과 다른 값을 비교합니다.",
        [_ref("revenue", "earnings", "fields.revenue.value")],
    )
    valid = _bind_stock(
        [fact],
        "{{numeric:revenue}} 다른 값을 비교합니다.",
        [
            _ref(
                "revenue",
                "earnings",
                "fields.revenue.value",
                postposition="와/과",
            )
        ],
    )

    assert any("numeric_fact_ref_raw_postposition" in error for error in invalid.errors)
    assert any(
        "numeric_fact_ref_raw_postposition" in error
        for error in raw_also_invalid.errors
    )
    assert valid.errors == ()
    assert "60조5,426억원과" in valid.output["stock_reviews"][0]["core_judgment"]["text"]


def test_bound_currency_numeric_postposition_uses_spoken_unit() -> None:
    fact = _fact(
        "price",
        "price",
        {"current_price": 345.9, "currency": "USD"},
    )

    invalid = _bind_stock(
        [fact],
        "{{numeric:price}}은 현재 기준입니다.",
        [_ref("price", "price", "fields.current_price")],
    )
    raw_also_invalid = _bind_stock(
        [fact],
        "{{numeric:price}}는 현재 기준입니다.",
        [_ref("price", "price", "fields.current_price")],
    )
    valid = _bind_stock(
        [fact],
        "{{numeric:price}} 현재 기준입니다.",
        [_ref("price", "price", "fields.current_price", postposition="은/는")],
    )

    assert any("numeric_fact_ref_raw_postposition" in error for error in invalid.errors)
    assert any(
        "numeric_fact_ref_raw_postposition" in error
        for error in raw_also_invalid.errors
    )
    assert valid.errors == ()
    assert "$345.9는" in valid.output["stock_reviews"][0]["core_judgment"]["text"]


@pytest.mark.parametrize(
    ("display", "family", "expected"),
    [
        ("1원", "와/과", "과"),
        ("1,750억원", "와/과", "과"),
        ("1조3,655억원", "은/는", "은"),
        ("100주", "와/과", "와"),
        ("1.2배", "이/가", "가"),
        ("3%", "을/를", "를"),
        ("-3bp", "은/는", "는"),
    ],
)
def test_numeric_postposition_uses_canonical_spoken_unit(
    display: str,
    family: str,
    expected: str,
) -> None:
    assert resolve_numeric_postposition(display, family) == expected


def test_bound_numeric_copula_rejects_subject_particle_connective() -> None:
    fact = _fact(
        "chart:risk_reward",
        "chart_risk_reward",
        {"ratio": 1.75, "currency": "USD"},
    )
    valid = _bind_stock(
        [fact],
        "{{numeric:rr}} 현재 구조를 보여줍니다.",
        [
            _ref(
                "rr",
                "chart:risk_reward",
                "fields.ratio",
                postposition="이/가",
            )
        ],
    )
    invalid = _bind_stock(
        [fact],
        "{{numeric:rr}}가며 현재 구조를 보여줍니다.",
        [_ref("rr", "chart:risk_reward", "fields.ratio")],
    )

    assert valid.errors == ()
    assert "차트 손익비 1.75배가 현재" in valid.output["stock_reviews"][0]["core_judgment"]["text"]
    assert any("numeric_fact_ref_raw_postposition" in error for error in invalid.errors)


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
        "TWD 기준인 {{numeric:revenue}} ADR 가격과 직접 환산하지 않습니다. "
        "현재 평가에서는 {{numeric:pe}} {{numeric:fpe}}의 방향을 비교합니다. "
        "다음 실적에서 {{numeric:margin}}의 지속성을 확인합니다."
    )
    refs = [
        _ref(
            "revenue",
            "earnings",
            "fields.revenue.value",
            postposition="을/를",
        ),
        _ref("pe", "valuation", "fields.trailing_pe", postposition="와/과"),
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


@pytest.mark.parametrize(
    (
        "pe_source",
        "book_source",
        "expected_pe",
        "expected_pbr",
        "expected_eps",
        "expected_bvps",
    ),
    [
        (
            "consensus_forward",
            "modeled_forward",
            "시장 예상 fPER 10배",
            "내부 추정 fPBR 2배",
            "시장 예상 EPS $3",
            "내부 추정 BVPS $4",
        ),
        (
            "modeled_forward",
            "consensus_forward",
            "내부 추정 fPER 10배",
            "시장 예상 fPBR 2배",
            "내부 추정 EPS $3",
            "시장 예상 BVPS $4",
        ),
    ],
)
def test_mixed_forward_sources_bind_occurrence_level_claims_without_cross_talk(
    pe_source: str,
    book_source: str,
    expected_pe: str,
    expected_pbr: str,
    expected_eps: str,
    expected_bvps: str,
) -> None:
    fact = _fact(
        "valuation:mixed",
        "valuation",
        {
            "currency": "USD",
            "forward_pe": 10.0,
            "forward_eps": 3.0,
            "forward_pe_source": pe_source,
            "forward_price_to_book": 2.0,
            "forward_bvps": 4.0,
            "forward_price_to_book_source": book_source,
        },
    )
    refs = [
        _ref(
            "fpe",
            "valuation:mixed",
            "fields.forward_pe",
            postposition="와/과",
        ),
        _ref(
            "fpbr",
            "valuation:mixed",
            "fields.forward_price_to_book",
            postposition="을/를",
        ),
        _ref(
            "eps",
            "valuation:mixed",
            "fields.forward_eps",
            postposition="와/과",
        ),
        _ref(
            "bvps",
            "valuation:mixed",
            "fields.forward_bvps",
            postposition="을/를",
        ),
    ]
    result = _bind_stock(
        [fact],
        (
            "{{numeric:fpe}} {{numeric:fpbr}} 함께 봅니다. "
            "{{numeric:eps}} {{numeric:bvps}}도 같은 source 경계를 유지합니다."
        ),
        refs,
    )

    assert result.errors == ()
    text = result.output["stock_reviews"][0]["core_judgment"]["text"]
    assert all(
        expected in text
        for expected in (expected_pe, expected_pbr, expected_eps, expected_bvps)
    )
    claims = result.output["stock_reviews"][0]["numeric_claims"]
    assert len(claims) == 4
    assert {item["text_ref"] for item in claims} == {"core_judgment.text"}


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
        "{{numeric:pe}}보다 {{numeric:fpe}} 높습니다.",
        [
            _ref("pe", "valuation:CRCL", "fields.trailing_pe"),
            _ref(
                "fpe",
                "valuation:CRCL",
                "fields.forward_pe",
                postposition="이/가",
            ),
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


@pytest.mark.parametrize(
    ("fact_type", "series_code", "field_path", "value", "expected"),
    [
        (
            "market_real_yield",
            "DFII10",
            "fields.level_pct",
            2.42,
            "미국 10년물 실질금리 2.4%",
        ),
        (
            "market_real_yield",
            "DFII10",
            "fields.change_bp",
            -3.0,
            "미국 10년물 실질금리 변동 -3bp",
        ),
        (
            "market_fx",
            "USDKRW",
            "fields.change_pct",
            0.26,
            "원/달러 환율 등락률 +0.3%",
        ),
    ],
)
def test_market_series_identity_owns_level_and_change_labels(
    fact_type: str,
    series_code: str,
    field_path: str,
    value: float,
    expected: str,
) -> None:
    field = field_path.removeprefix("fields.")
    fact = _fact(
        "market:series",
        fact_type,
        {"series_code": series_code, field: value},
    )

    result = _bind_market(
        [fact],
        "{{numeric:value}}",
        [_ref("value", "market:series", field_path)],
    )

    assert result.errors == ()
    assert result.output["market_review"]["core_judgment"]["text"] == expected


def test_authored_real_yield_synonym_before_full_phrase_is_rejected() -> None:
    fact = _fact(
        "market:real-yield",
        "market_real_yield",
        {"series_code": "DFII10", "change_bp": -3.0},
    )

    result = _bind_market(
        [fact],
        "미국 장기 실질금리 변동 {{numeric:change}}",
        [_ref("change", "market:real-yield", "fields.change_bp")],
    )

    assert any("numeric_fact_ref_redundant_authored_label" in error for error in result.errors)


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
