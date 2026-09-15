from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.working_capital_checkpoint_binding_service import (
    CHECKPOINT_FIELDS,
    CONTRACT_VERSION,
    MODEL_CHECKPOINT_FIELDS,
    STAGE2_MODEL_CHECKPOINT_FIELDS,
    VIEW_CONTRACT_VERSION,
    attach_working_capital_checkpoint_binding_view,
    build_working_capital_checkpoint_binding_view,
    validate_working_capital_checkpoint_bindings,
    working_capital_metrics_in_text,
)


FIXTURES = json.loads(
    Path("tests/fixtures/working_capital_checkpoint_binding_m12bb.json").read_text(
        encoding="utf-8"
    )
)


def _context(*metrics: str) -> dict[str, object]:
    aliases = {
        "inventory": "E06",
        "trade_accounts_receivable": "E05",
        "trade_accounts_payable": "E07",
    }
    return {
        "ticker": "FIXTURE",
        "financial_decision_context": {
            "evidence_items": [
                {
                    "evidence_id": aliases[metric],
                    "metric": metric,
                    "semantic_category": "WORKING_CAPITAL",
                    "comparison": {"kind": "prior_year_end"},
                    "period": {"type": "POINT_IN_TIME"},
                }
                for metric in metrics
            ]
        },
    }


def _view(*metrics: str):
    canonical = {
        "E05": "canonical:fixture:receivables",
        "E06": "canonical:fixture:inventory",
        "E07": "canonical:fixture:payables",
    }
    return build_working_capital_checkpoint_binding_view(
        ticker="FIXTURE",
        context=_context(*metrics),
        alias_to_canonical_ref=canonical,
    )


def _candidate(case: dict[str, object]) -> dict[str, object]:
    row = {"text": case["text"], "evidence_refs": case["refs"]}
    if case["field"] in {"buy_drivers", "sell_drivers"}:
        return {str(case["field"]): [row]}
    return {str(case["field"]): row}


def test_contract_and_existing_checkpoint_surface_are_frozen() -> None:
    assert CONTRACT_VERSION == "working-capital-checkpoint-typed-ref-binding-v1"
    assert VIEW_CONTRACT_VERSION == "working-capital-checkpoint-binding-view-v1"
    assert CHECKPOINT_FIELDS == (
        "core_investment_judgment",
        "dominant_evidence",
        "risk_context",
        "business_reevaluation_up",
        "business_reevaluation_down",
        "fundamental_new_buyer.confirmation_business_condition",
        "fundamental_holder.business_invalidation_condition",
        "buy_drivers",
        "sell_drivers",
    )
    assert MODEL_CHECKPOINT_FIELDS == (
        "core_investment_judgment",
        "dominant_evidence",
        "risk_context",
        "business_reevaluation_up",
        "business_reevaluation_down",
        "buy_drivers",
        "sell_drivers",
    )
    assert STAGE2_MODEL_CHECKPOINT_FIELDS == (
        "fundamental_new_buyer.confirmation_business_condition",
        "fundamental_holder.business_invalidation_condition",
    )


def test_binding_view_contains_alias_and_internal_canonical_identity() -> None:
    view = _view("inventory", "trade_accounts_receivable")

    assert view.metric_to_typed_aliases == {
        "inventory": ("E06",),
        "trade_accounts_receivable": ("E05",),
    }
    assert view.metric_to_canonical_refs == {
        "inventory": ("canonical:fixture:inventory",),
        "trade_accounts_receivable": ("canonical:fixture:receivables",),
    }
    assert "canonical_ref" not in json.dumps(view.model_context())
    assert "fundamental_new_buyer" not in json.dumps(view.model_context())
    assert "fundamental_holder" not in json.dumps(view.model_context())

    stage2 = view.stage2_model_context()
    assert stage2["checkpoint_fields"] == list(STAGE2_MODEL_CHECKPOINT_FIELDS)
    assert stage2["metric_to_typed_aliases"] == {
        "inventory": ["E06"],
        "trade_accounts_receivable": ["E05"],
    }
    assert "core_investment_judgment" not in json.dumps(stage2)


def test_model_context_rejects_unknown_checkpoint_field() -> None:
    with pytest.raises(ValueError, match="unsupported_working_capital_checkpoint_fields"):
        _view("inventory").model_context(checkpoint_fields=("not_a_field",))


@pytest.mark.parametrize("case", FIXTURES["positive"], ids=lambda row: row["id"])
def test_positive_claim_local_bindings_pass(case: dict[str, object]) -> None:
    result = validate_working_capital_checkpoint_bindings(
        _candidate(case),
        _view("inventory", "trade_accounts_receivable"),
    )

    assert result["status"] == "PASS"
    assert result["working_capital_grounding_failure_count"] == 0


@pytest.mark.parametrize("case", FIXTURES["negative"], ids=lambda row: row["id"])
def test_missing_or_wrong_metric_typed_refs_fail(case: dict[str, object]) -> None:
    result = validate_working_capital_checkpoint_bindings(
        _candidate(case),
        _view("inventory", "trade_accounts_receivable"),
    )

    assert result["status"] == "FAIL"
    assert result["working_capital_grounding_failure_count"] == 1


def test_multi_metric_claim_requires_both_selected_metric_refs() -> None:
    result = validate_working_capital_checkpoint_bindings(
        {
            "risk_context": {
                "text": "재고와 매출채권 증가를 확인해야 한다.",
                "evidence_refs": ["canonical:fixture:receivables"],
            }
        },
        _view("inventory", "trade_accounts_receivable"),
    )

    assert result["status"] == "FAIL"
    assert result["rows"][0]["missing_metrics"] == ["inventory"]
    assert result["metric_specific_ref_mismatch_count"] == 1


def test_generic_working_capital_claim_needs_one_selected_typed_ref() -> None:
    view = _view("inventory", "trade_accounts_receivable")
    positive = validate_working_capital_checkpoint_bindings(
        {
            "risk_context": {
                "text": "운전자본의 질은 추가 확인이 필요하다.",
                "evidence_refs": ["canonical:fixture:inventory"],
            }
        },
        view,
    )
    negative = validate_working_capital_checkpoint_bindings(
        {
            "risk_context": {
                "text": "운전자본의 질은 추가 확인이 필요하다.",
                "evidence_refs": ["narrative:risk"],
            }
        },
        view,
    )

    assert positive["status"] == "PASS"
    assert negative["status"] == "FAIL"
    assert negative["narrative_only_substitution_count"] == 1


def test_non_checkpoint_field_does_not_create_a_binding_requirement() -> None:
    result = validate_working_capital_checkpoint_bindings(
        {
            "sector_interpretation": {
                "text": "재고와 매출채권은 자동 악화가 아니다.",
                "evidence_refs": ["narrative:sector"],
            }
        },
        _view("inventory", "trade_accounts_receivable"),
    )

    assert result["status"] == "PASS"
    assert result["working_capital_checkpoint_count"] == 0


def test_no_selected_typed_wc_does_not_manufacture_grounding() -> None:
    result = validate_working_capital_checkpoint_bindings(
        {
            "risk_context": {
                "text": "재고 증가가 확인됐다.",
                "evidence_refs": ["narrative:risk"],
            }
        },
        _view(),
    )

    assert result["status"] == "PASS"
    assert result["working_capital_checkpoint_count"] == 0
    assert result["selected_typed_aliases"] == []


def test_payables_and_unambiguous_cues_are_supported_without_ar_ap() -> None:
    assert working_capital_metrics_in_text("매입채무와 trade payables") == (
        "trade_accounts_payable",
    )
    assert working_capital_metrics_in_text("AR/AP ratio") == ()


def test_binding_view_attachment_is_internal_and_non_mutating() -> None:
    context = _context("inventory")
    attached = attach_working_capital_checkpoint_binding_view(
        context,
        _view("inventory"),
    )

    assert "working_capital_checkpoint_binding" not in context
    assert attached["working_capital_checkpoint_binding"]["metric_to_typed_aliases"] == {
        "inventory": ["E06"]
    }
