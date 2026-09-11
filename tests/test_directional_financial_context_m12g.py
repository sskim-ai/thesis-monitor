from __future__ import annotations

from scripts import directional_core_price_timing_holdout as holdout
from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as m12g


def test_m12g_scope_reuses_frozen_model_runtime_and_topology() -> None:
    assert m12.MODEL == "gpt-5.6-sol"
    assert m12.EFFORT == "xhigh"
    assert m12.TIMEOUT_SECONDS == 1800
    assert m12.SUBJECTS_PER_CONTEXT == 4
    assert m12.CONTEXT_COUNT == 2
    assert m12.REPETITION_COUNT == 3
    assert m12.EXPECTED_MODEL_CALLS == 6


def test_m12g_prompt_adds_only_material_typed_grounding_behavior() -> None:
    core_prompt = holdout._core_prompt(
        packet_id="m12g-prompt",
        tickers=("FIC-FIN-06",),
        contexts=({"ticker": "FIC-FIN-06", "evidence": []},),
    )
    timing_prompt = holdout._timing_prompt(
        packet_id="m12g-prompt",
        tickers=("FIC-FIN-06",),
        contexts=({"ticker": "FIC-FIN-06", "evidence": []},),
    )

    assert m12g.GROUNDING_PROMPT_MARKER in core_prompt
    assert "not narrative alone" in core_prompt
    assert "no force/list/double count" in core_prompt
    assert m12g.GROUNDING_PROMPT_MARKER not in timing_prompt


def test_positive_and_negative_grounding_fixtures_are_closed() -> None:
    positive = m12g._positive_grounding_fixtures()
    negative = m12g._negative_grounding_fixtures()

    assert positive["fixture_count"] == 6
    assert positive["pass_count"] == 6
    assert positive["status"] == "PASS"
    assert negative["fixture_count"] == 3
    assert negative["rejected_count"] == 3
    assert negative["status"] == "PASS"


def test_narrative_only_substitution_does_not_ground_typed_financial_claim() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고와 매출채권이 연말 이후 증가했다.",
                "evidence_refs": ["fictional:risk"],
            }
        },
        selected_metrics_by_ref={
            "canonical:inventory": "inventory",
            "canonical:receivables": "trade_accounts_receivable",
        },
    )

    assert audit["status"] == "FAIL"
    assert audit["material_financial_anchor_grounding_failure_count"] == 1
    assert audit["working_capital_grounding_failure_count"] == 1
    assert audit["narrative_substitution_failure_count"] == 1


def test_irrelevant_typed_ref_does_not_ground_working_capital_claim() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고 전환과 매출채권 회수를 확인해야 한다.",
                "evidence_refs": ["canonical:cash"],
            }
        },
        selected_metrics_by_ref={
            "canonical:inventory": "inventory",
            "canonical:cash": "cash_and_cash_equivalents",
        },
    )

    assert audit["status"] == "FAIL"
    assert audit["irrelevant_financial_ref_grounding_failure_count"] == 1
    assert audit["financial_checkpoint_refs"] == []


def test_typed_ref_in_unrelated_sector_field_does_not_ground_checkpoint() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고와 매출채권의 전환을 확인해야 한다.",
                "evidence_refs": ["fictional:risk"],
            },
            "sector_interpretation": {
                "text": "산업 수요의 가시성을 확인한다.",
                "evidence_refs": ["canonical:inventory"],
            },
        },
        selected_metrics_by_ref={"canonical:inventory": "inventory"},
    )

    assert audit["status"] == "FAIL"
    assert audit["used_financial_refs"] == ["canonical:inventory"]
    assert audit["material_financial_anchor_refs"] == []
    assert audit["working_capital_grounding_failure_count"] == 1


def test_no_selected_financial_context_adds_no_fake_requirement() -> None:
    control = m12g._no_selected_financial_context_control()

    assert control["fake_grounding_requirement_count"] == 0
    assert control["audit"]["errors"] == []
    assert control["status"] == "PASS"


def test_one_relevant_typed_ref_is_enough_without_forcing_every_selected_ref() -> None:
    audit = m12g.audit_financial_grounding(
        {
            "risk_context": {
                "text": "재고 증가의 전환을 확인해야 한다.",
                "evidence_refs": ["canonical:inventory", "fictional:risk"],
            }
        },
        selected_metrics_by_ref={
            "canonical:inventory": "inventory",
            "canonical:receivables": "trade_accounts_receivable",
        },
    )

    assert audit["status"] == "PASS"
    assert audit["used_financial_refs"] == ["canonical:inventory"]
    assert "canonical:receivables" not in audit["used_financial_refs"]
