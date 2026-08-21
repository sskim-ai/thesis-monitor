from __future__ import annotations

from datetime import date, timedelta
import json
from types import SimpleNamespace

from app.schemas.ai_review import AIStockReview
from app.schemas.thesis import InvestorSupplyContext, PriceContext
from app.services.ai_review_service import _kr_supply_grounding_errors, _price_payload
from app.services.kr_investor_flow_service import (
    build_investor_flow_reconciliation,
    serialized_reconciliation_payload,
    serialize_price_context_with_reconciliation,
)
from app.services.notification_service import _supply_report


SK_HYNIX_WINDOWS = {
    "1d": {
        "foreign_net_buy_qty": 6_365,
        "institution_net_buy_qty": 66_258,
        "individual_net_buy_qty": -720_118,
        "other_corp_net_buy_qty": 647_846,
        "domestic_foreign_net_buy_qty": -351,
    },
    "5d": {
        "foreign_net_buy_qty": 312_747,
        "institution_net_buy_qty": -667_012,
        "individual_net_buy_qty": -926_294,
        "other_corp_net_buy_qty": 1_284_563,
        "domestic_foreign_net_buy_qty": -4_004,
    },
    "20d": {
        "foreign_net_buy_qty": -2_971_200,
        "institution_net_buy_qty": 407_050,
        "individual_net_buy_qty": 1_291_745,
        "other_corp_net_buy_qty": 1_264_923,
        "domestic_foreign_net_buy_qty": 7_482,
    },
}


def test_sk_hynix_full_participant_windows_reconcile_without_residual_inference() -> None:
    result = build_investor_flow_reconciliation(_window_rows(SK_HYNIX_WINDOWS))

    for window in ("1d", "5d", "20d"):
        reconciliation = result["reconciliations"][window]
        assert reconciliation.reconciliation_status == "complete_without_provider_total"
        assert reconciliation.all_participant_net == 0
        assert reconciliation.omitted_net == -reconciliation.displayed_net
        assert reconciliation.material_omitted_flow is True
        assert reconciliation.provider_total is None
    assert result["primary_signal"] == "mixed_window_flow"
    assert result["signal_basis_window"] == "mixed"
    assert result["attribution_safe"] is False
    assert result["other_corp_net_buy_qty"] == 647_846
    assert result["domestic_foreign_net_buy_qty"] == -351


def test_institution_subclasses_are_diagnostic_and_never_double_counted() -> None:
    row = _single_row(
        foreign_net_buy_qty=-100,
        institution_net_buy_qty=60,
        individual_net_buy_qty=40,
        other_corp_net_buy_qty=0,
        domestic_foreign_net_buy_qty=0,
        financial_investment_net_buy_qty=20,
        insurance_net_buy_qty=10,
        investment_trust_net_buy_qty=10,
        other_finance_net_buy_qty=5,
        bank_net_buy_qty=5,
        pension_fund_net_buy_qty=5,
        private_fund_net_buy_qty=5,
        government_net_buy_qty=0,
    )

    result = build_investor_flow_reconciliation([row])

    assert result["reconciliations"]["1d"].all_participant_net == 0
    assert sum(result["diagnostic_subcomponents"]["1d"].values()) == 60
    assert result["institution_subclass_difference"]["1d"] == 0


def test_missing_optional_participant_fails_closed_without_creating_residual_actor() -> None:
    row = _single_row(
        foreign_net_buy_qty=-100,
        institution_net_buy_qty=60,
        individual_net_buy_qty=20,
        other_corp_net_buy_qty=20,
    )

    result = build_investor_flow_reconciliation([row])
    reconciliation = result["reconciliations"]["1d"]

    assert reconciliation.reconciliation_status == "partial_participant_coverage"
    assert reconciliation.all_participant_net is None
    assert reconciliation.omitted_net is None
    assert reconciliation.attribution_safe is False
    assert reconciliation.signal == "participant_attribution_unavailable"
    assert "domestic_foreign" in reconciliation.missing_participants
    assert "residual" not in reconciliation.participant_flows


def test_zero_omitted_flow_allows_explicit_single_window_attribution() -> None:
    result = build_investor_flow_reconciliation(
        [
            _single_row(
                foreign_net_buy_qty=-100,
                institution_net_buy_qty=60,
                individual_net_buy_qty=40,
                other_corp_net_buy_qty=0,
                domestic_foreign_net_buy_qty=0,
            )
        ]
    )

    reconciliation = result["reconciliations"]["1d"]
    assert reconciliation.material_omitted_flow is False
    assert reconciliation.attribution_safe is True
    assert result["primary_signal"] == "foreign_exit_institution_retail_absorption"
    assert result["signal_basis_window"] == "1d"


def test_optional_provider_total_reconciles_or_conflicts_exactly() -> None:
    base = _single_row(
        foreign_net_buy_qty=-100,
        institution_net_buy_qty=60,
        individual_net_buy_qty=40,
        other_corp_net_buy_qty=0,
        domestic_foreign_net_buy_qty=0,
        investor_net_buy_total_qty=0,
    )
    matched = build_investor_flow_reconciliation([base])["reconciliations"]["1d"]
    assert matched.reconciliation_status == "reconciled_to_provider_total"
    assert matched.reconciliation_difference == 0

    conflict_row = {**base, "investor_net_buy_total_qty": 1}
    conflict = build_investor_flow_reconciliation([conflict_row])["reconciliations"]["1d"]
    assert conflict.reconciliation_status == "provider_total_conflict"
    assert conflict.reconciliation_difference == -1
    assert conflict.attribution_safe is False


def test_material_other_participant_flow_never_preserves_led_signal() -> None:
    result = build_investor_flow_reconciliation(
        [
            _single_row(
                foreign_net_buy_qty=100,
                institution_net_buy_qty=-20,
                individual_net_buy_qty=-10,
                other_corp_net_buy_qty=-70,
                domestic_foreign_net_buy_qty=0,
            )
        ]
    )

    assert result["primary_signal"] == "material_other_participant_flow"
    assert result["attribution_safe"] is False


def test_non_attribution_provider_signal_keeps_explicit_twenty_day_basis() -> None:
    rows = _window_rows(SK_HYNIX_WINDOWS)
    result = build_investor_flow_reconciliation(
        rows,
        provider_primary_signal="foreign_reentry",
    )

    # The SK fixture is mixed across 5d/20d, so horizon divergence still wins.
    assert result["primary_signal"] == "mixed_window_flow"

    aligned = {
        window: {
            "foreign_net_buy_qty": value,
            "institution_net_buy_qty": -value // 2,
            "individual_net_buy_qty": -value // 2,
            "other_corp_net_buy_qty": 0,
            "domestic_foreign_net_buy_qty": 0,
        }
        for window, value in (("1d", 10), ("5d", 50), ("20d", 200))
    }
    preserved = build_investor_flow_reconciliation(
        _window_rows(aligned),
        provider_primary_signal="foreign_reentry",
    )
    assert preserved["primary_signal"] == "foreign_reentry"
    assert preserved["signal_basis_window"] == "20d"


def test_fallback_qualifies_major_three_and_mixed_window_signal() -> None:
    result = build_investor_flow_reconciliation(_window_rows(SK_HYNIX_WINDOWS))
    supply = {
        "available": True,
        "as_of_date": "2026-08-21",
        "foreign_net_buy_qty": 6_365,
        "institution_net_buy_qty": 66_258,
        "individual_net_buy_qty": -720_118,
        "foreign_net_buy_qty_5": 312_747,
        "institution_net_buy_qty_5": -667_012,
        "individual_net_buy_qty_5": -926_294,
        "foreign_net_buy_qty_20": -2_971_200,
        "institution_net_buy_qty_20": 407_050,
        "individual_net_buy_qty_20": 1_291_745,
        "confidence": "high",
        "validation_status": "validated",
        "score": 50,
        "quality": "mixed_absorption",
        **result,
    }

    serialized_supply = serialized_reconciliation_payload(supply)
    report = _supply_report({"supply": serialized_supply})

    assert report is not None
    assert "📊 수급(주요 3주체) · 8/21 기준" in report
    assert "5일·20일 흐름 혼재" in report
    assert "기관/개인 흡수" not in report

    packet_supply = _price_payload(
        SimpleNamespace(
            price_context=json.dumps({"decision": {}, "supply": serialized_supply}),
        )
    )["supply"]
    assert packet_supply["primary_signal"] == serialized_supply["primary_signal"]
    assert packet_supply["signal_basis_window"] == serialized_supply["signal_basis_window"]
    assert packet_supply["attribution_safe"] == serialized_supply["attribution_safe"]
    assert packet_supply["reconciliations"] == {
        key: value.model_dump(mode="json") for key, value in result["reconciliations"].items()
    }


def test_semantic_validator_rejects_unsafe_absorber_and_requires_safe_window() -> None:
    review = _review("외국인 이탈·기관/개인 흡수")
    unsafe_stock = {
        "price_and_positioning": {
            "supply": {"attribution_safe": False, "signal_basis_window": "mixed"}
        }
    }
    assert any(
        "kr_supply_attribution_unsafe" in item
        for item in _kr_supply_grounding_errors("000660", "kr", review, unsafe_stock)
    )

    safe_stock = {
        "price_and_positioning": {
            "supply": {"attribution_safe": True, "signal_basis_window": "20d"}
        }
    }
    assert any(
        "kr_supply_attribution_window_missing" in item
        for item in _kr_supply_grounding_errors("000660", "kr", review, safe_stock)
    )
    explicit = _review("20일 기준 기관/개인 흡수")
    assert not _kr_supply_grounding_errors("000660", "kr", explicit, safe_stock)


def test_internal_reconciliation_persists_to_assessment_but_not_public_model_dump() -> None:
    supply = InvestorSupplyContext(available=True, primary_signal="mixed_window_flow")
    supply.set_reconciliation_payload(
        {
            "signal_basis_window": "mixed",
            "attribution_safe": False,
            "reconciliation_contract": "kr-investor-flow-reconciliation-v1",
        }
    )
    context = PriceContext(available=True, supply=supply)

    public_payload = context.model_dump(mode="json")
    assessment_payload = json.loads(serialize_price_context_with_reconciliation(context))

    assert "signal_basis_window" not in public_payload["supply"]
    assert "reconciliation_contract" not in public_payload["supply"]
    assert assessment_payload["supply"]["signal_basis_window"] == "mixed"
    assert assessment_payload["supply"]["attribution_safe"] is False


def _window_rows(windows: dict[str, dict[str, int]]) -> list[dict[str, object]]:
    rows = [
        {"date": (date(2026, 7, 24) + timedelta(days=index)).isoformat()} for index in range(20)
    ]
    fields = windows["20d"]
    for field, total_20 in fields.items():
        total_5 = windows["5d"][field]
        latest = windows["1d"][field]
        rows[0][field] = total_20 - total_5
        rows[15][field] = total_5 - latest
        rows[19][field] = latest
        for index in (*range(1, 15), *range(16, 19)):
            rows[index][field] = 0
    return rows


def _single_row(**values: int) -> dict[str, object]:
    return {"date": "2026-08-21", **values}


def _review(supply_text: str) -> AIStockReview:
    section = {"text": "근거", "fact_ids": []}
    return AIStockReview.model_validate(
        {
            "ticker": "000660",
            "thesis_version": 1,
            "ai_thesis_assessment": "no_material_change",
            "earnings_estimate_view": "unchanged",
            "valuation_view": "neutral",
            "facts_used": [],
            "frameworks_used": [],
            "core_judgment": section,
            "business_earnings": section,
            "price_positioning": {
                **section,
                "new_observer_view": "신규 관찰",
                "holder_view": "보유 관찰",
            },
            "supply_analysis": {"text": supply_text, "fact_ids": []},
            "valuation_analysis": section,
            "numeric_claims": [],
            "unknowns": [],
            "priority_watch": [],
            "next_checks": [],
            "confidence": 0.8,
        }
    )
