from __future__ import annotations

import json

from app.services.financial_quality_service import (
    build_financial_quality_state,
    sanitize_financial_snapshot_for_prose,
)
from app.services.notification_service import _message_for_assessment
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.numeric_semantic_registry import build_numeric_registry


def _snapshot(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "current_price": 211_000,
        "currency": "KRW",
        "financial_currency": "KRW",
        "latest_earnings_period": "2026-06-30",
        "earnings_context_source": "preliminary_earnings",
        "earnings_context_is_preliminary": True,
        "latest_revenue": 79_318_700_000_000,
        "latest_operating_income": 60_500_000_000_000,
        "latest_operating_margin": 76.3,
        "latest_revenue_qoq": 18.5,
        "latest_revenue_yoy": 256.8,
        "latest_operating_income_qoq": 44.2,
        "latest_operating_income_yoy": 557.2,
        "ttm_contains_preliminary": True,
        "ttm_eps_usable": True,
        "earnings_quarter_series": [
            {
                "period": period,
                "source": "full_statement" if index < 3 else "preliminary_earnings",
                "normalized_eps_usable": True,
            }
            for index, period in enumerate(
                ("2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30")
            )
        ],
        "trailing_pe_denominator_period_end": "2026-06-30",
        "trailing_pe_basis_status": "directly_comparable",
        "ttm_eps": 29_305.6,
        "trailing_pe": 7.2,
        "trailing_pe_status": "value",
        "forward_eps": 12_881.6,
        "forward_pe": 16.38,
        "forward_pe_status": "value",
        "forward_pe_source": "modeled_forward",
        "forward_pe_input_period": "FY1",
        "forward_pe_basis_status": "directly_comparable",
        "bvps": 52_750,
        "price_to_book": 4.0,
        "price_to_book_status": "value",
        "price_to_book_basis_status": "directly_comparable",
        "pbr_denominator_period_end": "2026-03-31",
        "historical_pe_statistics": {
            "current_value": 7.2,
            "current_percentile": 12.0,
            "historical_median": 10.0,
        },
        "historical_pb_statistics": {
            "current_value": 4.0,
            "current_percentile": 88.0,
        },
        "valuation_relative_position": "premium",
        "valuation_relative_position_reason": "PER와 PBR의 역사적 위치가 높습니다.",
        "data_coverage": {"reason_codes": []},
    }
    value.update(overrides)
    return value


def _critical_source(*, official: bool = True) -> dict[str, object]:
    critical = {
        "period": "2026-06-30",
        "source_type": "preliminary_earnings",
        "provider": "opendart" if official else "unverified_feed",
        "soft_outliers": [
            "net_income_exceeds_revenue",
            "unusually_high_or_low_operating_margin",
        ],
        "hard_errors": [] if official else ["outlier_not_verified_by_official_source"],
        "lineage_verified": True,
    }
    clean = [
        {
            "period": period,
            "source_type": "full_statement",
            "provider": "opendart",
            "hard_errors": [],
            "soft_outliers": [],
            "lineage_verified": True,
        }
        for period in ("2025-09-30", "2025-12-31", "2026-03-31")
    ]
    return {
        **critical,
        "direct_field_sources": {
            field: [critical]
            for field in (
                "latest_revenue",
                "latest_operating_income",
                "latest_operating_margin",
                "latest_revenue_qoq",
                "latest_revenue_yoy",
                "latest_operating_income_qoq",
                "latest_operating_income_yoy",
            )
        },
        "ttm_sources": [*clean, critical],
        "modeled_forward_sources": [*clean, critical],
        "book_source": {
            **clean[-1],
            "period": "2026-03-31",
        },
    }


def _clean_source() -> dict[str, object]:
    source = _critical_source()
    for key in ("soft_outliers", "hard_errors"):
        source[key] = []
    for records in source["direct_field_sources"].values():
        records[0]["soft_outliers"] = []
        records[0]["hard_errors"] = []
    source["ttm_sources"][-1]["soft_outliers"] = []
    source["ttm_sources"][-1]["hard_errors"] = []
    source["modeled_forward_sources"][-1]["soft_outliers"] = []
    source["modeled_forward_sources"][-1]["hard_errors"] = []
    return source


def test_clean_official_preliminary_is_caution_usable() -> None:
    state = build_financial_quality_state(
        _snapshot(),
        source_metadata=_clean_source(),
    )

    assert state["fields"]["latest_revenue"]["state"] == "caution_usable"
    assert state["fields"]["latest_revenue"]["prose_eligible"] is True
    assert state["denied_fields"] == []
    assert state["decision_version"] == "financial-quality-taint-v2"


def test_critical_official_preliminary_denies_direct_and_dependent_pe_fields() -> None:
    state = build_financial_quality_state(
        _snapshot(), source_metadata=_critical_source()
    )

    for field in (
        "latest_revenue",
        "latest_operating_income",
        "latest_operating_margin",
        "latest_revenue_qoq",
        "latest_revenue_yoy",
        "latest_operating_income_qoq",
        "latest_operating_income_yoy",
        "ttm_eps",
        "trailing_pe",
        "forward_eps",
        "forward_pe",
        "historical_pe_statistics.current_value",
        "historical_pe_statistics.current_percentile",
    ):
        assert state["fields"][field]["state"] == "denied"
        assert state["fields"][field]["prose_eligible"] is False
        assert state["fields"][field]["denial_reason"]
    assert state["fields"]["price_to_book"]["state"] == "verified_usable"
    assert state["fields"]["historical_pb_statistics.current_percentile"][
        "prose_eligible"
    ] is True


def test_non_official_outlier_keeps_hard_fail_taint() -> None:
    state = build_financial_quality_state(
        _snapshot(), source_metadata=_critical_source(official=False)
    )

    assert "financial_hard_error" in state["critical_reason_codes"]
    assert state["fields"]["latest_revenue"]["state"] == "denied"


def test_period_mapping_failure_denies_period_financials() -> None:
    state = build_financial_quality_state(
        _snapshot(),
        source_metadata={
            "period": "2026-06-30",
            "source_type": "preliminary_earnings",
            "period_mapping_validation_failed": True,
        },
    )

    assert "period_mapping_validation_failure" in state["critical_reason_codes"]
    assert state["fields"]["latest_operating_income"]["state"] == "denied"


def test_high_growth_without_quality_outlier_is_not_blocked() -> None:
    snapshot = _snapshot(
        latest_revenue_yoy=800.0,
        latest_operating_income_yoy=1_200.0,
    )
    state = build_financial_quality_state(
        snapshot,
        source_metadata={
            "period": "2026-06-30",
            "source_type": "preliminary_earnings",
            "provider": "opendart",
        },
    )

    assert state["fields"]["latest_revenue_yoy"]["state"] == "caution_usable"
    assert state["fields"]["latest_operating_income_yoy"]["state"] == "caution_usable"


def test_independent_consensus_forward_pe_survives_direct_earnings_taint() -> None:
    snapshot = _snapshot(
        forward_pe_source="consensus_forward",
        forward_eps=14_000,
        forward_pe=15.1,
    )
    state = build_financial_quality_state(
        snapshot, source_metadata=_critical_source()
    )

    assert state["fields"]["forward_eps"]["state"] == "verified_usable"
    assert state["fields"]["forward_pe"]["state"] == "verified_usable"
    assert state["fields"]["trailing_pe"]["state"] == "denied"


def test_full_statement_critical_period_in_ttm_denies_trailing_and_historical_pe() -> None:
    snapshot = _snapshot(
        earnings_context_source="full_statement",
        ttm_contains_preliminary=False,
    )
    source = _critical_source()
    source["source_type"] = "full_statement"
    for records in source["direct_field_sources"].values():
        records[0]["source_type"] = "full_statement"
    source["ttm_sources"][-1]["source_type"] = "full_statement"
    source["modeled_forward_sources"][-1]["source_type"] = "full_statement"

    state = build_financial_quality_state(snapshot, source_metadata=source)

    assert snapshot["ttm_contains_preliminary"] is False
    assert state["fields"]["ttm_eps"]["state"] == "denied"
    assert state["fields"]["trailing_pe"]["state"] == "denied"
    assert state["fields"]["historical_pe_statistics.current_value"]["state"] == "denied"
    assert state["fields"]["historical_pe_statistics.current_percentile"]["state"] == "denied"
    assert state["fields"]["trailing_pe"]["denial_reason"] == (
        "critical_input_in_ttm_denominator"
    )


def test_direct_critical_period_outside_verified_ttm_does_not_taint_trailing() -> None:
    snapshot = _snapshot(
        latest_earnings_period="2026-09-30",
        earnings_quarter_series=[
            {
                "period": period,
                "source": "full_statement",
                "normalized_eps_usable": True,
            }
            for period in ("2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30")
        ],
    )
    source = _critical_source()
    source["period"] = "2026-09-30"
    for records in source["direct_field_sources"].values():
        records[0]["period"] = "2026-09-30"
    source["ttm_sources"] = _clean_source()["ttm_sources"]

    state = build_financial_quality_state(snapshot, source_metadata=source)

    assert state["fields"]["latest_revenue"]["state"] == "denied"
    assert state["fields"]["trailing_pe"]["state"] == "verified_usable"
    assert state["fields"]["historical_pe_statistics.current_percentile"]["state"] == (
        "verified_usable"
    )


def test_older_critical_ttm_quarter_denies_trailing_when_latest_is_clean() -> None:
    source = _clean_source()
    older = source["ttm_sources"][1]
    older["soft_outliers"] = ["net_income_exceeds_revenue"]

    state = build_financial_quality_state(_snapshot(), source_metadata=source)

    assert state["fields"]["latest_revenue"]["state"] == "caution_usable"
    assert state["fields"]["ttm_eps"]["state"] == "denied"
    assert state["fields"]["trailing_pe"]["dependency_periods"] == [
        "2025-09-30",
        "2025-12-31",
        "2026-03-31",
        "2026-06-30",
    ]


def test_modeled_forward_only_taint_does_not_block_clean_historical_pe() -> None:
    source = _clean_source()
    source["modeled_forward_sources"] = [
        {
            "period": "2025-06-30",
            "source_type": "full_statement",
            "provider": "opendart",
            "soft_outliers": ["unusually_high_or_low_net_margin"],
            "lineage_verified": True,
        },
        *source["ttm_sources"],
    ]

    state = build_financial_quality_state(_snapshot(), source_metadata=source)

    assert state["fields"]["forward_pe"]["state"] == "denied"
    assert state["fields"]["trailing_pe"]["state"] == "verified_usable"
    assert state["fields"]["historical_pe_statistics.current_percentile"]["state"] == (
        "verified_usable"
    )


def test_clean_book_lineage_records_its_own_period_and_basis() -> None:
    state = build_financial_quality_state(
        _snapshot(), source_metadata=_critical_source()
    )

    pbr = state["fields"]["price_to_book"]
    assert pbr["state"] == "verified_usable"
    assert pbr["source_period"] == "2026-03-31"
    assert pbr["denominator_period"] == "2026-03-31"
    assert pbr["source_period"] != state["source_snapshot"]["period"]


def test_book_basis_conflict_is_not_reapproved_by_quality_service() -> None:
    state = build_financial_quality_state(
        _snapshot(price_to_book_basis_conflict=True),
        source_metadata=_clean_source(),
    )

    assert state["fields"]["price_to_book"]["state"] == "unknown"
    assert state["fields"]["price_to_book"]["prose_eligible"] is False


def test_unknown_ttm_lineage_is_not_promoted_to_verified() -> None:
    state = build_financial_quality_state(
        _snapshot(),
        source_metadata={
            "period": "2026-06-30",
            "source_type": "full_statement",
            "provider": "opendart",
        },
    )

    assert state["fields"]["trailing_pe"]["state"] == "unknown"
    assert state["fields"]["trailing_pe"]["prose_eligible"] is False
    assert state["fields"]["trailing_pe"]["lineage_verification_status"] == (
        "unverified"
    )


def test_fallback_sanitizer_preserves_independent_consensus_and_book() -> None:
    snapshot = _snapshot(
        forward_pe_source="consensus_forward",
        forward_pe_input_period="FY1",
        forward_eps=14_000,
        forward_pe=15.1,
        data_coverage={"reason_codes": ["preliminary_profitability_outlier"]},
    )

    sanitized = sanitize_financial_snapshot_for_prose(snapshot)

    assert sanitized["latest_revenue"] is None
    assert sanitized["trailing_pe"] is None
    assert sanitized["forward_pe"] == 15.1
    assert sanitized["price_to_book"] == 4.0


def test_provider_native_consensus_multiple_requires_non_depositary_identity() -> None:
    common = _snapshot(
        provider="ohlcv-analyst + finnhub",
        is_depositary_security=False,
        forward_pe_source="consensus_forward",
        forward_pe_input_period="provider-defined forward consensus",
        forward_pe_basis_status="not_applicable",
    )
    common_state = build_financial_quality_state(
        common,
        source_metadata=_clean_source(),
    )
    depositary_state = build_financial_quality_state(
        {
            **common,
            "is_depositary_security": True,
            "forward_pe_basis_status": "insufficient_metadata",
        },
        source_metadata=_clean_source(),
    )

    assert common_state["fields"]["forward_pe"]["state"] == "verified_usable"
    assert "provider_native_multiple_contract" in common_state["fields"][
        "forward_pe"
    ]["dependency_fields"]
    assert depositary_state["fields"]["forward_pe"]["state"] == "unknown"


def test_denied_numeric_registry_entry_has_no_display_and_binding_fails_closed() -> None:
    quality = build_financial_quality_state(
        _snapshot(), source_metadata=_critical_source()
    )["fields"]["latest_revenue"]
    facts = [
        {
            "fact_id": "earnings:2026-06-30",
            "fact_type": "earnings",
            "fields": {
                "revenue": {"value": 79_318_700_000_000, "currency": "KRW"}
            },
            "field_quality": {"fields.revenue.value": quality},
        }
    ]
    registry = build_numeric_registry(facts)
    revenue = registry[0]
    packet = {"stocks": [{"ticker": "GENERIC", "numeric_registry": registry}]}
    output = {
        "stock_reviews": [
            {
                "ticker": "GENERIC",
                "facts_used": ["earnings:2026-06-30"],
                "core_judgment": {"text": "{{numeric:revenue}}는 검증 보류입니다."},
                "numeric_claims": [],
                "numeric_fact_refs": [
                    {
                        "ref_id": "revenue",
                        "fact_id": "earnings:2026-06-30",
                        "field_path": "fields.revenue.value",
                        "text_ref": "core_judgment.text",
                    }
                ],
            }
        ]
    }

    bound = bind_numeric_fact_references(packet, output)

    assert revenue["registered"] is True
    assert revenue["prose_allowed"] is False
    assert revenue["canonical_display_value"] is None
    assert revenue["approved_display_variants"] == []
    assert revenue["financial_quality_state"] == "denied"
    assert revenue["dependency_fields"]
    assert revenue["denial_reason"] == "critical_financial_quality_outlier"
    assert any("numeric_fact_ref_semantic_not_supported" in error for error in bound.errors)


def test_sanitizer_removes_only_tainted_financial_and_pe_values() -> None:
    snapshot = _snapshot(
        data_coverage={"reason_codes": ["preliminary_profitability_outlier"]}
    )
    sanitized = sanitize_financial_snapshot_for_prose(snapshot)

    assert sanitized["latest_revenue"] is None
    assert sanitized["trailing_pe"] is None
    assert sanitized["forward_pe"] is None
    assert sanitized["historical_pe_statistics"]["current_percentile"] is None
    assert sanitized["price_to_book"] == 4.0
    assert sanitized["historical_pb_statistics"]["current_percentile"] == 88.0
    assert sanitized["current_price"] == 211_000


class _Assessment:
    def __init__(self) -> None:
        self.ticker = "GENERIC"
        self.assessment_date = "2026-08-14"
        self.thesis_version = 1
        self.status = "no_material_change"
        self.business_thesis_change = "no_material_change"
        self.score = 0
        self.confidence = 0.8
        self.summary = "변화 없음"
        self.new_buyer_view = "가격 구조를 확인합니다."
        self.holder_view = "사업 훼손 조건을 확인합니다."
        self.price_view = "현재 구조"
        self.risk_level = "normal"
        self.structural_risk_level = "normal"
        self.assessment_state = "final"
        self.market_session = "after_hours"
        self.evidence = "[]"
        self.confirmed_facts = json.dumps(["OpenDART financial fact: unit=KRW"])
        self.background_confirmed_facts = "[]"
        self.inferred_implications = "[]"
        self.unknowns = "[]"
        self.confirmed_warnings = "[]"
        self.new_warnings = "[]"
        self.open_warnings = "[]"
        self.open_confirmed_warnings = "[]"
        self.persistent_watch_risks = "[]"
        self.warning_states = "[]"
        self.watch_items = "[]"
        self.earnings_estimate_impact = "up"
        self.market_expectation_assessment = "{}"
        self.price_context = json.dumps(
            {"decision": {"current_price": 211_000, "currency": "KRW"}}
        )
        self.new_buyer_price_view = "가격 구조를 확인합니다."
        self.holder_price_view = "사업 훼손 조건을 확인합니다."
        self.valuation_context = json.dumps(
            {"impact": "expansion", "summary": "강한 이익 증가로 저평가입니다."}
        )
        snapshot = _snapshot(
            data_coverage={"reason_codes": ["preliminary_profitability_outlier"]}
        )
        self.valuation_snapshot = json.dumps(snapshot, ensure_ascii=False)
        self.thesis_snapshot = json.dumps(
            {"base_thesis": "검증된 장기 사업 지표를 확인합니다."},
            ensure_ascii=False,
        )


def test_deterministic_fallback_hides_tainted_numbers_and_interpretation() -> None:
    message = _message_for_assessment(_Assessment())

    for unsafe in (
        "79조",
        "76.3%",
        "256.8%",
        "557.2%",
        "PER: 7.2배",
        "fPER: 16.4배",
        "강한 이익 증가로 저평가",
    ):
        assert unsafe not in message
    assert "PBR" in message
    assert "4.0배" in message
    assert "현재가: 211,000원" in message
    assert "매출·이익과 이익 기반 배수의 정량 해석을 보류" in message
