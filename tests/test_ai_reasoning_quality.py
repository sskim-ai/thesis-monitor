from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_reasoning_quality_service import (
    _structural_template_exception,
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
        review["priority_watch"] = [f"{watch}의 다음 공시"]
        review["next_checks"] = [f"{core}의 다음 확인"]
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
