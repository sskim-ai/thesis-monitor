from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.direction_timing_ownership_service import compose_decision
from app.services.two_stage_directional_service import (
    DirectionalCoreJudgment,
    DirectionalCoreJudgmentBatch,
    FundamentalStanceBatch,
    FundamentalStanceCandidate,
    compose_directional_core,
    core_snapshot_sha256,
    extract_core_judgment,
    stage2_forbidden_core_fields,
)
from scripts.synthetic_canary_fixture_repair_ownership_resume import (
    fictional_owned,
    fixture_core,
    fixture_timing,
)
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as runner


def _parts():
    owned = fictional_owned("SYNTHETIC_TWO_STAGE", market="us")
    legacy = fixture_core(owned)
    core = extract_core_judgment(legacy)
    stance = FundamentalStanceCandidate(
        ticker=legacy.ticker,
        fundamental_new_buyer=legacy.fundamental_new_buyer,
        fundamental_holder=legacy.fundamental_holder,
    )
    return owned, legacy, core, stance


def test_stage1_schema_excludes_stance_fields() -> None:
    schema = DirectionalCoreJudgment.model_json_schema()
    assert "fundamental_new_buyer" not in schema["properties"]
    assert "fundamental_holder" not in schema["properties"]
    batch_schema = DirectionalCoreJudgmentBatch.model_json_schema()
    serialized = str(batch_schema)
    assert "fundamental_new_buyer" not in serialized
    assert "fundamental_holder" not in serialized


def test_stage2_schema_exposes_only_stance_fields() -> None:
    properties = FundamentalStanceCandidate.model_json_schema()["properties"]
    assert set(properties) == {
        "ticker",
        "fundamental_new_buyer",
        "fundamental_holder",
    }
    serialized = str(FundamentalStanceBatch.model_json_schema())
    for forbidden in (
        "overall_direction",
        "directional_balance",
        "hold_lean",
        "directional_confidence",
        "business_thesis_change",
        "buy_drivers",
        "sell_drivers",
    ):
        assert forbidden not in serialized


def test_stage_models_reject_cross_owned_fields() -> None:
    _owned, legacy, core, stance = _parts()
    with pytest.raises(ValidationError):
        DirectionalCoreJudgment.model_validate(
            {
                **core.model_dump(mode="json"),
                "fundamental_holder": legacy.fundamental_holder.model_dump(mode="json"),
            }
        )
    with pytest.raises(ValidationError):
        FundamentalStanceCandidate.model_validate(
            {
                **stance.model_dump(mode="json"),
                "overall_direction": legacy.overall_direction,
            }
        )
    assert stage2_forbidden_core_fields(
        {**stance.model_dump(mode="json"), "overall_direction": "HOLD"}
    ) == ("overall_direction",)


def test_composer_preserves_core_hash_and_legacy_shape() -> None:
    _owned, legacy, core, stance = _parts()
    composed = compose_directional_core(core, stance)
    assert composed.core_snapshot_sha256 == core_snapshot_sha256(core)
    assert composed.post_compose_core_sha256 == composed.core_snapshot_sha256
    assert composed.candidate == legacy
    assert extract_core_judgment(composed.candidate) == core


def test_composed_candidate_remains_price_timing_compatible() -> None:
    owned, legacy, core, stance = _parts()
    composed = compose_directional_core(core, stance)
    timing = fixture_timing(owned, legacy)
    decision = compose_decision(composed.candidate, timing)
    assert decision.core == legacy
    assert decision.candidate.ticker == legacy.ticker
    assert decision.candidate.decision == legacy.overall_direction


def test_composer_rejects_cross_subject_stance() -> None:
    _owned, _legacy, core, stance = _parts()
    with pytest.raises(ValueError, match="cross_subject_core_stance_composition"):
        compose_directional_core(core, stance.model_copy(update={"ticker": "OTHER"}))


def test_stage1_prompt_and_schema_have_no_stance_contract() -> None:
    generation = "two-stage-prompt-test"
    _packets, _owned, catalogs, contexts = runner.m12.fictional_inputs(generation)
    tickers = runner.m12.CONTEXTS[0]
    prompt = runner._stage1_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=[contexts[ticker] for ticker in tickers],
    )
    schema = runner._batch_schema(
        model=DirectionalCoreJudgment,
        contract=runner.CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    assert runner.CORE_JUDGMENT_OUTPUT_CONTRACT in prompt
    assert "fundamental_new_buyer" not in prompt
    assert "fundamental_holder" not in prompt
    assert runner.NEW_BUYER_STANCE_PROMPT not in prompt
    assert runner.HOLDER_STANCE_PROMPT.strip() not in prompt
    serialized = str(schema)
    assert "fundamental_new_buyer" not in serialized
    assert "fundamental_holder" not in serialized


def test_stage2_prompt_and_schema_are_stance_only() -> None:
    generation = "two-stage-stance-prompt-test"
    _packets, _owned, catalogs, contexts = runner.m12.fictional_inputs(generation)
    tickers = runner.m12.CONTEXTS[0]
    prompt = runner._stage2_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=[
            {
                **contexts[ticker],
                "core_snapshot_sha256": "0" * 64,
                "frozen_stage1_core": {"ticker": ticker},
            }
            for ticker in tickers
        ],
    )
    schema = runner._batch_schema(
        model=FundamentalStanceCandidate,
        contract=runner.FUNDAMENTAL_STANCE_OUTPUT_CONTRACT,
        packet_id=generation,
        tickers=tickers,
        catalogs=catalogs,
    )
    assert runner.NEW_BUYER_STANCE_PROMPT in prompt
    assert runner.HOLDER_STANCE_PROMPT.strip() in prompt
    assert "FIC-FIN-05" not in runner.NEW_BUYER_STANCE_PROMPT
    assert "FIC-FIN-05" not in runner.HOLDER_STANCE_PROMPT
    serialized = str(schema)
    assert "fundamental_new_buyer" in serialized
    assert "fundamental_holder" in serialized
    for field in (
        "overall_direction",
        "directional_balance",
        "hold_lean",
        "directional_confidence",
        "business_thesis_change",
        "buy_drivers",
        "sell_drivers",
    ):
        assert field not in serialized


def test_shadow_comparison_taxonomy_is_decision_material() -> None:
    _owned, legacy, _core, _stance = _parts()
    same = legacy.model_copy(
        update={
            "directional_confidence": (
                "MEDIUM" if legacy.directional_confidence != "MEDIUM" else "HIGH"
            )
        }
    )
    label, fields = runner._comparison_classification(legacy, same)
    assert label == "SAME_DIRECTION_CALIBRATION_CHANGE"
    assert fields == []

    changed = legacy.model_copy(
        update={
            "fundamental_holder": legacy.fundamental_holder.model_copy(
                update={
                    "stance": (
                        "REVIEW"
                        if legacy.fundamental_holder.stance != "REVIEW"
                        else "HOLDABLE"
                    )
                }
            )
        }
    )
    label, fields = runner._comparison_classification(legacy, changed)
    assert label == "HOLDER_STANCE_CHANGE"
    assert fields == ["fundamental_holder.stance"]
