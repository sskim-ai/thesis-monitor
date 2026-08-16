from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_reasoning_quality_service import (
    normalize_decision_text,
    relational_reasoning_quality_report,
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
    assert report["hard_checks_passed"] is True
    assert report["deterministic_quality_gate_passed"] is True
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
