from __future__ import annotations

from app.services.working_capital_checkpoint_binding_service import (
    STAGE2_MODEL_CHECKPOINT_FIELDS,
    build_working_capital_checkpoint_binding_view,
)
from scripts import working_capital_checkpoint_binding_m12bb as m12bb
from scripts import stage2_working_capital_binding_parity_m12bd as program


def _view():
    return build_working_capital_checkpoint_binding_view(
        ticker="FIXTURE",
        context={
            "financial_decision_context": {
                "evidence_items": [
                    {
                        "evidence_id": "E04",
                        "metric": "inventory",
                        "comparison": {"kind": "prior_year_end"},
                        "period": {"type": "POINT_IN_TIME"},
                    }
                ]
            }
        },
        alias_to_canonical_ref={"E04": "canonical:fixture:inventory"},
    )


def test_stage2_context_receives_only_stance_owned_wc_binding_fields(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        m12bb,
        "_ORIGINAL_STAGE2_CONTEXT",
        lambda **_kwargs: {"ticker": "FIXTURE", "frozen_stage1_core": {}},
    )
    monkeypatch.setitem(m12bb._ACTIVE_BINDING_VIEWS, "FIXTURE", _view())

    result = m12bb._patched_stage2_context(
        source_context={"ticker": "FIXTURE"},
        raw_stage1_core={},
        normalized_stage1_core={},
    )

    binding = result["working_capital_checkpoint_binding"]
    assert binding["checkpoint_fields"] == list(STAGE2_MODEL_CHECKPOINT_FIELDS)
    assert binding["metric_to_typed_aliases"] == {"inventory": ["E04"]}
    assert "core_investment_judgment" not in binding["checkpoint_fields"]


def test_stage2_context_without_selected_wc_does_not_invent_binding(
    monkeypatch,
) -> None:
    empty = build_working_capital_checkpoint_binding_view(
        ticker="EMPTY",
        context={},
    )
    monkeypatch.setattr(
        m12bb,
        "_ORIGINAL_STAGE2_CONTEXT",
        lambda **_kwargs: {"ticker": "EMPTY", "frozen_stage1_core": {}},
    )
    monkeypatch.setitem(m12bb._ACTIVE_BINDING_VIEWS, "EMPTY", empty)

    result = m12bb._patched_stage2_context(
        source_context={"ticker": "EMPTY"},
        raw_stage1_core={},
        normalized_stage1_core={},
    )

    assert "working_capital_checkpoint_binding" not in result


def test_stage2_prompt_adds_one_generic_rule_without_ticker_exception(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        m12bb,
        "_ORIGINAL_STAGE2_PROMPT",
        lambda **_kwargs: "BASE_STAGE2_PROMPT",
    )

    prompt = m12bb._patched_stage2_prompt(
        packet_id="generation",
        tickers=("FIXTURE",),
        contexts=({},),
    )

    assert prompt.count(m12bb.STAGE2_WC_BINDING_PROMPT) == 1
    assert prompt.endswith("BASE_STAGE2_PROMPT")
    assert "FIC-FIN-02" not in prompt


def test_m12bd_report_sequence_and_runtime_contract_are_frozen() -> None:
    assert len(program.REPORT_SLUGS) == 177
    assert len(set(program.REPORT_SLUGS)) == 177
    assert program.REPORT_SLUGS[0] == "repository-provenance"
    assert program.REPORT_SLUGS[-1] == "program-completion"
    assert program.MODEL == "gpt-5.6-sol"
    assert program.EFFORT == "xhigh"
    assert program.EXPECTED_FICTIONAL_CALLS == 12
    assert program.EXPECTED_SHADOW_CALLS == 18


def test_m12bd_stage2_hooks_are_installed_without_replacing_hard_validator(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        m12bb.capability.base,
        "_stage2_context",
        m12bb._ORIGINAL_STAGE2_CONTEXT,
    )
    monkeypatch.setattr(
        m12bb.capability.base,
        "_stage2_prompt",
        m12bb._ORIGINAL_STAGE2_PROMPT,
    )
    original_validator = m12bb.validate_working_capital_checkpoint_bindings

    m12bb._install_model_input_hooks()

    assert m12bb.capability.base._stage2_context is m12bb._patched_stage2_context
    assert m12bb.capability.base._stage2_prompt is m12bb._patched_stage2_prompt
    assert m12bb.validate_working_capital_checkpoint_bindings is original_validator
