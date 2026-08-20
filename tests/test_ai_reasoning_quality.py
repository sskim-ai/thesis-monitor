import pytest

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_reasoning_quality_service import (
    _final_rendered_language_report,
    _structural_template_exception,
    _typed_structural_template_exception,
    normalize_decision_text,
    relational_reasoning_quality_report,
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
)


def _output(*, identical_views: bool = False) -> AIDailyReviewOutput:
    stocks = []
    for index, ticker in enumerate(("AAA", "BBB", "CCC"), start=1):
        observer = "새 자금은 확인된 지지의 방어와 이익 개선을 기다립니다."
        holder = (
            observer
            if identical_views
            else "보유자는 차트 훼손과 현금흐름 악화를 서로 다른 재점검 조건으로 봅니다."
        )
        stocks.append(
            {
                "ticker": ticker,
                "thesis_version": 1,
                "ai_thesis_assessment": "no_material_change",
                "earnings_estimate_view": "unchanged",
                "valuation_view": "neutral",
                "facts_used": [f"fact:{ticker}"],
                "frameworks_used": ["market_expectations"],
                "core_judgment": {
                    "text": "같은 공통 결론입니다. 기업별 핵심 논점은 다릅니다.",
                    "fact_ids": [f"fact:{ticker}"],
                },
                "business_earnings": {
                    "text": f"{ticker}의 실행 조건을 확인합니다.",
                    "fact_ids": [f"fact:{ticker}"],
                },
                "price_positioning": {
                    "text": "가격 구조는 사업 논리와 분리합니다.",
                    "new_observer_view": observer,
                    "holder_view": holder,
                    "fact_ids": [f"fact:{ticker}"],
                },
                "supply_analysis": {
                    "text": "수급 공백은 펀더멘털 상태를 바꾸지 않습니다.",
                    "fact_ids": [],
                },
                "valuation_analysis": {
                    "text": f"{ticker}의 배수 관계를 업종 구조와 연결합니다.",
                    "fact_ids": [f"fact:{ticker}"],
                },
                "numeric_claims": [
                    {
                        "fact_id": f"fact:{ticker}",
                        "field_path": "fields.value",
                        "value": index,
                        "unit": "multiple",
                        "semantic_type": "pe_multiple",
                        "text_ref": "valuation_analysis.text",
                        "usage": f"현재 PER {index}배",
                    }
                ],
                "priority_watch": [f"{ticker} 고유 실행 조건"],
                "next_checks": [f"{ticker}의 다음 공식 공시"],
                "unknowns": [f"{ticker}의 현금 전환"],
                "confidence": 0.8,
            }
        )
    return AIDailyReviewOutput.model_validate(
        {
            "schema_version": "4",
            "packet_id": "quality-fixture",
            "claim_id": "quality-claim",
            "analysis_policy_version": "daily-review-v3.10",
            "knowledge_version": "3.0",
            "knowledge_sha256": "a" * 64,
            "chart_knowledge_version": "1.0",
            "chart_knowledge_sha256": "b" * 64,
            "market": "us",
            "assessment_date": "2026-08-15",
            "market_review": {
                "facts_used": [],
                "frameworks_used": ["macro_transmission"],
                "core_judgment": {"text": "시장 맥락", "fact_ids": []},
                "important_changes": [],
                "market_context": {"text": "시장 구조", "fact_ids": []},
                "market_assumptions": {"text": "시장 가정", "fact_ids": []},
                "portfolio_transmission": [],
                "next_checks": [],
                "numeric_claims": [],
                "unknowns": [],
            },
            "stock_reviews": stocks,
        }
    )


def test_quality_audit_detects_substantive_repetition_without_counting_safety() -> None:
    report = relational_reasoning_quality_report(_output())

    repeats = report["repeated_sentences"]
    assert any(
        item["sentence"] == "같은 공통 결론입니다."
        and item["classification"] == "substantive"
        for item in repeats
    )
    assert any(
        item["sentence"] == "수급 공백은 펀더멘털 상태를 바꾸지 않습니다."
        and item["classification"] == "required_common_safety"
        for item in repeats
    )
    assert report["observer_holder_distinct_count"] == 3
    assert report["stock_specific_next_check_count"] == 3
    assert report["generic_next_check_count"] == 0
    assert report["section_numeric_grounding"]["AAA"]["valuation"] == 1
    assert report["hard_checks_passed"] is False
    assert report["deterministic_quality_gate_passed"] is False
    assert report["production_assist_evidence_eligible"] is False


def test_quality_audit_fails_identical_observer_and_holder_decisions() -> None:
    report = relational_reasoning_quality_report(_output(identical_views=True))

    assert report["observer_holder_distinct_count"] == 0
    assert report["hard_checks_passed"] is False


def test_normalization_does_not_create_synonym_only_credit() -> None:
    assert normalize_decision_text("  • 같은   판단입니다. ") == "같은 판단입니다."
    assert normalize_decision_text("수급이 없습니다.") != normalize_decision_text(
        "투자주체 흐름은 미확인입니다."
    )


def test_quality_audit_flags_synonym_only_methodology_repetition() -> None:
    payload = _output().model_dump()
    phrases = (
        "수급은 사업 논리와 분리해 해석합니다.",
        "투자주체 흐름은 펀더멘털과 분리해서 판단합니다.",
        "매매 흐름을 사업 논리에서 분리해 봅니다.",
    )
    for review, phrase in zip(payload["stock_reviews"], phrases, strict=True):
        review["core_judgment"]["text"] = f"{review['ticker']} 고유 판단입니다."
        review["supply_analysis"]["text"] = phrase
    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    assert report["generic_methodology_repeat_count"] == 1
    assert report["generic_methodology_families"][0]["family"] == (
        "supply_separation_methodology"
    )
    assert report["hard_checks_passed"] is False


def test_quality_audit_reports_repeated_numeric_labels_as_hard_failure() -> None:
    payload = _output().model_dump()
    packet_stocks = []
    for index, review in enumerate(payload["stock_reviews"], start=1):
        usage = f"현재 PER {index}배"
        review["valuation_analysis"]["text"] = f"PER {usage}입니다."
        review["numeric_claims"][0].update(
            {
                "field_path": "fields.trailing_pe",
                "semantic_type": "trailing_pe",
                "usage": usage,
            }
        )
        packet_stocks.append(
            {
                "ticker": review["ticker"],
                "numeric_registry": [
                    {
                        "fact_id": f"fact:{review['ticker']}",
                        "field_path": "fields.trailing_pe",
                        "value": index,
                        "unit": "x",
                        "semantic_type": "trailing_pe",
                        "approved_labels": ["현재 PER", "PER"],
                        "canonical_label": None,
                        "canonical_label_required": False,
                        "canonical_label_kind": None,
                    }
                ],
            }
        )
    output = AIDailyReviewOutput.model_validate(payload)

    report = relational_reasoning_quality_report(
        output,
        packet={"market_context": {"numeric_registry": []}, "stocks": packet_stocks},
    )

    label_quality = report["numeric_label_quality"]
    assert label_quality["redundant_authored_label_count"] == 3
    assert label_quality["repeated_bound_label_count"] == 3
    assert label_quality["source_label_mismatch_count"] == 0
    assert label_quality["instrument_label_mismatch_count"] == 0
    assert label_quality["hard_checks_passed"] is False
    assert report["hard_checks_passed"] is False


def test_us_quality_audit_rejects_kr_horizons_and_repeated_flow_unknowns() -> None:
    payload = _output().model_dump()
    flow_unknowns = (
        "당일·단기·중기 투자주체 수급이 없어 방향은 미확인입니다.",
        "1일·5일·20일 외국인 수급이 제공되지 않아 흐름은 Unknown입니다.",
        "기관의 당일·단기·중기 순매수 자료가 없어 판단할 수 없습니다.",
    )
    for review, flow_unknown in zip(
        payload["stock_reviews"], flow_unknowns, strict=True
    ):
        review["core_judgment"]["text"] = f"{review['ticker']} 고유 결론입니다."
        review["supply_analysis"]["text"] = flow_unknown
    output = AIDailyReviewOutput.model_validate(payload)

    report = relational_reasoning_quality_report(output)

    supply = report["supply_routing"]
    assert supply["us_kr_style_horizon_count"] == 3
    assert supply["generic_us_investor_flow_unknown_count"] == 3
    assert report["hard_checks_passed"] is False
    assert report["deterministic_quality_gate_passed"] is False
    assert report["production_assist_evidence_eligible"] is False


def test_quality_audit_rejects_three_stock_numeric_template_skeleton() -> None:
    payload = _output().model_dump()
    rows = []
    for index, ticker in enumerate(("AAA", "BBB", "CCC"), start=1):
        row = payload["stock_reviews"][0].copy()
        row["ticker"] = ticker
        row["facts_used"] = [f"fact:{ticker}"]
        row["core_judgment"] = {
            "text": f"{ticker} 고유 판단은 현재 PER {index}배를 확인합니다.",
            "fact_ids": [f"fact:{ticker}"],
        }
        row["business_earnings"] = {
            "text": f"{ticker} 실적 조건입니다.",
            "fact_ids": [f"fact:{ticker}"],
        }
        row["valuation_analysis"] = {
            "text": f"{ticker} valuation 조건입니다.",
            "fact_ids": [f"fact:{ticker}"],
        }
        row["priority_watch"] = [f"{ticker} 감시"]
        row["next_checks"] = [f"{ticker} 다음 확인"]
        row["unknowns"] = [f"{ticker} 미확인"]
        row["numeric_claims"] = [
            {
                "fact_id": f"fact:{ticker}",
                "field_path": "fields.value",
                "value": index,
                "unit": "x",
                "semantic_type": "pe_multiple",
                "text_ref": "core_judgment.text",
                "usage": f"현재 PER {index}배",
            }
        ]
        rows.append(row)
    payload["stock_reviews"] = rows
    output = AIDailyReviewOutput.model_validate(payload)

    report = relational_reasoning_quality_report(output)

    assert report["template_skeleton_repeat_count"] >= 1
    assert report["hard_checks_passed"] is False


def test_quality_audit_groups_generic_numeric_summary_across_arities() -> None:
    payload = _output().model_dump()
    semantics = (
        [("revenue", "매출 1억원")],
        [("revenue", "매출 2억원"), ("operating_margin", "영업이익률 10%")],
        [
            ("revenue", "매출 3억원"),
            ("operating_income", "영업이익 1억원"),
            ("operating_margin", "영업이익률 20%"),
        ],
    )
    for review, metrics in zip(payload["stock_reviews"], semantics, strict=True):
        usages = "; ".join(usage for _, usage in metrics)
        review["business_earnings"]["text"] = (
            f"현재 확인된 핵심 숫자는 {usages}입니다. "
            f"{review['ticker']} 사업 전환을 확인합니다."
        )
        review["numeric_claims"] = [
            {
                "fact_id": f"earnings:{review['ticker']}",
                "field_path": f"fields.metric_{index}",
                "value": float(index),
                "unit": "amount",
                "semantic_type": semantic,
                "text_ref": "business_earnings.text",
                "usage": usage,
            }
            for index, (semantic, usage) in enumerate(metrics, start=1)
        ]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    assert report["generic_numeric_summary_repeat_count"] == 1
    family = report["generic_numeric_summary_families"][0]
    assert family["stock_count"] == 3
    assert family["tickers"] == ["AAA", "BBB", "CCC"]
    assert report["hard_checks_passed"] is False


def test_typed_skeleton_does_not_merge_rr_and_pbr_relations() -> None:
    payload = _output().model_dump()
    for index, review in enumerate(payload["stock_reviews"], start=1):
        review["core_judgment"]["text"] = f"{review['ticker']} 고유 결론입니다."
        review["business_earnings"]["text"] = f"{review['ticker']} 실적 조건입니다."
        review["priority_watch"] = [f"{review['ticker']} 감시"]
        review["next_checks"] = [f"{review['ticker']} 다음 확인"]
        review["unknowns"] = [f"{review['ticker']} 미확인"]
        if index < 3:
            review["supply_analysis"]["text"] = (
                f"이전 차트 손익비 {index}배; 현재 차트 손익비 {index + 1}배."
            )
            review["numeric_claims"] = [
                {
                    "fact_id": f"rr:{review['ticker']}",
                    "field_path": "fields.previous_ratio",
                    "value": float(index),
                    "unit": "x",
                    "semantic_type": "previous_risk_reward_ratio",
                    "text_ref": "supply_analysis.text",
                    "usage": f"이전 차트 손익비 {index}배",
                },
                {
                    "fact_id": f"rr:{review['ticker']}",
                    "field_path": "fields.current_ratio",
                    "value": float(index + 1),
                    "unit": "x",
                    "semantic_type": "current_risk_reward_ratio",
                    "text_ref": "supply_analysis.text",
                    "usage": f"현재 차트 손익비 {index + 1}배",
                },
            ]
        else:
            review["valuation_analysis"]["text"] = "현재 PBR 3배; PBR 역사적 백분위 90%."
            review["numeric_claims"] = [
                {
                    "fact_id": "valuation:current",
                    "field_path": "fields.price_to_book",
                    "value": 3.0,
                    "unit": "x",
                    "semantic_type": "price_to_book",
                    "text_ref": "valuation_analysis.text",
                    "usage": "현재 PBR 3배",
                },
                {
                    "fact_id": "valuation:current",
                    "field_path": "fields.historical_pb_statistics.current_percentile",
                    "value": 90.0,
                    "unit": "percentile",
                    "semantic_type": "historical_pb_percentile",
                    "text_ref": "valuation_analysis.text",
                    "usage": "PBR 역사적 백분위 90%",
                },
            ]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    numeric_pairs = [
        item
        for item in report["template_skeleton_repeats"]
        if item["skeleton"] == "<numeric>; <numeric>."
    ]
    assert numeric_pairs == []


def test_typed_skeleton_still_detects_same_rr_relation() -> None:
    payload = _output().model_dump()
    for index, review in enumerate(payload["stock_reviews"], start=1):
        review["core_judgment"]["text"] = f"{review['ticker']} 고유 결론입니다."
        review["business_earnings"]["text"] = f"{review['ticker']} 실적 조건입니다."
        review["supply_analysis"]["text"] = (
            f"이전 차트 손익비 {index}배; 현재 차트 손익비 {index + 1}배."
        )
        review["numeric_claims"] = [
            {
                "fact_id": f"rr:{review['ticker']}",
                "field_path": "fields.previous_ratio",
                "value": float(index),
                "unit": "x",
                "semantic_type": "previous_risk_reward_ratio",
                "text_ref": "supply_analysis.text",
                "usage": f"이전 차트 손익비 {index}배",
            },
            {
                "fact_id": f"rr:{review['ticker']}",
                "field_path": "fields.current_ratio",
                "value": float(index + 1),
                "unit": "x",
                "semantic_type": "current_risk_reward_ratio",
                "text_ref": "supply_analysis.text",
                "usage": f"현재 차트 손익비 {index + 1}배",
            },
        ]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    rr_repeat = next(
        item
        for item in report["template_skeleton_repeats"]
        if item["relation"] == "previous_to_current"
    )
    assert rr_repeat["owner"] == "price_context"
    assert rr_repeat["stock_count"] == 3


def test_business_numeric_ownership_rejects_valuation_fillers() -> None:
    payload = _output().model_dump()
    claims = (
        ("valuation:current", "bvps", "BVPS 10달러"),
        ("valuation:current", "ttm_eps", "TTM EPS 2달러"),
        ("earnings:2026-06-30", "ttm_eps", "TTM EPS 3달러"),
    )
    for review, (fact_id, semantic, usage) in zip(
        payload["stock_reviews"], claims, strict=True
    ):
        review["business_earnings"]["text"] = f"{usage}를 실적 맥락에서 확인합니다."
        review["numeric_claims"] = [
            {
                "fact_id": fact_id,
                "field_path": f"fields.{semantic}",
                "value": 1.0,
                "unit": "amount",
                "semantic_type": semantic,
                "text_ref": "business_earnings.text",
                "usage": usage,
            }
        ]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    ownership = report["numeric_ownership"]
    assert ownership["business_earnings_violation_count"] == 2
    assert {item["ticker"] for item in ownership["business_earnings_violations"]} == {
        "AAA",
        "BBB",
    }
    assert ownership["hard_checks_passed"] is False


def test_quality_audit_classifies_required_structural_templates() -> None:
    assert (
        _structural_template_exception(
            "동적 지지구간 하단 10원부터 동적 지지구간 상단 12원까지입니다.",
            "<numeric>부터 <numeric>까지입니다.",
        )
        == "canonical_zone_endpoint_contract"
    )
    assert (
        _structural_template_exception(
            (
                "당일 외국인 순매수 1주와 기관 순매도 2주, 최근 흐름은 "
                "외국인 5일 순매수 3주와 기관 5일 순매도 4주, 중기 누적은 "
                "외국인 20일 순매수 5주와 기관 20일 순매도 6주입니다."
            ),
            "numeric supply skeleton",
        )
        == "kr_six_horizon_numeric_supply_contract"
    )
    assert (
        _structural_template_exception(
            "현재가 10,000원 수준입니다.",
            "<numeric> 수준입니다.",
        )
        == "canonical_current_price_statement"
    )
    assert (
        _structural_template_exception(
            "외국인 당일 순매수 1주, 기관 당일 순매도 2주.",
            "<numeric>, <numeric>.",
        )
        == "kr_actor_horizon_numeric_pair"
    )


@pytest.mark.parametrize(
    ("semantic_types", "expected"),
    (
        (
            ["foreign_net_buy_qty", "institution_net_buy_qty"],
            "canonical_supply_flow_tuple_v1",
        ),
        (
            ["foreign_net_buy_qty_5d", "institution_net_buy_qty_5d"],
            "canonical_supply_flow_tuple_v1",
        ),
        (
            ["foreign_net_buy_qty_20d", "institution_net_buy_qty_20d"],
            "canonical_supply_flow_tuple_v1",
        ),
        (["foreign_net_buy_qty", "current_price_risk_reward_ratio"], None),
    ),
)
def test_typed_supply_tuple_exception_requires_exact_actor_horizon_pair(
    semantic_types: list[str],
    expected: str | None,
) -> None:
    assert (
        _typed_structural_template_exception(
            {
                "section": "supply_analysis",
                "owner": "positioning",
                "relation": "metric_set",
                "semantic_types": semantic_types,
                "skeleton": "<numeric>, <numeric>.",
            }
        )
        == expected
    )


def test_structured_supply_tuple_does_not_exempt_repeated_interpretive_prose() -> None:
    payload = _output().model_dump()
    payload["market"] = "kr"
    for index, review in enumerate(payload["stock_reviews"], start=1):
        review["core_judgment"]["text"] = f"{review['ticker']} 고유 판단입니다."
        review["business_earnings"]["text"] = f"{review['ticker']} 실적 조건입니다."
        review["supply_analysis"]["text"] = (
            f"외국인 당일 순매수 {index}주, 기관 당일 순매도 {index + 1}주. "
            "외국인과 기관의 방향을 추가 확인합니다."
        )
        review["priority_watch"] = [f"{review['ticker']} 감시"]
        review["next_checks"] = [f"{review['ticker']} 다음 확인"]
        review["unknowns"] = [f"{review['ticker']} 미확인"]
        review["numeric_claims"] = [
            {
                "fact_id": f"positioning:{review['ticker']}",
                "field_path": "fields.foreign_net_buy_qty",
                "value": index,
                "unit": "shares",
                "semantic_type": "foreign_net_buy_qty",
                "text_ref": "supply_analysis.text",
                "usage": f"외국인 당일 순매수 {index}주",
            },
            {
                "fact_id": f"positioning:{review['ticker']}",
                "field_path": "fields.institution_net_buy_qty",
                "value": -(index + 1),
                "unit": "shares",
                "semantic_type": "institution_net_buy_qty",
                "text_ref": "supply_analysis.text",
                "usage": f"기관 당일 순매도 {index + 1}주",
            },
        ]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    assert any(
        item["reason"] == "canonical_supply_flow_tuple_v1"
        for item in report["template_skeleton_exceptions"]
    )
    assert any(
        item["sentence"] == "외국인과 기관의 방향을 추가 확인합니다."
        and item["classification"] == "substantive"
        for item in report["repeated_sentences"]
    )
    assert report["hard_checks_passed"] is False


def test_current_rr_exact_value_has_one_price_context_owner() -> None:
    payload = _output().model_dump()
    review = payload["stock_reviews"][0]
    review["price_positioning"]["text"] = "현재가 기준 차트 손익비 1.2배입니다."
    review["numeric_claims"].append(
        {
            "fact_id": "chart:structure:risk_reward:current_price",
            "field_path": "fields.ratio",
            "value": 1.2,
            "unit": "x",
            "semantic_type": "current_price_risk_reward_ratio",
            "text_ref": "price_positioning.text",
            "usage": "현재가 기준 차트 손익비 1.2배",
        }
    )

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    assert report["numeric_primary_ownership"]["current_rr_violation_count"] == 0


def test_current_rr_exact_value_rejects_cross_section_duplicate() -> None:
    payload = _output().model_dump()
    review = payload["stock_reviews"][0]
    review["core_judgment"]["text"] = "현재가 기준 차트 손익비 1.2배입니다."
    review["price_positioning"]["text"] = "현재가 기준 차트 손익비 1.2배입니다."
    rr_claim = {
        "fact_id": "chart:structure:risk_reward:current_price",
        "field_path": "fields.ratio",
        "value": 1.2,
        "unit": "x",
        "semantic_type": "current_price_risk_reward_ratio",
        "usage": "현재가 기준 차트 손익비 1.2배",
    }
    review["numeric_claims"].extend(
        [
            {**rr_claim, "text_ref": "core_judgment.text"},
            {**rr_claim, "text_ref": "price_positioning.text"},
        ]
    )

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )

    ownership = report["numeric_primary_ownership"]
    assert ownership["current_rr_violation_count"] == 1
    assert ownership["current_rr_violations"][0]["reason"] == (
        "current_rr_outside_primary_owner"
    )
    assert report["hard_checks_passed"] is False


def test_kr_supply_coverage_requires_numeric_claims_for_eligible_horizons() -> None:
    payload = _output().model_dump()
    payload["market"] = "kr"
    semantic_types = (
        "foreign_net_buy_qty",
        "foreign_net_buy_qty_5d",
        "foreign_net_buy_qty_20d",
        "institution_net_buy_qty",
        "institution_net_buy_qty_5d",
        "institution_net_buy_qty_20d",
    )
    packet_stocks = []
    for review in payload["stock_reviews"]:
        ticker = review["ticker"]
        registry = [
            {
                "fact_id": f"positioning:{ticker}",
                "field_path": f"fields.{semantic_type}",
                "semantic_type": semantic_type,
                "prose_allowed": True,
            }
            for semantic_type in semantic_types
        ]
        packet_stocks.append({"ticker": ticker, "numeric_registry": registry})
    output = AIDailyReviewOutput.model_validate(payload)

    report = relational_reasoning_quality_report(
        output,
        packet={"market_context": {"numeric_registry": []}, "stocks": packet_stocks},
    )

    assert all(
        len(item["eligible_semantics"]) == 6
        and len(item["missing_semantics"]) == 6
        and item["numeric_horizon_coverage_passed"] is False
        for item in report["kr_supply_numeric_coverage"]
    )
    assert report["hard_checks_passed"] is False


def test_quality_audit_checks_rendered_market_specific_heading() -> None:
    output = _output()
    messages = ["market", *("📊 수급\nbody" for _ in output.stock_reviews)]

    report = relational_reasoning_quality_report(output, rendered_messages=messages)

    heading = report["rendered_heading_quality"]
    assert heading["expected_heading"] == "📊 거래량·포지셔닝"
    assert heading["mismatch_count"] == 3
    assert report["hard_checks_passed"] is False


def test_quality_audit_checks_identity_across_final_rendered_payload() -> None:
    output = _output()
    packet = {
        "market_context": {"numeric_registry": []},
        "stocks": [
            {
                "ticker": review.ticker,
                "numeric_registry": [],
                "valuation": {"security_identity_state": "unknown"},
            }
            for review in output.stock_reviews
        ],
    }
    messages = [
        "market",
        "📊 거래량·포지셔닝\nADR 가격 기준입니다.",
        "📊 거래량·포지셔닝\n현재 거래 증권 가격 기준입니다.",
        "📊 거래량·포지셔닝\n현재 거래 증권 가격 기준입니다.",
    ]

    report = relational_reasoning_quality_report(
        output,
        packet=packet,
        rendered_messages=messages,
    )

    assert report["rendered_identity_prose_mismatch_count"] == 1
    assert report["rendered_identity_prose_mismatches"][0]["ticker"] == "AAA"


def test_quality_gate_rejects_final_rendered_particle_duplicate_and_internal_terms() -> None:
    output = _output()
    messages = [
        "market",
        "📊 거래량·포지셔닝\n현재가 $20.18는 지지 안입니다.",
        "📊 거래량·포지셔닝\n현재가 현재가 기준 차트 손익비 1.77배입니다.",
        "📊 거래량·포지셔닝\n엔진이 가장 가까운 적격 저항을 쓴 값입니다.",
    ]

    report = relational_reasoning_quality_report(
        output, rendered_messages=messages
    )
    final = report["final_rendered_language"]

    assert final["price_particle_error_count"] == 1
    assert final["duplicate_canonical_label_count"] == 1
    assert final["internal_implementation_term_count"] == 1
    assert final["hard_checks_passed"] is False
    assert report["hard_checks_passed"] is False


def test_quality_gate_accepts_particle_safe_price_and_user_facing_rr_language() -> None:
    output = _output()
    messages = [
        "market",
        "📊 거래량·포지셔닝\n현재가는 $20.18이며 현재가 기준 차트 손익비는 1.77배입니다.",
        "📊 거래량·포지셔닝\n동적 지지구간 하단 $19.44와 $345.9 수준의 현재 가격을 확인합니다.",
        "📊 거래량·포지셔닝\n가장 가까운 적격 저항을 기준으로 현재가 손익비를 확인합니다.",
    ]

    report = relational_reasoning_quality_report(
        output, rendered_messages=messages
    )

    assert report["final_rendered_language"]["hard_checks_passed"] is True


def test_final_language_gate_checks_metric_and_korean_object_particles() -> None:
    failed = _final_rendered_language_report(
        ["FCF을 확인하고 투자 회수을 점검하며 cash runway을 검증합니다."]
    )
    passed = _final_rendered_language_report(
        ["FCF를 확인하고 투자 회수를 점검하며 cash runway를 검증합니다."]
    )

    assert failed["korean_particle_error_count"] == 3
    assert failed["hard_checks_passed"] is False
    assert passed["korean_particle_error_count"] == 0
    assert passed["hard_checks_passed"] is True


def test_final_language_gate_uses_canonical_metric_particle_vocabulary() -> None:
    failed = _final_rendered_language_report(
        ["PBR를, ROE을, RR를, HBM를 각각 확인합니다."]
    )
    passed = _final_rendered_language_report(
        ["PBR을, ROE를, RR을, HBM을 각각 확인합니다."]
    )

    assert failed["korean_particle_error_count"] == 4
    assert failed["hard_checks_passed"] is False
    assert passed["korean_particle_error_count"] == 0
    assert passed["hard_checks_passed"] is True


def test_final_language_gate_rejects_malformed_supply_parallel_fragment() -> None:
    failed = _final_rendered_language_report(
        ["외국인 5일 순매수 163,521주는, 기관 5일 순매도 124,946주를."]
    )
    passed = _final_rendered_language_report(
        [
            "최근 5일 외국인은 163,521주 순매수했지만 기관은 "
            "124,946주 순매도해 최근 수급 방향이 엇갈립니다."
        ]
    )

    assert failed["malformed_actor_flow_count"] == 2
    assert failed["incomplete_predicate_count"] >= 1
    assert failed["hard_checks_passed"] is False
    assert passed["malformed_actor_flow_count"] == 0
    assert passed["incomplete_predicate_count"] == 0
    assert passed["hard_checks_passed"] is True


def test_quality_gate_rejects_watch_next_exact_and_role_overlap() -> None:
    payload = _output().model_dump()
    duplicate = "다음 공식 실적에서 HBM 수율을 확인합니다."
    payload["stock_reviews"][0]["priority_watch"] = [duplicate]
    payload["stock_reviews"][0]["next_checks"] = [duplicate]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )
    overlap = report["watch_next_check_overlap"]

    assert overlap["exact_overlap_count"] == 1
    assert overlap["watch_role_violation_count"] == 1
    assert overlap["meaningless_overlap_count"] == 1
    assert overlap["hard_checks_passed"] is False


def test_quality_gate_allows_ongoing_watch_and_event_oriented_next_check() -> None:
    payload = _output().model_dump()
    payload["stock_reviews"][0]["priority_watch"] = [
        "HBM 수율과 공급 discipline"
    ]
    payload["stock_reviews"][0]["next_checks"] = [
        "다음 공식 실적에서 HBM 수율과 재고가 마진으로 이어지는지 확인합니다."
    ]
    payload["stock_reviews"][1]["priority_watch"] = []

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )
    overlap = report["watch_next_check_overlap"]

    assert overlap["meaningless_overlap_count"] == 0
    assert overlap["hard_checks_passed"] is True


def test_quality_gate_rejects_semantically_same_watch_and_undated_check() -> None:
    payload = _output().model_dump()
    payload["stock_reviews"][0]["priority_watch"] = ["HBM 수율 확인"]
    payload["stock_reviews"][0]["next_checks"] = ["HBM 수율 점검"]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )
    overlap = report["watch_next_check_overlap"]

    assert overlap["semantic_overlap_count"] == 1
    assert overlap["meaningless_overlap_count"] == 1
    assert overlap["hard_checks_passed"] is False


def test_quality_gate_rejects_same_numeric_fact_in_three_sections() -> None:
    payload = _output().model_dump()
    claim = payload["stock_reviews"][0]["numeric_claims"][0]
    payload["stock_reviews"][0]["numeric_claims"] = [
        dict(claim, text_ref="core_judgment.text"),
        dict(claim, text_ref="price_positioning.text"),
        dict(claim, text_ref="price_positioning.new_observer_view"),
    ]

    report = relational_reasoning_quality_report(
        AIDailyReviewOutput.model_validate(payload)
    )
    repetition = report["numeric_fact_repetition"]

    assert repetition["same_fact_three_or_more_count"] == 1
    assert repetition["rows"][0]["occurrence_count"] == 3
    assert repetition["hard_checks_passed"] is False


def test_quality_gate_allows_typed_neutral_absolute_valuation_statement() -> None:
    assert _structural_template_exception(
        "현재 PER 10배는 이익 기준의 절대 배수입니다.",
        "<numeric>는 이익 기준의 절대 배수입니다.",
    ) == "typed_neutral_absolute_valuation_statement"


def test_runtime_quality_receipt_binds_packet_output_and_rendered_payload() -> None:
    payload = _output().model_dump()
    descriptions = (
        ("수주 전환", "마진 회복", "박스 하단", "거래 감소", "현금흐름"),
        ("재고 정상화", "원가 안정", "돌파 재시험", "거래 증가", "제품 믹스"),
        ("고객 다변화", "매출 전환", "저항 확인", "거래 보통", "투자 집행"),
    )
    for review, description in zip(
        payload["stock_reviews"], descriptions, strict=True
    ):
        ticker = review["ticker"]
        core, earnings, price, volume, watch = description
        review["core_judgment"]["text"] = f"{ticker}의 {core} 여부가 핵심입니다."
        review["business_earnings"]["text"] = f"{earnings}의 공식 확인을 기다립니다."
        review["price_positioning"]["text"] = f"현재 {price}이 가격 기준입니다."
        review["price_positioning"]["new_observer_view"] = f"신규 자금은 {price} 방어를 봅니다."
        review["price_positioning"]["holder_view"] = f"보유자는 {watch} 훼손을 봅니다."
        review["supply_analysis"]["text"] = f"{volume} 상태를 상대거래량으로 확인합니다."
        review["valuation_analysis"]["text"] = f"{watch} 전에는 절대 배수만 봅니다."
        review["priority_watch"] = [f"{watch}의 지속 여부"]
        review["next_checks"] = [f"다음 공식 공시에서 {core} 여부를 확인합니다."]
        review["unknowns"] = [f"{earnings}의 지속성"]
    output = AIDailyReviewOutput.model_validate(payload)
    packet = {
        "packet_id": output.packet_id,
        "analysis_policy_version": output.analysis_policy_version,
        "output_schema_version": output.schema_version,
        "market_context": {"numeric_registry": []},
        "stocks": [
            {"ticker": review.ticker, "numeric_registry": []}
            for review in output.stock_reviews
        ],
    }
    messages = [
        {"ticker": "__DAILY_DIGEST__", "logical_identity": "market", "text": "market"},
        *(
            {
                "ticker": review.ticker,
                "logical_identity": f"stock:{review.ticker}",
                "text": "📊 거래량·포지셔닝\nbody",
            }
            for review in output.stock_reviews
        ),
    ]

    receipt = runtime_message_quality_receipt(packet, output, messages)

    assert receipt["status"] == "passed"
    assert verify_runtime_message_quality_receipt(receipt, packet, output, messages)
    tampered = [dict(item) for item in messages]
    tampered[-1]["text"] += " changed"
    assert not verify_runtime_message_quality_receipt(
        receipt, packet, output, tampered
    )

    wrong_policy = dict(receipt, policy_version="daily-review-v0")
    assert not verify_runtime_message_quality_receipt(
        wrong_policy, packet, output, messages
    )
    wrong_schema = dict(receipt, schema_version="3")
    assert not verify_runtime_message_quality_receipt(
        wrong_schema, packet, output, messages
    )
    invalid_checked_at = dict(receipt, checked_at="not-a-timestamp")
    assert not verify_runtime_message_quality_receipt(
        invalid_checked_at, packet, output, messages
    )
    naive_checked_at = dict(receipt, checked_at="2026-08-17T12:00:00")
    assert not verify_runtime_message_quality_receipt(
        naive_checked_at, packet, output, messages
    )
