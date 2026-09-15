from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.context_preserving_finalization import (
    FinalizationContractError,
    audit_shadow_context_aggregation,
    finalize_fictional_contexts,
)
from scripts.finalization_readiness_policy import (
    evaluate_finalization_readiness,
    evaluate_hard_readiness,
)


def _fictional_document(
    *,
    phase: str,
    repetition: int,
    context: int,
    tickers: tuple[str, ...],
) -> dict[str, object]:
    document: dict[str, object] = {
        "status": "PASS",
        "generation_id": "generation",
        "repetition": repetition,
        "context": context,
        "tickers": list(tickers),
        "transport": {
            "invocation_id": f"generation:run-{repetition}:context-{context}:{phase}"
        },
        "rows": [{"ticker": ticker} for ticker in tickers],
    }
    if phase == "stage2":
        document["compositions"] = [
            {
                "candidate": {"ticker": ticker},
                "core_snapshot_sha256": f"sha-{repetition}-{ticker}",
                "post_compose_core_sha256": f"sha-{repetition}-{ticker}",
            }
            for ticker in tickers
        ]
    return document


def _finalize_context(
    _stage1: dict[str, object],
    stage2: dict[str, object],
) -> list[dict[str, object]]:
    return [
        {"ticker": row["candidate"]["ticker"], "status": "PASS", "errors": []}
        for row in stage2["compositions"]
    ]


def _fictional_inputs(
    *,
    repetitions: int,
    contexts: tuple[tuple[str, ...], ...],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[tuple[int, int], tuple[str, ...]]]:
    stage1 = []
    stage2 = []
    expected = {}
    for repetition in range(1, repetitions + 1):
        for context, tickers in enumerate(contexts, start=1):
            expected[(repetition, context)] = tickers
            stage1.append(
                _fictional_document(
                    phase="stage1",
                    repetition=repetition,
                    context=context,
                    tickers=tickers,
                )
            )
            stage2.append(
                _fictional_document(
                    phase="stage2",
                    repetition=repetition,
                    context=context,
                    tickers=tickers,
                )
            )
    return stage1, stage2, expected


def test_final_01_one_context_four_subjects_passes() -> None:
    inputs = _fictional_inputs(repetitions=1, contexts=(("A", "B", "C", "D"),))
    result = finalize_fictional_contexts(
        generation_id="generation",
        stage1_documents=inputs[0],
        stage2_documents=inputs[1],
        expected_membership=inputs[2],
        finalize_context=_finalize_context,
    )
    assert result["status"] == "PASS"
    assert result["final_row_count"] == 4


def test_final_02_two_contexts_eight_subjects_do_not_form_global_batch() -> None:
    inputs = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D"), ("E", "F", "G", "H")),
    )
    result = finalize_fictional_contexts(
        generation_id="generation",
        stage1_documents=inputs[0],
        stage2_documents=inputs[1],
        expected_membership=inputs[2],
        finalize_context=_finalize_context,
    )
    assert result["final_row_count"] == 8
    assert result["aggregate_uses_context_model_schema"] is False
    assert result["directional_core_batch_over_limit_use_count"] == 0


def test_final_03_eight_subjects_three_repetitions_produce_24_rows() -> None:
    inputs = _fictional_inputs(
        repetitions=3,
        contexts=(("A", "B", "C", "D"), ("E", "F", "G", "H")),
    )
    result = finalize_fictional_contexts(
        generation_id="generation",
        stage1_documents=inputs[0],
        stage2_documents=inputs[1],
        expected_membership=inputs[2],
        finalize_context=_finalize_context,
    )
    assert result["final_row_count"] == 24
    assert result["unique_identity_count"] == 24


def test_final_batch_n01_callback_never_receives_cross_context_batch() -> None:
    inputs = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D"), ("E", "F", "G", "H")),
    )
    observed_sizes: list[int] = []

    def finalize_context(
        _stage1: dict[str, object],
        stage2: dict[str, object],
    ) -> list[dict[str, object]]:
        observed_sizes.append(len(stage2["compositions"]))
        return _finalize_context(_stage1, stage2)

    result = finalize_fictional_contexts(
        generation_id="generation",
        stage1_documents=inputs[0],
        stage2_documents=inputs[1],
        expected_membership=inputs[2],
        finalize_context=finalize_context,
    )
    assert observed_sizes == [4, 4]
    assert result["directional_core_batch_over_limit_use_count"] == 0


def test_final_04_missing_candidate_hard_fails() -> None:
    stage1, stage2, expected = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D"),),
    )
    stage2[0]["compositions"].pop()
    with pytest.raises(FinalizationContractError, match="MEMBERSHIP_MISMATCH"):
        finalize_fictional_contexts(
            generation_id="generation",
            stage1_documents=stage1,
            stage2_documents=stage2,
            expected_membership=expected,
            finalize_context=_finalize_context,
        )


def test_final_05_duplicate_ticker_hard_fails() -> None:
    stage1, stage2, expected = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D"),),
    )
    stage2[0]["compositions"][3]["candidate"]["ticker"] = "A"
    with pytest.raises(FinalizationContractError, match="DUPLICATE_TICKER"):
        finalize_fictional_contexts(
            generation_id="generation",
            stage1_documents=stage1,
            stage2_documents=stage2,
            expected_membership=expected,
            finalize_context=_finalize_context,
        )


def test_final_06_stage_membership_mismatch_hard_fails() -> None:
    stage1, stage2, expected = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D"),),
    )
    stage2[0]["tickers"] = ["A", "B", "C", "X"]
    with pytest.raises(FinalizationContractError, match="MEMBERSHIP_MISMATCH"):
        finalize_fictional_contexts(
            generation_id="generation",
            stage1_documents=stage1,
            stage2_documents=stage2,
            expected_membership=expected,
            finalize_context=_finalize_context,
        )


def test_final_07_core_hash_mismatch_hard_fails() -> None:
    stage1, stage2, expected = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D"),),
    )
    stage2[0]["compositions"][0]["post_compose_core_sha256"] = "changed"
    with pytest.raises(FinalizationContractError, match="CORE_HASH_MISMATCH"):
        finalize_fictional_contexts(
            generation_id="generation",
            stage1_documents=stage1,
            stage2_documents=stage2,
            expected_membership=expected,
            finalize_context=_finalize_context,
        )


def test_final_08_five_candidate_context_hard_fails() -> None:
    inputs = _fictional_inputs(
        repetitions=1,
        contexts=(("A", "B", "C", "D", "E"),),
    )
    with pytest.raises(FinalizationContractError, match="CONTEXT_EXCEEDS_MAX"):
        finalize_fictional_contexts(
            generation_id="generation",
            stage1_documents=inputs[0],
            stage2_documents=inputs[1],
            expected_membership=inputs[2],
            finalize_context=_finalize_context,
        )


def _shadow_document(
    *,
    phase: str,
    context: int,
    tickers: tuple[str, ...],
) -> dict[str, object]:
    document: dict[str, object] = {
        "status": "PASS",
        "generation_id": "shadow-generation",
        "context": context,
        "tickers": list(tickers),
        "transport": {
            "invocation_id": f"shadow-generation:context-{context}:{phase}"
        },
        "rows": [{"ticker": ticker} for ticker in tickers],
    }
    if phase == "stage2":
        document["compositions"] = [
            {
                "candidate": {"ticker": ticker},
                "core_snapshot_sha256": f"sha-{ticker}",
                "post_compose_core_sha256": f"sha-{ticker}",
            }
            for ticker in tickers
        ]
        document["final_rows"] = [{"ticker": ticker} for ticker in tickers]
    return document


def test_shadow_22_subjects_six_contexts_produce_unique_rows() -> None:
    tickers = tuple(f"T{index:02d}" for index in range(1, 23))
    contexts = tuple(
        tuple(tickers[index : index + 4]) for index in range(0, len(tickers), 4)
    )
    expected = {index: batch for index, batch in enumerate(contexts, start=1)}
    documents = {
        phase: [
            _shadow_document(phase=phase, context=index, tickers=batch)
            for index, batch in expected.items()
        ]
        for phase in ("monolithic", "stage1", "stage2")
    }
    result = audit_shadow_context_aggregation(
        generation_id="shadow-generation",
        monolithic_documents=documents["monolithic"],
        stage1_documents=documents["stage1"],
        stage2_documents=documents["stage2"],
        expected_membership=expected,
    )
    assert result["context_count"] == 6
    assert result["final_row_count"] == 22
    assert result["unique_ticker_count"] == 22
    assert result["aggregate_uses_context_model_schema"] is False


def test_shadow_duplicate_context_ticker_hard_fails() -> None:
    tickers = ("A", "B", "C", "D", "E")
    expected = {1: tickers[:4], 2: tickers[4:]}
    documents = {
        phase: [
            _shadow_document(phase=phase, context=index, tickers=batch)
            for index, batch in expected.items()
        ]
        for phase in ("monolithic", "stage1", "stage2")
    }
    broken = deepcopy(documents)
    broken["stage2"][1]["compositions"][0]["candidate"]["ticker"] = "A"
    with pytest.raises(FinalizationContractError, match="MEMBERSHIP_MISMATCH"):
        audit_shadow_context_aggregation(
            generation_id="shadow-generation",
            monolithic_documents=broken["monolithic"],
            stage1_documents=broken["stage1"],
            stage2_documents=broken["stage2"],
            expected_membership=expected,
        )


def test_readiness_p01_primary_and_buyer_variance_do_not_block() -> None:
    result = evaluate_hard_readiness(
        hard_gates={"semantic": True, "runtime": True, "core_immutability": True},
        variance_diagnostics={
            "primary_direction_unstable_subject_count": 1,
            "new_buyer_unstable_subject_count": 1,
        },
    )
    assert result["status"] == "PASS"
    assert result["decision_variance_readiness_blocking"] is False


def test_readiness_p02_same_direction_calibration_variance_does_not_block() -> None:
    result = evaluate_hard_readiness(
        hard_gates={"semantic": True},
        variance_diagnostics={
            "same_direction_calibration_variance_subject_count": 2,
        },
    )
    assert result["status"] == "PASS"


def test_readiness_p03_holder_variance_does_not_block() -> None:
    result = evaluate_hard_readiness(
        hard_gates={"holder_semantics": True},
        variance_diagnostics={"holder_unstable_subject_count": 1},
    )
    assert result["status"] == "PASS"


@pytest.mark.parametrize(
    "failed_gate",
    ("hard_semantic_error", "core_mutation", "invalid_evidence_ref"),
)
def test_readiness_negative_objective_gate_blocks(failed_gate: str) -> None:
    result = evaluate_hard_readiness(
        hard_gates={"baseline": True, failed_gate: False},
        variance_diagnostics={"primary_direction_unstable_subject_count": 0},
    )
    assert result["status"] == "FAIL"
    assert result["failed_hard_gates"] == [failed_gate]


def test_canonical_finalization_name_delegates_to_shared_policy() -> None:
    expected = evaluate_hard_readiness(
        hard_gates={"semantic": True},
        variance_diagnostics={"valid_variance": 2},
    )

    assert evaluate_finalization_readiness(
        hard_gates={"semantic": True},
        variance_diagnostics={"valid_variance": 2},
    ) == expected
